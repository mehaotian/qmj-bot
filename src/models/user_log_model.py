"""
日志表
@Author: ht
@Date: 2024-07-26
@description: 用户日志模型，用于管理和操作用户日志相关数据
"""
from tortoise import fields
from tortoise.models import Model
from typing import Dict, List, Optional
from nonebot import get_driver, logger

config = get_driver().config
imgurl = config.imgurl


class UserLogModel(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 发布用户
    user = fields.ForeignKeyField("default.UserTable", related_name="teamUser", on_delete=fields.CASCADE)
    # 日志类型 1: 发布抽奖 2: 中奖 3: 创建组队 4: 加入组队
    log_type = fields.IntField(default=1)
    # 日志内容
    log_content = fields.CharField(max_length=255, default="")

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_log_table"
        table_description = "用户日志表"

    @classmethod
    async def create_log(cls, data: Dict):

        pass

