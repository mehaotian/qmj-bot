import os
import nonebot
from nonebot.log import logger
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .utils.responses import create_response

from .interface import (
    auth,
    user,
    upload,
    lottery,
    system
)

app: FastAPI = nonebot.get_app()


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

# # 系统相关
# app.include_router(system.router)

logger.success('多功能群管WEB面板加载成功')
