from datetime import datetime

from apscheduler.jobstores.base import JobLookupError
from nonebot import require
from nonebot.log import logger
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from enum import IntEnum
from typing import List, Optional
from pydantic import BaseModel, Field
from src.models.prize_model import PrizeTable
from src.models.user_model import UserTable
from src.models.lottery_model import LotteryTable
from src.models.involved_lottery_model import InvolvedLotteryTable
from src.models.write_off_model import WriteOffTable
from src.utils.tools import Lottery

from ..utils.responses import create_response, create_page_response
from ..utils.security import get_user_data
from ..utils import scheduler_open_lottery

from ..api import lottery

try:
    scheduler = require("nonebot_plugin_apscheduler").scheduler
except Exception:
    scheduler = None

router = APIRouter()

# 抽离的用户验证函数
async def get_current_user(token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=400, message="用户未登录")
    user = get_user_data(token)
    if not user or 'openid' not in user:
        raise HTTPException(status_code=400, message="用户未登录，或登录过期")
    user_data = await UserTable.check_user(openid=user['openid'])
    if not user_data:
        raise HTTPException(status_code=404, message="用户不存在")
    return user_data

# 抽离的抽奖验证函数
async def verify_lottery(lottery_id: int):
    lottery = await LotteryTable.check_lottery(lottery_id=lottery_id)
    if not lottery:
        raise HTTPException(status_code=404, detail="抽奖不存在")
    return lottery

class PrizeType(IntEnum):
    PRIZE = 1
    GOLD_COIN = 2
    MEOW_COIN = 3
    VOUCHER = 4
    REDEMPTION_CODE = 5

class PrizeItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="奖品名称")
    img_url: str = Field(..., description="奖品图片URL")
    prize_type: PrizeType = Field(..., description="奖品类型")
    prize_count: int = Field(..., gt=0, description="奖品份数")

class OpenType(IntEnum):
    BY_NUMBER = 1
    BY_TIME = 2

class LotteryItem(BaseModel):
    user_id: int = Field(..., gt=0, description="发布者user_id")
    open_type: OpenType = Field(..., description="开奖类型")
    open_time: str = Field(..., description="开奖时间，如果type为1，未满足时按开奖时间")
    open_num: int = Field(..., gt=0, description="开奖人数")
    win_info: List[str] = Field(default=[], description="中奖信息")
    desc: Optional[str] = Field(None, max_length=500, description="抽奖描述（非必填）")
    desc_img: List[str] = Field(default=[], max_items=5, description="描述图片")
    prizes: List[PrizeItem] = Field(..., min_items=1, max_items=10, description="奖品列表")


@router.post(lottery.add.value)
async def lottery_add(item: LotteryItem, current_user: UserTable = Depends(get_current_user)):
    """
    发布抽奖
    @param item:
    @param token:
    @return:
    """
    try:
        if current_user.id != item.user_id:
            return create_response(ret=1004, message='用户信息不匹配')

        options = {
            "user_id": current_user.id,
            # 抽奖类型 1: 普通抽奖 2: 盲盒抽奖
            "lottery_type": 1,
            "open_type": item.open_type,
            "open_time": item.open_time,
            "open_num": item.open_num,
            "desc": item.desc,
            "win_info": item.win_info or [],
            "desc_img": item.desc_img
        }

        # 开奖时间必须大于当前时间
        open_time = datetime.strptime(item.open_time, "%Y-%m-%d %H:%M")
        if open_time <= datetime.now():
            return create_response(ret=1003, message='开奖时间必须大于当前时间')

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
        if scheduler:
            open_time = datetime.strptime(item.open_time, "%Y-%m-%d %H:%M")
            scheduler.add_job(
                scheduler_open_lottery,
                "date",  # 触发器类型，"date" 表示在指定的时间只执行一次
                run_date=open_time,  # 开奖时间
                args=[lotteryData.id, current_user.id],  # 传递给 open_lottery 函数的参数
                id=f"lottery_{str(lotteryData.id)}",  # 任务 ID，需要确保每个任务的 ID 是唯一的
            )
            print('----- 抽奖定时任务添加成功')

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
async def lottery_list(
    page: int = Query(1, ge=1, description="页码，默认为1"),
    limit: int = Query(10, ge=1, le=100, description="每页数量，默认为10，最大100"),
    status: Optional[int] = Query(0, ge=0, le=2, description="抽奖状态：0-全部，1-进行中，2-已结束")
):
    """
    获取抽奖列表

    参数:
    - page: 页码，从1开始
    - limit: 每页显示的数量，1-100之间
    - status: 抽奖状态筛选，0表示全部，1表示进行中，2表示已结束

    返回:
    - 成功：返回分页后的抽奖列表数据
    - 失败：返回错误信息
    """
    try:
        list_data = await LotteryTable.get_list(page=page, limit=limit, status=status if status != 0 else None)

        if not list_data['items']:
            return create_response(ret=0, data=[], message='暂无抽奖数据')

        return create_page_response(
            ret=0, 
            data=list_data['items'], 
            total=list_data['total'], 
            page=page, 
            limit=limit,
            message='获取抽奖列表成功'
        )

    except ValueError as ve:
        logger.warning(f'获取抽奖列表参数错误：{ve}')
        return create_response(ret=1002, message=f'参数错误：{str(ve)}')
    except Exception as e:
        logger.error(f'获取抽奖列表失败：{e}')
        return create_response(ret=1001, message='获取抽奖列表失败，请稍后重试')



@router.get(lottery.get_my_list.value)
async def lottery_my_list(
    page: int = Query(1, ge=1, description="页码，默认为1"),
    limit: int = Query(10, ge=1, le=100, description="每页数量，默认为10，最大100"),
    status: Optional[int] = Query(0, ge=0, le=2, description="抽奖状态：0-全部，1-进行中，2-已结束"),
    user: UserTable = Depends(get_current_user)
):
    """
    获取当前用户的抽奖列表

    参数:
    - page: 页码，从1开始
    - limit: 每页显示的数量，1-100之间
    - status: 抽奖状态筛选，0表示全部，1表示进行中，2表示已结束
    - user: 当前登录用户，通过依赖注入获取

    返回:
    - 成功：返回分页后的用户抽奖列表数据
    - 失败：返回错误信息
    """
    try:
        user_id = user.id
        
        list_data = await LotteryTable.get_list(
            page=page, 
            limit=limit, 
            status=status if status != 0 else None,
            user_id=user_id
        )

        if not list_data['items']:
            return create_response(ret=0, data=[], message='暂无抽奖数据')

        return create_page_response(
            ret=0, 
            data=list_data['items'], 
            total=list_data['total'], 
            page=page, 
            limit=limit,
            message='获取用户抽奖列表成功'
        )

    except ValueError as ve:
        logger.warning(f'获取用户抽奖列表参数错误：{ve}')
        return create_response(ret=1002, message=f'参数错误：{str(ve)}')
    except Exception as e:
        logger.error(f'获取用户抽奖列表失败：{e}')
        return create_response(ret=1001, message='获取用户抽奖列表失败，请稍后重试')
   


@router.get(lottery.get_prize_list.value)
async def lottery_prize_list(lottery_id: int = Query(..., gt=0, description="抽奖ID")):
    """
    获取指定抽奖的奖品列表

    参数:
    - lottery_id: 抽奖ID，必须大于0

    返回:
    - 成功：返回奖品列表数据
    - 失败：返回错误信息
    """
    try:
        # 验证抽奖是否存在
        lottery = await LotteryTable.check_lottery(lottery_id)
        if not lottery:
            return create_response(ret=1004, message='指定的抽奖不存在')

        prize_data = await PrizeTable.get_list(lottery_id=lottery_id)

        if not prize_data:
            return create_response(ret=0, data=[], message='该抽奖暂无奖品')

        return create_response(ret=0, data=prize_data, message='获取抽奖奖品列表成功')

    except ValueError as ve:
        logger.warning(f'获取抽奖奖品列表参数错误：{ve}')
        return create_response(ret=1002, message=f'参数错误：{str(ve)}')
    except Exception as e:
        logger.error(f'获取抽奖奖品列表失败：{e}')
        return create_response(ret=1001, message='获取抽奖奖品列表失败，请稍后重试')


@router.get(lottery.get_detail.value)
async def lottery_detail(lottery_id: int = Query(..., gt=0, description="抽奖ID")):
    """
    获取抽奖详情

    参数:
    - lottery_id: 抽奖ID，必须大于0

    返回:
    - 成功：返回抽奖详情数据
    - 失败：返回错误信息
    """
    try:
        lottery_data = await LotteryTable.get_detail(lottery_id=lottery_id)

        if not lottery_data:
            return create_response(ret=1004, message='抽奖不存在')

        return create_response(ret=0, data=lottery_data, message='获取抽奖详情成功')

    except ValueError as ve:
        logger.warning(f'获取抽奖详情参数错误：{ve}')
        return create_response(ret=1002, message=f'参数错误：{str(ve)}')
    except Exception as e:
        logger.error(f'获取抽奖详情失败：{e}')
        return create_response(ret=1001, message='获取抽奖详情失败，请稍后重试')


class JoinItem(BaseModel):
    lottery_id: int = Field(..., gt=0, description="抽奖ID")

@router.post(lottery.join.value)
async def lottery_join(item: JoinItem, current_user: UserTable = Depends(get_current_user)):
    """
    参与抽奖

    参数:
    - item: JoinItem 对象，包含抽奖ID
    - current_user: 当前登录用户

    返回:
    - 成功：返回参与抽奖成功的信息，包括join_id
    - 失败：返回错误信息

    可能的错误:
    - 1004: 抽奖不存在、抽奖已结束或用户已参与抽奖
    - 1001: 其他未预期的错误
    """
    try:
        lottery = await LotteryTable.check_lottery(lottery_id=item.lottery_id)
        if not lottery:
            logger.warning(f"抽奖不存在，lottery_id: {item.lottery_id}")
            return create_response(ret=1004, message='抽奖不存在')

        if lottery.status == 2:
            logger.info(f"尝试参与已结束的抽奖，lottery_id: {item.lottery_id}")
            return create_response(ret=1004, message='抽奖已结束')

        is_joined = await InvolvedLotteryTable.check_join(lottery_id=item.lottery_id, user_id=current_user.id)
        if is_joined:
            logger.info(f"用户已参与抽奖，user_id: {current_user.id}, lottery_id: {item.lottery_id}")
            return create_response(ret=1004, message='您已参与该抽奖')

        join_data = await InvolvedLotteryTable.user_join({
            "lottery_id": item.lottery_id,
            "user_id": current_user.id,
            "status": 1
        })

        logger.info(f"用户成功参与抽奖，user_id: {current_user.id}, lottery_id: {item.lottery_id}")
        return create_response(ret=0, data={"join_id": join_data.id}, message='参与抽奖成功')
    
    except Exception as e:
        logger.error(f'参与抽奖时发生未预期的错误：{str(e)}')
        return create_response(ret=1001, message='参与抽奖失败，请稍后重试')


@router.get(lottery.get_user.value)
async def lottery_user_list(lottery_id: int):
    """
    获取抽奖参与用户列表

    参数:
    - lottery_id: int, 抽奖ID

    返回:
    - 成功: 返回包含参与用户列表的分页响应
    - 失败: 返回错误信息

    错误代码:
    - 1001: 获取列表失败
    - 1004: 抽奖不存在
    """
    try:
        # 检查抽奖是否存在
        lottery = await LotteryTable.check_lottery(lottery_id=lottery_id)
        if not lottery:
            logger.warning(f"尝试获取不存在的抽奖参与用户列表，lottery_id: {lottery_id}")
            return create_response(ret=1004, message='抽奖不存在')

        # 获取参与用户列表
        list_data = await InvolvedLotteryTable.get_list(lottery_id=lottery_id)

        if not list_data:
            logger.info(f"抽奖 {lottery_id} 暂无参与用户")
            return create_page_response(ret=0, data=[], page=1, limit=0, total=0, message='暂无参与用户')

        return create_page_response(
            ret=0, 
            data=list_data['items'], 
            page=1, 
            limit=len(list_data['items']),
            total=list_data['total'], 
            message='获取抽奖参与用户列表成功'
        )
    except Exception as e:
        logger.error(f'获取抽奖参与用户列表失败：{e}')
        return create_response(ret=1001, message='获取抽奖参与用户列表失败，请稍后重试')


class OpenItem(BaseModel):
    lottery_id: int = Field(..., gt=0, description="抽奖ID")


@router.post(lottery.open.value)
async def lottery_open(item: OpenItem, current_user: UserTable = Depends(get_current_user)):
    """
    执行开奖操作

    参数:
    - item: OpenItem, 包含抽奖ID的对象
    - current_user: UserTable, 当前用户信息

    返回:
    - 成功: 返回开奖成功的消息
    - 失败: 返回错误信息

    错误代码:
    - 1001: 开奖过程中发生未知错误
    - 1004: 抽奖不存在或用户信息不匹配或抽奖已结束
    """
    # 关闭定时任务
    job_id = f"lottery_{str(item.lottery_id)}"
    try:
        scheduler.remove_job(job_id)
        print(f"任务 {job_id} 已经停止")
    except JobLookupError:
        print(f"任务 {job_id} 已经停止,本次为无效停止")
    return await scheduler_open_lottery(item.lottery_id, current_user.id)
    # try:
    #     # 验证抽奖信息
    #     check_data = await LotteryTable.check_lottery(lottery_id=item.lottery_id)
    #     if not check_data:
    #         logger.warning(f"尝试开奖的抽奖不存在，lottery_id: {item.lottery_id}")
    #         return create_response(ret=1004, message='抽奖不存在')
    #
    #     if check_data.user_id != current_user.id:
    #         logger.warning(f"用户 {current_user.id} 尝试开启不属于自己的抽奖 {item.lottery_id}")
    #         return create_response(ret=1004, message='用户信息不匹配')
    #
    #     if check_data.status == 2:
    #         logger.warning(f"尝试开启已结束的抽奖，lottery_id: {item.lottery_id}")
    #         return create_response(ret=1004, message='抽奖已结束')
    #
    #     # 获取参与抽奖的用户列表
    #     list_data = await InvolvedLotteryTable.get_list(lottery_id=item.lottery_id)
    #     win_info = check_data.win_info or []
    #
    #     win_info_arrs = [{"name": info, "value": ""} for info in win_info]
    #
    #     users = list_data['items']
    #     users_copy = users.copy()
    #
    #     # 获取奖品列表
    #     prize_data = await PrizeTable.get_list(lottery_id=item.lottery_id)
    #
    #     # 执行开奖流程
    #     for prize in prize_data:
    #         lottery_tools = Lottery(users_copy)
    #         winners = lottery_tools.draw_winners(num_winners=prize["prize_count"])
    #
    #         for winner in winners:
    #             for user in users_copy[:]:  # 使用切片创建副本进行迭代
    #                 if winner['user_id'] == user['user_id']:
    #                     # 创建奖品核销记录
    #                     await WriteOffTable.create_write_of({
    #                         "lottery_id": item.lottery_id,
    #                         "prize_id": prize['id'],
    #                         "user_id": winner['user_id'],
    #                         "write_off_info": win_info_arrs
    #                     })
    #                     users_copy.remove(user)
    #                     break
    #
    #         # 更新中奖者状态
    #         winner_ids = [winner['user_id'] for winner in winners]
    #         await InvolvedLotteryTable.edit_winner_status(
    #             lottery_id=item.lottery_id,
    #             winner_ids=winner_ids,
    #             prize_id=prize['id']
    #         )
    #
    #     # 更新未中奖者状态
    #     await InvolvedLotteryTable.edit_losers_status(lottery_id=item.lottery_id)
    #
    #     # 更新抽奖状态为已结束
    #     await LotteryTable.filter(id=item.lottery_id).update(status=2)
    #
    #     logger.info(f"抽奖 id: {item.lottery_id}, 开奖成功")
    #     return create_response(ret=0, data='', message='开奖成功')
    #
    # except Exception as e:
    #     logger.error(f'开奖过程中发生错误：{str(e)}')
    #     return create_response(ret=1001, data=str(e), message='开奖失败，请稍后重试')


@router.get(lottery.get_user_list.value)
async def lottery_user_list(lottery_id: int, current_user: UserTable = Depends(get_current_user)):
    """
    获取中奖名单

    参数:
    - lottery_id: int, 抽奖活动ID
    - current_user: UserTable, 当前用户信息 (通过依赖注入获取)

    返回:
    - 成功: 返回中奖用户列表
    - 失败: 返回错误信息
    """
    try:
        if lottery_id <= 0:
            return create_response(ret=1003, message='无效的抽奖ID')
        
        user_list = await WriteOffTable.get_user_list(lottery_id=lottery_id)
        
        if not user_list:
            return create_response(ret=0, data=[], message='该抽奖活动暂无中奖用户')
        
        return create_response(ret=0, data=user_list, message='获取抽奖中奖用户列表成功')
    
    except Exception as e:
        logger.error(f"获取中奖名单时发生错误: {str(e)}")
        return create_response(ret=1001, message='获取中奖名单失败，请稍后重试')


class WinnerItem(BaseModel):
    write_off_id: int
    info: List[dict]


@router.post(lottery.submit_winner_info.value)
async def lottery_submit_winner_info(item: WinnerItem, current_user: UserTable = Depends(get_current_user)):
    """
    提交中奖信息

    参数:
    - item: WinnerItem, 包含中奖信息的对象
    - current_user: UserTable, 当前用户信息 (通过依赖注入获取)

    返回:
    - 成功: 返回修改后的用户中奖信息列表
    - 失败: 返回错误信息
    """
    try:
        
        if not item.write_off_id or item.write_off_id <= 0:
            return create_response(ret=1003, message='无效的核销ID')
        
        if not item.info or not isinstance(item.info, list):
            return create_response(ret=1004, message='无效的中奖信息格式')
        
        # 检查核销记录是否存在
        write_off_record = await WriteOffTable.get_or_none(id=item.write_off_id)
        if not write_off_record:
            return create_response(ret=1005, message='核销记录不存在')
        
        user_list = await WriteOffTable.add_write_off_info(write_off_id=item.write_off_id, write_off_info=item.info)
        
        if not user_list:
            return create_response(ret=1006, message='更新中奖信息失败')
        
        return create_response(ret=0, data=user_list, message='用户中奖信息修改成功')
    except Exception as e:
        logger.error(f'提交中奖信息失败：{str(e)}')
        return create_response(ret=1001, data=str(e), message='提交中奖信息失败，请稍后重试')


@router.get(lottery.get_write_off_list.value)
async def lottery_write_off_list(lottery_id: int = Query(..., gt=0, description="抽奖ID"), 
                                current_user: UserTable = Depends(get_current_user)):
    """
    获取指定抽奖活动的核销名单

    参数:
    - lottery_id: 抽奖活动ID，必须大于0
    - current_user: 当前用户信息，通过依赖注入获取

    返回:
    - 成功: 返回核销名单列表
    - 失败: 返回错误信息
    """
    try:
        # 检查抽奖活动是否存在
        lottery = await LotteryTable.get_or_none(id=lottery_id)
        if not lottery:
            return create_response(ret=1004, message='抽奖活动不存在')
        
        user_list = await WriteOffTable.get_write_off_list(lottery_id=lottery_id)
        
        if user_list is None:
            return create_response(ret=1005, message='获取核销名单失败')
        
        return create_response(ret=0, data=user_list, message='获取核销名单成功')
    except Exception as e:
        logger.error(f"获取核销名单时发生错误: {str(e)}")
        return create_response(ret=1001, message='获取核销名单失败，请稍后重试')


class WriteOffItem(BaseModel):
    write_off_id: int = Field(..., gt=0, description="核销ID")
    status: int = Field(..., ge=1, le=2, description="核销状态")


@router.post(lottery.edit_write_off.value)
async def lottery_edit_write_off_status(item: WriteOffItem, token: str = Header(None)):
    """
    编辑核销状态

    参数:
    - item: WriteOffItem 对象，包含 write_off_id 和 status
    - token: 用户认证令牌，通过 Header 传递

    返回:
    - 成功: 返回更新后的核销信息
    - 失败: 返回错误信息
    """
    try:
        if not token:
            return create_response(ret=1002, message='用户未登录')
        
        user = get_user_data(token)
        if not user:
            return create_response(ret=1003, message='无效的用户 Token')
        
        openid = user.get('openid')
        user_data = await UserTable.check_user(openid=openid)
        if not user_data:
            return create_response(ret=1004, message='用户不存在')
        
        # user_id = user_data.id
        write_off_id = item.write_off_id
        status = item.status

        # 验证状态值是否有效
        if status not in [1, 2]:
            return create_response(ret=1005, message='无效的核销状态')

        # 判断是否存在核销记录
        is_edit = await WriteOffTable.get_or_none(id=write_off_id)
        if not is_edit:
            return create_response(ret=1006, message='核销记录不存在')

        # 检查是否重复操作
        if is_edit.status == status:
            return create_response(ret=1007, message='核销状态未发生变化')

        # 更新核销状态
        check_data = await WriteOffTable.edit_write_off_status(write_off_id=write_off_id, status=status)
        if not check_data:
            return create_response(ret=1008, message='更新核销状态失败')

        msg = '核销成功' if status == 1 else '撤回核销成功'

        # TODO: 实现发奖逻辑
        # if status == 1:
        #     await send_reward(user_id, write_off_id)

        return create_response(ret=0, data=check_data, message=msg)
    except Exception as e:
        logger.error(f"编辑核销状态时发生错误: {str(e)}")
        return create_response(ret=1001, message='编辑核销状态失败，请稍后重试')


class WinnerItem(BaseModel):
    lottery_id: int = Field(..., gt=0, description="抽奖ID")


@router.post(lottery.get_winner.value)
async def lottery_winner_list(item: WinnerItem, token: str = Header(None)):
    """
    TODO 暂时无用
    获取抽奖中奖用户列表

    参数:
    - item: WinnerItem 对象，包含抽奖ID
    - token: 用户认证令牌

    返回:
    - 成功: 返回中奖用户列表
    - 失败: 返回错误信息
    """
    try:
        # 验证用户token
        if not token:
            return create_response(ret=1002, message='用户Token不存在')
        
        user = get_user_data(token)
        if not user or 'openid' not in user:
            return create_response(ret=1003, message='无效的用户Token')
        
        openid = user['openid']
        user_data = await UserTable.check_user(openid=openid)
        if not user_data:
            return create_response(ret=1004, message='用户不存在')
        
        # 验证抽奖是否存在
        check_data = await LotteryTable.check_lottery(lottery_id=item.lottery_id)
        if not check_data:
            return create_response(ret=1005, message='抽奖不存在')
        
        # 获取中奖用户列表
        list_data = await InvolvedLotteryTable.get_winners_list(lottery_id=item.lottery_id)
        
        # 检查是否有中奖用户
        if not list_data:
            return create_response(ret=0, data=[], message='该抽奖暂无中奖用户')
        
        return create_response(ret=0, data=list_data, message='获取抽奖中奖用户列表成功')
    except Exception as e:
        logger.error(f'获取抽奖中奖用户列表失败：{str(e)}')
        return create_response(ret=1001, message='获取抽奖中奖用户列表失败，请稍后重试')
