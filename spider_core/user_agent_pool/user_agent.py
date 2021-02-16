# -*- coding: utf-8 -*-

import os

from spider_core.basic import BasePool


class UserAgentManager(BasePool):

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ua_file_path = os.path.join(base_dir, 'user-agents.txt')
        with open(ua_file_path, 'r') as f:
            self._cache = [line.strip() for line in f if line.strip()]


user_agent_manager = UserAgentManager()


if __name__ == '__main__':

    tool = UserAgentManager()
    print(tool.random_get())
