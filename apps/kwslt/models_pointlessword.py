# coding=UTF-8
from apps.common.cachekey import CacheKey
from mongoengine.fields import StringField, IntField
from mongoengine.document import Document
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_log import log

class PointlessWord(Document):
    """无意义词表，用于解析词、关键词打分时忽略掉这些词"""
    LEVEL_CHOICES = ((1, '修饰词过滤'), (2, '修饰词，关键词打分时过滤'))
    word = StringField(verbose_name = "关键词", max_length = 100)
    level = IntField(verbose_name = "无意义等级", choices = LEVEL_CHOICES, default = 1)
    meta = {"collection":"kwlib_pointlessword", "db_alias": "kwlib-db"}

    @staticmethod
    def update_memcache():
        objs = PointlessWord.objects.all()
        level_1_list = [obj.word for obj in objs if obj.level == 1]
        level_2_list = [obj.word for obj in objs if obj.level == 2]
        CacheAdpter.set(CacheKey.KWLIB_POINTLESSWORD, [level_1_list, level_2_list], 'web', 60 * 60 * 24 * 7)
        log.info('update PointlessWord into memcache')

    # 加载到缓存中
    @staticmethod
    def load_in_cache_if_not():
        word_list = CacheAdpter.get(CacheKey.KWLIB_POINTLESSWORD, 'web', [])
        if word_list:
            return
        PointlessWord.update_memcache()

    @staticmethod
    def get_pointlessword_list(level = 1):
        PointlessWord.load_in_cache_if_not()
        word_list = CacheAdpter.get(CacheKey.KWLIB_POINTLESSWORD, 'web', [[], []])
        return word_list[level - 1]

pointless_coll = PointlessWord._get_collection()