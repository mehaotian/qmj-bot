import httpx
from nonebot.log import logger
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates
from src.utils.tools.xhh_box import search_game
from src.utils.xhh_sdk import Xhh
from ..api import xhh

router = APIRouter()

logger.success(f'XHH API 接口，加载成功')

templates = Jinja2Templates(directory="./src/plugins/web-api/templates")


def get_detail(steam_appid: str):
    if not steam_appid:
        return None
    game_detail = Xhh.game_detail(steam_appid=steam_appid)
    game_data = game_detail["result"]

    game_type = game_data.get("game_type", "")
    types = game_data.get("type", "")
    result = {}
    if game_type == 'pc' and types == 'game':
        # 中文游戏名称
        result['name'] = game_data.get("name", "")
        # 英文游戏
        name_en = game_data.get("name_en", "")
        if name_en:
            result['name_en'] = name_en.split('-')[0].strip()

        # 评分
        result['score'] = game_data.get("score", 0)
        # 平台
        result['platform'] = game_data.get("platf", "")

        # 标签
        common_tags = game_data.get("common_tags", [])
        # 筛选分类标签 type = simple_tag
        simple_tags = [tag for tag in common_tags if tag.get("type", "") == "simple_tag"]
        result['tags'] = [tag.get("desc", "") for tag in simple_tags]

        # 玩家统计
        user_num = game_data.get("user_num", 0)
        user_game_data = user_num.get("game_data", {})
        # 从 user_game_data 数组中 获取 desc = "Steam好评率" 的一条数据
        steam_score = [item for item in user_game_data if item.get("desc", "") == "Steam好评率"]
        # 获取评分
        result['steam_score'] = steam_score[0].get("value", "") if steam_score else ""

        # 厂商信息
        menu_v2 = game_data.get("menu_v2", [])
        # 发布时间
        release_date = [item for item in menu_v2 if item.get("type", "") == "release_date"]
        result['release_date'] = release_date[0].get("value", "") if release_date else ""
        # 发行商
        publisher = [item for item in menu_v2 if item.get("type", "") == "publisher"]
        result['publisher'] = publisher[0].get("value", "") if publisher else ""
        # 开发商
        developer = [item for item in menu_v2 if item.get("type", "") == "developer"]
        result['developer'] = developer[0].get("value", "") if developer else ""
        # Metacritic评分
        mscore = [item for item in menu_v2 if item.get("type", "") == "mscore"]
        result['mscore'] = mscore[0].get("value", "") if mscore else ""

        # 获取成就
        game_award = game_data.get("game_award", [])
        result['game_award'] = game_award

        # 黑盒五项
        multidimensional_score_radar = game_data.get("multidimensional_score_radar", {})
        dimension_list = multidimensional_score_radar.get("dimension_list", [])
        result['dimension_list'] = dimension_list

        return result

    return {}


@router.get(xhh.game.value, response_class=HTMLResponse)
async def game(q: str):
    if not q:
        return HTMLResponse(content='请输入搜索关键词')

    page_result = Xhh.search(q)

    result_list = page_result["result"]['items']
    results = []
    for item in result_list:
        game_type = item["type"]
        game_info = item["info"]
        if game_type == 'game':
            results.append(game_info)

    template_text = '<div style="padding:50px;">'
    for game_item in results:
        try:
            # steam_appid
            steam_appid = game_item.get("steam_appid", "")
            game_data = get_detail(steam_appid)
        except KeyError:
            game_data = None

        if not game_data:
            continue

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

        # 游戏名字
        name_en = game_data.get("name_en", "")
        if name_en:
            name_en_str = f'({name_en})'
        template_text += f'<h3>{game_item.get("name", "-")}{name_en_str}</h3>'

        # 游戏图片
        template_text += f'<div class="img"><img style="width:300px;" src="{game_item.get("image", "")}"></div>'

        # 游戏图片 无logo水印
        libary_background = game_item.get("libary_background", "")
        # 无logo水印图片
        template_text += f'<div class="img" style="display:none;"><img style="width:300px;" src="{libary_background}"></div>'

        template_text += '<button id style="margin-top:10px;">切换图片</button>'

        # 游戏好评
        steam_score = game_data.get("steam_score", "")
        if steam_score:
            steam_score_str = f'({steam_score})'

        # 游戏评分
        template_text += f'<p style="color:red;">评分: <b style="font-size:18px;">{score}</b>{steam_score_str}</p>'

        # 地区
        region_name = price.get("region_name", "")
        if region_name:
            template_text += f'<p>地区: {region_name}</p>'
        # 平台
        platform = game_data.get("platform", "")
        if platform:
            template_text += f'<p>平台: {platform}</p>'

        # 类型
        tags = game_data.get("tags", [])
        if tags:
            template_text += f'<p>类型: {"/".join(tags)}</p>'

        # 发布日期
        release_date = game_data.get("release_date", "")
        if release_date:
            template_text += f'<p>发布日期: {release_date}</p>'
        # 发行开发商
        publisher = game_data.get("publisher", "")
        developer = game_data.get("developer", "")
        if publisher:
            template_text += f'<p>发行商: {publisher}</p>'
        if developer:
            template_text += f'<p>开发商: {developer}</p>'

        # Metacritic评分
        mscore = game_data.get("mscore", "")
        if mscore:
            template_text += f'<p>Metacritic评分: {mscore}</p>'

        # 奖项
        game_award = game_data.get("game_award", [])
        if game_award:
            game_award_texts = []
            for award in game_award:
                if award.get("desc", "") and award.get("name", "detail_name"):
                    game_award_text = f'{award.get("desc", "")} - {award.get("detail_name", "")}'
                    game_award_texts.append(game_award_text)
            template_text += f'<p>奖项: {"/".join(game_award_texts)}</p>'

        # 黑盒五项
        dimension_list = game_data.get("dimension_list", [])
        if dimension_list:
            dimension_texts = []
            for dimension in dimension_list:
                if dimension.get("dimension_name", "") and dimension.get("score", ""):
                    dimension_text = f'{dimension.get("dimension_name", "")}: {dimension.get("score", "")}'
                    dimension_texts.append(dimension_text)
            template_text += f'<p>印象评分: {"/".join(dimension_texts)}</p>'

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


@router.get('/xhh/game2')
async def game_test(id: str):
    page_result = Xhh.game_detail(steam_appid=id)
    # result_list = page_result["result"]['items']

    return page_result


@router.get('/xhh/game/{name}')
async def xhh_index(request: Request,name:str):
    if not name:
        return HTMLResponse(content='请输入搜索关键词')

    page_result = Xhh.search(name)

    result_list = page_result["result"]['items']
    results = []
    for item in result_list:
        game_type = item["type"]
        game_info = item["info"]

        # 黑盒价格
        heybox_price = game_info.get("heybox_price", {})
        # steam 价格
        price = game_info.get("price", {})
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

        game_info['initial'] = price.get("initial", 0)
        game_info['current'] = price.get("current", 0)
        game_info['is_free'] = is_free
        game_info['discount'] = discount
        game_info['cost_coin'] = cost_coin
        game_info['is_lowest'] = is_lowest
        game_info['new_lowest'] = new_lowest
        game_info['lowest_price'] = lowest_price


        if game_type == 'game':
            try:
                # steam_appid
                steam_appid = game_info.get("steam_appid", "")
                game_data = get_detail(steam_appid)
            except KeyError:
                game_data = None

            if game_data:
                # game_info['game_data'] = game_data
                # game_data 展开到 game_info
                game_info.update(game_data)
                results.append(game_info)

    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "data": results})
