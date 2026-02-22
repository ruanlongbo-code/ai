"""
权限校验依赖模块
使用FastAPI依赖注入实现权限校验的封装
"""
from fastapi import HTTPException, Depends, status
from service.user.models import User
from service.project.models import Project, ProjectMember, BusinessLineMember
from utils.auth import get_current_user


async def verify_admin_or_project_member(
    project_id: int,
    current_user: User = Depends(get_current_user)
) -> tuple[Project, User]:
    """
    权限校验：管理员 + 项目成员
    
    适用场景：
    - 查看项目信息
    - 获取项目列表
    - 查看测试环境列表等只读操作
    
    Args:
        project_id: 项目ID
        current_user: 当前用户
        
    Returns:
        tuple[Project, User]: 项目对象和用户对象
        
    Raises:
        HTTPException: 项目不存在或权限不足
    """
    # 查询项目是否存在
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限校验：管理员、项目负责人或项目成员可以访问
    is_admin = current_user.is_superuser
    is_owner = project.owner_id == current_user.id
    is_member = await ProjectMember.exists(
        project_id=project_id,
        user_id=current_user.id,
        status=1  # 只有启用状态的成员才有权限
    )

    if not (is_admin or is_owner or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有项目成员和管理员可以访问"
        )

    return project, current_user


async def verify_admin_or_project_owner(
    project_id: int,
    current_user: User = Depends(get_current_user)
) -> tuple[Project, User]:
    """
    权限校验：管理员 + 项目负责人
    
    适用场景：
    - 管理项目成员
    - 修改项目设置
    - 删除项目等高权限操作
    
    Args:
        project_id: 项目ID
        current_user: 当前用户
        
    Returns:
        tuple[Project, User]: 项目对象和用户对象
        
    Raises:
        HTTPException: 项目不存在或权限不足
    """
    # 查询项目是否存在
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限校验：只有项目负责人和管理员才能访问
    if not (current_user.is_superuser or project.owner_id == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有项目负责人和管理员才能访问"
        )

    return project, current_user


async def verify_admin_or_project_editor(
    project_id: int,
    current_user: User = Depends(get_current_user)
) -> tuple[Project, User]:
    """
    权限校验：管理员 + 项目负责人 + 项目编辑者
    
    适用场景：
    - 创建/修改测试环境
    - 创建/修改测试用例
    - 执行测试等操作权限
    
    Args:
        project_id: 项目ID
        current_user: 当前用户
        
    Returns:
        tuple[Project, User]: 项目对象和用户对象
        
    Raises:
        HTTPException: 项目不存在或权限不足
    """
    # 查询项目是否存在
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限校验：管理员、项目负责人或项目编辑者可以访问
    is_admin = current_user.is_superuser
    is_owner = project.owner_id == current_user.id
    
    # 如果是管理员或项目负责人，直接通过
    if is_admin or is_owner:
        return project, current_user
    
    # 检查是否为项目编辑者（role=1）或负责人（role=2）
    member = await ProjectMember.get_or_none(
        project_id=project_id,
        user_id=current_user.id,
        status=1  # 只有启用状态的成员才有权限
    )
    is_editor_or_owner = member and member.role >= 1  # role >= 1 表示编辑者或负责人

    if not is_editor_or_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有项目负责人、项目编辑者和管理员可以访问"
        )

    return project, current_user


# 针对测试环境的特殊权限校验函数
async def verify_test_environment_permission(
    environment_id: int,
    current_user: User = Depends(get_current_user)
) -> tuple[object, User]:
    """
    测试环境权限校验：管理员 + 项目负责人 + 项目编辑者
    
    适用场景：
    - 创建/修改测试环境配置
    - 删除测试环境等操作
    
    Args:
        environment_id: 测试环境ID
        current_user: 当前用户
        
    Returns:
        tuple[TestEnvironment, User]: 测试环境对象和用户对象
        
    Raises:
        HTTPException: 测试环境不存在或权限不足
    """
    from service.test_environment.models import TestEnvironment
    
    # 查询测试环境是否存在
    environment = await TestEnvironment.get_or_none(id=environment_id).select_related('project')
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试环境不存在"
        )

    # 权限校验：管理员、项目负责人或项目编辑者可以访问
    is_admin = current_user.is_superuser
    is_owner = environment.project.owner_id == current_user.id
    
    # 检查是否为项目编辑者（role=1）或负责人（role=2）
    member = await ProjectMember.get_or_none(
        project_id=environment.project_id,
        user_id=current_user.id,
        status=1  # 只有启用状态的成员才有权限
    )
    is_editor_or_owner = member and member.role >= 1  # role >= 1 表示编辑者或负责人

    if not (is_admin or is_owner or is_editor_or_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，只有项目负责人、项目编辑者和管理员可以访问"
        )

    return environment, current_user


async def verify_schedule_access(
    project_id: int,
    current_user: User = Depends(get_current_user)
) -> tuple[Project, User]:
    """
    排期模块权限校验：管理员 + 项目负责人 + 项目成员 + 业务线成员

    适用场景：
    - 排期管理页面访问（查看迭代、排期条目列表）
    - 创建/更新排期条目
    - 提交日报等排期相关操作

    业务线成员（BusinessLineMember）也被视为有效项目成员。

    Returns:
        tuple[Project, User]: 项目对象和用户对象
    """
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 管理员直接通过
    if current_user.is_superuser:
        return project, current_user

    # 项目负责人直接通过
    if project.owner_id == current_user.id:
        return project, current_user

    # 检查是否为项目成员
    is_member = await ProjectMember.exists(
        project_id=project_id,
        user_id=current_user.id,
        status=1
    )
    if is_member:
        return project, current_user

    # 检查是否为该项目下任意业务线的成员
    from service.project.models import ProjectModule
    project_module_ids = await ProjectModule.filter(
        project_id=project_id
    ).values_list('id', flat=True)
    if project_module_ids:
        is_biz_member = await BusinessLineMember.exists(
            module_id__in=project_module_ids,
            user_id=current_user.id
        )
        if is_biz_member:
            return project, current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="权限不足，只有项目成员和业务线成员可以访问"
    )
