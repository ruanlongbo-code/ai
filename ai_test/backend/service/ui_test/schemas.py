from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ======================== 页面管理 ========================

class UiPageCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="页面名称")
    url: str = Field(..., min_length=1, max_length=1000, description="页面URL")
    description: Optional[str] = Field(None, description="页面描述")


class UiPageUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1, max_length=1000)
    description: Optional[str] = None


class UiPageResponse(BaseModel):
    id: int
    project_id: int
    name: str
    url: str
    description: Optional[str] = None
    creator_id: int
    created_at: datetime
    updated_at: datetime


# ======================== 用例管理 ========================

class UiStepRequest(BaseModel):
    sort_order: int = Field(0, description="步骤顺序")
    action: str = Field(..., min_length=1, description="操作描述")
    input_data: Optional[str] = Field(None, description="输入数据")
    expected_result: str = Field(..., min_length=1, description="预期结果（AI验证用）")
    # 结构化断言
    assertion_type: str = Field(..., min_length=1, description="断言类型")
    assertion_target: Optional[str] = Field(None, description="断言目标（CSS选择器）")
    assertion_value: Optional[str] = Field(None, description="断言期望值")


class UiCaseCreateRequest(BaseModel):
    page_id: Optional[int] = Field(None, description="关联页面ID")
    name: str = Field(..., min_length=1, max_length=255, description="用例名称")
    priority: str = Field("P1", description="优先级")
    preconditions: Optional[str] = Field(None, description="前置条件")
    steps: List[UiStepRequest] = Field(default_factory=list, description="测试步骤列表")


class UiCaseUpdateRequest(BaseModel):
    page_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    priority: Optional[str] = None
    preconditions: Optional[str] = None
    steps: Optional[List[UiStepRequest]] = None


class UiStepResponse(BaseModel):
    id: int
    case_id: int
    sort_order: int
    action: str
    input_data: Optional[str] = None
    expected_result: Optional[str] = None
    assertion_type: Optional[str] = None
    assertion_target: Optional[str] = None
    assertion_value: Optional[str] = None


class UiCaseResponse(BaseModel):
    id: int
    project_id: int
    page_id: Optional[int] = None
    page_name: Optional[str] = None
    page_url: Optional[str] = None
    name: str
    priority: str
    preconditions: Optional[str] = None
    status: str
    last_run_at: Optional[datetime] = None
    creator_id: int
    created_at: datetime
    updated_at: datetime
    steps: List[UiStepResponse] = []


# ======================== 执行记录 ========================

class UiStepResultResponse(BaseModel):
    id: int
    execution_id: int
    step_id: int
    sort_order: int
    status: str
    screenshot_url: Optional[str] = None
    ai_action: Optional[str] = None
    actual_result: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    assertion_type: Optional[str] = None
    assertion_passed: Optional[bool] = None
    assertion_detail: Optional[str] = None


class UiExecutionResponse(BaseModel):
    id: int
    case_id: int
    project_id: int
    case_name: Optional[str] = None
    status: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    executor_id: int
    created_at: datetime
    step_results: List[UiStepResultResponse] = []


class UiExecutionListResponse(BaseModel):
    executions: List[UiExecutionResponse]
    total: int


# ======================== 测试报告 ========================

class UiReportListItem(BaseModel):
    """报告列表项"""
    execution_id: int
    case_id: int
    case_name: Optional[str] = None
    page_name: Optional[str] = None
    status: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    pass_rate: float
    duration_ms: Optional[int] = None
    executor_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime
    # 断言统计
    total_assertions: int = 0
    passed_assertions: int = 0
    failed_assertions: int = 0


class UiReportListResponse(BaseModel):
    """报告列表响应"""
    reports: List[UiReportListItem]
    total: int


class UiReportStepDetail(BaseModel):
    """报告中的步骤详情"""
    sort_order: int
    action: str
    input_data: Optional[str] = None
    expected_result: Optional[str] = None
    status: str
    actual_result: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_url: Optional[str] = None
    ai_action: Optional[str] = None
    duration_ms: Optional[int] = None
    assertion_type: Optional[str] = None
    assertion_passed: Optional[bool] = None
    assertion_detail: Optional[str] = None


class UiTestReportResponse(BaseModel):
    """UI测试报告响应"""
    execution_id: int
    case_id: int
    case_name: str
    page_name: Optional[str] = None
    page_url: Optional[str] = None
    priority: str
    preconditions: Optional[str] = None
    status: str
    # 统计
    total_steps: int
    passed_steps: int
    failed_steps: int
    pass_rate: float
    total_duration_ms: int
    avg_step_duration_ms: int
    # 断言统计
    total_assertions: int = 0
    passed_assertions: int = 0
    failed_assertions: int = 0
    # 时间
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    executor_name: Optional[str] = None
    # 步骤详情
    steps: List[UiReportStepDetail] = []
