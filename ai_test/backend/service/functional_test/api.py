"""
功能测试模块API路由
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, Response
from typing import Optional
from tortoise.transactions import in_transaction
import json
import re
import asyncio
import logging
import traceback
from .models import RequirementDoc, FunctionalCase, FunctionalCaseSet
from .schemas import (RequirementCreateRequest, RequirementResponse, RequirementUpdateRequest, RequirementDetailItem,
                      RequirementDetailListResponse, RequirementReviewRequest,
    FunctionalCaseSimple, FunctionalCaseListResponse, FunctionalCaseCreateRequest,
    FunctionalCaseUpdateRequest, FunctionalCaseResponse, FunctionalCaseReviewRequest,
    FunctionalCaseSetSimple, FunctionalCaseSetListResponse, FunctionalCaseSetDetailResponse,
    FunctionalCaseSetCreateRequest, FunctionalCaseSetUpdateRequest, ScenarioCaseGroup)
from service.user.models import User
from service.project.models import Project, ProjectModule
from utils.permissions import verify_admin_or_project_owner, verify_admin_or_project_member, \
    verify_admin_or_project_editor
from workflow.case_generator_workflow import GeneratorTestCaseWorkflow

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/requirements", response_model=RequirementResponse, summary="添加需求")
async def create_requirement(
        requirement_data: RequirementCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    添加需求接口
    """
    project, current_user = project_user

    try:
        if requirement_data.module_id:
            module = await ProjectModule.get_or_none(id=requirement_data.module_id)
            if not module:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的项目模块不存在"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模块ID不能为空"
            )

        # 如果传入了 schedule_item_id，验证排期条目是否存在
        schedule_item_id = getattr(requirement_data, 'schedule_item_id', None)
        if schedule_item_id:
            from service.schedule.models import ScheduleItem
            si = await ScheduleItem.get_or_none(id=schedule_item_id)
            if not si:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="关联的排期需求不存在"
                )

        async with in_transaction() as conn:
            requirement = await RequirementDoc.create(
                module_id=requirement_data.module_id,
                title=requirement_data.title,
                doc_no=requirement_data.doc_no,
                description=requirement_data.description,
                priority=requirement_data.priority,
                schedule_item_id=schedule_item_id,
                creator_id=current_user.id,
                status="draft",
                using_db=conn
            )

        # 获取关联排期需求标题
        schedule_item_title = None
        if requirement.schedule_item_id:
            from service.schedule.models import ScheduleItem
            si = await ScheduleItem.get_or_none(id=requirement.schedule_item_id)
            schedule_item_title = si.requirement_title if si else None

        return RequirementResponse(
            id=requirement.id,
            module_id=requirement.module_id,
            title=requirement.title,
            doc_no=requirement.doc_no,
            description=requirement.description,
            priority=requirement.priority,
            status=requirement.status,
            schedule_item_id=requirement.schedule_item_id,
            schedule_item_title=schedule_item_title,
            creator_id=current_user.id,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="需求创建失败，请稍后重试"
        )


@router.get("/{project_id}/requirements", response_model=RequirementDetailListResponse, summary="获取需求列表")
async def get_requirements_list(
        project_id: int,
        module_id: Optional[int] = None,
        req_status: Optional[str] = Query(None, alias="status"),
        priority: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取需求详细列表接口"""
    project, current_user = project_user

    try:
        modules = await ProjectModule.filter(project_id=project_id).all()
        module_dict = {module.id: module.name for module in modules}
        
        if not module_dict:
            return RequirementDetailListResponse(
                requirements=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0
            )

        query_filters = {"module_id__in": list(module_dict.keys())}
        
        if module_id is not None:
            if module_id not in module_dict:
                return RequirementDetailListResponse(
                    requirements=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )
            query_filters["module_id"] = module_id
            
        if req_status is not None:
            query_filters["status"] = req_status
            
        if priority is not None:
            query_filters["priority"] = priority

        total = await RequirementDoc.filter(**query_filters).count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        offset = (page - 1) * page_size
        requirements = await RequirementDoc.filter(**query_filters).order_by('-created_at').offset(offset).limit(page_size).all()

        # 获取所有关联的排期需求标题
        from service.schedule.models import ScheduleItem
        schedule_item_ids = set(r.schedule_item_id for r in requirements if r.schedule_item_id)
        schedule_item_dict = {}
        if schedule_item_ids:
            si_list = await ScheduleItem.filter(id__in=list(schedule_item_ids)).all()
            schedule_item_dict = {si.id: si.requirement_title for si in si_list}

        detailed_requirements = []
        for requirement in requirements:
            module_name = module_dict.get(requirement.module_id, "未知模块")
            detailed_requirements.append(
                RequirementDetailItem(
                    id=requirement.id,
                    module_id=requirement.module_id,
                    module_name=module_name,
                    title=requirement.title,
                    priority=requirement.priority,
                    status=requirement.status,
                    schedule_item_id=requirement.schedule_item_id,
                    schedule_item_title=schedule_item_dict.get(requirement.schedule_item_id),
                    creator_id=requirement.creator_id,
                    created_at=requirement.created_at,
                    updated_at=requirement.updated_at
                )
            )

        return RequirementDetailListResponse(
            requirements=detailed_requirements,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取需求详细列表失败，请稍后重试"
        )


@router.get("/{project_id}/requirements/{requirement_id}", response_model=RequirementResponse, summary="获取需求详情")
async def get_requirement_detail(
        project_id: int,
        requirement_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取需求详情接口"""
    project, current_user = project_user
    
    try:
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )

        schedule_item_title = None
        if requirement.schedule_item_id:
            from service.schedule.models import ScheduleItem
            si = await ScheduleItem.get_or_none(id=requirement.schedule_item_id)
            schedule_item_title = si.requirement_title if si else None

        return RequirementResponse(
            id=requirement.id,
            module_id=requirement.module_id,
            title=requirement.title,
            doc_no=requirement.doc_no,
            description=requirement.description,
            priority=requirement.priority,
            status=requirement.status,
            schedule_item_id=requirement.schedule_item_id,
            schedule_item_title=schedule_item_title,
            creator_id=requirement.creator_id,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取需求详情失败，请稍后重试"
        )


@router.delete("/{project_id}/requirements/{requirement_id}", summary="删除需求")
async def delete_requirement(
        project_id: int,
        requirement_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """删除需求接口"""
    project, current_user = project_user

    try:
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )
        await requirement.delete()

        return {"message": "需求删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="需求删除失败，请稍后重试"
        )


@router.put("/{project_id}/requirements/{requirement_id}", response_model=RequirementResponse, summary="修改需求")
async def update_requirement(
        project_id: int,
        requirement_id: int,
        request: RequirementUpdateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """修改需求接口"""
    project, current_user = project_user

    try:
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )

        requirement.title = request.title
        requirement.description = request.description
        requirement.priority = request.priority
        requirement.status = request.status

        await requirement.save()

        schedule_item_title = None
        if requirement.schedule_item_id:
            from service.schedule.models import ScheduleItem
            si = await ScheduleItem.get_or_none(id=requirement.schedule_item_id)
            schedule_item_title = si.requirement_title if si else None

        return RequirementResponse(
            id=requirement.id,
            module_id=requirement.module_id,
            title=requirement.title,
            description=requirement.description,
            priority=requirement.priority,
            status=requirement.status,
            schedule_item_id=requirement.schedule_item_id,
            schedule_item_title=schedule_item_title,
            creator_id=requirement.creator_id,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="需求修改失败，请稍后重试"
        )


@router.put("/{project_id}/requirements/{requirement_id}/review", response_model=RequirementResponse, summary="审核需求")
async def review_requirement(
        project_id: int,
        requirement_id: int,
        request: RequirementReviewRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """审核需求接口"""
    project, current_user = project_user

    try:
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )

        requirement.status = request.status
        await requirement.save()

        schedule_item_title = None
        if requirement.schedule_item_id:
            from service.schedule.models import ScheduleItem
            si = await ScheduleItem.get_or_none(id=requirement.schedule_item_id)
            schedule_item_title = si.requirement_title if si else None

        return RequirementResponse(
            id=requirement.id,
            module_id=requirement.module_id,
            title=requirement.title,
            description=requirement.description,
            priority=requirement.priority,
            status=requirement.status,
            schedule_item_id=requirement.schedule_item_id,
            schedule_item_title=schedule_item_title,
            creator_id=requirement.creator_id,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="需求审核失败，请稍后重试"
        )


# ==================== 排期需求列表 API ====================

@router.get("/{project_id}/schedule-items-for-link", summary="获取可关联的排期需求列表")
async def get_schedule_items_for_link(
        project_id: int,
        keyword: Optional[str] = Query(None, description="按需求标题搜索"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取排期管理中的需求列表，供功能测试需求关联使用"""
    from service.schedule.models import ScheduleItem
    project, current_user = project_user

    try:
        query = ScheduleItem.filter(iteration__project_id=project_id)
        if keyword:
            query = query.filter(requirement_title__icontains=keyword)
        items = await query.order_by('-id').limit(100).all()
        result = []
        for item in items:
            result.append({
                "id": item.id,
                "requirement_title": item.requirement_title,
                "category": item.category,
                "requirement_status": item.requirement_status,
                "ticket_url": item.ticket_url,
            })
        return {"items": result, "total": len(result)}
    except Exception as e:
        logger.error(f"获取排期需求列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取排期需求列表失败")


# ==================== 用例集 API ====================

@router.get("/{project_id}/case_sets", response_model=FunctionalCaseSetListResponse, summary="获取用例集列表")
async def get_case_sets(
        project_id: int,
        requirement_id: Optional[int] = None,
        keyword: Optional[str] = None,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取项目下的用例集列表"""
    project, current_user = project_user

    try:
        query_filters = {"project_id": project_id}
        if requirement_id:
            query_filters["requirement_id"] = requirement_id

        case_sets = await FunctionalCaseSet.filter(**query_filters).order_by('-created_at').all()

        # 获取关联需求标题和创建人
        result = []
        for cs in case_sets:
            req_title = None
            if cs.requirement_id:
                req = await RequirementDoc.get_or_none(id=cs.requirement_id)
                req_title = req.title if req else None

            creator_name = None
            if cs.creator_id:
                creator = await User.get_or_none(id=cs.creator_id)
                creator_name = creator.real_name or creator.username if creator else None

            # 实时计算用例数和场景数
            case_count = await FunctionalCase.filter(case_set_id=cs.id).count()
            scenarios = await FunctionalCase.filter(case_set_id=cs.id).distinct().values_list('scenario', flat=True)
            scenario_count = len([s for s in scenarios if s])

            if keyword and keyword.lower() not in (cs.name or '').lower():
                continue

            result.append(FunctionalCaseSetSimple(
                id=cs.id,
                name=cs.name,
                description=cs.description,
                case_count=case_count,
                scenario_count=scenario_count,
                requirement_id=cs.requirement_id,
                requirement_title=req_title,
                creator_name=creator_name,
                created_at=cs.created_at,
                updated_at=cs.updated_at,
            ))

        return FunctionalCaseSetListResponse(case_sets=result, total=len(result))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用例集列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取用例集列表失败")


@router.get("/{project_id}/case_sets/{case_set_id}", response_model=FunctionalCaseSetDetailResponse, summary="获取用例集详情（含场景分组）")
async def get_case_set_detail(
        project_id: int,
        case_set_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取用例集详情，用例按场景分组返回"""
    project, current_user = project_user

    try:
        cs = await FunctionalCaseSet.get_or_none(id=case_set_id, project_id=project_id)
        if not cs:
            raise HTTPException(status_code=404, detail="用例集不存在")

        req_title = None
        if cs.requirement_id:
            req = await RequirementDoc.get_or_none(id=cs.requirement_id)
            req_title = req.title if req else None

        creator_name = None
        if cs.creator_id:
            creator = await User.get_or_none(id=cs.creator_id)
            creator_name = creator.real_name or creator.username if creator else None

        # 查询用例按场景排序
        cases = await FunctionalCase.filter(case_set_id=case_set_id).order_by('scenario_sort', 'id').all()

        # 获取需求标题映射
        requirement_ids = set(c.requirement_id for c in cases if c.requirement_id)
        req_dict = {}
        if requirement_ids:
            reqs = await RequirementDoc.filter(id__in=list(requirement_ids)).all()
            req_dict = {r.id: r.title for r in reqs}

        # 获取创建人映射
        creator_ids = set(c.creator_id for c in cases if c.creator_id)
        creator_dict = {}
        if creator_ids:
            creators = await User.filter(id__in=list(creator_ids)).all()
            creator_dict = {u.id: u.real_name or u.username for u in creators}

        # 按场景分组
        scenario_map = {}
        for case in cases:
            scenario_name = case.scenario or "未分类场景"
            if scenario_name not in scenario_map:
                scenario_map[scenario_name] = []
            scenario_map[scenario_name].append(FunctionalCaseSimple(
                id=case.id,
                case_no=case.case_no,
                case_name=case.case_name,
                priority=case.priority,
                status=case.status,
                scenario=case.scenario,
                scenario_sort=case.scenario_sort,
                requirement_id=case.requirement_id,
                requirement_title=req_dict.get(case.requirement_id),
                case_set_id=case.case_set_id,
                creator_name=creator_dict.get(case.creator_id),
                created_at=case.created_at,
                updated_at=case.updated_at,
            ))

        scenario_groups = [
            ScenarioCaseGroup(scenario=name, cases=case_list)
            for name, case_list in scenario_map.items()
        ]

        return FunctionalCaseSetDetailResponse(
            id=cs.id,
            name=cs.name,
            description=cs.description,
            case_count=len(cases),
            scenario_count=len(scenario_groups),
            requirement_id=cs.requirement_id,
            requirement_title=req_title,
            creator_name=creator_name,
            created_at=cs.created_at,
            updated_at=cs.updated_at,
            scenario_groups=scenario_groups,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用例集详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取用例集详情失败")


@router.post("/{project_id}/case_sets", summary="创建用例集")
async def create_case_set(
        project_id: int,
        data: FunctionalCaseSetCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """手动创建用例集"""
    project, current_user = project_user
    try:
        cs = await FunctionalCaseSet.create(
            name=data.name,
            description=data.description,
            requirement_id=data.requirement_id,
            project_id=project_id,
            creator_id=current_user.id,
        )
        return {"id": cs.id, "name": cs.name, "message": "用例集创建成功"}
    except Exception as e:
        logger.error(f"创建用例集失败: {e}")
        raise HTTPException(status_code=500, detail="创建用例集失败")


@router.put("/{project_id}/case_sets/{case_set_id}", summary="更新用例集")
async def update_case_set(
        project_id: int,
        case_set_id: int,
        data: FunctionalCaseSetUpdateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """更新用例集"""
    project, current_user = project_user
    try:
        cs = await FunctionalCaseSet.get_or_none(id=case_set_id, project_id=project_id)
        if not cs:
            raise HTTPException(status_code=404, detail="用例集不存在")
        if data.name is not None:
            cs.name = data.name
        if data.description is not None:
            cs.description = data.description
        await cs.save()
        return {"id": cs.id, "name": cs.name, "message": "用例集更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用例集失败: {e}")
        raise HTTPException(status_code=500, detail="更新用例集失败")


@router.delete("/{project_id}/case_sets/{case_set_id}", summary="删除用例集")
async def delete_case_set(
        project_id: int,
        case_set_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """删除用例集（级联删除其下用例）"""
    project, current_user = project_user
    try:
        cs = await FunctionalCaseSet.get_or_none(id=case_set_id, project_id=project_id)
        if not cs:
            raise HTTPException(status_code=404, detail="用例集不存在")
        # 删除关联用例
        await FunctionalCase.filter(case_set_id=case_set_id).delete()
        await cs.delete()
        return {"message": "用例集及其用例已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用例集失败: {e}")
        raise HTTPException(status_code=500, detail="删除用例集失败")


# ==================== 功能用例 API ====================

@router.get("/{project_id}/functional_cases", response_model=FunctionalCaseListResponse, summary="获取功能用例列表")
async def get_functional_cases_list(
        project_id: int,
        page: int = 1,
        page_size: int = 20,
        requirement_id: Optional[int] = None,
        case_set_id: Optional[int] = None,
        scenario: Optional[str] = None,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取功能用例列表接口"""
    project, current_user = project_user

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 50
    try:
        modules = await ProjectModule.filter(project_id=project_id).all()
        module_ids = [module.id for module in modules]

        requirements = await RequirementDoc.filter(
            module_id__in=module_ids
        ).all()
        requirement_dict = {req.id: req.title for req in requirements}

        query_conditions = {}

        if case_set_id is not None:
            query_conditions['case_set_id'] = case_set_id
        elif requirement_id is not None:
            if requirement_id not in requirement_dict:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的需求不存在"
                )
            query_conditions['requirement_id'] = requirement_id
        else:
            query_conditions['requirement_id__in'] = list(requirement_dict.keys())

        if scenario:
            query_conditions['scenario'] = scenario

        total_count = await FunctionalCase.filter(**query_conditions).count()

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        offset = (page - 1) * page_size
        functional_cases = await FunctionalCase.filter(
            **query_conditions
        ).order_by('scenario_sort', 'id').offset(offset).limit(page_size).all()

        # 获取创建人映射
        creator_ids = set(c.creator_id for c in functional_cases if c.creator_id)
        creator_dict = {}
        if creator_ids:
            creators = await User.filter(id__in=list(creator_ids)).all()
            creator_dict = {u.id: u.real_name or u.username for u in creators}

        cases_list = []
        for case in functional_cases:
            requirement_title = requirement_dict.get(case.requirement_id, None)
            
            cases_list.append(
                FunctionalCaseSimple(
                    id=case.id,
                    case_no=case.case_no,
                    case_name=case.case_name,
                    priority=case.priority,
                    status=case.status,
                    scenario=case.scenario,
                    scenario_sort=case.scenario_sort,
                    requirement_id=case.requirement_id,
                    requirement_title=requirement_title,
                    case_set_id=case.case_set_id,
                    creator_name=creator_dict.get(case.creator_id),
                    created_at=case.created_at,
                    updated_at=case.updated_at
                )
            )

        return FunctionalCaseListResponse(
            cases=cases_list,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取功能用例列表失败，请稍后重试"
        )


@router.get("/{project_id}/functional_cases/{case_id}", response_model=FunctionalCaseResponse, summary="获取功能用例详情")
async def get_functional_case_detail(
        project_id: int,
        case_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取功能用例详情接口"""
    project, current_user = project_user
    
    try:
        case = await FunctionalCase.get_or_none(id=case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="功能用例不存在"
            )

        if case.requirement_id:
            requirement = await RequirementDoc.get_or_none(id=case.requirement_id)
            if requirement:
                module = await ProjectModule.get_or_none(id=requirement.module_id)
                if not module or module.project_id != project_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="功能用例不属于该项目"
                    )
        
        return FunctionalCaseResponse(
            id=case.id,
            case_no=case.case_no,
            case_name=case.case_name,
            priority=case.priority,
            status=case.status,
            scenario=case.scenario,
            preconditions=case.preconditions,
            test_steps=case.test_steps,
            test_data=case.test_data,
            expected_result=case.expected_result,
            actual_result=case.actual_result,
            requirement_id=case.requirement_id,
            case_set_id=case.case_set_id,
            creator_id=case.creator_id,
            created_at=case.created_at,
            updated_at=case.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取功能用例详情失败，请稍后重试"
        )


@router.put("/{project_id}/functional_cases/{case_id}", response_model=FunctionalCaseResponse, summary="编辑功能用例")
async def update_functional_case(
        project_id: int,
        case_id: int,
        case_data: FunctionalCaseUpdateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """编辑功能用例接口"""
    project, current_user = project_user

    try:
        case = await FunctionalCase.get_or_none(id=case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的功能用例不存在"
            )

        if case_data.requirement_id:
            requirement = await RequirementDoc.get_or_none(
                id=case_data.requirement_id,
            )
            if not requirement:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的需求不存在"
                )
            module = await requirement.module
            if module and module.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="关联需求所属的模块不属于当前项目"
                )

        update_data = {}
        for field, value in case_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        if update_data:
            await case.update_from_dict(update_data)
            await case.save()

        updated_case = await FunctionalCase.get(id=case_id)

        return FunctionalCaseResponse(
            id=updated_case.id,
            case_no=updated_case.case_no,
            case_name=updated_case.case_name,
            priority=updated_case.priority,
            status=updated_case.status,
            scenario=updated_case.scenario,
            preconditions=updated_case.preconditions,
            test_steps=updated_case.test_steps,
            test_data=updated_case.test_data,
            expected_result=updated_case.expected_result,
            actual_result=updated_case.actual_result,
            requirement_id=updated_case.requirement_id,
            case_set_id=updated_case.case_set_id,
            creator_id=updated_case.creator_id,
            created_at=updated_case.created_at,
            updated_at=updated_case.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="编辑功能用例失败，请稍后重试"
        )


@router.delete("/{project_id}/functional_cases/{case_id}", summary="删除功能用例")
async def delete_functional_case(
        project_id: int,
        case_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """删除功能用例接口"""
    project, current_user = project_user

    try:
        case = await FunctionalCase.get_or_none(id=case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的功能用例不存在"
            )

        if case.requirement_id:
            requirement = await RequirementDoc.get_or_none(id=case.requirement_id)
            if requirement:
                module = await ProjectModule.get_or_none(id=requirement.module_id)
                if not module or module.project_id != project_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="功能用例不属于指定项目"
                    )

        await case.delete()

        return {"message": "功能用例删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除功能用例失败，请稍后重试"
        )


@router.post("/{project_id}/functional_cases", response_model=FunctionalCaseResponse, summary="创建功能用例")
async def create_functional_case(
        project_id: int,
        case_data: FunctionalCaseCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """创建功能用例"""
    try:
        project, current_user = project_user
        if case_data.requirement_id:
            requirement = await RequirementDoc.get_or_none(
                id=case_data.requirement_id,
            )
            if not requirement:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的需求不存在"
                )
            module = await requirement.module
            if module and module.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="关联需求所属的模块不属于当前项目"
                )
        case = await FunctionalCase.create(
            case_no=case_data.case_no,
            case_name=case_data.case_name,
            priority=case_data.priority,
            status="pending_review",
            scenario=case_data.scenario,
            preconditions=case_data.preconditions,
            test_steps=case_data.test_steps,
            test_data=case_data.test_data,
            expected_result=case_data.expected_result,
            actual_result="",
            requirement_id=case_data.requirement_id,
            case_set_id=case_data.case_set_id,
            creator_id=current_user.id
        )

        return FunctionalCaseResponse(
            id=case.id,
            case_no=case.case_no,
            case_name=case.case_name,
            priority=case.priority,
            status=case.status,
            scenario=case.scenario,
            preconditions=case.preconditions,
            test_steps=case.test_steps,
            test_data=case.test_data,
            expected_result=case.expected_result,
            actual_result=case.actual_result,
            requirement_id=case.requirement_id,
            case_set_id=case.case_set_id,
            creator_id=case.creator_id,
            created_at=case.created_at,
            updated_at=case.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建功能用例失败，请稍后重试"
        )


@router.put("/{project_id}/functional_cases/{case_id}/review", response_model=FunctionalCaseResponse,
            summary="审核功能用例")
async def review_functional_case(
        project_id: int,
        case_id: int,
        review_data: FunctionalCaseReviewRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """审核功能用例接口"""
    project, current_user = project_user

    try:
        case = await FunctionalCase.get_or_none(id=case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的功能用例不存在"
            )

        if case.requirement_id:
            requirement = await RequirementDoc.get_or_none(id=case.requirement_id)
            if requirement:
                module = await ProjectModule.get_or_none(id=requirement.module_id)
                if not module or module.project_id != project_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="指定的功能用例不属于当前项目"
                    )

        valid_statuses = ["pass", "smoke", "wait", "regression", "smoke", "obsolete"]
        if review_data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的审核状态，只能设置为: {', '.join(valid_statuses)}"
            )

        case.status = review_data.status
        await case.save()

        updated_case = await FunctionalCase.get(id=case_id)

        return FunctionalCaseResponse(
            id=updated_case.id,
            case_no=updated_case.case_no,
            case_name=updated_case.case_name,
            priority=updated_case.priority,
            status=updated_case.status,
            scenario=updated_case.scenario,
            preconditions=updated_case.preconditions,
            test_steps=updated_case.test_steps,
            test_data=updated_case.test_data,
            expected_result=updated_case.expected_result,
            actual_result=updated_case.actual_result,
            requirement_id=updated_case.requirement_id,
            case_set_id=updated_case.case_set_id,
            creator_id=updated_case.creator_id,
            created_at=updated_case.created_at,
            updated_at=updated_case.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审核功能用例失败，请稍后重试"
        )


@router.post("/{project_id}/requirements/{requirement_id}/generate_cases", summary="根据需求生成测试用例")
async def generate_test_cases_from_requirement(
        project_id: int,
        requirement_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    根据需求生成测试用例接口（知识增强版，含场景分组和用例集）

    完整业务链路：
    1. 从数据库读取需求基本信息（标题、描述、优先级）
    2. 从 RAG 知识库检索与该需求相关的补充信息（需求文档、技术文档等）
    3. 从评审记录获取评审知识（需求评审、技术评审、用例评审的 AI 分析结果）
    4. 从历史用例集获取参考用例
    5. 将以上所有信息合并为"增强需求文档"
    6. 调用 GeneratorTestCaseWorkflow 生成测试用例
    7. SSE 实时流式输出进度和结果
    """
    project, current_user = project_user

    try:
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的需求不存在"
            )

        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需求不属于当前项目"
            )

        # ============ 知识增强：检索 RAG + 评审知识 + 历史用例 ============
        from utils.knowledge_enhancer import build_enhanced_requirement

        enhanced_result = await build_enhanced_requirement(
            requirement_title=requirement.title,
            requirement_description=requirement.description or "",
            requirement_priority=str(requirement.priority) if requirement.priority else "",
            requirement_status=requirement.status or "",
            project_id=project_id,
            enable_rag=True,
            enable_review=True,
            enable_case_set=True,
        )

        # 使用增强后的完整文档作为输入（包含 RAG 知识 + 评审知识 + 历史用例）
        requirement_content = enhanced_result["enhanced_content"]
        knowledge_sources = enhanced_result["sources"]

        logger.info(f"知识增强完成，数据来源: {knowledge_sources}")

        # 工作流节点 -> 进度百分比映射
        node_progress_map = {
            '开始执行节点': 10,
            '测试点覆盖率验证通过': 30,
            '测试点覆盖率验证未通过': 25,
            '开始用例生成': 40,
            '用例覆盖率验证通过': 70,
            '用例覆盖率验证未通过': 60,
            '开始保存': 80,
            '共保存': 90,
        }

        async def generate_stream():
            """生成测试用例的流式输出函数"""
            try:
                # 发送知识增强信息
                source_labels = {
                    "database": "数据库需求",
                    "rag_knowledge": "RAG知识库",
                    "review_knowledge": "评审记录",
                    "case_set_knowledge": "历史用例集",
                }
                source_names = [source_labels.get(s, s) for s in knowledge_sources]
                source_names_str = "、".join(source_names)
                yield f"data: {json.dumps({'type': 'info', 'message': f'【知识增强】已检索到 {len(knowledge_sources)} 个知识源：{source_names_str}', 'progress': 3}, ensure_ascii=False)}\n\n"

                if "rag_knowledge" in knowledge_sources:
                    yield f"data: {json.dumps({'type': 'info', 'message': '【RAG检索】已从知识库检索到相关需求/技术文档，将作为补充上下文'}, ensure_ascii=False)}\n\n"
                if "review_knowledge" in knowledge_sources:
                    yield f"data: {json.dumps({'type': 'info', 'message': '【评审知识】已获取到评审分析结果（需求评审/技术评审/用例评审），将补充遗漏场景'}, ensure_ascii=False)}\n\n"
                if "case_set_knowledge" in knowledge_sources:
                    yield f"data: {json.dumps({'type': 'info', 'message': '【历史参考】已加载历史用例集作为参考'}, ensure_ascii=False)}\n\n"

                # 发送开始生成的消息
                yield f"data: {json.dumps({'type': 'start', 'message': '【开始生成】基于增强知识调用AI大模型...', 'progress': 5}, ensure_ascii=False)}\n\n"

                workflow_instance = GeneratorTestCaseWorkflow()
                workflow = workflow_instance.create_workflow()

                # 流式执行工作流（传入增强后的完整需求文档）
                stream_response = workflow.stream(
                    {
                        "input_requirement": requirement_content
                    },
                    config={
                        "metadata": {
                            "requirement_id": requirement.id,
                            "creator_id": current_user.id,
                            "project_id": project_id,
                        }
                    },
                    subgraphs=True,
                    stream_mode=["messages", "custom"]
                )

                generated_cases_count = 0
                current_progress = 5

                for item in stream_response:
                    if len(item) >= 3:
                        if item[1] == "messages":
                            message = item[2][0].content if hasattr(item[2][0], 'content') else str(item[2][0])
                            yield f"data: {json.dumps({'type': 'progress', 'message': message, 'progress': current_progress}, ensure_ascii=False)}\n\n"
                        elif item[1] == "custom":
                            custom_msg = str(item[2])
                            # 根据关键字匹配进度百分比
                            for keyword, pct in node_progress_map.items():
                                if keyword in custom_msg:
                                    current_progress = max(current_progress, pct)
                                    break
                            yield f"data: {json.dumps({'type': 'info', 'message': custom_msg, 'progress': current_progress}, ensure_ascii=False)}\n\n"
                            # 从自定义消息中提取保存数量
                            if "共保存" in custom_msg:
                                import re as _re
                                m = _re.search(r'共保存\s*(\d+)', custom_msg)
                                if m:
                                    generated_cases_count = int(m.group(1))

                    await asyncio.sleep(0.1)
                # 发送完成消息
                yield f"data: {json.dumps({'type': 'complete', 'message': f'测试用例生成完成！共生成 {generated_cases_count} 个测试用例（含场景分组，知识源：{source_names_str}）', 'progress': 100}, ensure_ascii=False)}\n\n"

            except Exception as e:
                error_message = f"生成测试用例时发生错误：{str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_message, 'progress': current_progress}, ensure_ascii=False)}\n\n"
            finally:
                yield f"data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成测试用例失败：{str(e)}"
        )


@router.post("/extract_requirement", summary="从文档中AI提取需求信息")
async def extract_requirement_from_document(
        file: Optional[UploadFile] = File(None, description="需求文档文件（支持 PDF、DOCX、TXT、MD）"),
        image: Optional[UploadFile] = File(None, description="需求截图/图片（支持 PNG、JPG、JPEG、WebP）"),
        url: Optional[str] = Form(None, description="需求文档链接（仅支持公开可访问的链接）"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """从上传的文档文件、图片截图或文档链接中，使用AI提取结构化的需求信息。"""
    project, current_user = project_user

    try:
        has_file = file and file.filename
        has_image = image and image.filename
        has_url = url and url.strip()

        if not has_file and not has_image and not has_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传文档文件、需求截图或提供文档链接"
            )

        # ===== 图像识别模式 =====
        if has_image:
            import base64
            from langchain_core.messages import HumanMessage

            allowed_image_types = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
            if image.content_type not in allowed_image_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的图片格式: {image.content_type}，请上传 PNG、JPG、JPEG 或 WebP 格式"
                )

            image_content = await image.read()
            if len(image_content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="图片大小不能超过 10MB"
                )

            base64_image = base64.b64encode(image_content).decode('utf-8')
            content_type = image.content_type or "image/png"

            from config.settings import llm

            vision_message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": """请仔细分析这张图片，它可能是需求文档、PRD、用户故事、功能规格说明书等的截图。

### 任务
请从图片中识别出所有文字内容，并从中提取出功能需求的关键信息，按照指定格式输出。

### 提取规则
1. **需求标题**：从图片文字中提取出最核心的功能需求标题，简洁明确（不超过100个字符）
2. **需求描述**：从图片文字中提取并整理出详细的功能需求描述，应包含以下方面（如果图片中有提及）：
   - 功能目标和用途
   - 用户场景和使用流程
   - 功能边界和限制条件
   - 预期的输入输出
   - 验收标准/验收条件
   - 特殊要求或约束条件
3. **优先级建议**：根据内容判断需求优先级（1=低, 2=中, 3=高），如果无法判断，默认为2（中）

### 重要约束
- 严禁编造或推测图片中未明确提及的信息
- 请逐字逐句仔细识别图片中的所有文字
- 如果图片中包含多个需求，提取最主要/核心的一个需求
- 需求描述应该尽可能详细和结构化，完整保留图片中的原始信息
- 如果图片内容不是需求相关的，请在描述中说明图片中实际包含的内容

### 输出格式要求
请严格按照以下JSON格式输出，不要添加任何多余的说明文字或markdown标记：
{
    "title": "需求标题",
    "description": "详细的需求描述，使用换行符分段",
    "priority": 2
}"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{content_type};base64,{base64_image}"}
                    },
                ]
            )

            result = llm.invoke([vision_message])
            ai_content = result.content

            # 解析JSON
            json_match = re.search(r'\{[\s\S]*\}', ai_content)
            if json_match:
                try:
                    ai_result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="AI返回的数据格式异常，请重试"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI无法从图片中提取需求信息，请确认图片内容是否清晰"
                )

            return {
                "success": True,
                "message": "图像识别提取需求成功",
                "data": {
                    "title": ai_result.get("title", ""),
                    "description": ai_result.get("description", ""),
                    "priority": ai_result.get("priority", 2),
                    "raw_text": ai_result.get("description", "")[:2000]
                }
            }

        # ===== 文档文件模式 =====
        extracted_text = ""

        if has_file:
            from utils.parser.requirement_document_parser import (
                extract_text_from_file,
                SUPPORTED_EXTENSIONS,
                MAX_FILE_SIZE
            )
            import os

            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的文件格式: {ext}，支持的格式为: PDF, DOCX, TXT, MD"
                )

            file_content = await file.read()

            if len(file_content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="文件大小超过限制（最大10MB）"
                )

            try:
                extracted_text = extract_text_from_file(file.filename, file_content)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"文件解析失败: {str(e)}"
                )

        # ===== URL模式 =====
        elif has_url:
            from utils.parser.requirement_document_parser import extract_text_from_url

            if not url.startswith(('http://', 'https://')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="请提供有效的HTTP/HTTPS链接"
                )

            try:
                extracted_text = extract_text_from_url(url)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无法获取链接内容: {str(e)}"
                )

        if not extracted_text or not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未能从文档中提取到有效文本内容"
            )

        max_text_length = 8000
        if len(extracted_text) > max_text_length:
            extracted_text_for_ai = extracted_text[:max_text_length] + "\n\n[... 文档内容过长，已截断 ...]"
        else:
            extracted_text_for_ai = extracted_text

        from config.prompts.parser.requirement_extractor import prompt as req_prompt
        from config.settings import llm
        from langchain_core.output_parsers import JsonOutputParser

        chain = req_prompt | llm | JsonOutputParser()
        ai_result = chain.invoke({"document_content": extracted_text_for_ai})

        return {
            "success": True,
            "message": "需求信息提取成功",
            "data": {
                "title": ai_result.get("title", ""),
                "description": ai_result.get("description", ""),
                "priority": ai_result.get("priority", 2),
                "raw_text": extracted_text[:2000] + ("..." if len(extracted_text) > 2000 else "")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI提取需求信息失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI提取需求信息失败: {str(e)}"
        )


@router.post("/extract_requirement_stream", summary="流式混合提取需求信息（文本+图片+文档+视频+链接）")
async def extract_requirement_stream(
        text: Optional[str] = Form(None, description="直接输入的文本内容"),
        files: list[UploadFile] = File(default=[], description="上传的文件列表（文档/图片/视频）"),
        url: Optional[str] = Form(None, description="文档链接"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    统一混合输入流式提取接口。
    支持同时接收文本、多个文件（文档/图片/视频）和URL，
    并行处理后合并所有内容，使用AI流式提取需求信息。
    """
    project, current_user = project_user

    has_text = text and text.strip()
    has_files = files and len(files) > 0 and any(f.filename for f in files)
    has_url = url and url.strip()

    if not has_text and not has_files and not has_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请输入文本、上传文件或提供链接"
        )

    import base64
    import os
    from langchain_core.messages import HumanMessage

    # ---- 预处理阶段：并行读取所有文件内容 ----
    all_text_parts = []
    image_data_list = []  # [(base64_data, content_type)]
    video_filenames = []

    # 1. 直接文本
    if has_text:
        all_text_parts.append(f"【用户输入文本】\n{text.strip()}")

    # 2. 处理上传的文件
    if has_files:
        for f in files:
            if not f.filename:
                continue
            fname = f.filename.lower()
            ftype = f.content_type or ""
            file_content = await f.read()

            if not file_content:
                continue

            # 图片文件
            if ftype.startswith("image/") or fname.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                if len(file_content) <= 10 * 1024 * 1024:
                    b64 = base64.b64encode(file_content).decode('utf-8')
                    ct = ftype if ftype else "image/png"
                    image_data_list.append((b64, ct, f.filename))

            # 视频文件
            elif ftype.startswith("video/") or fname.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                video_filenames.append(f.filename)
                # 对视频暂时只记录文件名，提示用户
                all_text_parts.append(f"【视频文件】{f.filename}（视频内容需人工确认）")

            # 文档文件
            else:
                ext = os.path.splitext(f.filename)[1].lower()
                doc_exts = {'.pdf', '.docx', '.doc', '.txt', '.md'}
                if ext in doc_exts:
                    try:
                        from utils.parser.requirement_document_parser import extract_text_from_file
                        doc_text = extract_text_from_file(f.filename, file_content)
                        if doc_text and doc_text.strip():
                            # 截断过长文档
                            if len(doc_text) > 6000:
                                doc_text = doc_text[:6000] + "\n[...文档内容过长已截断...]"
                            all_text_parts.append(f"【文档：{f.filename}】\n{doc_text}")
                    except Exception as e:
                        all_text_parts.append(f"【文档解析失败：{f.filename}】错误: {str(e)}")

    # 3. URL
    if has_url:
        try:
            from utils.parser.requirement_document_parser import extract_text_from_url
            if url.startswith(('http://', 'https://')):
                url_text = extract_text_from_url(url)
                if url_text and url_text.strip():
                    if len(url_text) > 6000:
                        url_text = url_text[:6000] + "\n[...链接内容过长已截断...]"
                    all_text_parts.append(f"【链接内容：{url}】\n{url_text}")
        except Exception as e:
            all_text_parts.append(f"【链接获取失败：{url}】错误: {str(e)}")

    merged_text = "\n\n---\n\n".join(all_text_parts) if all_text_parts else ""

    from config.settings import llm

    # ---- 构建LLM消息 ----
    content_blocks = []

    # 精简的提取 prompt
    extract_prompt = """你是资深需求分析师。请从以下输入内容中快速提取功能需求信息。

## 规则
1. 标题：简洁明确，不超过100字符
2. 描述：结构化整理，包含功能目标、场景、细节、输入输出、边界条件
3. 优先级：1=低 2=中 3=高，默认2
4. 严禁编造未提及的信息

## 输出JSON（不要markdown标记）
{"title":"需求标题","description":"详细描述","priority":2}"""

    if merged_text and image_data_list:
        # 混合模式：文本+图片
        content_blocks.append({"type": "text", "text": f"{extract_prompt}\n\n## 文本内容\n{merged_text}\n\n## 以下是图片内容，请识别图中文字后一并提取需求："})
        for b64, ct, fname in image_data_list:
            content_blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:{ct};base64,{b64}"}
            })
    elif image_data_list:
        # 纯图片模式
        content_blocks.append({"type": "text", "text": f"{extract_prompt}\n\n请识别以下图片中的文字内容并提取需求："})
        for b64, ct, fname in image_data_list:
            content_blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:{ct};base64,{b64}"}
            })
    elif merged_text:
        # 纯文本模式
        content_blocks.append({"type": "text", "text": f"{extract_prompt}\n\n## 输入内容\n{merged_text}"})
    else:
        raise HTTPException(status_code=400, detail="未能获取到任何有效内容")

    message = HumanMessage(content=content_blocks)

    # ---- 流式输出 ----
    async def generate():
        try:
            input_summary_parts = []
            if has_text:
                input_summary_parts.append("文本")
            if image_data_list:
                input_summary_parts.append(f"{len(image_data_list)}张图片")
            doc_count = sum(1 for p in all_text_parts if p.startswith("【文档"))
            if doc_count:
                input_summary_parts.append(f"{doc_count}个文档")
            if has_url:
                input_summary_parts.append("链接")
            if video_filenames:
                input_summary_parts.append(f"{len(video_filenames)}个视频")

            summary = "、".join(input_summary_parts)
            yield f"data: {json.dumps({'type': 'progress', 'message': f'已接收到 {summary}，正在AI分析中...', 'progress': 20}, ensure_ascii=False)}\n\n"

            full_content = ""
            async for chunk in llm.astream([message]):
                if chunk.content:
                    full_content += chunk.content
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'progress', 'message': 'AI分析完成，正在解析结果...', 'progress': 90}, ensure_ascii=False)}\n\n"

            # 解析JSON结果
            clean = full_content.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            json_match = re.search(r'\{[\s\S]*\}', clean)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    yield f"data: {json.dumps({'type': 'result', 'data': result}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    yield f"data: {json.dumps({'type': 'result', 'data': {'title': '', 'description': full_content, 'priority': 2}}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'result', 'data': {'title': '', 'description': full_content, 'priority': 2}}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'progress': 100})}\n\n"

        except Exception as e:
            logger.error(f"流式提取失败: {e}\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.get("/{project_id}/requirements/{requirement_id}/export_xmind", summary="导出测试用例为XMind文件")
async def export_cases_as_xmind(
        project_id: int,
        requirement_id: int,
        show_priority: bool = Query(True, description="用例标题前显示优先级"),
        show_case_id: bool = Query(False, description="用例标题显示用例编号"),
        show_node_labels: bool = Query(False, description="注明节点属性（如 前置条件：xxx）"),
        scenario_prefix: str = Query("验证", description="场景名称前缀"),
        scenario_suffix: str = Query("功能", description="场景名称后缀"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """导出测试用例为 XMind 思维导图文件（含场景中间层级）"""
    project, current_user = project_user

    try:
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )

        cases = await FunctionalCase.filter(requirement_id=requirement_id).order_by('scenario_sort', 'id').all()

        if not cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该需求下暂无测试用例，请先生成用例后再导出"
            )

        # 按场景分组
        scenario_map = {}
        for case in cases:
            scenario_name = case.scenario or "未分类场景"
            if scenario_name not in scenario_map:
                scenario_map[scenario_name] = []
            scenario_map[scenario_name].append({
                "case_no": case.case_no,
                "case_name": case.case_name,
                "priority": case.priority,
                "preconditions": case.preconditions or "",
                "test_steps": case.test_steps or "",
                "expected_result": case.expected_result or "",
            })

        template_settings = {
            "show_priority": show_priority,
            "show_case_id": show_case_id,
            "show_node_labels": show_node_labels,
            "scenario_prefix": scenario_prefix,
            "scenario_suffix": scenario_suffix,
        }

        from utils.xmind_generator import generate_xmind_file

        xmind_bytes = generate_xmind_file(
            requirement_title=requirement.title,
            test_cases=None,  # 不传旧参数
            template_settings=template_settings,
            scenario_groups=scenario_map  # 传场景分组
        )

        safe_title = re.sub(r'[\\/:*?"<>|]', '_', requirement.title)[:50]
        filename = f"{safe_title}_测试用例.xmind"

        from urllib.parse import quote
        encoded_filename = quote(filename)

        return Response(
            content=xmind_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Type": "application/octet-stream",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出XMind失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出XMind文件失败: {str(e)}"
        )


# ==================== AI 优化需求 ====================

@router.post("/{project_id}/doc_to_xmind_stream", summary="一键文档生成XMind用例（流式）")
async def doc_to_xmind_stream(
        project_id: int,
        text: Optional[str] = Form(None, description="直接输入的需求文本"),
        files: list[UploadFile] = File(default=[], description="上传的文件（文档/图片）"),
        url: Optional[str] = Form(None, description="文档链接"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    一键从文档/文本/图片生成完整的XMind测试用例。
    流程：解析输入 → AI一次性生成场景+用例 → 构建XMind → SSE流式返回进度+结果。
    最终返回 base64 编码的 XMind 文件 + 用例预览数据。
    """
    project, current_user = project_user

    has_text = text and text.strip()
    has_files = files and len(files) > 0 and any(f.filename for f in files)
    has_url = url and url.strip()

    if not has_text and not has_files and not has_url:
        raise HTTPException(status_code=400, detail="请输入文本、上传文件或提供链接")

    import base64
    import os
    from langchain_core.messages import HumanMessage

    # ---- 预处理：提取所有输入内容 ----
    all_text_parts = []
    image_data_list = []

    if has_text:
        all_text_parts.append(f"【用户输入】\n{text.strip()}")

    if has_files:
        for f in files:
            if not f.filename:
                continue
            fname = f.filename.lower()
            ftype = f.content_type or ""
            file_content = await f.read()
            if not file_content:
                continue

            if ftype.startswith("image/") or fname.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                if len(file_content) <= 10 * 1024 * 1024:
                    b64 = base64.b64encode(file_content).decode('utf-8')
                    ct = ftype if ftype else "image/png"
                    image_data_list.append((b64, ct, f.filename))
            else:
                ext = os.path.splitext(f.filename)[1].lower()
                doc_exts = {'.pdf', '.docx', '.doc', '.txt', '.md'}
                if ext in doc_exts:
                    try:
                        from utils.parser.requirement_document_parser import extract_text_from_file
                        doc_text = extract_text_from_file(f.filename, file_content)
                        if doc_text and doc_text.strip():
                            if len(doc_text) > 8000:
                                doc_text = doc_text[:8000] + "\n[...文档内容过长已截断...]"
                            all_text_parts.append(f"【文档：{f.filename}】\n{doc_text}")
                    except Exception as e:
                        all_text_parts.append(f"【文档解析失败：{f.filename}】{str(e)}")

    if has_url:
        try:
            from utils.parser.requirement_document_parser import extract_text_from_url
            if url.startswith(('http://', 'https://')):
                url_text = extract_text_from_url(url)
                if url_text and url_text.strip():
                    if len(url_text) > 8000:
                        url_text = url_text[:8000] + "\n[...链接内容过长已截断...]"
                    all_text_parts.append(f"【链接：{url}】\n{url_text}")
        except Exception as e:
            all_text_parts.append(f"【链接获取失败】{str(e)}")

    merged_text = "\n\n---\n\n".join(all_text_parts) if all_text_parts else ""

    from config.settings import llm

    # ---- 查询知识库获取XMind参考用例 ----
    rag_reference = ""
    try:
        from utils.knowledge_enhancer import search_rag_knowledge, get_case_set_knowledge
        # 从RAG知识库查找相关的测试用例参考
        search_query = text.strip()[:200] if has_text and text.strip() else "测试用例 功能测试"
        rag_result = await search_rag_knowledge(search_query)
        if rag_result:
            rag_reference += f"\n## 知识库参考用例（请学习以下格式和覆盖思路）\n{rag_result[:4000]}\n"

        # 从历史用例集获取参考
        case_set_ref = await get_case_set_knowledge(project_id)
        if case_set_ref:
            rag_reference += f"\n## 历史用例集参考\n{case_set_ref[:2000]}\n"
    except Exception as e:
        logger.warning(f"知识库检索失败（不影响生成）: {e}")

    # ---- 构建一次性生成用例的 Prompt ----
    case_gen_prompt = f"""你是一位资深测试工程师。请根据以下需求内容，直接生成完整的、按测试点（测试场景）分组的功能测试用例。
{rag_reference}

## 核心要求
1. 必须按"测试点"分组输出，每个测试点包含多个用例
2. 覆盖正向验证、边界测试、异常处理三类测试点
3. 用例要全面、详细、可执行
4. 测试点名称简洁，能一眼看出验证的功能点
5. 如果知识库参考中有相关用例，请学习其覆盖思路和写法风格

## XMind层级结构说明
生成的用例将以如下 XMind 层级展示：
  需求标题（根节点）
    └── 测试点（场景分组）
         └── 测试标题（用例名称）
              ├── 前置条件
              ├── 测试步骤
              └── 预期结果

## 输出格式（严格JSON，不要markdown标记）
[
  {{
    "scenario": "测试点名称",
    "cases": [
      {{
        "case_name": "用例标题",
        "priority": "P0/P1/P2/P3",
        "preconditions": "前置条件（环境、数据、用户状态等）",
        "test_steps": "详细测试步骤（多步骤用换行分隔，如：\\n1.打开页面\\n2.输入数据\\n3.点击提交）",
        "expected_result": "预期结果（明确可验证的结果描述）"
      }}
    ]
  }}
]

## 用例质量标准
- P0: 核心功能主流程，必须通过
- P1: 重要分支流程和关键边界
- P2: 一般性边界和异常
- P3: 极端情况和低频场景
- 每个测试点至少2个用例，建议3-5个
- 前置条件必须写清楚环境和数据准备
- 测试步骤必须具体可操作，不能笼统
- 预期结果必须明确可验证"""

    content_blocks = []

    if merged_text and image_data_list:
        content_blocks.append({"type": "text", "text": f"{case_gen_prompt}\n\n## 需求文档内容\n{merged_text}\n\n## 以下图片也是需求的一部分，请识别图中文字后一并分析生成用例："})
        for b64, ct, fname in image_data_list:
            content_blocks.append({"type": "image_url", "image_url": {"url": f"data:{ct};base64,{b64}"}})
    elif image_data_list:
        content_blocks.append({"type": "text", "text": f"{case_gen_prompt}\n\n请识别以下图片中的需求内容，然后生成完整测试用例："})
        for b64, ct, fname in image_data_list:
            content_blocks.append({"type": "image_url", "image_url": {"url": f"data:{ct};base64,{b64}"}})
    elif merged_text:
        content_blocks.append({"type": "text", "text": f"{case_gen_prompt}\n\n## 需求文档内容\n{merged_text}"})
    else:
        raise HTTPException(status_code=400, detail="未能获取到任何有效内容")

    message = HumanMessage(content=content_blocks)

    async def generate():
        try:
            # 进度 10%：输入摘要
            input_parts = []
            if has_text:
                input_parts.append("文本")
            if image_data_list:
                input_parts.append(f"{len(image_data_list)}张图片")
            doc_count = sum(1 for p in all_text_parts if p.startswith("【文档"))
            if doc_count:
                input_parts.append(f"{doc_count}个文档")
            if has_url:
                input_parts.append("链接")
            summary = "、".join(input_parts)
            yield f"data: {json.dumps({'type': 'progress', 'message': f'已接收 {summary}，正在AI分析生成用例...', 'progress': 10}, ensure_ascii=False)}\n\n"

            # 进度 20%：开始 AI 生成
            yield f"data: {json.dumps({'type': 'progress', 'message': 'AI 正在分析需求并生成测试场景和用例...', 'progress': 20}, ensure_ascii=False)}\n\n"

            full_content = ""
            chunk_count = 0
            async for chunk in llm.astream([message]):
                if chunk.content:
                    full_content += chunk.content
                    chunk_count += 1
                    # 每10个chunk发一次内容更新
                    if chunk_count % 10 == 0:
                        progress = min(20 + int(chunk_count * 0.5), 75)
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content, 'progress': progress}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'progress', 'message': 'AI生成完成，正在解析用例数据...', 'progress': 80}, ensure_ascii=False)}\n\n"

            # 解析JSON
            clean = full_content.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            json_match = re.search(r'\[[\s\S]*\]', clean)
            scenarios = []
            if json_match:
                try:
                    scenarios = json.loads(json_match.group())
                except json.JSONDecodeError:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'AI返回的用例数据解析失败，请重试'}, ensure_ascii=False)}\n\n"
                    return
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': 'AI未返回有效的用例数据，请检查输入内容后重试'}, ensure_ascii=False)}\n\n"
                return

            if not scenarios:
                yield f"data: {json.dumps({'type': 'error', 'message': '未生成任何测试用例，输入内容可能不是需求文档'}, ensure_ascii=False)}\n\n"
                return

            # 统计
            total_cases = sum(len(s.get("cases", [])) for s in scenarios)
            total_scenarios = len(scenarios)

            yield f"data: {json.dumps({'type': 'progress', 'message': f'成功生成 {total_scenarios} 个测试场景、{total_cases} 条用例，正在构建XMind文件...', 'progress': 85}, ensure_ascii=False)}\n\n"

            # 构建 XMind
            from utils.xmind_generator import generate_xmind_file

            # 转换为 XMind 格式的 scenario_groups
            scenario_groups = {}
            priority_map = {"P0": 1, "P1": 2, "P2": 3, "P3": 4}

            for s in scenarios:
                scenario_name = s.get("scenario", "未分类场景")
                cases = []
                for idx, c in enumerate(s.get("cases", []), 1):
                    p_str = c.get("priority", "P2")
                    cases.append({
                        "case_no": f"TC-{idx:03d}",
                        "case_name": c.get("case_name", f"用例{idx}"),
                        "priority": priority_map.get(p_str, 3),
                        "preconditions": c.get("preconditions", ""),
                        "test_steps": c.get("test_steps", ""),
                        "expected_result": c.get("expected_result", ""),
                    })
                scenario_groups[scenario_name] = cases

            # 自动提取标题
            title_hint = ""
            if has_text and text.strip():
                title_hint = text.strip()[:50]
            elif all_text_parts:
                for p in all_text_parts:
                    if "】" in p:
                        title_hint = p.split("】")[0].replace("【", "").replace("文档：", "").replace("链接：", "")[:50]
                        break
            if not title_hint:
                title_hint = "需求文档"

            root_title = f"{title_hint} - 测试用例"

            xmind_bytes = generate_xmind_file(
                requirement_title=root_title,
                template_settings={
                    "show_priority": True,
                    "show_case_id": True,
                    "show_node_labels": True,
                    "scenario_prefix": "",
                    "scenario_suffix": "",
                },
                scenario_groups=scenario_groups
            )

            xmind_b64 = base64.b64encode(xmind_bytes).decode('utf-8')

            yield f"data: {json.dumps({'type': 'progress', 'message': 'XMind文件构建完成！', 'progress': 95}, ensure_ascii=False)}\n\n"

            # 发送最终结果
            yield f"data: {json.dumps({'type': 'result', 'data': {'scenarios': scenarios, 'total_cases': total_cases, 'total_scenarios': total_scenarios, 'xmind_base64': xmind_b64, 'xmind_filename': f'{title_hint}_测试用例.xmind'}}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'progress': 100})}\n\n"

        except Exception as e:
            logger.error(f"一键生成XMind失败: {e}\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'生成失败: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.post("/{project_id}/download_xmind_from_cases", summary="根据用例数据生成XMind文件下载")
async def download_xmind_from_cases(
        project_id: int,
        request_data: dict,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    接收前端传来的场景分组用例数据，生成XMind文件并返回下载。
    用于用户预览用例后再次下载或修改后下载。
    """
    from utils.xmind_generator import generate_xmind_file
    from urllib.parse import quote

    scenarios = request_data.get("scenarios", [])
    title = request_data.get("title", "测试用例")

    if not scenarios:
        raise HTTPException(status_code=400, detail="用例数据为空")

    priority_map = {"P0": 1, "P1": 2, "P2": 3, "P3": 4}
    scenario_groups = {}

    for s in scenarios:
        scenario_name = s.get("scenario", "未分类场景")
        cases = []
        for idx, c in enumerate(s.get("cases", []), 1):
            p_str = c.get("priority", "P2")
            cases.append({
                "case_no": f"TC-{idx:03d}",
                "case_name": c.get("case_name", f"用例{idx}"),
                "priority": priority_map.get(p_str, 3) if isinstance(p_str, str) else p_str,
                "preconditions": c.get("preconditions", ""),
                "test_steps": c.get("test_steps", ""),
                "expected_result": c.get("expected_result", ""),
            })
        scenario_groups[scenario_name] = cases

    xmind_bytes = generate_xmind_file(
        requirement_title=title,
        template_settings={
            "show_priority": True,
            "show_case_id": True,
            "show_node_labels": True,
            "scenario_prefix": "",
            "scenario_suffix": "",
        },
        scenario_groups=scenario_groups
    )

    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)[:50]
    filename = f"{safe_title}_测试用例.xmind"
    encoded_filename = quote(filename)

    return Response(
        content=xmind_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/octet-stream",
        }
    )


# ==================== AI 优化需求 ====================

@router.post("/{project_id}/requirements/{requirement_id}/ai_optimize", summary="AI优化需求")
async def ai_optimize_requirement(
        project_id: int,
        requirement_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    使用AI优化需求的标题和描述，使其更清晰、完整、可测试。
    返回SSE流式输出优化结果。
    """
    project, current_user = project_user

    try:
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求不存在")

        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求不属于该项目")

        from config.settings import llm

        prompt = f"""你是一位资深的软件需求分析师和测试专家。请对以下需求进行全面优化，使其更加清晰、完整、可测试。

## 原始需求信息
- **标题**: {requirement.title}
- **描述**: {requirement.description or '无描述'}
- **优先级**: {requirement.priority}
- **所属模块**: {module.name if module else '未分类'}

## 优化要求
请从以下几个维度优化该需求：

1. **标题优化**: 使标题更准确、简洁、易于理解
2. **描述优化**: 补充和完善需求描述，包括：
   - 功能概述（用1-2句话概括核心功能）
   - 用户场景（描述用户在什么场景下使用该功能）
   - 功能细节（列出具体的功能点）
   - 输入输出（明确输入条件和预期输出）
   - 边界条件（列出需要注意的边界情况）
   - 非功能性要求（如性能、安全性等，如适用）
3. **验收标准**: 列出明确的验收标准，方便测试人员编写用例
4. **潜在风险**: 指出可能存在的技术风险或业务风险

## 输出格式
请严格按以下JSON格式输出（不要包含markdown代码块标记）：
{{
    "optimized_title": "优化后的标题",
    "optimized_description": "优化后的完整描述（使用markdown格式）",
    "acceptance_criteria": ["验收标准1", "验收标准2", "..."],
    "risks": ["风险点1", "风险点2"],
    "optimization_summary": "优化说明（简要说明做了哪些优化）"
}}"""

        async def generate():
            try:
                full_content = ""
                async for chunk in llm.astream(prompt):
                    if chunk.content:
                        full_content += chunk.content
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

                # 尝试解析完整的JSON结果
                try:
                    # 清理可能的markdown代码块标记
                    clean_content = full_content.strip()
                    if clean_content.startswith("```json"):
                        clean_content = clean_content[7:]
                    if clean_content.startswith("```"):
                        clean_content = clean_content[3:]
                    if clean_content.endswith("```"):
                        clean_content = clean_content[:-3]
                    clean_content = clean_content.strip()

                    result = json.loads(clean_content)
                    yield f"data: {json.dumps({'type': 'result', 'data': result}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    yield f"data: {json.dumps({'type': 'result', 'data': {'raw': full_content}}, ensure_ascii=False)}\n\n"

                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"AI优化需求流式输出失败: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI优化需求失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI优化需求失败: {str(e)}"
        )


@router.post("/{project_id}/ai_optimize_doc_stream", summary="AI优化需求文档（支持MD文件上传，流式）")
async def ai_optimize_doc_stream(
        project_id: int,
        text: Optional[str] = Form(None, description="直接输入的需求文本"),
        file: Optional[UploadFile] = File(None, description="需求文档文件（支持 MD、TXT、PDF、DOCX）"),
        title: Optional[str] = Form(None, description="需求标题（可选）"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    AI优化需求文档（支持上传MD等文件 + 文本输入），流式输出。
    先总结需求文档内容，再输出结构化的优化需求。
    """
    project, current_user = project_user

    has_text = text and text.strip()
    has_file = file and file.filename

    if not has_text and not has_file:
        raise HTTPException(status_code=400, detail="请输入需求文本或上传需求文档")

    # 提取文档内容
    doc_content = ""
    doc_filename = ""

    if has_file:
        import os
        ext = os.path.splitext(file.filename)[1].lower()
        supported_ext = {'.md', '.txt', '.pdf', '.docx', '.doc'}
        if ext not in supported_ext:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，支持 MD、TXT、PDF、DOCX")

        file_content = await file.read()
        if len(file_content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过20MB")

        try:
            from utils.parser.requirement_document_parser import extract_text_from_file
            doc_content = extract_text_from_file(file.filename, file_content)
            doc_filename = file.filename
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    # 合并输入
    merged_input = ""
    if has_text:
        merged_input += f"【用户输入】\n{text.strip()}\n\n"
    if doc_content:
        if len(doc_content) > 10000:
            doc_content = doc_content[:10000] + "\n[...文档内容过长已截断...]"
        merged_input += f"【文档：{doc_filename}】\n{doc_content}"

    if not merged_input.strip():
        raise HTTPException(status_code=400, detail="未能获取到有效内容")

    # 查询知识库获取参考用例格式
    rag_context = ""
    try:
        from utils.knowledge_enhancer import search_rag_knowledge
        rag_result = await search_rag_knowledge(f"需求文档 测试用例 {title or ''}")
        if rag_result:
            rag_context = f"\n\n## 知识库参考信息\n{rag_result[:3000]}"
    except Exception as e:
        logger.warning(f"RAG检索失败（不影响功能）: {e}")

    from config.settings import llm

    prompt = f"""你是一位资深的软件需求分析师和测试专家。请对以下输入内容进行全面分析和优化。

## 输入内容
{f'**标题**: {title}' if title and title.strip() else '（未提供标题，请根据内容自动生成）'}
{merged_input}
{rag_context}

## 任务
1. **需求总结**：用2-3句话概括这份需求文档的核心内容
2. **标题优化**：给出简洁、准确的需求标题（不超过100字符）
3. **需求规范化**：将原始内容整理为标准化需求描述，包括：
   - 功能概述
   - 用户场景
   - 功能细节（具体功能点列表）
   - 输入输出要求
   - 边界条件与约束
4. **验收标准**：列出明确的验收标准
5. **风险提示**：指出可能的风险点

## 重要约束
- 严禁编造原文中未提及的功能需求
- 可以做合理推断和补充，但不能改变原意
- 需求描述应该结构化、可测试

## 输出格式（严格JSON，不要markdown标记）
{{
    "requirement_summary": "需求文档核心内容概述（2-3句话）",
    "optimized_title": "优化后的标题",
    "optimized_description": "优化后的完整描述（使用markdown格式）",
    "acceptance_criteria": ["验收标准1", "验收标准2"],
    "risks": ["风险点1", "风险点2"],
    "optimization_summary": "优化说明",
    "test_points": ["测试点1", "测试点2", "测试点3"]
}}"""

    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'progress', 'message': '正在分析需求文档...', 'progress': 10}, ensure_ascii=False)}\n\n"

            full_content = ""
            async for chunk in llm.astream(prompt):
                if chunk.content:
                    full_content += chunk.content
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'progress', 'message': '分析完成，正在解析结果...', 'progress': 90}, ensure_ascii=False)}\n\n"

            # 解析JSON
            clean = full_content.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            json_match = re.search(r'\{[\s\S]*\}', clean)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    yield f"data: {json.dumps({'type': 'result', 'data': result}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'AI返回格式解析失败'}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': 'AI返回格式解析失败'}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'progress': 100})}\n\n"

        except Exception as e:
            logger.error(f"AI优化文档流式输出失败: {e}\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.post("/{project_id}/ai_optimize_text", summary="AI优化任意文本为规范需求")
async def ai_optimize_text(
        project_id: int,
        request_data: dict,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    对任意文本内容（需求描述、文档片段、会议纪要等）进行AI优化，
    生成规范化的需求文档。
    返回SSE流式输出优化结果。
    """
    project, current_user = project_user

    try:
        text = request_data.get("text", "").strip()
        title = request_data.get("title", "").strip()

        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请输入需要优化的文本内容"
            )

        from config.settings import llm

        prompt = f"""你是一位资深的软件需求分析师和测试专家。请对以下输入内容进行全面分析和优化，将其转化为规范的需求文档。

## 输入内容
{f'- **标题**: {title}' if title else '（未提供标题，请根据内容自动生成）'}
- **内容**:
{text}

## 优化要求
请将上述内容整理为规范的需求文档，包含以下部分：

1. **标题**: 简洁、准确的需求标题（不超过100字符）
2. **描述**: 完整规范的需求描述，包括：
   - 功能概述（用1-2句话概括核心功能）
   - 用户场景（描述用户在什么场景下使用该功能）
   - 功能细节（列出具体的功能点）
   - 输入输出（明确输入条件和预期输出）
   - 边界条件（列出需要注意的边界情况）
   - 非功能性要求（如性能、安全性等，如适用）
3. **验收标准**: 列出明确的验收标准，方便测试人员编写用例
4. **潜在风险**: 指出可能存在的技术风险或业务风险

## 重要约束
- 严禁编造原文中未提及的功能需求
- 可以对原文进行合理推断和补充，但不能改变原意
- 需求描述应该结构化、可测试
- 如果输入内容不是需求相关的，请尽量提取其中的功能性内容

## 输出格式
请严格按以下JSON格式输出（不要包含markdown代码块标记）：
{{
    "optimized_title": "优化后的标题",
    "optimized_description": "优化后的完整描述（使用markdown格式）",
    "acceptance_criteria": ["验收标准1", "验收标准2", "..."],
    "risks": ["风险点1", "风险点2"],
    "optimization_summary": "优化说明（简要说明做了哪些处理）"
}}"""

        async def generate():
            try:
                full_content = ""
                async for chunk in llm.astream(prompt):
                    if chunk.content:
                        full_content += chunk.content
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

                # 尝试解析完整的JSON结果
                try:
                    clean_content = full_content.strip()
                    if clean_content.startswith("```json"):
                        clean_content = clean_content[7:]
                    if clean_content.startswith("```"):
                        clean_content = clean_content[3:]
                    if clean_content.endswith("```"):
                        clean_content = clean_content[:-3]
                    clean_content = clean_content.strip()

                    result = json.loads(clean_content)
                    yield f"data: {json.dumps({'type': 'result', 'data': result}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    # 尝试用正则提取JSON
                    json_match = re.search(r'\{[\s\S]*\}', full_content)
                    if json_match:
                        try:
                            result = json.loads(json_match.group())
                            yield f"data: {json.dumps({'type': 'result', 'data': result}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            yield f"data: {json.dumps({'type': 'error', 'message': 'AI返回格式解析失败'}, ensure_ascii=False)}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'AI返回格式解析失败'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"AI优化文本流式输出失败: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI优化文本失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI优化文本失败: {str(e)}"
        )


@router.put("/{project_id}/requirements/{requirement_id}/apply_optimization", summary="应用AI优化结果")
async def apply_ai_optimization(
        project_id: int,
        requirement_id: int,
        optimization_data: dict,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """将AI优化的结果应用到需求上"""
    project, current_user = project_user

    try:
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求不存在")

        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求不属于该项目")

        # 更新需求
        if "optimized_title" in optimization_data:
            requirement.title = optimization_data["optimized_title"]
        if "optimized_description" in optimization_data:
            # 合并验收标准和风险到描述中
            desc = optimization_data["optimized_description"]
            if optimization_data.get("acceptance_criteria"):
                desc += "\n\n## 验收标准\n"
                for i, criteria in enumerate(optimization_data["acceptance_criteria"], 1):
                    desc += f"{i}. {criteria}\n"
            if optimization_data.get("risks"):
                desc += "\n## 潜在风险\n"
                for i, risk in enumerate(optimization_data["risks"], 1):
                    desc += f"{i}. {risk}\n"
            requirement.description = desc

        await requirement.save()

        return {
            "message": "AI优化结果已应用",
            "requirement": {
                "id": requirement.id,
                "title": requirement.title,
                "description": requirement.description,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"应用AI优化结果失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"应用AI优化结果失败: {str(e)}"
        )
