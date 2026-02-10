"""
测试执行模块Pydantic模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class RunSingleTestCaseRequest(BaseModel):
    """运行单条测试用例请求模型"""
    case_id: int = Field(..., description="测试用例ID")
    environment_id: int = Field(..., description="测试环境ID")

    class Config:
        from_attributes = True


class RunSingleTestCaseResponse(BaseModel):
    """运行单条测试用例响应模型"""
    case_run_id: int = Field(..., description="用例执行记录ID")
    case_id: int = Field(..., description="测试用例ID")
    case_name: str = Field(..., description="测试用例名称")
    status: str = Field(..., description="执行状态")
    duration: Optional[Decimal] = Field(None, description="执行时长（秒）")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    logs: Any = Field(..., description="日志数据")
    request_info: Any = Field(..., description="请求详情")


    class Config:
        from_attributes = True


class RunTestSuiteRequest(BaseModel):
    """运行测试套件请求模型"""
    suite_id: int
    environment_id: int


class TestSuiteSummary(BaseModel):
    """测试套件执行统计信息"""
    total: int
    success: int
    failed: int
    error: int
    skip: int
    duration: float


class RunTestSuiteResponse(BaseModel):
    """运行测试套件响应模型"""
    run_id: int
    suite_id: int
    environment_id: int
    status: str
    duration: float
    error_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    summary: Optional[TestSuiteSummary] = None


class RunTestTaskRequest(BaseModel):
    """运行测试任务请求模型"""
    task_id: int = Field(..., description="测试任务ID")
    environment_id: int = Field(..., description="测试环境ID")

    class Config:
        from_attributes = True


class TestTaskSummary(BaseModel):
    """测试任务执行统计信息"""
    total_suites: int = Field(..., description="总套件数")
    total_cases: int = Field(..., description="总用例数")
    success_cases: int = Field(..., description="成功用例数")
    failed_cases: int = Field(..., description="失败用例数")
    error_cases: int = Field(..., description="错误用例数")
    skip_cases: int = Field(..., description="跳过用例数")
    duration: float = Field(..., description="执行时长（秒）")

    class Config:
        from_attributes = True


class RunTestTaskResponse(BaseModel):
    """运行测试任务响应模型"""
    task_run_id: int = Field(..., description="任务执行记录ID")
    task_id: int = Field(..., description="测试任务ID")
    task_name: str = Field(..., description="测试任务名称")
    status: str = Field(..., description="执行状态")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    summary: Optional[TestTaskSummary] = Field(None, description="执行统计信息")

    class Config:
        from_attributes = True


class RunTestTaskBackgroundRequest(BaseModel):
    """后台运行测试任务请求模型"""
    task_id: int = Field(..., description="测试任务ID")
    environment_id: int = Field(..., description="测试环境ID")

    class Config:
        from_attributes = True


class RunTestTaskBackgroundResponse(BaseModel):
    """后台运行测试任务响应模型"""
    task_run_id: int = Field(..., description="任务执行记录ID")
    task_id: int = Field(..., description="测试任务ID")
    task_name: str = Field(..., description="测试任务名称")
    status: str = Field(..., description="执行状态")
    message: str = Field(..., description="响应消息")

    class Config:
        from_attributes = True


class TaskStatusQueryResponse(BaseModel):
    """任务状态查询响应模型"""
    task_run_id: int = Field(..., description="任务执行记录ID")
    task_id: int = Field(..., description="测试任务ID")
    task_name: str = Field(..., description="测试任务名称")
    status: str = Field(..., description="执行状态")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    summary: Optional[TestTaskSummary] = Field(None, description="执行统计信息")

    class Config:
        from_attributes = True


# ==================== 新增接口响应模型 ====================

class ApiCaseRunDetailResponse(BaseModel):
    """单条测试用例运行详情响应模型"""
    id: int = Field(..., description="用例运行记录ID")
    suite_run_id: Optional[int] = Field(None, description="所属套件运行记录ID")
    api_case_id: int = Field(..., description="API用例ID")
    case_name: str = Field(..., description="用例名称")
    error_message: Optional[str] = Field(None, description="错误信息")
    traceback: Optional[str] = Field(None, description="异常堆栈")
    start_time: Optional[datetime] = Field(None, description="执行开始时间")
    end_time: Optional[datetime] = Field(None, description="执行结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    logs: Optional[List[Dict[str, Any]]] = Field(None, description="执行日志列表")
    request_info: Optional[List[Dict[str, Any]]] = Field(None, description="接口请求信息列表")
    created_at: datetime = Field(..., description="创建时间")
    status: str = Field(..., description="执行状态")
    class Config:
        from_attributes = True


class ApiCaseRunListItem(BaseModel):
    """用例运行记录列表项"""
    id: int = Field(..., description="用例运行记录ID")
    suite_run_id: Optional[int] = Field(None, description="所属套件运行记录ID")
    api_case_id: int = Field(..., description="API用例ID")
    case_name: str = Field(..., description="用例名称")
    status: str = Field(..., description="执行状态")
    start_time: Optional[datetime] = Field(None, description="执行开始时间")
    end_time: Optional[datetime] = Field(None, description="执行结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ApiCaseRunListResponse(BaseModel):
    """用例运行记录列表响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: List[ApiCaseRunListItem] = Field(..., description="记录列表")

    class Config:
        from_attributes = True


class TestSuiteRunListItem(BaseModel):
    """测试套件运行记录列表项"""
    id: int = Field(..., description="套件运行记录ID")
    suite_id: int = Field(..., description="套件ID")
    suite_name: str = Field(..., description="套件名称")
    run_task_id: Optional[int] = Field(None, description="所属任务运行记录ID")
    status: str = Field(..., description="套件执行状态")
    total_cases: int = Field(..., description="套件包含的总用例数")
    passed_cases: int = Field(..., description="执行通过的用例数")
    failed_cases: int = Field(..., description="执行失败的用例数")
    skipped_cases: int = Field(..., description="被跳过的用例数")
    error_cases: int = Field(0, description="执行错误的用例数")
    start_time: Optional[datetime] = Field(None, description="套件执行开始时间")
    end_time: Optional[datetime] = Field(None, description="套件执行结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class TestSuiteRunListResponse(BaseModel):
    """测试套件运行记录列表响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: List[TestSuiteRunListItem] = Field(..., description="记录列表")

    class Config:
        from_attributes = True


class TestSuiteRunDetailResponse(BaseModel):
    """测试套件运行详情响应模型"""
    id: int = Field(..., description="套件运行记录ID")
    suite_id: int = Field(..., description="套件ID")
    suite_name: str = Field(..., description="套件名称")
    run_task_id: Optional[int] = Field(None, description="所属任务运行记录ID")
    status: str = Field(..., description="套件执行状态")
    total_cases: int = Field(..., description="套件包含的总用例数")
    passed_cases: int = Field(..., description="执行通过的用例数")
    failed_cases: int = Field(..., description="执行失败的用例数")
    skipped_cases: int = Field(..., description="被跳过的用例数")
    error_cases: int = Field(..., description="执行错误的用例数")
    start_time: Optional[datetime] = Field(None, description="套件执行开始时间")
    end_time: Optional[datetime] = Field(None, description="套件执行结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    case_runs: List[ApiCaseRunListItem] = Field(..., description="用例运行记录列表")

    class Config:
        from_attributes = True


class TestTaskRunListItem(BaseModel):
    """测试任务运行记录列表项"""
    id: int = Field(..., description="任务运行记录ID")
    task_id: int = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务执行状态")
    total_suites: int = Field(..., description="任务包含的总套件数")
    total_cases: int = Field(..., description="任务包含的总用例数")
    passed_cases: int = Field(..., description="执行通过的用例数")
    failed_cases: int = Field(..., description="执行失败的用例数")
    skipped_cases: int = Field(..., description="被跳过的用例数")
    start_time: Optional[datetime] = Field(None, description="任务执行开始时间")
    end_time: Optional[datetime] = Field(None, description="任务执行结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class TestTaskRunListResponse(BaseModel):
    """测试任务运行记录列表响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: List[TestTaskRunListItem] = Field(..., description="记录列表")

    class Config:
        from_attributes = True


class TestTaskRunDetailResponse(BaseModel):
    """测试任务运行详情响应模型"""
    id: int = Field(..., description="任务运行记录ID")
    task_id: int = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务执行状态")
    total_suites: int = Field(..., description="任务包含的总套件数")
    total_cases: int = Field(..., description="任务包含的总用例数")
    passed_cases: int = Field(..., description="执行通过的用例数")
    failed_cases: int = Field(..., description="执行失败的用例数")
    skipped_cases: int = Field(..., description="被跳过的用例数")
    error_cases: int = Field(0, description="执行错误的用例数")
    start_time: Optional[datetime] = Field(None, description="任务执行开始时间")
    end_time: Optional[datetime] = Field(None, description="任务执行结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    suite_runs: List[TestSuiteRunListItem] = Field(..., description="套件运行记录列表")

    class Config:
        from_attributes = True
