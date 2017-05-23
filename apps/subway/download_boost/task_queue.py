# coding=utf-8

# from django.conf import settings
from apps.kwslt.models_queue import RedisQueue

class DownloadRedisQueue(RedisQueue):

    # _redis = redis.Redis(**settings.REDIS_WORKER_QUEUE)
    channel_key = "download:queue"

class SlowerDownloadRedisQueue(RedisQueue):
    channel_key = "slower:download:queue"