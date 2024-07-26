"""
签到表
"""
from tortoise import fields
from tortoise.models import Model


class CheckInsTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 用户唯一标识
    uid = fields.ForeignKeyField("default.UserTable", related_name="checkins", on_delete=fields.CASCADE)
    # 累计签到次数
    total_count = fields.IntField(default=0)
    # 连续签到次数
    continuous_count = fields.IntField(default=0)
    # 最后签到时间
    last_sign = fields.DateField(null=True)
    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "checkins_table"
        table_description = "签到表"
