"""测试排期管理模块数据模型"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# ==================== 测试阶段标签（按软件测试流程正序） ====================

PROGRESS_STAGE_TAGS = [
    {"key": "requirement_clarify", "label": "参与需求澄清"},
    {"key": "tech_review", "label": "参与技术评审"},
    {"key": "case_writing", "label": "用例编写"},
    {"key": "case_review", "label": "用例评审"},
    {"key": "smoke_test", "label": "冒烟测试"},
    {"key": "first_round_test", "label": "一轮测试"},
    {"key": "functional_test", "label": "功能测试"},
    {"key": "exploratory_test", "label": "探索性测试"},
    {"key": "cross_test", "label": "交叉测试"},
    {"key": "regression_test", "label": "回归测试"},
    {"key": "bug_verify", "label": "Bug验证"},
]

PROGRESS_STATUS_OPTIONS = [
    {"key": "normal", "label": "正常推进"},
    {"key": "blocked", "label": "阻塞等待"},
    {"key": "ahead", "label": "提前完成"},
    {"key": "delayed", "label": "进度延迟"},
]

# ==================== 需求状态枚举（对齐飞书项目） ====================

REQUIREMENT_STATUS_OPTIONS = [
    {"key": "paused", "label": "暂停"},
    {"key": "clarified_pending_review", "label": "已澄清&待技术评审"},
    {"key": "pending", "label": "待排期"},
    {"key": "scheduled", "label": "已排期待开发"},
    {"key": "developing", "label": "开发中"},
    {"key": "submitted_testing", "label": "已提测"},
    {"key": "testing", "label": "测试中"},
    {"key": "test_done_pending_release", "label": "测试完成待发布"},
    {"key": "gray_ab_testing", "label": "灰度/AB中"},
    {"key": "released", "label": "已上线"},
    {"key": "no_test_needed", "label": "免测"},
]

# ==================== 智能状态映射 ====================

# 测试阶段 → 需求状态（取选中阶段中最高的映射）
STAGE_TO_REQUIREMENT_STATUS = {
    "requirement_clarify": "clarified_pending_review",
    "tech_review": "pending",
    "case_writing": None,
    "case_review": None,
    "smoke_test": "testing",
    "first_round_test": "testing",
    "functional_test": "testing",
    "exploratory_test": "testing",
    "cross_test": "testing",
    "regression_test": "testing",
    "bug_verify": "testing",
}

# 测试阶段 → 用例状态
STAGE_TO_CASE_STATUS = {
    "requirement_clarify": None,
    "tech_review": None,
    "case_writing": "in_progress",
    "case_review": "in_progress",
    "smoke_test": "completed",
    "first_round_test": "completed",
    "functional_test": "completed",
    "exploratory_test": "completed",
    "cross_test": "completed",
    "regression_test": "completed",
    "bug_verify": "completed",
}

# 未进入正式测试的阶段（不需要填写用例/Bug数据即可提交）
PRE_TESTING_STAGES = {"requirement_clarify", "tech_review", "case_writing", "case_review"}
FORMAL_TESTING_STAGES = {"smoke_test", "first_round_test", "functional_test", "exploratory_test", "cross_test", "regression_test", "bug_verify"}

# 阶段优先级顺序（index越大优先级越高，用于确定最高阶段）
STAGE_PRIORITY_ORDER = [
    "requirement_clarify", "tech_review", "case_writing", "case_review",
    "smoke_test", "first_round_test", "functional_test", "exploratory_test",
    "cross_test", "regression_test", "bug_verify",
]


# ==================== 迭代相关 ====================

class IterationCreateRequest(BaseModel):
    """创建迭代请求"""
    name: str = Field(..., min_length=1, max_length=100, description="迭代名称")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    status: str = Field("active", description="状态")


class IterationUpdateRequest(BaseModel):
    """更新迭代请求"""
    name: Optional[str] = Field(None, max_length=100, description="迭代名称")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    status: Optional[str] = Field(None, description="状态")


class IterationResponse(BaseModel):
    """迭代响应"""
    id: int
    name: str
    project_id: int
    start_date: date
    end_date: date
    status: str
    created_by_id: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # 汇总信息
    total_items: int = 0
    completed_items: int = 0
    overall_progress: int = 0
    remaining_days: int = 0


class IterationListResponse(BaseModel):
    """迭代列表响应"""
    iterations: List[IterationResponse]
    total: int


# ==================== 排期条目相关 ====================

class ScheduleItemCreateRequest(BaseModel):
    """创建排期条目请求"""
    iteration_id: int = Field(..., description="所属迭代ID")
    requirement_title: str = Field(..., min_length=1, max_length=500, description="需求名称")
    requirement_id: Optional[int] = Field(None, description="关联平台需求ID")
    category: Optional[str] = Field(None, max_length=50, description="业务线分类")
    assignee_id: int = Field(..., description="测试负责人ID")
    requirement_status: str = Field("pending", description="需求状态")
    ticket_url: Optional[str] = Field(None, max_length=500, description="需求工单链接")
    priority: Optional[str] = Field(None, max_length=10, description="优先级")
    planned_test_date: Optional[str] = Field(None, max_length=50, description="预计提测时间")
    estimated_case_days: Optional[float] = Field(None, description="预估用例人日")
    case_output_date: Optional[str] = Field(None, max_length=50, description="用例输出时间")
    case_status: Optional[str] = Field(None, description="用例状态")
    estimated_test_days: Optional[float] = Field(None, description="预估测试人日")
    test_date_range: Optional[str] = Field(None, max_length=50, description="测试时间段")
    integration_test_date: Optional[str] = Field(None, max_length=50, description="集成测试时间")
    remark: Optional[str] = Field(None, description="备注")


class ScheduleItemUpdateRequest(BaseModel):
    """更新排期条目请求"""
    requirement_title: Optional[str] = Field(None, max_length=500)
    requirement_id: Optional[int] = None
    category: Optional[str] = None
    assignee_id: Optional[int] = None
    requirement_status: Optional[str] = None
    ticket_url: Optional[str] = None
    priority: Optional[str] = None
    planned_test_date: Optional[str] = None
    estimated_case_days: Optional[float] = None
    case_output_date: Optional[str] = None
    case_status: Optional[str] = None
    estimated_test_days: Optional[float] = None
    test_date_range: Optional[str] = None
    integration_test_date: Optional[str] = None
    remark: Optional[str] = None
    actual_progress: Optional[int] = None


class ScheduleItemResponse(BaseModel):
    """排期条目响应"""
    id: int
    iteration_id: int
    requirement_title: str
    requirement_id: Optional[int] = None
    category: Optional[str] = None
    assignee_id: int
    assignee_name: Optional[str] = None
    requirement_status: str
    ticket_url: Optional[str] = None
    priority: Optional[str] = None
    planned_test_date: Optional[str] = None
    estimated_case_days: Optional[float] = None
    case_output_date: Optional[str] = None
    case_status: Optional[str] = None
    estimated_test_days: Optional[float] = None
    test_date_range: Optional[str] = None
    integration_test_date: Optional[str] = None
    remark: Optional[str] = None
    actual_progress: int = 0
    risk_level: str = "none"
    risk_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ScheduleItemListResponse(BaseModel):
    """排期条目列表响应（按分类分组）"""
    items: List[ScheduleItemResponse]
    total: int
    categories: List[str] = []


# ==================== 日报相关 ====================

class DailyReportCreateRequest(BaseModel):
    """同步测试进度请求"""
    schedule_item_id: int = Field(..., description="关联排期条目ID")
    today_progress: str = Field(..., min_length=1, description="今日进展（JSON格式或纯文本）")
    next_plan: Optional[str] = Field(None, description="明日计划")
    stage_tags: Optional[List[str]] = Field(None, description="测试阶段标签列表（用于智能同步状态）")
    # Bug/用例数据会从缺陷表自动统计，也支持手动覆盖
    bug_total: Optional[int] = Field(None, description="Bug总数")
    bug_open: Optional[int] = Field(None, description="待处理Bug数")
    bug_fixed: Optional[int] = Field(None, description="已修复Bug数")
    bug_closed: Optional[int] = Field(None, description="已关闭Bug数")
    case_execution_progress: Optional[int] = Field(None, ge=0, le=100, description="用例执行进度百分比")
    actual_progress: Optional[int] = Field(None, ge=0, le=100, description="更新进度百分比")


class DailyReportResponse(BaseModel):
    """日报响应"""
    id: int
    schedule_item_id: int
    requirement_title: Optional[str] = None
    reporter_id: int
    reporter_name: Optional[str] = None
    report_date: date
    today_progress: str
    next_plan: Optional[str] = None
    case_execution_progress: Optional[int] = 0
    bug_total: int = 0
    bug_open: int = 0
    bug_fixed: int = 0
    bug_closed: int = 0
    ai_report_content: Optional[str] = None
    feishu_sent: bool = False
    actual_progress: int = 0
    risk_level: str = "none"
    requirement_status: Optional[str] = None
    case_status: Optional[str] = None
    created_at: datetime


class DailyReportListResponse(BaseModel):
    """日报列表响应"""
    reports: List[DailyReportResponse]
    total: int


# ==================== Dashboard 相关 ====================

class DashboardDailyUpdate(BaseModel):
    """Dashboard 当日更新条目"""
    reporter_name: str
    reporter_id: int
    reports: List[DailyReportResponse]


class DashboardDailyResponse(BaseModel):
    """Dashboard 当日动态响应（场景1）"""
    date: date
    updates: List[DashboardDailyUpdate]
    no_report_users: List[str] = []
    # 当日统计
    daily_bugs_new: int = 0
    daily_bugs_closed: int = 0
    daily_cases_executed: int = 0


class IterationSummaryItem(BaseModel):
    """迭代汇总中的需求条目"""
    id: int
    requirement_title: str
    assignee_name: Optional[str] = None
    requirement_status: str
    priority: Optional[str] = None
    case_execution_progress: int = 0
    bug_total: int = 0
    bug_open: int = 0
    actual_progress: int = 0
    risk_level: str = "none"
    case_status: Optional[str] = None
    risk_reason: Optional[str] = None


class DashboardIterationSummaryResponse(BaseModel):
    """Dashboard 迭代汇总响应（场景2&3）"""
    iteration_id: int
    iteration_name: str
    start_date: date
    end_date: date
    remaining_days: int
    is_closing: bool = False  # 是否处于收尾阶段（剩余<=3天）
    overall_progress: int = 0
    total_requirements: int = 0
    completed_requirements: int = 0
    testing_requirements: int = 0
    developing_requirements: int = 0
    total_bugs: int = 0
    open_bugs: int = 0
    items: List[IterationSummaryItem] = []
    # 收尾模式分组
    high_risk_items: List[IterationSummaryItem] = []
    medium_risk_items: List[IterationSummaryItem] = []
    ready_items: List[IterationSummaryItem] = []


# ==================== 飞书Webhook相关 ====================

class FeishuWebhookCreateRequest(BaseModel):
    """创建需求群Webhook请求"""
    name: str = Field(..., min_length=1, max_length=100, description="群名称")
    webhook_url: str = Field(..., min_length=1, max_length=500, description="Webhook URL")
    linked_schedule_item_ids: Optional[List[int]] = Field(None, description="关联排期条目（需求）ID列表")


class FeishuWebhookUpdateRequest(BaseModel):
    """更新需求群Webhook请求"""
    name: Optional[str] = Field(None, max_length=100)
    webhook_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    linked_schedule_item_ids: Optional[List[int]] = Field(None, description="关联排期条目（需求）ID列表")


class FeishuWebhookResponse(BaseModel):
    """需求群Webhook响应"""
    id: int
    project_id: int
    name: str
    webhook_url: str
    is_active: bool
    linked_schedule_item_ids: Optional[List[int]] = None
    linked_requirement_names: Optional[List[str]] = None
    created_by_id: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FeishuWebhookListResponse(BaseModel):
    """需求群Webhook列表响应"""
    webhooks: List[FeishuWebhookResponse]
    total: int


# ==================== 飞书推送相关 ====================

class FeishuSendRequest(BaseModel):
    """飞书推送请求"""
    webhook_ids: List[int] = Field(..., description="要推送的Webhook ID列表")
    report_id: int = Field(..., description="日报ID")


# ==================== AI报告编辑相关 ====================

class AiReportUpdateRequest(BaseModel):
    """编辑AI报告内容"""
    ai_report_content: str = Field(..., description="编辑后的AI报告内容")


# ==================== 进度计算相关 ====================

class ProgressCalculateRequest(BaseModel):
    """进度计算请求"""
    schedule_item_id: int = Field(..., description="排期条目ID")
    stage_tags: List[str] = Field(default=[], description="测试阶段标签")
    progress_status: Optional[str] = Field(None, description="进度状态")
    case_execution_progress: Optional[int] = Field(None, ge=0, le=100, description="用例执行进度百分比")


class ProgressCalculateResponse(BaseModel):
    """进度计算响应"""
    suggested_progress: int = Field(..., description="AI建议进度")
    factors: List[str] = Field(default=[], description="计算因子说明")


# ==================== 缺陷管理相关 ====================

class DefectCreateRequest(BaseModel):
    """创建缺陷单请求"""
    schedule_item_id: int = Field(..., description="关联排期条目（需求）ID")
    title: str = Field(..., min_length=1, max_length=500, description="缺陷标题")
    description: str = Field("", description="缺陷描述")
    defect_type: str = Field("functional", description="缺陷类型")
    severity: str = Field("P2", description="严重程度 P0/P1/P2/P3")
    assignee_id: Optional[int] = Field(None, description="经办人（开发）ID")
    reproduce_steps: Optional[str] = Field(None, description="复现步骤")
    expected_result: Optional[str] = Field(None, description="预期结果")
    actual_result: Optional[str] = Field(None, description="实际结果")


class DefectUpdateRequest(BaseModel):
    """更新缺陷单请求"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    defect_type: Optional[str] = None
    severity: Optional[str] = None
    defect_status: Optional[str] = None
    assignee_id: Optional[int] = None
    reproduce_steps: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None


class DefectResponse(BaseModel):
    """缺陷单响应"""
    id: int
    schedule_item_id: int
    requirement_title: Optional[str] = None
    title: str
    description: str
    defect_type: str
    severity: str
    defect_status: str
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    reporter_id: int
    reporter_name: Optional[str] = None
    screenshots: Optional[List[str]] = None
    reproduce_steps: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    feishu_ticket_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DefectListResponse(BaseModel):
    """缺陷列表响应"""
    defects: List[DefectResponse]
    total: int


class DefectStatsResponse(BaseModel):
    """缺陷统计响应"""
    total: int = 0
    open: int = 0
    fixing: int = 0
    fixed: int = 0
    verified: int = 0
    closed: int = 0
    rejected: int = 0
    by_severity: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
