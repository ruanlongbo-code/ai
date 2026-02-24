"""
接口测试模块数据库模型
"""
from tortoise.models import Model
from tortoise import fields


class ApiInterface(Model):
    """接口表"""
    id = fields.IntField(pk=True, description="主键ID，自增")
    method = fields.CharField(max_length=10, description="HTTP请求方法")
    path = fields.CharField(max_length=255, description="接口路径")
    summary = fields.TextField(null=True, description="接口简要说明")
    parameters = fields.JSONField(description="查询参数说明")
    request_body = fields.JSONField(description="请求体结构")
    responses = fields.JSONField(description="响应体结构")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 外键关联
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='api_interfaces',
        on_delete=fields.CASCADE,
        description="所属项目"
    )

    class Meta:
        table = "api_interface"
        table_description = "接口表"


class ApiDependencyGroup(Model):
    """接口依赖分组表"""
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=100, description="分组名称")
    description = fields.TextField(null=True, description="分组描述")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 外键关联
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='api_dependency_groups',
        on_delete=fields.CASCADE,
        description="所属项目"
    )
    creator = fields.ForeignKeyField(
        'models.User',
        related_name='created_api_dependency_groups',
        on_delete=fields.CASCADE,
        description="创建人"
    )
    target_interface = fields.ForeignKeyField(
        'models.ApiInterface',
        related_name='dependency_groups',
        on_delete=fields.CASCADE,
        description="目标接口"
    )

    class Meta:
        table = "api_dependency_group"
        table_description = "接口依赖分组表"


class ApiDependency(Model):
    """接口依赖表"""
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=100, description="依赖名称")
    description = fields.TextField(null=True, description="依赖描述")
    dependency_type = fields.CharField(max_length=20, description="依赖类型（header=请求头, param=参数, body=请求体, response=响应）")
    source_interface_id = fields.IntField(null=True, description="源接口ID")
    source_field_path = fields.CharField(max_length=255, null=True, description="源字段路径")
    target_field_name = fields.CharField(max_length=100, description="目标字段名称")
    transform_rule = fields.JSONField(null=True, description="转换规则")
    is_active = fields.BooleanField(default=True, description="是否启用")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    # 外键关联
    dependency_group = fields.ForeignKeyField(
        'models.ApiDependencyGroup',
        related_name='dependencies',
        on_delete=fields.CASCADE,
        description="所属分组"
    )

    class Meta:
        table = "api_dependency"
        table_description = "接口依赖表"


class ApiBaseCase(Model):
    """基础用例表api_base_case"""
    id = fields.IntField(pk=True, description="主键ID，自增")
    name = fields.CharField(max_length=255, description="测试用例名称")
    steps = fields.JSONField(description="测试步骤列表")
    expected = fields.JSONField(description="预期结果列表")
    status = fields.CharField(max_length=20, description="用例状态")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    interface = fields.ForeignKeyField(
        'models.ApiInterface',
        related_name='base_cases',
        on_delete=fields.CASCADE,
        description="关联接口"
    )
    class Meta:
        table = "api_base_case"
        table_description = "基础用例表"


class ApiTestCase(Model):
    """API 测试用例api_test_case"""
    id = fields.IntField(pk=True, description="自增主键ID")
    name = fields.CharField(max_length=255, description="用例名称")
    description = fields.TextField(null=True, description="用例描述")
    interface_name = fields.CharField(max_length=255, null=True, description="接口名称")
    type = fields.CharField(
        max_length=20,
        default='api',
        description="用例类型"
    )  # api=接口用例，business=业务流用例
    preconditions = fields.JSONField(null=True, description="前置步骤列表", default=[])
    request = fields.JSONField(null=True, description="主请求信息")
    assertions = fields.JSONField(null=True, description="断言信息")
    test_data = fields.JSONField(null=True, description="数据驱动测试数据集", default=None)
    status = fields.CharField(
        max_length=20,
        default='pending',
        description="用例状态"
    )  # pending=待审核（不可执行）、ready=可执行、disabled=不可执行
    generation_count = fields.IntField(default=1, description="用例生成次数")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    base_case = fields.ForeignKeyField(
        'models.ApiBaseCase',
        related_name='test_cases',
        on_delete=fields.CASCADE,
        description="关联的基础用例"
    )

    class Meta:
        table = "api_test_case"
        table_description = "API测试用例表"


class QuickDebugHistory(Model):
    """快捷调试请求历史记录"""
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=255, null=True, description="请求名称备注")
    method = fields.CharField(max_length=10, description="HTTP请求方法")
    url = fields.TextField(description="请求URL（含路径）")
    headers = fields.JSONField(null=True, description="请求头", default={})
    params = fields.JSONField(null=True, description="查询参数", default={})
    body = fields.JSONField(null=True, description="请求体", default=None)
    body_type = fields.CharField(max_length=20, default='json', description="请求体类型 json/form/text/none")
    response_status = fields.IntField(null=True, description="响应状态码")
    response_headers = fields.JSONField(null=True, description="响应头")
    response_body = fields.TextField(null=True, description="响应体（截断保存）")
    response_time = fields.FloatField(null=True, description="响应耗时（毫秒）")
    response_size = fields.IntField(null=True, description="响应大小（字节）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    # 外键关联
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='quick_debug_histories',
        on_delete=fields.CASCADE,
        description="所属项目"
    )
    user = fields.ForeignKeyField(
        'models.User',
        related_name='quick_debug_histories',
        on_delete=fields.CASCADE,
        description="操作用户"
    )

    class Meta:
        table = "quick_debug_history"
        table_description = "快捷调试请求历史记录"


class ScheduledTask(Model):
    """定时/CI触发执行任务"""
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=200, description="定时任务名称")
    task_type = fields.CharField(max_length=20, default='cron', description="触发类型 cron/ci/manual")
    cron_expression = fields.CharField(max_length=100, null=True, description="Cron表达式（如 0 8 * * *）")
    test_task = fields.ForeignKeyField(
        'models.TestTask',
        related_name='scheduled_tasks',
        on_delete=fields.CASCADE,
        description="关联的测试任务/计划"
    )
    environment = fields.ForeignKeyField(
        'models.TestEnvironment',
        related_name='scheduled_tasks',
        on_delete=fields.CASCADE,
        description="执行环境"
    )
    is_active = fields.BooleanField(default=True, description="是否启用")
    last_run_at = fields.DatetimeField(null=True, description="上次执行时间")
    next_run_at = fields.DatetimeField(null=True, description="下次执行时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='scheduled_tasks',
        on_delete=fields.CASCADE,
        description="所属项目"
    )
    creator = fields.ForeignKeyField(
        'models.User',
        related_name='created_scheduled_tasks',
        on_delete=fields.CASCADE,
        description="创建人"
    )

    class Meta:
        table = "scheduled_task"
        table_description = "定时/CI触发执行任务"


class WebhookConfig(Model):
    """Webhook 通知配置"""
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=200, description="通知名称")
    webhook_url = fields.TextField(description="Webhook URL")
    webhook_type = fields.CharField(max_length=20, default='feishu', description="通知类型 feishu/dingtalk/custom")
    trigger_on = fields.CharField(max_length=30, default='always', description="触发条件 always/on_failure/on_success")
    is_active = fields.BooleanField(default=True, description="是否启用")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='webhook_configs',
        on_delete=fields.CASCADE,
        description="所属项目"
    )

    class Meta:
        table = "webhook_config"
        table_description = "Webhook通知配置"

