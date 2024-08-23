import json
from typing import Optional, Union
import httpx
import os
import re
from datetime import datetime, timedelta

import nonebot
from nonebot.adapters.qq import (
    Bot,
    MessageSegment,
    Message,
)

from io import BytesIO
from nonebot.log import logger
from PIL import Image
from ..config import cache_directory


def json_load(path) -> Optional[dict]:
    """
    加载json文件
    :return: Optional[dict]
    """
    try:
        with open(path, mode='r', encoding='utf-8') as f:
            contents = json.load(f)
            return contents
    except FileNotFoundError:
        return None


def json_upload(path, dict_content) -> None:
    """
    更新json文件
    :param path: 路径
    :param dict_content: python对象，字典
    """
    with open(path, mode='w', encoding='utf-8') as c:
        c.write(json.dumps(dict_content, ensure_ascii=False, indent=4))


def download_image(url, cache_path):
    """
    下载文件并缓存
    """
    # 如果缓存目录不存在，则创建
    if not os.path.exists(cache_directory):
        os.makedirs(cache_directory)

    if os.path.exists(cache_path):
        logger.debug(f"缓存文件已存在: {cache_path}")
        # 如果缓存文件已存在，直接加载并返回
        with open(cache_path, "rb") as file:
            return Image.open(BytesIO(file.read()))
    else:
        logger.debug(f"缓存文件不存在: {cache_path}")
        # 否则下载远程图片，并保存到缓存目录
        response = httpx.get(url)
        if response.status_code == 200:
            with open(cache_path, "wb") as file:
                file.write(response.content)
            return Image.open(BytesIO(response.content))
        else:
            # 处理下载失败的情况
            return None


def At(data: str) -> Union[list[str], list[int], list]:
    """
    检测at了谁，返回[qq, qq, qq,...]
    包含全体成员直接返回['all']
    如果没有at任何人，返回[]
    :param data: event.json
    :return: list
    """
    try:
        qq_list = []
        data = json.loads(data)
        for msg in data['message']:
            if msg['type'] == 'at':
                if 'all' not in str(msg):
                    qq_list.append(int(msg['data']['qq']))
                else:
                    return ['all']
        return qq_list
    except KeyError:
        return []


def MsgText(data: str):
    """
    返回消息文本段内容(即去除 cq 码后的内容)
    :param data: event.json()
    :return: str
    """
    data = json.loads(data)
    pattern = r'/([\w\u4e00-\u9fa5]+)\s+(.+)'
    command = data['content'].strip()
    match = re.match(pattern, command)
    if match:
        command_name = match.group(1)
        params = match.group(2).split()
        return command_name, params
    return None, []


def Reply(data: str):
    """
    检测回复哪条消息，返回 reply 对象
    如果没有回复任何人，返回 None
    :param data: event.json()
    :return: dict | None
    """
    try:
        data = json.loads(data)
        if data['reply'] and data['reply']['message_id']:  # 待优化
            return data['reply']
        else:
            return None
    except KeyError:
        return None
