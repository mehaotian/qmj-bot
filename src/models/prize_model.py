"""
抽奖表
@Author: ht
@Date: 2024-07-26
@description: 奖品表
"""
from tortoise import fields
from tortoise.models import Model

from src.models.user_model import UserTable


class PrizeTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 抽奖id
    lottery = fields.ForeignKeyField("default.LotteryTable", related_name="join_users", on_delete=fields.CASCADE)
    # 抽奖类型 1 通用抽奖 2 盲盒抽奖
    type = fields.IntField(default=1)
    # 奖品类型 1: 奖品 2: 金币 3: 喵币 4: 兑换券(签到券,抽奖券) 5: 兑换码
    prize_type = fields.IntField(default=1)
    # 奖品名称
    name = fields.CharField(max_length=255, default="")
    # 奖品图片 ,只有盲盒抽奖才会上传图片
    img_url = fields.CharField(max_length=255, default="")
    # 奖品份数 ,最低1份
    prize_count = fields.IntField(default=1)
    # 奖品概率 ,最小 0.01 最大 100 ,总概率不能超过100 (只有盲盒抽奖才有)
    prize_rate = fields.IntField(default=0)
    # 中奖id
    win_id = fields.IntField(default=0)

    # 状态 1: 已完成 2: 待开奖 3: 待核销
    status = fields.IntField(default=1)

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "prize_table"
        table_description = "奖品列表"  # 可选

    @classmethod
    async def create_prize(cls, data: dict):
        """
        创建奖品
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

            items = await cls.all().prefetch_related("user").limit(limit).offset((page - 1) * limit)
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
                item_dict['user'] = user_dict
                result.append(item_dict)

            print(result)

            return {"total": total_count, "items": result}
        except Exception as e:
            print(e)
            return {"total": 0, "items": []}


