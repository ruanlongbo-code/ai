"""
项目模块Pydantic模型
定义接口请求和响应的数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class ProjectCreateRequest(BaseModel):
    """项目创建请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: str = Field(..., min_length=1, description="项目描述")


class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: int = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: str = Field(..., description="项目描述")
    owner_id: int = Field(..., description="项目负责人ID")
    # owner_name: str = Field(..., description="项目负责人姓名")
    # api_case_count: int = Field(default=0, description="接口用例总数")
    # functional_case_count: int = Field(default=0, description="功能用例总数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应模型"""
    projects: List[ProjectResponse] = Field(..., description="项目列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class ProjectMemberAddRequest(BaseModel):
    """项目成员添加请求模型"""
    user_id: int = Field(..., description="用户ID")
    role: int = Field(default=1, ge=0, le=1, description="成员角色（0=只读, 1=可操作）注意：不能设置为负责人角色")

    class Config:
        from_attributes = True


class ProjectMemberStatusUpdateRequest(BaseModel):
    """项目成员状态更新请求模型"""
    status: int = Field(..., ge=0, le=1, description="成员状态（0=禁用, 1=启用）")

    class Config:
        from_attributes = True


class ProjectMemberRoleUpdateRequest(BaseModel):
    """项目成员角色更新请求模型"""
    role: int = Field(..., ge=0, le=2, description="成员角色（0=只读, 1=可操作, 2=负责人）注意：只有管理员可以设置负责人角色")

    class Config:
        from_attributes = True


class ProjectUpdateRequest(BaseModel):
    """项目信息更新请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: str = Field(..., min_length=1, description="项目描述")

    class Config:
        from_attributes = True


class ProjectMemberResponse(BaseModel):
    """项目成员响应模型"""
    id: int = Field(..., description="成员ID")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    real_name: Optional[str] = Field(None, description="真实姓名")
    role: int = Field(..., description="成员角色（0=只读, 1=可操作, 2=负责人）")
    role_name: str = Field(..., description="角色名称")
    status: int = Field(..., description="成员状态（0=禁用, 1=启用）")
    created_at: datetime = Field(..., description="加入时间")

    class Config:
        from_attributes = True


class ProjectMemberListResponse(BaseModel):
    """项目成员列表响应模型"""
    members: List[ProjectMemberResponse] = Field(..., description="成员列表")

    class Config:
        from_attributes = True


class ProjectDetailResponse(BaseModel):
    """项目详情响应模型"""
    id: int = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: str = Field(..., description="项目描述")
    owner_id: int = Field(..., description="项目负责人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    members: List[ProjectMemberResponse] = Field(..., description="项目成员列表")

    class Config:
        from_attributes = True


class ProjectModuleCreateRequest(BaseModel):
    """项目模块创建请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="模块名称")
    description: Optional[str] = Field(None, description="模块描述")

    class Config:
        from_attributes = True


class ProjectModuleUpdateRequest(BaseModel):
    """项目模块更新请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="模块名称")
    description: Optional[str] = Field(None, description="模块描述")

    class Config:
        from_attributes = True


class ProjectModuleResponse(BaseModel):
    """项目模块响应模型"""
    id: int = Field(..., description="模块ID")
    name: str = Field(..., description="模块名称")
    description: Optional[str] = Field(None, description="模块描述")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ProjectModuleListResponse(BaseModel):
    """项目模块列表响应模型"""
    datas: List[ProjectModuleResponse] = Field(..., description="模块列表")

    class Config:
        from_attributes = True


# ================== 仪表盘统计相关模型 ==================

class DashboardTrendPoint(BaseModel):
    """仪表盘趋势数据点"""
    date: str = Field(..., description="日期，格式 YYYY-MM-DD")
    runs: int = Field(..., description="执行次数")
    passed: int = Field(..., description="通过次数")
    failed: int = Field(..., description="失败次数")
    errors: int = Field(..., description="错误次数")
    skipped: int = Field(..., description="跳过次数")


class DashboardCaseTrendPoint(BaseModel):
    """最近7天用例执行趋势数据点（含通过率）"""
    date: str = Field(..., description="日期，格式 YYYY-MM-DD")
    executed: int = Field(..., description="当天执行用例数量")
    success: int = Field(..., description="当天通过用例数量")
    pass_rate: float = Field(..., description="当天通过率，0-100")


class DashboardActivityItem(BaseModel):
    """仪表盘最近活动项"""
    id: str = Field(..., description="活动ID")
    content: str = Field(..., description="活动描述")
    timestamp: str = Field(..., description="时间戳，格式 YYYY-MM-DD HH:mm")
    type: str = Field(..., description="类型（primary/success/warning/info等）")


class DashboardTaskRunItem(BaseModel):
    """最近任务执行记录项"""
    id: int = Field(..., description="任务运行ID")
    status: Optional[str] = Field(None, description="运行状态")
    total_suites: Optional[int] = Field(None, description="包含套件数")
    total_cases: Optional[int] = Field(None, description="包含用例数")
    passed_cases: Optional[int] = Field(None, description="通过用例数")
    failed_cases: Optional[int] = Field(None, description="失败用例数")
    skipped_cases: Optional[int] = Field(None, description="跳过用例数")
    duration: Optional[float] = Field(None, description="运行耗时(秒)")
    timestamp: str = Field(..., description="开始时间，格式 YYYY-MM-DD HH:mm")


class DashboardTaskSummary(BaseModel):
    """最近一次任务执行摘要"""
    id: int = Field(..., description="任务运行ID")
    status: Optional[str] = Field(None, description="运行状态")
    total_suites: Optional[int] = Field(None, description="包含套件数")
    total_cases: Optional[int] = Field(None, description="包含用例数")
    passed_cases: Optional[int] = Field(None, description="通过用例数")
    failed_cases: Optional[int] = Field(None, description="失败用例数")
    skipped_cases: Optional[int] = Field(None, description="跳过用例数")
    duration: Optional[float] = Field(None, description="运行耗时(秒)")
    timestamp: str = Field(..., description="开始时间，格式 YYYY-MM-DD HH:mm")


class DashboardStatsResponse(BaseModel):
    """仪表盘统计响应模型（按项目）"""
    project_id: int = Field(..., description="项目ID")
    projects: int = Field(1, description="项目总数（当前视图为单项目时为1）")
    api_interfaces: int = Field(..., description="接口数量")
    api_cases: int = Field(..., description="API可执行用例数量")
    functional_cases: int = Field(..., description="功能用例数量")
    requirements: int = Field(..., description="项目需求数量")
    suites: int = Field(..., description="测试套件数量")
    tasks: int = Field(..., description="测试任务数量")
    executions: int = Field(..., description="近30天执行总次数")
    success_rate: float = Field(..., description="近30天执行通过率，0-100")
    trend: List[DashboardTrendPoint] = Field(default_factory=list, description="近14天执行趋势")
    activities: List[DashboardActivityItem] = Field(default_factory=list, description="最近活动")
    api_run_counts_by_status: Dict[str, int] = Field(default_factory=dict, description="接口用例运行次数（按状态分类）")
    api_run_counts_by_type: Dict[str, int] = Field(default_factory=dict, description="接口用例运行次数（按类型分类）")
    case_trend_7d: List[DashboardCaseTrendPoint] = Field(default_factory=list, description="最近7天用例执行趋势（含通过率）")
    recent_task_runs: List[DashboardTaskRunItem] = Field(default_factory=list, description="最近30次测试任务执行记录")
    last_task_summary: Optional[DashboardTaskSummary] = Field(None, description="最近一次任务执行统计数据")

    class Config:
        from_attributes = True
