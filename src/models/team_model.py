"""
抽奖表
@Author: ht
@Date: 2024-07-26
@description: 组队模型，用于管理和操作组队相关数据
"""
from tortoise import fields
from tortoise.models import Model
from typing import Dict, List, Optional
from datetime import datetime

from src.models.user_model import UserTable
from nonebot import get_driver, logger

config = get_driver().config
imgurl = config.imgurl


class TeamTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 发布用户
    user = fields.ForeignKeyField("default.UserTable", related_name="teamUser", on_delete=fields.CASCADE)
    # 组队名称
    name = fields.CharField(max_length=255, default="")
    # 当前队伍人数
    current_num = fields.IntField(default=1)
    # 需要等位多少人
    need_num = fields.IntField(default=1)
    # 组队时限 1: 短期 2: 长期
    time_limit = fields.IntField(default=1)
    # 组队性质  1: 游戏 2: 团建  3: 活动
    nature = fields.IntField(default=1)
    # 组队要求 []
    team_info = fields.JSONField(default=[])

    # 开始时间
    start_time = fields.DatetimeField(null=True)
    # 结束时间 为空则为长期
    end_time = fields.DatetimeField(null=True)

    # 组队描述
    desc = fields.CharField(max_length=255, default="")
    # 描述图片 例子 ['lottery/1.jpg', 'https://lottery/2.jpg']
    desc_img = fields.JSONField(default=[])
    # 组队状态 1: 进行中 2:已结束
    status = fields.IntField(default=1)

    # 创建时间
    create_time = fields.DatetimeField(auto_now_add=True)
    # 更新时间
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "team_table"
        table_description = "组队表"

    @staticmethod
    def format_datetime(dt: Optional[datetime]) -> Optional[str]:
        """
        格式化日期时间

        @param dt: 日期时间对象
        @return: 格式化后的字符串，如果输入为None则返回None
        """
        return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None

    @classmethod
    async def check_team(cls, team_id: str = ''):
        """
        检查组队是否存在
        @return:
        """
        return await cls.get_or_none(id=team_id)

    @classmethod
    async def create_team(cls, data: Dict) -> "TeamTable":
        """
        创建新的组队记录

        @param data: 包含组队信息的字典
        @return: 创建的抽奖对象
        @raises ValueError: 如果提供的数据无效
        """
        try:
            team = cls(**data)
            await team.save()
            return team
        except Exception as e:
            logger.error(f"创建组队失败: {str(e)}")
            raise ValueError("创建组队失败，请检查提供的数据")

    @classmethod
    async def get_team_list(cls, page: int = 1, limit: int = 10, status: Optional[int] = None,
                            user_id: Optional[int] = None) -> Dict[str, any]:
        """
        获取组队列表
        @param page:
        @param limit:
        @param status:
        @param user_id:
        @return: 包含总数和组队列表的字典
        """
        try:
            query = cls.all().prefetch_related('user')
            if status is not None:
                if status in [1, 2]:
                    query = query.filter(status=status)
                else:
                    logger.warning(f"无效的状态值: {status}，将返回空列表")
                    return {"total": 0, "items": []}

            # 查询自己发布的组队
            if user_id is not None:
                query = query.filter(user_id=user_id)

            # 获取列表总数
            total_count = await query.count()

            items = await query.order_by('-create_time').limit(limit).offset((page - 1) * limit)

            result = []
            for item in items:
                """
                将发布者详细信息插入到组队信息中
                """
                item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
                # 获取关联用户
                user = item.user
                item_dict['user'] = {
                    "id": user.id if user else None,
                    "nickname": user.nickname if user else None,
                    "avatar": user.avatar if user else None,
                }

                # 格式化时间
                item_dict['start_time'] = cls.format_datetime(item.start_time)
                item_dict['end_time'] = cls.format_datetime(item.end_time)
                item_dict['create_time'] = cls.format_datetime(item.create_time)
                item_dict['update_time'] = cls.format_datetime(item.update_time)

                result.append(item_dict)

            return {"total": total_count, "items": result}

        except Exception as e:
            logger.error(f"获取组队列表失败: {str(e)}")
            return {"total": 0, "items": []}

    @classmethod
    async def get_detail(cls, team_id: int) -> Optional[Dict[str, any]]:
        """
        获取组队详情
        @param team_id: 抽奖 ID
        @return: 包含抽奖详细信息的字典，如果不存在则返回None
        """
        try:
            team_data = await cls.get_or_none(id=team_id).prefetch_related('user')
            if not team_data:
                return None
            user = team_data.user
            if not user:
                logger.warning(f"组队 {team_id} 的用户 {team_data.user_id} 不存在")
                return None

            team_dict = {k: v for k, v in team_data.__dict__.items() if not k.startswith('_')}

            # 格式化时间
            team_dict['start_time'] = cls.format_datetime(team_data.start_time)
            team_dict['end_time'] = cls.format_datetime(team_data.end_time)
            team_dict['create_time'] = cls.format_datetime(team_data.create_time)
            team_dict['update_time'] = cls.format_datetime(team_data.update_time)

            team_dict['user'] = {
                "id": user.id,
                "nickname": user.nickname,
                "avatar": user.avatar,
            }

            return team_dict

        except Exception as e:
            logger.error(f"获取抽奖详情失败: {str(e)}")
            return None
