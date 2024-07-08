import os
from pydantic import Extra, BaseModel
from pathlib import Path
from nonebot import get_driver
from .config import Config


# 机器人缓存目录，用于存放头像背景等图片信息
cache_dir = Path() / "cache_image"
cache_directory = Path(os.getenv('CACHE_DIR', cache_dir))

# 当前目录
current_directory = Path(__file__).resolve().parent
# 静态资源路径
static_path = current_directory / "resource"

text_bg_path = current_directory / "resource" / "imgs"

sgin_bg_path = current_directory / "resource" / "sgin-bg-imgs"

# 从 NoneBot 配置中解析出的插件配置
plugin_config = Config()
global_config = get_driver().config

# if global_config.environment == 'dev':
#     web_url = 'http://127.0.0.1:8080'
# else:
#     web_url = 'https://botapi.mehaotian.com'

# 签到基础点数
BASE = plugin_config.daily_sign_base

# 连续签到加成比例
MULTIPLIER = plugin_config.daily_sign_multiplier

# 最大幸运值
MAX_LUCKY = plugin_config.daily_sign_max_lucky

# steam key
steam_base_url = 'http://api.steampowered.com'
