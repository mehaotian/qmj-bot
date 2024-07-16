
import nonebot
from nonebot.adapters.qq import Event
from nonebot.exception import IgnoredException
from nonebot.message import run_preprocessor
@run_preprocessor
async def ignore_prod(event: Event):
    """
    全局预处理函数,忽略线上指定群组的消息
    """
    config = nonebot.get_driver().config
    group_openid = str(event.group_openid)
    # 沙盒群 喵叽bot测试群的 群 openid
    openid ='DD6D90FACAD2176FE8E2C1247828B0B0'

    if group_openid == openid and config.environment == 'prod':
        raise IgnoredException("信息已经忽略")