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


def _build_step_sub_topics(text: str) -> List[Dict]:
    """将多行步骤/预期结果文本拆分为独立的子节点列表"""
    if not text or not text.strip():
        return []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if len(lines) <= 1:
        split_lines = re.split(r'\s+(?=\d+[\.\)、])', text)
        if len(split_lines) > 1:
            lines = [line.strip() for line in split_lines if line.strip()]
        else:
            split_lines2 = re.split(r'(?<=[\u4e00-\u9fff\w\)）])(?=\d+[\.\)、])', text)
            if len(split_lines2) > 1:
                lines = [line.strip() for line in split_lines2 if line.strip()]
    result = []
    for i, line in enumerate(lines, 1):
        clean_line = re.sub(r'^\d+[\.\)、]\s*', '', line)
        if clean_line:
            result.append({
                "id": _generate_id(),
                "title": f"{i}.{clean_line}",
                "class": "topic"
            })
    if not result and text.strip():
        result.append({
            "id": _generate_id(),
            "title": text.strip(),
            "class": "topic"
        })
    return result


_LEADING_NUMBER_RE = re.compile(
    r'^(?:[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]\s*[\.、)）:：]?\s*|\d+\s*[\.、)）:：]\s*)'
)


def _strip_leading_number(text: str) -> str:
    """循环去掉文本开头的所有编号前缀，处理 ①1. / 1.① 等多重编号叠加"""
    text = text.strip()
    while True:
        new_text = _LEADING_NUMBER_RE.sub('', text)
        if new_text == text:
            break
        text = new_text.strip()
    return text


def _normalize_list(raw) -> List[str]:
    """将 str / list[str] / list[dict] 统一转为 list[str]，并去掉编号前缀"""
    if not raw:
        return []
    if isinstance(raw, str):
        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        cleaned = [_strip_leading_number(l) for l in lines]
        cleaned = [c for c in cleaned if c]
        return cleaned if cleaned else [raw.strip()]
    if isinstance(raw, list):
        result = []
        for item in raw:
            if isinstance(item, dict):
                val = str(item.get('action', item.get('step', item.get('result', ''))))
            else:
                val = str(item)
            val = _strip_leading_number(val)
            if val:
                result.append(val)
        return result
    return [_strip_leading_number(str(raw)) or str(raw)]


def _build_case_topic(case: Dict, settings: Dict) -> Dict:
    """
    构建单个用例的 XMind 主题节点（三层链式结构）。

    XMind 层级：
      根节点(项目/需求)
        └── 场景(scenario)
             └── [P1][TC-0001] 用例标题
                  └── 前置条件：条件A；条件B
                       └── 步骤①：xxx 步骤②：xxx
                            └── 预期结果：1. xxx；2. xxx
    """
    step_labels = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩',
                   '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳']

    show_priority = settings.get('show_priority', True)
    show_case_id = settings.get('show_case_id', False)

    case_title_parts = []

    if show_priority:
        priority = case.get('priority', 3)
        case_title_parts.append(f'[{_priority_label(priority)}]')

    if show_case_id:
        case_id = case.get('case_no', case.get('case_id', ''))
        if case_id:
            case_title_parts.append(f'[{case_id}]')

    case_name = case.get('case_name', case.get('case_title', '未命名用例'))
    case_title_parts.append(case_name)

    case_title = ' '.join(case_title_parts)

    # --- 收集数据 ---
    preconditions_raw = case.get('preconditions', case.get('precondition', ''))
    preconditions_list = _normalize_list(preconditions_raw)

    steps_list = _normalize_list(case.get('test_steps', ''))
    expected_list = _normalize_list(
        case.get('expected_result', case.get('expected_results', ''))
    )

    tags = case.get('tags', [])

    # --- 合并所有步骤为一个节点文本（换行分隔） ---
    steps_text = ""
    if steps_list:
        parts = []
        for i, step_text in enumerate(steps_list):
            label = step_labels[i] if i < len(step_labels) else f'{i+1}'
            parts.append(f"步骤{label}：{step_text}")
        steps_text = "\n".join(parts)

    # --- 合并所有预期结果为一个节点文本（换行分隔） ---
    expected_text = ""
    if expected_list:
        if len(expected_list) == 1:
            expected_text = expected_list[0]
        else:
            parts = []
            for i, e in enumerate(expected_list):
                label = step_labels[i] if i < len(step_labels) else f'{i+1}'
                parts.append(f"{label}{e}")
            expected_text = "\n".join(parts)

    # --- 构建链式层级：用例标题 → 前置条件 → 步骤 → 预期结果 ---
    # 从最内层往外构建

    # 预期结果节点
    expected_node = None
    if expected_text:
        expected_node = {
            "id": _generate_id(),
            "title": f"预期结果：{expected_text}",
            "class": "topic"
        }

    # 步骤节点
    steps_node = None
    if steps_text:
        steps_node = {
            "id": _generate_id(),
            "title": steps_text,
            "class": "topic"
        }
        if expected_node:
            steps_node["children"] = {"attached": [expected_node]}
    elif expected_node:
        steps_node = expected_node

    # 标签作为额外子节点（与步骤同级，挂在前置条件下）
    pre_children = []
    if steps_node:
        pre_children.append(steps_node)
    if tags and isinstance(tags, list):
        pre_children.append({
            "id": _generate_id(),
            "title": f"标签：{', '.join(str(t) for t in tags)}",
            "class": "topic"
        })

    # 前置条件节点
    case_topic = {
        "id": _generate_id(),
        "title": case_title,
        "class": "topic"
    }

    if preconditions_list:
        pre_text = "；".join(preconditions_list)
        pre_node = {
            "id": _generate_id(),
            "title": f"前置条件：{pre_text}",
            "class": "topic"
        }
        if pre_children:
            pre_node["children"] = {"attached": pre_children}
        case_topic["children"] = {"attached": [pre_node]}
    elif pre_children:
        case_topic["children"] = {"attached": pre_children}

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

    # 根节点标题格式化为【xxx】测试用例
    clean_title = re.sub(r'[\s_\-]*测试[点用]例.*$', '', requirement_title).strip()
    clean_title = re.sub(r'[\s_\-]*测试点.*$', '', clean_title).strip()
    clean_title = re.sub(r'[\s_\-]*功能测试.*$', '', clean_title).strip()
    clean_title = clean_title.strip(' -_—')
    root_title = f"【{clean_title}】测试用例"

    if scenario_groups:
        scenario_topics = []
        for scenario_name, cases in scenario_groups.items():
            case_topics = [_build_case_topic(c, settings) for c in cases]
            display_name = f"{scenario_prefix}{scenario_name}{scenario_suffix}" if (scenario_prefix or scenario_suffix) else scenario_name
            scenario_topic = {
                "id": _generate_id(),
                "title": display_name,
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
