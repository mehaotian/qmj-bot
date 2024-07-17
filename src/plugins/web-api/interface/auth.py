import httpx
from nonebot.log import logger
from fastapi import APIRouter
from pydantic import BaseModel
# 获取配置信息
from src.config import global_config

from src.models.user_model import UserTable
from ..utils.hashing import check_signature, decrypt_data

from ..utils.responses import create_response
from ..utils.security import get_token_data, get_user_data

from ..api import users

router = APIRouter()

logger.success(f'USER API 接口，加载成功')


class QQAuth(BaseModel):
    code: str


@router.post(users.qqauth.value)
async def qq_auth(item: QQAuth):
    """
    qq小程序登录，code换取session_key
    入参
        - code: 登录凭证
    """

    if item.code:
        appid = global_config.qq_appid
        secret = global_config.qq_secret
        url = f'https://api.q.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={item.code}&grant_type=authorization_code'
        res = httpx.get(url)
        try:
            jsondata = res.json()
        except httpx.HTTPStatusError as e:
            jsondata = None

        if jsondata:
            print(jsondata)
            openid = jsondata['openid']
            session_key = jsondata['session_key']
            token_data = get_token_data(openid=openid, session_key=session_key)
            token = token_data['token']
            try:
                have_user = await UserTable.check_user(openid=openid)
                user_data = {
                    "token": token
                }
                if not have_user:
                    user = await UserTable.create_user(openid=openid, token=token)
                    print('创建用户成功')
                else:
                    user = await UserTable.update_token(openid=openid, token=token)
                    print('更新用户成功')

                user_data.update({"id": user.id})

                return create_response(data=user_data, message='success')
            except Exception as e:
                logger.error(f'创建用户失败：{e}')
                return create_response(ret=1, message='创建用户失败')

    return create_response(ret=1, message='error')


class UserItem(BaseModel):
    signature: str
    rawData: str
    token: str
    iv: str
    encryptedData: str


@router.post(users.login.value)
async def loign(item: UserItem):
    """
    用户登录
    """

    user = get_user_data(item.token)
    openid = user.get('openid')
    session_key = user.get('session_key')
    print('session_key:', session_key)

    if check_signature(item.rawData, session_key, item.signature):
        user_info = decrypt_data(item.encryptedData, session_key, item.iv)
        user = await UserTable.update_user(
            openid=openid,
            nickname=user_info.get('nickName'),
            avatar=user_info.get('avatarUrl'),
        )
        print(user)
        return create_response(data=user, message='success')
    else:
        print("数据签名验证失败")
        return create_response(ret=1, message='error')


# @router.post(users.get_user.value)
# async def get_user(item: UserItem):
#     """
#     获取用户信息
#     """
#     if check_signature(item.rawData, item.session_key, item.signature):
#         user_info = decrypt_data(item.encryptedData, item.session_key, item.iv)
#         return create_response(data=user_info, message='success')
#     else:
#         print("数据签名验证失败")
#         return create_response(ret=1, message='error')


@router.get('/')
async def root():
    # user = get_user_data("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXNzaW9uX2tleSI6ImIwRnhiVEZ6TldGWFNYbGxkMk16Vnc9PSIsIm9wZW5pZCI6IjQ0Q0QwNUM5QTNFQzZEQTg0MUE0RUUxQzdEOEE4RUZCIiwiZXhwIjoxNzIxMjMzMTAwfQ.FsRNMtwrIvinYioaC7ZLqbcDx-JtvrQqGhh1nPwjaEM")
    return {"message": 'Not Found'}
