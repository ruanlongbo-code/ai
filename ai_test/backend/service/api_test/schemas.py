"""
接口测试模块Pydantic模型
定义接口请求和响应的数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime


class ApiImportRequest(BaseModel):
    """接口导入请求模型"""
    project_id: int = Field(..., description="项目ID")

    class Config:
        from_attributes = True


class ApiImportResponse(BaseModel):
    """接口导入响应模型"""
    success: bool = Field(..., description="导入是否成功")
    message: str = Field(..., description="导入结果消息")
    imported_count: int = Field(..., description="成功导入的接口数量")
    failed_count: int = Field(default=0, description="导入失败的接口数量")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")

    class Config:
        from_attributes = True


class OpenApiImportRequest(BaseModel):
    """OpenAPI接口导入请求模型"""
    project_id: int = Field(..., description="项目ID")

    class Config:
        from_attributes = True


class ApiCompleteTestCaseGenerateRequest(BaseModel):
    """基于接口生成完整测试用例请求模型"""
    test_id: int = Field(..., description="测试环境ID")
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外的配置信息")

    class Config:
        from_attributes = True


class ApiCompleteTestCaseGenerateResponse(BaseModel):
    """基于接口生成完整测试用例响应模型"""
    success: bool = Field(..., description="生成是否成功")
    message: str = Field(..., description="生成结果消息")
    generated_cases: List[Dict[str, Any]] = Field(..., description="生成的完整测试用例列表")
    interface_info: Optional[Dict[str, Any]] = Field(None, description="接口信息")
    test_environment_info: Optional[Dict[str, Any]] = Field(None, description="测试环境信息")
    test_variables: Optional[List[Dict[str, Any]]] = Field(None, description="测试环境变量")
    database_config: Optional[Dict[str, Any]] = Field(None, description="数据库配置信息")
    dependencies: Optional[List[Dict[str, Any]]] = Field(None, description="前置依赖接口信息")

    class Config:
        from_attributes = True


class OpenApiImportResponse(BaseModel):
    """OpenAPI接口导入响应模型"""
    success: bool = Field(..., description="导入是否成功")
    message: str = Field(..., description="导入结果消息")
    imported_count: int = Field(..., description="成功导入的接口数量")
    failed_count: int = Field(default=0, description="导入失败的接口数量")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")

    class Config:
        from_attributes = True


class AiParseRequest(BaseModel):
    """AI解析接口文档请求模型"""
    project_id: int = Field(..., description="项目ID")
    api_document: str = Field(..., description="接口文档的文字描述内容")

    class Config:
        from_attributes = True


class AiParseResponse(BaseModel):
    """AI解析接口文档响应模型"""
    success: bool = Field(..., description="解析是否成功")
    message: str = Field(..., description="解析结果消息")
    parsed_data: Optional[Dict[str, Any]] = Field(None, description="解析出的结构化接口数据")
    error_details: Optional[str] = Field(None, description="错误详情")

    class Config:
        from_attributes = True


class ApiInterfaceItem(BaseModel):
    """接口列表项模型"""
    id: int = Field(..., description="接口ID")
    method: str = Field(..., description="HTTP请求方法")
    path: str = Field(..., description="接口路径")
    summary: Optional[str] = Field(None, description="接口简要说明")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiInterfaceListResponse(BaseModel):
    """接口列表响应模型"""
    interfaces: List[ApiInterfaceItem] = Field(..., description="接口列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class ApiInterfaceCreateRequest(BaseModel):
    """新增接口请求模型"""
    method: str = Field(..., description="HTTP请求方法", max_length=10)
    path: str = Field(..., description="接口路径", max_length=255)
    summary: Optional[str] = Field(None, description="接口简要说明")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="查询参数说明")
    request_body: Optional[Dict[str, Any]] = Field(default_factory=dict, description="请求体结构")
    responses: List = Field(default_factory=list, description="响应体结构")

    class Config:
        from_attributes = True


class ApiInterfaceCreateResponse(BaseModel):
    """新增接口响应模型"""
    id: int = Field(..., description="接口ID")
    method: str = Field(..., description="HTTP请求方法")
    path: str = Field(..., description="接口路径")
    summary: Optional[str] = Field(None, description="接口简要说明")
    parameters: Dict[str, Any] = Field(..., description="查询参数说明")
    request_body: Dict[str, Any] = Field(..., description="请求体结构")
    responses: List = Field(..., description="响应体结构")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiInterfaceDeleteResponse(BaseModel):
    """删除接口响应模型"""
    message: str = Field(..., description="删除结果消息")

    class Config:
        from_attributes = True


class ApiInterfaceUpdateRequest(BaseModel):
    """编辑接口请求模型"""
    method: Optional[str] = Field(None, description="HTTP请求方法", max_length=10)
    path: Optional[str] = Field(None, description="接口路径", max_length=255)
    summary: Optional[str] = Field(None, description="接口简要说明")
    parameters: Optional[Dict[str, Any]] = Field(None, description="查询参数说明")
    request_body: Optional[Dict[str, Any]] = Field(None, description="请求体结构")
    responses: List | None = Field(None, description="响应体结构")

    class Config:
        from_attributes = True


class ApiInterfaceUpdateResponse(BaseModel):
    """编辑接口响应模型"""
    id: int = Field(..., description="接口ID")
    method: str = Field(..., description="HTTP请求方法")
    path: str = Field(..., description="接口路径")
    summary: Optional[str] = Field(None, description="接口简要说明")
    parameters: Dict[str, Any] = Field(..., description="查询参数说明")
    request_body: Dict[str, Any] = Field(..., description="请求体结构")
    responses: List = Field(..., description="响应体结构")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# 接口依赖分组相关模型
class ApiDependencyGroupCreateRequest(BaseModel):
    """创建接口依赖分组请求模型"""
    name: str = Field(..., description="分组名称", max_length=100)
    description: Optional[str] = Field(None, description="分组描述")
    target_interface_id: int = Field(..., description="目标接口ID")

    class Config:
        from_attributes = True


class ApiDependencyGroupCreateResponse(BaseModel):
    """创建接口依赖分组响应模型"""
    id: int = Field(..., description="分组ID")
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    target_interface_id: int = Field(..., description="目标接口ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiDependencyGroupUpdateRequest(BaseModel):
    """更新接口依赖分组请求模型"""
    name: Optional[str] = Field(None, max_length=100, description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")

    class Config:
        from_attributes = True


class ApiDependencyGroupUpdateResponse(BaseModel):
    """更新接口依赖分组响应模型"""
    id: int = Field(..., description="分组ID")
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    target_interface_id: int = Field(..., description="目标接口ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiDependencyGroupItem(BaseModel):
    """依赖分组列表项模型"""
    id: int = Field(..., description="分组ID")
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    target_interface_id: int = Field(..., description="目标接口ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiDependencyGroupListResponse(BaseModel):
    """依赖分组列表响应模型"""
    dependency_groups: List[ApiDependencyGroupItem] = Field(..., description="依赖分组列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class ApiDependencyCreateRequest(BaseModel):
    """接口依赖创建请求模型"""
    name: str = Field(..., max_length=100, description="依赖名称")
    description: Optional[str] = Field(None, description="依赖描述")
    dependency_type: str = Field(..., max_length=20, description="依赖类型（header=请求头, param=参数, body=请求体, response=响应）")
    source_interface_id: Optional[int] = Field(None, description="源接口ID")
    source_field_path: Optional[str] = Field(None, max_length=255, description="源字段路径")
    target_field_name: str = Field(..., max_length=100, description="目标字段名称")
    transform_rule: Optional[dict] = Field(None, description="转换规则")
    is_active: bool = Field(True, description="是否启用")

    class Config:
        from_attributes = True


class ApiDependencyCreateResponse(BaseModel):
    """接口依赖创建响应模型"""
    id: int = Field(..., description="依赖ID")
    name: str = Field(..., description="依赖名称")
    description: Optional[str] = Field(None, description="依赖描述")
    dependency_type: str = Field(..., description="依赖类型")
    source_interface_id: Optional[int] = Field(None, description="源接口ID")
    source_interface_name: Optional[str] = Field(None, description="源接口名称")
    source_interface_method: Optional[str] = Field(None, description="源接口请求方法")
    source_interface_path: Optional[str] = Field(None, description="源接口路径")
    source_field_path: Optional[str] = Field(None, description="源字段路径")
    target_field_name: str = Field(..., description="目标字段名称")
    transform_rule: Optional[dict] = Field(None, description="转换规则")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiDependencyUpdateRequest(BaseModel):
    """接口依赖编辑请求模型"""
    name: Optional[str] = Field(None, max_length=100, description="依赖名称")
    description: Optional[str] = Field(None, description="依赖描述")
    dependency_type: Optional[str] = Field(None, description="依赖类型（header=请求头, param=参数, body=请求体, response=响应）")
    source_interface_id: Optional[int] = Field(None, description="源接口ID")
    source_field_path: Optional[str] = Field(None, max_length=255, description="源字段路径")
    target_field_name: Optional[str] = Field(None, max_length=100, description="目标字段名称")
    transform_rule: Optional[dict] = Field(None, description="转换规则")
    is_active: Optional[bool] = Field(None, description="是否启用")

    class Config:
        from_attributes = True


class ApiDependencyUpdateResponse(BaseModel):
    """接口依赖编辑响应模型"""
    id: int = Field(..., description="依赖ID")
    name: str = Field(..., description="依赖名称")
    description: Optional[str] = Field(None, description="依赖描述")
    dependency_type: str = Field(..., description="依赖类型")
    source_interface_id: Optional[int] = Field(None, description="源接口ID")
    source_interface_name: Optional[str] = Field(None, description="源接口名称")
    source_interface_method: Optional[str] = Field(None, description="源接口请求方法")
    source_interface_path: Optional[str] = Field(None, description="源接口路径")
    source_field_path: Optional[str] = Field(None, description="源字段路径")
    target_field_name: str = Field(..., description="目标字段名称")
    transform_rule: Optional[dict] = Field(None, description="转换规则")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiDependencyDeleteResponse(BaseModel):
    """删除接口依赖响应模型"""
    message: str = Field(..., description="删除结果消息")

    class Config:
        from_attributes = True


class ApiDependencyGroupDeleteResponse(BaseModel):
    """删除接口依赖分组响应模型"""
    message: str = Field(..., description="删除结果消息")

    class Config:
        from_attributes = True


class ApiDependencyItem(BaseModel):
    """接口依赖项模型"""
    id: int = Field(..., description="依赖ID")
    name: str = Field(..., description="依赖名称")
    description: Optional[str] = Field(None, description="依赖描述")
    dependency_type: str = Field(..., description="依赖类型")
    source_interface_id: Optional[int] = Field(None, description="源接口ID")
    source_interface_name: Optional[str] = Field(None, description="源接口名称")
    source_interface_method: Optional[str] = Field(None, description="源接口请求方法")
    source_interface_path: Optional[str] = Field(None, description="源接口路径")
    source_field_path: Optional[str] = Field(None, description="源字段路径")
    target_field_name: str = Field(..., description="目标字段名称")
    transform_rule: Optional[dict] = Field(None, description="转换规则")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiDependencyGroupDetail(BaseModel):
    """接口依赖分组详情模型"""
    id: int = Field(..., description="分组ID")
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    dependencies: List[ApiDependencyItem] = Field(..., description="依赖列表")

    class Config:
        from_attributes = True


class ApiInterfaceDetailResponse(BaseModel):
    """接口详情响应模型"""
    id: int = Field(..., description="接口ID")
    method: str = Field(..., description="HTTP请求方法")
    path: str = Field(..., description="接口路径")
    summary: Optional[str] = Field(None, description="接口简要说明")
    parameters: Dict[str, Any] = Field(..., description="查询参数说明")
    request_body: Dict[str, Any] = Field(..., description="请求体结构")
    responses: List = Field(..., description="响应体结构")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    dependency_groups: List[ApiDependencyGroupDetail] = Field(..., description="关联的依赖分组列表")

    class Config:
        from_attributes = True


class ApiBaseCaseItem(BaseModel):
    """基础用例项模型"""
    id: int = Field(..., description="用例ID")
    interface_id: str = Field(..., description="关联接口ID")
    interface_name: Optional[str] = Field(None, description="接口名称")
    name: str = Field(..., description="测试用例名称")
    steps: List[Dict[str, Any]] = Field(..., description="测试步骤列表")
    expected: List[Dict[str, Any]] = Field(..., description="预期结果列表")
    status: str = Field(..., description="用例状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiBaseCaseListResponse(BaseModel):
    """基础用例列表响应模型"""
    base_cases: List[ApiBaseCaseItem] = Field(..., description="基础用例列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class ApiTestCaseItem(BaseModel):
    """接口测试用例项模型"""
    id: int = Field(..., description="用例ID")
    base_case_id: int = Field(..., description="关联的基础用例ID")
    name: str = Field(..., description="用例名称")
    description: Optional[str] = Field(None, description="用例描述")
    interface_name: Optional[str] = Field(None, description="接口名称")
    type: str = Field(..., description="用例类型")
    preconditions: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = Field(None, description="前置步骤列表")
    request: Optional[Dict[str, Any]] = Field(None, description="主请求信息")
    assertions: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = Field(None, description="断言信息")
    status: str = Field(..., description="用例状态")
    generation_count: int = Field(..., description="用例生成次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiTestCaseListResponse(BaseModel):
    """接口测试用例列表响应模型"""
    test_cases: List[ApiTestCaseItem] = Field(..., description="测试用例列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class ApiTestCaseBatchEditRequest(BaseModel):
    """接口测试用例批量编辑请求模型"""
    test_case_ids: List[int] = Field(..., description="要编辑的测试用例ID列表")
    name: Optional[str] = Field(None, max_length=255, description="用例名称")
    description: Optional[str] = Field(None, description="用例描述")
    interface_name: Optional[str] = Field(None, max_length=255, description="接口名称")
    type: Optional[str] = Field(None, max_length=20, description="用例类型（api=接口用例，business=业务流用例）")
    preconditions: Optional[list] = Field(None, description="前置步骤列表")
    request: Optional[dict] = Field(None, description="主请求信息")
    assertions: Optional[dict] = Field(None, description="断言信息")
    status: Optional[str] = Field(None, max_length=20, description="用例状态（pending=待审核，ready=可执行，disabled=不可执行）")

    class Config:
        from_attributes = True


class ApiTestCaseBatchEditResponse(BaseModel):
    """接口测试用例批量编辑响应模型"""
    success_count: int = Field(..., description="成功编辑的用例数量")
    failed_count: int = Field(..., description="编辑失败的用例数量")
    success_ids: List[int] = Field(..., description="成功编辑的用例ID列表")
    failed_items: List[dict] = Field(..., description="编辑失败的用例信息")
    updated_cases: List[ApiTestCaseItem] = Field(..., description="更新后的测试用例列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

    class Config:
        from_attributes = True


class ApiTestCaseUpdateRequest(BaseModel):
    """接口测试用例编辑请求模型"""
    name: Optional[str] = Field(None, max_length=255, description="用例名称")
    description: Optional[str] = Field(None, description="用例描述")
    interface_name: Optional[str] = Field(None, max_length=255, description="接口名称")
    type: Optional[str] = Field(None, max_length=20, description="用例类型（api=接口用例，business=业务流用例）")
    preconditions: Optional[list] = Field(None, description="前置步骤列表")
    request: Optional[dict] = Field(None, description="主请求信息")
    assertions: Optional[dict] = Field(None, description="断言信息")
    status: Optional[str] = Field(None, max_length=20, description="用例状态（pending=待审核，ready=可执行，disabled=不可执行）")

    class Config:
        from_attributes = True


class ApiTestCaseUpdateResponse(BaseModel):
    """接口测试用例编辑响应模型"""
    id: int = Field(..., description="用例ID")
    base_case_id: int = Field(..., description="关联的基础用例ID")
    name: str = Field(..., description="用例名称")
    description: Optional[str] = Field(None, description="用例描述")
    interface_name: Optional[str] = Field(None, description="接口名称")
    type: str = Field(..., description="用例类型")
    preconditions: Optional[list] = Field(None, description="前置步骤列表")
    request: Optional[dict] = Field(None, description="主请求信息")
    assertions: Optional[dict] = Field(None, description="断言信息")
    status: str = Field(..., description="用例状态")
    generation_count: int = Field(..., description="用例生成次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ApiBaseCaseUpdateRequest(BaseModel):
    """基础用例更新请求模型"""
    name: Optional[str] = Field(None, description="测试用例名称")
    steps: Optional[List[Dict[str, Any]]] = Field(None, description="测试步骤列表")
    expected: Optional[List[Dict[str, Any]]] = Field(None, description="预期结果列表")
    status: Optional[str] = Field(None, description="用例状态")

    class Config:
        from_attributes = True


class ApiBaseCaseUpdateResponse(BaseModel):
    """基础用例更新响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果消息")
    data: Optional[ApiBaseCaseItem] = Field(None, description="更新后的基础用例信息")

    class Config:
        from_attributes = True


class ApiBaseCaseDeleteResponse(BaseModel):
    """基础用例删除响应模型"""
    message: str = Field(..., description="删除结果消息")

    class Config:
        from_attributes = True


class ApiBaseCaseCreateRequest(BaseModel):
    """基础用例创建请求模型"""
    name: str = Field(..., description="测试用例名称")
    steps: List[Dict[str, Any]] = Field(..., description="测试步骤列表")
    expected: List[Dict[str, Any]] = Field(..., description="预期结果列表")
    status: Optional[str] = Field('draft', description="用例状态")

    class Config:
        from_attributes = True


class ApiBaseCaseCreateResponse(BaseModel):
    """基础用例创建响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果消息")
    data: ApiBaseCaseItem = Field(..., description="创建后的基础用例信息")

    class Config:
        from_attributes = True


class ApiBaseCaseGenerateRequest(BaseModel):
    """生成基础用例请求模型"""
    interface_id: int = Field(..., description="接口ID")

    class Config:
        from_attributes = True


class ApiBaseCaseGenerateResponse(BaseModel):
    """生成基础用例响应模型"""
    success: bool = Field(..., description="生成是否成功")
    message: str = Field(..., description="生成结果消息")
    generated_cases: List[Dict[str, Any]] = Field(..., description="生成的基础用例列表")
    interface_info: Optional[Dict[str, Any]] = Field(None, description="接口信息")
    dependencies: Optional[List[Dict[str, Any]]] = Field(None, description="依赖信息")

    class Config:
        from_attributes = True


class ApiTestCaseGenerateRequest(BaseModel):
    """基于基础用例生成接口测试用例请求模型"""
    test_id: int = Field(..., description="测试环境ID")
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外的配置信息")

    class Config:
        from_attributes = True


class ApiTestCaseGenerateResponse(BaseModel):
    """基于基础用例生成接口测试用例响应模型"""
    success: bool = Field(..., description="生成是否成功")
    message: str = Field(..., description="生成结果消息")
    generated_cases: List[Dict[str, Any]] = Field(..., description="生成的接口测试用例列表")
    base_case_info: Optional[Dict[str, Any]] = Field(None, description="基础用例信息")
    interface_info: Optional[Dict[str, Any]] = Field(None, description="接口信息")
    test_environment_info: Optional[Dict[str, Any]] = Field(None, description="测试环境信息")
    dependencies: Optional[List[Dict[str, Any]]] = Field(None, description="依赖信息")

    class Config:
        from_attributes = True
