# coding=utf-8

import redis
import cPickle as pickle
from django.conf import settings


class RedisQueue(object):

    _redis = redis.Redis(**settings.REDIS_WORKER_QUEUE)

    channel_key = "select:word:queue"

    @classmethod
    def publish_tasks(cls, task_list):
        pickled_list = []
        for task in task_list:
            pickled_list.append(pickle.dumps(task))
        cls._redis.lpush(cls.channel_key, *pickled_list)

    @classmethod
    def get_tasks(cls, need_count):
        task_list = []
        for _ in xrange(need_count):
            task = cls._redis.rpop(cls.channel_key)
            if task:
                task_list.append(pickle.loads(task))
            else:
                break
        return task_list
