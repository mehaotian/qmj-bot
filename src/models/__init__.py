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
    # 添加参与抽奖模型
    add_model("src.models.involved_lottery_model")
    # 添加奖品模型
    add_model("src.models.prize_model")
    # 核销表
    add_model("src.models.write_off_model")

    # --- 组队 ---
    # 添加团队模型
    add_model("src.models.team_model")
    # 添加团队成员模型
    add_model("src.models.team_members_model")

    # --- 管理员 ---
    # 添加管理员用户模型
    add_model("src.models.admin_user_model")


class MemcacheClient:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None or cls._client.closed:
            cls._client = aiomcache.Client("127.0.0.1", 11211)
        return cls._client
