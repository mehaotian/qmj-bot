import httpx
from nonebot.log import logger
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from ..utils.responses import create_response
from src.utils.tools.xhh_box import search_game
from ..api import xhh

router = APIRouter()

logger.success(f'XHH API 接口，加载成功')


#
@router.get(xhh.game.value, response_class=HTMLResponse)
async def game(q: str):

    if not q:
        return HTMLResponse(content='请输入搜索关键词')

    page_result = search_game(q)
    result_list = page_result["result"]['items']

    results = []
    for item in result_list:
        game_type = item["type"]
        game_info = item["info"]
        if game_type == 'game':
            results.append(game_info)

    game_lists = []
    template_text = '<div style="padding:50px;">'
    for game_item in results:
        template_text += '<div style="font-size:14px;">'
        # 黑盒价格
        heybox_price = game_item.get("heybox_price", {})
        # steam 价格
        price = game_item.get("price", {})
        # 黑盒折扣信息
        coupon_info = heybox_price.get("coupon_info", {})
        # 当前折扣
        discount = price.get("discount", "0") or heybox_price.get("discount", "0")

        # 是否免费
        is_free = price.get("is_free", False)
        # 折扣计算
        cost_coin = 0
        if coupon_info.get('type', 0) == 2:
            cost_coin = round(heybox_price.get("cost_coin", 0) / 1000 - coupon_info.get("value", 0), 2)
        if coupon_info.get('type', 0) == 4:
            cost_coin = round((heybox_price.get("cost_coin", 0) / 1000) * (coupon_info.get("value", 0) / 100), 2)

        # 是否史低， is_lowest = 1 为史低
        is_lowest = heybox_price.get("is_lowest", 0) == 1 or price.get("is_lowest", 0) == 1
        # 是否新史低 new_lowest = 1 为新史低
        new_lowest = price.get("new_lowest", 0) == 1 or heybox_price.get("new_lowest", 0) == 1

        # 史低价格
        lowest_price = price.get("lowest_price", '0')

        # 评分
        score = game_item.get("score", 0)
        # 地区
        region_name = price.get("region_name", "")

        # 游戏名字
        template_text += f'<h1>{game_item.get("name", "-")}</h1>'
        # 游戏图片
        template_text += f'<div><img style="width:300px;" src="{game_item.get("image", "")}"></div>'
        # 游戏评分
        template_text += f'<p style="color:red;">评分: <b style="font-size:18px;">{score}</b></p>'
        # 地区
        if region_name:
            template_text += f'<p>地区: {region_name}</p>'
        if not is_free:
            # 游戏原价
            template_text += f'<p>原价: {price.get("initial", 0)}元</p>'
            # 游戏现价
            template_text += f'<p>当前价: {price.get("current", 0)}元</p>'
            # 券后价格
            template_text += f'<p>券后价格: {cost_coin}元</p>'
            # 折扣
            template_text += f'<p>折扣: {discount}%</p>'
            # 史低价格
            template_text += f'<p>史低价格: {lowest_price}元</p>'
            # 是否史低
            template_text += f'<p>是否史低: {"是" if is_lowest else "否"}</p>'
            # 是否新史低
            template_text += f'<p>是否新史低: {"是" if new_lowest else "否"}</p>'
        else:
            template_text += f'<p>原价: 免费</p>'

        template_text += '</div>'

    template_text += '</div>'

    return HTMLResponse(content=template_text)


@router.get('/xhh/game1')
async def game_test(q: str):
    page_result = search_game(q)
    # result_list = page_result["result"]['items']

    return page_result
