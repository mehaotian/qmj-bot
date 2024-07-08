
from src.plugins.tortoise_orm import add_model
# 获取插件的根目录
root = __name__.rpartition('.')[0]
# 添加用户模型
add_model(f"{root}.models.user_model")
