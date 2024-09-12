from datetime import datetime

from apscheduler.jobstores.base import JobLookupError
from click import option
from nonebot import require
from nonebot.log import logger
from fastapi import APIRouter, Depends, HTTPException, Header, Query

from src.models.team_model import TeamTable
from src.models.user_model import UserTable
from pydantic import BaseModel, Field

from ..utils.responses import create_response, create_page_response
from ..utils.security import get_user_data
from ..utils import scheduler_open_lottery

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
    if not user or 'openid' not in user:
        raise HTTPException(status_code=400, detail="用户未登录，或登录过期")
    user_data = await UserTable.check_user(openid=user['openid'])
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user_data


class AddTeamItem(BaseModel):
    name = Field(..., title="团队名称")
    current_num = Field(..., title="当前队伍人数")
    need_num = Field(..., title="需要等位多少人")
    time_limit = Field(..., title="组队时限")
    nature = Field(..., title="组队性质")
    team_info = Field(..., title="组队要求")
    start_time = Field(..., title="开始时间")
    end_time = Field(..., title="结束时间")
    desc = Field(..., title="组队描述")
    desc_img = Field(..., title="描述图片")


@router.post(team.add.value)
async def add_team(item: AddTeamItem, current_user: UserTable = Depends(get_current_user)):
    """
    创建团队
    """
    if current_user.id != item.user_id:
        return create_response(ret=1004, message='用户信息不匹配')

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
    if start_time < datetime.now():
        return create_response(ret=1004, message='开始时间需要大于当前时间')

    # 结束时间大于开始时间
    if item.end_time:
        end_time = datetime.strptime(item.end_time, "%Y-%m-%d %H:%M")
        if end_time < start_time:
            return create_response(ret=1004, message='结束时间需要大于开始时间')

    options = {
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
    }

    await TeamTable.create_team(options)

    return create_response(ret=0, data='', message='创建成功')
