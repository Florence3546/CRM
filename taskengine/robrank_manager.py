# coding=utf-8

import sys
import signal
import time

from multiprocessing import Process, Event


class Consumer(Process):
    """消费者，继承自进程，初始化：
    poison: 毒药，在发作前一直工作
    consume: 消费方法，由具体的业务指定
    """

    def __init__(self, poison, consume):
        super(Consumer, self).__init__()
        self.poison = poison
        self.consume = consume

    def run(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.consume(self.poison)


class Manager(object):
    """管理者，初始化：
    cfg_list： 是针对每个分配者的对应的配置"""

    def __init__(self, consume, consumer_count, consume_timeout = 60):
        self.consume_timeout = consume_timeout
        self.consumer_list = []
        self.event_list = []
        for i in xrange(consumer_count):
            event = Event()
            self.consumer_list.append(Consumer(poison = event, consume = consume))
            self.event_list.append(event)

    def start_all(self):
        """让所有的分配者开始工作"""
        self.process_list = []
        for consumer in self.consumer_list:
            process = Process(target = consumer.run)
            process.start()
            self.process_list.append(process)

    def stop_all(self, signal, frame):
        """将毒药激活，等待分配者执行完毕"""
        for event in self.event_list:
            event.set()
        for process in self.process_list:
            process.join(self.consume_timeout) # 如果消费操作超时，则强制终止掉
            if self.consume_timeout and process.is_alive():
                process.terminate()
                process.join()
        sys.exit()

    @classmethod
    def trigger(cls, **kargs):
        """对外接口，启动后监听退出"""

        manager = cls(**kargs)
        manager.start_all()

        signal.signal(signal.SIGINT, manager.stop_all)
        signal.signal(signal.SIGTERM, manager.stop_all)

        for i in range(36000): # 超过20小时，mysql就会出现mysql server has gone away!
            time.sleep(2)

        manager.stop_all(None, None)

def main():

    def consume(poison):
        count = 0
        while not poison.is_set():
            count += 1
            print count
            time.sleep(2)

    Manager.trigger(consume = consume, consumer_count = 3)


if __name__ == '__main__':
    main()
