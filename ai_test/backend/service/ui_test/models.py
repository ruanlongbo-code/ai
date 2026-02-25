from tortoise.models import Model
from tortoise import fields


class UiTestPage(Model):
    """UI测试页面（页面对象）"""
    id = fields.IntField(pk=True, description="主键ID")
    project_id = fields.IntField(description="所属项目ID")
    name = fields.CharField(max_length=255, description="页面名称")
    url = fields.CharField(max_length=1000, description="页面URL")
    description = fields.TextField(null=True, description="页面描述")
    creator_id = fields.IntField(description="创建者ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "ui_test_page"
        table_description = "UI测试页面"


class UiTestCase(Model):
    """UI测试用例"""
    id = fields.IntField(pk=True, description="主键ID")
    project_id = fields.IntField(description="所属项目ID")
    page_id = fields.IntField(null=True, description="关联页面ID")
    name = fields.CharField(max_length=255, description="用例名称")
    priority = fields.CharField(max_length=10, default="P1", description="优先级(P0/P1/P2/P3)")
    preconditions = fields.TextField(null=True, description="前置条件")
    status = fields.CharField(max_length=20, default="draft", description="状态(draft/ready/passed/failed)")
    last_run_at = fields.DatetimeField(null=True, description="最近执行时间")
    creator_id = fields.IntField(description="创建者ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "ui_test_case"
        table_description = "UI测试用例"


class UiTestStep(Model):
    """UI测试步骤"""
    id = fields.IntField(pk=True, description="主键ID")
    case_id = fields.IntField(description="所属用例ID")
    sort_order = fields.IntField(default=0, description="步骤顺序")
    action = fields.TextField(description="操作描述（自然语言）")
    input_data = fields.TextField(null=True, description="输入数据")
    expected_result = fields.TextField(null=True, description="预期结果（AI验证用）")
    # 结构化断言字段
    assertion_type = fields.CharField(
        max_length=50, null=True, default=None,
        description="断言类型: url_contains/url_equals/title_contains/title_equals/"
                    "element_visible/element_hidden/element_text_contains/element_text_equals/"
                    "element_exists/page_contains/toast_contains"
    )
    assertion_target = fields.CharField(
        max_length=500, null=True, default=None,
        description="断言目标（CSS选择器或无）"
    )
    assertion_value = fields.TextField(
        null=True, default=None,
        description="断言期望值"
    )

    class Meta:
        table = "ui_test_step"
        table_description = "UI测试步骤"


class UiTestExecution(Model):
    """UI测试执行记录"""
    id = fields.IntField(pk=True, description="主键ID")
    case_id = fields.IntField(description="所属用例ID")
    project_id = fields.IntField(description="所属项目ID")
    status = fields.CharField(max_length=20, default="pending", description="执行状态(pending/running/passed/failed/error)")
    total_steps = fields.IntField(default=0, description="总步骤数")
    passed_steps = fields.IntField(default=0, description="通过步骤数")
    failed_steps = fields.IntField(default=0, description="失败步骤数")
    start_time = fields.DatetimeField(null=True, description="开始时间")
    end_time = fields.DatetimeField(null=True, description="结束时间")
    duration_ms = fields.IntField(null=True, description="总耗时(毫秒)")
    error_message = fields.TextField(null=True, description="错误信息")
    executor_id = fields.IntField(description="执行者ID")
    # 报告摘要（JSON）
    report_summary = fields.TextField(null=True, description="报告摘要JSON")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "ui_test_execution"
        table_description = "UI测试执行记录"


class UiTestStepResult(Model):
    """UI测试步骤执行结果"""
    id = fields.IntField(pk=True, description="主键ID")
    execution_id = fields.IntField(description="所属执行记录ID")
    step_id = fields.IntField(description="对应步骤ID")
    sort_order = fields.IntField(default=0, description="步骤顺序")
    status = fields.CharField(max_length=20, default="pending", description="执行状态(pending/running/passed/failed/skipped)")
    screenshot_path = fields.CharField(max_length=500, null=True, description="截图文件路径")
    ai_action = fields.TextField(null=True, description="AI执行的操作（JSON）")
    actual_result = fields.TextField(null=True, description="实际结果")
    error_message = fields.TextField(null=True, description="错误信息")
    duration_ms = fields.IntField(null=True, description="耗时(毫秒)")
    # 断言结果
    assertion_type = fields.CharField(max_length=50, null=True, description="断言类型")
    assertion_passed = fields.BooleanField(null=True, description="断言是否通过")
    assertion_detail = fields.TextField(null=True, description="断言详情")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "ui_test_step_result"
        table_description = "UI测试步骤执行结果"
