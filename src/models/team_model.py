"""
抽奖表
@Author: ht
@Date: 2024-07-26
@description: 组队模型，用于管理和操作组队相关数据
"""
from tortoise import fields
from tortoise.models import Model
from typing import Dict, List, Optional
from datetime import datetime

from src.models.user_model import UserTable
from nonebot import get_driver, logger

config = get_driver().config
imgurl = config.imgurl


class TeamTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 发布用户
    user = fields.ForeignKeyField("default.UserTable", related_name="teamUser", on_delete=fields.CASCADE)
    # 组队名称
    name = fields.CharField(max_length=255, default="")
    # 当前队伍人数
    current_num = fields.IntField(default=1)
    # 需要等位多少人
    need_num = fields.IntField(default=1)
    # 组队时限 1: 短期 2: 长期
    time_limit = fields.IntField(default=1)
    # 组队性质  1: 游戏 2: 团建  3: 活动
    nature = fields.IntField(default=1)
    # 组队要求 []
    team_info = fields.JSONField(default=[])

    # 开始时间
    start_time = fields.DatetimeField(null=True)
    # 结束时间 为空则为长期
    end_time = fields.DatetimeField(null=True)

    # 组队描述
    desc = fields.CharField(max_length=255, default="")
    # 描述图片 例子 ['lottery/1.jpg', 'https://lottery/2.jpg']
    desc_img = fields.JSONField(default=[])
    # 组队状态 1: 进行中 2:未开始 3:已结束
    status = fields.IntField(default=1)

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "team_table"
        table_description = "组队表"

    @classmethod
    async def create_team(cls, data: Dict) -> "TeamTable":
        """
        创建新的组队记录

        @param data: 包含组队信息的字典
        @return: 创建的抽奖对象
        @raises ValueError: 如果提供的数据无效
        """
        try:
            team = cls(**data)
            await team.save()
            return team
        except Exception as e:
            logger.error(f"创建组队失败: {str(e)}")
            raise ValueError("创建组队失败，请检查提供的数据")
