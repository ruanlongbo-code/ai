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
    """根据需求生成测试用例接口（含场景分组和用例集）"""
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

        requirement_content = f"""
            需求标题：{requirement.title}
            需求描述：{requirement.description}
            需求优先级：{requirement.priority}
            需求状态：{requirement.status}
            """

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
                yield f"data: {json.dumps({'type': 'start', 'message': '【开始生成】调用AI大模型...', 'progress': 5}, ensure_ascii=False)}\n\n"

                workflow_instance = GeneratorTestCaseWorkflow()
                workflow = workflow_instance.create_workflow()

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
                yield f"data: {json.dumps({'type': 'complete', 'message': f'测试用例生成完成！共生成 {generated_cases_count} 个测试用例（含场景分组）', 'progress': 100}, ensure_ascii=False)}\n\n"

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
        url: Optional[str] = Form(None, description="需求文档链接（仅支持公开可访问的链接）"),
        text: Optional[str] = Form(None, description="粘贴的文档文本内容（推荐用于飞书等需要登录的云文档）"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """从上传的文档文件、粘贴的文本内容或文档链接中，使用AI提取结构化的需求信息。"""
    project, current_user = project_user

    try:
        if not (file and file.filename) and not text and not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传文档文件、粘贴文档内容或提供文档链接"
            )

        extracted_text = ""

        if file and file.filename:
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

        elif text:
            extracted_text = text.strip()
            if not extracted_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="粘贴的文本内容为空，请确认已正确复制文档内容"
                )

        elif url:
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
