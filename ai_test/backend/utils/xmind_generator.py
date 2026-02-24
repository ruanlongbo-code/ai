"""
XMind 文件生成器 - 将测试用例导出为 XMind 思维导图格式
支持 XMind 8+ 格式（.xmind = ZIP 包含 content.json）

无需额外依赖，使用 Python 标准库 zipfile 直接构建 .xmind 文件。
"""

import json
import uuid
import zipfile
import io
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def _generate_id() -> str:
    """生成唯一节点ID"""
    return str(uuid.uuid4()).replace('-', '')[:24]


def _priority_label(priority) -> str:
    """将优先级数字转为显示标签"""
    priority_map = {1: 'P0', 2: 'P1', 3: 'P2', 4: 'P3'}
    if isinstance(priority, int):
        return priority_map.get(priority, f'P{priority}')
    if isinstance(priority, str) and priority.upper().startswith('P'):
        return priority.upper()
    return f'P{priority}'


def _format_numbered_list(text: str) -> str:
    """将文本格式化为编号列表的多行格式"""
    if not text or not text.strip():
        return ''

    text = text.strip()

    lines = [line.strip() for line in text.split('\n') if line.strip()]

    if len(lines) <= 1:
        split_lines = re.split(r'\s+(?=\d+[\.\)、])', text)
        if len(split_lines) > 1:
            lines = [line.strip() for line in split_lines if line.strip()]
        else:
            split_lines2 = re.split(r'(?<=[\u4e00-\u9fff\w\)）])(?=\d+[\.\)、])', text)
            if len(split_lines2) > 1:
                lines = [line.strip() for line in split_lines2 if line.strip()]

    expanded_lines = []
    for line in lines:
        sub_split = re.split(r'\s+(?=\d+[\.\)、])', line)
        if len(sub_split) > 1:
            expanded_lines.extend([s.strip() for s in sub_split if s.strip()])
        else:
            expanded_lines.append(line)

    lines = expanded_lines

    numbered = []
    for i, line in enumerate(lines, 1):
        clean_line = re.sub(r'^\d+[\.\)、]\s*', '', line)
        if clean_line:
            numbered.append(f'{i}.{clean_line}')

    if not numbered:
        return text

    return '\n'.join(numbered)


def _format_steps_from_json(test_steps) -> str:
    """从 JSON 格式的测试步骤中提取为文本。"""
    if not test_steps:
        return ''

    if isinstance(test_steps, str):
        return test_steps

    if isinstance(test_steps, list):
        steps_text = []
        for step in test_steps:
            if isinstance(step, dict):
                action = step.get('action', step.get('step', ''))
                if action:
                    steps_text.append(str(action))
            else:
                steps_text.append(str(step))
        return '\n'.join(steps_text)

    return str(test_steps)


def _build_case_topic(case: Dict, settings: Dict) -> Dict:
    """构建单个用例的 XMind 主题节点"""
    show_priority = settings.get('show_priority', True)
    show_case_id = settings.get('show_case_id', False)
    show_node_labels = settings.get('show_node_labels', False)

    case_title_parts = []

    if show_priority:
        priority = case.get('priority', 3)
        case_title_parts.append(f'{{{_priority_label(priority)}}}')

    if show_case_id:
        case_id = case.get('case_no', case.get('case_id', ''))
        if case_id:
            case_title_parts.append(f'[{case_id}]')

    case_name = case.get('case_name', '未命名用例')
    case_title_parts.append(case_name)

    case_title = ' '.join(case_title_parts)

    node_definitions = [
        ("preconditions", "前置条件"),
        ("test_steps", "测试步骤"),
        ("expected_result", "预期结果"),
    ]

    nodes = []
    for field_key, label in node_definitions:
        raw_value = case.get(field_key, '')

        if field_key == "test_steps":
            text = _format_steps_from_json(raw_value)
        else:
            text = str(raw_value) if raw_value else ''

        if not text or not text.strip():
            continue

        content = _format_numbered_list(text)

        if show_node_labels:
            content = f"{label}：{content}"

        nodes.append({
            "id": _generate_id(),
            "title": content,
            "class": "topic"
        })

    for i in range(len(nodes) - 1, 0, -1):
        nodes[i - 1]["children"] = {"attached": [nodes[i]]}

    children = [nodes[0]] if nodes else []

    case_topic = {
        "id": _generate_id(),
        "title": case_title,
        "class": "topic"
    }

    if children:
        case_topic["children"] = {"attached": children}

    return case_topic


def generate_xmind_content(
        requirement_title: str,
        test_cases: Optional[List[Dict]] = None,
        template_settings: Optional[Dict] = None,
        scenario_groups: Optional[Dict[str, List[Dict]]] = None
) -> list:
    """
    生成 XMind content.json 的数据结构（支持场景分组）
    
    三级结构: 根节点(需求标题) → 场景节点(带前后缀) → 用例节点
    """
    settings = template_settings or {}
    scenario_prefix = settings.get('scenario_prefix', settings.get('root_prefix', '验证'))
    scenario_suffix = settings.get('scenario_suffix', settings.get('root_suffix', '功能'))

    # 根节点直接使用需求标题
    root_title = requirement_title

    # 如果提供了场景分组，按场景→用例构建三级结构
    if scenario_groups:
        scenario_topics = []
        for scenario_name, cases in scenario_groups.items():
            case_topics = [_build_case_topic(c, settings) for c in cases]
            # 场景名称应用前后缀
            display_name = f"{scenario_prefix}{scenario_name}{scenario_suffix}" if (scenario_prefix or scenario_suffix) else scenario_name
            scenario_topic = {
                "id": _generate_id(),
                "title": f"🎯 {display_name}",
                "class": "topic"
            }
            if case_topics:
                scenario_topic["children"] = {"attached": case_topics}
            scenario_topics.append(scenario_topic)

        attached = scenario_topics
    elif test_cases:
        # 兼容旧的扁平结构
        attached = [_build_case_topic(c, settings) for c in test_cases]
    else:
        attached = []

    content = [{
        "id": _generate_id(),
        "class": "sheet",
        "title": "测试用例",
        "rootTopic": {
            "id": _generate_id(),
            "class": "topic",
            "title": root_title,
            "children": {
                "attached": attached
            } if attached else {}
        }
    }]

    return content


def generate_xmind_file(
        requirement_title: str,
        test_cases: Optional[List[Dict]] = None,
        template_settings: Optional[Dict] = None,
        scenario_groups: Optional[Dict[str, List[Dict]]] = None
) -> bytes:
    """
    生成 XMind 文件（.xmind）并返回二进制内容
    """
    content = generate_xmind_content(requirement_title, test_cases, template_settings, scenario_groups)

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('content.json', json.dumps(content, ensure_ascii=False, indent=2))

        metadata = {
            "creator": {
                "name": "AiProtect",
                "version": "1.0.0"
            }
        }
        zf.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))

        manifest = {
            "file-entries": {
                "content.json": {},
                "metadata.json": {}
            }
        }
        zf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))

    total = sum(len(cases) for cases in scenario_groups.values()) if scenario_groups else (len(test_cases) if test_cases else 0)
    logger.info(f"XMind 文件生成成功: {requirement_title}, 共 {total} 条用例")
    return buffer.getvalue()


# 默认模板设置
DEFAULT_TEMPLATE_SETTINGS = {
    "show_priority": True,
    "show_case_id": False,
    "show_node_labels": False,
    "scenario_prefix": "验证",
    "scenario_suffix": "功能",
}
