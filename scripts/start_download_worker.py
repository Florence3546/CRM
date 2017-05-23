# coding=utf-8

import init_environ

from taskengine.worker_allocator import Allocator
from apps.subway.download_boost.contractor import download_task
from apps.subway.download_boost.task_queue import DownloadRedisQueue


if __name__ == "__main__":
    cfg_dict = {
        'retrieve_items': DownloadRedisQueue.get_tasks,
        'consume': download_task,
        'consumer_count': 8,
        'consume_timeout': 30
    }
    allocator = Allocator(**cfg_dict)
    allocator.start()
