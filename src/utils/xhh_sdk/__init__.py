import requests
import json
from urllib.parse import urlencode
from .auth import XhhAuth

# 其他必需的配置项，不了解的话请勿乱改
s_request = requests.session()
proxies = {}
header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.xiaoheihe.cn/",
}


class Xhh():
    url = "https://api.xiaoheihe.cn"

    # 文章列表
    links_text = "/bbs/web/profile/post/links"
    # 文章详情
    link_detial_text = "/bbs/app/api/share/data"
    # 评论列表
    game_list_text = '/game/get_game_list_v3'
    # 搜索
    search_text = '/bbs/app/api/general/search/v1'
    # 游戏详情
    game_detail_text = '/game/get_game_detail'

    def __init__(self):
        pass
        # self.auth = XhhAuth()

    def request(self, url: str, headers=None, cookie=None):
        """
        请求
        @param headers:
        @param cookie:
        @return:
        """

        try:
            content = s_request.get(url, headers=headers, cookies=cookie, timeout=4)
        except Exception:
            content = s_request.get(url, headers=headers, cookies=cookie, proxies=proxies, timeout=4)
        return content
    @classmethod
    def dict_to_query_string(cls,params: dict, text_url: str) -> str:
        """
        将字典转换为 URL 查询参数格式
        :param params: 要转换的字典
        :return: 转换后的查询参数字符串
        """

        obj = XhhAuth.create_sign(text_url)
        baseQuery = {
            "client_type": "heybox_chat",
            "x_client_type": "web",
            "os_type": "web",
            "x_os_type": "Windows",
            "device_info": "Chrome",
            "x_app": "heybox_chat",
            "version": "999.0.3",
            "web_version": "1.0.0",
            "chat_os_type": "web",
            "chat_version": "1.24.4",
            "chat_exe_version": "",
            "heybox_id": "36331242",
            "hkey": obj["hkey"],
            "_time": obj["_time"],
            "nonce": obj["nonce"],
            "imei": "58dcf9f48bba35a0",
            "build": "783"
        }

        params.update(baseQuery)

        # 使用 urllib.parse.urlencode 将字典转换为查询参数字符串
        query_string = urlencode(params)
        return f"?{query_string}"

    def get_url(self, text: str, data: dict):
        """
        获取请求地址
        @param text:
        @return:
        """
        query_string = self.dict_to_query_string(data, text)
        return f'{self.url}{text}{query_string}'

    @classmethod
    def search(cls, q: str):
        """
        搜索
        @param q:
        @return:
        """
        interface = cls()
        url = cls.get_url(cls, cls.search_text, {
            "q": q,
            "search_type": "game",
            "game_type": "pc",
            "limit": 20,
            "offset": 0,
            "time_range": "",
            "sort_filter": "sort_filter",
        })
        json_page = json.loads(interface.request(url).text)

        return json_page

    @classmethod
    def game_detail(cls, steam_appid: str):
        interface = cls()
        url = interface.get_url(cls.game_detail_text, {
            "steam_appid": steam_appid,
        })
        json_page = json.loads(interface.request(url, headers=header).text)

        return json_page

