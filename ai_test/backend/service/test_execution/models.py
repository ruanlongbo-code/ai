"""
测试执行模块数据库模型
"""
from tortoise.models import Model
from tortoise import fields


class ApiCaseRun(Model):
    """API用例运行记录表"""
    id = fields.IntField(pk=True, description="主键ID")
    suite_run = fields.ForeignKeyField(
        'models.TestSuiteRun',
        related_name='case_runs',
        on_delete=fields.CASCADE,
        null=True,
        description="所属套件运行记录ID"
    )
    api_case = fields.ForeignKeyField(
        'models.ApiTestCase',
        related_name='case_runs',
        on_delete=fields.CASCADE,
        description="可执行用例ID"
    )
    case_name = fields.CharField(max_length=255, description="用例名称")
    error_message = fields.TextField(null=True, description="错误信息")
    traceback = fields.TextField(null=True, description="异常堆栈")
    start_time = fields.DatetimeField(null=True, description="执行开始时间")
    end_time = fields.DatetimeField(null=True, description="执行结束时间")
    duration = fields.FloatField(null=True, description="执行时长（秒）")
    logs = fields.JSONField(null=True, description="执行日志列表")
    api_requests_info = fields.JSONField(null=True, description="接口请求信息列表")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    # 执行结果 success  failed error
    status = fields.CharField(max_length=20, null=True, description="执行结果")

    class Meta:
        table = "api_case_run"
        table_description = "API用例运行记录表"


class TestSuiteRun(Model):
    """API测试套件运行记录表"""
    id = fields.IntField(pk=True, description="主键ID")
    suite = fields.ForeignKeyField(
        'models.TestSuite',
        related_name='suite_runs',
        on_delete=fields.CASCADE,
        description="所属套件ID"
    )
    run_task = fields.ForeignKeyField(
        'models.TestTaskRun',
        related_name='suite_runs',
        on_delete=fields.CASCADE,
        null=True,
        description="所属任务ID"
    )
    status = fields.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending',
        description="套件执行状态"
    )
    total_cases = fields.IntField(default=0, description="套件包含的总用例数")
    passed_cases = fields.IntField(default=0, description="执行通过的用例数")
    failed_cases = fields.IntField(default=0, description="执行失败的用例数")
    skipped_cases = fields.IntField(default=0, description="被跳过的用例数")
    error_cases = fields.IntField(default=0, description="执行出错的用例数")
    start_time = fields.DatetimeField(null=True, description="套件执行开始时间")
    end_time = fields.DatetimeField(null=True, description="套件执行结束时间")
    duration = fields.FloatField(null=True, description="执行时长（秒）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "test_suite_run"
        table_description = "API测试套件运行记录表"


class TestTaskRun(Model):
    """API测试任务运行记录表"""
    id = fields.IntField(pk=True, description="主键ID")
    task = fields.ForeignKeyField(
        'models.TestTask',
        related_name='task_runs',
        on_delete=fields.CASCADE,
        description="所属任务ID"
    )
    status = fields.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending',
        description="任务执行状态"
    )
    total_suites = fields.IntField(default=0, description="任务包含的总套件数")
    total_cases = fields.IntField(default=0, description="任务包含的总用例数")
    passed_cases = fields.IntField(default=0, description="执行通过的用例数")
    failed_cases = fields.IntField(default=0, description="执行失败的用例数")
    skipped_cases = fields.IntField(default=0, description="被跳过的用例数")
    start_time = fields.DatetimeField(null=True, description="任务执行开始时间")
    end_time = fields.DatetimeField(null=True, description="任务执行结束时间")
    duration = fields.FloatField(null=True, description="执行时长（秒）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "test_task_run"
        table_description = "API测试任务运行记录表"
