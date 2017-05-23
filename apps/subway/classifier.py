# coding=utf-8

import redis
import collections

from django.conf import settings
from apps.kwslt.analyzer import ChSegement


"""
违禁词分类器

考虑了再三，觉得这里还是使用redis作数据存储比较好。

key为 word:连衣裙:1
value为出现的频率，即数字
"""

class IllegalClassifier(object):

    # TODO: wangqi 20151214 需要解决的问题还有几个
    # 1. 分词之后，需要去掉停用词之类的无用词，如“的”
    # 2. 要考虑整体数据量的大小，据说原子词才16万？

    _redis = redis.Redis(**settings.REDIS_WORKER_QUEUE)

    @classmethod
    def train(cls, source_list):
        """
        :arg
            source_list [{'category': 16, 'keyword': '粉色连衣裙', 'shop_type': 'B', 'is_illegal': True}, ...]
        """
        counter_dict = collections.Counter()
        result_dict = {}

        for source in source_list:
            is_illegal = source['is_illegal'] and 1 or 0
            word_list = ChSegement.chsgm_keyword(source['keyword'])
            counter_dict['%s:%s:%s' % ('category', source['category'], is_illegal)] += 1
            counter_dict['%s:%s:%s' % ('shop_type', source['shop_type'], is_illegal)] += 1
            for word in word_list:
                counter_dict['%s:%s:%s' % ('word', word, is_illegal)] += 1

        cls.set_data(counter_dict)

    @classmethod
    def load_data(cls, feature_type, feature):

        illegal_key = "%s:%s:1" % (feature_type, feature)
        ok_key = "%s:%s:0" % (feature_type, feature)

        return {True: int(cls._redis.get(illegal_key) or 0), False: int(cls._redis.get(ok_key) or 0)}

    @classmethod
    def set_data(cls, counter_dict):
        """数据格式为{'word:连衣裙:0': 200}"""
        for key, count in counter_dict.items():
            cls._redis.incrby(key, count)
        return True

    @classmethod
    def classify(cls, shop_type, category, keyword):
        word_list = ChSegement.chsgm_keyword(keyword)
        r1 = cls.calc_prob(shop_type, category, word_list, True)
        r2 = cls.calc_prob(shop_type, category, word_list, False)
        print r1, r2
        return r1 > r2 and True or False


    @classmethod
    def calc_prob(cls, shop_type, category, word_list, result_type = True):
        shop_type_prob = cls.calc_feature_prob(feature_type = "shop_type", feature = shop_type, result_type = result_type)
        category_prob = cls.calc_feature_prob(feature_type = "category", feature = category, result_type = result_type)
        p = pow(shop_type_prob * category_prob, len(word_list))
        for word in word_list:
            p *= cls.calc_feature_prob(feature_type = "word", feature = word, result_type = result_type)
        return p

    @classmethod
    def calc_feature_prob(cls, feature_type, feature, result_type):
        result_dict = cls.load_data(feature_type, feature)
        total_count = sum(result_dict.values())
        if total_count > 0:
            return result_dict.get(result_type, 0) / float(total_count)
        else:
            return 1