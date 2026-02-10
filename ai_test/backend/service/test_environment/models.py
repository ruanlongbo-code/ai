"""
测试环境模块数据库模型
"""
from tortoise.models import Model
from tortoise import fields
import os


def get_default_func_global():
    """获取默认的全局函数内容"""
    file_path = r"G:\AI\上课代码\AI2502\AgentTest\api_case_run\global_tools.py"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        # 如果文件读取失败，返回空字符串
        return ""


class TestEnvironment(Model):
    """测试环境表"""
    id = fields.IntField(pk=True, description="主键ID")
    project = fields.ForeignKeyField(
        'models.Project',
        related_name='test_environments',
        on_delete=fields.CASCADE,
        description="关联项目"
    )
    name = fields.CharField(max_length=100, description="环境名称")
    func_global = fields.TextField(null=True, default=get_default_func_global, description="全局函数")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "test_environment"
        table_description = "测试环境表"
        unique_together = (("project", "name"),)


class TestEnvironmentConfig(Model):
    """测试环境配置表"""
    id = fields.IntField(pk=True, description="主键ID")
    environment = fields.ForeignKeyField(
        'models.TestEnvironment',
        related_name='configs',
        on_delete=fields.CASCADE,
        description="关联环境"
    )
    name = fields.CharField(max_length=100, description="配置名称")
    value = fields.CharField(max_length=500, description="配置值")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "test_environment_config"
        table_description = "测试环境配置表"
        unique_together = (("environment", "name"),)


class TestEnvironmentDb(Model):
    """测试环境数据库表"""
    id = fields.IntField(pk=True, description="主键ID")
    environment = fields.ForeignKeyField(
        'models.TestEnvironment',
        related_name='databases',
        on_delete=fields.CASCADE,
        description="关联环境"
    )
    name = fields.CharField(max_length=100, description="数据库名称")
    type = fields.CharField(max_length=50, description="数据库类型")
    config = fields.JSONField(description="数据库配置")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "test_environment_db"
        table_description = "测试环境数据库表"
        unique_together = (("environment", "name"),)