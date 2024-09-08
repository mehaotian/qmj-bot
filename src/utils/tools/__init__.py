import random


def generate_6_digit_uid():
    """
    Generate a 6 digit unique id
    """
    return ''.join(random.choices('0123456789', k=6))


class Lottery:
    def __init__(self, users, open_rule):
        """
        初始化抽奖类，每个用户有预先定义的权重。
        参数:
        users (list): 包含用户信息的字典列表，每个字典有'name'和'weight'键。
        """
        self.users = users
        self.open_rule = open_rule

    def draw_winners(self, num_winners):
        """
        根据用户的权重随机抽取多个中奖者，中奖后降低其权重。

        参数:
        num_winners (int): 要抽取的中奖人数。

        返回:
        list: 中奖用户的名字列表。
        """
        winners = []
        candidates = self.users.copy()  # 复制用户列表以避免修改原始数据

        for _ in range(num_winners):
            if not candidates:
                break  # 如果候选用户列表为空，停止抽奖
            if not self.open_rule or self.open_rule == 0:
                # 如果开奖规则为0，直接随机选择一个用户
                winner = random.choice(candidates)
                winners.append(winner)
                candidates.remove(winner)
                continue

            # 如果开奖规则为1，按权重随机选择一个用户
            if self.open_rule == 1:
                weights = [user['user']['weight'] for user in candidates]
                print('权重开奖', weights)
                # 使用 random.choices 按权重随机选择一个用户
                winner = random.choices(candidates, weights=weights, k=1)[0]
                winners.append(winner)
                candidates.remove(winner)

            # 使用 random.choices 按权重随机选择一个用户
            # winner = random.choices(candidates, weights=weights, k=1)[0]
            # winners.append(winner)
            # # 从候选用户列表中移除中奖用户
            # candidates.remove(winner)

        # # 找到中奖用户并降低权重
        # for user in self.users:
        #     if user['user']['user_id'] == winner['user']['user_id']:
        #         user['user']['weight'] = max(10, user['user']['weight'] * 0.9)  # 将权重乘以 0.9，但不低于 10
        #         break

        return winners
