from nonebot import logger

from src.models.involved_lottery_model import InvolvedLotteryTable
from src.models.lottery_model import LotteryTable
from src.models.prize_model import PrizeTable
from src.models.write_off_model import WriteOffTable
from src.utils.tools import Lottery
from .responses import create_response
from .goeasy import goeasy_send_message


async def scheduler_open_lottery(lottery_id: int, user_id: int):
    """
    开奖
    @param user_id:
    @param lottery_id:
    @return:
    """
    print('----- 开奖', lottery_id)
    try:
        # 验证抽奖信息
        check_data = await LotteryTable.check_lottery(lottery_id=lottery_id)
        if not check_data:
            logger.warning(f"尝试开奖的抽奖不存在，lottery_id: {lottery_id}")
            return create_response(ret=1004, message='抽奖不存在')

        if check_data.user_id != user_id:
            logger.warning(f"用户 {user_id} 尝试开启不属于自己的抽奖 {lottery_id}")
            return create_response(ret=1004, message='用户信息不匹配')

        if check_data.status == 2:
            logger.warning(f"尝试开启已结束的抽奖，lottery_id: {lottery_id}")
            return create_response(ret=1004, message='抽奖已结束')

        # 获取参与抽奖的用户列表
        list_data = await InvolvedLotteryTable.get_list(lottery_id=lottery_id)
        win_info = check_data.win_info or []

        win_info_arrs = [{"name": info, "value": ""} for info in win_info]

        users = list_data['items']
        users_copy = users.copy()

        # 获取奖品列表
        prize_data = await PrizeTable.get_list(lottery_id=lottery_id)

        # 执行开奖流程
        for prize in prize_data:
            lottery_tools = Lottery(users_copy)
            winners = lottery_tools.draw_winners(num_winners=prize["prize_count"])

            for winner in winners:
                for user in users_copy[:]:  # 使用切片创建副本进行迭代
                    if winner['user_id'] == user['user_id']:
                        # 创建奖品核销记录
                        await WriteOffTable.create_write_of({
                            "lottery_id": lottery_id,
                            "prize_id": prize['id'],
                            "user_id": winner['user_id'],
                            "write_off_info": win_info_arrs
                        })
                        users_copy.remove(user)
                        break

            # 更新中奖者状态
            winner_ids = [winner['user_id'] for winner in winners]
            await InvolvedLotteryTable.edit_winner_status(
                lottery_id=lottery_id,
                winner_ids=winner_ids,
                prize_id=prize['id']
            )

        # 更新未中奖者状态
        await InvolvedLotteryTable.edit_losers_status(lottery_id=lottery_id)

        # 更新抽奖状态为已结束
        await LotteryTable.filter(id=lottery_id).update(status=2)

        goeasy_content = {
            "lottery_id": lottery_id,
            "code": 200,
            "msg": "已开奖，中奖名单已公布，请刷新页面查看"
        }

        # 发送中奖消息
        goeasy_send_message(channel=f"onOpenLotteryMessage", content=goeasy_content)
        logger.info(f"抽奖 id: {lottery_id}, 开奖成功")
        return create_response(ret=0, data='', message='开奖成功')

    except Exception as e:
        logger.error(f'开奖过程中发生错误：{str(e)}')
        return create_response(ret=1001, data=str(e), message='开奖失败，请稍后重试')
