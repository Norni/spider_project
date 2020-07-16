import random
from qianqianyinyue.settings import USER_AGENT_LIST


class RandomUserAgent(object):
    def __init__(self):
        self.user_agent_list = USER_AGENT_LIST

    @property
    def get_random_user_agent(self):
        return random.choice(self.user_agent_list)


random_user_agent = RandomUserAgent().get_random_user_agent

if __name__ == "__main__":
    # obj = RandomUserAgent()
    data = {
        "a": random_user_agent
    }
    print(data)
