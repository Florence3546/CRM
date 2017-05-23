# coding=utf-8

import sys
import signal
import time

from multiprocessing import Process

from allocator import Allocator, Event


class Manager(object):
    """管理者，初始化：
    cfg_list： 是针对每个分配者的对应的配置"""

    def __init__(self, cfg_list):
        self.allocator_list = []
        self.event_list = []
        for cfg in cfg_list:
            event = Event()
            cfg.update({'poison': event})
            self.allocator_list.append(Allocator(**cfg))
            self.event_list.append(event)

    def start_all(self):
        """让所有的分配者开始工作"""
        self.process_list = []
        for allocator in self.allocator_list:
            process = Process(target = allocator.start)
            process.start()
            self.process_list.append(process)

    def stop_all(self, signal, frame):
        """将毒药激活，等待分配者执行完毕"""
        for event in self.event_list:
            event.set()
        for process in self.process_list:
            process.join()
        sys.exit()

    @classmethod
    def trigger(cls, cfg_list):
        """对外接口，启动后监听退出"""
        manager = cls(cfg_list)
        manager.start_all()

        signal.signal(signal.SIGINT, manager.stop_all)
        signal.signal(signal.SIGTERM, manager.stop_all)

        for i in range(36000): # 超过20小时，mysql就会出现mysql server has gone away!
            time.sleep(2)

        manager.stop_all(None, None)
