import httpx
from nonebot.log import logger
from fastapi import APIRouter, Header, Query
from pydantic import BaseModel
# 获取配置信息
from src.config import global_config
from typing import List
from src.models.user_model import UserTable
from src.models.lottery_model import LotteryTable
from src.models.involved_lottery_model import InvolvedLotteryTable

from ..utils.hashing import check_signature, decrypt_data

from ..utils.responses import create_response, create_page_response
from ..utils.security import get_token_data, get_user_data

from ..api import lottery

router = APIRouter()


class LotteryItem(BaseModel):
    # 发布者user_id
    user_id: int
    # 抽奖类型 1: 普通抽奖 2: 兑换码
    lottery_type: int
    # 抽奖名称
    name: str
    # 抽奖份数
    num: int
    # 开奖类型 1: 按人数开奖 2: 按时间开奖
    open_type: int
    # 开奖时间 ，如果type 为 1 , 未满足时按开奖时间
    open_time: str
    # 开奖人数
    open_num: int
    # 抽奖图片
    img_url: str
    # 抽奖描述
    desc: str
    # 描述图片 例子 ['lottery/1.jpg', 'https://lottery/2.jpg']
    desc_img: List[str]


@router.post(lottery.add.value)
async def lottery_add(item: LotteryItem, token: str = Header(None)):
    """
    发布抽奖
    @param item:
    @param token:
    @return:
    """
    try:
        if not token:
            return create_response(ret=1002, message='用户 Token 不存在')
        user = get_user_data(token)
        openid = user.get('openid')
        user_data = await UserTable.check_user(openid=openid)
        if not user_data:
            return create_response(ret=1003, message='用户不存在')
        user_id = user_data.id

        if user_id != item.user_id:
            return create_response(ret=1004, message='用户信息不匹配')

        options = {
            "user_id": user_id,
            "lottery_type": item.lottery_type,
            "name": item.name,
            "num": item.num,
            "open_type": item.open_type,
            "open_time": item.open_time,
            "open_num": item.open_num,
            "img_url": item.img_url,
            "desc": item.desc,
            "desc_img": item.desc_img
        }

        lotteryData = await LotteryTable.create_lottery(options)

        return create_response(ret=0, data={"lottery_id": lotteryData.id}, message='发布抽奖成功')
    except Exception as e:
        logger.error(f'发布抽奖失败：{e}')
        return create_response(ret=1001, data=str(e), message='发布抽奖失败')


@router.get(lottery.get_list.value)
async def lottery_list(page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    """
    获取抽奖列表
    @return:
    """

    try:
        list_data = await LotteryTable.get_list(page=page, limit=limit)

        return create_page_response(ret=0, data=list_data['items'], total=list_data['total'], page=page, limit=limit,
                                    message='获取抽奖列表成功')

    except Exception as e:
        logger.error(f'获取抽奖列表失败：{e}')
        return create_response(ret=1001, data=str(e), message='获取抽奖列表失败')


@router.get(lottery.get_detail.value)
async def lottery_detail(loerry_id: int):
    """
    获取抽奖详情
    @param lottery_id:
    @return:
    """
    try:
        lottery_data = await LotteryTable.get_detail(lottery_id=loerry_id)

        if not lottery_data:
            return create_response(ret=1001, message='抽奖不存在')

        return create_response(ret=0, data=lottery_data, message='获取抽奖详情成功')

    except Exception as e:
        logger.error(f'获取抽奖详情失败：{e}')
        return create_response(ret=1001, data=str(e), message='获取抽奖详情失败')


class JoinItem(BaseModel):
    lottery_id: int


@router.post(lottery.join.value)
async def lottery_join(item: JoinItem, token: str = Header(None)):
    """
    参与抽奖
    @param item:
    @param token:
    @return:
    """
    try:
        if not token:
            return create_response(ret=1002, message='用户 Token 不存在')
        user = get_user_data(token)
        openid = user.get('openid')
        user_data = await UserTable.check_user(openid=openid)
        if not user_data:
            return create_response(ret=1003, message='用户不存在')
        user_id = user_data.id

        options = {
            "lottery_id": item.lottery_id,
            "user_id": user_id,
            "status": 1
        }

        check_data = await LotteryTable.check_lottery(lottery_id=item.lottery_id)
        if not check_data:
            return create_response(ret=1004, message='抽奖不存在')

        check_data = await InvolvedLotteryTable.check_join(lottery_id=item.lottery_id, user_id=user_id)
        if check_data:
            return create_response(ret=1004, message='用户已参与抽奖')

        join_data = await InvolvedLotteryTable.user_join(options)

        return create_response(ret=0, data={"join_id": join_data.id}, message='参与抽奖成功')
    except Exception as e:
        logger.error(f'参与抽奖失败：{e}')
        return create_response(ret=1001, data=str(e), message='参与抽奖失败')


@router.get(lottery.get_user.value)
async def lottery_user_list(lottery_id: int):
    """
    获取抽奖参与用户列表
    @param lottery_id:
    @return:
    """
    try:

        list_data = await InvolvedLotteryTable.get_list(lottery_id=lottery_id)

        return create_page_response(ret=0, data=list_data['items'], page=1, limit=list_data['total'],
                                    total=list_data['total'], message='获取抽奖参与用户列表成功')
    except Exception as e:
        logger.error(f'获取抽奖参与用户列表失败：{e}')
        return create_response(ret=1001, data=str(e), message='获取抽奖参与用户列表失败')


class OpenItem(BaseModel):
    lottery_id: int


@router.get(lottery.open.value)
async def lottery_open(item: OpenItem, token: str = Header(None)):
    """
    开奖
    @param item:
    @param token:
    @return:
    """
    try:
        if not token:
            return create_response(ret=1002, message='用户 Token 不存在')
        user = get_user_data(token)
        openid = user.get('openid')
        user_data = await UserTable.check_user(openid=openid)
        if not user_data:
            return create_response(ret=1003, message='用户不存在')
        user_id = user_data.id

        check_data = await LotteryTable.check_lottery(lottery_id=item.lottery_id)
        if not check_data:
            return create_response(ret=1004, message='抽奖不存在')

        if check_data.user_id != user_id:
            return create_response(ret=1004, message='用户信息不匹配')

        if check_data.status == 2:
            return create_response(ret=1004, message='抽奖已开奖')

    except Exception as e:
        logger.error(f'开奖失败：{e}')
        return create_response(ret=1001, data=str(e), message='开奖失败')
