"""
测试排期管理模块 API
包含：迭代管理、排期条目、测试日报、管理员Dashboard、飞书推送
"""
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Depends, status, Query
from tortoise.transactions import in_transaction

from service.user.models import User
from service.project.models import Project, ProjectMember, BusinessLineMember
from utils.auth import get_current_user
from utils.permissions import (
    verify_admin_or_project_member,
    verify_admin_or_project_owner,
    verify_admin_or_project_editor,
    verify_schedule_access,
)
from .models import TestIteration, ScheduleItem, DailyReport, ProgressReport, FeishuWebhook
from .schemas import (
    IterationCreateRequest, IterationUpdateRequest, IterationResponse, IterationListResponse,
    ScheduleItemCreateRequest, ScheduleItemUpdateRequest, ScheduleItemResponse, ScheduleItemListResponse,
    DailyReportCreateRequest, DailyReportResponse, DailyReportListResponse,
    DashboardDailyUpdate, DashboardDailyResponse,
    DashboardIterationSummaryResponse, IterationSummaryItem,
    FeishuWebhookCreateRequest, FeishuWebhookUpdateRequest,
    FeishuWebhookResponse, FeishuWebhookListResponse,
    FeishuSendRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["测试排期管理"])


# ==================== 辅助函数 ====================

async def _get_user_name(user_id: int) -> str:
    """获取用户名"""
    user = await User.get_or_none(id=user_id)
    return user.real_name or user.username if user else "未知用户"


def _calc_remaining_days(end_date) -> int:
    """计算剩余天数"""
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    delta = end_date - date.today()
    return max(0, delta.days)


def _calc_risk_level(item: ScheduleItem, iteration: TestIteration) -> tuple:
    """
    自动计算风险等级
    Returns: (risk_level, risk_reason)
    """
    today = date.today()
    remaining = _calc_remaining_days(iteration.end_date)

    # 规则1: 迭代快结束但进度低
    if remaining <= 3 and item.actual_progress < 80:
        return "high", f"迭代剩余{remaining}天，进度仅{item.actual_progress}%"

    # 规则2: 状态仍在开发中但已过排期中点
    total_days = (iteration.end_date - iteration.start_date).days or 1
    elapsed = (today - iteration.start_date).days
    if elapsed > total_days * 0.5 and item.requirement_status in ('pending', 'developing'):
        return "medium", f"迭代已过半，需求仍为{item.requirement_status}状态"

    # 规则3: 测试中但进度偏低
    if item.requirement_status == 'testing' and elapsed > total_days * 0.7:
        expected = int(elapsed / total_days * 100)
        if item.actual_progress < expected * 0.6:
            return "medium", f"预期进度{expected}%，实际{item.actual_progress}%"

    # 规则4: 进度为0且已过排期1/3
    if item.actual_progress == 0 and elapsed > total_days * 0.3:
        return "low", "进度为0%，建议关注"

    return "none", None


async def _build_schedule_item_response(item: ScheduleItem) -> ScheduleItemResponse:
    """构建排期条目响应"""
    assignee_name = await _get_user_name(item.assignee_id)
    return ScheduleItemResponse(
        id=item.id,
        iteration_id=item.iteration_id,
        requirement_title=item.requirement_title,
        requirement_id=item.requirement_id,
        category=item.category,
        assignee_id=item.assignee_id,
        assignee_name=assignee_name,
        requirement_status=item.requirement_status,
        ticket_url=item.ticket_url,
        priority=item.priority,
        planned_test_date=item.planned_test_date,
        estimated_case_days=float(item.estimated_case_days) if item.estimated_case_days else None,
        case_output_date=item.case_output_date,
        case_status=item.case_status,
        estimated_test_days=float(item.estimated_test_days) if item.estimated_test_days else None,
        test_date_range=item.test_date_range,
        integration_test_date=item.integration_test_date,
        remark=item.remark,
        actual_progress=item.actual_progress,
        risk_level=item.risk_level,
        risk_reason=item.risk_reason,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


# ==================== 可分配用户 API ====================

@router.get("/{project_id}/assignable-users", summary="获取可分配用户列表")
async def get_assignable_users(
        project_id: int,
        current_user: User = Depends(get_current_user)
):
    """获取该项目下所有可分配的用户（业务线成员 + 项目成员，去重合并）"""
    from service.project.models import ProjectModule

    # 1. 获取项目成员
    project_members = await ProjectMember.filter(project_id=project_id, status=1).all()
    pm_user_ids = {m.user_id for m in project_members}

    # 2. 获取业务线成员
    module_ids = await ProjectModule.filter(project_id=project_id).values_list('id', flat=True)
    blm_user_ids = set()
    if module_ids:
        blm_list = await BusinessLineMember.filter(module_id__in=module_ids).all()
        blm_user_ids = {b.user_id for b in blm_list}

    # 3. 合并去重
    all_user_ids = pm_user_ids | blm_user_ids
    if not all_user_ids:
        return {"users": []}

    users = await User.filter(id__in=list(all_user_ids), is_active=True).all()
    result = [
        {"id": u.id, "username": u.username, "real_name": u.real_name}
        for u in users
    ]
    return {"users": result}


# ==================== 迭代管理 API ====================

@router.post("/{project_id}/iterations", response_model=IterationResponse, summary="创建迭代")
async def create_iteration(
        project_id: int,
        request: IterationCreateRequest,
        project_user: tuple = Depends(verify_admin_or_project_owner)
):
    """创建新的测试迭代（仅Leader/管理员）"""
    project, current_user = project_user

    if request.end_date <= request.start_date:
        raise HTTPException(status_code=400, detail="结束日期必须晚于开始日期")

    iteration = await TestIteration.create(
        name=request.name,
        project_id=project_id,
        start_date=request.start_date,
        end_date=request.end_date,
        status=request.status,
        created_by_id=current_user.id,
    )

    creator_name = await _get_user_name(current_user.id)
    return IterationResponse(
        id=iteration.id,
        name=iteration.name,
        project_id=project_id,
        start_date=iteration.start_date,
        end_date=iteration.end_date,
        status=iteration.status,
        created_by_id=current_user.id,
        created_by_name=creator_name,
        created_at=iteration.created_at,
        updated_at=iteration.updated_at,
        remaining_days=_calc_remaining_days(iteration.end_date),
    )


@router.get("/{project_id}/iterations", response_model=IterationListResponse, summary="获取迭代列表")
async def get_iterations(
        project_id: int,
        status_filter: Optional[str] = Query(None, alias="status", description="状态过滤"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取项目的迭代列表"""
    project, current_user = project_user

    filters = {"project_id": project_id}
    if status_filter:
        filters["status"] = status_filter

    iterations = await TestIteration.filter(**filters).order_by("-start_date").all()

    result = []
    for it in iterations:
        items = await ScheduleItem.filter(iteration_id=it.id).all()
        total_items = len(items)
        completed_items = len([i for i in items if i.requirement_status == 'completed'])
        overall = int(sum(i.actual_progress for i in items) / total_items) if total_items > 0 else 0

        creator_name = await _get_user_name(it.created_by_id)
        result.append(IterationResponse(
            id=it.id,
            name=it.name,
            project_id=project_id,
            start_date=it.start_date,
            end_date=it.end_date,
            status=it.status,
            created_by_id=it.created_by_id,
            created_by_name=creator_name,
            created_at=it.created_at,
            updated_at=it.updated_at,
            total_items=total_items,
            completed_items=completed_items,
            overall_progress=overall,
            remaining_days=_calc_remaining_days(it.end_date),
        ))

    return IterationListResponse(iterations=result, total=len(result))


@router.put("/{project_id}/iterations/{iteration_id}", response_model=IterationResponse, summary="更新迭代")
async def update_iteration(
        project_id: int,
        iteration_id: int,
        request: IterationUpdateRequest,
        project_user: tuple = Depends(verify_admin_or_project_owner)
):
    """更新迭代信息"""
    project, current_user = project_user

    iteration = await TestIteration.get_or_none(id=iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="迭代不存在")

    update_data = request.dict(exclude_unset=True)
    if update_data:
        await iteration.update_from_dict(update_data)
        await iteration.save()

    creator_name = await _get_user_name(iteration.created_by_id)
    return IterationResponse(
        id=iteration.id,
        name=iteration.name,
        project_id=project_id,
        start_date=iteration.start_date,
        end_date=iteration.end_date,
        status=iteration.status,
        created_by_id=iteration.created_by_id,
        created_by_name=creator_name,
        created_at=iteration.created_at,
        updated_at=iteration.updated_at,
        remaining_days=_calc_remaining_days(iteration.end_date),
    )


@router.delete("/{project_id}/iterations/{iteration_id}", summary="删除迭代")
async def delete_iteration(
        project_id: int,
        iteration_id: int,
        project_user: tuple = Depends(verify_admin_or_project_owner)
):
    """删除迭代（级联删除排期条目和日报）"""
    project, current_user = project_user

    iteration = await TestIteration.get_or_none(id=iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="迭代不存在")

    await iteration.delete()
    return {"message": "迭代已删除"}


# ==================== 排期条目 API ====================

@router.post("/{project_id}/schedule-items", response_model=ScheduleItemResponse, summary="创建排期条目")
async def create_schedule_item(
        project_id: int,
        request: ScheduleItemCreateRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """创建排期条目（Leader分配需求）"""
    project, current_user = project_user

    # 验证迭代存在且属于本项目
    iteration = await TestIteration.get_or_none(id=request.iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="迭代不存在")

    # 验证负责人存在
    assignee = await User.get_or_none(id=request.assignee_id)
    if not assignee:
        raise HTTPException(status_code=404, detail="指定的负责人不存在")

    item = await ScheduleItem.create(
        iteration_id=request.iteration_id,
        requirement_title=request.requirement_title,
        requirement_id=request.requirement_id,
        category=request.category,
        assignee_id=request.assignee_id,
        requirement_status=request.requirement_status,
        ticket_url=request.ticket_url,
        priority=request.priority,
        planned_test_date=request.planned_test_date,
        estimated_case_days=request.estimated_case_days,
        case_output_date=request.case_output_date,
        case_status=request.case_status,
        estimated_test_days=request.estimated_test_days,
        test_date_range=request.test_date_range,
        integration_test_date=request.integration_test_date,
        remark=request.remark,
    )

    return await _build_schedule_item_response(item)


@router.get("/{project_id}/schedule-items", response_model=ScheduleItemListResponse, summary="获取排期条目列表")
async def get_schedule_items(
        project_id: int,
        iteration_id: int = Query(..., description="迭代ID"),
        category: Optional[str] = Query(None, description="业务线分类过滤"),
        assignee_id: Optional[int] = Query(None, description="负责人过滤"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取指定迭代的排期条目列表"""
    project, current_user = project_user

    filters = {"iteration_id": iteration_id, "iteration__project_id": project_id}
    if category:
        filters["category"] = category
    if assignee_id:
        filters["assignee_id"] = assignee_id

    items = await ScheduleItem.filter(**filters).order_by("category", "id").all()

    result = []
    categories = set()
    for item in items:
        resp = await _build_schedule_item_response(item)
        result.append(resp)
        if item.category:
            categories.add(item.category)

    return ScheduleItemListResponse(
        items=result,
        total=len(result),
        categories=sorted(categories),
    )


@router.put("/{project_id}/schedule-items/{item_id}", response_model=ScheduleItemResponse, summary="更新排期条目")
async def update_schedule_item(
        project_id: int,
        item_id: int,
        request: ScheduleItemUpdateRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """更新排期条目（同业务线成员或管理员可编辑）"""
    project, current_user = project_user

    item = await ScheduleItem.get_or_none(id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="排期条目不存在")

    # 验证条目属于本项目
    iteration = await TestIteration.get_or_none(id=item.iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="排期条目不属于本项目")

    # 权限校验：管理员 / 项目负责人 / 同业务线成员 / 本人负责的条目
    if not current_user.is_superuser and project.owner_id != current_user.id and item.assignee_id != current_user.id:
        # 检查用户是否属于该条目的业务线
        can_edit = False
        if item.category:
            from service.project.models import ProjectModule
            module = await ProjectModule.get_or_none(
                project_id=project_id, name=item.category, parent_id=None
            )
            if module:
                blm = await BusinessLineMember.get_or_none(
                    module_id=module.id, user_id=current_user.id
                )
                can_edit = blm is not None
        if not can_edit:
            raise HTTPException(status_code=403, detail="没有编辑权限，只能编辑自己业务线的排期条目")

    update_data = request.dict(exclude_unset=True)
    if update_data:
        await item.update_from_dict(update_data)

        # 自动计算风险等级
        risk_level, risk_reason = _calc_risk_level(item, iteration)
        item.risk_level = risk_level
        item.risk_reason = risk_reason

        await item.save()

    return await _build_schedule_item_response(item)


@router.delete("/{project_id}/schedule-items/{item_id}", summary="删除排期条目")
async def delete_schedule_item(
        project_id: int,
        item_id: int,
        project_user: tuple = Depends(verify_admin_or_project_owner)
):
    """删除排期条目"""
    project, current_user = project_user

    item = await ScheduleItem.get_or_none(id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="排期条目不存在")

    iteration = await TestIteration.get_or_none(id=item.iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="排期条目不属于本项目")

    await item.delete()
    return {"message": "排期条目已删除"}


# ==================== 测试日报 API ====================

@router.post("/{project_id}/daily-reports", response_model=DailyReportResponse, summary="提交日报")
async def submit_daily_report(
        project_id: int,
        request: DailyReportCreateRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """测试人员提交当日工作日报"""
    project, current_user = project_user
    today = date.today()

    # 验证排期条目存在
    item = await ScheduleItem.get_or_none(id=request.schedule_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="排期条目不存在")

    # 验证条目属于本项目
    iteration = await TestIteration.get_or_none(id=item.iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="排期条目不属于本项目")

    # 检查今天是否已提交过该条目的日报
    existing = await DailyReport.get_or_none(
        schedule_item_id=request.schedule_item_id,
        reporter_id=current_user.id,
        report_date=today
    )

    if existing:
        # 更新已有日报
        existing.today_progress = request.today_progress
        existing.next_plan = request.next_plan
        if request.bug_total is not None:
            existing.bug_total = request.bug_total
        if request.bug_open is not None:
            existing.bug_open = request.bug_open
        if request.bug_fixed is not None:
            existing.bug_fixed = request.bug_fixed
        if request.bug_closed is not None:
            existing.bug_closed = request.bug_closed
        if request.case_total is not None:
            existing.case_total = request.case_total
        if request.case_executed is not None:
            existing.case_executed = request.case_executed
        if request.case_passed is not None:
            existing.case_passed = request.case_passed
        if request.case_failed is not None:
            existing.case_failed = request.case_failed
        await existing.save()
        report = existing
    else:
        # 创建新日报
        report = await DailyReport.create(
            schedule_item_id=request.schedule_item_id,
            reporter_id=current_user.id,
            report_date=today,
            today_progress=request.today_progress,
            next_plan=request.next_plan,
            bug_total=request.bug_total or 0,
            bug_open=request.bug_open or 0,
            bug_fixed=request.bug_fixed or 0,
            bug_closed=request.bug_closed or 0,
            case_total=request.case_total or 0,
            case_executed=request.case_executed or 0,
            case_passed=request.case_passed or 0,
            case_failed=request.case_failed or 0,
        )

    # 同步更新排期条目进度
    if request.actual_progress is not None:
        item.actual_progress = request.actual_progress
        # 自动更新风险等级
        risk_level, risk_reason = _calc_risk_level(item, iteration)
        item.risk_level = risk_level
        item.risk_reason = risk_reason
        await item.save()

    reporter_name = await _get_user_name(current_user.id)
    return DailyReportResponse(
        id=report.id,
        schedule_item_id=report.schedule_item_id,
        requirement_title=item.requirement_title,
        reporter_id=current_user.id,
        reporter_name=reporter_name,
        report_date=report.report_date,
        today_progress=report.today_progress,
        next_plan=report.next_plan,
        case_total=report.case_total,
        case_executed=report.case_executed,
        case_passed=report.case_passed,
        case_failed=report.case_failed,
        bug_total=report.bug_total,
        bug_open=report.bug_open,
        bug_fixed=report.bug_fixed,
        bug_closed=report.bug_closed,
        ai_report_content=report.ai_report_content,
        feishu_sent=report.feishu_sent,
        actual_progress=item.actual_progress,
        risk_level=item.risk_level,
        created_at=report.created_at,
    )


@router.get("/{project_id}/daily-reports/my", response_model=DailyReportListResponse, summary="获取我的日报")
async def get_my_daily_reports(
        project_id: int,
        iteration_id: int = Query(..., description="迭代ID"),
        report_date: Optional[date] = Query(None, description="日期过滤"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取当前用户的日报列表"""
    project, current_user = project_user

    # 获取该迭代中分配给当前用户的排期条目
    items = await ScheduleItem.filter(
        iteration_id=iteration_id,
        iteration__project_id=project_id,
        assignee_id=current_user.id,
    ).all()

    item_ids = [i.id for i in items]
    item_map = {i.id: i for i in items}

    if not item_ids:
        return DailyReportListResponse(reports=[], total=0)

    filters = {"schedule_item_id__in": item_ids, "reporter_id": current_user.id}
    if report_date:
        filters["report_date"] = report_date

    reports = await DailyReport.filter(**filters).order_by("-report_date", "-created_at").all()

    reporter_name = await _get_user_name(current_user.id)
    result = []
    for r in reports:
        item = item_map.get(r.schedule_item_id)
        result.append(DailyReportResponse(
            id=r.id,
            schedule_item_id=r.schedule_item_id,
            requirement_title=item.requirement_title if item else None,
            reporter_id=r.reporter_id,
            reporter_name=reporter_name,
            report_date=r.report_date,
            today_progress=r.today_progress,
            next_plan=r.next_plan,
            case_total=r.case_total,
            case_executed=r.case_executed,
            case_passed=r.case_passed,
            case_failed=r.case_failed,
            bug_total=r.bug_total,
            bug_open=r.bug_open,
            bug_fixed=r.bug_fixed,
            bug_closed=r.bug_closed,
            ai_report_content=r.ai_report_content,
            feishu_sent=r.feishu_sent,
            actual_progress=item.actual_progress if item else 0,
            risk_level=item.risk_level if item else "none",
            created_at=r.created_at,
        ))

    return DailyReportListResponse(reports=result, total=len(result))


@router.get("/{project_id}/my-schedule-items", summary="获取我今日的排期条目")
async def get_my_schedule_items(
        project_id: int,
        iteration_id: int = Query(..., description="迭代ID"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取当前用户在指定迭代中被分配的排期条目（用于日报填写页面）"""
    project, current_user = project_user

    items = await ScheduleItem.filter(
        iteration_id=iteration_id,
        iteration__project_id=project_id,
        assignee_id=current_user.id,
    ).order_by("category", "id").all()

    today = date.today()
    result = []
    for item in items:
        # 检查今天是否已提交日报
        today_report = await DailyReport.get_or_none(
            schedule_item_id=item.id,
            reporter_id=current_user.id,
            report_date=today,
        )

        resp = await _build_schedule_item_response(item)
        result.append({
            **resp.dict(),
            "has_today_report": today_report is not None,
            "today_report_id": today_report.id if today_report else None,
        })

    return {"items": result, "total": len(result)}


# ==================== 管理员 Dashboard API ====================

@router.get("/{project_id}/dashboard/daily", response_model=DashboardDailyResponse, summary="Dashboard-当日动态")
async def get_dashboard_daily(
        project_id: int,
        iteration_id: int = Query(..., description="迭代ID"),
        target_date: Optional[date] = Query(None, description="查询日期，默认今天"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """管理员Dashboard场景1：查看当日各需求的进度内容"""
    project, current_user = project_user
    query_date = target_date or date.today()

    # 获取该迭代的所有排期条目
    items = await ScheduleItem.filter(
        iteration_id=iteration_id,
        iteration__project_id=project_id,
    ).all()
    item_ids = [i.id for i in items]
    item_map = {i.id: i for i in items}

    # 获取当日的日报
    reports = await DailyReport.filter(
        schedule_item_id__in=item_ids,
        report_date=query_date,
    ).order_by("reporter_id").all()

    # 按人聚合
    reporter_reports = {}
    for r in reports:
        if r.reporter_id not in reporter_reports:
            reporter_reports[r.reporter_id] = []
        item = item_map.get(r.schedule_item_id)
        reporter_name = await _get_user_name(r.reporter_id)
        reporter_reports[r.reporter_id].append(DailyReportResponse(
            id=r.id,
            schedule_item_id=r.schedule_item_id,
            requirement_title=item.requirement_title if item else None,
            reporter_id=r.reporter_id,
            reporter_name=reporter_name,
            report_date=r.report_date,
            today_progress=r.today_progress,
            next_plan=r.next_plan,
            case_total=r.case_total,
            case_executed=r.case_executed,
            case_passed=r.case_passed,
            case_failed=r.case_failed,
            bug_total=r.bug_total,
            bug_open=r.bug_open,
            bug_fixed=r.bug_fixed,
            bug_closed=r.bug_closed,
            ai_report_content=r.ai_report_content,
            feishu_sent=r.feishu_sent,
            actual_progress=item.actual_progress if item else 0,
            risk_level=item.risk_level if item else "none",
            created_at=r.created_at,
        ))

    updates = []
    reported_user_ids = set()
    for uid, reps in reporter_reports.items():
        name = await _get_user_name(uid)
        reported_user_ids.add(uid)
        updates.append(DashboardDailyUpdate(
            reporter_name=name,
            reporter_id=uid,
            reports=reps,
        ))

    # 找出未提交日报的成员
    all_assignee_ids = set(i.assignee_id for i in items)
    no_report_ids = all_assignee_ids - reported_user_ids
    no_report_users = []
    for uid in no_report_ids:
        name = await _get_user_name(uid)
        no_report_users.append(name)

    # 当日统计
    daily_bugs_new = sum(r.bug_total for r in reports)
    daily_bugs_closed = sum(r.bug_closed for r in reports)
    daily_cases_executed = sum(r.case_executed for r in reports)

    return DashboardDailyResponse(
        date=query_date,
        updates=updates,
        no_report_users=no_report_users,
        daily_bugs_new=daily_bugs_new,
        daily_bugs_closed=daily_bugs_closed,
        daily_cases_executed=daily_cases_executed,
    )


@router.get("/{project_id}/dashboard/iteration-summary", response_model=DashboardIterationSummaryResponse,
            summary="Dashboard-迭代汇总")
async def get_dashboard_iteration_summary(
        project_id: int,
        iteration_id: int = Query(..., description="迭代ID"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """管理员Dashboard场景2&3：迭代中/收尾时查看各需求汇总"""
    project, current_user = project_user

    iteration = await TestIteration.get_or_none(id=iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="迭代不存在")

    items = await ScheduleItem.filter(
        iteration_id=iteration_id,
        iteration__project_id=project_id,
    ).order_by("category", "id").all()

    remaining_days = _calc_remaining_days(iteration.end_date)
    is_closing = remaining_days <= 3

    # 统计数据
    total_requirements = len(items)
    completed = len([i for i in items if i.requirement_status == 'completed'])
    testing = len([i for i in items if i.requirement_status == 'testing'])
    developing = len([i for i in items if i.requirement_status in ('developing', 'pending', 'scheduled')])

    # 聚合用例和Bug数据（从日报中获取最新数据）
    total_cases = 0
    executed_cases = 0
    passed_cases = 0
    total_bugs = 0
    open_bugs = 0

    summary_items = []
    high_risk = []
    medium_risk = []
    ready = []

    for item in items:
        # 获取该条目最新的日报数据
        latest_report = await DailyReport.filter(
            schedule_item_id=item.id
        ).order_by("-report_date").first()

        case_t = latest_report.case_total if latest_report else 0
        case_e = latest_report.case_executed if latest_report else 0
        bug_t = latest_report.bug_total if latest_report else 0
        bug_o = latest_report.bug_open if latest_report else 0

        total_cases += case_t
        executed_cases += case_e
        passed_cases += (latest_report.case_passed if latest_report else 0)
        total_bugs += bug_t
        open_bugs += bug_o

        # 自动更新风险等级
        risk_level, risk_reason = _calc_risk_level(item, iteration)
        if item.risk_level != risk_level:
            item.risk_level = risk_level
            item.risk_reason = risk_reason
            await item.save()

        assignee_name = await _get_user_name(item.assignee_id)
        summary_item = IterationSummaryItem(
            id=item.id,
            requirement_title=item.requirement_title,
            assignee_name=assignee_name,
            requirement_status=item.requirement_status,
            priority=item.priority,
            case_total=case_t,
            case_executed=case_e,
            bug_total=bug_t,
            bug_open=bug_o,
            actual_progress=item.actual_progress,
            risk_level=item.risk_level,
            risk_reason=item.risk_reason,
        )
        summary_items.append(summary_item)

        # 收尾模式分组
        if item.risk_level == 'high':
            high_risk.append(summary_item)
        elif item.risk_level in ('medium', 'low'):
            medium_risk.append(summary_item)
        else:
            ready.append(summary_item)

    overall_progress = int(sum(i.actual_progress for i in items) / total_requirements) if total_requirements > 0 else 0

    return DashboardIterationSummaryResponse(
        iteration_id=iteration.id,
        iteration_name=iteration.name,
        start_date=iteration.start_date,
        end_date=iteration.end_date,
        remaining_days=remaining_days,
        is_closing=is_closing,
        overall_progress=overall_progress,
        total_requirements=total_requirements,
        completed_requirements=completed,
        testing_requirements=testing,
        developing_requirements=developing,
        total_cases=total_cases,
        executed_cases=executed_cases,
        passed_cases=passed_cases,
        total_bugs=total_bugs,
        open_bugs=open_bugs,
        items=summary_items,
        high_risk_items=high_risk,
        medium_risk_items=medium_risk,
        ready_items=ready,
    )


# ==================== AI 报告生成 API ====================

@router.post("/{project_id}/daily-reports/{report_id}/generate-ai-report", summary="AI生成格式化日报")
async def generate_ai_report(
        project_id: int,
        report_id: int,
        project_user: tuple = Depends(verify_schedule_access)
):
    """调用AI生成格式化的测试进度报告"""
    project, current_user = project_user

    report = await DailyReport.get_or_none(id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")

    item = await ScheduleItem.get_or_none(id=report.schedule_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="排期条目不存在")

    iteration = await TestIteration.get_or_none(id=item.iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="迭代不属于本项目")

    reporter_name = await _get_user_name(report.reporter_id)

    # 构建 AI Prompt
    report_data = {
        "requirement": item.requirement_title,
        "assignee": reporter_name,
        "priority": item.priority or "未设定",
        "date": str(report.report_date),
        "progress_percent": item.actual_progress,
        "status": item.requirement_status,
        "planned_test_date": item.planned_test_date or "未设定",
        "test_date_range": item.test_date_range or "未设定",
        "risk_level": item.risk_level,
        "risk_reason": item.risk_reason or "无",
        "today_progress": report.today_progress,
        "next_plan": report.next_plan or "待定",
        "case_summary": {
            "total": report.case_total,
            "executed": report.case_executed,
            "passed": report.case_passed,
            "failed": report.case_failed,
        },
        "bug_summary": {
            "total": report.bug_total,
            "open": report.bug_open,
            "fixed": report.bug_fixed,
            "closed": report.bug_closed,
        },
        "iteration": {
            "name": iteration.name,
            "remaining_days": _calc_remaining_days(iteration.end_date),
        }
    }

    try:
        from config.settings import llm

        prompt = f"""你是一个资深测试经理，请根据以下数据生成一份简洁的测试进度报告。

报告格式要求：
1. 第一行：需求名称 + 测试进度百分比 + 风险状态（一句话概括）
2. 进展说明（用 • 号列举关键进展，2-4条）
3. 缺陷概况（Bug总数、待处理数、各优先级分布）
4. 下一步计划（2-3条）

语言要求：简洁、专业、直接说重点，不要客套话。

数据：
{json.dumps(report_data, ensure_ascii=False, indent=2)}
"""

        result = llm.invoke(prompt)
        ai_content = result.content

        # 保存 AI 报告
        report.ai_report_content = ai_content
        await report.save()

        return {
            "report_id": report.id,
            "ai_report_content": ai_content,
        }

    except Exception as e:
        logger.error(f"AI报告生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI报告生成失败: {str(e)}")


# ==================== 飞书推送 API ====================

@router.post("/{project_id}/feishu-webhooks", response_model=FeishuWebhookResponse, summary="添加飞书群")
async def create_feishu_webhook(
        project_id: int,
        request: FeishuWebhookCreateRequest,
        project_user: tuple = Depends(verify_admin_or_project_owner)
):
    """添加飞书群Webhook配置"""
    project, current_user = project_user

    webhook = await FeishuWebhook.create(
        project_id=project_id,
        name=request.name,
        webhook_url=request.webhook_url,
        created_by_id=current_user.id,
    )

    creator_name = await _get_user_name(current_user.id)
    return FeishuWebhookResponse(
        id=webhook.id,
        project_id=project_id,
        name=webhook.name,
        webhook_url=webhook.webhook_url,
        is_active=webhook.is_active,
        created_by_id=current_user.id,
        created_by_name=creator_name,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
    )


@router.get("/{project_id}/feishu-webhooks", response_model=FeishuWebhookListResponse, summary="获取飞书群列表")
async def get_feishu_webhooks(
        project_id: int,
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取项目的飞书群Webhook配置列表"""
    project, current_user = project_user

    webhooks = await FeishuWebhook.filter(project_id=project_id).order_by("-created_at").all()

    result = []
    for wh in webhooks:
        creator_name = await _get_user_name(wh.created_by_id)
        result.append(FeishuWebhookResponse(
            id=wh.id,
            project_id=project_id,
            name=wh.name,
            webhook_url=wh.webhook_url,
            is_active=wh.is_active,
            created_by_id=wh.created_by_id,
            created_by_name=creator_name,
            created_at=wh.created_at,
            updated_at=wh.updated_at,
        ))

    return FeishuWebhookListResponse(webhooks=result, total=len(result))


@router.put("/{project_id}/feishu-webhooks/{webhook_id}", response_model=FeishuWebhookResponse, summary="更新飞书群")
async def update_feishu_webhook(
        project_id: int,
        webhook_id: int,
        request: FeishuWebhookUpdateRequest,
        project_user: tuple = Depends(verify_admin_or_project_owner)
):
    """更新飞书群Webhook配置"""
    project, current_user = project_user

    webhook = await FeishuWebhook.get_or_none(id=webhook_id, project_id=project_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook配置不存在")

    update_data = request.dict(exclude_unset=True)
    if update_data:
        await webhook.update_from_dict(update_data)
        await webhook.save()

    creator_name = await _get_user_name(webhook.created_by_id)
    return FeishuWebhookResponse(
        id=webhook.id,
        project_id=project_id,
        name=webhook.name,
        webhook_url=webhook.webhook_url,
        is_active=webhook.is_active,
        created_by_id=webhook.created_by_id,
        created_by_name=creator_name,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
    )


@router.delete("/{project_id}/feishu-webhooks/{webhook_id}", summary="删除飞书群")
async def delete_feishu_webhook(
        project_id: int,
        webhook_id: int,
        project_user: tuple = Depends(verify_admin_or_project_owner)
):
    """删除飞书群Webhook配置"""
    project, current_user = project_user

    webhook = await FeishuWebhook.get_or_none(id=webhook_id, project_id=project_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook配置不存在")

    await webhook.delete()
    return {"message": "Webhook配置已删除"}


@router.post("/{project_id}/feishu-webhooks/{webhook_id}/test", summary="测试飞书Webhook")
async def test_feishu_webhook(
        project_id: int,
        webhook_id: int,
        project_user: tuple = Depends(verify_admin_or_project_owner)
):
    """发送测试消息到飞书群"""
    project, current_user = project_user

    webhook = await FeishuWebhook.get_or_none(id=webhook_id, project_id=project_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook配置不存在")

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "🔔 AI测试平台 - 连接测试"},
                "template": "blue"
            },
            "elements": [{
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"✅ 飞书群 **{webhook.name}** 连接成功！\n\n来自项目：**{project.name}**\n测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }]
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook.webhook_url, json=card)
            if resp.status_code == 200:
                return {"success": True, "message": "测试消息发送成功"}
            else:
                return {"success": False, "message": f"发送失败: {resp.text}"}
    except Exception as e:
        return {"success": False, "message": f"发送失败: {str(e)}"}


@router.post("/{project_id}/daily-reports/{report_id}/send-feishu", summary="推送日报到飞书群")
async def send_report_to_feishu(
        project_id: int,
        report_id: int,
        request: FeishuSendRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """将日报推送到飞书群"""
    project, current_user = project_user

    report = await DailyReport.get_or_none(id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")

    item = await ScheduleItem.get_or_none(id=report.schedule_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="排期条目不存在")

    reporter_name = await _get_user_name(report.reporter_id)

    # 构建风险标签
    risk_labels = {"none": "🟢 进度正常", "low": "🟡 需关注", "medium": "🟡 有风险", "high": "🔴 高风险"}
    risk_label = risk_labels.get(item.risk_level, "🟢 进度正常")

    # 构建进度条
    progress = item.actual_progress
    filled = progress // 10
    bar = "█" * filled + "░" * (10 - filled)

    # 构建Bug概况
    bug_md = ""
    if report.bug_total > 0:
        bug_md = f"总缺陷：{report.bug_total}个 | 待处理：{report.bug_open}个 | 已修复：{report.bug_fixed}个 | 已关闭：{report.bug_closed}个"
    else:
        bug_md = "暂无缺陷"

    # 使用AI报告或手动构建
    report_content = report.ai_report_content or report.today_progress

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📋 测试进度报告 — {item.requirement_title}"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"📊 **测试进度**：{progress}%  {bar}\n"
                            f"👤 **负责人**：{reporter_name}\n"
                            f"🏷 **风险等级**：{risk_label}"
                        )
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**进展说明**\n{report_content}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**缺陷概况**\n{bug_md}"
                    }
                },
            ]
        }
    }

    if report.next_plan:
        card["card"]["elements"].extend([
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**下一步计划**\n{report.next_plan}"
                }
            }
        ])

    # 发送到所有指定的Webhook
    results = []
    for wh_id in request.webhook_ids:
        webhook = await FeishuWebhook.get_or_none(id=wh_id, project_id=project_id)
        if not webhook or not webhook.is_active:
            results.append({"webhook_id": wh_id, "success": False, "message": "Webhook不存在或已禁用"})
            continue

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook.webhook_url, json=card)
                success = resp.status_code == 200
                results.append({
                    "webhook_id": wh_id,
                    "webhook_name": webhook.name,
                    "success": success,
                    "message": "发送成功" if success else f"发送失败: {resp.text}"
                })
        except Exception as e:
            results.append({"webhook_id": wh_id, "success": False, "message": str(e)})

    # 更新日报的飞书推送状态
    if any(r["success"] for r in results):
        report.feishu_sent = True
        report.feishu_sent_at = datetime.now()
        await report.save()

    return {"results": results}
