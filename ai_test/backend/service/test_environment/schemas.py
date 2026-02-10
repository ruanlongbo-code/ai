"""
测试环境模块Pydantic模型
定义接口请求和响应的数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TestEnvironmentCreateRequest(BaseModel):
    """创建测试环境请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="环境名称")
    func_global: Optional[str] = Field(None, description="全局函数")

    class Config:
        from_attributes = True


class TestEnvironmentUpdateRequest(BaseModel):
    """编辑测试环境请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="环境名称")
    func_global: Optional[str] = Field(None, description="全局函数")

    class Config:
        from_attributes = True


class TestEnvironmentConfigCreateRequest(BaseModel):
    """创建测试环境配置请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    value: str = Field(..., min_length=1, max_length=500, description="配置值")

    class Config:
        from_attributes = True


class TestEnvironmentConfigUpdateRequest(BaseModel):
    """编辑测试环境配置请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="配置名称")
    value: Optional[str] = Field(None, min_length=1, max_length=500, description="配置值")

    class Config:
        from_attributes = True


class TestEnvironmentConfigResponse(BaseModel):
    """测试环境配置响应模型"""
    id: int = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    value: str = Field(..., description="配置值")
    environment_id: int = Field(..., description="所属环境ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class TestEnvironmentResponse(BaseModel):
    """测试环境响应模型"""
    id: int = Field(..., description="环境ID")
    name: str = Field(..., description="环境名称")
    func_global: Optional[str] = Field(None, description="全局函数")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class TestEnvironmentDbCreateRequest(BaseModel):
    """创建测试环境数据库配置请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="数据库名称")
    type: str = Field(..., min_length=1, max_length=50, description="数据库类型")
    config: dict = Field(..., description="数据库配置")

    class Config:
        from_attributes = True


class TestEnvironmentDbUpdateRequest(BaseModel):
    """编辑测试环境数据库配置请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="数据库名称")
    type: Optional[str] = Field(None, min_length=1, max_length=50, description="数据库类型")
    config: Optional[dict] = Field(None, description="数据库配置")

    class Config:
        from_attributes = True


class TestEnvironmentDbResponse(BaseModel):
    """测试环境数据库配置响应模型"""
    id: int = Field(..., description="数据库配置ID")
    name: str = Field(..., description="数据库名称")
    type: str = Field(..., description="数据库类型")
    config: dict = Field(..., description="数据库配置")
    environment_id: int = Field(..., description="所属环境ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class TestEnvironmentListResponse(BaseModel):
    """测试环境列表响应模型"""
    environments: List[TestEnvironmentResponse] = Field(..., description="环境列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class TestEnvironmentConfigDetailResponse(BaseModel):
    """测试环境配置详情响应模型（不包含时间字段）"""
    id: int = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    value: str = Field(..., description="配置值")
    environment_id: int = Field(..., description="所属环境ID")

    class Config:
        from_attributes = True


class TestEnvironmentDbDetailResponse(BaseModel):
    """测试环境数据库配置详情响应模型（不包含时间字段）"""
    id: int = Field(..., description="数据库配置ID")
    name: str = Field(..., description="数据库名称")
    type: str = Field(..., description="数据库类型")
    config: dict = Field(..., description="数据库配置")
    environment_id: int = Field(..., description="所属环境ID")

    class Config:
        from_attributes = True


class TestEnvironmentDetailResponse(BaseModel):
    """测试环境详情响应模型"""
    id: int = Field(..., description="环境ID")
    name: str = Field(..., description="环境名称")
    func_global: Optional[str] = Field(None, description="全局函数")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    configs: List[TestEnvironmentConfigDetailResponse] = Field(default=[], description="环境配置列表")
    databases: List[TestEnvironmentDbDetailResponse] = Field(default=[], description="数据库配置列表")

    class Config:
        from_attributes = True