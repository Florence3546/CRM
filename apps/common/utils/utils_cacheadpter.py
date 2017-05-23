# coding=UTF-8
'''
全局管理memcache的调用，封装django自带的cache
主要用于小数据量的调用
'''
from django.core.cache import get_cache
from apps.common.utils.utils_collection import genr_sublist

# TODO: wangqi 20151201 这里可以改进成享元模式，如下代码所示

"""
class CacheAdaptar(object):

    cache_name_dict = {}

    @classmethod
    def get_cache(cls, cache_name):
        pass # 将对应的cache塞入自己的dict中去


    def get(self, key, default = None):
        pass

    def set(self, key, timeout):
        pass

    def delete(self, key):
        pass


web_cache = CacheAdpter.get_cache('web')

"""

class CacheAdpter():

    @classmethod
    def get_time_out(cls, timeout, cache):
        if not timeout:
            timeout = cache.default_timeout
        return timeout

    @classmethod
    def get(cls, key, cache_name, default = None):
        use_cache = get_cache(cache_name)
        value = use_cache.get(key)
        if value is None:
            return default
        return value

    @classmethod
    def set(cls, key, value, cache_name, timeout = 0):
        use_cache = get_cache(cache_name)
        use_cache.set(key, value, cls.get_time_out(timeout, use_cache))

    @classmethod
    def get_many(cls, keys, cache_name, default = {}):
        use_cache = get_cache(cache_name)
        value_dict = use_cache.get_many(keys)
        if value_dict is None:
            return default
        return value_dict

    @classmethod
    def set_many(cls, keys, cache_name, timeout = 0):
        use_cache = get_cache(cache_name)
        use_cache.set_many(keys, cls.get_time_out(timeout, use_cache))

    @classmethod
    def delete(cls, key, cache_name):
        use_cache = get_cache(cache_name)
        use_cache.delete(key)

    @classmethod
    def delete_many(cls, keys, cache_name):
        use_cache = get_cache(cache_name)
        for key in keys:
            use_cache.delete(key)


    @classmethod
    def set_large_list(cls, key, value_list, split_size, cache_name, timeout = 0):
        if value_list:
            use_cache = get_cache(cache_name)
            value_map = {}

            for index, temp_sublist in enumerate(genr_sublist(value_list, split_size)):
                value_map.update({'%s_%s' % (key, index):temp_sublist})

            use_cache.set_many(value_map, timeout) # 存入分解后的数据
            use_cache.set(key, index + 1, timeout) # 被分解的N组
        return True

    @classmethod
    def get_large_list(cls, key, cache_name):
        use_cache = get_cache(cache_name)

        value_list = []
        grp_num = use_cache.get(key)
        if grp_num is None:
            return value_list

        keys = [key + '_' + str(i) for i in range(grp_num)]
        value_dict = use_cache.get_many(keys)
        if not value_dict:
            return value_list
        else:
            return reduce(list.__add__, value_dict.values())