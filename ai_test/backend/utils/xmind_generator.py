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
    # 如果已经是字符串格式如 P0, P1 等
    if isinstance(priority, str) and priority.upper().startswith('P'):
        return priority.upper()
    return f'P{priority}'


def _format_numbered_list(text: str) -> str:
    """
    将文本格式化为编号列表的多行格式（每条编号独占一行）。

    支持多种输入格式：
    1. 已有换行分隔：  "步骤1\n步骤2\n步骤3"
    2. 空格分隔编号：  "1.步骤1 2.步骤2 3.步骤3"
    3. 混合格式：      "1.步骤1 2.步骤2\n3.步骤3"

    输出统一为：
        1.步骤1
        2.步骤2
        3.步骤3
    """
    if not text or not text.strip():
        return ''

    text = text.strip()

    # 先尝试按换行符分割
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # 如果只有1行，尝试按编号模式拆分（如 "1.xxx 2.xxx 3.xxx"）
    if len(lines) <= 1:
        # 匹配 "数字." "数字)" "数字、" 前面有空格的位置进行拆分
        # 例如: "1.打开首页 2.点击登录 3.输入密码" → ["1.打开首页", "2.点击登录", "3.输入密码"]
        split_lines = re.split(r'\s+(?=\d+[\.\)、])', text)
        if len(split_lines) > 1:
            lines = [line.strip() for line in split_lines if line.strip()]
        else:
            # 尝试无空格的紧邻编号拆分（如 "1.打开首页2.点击登录3.输入密码"）
            # 在中文字符后面紧跟数字编号的位置拆分
            split_lines2 = re.split(r'(?<=[\u4e00-\u9fff\w\)）])(?=\d+[\.\)、])', text)
            if len(split_lines2) > 1:
                lines = [line.strip() for line in split_lines2 if line.strip()]

    # 对每行也做一次空格编号拆分（处理混合情况，如每行内还有"1.xx 2.xx"）
    expanded_lines = []
    for line in lines:
        sub_split = re.split(r'\s+(?=\d+[\.\)、])', line)
        if len(sub_split) > 1:
            expanded_lines.extend([s.strip() for s in sub_split if s.strip()])
        else:
            expanded_lines.append(line)

    lines = expanded_lines

    # 去除已有的编号前缀，统一重新编号
    numbered = []
    for i, line in enumerate(lines, 1):
        # 移除已有的编号格式（如 "1. ", "1) ", "1、"）
        clean_line = re.sub(r'^\d+[\.\)、]\s*', '', line)
        if clean_line:
            numbered.append(f'{i}.{clean_line}')

    if not numbered:
        return text

    return '\n'.join(numbered)


def _format_steps_from_json(test_steps) -> str:
    """
    从 JSON 格式的测试步骤中提取为文本。

    处理两种常见数据格式：
    1. 标准格式：[{"step":1,"action":"步骤1"}, {"step":2,"action":"步骤2"}]
    2. 合并格式：[{"step":1,"action":"1.步骤1 2.步骤2 3.步骤3"}] (所有步骤在一个action里)
    """
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
        # 合并所有action文本，后续由 _format_numbered_list 统一拆分和编号
        return '\n'.join(steps_text)

    return str(test_steps)


def generate_xmind_content(
        requirement_title: str,
        test_cases: List[Dict],
        template_settings: Optional[Dict] = None
) -> list:
    """
    生成 XMind content.json 的数据结构

    Args:
        requirement_title: 需求标题（根节点名称）
        test_cases: 测试用例列表，每条用例包含:
            - case_name: 用例名称
            - priority: 优先级 (1-4)
            - case_no/case_id: 用例编号
            - preconditions: 前置条件
            - test_steps: 测试步骤 (str 或 JSON)
            - expected_result: 预期结果
        template_settings: 模板设置项

    Returns:
        XMind content.json 数据结构（列表）
    """
    settings = template_settings or {}
    show_priority = settings.get('show_priority', True)
    show_case_id = settings.get('show_case_id', False)
    show_node_labels = settings.get('show_node_labels', False)  # 是否注明节点属性（如 "前置条件：xxx"）
    root_prefix = settings.get('root_prefix', '验证')
    root_suffix = settings.get('root_suffix', '功能')

    # 构建根节点标题
    root_title = f"{root_prefix}{requirement_title}{root_suffix}"

    # 构建每个用例的子主题
    case_topics = []
    for case in test_cases:
        # ===== 构建用例标题 =====
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

        # ===== 构建子节点（前置条件、测试步骤、预期结果）=====
        # 节点属性标签映射
        node_definitions = [
            ("preconditions", "前置条件"),
            ("test_steps", "测试步骤"),
            ("expected_result", "预期结果"),
        ]

        # 构建各节点，按链式嵌套：前置条件 → 测试步骤 → 预期结果
        nodes = []
        for field_key, label in node_definitions:
            raw_value = case.get(field_key, '')

            # 测试步骤可能是 JSON 格式，需要特殊处理
            if field_key == "test_steps":
                text = _format_steps_from_json(raw_value)
            else:
                text = str(raw_value) if raw_value else ''

            if not text or not text.strip():
                continue

            content = _format_numbered_list(text)

            # 是否在内容前注明节点属性标签
            if show_node_labels:
                content = f"{label}：{content}"

            nodes.append({
                "id": _generate_id(),
                "title": content,
                "class": "topic"
            })

        # 链式嵌套：后一个节点作为前一个节点的子节点
        # 前置条件 → 测试步骤 → 预期结果
        for i in range(len(nodes) - 1, 0, -1):
            nodes[i - 1]["children"] = {"attached": [nodes[i]]}

        children = [nodes[0]] if nodes else []

        # 构建用例主题节点
        case_topic = {
            "id": _generate_id(),
            "title": case_title,
            "class": "topic"
        }

        if children:
            case_topic["children"] = {"attached": children}

        case_topics.append(case_topic)

    # 构建完整的 XMind content.json 结构
    content = [{
        "id": _generate_id(),
        "class": "sheet",
        "title": "测试用例",
        "rootTopic": {
            "id": _generate_id(),
            "class": "topic",
            "title": root_title,
            "children": {
                "attached": case_topics
            } if case_topics else {}
        }
    }]

    return content


def generate_xmind_file(
        requirement_title: str,
        test_cases: List[Dict],
        template_settings: Optional[Dict] = None
) -> bytes:
    """
    生成 XMind 文件（.xmind）并返回二进制内容

    Args:
        requirement_title: 需求标题
        test_cases: 测试用例列表
        template_settings: 模板设置项

    Returns:
        .xmind 文件的二进制内容（可直接写入文件或返回给前端下载）
    """
    content = generate_xmind_content(requirement_title, test_cases, template_settings)

    # 创建 .xmind 文件（ZIP 格式）
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # content.json - 主内容
        zf.writestr('content.json', json.dumps(content, ensure_ascii=False, indent=2))

        # metadata.json - 元数据
        metadata = {
            "creator": {
                "name": "AiProtect",
                "version": "1.0.0"
            }
        }
        zf.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))

        # manifest.json - 清单
        manifest = {
            "file-entries": {
                "content.json": {},
                "metadata.json": {}
            }
        }
        zf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))

    logger.info(f"XMind 文件生成成功: {requirement_title}, 共 {len(test_cases)} 条用例")
    return buffer.getvalue()


# 默认模板设置
DEFAULT_TEMPLATE_SETTINGS = {
    "show_priority": True,          # 用例标题前显示优先级
    "show_case_id": False,          # 用例标题不显示编号
    "show_node_labels": False,      # 是否注明节点属性（默认不注明）
    "root_prefix": "验证",           # 根节点前缀
    "root_suffix": "功能",           # 根节点后缀
}
