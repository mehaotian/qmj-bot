from datetime import datetime
from enum import IntEnum
from typing import List, Optional
from apscheduler.jobstores.base import JobLookupError

from nonebot import require
from nonebot.log import logger
from fastapi import APIRouter, Depends, HTTPException, Header, Query

from src.models.team_model import TeamTable
from src.models.team_members_model import TeamMembersTable
from src.models.user_model import UserTable
from pydantic import BaseModel, Field

from ..utils.responses import create_response, create_page_response
from ..utils.security import get_user_data
from ..utils.goeasy import goeasy_send_message

from ..api import team

try:
    scheduler = require("nonebot_plugin_apscheduler").scheduler
except Exception:
    scheduler = None

router = APIRouter()


# 抽离的用户验证函数
async def get_current_user(token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=400, detail="用户未登录")
    user = get_user_data(token)
    if not user or 'user_id' not in user:
        raise HTTPException(status_code=400, detail="用户未登录，或登录过期")
    user_data = await UserTable.get(id=user['user_id'])
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user_data


class TimeLimitType(IntEnum):
    """
    组队时限枚举表
    """
    short = 1  # 短期
    long = 2  # 长期


class NatureType(IntEnum):
    """
    组队性质枚举表
    """
    game = 1  # 游戏
    building = 2  # 团建
    activity = 3  # 活动


class AddTeamItem(BaseModel):
    name: str = Field(..., title="团队名称")
    current_num: int = Field(..., title="当前队伍人数")
    need_num: int = Field(..., title="需要等位多少人")
    time_limit: TimeLimitType = Field(..., title="组队时限")
    nature: NatureType = Field(..., title="组队性质")
    team_info: List[str] = Field(..., title="组队要求")
    start_time: str = Field(..., title="开始时间")
    end_time: str = Field(..., title="结束时间")
    desc: Optional[str] = Field(..., title="组队描述")
    desc_img: List[str] = Field(..., title="描述图片")


async def s_team_start(team_id: int):
    """
    开始组队
    @param id:
    @return:
    """
    table = await TeamTable.get(id=team_id)
    table.status = 1
    await table.save(update_fields=['status'])

    goeasy_send_message('onTeamChange', 'start')


async def s_team_end(team_id: int):
    """
    结束组队
    @param id:
    @return:
    """
    table = await TeamTable.get(id=team_id)
    table.status = 3
    await table.save(update_fields=['status'])
    goeasy_send_message('onTeamChange', 'end')


@router.post(team.add.value)
async def add_team(item: AddTeamItem, current_user: UserTable = Depends(get_current_user)):
    """
    创建团队
    参数：
    - item: 团队信息
    - token: 用户授权信息
    返回:
    - 成功：返回组队创建成功个信息
    - 失败：返回错误信息
    """
    # 组队名称 限制 3-12 字符
    if len(item.name) < 3 or len(item.name) > 12:
        return create_response(ret=1004, message='团队名称限制 3-12 字符')

    # 当前队伍人数 限制 1-100
    if item.current_num < 1 or item.current_num > 100:
        return create_response(ret=1004, message='当前队伍人数限制 1-100')

    # 需要等位多少人 限制 1-100
    if item.need_num < 1 or item.need_num > 100:
        return create_response(ret=1004, message='需要等位多少人限制 1-100')

    # 组队描述 限制 500 字内
    if len(item.desc) > 500:
        return create_response(ret=1004, message='组队描述限制 500 字内')

    # 描述图片 限制 0-9 张
    if len(item.desc_img) > 9:
        return create_response(ret=1004, message='组队描述图片最多上传 9 张')

    # 开始时间需要大于当前时间
    start_time = datetime.strptime(item.start_time, "%Y-%m-%d %H:%M")
    end_time = datetime.strptime(item.end_time, "%Y-%m-%d %H:%M")

    if start_time < datetime.now():
        team_status = 1
    else:
        team_status = 2

    # 结束时间大于开始时间
    if item.end_time:
        if end_time < start_time and end_time < datetime.now():
            return create_response(ret=1004, message='结束时间需要大于开始时间或当前时间')

    try:
        options = {
            "user_id": current_user.id,
            "name": item.name,
            "current_num": item.current_num,
            "need_num": item.need_num,
            "time_limit": item.time_limit,
            "nature": item.nature,
            "team_info": item.team_info,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "desc": item.desc,
            "desc_img": item.desc_img,
            "status": team_status
        }

        teamdata = await TeamTable.create_team(options)
        print('id', teamdata.id)
        if scheduler:

            if team_status == 2:
                # 如果当前时间大于的能与 开奖时间，直接开奖
                scheduler.add_job(
                    s_team_start,
                    "date",  # 触发器类型，"date" 表示在指定的时间只执行一次
                    run_date=start_time,  # 开奖时间
                    args=[teamdata.id],  # 传递给 open_lottery 函数的参数
                    id=f"team_start_{str(teamdata.id)}",  # 任务 ID，需要确保每个任务的 ID 是唯一的
                )
                print('----- 组队开始定时任务添加成功')
            scheduler.add_job(
                s_team_end,
                "date",  # 触发器类型，"date" 表示在指定的时间只执行一次
                run_date=end_time,  # 开奖时间
                args=[teamdata.id],  # 传递给 open_lottery 函数的参数
                id=f"team_end_{str(teamdata.id)}",  # 任务 ID，需要确保每个任务的 ID 是唯一的
            )

        return create_response(ret=0, data={
            "team_id": teamdata.id,
            "user_id": teamdata.user_id,
            "user_name": current_user.nickname,
            "team_name": teamdata.name
        }, message='创建成功')
    except Exception as e:
        logger.error(e)
        return create_response(ret=1001, message='创建组队失败')


@router.get(team.get_list.value)
async def get_team_list(
        page: int = Query(1, ge=1, description="页码，默认为1"),
        limit: int = Query(10, ge=1, le=100, description="每页数量，默认为10，最大100"),
        status: Optional[int] = Query(0, ge=0, le=3, description="组队状态：0-全部，1-进行中，2-进行中，3-已结束")
):
    """
    获取组队列表

    参数:
    - page: 页码，从1开始
    - limit: 每页显示的数量，1-100之间
    - status: 组队状态筛选，0表示全部，1表示进行中，2表示已结束

    返回:
    - 成功：返回分页后的组队列表数据
    - 失败：返回错误信息
    """
    try:
        list_data = await TeamTable.get_team_list(page=page, limit=limit, status=status if status != 0 else None)

        if not list_data['items']:
            return create_response(ret=0, data=[], message='暂无组队数据')

        return create_page_response(
            ret=0,
            data=list_data['items'],
            total=list_data['total'],
            page=page,
            limit=limit,
            message='获取组队列表成功'
        )

    except ValueError as ve:
        logger.warning(f'获取组队列表参数错误：{ve}')
        return create_response(ret=1002, message=f'参数错误：{str(ve)}')
    except Exception as e:
        logger.error(f'获取组队列表失败：{e}')
        return create_response(ret=1001, message='获取组队列表失败，请稍后重试')


@router.get(team.get_my_list.value)
async def lottery_my_list(
        page: int = Query(1, ge=1, description="页码，默认为1"),
        limit: int = Query(10, ge=1, le=100, description="每页数量，默认为10，最大100"),
        status: Optional[int] = Query(0, ge=0, le=3, description="抽奖状态：0-全部，1-进行中2-未开始，3-已结束"),
        user: UserTable = Depends(get_current_user)
):
    """
    获取当前用户的组队列表

    参数:
    - page: 页码，从1开始
    - limit: 每页显示的数量，1-100之间
    - status: 抽奖状态筛选，0表示全部，1表示进行中，2表示未开始， 3表示已结束
    - user: 当前登录用户，通过依赖注入获取

    返回:
    - 成功：返回分页后的用户抽奖列表数据
    - 失败：返回错误信息
    """
    try:
        user_id = user.id

        list_data = await TeamTable.get_team_list(
            page=page,
            limit=limit,
            status=status if status != 0 else None,
            user_id=user_id
        )

        if not list_data['items']:
            return create_response(ret=0, data=[], message='暂无组队数据')

        return create_page_response(
            ret=0,
            data=list_data['items'],
            total=list_data['total'],
            page=page,
            limit=limit,
            message='获取用户组队列表成功'
        )

    except ValueError as ve:
        logger.warning(f'获取用户组队列表参数错误：{ve}')
        return create_response(ret=1002, message=f'参数错误：{str(ve)}')
    except Exception as e:
        logger.error(f'获取用户组队列表失败：{e}')
        return create_response(ret=1001, message='获取用户组队列表失败，请稍后重试')


@router.get(team.get_detail.value)
async def team_detail(team_id: int = Query(..., gt=0, description="组队ID")):
    """
    获取组队详情

    参数:
    - team_id: 组队ID，必须大于0

    返回:
    - 成功：返回组队详情数据
    - 失败：返回错误信息
    """
    try:
        team_data = await TeamTable.get_detail(team_id=team_id)
        if not team_data:
            return create_response(ret=1004, message='组队不存在')

        return create_response(ret=0, data=team_data, message='获取组队详情成功')

    except ValueError as ve:
        logger.warning(f'获取组队详情参数错误：{ve}')
        return create_response(ret=1002, message=f'参数错误：{str(ve)}')
    except Exception as e:
        logger.error(f'获取组队详情失败：{e}')
        return create_response(ret=1001, message='获取组队详情失败，请稍后重试')


class JoinItem(BaseModel):
    team_id: int = Field(..., gt=0, description="组队ID")


@router.post(team.join.value)
async def join_team(team: JoinItem, current_user: UserTable = Depends(get_current_user)):
    """
    参与组队

    方式: POST

    参数:
    - team_id: 组队ID

    请求头
    - token: 用户授权信息

    返回:
    - 成功：返回参与成功信息
    - 失败：返回错误信息
    """
    try:
        team_id = team.team_id
        user_id = current_user.id
        team_data = await TeamTable.get(id=team_id)
        if not team_data:
            return create_response(ret=1004, message='组队不存在')

        # 检查组队状态
        if team_data.status == 3:
            return create_response(ret=1004, message='组队已结束')

        # 检查用户是否已经参与组队
        check_join = await TeamMembersTable.check_join(team_id=team_id, user_id=user_id)
        if check_join and check_join.status == 1:
            return create_response(ret=1004, message='您已参与当前组队')

        # 检查组队是否已满
        # 获取当前已加入人数
        team_members_count = await TeamMembersTable.get_join_count(team_id=team_id)
        # 已存在人数

        if team_members_count >= team_data.need_num:
            return create_response(ret=1004, message='组队已满员')

        # 创建参与组队
        join_data = {
            "team_id": team_id,
            "user_id": user_id,
        }
        await TeamMembersTable.user_join(join_data)

        return create_response(ret=0, message='参与组队成功')


    except Exception as e:
        logger.error(e)
        return create_response(ret=1001, message='参与组队失败')


@router.post(team.leave.value)
async def leave_team(team: JoinItem, current_user: UserTable = Depends(get_current_user)):
    """
    离开组队

    方式: POST

    参数:
    - team_id: 组队ID

    请求头
    - token: 用户授权信息

    返回:
    - 成功：返回离开成功信息
    - 失败：返回错误信息
    """
    try:
        team_id = team.team_id
        user_id = current_user.id
        team_data = await TeamTable.get(id=team_id)
        if not team_data:
            return create_response(ret=1004, message='组队不存在')

        # 检查用户是否已经参与组队
        check_join = await TeamMembersTable.check_join(team_id=team_id, user_id=user_id)
        if not check_join:
            return create_response(ret=1004, message='您未参与当前组队')

        # 离开组队
        await check_join.delete()

        return create_response(ret=0, message='离开组队成功')

    except Exception as e:
        logger.error(e)
        return create_response(ret=1001, message='离开组队失败')


@router.post(team.end.value)
async def close_team(team: JoinItem, current_user: UserTable = Depends(get_current_user)):
    """
    关闭组队

    方式: POST

    参数:
    - team_id: 组队ID

    请求头
    - token: 用户授权信息

    返回:
    - 成功：返回关闭成功信息
    - 失败：返回错误信息
    """
    try:
        team_id = team.team_id
        user_id = current_user.id
        team_data = await TeamTable.get(id=team_id)
        if not team_data:
            return create_response(ret=1004, message='组队不存在')

        if team_data.user_id != user_id:
            return create_response(ret=1004, message='您不是组队创建者')

        # 关闭组队
        team_data.status = 3
        await team_data.save(update_fields=['status'])

        return create_response(ret=0, message='关闭组队成功')

    except Exception as e:
        logger.error(e)
        return create_response(ret=1001, message='关闭组队失败')


@router.get(team.get_user.value)
async def get_team_user(team_id: int = Query(..., gt=0, description="组队ID")):
    """
    获取组队用户列表

    参数:
    - team_id: 组队ID，必须大于0

    返回:
    - 成功：返回组队用户列表数据
    - 失败：返回错误信息
    """
    try:
        team_data = await TeamMembersTable.get_list(team_id=team_id)
        if not team_data:
            return create_response(ret=1004, message='组队不存在')

        if not team_data['items']:
            return create_response(ret=0, data=[], message='暂无人参与')

        return create_page_response(
            ret=0,
            data=team_data['items'],
            total=team_data['total'],
            message='获取组队列表成功'
        )

    except ValueError as ve:
        logger.warning(f'获取组队用户列表参数错误：{ve}')
        return create_response(ret=1002, message=f'参数错误：{str(ve)}')
    except Exception as e:
        logger.error(f'获取组队用户列表失败：{e}')
        return create_response(ret=1001, message='获取组队用户列表失败，请稍后重试')
