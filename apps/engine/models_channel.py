# coding=utf-8

import redis
from django.conf import settings


class MessageChannel(object):

    _redis = redis.Redis(**settings.REDIS_RANK_CHANNEL)
    msg_prefix = "keyword:%s"
    history_prefix = "opt:history:%s"

    @classmethod
    def publish_msg(cls, msg_dict):
        for keyword_id, msg in msg_dict.items():
            cls._redis.publish(cls.msg_prefix % keyword_id, msg)
        return True

    @classmethod
    def save_msg(cls, msg_dict):
        for keyword_id, msg in msg_dict.items():
            cls._redis.lpush(cls.history_prefix % keyword_id, msg)
            cls._redis.ltrim(cls.history_prefix % keyword_id, 0, 300) # 只保存最新的300条记录
        return True

    @classmethod
    def subscribe(cls, keyword_id_list):
        p = cls._redis.pubsub()
        channel_list = [cls.msg_prefix % keyword_id for keyword_id in keyword_id_list]
        p.subscribe(*channel_list)
        return p

    @classmethod
    def unsubscribe(cls, p, keyword_id_list):
        channel_list = [cls.msg_prefix % keyword_id for keyword_id in keyword_id_list]
        p.unsubscribe(*channel_list)
        return True

    @classmethod
    def delete_publish_history(cls, keyword_id_list):
        for keyword_id in keyword_id_list:
            cls._redis.delete(cls.msg_prefix % keyword_id)
        return True

    @classmethod
    def delete_msg_history(cls, keyword_id_list):
        for keyword_id in keyword_id_list:
            cls._redis.delete(cls.msg_prefix % keyword_id)
            cls._redis.delete(cls.history_prefix % keyword_id)
        return True

    @classmethod
    def get_history(cls, keyword_id_list):
        msg_dict = {}
        for keyword_id in keyword_id_list:
            msg_dict.update({keyword_id: cls._redis.lrange(cls.history_prefix % keyword_id, 0, -1)})
        return msg_dict


class OrderChannel(object):
    """用于订单催付功能的一个简单pubsub"""

    _redis = redis.Redis(**settings.REDIS_RANK_CHANNEL)
    channel_key = "order:pubsub"

    @classmethod
    def publish(cls, msg):
        cls._redis.publish(cls.channel_key, msg)
        return True

    @classmethod
    def subscribe(cls):
        p = cls._redis.pubsub()
        p.subscribe(cls.channel_key)
        return p

    @classmethod
    def unsubscribe(cls, p):
        p.unsubscribe(cls.channel_key)
        return True