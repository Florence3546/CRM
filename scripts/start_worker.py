# coding=utf-8

import init_environ

from taskengine.worker_allocator import Allocator
from apps.kwslt.contractor import calc_match
from apps.kwslt.models_queue import RedisQueue


if __name__ == "__main__":
    cfg_dict = {
        'retrieve_items': RedisQueue.get_tasks,
        'consume': calc_match,
        'consumer_count': 4,
        'consume_timeout': 30
    }
    allocator = Allocator(**cfg_dict)
    allocator.start()