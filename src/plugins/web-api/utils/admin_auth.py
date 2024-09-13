from typing import Union
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from passlib.context import CryptContext
from datetime import datetime, timedelta
# from app.models.user import User
from jose import JWTError, jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "91ff62b8c69635ed8338de0199c6da5f7c9b65d1c029daaa1c1cb8c62ff1fa00"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# 一个月过期
REFRESH_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

refresh_token_expires = timedelta(minutes=REFRESH_ACCESS_TOKEN_EXPIRE_MINUTES)


class TokenData(BaseModel):
    """令牌数据"""
    username: Union[str, None] = None
    user_id: Union[int, None] = None


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# async def get_user(username):
#     """获取用户"""
#     existing_user = await User.get_or_none(username=username)
#     return existing_user


def get_pwd_hash(password):
    """获取密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_user_data(user):
    """获取用户数据"""
    access_token: str = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
    )

    refresh_token: str = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=refresh_token_expires
    )
    return {
        "uid": user.id,
        "username": user.username,
        "accessTokenExpires": int(access_token_expires.total_seconds()),
        "refreshToken": refresh_token,
        "accessToken": access_token,
        "tokenType": "bearer",
        "roles": user.roles
    }


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    # try:
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="无效的授权头部")

    token = token[len("Bearer "):]  # 去掉 Bearer 前缀
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    if username is None:
        raise HTTPException(status_code=400, detail="未找到用户")
    return TokenData(username=username,user_id=user_id)
    # except JWTError:
    #     raise HTTPException(status_code=400, detail="未找到用户")

# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     """获取当前用户"""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except JWTError:
#         raise credentials_exception
#     user = await get_user(username=token_data.username)
#     if user is None:
#         raise credentials_exception
#
#     return User(**user.to_dict())


# async def get_current_active_user(current_user: User = Depends(get_current_user)):
#     """获取当前活动用户"""
#     if current_user.status != 1:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user


# async def authenticate_user(fake_db):
#     password = fake_db.password
#     username = fake_db.username
#     """验证用户"""
#     user = await get_user(fake_db.username)
#     if not user:
#         return False
#
#     if not verify_password(password, user.password):
#         return False
#     return user
