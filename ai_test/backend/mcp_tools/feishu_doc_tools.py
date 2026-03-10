"""
飞书文档 MCP 工具
================
通过 langchain-mcp-adapters 连接 @larksuiteoapi/lark-mcp（stdio 子进程），
将所有 MCP 工具转为 LangChain Tools，供知识库导入使用。

支持的飞书文档 URL 格式：
  - https://*.feishu.cn/docx/{token}   新版文档
  - https://*.feishu.cn/docs/{token}   旧版文档
  - https://*.feishu.cn/wiki/{token}   知识库 Wiki
  - https://*.larksuite.com/...        国际版 Lark
"""
import re
import logging
from typing import Optional

from config.settings import FEISHU_APP_ID, FEISHU_APP_SECRET

logger = logging.getLogger(__name__)

# 飞书文档 URL 正则：匹配域名 + 文档类型 + token
FEISHU_URL_PATTERN = re.compile(
    r"https://[a-zA-Z0-9\-]+\.(feishu\.cn|larksuite\.com|larkoffice\.com)"
    r"/(docx|docs|wiki)/([A-Za-z0-9\-_]+)"
)


def parse_feishu_url(url: str) -> Optional[dict]:
    """
    解析飞书文档 URL，提取文档类型和 token。

    返回: {"doc_type": "docx"|"docs"|"wiki", "token": "..."}
    若不是有效的飞书文档 URL 则返回 None。
    """
    # 去掉 URL 中的查询参数和 hash
    clean_url = url.split("?")[0].split("#")[0].rstrip("/")
    match = FEISHU_URL_PATTERN.search(clean_url)
    if not match:
        return None
    doc_type = match.group(2)   # docx / docs / wiki
    token = match.group(3)
    return {"doc_type": doc_type, "token": token}


def is_feishu_url(url: str) -> bool:
    """校验是否为有效的飞书文档 URL"""
    return parse_feishu_url(url) is not None


async def get_feishu_doc_content(doc_url: str) -> str:
    """
    通过 langchain-mcp-adapters 连接 @larksuiteoapi/lark-mcp MCP 服务器，
    将所有 MCP 工具转为 LangChain Tools，然后调用对应工具获取飞书文档内容。

    凭证通过 CLI 参数传入（-a APP_ID -s APP_SECRET），无需手动授权，
    app_access_token 由 MCP Server 自动获取和刷新。

    :param doc_url: 飞书文档链接
    :return: 文档的 Markdown/纯文本内容
    :raises ValueError: URL 格式不正确
    :raises RuntimeError: MCP 调用失败
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient

    url_info = parse_feishu_url(doc_url)
    if not url_info:
        raise ValueError(f"不是有效的飞书文档链接: {doc_url}")

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        raise RuntimeError("未配置 FEISHU_APP_ID 或 FEISHU_APP_SECRET，请检查环境变量")

    doc_type = url_info["doc_type"]
    token = url_info["token"]

    logger.info(f"开始获取飞书文档: type={doc_type}, token={token}")

    # 启动 @larksuiteoapi/lark-mcp stdio 子进程，凭证通过 CLI 参数传入
    # 注意：langchain-mcp-adapters >= 0.1.0 不支持 async with，直接调用 get_tools()
    client = MultiServerMCPClient({
        "lark": {
            "command": "npx",
            "args": [
                "-y",
                "@larksuiteoapi/lark-mcp",
                "mcp",
                "-a", FEISHU_APP_ID,
                "-s", FEISHU_APP_SECRET,
                "--oauth",
                "--token-mode", "user_access_token",
            ],
            "transport": "stdio",
        }
    })
    # 获取所有 MCP 工具并转为 LangChain Tools
    tools = await client.get_tools()
    tool_names = [t.name for t in tools]
    logger.info(f"MCP 可用工具: {tool_names}")

    content = await _call_doc_tool(tools, doc_type, token, doc_url)

    if not content:
        raise RuntimeError("获取到的文档内容为空，请确认文档已分享给应用Bot")

    return content


async def _call_doc_tool(tools: list, doc_type: str, token: str, doc_url: str) -> str:
    """
    根据文档类型从工具列表中找到最合适的工具并调用。
    精确匹配 @larksuiteoapi/lark-mcp 实际工具名，再做模糊兜底。

    Wiki 文档需要两步：
      1) wiki_v2_space_getNode 获取节点信息（含 obj_token / obj_type）
      2) docx_v1_document_rawContent 用 obj_token 获取实际文档内容
    """
    import json as _json
    tool_map = {t.name: t for t in tools}

    # ---- 获取文档原始内容的通用工具 ----
    doc_tool = (
        tool_map.get("docx_v1_document_rawContent")
        or _fuzzy_find(tool_map, "rawContent")
        or _fuzzy_find(tool_map, "document")
    )

    # Wiki 类型：先取节点元信息，再用 obj_token 获取文档正文
    if doc_type == "wiki":
        wiki_tool = (
            tool_map.get("wiki_v2_space_getNode")
            or _fuzzy_find(tool_map, "wiki")
        )
        if wiki_tool:
            logger.info(f"调用 Wiki 工具: {wiki_tool.name}, token={token}")
            node_result = await wiki_tool.ainvoke({
                "params": {"token": token, "obj_type": "wiki"}
            })
            logger.info(f"Wiki getNode 返回: {str(node_result)[:500]}")

            # 从节点信息中提取 obj_token（即底层文档 ID）
            obj_token = _extract_obj_token(node_result, token)
            logger.info(f"Wiki obj_token={obj_token}")

            # 用 obj_token 获取文档正文
            if doc_tool and obj_token:
                logger.info(f"调用文档工具获取 Wiki 正文: {doc_tool.name}, document_id={obj_token}")
                result = await doc_tool.ainvoke({
                    "path": {"document_id": obj_token}
                })
                text = _extract_text(result)
                if text and text.strip():
                    return text

            # 兜底：直接从 node_result 提取文本（部分 MCP 版本直接返回内容）
            text = _extract_text(node_result)
            if text and text.strip():
                return text

    # docx / docs 类型：直接用 document_id 获取
    if doc_tool:
        logger.info(f"调用文档工具: {doc_tool.name}, document_id={token}")
        result = await doc_tool.ainvoke({
            "path": {"document_id": token}
        })
        return _extract_text(result)

    raise RuntimeError(
        f"MCP Server 没有可用的文档读取工具。可用工具: {list(tool_map.keys())}"
    )


def _extract_obj_token(node_result, fallback_token: str) -> str:
    """
    从 wiki_v2_space_getNode 的返回中提取底层文档 obj_token。
    返回格式一般为：{"data": {"node": {"obj_token": "xxx", "obj_type": "docx", ...}}}
    """
    if isinstance(node_result, str):
        try:
            import json as _json
            node_result = _json.loads(node_result)
        except (ValueError, TypeError):
            return fallback_token

    if isinstance(node_result, dict):
        # 直接在顶层查找
        if "obj_token" in node_result:
            return node_result["obj_token"]
        # data.node.obj_token
        data = node_result.get("data", node_result)
        if isinstance(data, dict):
            node = data.get("node", data)
            if isinstance(node, dict) and "obj_token" in node:
                return node["obj_token"]

    return fallback_token


def _fuzzy_find(tool_map: dict, keyword: str):
    """在工具名中模糊匹配关键字"""
    keyword = keyword.lower()
    for name, tool in tool_map.items():
        if keyword in name.lower():
            return tool
    return None


def _extract_text(result) -> str:
    """从工具调用结果中提取文本内容"""
    import json as _json

    if isinstance(result, str):
        # 尝试解析 JSON 字符串
        try:
            parsed = _json.loads(result)
            return _extract_text(parsed)
        except (ValueError, TypeError):
            return result

    # lark-mcp 返回格式: [{'type': 'text', 'text': '{"content":"..."}'}]
    if isinstance(result, list):
        parts = []
        for item in result:
            if isinstance(item, dict) and item.get("type") == "text":
                text_val = item.get("text", "")
                # text 字段本身可能是 JSON {"content": "..."}
                try:
                    inner = _json.loads(text_val)
                    parts.append(_extract_text(inner))
                except (ValueError, TypeError):
                    parts.append(text_val)
            else:
                parts.append(_extract_text(item))
        return "\n".join(p for p in parts if p.strip())

    if isinstance(result, dict):
        # 优先取 content 字段
        for key in ("content", "text", "markdown", "body", "data"):
            val = result.get(key)
            if val and isinstance(val, str):
                return val
            if val and isinstance(val, (dict, list)):
                extracted = _extract_text(val)
                if extracted.strip():
                    return extracted
        return _json.dumps(result, ensure_ascii=False)

    return str(result)
