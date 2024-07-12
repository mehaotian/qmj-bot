from datetime import date, timedelta
from tortoise import fields
from tortoise.models import Model

# from nonebot.log import logger
from src.utils import download_image


class UserTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 用户 ID ，使用str ，int容易超过范围
    user_id = fields.CharField(max_length=255, default="")
    # 群组 ID ，使用str ，int容易超过范围
    group_id = fields.CharField(max_length=255, default="")
    # 登录密钥
    login_key = fields.CharField(max_length=255, default="")
    # 昵称
    nickname = fields.CharField(max_length=255, default="")
    # 头像
    avatar = fields.CharField(max_length=255, default="")
    # 魅力值
    charm = fields.IntField(default=0)
    # 金币
    gold = fields.IntField(default=0)
    # 累计登录次数
    sign_count = fields.IntField(default=0)

    # 连续登录天数
    days_count = fields.IntField(default=0)
    # 背景图地址
    bg_img = fields.CharField(max_length=255, default="")
    # 登录时间
    sign_at = fields.IntField(default=0)
    # 最后登录时间
    last_sign = fields.DateField(default=date(2000, 1, 1))

    class Meta:
        table = "user_table"
        table_description = "用户表"  # 可选
