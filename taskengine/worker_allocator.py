# coding=utf-8

import sys
import signal
import time
from Queue import Full as QueueIsFull
from multiprocessing import Queue, Event

from worker_consumer import Consumer


class Allocator(object):

    """分配者，初始化：
    retrieve_items: get_items
    consume: 消费item的方法，由业务决定，传递给consumer
    consumer_count: 消费者个数
    consume_timeout: 仅终止时使用，超时时间
    """

    def __init__(self, retrieve_items, consume, consumer_count, consume_timeout = 60):
        self.retrieve_items = retrieve_items
        self.consume = consume
        self.consumer_count = consumer_count
        self.queue = Queue(consumer_count)
        self.consume_timeout = consume_timeout

    def wake_consumer(self):
        """唤醒消费者"""
        self.consumer_poison_list = []
        self.consumer_list = []
        for _ in xrange(self.consumer_count):
            tmp_poison = Event()
            consumer = Consumer(queue = self.queue, poison = tmp_poison, consume = self.consume)
            consumer.start()
            self.consumer_poison_list.append(tmp_poison)
            self.consumer_list.append(consumer)

    def add_items(self, item_list):
        """将item放到broker中"""
        while item_list:
            try:
                item = item_list.pop()
                self.queue.put(item, block = True, timeout = 0.01)
            except IndexError:
                break
            except QueueIsFull:
                item_list.append(item)
                time.sleep(0.01)

    def start(self):
        """开始工作"""

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        self.wake_consumer()
        while True:
            item_list = self.get_items(need_count = self.consumer_count - self.queue.qsize())
            self.add_items(item_list)
            time.sleep(0.1)

    def get_items(self, need_count):
        """从消息队列中取items"""
        task_list = []
        if need_count > 0:
            try:
                return self.retrieve_items(need_count)
            except Exception:
                return task_list
        return task_list

    def stop(self,  signal, frame):
        """将消费者的毒药激活，并等待他们执行完毕"""
        for poison in self.consumer_poison_list:
            poison.set()
        for consumer in self.consumer_list:
            consumer.join(self.consume_timeout) # 如果消费操作超时，则强制终止掉
            if self.consume_timeout and consumer.is_alive():
                consumer.terminate()
                consumer.join()
        sys.exit()
