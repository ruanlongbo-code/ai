"""
测试管理模块数据库模型
"""
from tortoise.models import Model
from tortoise import fields


class TestTask(Model):
    """测试任务表"""
    id = fields.IntField(pk=True, description="主键ID")
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='test_tasks',
        on_delete=fields.CASCADE,
        description="项目ID（外键关联项目的id）"
    )
    task_name = fields.CharField(max_length=255, description="任务名称")
    description = fields.TextField(null=True, description="任务描述")
    type = fields.CharField(
        max_length=20,
        choices=[('api', 'API'), ('ui', 'UI'), ('functional', 'Functional')],
        description="任务类型（接口 / UI / 功能）"
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
        description="任务状态"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "test_task"
        table_description = "测试任务表"


class TestSuite(Model):
    """测试套件表"""
    id = fields.IntField(pk=True, description="主键ID")
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='test_suites',
        on_delete=fields.CASCADE,
        description="项目ID（外键关联项目的id）"
    )
    suite_name = fields.CharField(max_length=255, description="套件名称")
    description = fields.TextField(null=True, description="套件描述")
    type = fields.CharField(
        max_length=10,
        choices=[('api', 'API'), ('ui', 'UI')],
        description="套件类型（接口 / UI）"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "test_suite"
        table_description = "测试套件表"


class SuiteCaseRelation(Model):
    """套件-用例关系表"""
    id = fields.IntField(pk=True, description="主键ID")
    suite = fields.ForeignKeyField(
        'models.TestSuite',
        related_name='case_relations',
        on_delete=fields.CASCADE,
        description="外键 → test_suite.id"
    )
    case = fields.ForeignKeyField(
        'models.ApiTestCase',
        related_name='suite_relations',
        on_delete=fields.CASCADE,
        description="外键 → api_case.id"
    )
    case_order = fields.IntField(description="用例执行顺序")

    class Meta:
        table = "suite_case_relation"
        table_description = "套件-用例关系表"


class TaskSuiteRelation(Model):
    """任务-套件关系表"""
    id = fields.IntField(pk=True, description="主键ID")
    task = fields.ForeignKeyField(
        'models.TestTask',
        related_name='suite_relations',
        on_delete=fields.CASCADE,
        description="外键 → test_task.id"
    )
    suite = fields.ForeignKeyField(
        'models.TestSuite',
        related_name='task_relations',
        on_delete=fields.CASCADE,
        description="外键 → test_suite.id"
    )
    suite_order = fields.IntField(description="套件执行顺序")

    class Meta:
        table = "task_suite_relation"
        table_description = "任务-套件关系表"
