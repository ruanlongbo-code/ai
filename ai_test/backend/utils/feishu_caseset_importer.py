"""
飞书测试用例集导入器
===================
将 JSON 格式测试用例导入飞书项目用例管理（用例集脑图）。

流程：
 1. 通过 xmind/import 上传占位 xmind 创建用例集 → 拿到 work_item_id
 2. 将 JSON 按严格模式层级转为飞书 mind_content（带 nodeType）
 3. 调 m-api (x-token) mind/save 写入完整脑图
 4. 返回用例集链接

认证：全程使用 m-api (x-token)
"""
import asyncio
import io
import json
import time
import logging
import zipfile
from typing import Any, Optional
from urllib.parse import quote

import httpx

from config.settings import FEISHU_PROJECT_KEY

logger = logging.getLogger(__name__)

CASE_SET_TYPE_KEY = "65f2fed3067c907f0466f016"
INTERNAL_API_BASE = "https://project.feishu.cn/m-api/v1/builtin_app/test_management"
OPEN_API_BASE = "https://project.feishu.cn/open_api"
DEFAULT_DIR_ID = "7577242005904542944"

NODE_TYPE_CASE_TITLE = 11
NODE_TYPE_PRECONDITION = 12
NODE_TYPE_STEP = 13
NODE_TYPE_EXPECTED = 14

PRIORITY_MAP = {"P0": 1, "P1": 2, "P2": 3, "P3": 4}

_id_counter = 0


def _next_id() -> str:
    global _id_counter
    _id_counter += 1
    return f"n_{int(time.time() * 1000)}_{_id_counter}"


def _mk_text(s: str) -> list[dict]:
    return [{"type": 0, "text": s}]


def json_to_mind_content(test_cases: list[dict]) -> list[dict]:
    """
    将测试用例列表转为飞书脑图 mind_content 树结构。
    module 字段支持 "/" 分隔多层级。
    """

    class _TreeNode:
        __slots__ = ("node", "children_map")

        def __init__(self, node: dict):
            self.node = node
            self.children_map: dict[str, "_TreeNode"] = {}

    root_map: dict[str, _TreeNode] = {}

    def get_or_create_path(parts: list[str]) -> list[dict]:
        current_map = root_map
        parent_children: Optional[list[dict]] = None

        for part in parts:
            if part not in current_map:
                node = {"id": _next_id(), "text": _mk_text(part), "children": []}
                tree_node = _TreeNode(node)
                current_map[part] = tree_node
                if parent_children is not None:
                    parent_children.append(node)

            tree_node = current_map[part]
            parent_children = tree_node.node["children"]
            current_map = tree_node.children_map

        return parent_children

    for tc in test_cases:
        module = tc.get("module", "") or tc.get("scenario", "") or "未分类"
        parts = [p.strip() for p in module.split("/") if p.strip()]
        if not parts:
            parts = ["未分类"]

        steps = tc.get("test_steps", [])
        expected = tc.get("expected_results", [])

        step_nodes = []
        for i, step_text in enumerate(steps):
            exp_text = expected[i] if i < len(expected) else ""
            step_nodes.append({
                "id": _next_id(),
                "text": _mk_text(step_text),
                "nodeType": NODE_TYPE_STEP,
                "children": [{
                    "id": _next_id(),
                    "text": _mk_text(exp_text),
                    "nodeType": NODE_TYPE_EXPECTED,
                }],
            })

        precondition = tc.get("precondition", "")
        precond_node = {
            "id": _next_id(),
            "text": _mk_text(precondition),
            "nodeType": NODE_TYPE_PRECONDITION,
            "children": step_nodes,
        }

        case_title = tc.get("case_title", "") or tc.get("case_name", "")
        case_node: dict[str, Any] = {
            "id": _next_id(),
            "text": _mk_text(case_title),
            "nodeType": NODE_TYPE_CASE_TITLE,
            "children": [precond_node],
        }

        priority_str = tc.get("priority", "")
        if priority_str and priority_str in PRIORITY_MAP:
            case_node["priority"] = PRIORITY_MAP[priority_str]

        leaf_children = get_or_create_path(parts)
        leaf_children.append(case_node)

    return [tn.node for tn in root_map.values()]


COMMON_HEADERS = {
    "Referer": "https://project.feishu.cn/",
}


async def _internal_get(endpoint: str, params: dict[str, str], token: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{INTERNAL_API_BASE}/{endpoint}",
            params=params,
            headers={"x-token": token, **COMMON_HEADERS},
        )
        return resp.json()


async def _internal_post(endpoint: str, body: dict, token: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{INTERNAL_API_BASE}/{endpoint}",
            json=body,
            headers={
                "Content-Type": "application/json",
                "x-token": token,
                **COMMON_HEADERS,
            },
        )
        return resp.json()


async def list_case_dirs(token: str, project_key: str = "") -> list[dict]:
    """获取飞书用例管理的目录树，返回扁平列表 [{id, name, parent_id}, ...]"""
    pk = project_key or FEISHU_PROJECT_KEY

    url = f"https://project.feishu.cn/m-api/v1/work_item/dir"
    params = {
        "project_key": pk,
        "work_item_type_key": CASE_SET_TYPE_KEY,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            url,
            params=params,
            headers={"x-token": token, **COMMON_HEADERS},
        )
        data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(
            f"获取目录列表失败: code={data.get('code')} msg={data.get('msg', json.dumps(data))}"
        )

    def _flatten(nodes: list[dict], parent_id: str = "") -> list[dict]:
        result = []
        for node in nodes:
            result.append({
                "id": str(node.get("id", "")),
                "name": node.get("name", ""),
                "parent_id": parent_id,
            })
            children = node.get("children") or node.get("sub_dirs") or []
            if children:
                result.extend(_flatten(children, str(node.get("id", ""))))
        return result

    raw_dirs = data.get("data", [])
    if isinstance(raw_dirs, dict):
        raw_dirs = raw_dirs.get("dirs") or raw_dirs.get("data") or []
    return _flatten(raw_dirs)


async def resolve_dir_id_by_name(dir_name: str, token: str, project_key: str = "") -> str:
    """根据目录名称查找 dir_id，支持用 '/' 分隔的路径匹配"""
    dirs = await list_case_dirs(token, project_key)
    if not dirs:
        raise ValueError("获取飞书目录列表为空")

    parts = [p.strip() for p in dir_name.split("/") if p.strip()]

    if len(parts) == 1:
        for d in dirs:
            if d["name"] == parts[0]:
                return d["id"]
        raise ValueError(f"未找到名为 '{dir_name}' 的目录")

    current_parent = ""
    found_id = ""
    for part in parts:
        matched = [d for d in dirs if d["name"] == part and d["parent_id"] == current_parent]
        if not matched:
            matched = [d for d in dirs if d["name"] == part]
        if not matched:
            raise ValueError(f"未找到目录路径 '{dir_name}' 中的 '{part}'")
        found_id = matched[0]["id"]
        current_parent = found_id

    return found_id


def _pack_placeholder_xmind(title: str) -> bytes:
    """打包一个最小占位 .xmind 文件（zip 格式），用于 xmind/import 创建用例集"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        content = [{"id": "sheet1", "title": "Sheet 1", "rootTopic": {"id": "root", "title": title}}]
        zf.writestr("content.json", json.dumps(content))
        zf.writestr("metadata.json", json.dumps({"creator": {"name": "ai-test", "version": "1.0"}}))
        zf.writestr("manifest.json", json.dumps({"file-entries": {"content.json": {}, "metadata.json": {}}}))
    return buf.getvalue()


async def create_case_set_via_xmind_import(
    title: str, token: str, project_key: str = "", dir_id: str = ""
) -> int:
    """通过 xmind/import 上传占位文件创建用例集（与 TS 脚本一致），返回 work_item_id"""
    pk = project_key or FEISHU_PROJECT_KEY
    xmind_bytes = _pack_placeholder_xmind(title)
    file_name = title.replace(" ", "_") + ".xmind"

    url = f"{INTERNAL_API_BASE}/xmind/import"
    params = {
        "project_key": pk,
        "work_item_type_key": CASE_SET_TYPE_KEY,
        "mind_format": "standard",
        "target": "online_mind",
        "dir_id": dir_id or DEFAULT_DIR_ID,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            url,
            params=params,
            files={"file": (file_name, xmind_bytes, "application/octet-stream")},
            headers={"x-token": token, **COMMON_HEADERS},
        )
        data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(
            f"xmind/import 创建用例集失败: code={data.get('code')} msg={data.get('msg', json.dumps(data))}"
        )

    work_item_id = data["data"]["case_set_work_item_id"]
    logger.info(f"xmind/import 创建用例集成功: work_item_id={work_item_id}")
    return int(work_item_id)


async def create_case_set_via_open_api(
    title: str, project_key: str, plugin_id: str, plugin_secret: str, user_key: str
) -> int:
    """通过 Open API (plugin_token) 创建用例集工作项（备用方案）"""
    from utils.feishu_plugin_auth import get_plugin_token

    pk = project_key or FEISHU_PROJECT_KEY
    token = await get_plugin_token(plugin_id, plugin_secret)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{OPEN_API_BASE}/{pk}/work_item/create",
            json={
                "work_item_type_key": "63fc6356a3568b3fd3800e88",
                "field_value_pairs": [
                    {"field_key": "name", "field_value": title},
                ],
            },
            headers={
                "Content-Type": "application/json",
                "X-PLUGIN-TOKEN": token,
                "X-USER-KEY": user_key,
            },
        )
        data = resp.json()

    if data.get("err_code") != 0:
        raise RuntimeError(
            f"Open API 创建用例集失败: err_code={data.get('err_code')} msg={data.get('err_msg', json.dumps(data))}"
        )

    work_item_id = data["data"]
    logger.info(f"Open API 创建用例集成功: work_item_id={work_item_id}")
    return int(work_item_id)


async def save_mind_content(work_item_id: int, mind_content: list[dict], token: str, project_key: str = "") -> None:
    """通过 m-api (x-token) 查询 mind_version 后写入完整脑图"""
    pk = project_key or FEISHU_PROJECT_KEY
    params = {
        "project_key": pk,
        "work_item_id": str(work_item_id),
        "work_item_type_key": CASE_SET_TYPE_KEY,
        "mind_type": "1",
    }

    max_retries = 8
    query_res = None
    for attempt in range(max_retries):
        query_res = await _internal_get("mind/query", params, token)
        if query_res.get("code") == 0:
            break
        logger.warning(f"mind/query 第{attempt+1}次失败: code={query_res.get('code')} msg={query_res.get('msg', '')}")
        if attempt < max_retries - 1:
            await asyncio.sleep(2 * (attempt + 1))

    if query_res.get("code") != 0:
        raise RuntimeError(f"查询脑图失败: code={query_res.get('code')} msg={query_res.get('msg', '')}")

    mind_version = query_res["data"]["mind_updated_at"]

    content_str = json.dumps(mind_content)
    logger.info(f"mind/save payload: work_item_id={work_item_id}, mind_content长度={len(content_str)}字符")

    save_res = await _internal_post("mind/save", {
        "project_key": pk,
        "work_item_id": work_item_id,
        "work_item_type_key": CASE_SET_TYPE_KEY,
        "mind_content": content_str,
        "mind_version": mind_version,
        "mind_type": 1,
    }, token)

    if save_res.get("code") != 0:
        raise RuntimeError(f"保存脑图失败: code={save_res.get('code')} msg={save_res.get('msg', '')}")


URL_PROJECT_KEY = "research__development"


def build_case_set_url(work_item_id: int) -> str:
    parent_url = quote(
        f"/{URL_PROJECT_KEY}/meegoPlg/MII_642BBF6AC6C74001_test_management_use_case_set"
    )
    return f"https://project.feishu.cn/{URL_PROJECT_KEY}/test_cases_set/detail/{work_item_id}?parentUrl={parent_url}&openScene=6"


async def import_cases_to_feishu(
    test_cases: list[dict],
    title: str,
    token: str = "",
    dir_id: str = "",
    project_key: str = "",
    plugin_id: str = "",
    plugin_secret: str = "",
    user_key: str = "",
) -> dict:
    """
    一键导入入口：JSON 用例列表 → 飞书用例集。

    认证：全程使用 m-api (x-token)
    - 创建用例集：xmind/import 上传占位文件
    - 写入脑图：mind/save

    x-token 优先使用传入的 token，没传则使用服务端缓存的。

    返回 {"work_item_id": int, "case_set_url": str, "case_count": int}
    """
    from utils.feishu_plugin_auth import get_cached_x_token, set_cached_x_token

    if not test_cases:
        raise ValueError("用例列表为空")
    if len(test_cases) > 500:
        raise ValueError(f"飞书单次上传最多 500 条用例，当前 {len(test_cases)} 条，请拆分后导入")

    x_token = token or get_cached_x_token()
    if not x_token:
        raise ValueError("缺少飞书 x-token，请先在设置中配置")

    if token:
        set_cached_x_token(token)

    pk = project_key or FEISHU_PROJECT_KEY
    if not pk:
        raise ValueError("缺少 FEISHU_PROJECT_KEY 配置")

    logger.info(f"开始导入飞书用例集: title={title}, cases={len(test_cases)}")

    work_item_id = await create_case_set_via_xmind_import(
        title, x_token, pk, dir_id or DEFAULT_DIR_ID
    )

    logger.info(f"用例集已创建: work_item_id={work_item_id}")

    mind_content = json_to_mind_content(test_cases)
    await save_mind_content(work_item_id, mind_content, x_token, pk)
    logger.info("脑图写入成功")

    case_set_url = build_case_set_url(work_item_id)

    return {
        "work_item_id": work_item_id,
        "case_set_url": case_set_url,
        "case_count": len(test_cases),
    }
