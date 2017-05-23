# coding=UTF-8
import math
import importlib

from django.core.cache.backends.base import InvalidCacheBackendError

from settings import CACHES
from apps.common.utils.utils_collection import genr_sublist


# TODO: yangrongkai 理论上该类应该继承CacheAdpter, MemcacheAdpter
# 但是由于CacheAdpter, MemcacheAdpter两者都没有继承object类势必要
# 造成深度继承, 如果出现多级继承 B-> A  C->A  D->B,C 则构建D对象时会
# 出现重复加载问题，建议采用 C3算法(广度继承) 来解决这个问题。以下
# 类将会调用 CacheAdpter, MemcacheAdpter 来通过底层适配器完成CRM
# 相关工作
class BaseCacheAdapter(object):
    """为了方便扩展，此处做成适配器形式"""
    __slots__ = ['cache_name', 'time_out', 'adapter', '_backend', '_location',
                 'launch_log', '_args']

    def __init__(self, cache_name, **kwargs):
        self.cache_name = cache_name
        self._backend, self._location, self.launch_log, self.time_out, \
            self._args = self._load_args(**kwargs)
        self.adapter = self._load_adapter()

    def _load_args(self, **kwargs):
        conf = CACHES.get(self.cache_name, None)
        if conf is not None:
            _args = conf.copy()
            _args.update(kwargs)
            _backend = _args.pop('BACKEND')
            _location = _args.pop('LOCATION', '')
            _launch_log = _args.pop('LOG', False)
            _timeout = _args.pop('TIMEOUT', 60)
            return _backend, _location, _launch_log, _timeout, _args
        raise Exception('%s is not existed in setting CACHES.' % (self.cache_name))

    def _load_adapter(self):
        mod_path, cls_name = self._backend.rsplit('.', 1)
        try:
            mod = importlib.import_module(mod_path)
            backend_cls = getattr(mod, cls_name)
        except (AttributeError, ImportError), e:
            raise InvalidCacheBackendError(
                "Could not find backend '%s': %s" % (self._backend, e))
        return backend_cls(self._location, self._args)

    def get(self, key):
        return self.adapter.get(key)

    def set(self, key, value, time_out = 0):
        if not time_out or time_out <= 0:
            time_out = self.time_out
        self.adapter.set(key, value, timeout = time_out)

    def delete(self, key):
        self.adapter.delete(key)

class CrmCacheAdapter(BaseCacheAdapter):
    __slots__ = ['cache_name', 'time_out', 'adapter', '_backend', '_location',
                 'launch_log', '_args', '_large_size']

    def __init__(self, size = 1000, **kwargs):
        self._large_size = size
        super(CrmCacheAdapter, self).__init__('crm', **kwargs)

    def get_many(self, keys):
        return self.adapter.set_many(keys)

    def set_many(self, value_map, time_out = None):
        if time_out is None:
            time_out = self.time_out
        self.adapter.set_many(value_map, time_out)

    def set_large_list(self, key, value_list):
        value_map = {}

        i = 0
        for temp_sublist in genr_sublist(value_list, self._large_size):
            value_map.update({'%s_%s' % (key, i):temp_sublist})
            i += 1

        # 存入内存
        self.adapter.set_many(value_map, self.time_out) # 存入数据
        self.adapter.set(key, i, self.time_out) # 存入组数

        return True

    def get_large_list(self, key):
        value_list = []

        grp_num = self.adapter.get(key)
        if grp_num == None:
            return value_list

        keys = [key + '_' + str(i) for i in range(grp_num)]
        value_dict = self.adapter.get_many(keys)
        if len(value_dict) != grp_num:
            return value_list

        for key in keys:
            if value_dict.has_key(key):
                value_list.extend(value_dict[key])

        return value_list

    def delete_large_list(self, key):
        grp_num = self.adapter.get(key)
        if grp_num == None:
            return True

        keys = [key + '_' + str(i) for i in range(grp_num)]
        for key in keys:
            self.adapter.delete(key)

        return True

class GDataCacheAdapter(BaseCacheAdapter):
    __slots__ = ['cache_name', 'time_out', 'adapter', '_backend', '_location',
                 'launch_log', '_args', '_large_size']

    def __init__(self, size = 100, **kwargs):
        self._large_size = size
        super(GDataCacheAdapter, self).__init__('g_data', **kwargs)
        if 'Memcached' not in self._backend:
            raise ValueError("GDataCacheAdapter need to use memcache driver.")

    def generate_keys(self, keys):
        k_len = len(keys)
        cycle = int(math.ceil(k_len * 1.0 / self._large_size))
        for index in xrange(cycle):
            yield keys[index * self._large_size: (index + 1) * self._large_size]

    def get_many(self, keys):
        result_dict = {}
        for sub_keys in self.generate_keys(keys):
            c_dict = self.adapter.get_many(sub_keys)
            result_dict.update(c_dict)
        return result_dict

    def set_many(self, data):
        for sub_keys in self.generate_keys(data.keys()):
            b_data = {}
            for key in sub_keys:
                b_data[key] = data[key]
            self.adapter.set_many(b_data, self.time_out)

    def delete_many(self, keys):
        for sub_keys in self.generate_keys(keys):
            for key in sub_keys:
                self.adapter.delete(key)
