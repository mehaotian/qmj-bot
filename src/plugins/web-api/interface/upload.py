import os
import shutil
from datetime import datetime
from distutils.command.upload import upload

import httpx
from nonebot.log import logger
from fastapi import APIRouter, Header, File, UploadFile
from pydantic import BaseModel
import uuid
from ..utils.responses import create_response
from ..utils.tcb_cos import Cos, bucket
from ..api import upload

client = Cos()
bucket = 'qmj-bot-1255788064'
response = client.list_objects(Bucket='qmj-bot-1255788064')

print('upload.py', response)
router = APIRouter()

logger.success(f'Upload API 接口，加载成功')


@router.post(upload.api.value)
async def userinfo(token: str = Header(None), file: UploadFile = File(...)):
    """
    获取用户信息
    """
    # 生成一个短 UUID（前 8 个字符）
    short_uuid = str(uuid.uuid4())[:6]
    # 获取文件扩展名
    _, file_extension = os.path.splitext(file.filename)
    # 生成唯一的文件名
    unique_filename = f"{short_uuid}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{file_extension}"
    # if not token:
    #     return create_response(ret=1002, message='用户 Token 不存在')
    # 将上传的文件保存到本地临时目录
    temp_file_location = os.path.join("temp", file.filename)
    os.makedirs(os.path.dirname(temp_file_location), exist_ok=True)
    with open(temp_file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 上传文件到腾讯云 COS
    with open(temp_file_location, "rb") as fp:
        # 按当前时间戳重命名文件

        response = client.upload_file(
            Bucket=bucket,
            Key='lottery/' + unique_filename,
            LocalFilePath=temp_file_location,
            EnableMD5=False,
            progress_callback=None

        )

    # 删除本地临时文件
    os.remove(temp_file_location)

    return {"filename": file.filename, "cos_response": unique_filename}
