from src.plugins.tortoise_orm import add_model




def init_models():
    """
    初始化模型
    """
    # 获取插件的根目录
    root = __name__.rpartition('.')[0]
    # 添加用户模型
    add_model("src.models.user_model")
