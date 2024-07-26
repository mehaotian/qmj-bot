import httpx
from nonebot.log import logger
from fastapi import APIRouter, Header
from pydantic import BaseModel

from src.models.user_model import UserTable
from ..utils.hashing import check_signature, decrypt_data

from ..utils.responses import create_response
from ..utils.security import get_token_data, get_user_data

from ..api import users

router = APIRouter()

logger.success(f'USER API 接口，加载成功')


class UserItem(BaseModel):
    code: str


@router.get(users.get_user.value)
async def userinfo(token: str = Header(None)):
    """
    获取用户信息
    """
    if not token:
        return create_response(ret=1002, message='用户 Token 不存在')

    user = get_user_data(token)

    return create_response(ret=0, data=user, message='获取用户信息成功')
