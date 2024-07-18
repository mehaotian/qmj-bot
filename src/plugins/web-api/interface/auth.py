import httpx
from nonebot.log import logger
from fastapi import APIRouter, Header
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
        return create_response(ret=1002, message='用户 Token 不存在')

    user = get_user_data(token)
    openid = user.get('openid')
    session_key = user.get('session_key')

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
        logger.error("数据签名验证失败")
        return create_response(ret=1001, message='数据签名验证失败')


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
        return create_response(ret=1002, message='用户 Token 不存在')
    try:
        user = get_user_data(token)
        encrypted_data = item.encryptedData
        iv = item.iv
        session_key = user['session_key']

        print('encrypted_data', encrypted_data)
        print('iv', iv)
        print('session_key', session_key)

        group_info = decrypt_data(encrypted_data=encrypted_data, session_key=session_key, iv=iv)

        return create_response(data=group_info, message='success')
    except Exception as e:
        logger.error(e)
        return create_response(ret=1001, message='获取群信息失败:'+str(e))


@router.get('/')
async def root():
    user = get_user_data(
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcGVuaWQiOiI0NENEMDVDOUEzRUM2REE4NDFBNEVFMUM3RDhBOEVGQiIsImV4cCI6MTc0NzE4OTk4MCwic2Vzc2lvbl9rZXkiOiJjRlZwWnpWNlluWlljVEp4VDBRd2JnPT0ifQ.D--j-2mA1-mqpG3WLMAsdQ9Pc6bZAx1vVhHkCyBhGW0")
    encrypted_data = "yNtVzxH4HjTDLxI4TAQ57z1FfGeuNFp08Zgu5jZ32OT3V8hgq2Dfbrwww8DuGyI+ERGy0Qpe+HU5i5V+Jlbkvybk4l3wjOiXtMXtsKeTKIbkWuNxqRI02+05vtbq8woEJEfEre+vwwjZGjF0Mvrk0peYrt/7m05vsrPaU/ewSPg="
    iv = "M2U0MGZiNjU4ZGQ0NDYwNw=="
    session_key = "cFVpZzV6YnZYcTJxT0Qwbg=="

    userinfo = decrypt_data(encrypted_data=encrypted_data, session_key=session_key, iv=iv)
    return {"message": user, "userinfo": userinfo}
