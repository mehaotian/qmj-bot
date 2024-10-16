from enum import Enum


# 接口枚举
class Urls(Enum):
    # 文章列表
    links = "/bbs/web/profile/post/links"
    link_detial = "/bbs/app/api/share/data"
    game_list = '/game/get_game_list_v3'
    search = '/bbs/app/api/general/search/v1'
