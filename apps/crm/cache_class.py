# coding=UTF-8
import re

from apps.common.biz_utils.utils_cacheadapter import CrmCacheAdapter

class CrmCacheStructAdapter(object):
    __slots__ = ['separator', 'field_types', 'user_id', 'prefix', 'all_types', 'adapter_cls', 'field_mapping', \
                    'sub_marks', '_larger_save_filed', '_models']

    separator = '='

    sub_marks = ('_cond', '_ids', '_data')
    base_types = ('base',)
    field_types = ('account', 'campaign', 'campbak', 'adgroup', 'adgbak', 'keyword', 'kwbak')
    all_types = base_types + field_types

    _larger_save_fileds = set(('last_data',))
    _models = ['last_%s_cond', 'last_%s_ids']
    _field_nams = ['account', 'campaign', 'adgroup', 'keyword']

    def __init__(self, user_id, adapter = None):
        self.user_id = user_id
        self.prefix = "%s"*2 % (self.user_id, self.separator)
        self.adapter_cls = adapter if adapter is not None else CrmCacheAdapter()
        self.field_mapping = self._load_field_mapping()

    def __call__(self, fields = all_types):
        result_dict = {}
        if not fields:
            return result_dict

        return self._multi_generate_cache(\
                        self.get_cache_keys(fields = fields, is_short = True), result_dict) \
                            .pop('%s' % self.user_id)

    def _load_field_mapping(self):
        mapping = {}

        for i, field in enumerate(self.field_types):
            index = (i + 1) / 2 + 1
            field_list = []
            for field_name in self._field_nams[:index]:
                for _model in self._models:
                    field_list.append(_model % (field_name))
            field_list.append('last_data')
            mapping[field] = tuple(field_list)

        mapping.update({
            self.base_types[0]:(
                'cat_id',
                'consult_id',
                'rpt_day',
                'valid_accounts'
            )
        })

        return mapping

    def _hang_tree(self, cache_key, result_dict, data):
        paths = cache_key.split(self.separator, 1)
        if paths and paths > 0:
            key = paths[0]
            if len(paths) > 1:
                if not result_dict.has_key(key):
                    result_dict[key] = {}
                self._hang_tree(paths[1], result_dict[key], data)
            else:
                result_dict[key] = data

    def _generate_cache(self, short_key, result_dict):
        # Requirement:
        #     first       : cache_key isn't blank, and it must validly.
        #     second : cache_key must be short key, as base=cat_id
        cache_key = '%s' * 2 % (self.prefix , short_key)

        if self.is_large_field(cache_key):
            cache_data = self.adapter_cls.get_large_list(cache_key)
        else:
            cache_data = self.adapter_cls.get(cache_key)

        # is cache_data isn't existed, It will equal to None
        self._hang_tree(cache_key, result_dict, cache_data)
        return result_dict

    def _multi_generate_cache(self, short_keys, result_dict):
        for short_key in short_keys:
            self._generate_cache(short_key, result_dict)
        return result_dict

    def _get_cache_key_byshort(self, cache_key):
        return "%s"*2 % (self.prefix, cache_key)

    def _get_cache_key(self, field, sub_field, is_short = False):
        cache_key = "%s"*3 % (field, self.separator, sub_field)
        if not is_short:
            cache_key = self._get_cache_key_byshort(cache_key)
        return cache_key

    def _is_same_4submark(self, sub_key, marks):
        rule = "(%s)" % ('|'.join(marks))
        if re.search(rule, sub_key):
            return True
        return False

    def _filter_valid_data(self, cache_dict):
        # for this function, I just consider two level, and it is cache's bound.
        result_dict = {}
        for key, val_dict in cache_dict.items():
            if key in self.field_mapping.keys() :
                for sub_key, data in val_dict.items():
                    if sub_key in self.field_mapping[key]:
                        result_dict.update({self._get_cache_key(key, sub_key, is_short = False):data})
        return result_dict

    def get_shor_mark(self, cache_key):
        return  cache_key.rsplit(self.separator, 1)[-1]

    def is_large_field(self, cache_key):
        if self.get_shor_mark(cache_key) in self._larger_save_fileds:
            return True
        else:
            return False

    def get_cache_keys(self, fields = all_types, sub_marks = sub_marks, is_short = False):
        cache_keys = []
        for field in fields:
            if self.field_mapping.has_key(field):
                for sub_field in self.field_mapping[field]:
                    if sub_field in self.field_mapping['base']:
                        cache_keys.append(self._get_cache_key(field, sub_field, is_short))
                    else:
                        if self._is_same_4submark(sub_field, sub_marks):
                            cache_keys.append(self._get_cache_key(field, sub_field, is_short))
        return cache_keys

    def delete_cache(self, fields = all_types):
        for cache_key in self.get_cache_keys(fields = fields):
            if self.is_large_field(cache_key):
                self.adapter_cls.delete_large_list(cache_key)
            else:
                self.adapter_cls.delete(cache_key)
        return True

    def save_cache(self, cache_dict):
        for cache_key, cache_data in self._filter_valid_data(cache_dict).items():
            if self.is_large_field(cache_key):
                self.adapter_cls.set_large_list(cache_key, cache_data)
            else:
                self.adapter_cls.set(cache_key, cache_data)
        return True

    def _condtion_keys(self, fields):
        return self.get_cache_keys(fields = fields, sub_marks = ('_cond',), is_short = True)

    def _last_data_keys(self, fields, is_short = False):
        return self.get_cache_keys(fields = fields, sub_marks = ('_data',), is_short = True)

    def _objid_keys(self, fields, is_short = False):
        return self.get_cache_keys(fields = fields, sub_marks = ('_ids',), is_short = True)

    def get_last_cond_keys(self, num = 1, fields = field_types):
        cache_keys = []
        for field in fields:
            sub_keys = self._condtion_keys((field,))[-num:]
            for sub_key in sub_keys:
                cache_keys.append(self._get_cache_key_byshort(sub_key))
        return cache_keys

    def delete_last_data(self, fields = field_types):
        for cache_key in self._last_data_keys(fields):
            self.adapter_cls.delete(self._get_cache_key_byshort(cache_key))
        return True

    def delete_last_cond(self, num = 1, fields = field_types):
        for cache_key in self.get_last_cond_keys(num, fields):
            self.adapter_cls.delete(cache_key)
        return True

    def get_condtion_data(self, fields):
        return self._multi_generate_cache(self._condtion_keys(fields), {}).pop('%s' % self.user_id)

    def get_objid_data(self, fields):
        return self._multi_generate_cache(self._objid_keys(fields), {}).pop('%s' % self.user_id)

    def get_last_data(self, fields):
        return self._multi_generate_cache(self._last_data_keys(fields), {}).pop('%s' % self.user_id)
