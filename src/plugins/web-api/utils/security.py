from typing import Union
from fastapi.security import OAuth2PasswordBearer

from passlib.context import CryptContext
from jose import JWTError, jwt

from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "91ff62b8c69635ed"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# 一个月过期
REFRESH_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)


def get_token_data(openid: str, session_key: str):
    """
    获取用户数据
    """
    access_token: str = create_access_token(
        data={"openid": openid},
        expires_delta=access_token_expires,
        session_key=session_key
    )

    return {
        "token": access_token,
        "token_type": "bearer",
    }


def get_user_data(token: str):
    """
    同意token获取用户数据
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None, session_key: str = ''):
    """
    创建访问令牌
    参数:
        - data: 数据
        - expires_delta: 过期时间
        - openid: 用户唯一标识
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    to_encode.update({"session_key": session_key})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
