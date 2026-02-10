"""
测试环境管理API
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional

from .models import TestEnvironment, TestEnvironmentConfig, TestEnvironmentDb
from .schemas import TestEnvironmentListResponse, TestEnvironmentResponse, TestEnvironmentCreateRequest, TestEnvironmentUpdateRequest, TestEnvironmentConfigCreateRequest, TestEnvironmentConfigUpdateRequest, TestEnvironmentConfigResponse, TestEnvironmentDbCreateRequest, TestEnvironmentDbUpdateRequest, TestEnvironmentDbResponse, TestEnvironmentDetailResponse, TestEnvironmentConfigDetailResponse, TestEnvironmentDbDetailResponse
from service.project.models import Project, ProjectMember
from service.user.models import User
from utils.auth import get_current_user
from utils.permissions import verify_admin_or_project_member, verify_admin_or_project_editor, verify_test_environment_permission

router = APIRouter()


@router.get("/{project_id}/environments", response_model=TestEnvironmentListResponse, summary="获取测试环境列表")
async def get_test_environments(
        project_id: int,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取测试环境列表接口
    
    权限要求：
    - 只有项目成员和管理员可以访问
    
    参数：
    - project_id: 项目ID（必填）
    - page: 页码，默认1
    - page_size: 每页数量，默认10，范围1-100
    
    返回：
    - 分页的测试环境列表
    """
    try:
        project, current_user = project_and_user

        # 计算分页偏移量
        offset = (page - 1) * page_size

        # 查询测试环境总数
        total = await TestEnvironment.filter(project_id=project_id).count()

        # 分页查询测试环境列表
        environments = await TestEnvironment.filter(
            project_id=project_id
        ).order_by("id").offset(offset).limit(page_size)

        # 构建响应数据
        environment_list = [
            TestEnvironmentResponse(
                id=env.id,
                name=env.name,
                func_global=env.func_global,
                project_id=env.project_id,
                created_at=env.created_at,
                updated_at=env.updated_at
            )
            for env in environments
        ]

        return TestEnvironmentListResponse(
            environments=environment_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取测试环境列表失败，请稍后重试"
        )


@router.get("/{project_id}/environments/{environment_id}", response_model=TestEnvironmentDetailResponse, summary="获取测试环境详情")
async def get_test_environment_detail(
        project_id: int,
        environment_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
) -> TestEnvironmentDetailResponse:
    """
    获取测试环境详情接口
    
    权限要求：
    - 只有项目成员和管理员可以访问
    
    参数：
    - project_id: 项目ID（必填）
    - environment_id: 环境ID（必填）
    
    返回：
    - 测试环境详情，包含环境基本信息、所有配置和数据库配置
    """
    try:
        project, current_user = project_and_user

        # 查询测试环境
        environment = await TestEnvironment.get_or_none(id=environment_id, project_id=project_id)
        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在"
            )

        # 查询环境配置列表
        configs = await TestEnvironmentConfig.filter(environment_id=environment_id).order_by("id")
        config_list = [
            TestEnvironmentConfigDetailResponse(
                id=config.id,
                name=config.name,
                value=config.value,
                environment_id=config.environment_id
            )
            for config in configs
        ]

        # 查询数据库配置列表
        databases = await TestEnvironmentDb.filter(environment_id=environment_id).order_by("id")
        database_list = [
            TestEnvironmentDbDetailResponse(
                id=db.id,
                name=db.name,
                type=db.type,
                config=db.config,
                environment_id=db.environment_id
            )
            for db in databases
        ]

        # 构建详情响应
        return TestEnvironmentDetailResponse(
            id=environment.id,
            name=environment.name,
            func_global=environment.func_global,
            project_id=environment.project_id,
            created_at=environment.created_at,
            updated_at=environment.updated_at,
            configs=config_list,
            databases=database_list
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取测试环境详情失败，请稍后重试"
        )


@router.post("/{project_id}/environments", response_model=TestEnvironmentResponse, summary="创建测试环境")
async def create_test_environment(
        project_id: int,
        environment_data: TestEnvironmentCreateRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    创建测试环境接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以创建测试环境
    
    参数：
    - project_id: 项目ID（必填）
    - environment_data: 测试环境数据（包含名称和全局函数）
    
    返回：
    - 创建的测试环境信息
    """
    try:
        project, current_user = project_and_user

        # 检查环境名称是否重复
        existing_environment = await TestEnvironment.get_or_none(
            project_id=project_id,
            name=environment_data.name
        )
        if existing_environment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该项目中已存在同名测试环境"
            )

        # 创建测试环境
        create_data = {
            "name": environment_data.name,
            "project_id": project_id
        }
        
        # 只有当func_global不为None时才添加到创建数据中
        if environment_data.func_global is not None:
            create_data["func_global"] = environment_data.func_global
            
        environment = await TestEnvironment.create(**create_data)

        return TestEnvironmentResponse(
            id=environment.id,
            name=environment.name,
            func_global=environment.func_global,
            project_id=environment.project_id,
            created_at=environment.created_at,
            updated_at=environment.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建测试环境失败，请稍后重试"
        )


@router.post("/{environment_id}/configs", response_model=TestEnvironmentConfigResponse, summary="创建测试环境配置")
async def create_test_environment_config(
        environment_id: int,
        config_data: TestEnvironmentConfigCreateRequest,
        environment_and_user: tuple[object, User] = Depends(verify_test_environment_permission)
):
    """
    创建测试环境配置接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以创建测试环境配置
    
    参数：
    - environment_id: 测试环境ID（必填）
    - config_data: 配置数据（包含配置名称和配置值）
    
    返回：
    - 创建的测试环境配置信息
    """
    try:
        environment, current_user = environment_and_user

        # 检查配置名称是否重复（联合唯一约束：environment + name）
        existing_config = await TestEnvironmentConfig.get_or_none(
            environment_id=environment_id,
            name=config_data.name
        )
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该测试环境中已存在同名配置"
            )

        # 创建测试环境配置
        config = await TestEnvironmentConfig.create(
            name=config_data.name,
            value=config_data.value,
            environment_id=environment_id
        )

        return TestEnvironmentConfigResponse(
            id=config.id,
            name=config.name,
            value=config.value,
            environment_id=config.environment_id,
            created_at=config.created_at,
            updated_at=config.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建测试环境配置失败，请稍后重试"
        )


@router.post("/{environment_id}/databases", response_model=TestEnvironmentDbResponse, summary="创建测试环境数据库配置")
async def create_test_environment_database(
        environment_id: int,
        db_data: TestEnvironmentDbCreateRequest,
        environment_and_user: tuple[object, User] = Depends(verify_test_environment_permission)
):
    """
    创建测试环境数据库配置接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以访问
    
    参数：
    - environment_id: 测试环境ID
    - db_data: 数据库配置数据
    
    返回：
    - 创建的数据库配置信息
    """
    try:
        environment, user = environment_and_user
        
        # 检查数据库名称是否已存在（联合唯一约束）
        existing_db = await TestEnvironmentDb.filter(
            environment_id=environment_id,
            name=db_data.name
        ).first()
        
        if existing_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"数据库配置名称 '{db_data.name}' 在该环境中已存在"
            )
        
        # 创建数据库配置
        db_config = await TestEnvironmentDb.create(
            environment_id=environment_id,
            name=db_data.name,
            type=db_data.type,
            config=db_data.config
        )

        return TestEnvironmentDbResponse(
            id=db_config.id,
            name=db_config.name,
            type=db_config.type,
            config=db_config.config,
            environment_id=db_config.environment_id,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建测试环境数据库配置失败，请稍后重试"
        )


@router.put("/{project_id}/environments/{environment_id}", response_model=TestEnvironmentResponse, summary="编辑测试环境")
async def update_test_environment(
        project_id: int,
        environment_id: int,
        environment_data: TestEnvironmentUpdateRequest,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    编辑测试环境接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以编辑测试环境
    
    参数：
    - project_id: 项目ID（必填）
    - environment_id: 环境ID（必填）
    - environment_data: 测试环境数据（包含名称和全局函数）
    
    返回：
    - 更新后的测试环境信息
    """
    try:
        project, current_user = project_and_user

        # 检查测试环境是否存在且属于指定项目
        environment = await TestEnvironment.get_or_none(
            id=environment_id,
            project_id=project_id
        )
        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在"
            )

        # 检查环境名称是否重复（如果要更新名称）
        if environment_data.name and environment_data.name != environment.name:
            existing_environment = await TestEnvironment.get_or_none(
                project_id=project_id,
                name=environment_data.name
            )
            if existing_environment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该项目中已存在同名测试环境"
                )

        # 更新测试环境
        update_data = {}
        if environment_data.name is not None:
            update_data['name'] = environment_data.name
        if environment_data.func_global is not None:
            update_data['func_global'] = environment_data.func_global

        if update_data:
            await environment.update_from_dict(update_data)
            await environment.save()

        return TestEnvironmentResponse(
            id=environment.id,
            name=environment.name,
            func_global=environment.func_global,
            project_id=environment.project_id,
            created_at=environment.created_at,
            updated_at=environment.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="编辑测试环境失败，请稍后重试"
        )


@router.put("/{environment_id}/configs/{config_id}", response_model=TestEnvironmentConfigResponse, summary="编辑测试环境配置")
async def update_test_environment_config(
        environment_id: int,
        config_id: int,
        config_data: TestEnvironmentConfigUpdateRequest,
        environment_and_user: tuple[object, User] = Depends(verify_test_environment_permission)
):
    """
    编辑测试环境配置接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以编辑测试环境配置
    
    参数：
    - environment_id: 环境ID（必填）
    - config_id: 配置ID（必填）
    - config_data: 测试环境配置数据（包含名称和值）
    
    返回：
    - 更新后的测试环境配置信息
    """
    try:
        environment, current_user = environment_and_user

        # 检查配置是否存在且属于指定环境
        config = await TestEnvironmentConfig.get_or_none(
            id=config_id,
            environment_id=environment_id
        )
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境配置不存在"
            )

        # 检查配置名称是否重复（如果要更新名称）
        if config_data.name and config_data.name != config.name:
            existing_config = await TestEnvironmentConfig.get_or_none(
                environment_id=environment_id,
                name=config_data.name
            )
            if existing_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该环境中已存在同名配置"
                )

        # 更新配置
        update_data = {}
        if config_data.name is not None:
            update_data['name'] = config_data.name
        if config_data.value is not None:
            update_data['value'] = config_data.value

        if update_data:
            await config.update_from_dict(update_data)
            await config.save()

        return TestEnvironmentConfigResponse(
            id=config.id,
            name=config.name,
            value=config.value,
            environment_id=config.environment_id,
            created_at=config.created_at,
            updated_at=config.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="编辑测试环境配置失败，请稍后重试"
        )


@router.put("/{environment_id}/databases/{db_id}", response_model=TestEnvironmentDbResponse, summary="编辑测试环境数据库配置")
async def update_test_environment_database(
        environment_id: int,
        db_id: int,
        db_data: TestEnvironmentDbUpdateRequest,
        environment_and_user: tuple[object, User] = Depends(verify_test_environment_permission)
):
    """
    编辑测试环境数据库配置接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以编辑测试环境数据库配置
    
    参数：
    - environment_id: 环境ID（必填）
    - db_id: 数据库配置ID（必填）
    - db_data: 测试环境数据库配置数据（包含名称、类型和配置）
    
    返回：
    - 更新后的测试环境数据库配置信息
    """
    try:
        environment, current_user = environment_and_user

        # 检查数据库配置是否存在且属于指定环境
        db_config = await TestEnvironmentDb.get_or_none(
            id=db_id,
            environment_id=environment_id
        )
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境数据库配置不存在"
            )

        # 检查数据库名称是否重复（如果要更新名称）
        if db_data.name and db_data.name != db_config.name:
            existing_db = await TestEnvironmentDb.get_or_none(
                environment_id=environment_id,
                name=db_data.name
            )
            if existing_db:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该环境中已存在同名数据库配置"
                )

        # 更新数据库配置
        update_data = {}
        if db_data.name is not None:
            update_data['name'] = db_data.name
        if db_data.type is not None:
            update_data['type'] = db_data.type
        if db_data.config is not None:
            update_data['config'] = db_data.config

        if update_data:
            await db_config.update_from_dict(update_data)
            await db_config.save()

        return TestEnvironmentDbResponse(
            id=db_config.id,
            name=db_config.name,
            type=db_config.type,
            config=db_config.config,
            environment_id=db_config.environment_id,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="编辑测试环境数据库配置失败，请稍后重试"
        )


@router.delete("/{project_id}/environments/{environment_id}", summary="删除测试环境")
async def delete_test_environment(
        project_id: int,
        environment_id: int,
        project_and_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    删除测试环境
    
    需要项目管理员、编辑者或系统管理员权限
    """
    project, user = project_and_user
    
    try:
        # 检查测试环境是否存在
        environment = await TestEnvironment.get_or_none(id=environment_id, project_id=project_id)
        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在"
            )
        
        # 删除测试环境（级联删除相关配置和数据库配置）
        await environment.delete()
        
        return {"message": "测试环境删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除测试环境失败，请稍后重试"
        )


@router.delete("/{environment_id}/configs/{config_id}", summary="删除测试环境配置")
async def delete_test_environment_config(
        environment_id: int,
        config_id: int,
        environment_and_user: tuple[object, User] = Depends(verify_test_environment_permission)
):
    """
    删除测试环境配置
    
    需要项目管理员、编辑者或系统管理员权限
    """
    environment, user = environment_and_user
    
    try:
        # 检查配置是否存在
        config = await TestEnvironmentConfig.get_or_none(id=config_id, environment_id=environment_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境配置不存在"
            )
        
        # 删除配置
        await config.delete()
        
        return {"message": "测试环境配置删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除测试环境配置失败，请稍后重试"
        )


@router.delete("/{environment_id}/databases/{db_id}", summary="删除测试环境数据库配置")
async def delete_test_environment_database(
        environment_id: int,
        db_id: int,
        environment_and_user: tuple[object, User] = Depends(verify_test_environment_permission)
):
    """
    删除测试环境数据库配置
    
    需要项目管理员、编辑者或系统管理员权限
    """
    environment, user = environment_and_user
    
    try:
        # 检查数据库配置是否存在
        db_config = await TestEnvironmentDb.get_or_none(id=db_id, environment_id=environment_id)
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境数据库配置不存在"
            )
        
        # 删除数据库配置
        await db_config.delete()
        
        return {"message": "测试环境数据库配置删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除测试环境数据库配置失败，请稍后重试"
        )