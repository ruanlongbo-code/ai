"""
测试排期管理模块数据库模型
包含：迭代管理、排期条目、测试日报、进度报告、飞书Webhook配置
"""
from tortoise.models import Model
from tortoise import fields


class TestIteration(Model):
    """测试迭代表"""
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=100, description="迭代名称，如 2.06迭代")
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='iterations',
        on_delete=fields.CASCADE,
        description="关联项目"
    )
    start_date = fields.DateField(description="迭代开始日期")
    end_date = fields.DateField(description="迭代结束日期")
    status = fields.CharField(
        max_length=20, default='active',
        description="状态（draft=草稿, active=进行中, completed=已完成, archived=已归档）"
    )
    created_by = fields.ForeignKeyField(
        'models.User',
        related_name='created_iterations',
        on_delete=fields.CASCADE,
        description="创建人（Leader）"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "test_iteration"
        table_description = "测试迭代表"


class ScheduleItem(Model):
    """排期条目表 - 对应飞书需求排期表的每一行"""
    id = fields.IntField(pk=True, description="主键ID")
    iteration = fields.ForeignKeyField(
        'models.TestIteration',
        related_name='schedule_items',
        on_delete=fields.CASCADE,
        description="所属迭代"
    )
    requirement_title = fields.CharField(max_length=500, description="需求名称")
    requirement_id = fields.IntField(null=True, description="关联平台需求ID（可选）")
    category = fields.CharField(max_length=50, null=True, description="业务线分类（如 Solution/Payment）")
    assignee = fields.ForeignKeyField(
        'models.User',
        related_name='assigned_schedule_items',
        on_delete=fields.CASCADE,
        description="测试负责人"
    )
    requirement_status = fields.CharField(
        max_length=30, default='pending',
        description="需求当前状态（pending=待排期, scheduled=已排期, developing=开发中, testing=测试中, completed=已完成）"
    )
    ticket_url = fields.CharField(max_length=500, null=True, description="需求工单链接")
    priority = fields.CharField(max_length=10, null=True, description="优先级（P0/P1/P2/P3）")
    planned_test_date = fields.CharField(max_length=50, null=True, description="预计提测时间")
    estimated_case_days = fields.DecimalField(max_digits=5, decimal_places=1, null=True, description="预估用例人日")
    case_output_date = fields.CharField(max_length=50, null=True, description="用例输出时间")
    case_status = fields.CharField(
        max_length=20, null=True,
        description="用例状态（pending=未开始, in_progress=进行中, completed=已完成）"
    )
    estimated_test_days = fields.DecimalField(max_digits=5, decimal_places=1, null=True, description="预估测试人日")
    test_date_range = fields.CharField(max_length=50, null=True, description="测试时间段")
    integration_test_date = fields.CharField(max_length=50, null=True, description="集成测试时间")
    remark = fields.TextField(null=True, description="备注")
    # 系统自动计算字段
    actual_progress = fields.SmallIntField(default=0, description="实际完成百分比（0-100）")
    risk_level = fields.CharField(
        max_length=10, default='none',
        description="风险等级（none=无风险, low=低风险, medium=中风险, high=高风险）"
    )
    risk_reason = fields.CharField(max_length=500, null=True, description="风险原因")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "schedule_item"
        table_description = "排期条目表"


class DailyReport(Model):
    """测试日报表 - 测试人员每日提交"""
    id = fields.IntField(pk=True, description="主键ID")
    schedule_item = fields.ForeignKeyField(
        'models.ScheduleItem',
        related_name='daily_reports',
        on_delete=fields.CASCADE,
        description="关联排期条目"
    )
    reporter = fields.ForeignKeyField(
        'models.User',
        related_name='daily_reports',
        on_delete=fields.CASCADE,
        description="提交人"
    )
    report_date = fields.DateField(description="报告日期")
    today_progress = fields.TextField(description="今日进展")
    next_plan = fields.TextField(null=True, description="明日计划")
    # 系统自动采集的数据快照
    case_total = fields.IntField(default=0, description="用例总数")
    case_executed = fields.IntField(default=0, description="已执行用例数")
    case_passed = fields.IntField(default=0, description="通过用例数")
    case_failed = fields.IntField(default=0, description="失败用例数")
    bug_total = fields.IntField(default=0, description="Bug总数")
    bug_open = fields.IntField(default=0, description="待处理Bug数")
    bug_fixed = fields.IntField(default=0, description="已修复Bug数")
    bug_closed = fields.IntField(default=0, description="已关闭Bug数")
    # AI生成的格式化报告
    ai_report_content = fields.TextField(null=True, description="AI生成的格式化报告内容")
    # 飞书推送状态
    feishu_sent = fields.BooleanField(default=False, description="是否已推送到飞书群")
    feishu_sent_at = fields.DatetimeField(null=True, description="飞书推送时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "daily_report"
        table_description = "测试日报表"
        unique_together = (("schedule_item", "reporter", "report_date"),)


class ProgressReport(Model):
    """迭代进度报告表 - 管理员查看的汇总报告"""
    id = fields.IntField(pk=True, description="主键ID")
    iteration = fields.ForeignKeyField(
        'models.TestIteration',
        related_name='progress_reports',
        on_delete=fields.CASCADE,
        description="关联迭代"
    )
    report_date = fields.DateField(description="报告日期")
    report_type = fields.CharField(
        max_length=20, default='daily',
        description="报告类型（daily=每日, weekly=每周, milestone=里程碑, closing=收尾）"
    )
    # 统计数据快照
    overall_progress = fields.SmallIntField(default=0, description="整体完成百分比")
    total_requirements = fields.IntField(default=0, description="总需求数")
    completed_requirements = fields.IntField(default=0, description="已完成需求数")
    testing_requirements = fields.IntField(default=0, description="测试中需求数")
    developing_requirements = fields.IntField(default=0, description="开发中需求数")
    total_cases = fields.IntField(default=0, description="总用例数")
    executed_cases = fields.IntField(default=0, description="已执行用例数")
    passed_cases = fields.IntField(default=0, description="通过用例数")
    total_bugs = fields.IntField(default=0, description="总Bug数")
    open_bugs = fields.IntField(default=0, description="待处理Bug数")
    # AI分析内容
    ai_summary = fields.TextField(null=True, description="AI生成的摘要")
    ai_risk_analysis = fields.TextField(null=True, description="AI风险分析")
    risk_items = fields.JSONField(null=True, description="风险条目列表（JSON）")
    # 状态
    is_read = fields.BooleanField(default=False, description="管理员是否已读")
    generated_by = fields.CharField(max_length=20, default='auto', description="生成方式（auto/manual）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "progress_report"
        table_description = "迭代进度报告表"


class FeishuWebhook(Model):
    """飞书群Webhook配置表"""
    id = fields.IntField(pk=True, description="主键ID")
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='feishu_webhooks',
        on_delete=fields.CASCADE,
        description="关联项目"
    )
    name = fields.CharField(max_length=100, description="群名称")
    webhook_url = fields.CharField(max_length=500, description="Webhook URL")
    is_active = fields.BooleanField(default=True, description="是否启用")
    created_by = fields.ForeignKeyField(
        'models.User',
        related_name='created_webhooks',
        on_delete=fields.CASCADE,
        description="创建人"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "feishu_webhook"
        table_description = "飞书群Webhook配置表"
