import os
from pydantic import BaseModel


class Config(BaseModel):
    """
    配置类
    """
    # 签到基础点数
    daily_sign_base: int = 100

    # 连续签到加成比例
    daily_sign_multiplier: float = 0.2

    # 最大幸运值
    daily_sign_max_lucky: int = 10

    # steam key
    steam_api_key:str = "CFBCDCA9ACBFDDACD0321DB2BA4BDBCB"