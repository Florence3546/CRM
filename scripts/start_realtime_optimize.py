# coding=utf-8

import init_environ
from taskengine.robrank_manager import Manager
from apps.engine.realtime_opt import RealtimeOptimizeMng

if __name__ == "__main__":

    Manager.trigger(consume = RealtimeOptimizeMng.execute, consumer_count = 1) # 实时优化只能单线程跑

    # def test(poison):
    #     import time
    #     from apps.common.utils.utils_log import log

    #     count = 0
    #     while not poison.is_set():
    #         count += 1
    #         log.info(count)
    #         time.sleep(2)

    # Manager.trigger(consume = test, consumer_count = 3)
