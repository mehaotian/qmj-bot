"""
抽奖表
@Author: ht
@Date: 2024-07-26
@description: 奖品表
"""
from datetime import datetime

from tortoise import fields
from tortoise.models import Model

from src.models.user_model import UserTable
from nonebot import get_driver

config = get_driver().config
imgurl = config.imgurl


class WriteOffTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 抽奖id
    lottery = fields.ForeignKeyField("default.LotteryTable", related_name="lottery_users", on_delete=fields.CASCADE)
    # 奖品 id
    prize = fields.ForeignKeyField("default.PrizeTable", related_name="prize_user", on_delete=fields.CASCADE)
    # 中奖用户id
    user = fields.ForeignKeyField("default.UserTable", related_name="win_users", on_delete=fields.CASCADE)
    # 核销信息
    write_off_info = fields.JSONField(default={})
    # 状态 1: 已完成 2: 待核销
    status = fields.IntField(default=2)

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "write_off_table"
        table_description = "奖品核销表"  # 可选

    @classmethod
    async def create_write_of(cls, data: dict):
        """
        创建奖品
        """
        lottery = cls(**data)
        await lottery.save()
        return lottery

    @classmethod
    async def get_user_list(cls, lottery_id: int):
        """
        获取核销名单
        @param lottery_id:
        @return:
        """
        results = await cls.filter(lottery_id=lottery_id).select_related('user', 'prize', 'lottery').all()
        grouped_data = []
        prize_dict = {}

        for result in results:
            prize_id = result.prize.id

            if prize_id not in prize_dict:

                prize_img = ""

                if result.prize.img_url:
                    prize_img = config.imgurl + "/" + result.prize.img_url

                prize_info = {
                    "prize_id": prize_id,
                    "prize_name": result.prize.name,
                    "prize_img": prize_img,
                    "users": []
                }
                prize_dict[prize_id] = prize_info
                grouped_data.append(prize_info)

            user_info = {
                "id": result.id,
                "user_id": result.user.id,
                "nickname": result.user.nickname,
                "status": result.status,
                "avatar": result.user.avatar,
                # "write_off_info": result.write_off_info,
                "create_time": result.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                "update_time": result.update_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            prize_dict[prize_id]["users"].append(user_info)

        return grouped_data

    @classmethod
    async def get_write_off_list(cls, lottery_id: int):
        """
        获取核销列表
        """
        try:

            results = await cls.filter(lottery_id=lottery_id).select_related('user', 'prize', 'lottery').all()

            result = []
            for item in results:
                item_dict = {
                    "id": item.id,
                    "prize_id": item.prize.id,
                    "prize_name": item.prize.name,
                    "prize_img": config.imgurl + "/" + item.prize.img_url,
                    "user_id": item.user.id,
                    "nickname": item.user.nickname,
                    "avatar": item.user.avatar,
                    "status": item.status,
                    "write_off_info": item.write_off_info,
                    "create_time": item.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "update_time": item.update_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                result.append(item_dict)

            return result

        except Exception as e:
            print(e)
            return []

    @classmethod
    async def edit_write_off_status(cls, write_off_id: int,status: int):
        """
        编辑核销状态
        @param write_off_id: 核销id
        @param status: 状态
        """
        # 是否存在
        current_time = datetime.now()
        return await cls.filter(id=write_off_id).update(status=status, update_time=current_time)

    @classmethod
    async def add_write_off_info(cls, write_off_id: int, write_off_info: dict):
        """
        添加核销信息
        @param write_off_id: 核销id
        @param write_off_info: 核销信息
        """
        # 是否存在
        return await cls.filter(id=write_off_id).update(write_off_info=write_off_info)