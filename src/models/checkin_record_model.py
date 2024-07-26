"""
签到记录表
"""
from tortoise import fields
from tortoise.models import Model


class CheckInsTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 用户唯一标识
    uid = fields.ForeignKeyField("default.UserTable", related_name="checkin_record", on_delete=fields.CASCADE)
    # 实际签到日期
    sign_date = fields.DateField(null=True)
    # 是否补签 默认为 False
    is_make_up = fields.BooleanField(default=False)
    # 签到奖励
    reward = fields.IntField(default=0)
    # 签到状态 1: 正常 2: 失败
    status = fields.IntField(default=1)
    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "checkins_table"
        table_description = "签到表"
