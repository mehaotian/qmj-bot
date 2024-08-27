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
from ..utils.tcb_cos import Cos, bucket, imgurl
from ..api import upload

client = Cos()
bucket = 'qmj-bot-1255788064'
response = client.list_objects(Bucket='qmj-bot-1255788064')

print('upload.py', response)
router = APIRouter()

logger.success(f'Upload API 接口，加载成功')


@router.post(upload.api.value)
async def upload_image(token: str = Header(None), file: UploadFile = File(...)):
    """
    上传图片
    """

    try:

        # 生成一个短 UUID（前 8 个字符）
        # 获取文件扩展名
        # 生成唯一的文件名
        short_uuid = str(uuid.uuid4())[:6]
        _, file_extension = os.path.splitext(file.filename)
        unique_filename = f"{short_uuid}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{file_extension}"
        # if not token:
        #     return create_response(ret=1002, message='用户 Token 不存在')
        # 将上传的文件保存到本地临时目录
        temp_file_location = os.path.join("temp", file.filename)
        os.makedirs(os.path.dirname(temp_file_location), exist_ok=True)
        with open(temp_file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 上传的key
        key = 'lottery/' + unique_filename

        # 上传文件到腾讯云 COS
        response = client.upload_file(
            Bucket=bucket,
            Key=key,
            LocalFilePath=temp_file_location,
            EnableMD5=False,
            progress_callback=upload_percentage,

        )

        # 删除本地临时文件
        os.remove(temp_file_location)
        url = imgurl + '/' + key
        # return
        back_ata = {"filename": file.filename, "img_url": url, "img_name": key, 'ETag': response['ETag']}
        return create_response(ret=0, data=back_ata, message='上传成功')
    except Exception as e:
        print(e)
        return create_response(ret=1001, data=str(e), message='上传失败')


def upload_percentage(consumed_bytes, total_bytes):
    """进度条回调函数，计算当前上传的百分比

    :param consumed_bytes: 已经上传的数据量
    :param total_bytes: 总数据量
    """
    if total_bytes:
        rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
        print('\r{0}% '.format(rate))
        sys.stdout.flush()
