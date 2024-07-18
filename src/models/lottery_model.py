import uuid
from datetime import date, timedelta
from tortoise import fields
from tortoise.models import Model

# from nonebot.log import logger
from src.utils import download_image


class LotteryTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 发布用户
    uid = fields.IntField(default=0)
    # 抽奖名称
    name = fields.CharField(max_length=255, default="")
    # 抽奖分数
    score = fields.IntField(default=0)
    # 开奖类型 1: 按人数开奖 2: 按时间开奖
    type = fields.IntField(default=1)
    # 开奖时间 ，如果type 为1 ,未满足时按开奖时间
    open_time = fields.DatetimeField(null=True)
    # 开奖人数
    open_num = fields.IntField(default=0)

    # 抽奖状态 1: 进行中 2:已结束
    status = fields.IntField(default=1)

    # 抽奖图片
    img = fields.CharField(max_length=255, default="")
    # 抽奖描述
    desc = fields.TextField(default="")



    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "lottery_table"
        table_description = "抽奖表"  # 可选
