import random

import random


def generate_6_digit_uid():
    """
    Generate a 6 digit unique id
    """
    return ''.join(random.choices('0123456789', k=6))


class Lottery:
    def __init__(self, users):
        """
        初始化抽奖类，每个用户有预先定义的权重。
        参数:
        users (list): 包含用户信息的字典列表，每个字典有'name'和'weight'键。
        """
        self.users = users

    def draw_winner(self):
        """
        根据用户的权重随机抽取一个中奖者，中奖后降低其权重。

        返回:
        str: 中奖用户的名字。
        """

        # names = [user['user_id'] for user in self.users]
        weights = [user['user']['weight'] for user in self.users]

        # 使用 random.choices 按权重随机选择一个用户
        winner = random.choices(self.users, weights=weights, k=1)[0]

        # # 找到中奖用户并降低权重
        # for user in self.users:
        #     if user['name'] == winner:
        #         # user['weight'] = max(10, user['weight'] * 0.9)  # 将权重乘以 0.9，但不低于 10
        #         # self.win_count[winner] += 1  # 记录中奖次数
        #         break

        return winner
