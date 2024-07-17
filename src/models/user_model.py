import uuid
from datetime import date, timedelta
from tortoise import fields
from tortoise.models import Model

# from nonebot.log import logger
from src.utils import download_image


class UserTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 用户唯一标识
    openid = fields.CharField(max_length=255, default="")
    # 用户 token
    token = fields.CharField(max_length=255, default="")
    # 用户 ID ，使用str ，int容易超过范围
    user_id = fields.CharField(max_length=255, default="")
    # 群组 ID ，使用str ，int容易超过范围
    group_id = fields.CharField(max_length=255, default="")
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
    sign_day = fields.IntField(default=0)
    # 背景图地址
    bg_img = fields.CharField(max_length=255, default="")

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
    async def create_user(cls, openid: str, token: str):
        """
        创建用户
        """
        user = cls(openid=openid, token=token)
        await user.save()
        return user

    @classmethod
    async def check_user(cls, openid: str):
        """
        检查用户
        """
        return await cls.get_or_none(openid=openid)

    @classmethod
    async def update_token(cls, openid: str, token: str):
        """
        更新用户 token ，并返回用户
        """
        user = await cls.filter(openid=openid).first()
        user.token = token
        await user.save(update_fields=["token"])
        return user

    @classmethod
    async def update_user(cls, openid: str, **kwargs):
        """
        更新用户信息
        """
        user = await cls.filter(openid=openid).first()
        update_fields = []
        for key, value in kwargs.items():
            setattr(user, key, value)
            update_fields.append(key)
        await user.save(update_fields=update_fields)

        # 获取用户信息，不返回token 和 openid ,讲时间转为 2024-01-01 12:11:12 格式
        user = await cls.filter(openid=openid).first()
        user_dict = {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
        user_dict.pop('token')
        user_dict.pop('openid')
        user_dict['create_time'] = user_dict['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        user_dict['update_time'] = user_dict['update_time'].strftime('%Y-%m-%d %H:%M:%S')
        return user_dict
