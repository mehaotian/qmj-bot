from nonebot import on_command
from nonebot.adapters.qq import (
    Bot,
    GroupAtMessageCreateEvent,
    MessageSegment,
    Message
)
# from nonebot.adapters.qq.message import MessageMarkdown
# from nonebot.adapters.qq.models import MessageMarkdownParams
from nonebot.rule import to_me

# 定义一个指令，指令名称为 say，优先级为 9，阻塞为 True
say = on_command("签到", rule=to_me(), priority=9, block=True)


@say.handle()
async def to_say_handle(bot: Bot, event: GroupAtMessageCreateEvent):
    """
    say 指令的处理函数
    :param bot:
    :param event:
    :return:
    """
    # msg = MessageSegment.markdown(
    #     MessageMarkdown(
    #         custom_template_id="",
    #         params=[
    #             MessageMarkdownParams(key='title', values=['这是一个标题'])
    #         ],
    #     )
    # )
    # sender = event.sender
    print(event.get_event_description())

    await bot.send(event=event, message=Message('test'))
