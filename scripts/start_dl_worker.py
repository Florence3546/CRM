# coding=utf-8

import init_environ

from taskengine.worker_allocator import Allocator
from apps.subway.download_boost.contractor import download_task_new
from apps.subway.download_boost.task_queue import SlowerDownloadRedisQueue


if __name__ == "__main__":
    cfg_dict = {
        'retrieve_items': SlowerDownloadRedisQueue.get_tasks,
        'consume': download_task_new,
        'consumer_count': 8,
        'consume_timeout': 30
    }
    allocator = Allocator(**cfg_dict)
    allocator.start()
