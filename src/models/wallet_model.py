"""
货币表
@Author: ht
@Date: 2024-07-26
@description: 钱包记录
"""
from tortoise import fields
from tortoise.models import Model


class WalletTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 用户唯一标识
    uid = fields.ForeignKeyField("default.UserTable", related_name="wallet", on_delete=fields.CASCADE)
    # 钱包类型 1: 金币 2: 积分 3: 喵币
    type = fields.IntField(default=1)
    # 金额
    amount = fields.IntField(default=0)

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "wallet_table"
        table_description = "钱包表"  # 可选
