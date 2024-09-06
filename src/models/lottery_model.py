"""
抽奖表
@Author: ht
@Date: 2024-07-26
@description: 抽奖表模型，用于管理和操作抽奖相关数据
"""
from tortoise import fields
from tortoise.models import Model
from typing import Dict, List, Optional
from datetime import datetime

from src.models import MemcacheClient
from src.models.prize_model import PrizeTable
from src.models.user_model import UserTable
from nonebot import get_driver, logger

config = get_driver().config
imgurl = config.imgurl


class LotteryTable(Model):
    # 自增 ID (Primary key)
    id = fields.IntField(pk=True, generated=True)
    # 发布用户
    user = fields.ForeignKeyField("default.UserTable", related_name="lottery", on_delete=fields.CASCADE)
    # 抽奖类型 1: 普通抽奖 2: 兑换码
    lottery_type = fields.IntField(default=1)
    # 开奖类型 1: 按人数开奖 2: 按时间开奖
    open_type = fields.IntField(default=1)
    # 开奖时间 ，如果type 为 1 , 未满足时按开奖时间
    open_time = fields.DatetimeField(null=True)
    # 开奖人数
    open_num = fields.IntField(default=0)
    # 抽奖状态 1: 进行中 2:已结束
    status = fields.IntField(default=1)
    # 中奖信息 []
    win_info = fields.JSONField(default=[])
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
        table_description = "抽奖表"

    @classmethod
    async def create_lottery(cls, data: Dict) -> "LotteryTable":
        """
        创建新的抽奖记录
        
        @param data: 包含抽奖信息的字典
        @return: 创建的抽奖对象
        @raises ValueError: 如果提供的数据无效
        """
        try:
            lottery = cls(**data)
            await lottery.save()
            return lottery
        except Exception as e:
            logger.error(f"创建抽奖失败: {str(e)}")
            raise ValueError("创建抽奖失败，请检查提供的数据")

    @classmethod
    async def check_lottery(cls, lottery_id: int) -> Optional["LotteryTable"]:
        """
        检查指定ID的抽奖是否存在
        
        @param lottery_id: 抽奖ID
        @return: 如果存在返回抽奖对象，否则返回None
        """
        return await cls.get_or_none(id=lottery_id)

    @staticmethod
    def format_datetime(dt: Optional[datetime]) -> Optional[str]:
        """
        格式化日期时间
        
        @param dt: 日期时间对象
        @return: 格式化后的字符串，如果输入为None则返回None
        """
        return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None

    @staticmethod
    def format_image_url(img: str) -> str:
        """
        格式化图片URL
        
        @param img: 图片路径或URL
        @return: 完整的图片URL
        """
        return imgurl + '/' + img if not img.startswith('http') else img

    @classmethod
    def process_lottery_dict(cls, lottery_dict: Dict) -> Dict:
        """
        处理抽奖字典数据
        
        @param lottery_dict: 原始抽奖数据字典
        @return: 处理后的抽奖数据字典
        """
        lottery_dict['create_time'] = cls.format_datetime(lottery_dict.get('create_time'))
        lottery_dict['open_time'] = cls.format_datetime(lottery_dict.get('open_time'))
        lottery_dict['update_time'] = cls.format_datetime(lottery_dict.get('update_time'))

        desc_img = lottery_dict.get('desc_img', [])
        lottery_dict['desc_img'] = [cls.format_image_url(img) for img in desc_img]

        return lottery_dict

    @classmethod
    async def get_list(cls, page: int = 1, limit: int = 10, status: Optional[int] = None,
                       user_id: Optional[int] = None) -> Dict[str, any]:
        """
        获取抽奖列表
        
        @param page: 页码
        @param limit: 每页数量
        @param status: 状态 1: 进行中 2: 已结束，默认为None，查询全部
        @param user_id: 用户ID，默认为None，查询全部用户的抽奖
        @return: 包含总数和抽奖列表的字典
        """
        try:
            query = cls.all()
            if status is not None:
                if status in [1, 2]:
                    query = query.filter(status=status)
                else:
                    logger.warning(f"无效的状态值: {status}，将返回空列表")
                    return {"total": 0, "items": []}

            if user_id is not None:
                query = query.filter(user_id=user_id)

            total_count = await query.count()

            items = await query.order_by('-create_time').limit(limit).offset((page - 1) * limit)
            user_ids = [item.user_id for item in items]
            users = await UserTable.get_users_by_ids(user_ids)

            result = []
            for item in items:
                item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
                item_dict = cls.process_lottery_dict(item_dict)

                user = users.get(item.user_id, {})
                item_dict['user'] = {
                    "id": user.id if user else None,
                    "nickname": user.nickname if user else None,
                    "avatar": user.avatar if user else None,
                }

                item_dict['prizes'] = await PrizeTable.get_list(item.id, 2)

                result.append(item_dict)

            return {"total": total_count, "items": result}

        except Exception as e:
            logger.error(f"获取抽奖列表失败: {str(e)}")
            return {"total": 0, "items": []}

    @classmethod
    async def get_detail(cls, lottery_id: int) -> Optional[Dict[str, any]]:
        """
        获取抽奖详情
        
        @param lottery_id: 抽奖 ID
        @return: 包含抽奖详细信息的字典，如果不存在则返回None
        """
        try:
            lottery = await cls.get_or_none(id=lottery_id)
            if not lottery:
                return None

            user = await UserTable.get_or_none(id=lottery.user_id)
            if not user:
                logger.warning(f"抽奖 {lottery_id} 的用户 {lottery.user_id} 不存在")
                return None

            lottery_dict = {k: v for k, v in lottery.__dict__.items() if not k.startswith('_')}
            lottery_dict = cls.process_lottery_dict(lottery_dict)

            lottery_dict['user'] = {
                "id": user.id,
                "nickname": user.nickname,
                "avatar": user.avatar,
            }

            return lottery_dict

        except Exception as e:
            logger.error(f"获取抽奖详情失败: {str(e)}")
            return None
