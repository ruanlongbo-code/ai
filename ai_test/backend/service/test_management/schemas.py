"""
测试管理模块Pydantic模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TestSuiteCreateRequest(BaseModel):
    """创建测试套件请求模型"""
    suite_name: str = Field(..., min_length=1, max_length=100, description="套件名称")
    description: Optional[str] = Field(None, max_length=500, description="套件描述")
    type: str = Field(..., description="套件类型：api/ui")

    class Config:
        from_attributes = True


class TestSuiteDeleteResponse(BaseModel):
    """删除测试套件响应模型"""
    message: str = Field(..., description="删除结果消息")

    class Config:
        from_attributes = True


class TestSuiteResponse(BaseModel):
    """测试套件响应模型"""
    id: int = Field(..., description="套件ID")
    suite_name: str = Field(..., description="套件名称")
    description: Optional[str] = Field(None, description="套件描述")
    type: str = Field(..., description="套件类型")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class TestSuiteListResponse(BaseModel):
    """测试套件列表响应模型"""
    suites: List[TestSuiteResponse] = Field(..., description="测试套件列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class SuiteCaseItem(BaseModel):
    """套件用例项模型"""
    relation_id: int = Field(..., description="关联关系ID")
    case_order: int = Field(..., description="用例执行顺序")
    case_id: int = Field(..., description="用例ID")
    case_name: str = Field(..., description="用例名称")

    class Config:
        from_attributes = True


class TestSuiteDetailResponse(BaseModel):
    """测试套件详情响应模型"""
    id: int = Field(..., description="套件ID")
    suite_name: str = Field(..., description="套件名称")
    description: Optional[str] = Field(None, description="套件描述")
    type: str = Field(..., description="套件类型")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    cases: List[SuiteCaseItem] = Field(..., description="套件中的用例列表")

    class Config:
        from_attributes = True


class AddCaseToSuiteRequest(BaseModel):
    """往测试套件中添加用例请求模型"""
    case_id: int = Field(..., description="用例ID")

    class Config:
        from_attributes = True


class AddCaseToSuiteResponse(BaseModel):
    """添加用例到套件的响应"""
    message: str = Field(..., description="添加结果消息")
    relation_id: int = Field(..., description="关联关系ID")
    case_order: int = Field(..., description="用例执行顺序")

    class Config:
        from_attributes = True


class DeleteCaseFromSuiteResponse(BaseModel):
    """从套件中删除用例的响应"""
    message: str = Field(..., description="删除结果消息")
    deleted_relation_id: int = Field(..., description="已删除的关联关系ID")
    reordered_count: int = Field(..., description="重新排序的用例数量")

    class Config:
        from_attributes = True


class ReorderSuiteCasesRequest(BaseModel):
    """测试套件用例排序请求"""
    case_ids: List[int] = Field(..., min_items=1, description="用例ID列表，按新的执行顺序排列")

    class Config:
        from_attributes = True


class ReorderSuiteCasesResponse(BaseModel):
    """测试套件用例排序响应"""
    message: str = Field(..., description="排序结果消息")
    reordered_count: int = Field(..., description="重新排序的用例数量")
    updated_cases: List[SuiteCaseItem] = Field(..., description="更新后的用例列表")

    class Config:
        from_attributes = True


class TestTaskCreateRequest(BaseModel):
    """测试任务创建请求"""
    task_name: str = Field(..., min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    type: str = Field(..., description="任务类型：api/ui/functional")

    class Config:
        from_attributes = True


class TestTaskResponse(BaseModel):
    """测试任务响应"""
    id: int = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    type: str = Field(..., description="任务类型")
    status: str = Field(..., description="任务状态")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class TestTaskDeleteResponse(BaseModel):
    """测试任务删除响应"""
    message: str = Field(..., description="删除结果消息")

    class Config:
        from_attributes = True


class TestTaskListResponse(BaseModel):
    """测试任务列表响应模型"""
    tasks: List[TestTaskResponse] = Field(..., description="测试任务列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class AddSuiteToTaskRequest(BaseModel):
    """往测试任务中添加套件请求模型"""
    suite_id: int = Field(..., description="套件ID")

    class Config:
        from_attributes = True


class AddSuiteToTaskResponse(BaseModel):
    """添加套件到任务的响应"""
    message: str = Field(..., description="添加结果消息")
    relation_id: int = Field(..., description="关联关系ID")
    suite_order: int = Field(..., description="套件执行顺序")

    class Config:
        from_attributes = True


class DeleteSuiteFromTaskResponse(BaseModel):
    """删除测试任务中测试套件响应"""
    message: str = Field(..., description="删除结果消息")
    deleted_relation_id: int = Field(..., description="已删除的关联关系ID")
    reordered_count: int = Field(..., description="重新排序的套件数量")

    class Config:
        from_attributes = True


class TaskSuiteItem(BaseModel):
    """测试任务中的套件项"""
    relation_id: int = Field(..., description="关联关系ID")
    suite_order: int = Field(..., description="套件执行顺序")
    suite_id: int = Field(..., description="套件ID")
    suite_name: str = Field(..., description="套件名称")

    class Config:
        from_attributes = True


class ReorderTaskSuitesRequest(BaseModel):
    """测试任务套件排序请求"""
    suite_ids: List[int] = Field(..., min_items=1, description="套件ID列表，按新的执行顺序排列")

    class Config:
        from_attributes = True


class ReorderTaskSuitesResponse(BaseModel):
    """测试任务套件排序响应"""
    message: str = Field(..., description="排序结果消息")
    reordered_count: int = Field(..., description="重新排序的套件数量")
    updated_suites: List[TaskSuiteItem] = Field(..., description="更新后的套件列表")

    class Config:
        from_attributes = True


class TestTaskDetailResponse(BaseModel):
    """测试任务详情响应模型"""
    id: int = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    type: str = Field(..., description="任务类型")
    status: str = Field(..., description="任务状态")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    suites: List[TaskSuiteItem] = Field(..., description="任务中的套件列表")

    class Config:
        from_attributes = True
