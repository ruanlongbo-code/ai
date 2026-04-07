"""功能测试模块数据模型"""
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RequirementCreateRequest(BaseModel):
    """需求创建请求模型"""
    module_id: int = Field(..., description="项目模块ID")
    title: str = Field(..., min_length=1, max_length=200, description="需求标题")
    doc_no: Optional[str] = Field(None, max_length=50, description="需求文档编号，可选")
    description: Optional[str] = Field(None, description="需求描述，可选")
    priority: int = Field(1, ge=1, le=3, description="需求优先级（1=低, 2=中, 3=高）")
    schedule_item_id: Optional[int] = Field(None, description="关联排期管理中的需求ID，可选")


class RequirementResponse(BaseModel):
    """需求响应模型"""
    id: int = Field(..., description="需求ID")
    module_id: Optional[int] = Field(None, description="项目模块ID")
    title: str = Field(..., description="需求标题")
    description: Optional[str] = Field(None, description="需求描述")
    priority: int = Field(..., description="需求优先级")
    status: str = Field(..., description="需求状态")
    schedule_item_id: Optional[int] = Field(None, description="关联排期需求ID")
    schedule_item_title: Optional[str] = Field(None, description="关联排期需求标题")
    creator_id: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class RequirementSimple(BaseModel):
    """简化的需求信息模型"""
    id: int = Field(..., description="需求ID")
    title: str = Field(..., description="需求标题")


class RequirementUpdateRequest(BaseModel):
    """修改需求请求模型"""
    title: str = Field(..., min_length=1, max_length=200, description="需求标题")
    description: Optional[str] = Field(None, description="需求描述")
    priority: int = Field(1, ge=1, le=5, description="优先级，1-5，数字越大优先级越高")
    status: str = Field(..., description="状态：0-禁用，1-启用，2-已完成")


class RequirementListResponse(BaseModel):
    """需求列表响应模型"""
    requirements: Dict[str, List[RequirementSimple]] = Field(..., description="按模块分组的需求列表")


class RequirementDetailItem(BaseModel):
    """需求详细信息模型"""
    id: int = Field(..., description="需求ID")
    module_id: Optional[int] = Field(None, description="项目模块ID")
    module_name: str = Field(..., description="模块名称")
    title: str = Field(..., description="需求标题")
    priority: int = Field(..., description="需求优先级")
    status: str = Field(..., description="需求状态")
    schedule_item_id: Optional[int] = Field(None, description="关联排期需求ID")
    schedule_item_title: Optional[str] = Field(None, description="关联排期需求标题")
    creator_id: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class RequirementDetailListResponse(BaseModel):
    """需求详细列表响应模型"""
    requirements: List[RequirementDetailItem] = Field(..., description="需求详细列表")
    total: int = Field(..., description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(1, description="总页数")


class RequirementReviewRequest(BaseModel):
    """需求审核请求模型"""
    status: str = Field(..., description="审核状态")


# ===== 用例集 Schemas =====

class FunctionalCaseSetSimple(BaseModel):
    """用例集简要信息"""
    id: int = Field(..., description="用例集ID")
    name: str = Field(..., description="用例集名称")
    description: Optional[str] = Field(None, description="用例集描述")
    case_count: int = Field(0, description="用例总数")
    scenario_count: int = Field(0, description="场景数")
    requirement_id: Optional[int] = Field(None, description="关联需求ID")
    requirement_title: Optional[str] = Field(None, description="关联需求标题")
    creator_name: Optional[str] = Field(None, description="创建人")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class FunctionalCaseSetListResponse(BaseModel):
    """用例集列表响应"""
    case_sets: List[FunctionalCaseSetSimple] = Field(..., description="用例集列表")
    total: int = Field(..., description="总数")


class ScenarioCaseGroup(BaseModel):
    """场景分组下的用例"""
    scenario: str = Field(..., description="场景名称")
    cases: List['FunctionalCaseSimple'] = Field(..., description="该场景下的用例列表")


class FunctionalCaseSetDetailResponse(BaseModel):
    """用例集详情响应（含场景分组）"""
    id: int
    name: str
    description: Optional[str] = None
    case_count: int = 0
    scenario_count: int = 0
    requirement_id: Optional[int] = None
    requirement_title: Optional[str] = None
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    scenario_groups: List[ScenarioCaseGroup] = Field(default_factory=list, description="按场景分组的用例")


class FunctionalCaseSetCreateRequest(BaseModel):
    """用例集创建请求"""
    name: str = Field(..., min_length=1, max_length=255, description="用例集名称")
    description: Optional[str] = Field(None, description="用例集描述")
    requirement_id: Optional[int] = Field(None, description="关联需求ID")


class FunctionalCaseSetUpdateRequest(BaseModel):
    """用例集更新请求"""
    name: Optional[str] = Field(None, max_length=255, description="用例集名称")
    description: Optional[str] = Field(None, description="用例集描述")


# ===== 测试点集 Schemas =====

class TestPointSimple(BaseModel):
    """测试点简要信息"""
    id: int
    name: str
    point_type: Optional[str] = None
    sort_order: int = 0

class TestPointSetSimple(BaseModel):
    """测试点集简要信息"""
    id: int
    name: str
    description: Optional[str] = None
    point_count: int = 0
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TestPointSetListResponse(BaseModel):
    """测试点集列表响应"""
    test_point_sets: List[TestPointSetSimple]
    total: int

class TestPointSetUpdateRequest(BaseModel):
    """测试点集更新请求"""
    name: Optional[str] = Field(None, max_length=255, description="测试点集名称")
    description: Optional[str] = Field(None, description="测试点集描述")


class TestPointSetDetailResponse(BaseModel):
    """测试点集详情响应（含测试点列表）"""
    id: int
    name: str
    description: Optional[str] = None
    point_count: int = 0
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    points: List[TestPointSimple] = Field(default_factory=list)


# ===== 用例 Schemas =====

class FunctionalCaseSimple(BaseModel):
    """简化的功能用例信息模型"""
    id: int = Field(..., description="用例ID")
    case_no: Optional[str] = Field(None, description="用例编号")
    case_name: str = Field(..., description="用例名称")
    priority: int = Field(..., description="优先级（1=P0, 2=P1, 3=P2, 4=P3）")
    status: str = Field(..., description="当前状态")
    scenario: Optional[str] = Field(None, description="所属测试场景")
    scenario_sort: int = Field(0, description="场景内排序")
    requirement_id: Optional[int] = Field(None, description="关联需求ID")
    requirement_title: Optional[str] = Field(None, description="关联需求标题")
    case_set_id: Optional[int] = Field(None, description="关联用例集ID")
    creator_name: Optional[str] = Field(None, description="创建人")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class FunctionalCaseListRequest(BaseModel):
    """功能用例列表请求模型"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，最大100")
    requirement_id: Optional[int] = Field(None, description="需求ID过滤，为空则获取所有")


class FunctionalCaseListResponse(BaseModel):
    """功能用例列表响应模型"""
    cases: List[FunctionalCaseSimple] = Field(..., description="功能用例列表")
    total: int = Field(..., description="总用例数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")


class FunctionalCaseCreateRequest(BaseModel):
    """功能用例创建请求模型"""
    case_no: Optional[str] = Field(None, max_length=100, description="用例编号")
    case_name: str = Field(..., min_length=1, max_length=255, description="用例名称")
    priority: int = Field(3, ge=1, le=4, description="优先级（1=P0, 2=P1, 3=P2, 4=P3）")
    scenario: Optional[str] = Field(None, description="所属测试场景")
    preconditions: Optional[str] = Field(None, description="前置步骤")
    test_steps: Optional[List[Dict]] = Field(None, description="测试步骤列表")
    test_data: Optional[Dict] = Field(None, description="输入数据")
    expected_result: Optional[str] = Field(None, description="预期结果")
    requirement_id: Optional[int] = Field(None, description="关联需求ID")
    case_set_id: Optional[int] = Field(None, description="关联用例集ID")


class FunctionalCaseUpdateRequest(BaseModel):
    """功能用例更新请求模型"""
    case_no: Optional[str] = Field(None, max_length=100, description="用例编号")
    case_name: str = Field(..., min_length=1, max_length=255, description="用例名称")
    priority: int = Field(3, ge=1, le=4, description="优先级（1=P0, 2=P1, 3=P2, 4=P3）")
    status: str = Field(..., description="当前状态")
    scenario: Optional[str] = Field(None, description="所属测试场景")
    preconditions: Optional[str] = Field(None, description="前置步骤")
    test_steps: Optional[List[Dict]] = Field(None, description="测试步骤列表")
    test_data: Optional[Dict] = Field(None, description="输入数据")
    expected_result: Optional[str] = Field(None, description="预期结果")
    actual_result: Optional[str] = Field(None, description="实际结果")
    requirement_id: Optional[int] = Field(None, description="关联需求ID")
    case_set_id: Optional[int] = Field(None, description="关联用例集ID")


class FunctionalCaseReviewRequest(BaseModel):
    """功能用例审核请求模型"""
    status: str = Field(..., description="审核后的状态（ready=审核通过, design=审核不通过）")


class FunctionalCaseResponse(BaseModel):
    """功能用例响应模型"""
    id: int = Field(..., description="用例ID")
    case_no: Optional[str] = Field(None, description="用例编号")
    case_name: str = Field(..., description="用例名称")
    priority: int = Field(..., description="优先级（1=P0, 2=P1, 3=P2, 4=P3）")
    status: str = Field(..., description="当前状态")
    scenario: Optional[str] = Field(None, description="所属测试场景")
    preconditions: Optional[str] = Field(None, description="前置步骤")
    test_steps: Optional[List[Dict]] = Field(None, description="测试步骤列表")
    test_data: Optional[Dict] = Field(None, description="输入数据")
    expected_result: Optional[str] = Field(None, description="预期结果")
    actual_result: Optional[str] = Field(None, description="实际结果")
    requirement_id: Optional[int] = Field(None, description="关联需求ID")
    case_set_id: Optional[int] = Field(None, description="关联用例集ID")
    creator_id: int = Field(..., description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# ==================== 飞书用例集导入 ====================

class FeishuCaseItem(BaseModel):
    """飞书导入用例条目"""
    case_title: str = Field(..., description="用例标题")
    module: str = Field("未分类", description="模块路径（/分隔多层级）")
    priority: Optional[str] = Field(None, description="优先级（P0/P1/P2/P3）")
    precondition: str = Field("", description="前置条件")
    test_steps: List[str] = Field(default_factory=list, description="测试步骤")
    expected_results: List[str] = Field(default_factory=list, description="预期结果")


class ImportToFeishuRequest(BaseModel):
    """导入飞书用例集请求"""
    requirement_id: Optional[int] = Field(None, description="需求ID（从数据库取用例）")
    case_set_id: Optional[int] = Field(None, description="用例集ID（从数据库取用例）")
    cases: Optional[List[FeishuCaseItem]] = Field(None, description="直接传入用例JSON数组")
    title: Optional[str] = Field(None, description="用例集标题（不传则自动生成）")
    feishu_token: Optional[str] = Field(None, description="飞书 x-token（可选，不传则使用服务端缓存）")
    dir_id: Optional[str] = Field(None, description="飞书用例管理目录ID")
    dir_name: Optional[str] = Field(None, description="飞书目录名称（会自动解析为 dir_id，支持 '/' 分隔路径）")


class ImportToFeishuResponse(BaseModel):
    """导入飞书用例集响应"""
    work_item_id: int = Field(..., description="飞书用例集工作项ID")
    case_set_url: str = Field(..., description="飞书用例集链接")
    case_count: int = Field(..., description="导入用例数量")


class FeishuDirItem(BaseModel):
    """飞书目录项"""
    id: str = Field(..., description="目录ID")
    name: str = Field(..., description="目录名称")
    parent_id: str = Field("", description="父目录ID")


class FeishuDirsResponse(BaseModel):
    """飞书目录列表响应"""
    dirs: List[FeishuDirItem] = Field(default_factory=list, description="目录列表")
