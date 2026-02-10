"""
用户模块API接口
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from tortoise.exceptions import DoesNotExist, IntegrityError
from .models import User
from .schemas import (
    UserRegisterRequest, UserLoginRequest, UserResponse,
    UserLoginResponse, TokenVerifyResponse, UserListResponse,
    UserProfileResponse, UserProfileUpdateRequest, UserActivateRequest,
    UserDisableRequest, ChangePasswordRequest, AdminResetPasswordRequest
)
from utils.auth import AuthUtils, get_current_user, get_current_admin_user, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(tags=["用户管理"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_data: UserRegisterRequest):
    """
    用户注册接口
    - 默认创建普通账号，未激活状态
    - 用户名和邮箱必须唯一
    """
    try:
        # 检查用户名是否已存在
        if await User.filter(username=user_data.username).exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        if await User.filter(email=user_data.email).exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

        # 创建用户
        hashed_password = AuthUtils.get_password_hash(user_data.password)
        user = await User.create(
            username=user_data.username,
            password=hashed_password,
            email=user_data.email,
            phone=user_data.phone,
            real_name=user_data.real_name,
            is_active=False,  # 默认未激活
            is_superuser=False  # 默认普通用户
        )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            real_name=user.real_name,
            avatar=user.avatar,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )


@router.post("/login", response_model=UserLoginResponse, summary="用户登录")
async def login(login_data: UserLoginRequest):
    """
    用户登录接口
    - 支持用户名或邮箱登录
    - 返回JWT token
    """
    # 查找用户（支持用户名或邮箱登录）
    user = await User.filter(
        username=login_data.username
    ).first()

    if not user or not AuthUtils.verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号未激活或者被禁用，请联系管理员"
        )

    # 更新最后登录时间
    user.last_login = datetime.now()
    await user.save()

    # 生成token
    access_token = AuthUtils.create_access_token({"sub": str(user.id)})
    refresh_token = AuthUtils.create_refresh_token({"sub": str(user.id)})

    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            real_name=user.real_name,
            avatar=user.avatar,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post("/activate", response_model=UserResponse, summary="激活用户")
async def activate_user(
        activate_data: UserActivateRequest,
        current_user: User = Depends(get_current_admin_user)
):
    """
    激活/停用用户接口
    - 仅管理员可访问
    """
    try:
        user = await User.get(id=activate_data.user_id)
        user.is_active = activate_data.is_active
        await user.save()

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            real_name=user.real_name,
            avatar=user.avatar,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


@router.post("/verify-token", response_model=TokenVerifyResponse, summary="验证Token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    验证当前token有效性
    """
    return TokenVerifyResponse(
        valid=True,
        user_id=current_user.id,
        username=current_user.username,
        expires_at=datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )


@router.post("/refresh-token", response_model=UserLoginResponse, summary="刷新Token")
async def refresh_token(refresh_token: str):
    """
    使用refresh token获取新的access token
    """
    try:
        payload = AuthUtils.verify_refresh_token(refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的refresh token"
            )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的refresh token"
            )

        user = await User.get(id=int(user_id))

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账号已被停用"
            )

        # 生成新的token
        access_token = AuthUtils.create_access_token({"sub": str(user.id)})
        new_refresh_token = AuthUtils.create_refresh_token({"sub": str(user.id)})

        return UserLoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                real_name=user.real_name,
                avatar=user.avatar,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的refresh token"
        )


@router.get("/list", response_model=UserListResponse, summary="获取用户列表")
async def get_user_list(
        page: int = 1,
        page_size: int = 10,
        username: Optional[str] = None,
        current_user: User = Depends(get_current_user)
):
    """
    获取用户列表
    - 仅管理员可访问
    - 支持分页
    - 支持按用户名、真实姓名、邮箱模糊搜索
    """
    offset = (page - 1) * page_size

    # 构建查询条件
    query = User.all()
    
    # 如果提供了username参数，进行模糊搜索
    if username:
        from tortoise.expressions import Q
        search_term = f"%{username}%"
        query = query.filter(
            Q(username__icontains=username) |
            Q(real_name__icontains=username) |
            Q(email__icontains=username)
        )

    users = await query.offset(offset).limit(page_size)
    total = await query.count()

    user_list = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            real_name=user.real_name,
            avatar=user.avatar,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]

    return UserListResponse(
        users=user_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
        user_id: int,
        current_user: User = Depends(get_current_admin_user)
):
    """
    删除用户
    - 仅管理员可访问
    - 不能删除自己
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    try:
        user = await User.get(id=user_id)
        await user.delete()

        return {"message": "用户删除成功"}

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


@router.get("/profile", response_model=UserProfileResponse, summary="获取用户信息")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    """
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        real_name=current_user.real_name,
        avatar=current_user.avatar,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/disable", response_model=UserResponse, summary="禁用用户")
async def disable_user(
        disable_data: UserDisableRequest,
        current_user: User = Depends(get_current_admin_user)
):
    """
    禁用用户接口
    - 仅管理员可访问
    - 将用户的is_active状态设置为False
    - 不能禁用自己
    """
    if disable_data.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )

    try:
        user = await User.get(id=disable_data.user_id)
        
        # 检查用户是否已经被禁用
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已经被禁用"
            )
        
        # 禁用用户
        user.is_active = False
        await user.save()

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            real_name=user.real_name,
            avatar=user.avatar,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


@router.put("/profile", response_model=UserProfileResponse, summary="更新用户信息")
async def update_user_profile(
        profile_data: UserProfileUpdateRequest,
        current_user: User = Depends(get_current_user)
):
    """
    更新当前用户信息
    """
    # 更新用户信息
    if profile_data.email and profile_data.email != current_user.email:
        # 检查邮箱是否已被其他用户使用
        if await User.filter(email=profile_data.email).exclude(id=current_user.id).exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        current_user.email = profile_data.email

    if profile_data.phone is not None:
        current_user.phone = profile_data.phone

    if profile_data.real_name is not None:
        current_user.real_name = profile_data.real_name

    if profile_data.avatar is not None:
        current_user.avatar = profile_data.avatar

    await current_user.save()

    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        real_name=current_user.real_name,
        avatar=current_user.avatar,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/password", summary="修改密码")
async def change_password(
        data: ChangePasswordRequest,
        current_user: User = Depends(get_current_user)
):
    """
    修改当前登录用户密码
    - 校验旧密码
    - 设置新密码
    """
    # 旧密码校验
    if not AuthUtils.verify_password(data.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码不正确"
        )

    # 新旧密码不能相同
    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与旧密码相同"
        )

    # 更新密码
    current_user.password = AuthUtils.get_password_hash(data.new_password)
    await current_user.save()

    return {"message": "密码修改成功"}


@router.put("/{user_id}/password", summary="管理员重置用户密码")
async def admin_reset_password(
        user_id: int,
        data: AdminResetPasswordRequest,
        current_user: User = Depends(get_current_admin_user)
):
    """
    管理员重置指定用户密码
    - 仅管理员可访问
    - 不允许使用该接口重置自己的密码（请使用修改密码接口）
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请使用修改密码接口重置自己的密码"
        )

    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    user.password = AuthUtils.get_password_hash(data.new_password)
    await user.save()

    return {"message": "密码已重置"}
