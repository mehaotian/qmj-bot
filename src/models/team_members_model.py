"""
抽奖表
@Author: ht
@Date: 2024-10-12
@description: 加入组队
"""
from datetime import datetime
from typing import List, Any

from tortoise import fields
from tortoise.models import Model
from src.models.user_model import UserTable


class TeamMembersTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 队伍ID
    team = fields.ForeignKeyField("default.TeamTable", related_name="team", on_delete=fields.CASCADE)
    # 加入者ID
    user = fields.ForeignKeyField("default.UserTable", related_name="team_user", on_delete=fields.CASCADE)
    # 状态 1: 加入 2: 离开
    status = fields.IntField(default=1)

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "team_members_table"
        table_description = "参与组队"  # 可选

    @classmethod
    async def user_join(cls, data: dict):
        """
        创建抽奖
        """
        joinuser = cls(**data)
        await joinuser.save()
        return joinuser

    @classmethod
    async def check_join(cls, team_id: int, user_id: int):
        """
        检查用户是否参与组队
        """
        return await cls.get_or_none(team_id=team_id, user_id=user_id)

    @classmethod
    async def get_list(cls, team_id: int):
        """
        获取参与组队列表
        @param team_id 组队ID
        """
        try:
            total_count = await cls.filter(team_id=team_id).count()

            items = await cls.filter(team_id=team_id).order_by('-create_time')

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
                    "avatar": user.avatar,
                }
                item_dict['user'] = user_dict
                result.append(item_dict)
            return {"total": total_count, "items": result}
        except Exception as e:
            print(e)
            return {"total": 0, "items": []}

    @classmethod
    async def get_join_count(cls, team_id: int):
        """
        获取参与抽奖人数
        """

        return await cls.filter(team_id=team_id,status=1).count()
