"""
知识增强检索工具
在用例生成前，检索 RAG 知识库和评审记录，构建增强上下文
使 Workflow 能基于更完整的信息生成更高质量的测试用例
"""
import asyncio
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def search_rag_knowledge(query: str) -> str:
    """
    从 RAG 知识库检索与需求相关的知识
    包括：上传的需求文档、技术文档、历史用例集等
    :param query: 检索关键词（通常是需求标题或描述）
    :return: 检索到的知识文本
    """
    try:
        from rag.rag_api import RAGClient
        rag_client = RAGClient()
        # RAGClient.query() 是同步方法(requests库)，放到线程池执行避免阻塞事件循环
        result = await asyncio.to_thread(rag_client.query, query)
        response_text = result.get("response", "")
        if response_text and len(response_text.strip()) > 10:
            return response_text
        return ""
    except Exception as e:
        logger.warning(f"RAG知识库检索失败（不影响用例生成）: {e}")
        return ""


async def get_review_knowledge(project_id: int, requirement_title: str = "") -> str:
    """
    从数据库获取项目已完成分析的评审记录
    包括：需求评审、技术评审、用例评审的 AI 分析结果
    :param project_id: 项目ID
    :param requirement_title: 需求标题（用于匹配相关评审）
    :return: 汇总的评审知识文本
    """
    try:
        from service.knowledge.models import ReviewRecord

        # 获取该项目所有已完成分析的评审记录
        reviews = await ReviewRecord.filter(
            project_id=project_id,
            status="completed"
        ).order_by("-created_at").all()

        if not reviews:
            return ""

        review_type_names = {
            "requirement": "需求评审",
            "technical": "技术评审",
            "testcase": "用例评审",
        }

        sections = []
        for review in reviews:
            type_name = review_type_names.get(review.review_type, "评审")
            section = f"### {type_name}：{review.title}\n"

            # 添加关键决策
            if review.key_decisions:
                try:
                    decisions = json.loads(review.key_decisions)
                    if decisions:
                        section += "**关键决策：**\n"
                        for d in decisions:
                            section += f"- {d}\n"
                except (json.JSONDecodeError, TypeError):
                    pass

            # 添加待办事项
            if review.action_items:
                try:
                    actions = json.loads(review.action_items)
                    if actions:
                        section += "**待办事项：**\n"
                        for a in actions:
                            section += f"- {a}\n"
                except (json.JSONDecodeError, TypeError):
                    pass

            # 添加 AI 分析汇总（截取关键部分，避免过长）
            if review.extracted_text:
                text = review.extracted_text
                # 限制长度，避免 prompt 过长
                if len(text) > 2000:
                    text = text[:2000] + "...(已截断)"
                section += f"**AI分析摘要：**\n{text}\n"

            sections.append(section)

        return "\n\n".join(sections)

    except Exception as e:
        logger.warning(f"获取评审知识失败（不影响用例生成）: {e}")
        return ""


async def get_case_set_knowledge(project_id: int) -> str:
    """
    从知识库用例集获取历史用例信息
    可作为参考，避免生成重复用例
    :param project_id: 项目ID
    :return: 历史用例知识文本
    """
    try:
        from service.knowledge.models import KnowledgeCaseSet, KnowledgeCaseItem

        case_sets = await KnowledgeCaseSet.filter(
            project_id=project_id
        ).order_by("-created_at").limit(3).all()  # 最多取最近3个用例集

        if not case_sets:
            return ""

        sections = []
        for cs in case_sets:
            # 获取该用例集的顶层用例（不递归，避免数据量过大）
            items = await KnowledgeCaseItem.filter(
                case_set_id=cs.id,
                node_type="case"
            ).limit(20).all()

            if items:
                section = f"### 历史用例集：{cs.name}（共{cs.total_cases}条）\n"
                for item in items:
                    section += f"- {item.title}"
                    if item.priority:
                        section += f" [{item.priority}]"
                    section += "\n"
                sections.append(section)

        return "\n".join(sections)

    except Exception as e:
        logger.warning(f"获取历史用例集失败（不影响用例生成）: {e}")
        return ""


async def build_enhanced_requirement(
    requirement_title: str,
    requirement_description: str,
    requirement_priority: str,
    requirement_status: str,
    project_id: int,
    enable_rag: bool = True,
    enable_review: bool = True,
    enable_case_set: bool = True,
) -> dict:
    """
    构建知识增强的需求文档
    将数据库需求 + RAG 知识 + 评审知识 + 历史用例 合并为一份完整的输入文档

    :return: {
        "enhanced_content": "增强后的完整文档",
        "rag_knowledge": "RAG检索到的内容",
        "review_knowledge": "评审知识",
        "case_set_knowledge": "历史用例",
        "sources": ["rag", "requirement_review", "technical_review", ...]
    }
    """
    sources = ["database"]

    # 1. 基础需求文档（来自数据库）
    base_content = f"""## 原始需求文档

需求标题：{requirement_title}
需求描述：{requirement_description}
需求优先级：{requirement_priority}
需求状态：{requirement_status}
"""

    # 2. RAG 知识库检索
    rag_knowledge = ""
    if enable_rag:
        search_query = f"{requirement_title} {requirement_description[:100] if requirement_description else ''}"
        rag_knowledge = await search_rag_knowledge(search_query)
        if rag_knowledge:
            sources.append("rag_knowledge")

    # 3. 评审知识
    review_knowledge = ""
    if enable_review:
        review_knowledge = await get_review_knowledge(project_id, requirement_title)
        if review_knowledge:
            sources.append("review_knowledge")

    # 4. 历史用例集
    case_set_knowledge = ""
    if enable_case_set:
        case_set_knowledge = await get_case_set_knowledge(project_id)
        if case_set_knowledge:
            sources.append("case_set_knowledge")

    # 5. 拼接增强文档
    enhanced_content = base_content

    if rag_knowledge:
        enhanced_content += f"""

## RAG知识库补充信息（来自需求文档/技术文档）

以下内容是从知识库中检索到的与该需求相关的补充信息，请在生成测试用例时参考：

{rag_knowledge}
"""

    if review_knowledge:
        enhanced_content += f"""

## 评审会议知识（来自需求评审/技术评审/用例评审）

以下内容来自评审会议的AI分析，包含了评审中发现的关键决策、遗漏场景和补充说明，
这些信息在原始需求文档中可能没有体现，请务必在测试用例中覆盖这些场景：

{review_knowledge}
"""

    if case_set_knowledge:
        enhanced_content += f"""

## 历史用例参考

以下是已有的历史用例，可作为参考以避免遗漏和重复：

{case_set_knowledge}
"""

    return {
        "enhanced_content": enhanced_content,
        "rag_knowledge": rag_knowledge,
        "review_knowledge": review_knowledge,
        "case_set_knowledge": case_set_knowledge,
        "sources": sources,
    }
