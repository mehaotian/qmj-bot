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
    # websocket OTP
    ws_otp: str = f"{api}/ws_otp"
    # 退出登录
    logout: str = f"{api}/logout"
    # 获取所有用户
    get_all: str = f"{api}/all"
    # 切换登录用户
    switch: str = f"{api}/switch"



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
    # 获取我的抽奖
    get_my_list = f"{api}/my_list"
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
    # 获取奖品列表
    get_prize_list = f"{api}/prize_list"
    # 获取中奖名单
    get_user_list = f"{api}/user_list"
    # 获取核销列表
    get_write_off_list = f"{api}/write_off_list"
    # 修改核销状态
    edit_write_off = f"{api}/edit_write_off"
    # 提交中奖信息
    submit_winner_info = f"{api}/submit_winner_info"


class team(Enum):
    """
    团队接口
    """
    # 接口前缀
    api = "/api/team"
    # 创建团队
    add = f"{api}/add"
    # 获取团队列表
    get_list = f"{api}/list"
    # 获取团队详情
    get_detail = f"{api}/detail"
    # 加入团队
    join = f"{api}/join"
    # 离开团队
    leave = f"{api}/leave"
    # 结束组队
    end = f"{api}/end"
    # 获取加入组队用户
    get_user = f"{api}/get_user"
    # 获取我的组队
    get_my_list = f"{api}/my_list"


class upload(Enum):
    """
    上传接口
    """
    # 接口前缀
    api = "/api/upload"



class admin(Enum):
    """
    管理员接口
    """
    # 接口前缀
    api = "/admin"
    register = f"{api}/auth/register"
    login = f"{api}/auth/login"
    logout = f"{api}/auth/logout"
    userinfo = f"{api}/user/info"

class xhh(Enum):
    """
    小黑盒相关接口
    """
    # 接口前缀
    api = "/xhh"
    game = f"{api}/game"
