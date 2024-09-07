import json

import requests
from requests.structures import CaseInsensitiveDict
from nonebot import get_driver, logger

config = get_driver().config
restkey = config.goeasyrestapikey
url = config.goeasyrestapiurl

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"
headers["Content-Type"] = "application/json"


def goeasy_send_message(channel: str, content: dict):
    # 将content转换为JSON字符串
    content_json = json.dumps(content)
    data = {
        "appkey": restkey,
        "channel": channel,
        "content": content_json
    }
    
    # 将整个data转换为JSON字符串
    data_json = json.dumps(data)
    
    resp = requests.post(url, headers=headers, data=data_json)
    
    if resp.status_code == 200:
        logger.success(f'GoEasy消息发送成功: {content_json}')
    else:
        logger.error(f'GoEasy消息发送失败: {content_json}')
        logger.error(f'错误信息: {resp.text}')
