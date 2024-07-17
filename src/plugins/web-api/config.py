#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   config.py
@Time    :   2023/10/07 16:28:28
@Author  :   haotian
@Version :   1.0
@Desc    :   数据库配置文件
"""

from nonebot import get_driver
from pydantic import Extra, BaseModel
from typing import ClassVar
import os


class Config(BaseModel, extra=Extra.ignore):
    # 项目名称
    APP_NAME: str = "API Server "
    # 是否开启debug
    DEBUG: bool = False
    # 数据库连接URL
    DATABASE_URL: str = "postgres://user:pass@ip/db"

    # 程序配置
    BASE_DIR: ClassVar[str] = os.path.dirname(os.path.abspath(__file__))


plugin_config = Config()

global_config = get_driver().config

