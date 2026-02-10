"""
功能测试模块数据库模型
"""
from tortoise.models import Model
from tortoise import fields


class RequirementDoc(Model):
    """需求表"""
    id = fields.IntField(pk=True, description="主键ID")
    title = fields.CharField(max_length=255, description="需求标题")
    doc_no = fields.CharField(max_length=100, null=True, description="需求编号")
    description = fields.TextField(null=True, description="需求详细描述（Markdown/富文本）")
    priority = fields.SmallIntField(default=3, description="优先级（1=紧急, 2=高, 3=中, 4=低）")
    status = fields.CharField(max_length=20,
                              description="状态（draft=草稿, reviewing=已确认, approved=待完善, rejected=完成, changed=废弃）")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    # 外键关联
    module = fields.ForeignKeyField(
        'models.ProjectModule',
        related_name='requirements',
        null=True,
        on_delete=fields.SET_NULL,
        description="关联项目模块"
    )
    creator = fields.ForeignKeyField(
        'models.User',
        related_name='created_requirements',
        on_delete=fields.CASCADE,
        description="创建人"
    )

    class Meta:
        table = "requirement_doc"
        table_description = "需求表"


class FunctionalCase(Model):
    """功能用例表"""
    id = fields.IntField(pk=True, description="用例ID")
    case_no = fields.CharField(max_length=100, null=True, description="用例编号")
    case_name = fields.CharField(max_length=255, description="用例名称")
    priority = fields.SmallIntField(default=3, description="优先级（1=P0, 2=P1, 3=P2, 4=P3）")
    status = fields.CharField(
        max_length=20,
        description="当前状态（design=待审核, pass=审核通过,wait=待执行， smoke=执行通过, regression=执行失败, obsolete=已废弃）"
    )
    preconditions = fields.TextField(null=True, description="前置步骤")
    test_steps = fields.JSONField(null=True, description="测试步骤列表")
    test_data = fields.JSONField(null=True, description="输入数据")
    expected_result = fields.TextField(null=True, description="预期结果")
    actual_result = fields.TextField(null=True, description="实际结果")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    # 外键关联
    requirement = fields.ForeignKeyField(
        'models.RequirementDoc',
        related_name='functional_cases',
        null=True,
        on_delete=fields.SET_NULL,
        description="关联需求"
    )
    creator = fields.ForeignKeyField(
        'models.User',
        related_name='created_functional_cases',
        on_delete=fields.CASCADE,
        description="创建人"
    )

    class Meta:
        table = "functional_case"
        table_description = "功能用例表"
