"""
测试排期管理模块 API
包含：迭代管理、排期条目、测试日报、管理员Dashboard、飞书推送
"""
import json
import logging
import base64
from datetime import date, datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Depends, status, Query, File, UploadFile
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
from .models import TestIteration, ScheduleItem, DailyReport, ProgressReport, FeishuWebhook, Defect
from .schemas import (
    IterationCreateRequest, IterationUpdateRequest, IterationResponse, IterationListResponse,
    ScheduleItemCreateRequest, ScheduleItemUpdateRequest, ScheduleItemResponse, ScheduleItemListResponse,
    DailyReportCreateRequest, DailyReportResponse, DailyReportListResponse,
    DashboardDailyUpdate, DashboardDailyResponse,
    DashboardIterationSummaryResponse, IterationSummaryItem,
    FeishuWebhookCreateRequest, FeishuWebhookUpdateRequest,
    FeishuWebhookResponse, FeishuWebhookListResponse,
    FeishuSendRequest,
    AiReportUpdateRequest, ProgressCalculateRequest, ProgressCalculateResponse,
    DefectCreateRequest, DefectUpdateRequest, DefectResponse, DefectListResponse, DefectStatsResponse,
    PROGRESS_STAGE_TAGS, PROGRESS_STATUS_OPTIONS, REQUIREMENT_STATUS_OPTIONS,
    STAGE_TO_REQUIREMENT_STATUS, STAGE_TO_CASE_STATUS,
    PRE_TESTING_STAGES, FORMAL_TESTING_STAGES, STAGE_PRIORITY_ORDER,
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


async def _get_linked_requirement_names(item_ids: list) -> list:
    """根据排期条目ID列表获取需求名称列表"""
    if not item_ids:
        return []
    items = await ScheduleItem.filter(id__in=item_ids).all()
    return [item.requirement_title for item in items]


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
        requirement_status=request.requirement_status or 'pending',
        ticket_url=request.ticket_url,
        priority=request.priority,
        planned_test_date=request.planned_test_date,
        estimated_case_days=request.estimated_case_days,
        case_output_date=request.case_output_date,
        case_status=request.case_status or 'pending',
        estimated_test_days=request.estimated_test_days,
        test_date_range=request.test_date_range,
        integration_test_date=request.integration_test_date,
        remark=request.remark,
    )

    return await _build_schedule_item_response(item)


@router.get("/{project_id}/schedule-items", response_model=ScheduleItemListResponse, summary="获取排期条目列表")
async def get_schedule_items(
        project_id: int,
        iteration_id: Optional[int] = Query(None, description="迭代ID（不传则返回项目所有排期条目）"),
        category: Optional[str] = Query(None, description="业务线分类过滤"),
        assignee_id: Optional[int] = Query(None, description="负责人过滤"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取排期条目列表，不传iteration_id则返回项目下所有迭代的排期条目"""
    project, current_user = project_user

    filters = {"iteration__project_id": project_id}
    if iteration_id:
        filters["iteration_id"] = iteration_id
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

    # 自动从缺陷表统计Bug数据
    defects = await Defect.filter(schedule_item_id=request.schedule_item_id).all()
    auto_bug_total = len(defects)
    auto_bug_open = len([d for d in defects if d.defect_status in ('open', 'fixing')])
    auto_bug_fixed = len([d for d in defects if d.defect_status == 'fixed'])
    auto_bug_closed = len([d for d in defects if d.defect_status in ('closed', 'verified')])

    # 手动值优先，没有手动值则使用自动统计
    bug_total = request.bug_total if request.bug_total is not None else auto_bug_total
    bug_open = request.bug_open if request.bug_open is not None else auto_bug_open
    bug_fixed = request.bug_fixed if request.bug_fixed is not None else auto_bug_fixed
    bug_closed = request.bug_closed if request.bug_closed is not None else auto_bug_closed

    if existing:
        # 更新已有日报
        existing.today_progress = request.today_progress
        existing.next_plan = request.next_plan
        existing.bug_total = bug_total
        existing.bug_open = bug_open
        existing.bug_fixed = bug_fixed
        existing.bug_closed = bug_closed
        if request.case_execution_progress is not None:
            existing.case_execution_progress = request.case_execution_progress
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
            bug_total=bug_total,
            bug_open=bug_open,
            bug_fixed=bug_fixed,
            bug_closed=bug_closed,
            case_execution_progress=request.case_execution_progress or 0,
        )

    # 同步更新排期条目进度
    if request.actual_progress is not None:
        item.actual_progress = request.actual_progress

    # ====== 智能状态同步 ======
    # 根据选中的测试阶段自动更新排期条目的需求状态和用例状态
    if request.stage_tags:
        # 找出选中阶段中优先级最高的
        highest_idx = -1
        for tag in request.stage_tags:
            if tag in STAGE_PRIORITY_ORDER:
                idx = STAGE_PRIORITY_ORDER.index(tag)
                if idx > highest_idx:
                    highest_idx = idx

        if highest_idx >= 0:
            highest_stage = STAGE_PRIORITY_ORDER[highest_idx]

            # 同步需求状态
            new_req_status = STAGE_TO_REQUIREMENT_STATUS.get(highest_stage)
            if new_req_status and item.requirement_status != new_req_status:
                item.requirement_status = new_req_status
                logger.info(f"智能同步: 排期条目 {item.id} 需求状态更新为 {new_req_status} (基于阶段 {highest_stage})")

            # 同步用例状态
            new_case_status = STAGE_TO_CASE_STATUS.get(highest_stage)
            if new_case_status and item.case_status != new_case_status:
                item.case_status = new_case_status
                logger.info(f"智能同步: 排期条目 {item.id} 用例状态更新为 {new_case_status} (基于阶段 {highest_stage})")

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
        case_execution_progress=getattr(report, 'case_execution_progress', 0),
        bug_total=report.bug_total,
        bug_open=report.bug_open,
        bug_fixed=report.bug_fixed,
        bug_closed=report.bug_closed,
        ai_report_content=report.ai_report_content,
        feishu_sent=report.feishu_sent,
        actual_progress=item.actual_progress,
        risk_level=item.risk_level,
        requirement_status=item.requirement_status,
        case_status=item.case_status,
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
            case_execution_progress=getattr(r, 'case_execution_progress', 0),
            bug_total=r.bug_total,
            bug_open=r.bug_open,
            bug_fixed=r.bug_fixed,
            bug_closed=r.bug_closed,
            ai_report_content=r.ai_report_content,
            feishu_sent=r.feishu_sent,
            actual_progress=item.actual_progress if item else 0,
            risk_level=item.risk_level if item else "none",
            requirement_status=item.requirement_status if item else None,
            case_status=item.case_status if item else None,
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
            case_execution_progress=getattr(r, 'case_execution_progress', 0),
            bug_total=r.bug_total,
            bug_open=r.bug_open,
            bug_fixed=r.bug_fixed,
            bug_closed=r.bug_closed,
            ai_report_content=r.ai_report_content,
            feishu_sent=r.feishu_sent,
            actual_progress=item.actual_progress if item else 0,
            risk_level=item.risk_level if item else "none",
            requirement_status=item.requirement_status if item else None,
            case_status=item.case_status if item else None,
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
    daily_cases_executed = sum(getattr(r, 'case_execution_progress', 0) for r in reports)

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

    # 聚合Bug数据（从日报中获取最新数据）
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

        case_ep = getattr(latest_report, 'case_execution_progress', 0) if latest_report else 0
        bug_t = latest_report.bug_total if latest_report else 0
        bug_o = latest_report.bug_open if latest_report else 0

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
            case_execution_progress=case_ep,
            bug_total=bug_t,
            bug_open=bug_o,
            actual_progress=item.actual_progress,
            risk_level=item.risk_level,
            case_status=item.case_status,
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
            "execution_progress": getattr(report, 'case_execution_progress', 0),
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
        project_user: tuple = Depends(verify_schedule_access)
):
    """添加飞书群Webhook配置"""
    project, current_user = project_user

    webhook = await FeishuWebhook.create(
        project_id=project_id,
        name=request.name,
        webhook_url=request.webhook_url,
        linked_schedule_item_ids=request.linked_schedule_item_ids,
        created_by_id=current_user.id,
    )

    creator_name = await _get_user_name(current_user.id)
    linked_names = await _get_linked_requirement_names(webhook.linked_schedule_item_ids)
    return FeishuWebhookResponse(
        id=webhook.id,
        project_id=project_id,
        name=webhook.name,
        webhook_url=webhook.webhook_url,
        is_active=webhook.is_active,
        linked_schedule_item_ids=webhook.linked_schedule_item_ids,
        linked_requirement_names=linked_names,
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
        linked_names = await _get_linked_requirement_names(wh.linked_schedule_item_ids)
        result.append(FeishuWebhookResponse(
            id=wh.id,
            project_id=project_id,
            name=wh.name,
            webhook_url=wh.webhook_url,
            is_active=wh.is_active,
            linked_schedule_item_ids=wh.linked_schedule_item_ids,
            linked_requirement_names=linked_names,
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
        project_user: tuple = Depends(verify_schedule_access)
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
    linked_names = await _get_linked_requirement_names(webhook.linked_schedule_item_ids)
    return FeishuWebhookResponse(
        id=webhook.id,
        project_id=project_id,
        name=webhook.name,
        webhook_url=webhook.webhook_url,
        is_active=webhook.is_active,
        linked_schedule_item_ids=webhook.linked_schedule_item_ids,
        linked_requirement_names=linked_names,
        created_by_id=webhook.created_by_id,
        created_by_name=creator_name,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
    )


@router.delete("/{project_id}/feishu-webhooks/{webhook_id}", summary="删除需求群")
async def delete_feishu_webhook(
        project_id: int,
        webhook_id: int,
        project_user: tuple = Depends(verify_schedule_access)
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
        project_user: tuple = Depends(verify_schedule_access)
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


@router.get("/{project_id}/daily-reports/{report_id}/matched-webhooks", summary="获取自动匹配的需求群")
async def get_matched_webhooks(
        project_id: int,
        report_id: int,
        project_user: tuple = Depends(verify_schedule_access)
):
    """根据需求自动匹配对应的需求群"""
    project, current_user = project_user

    report = await DailyReport.get_or_none(id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")

    item = await ScheduleItem.get_or_none(id=report.schedule_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="排期条目不存在")

    # 获取所有活跃的webhook
    webhooks = await FeishuWebhook.filter(project_id=project_id, is_active=True).all()

    matched = []
    for wh in webhooks:
        linked_ids = wh.linked_schedule_item_ids or []
        if not isinstance(linked_ids, list):
            linked_ids = []
        # 全局群（没有关联需求）始终匹配
        if not linked_ids:
            matched.append({"id": wh.id, "name": wh.name, "match_type": "global"})
        elif item.id in linked_ids:
            # 该需求群关联了当前需求，精确匹配
            matched.append({"id": wh.id, "name": wh.name, "match_type": "requirement"})

    return {"matched_webhooks": matched, "requirement_title": item.requirement_title}


@router.post("/{project_id}/daily-reports/{report_id}/send-feishu", summary="同步到需求群")
async def send_report_to_feishu(
        project_id: int,
        report_id: int,
        request: FeishuSendRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """将测试进度同步到需求群"""
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


# ==================== AI 报告编辑 API ====================

@router.put("/{project_id}/daily-reports/{report_id}/ai-content", summary="编辑AI报告内容")
async def update_ai_report_content(
        project_id: int,
        report_id: int,
        request: AiReportUpdateRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """允许测试人员编辑AI生成的报告内容"""
    project, current_user = project_user

    report = await DailyReport.get_or_none(id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")

    # 只允许报告人本人或管理员编辑
    if report.reporter_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只能编辑自己的报告")

    report.ai_report_content = request.ai_report_content
    await report.save()

    return {"report_id": report.id, "ai_report_content": report.ai_report_content}


# ==================== 进度智能计算 API ====================

@router.post("/{project_id}/calculate-progress", response_model=ProgressCalculateResponse,
             summary="AI计算建议进度")
async def calculate_progress(
        project_id: int,
        request: ProgressCalculateRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """根据多维度数据智能计算建议进度"""
    project, current_user = project_user

    item = await ScheduleItem.get_or_none(id=request.schedule_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="排期条目不存在")

    iteration = await TestIteration.get_or_none(id=item.iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="排期条目不属于本项目")

    factors = []
    base_progress = 0

    # 维度1: 测试阶段标签权重（按软件测试流程正序）
    stage_weights = {
        "requirement_clarify": 3,
        "tech_review": 5,
        "case_writing": 10,
        "case_review": 15,
        "smoke_test": 25,
        "first_round_test": 40,
        "functional_test": 55,
        "exploratory_test": 65,
        "cross_test": 70,
        "regression_test": 80,
        "bug_verify": 90,
    }
    if request.stage_tags:
        max_stage = max(stage_weights.get(t, 0) for t in request.stage_tags)
        base_progress = max_stage
        tag_labels = [next((s["label"] for s in PROGRESS_STAGE_TAGS if s["key"] == t), t) for t in request.stage_tags]
        factors.append(f"当前阶段: {', '.join(tag_labels)} → 基础进度 {max_stage}%")

    # 维度2: 缺陷数据修正
    defect_total = await Defect.filter(schedule_item_id=item.id).count()
    defect_open = await Defect.filter(schedule_item_id=item.id, defect_status='open').count()
    defect_fixing = await Defect.filter(schedule_item_id=item.id, defect_status='fixing').count()
    if defect_total > 0:
        resolved_rate = (defect_total - defect_open - defect_fixing) / defect_total
        if resolved_rate < 0.5 and base_progress > 70:
            base_progress = min(base_progress, 70)
            factors.append(f"缺陷收敛率 {resolved_rate:.0%}（待处理{defect_open}个），进度修正至 ≤70%")
        elif resolved_rate >= 0.8:
            factors.append(f"缺陷收敛率 {resolved_rate:.0%}，Bug修复良好")

    # 维度3: 用例执行进度（优先使用前端传入的进度值）
    case_progress = None
    if request.case_execution_progress is not None:
        case_progress = request.case_execution_progress
        factors.append(f"用例执行进度: {case_progress}%")
    else:
        # 回退：从最新日报获取
        latest_report = await DailyReport.filter(
            schedule_item_id=item.id
        ).order_by("-report_date").first()
        if latest_report and getattr(latest_report, 'case_execution_progress', 0) > 0:
            case_progress = latest_report.case_execution_progress
            factors.append(f"用例执行进度(历史): {case_progress}%")

    if case_progress is not None and case_progress > 0:
        # 用例进度占比调和
        adjusted = int(base_progress * 0.6 + case_progress * 0.4)
        if abs(adjusted - base_progress) > 5:
            base_progress = adjusted
            factors.append(f"结合用例进度调和为 {adjusted}%")

    # 维度4: 进度状态修正
    if request.progress_status == "blocked":
        base_progress = max(base_progress - 10, 0)
        factors.append("状态: 阻塞等待，进度 -10%")
    elif request.progress_status == "ahead":
        base_progress = min(base_progress + 5, 100)
        factors.append("状态: 提前完成，进度 +5%")
    elif request.progress_status == "delayed":
        base_progress = max(base_progress - 5, 0)
        factors.append("状态: 进度延迟，进度 -5%")

    # 确保进度范围
    base_progress = max(0, min(100, base_progress))

    if not factors:
        factors.append("暂无足够数据，使用默认进度")

    return ProgressCalculateResponse(
        suggested_progress=base_progress,
        factors=factors,
    )


# ==================== 进度标签选项 API ====================

@router.get("/{project_id}/progress-options", summary="获取进度标签选项")
async def get_progress_options(
        project_id: int,
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取测试阶段标签和状态选项"""
    return {
        "stage_tags": PROGRESS_STAGE_TAGS,
        "status_options": PROGRESS_STATUS_OPTIONS,
        "requirement_status_options": REQUIREMENT_STATUS_OPTIONS,
    }


# ==================== 截图AI识别 API ====================

@router.post("/{project_id}/analyze-screenshot", summary="截图AI识别缺陷数据")
async def analyze_screenshot(
        project_id: int,
        file: UploadFile = File(...),
        project_user: tuple = Depends(verify_schedule_access)
):
    """
    上传飞书项目缺陷列表截图，AI自动识别并提取缺陷统计数据。
    支持分析缺陷列表、测试用例列表等截图。
    """
    project, current_user = project_user

    # 验证文件类型
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}，请上传图片文件")

    # 限制文件大小 (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

    content_type = file.content_type or "image/png"
    base64_image = base64.b64encode(contents).decode('utf-8')

    try:
        from config.settings import llm
        from langchain_core.messages import HumanMessage

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": """请仔细逐行分析这张项目管理工具（如飞书项目）的缺陷/Bug列表截图。

## 分析步骤（请严格按步骤执行）

### 第1步：逐行识别
逐行读取截图中每一条缺陷记录，记下它的：标题、优先级(P0/P1/P2/P3)、当前状态（如"待处理"、"修复中"、"待验证"、"回归通过"、"已修复"、"已拒绝"、"已关闭"等）。

### 第2步：分类统计
按以下规则对每条缺陷进行分类：
- **待处理(bug_open)**：状态为"待处理"、"修复中"、"待验证"、"处理中"的缺陷（即尚未最终解决的）
- **已修复(bug_fixed)**：状态为"已修复"、"已解决"、"回归通过"、"验证通过"的缺陷
- **已关闭(bug_closed)**：状态为"已关闭"、"已拒绝"、"不修复"、"重复"、"无法复现"的缺陷

### 第3步：校验
确保 bug_open + bug_fixed + bug_closed = bug_total（总条目数）。如果不等，重新检查每条记录的分类。

## 输出格式
请只返回JSON，不要任何其他文字：
{
  "bug_total": 总缺陷条目数,
  "bug_open": 待处理数量,
  "bug_fixed": 已修复数量,
  "bug_closed": 已关闭数量,
  "by_severity": {"P0": 数量, "P1": 数量, "P2": 数量, "P3": 数量},
  "details": [
    {"title": "缺陷名称摘要（尽量完整）", "severity": "P0/P1/P2/P3", "status": "截图中显示的原始状态文本"}
  ]
}

## 重要提醒
- 请逐条仔细阅读，不要遗漏也不要多算
- details数组中的条目数量必须等于bug_total
- severity按截图中显示的优先级填写
- status请填写截图中显示的原始状态文本，不要自行转换"""
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{content_type};base64,{base64_image}"}
                },
            ]
        )

        result = llm.invoke([message])
        ai_content = result.content

        # 解析JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', ai_content)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {"success": True, "data": parsed}
            except json.JSONDecodeError:
                return {"success": False, "message": "AI返回的数据格式异常", "raw": ai_content}
        else:
            return {"success": False, "message": "AI无法解析截图内容", "raw": ai_content}

    except Exception as e:
        logger.error(f"截图分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"截图分析失败: {str(e)}")


# ==================== 缺陷管理 API ====================

async def _build_defect_response(defect: Defect) -> DefectResponse:
    """构建缺陷响应"""
    item = await ScheduleItem.get_or_none(id=defect.schedule_item_id)
    reporter_name = await _get_user_name(defect.reporter_id)
    assignee_name = await _get_user_name(defect.assignee_id) if defect.assignee_id else None

    return DefectResponse(
        id=defect.id,
        schedule_item_id=defect.schedule_item_id,
        requirement_title=item.requirement_title if item else None,
        title=defect.title,
        description=defect.description or "",
        defect_type=defect.defect_type,
        severity=defect.severity,
        defect_status=defect.defect_status,
        assignee_id=defect.assignee_id,
        assignee_name=assignee_name,
        reporter_id=defect.reporter_id,
        reporter_name=reporter_name,
        screenshots=defect.screenshots,
        reproduce_steps=defect.reproduce_steps,
        expected_result=defect.expected_result,
        actual_result=defect.actual_result,
        feishu_ticket_url=defect.feishu_ticket_url,
        created_at=defect.created_at,
        updated_at=defect.updated_at,
    )


@router.post("/{project_id}/defects", response_model=DefectResponse, summary="快捷提交缺陷")
async def create_defect(
        project_id: int,
        request: DefectCreateRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """测试人员快捷提交缺陷单"""
    project, current_user = project_user

    # 验证排期条目
    item = await ScheduleItem.get_or_none(id=request.schedule_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="排期条目不存在")

    iteration = await TestIteration.get_or_none(id=item.iteration_id, project_id=project_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="排期条目不属于本项目")

    # 验证经办人（如果指定）
    if request.assignee_id:
        assignee = await User.get_or_none(id=request.assignee_id)
        if not assignee:
            raise HTTPException(status_code=404, detail="指定的经办人不存在")

    defect = await Defect.create(
        schedule_item_id=request.schedule_item_id,
        title=request.title,
        description=request.description or "",
        defect_type=request.defect_type,
        severity=request.severity,
        assignee_id=request.assignee_id,
        reporter_id=current_user.id,
        reproduce_steps=request.reproduce_steps,
        expected_result=request.expected_result,
        actual_result=request.actual_result,
    )

    return await _build_defect_response(defect)


@router.get("/{project_id}/defects", response_model=DefectListResponse, summary="获取缺陷列表")
async def get_defects(
        project_id: int,
        schedule_item_id: Optional[int] = Query(None, description="按排期条目过滤"),
        iteration_id: Optional[int] = Query(None, description="按迭代过滤"),
        defect_status: Optional[str] = Query(None, description="按状态过滤"),
        severity: Optional[str] = Query(None, description="按严重程度过滤"),
        reporter_id: Optional[int] = Query(None, description="按报告人过滤"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取缺陷列表"""
    project, current_user = project_user

    # 获取本项目的排期条目IDs
    if schedule_item_id:
        item_ids = [schedule_item_id]
    elif iteration_id:
        items = await ScheduleItem.filter(
            iteration_id=iteration_id, iteration__project_id=project_id
        ).values_list('id', flat=True)
        item_ids = list(items)
    else:
        iterations = await TestIteration.filter(project_id=project_id).values_list('id', flat=True)
        items = await ScheduleItem.filter(iteration_id__in=list(iterations)).values_list('id', flat=True)
        item_ids = list(items)

    if not item_ids:
        return DefectListResponse(defects=[], total=0)

    filters = {"schedule_item_id__in": item_ids}
    if defect_status:
        filters["defect_status"] = defect_status
    if severity:
        filters["severity"] = severity
    if reporter_id:
        filters["reporter_id"] = reporter_id

    defects = await Defect.filter(**filters).order_by("-created_at").all()

    result = []
    for d in defects:
        result.append(await _build_defect_response(d))

    return DefectListResponse(defects=result, total=len(result))


# 注意: 固定路径路由 (stats) 需要放在参数路由 ({defect_id}) 之前
@router.get("/{project_id}/defects/stats", response_model=DefectStatsResponse,
            summary="获取缺陷统计")
async def get_defect_stats(
        project_id: int,
        schedule_item_id: int = Query(..., description="排期条目ID"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """获取某个排期条目的缺陷统计数据"""
    project, current_user = project_user

    defects = await Defect.filter(schedule_item_id=schedule_item_id).all()

    stats = {
        "total": len(defects),
        "open": 0, "fixing": 0, "fixed": 0,
        "verified": 0, "closed": 0, "rejected": 0,
        "by_severity": {}, "by_type": {},
    }

    for d in defects:
        if d.defect_status in stats:
            stats[d.defect_status] += 1
        sev = d.severity or "P2"
        stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
        dt = d.defect_type or "functional"
        stats["by_type"][dt] = stats["by_type"].get(dt, 0) + 1

    return DefectStatsResponse(**stats)


@router.put("/{project_id}/defects/{defect_id}", response_model=DefectResponse, summary="更新缺陷")
async def update_defect(
        project_id: int,
        defect_id: int,
        request: DefectUpdateRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """更新缺陷单信息"""
    project, current_user = project_user

    defect = await Defect.get_or_none(id=defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="缺陷不存在")

    update_data = request.dict(exclude_unset=True)
    if update_data:
        await defect.update_from_dict(update_data)
        await defect.save()

    return await _build_defect_response(defect)


@router.delete("/{project_id}/defects/{defect_id}", summary="删除缺陷")
async def delete_defect(
        project_id: int,
        defect_id: int,
        project_user: tuple = Depends(verify_schedule_access)
):
    """删除缺陷单"""
    project, current_user = project_user

    defect = await Defect.get_or_none(id=defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="缺陷不存在")

    # 只有报告人或管理员可以删除
    if defect.reporter_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有报告人或管理员可以删除")

    await defect.delete()
    return {"message": "缺陷已删除"}


# ==================== 飞书集成 API ====================

@router.get("/{project_id}/feishu/verify", summary="验证飞书应用连接")
async def verify_feishu_connection(
        project_id: int,
        project_user: tuple = Depends(verify_schedule_access)
):
    """验证飞书开放平台和飞书项目 MCP 连接是否有效"""
    from utils.feishu_client import verify_connection, verify_mcp_connection

    project, current_user = project_user
    open_result = await verify_connection()
    mcp_result = await verify_mcp_connection(user_key=current_user.feishu_user_key or "")

    return {
        "open_platform": open_result,
        "project_mcp": mcp_result,
        "success": open_result.get("success") or mcp_result.get("success"),
        "has_user_key": bool(current_user.feishu_user_key),
    }


@router.post("/{project_id}/defects/{defect_id}/sync-to-feishu", summary="同步缺陷到飞书项目")
async def sync_defect_to_feishu(
        project_id: int,
        defect_id: int,
        project_user: tuple = Depends(verify_schedule_access)
):
    """
    将系统中的缺陷单同步到飞书项目（创建 issue）
    同时通过 Webhook 通知对应需求群
    注意: 飞书项目 API 目前不支持自动关联 issue 到 story，
    创建后的 issue 需要用户在飞书项目中手动关联需求。
    """
    project, current_user = project_user

    defect = await Defect.get_or_none(id=defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="缺陷不存在")

    # 如果已经同步过，返回已有链接
    if defect.feishu_ticket_url:
        return {
            "success": True,
            "defect_id": defect.id,
            "feishu_issue_url": defect.feishu_ticket_url,
            "message": "该缺陷已同步到飞书项目",
            "already_synced": True,
        }

    item = await ScheduleItem.get_or_none(id=defect.schedule_item_id)

    severity_map = {"P0": "阻塞", "P1": "严重", "P2": "一般", "P3": "轻微"}
    feishu_issue_url = None
    feishu_issue_id = None

    # 1. 尝试在飞书项目中创建 issue
    try:
        from utils.feishu_client import create_issue_in_project, build_feishu_issue_url, parse_feishu_project_url

        # 构建缺陷描述
        desc_parts = []
        if item:
            desc_parts.append(f"关联需求: {item.requirement_title}")
            if item.ticket_url:
                desc_parts.append(f"需求链接: {item.ticket_url}")
        if defect.description:
            desc_parts.append(f"\n{defect.description}")
        if defect.reproduce_steps:
            desc_parts.append(f"\n复现步骤:\n{defect.reproduce_steps}")
        if defect.expected_result:
            desc_parts.append(f"\n预期结果: {defect.expected_result}")
        if defect.actual_result:
            desc_parts.append(f"\n实际结果: {defect.actual_result}")
        description = "\n".join(desc_parts) if desc_parts else defect.title

        # 创建飞书项目 issue（使用当前用户的飞书UserKey）
        result = await create_issue_in_project(
            name=f"[{defect.severity}] {defect.title}",
            description=description,
            user_key=current_user.feishu_user_key,
        )

        # 检查返回结果（飞书项目 API 错误在 error 字段，成功在 data 字段）
        if not result.get("error"):
            new_id = result.get("data", {}).get("id") or result.get("data", {}).get("work_item_id")
            if new_id:
                feishu_issue_id = new_id
                feishu_issue_url = build_feishu_issue_url(new_id)
                defect.feishu_ticket_id = str(new_id)
                defect.feishu_ticket_url = feishu_issue_url
                await defect.save()
                logger.info(f"缺陷 {defect.id} 已同步到飞书项目 issue {new_id}")
        else:
            err_msg = result.get("error", {}).get("message", "未知错误")
            logger.warning(f"飞书项目创建 issue 失败: {err_msg}")

    except Exception as e:
        logger.warning(f"同步到飞书项目失败（将继续尝试 Webhook 通知）: {e}")

    # 2. 通过 Webhook 发送缺陷通知到对应需求群
    webhooks = await FeishuWebhook.filter(project_id=project_id, is_active=True).all()
    sent_count = 0

    for wh in webhooks:
        should_send = False
        linked_ids = wh.linked_schedule_item_ids or []
        if not isinstance(linked_ids, list):
            linked_ids = []
        if not linked_ids:
            should_send = True  # 全局群
        elif item and item.id in linked_ids:
            should_send = True  # 需求匹配

        if should_send:
            card = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": f"🐛 新缺陷 — {defect.title}"},
                        "template": "red"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": (
                                    f"**需求**: {item.requirement_title if item else '未知'}\n"
                                    f"**严重程度**: {severity_map.get(defect.severity, defect.severity)}\n"
                                    f"**缺陷描述**: {defect.description or '无'}"
                                )
                            }
                        },
                    ]
                }
            }
            if defect.reproduce_steps:
                card["card"]["elements"].append({
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**复现步骤**:\n{defect.reproduce_steps}"}
                })
            if feishu_issue_url:
                card["card"]["elements"].append({"tag": "hr"})
                card["card"]["elements"].append({
                    "tag": "action",
                    "actions": [{
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看飞书缺陷单"},
                        "type": "primary",
                        "url": feishu_issue_url,
                    }]
                })

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(wh.webhook_url, json=card)
                    if resp.status_code == 200:
                        sent_count += 1
            except Exception as e:
                logger.warning(f"缺陷通知到飞书群 {wh.name} 失败: {e}")

    return {
        "success": True,
        "defect_id": defect.id,
        "feishu_issue_url": feishu_issue_url,
        "feishu_issue_id": feishu_issue_id,
        "sent_to_groups": sent_count,
        "message": (
            f"缺陷已同步到飞书项目" + (f"，并通知 {sent_count} 个需求群" if sent_count > 0 else "")
            if feishu_issue_url
            else f"缺陷已通知 {sent_count} 个需求群" if sent_count > 0
            else "同步完成，但未匹配到需求群"
        ),
    }


@router.get("/{project_id}/feishu/story-issues", summary="获取飞书项目需求下的缺陷列表")
async def get_feishu_story_issues(
        project_id: int,
        ticket_url: str = Query(..., description="飞书项目需求链接"),
        project_user: tuple = Depends(verify_schedule_access)
):
    """
    根据飞书项目需求链接，获取该需求下关联的缺陷(issue)列表
    用于同步进度时自动采集 Bug 数据
    """
    from utils.feishu_client import parse_feishu_project_url, get_story_related_issues

    project, current_user = project_user

    parsed = parse_feishu_project_url(ticket_url)
    if not parsed:
        raise HTTPException(status_code=400, detail="无法解析飞书项目链接，请确认格式正确")

    if parsed["work_item_type"] != "story":
        raise HTTPException(status_code=400, detail="请提供需求(story)链接")

    try:
        result = await get_story_related_issues(
            story_id=parsed["work_item_id"],
            project_key=parsed["project_key"],
            user_key=current_user.feishu_user_key,
        )
        # 飞书项目 API 返回在 data 字段
        relations = result.get("data", [])
        # 过滤出 issue 类型的关联
        issues = []
        if isinstance(relations, list):
            for r in relations:
                if r.get("work_item_type_key") == "issue":
                    issues.extend(r.get("work_items", []))
        elif isinstance(relations, dict):
            issues = relations.get("work_items", [])

        return {
            "success": True,
            "story_id": parsed["work_item_id"],
            "project_key": parsed["project_key"],
            "issues": issues,
            "total": len(issues),
        }
    except Exception as e:
        logger.error(f"获取飞书项目缺陷列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/{project_id}/defects/ai-expand-preview", summary="AI扩写缺陷描述（预览，不创建缺陷）")
async def ai_expand_defect_preview(
        project_id: int,
        request: DefectCreateRequest,
        project_user: tuple = Depends(verify_schedule_access)
):
    """
    使用AI扩写缺陷描述，生成规范化的Bug描述。
    此接口不创建缺陷，仅返回AI扩写后的描述内容，用户确认后再提交。
    """
    project, current_user = project_user

    # 获取需求名称用于上下文
    item = await ScheduleItem.get_or_none(id=request.schedule_item_id)

    try:
        from config.settings import llm

        prompt = f"""你是一个资深QA工程师，请根据以下简要信息，扩写成一份规范化的缺陷描述。

需求名称: {item.requirement_title if item else '未知'}
缺陷标题: {request.title}
缺陷描述: {request.description or '无'}
缺陷类型: {request.defect_type}
严重程度: {request.severity}
复现步骤: {request.reproduce_steps or '无'}
预期结果: {request.expected_result or '无'}
实际结果: {request.actual_result or '无'}

请按以下格式输出（使用Markdown）:

**缺陷描述**
（2-3句话的详细描述）

**复现步骤**
1. 步骤1
2. 步骤2
...

**预期结果**
（描述正确行为）

**实际结果**
（描述当前错误行为）

**影响范围**
（分析影响范围）

要求：简洁专业，不要多余的客套话。"""

        result = llm.invoke(prompt)
        ai_content = result.content

        return {
            "ai_expanded_description": ai_content,
        }

    except Exception as e:
        logger.error(f"AI缺陷扩写失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI缺陷扩写失败: {str(e)}")


@router.post("/{project_id}/defects/{defect_id}/ai-expand", summary="AI扩写已有缺陷描述")
async def ai_expand_defect(
        project_id: int,
        defect_id: int,
        project_user: tuple = Depends(verify_schedule_access)
):
    """使用AI扩写已有缺陷的描述，生成规范化的Bug描述"""
    project, current_user = project_user

    defect = await Defect.get_or_none(id=defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="缺陷不存在")

    item = await ScheduleItem.get_or_none(id=defect.schedule_item_id)

    try:
        from config.settings import llm

        prompt = f"""你是一个资深QA工程师，请根据以下简要信息，扩写成一份规范化的缺陷描述。

需求名称: {item.requirement_title if item else '未知'}
缺陷标题: {defect.title}
缺陷描述: {defect.description or '无'}
缺陷类型: {defect.defect_type}
严重程度: {defect.severity}
复现步骤: {defect.reproduce_steps or '无'}
预期结果: {defect.expected_result or '无'}
实际结果: {defect.actual_result or '无'}

请按以下格式输出（使用Markdown）:

**缺陷描述**
（2-3句话的详细描述）

**复现步骤**
1. 步骤1
2. 步骤2
...

**预期结果**
（描述正确行为）

**实际结果**
（描述当前错误行为）

**影响范围**
（分析影响范围）

要求：简洁专业，不要多余的客套话。"""

        result = llm.invoke(prompt)
        ai_content = result.content

        return {
            "defect_id": defect.id,
            "ai_expanded_description": ai_content,
        }

    except Exception as e:
        logger.error(f"AI缺陷扩写失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI缺陷扩写失败: {str(e)}")
