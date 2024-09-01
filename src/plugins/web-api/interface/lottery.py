from datetime import datetime

import httpx
from nonebot.log import logger
from fastapi import APIRouter, Header, Query

from pydantic import BaseModel
from typing import List

from src.models.prize_model import PrizeTable
from src.models.user_model import UserTable
from src.models.lottery_model import LotteryTable
from src.models.involved_lottery_model import InvolvedLotteryTable
from src.utils.tools import Lottery

from ..utils.responses import create_response, create_page_response
from ..utils.security import get_user_data

from ..api import lottery

router = APIRouter()


class PrizeItem(BaseModel):
    # 抽奖名称
    name: str
    # 抽奖图片
    img_url: str
    # 奖品类型 1: 奖品 2: 金币 3: 喵币 4: 兑换券(签到券,抽奖券) 5: 兑换码
    prize_type: int
    # 奖品份数
    prize_count: int


class LotteryItem(BaseModel):
    # 发布者user_id
    user_id: int
    # 开奖类型 1: 按人数开奖 2: 按时间开奖
    open_type: int
    # 开奖时间 ，如果type 为 1 , 未满足时按开奖时间
    open_time: str
    # 开奖人数
    open_num: int
    # 抽奖描述
    desc: str
    # 描述图片 例子 ['lottery/1.jpg', 'https://lottery/2.jpg']
    desc_img: List[str]
    # 奖品
    prizes: List[PrizeItem]


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

        print(item.prizes)
        options = {
            "user_id": user_id,
            # 抽奖类型 1: 普通抽奖 2: 盲盒抽奖
            "lottery_type": 1,
            "open_type": item.open_type,
            "open_time": item.open_time,
            "open_num": item.open_num,
            "desc": item.desc,
            "desc_img": item.desc_img
        }

        lotteryData = await LotteryTable.create_lottery(options)

        for prize in item.prizes:
            prize_data = {
                # 抽奖id
                "lottery_id": lotteryData.id,
                # 抽奖类型 1 通用抽奖 2 盲盒抽奖
                "type": 1,
                # 奖品类型 1: 奖品 2: 金币 3: 喵币 4: 兑换券(签到券,抽奖券) 5: 兑换码
                "prize_type": prize.prize_type,
                "name": prize.name,
                "img_url": prize.img_url,
                "prize_count": prize.prize_count,
                # 状态 ,默认是2 ,没有开奖
                "status": 2
            }
            await PrizeTable.create_prize(prize_data)

        return create_response(
            ret=0,
            data={
                "lottery_id": lotteryData.id,
            },
            message='发布抽奖成功'
        )

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

@router.get(lottery.get_prize_list.value)
async def lottery_prize_list(lottery_id=Query('')):
    """
    获取抽奖奖品列表
    @param lottery_id:
    @return:
    """
    try:
        prize_data = await PrizeTable.get_list(lottery_id=lottery_id)

        return create_response(ret=0, data=prize_data, message='获取抽奖奖品列表成功')

    except Exception as e:
        logger.error(f'获取抽奖奖品列表失败：{e}')
        return create_response(ret=1001, data=str(e), message='获取抽奖奖品列表失败')


@router.get(lottery.get_detail.value)
async def lottery_detail(lottery_id=Query('')):
    """
    获取抽奖详情
    @param lottery_id:
    @return:
    """
    try:
        if not lottery_id:
            return create_response(ret=1002, message='抽奖 ID 不存在')

        lottery_data = await LotteryTable.get_detail(lottery_id=lottery_id)

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
        print(user)
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

        if check_data.status == 2:
            return create_response(ret=1004, message='抽奖已结束')

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


@router.post(lottery.open.value)
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
            return create_response(ret=1004, message='抽奖已结束')

        num = check_data.num
        list_data = await InvolvedLotteryTable.get_list(lottery_id=item.lottery_id)

        users = list_data['items']
        lottery_tools = Lottery(users)
        print(num)
        winners = lottery_tools.draw_winners(num_winners=num)

        wids = [winner['user_id'] for winner in winners]
        await InvolvedLotteryTable.edit_winner_status(lottery_id=item.lottery_id, winner_ids=wids)
        await LotteryTable.filter(id=item.lottery_id).update(status=2)

        return create_response(ret=0, data=winners, message='开奖成功')
    except Exception as e:
        logger.error(f'开奖失败：{e}')
        return create_response(ret=1001, data=str(e), message='开奖失败')


class WinnerItem(BaseModel):
    lottery_id: int


@router.post(lottery.get_winner.value)
async def lottery_winner_list(item: WinnerItem, token: str = Header(None)):
    """
    获取抽奖中奖用户列表
    @param lottery_id:
    @return:
    """
    # try:
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

    list_data = await InvolvedLotteryTable.get_winners_list(lottery_id=item.lottery_id)

    return create_response(ret=0, data=list_data, message='获取抽奖中奖用户列表成功')
# except Exception as e:
#     logger.error(f'获取抽奖中奖用户列表失败：{e}')
#     return create_response(ret=1001, data=str(e), message='获取抽奖中奖用户列表失败')
