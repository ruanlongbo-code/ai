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
from .models import RequirementDoc, FunctionalCase
from .schemas import (RequirementCreateRequest, RequirementResponse, RequirementUpdateRequest, RequirementDetailItem,
                      RequirementDetailListResponse, RequirementReviewRequest,
    FunctionalCaseSimple, FunctionalCaseListResponse, FunctionalCaseCreateRequest,
    FunctionalCaseUpdateRequest, FunctionalCaseResponse, FunctionalCaseReviewRequest)
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
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    添加需求接口
    
    权限要求：
    - 只有项目的负责人和管理员才能添加需求
    
    业务逻辑：
    - 需求的创建人为当前请求的用户
    
    参数：
    - requirement_data: 需求创建请求数据
    """
    project, current_user = project_user

    try:
        # 如果指定了模块ID，需要验证模块是否存在
        if requirement_data.module_id:
            # 查询模块是否存在
            module = await ProjectModule.get_or_none(id=requirement_data.module_id)
            if not module:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的项目模块不存在"
                )
        else:
            # 如果没有指定模块ID，返回错误
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模块ID不能为空"
            )

        # 使用数据库事务确保数据一致性
        async with in_transaction() as conn:
            # 仅保存到数据库，不再同步知识库
            requirement = await RequirementDoc.create(
                module_id=requirement_data.module_id,
                title=requirement_data.title,
                doc_no=requirement_data.doc_no,
                description=requirement_data.description,
                priority=requirement_data.priority,
                creator_id=current_user.id,
                status="draft",
                using_db=conn
            )
        # 返回创建的需求信息
        return RequirementResponse(
            id=requirement.id,
            module_id=requirement.module_id,
            title=requirement.title,
            doc_no=requirement.doc_no,
            description=requirement.description,
            priority=requirement.priority,
            status=requirement.status,
            creator_id=current_user.id,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
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
    """
    获取需求详细列表接口
    
    权限要求：
    - 只有项目成员和管理员可以访问需求列表
    
    参数：
    - project_id: 项目ID
    - module_id: 可选，按模块筛选
    - status: 可选，按状态筛选
    - priority: 可选，按优先级筛选
    - page: 页码，默认为1
    - page_size: 每页数量，默认为20
    """
    project, current_user = project_user

    try:
        # 获取项目所有模块
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

        # 构建查询条件
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

        # 获取总数
        total = await RequirementDoc.filter(**query_filters).count()
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        # 获取分页数据
        offset = (page - 1) * page_size
        requirements = await RequirementDoc.filter(**query_filters).offset(offset).limit(page_size).all()

        # 构建详细需求列表
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
        # 重新抛出HTTP异常
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
    """
    获取需求详情接口
    
    权限要求：
    - 项目成员、编辑者、负责人和管理员都可以访问
    
    参数：
    - project_id: 项目ID
    - requirement_id: 需求ID
    
    返回：
    - 需求详情信息
    """
    project, current_user = project_user
    
    try:
        # 查询需求是否存在
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        # 验证需求是否属于该项目
        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )
        
        return RequirementResponse(
            id=requirement.id,
            module_id=requirement.module_id,
            title=requirement.title,
            doc_no=requirement.doc_no,
            description=requirement.description,
            priority=requirement.priority,
            status=requirement.status,
            creator_id=requirement.creator_id,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )
    
    except HTTPException:
        # 重新抛出HTTP异常
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
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    删除需求接口
    
    权限要求：
    - 只有项目负责人和管理员可以访问
    
    业务逻辑：
    - 验证需求归属后，直接删除数据库记录（不再同步知识库）
    
    参数：
    - project_id: 项目ID
    - requirement_id: 需求ID
    """
    project, current_user = project_user

    try:
        # 查询需求是否存在
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        # 验证需求是否属于该项目
        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )
        # 删除数据库中的需求
        await requirement.delete()

        return {"message": "需求删除成功"}

    except HTTPException:
        # 重新抛出HTTP异常
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
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_owner)
):
    """
    修改需求接口
    
    权限要求：
    - 只有项目负责人和管理员可以访问
    
    业务逻辑：
    - 仅更新数据库中的需求信息（不再同步知识库）
    
    参数：
    - project_id: 项目ID
    - requirement_id: 需求ID
    - request: 修改需求的请求数据
    """
    project, current_user = project_user

    try:
        # 查询需求是否存在
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        # 验证需求是否属于该项目
        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )

        # 更新数据库中的需求
        requirement.title = request.title
        requirement.description = request.description
        requirement.priority = request.priority
        requirement.status = request.status

        await requirement.save()

        return RequirementResponse(
            id=requirement.id,
            module_id=requirement.module_id,
            title=requirement.title,
            description=requirement.description,
            priority=requirement.priority,
            status=requirement.status,
            creator_id=requirement.creator_id,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
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
    """
    审核需求接口
    
    权限要求：
    - 项目编辑者、负责人和管理员可以审核需求
    
    业务逻辑：
    - 更新需求的状态和审核意见
    - 记录审核时间
    
    参数：
    - project_id: 项目ID
    - requirement_id: 需求ID
    - request: 审核请求数据
    """
    project, current_user = project_user

    try:
        # 查询需求是否存在
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        # 验证需求是否属于该项目
        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )

        # 更新需求状态
        requirement.status = request.status
        
        await requirement.save()

        return RequirementResponse(
            id=requirement.id,
            module_id=requirement.module_id,
            title=requirement.title,
            description=requirement.description,
            priority=requirement.priority,
            status=requirement.status,
            creator_id=requirement.creator_id,
            created_at=requirement.created_at,
            updated_at=requirement.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="需求审核失败，请稍后重试"
        )


@router.get("/{project_id}/functional_cases", response_model=FunctionalCaseListResponse, summary="获取功能用例列表")
async def get_functional_cases_list(
        project_id: int,
        page: int = 1,
        page_size: int = 20,
        requirement_id: Optional[int] = None,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取功能用例列表接口
    
    权限要求：
    - 只有项目成员和管理员可以访问
    
    业务逻辑：
    - 获取当前项目所有的功能用例，按需求进行分组并返回
    - 支持分页和按需求过滤
    - 每个用例返回基本信息：ID、编号、名称、优先级、状态、关联需求ID
    
    参数：
    - project_id: 项目ID
    - page: 页码，从1开始，默认1
    - page_size: 每页数量，默认为20，最大100
    - requirement_id: 需求ID过滤，为空则获取所有
    """
    project, current_user = project_user

    # 验证分页参数
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    try:

        # 获取项目所有模块
        modules = await ProjectModule.filter(project_id=project_id).all()
        module_ids = [module.id for module in modules]

        # 获取项目所有需求
        requirements = await RequirementDoc.filter(
            module_id__in=module_ids
        ).all()
        requirement_dict = {req.id: req.title for req in requirements}

        # 构建查询条件
        query_conditions = {}

        if requirement_id is not None:
            # 如果指定了需求ID，只查询该需求下的用例
            if requirement_id not in requirement_dict:
                # 检查需求是否存在
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的需求不存在"
                )
            query_conditions['requirement_id'] = requirement_id
        else:
            # 如果没有指定需求ID，查询所有需求下的用例
            query_conditions['requirement_id__in'] = list(requirement_dict.keys())

        # 获取总数量（用于分页计算）
        total_count = await FunctionalCase.filter(**query_conditions).count()

        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取分页的功能用例
        functional_cases = await FunctionalCase.filter(
            **query_conditions
        ).offset(offset).limit(page_size).all()

        # 构建功能用例列表
        cases_list = []
        for case in functional_cases:
            # 获取需求标题
            requirement_title = requirement_dict.get(case.requirement_id, None)
            
            cases_list.append(
                FunctionalCaseSimple(
                    id=case.id,
                    case_no=case.case_no,
                    case_name=case.case_name,
                    priority=case.priority,
                    status=case.status,
                    requirement_id=case.requirement_id,
                    requirement_title=requirement_title,
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
        # 重新抛出HTTP异常
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
    """
    获取功能用例详情接口
    
    权限要求：
    - 项目成员、编辑者、负责人和管理员都可以访问
    
    参数：
    - project_id: 项目ID
    - case_id: 功能用例ID
    
    返回：
    - 功能用例详情信息
    """
    project, current_user = project_user
    
    try:
        # 查询功能用例是否存在
        case = await FunctionalCase.get_or_none(id=case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="功能用例不存在"
            )

        # 验证功能用例是否属于该项目（通过关联需求验证）
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
            preconditions=case.preconditions,
            test_steps=case.test_steps,
            test_data=case.test_data,
            expected_result=case.expected_result,
            actual_result=case.actual_result,
            requirement_id=case.requirement_id,
            creator_id=case.creator_id,
            created_at=case.created_at,
            updated_at=case.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
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
    """
    编辑功能用例接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员能够编辑功能用例
    
    业务逻辑：
    - 验证功能用例是否存在
    - 验证需求是否存在（如果提供了requirement_id）
    - 更新功能用例信息
    
    参数：
    - project_id: 项目ID
    - case_id: 功能用例ID
    - case_data: 功能用例更新请求数据
    """
    project, current_user = project_user

    try:
        # 查询功能用例是否存在
        case = await FunctionalCase.get_or_none(id=case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的功能用例不存在"
            )

        # 如果提供了requirement_id，验证需求是否存在且属于当前项目
        # 验证关联需求是否存在且属于当前项目
        if case_data.requirement_id:
            # 通过需求id查找需求
            requirement = await RequirementDoc.get_or_none(
                id=case_data.requirement_id,
            )
            if not requirement:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的需求不存在"
                )
            # 获取需求所属的模块
            module = await requirement.module
            # 验证模块是否属于当前项目
            if module and module.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="关联需求所属的模块不属于当前项目"
                )

        # 更新功能用例信息
        update_data = {}
        for field, value in case_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        if update_data:
            await case.update_from_dict(update_data)
            await case.save()

        # 重新查询更新后的用例
        updated_case = await FunctionalCase.get(id=case_id)

        return FunctionalCaseResponse(
            id=updated_case.id,
            case_no=updated_case.case_no,
            case_name=updated_case.case_name,
            priority=updated_case.priority,
            status=updated_case.status,
            preconditions=updated_case.preconditions,
            test_steps=updated_case.test_steps,
            test_data=updated_case.test_data,
            expected_result=updated_case.expected_result,
            actual_result=updated_case.actual_result,
            requirement_id=updated_case.requirement_id,
            creator_id=updated_case.creator_id,
            created_at=updated_case.created_at,
            updated_at=updated_case.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
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
    """
    删除功能用例接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以删除功能用例
    
    业务逻辑：
    - 验证功能用例是否存在
    - 验证功能用例是否属于指定项目
    - 删除功能用例
    
    参数：
    - project_id: 项目ID
    - case_id: 功能用例ID
    """
    project, current_user = project_user

    try:
        # 查询功能用例是否存在
        case = await FunctionalCase.get_or_none(id=case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的功能用例不存在"
            )

        # 验证功能用例是否属于指定项目（通过关联的需求验证）
        if case.requirement_id:
            requirement = await RequirementDoc.get_or_none(id=case.requirement_id)
            if requirement:
                module = await ProjectModule.get_or_none(id=requirement.module_id)
                if not module or module.project_id != project_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="功能用例不属于指定项目"
                    )

        # 删除功能用例
        await case.delete()

        return {"message": "功能用例删除成功"}

    except HTTPException:
        # 重新抛出HTTP异常
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
    """
    创建功能用例
    
    权限要求：
    - 管理员
    - 项目负责人
    - 项目编辑者
    
    业务逻辑：
    - 创建人默认为当前发送请求的用户
    - 状态默认为待审核状态
    - 实际结果默认为空字符串
    """
    try:
        project, current_user = project_user
        # 验证关联需求是否存在且属于当前项目
        if case_data.requirement_id:
            # 通过需求id查找需求
            requirement = await RequirementDoc.get_or_none(
                id=case_data.requirement_id,
            )
            if not requirement:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的需求不存在"
                )
            # 获取需求所属的模块
            module = await requirement.module
            # 验证模块是否属于当前项目
            if module and module.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="关联需求所属的模块不属于当前项目"
                )
        # 创建功能用例
        case = await FunctionalCase.create(
            case_no=case_data.case_no,
            case_name=case_data.case_name,
            priority=case_data.priority,
            status="pending_review",  # 默认为待审核状态
            preconditions=case_data.preconditions,
            test_steps=case_data.test_steps,
            test_data=case_data.test_data,
            expected_result=case_data.expected_result,
            actual_result="",  # 默认为空字符串
            requirement_id=case_data.requirement_id,
            creator_id=current_user.id  # 创建人默认为当前用户
        )

        # 返回创建的功能用例信息
        return FunctionalCaseResponse(
            id=case.id,
            case_no=case.case_no,
            case_name=case.case_name,
            priority=case.priority,
            status=case.status,
            preconditions=case.preconditions,
            test_steps=case.test_steps,
            test_data=case.test_data,
            expected_result=case.expected_result,
            actual_result=case.actual_result,
            requirement_id=case.requirement_id,
            creator_id=case.creator_id,
            created_at=case.created_at,
            updated_at=case.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise e
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
    """
    审核功能用例接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以审核功能用例
    
    业务逻辑：
    - 验证功能用例是否存在且属于指定项目
    - 更新用例状态为审核通过(ready)或审核不通过(design)
    - 记录审核意见（可选）
    
    参数：
    - project_id: 项目ID
    - case_id: 功能用例ID
    - review_data: 审核请求数据（包含审核状态和意见）
    
    返回：
    - 审核后的功能用例信息
    """
    project, current_user = project_user

    try:
        # 查询功能用例是否存在
        case = await FunctionalCase.get_or_none(id=case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的功能用例不存在"
            )

        # 验证功能用例是否属于当前项目（通过关联的需求验证）
        if case.requirement_id:
            requirement = await RequirementDoc.get_or_none(id=case.requirement_id)
            if requirement:
                module = await ProjectModule.get_or_none(id=requirement.module_id)
                if not module or module.project_id != project_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="指定的功能用例不属于当前项目"
                    )

        # 验证审核状态的有效性
        valid_statuses = ["pass", "smoke","wait", "regression", "smoke", "obsolete"]
        if review_data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的审核状态，只能设置为: {', '.join(valid_statuses)}"
            )

        # 更新功能用例状态
        case.status = review_data.status
        await case.save()

        # 重新查询更新后的用例
        updated_case = await FunctionalCase.get(id=case_id)

        return FunctionalCaseResponse(
            id=updated_case.id,
            case_no=updated_case.case_no,
            case_name=updated_case.case_name,
            priority=updated_case.priority,
            status=updated_case.status,
            preconditions=updated_case.preconditions,
            test_steps=updated_case.test_steps,
            test_data=updated_case.test_data,
            expected_result=updated_case.expected_result,
            actual_result=updated_case.actual_result,
            requirement_id=updated_case.requirement_id,
            creator_id=updated_case.creator_id,
            created_at=updated_case.created_at,
            updated_at=updated_case.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
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
    根据需求生成测试用例接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以生成测试用例
    
    业务逻辑：
    - 从数据库获取详细的需求数据
    - 调用GeneratorTestCaseWorkflow生成功能测试用例
    - 使用SSE实时流式输出生成进度
    - 生成的用例直接保存到数据库
    
    参数：
    - project_id: 项目ID
    - requirement_id: 需求ID
    
    返回：
    - SSE流式输出生成进度和结果
    """
    project, current_user = project_user

    try:
        # 查询需求是否存在且属于当前项目
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的需求不存在"
            )

        # 验证需求是否属于当前项目（通过模块验证）
        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需求不属于当前项目"
            )

        # 构建需求文档内容
        requirement_content = f"""
            需求标题：{requirement.title}
            需求描述：{requirement.description}
            需求优先级：{requirement.priority}
            需求状态：{requirement.status}
            """

        async def generate_stream():
            """生成测试用例的流式输出函数"""
            try:
                # 发送开始生成的消息
                yield f"data: {json.dumps({'type': 'start', 'message': '【开始生成】调用AI大模型...'}, ensure_ascii=False)}\n\n"

                # 创建工作流实例
                workflow_instance = GeneratorTestCaseWorkflow()
                workflow = workflow_instance.create_workflow()

                # 流式执行工作流
                stream_response = workflow.stream(
                    {
                        "input_requirement": requirement_content
                    },
                    config={
                        "requirement_id": requirement.id,
                        "creator_id": current_user.id
                    },
                    subgraphs=True,
                    stream_mode=["messages", "custom"]
                )

                generated_cases_count = 0

                # 处理流式输出
                for item in stream_response:
                    if len(item) >= 3:
                        if item[1] == "messages":
                            # 发送进度消息
                            message = item[2][0].content if hasattr(item[2][0], 'content') else str(item[2][0])
                            yield f"data: {json.dumps({'type': 'progress', 'message': message}, ensure_ascii=False)}\n\n"
                        elif item[1] == "custom":
                            # 发送自定义消息
                            yield f"data: {json.dumps({'type': 'info', 'message': str(item[2])}, ensure_ascii=False)}\n\n"

                    # 模拟进度更新
                    await asyncio.sleep(0.1)
                # 发送完成消息
                yield f"data: {json.dumps({'type': 'complete', 'message': f'测试用例生成完成！共生成 {generated_cases_count} 个测试用例'}, ensure_ascii=False)}\n\n"

            except Exception as e:
                # 发送错误消息
                error_message = f"生成测试用例时发生错误：{str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_message}, ensure_ascii=False)}\n\n"
            finally:
                # 发送结束标记
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
    """
    从上传的文档文件、粘贴的文本内容或文档链接中，使用AI提取结构化的需求信息。

    支持三种输入方式（三选一）：
    1. 上传文件：支持 PDF、DOCX、TXT、MD 格式，最大 10MB
    2. 粘贴文本：直接粘贴文档内容（推荐用于飞书、Notion等需要登录才能访问的云文档）
    3. 文档链接：支持公开可访问的网页链接，会自动抓取页面内容

    返回：
    - title: 提取的需求标题
    - description: 提取的需求描述
    - priority: 建议的优先级（1=低, 2=中, 3=高）
    - raw_text: 从文档中提取的原始文本（前2000字符预览）
    """
    project, current_user = project_user

    try:
        # 验证输入：必须提供文件、文本或链接
        if not (file and file.filename) and not text and not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请上传文档文件、粘贴文档内容或提供文档链接"
            )

        extracted_text = ""

        # 方式一：从上传的文件中提取文本
        if file and file.filename:
            from utils.parser.requirement_document_parser import (
                extract_text_from_file,
                SUPPORTED_EXTENSIONS,
                MAX_FILE_SIZE
            )
            import os

            # 验证文件扩展名
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的文件格式: {ext}，支持的格式为: PDF, DOCX, TXT, MD"
                )

            # 读取文件内容
            file_content = await file.read()

            # 验证文件大小
            if len(file_content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="文件大小超过限制（最大10MB）"
                )

            # 提取文本
            try:
                extracted_text = extract_text_from_file(file.filename, file_content)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"文件解析失败: {str(e)}"
                )

        # 方式二：直接使用粘贴的文本内容
        elif text:
            extracted_text = text.strip()
            if not extracted_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="粘贴的文本内容为空，请确认已正确复制文档内容"
                )

        # 方式三：从URL中提取文本
        elif url:
            from utils.parser.requirement_document_parser import extract_text_from_url

            # 基本URL验证
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

        # 验证提取的文本不为空
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未能从文档中提取到有效文本内容"
            )

        # 截断过长的文本（避免超出LLM上下文窗口）
        max_text_length = 8000
        if len(extracted_text) > max_text_length:
            extracted_text_for_ai = extracted_text[:max_text_length] + "\n\n[... 文档内容过长，已截断 ...]"
        else:
            extracted_text_for_ai = extracted_text

        # 使用AI提取需求信息
        from config.prompts.parser.requirement_extractor import prompt as req_prompt
        from config.settings import llm
        from langchain_core.output_parsers import JsonOutputParser

        chain = req_prompt | llm | JsonOutputParser()
        ai_result = chain.invoke({"document_content": extracted_text_for_ai})

        # 构建返回结果
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
        root_prefix: str = Query("验证", description="根节点前缀"),
        root_suffix: str = Query("功能", description="根节点后缀"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    将需求关联的测试用例导出为 XMind 思维导图文件。

    默认模板格式：
    - 根节点：验证{需求标题}功能
    - 二级节点：{优先级} 用例标题（不含用例编号）
    - 三级叶子节点：前置条件、测试步骤、预期结果（编号列表合并为单行）
    - 默认不显示节点属性标记

    参数：
    - show_priority: 用例标题前显示优先级（默认 True）
    - show_case_id: 用例标题显示用例编号（默认 False）
    - show_node_labels: 注明节点属性标签（默认 False，如 "前置条件：xxx"）
    - root_prefix: 根节点前缀（默认 "验证"）
    - root_suffix: 根节点后缀（默认 "功能"）
    """
    project, current_user = project_user

    try:
        # 查询需求
        requirement = await RequirementDoc.get_or_none(id=requirement_id)
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )

        # 验证需求属于该项目
        module = await ProjectModule.get_or_none(id=requirement.module_id)
        if not module or module.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不属于该项目"
            )

        # 查询关联的测试用例
        cases = await FunctionalCase.filter(requirement_id=requirement_id).order_by('id').all()

        if not cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该需求下暂无测试用例，请先生成用例后再导出"
            )

        # 将 ORM 对象转为字典列表
        cases_data = []
        for case in cases:
            cases_data.append({
                "case_no": case.case_no,
                "case_name": case.case_name,
                "priority": case.priority,
                "preconditions": case.preconditions or "",
                "test_steps": case.test_steps or "",
                "expected_result": case.expected_result or "",
            })

        # 构建模板设置
        template_settings = {
            "show_priority": show_priority,
            "show_case_id": show_case_id,
            "show_node_labels": show_node_labels,
            "root_prefix": root_prefix,
            "root_suffix": root_suffix,
        }

        # 生成 XMind 文件
        from utils.xmind_generator import generate_xmind_file

        xmind_bytes = generate_xmind_file(
            requirement_title=requirement.title,
            test_cases=cases_data,
            template_settings=template_settings
        )

        # 构建文件名
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', requirement.title)[:50]
        filename = f"{safe_title}_测试用例.xmind"

        # 返回文件下载响应
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
