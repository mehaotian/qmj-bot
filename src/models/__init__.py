import aiomcache

from src.plugins.tortoise_orm import add_model


def init_models():
    """
    初始化模型
    """
    # 获取插件的根目录
    root = __name__.rpartition('.')[0]
    # 添加用户模型
    add_model("src.models.user_model")
    # 添加钱包模型
    add_model("src.models.wallet_model")
    # --- 签到 ---
    # 添加签记录模型
    add_model("src.models.checkin_record_model")
    # 添加签到模型
    add_model("src.models.checkins_model")

    # --- 抽奖 ---
    # 添加抽奖模型
    add_model("src.models.lottery_model")


class MemcacheClient:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None or cls._client.closed:
            cls._client = aiomcache.Client("127.0.0.1", 11211)
        return cls._client
