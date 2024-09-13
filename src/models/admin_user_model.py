"""
用户表
@Author: ht
@Date: 2024-07-26
@description: 管理员用户表
"""

from typing import Dict, Any, List

from nonebot import logger
from tortoise import fields
from tortoise.models import Model


class AdminUserTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 用户名
    username = fields.CharField(max_length=50, null=True)
    # 密码
    password = fields.CharField(max_length=255, null=True)
    # 权限 []
    roles = fields.JSONField(null=True)
    # 真实姓名
    realName = fields.CharField(max_length=50, null=True)
    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "admin_user_table"
        table_description = "管理员用户表"  # 可选

    @classmethod
    async def create_user(cls, data: Dict) -> "AdminUserTable":
        """
        创建管理员用户
        @param data: 包含用户信息的字典
        @return: 创建的用户对象
        @raises ValueError: 如果提供的数据无效
        """
        try:
            user = cls(**data)
            await user.save()
            return user
        except Exception as e:
            logger.error(f"创建管理员用户失败: {str(e)}")
            raise ValueError("创建管理员用户，请检查提供的数据")

    @classmethod
    async def check_user(cls, username: str) -> bool:
        """
        检查用户是否存在
        @param username: 用户名
        @return: 用户是否存在
        """
        user = await cls.filter(username=username).first()
        return user is not None

    @classmethod
    async def get_user(cls, user_id: int) -> "AdminUserTable":
        """
        获取用户
        @param username: 用户名
        @return: 用户对象
        """
        user = await cls.get_or_none(id=user_id)

        userinfo = {
            'userId': user.id,
            'username': user.username,
            'roles': user.roles,
            'realName': user.realName
        }

        return userinfo
