"""
用户表
@Author: ht
@Date: 2024-07-26
@description: 用户表
"""
import uuid
from datetime import date, timedelta, datetime
from typing import Dict, Any, List

from tortoise import fields
from tortoise.models import Model

# from nonebot.log import logger
from src.utils import download_image


class UserTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 用户唯一标识
    openid = fields.CharField(max_length=255, default="")
    # 用户 ID ，使用str ，int容易超过范围
    qq_id = fields.CharField(max_length=255, default="")
    # 群组 ID ，使用str ，int容易超过范围
    group_id = fields.CharField(max_length=255, default="")
    # 昵称
    nickname = fields.CharField(max_length=255, default="")
    # 头像
    avatar = fields.CharField(max_length=255, default="")

    # 中奖权重
    weight = fields.IntField(default=100)

    # 最后登录时间
    last_sign = fields.DateField(default=date(2000, 1, 1))

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_table"
        table_description = "用户表"  # 可选

    @classmethod
    async def create_user(cls, openid: str):
        """
        创建用户
        """
        user = cls(openid=openid)
        await user.save()
        return user

    @classmethod
    async def check_user(cls, openid: str):
        """
        检查用户
        """
        return await cls.get_or_none(openid=openid)

    @classmethod
    async def update_openid(cls, user_id: str,openid: str):
        """
        更新用户 token ，并返回用户
        """
        user = await cls.filter(id=user_id).first()
        user.openid = openid
        await user.save(update_fields=["openid"])
        return user

    @classmethod
    async def update_user(cls, user_id:str='',openid: str='', **kwargs):
        """
        更新用户信息
        """
        user = await cls.get(id=user_id)

        print('----- 更新用户信息', user, kwargs)
        update_fields = []
        for key, value in kwargs.items():
            setattr(user, key, value)
            update_fields.append(key)

        # 如果存在openid 则更新
        if openid:
            user.openid = openid
            update_fields.append('openid')
        await user.save(update_fields=update_fields)

        # 获取用户信息，不返回token 和 openid ,讲时间转为 2024-01-01 12:11:12 格式
        user = await cls.get(id=user_id)
        if user:
            user_dict = {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
            user_dict.pop('openid')
            user_dict['create_time'] = user_dict['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            user_dict['update_time'] = user_dict['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            return user_dict
        return {}

    @classmethod
    async def get_users_by_ids(cls, user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        获取用户 ids
        @param user_ids:
        @return:
        """
        users = await cls.filter(id__in=user_ids)
        return {user.id: user for user in users}

    @classmethod
    async def set_user_weight(cls, user_id: int, weight: int):
        """
        设置用户权重
        """
        user = await cls.get(id=user_id)

        user.weight = weight
        if weight < 10:
            user.weight = 10

        await user.save(update_fields=["weight"])
        return user

    @classmethod
    async def edit_user_weight(cls,  user_id: int, weight: int):
        """
        修改用户权重
        """
        current_time = datetime.now()
        print('----- 修改用户权重', user_id, weight)
        # 修改中奖者状态
        await cls.filter(id=user_id).update(weight=weight, update_time=current_time)

        return True