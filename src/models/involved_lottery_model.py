"""
抽奖表
@Author: ht
@Date: 2024-07-26
@description: 抽奖表
"""
from typing import List, Any

from tortoise import fields
from tortoise.models import Model

from src.models import MemcacheClient
from src.models.user_model import UserTable


class InvolvedLotteryTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 抽奖id
    lottery = fields.ForeignKeyField("default.LotteryTable", related_name="join_users", on_delete=fields.CASCADE)
    # 参与者 id
    user = fields.ForeignKeyField("default.UserTable", related_name="join_users", on_delete=fields.CASCADE)
    # 状态 1: 参与 2: 中奖 3: 未中奖
    status = fields.IntField(default=1)

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
                user = users.get(item.user_id, {})
                user_dict = {
                    "id": user.id,
                    "nickname": user.nickname,

                    "avatar": user.avatar,
                }
                item_dict['user'] = user_dict
                result.append(item_dict)

            print(result)

            return {"total": total_count, "items": result}
        except Exception as e:
            print(e)
            return {"total": 0, "items": []}
