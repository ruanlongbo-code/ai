"""
XMind 文件解析器 - 从 .xmind 文件中提取测试用例树形结构
支持 XMind 8+ 格式（.xmind = ZIP 包含 content.json）
"""
import json
import zipfile
import io
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def parse_xmind_file(file_content: bytes) -> List[Dict]:
    """
    解析 XMind 文件，返回树形结构的用例数据。

    Returns:
        [
            {
                "title": "根节点标题",
                "children": [
                    {
                        "title": "子节点/用例名",
                        "priority": "P1",
                        "preconditions": "...",
                        "test_steps": "...",
                        "expected_result": "...",
                        "children": [...]
                    }
                ]
            }
        ]
    """
    try:
        with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zf:
            if 'content.json' in zf.namelist():
                content = json.loads(zf.read('content.json'))
            else:
                raise ValueError("XMind文件中未找到content.json")
    except zipfile.BadZipFile:
        raise ValueError("无效的XMind文件格式")

    result = []
    for sheet in content:
        root_topic = sheet.get('rootTopic', {})
        if root_topic:
            parsed = _parse_topic(root_topic)
            result.append(parsed)

    return result


def _parse_topic(topic: dict) -> dict:
    """递归解析一个 topic 节点"""
    title = topic.get('title', '').strip()
    children_data = topic.get('children', {}).get('attached', [])

    priority = _extract_priority(title)
    clean_title = _clean_title(title)

    node = {
        "title": clean_title,
        "original_title": title,
    }

    if priority:
        node["priority"] = priority

    if children_data:
        parsed_children = [_parse_topic(child) for child in children_data]

        if _looks_like_case_detail(parsed_children):
            detail = _extract_case_detail(parsed_children)
            node.update(detail)
        else:
            node["children"] = parsed_children
    return node


def _extract_priority(title: str) -> Optional[str]:
    """从标题中提取优先级，如 {P0}、{P1}"""
    match = re.search(r'\{(P\d)\}', title, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def _clean_title(title: str) -> str:
    """清理标题中的优先级标记和编号标记"""
    title = re.sub(r'\{P\d\}\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\[[\w-]+\]\s*', '', title)
    return title.strip()


def _looks_like_case_detail(children: List[Dict]) -> bool:
    """
    判断子节点是否为用例详情（前置条件→测试步骤→预期结果）而非子模块。
    如果子节点都没有自己的 children，且数量 <= 3，大概率是链式详情节点。
    """
    if not children or len(children) > 4:
        return False
    leaf_count = sum(1 for c in children if 'children' not in c)
    return leaf_count >= len(children) - 1


def _extract_case_detail(children: List[Dict]) -> dict:
    """从链式详情节点中提取前置条件、测试步骤、预期结果"""
    detail = {}
    texts = []

    def _collect_texts(nodes):
        for n in nodes:
            texts.append(n.get('title', ''))
            if 'children' in n:
                _collect_texts(n['children'])

    _collect_texts(children)

    keywords = {
        'preconditions': ['前置条件', '前提条件', '前置'],
        'test_steps': ['测试步骤', '操作步骤', '步骤'],
        'expected_result': ['预期结果', '期望结果', '预期'],
    }

    for text in texts:
        matched = False
        for field, kws in keywords.items():
            for kw in kws:
                if text.startswith(f'{kw}：') or text.startswith(f'{kw}:'):
                    detail[field] = text.split('：', 1)[-1].split(':', 1)[-1].strip()
                    matched = True
                    break
            if matched:
                break

    if not detail and len(texts) == 3:
        detail['preconditions'] = texts[0]
        detail['test_steps'] = texts[1]
        detail['expected_result'] = texts[2]
    elif not detail and len(texts) == 2:
        detail['test_steps'] = texts[0]
        detail['expected_result'] = texts[1]
    elif not detail and len(texts) == 1:
        detail['test_steps'] = texts[0]

    return detail


def flatten_xmind_to_cases(tree: List[Dict]) -> List[Dict]:
    """
    将 XMind 树形结构展平为用例列表。
    返回 [{ module_path, title, priority, preconditions, test_steps, expected_result }]
    """
    cases = []

    def _walk(node, path=""):
        title = node.get('title', '')
        current_path = f"{path}/{title}" if path else title

        if 'test_steps' in node or 'expected_result' in node:
            cases.append({
                "module_path": path,
                "title": title,
                "priority": node.get('priority'),
                "preconditions": node.get('preconditions', ''),
                "test_steps": node.get('test_steps', ''),
                "expected_result": node.get('expected_result', ''),
            })
        elif 'children' in node:
            for child in node['children']:
                _walk(child, current_path)
        else:
            cases.append({
                "module_path": path,
                "title": title,
                "priority": node.get('priority'),
                "preconditions": '',
                "test_steps": '',
                "expected_result": '',
            })

    for root in tree:
        _walk(root)

    return cases


def xmind_to_text_for_rag(tree: List[Dict]) -> str:
    """将 XMind 结构转换为文本格式，用于导入 RAG 知识库"""
    lines = []

    def _walk(node, depth=0):
        indent = "  " * depth
        title = node.get('title', '')
        priority = node.get('priority', '')

        header = f"{indent}{'#' * min(depth + 1, 4)} {priority + ' ' if priority else ''}{title}"
        lines.append(header)

        if node.get('preconditions'):
            lines.append(f"{indent}前置条件：{node['preconditions']}")
        if node.get('test_steps'):
            lines.append(f"{indent}测试步骤：{node['test_steps']}")
        if node.get('expected_result'):
            lines.append(f"{indent}预期结果：{node['expected_result']}")

        if 'children' in node:
            for child in node['children']:
                _walk(child, depth + 1)

    for root in tree:
        _walk(root)

    return '\n'.join(lines)
