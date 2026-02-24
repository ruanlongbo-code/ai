"""
飞书项目客户端
=============
通过 MCP (Model Context Protocol) 协议与飞书项目交互。
MCP Server: https://project.feishu.cn/mcp_server/v1

同时保留飞书开放平台的 tenant_access_token 用于 Webhook/机器人消息功能。
"""
import time
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import httpx

from config.settings import (
    FEISHU_APP_ID, FEISHU_APP_SECRET,
    FEISHU_PROJECT_KEY, FEISHU_MCP_KEY,
)

logger = logging.getLogger(__name__)


# ==================== 飞书项目 MCP Client ====================

FEISHU_MCP_BASE = "https://project.feishu.cn/mcp_server/v1"


class FeishuMCPClient:
    """
    轻量级 MCP (Model Context Protocol) 客户端。
    支持 Streamable HTTP 和 SSE 两种传输方式，自动检测。

    用法:
        client = FeishuMCPClient(user_key="xxx", mcp_key="m-xxx")
        tools = await client.list_tools()
        result = await client.call_tool("search_work_item", {"query": "..."})
    """

    def __init__(self, user_key: str, mcp_key: str):
        self.user_key = user_key
        self.mcp_key = mcp_key
        self.url = f"{FEISHU_MCP_BASE}?mcpKey={mcp_key}&userKey={user_key}"
        self._session_id: Optional[str] = None
        self._tools: Optional[List[Dict]] = None
        self._req_id = 0
        self._initialized = False
        self._transport: Optional[str] = None  # "streamable" | "sse"

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    # ---------- Streamable HTTP Transport ----------

    async def _post_jsonrpc(self, method: str, params: Optional[Dict] = None) -> Dict:
        """通过 Streamable HTTP 发送 JSON-RPC 请求"""
        msg = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params is not None:
            msg["params"] = params

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.url, json=msg, headers=headers)

            # 保存 session ID
            sid = resp.headers.get("mcp-session-id") or resp.headers.get("Mcp-Session-Id")
            if sid:
                self._session_id = sid

            # 检查 HTTP 状态码
            if resp.status_code == 405:
                raise _TransportNotSupported("Streamable HTTP not supported")

            resp.raise_for_status()

            ct = resp.headers.get("content-type", "")
            if "text/event-stream" in ct:
                return self._parse_sse_response(resp.text)
            else:
                return resp.json()

    # ---------- SSE Transport ----------

    async def _sse_call(self, method: str, params: Optional[Dict] = None) -> Dict:
        """
        通过 SSE 传输发送 JSON-RPC 请求。
        1. GET SSE → 获取 endpoint 事件
        2. POST JSON-RPC 到 endpoint
        3. 从 SSE 流或 POST 响应中获取结果
        """
        msg = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params is not None:
            msg["params"] = params

        msg_id = msg["id"]

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: 连接 SSE 获取 endpoint
            async with client.stream(
                "GET", self.url,
                headers={"Accept": "text/event-stream"},
                timeout=httpx.Timeout(30.0, connect=10.0),
            ) as sse_resp:
                endpoint_url = None
                event_type = ""

                async for line in sse_resp.aiter_lines():
                    line = line.strip()
                    if not line:
                        event_type = ""
                        continue
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        if event_type == "endpoint":
                            endpoint_url = data_str
                            break

                if not endpoint_url:
                    raise Exception("MCP Server 未返回 endpoint")

                # 处理相对路径
                if endpoint_url.startswith("/"):
                    endpoint_url = f"https://project.feishu.cn{endpoint_url}"

                logger.debug(f"MCP SSE endpoint: {endpoint_url}")

                # Step 2: POST JSON-RPC 到 endpoint
                post_headers = {"Content-Type": "application/json"}
                post_resp = await client.post(endpoint_url, json=msg, headers=post_headers)

                # 检查 POST 响应是否直接包含结果
                if post_resp.status_code == 200:
                    try:
                        post_data = post_resp.json()
                        if "result" in post_data or "error" in post_data:
                            return post_data
                    except Exception:
                        pass

                # Step 3: 从 SSE 流中读取响应
                async for line in sse_resp.aiter_lines():
                    line = line.strip()
                    if not line:
                        event_type = ""
                        continue
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        if event_type == "message":
                            try:
                                data = json.loads(data_str)
                                if data.get("id") == msg_id:
                                    return data
                            except json.JSONDecodeError:
                                continue

        raise Exception("MCP: 未收到响应")

    # ---------- 自动选择传输方式 ----------

    async def request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """发送 MCP 请求，自动检测传输方式"""
        # 如果已知是 SSE 传输
        if self._transport == "sse":
            return await self._sse_call(method, params)

        # 先尝试 Streamable HTTP
        try:
            result = await self._post_jsonrpc(method, params)
            self._transport = "streamable"
            return result
        except _TransportNotSupported:
            logger.info("MCP: Streamable HTTP 不支持，切换到 SSE 传输")
            self._transport = "sse"
            return await self._sse_call(method, params)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 405:
                logger.info("MCP: 收到 405，切换到 SSE 传输")
                self._transport = "sse"
                return await self._sse_call(method, params)
            raise

    # ---------- MCP 协议方法 ----------

    async def initialize(self) -> Dict:
        """初始化 MCP 会话"""
        if self._initialized:
            return {}

        result = await self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "AiProtect-QA",
                "version": "1.0.0"
            }
        })

        # 发送 initialized 通知（无 id）
        try:
            notify_msg = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if self._session_id:
                headers["Mcp-Session-Id"] = self._session_id
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.url, json=notify_msg, headers=headers)
        except Exception:
            pass  # 通知失败不影响

        self._initialized = True
        logger.info(f"MCP 会话初始化成功 (transport={self._transport})")
        return result

    async def list_tools(self) -> List[Dict]:
        """获取可用工具列表"""
        if self._tools is not None:
            return self._tools

        await self.initialize()
        result = await self.request("tools/list")

        tools = result.get("result", {}).get("tools", [])
        self._tools = tools

        tool_names = [t.get("name", "") for t in tools]
        logger.info(f"MCP 可用工具: {tool_names}")
        # 打印每个工具的参数定义，便于调试
        for t in tools:
            schema = t.get("inputSchema", {})
            logger.info(f"MCP 工具 [{t.get('name')}] 参数: {json.dumps(schema, ensure_ascii=False)[:500]}")
        return self._tools

    async def call_tool(self, name: str, arguments: Dict) -> Any:
        """调用 MCP 工具"""
        await self.list_tools()  # 确保已初始化

        result = await self.request("tools/call", {
            "name": name,
            "arguments": arguments,
        })

        # 提取工具结果
        tool_result = result.get("result", result)

        # MCP 工具结果格式: { "content": [{"type": "text", "text": "..."}], "isError": false }
        if isinstance(tool_result, dict):
            if tool_result.get("isError"):
                content = tool_result.get("content", [])
                err_text = ""
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        err_text += c.get("text", "")
                raise Exception(f"MCP 工具调用失败: {err_text}")

            content = tool_result.get("content", [])
            if content:
                # 尝试从 text content 中解析 JSON
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        text = c.get("text", "")
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            return text
                return content

        return tool_result

    def find_tool(self, *candidate_names: str) -> Optional[str]:
        """在已缓存的工具列表中查找匹配的工具名"""
        if not self._tools:
            return None
        available = {t.get("name", "") for t in self._tools}
        for name in candidate_names:
            if name in available:
                return name
        # 模糊匹配
        for name in candidate_names:
            for avail in available:
                if name in avail or avail in name:
                    return avail
        return None

    # ---------- 辅助方法 ----------

    @staticmethod
    def _parse_sse_response(text: str) -> Dict:
        """从 SSE 文本中解析 JSON-RPC 响应"""
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                data_str = line[5:].strip()
                try:
                    data = json.loads(data_str)
                    if "result" in data or "error" in data:
                        return data
                except json.JSONDecodeError:
                    continue
        # 如果没解析出来，尝试整体解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": {"message": f"无法解析 MCP 响应: {text[:200]}"}}


class _TransportNotSupported(Exception):
    pass


# ==================== MCP 客户端管理 ====================

_mcp_clients: Dict[str, FeishuMCPClient] = {}


def _get_mcp_client(user_key: str) -> FeishuMCPClient:
    """获取或创建 MCP 客户端（按 user_key 缓存）"""
    if not FEISHU_MCP_KEY:
        raise Exception("未配置飞书项目 MCP Key (FEISHU_MCP_KEY)")
    if not user_key:
        raise Exception("未提供飞书 User Key，请在个人设置中绑定")

    key = user_key.strip()
    if key not in _mcp_clients:
        _mcp_clients[key] = FeishuMCPClient(user_key=key, mcp_key=FEISHU_MCP_KEY)
    return _mcp_clients[key]


# ==================== 验证连接 ====================

async def verify_mcp_connection(user_key: str = "") -> Dict:
    """验证飞书项目 MCP 连接是否有效"""
    if not FEISHU_MCP_KEY:
        return {
            "success": False,
            "message": "未配置飞书项目 MCP Key",
            "mcp_key": "",
        }

    if not user_key:
        return {
            "success": False,
            "message": "未绑定飞书 User Key，请在个人设置中绑定",
            "mcp_key": FEISHU_MCP_KEY[:10] + "...",
        }

    try:
        client = FeishuMCPClient(user_key=user_key, mcp_key=FEISHU_MCP_KEY)
        tools = await client.list_tools()
        tool_names = [t.get("name", "") for t in tools]
        return {
            "success": True,
            "message": f"MCP 连接成功，可用工具: {len(tools)} 个",
            "mcp_key": FEISHU_MCP_KEY[:10] + "...",
            "transport": client._transport,
            "tools": tool_names,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"MCP 连接失败: {str(e)}",
            "mcp_key": FEISHU_MCP_KEY[:10] + "...",
        }


async def verify_user_key(user_key: str) -> Dict:
    """
    验证飞书项目 User Key 是否有效。
    通过尝试初始化 MCP 会话并获取工具列表来验证。
    然后用 search_by_mql 搜索当前用户负责的需求来获取用户信息。
    """
    if not user_key or not user_key.strip():
        return {"valid": False, "message": "User Key 不能为空"}

    if not FEISHU_MCP_KEY:
        return {"valid": False, "message": "未配置飞书项目 MCP Key"}

    try:
        client = FeishuMCPClient(user_key=user_key.strip(), mcp_key=FEISHU_MCP_KEY)
        tools = await client.list_tools()
        tool_names = [t.get("name", "") for t in tools]

        user_info = {
            "valid": True,
            "message": "User Key 验证通过（MCP 连接成功）",
            "project_key": FEISHU_PROJECT_KEY,
            "available_tools": tool_names,
            "accessible_stories": 0,
        }

        # 尝试多种工具获取用户信息和需求数据
        # 方案1: 用 get_workitem_info 获取需求类型信息
        info_tool = client.find_tool("get_workitem_info")
        if info_tool:
            try:
                info_result = await client.call_tool(info_tool, {
                    "work_item_type": "story",
                    "project_key": FEISHU_PROJECT_KEY,
                })
                logger.info(f"MCP get_workitem_info 结果: {str(info_result)[:800]}")
                _parse_mcp_result_for_user_info(info_result, user_info)
            except Exception as e:
                logger.warning(f"MCP get_workitem_info 失败: {e}")

        # 方案2: 如果方案1没获取到，尝试 search_by_mql
        if not user_info.get("feishu_name"):
            search_tool = client.find_tool("search_by_mql")
            if search_tool:
                try:
                    search_result = await client.call_tool(search_tool, {
                        "project_key": FEISHU_PROJECT_KEY,
                        "moql": "SELECT * FROM story WHERE 负责人 = currentUser LIMIT 5",
                    })
                    logger.info(f"MCP search_by_mql 结果: {str(search_result)[:800]}")
                    _parse_mcp_result_for_user_info(search_result, user_info)
                except Exception as e:
                    logger.warning(f"MCP search_by_mql 失败（不影响验证）: {e}")

        logger.info(f"User Key 验证通过 (MCP), tools={tool_names}, name={user_info.get('feishu_name')}")
        return user_info

    except Exception as e:
        err_str = str(e)
        logger.warning(f"User Key 验证失败 (MCP): {err_str}")

        if "user" in err_str.lower() and ("invalid" in err_str.lower() or "key" in err_str.lower()):
            return {"valid": False, "message": "User Key 无效，请检查是否正确"}
        if "401" in err_str or "403" in err_str or "unauthorized" in err_str.lower():
            return {"valid": False, "message": "User Key 无效或无权限"}

        return {"valid": False, "message": f"MCP 连接失败: {err_str}"}


def _parse_mcp_result_for_user_info(result: Any, user_info: Dict):
    """从 MCP 工具返回的结果中提取用户信息和需求数"""
    import re

    if isinstance(result, str):
        # MCP 返回纯文本，尝试提取信息
        text = result

        # 提取需求数量
        count_patterns = [
            r'(\d+)\s*(?:个|条|项).*?(?:需求|story|工作项)',
            r'(?:共|总计|找到|共计)\s*(\d+)',
            r'(?:需求|story|工作项).*?(\d+)\s*(?:个|条|项)',
        ]
        for pattern in count_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                user_info["accessible_stories"] = int(m.group(1))
                break

        # 提取用户名
        name_patterns = [
            r'负责人[：:]\s*(.+?)(?:\s|$|，|,|\n)',
            r'(?:创建人|用户|账号|owner)[：:]\s*(.+?)(?:\s|$|，|,|\n)',
        ]
        for pattern in name_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                if name and len(name) < 30:  # 合理的名字长度
                    user_info["feishu_name"] = name
                    break

    elif isinstance(result, dict):
        total = result.get("total", 0)
        if not total:
            total = result.get("pagination", {}).get("total", 0)
        items = result.get("data", result.get("items", result.get("work_items", [])))
        if not total and isinstance(items, list):
            total = len(items)
        if total:
            user_info["accessible_stories"] = total

        # 从工作项中提取用户信息
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                for fk in ["owner", "assignee", "created_by", "role_owners", "负责人"]:
                    fv = item.get(fk)
                    if isinstance(fv, str) and fv and len(fv) < 30:
                        user_info["feishu_name"] = fv
                        return
                    elif isinstance(fv, dict) and fv.get("name"):
                        user_info["feishu_name"] = fv["name"]
                        user_info["feishu_email"] = fv.get("email", "")
                        return
                    elif isinstance(fv, list):
                        for m in fv:
                            if isinstance(m, str) and m and len(m) < 30:
                                user_info["feishu_name"] = m
                                return
                            elif isinstance(m, dict) and m.get("name"):
                                user_info["feishu_name"] = m["name"]
                                user_info["feishu_email"] = m.get("email", "")
                                return

    elif isinstance(result, list):
        user_info["accessible_stories"] = len(result)
        for item in result:
            if isinstance(item, dict):
                for fk in ["owner", "assignee", "created_by", "负责人"]:
                    fv = item.get(fk)
                    if isinstance(fv, str) and fv and len(fv) < 30:
                        user_info["feishu_name"] = fv
                        return
                    elif isinstance(fv, dict) and fv.get("name"):
                        user_info["feishu_name"] = fv["name"]
                        user_info["feishu_email"] = fv.get("email", "")
                        return


# ==================== 飞书开放平台 tenant_access_token ====================
# 用于 Webhook / 机器人消息等功能（这部分保持不变）

FEISHU_OPEN_BASE = "https://open.feishu.cn/open-apis"

_tenant_token_cache: Dict[str, Any] = {
    "token": None,
    "expire_time": 0,
}


async def get_tenant_access_token() -> str:
    """获取飞书开放平台 tenant_access_token"""
    now = time.time()
    if _tenant_token_cache["token"] and _tenant_token_cache["expire_time"] > now + 60:
        return _tenant_token_cache["token"]

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        raise Exception("未配置飞书开放平台 App ID / App Secret")

    url = f"{FEISHU_OPEN_BASE}/auth/v3/tenant_access_token/internal"
    payload = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if data.get("code") != 0:
        raise Exception(f"获取 tenant_access_token 失败: {data.get('msg')}")

    _tenant_token_cache["token"] = data["tenant_access_token"]
    _tenant_token_cache["expire_time"] = now + data.get("expire", 7200)

    logger.info("飞书开放平台 tenant_access_token 获取成功")
    return _tenant_token_cache["token"]


async def verify_connection() -> Dict:
    """验证飞书开放平台应用连接（用于 Webhook）"""
    try:
        token = await get_tenant_access_token()
        return {
            "success": True,
            "message": "飞书开放平台应用连接成功",
            "app_id": FEISHU_APP_ID,
            "token_preview": token[:10] + "..." if token else None,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"飞书开放平台连接失败: {str(e)}",
            "app_id": FEISHU_APP_ID,
        }


# ==================== 飞书项目 MCP 工作项操作 ====================


async def create_issue_in_project(
    name: str,
    description: str = "",
    priority: Optional[str] = None,
    project_key: Optional[str] = None,
    user_key: Optional[str] = None,
) -> Dict:
    """
    在飞书项目中创建缺陷(issue)，通过 MCP 工具调用。
    """
    client = _get_mcp_client(user_key)
    tools = await client.list_tools()

    # 查找创建工具（飞书项目 MCP 的工具名为 create_workitem）
    create_tool = client.find_tool(
        "create_workitem", "create_work_item",
        "create_issue", "create_bug", "create",
    )

    if not create_tool:
        tool_names = [t.get("name", "") for t in tools]
        raise Exception(f"MCP Server 不提供创建工作项的工具。可用工具: {tool_names}")

    # 构建参数
    arguments = {
        "name": name,
        "work_item_type_key": "issue",
    }
    if project_key:
        arguments["project_key"] = project_key
    if description:
        arguments["description"] = description
    if priority:
        arguments["priority"] = priority

    try:
        result = await client.call_tool(create_tool, arguments)
        logger.info(f"MCP 创建缺陷成功: {name}")
        return {"data": result} if not isinstance(result, dict) or "data" not in result else result
    except Exception as e:
        logger.error(f"MCP 创建缺陷失败: {e}")
        return {"error": {"message": str(e)}}


async def filter_work_items(
    work_item_type_key: str,
    search_group: Optional[Dict] = None,
    page_size: int = 50,
    page_num: int = 1,
    project_key: Optional[str] = None,
    user_key: Optional[str] = None,
) -> Dict:
    """通过 MCP 搜索/过滤工作项"""
    client = _get_mcp_client(user_key)
    tools = await client.list_tools()

    search_tool = client.find_tool(
        "search_by_mql", "search_work_item", "filter_work_items",
        "list_work_items", "search", "query_work_items",
    )

    if not search_tool:
        tool_names = [t.get("name", "") for t in tools]
        raise Exception(f"MCP Server 不提供搜索工作项的工具。可用工具: {tool_names}")

    arguments = {
        "work_item_type_key": work_item_type_key,
    }
    if project_key:
        arguments["project_key"] = project_key
    if search_group:
        # 如果工具是 search_by_mql，转换 search_group 为 MOQL 查询
        if search_tool == "search_by_mql" and isinstance(search_group, dict):
            moql_parts = []
            for param in search_group.get("search_params", []):
                moql_parts.append(f'{param.get("param_key")} = "{param.get("value")}"')
            if moql_parts:
                arguments["moql"] = "SELECT * FROM " + work_item_type_key + " WHERE " + " AND ".join(moql_parts)
        else:
            arguments["search_group"] = search_group

    try:
        result = await client.call_tool(search_tool, arguments)
        return result if isinstance(result, dict) else {"data": result}
    except Exception as e:
        logger.error(f"MCP 搜索工作项失败: {e}")
        return {"error": {"message": str(e)}}


async def get_story_related_issues(
    story_id: int,
    project_key: Optional[str] = None,
    user_key: Optional[str] = None,
) -> Dict:
    """
    获取某个需求(story)下关联的缺陷(issue)列表，通过 MCP 工具调用。
    """
    client = _get_mcp_client(user_key)
    tools = await client.list_tools()

    # 查找关联查询工具（飞书项目 MCP 的工具名为 get_workitem_info）
    relation_tool = client.find_tool(
        "get_workitem_info", "get_work_item_relations",
        "get_relations", "query_related_items",
    )

    if relation_tool:
        arguments = {
            "work_item_type_key": "story",
            "work_item_id": story_id,
        }
        if project_key:
            arguments["project_key"] = project_key

        try:
            result = await client.call_tool(relation_tool, arguments)
            return result if isinstance(result, dict) else {"data": result}
        except Exception as e:
            logger.error(f"MCP 获取关联缺陷失败: {e}")
            return {"error": {"message": str(e)}, "data": []}

    # 如果没有关联查询工具，尝试用搜索工具
    search_tool = client.find_tool(
        "search_by_mql", "search_work_item",
        "filter_work_items", "list_work_items",
    )
    if search_tool:
        try:
            result = await client.call_tool(search_tool, {
                "work_item_type_key": "issue",
                "search_group": {
                    "conjunction": "AND",
                    "search_params": [{
                        "param_key": "related_story_id",
                        "value": str(story_id),
                    }]
                },
            })
            return result if isinstance(result, dict) else {"data": result}
        except Exception as e:
            logger.warning(f"MCP 搜索关联缺陷失败: {e}")

    tool_names = [t.get("name", "") for t in tools]
    return {"error": {"message": f"MCP Server 不提供关联查询工具。可用工具: {tool_names}"}, "data": []}


# ==================== URL 工具方法（保持不变）====================

def build_feishu_story_url(story_id: int, project_key: Optional[str] = None) -> str:
    """构建飞书项目需求链接"""
    pk = project_key or FEISHU_PROJECT_KEY
    return f"https://project.feishu.cn/{pk}/story/detail/{story_id}"


def build_feishu_issue_url(issue_id: int, project_key: Optional[str] = None) -> str:
    """构建飞书项目缺陷链接"""
    pk = project_key or FEISHU_PROJECT_KEY
    return f"https://project.feishu.cn/{pk}/issue/detail/{issue_id}"


def parse_feishu_project_url(url: str) -> Optional[Dict]:
    """
    解析飞书项目 URL，提取 project_key、work_item_type、work_item_id

    支持格式:
        https://project.feishu.cn/research__development/story/detail/6645133065
        https://project.feishu.cn/research__development/issue/detail/6796081388
    """
    if not url or "project.feishu.cn" not in url:
        return None

    try:
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        # parts = ['research__development', 'story', 'detail', '6645133065']
        if len(parts) >= 4 and parts[2] == "detail":
            return {
                "project_key": parts[0],
                "work_item_type": parts[1],  # story / issue
                "work_item_id": int(parts[3]),
            }
    except Exception:
        pass

    return None
