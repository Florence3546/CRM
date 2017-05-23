# coding=utf-8

import init_environ
from taskengine.robrank_manager import Manager
from apps.engine.rob_rank import RobRankMng

if __name__ == "__main__":

    Manager.trigger(consume = RobRankMng.execute, consumer_count = 3)

    # def test(poison):
    #     import time
    #     import signal
    #     from apps.common.utils.utils_log import log

    #     signal.signal(signal.SIGINT, signal.SIG_IGN)
    #     count = 0
    #     while not poison.is_set():
    #         count += 1
    #         log.info(count)
    #         time.sleep(2)

    # Manager.trigger(consume = test, consumer_count = 3)
