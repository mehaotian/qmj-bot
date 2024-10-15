import base64
import time

import httpx
from nonebot.log import logger
from fastapi import APIRouter, Header,Query
from pydantic import BaseModel
from Crypto.Cipher import AES

# 获取配置信息
from src.config import global_config

from src.models.user_model import UserTable
from ..utils.hashing import check_signature, decrypt_data

from ..utils.responses import create_response
from ..utils.security import get_token_data, get_user_data

from ..api import users
from nonebot import get_driver

config = get_driver().config
GoEasySecretKey = config.goeasysecretkey

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
            openid = jsondata['openid']
            session_key = jsondata['session_key']

            try:
                have_user = await UserTable.check_user(openid=openid)

                if not have_user:
                    user = await UserTable.create_user(openid=openid)
                else:
                    user = await UserTable.update_user(openid=openid,user_id=have_user.id)
                token_data = get_token_data(user_id=user.get("id"),session_key=session_key)
                token = token_data['token']

                user_data = {
                    "token": token
                }
                user_data.update({"id": user.get("id")})
                return create_response(data=user_data, message='success')
            except Exception as e:
                logger.error(f'创建用户失败：{e}')
                return create_response(ret=1001, message='创建用户失败')

    return create_response(ret=1002, message='code 不存在')


class UserItem(BaseModel):
    signature: str
    rawData: str
    iv: str
    encryptedData: str


@router.post(users.login.value)
async def loign(item: UserItem, token: str = Header(None)):
    """
    用户登录
    """
    if not token:
        return create_response(ret=1002, message='用户未登录')
    user = get_user_data(token)
    user_id = user.get('user_id')
    session_key = user.get('session_key')

    if check_signature(item.rawData, session_key, item.signature):
        try:
            user_info = decrypt_data(item.encryptedData, session_key, item.iv)
        except Exception as e:
            logger.error(e)
            return create_response(ret=1001, message='解密用户信息失败')

        # 验证用户是否存在
        # 这里主要是解决用户信息更新问题，有可能存储的token是错误的，但是仍然走有token的登录，这时候要更新
        user_data = await UserTable.get(id=user_id)

        user = await UserTable.update_user(
            user_id=user_data.id,
            nickname=user_info.get('nickName'),
            avatar=user_info.get('avatarUrl'),
        )
        return create_response(data=user, message='success')
    else:
        logger.error("数据签名验证失败")
        return create_response(ret=1001, message='数据签名验证失败')


@router.post(users.logout.value)
async def logout(token: str = Header(None)):
    """
    用户登出
    """
    if not token:
        return create_response(ret=1002, message='用户未登录')
    user = get_user_data(token)
    user_id = user.get('user_id')
    # 验证用户是否存在
    have_user = await UserTable.get(id=user_id)

    if not have_user:
        return create_response(ret=0, message='用户不存在')
    else:
        user = await UserTable.update_user(
            user_id=have_user.id
        )
        return create_response(data=user, message='success')


class GidItem(BaseModel):
    iv: str
    encryptedData: str


@router.post(users.bind_group.value)
async def bind_group(item: GidItem, token: str = Header(None)):
    """
    获取群gid
    参数：
        - item: GidItem
        - token: 用户token
    """
    if not token:
        return create_response(ret=1002, message='用户未登录')
    try:
        user = get_user_data(token)
        encrypted_data = item.encryptedData
        iv = item.iv
        session_key = user['session_key']

        try:
            group_info = decrypt_data(encrypted_data=encrypted_data, session_key=session_key, iv=iv)
        except Exception as e:
            logger.error(e)
            return create_response(ret=1001, message='解密群信息失败')

        return create_response(data=group_info, message='success')
    except Exception as e:
        logger.error(e)
        return create_response(ret=1001, message='获取群信息失败:' + str(e))


class UserItem(BaseModel):
    openid: str
    session_key: str
    nickname: str
    avatar: str


@router.post(users.create.value)
async def create_user(item: UserItem):
    """
    创建用户
    """
    openid = item.openid
    session_key = item.session_key


    have_user = await UserTable.check_user(openid=openid)

    if not have_user:
        user = await UserTable.create_user(openid=openid)


    have_user = await UserTable.check_user(openid=openid)


    user = await UserTable.update_user(
        user_id=have_user.id,
        nickname=item.nickname,
        avatar=item.avatar,
    )

    return create_response(data=user, message='success')


@router.post(users.ws_otp.value)
async def ws_otp(token: str = Header(None)):
    """
    获取 GoEasy-OTP
    """
    if not token:
        return create_response(ret=1002, message='用户未登录')
    key = GoEasySecretKey.encode('utf-8')
    otp = "000" + str(int(round(time.time() * 1000)))

    cipher = AES.new(key, AES.MODE_ECB)
    # 确保otp的长度是16的倍数
    otp = otp.encode('utf-8')
    encryptedOtp = cipher.encrypt(otp)
    encryptedOtp = base64.b64encode(encryptedOtp).decode('utf-8')
    return create_response(ret=0, data={"key": encryptedOtp}, message='获取 otp 成功')

@router.get(users.get_all.value)
async def get_all_user():
    """
    获取所有用户
    """
    users = await UserTable.all()
    return create_response(data=users, message='success')

@router.get(users.switch.value)
async def switch_user(user_id:int  = Query(..., gt=0, description="用户ID")):
    """
    切换用户,测试用，非正经接口
    """
    try:
        user = await UserTable.get(id=user_id)
        if not user:
             return create_response(ret=1001, message='用户不存在')
    except Exception as e:
        logger.error(e)
        return create_response(ret=1001, message='用户不存在')

    token_data = get_token_data(user_id=user.id,session_key='')
    # token = token_data['token']
    # user_data = {
    #     "token": token
    # }
    # user_data.update({"id": user.get("id")})
    return create_response(data=token_data, message='success')


@router.get('/')
async def root():
    user = get_user_data(
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcGVuaWQiOiI0NENEMDVDOUEzRUM2REE4NDFBNEVFMUM3RDhBOEVGQiIsImV4cCI6MTc0NzE4OTk4MCwic2Vzc2lvbl9rZXkiOiJjRlZwWnpWNlluWlljVEp4VDBRd2JnPT0ifQ.D--j-2mA1-mqpG3WLMAsdQ9Pc6bZAx1vVhHkCyBhGW0")
    encrypted_data = "yNtVzxH4HjTDLxI4TAQ57z1FfGeuNFp08Zgu5jZ32OT3V8hgq2Dfbrwww8DuGyI+ERGy0Qpe+HU5i5V+Jlbkvybk4l3wjOiXtMXtsKeTKIbkWuNxqRI02+05vtbq8woEJEfEre+vwwjZGjF0Mvrk0peYrt/7m05vsrPaU/ewSPg="
    iv = "M2U0MGZiNjU4ZGQ0NDYwNw=="
    session_key = "cFVpZzV6YnZYcTJxT0Qwbg=="

    userinfo = decrypt_data(encrypted_data=encrypted_data, session_key=session_key, iv=iv)
    return {"message": user, "userinfo": userinfo}
