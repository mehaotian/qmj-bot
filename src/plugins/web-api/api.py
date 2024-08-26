from enum import Enum


class users(Enum):
    """
    定义用户相关接口
    """
    # 接口前缀
    api:str = "/api/users"
    # 注册用户
    qqauth:str = f"{api}/qqauth"
    # 登录
    login:str = f"{api}/login"

    # 获取用户信息
    get_user:str = f"{api}/userinfo"
    # 绑定群组
    bind_group: str = f"{api}/bind_group"


class sys(Enum):
    """
    系统接口
    """
    # 接口前缀
    api = "/api/sys"
    # 提交抽奖
    lottery = f"{api}/lottery"
    # 获取抽奖用户
    get_user = f"{api}/get_user"
    # 验证用户key
    verify_key = f"{api}/verify_key"


class upload(Enum):
    """
    上传接口
    """
    # 接口前缀
    api = "/api/upload"
    # 上传文件
    lottery = f"{api}/lottery"
