import random
from itertools import count


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
        # # 计算权重总和
        # total_weight = sum(user['weight'] for user in self.users)
        # # 生成一个随机数
        # pick = random.uniform(0, total_weight)
        # current = 0
        # print(pick)
        # # 遍历用户，找到中奖者
        # for user in self.users:
        #     print('current',current)
        #     current += user['weight']
        #     if current >= pick:
        #         # 中奖后降低用户的权重，但不低于最低限度
        #         # user['weight'] = max(10, user['weight'] * 0.9)  # 将权重乘以 0.9，但不低于 10
        #         return user['name']
        names = [user['name'] for user in self.users]
        weights = [user['weight'] for user in self.users]

        # 使用 random.choices 按权重随机选择一个用户
        winner = random.choices(names, weights=weights, k=1)[0]

        # 找到中奖用户并降低权重
        for user in self.users:
            if user['name'] == winner:
                # user['weight'] = max(10, user['weight'] * 0.9)  # 将权重乘以 0.9，但不低于 10
                # self.win_count[winner] += 1  # 记录中奖次数
                break

        return winner


# 示例使用
users = [
    {'name': '张三', 'weight': 100},
    {'name': '李四', 'weight': 1},
    # {'name': '王二', 'weight': 50},
    # {'name': '麻子', 'weight': 50},
    # {'name': '小妹', 'weight': 50},
    # {'name': '小刚', 'weight': 50},
    # {'name': '小李', 'weight': 50}
]

lottery = Lottery(users)

winners = {}

count_data = 100

# 进行多次抽奖，观察不同用户的中奖情况
for _ in range(count_data):
    winner = lottery.draw_winner()

    # print(f"中奖者是: {winner}, 当前权重: {[user['weight'] for user in users]}")

    # 中奖次数 +1
    if winner in winners:
        winners[winner] += 1
    else:
        winners[winner] = 1

print(winners)
arr = []
# 打印中奖情况 \n 换行
for winner, count in winners.items():
    arr.append({winner: count})
    # print(f"{winner}: {count}")

# 将列表按值从大到小排序
sorted_results = sorted(arr, key=lambda x: list(x.values())[0], reverse=True)

print(f'{count_data}次抽奖结果：')
# 按要求打印结果
for result in sorted_results:
    for name, count in result.items():
        print(f"中奖 - {name} ：{count}次")