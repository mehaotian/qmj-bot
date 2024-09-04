import os
import shutil
import sys
from datetime import datetime
import httpx
from nonebot.log import logger
from fastapi import APIRouter, Header, File, UploadFile, Query
import uuid
from ..utils.responses import create_response
from ..utils.tcb_cos import Cos, bucket, imgurl
from ..api import upload

client = Cos()
bucket = 'qmj-bot-1255788064'

router = APIRouter()

logger.success(f'Upload API 接口，加载成功')


@router.post(upload.api.value)
async def upload_image(type: int = Query(1, description="上传类型: 1-抽奖, 2-团队, 3-其他"),
                       token: str = Header(None, description="用户令牌"),
                       file: UploadFile = File(..., description="要上传的文件")):
    """
    上传图片接口

    参数:
    - type: 上传类型，1-抽奖相关, 2-团队相关, 3-其他
    - token: 用户认证令牌
    - file: 要上传的文件

    返回:
    - 成功: 返回上传成功的信息，包括文件名、图片URL、图片名称和ETag
    - 失败: 返回错误信息
    """

    try:
        # 生成唯一文件名
        short_uuid = str(uuid.uuid4())[:6]
        _, file_extension = os.path.splitext(file.filename)
        unique_filename = f"{short_uuid}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{file_extension}"

        # 验证文件类型
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        if file_extension.lower() not in allowed_extensions:
            return create_response(ret=1003, message='不支持的文件类型')

        # 验证文件大小（例如，限制为5MB）
        if file.file._file.tell() > 5 * 1024 * 1024:
            return create_response(ret=1004, message='文件大小超过限制')

        # 保存文件到临时目录
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_location = os.path.join(temp_dir, unique_filename)

        with open(temp_file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 根据类型确定上传路径
        upload_paths = {
            1: 'lottery/',
            2: 'team/',
            3: 'other/'
        }
        key = upload_paths.get(type, 'other/') + unique_filename

        # 上传文件到腾讯云 COS
        try:
            response = client.upload_file(
                Bucket=bucket,
                Key=key,
                LocalFilePath=temp_file_location,
                EnableMD5=False,
                progress_callback=upload_percentage,
            )
        except Exception as cos_error:
            logger.error(f"COS上传失败: {cos_error}")
            return create_response(ret=1005, message='COS上传失败')

        # 删除临时文件
        os.remove(temp_file_location)

        url = imgurl + '/' + key
        back_data = {
            "filename": file.filename,
            "img_url": url,
            "img_name": key,
            'ETag': response['ETag']
        }
        return create_response(ret=0, data=back_data, message='上传成功')

    except Exception as e:
        logger.error(f"上传过程中发生错误: {str(e)}")
        return create_response(ret=1001, data=str(e), message='上传失败')


def upload_percentage(consumed_bytes, total_bytes):
    """进度条回调函数，计算当前上传的百分比

    :param consumed_bytes: 已经上传的数据量
    :param total_bytes: 总数据量
    """
    if total_bytes:
        rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
        # print('\r{0}% '.format(rate))
        sys.stdout.flush()
