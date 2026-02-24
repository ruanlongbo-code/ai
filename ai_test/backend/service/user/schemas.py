"""
用户模块数据模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: EmailStr = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    real_name: Optional[str] = Field(None, max_length=50, description="真实姓名")


class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    real_name: Optional[str] = Field(None, description="真实姓名")
    avatar: Optional[str] = Field(None, description="头像URL")
    feishu_user_key: Optional[str] = Field(None, description="飞书项目UserKey")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class UserLoginResponse(BaseModel):
    """用户登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user: UserResponse = Field(..., description="用户信息")


class TokenVerifyResponse(BaseModel):
    """Token验证响应模型"""
    valid: bool = Field(..., description="是否有效")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    expires_at: datetime = Field(..., description="过期时间")


class UserActivateRequest(BaseModel):
    """用户激活请求模型"""
    user_id: int = Field(..., description="用户ID")
    is_active: bool = Field(..., description="是否激活")


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class UserProfileResponse(BaseModel):
    """用户个人信息响应模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    real_name: Optional[str] = Field(None, description="真实姓名")
    avatar: Optional[str] = Field(None, description="头像URL")
    feishu_user_key: Optional[str] = Field(None, description="飞书项目UserKey")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    """用户个人信息更新请求模型"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    real_name: Optional[str] = Field(None, max_length=50, description="真实姓名")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    feishu_user_key: Optional[str] = Field(None, max_length=128, description="飞书项目UserKey")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class UserDisableRequest(BaseModel):
    """禁用用户请求模型"""
    user_id: int = Field(..., description="用户ID", gt=0)


class ChangePasswordRequest(BaseModel):
    """用户修改密码请求模型"""
    old_password: str = Field(..., min_length=6, max_length=128, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class AdminResetPasswordRequest(BaseModel):
    """管理员重置用户密码请求模型"""
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
