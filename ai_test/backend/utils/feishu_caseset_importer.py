"""
飞书测试用例集导入器
===================
将 JSON 格式测试用例导入飞书项目用例管理（用例集脑图）。

流程：
 1. 通过 Open API (plugin_token) 创建用例集工作项
 2. 将 JSON 按严格模式层级转为飞书 mind_content（带 nodeType）
 3. 调 m-api (x-token) mind/save 写入完整脑图
 4. 返回用例集链接

混合认证：Open API 创建工作项（自动）+ m-api 写脑图（需 x-token）
"""
import asyncio
import json
import time
import logging
from typing import Any, Optional
from urllib.parse import quote

import httpx

from config.settings import FEISHU_PROJECT_KEY

logger = logging.getLogger(__name__)

CASE_SET_TYPE_KEY = "63fc6356a3568b3fd3800e88"
CASE_SET_MIND_TYPE_KEY = "65f2fed3067c907f0466f016"
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
    "Referer": "https://projectplg.feishupkg.com/",
    "origin": "https://projectplg.feishupkg.com",
    "x-lark-gw": "1",
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


async def create_case_set_via_open_api(
    title: str, project_key: str, plugin_id: str, plugin_secret: str, user_key: str
) -> int:
    """通过 Open API (plugin_token) 创建用例集工作项，无需 x-token"""
    from utils.feishu_plugin_auth import get_plugin_token

    pk = project_key or FEISHU_PROJECT_KEY
    token = await get_plugin_token(plugin_id, plugin_secret)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{OPEN_API_BASE}/{pk}/work_item/create",
            json={
                "work_item_type_key": CASE_SET_TYPE_KEY,
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


def _count_case_nodes(nodes: list[dict]) -> int:
    """递归统计脑图树中 nodeType=11（用例标题）的节点数"""
    count = 0
    for node in nodes:
        if node.get("nodeType") == NODE_TYPE_CASE_TITLE:
            count += 1
        count += _count_case_nodes(node.get("children", []))
    return count


def _split_mind_content(mind_content: list[dict], batch_size: int = 20) -> list[list[dict]]:
    """
    将脑图分批：每批最多 batch_size 条用例。
    按顶层分类节点拆分，保证同一分类的用例不被割裂。
    如果单个分类超过 batch_size，该分类独占一批。
    """
    if _count_case_nodes(mind_content) <= batch_size:
        return [mind_content]

    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    current_count = 0

    for top_node in mind_content:
        node_cases = _count_case_nodes([top_node])
        if current_count + node_cases > batch_size and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_count = 0
        current_batch.append(top_node)
        current_count += node_cases

    if current_batch:
        batches.append(current_batch)

    return batches


async def _query_mind_version(params: dict, token: str) -> int:
    """查询脑图当前版本号，带重试"""
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

    return query_res["data"]["mind_updated_at"]


async def save_mind_content(work_item_id: int, mind_content: list[dict], token: str, project_key: str = "") -> None:
    """
    通过 m-api (x-token) 写入脑图。
    当用例数量多时自动分批写入（累积式），避免飞书接口 500 错误。
    """
    pk = project_key or FEISHU_PROJECT_KEY
    params = {
        "project_key": pk,
        "work_item_id": str(work_item_id),
        "work_item_type_key": CASE_SET_MIND_TYPE_KEY,
        "mind_type": "1",
    }

    batches = _split_mind_content(mind_content, batch_size=20)
    total_cases = _count_case_nodes(mind_content)
    content_size = len(json.dumps(mind_content, ensure_ascii=False))
    logger.info(f"脑图数据: {total_cases}条用例, {content_size}字符, 拆分为{len(batches)}批写入")

    accumulated: list[dict] = []

    for batch_idx, batch in enumerate(batches):
        accumulated.extend(batch)
        batch_cases = _count_case_nodes(batch)

        mind_version = await _query_mind_version(params, token)

        payload = {
            "project_key": pk,
            "work_item_id": work_item_id,
            "work_item_type_key": CASE_SET_MIND_TYPE_KEY,
            "mind_content": json.dumps(accumulated),
            "mind_version": mind_version,
            "mind_type": 1,
        }
        payload_size = len(json.dumps(payload, ensure_ascii=False))
        logger.info(f"写入第{batch_idx+1}/{len(batches)}批: {batch_cases}条用例, 累计{_count_case_nodes(accumulated)}条, payload={payload_size}字符")

        save_res = await _internal_post("mind/save", payload, token)

        if save_res.get("code") != 0:
            logger.error(f"第{batch_idx+1}批保存失败: code={save_res.get('code')} msg={save_res.get('msg', '')} payload_size={payload_size}")
            raise RuntimeError(
                f"保存脑图失败(第{batch_idx+1}/{len(batches)}批): code={save_res.get('code')} msg={save_res.get('msg', '')}"
            )

        if batch_idx < len(batches) - 1:
            await asyncio.sleep(1)


def build_case_set_url(work_item_id: int, project_key: str = "") -> str:
    pk = project_key or FEISHU_PROJECT_KEY
    parent_url = quote(
        f"/{pk}/meegoPlg/MII_642BBF6AC6C74001_test_management_use_case_set"
    )
    return f"https://project.feishu.cn/{pk}/test_cases_set/detail/{work_item_id}?parentUrl={parent_url}&openScene=6"


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

    混合认证：
    - 创建用例集：优先用 Open API (plugin_token)，不需要 x-token
    - 写入脑图：用 m-api (x-token)

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

    if plugin_id and plugin_secret and user_key:
        work_item_id = await create_case_set_via_open_api(title, pk, plugin_id, plugin_secret, user_key)
    else:
        raise ValueError("缺少飞书插件凭证配置 (FEISHU_PROJECT_PLUGIN_ID / PLUGIN_SECRET / USER_KEY)")

    logger.info(f"用例集已创建: work_item_id={work_item_id}")

    mind_content = json_to_mind_content(test_cases)
    await save_mind_content(work_item_id, mind_content, x_token, pk)
    logger.info("脑图写入成功")

    case_set_url = build_case_set_url(work_item_id, pk)

    return {
        "work_item_id": work_item_id,
        "case_set_url": case_set_url,
        "case_count": len(test_cases),
    }
