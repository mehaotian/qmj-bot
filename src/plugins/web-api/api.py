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
    # 忘记密码
    forget_password:str = f"{api}/forget_password"
    # 获取用户信息
    get_user:str = f"{api}/get_user"
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
