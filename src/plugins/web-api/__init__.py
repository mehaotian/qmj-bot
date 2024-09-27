import os
import nonebot
from nonebot.log import logger
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from nonebot.log import logger
from nonebot import require, get_driver
from starlette.middleware.cors import CORSMiddleware

require('nonebot_plugin_apscheduler')
from nonebot_plugin_apscheduler import scheduler
from .utils.responses import create_response

from .interface import (
    auth,
    user,
    upload,
    lottery,
    team,
    admin,
    xhh,
    system
)

config = get_driver().config
scheduler_db_url = config.scheduler_db_url

app: FastAPI = nonebot.get_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 自定义错误响应格式
    # create_response(ret=422, data=exc.errors(), message='请求参数验证失败')
    return JSONResponse(
        status_code=200,
        content={
            "ret": 422,
            "data": exc.errors(),
            "message": '请求参数验证失败'
        },
    )


# 注册鉴权信息
app.include_router(auth.router)

# 用户相关接口
app.include_router(user.router)

# 上传相关接口
app.include_router(upload.router)

# 抽奖相关接口
app.include_router(lottery.router)

# 组队相关接口
app.include_router(team.router)

# # 系统相关
# app.include_router(system.router)

# admin 接口
app.include_router(admin.router)

# 小黑盒接口
app.include_router(xhh.router)

logger.success('多功能群管WEB面板加载成功')

# 定时任务
try:
    scheduler.add_jobstore(SQLAlchemyJobStore(
        url=scheduler_db_url))
    logger.success('Jobstore 1持久化成功')
except Exception:
    logger.error('Jobstore 持久化失败')
    scheduler = None
