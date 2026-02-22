"""测试排期管理模块数据模型"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


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
    """提交日报请求"""
    schedule_item_id: int = Field(..., description="关联排期条目ID")
    today_progress: str = Field(..., min_length=1, description="今日进展")
    next_plan: Optional[str] = Field(None, description="明日计划")
    # 可选：手动填写的Bug概况
    bug_total: Optional[int] = Field(None, description="Bug总数")
    bug_open: Optional[int] = Field(None, description="待处理Bug数")
    bug_fixed: Optional[int] = Field(None, description="已修复Bug数")
    bug_closed: Optional[int] = Field(None, description="已关闭Bug数")
    # 可选：手动填写的用例概况
    case_total: Optional[int] = Field(None, description="用例总数")
    case_executed: Optional[int] = Field(None, description="已执行用例数")
    case_passed: Optional[int] = Field(None, description="通过用例数")
    case_failed: Optional[int] = Field(None, description="失败用例数")
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
    case_total: int = 0
    case_executed: int = 0
    case_passed: int = 0
    case_failed: int = 0
    bug_total: int = 0
    bug_open: int = 0
    bug_fixed: int = 0
    bug_closed: int = 0
    ai_report_content: Optional[str] = None
    feishu_sent: bool = False
    actual_progress: int = 0
    risk_level: str = "none"
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
    case_total: int = 0
    case_executed: int = 0
    bug_total: int = 0
    bug_open: int = 0
    actual_progress: int = 0
    risk_level: str = "none"
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
    total_cases: int = 0
    executed_cases: int = 0
    passed_cases: int = 0
    total_bugs: int = 0
    open_bugs: int = 0
    items: List[IterationSummaryItem] = []
    # 收尾模式分组
    high_risk_items: List[IterationSummaryItem] = []
    medium_risk_items: List[IterationSummaryItem] = []
    ready_items: List[IterationSummaryItem] = []


# ==================== 飞书Webhook相关 ====================

class FeishuWebhookCreateRequest(BaseModel):
    """创建飞书Webhook请求"""
    name: str = Field(..., min_length=1, max_length=100, description="群名称")
    webhook_url: str = Field(..., min_length=1, max_length=500, description="Webhook URL")


class FeishuWebhookUpdateRequest(BaseModel):
    """更新飞书Webhook请求"""
    name: Optional[str] = Field(None, max_length=100)
    webhook_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class FeishuWebhookResponse(BaseModel):
    """飞书Webhook响应"""
    id: int
    project_id: int
    name: str
    webhook_url: str
    is_active: bool
    created_by_id: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FeishuWebhookListResponse(BaseModel):
    """飞书Webhook列表响应"""
    webhooks: List[FeishuWebhookResponse]
    total: int


# ==================== 飞书推送相关 ====================

class FeishuSendRequest(BaseModel):
    """飞书推送请求"""
    webhook_ids: List[int] = Field(..., description="要推送的Webhook ID列表")
    report_id: int = Field(..., description="日报ID")
