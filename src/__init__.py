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
    openid = str(event.group_openid)
    group_openid = config.groups_openid
    print(group_openid)
    if group_openid and openid in group_openid :
        raise IgnoredException("信息已经忽略")