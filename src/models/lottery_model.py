"""
抽奖表
@Author: ht
@Date: 2024-07-26
@description: 抽奖表
"""
from tortoise import fields
from tortoise.models import Model

from src.models import MemcacheClient
from src.models.user_model import UserTable
from nonebot import get_driver

config = get_driver().config
imgurl = config.imgurl


class LotteryTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 发布用户
    user = fields.ForeignKeyField("default.UserTable", related_name="lottery", on_delete=fields.CASCADE)
    # 抽奖类型 1: 普通抽奖 2: 兑换码
    lottery_type = fields.IntField(default=1)
    # 抽奖名称
    name = fields.CharField(max_length=255, default="")
    # 抽奖份数
    num = fields.IntField(default=1)
    # 开奖类型 1: 按人数开奖 2: 按时间开奖
    open_type = fields.IntField(default=1)
    # 开奖时间 ，如果type 为 1 , 未满足时按开奖时间
    open_time = fields.DatetimeField(null=True)
    # 开奖人数
    open_num = fields.IntField(default=0)
    # 抽奖状态 1: 进行中 2:已结束
    status = fields.IntField(default=1)
    # 抽奖图片
    img_url = fields.CharField(max_length=255, default="")
    # 抽奖描述
    desc = fields.CharField(max_length=255, default="")
    # 描述图片 例子 ['lottery/1.jpg', 'https://lottery/2.jpg']
    desc_img = fields.JSONField(default=[])
    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "lottery_table"
        table_description = "抽奖表"  # 可选

    @classmethod
    async def create_lottery(cls, data: dict):
        """
        创建抽奖
        """
        lottery = cls(**data)
        await lottery.save()
        return lottery

    @classmethod
    async def check_lottery(cls, lottery_id: int):
        """
        检查抽奖
        """
        return await cls.get_or_none(id=lottery_id)

    @classmethod
    async def get_list(cls, page: int = 1, limit: int = 10):
        """
        获取抽奖列表
        @param page: 页码
        @param limit: 每页数量
        @retur 抽奖列表
        """

        try:
            total_count = await cls.all().count()

            items = await cls.all().order_by('-create_time').limit(limit).offset((page - 1) * limit)
            user_ids = [item.user_id for item in items]
            users = await UserTable.get_users_by_ids(user_ids)

            result = []
            for item in items:
                item_dict = {k: v for k, v in item.__dict__.items()
                             if not k.startswith('_')}
                user = users.get(item.user_id, {})
                user_dict = {
                    "id": user.id,
                    "nickname": user.nickname,
                    "avatar": user.avatar,
                }

                # 获取时间
                item_dict['create_time'] = item_dict['create_time'].strftime('%Y-%m-%d %H:%M:%S')
                # 获取开奖时间
                item_dict['open_time'] = item_dict['open_time'].strftime('%Y-%m-%d %H:%M:%S')
                # 获取最后更新时间
                item_dict['update_time'] = item_dict['update_time'].strftime('%Y-%m-%d %H:%M:%S')

                # 封面图
                item_dict['img_url'] = imgurl + '/' + item_dict['img_url']
                # 描述图
                desc_img = item_dict['desc_img']
                for i in range(len(desc_img)):
                    if not desc_img[i].startswith('http'):
                        desc_img[i] = imgurl + '/' + desc_img[i]

                item_dict['user'] = user_dict
                result.append(item_dict)

            return {"total": total_count, "items": result}

        except Exception as e:
            print(e)
            return {"total": 0, "items": []}

    @classmethod
    async def get_detail(cls, lottery_id: int):
        """
        获取抽奖详情
        @param lottery_id: 抽奖 ID
        @return: 抽奖详情
        """
        lottery = await cls.get_or_none(id=lottery_id)
        user = await UserTable.get_or_none(id=lottery.user_id)

        lottery_dict = {k: v for k, v in lottery.__dict__.items() if not k.startswith('_')}
        user_dict = {
            "id": user.id,
            "nickname": user.nickname,
            "avatar": user.avatar,
        }
        lottery_dict['user'] = user_dict

        # 获取时间
        lottery_dict['create_time'] = lottery_dict['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        # 获取开奖时间
        if lottery_dict['open_time']:
            lottery_dict['open_time'] = lottery_dict['open_time'].strftime('%Y-%m-%d %H:%M:%S')

        # 获取最后更新时间
        lottery_dict['update_time'] = lottery_dict['update_time'].strftime('%Y-%m-%d %H:%M:%S')

        # 封面图
        lottery_dict['img_url'] = imgurl + '/' + lottery_dict['img_url']

        # 描述图
        desc_img = lottery_dict['desc_img']
        for i in range(len(desc_img)):
            if not desc_img[i].startswith('http'):
                desc_img[i] = imgurl + '/' + desc_img[i]

        lottery_dict['desc_img'] = desc_img

        return lottery_dict
