"""
抽奖表
@Author: ht
@Date: 2024-07-26
@description: 抽奖表
"""
from datetime import datetime
from typing import List, Any

from tortoise import fields
from tortoise.models import Model

from src.models import MemcacheClient
from src.models.lottery_model import LotteryTable
from src.models.user_model import UserTable


class InvolvedLotteryTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 抽奖id
    lottery = fields.ForeignKeyField("default.LotteryTable", related_name="lottery_user", on_delete=fields.CASCADE)
    # 参与者 id
    user = fields.ForeignKeyField("default.UserTable", related_name="join_users", on_delete=fields.CASCADE)
    # 状态 1: 参与 2: 中奖 3: 未中奖
    status = fields.IntField(default=1)
    # 中奖 id
    win_id = fields.IntField(default=0)

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "involved_lottery_table"
        table_description = "参与抽奖"  # 可选

    @classmethod
    async def user_join(cls, data: dict):
        """
        创建抽奖
        """
        joinuser = cls(**data)
        await joinuser.save()
        return joinuser

    @classmethod
    async def check_join(cls, lottery_id: int, user_id: int):
        """
        检查用户是否参与抽奖
        """
        return await cls.get_or_none(lottery_id=lottery_id, user_id=user_id)

    @classmethod
    async def get_list(cls, lottery_id: int):
        """
        获取参与抽奖列表
        """
        try:
            total_count = await cls.filter(lottery_id=lottery_id).count()

            items = await cls.filter(lottery_id=lottery_id).order_by('-create_time')

            user_ids: list[Any] = [item.user_id for item in items]

            users: dict[int, dict[str, Any]] = await UserTable.get_users_by_ids(user_ids)

            result = []
            for item in items:
                item_dict = {k: v for k, v in item.__dict__.items()
                             if not k.startswith('_')}
                item_dict['create_time'] = item_dict['create_time'].strftime('%Y-%m-%d %H:%M:%S')
                item_dict['update_time'] = item_dict['update_time'].strftime('%Y-%m-%d %H:%M:%S')

                user = users.get(item.user_id, {})
                user_dict = {
                    "id": user.id,
                    "nickname": user.nickname,
                    "weight": user.weight,
                    "avatar": user.avatar,
                }
                item_dict['user'] = user_dict
                result.append(item_dict)
            return {"total": total_count, "items": result}
        except Exception as e:
            print(e)
            return {"total": 0, "items": []}

    @classmethod
    async def edit_winner_status(cls, lottery_id: int, winner_ids: int, prize_id: int):
        """
        编辑中奖状态
        """
        current_time = datetime.now()

        # 修改中奖者状态
        await cls.filter(lottery_id=lottery_id, user_id__in=winner_ids).update(status=2, win_id=prize_id,
                                                                               update_time=current_time)
        # # 修改未中奖者状态
        # await cls.filter(lottery_id=lottery_id).exclude(user_id__in=winner_ids).update(status=3,
        #                                                                                update_time=current_time)

        return True

    @classmethod
    async def edit_losers_status(cls, lottery_id: int):
        """
        修改未中奖者状态
        @param lottery_id:
        @return:
        """
        current_time = datetime.now()
        # 修改 status 为 1，都变成3
        await cls.filter(lottery_id=lottery_id, status=1).update(status=3, update_time=current_time)
        return True

    @classmethod
    async def get_winners_list(cls, lottery_id: int):
        """
        获取抽奖中奖者
        """
        items = await cls.filter(lottery_id=lottery_id, status=2)
        user_ids = [item.user_id for item in items]
        users = await UserTable.get_users_by_ids(user_ids)

        # 获取当前抽奖详情
        lottery = await LotteryTable.get_or_none(id=lottery_id)

        result = []
        for item in items:
            item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
            item_dict['create_time'] = item_dict['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            item_dict['update_time'] = item_dict['update_time'].strftime('%Y-%m-%d %H:%M:%S')

            user = users.get(item.user_id, {})
            item_dict['lottery_name'] = lottery.name

            user_dict = {
                "id": user.id,
                "nickname": user.nickname,
                "avatar": user.avatar,
            }
            item_dict['user'] = user_dict
            result.append(item_dict)

        return result
