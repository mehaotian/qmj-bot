from datetime import datetime

from nonebot.log import logger
from fastapi import APIRouter, Header, HTTPException
from pycparser.ply.yacc import token
from pydantic import BaseModel, Field
from src.models.admin_user_model import AdminUserTable
from ..utils.admin_auth import get_pwd_hash, verify_password, get_user_data, get_current_user
from ..utils.responses import create_response, create_page_response
from ..api import admin

router = APIRouter()

logger.success(f'ADMIN API 接口，加载成功')


class UserItem(BaseModel):
    username: str = Field(..., min_length=1, max_length=100, description="用户名")
    password: str = Field(..., min_length=1, max_length=150, description="密码")
    roles: list[str] = Field(..., description="角色列表")
    realName: str = Field(..., min_length=1,
                          max_length=10, description="真实姓名")


@router.post(admin.register.value)
async def admin_register(user: UserItem):
    """
    注册新管理员用户

    参数:
    - item: UserItem 对象，包含用户名、密码、角色列表和真实姓名

    返回:
    - 成功: 返回注册成功的用户信息
    - 失败: 返回错误信息
    """
    try:
        username = user.username
        # 判断用户长度
        if len(username) < 5 or len(username) > 20:
            return create_response(ret=1001, message='用户名长度必须在5-20之间')

        # 判断用户是否存在
        have_user = await AdminUserTable.check_user(username=username)
        if have_user:
            return create_response(ret=1001, message='用户已存在')

        password = user.password
        # 密码最少 6 位
        if len(password) < 6 or len(username) > 20:
            return create_response(ret=1001, message='密码长度必须在6-20之间')

        pwd = get_pwd_hash(user.password)

        real_name = user.realName
        # 判断真实姓名长度
        if len(real_name) < 2 or len(real_name) > 10:
            return create_response(ret=1001, message='真实姓名长度必须在2-10之间')
        userinfo = {
            'username': username,
            'password': pwd,
            'roles': user.roles,
            'realName': real_name
        }
        # 创建用户
        registered_user = await AdminUserTable.create_user(data=userinfo)

        return create_response(ret=0, data=registered_user, message='用户注册成功')
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        return create_response(ret=1001, message='用户注册失败，请稍后重试')


class LoginItem(BaseModel):
    username: str = Field(..., min_length=1, max_length=100, description="用户名")
    password: str = Field(..., min_length=1, max_length=150, description="密码")


@router.post(admin.login.value)
async def admin_login(user: LoginItem):
    """
    管理员登录
    入参
        - code: 登录凭证
    """
    # try:
    username = user.username
    password = user.password
    # 判断用户长度
    if len(username) < 5 or len(username) > 20:
        return create_response(ret=1001, message='用户名长度必须在5-20之间')

    # 密码最少 6 位
    if len(password) < 6 or len(username) > 20:
        return create_response(ret=1001, message='密码长度必须在6-20之间')
    # 判断用户是否存在
    have_user = await AdminUserTable.get_or_none(username=username)
    print(have_user)
    if not have_user:
        return create_response(ret=1001, message='用户不存在')

    if not verify_password(password, have_user.password):
        return create_response(ret=1001, message='密码错误')
    login_data = get_user_data(user=have_user)

    return create_response(ret=0, data=login_data, message='用户登录成功')
    # except Exception as e:
    #     logger.error(f"用户登录失败: {str(e)}")
    #     return create_response(ret=1001, message='用户登录失败，请稍后重试')


@router.get(admin.userinfo.value)
async def get_user_info(authorization: str = Header(None)):
    """
    获取用户信息
    """


    token_data = await get_current_user(authorization)
    if not token_data:
        return create_response(ret=1001, message='用户不存在')

    print(token_data.exp , datetime.now().timestamp() ,token_data.exp < datetime.now().timestamp())
    # 登录过期
    if token_data.exp < datetime.now().timestamp():
        raise HTTPException(status_code=401, detail="用户未登录，或登录过期")


    user_id = token_data.user_id
    username = token_data.username
    user = await AdminUserTable.get_user(user_id)

    if not user:
        return create_response(ret=1001, message='用户不存在')

    return create_response(ret=0, data=user, message='获取用户信息成功')

@router.post(admin.logout.value)
async def admin_logout():
    """
    退出登录
    """
    return create_response(ret=0, message='退出登录成功')