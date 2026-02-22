"""
项目模块数据库模型
"""
from tortoise.models import Model
from tortoise import fields


class Project(Model):
    """项目表"""
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=100, unique=True, description="项目名称")
    description = fields.TextField(null=True, description="项目描述")
    owner_id = fields.IntField(description="项目负责人ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "project"
        table_description = "项目表"


class ProjectMember(Model):
    """项目成员表"""
    id = fields.IntField(pk=True, description="主键ID")
    project_id = fields.IntField(description="所属项目ID")
    user_id = fields.IntField(description="用户ID")
    role = fields.SmallIntField(default=1, description="成员角色（0=viewer, 1=editor, 2=owner）")
    status = fields.SmallIntField(default=1, description="成员状态（0=禁用, 1=启用）")
    granted_by = fields.IntField(null=True, description="授权人ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="加入时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "project_member"
        table_description = "项目成员表"


class ProjectModule(Model):
    """项目模块表（业务线）- 支持二级层级"""
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=100, description="模块/业务线名称")
    description = fields.TextField(null=True, description="描述")
    project_id = fields.IntField(description="所属项目ID")
    parent_id = fields.IntField(null=True, description="父级ID，null=一级业务线")
    sort_order = fields.IntField(default=0, description="排序序号")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "project_module"
        table_description = "项目模块/业务线表"


class BusinessLineMember(Model):
    """业务线成员表 - 关联用户到业务线，含角色"""
    id = fields.IntField(pk=True, description="主键ID")
    module_id = fields.IntField(description="业务线（一级模块）ID")
    user_id = fields.IntField(description="用户ID")
    role = fields.CharField(
        max_length=20, default='member',
        description="角色（admin=管理员, lead=组长, member=测试人员）"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="分配时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "business_line_member"
        table_description = "业务线成员表"
        unique_together = (("module_id", "user_id"),)
