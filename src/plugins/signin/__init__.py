from nonebot import on_command
from nonebot.adapters.qq import (
    Bot,
    GroupAtMessageCreateEvent,
    MessageSegment,
    Message
)
from nonebot.adapters.qq.message import MessageMarkdown
from nonebot.adapters.qq.models import MessageMarkdownParams
from nonebot.rule import to_me
from nonebot.matcher import Matcher
from src.utils import MsgText

# 绑定用户
bind = on_command("绑定", priority=9, block=True)

# 签到
sign = on_command("签到", priority=9, block=True)


@bind.handle()
async def bind_handle(matcher: Matcher, event: GroupAtMessageCreateEvent):
    """
    绑定指令的处理函数
    @type matcher: Matcher
    @type event: GroupAtMessageCreateEvent
    """
    print(event.json())
    # msg = MsgText(event.json())
    # print('--', msg)
    # await matcher.send(message=Message('test'))
    pass


@sign.handle()
async def to_say_handle(bot: Bot, matcher: Matcher, event: GroupAtMessageCreateEvent):
    """
    say 指令的处理函数
    :param bot:
    :param event:
    :return:
    """
    # msg = MessageSegment.markdown(
    #     MessageMarkdown(
    #         custom_template_id="102129847_1722007007",
    #         params=[
    #             MessageMarkdownParams(key='test', values=["签到不仅仅是一份任务，更是对自己的承诺。"])
    #         ],
    #     )
    # )
    # # sender = event.sender
    print(event.get_user_id())
    # print(event.get_session_id())
    # print(event.group_openid)
    #
    # await bot.send(event=event, message=Message(msg))
    pass
