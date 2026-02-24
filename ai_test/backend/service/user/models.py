"""
用户模块数据库模型
"""
from tortoise.models import Model
from tortoise import fields


class User(Model):
    """用户表"""
    id = fields.IntField(pk=True, description="主键ID")
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password = fields.CharField(max_length=255, description="密码")
    email = fields.CharField(max_length=100, unique=True, description="邮箱")
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    real_name = fields.CharField(max_length=50, null=True, description="真实姓名")
    avatar = fields.CharField(max_length=255, null=True, description="头像URL")
    feishu_user_key = fields.CharField(max_length=128, null=True, description="飞书项目UserKey")
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_superuser = fields.BooleanField(default=False, description="是否超级用户")
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "user"
        table_description = "用户表"
