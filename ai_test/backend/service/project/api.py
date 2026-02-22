"""项目模块API路由"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from tortoise.transactions import in_transaction
from tortoise.exceptions import IntegrityError
from .models import Project, ProjectMember, ProjectModule, BusinessLineMember
from .schemas import (
    ProjectCreateRequest, ProjectResponse, ProjectListResponse, ProjectMemberAddRequest,
    ProjectMemberStatusUpdateRequest, ProjectMemberListResponse, ProjectMemberRoleUpdateRequest, ProjectUpdateRequest,
    ProjectDetailResponse, ProjectModuleCreateRequest, ProjectModuleUpdateRequest, ProjectModuleResponse,
    ProjectModuleListResponse, DashboardStatsResponse, DashboardTrendPoint, DashboardActivityItem,
    DashboardCaseTrendPoint, DashboardTaskRunItem, DashboardTaskSummary,
    BusinessLineMemberInfo, BusinessLineMemberAddRequest, BusinessLineMemberUpdateRequest, UserBusinessLineInfo
)
from service.user.models import User
from utils.auth import get_current_user
from utils.permissions import verify_admin_or_project_member, verify_admin_or_project_owner, verify_admin_or_project_editor
from service.api_test.models import ApiInterface, ApiTestCase
from service.functional_test.models import FunctionalCase, RequirementDoc
from service.test_management.models import TestSuite, TestTask
from service.test_execution.models import ApiCaseRun, TestSuiteRun, TestTaskRun
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["项目管理"])


@router.get("/list", response_model=ProjectListResponse, summary="获取项目列表")
async def get_project_list(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        project_name: Optional[str] = Query(None, description="项目名称模糊查询"),
        current_user: User = Depends(get_current_user)
):
    """
    获取项目列表接口
    - 普通用户只能查看自己参与的项目
    - 管理员可以查看所有项目
    - 支持分页查询
    - 支持项目名称模糊搜索
    """
    try:
        offset = (page - 1) * page_size

        # 根据用户权限构建查询条件
        if current_user.is_superuser:
            # 管理员可以查看所有项目
            query = Project.all()
        else:
            # 普通用户只能查看自己参与的项目
            # 通过项目成员表关联查询
            project_ids = await ProjectMember.filter(user_id=current_user.id).values_list('project_id', flat=True)
            query = Project.filter(id__in=project_ids)

        # 项目名称模糊搜索
        if project_name:
            query = query.filter(name__icontains=project_name)

        # 获取总数
        total = await query.count()

        # 分页查询
        projects = await query.offset(offset).limit(page_size)
        # 构建响应数据
        project_list = []
        for project in projects:
            # 查询项目负责人名称
            user = await User.get_or_none(id=project.owner_id)
            owner_name = user.real_name
            # 统计项目的功能用例数
            # 统计项目的api用例数
            project = ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                owner_id=project.owner_id,
                created_at=project.created_at,
                updated_at=project.updated_at
            )
            project_list.append(project)
        return ProjectListResponse(
            projects=project_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目列表失败，请稍后重试"
        )


@router.post("/create", response_model=ProjectResponse, summary="创建项目")
async def create_project(
        project_data: ProjectCreateRequest,
        current_user: User = Depends(get_current_user)
):
    """
    创建项目接口
    - 需要登录后才能创建项目
    - 项目负责人默认为当前创建的用户
    - 项目名称和描述不能为空
    - 使用数据库事务确保数据一致性
    """
    try:
        # 使用数据库事务确保数据一致性
        async with in_transaction() as conn:
            # 创建项目
            project = await Project.create(
                name=project_data.name,
                description=project_data.description,
                owner_id=current_user.id,
                using_db=conn
            )

            # 创建项目成员记录，项目负责人默认为项目成员
            await ProjectMember.create(
                project_id=project.id,
                user_id=current_user.id,
                role=2,  # 项目创建者默认为负责人角色
                status=1,  # 默认状态为启用
                granted_by=current_user.id,  # 授权人为自己
                using_db=conn
            )

            return ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                owner_id=project.owner_id,
                created_at=project.created_at,
                updated_at=project.updated_at
            )

    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目创建失败，可能存在重复的项目名称"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="项目创建失败，请稍后重试"
        )


@router.delete("/{project_id}", summary="删除项目")
async def delete_project(
        project_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    删除项目接口
    - 只有项目负责人和管理员才能删除项目
    - 删除项目时会同时删除项目中的所有成员
    - 使用数据库事务确保数据一致性
    """
    try:
        project, current_user = project_and_user

        # 使用数据库事务确保数据一致性
        async with in_transaction() as conn:
            # 先删除项目成员
            await ProjectMember.filter(project_id=project_id).using_db(conn).delete()

            # 再删除项目
            await Project.filter(id=project_id).using_db(conn).delete()

        return {"message": "项目删除成功"}

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="项目删除失败，请稍后重试"
        )


@router.put("/{project_id}", response_model=ProjectResponse, summary="修改项目信息")
async def update_project(
        project_id: int,
        project_data: ProjectUpdateRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    修改项目信息接口
    
    权限要求：
    - 只有项目负责人和管理员可以修改项目信息
    
    可修改字段：
    - 项目名称
    - 项目描述
    
    参数：
    - project_id: 项目ID
    - project_data: 项目更新数据（包含名称和描述）
    
    返回：
    - 更新后的项目信息
    """
    try:
        project, current_user = project_and_user

        # 更新项目信息
        project.name = project_data.name
        project.description = project_data.description
        await project.save()

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改项目信息失败，请稍后重试"
        )


@router.post("/{project_id}/members", summary="添加项目成员")
async def add_project_member(
        project_id: int,
        member_data: ProjectMemberAddRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    添加项目成员接口
    - 只有项目负责人和管理员才能添加项目成员
    - 默认成员状态为启用
    - 授权人为进行添加操作的用户
    """
    try:
        project, current_user = project_and_user

        # 检查用户是否存在
        user = await User.get_or_none(id=member_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 检查用户是否已经是项目成员
        existing_member = await ProjectMember.get_or_none(
            project_id=project_id,
            user_id=member_data.user_id
        )
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已经是项目成员"
            )

        # 角色验证：添加成员时不能设置为负责人角色（角色2）
        if member_data.role == 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="添加成员时不能设置为负责人角色，每个项目只有一个负责人"
            )

        # 创建项目成员记录
        project_member = await ProjectMember.create(
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role,
            status=1,  # 默认状态为启用
            granted_by=current_user.id  # 授权人为当前用户
        )

        return {
            "message": "项目成员添加成功",
            "member_id": project_member.id,
            "user_id": project_member.user_id,
            "role": project_member.role,
            "status": project_member.status,
            "granted_by": project_member.granted_by
        }

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加项目成员失败，请稍后重试"
        )


@router.delete("/{project_id}/members/{user_id}", summary="移除项目成员")
async def remove_project_member(
        project_id: int,
        user_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    移除项目成员接口
    - 只有项目负责人和管理员才能移除项目成员
    """
    try:
        project, current_user = project_and_user

        # 查询项目成员是否存在
        project_member = await ProjectMember.get_or_none(
            project_id=project_id,
            user_id=user_id
        )
        if not project_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目成员不存在"
            )

        # 删除项目成员
        await project_member.delete()

        return {"message": "项目成员移除成功"}

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="移除项目成员失败，请稍后重试"
        )


@router.put("/{project_id}/members/{user_id}/status", summary="更新项目成员状态")
async def update_project_member_status(
        project_id: int,
        user_id: int,
        request: ProjectMemberStatusUpdateRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    更新项目成员状态接口（禁用/启用）
    - 只有项目负责人和管理员才能更新项目成员状态
    """
    try:
        project, current_user = project_and_user

        # 查询项目成员是否存在
        project_member = await ProjectMember.get_or_none(
            project_id=project_id,
            user_id=user_id
        )
        if not project_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目成员不存在"
            )

        # 更新项目成员状态
        project_member.status = request.status
        await project_member.save()

        status_text = "启用" if request.status == 1 else "禁用"
        return {"message": f"项目成员状态已更新为{status_text}"}

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新项目成员状态失败，请稍后重试"
        )


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse, summary="获取项目成员列表")
async def get_project_members(
        project_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    获取项目成员列表接口
    - 只有项目负责人和管理员才能访问
    """
    try:
        project, current_user = project_and_user

        # 查询项目成员列表
        project_members = await ProjectMember.filter(project_id=project_id).all()

        # 获取所有成员的用户信息
        user_ids = [member.user_id for member in project_members]
        users = await User.filter(id__in=user_ids).all()
        user_dict = {user.id: user for user in users}

        # 角色映射
        role_mapping = {
            0: "只读",
            1: "可操作",
            2: "负责人"
        }

        # 构建响应数据
        members_data = []
        for member in project_members:
            user = user_dict.get(member.user_id)
            if user:
                members_data.append({
                    "id": member.id,
                    "user_id": member.user_id,
                    "username": user.username,
                    "real_name": user.real_name,
                    "role": member.role,
                    "role_name": role_mapping.get(member.role, "未知"),
                    "status": member.status,
                    "created_at": member.created_at
                })

        return ProjectMemberListResponse(members=members_data)

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目成员列表失败，请稍后重试"
        )


@router.get("/{project_id}/detail", response_model=ProjectDetailResponse, summary="获取项目详情")
async def get_project_detail(
        project_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取项目详情接口
    - 只有项目成员才能访问该接口
    - 返回项目基本信息和成员详细信息
    """
    try:
        project, current_user = project_and_user

        # 查询项目成员列表
        project_members = await ProjectMember.filter(project_id=project_id).all()

        # 获取所有成员的用户信息
        user_ids = [member.user_id for member in project_members]
        users = await User.filter(id__in=user_ids).all()
        user_dict = {user.id: user for user in users}

        # 角色映射
        role_mapping = {
            0: "只读",
            1: "可操作",
            2: "负责人"
        }

        # 构建成员数据
        members_data = []
        for member in project_members:
            user = user_dict.get(member.user_id)
            if user:
                members_data.append({
                    "id": member.id,
                    "user_id": member.user_id,
                    "username": user.username,
                    "real_name": user.real_name,
                    "role": member.role,
                    "role_name": role_mapping.get(member.role, "未知"),
                    "status": member.status,
                    "created_at": member.created_at
                })

        # 构建项目详情响应数据
        project_detail = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "members": members_data
        }

        return ProjectDetailResponse(**project_detail)

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目详情失败，请稍后重试"
        )


@router.get("/{project_id}/dashboard", response_model=DashboardStatsResponse, summary="获取项目仪表盘统计")
async def get_project_dashboard(
        project_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    仪表盘统计接口（项目级）
    - 返回接口数量、API用例数、功能用例数、套件数、任务数
    - 近30天执行次数与通过率
    - 近14天趋势与最近活动
    """
    try:
        project, current_user = project_and_user

        # 基础计数
        api_interfaces_count = await ApiInterface.filter(project_id=project_id).count()
        api_cases_count = await ApiTestCase.filter(base_case__interface__project_id=project_id).count()
        # 功能用例通过 requirement -> module -> project 关联过滤
        functional_cases_count = await FunctionalCase.filter(requirement__module__project_id=project_id).count()
        # 项目需求总数
        requirements_count = await RequirementDoc.filter(module__project_id=project_id).count()
        suites_count = await TestSuite.filter(project_id=project_id).count()
        tasks_count = await TestTask.filter(project_id=project_id).count()

        # 近30天执行统计
        now = datetime.utcnow()
        window_30 = now - timedelta(days=30)
        runs_30 = await ApiCaseRun.filter(
            api_case__base_case__interface__project_id=project_id,
            created_at__gte=window_30
        ).all()
        suite_runs_30 = await TestSuiteRun.filter(
            suite__project_id=project_id,
            created_at__gte=window_30
        ).all()
        task_runs_30 = await TestTaskRun.filter(
            task__project_id=project_id,
            created_at__gte=window_30
        ).all()

        executions_30 = len(runs_30) + len(suite_runs_30) + len(task_runs_30)

        # 接口用例运行次数（按状态分类）
        api_run_counts_by_status: dict[str, int] = {}
        for r in runs_30:
            status_val = (getattr(r, "status", None) or "").lower()
            if status_val in ["passed", "ok"]:
                status_key = "success"
            elif status_val in ["success", "failed", "error"]:
                status_key = status_val
            else:
                status_key = "unknown"
            api_run_counts_by_status[status_key] = api_run_counts_by_status.get(status_key, 0) + 1

        # 接口用例运行次数（按类型分类）
        type_values = await ApiCaseRun.filter(
            api_case__base_case__interface__project_id=project_id,
            created_at__gte=window_30
        ).values_list('api_case__type', flat=True)
        api_run_counts_by_type: dict[str, int] = {}
        for t in type_values:
            key = (t or "unknown").lower()
            api_run_counts_by_type[key] = api_run_counts_by_type.get(key, 0) + 1

        # 通过率（按ApiCaseRun简单统计，通过状态可能字段名不同，做兼容）
        passed_30 = 0
        for r in runs_30:
            status_val = getattr(r, "status", None)
            success = False
            if isinstance(status_val, int):
                # 常见：1=成功
                success = (status_val == 1)
            elif isinstance(status_val, str):
                success = status_val.lower() in ["success", "passed", "ok"]
            passed_30 += 1 if success else 0
        success_rate = (passed_30 / len(runs_30) * 100.0) if runs_30 else 0.0

        # 近14天趋势（按天聚合，仅基于 ApiCaseRun 用例运行记录）
        window_14 = now - timedelta(days=14)
        trend_map = {}
        def add_trend(dt: Optional[datetime], category: Optional[str]):
            # 兼容某些历史记录的时间戳可能为 None 的情况
            base_dt = dt or now
            day = base_dt.strftime("%Y-%m-%d")
            if day not in trend_map:
                trend_map[day] = {"runs": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
            trend_map[day]["runs"] += 1
            if category == "passed":
                trend_map[day]["passed"] += 1
            elif category == "failed":
                trend_map[day]["failed"] += 1
            elif category == "errors":
                trend_map[day]["errors"] += 1
            elif category == "skipped":
                trend_map[day]["skipped"] += 1

        for r in await ApiCaseRun.filter(api_case__base_case__interface__project_id=project_id, created_at__gte=window_14).all():
            status_val = getattr(r, "status", None)
            category: Optional[str] = None
            if isinstance(status_val, int):
                # 常见：1=成功，其它视为失败
                category = "passed" if status_val == 1 else "failed"
            elif isinstance(status_val, str):
                low = status_val.lower()
                if low in ["success", "passed", "ok"]:
                    category = "passed"
                elif low in ["failed"]:
                    category = "failed"
                elif low in ["error", "exception"]:
                    category = "errors"
                elif low in ["skipped", "skip"]:
                    category = "skipped"
                else:
                    category = None
            add_trend(getattr(r, "created_at", None), category)

        # 移除套件与任务运行在趋势中的计数，保证执行次数严格来源于用例运行记录

        # 按日期生成列表，保持时间顺序
        trend_points: list[DashboardTrendPoint] = []
        for i in range(14):
            day = (window_14 + timedelta(days=i)).strftime("%Y-%m-%d")
            agg = trend_map.get(day, {"runs": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0})
            trend_points.append(DashboardTrendPoint(
                date=day,
                runs=agg["runs"],
                passed=agg["passed"],
                failed=agg["failed"],
                errors=agg["errors"],
                skipped=agg["skipped"]
            ))

        # 最近7天用例执行趋势（仅按 ApiCaseRun，含通过率）
        window_7 = now - timedelta(days=7)
        case_trend_map: dict[str, dict[str, int]] = {}
        runs_7 = await ApiCaseRun.filter(
            api_case__base_case__interface__project_id=project_id,
            created_at__gte=window_7
        ).all()
        for r in runs_7:
            base_dt = getattr(r, "created_at", None) or now
            day = base_dt.strftime("%Y-%m-%d")
            if day not in case_trend_map:
                case_trend_map[day] = {"executed": 0, "success": 0}
            case_trend_map[day]["executed"] += 1
            status_val = (getattr(r, "status", None) or "").lower()
            is_success = status_val in ["success", "passed", "ok"]
            if is_success:
                case_trend_map[day]["success"] += 1

        case_trend_7d: list[DashboardCaseTrendPoint] = []
        for i in range(7):
            day = (window_7 + timedelta(days=i)).strftime("%Y-%m-%d")
            agg = case_trend_map.get(day, {"executed": 0, "success": 0})
            executed = agg["executed"]
            success = agg["success"]
            rate = (success / executed * 100.0) if executed else 0.0
            case_trend_7d.append(DashboardCaseTrendPoint(date=day, executed=executed, success=success, pass_rate=round(rate, 2)))

        # 最近活动（整合最近的执行记录）
        recent_items: list[DashboardActivityItem] = []
        recent_case_runs = await ApiCaseRun.filter(api_case__base_case__interface__project_id=project_id).order_by("-created_at").limit(5)
        for r in recent_case_runs:
            ts = getattr(r, "created_at", None) or now
            status_val = getattr(r, "status", "")
            content = f"API用例执行 #{getattr(r, 'id', '')} 状态: {status_val}"
            recent_items.append(DashboardActivityItem(id=str(getattr(r, "id", "")), content=content, timestamp=ts.strftime("%Y-%m-%d %H:%M"), type="info"))

        recent_suite_runs = await TestSuiteRun.filter(suite__project_id=project_id).order_by("-created_at").limit(3)
        for r in recent_suite_runs:
            ts = getattr(r, "created_at", None) or now
            content = f"套件执行 #{getattr(r, 'id', '')}"
            recent_items.append(DashboardActivityItem(id=str(getattr(r, "id", "")), content=content, timestamp=ts.strftime("%Y-%m-%d %H:%M"), type="primary"))

        recent_task_runs = await TestTaskRun.filter(task__project_id=project_id).order_by("-created_at").limit(2)
        for r in recent_task_runs:
            ts = getattr(r, "created_at", None) or now
            content = f"任务执行 #{getattr(r, 'id', '')}"
            recent_items.append(DashboardActivityItem(id=str(getattr(r, "id", "")), content=content, timestamp=ts.strftime("%Y-%m-%d %H:%M"), type="success"))

        # 最近30次任务执行记录（用于任务面板）
        recent_task_runs_full = await TestTaskRun.filter(task__project_id=project_id).order_by("-created_at").limit(30)
        recent_task_runs_items: list[DashboardTaskRunItem] = []
        for tr in recent_task_runs_full:
            ts = getattr(tr, "created_at", None) or now
            recent_task_runs_items.append(
                DashboardTaskRunItem(
                    id=getattr(tr, "id", 0),
                    status=getattr(tr, "status", None),
                    total_suites=getattr(tr, "total_suites", None),
                    total_cases=getattr(tr, "total_cases", None),
                    passed_cases=getattr(tr, "passed_cases", None),
                    failed_cases=getattr(tr, "failed_cases", None),
                    skipped_cases=getattr(tr, "skipped_cases", None),
                    duration=getattr(tr, "duration", None),
                    timestamp=ts.strftime("%Y-%m-%d %H:%M")
                )
            )

        # 最近一次任务执行摘要
        last_task_run = await TestTaskRun.filter(task__project_id=project_id).order_by("-created_at").first()
        last_task_summary: Optional[DashboardTaskSummary] = None
        if last_task_run:
            ts = getattr(last_task_run, "created_at", None) or now
            last_task_summary = DashboardTaskSummary(
                id=getattr(last_task_run, "id", 0),
                status=getattr(last_task_run, "status", None),
                total_suites=getattr(last_task_run, "total_suites", None),
                total_cases=getattr(last_task_run, "total_cases", None),
                passed_cases=getattr(last_task_run, "passed_cases", None),
                failed_cases=getattr(last_task_run, "failed_cases", None),
                skipped_cases=getattr(last_task_run, "skipped_cases", None),
                duration=getattr(last_task_run, "duration", None),
                timestamp=ts.strftime("%Y-%m-%d %H:%M")
            )

        modules_count = await ProjectModule.filter(project_id=project_id).count()

        return DashboardStatsResponse(
            project_id=project_id,
            modules=modules_count,
            api_interfaces=api_interfaces_count,
            api_cases=api_cases_count,
            functional_cases=functional_cases_count,
            requirements=requirements_count,
            suites=suites_count,
            tasks=tasks_count,
            executions=executions_30,
            success_rate=round(success_rate, 2),
            trend=trend_points,
            activities=recent_items,
            api_run_counts_by_status=api_run_counts_by_status,
            api_run_counts_by_type=api_run_counts_by_type,
            case_trend_7d=case_trend_7d,
            recent_task_runs=recent_task_runs_items,
            last_task_summary=last_task_summary
        )

    except HTTPException:
        raise
    except Exception as e:
        raise e
        logger.exception("获取项目仪表盘统计失败: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取项目仪表盘统计失败，请稍后重试"
        )


@router.put("/{project_id}/members/{user_id}/role", summary="修改项目成员角色")
async def update_project_member_role(
        project_id: int,
        user_id: int,
        request: ProjectMemberRoleUpdateRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    修改项目成员角色
    
    权限要求：
    - 只有项目负责人和管理员可以修改成员角色
    
    参数：
    - project_id: 项目ID
    - user_id: 成员用户ID
    - request: 角色更新请求（包含新的角色值）
    
    返回：
    - 成功消息和更新后的成员信息
    """
    try:
        project, current_user = project_and_user

        # 查询项目成员是否存在
        member = await ProjectMember.get_or_none(project_id=project_id, user_id=user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目成员不存在"
            )

        # 不能修改项目负责人的角色
        if member.user_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改项目负责人的角色"
            )

        # 角色验证：只有管理员才能将成员角色修改为负责人（角色2）
        if request.role == 2 and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员才能设置负责人角色"
            )

        # 如果要设置为负责人角色，需要检查项目是否已有负责人
        if request.role == 2:
            # 检查是否已有其他负责人（除了项目创建者）
            existing_owner_member = await ProjectMember.get_or_none(
                project_id=project_id,
                role=2
            )
            if existing_owner_member and existing_owner_member.user_id != project.owner_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="项目已有负责人，每个项目只能有一个负责人"
                )

        # 使用数据库事务确保数据一致性
        async with in_transaction():
            # 如果设置新的负责人，需要更新项目的owner_id
            if request.role == 2:
                project.owner_id = user_id
                await project.save()

            # 更新成员角色
            member.role = request.role
            await member.save()

        # 获取用户信息
        user = await User.get_or_none(id=user_id)
        username = user.username if user else "未知用户"

        # 角色映射
        role_mapping = {0: "只读", 1: "可操作", 2: "负责人"}

        return {
            "message": "成员角色修改成功",
            "member": {
                "id": member.id,
                "user_id": member.user_id,
                "username": username,
                "role": member.role,
                "role_name": role_mapping.get(member.role, "未知"),
                "status": member.status
            }
        }

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改成员角色失败，请稍后重试"
        )


# 项目模块管理接口

@router.get("/{project_id}/modules", response_model=ProjectModuleListResponse, summary="获取业务线树形列表")
async def get_project_modules(
        project_id: int,
        current_user: User = Depends(get_current_user)
):
    """获取业务线列表（树结构，含成员信息）- 所有登录用户可访问"""
    try:
        project = await Project.get_or_none(id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        modules = await ProjectModule.filter(project_id=project_id).order_by("sort_order", "id")

        # 获取所有一级业务线ID
        top_ids = [m.id for m in modules if m.parent_id is None]

        # 获取所有一级业务线的成员
        all_blm = await BusinessLineMember.filter(module_id__in=top_ids)
        user_ids = list(set(b.user_id for b in all_blm))
        users_map = {}
        if user_ids:
            users = await User.filter(id__in=user_ids)
            users_map = {u.id: u for u in users}

        # 构建成员映射 {module_id: [BusinessLineMemberInfo]}
        members_map = {}
        for b in all_blm:
            u = users_map.get(b.user_id)
            if u:
                info = BusinessLineMemberInfo(
                    id=b.id, user_id=b.user_id,
                    username=u.username,
                    real_name=u.real_name,
                    role=b.role
                )
                members_map.setdefault(b.module_id, []).append(info)

        # 构建树
        children_map = {}
        for m in modules:
            if m.parent_id is not None:
                children_map.setdefault(m.parent_id, []).append(m)

        tree = []
        for m in modules:
            if m.parent_id is not None:
                continue  # 跳过子节点，在父节点中组装
            child_list = []
            for c in children_map.get(m.id, []):
                child_list.append(ProjectModuleResponse(
                    id=c.id, name=c.name, description=c.description,
                    project_id=c.project_id, parent_id=c.parent_id,
                    children=[], members=[],
                    created_at=c.created_at, updated_at=c.updated_at
                ))
            tree.append(ProjectModuleResponse(
                id=m.id, name=m.name, description=m.description,
                project_id=m.project_id, parent_id=None,
                children=child_list,
                members=members_map.get(m.id, []),
                created_at=m.created_at, updated_at=m.updated_at
            ))

        return ProjectModuleListResponse(datas=tree)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取业务线列表失败: %s", e)
        raise HTTPException(status_code=500, detail="获取业务线列表失败")


@router.post("/{project_id}/modules", summary="创建业务线/子模块")
async def create_project_module(
        project_id: int,
        module_data: ProjectModuleCreateRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """创建业务线或子模块（仅管理员/项目负责人）"""
    try:
        project, current_user = project_and_user

        # 如果有父级，校验父级存在且属于同一项目
        if module_data.parent_id:
            parent = await ProjectModule.get_or_none(id=module_data.parent_id, project_id=project_id)
            if not parent:
                raise HTTPException(status_code=404, detail="父级业务线不存在")
            if parent.parent_id is not None:
                raise HTTPException(status_code=400, detail="只支持二级层级，不能在子模块下创建")

        # 同级重名校验
        existing = await ProjectModule.get_or_none(
            project_id=project_id, name=module_data.name, parent_id=module_data.parent_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="同级下已存在同名业务线")

        module = await ProjectModule.create(
            name=module_data.name,
            description=module_data.description,
            project_id=project_id,
            parent_id=module_data.parent_id
        )

        return {
            "id": module.id, "name": module.name, "description": module.description,
            "project_id": module.project_id, "parent_id": module.parent_id,
            "created_at": module.created_at, "updated_at": module.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("创建业务线失败: %s", e)
        raise HTTPException(status_code=500, detail="创建业务线失败")


@router.put("/{project_id}/modules/{module_id}", summary="更新业务线/子模块")
async def update_project_module(
        project_id: int,
        module_id: int,
        module_data: ProjectModuleUpdateRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """更新业务线名称和描述（仅管理员/项目负责人）"""
    try:
        project, current_user = project_and_user
        module = await ProjectModule.get_or_none(id=module_id, project_id=project_id)
        if not module:
            raise HTTPException(status_code=404, detail="业务线不存在")

        if module_data.name and module_data.name != module.name:
            existing = await ProjectModule.get_or_none(
                project_id=project_id, name=module_data.name, parent_id=module.parent_id
            )
            if existing:
                raise HTTPException(status_code=400, detail="同级下已存在同名业务线")

        if module_data.name is not None:
            module.name = module_data.name
        if module_data.description is not None:
            module.description = module_data.description
        await module.save()

        return {
            "id": module.id, "name": module.name, "description": module.description,
            "project_id": module.project_id, "parent_id": module.parent_id,
            "created_at": module.created_at, "updated_at": module.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("更新业务线失败: %s", e)
        raise HTTPException(status_code=500, detail="更新业务线失败")


@router.delete("/{project_id}/modules/{module_id}", summary="删除业务线/子模块")
async def delete_project_module(
        project_id: int,
        module_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """删除业务线（连带子模块和成员绑定）（仅管理员/项目负责人）"""
    try:
        project, current_user = project_and_user
        module = await ProjectModule.get_or_none(id=module_id, project_id=project_id)
        if not module:
            raise HTTPException(status_code=404, detail="业务线不存在")

        # 如果是一级业务线，删除所有子模块和成员
        if module.parent_id is None:
            await ProjectModule.filter(parent_id=module_id).delete()
            await BusinessLineMember.filter(module_id=module_id).delete()

        await module.delete()
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("删除业务线失败: %s", e)
        raise HTTPException(status_code=500, detail="删除业务线失败")


# ==================== 业务线成员管理 ====================

@router.post("/{project_id}/modules/{module_id}/members", summary="添加业务线成员")
async def add_business_line_member(
        project_id: int,
        module_id: int,
        data: BusinessLineMemberAddRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """给一级业务线添加成员（仅管理员/项目负责人）"""
    try:
        project, current_user = project_and_user
        module = await ProjectModule.get_or_none(id=module_id, project_id=project_id)
        if not module:
            raise HTTPException(status_code=404, detail="业务线不存在")
        if module.parent_id is not None:
            raise HTTPException(status_code=400, detail="只能在一级业务线下添加成员")

        # 校验用户存在
        user = await User.get_or_none(id=data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 去重
        existing = await BusinessLineMember.get_or_none(module_id=module_id, user_id=data.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="该用户已在此业务线中")

        blm = await BusinessLineMember.create(
            module_id=module_id, user_id=data.user_id, role=data.role
        )
        return {
            "id": blm.id, "module_id": blm.module_id, "user_id": blm.user_id,
            "role": blm.role, "username": user.username, "real_name": user.real_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("添加业务线成员失败: %s", e)
        raise HTTPException(status_code=500, detail="添加业务线成员失败")


@router.put("/{project_id}/modules/{module_id}/members/{member_id}", summary="更新业务线成员角色")
async def update_business_line_member(
        project_id: int,
        module_id: int,
        member_id: int,
        data: BusinessLineMemberUpdateRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """更新业务线成员角色（仅管理员/项目负责人）"""
    try:
        project, current_user = project_and_user
        blm = await BusinessLineMember.get_or_none(id=member_id, module_id=module_id)
        if not blm:
            raise HTTPException(status_code=404, detail="成员记录不存在")
        blm.role = data.role
        await blm.save()
        return {"message": "角色更新成功", "id": blm.id, "role": blm.role}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("更新成员角色失败: %s", e)
        raise HTTPException(status_code=500, detail="更新成员角色失败")


@router.delete("/{project_id}/modules/{module_id}/members/{member_id}", summary="移除业务线成员")
async def remove_business_line_member(
        project_id: int,
        module_id: int,
        member_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """移除业务线成员（仅管理员/项目负责人）"""
    try:
        project, current_user = project_and_user
        blm = await BusinessLineMember.get_or_none(id=member_id, module_id=module_id)
        if not blm:
            raise HTTPException(status_code=404, detail="成员记录不存在")
        await blm.delete()
        return {"message": "移除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("移除成员失败: %s", e)
        raise HTTPException(status_code=500, detail="移除成员失败")


@router.get("/{project_id}/my-business-lines", summary="获取当前用户所属业务线")
async def get_my_business_lines(
        project_id: int,
        current_user: User = Depends(get_current_user)
):
    """获取当前登录用户在该项目下所属的所有业务线"""
    try:
        blm_list = await BusinessLineMember.filter(user_id=current_user.id)
        module_ids = [b.module_id for b in blm_list]
        if not module_ids:
            return {"business_lines": [], "is_admin": current_user.is_superuser}

        modules = await ProjectModule.filter(id__in=module_ids, project_id=project_id)
        module_map = {m.id: m for m in modules}

        result = []
        for b in blm_list:
            m = module_map.get(b.module_id)
            if m:
                result.append(UserBusinessLineInfo(
                    module_id=m.id, module_name=m.name, role=b.role
                ))

        return {"business_lines": result, "is_admin": current_user.is_superuser}
    except Exception as e:
        logger.exception("获取用户业务线失败: %s", e)
        raise HTTPException(status_code=500, detail="获取用户业务线信息失败")
