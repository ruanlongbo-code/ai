"""
数据分析模块 API
包含：缺陷分析（AI驱动）、用户行为分析（AI驱动）
"""
import json
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse

from service.user.models import User
from service.project.models import Project
from utils.permissions import verify_admin_or_project_member
from config.settings import llm

logger = logging.getLogger(__name__)

router = APIRouter(tags=["数据分析"])


# ==================== 缺陷分析 ====================

@router.get("/{project_id}/defect-analysis/stats", summary="获取缺陷统计数据")
async def get_defect_stats(
        project_id: int,
        iteration_id: Optional[int] = Query(None, description="迭代ID"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取项目的缺陷统计数据（用于图表展示）"""
    project, current_user = project_user

    try:
        from service.schedule.models import Defect, ScheduleItem, TestIteration
        from tortoise.functions import Count

        # 构建查询
        base_query = Defect.all()

        # 如果指定迭代，先找到迭代下的排期条目
        if iteration_id:
            schedule_item_ids = await ScheduleItem.filter(
                iteration_id=iteration_id
            ).values_list('id', flat=True)
            base_query = base_query.filter(schedule_item_id__in=schedule_item_ids)
        else:
            # 获取项目下所有迭代的排期条目
            iterations = await TestIteration.filter(project_id=project_id).values_list('id', flat=True)
            if iterations:
                schedule_item_ids = await ScheduleItem.filter(
                    iteration_id__in=iterations
                ).values_list('id', flat=True)
                base_query = base_query.filter(schedule_item_id__in=schedule_item_ids)
            else:
                return {
                    "total": 0,
                    "by_status": {},
                    "by_severity": {},
                    "by_type": {},
                    "recent_trend": [],
                    "top_requirements": []
                }

        # 总数
        total = await base_query.count()

        # 按状态分组
        all_defects = await base_query.all()

        status_map = {}
        severity_map = {}
        type_map = {}
        requirement_map = {}

        status_labels = {
            'open': '待处理', 'fixing': '修复中', 'fixed': '已修复',
            'verified': '已验证', 'closed': '已关闭', 'rejected': '已拒绝'
        }
        severity_labels = {'P0': 'P0-阻塞', 'P1': 'P1-严重', 'P2': 'P2-一般', 'P3': 'P3-轻微'}
        type_labels = {
            'functional': '功能缺陷', 'ui': '界面显示',
            'performance': '性能问题', 'compatibility': '兼容性', 'other': '其他'
        }

        for d in all_defects:
            st = d.defect_status
            status_map[status_labels.get(st, st)] = status_map.get(status_labels.get(st, st), 0) + 1

            sv = d.severity
            severity_map[severity_labels.get(sv, sv)] = severity_map.get(severity_labels.get(sv, sv), 0) + 1

            tp = d.defect_type
            type_map[type_labels.get(tp, tp)] = type_map.get(type_labels.get(tp, tp), 0) + 1

            sid = d.schedule_item_id
            if sid not in requirement_map:
                requirement_map[sid] = 0
            requirement_map[sid] += 1

        # 近7天趋势
        now = datetime.now()
        trend = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            day_str = day.strftime('%m-%d')
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            count = sum(1 for d in all_defects if d.created_at and day_start <= d.created_at.replace(tzinfo=None) <= day_end)
            trend.append({"date": day_str, "count": count})

        # Top 缺陷需求
        top_requirements = []
        if requirement_map:
            sorted_reqs = sorted(requirement_map.items(), key=lambda x: x[1], reverse=True)[:5]
            for sid, count in sorted_reqs:
                item = await ScheduleItem.get_or_none(id=sid)
                top_requirements.append({
                    "requirement_id": sid,
                    "requirement_title": item.requirement_title if item else f"需求#{sid}",
                    "defect_count": count
                })

        # 获取迭代列表
        iterations_list = await TestIteration.filter(project_id=project_id).order_by('-created_at').all()
        iterations_data = [{"id": it.id, "name": it.name, "status": it.status} for it in iterations_list]

        return {
            "total": total,
            "by_status": status_map,
            "by_severity": severity_map,
            "by_type": type_map,
            "recent_trend": trend,
            "top_requirements": top_requirements,
            "iterations": iterations_data
        }

    except Exception as e:
        logger.error(f"获取缺陷统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缺陷统计失败: {str(e)}")


@router.post("/{project_id}/defect-analysis/ai-analyze", summary="AI智能缺陷分析")
async def ai_defect_analysis(
        project_id: int,
        iteration_id: Optional[int] = Query(None, description="迭代ID"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """使用AI对项目缺陷数据进行深度分析，SSE流式返回"""
    project, current_user = project_user

    try:
        from service.schedule.models import Defect, ScheduleItem, TestIteration

        # 收集缺陷数据
        base_query = Defect.all()
        if iteration_id:
            schedule_item_ids = await ScheduleItem.filter(
                iteration_id=iteration_id
            ).values_list('id', flat=True)
            base_query = base_query.filter(schedule_item_id__in=schedule_item_ids)
        else:
            iterations = await TestIteration.filter(project_id=project_id).values_list('id', flat=True)
            if iterations:
                schedule_item_ids = await ScheduleItem.filter(
                    iteration_id__in=iterations
                ).values_list('id', flat=True)
                base_query = base_query.filter(schedule_item_id__in=schedule_item_ids)

        all_defects = await base_query.all()

        if not all_defects:
            async def empty_response():
                yield f"data: {json.dumps({'type': 'result', 'content': '当前项目暂无缺陷数据，无法进行分析。请先创建缺陷记录后再试。'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return StreamingResponse(empty_response(), media_type="text/event-stream")

        # 构建缺陷摘要
        defect_summary = []
        for d in all_defects[:50]:  # 限制50条防止 prompt 过长
            item = await ScheduleItem.get_or_none(id=d.schedule_item_id)
            defect_summary.append({
                "标题": d.title,
                "类型": d.defect_type,
                "严重程度": d.severity,
                "状态": d.defect_status,
                "关联需求": item.requirement_title if item else "未知",
                "创建时间": d.created_at.strftime('%Y-%m-%d') if d.created_at else "",
            })

        status_dist = {}
        severity_dist = {}
        type_dist = {}
        for d in all_defects:
            status_dist[d.defect_status] = status_dist.get(d.defect_status, 0) + 1
            severity_dist[d.severity] = severity_dist.get(d.severity, 0) + 1
            type_dist[d.defect_type] = type_dist.get(d.defect_type, 0) + 1

        prompt = f"""你是一位资深的软件测试质量分析师。请根据以下项目的缺陷数据进行全面深度分析。

## 项目信息
- 项目名称: {project.name}
- 缺陷总数: {len(all_defects)}

## 缺陷状态分布
{json.dumps(status_dist, ensure_ascii=False, indent=2)}

## 严重程度分布
{json.dumps(severity_dist, ensure_ascii=False, indent=2)}

## 缺陷类型分布
{json.dumps(type_dist, ensure_ascii=False, indent=2)}

## 缺陷详细列表（前50条）
{json.dumps(defect_summary, ensure_ascii=False, indent=2)}

## 请进行以下分析

### 1. 质量概况
- 整体质量评估（优/良/中/差）
- 关键质量指标

### 2. 缺陷趋势分析
- 缺陷分布特征
- 高频缺陷类型和模块

### 3. 根因分析
- 主要缺陷产生原因推测
- 缺陷集中在哪些功能模块

### 4. 风险预警
- 当前未解决的高优先级缺陷
- 潜在的质量风险点

### 5. 改进建议
- 针对开发团队的建议
- 针对测试团队的建议
- 流程优化建议

请用清晰的 Markdown 格式输出分析报告。"""

        async def generate():
            try:
                async for chunk in llm.astream(prompt):
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"AI缺陷分析失败: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI缺陷分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI缺陷分析失败: {str(e)}")


# ==================== 用户行为分析 ====================

@router.get("/{project_id}/behavior-analysis/stats", summary="获取用户行为统计数据")
async def get_behavior_stats(
        project_id: int,
        days: int = Query(30, description="统计天数"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取项目的用户行为统计数据"""
    project, current_user = project_user

    try:
        from service.schedule.models import TestIteration, ScheduleItem, DailyReport
        from service.functional_test.models import RequirementDoc, FunctionalCase
        from service.api_test.models import ApiTestCase
        from service.ui_test.models import UiTestExecution

        now = datetime.now()
        start_date = now - timedelta(days=days)

        # 用户活跃度统计（基于各种操作）
        # 需求创建活动
        from service.project.models import ProjectModule
        modules = await ProjectModule.filter(project_id=project_id).values_list('id', flat=True)
        req_count = await RequirementDoc.filter(
            module_id__in=modules if modules else [-1],
            created_at__gte=start_date
        ).count()

        # 功能用例活动
        case_count = await FunctionalCase.filter(
            requirement__module_id__in=modules if modules else [-1],
            created_at__gte=start_date
        ).count()

        # API测试活动
        api_case_count = await ApiTestCase.filter(
            project_id=project_id,
            created_at__gte=start_date
        ).count()

        # UI测试执行活动
        ui_exec_count = await UiTestExecution.filter(
            case__project_id=project_id,
            created_at__gte=start_date
        ).count()

        # 日报活动
        iterations = await TestIteration.filter(project_id=project_id).values_list('id', flat=True)
        schedule_items = []
        if iterations:
            schedule_items = await ScheduleItem.filter(
                iteration_id__in=iterations
            ).values_list('id', flat=True)

        daily_report_count = await DailyReport.filter(
            schedule_item_id__in=schedule_items if schedule_items else [-1],
            created_at__gte=start_date
        ).count()

        # 缺陷提交活动
        from service.schedule.models import Defect
        defect_count = 0
        if schedule_items:
            defect_count = await Defect.filter(
                schedule_item_id__in=schedule_items,
                created_at__gte=start_date
            ).count()

        # 按天统计活动趋势
        activity_trend = []
        for i in range(min(days, 14) - 1, -1, -1):
            day = now - timedelta(days=i)
            day_str = day.strftime('%m-%d')
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

            day_reqs = await RequirementDoc.filter(
                module_id__in=modules if modules else [-1],
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()

            day_cases = await FunctionalCase.filter(
                requirement__module_id__in=modules if modules else [-1],
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()

            day_api = await ApiTestCase.filter(
                project_id=project_id,
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()

            activity_trend.append({
                "date": day_str,
                "requirements": day_reqs,
                "cases": day_cases,
                "api_cases": day_api,
                "total": day_reqs + day_cases + day_api
            })

        # 用户贡献排行
        # 按创建者统计需求
        user_contributions = {}
        reqs = await RequirementDoc.filter(
            module_id__in=modules if modules else [-1],
            created_at__gte=start_date
        ).all()
        for r in reqs:
            uid = r.creator_id
            if uid not in user_contributions:
                user_contributions[uid] = {"requirements": 0, "cases": 0, "defects": 0}
            user_contributions[uid]["requirements"] += 1

        cases = await FunctionalCase.filter(
            requirement__module_id__in=modules if modules else [-1],
            created_at__gte=start_date
        ).all()
        for c in cases:
            uid = c.creator_id
            if uid not in user_contributions:
                user_contributions[uid] = {"requirements": 0, "cases": 0, "defects": 0}
            user_contributions[uid]["cases"] += 1

        if schedule_items:
            defects = await Defect.filter(
                schedule_item_id__in=schedule_items,
                created_at__gte=start_date
            ).all()
            for d in defects:
                uid = d.reporter_id
                if uid not in user_contributions:
                    user_contributions[uid] = {"requirements": 0, "cases": 0, "defects": 0}
                user_contributions[uid]["defects"] += 1

        # 获取用户名
        user_ranking = []
        for uid, contrib in user_contributions.items():
            user = await User.get_or_none(id=uid)
            user_ranking.append({
                "user_id": uid,
                "username": user.real_name or user.username if user else f"用户#{uid}",
                "requirements": contrib["requirements"],
                "cases": contrib["cases"],
                "defects": contrib["defects"],
                "total": contrib["requirements"] + contrib["cases"] + contrib["defects"]
            })
        user_ranking.sort(key=lambda x: x["total"], reverse=True)

        # 功能模块使用热力图
        module_heat = {}
        for m_id in modules:
            m = await ProjectModule.get_or_none(id=m_id)
            m_reqs = await RequirementDoc.filter(module_id=m_id, created_at__gte=start_date).count()
            if m_reqs > 0:
                module_heat[m.name if m else f"模块#{m_id}"] = m_reqs

        return {
            "overview": {
                "requirements_created": req_count,
                "cases_created": case_count,
                "api_cases_created": api_case_count,
                "ui_executions": ui_exec_count,
                "daily_reports": daily_report_count,
                "defects_submitted": defect_count,
                "total_activities": req_count + case_count + api_case_count + ui_exec_count + daily_report_count + defect_count
            },
            "activity_trend": activity_trend,
            "user_ranking": user_ranking[:10],
            "module_heat": module_heat,
            "period_days": days
        }

    except Exception as e:
        logger.error(f"获取用户行为统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户行为统计失败: {str(e)}")


@router.post("/{project_id}/behavior-analysis/ai-analyze", summary="AI智能行为分析")
async def ai_behavior_analysis(
        project_id: int,
        days: int = Query(30, description="统计天数"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """使用AI对项目的用户行为数据进行深度分析，SSE流式返回"""
    project, current_user = project_user

    try:
        # 先获取统计数据
        stats = await get_behavior_stats(project_id, days, (project, current_user))

        prompt = f"""你是一位资深的软件工程效能分析师。请根据以下项目的团队行为数据进行全面分析。

## 项目信息
- 项目名称: {project.name}
- 统计周期: 最近 {days} 天

## 活动总览
{json.dumps(stats['overview'], ensure_ascii=False, indent=2)}

## 活动趋势（按天）
{json.dumps(stats['activity_trend'], ensure_ascii=False, indent=2)}

## 团队成员贡献排行
{json.dumps(stats['user_ranking'], ensure_ascii=False, indent=2)}

## 模块活跃度
{json.dumps(stats['module_heat'], ensure_ascii=False, indent=2)}

## 请进行以下分析

### 1. 团队效能概况
- 整体活跃度评估
- 日均工作量分析
- 工作节奏分析（是否存在集中突击/长期空闲）

### 2. 团队协作分析
- 成员工作量分布是否均衡
- 是否存在单点依赖
- 团队协作效率评估

### 3. 测试覆盖分析
- 需求与用例的转化率
- 各模块的测试深度
- 自动化测试使用情况

### 4. 效率瓶颈
- 哪些环节效率不足
- 时间安排是否合理
- 资源利用率

### 5. 优化建议
- 团队分工优化建议
- 测试流程优化建议
- 工具使用建议
- 质量保障建议

请用清晰的 Markdown 格式输出分析报告。"""

        async def generate():
            try:
                async for chunk in llm.astream(prompt):
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"AI行为分析失败: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI行为分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI行为分析失败: {str(e)}")
