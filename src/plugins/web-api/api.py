from enum import Enum


class users(Enum):
    """
    定义用户相关接口
    """
    # 接口前缀
    api: str = "/api/users"
    # 注册用户
    qqauth: str = f"{api}/qqauth"
    # 登录
    login: str = f"{api}/login"
    # 获取用户信息
    get_user: str = f"{api}/userinfo"
    # 绑定群组
    bind_group: str = f"{api}/bind_group"
    # 创建用户
    create: str = f"{api}/create"


class lottery(Enum):
    """
    抽奖接口
    """
    # 接口前缀
    api = "/api/lottery"
    # 发布抽奖
    add = f"{api}/add"
    # 获取抽奖列表
    get_list = f"{api}/list"
    # 获取抽奖详情
    get_detail = f"{api}/detail"
    # 加入抽奖
    join = f"{api}/join"
    # 获取抽奖用户
    get_user = f"{api}/get_user"
    # 获取中奖用户
    get_winner = f"{api}/get_winner"
    # 手动开奖
    open = f"{api}/open"

class upload(Enum):
    """
    上传接口
    """
    # 接口前缀
    api = "/api/upload"
