 # coding=utf-8
import zlib
import datetime

from apps.common.constant import Const
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import date_2datetime
from apps.crm.cache_class import CrmCacheAdapter, CrmCacheStructAdapter
from apps.subway.models import adg_coll, account_coll
from apps.subway.download import dler_coll
from apps.kwslt.models_cat import cat_coll

crm_cache = CrmCacheAdapter()

def get_statictics_category_info():
        key = CacheKey.CRM_CAT_ADG_STATISTICS
        cat_data = crm_cache.get(key)
        if not cat_data:
            crm_cache.delete(CacheKey.CRM_CAT_ADG_STATISTICS_LOCK)
            lock_flag = crm_cache.get(CacheKey.CRM_CAT_ADG_STATISTICS_LOCK)
            if lock_flag:
                return {}

            lock_flag = crm_cache.set(CacheKey.CRM_CAT_ADG_STATISTICS_LOCK, True, 10 * 60 * 60)
            aggr_pipeline = [
                                {
                                    '$group':{
                                                  '_id':{'category_ids':'$category_ids'},
                                                  'adgroup_total' : { '$sum': 1 }
                                              }
                                },
                                # 暂过滤掉 < 5000,日后将会扩展
#                                 {
#                                     '$match':{
#                                                     'adgroup_total':{
#                                                                                 "$gte":5000
#                                                                      }
#                                               }
#                                  },
                                {
                                    '$project':{
                                                    '_id':0,
                                                    'cat_path':"$_id.category_ids",
                                                    'total':'$adgroup_total'
                                                }
                                 },
                                 {
                                    '$sort':{
                                                'cat_path':1,
                                                'total':-1
                                             }
                                  }
                     ]

            cat_data = {}
            try:
                result = adg_coll.aggregate(aggr_pipeline)['result']
            except Exception, e:
                log.error('aggregate adgroup by category error, e=%s' % e)
                return cat_data

            cat_mapping = {}
            cat_id_set = set()
            for temp in result:
                total = temp['total']
                if temp.has_key('cat_path'):
                    category_ids = str(temp['cat_path']).split()
                    for index in xrange(len(category_ids)):
                        cat = '>'.join(category_ids[:index + 1])
                        if cat and cat != 'None':
                            if not cat_mapping.has_key(cat):
                                cat_mapping[cat] = 0
                                cat_id_set.add(int(category_ids[index]))
                            cat_mapping[cat] += total
                else:
                    # 理论上应该不存在这个问题
                    pass

            cat_name_mapping = { cat['_id'] : cat['cat_name'] for cat in cat_coll.find({'_id':{"$in":list(cat_id_set)}}, {'cat_name':1}) }
            for cat_all_path, total in cat_mapping.items():
                cat_id_list = cat_all_path.split('>')
                #  此处需要进行ID与名称之间转换
                cat_all_name = []
                for cat_id in cat_id_list:
                    cat_name = cat_name_mapping.get(int(cat_id), '')
                    if cat_name:
                        cat_all_name.append(cat_name)
                    else:
                        # 理论应不会出现该问题
                        log.error('error : it should not happen, the program is wrong if it appear, cat_id=%s' % (cat_id))
                        continue
                if cat_id_list :
                    base_dict = {
                                        'cat_id':cat_id_list[-1],
                                        'cat_name':'>'.join(cat_all_name),
                                        'adgroup_total':total
                                    }
                    cat_data[int(cat_id_list[-1])] = base_dict

            data = zlib.compress(json.dumps(cat_data) , 5)
            crm_cache.set(key, data, 10 * 24 * 60 * 60)
            crm_cache.delete(CacheKey.CRM_CAT_ADG_STATISTICS_LOCK)
#             log.info('The space of statictics catetgory data is %s bytes, length=%s.' % (sys.getsizeof(data), len(data)))
        else:
            cat_data = json.loads(zlib.decompress(cat_data))
        return cat_data

def get_valid_account_list():
    """获取有效的账户列表"""
    valid_list = crm_cache.get(CacheKey.CRM_VALID_ACCOUNT_FLAG)
    if not valid_list:
        try:
            valid_list = []
            yes_time = date_2datetime(datetime.date.today() - datetime.timedelta(days = 1))
            for dl in dler_coll.find({'api_valid_time':{"$gte":yes_time}}, {'_id':1}):
                try:
                    valid_list.append(int(dl['_id']))
                except Exception, e:
                    log.error("get shop_id error,  e=%s" % (e))
            # 每 20 分钟刷新一次
            crm_cache.set(CacheKey.CRM_VALID_ACCOUNT_FLAG , valid_list, time_out = 20 * 60)
        except Exception, e:
            log.error("get valid accounts error, e=%s" % e)
            return []
    return valid_list

class CrmCacheServer(object):
    _clear_fields = ('cat_id', 'consult_id')
    _reset_fields = ('rpt_day',)

    _cond_types = ('account', 'campaign', 'adgroup', 'keyword')
    _last_level_mapping = {
                           _cond_types[0]:'_id',
                           _cond_types[1]:'shop_id',
                           _cond_types[2]:'campaign_id',
                           _cond_types[3]:'adgroup_id'
                           }
    _name_mapping = {
        "account":(('_id', 'shop_id'),),
        "campaign":(('shop_id', 'shop_id'), ('_id', 'camp_id')),
        "adgroup":(('shop_id', 'shop_id'), ('campaign_id', 'camp_id'), ('_id', 'adg_id')),
        "keyword":(('shop_id', 'shop_id'), ('campaign_id', 'camp_id'), ('adgroup_id', 'adg_id'), ('_id', 'kw_id'))
    }

    def __init__(self, user_id):
        self.worker = CrmCacheStructAdapter(user_id = user_id)
        base_dict = self.worker(self.worker.base_types)
        self.user_id = user_id
        self.cat_id = base_dict.get('cat_id', -1)
        self.consult_id = base_dict.get('consult_id', int(user_id))
        self.rpt_day = base_dict.get('rpt_day', 7)

    def reload_cache(self, user_id, cat_id, consult_id, cur_page, rpt_day = 7):
        self.user_id = int(user_id)
        self.cat_id = int(cat_id)
        self.consult_id = consult_id
        self.rpt_day = rpt_day
        self.status = 0
        self._check_cache(fields = [cur_page])
        return self.status

    def _decide_tool(self, fields):
        # here will don't consider to use local cache,
        # target is to ensure data consistency
        base_dict = self.worker(self.worker.base_types).pop('base')
        for _field in fields:
            val = getattr(self, _field, None)
            if val is None or not base_dict.get(_field, None) == val:
                return True
        return False

    def _reset_base_info(self):
        shop_id_list = get_valid_account_list()

        if self.cat_id > 0 :
            shop_id_list = [acc['_id'] for acc in account_coll.\
                            find({'cat_id':self.cat_id, '_id':{"$in":shop_id_list}}, {'_id':1}) if acc.has_key('_id')]

        if self.consult_id > 0 :
            from apps.ncrm.models import Subscribe
            today = datetime.date.today()
            end_date = today - datetime.timedelta(days = 15)
#             temp_list = [ subscribe.shop_id for subscribe in\
#                          Subscribe.objects.only('shop_id').filter(shop__in = shop_id_list, \
#                     operater__id = self.consult_id, article_code__in = Const.COMMON_SUBSCRIBE_MAPPING['rjjh'], \
#                 start_date__lte = today, end_date__gte = end_date) ]
            temp_list = Subscribe.objects.filter(shop__in = shop_id_list, operater__id = self.consult_id, category = 'rjjh', start_date__lte = today, end_date__gte = end_date).values_list('shop_id', flat = True)
            shop_id_list = temp_list

        data_dict = {}
        data_dict.update({
                'cat_id':self.cat_id,
                'consult_id':self.consult_id,
                'rpt_day':self.rpt_day,
                'valid_accounts':shop_id_list
        })

        base_dict = {}
        base_dict.update({'base':data_dict})
        self.save(base_dict)

    def _is_clear(self):
        return self._decide_tool(self._clear_fields)

    def _clear_struct(self):
        return self.delete(fields = self.worker.field_types)

    def _is_reset(self):
        return self._decide_tool(self._reset_fields)

    def _clear_last_data_cache(self, field_types):
        return self.worker.delete_last_data(fields = field_types)

    def _clear_last_cond(self, fields):
        return self.worker.delete_last_cond(fields = fields)

    def _set_rpt_day(self):
        return self.worker.save_cache({"base":{'rpt_day':self.rpt_day}})

    def _reset_data(self, fields):
        return self._clear_last_data_cache(field_types = fields)

    def _check_cache(self, fields):
        if self._is_clear():
            self._clear_struct()
            self._reset_base_info()
            self.status = 2
        elif self._is_reset():
            self._reset_data(fields)
            self._clear_last_cond(fields)
            self._set_rpt_day()
            self.status = 1

    def _generate_dict(self, data_dict, mark , index = 1):
        new_dict = {}
        for key, val in data_dict.items():
            if mark in key:
                new_dict[key.split('_')[1]] = val
        return new_dict

    def clear_user_cache(self):
        return self.delete()

    def get_condition_cache(self, page_type):
        return self.worker.get_condtion_data(fields = (page_type,))

    def get_objids_cache(self, page_type):
        return self.worker.get_objid_data(fields = (page_type,))

    def get_last_data_cache(self, page_type):
        last_data = self.worker.get_last_data(fields = (page_type,))
        if last_data and last_data.has_key(page_type)  \
            and last_data[page_type].has_key('last_data'):
            return last_data.pop(page_type).pop('last_data')
        return []

    def save_last_data_cache(self, page_type, last_data):
        old_last_data = self.worker.get_last_data(fields = (page_type,))
        if old_last_data and old_last_data.has_key(page_type):
            old_last_data[page_type]['last_data'] = last_data
        return self.save(old_last_data)

    def get_cond_type_bypage(self, page_type):
        _mark_page_mapping = {
                        'account':'account',
                        'campaign':'campaign',
                        'campbak':'campaign',
                        'adgroup':'adgroup',
                        'adgbak':'adgroup',
                        'keyword':'keyword',
                        'kwbak':'keyword'
                     }
        return _mark_page_mapping.get(page_type)

    def get_page_type(self, sour_index, sour_jump_status, curr_index):
        # key : (source_index,source_is_jump),dest_index)
        # val  : (source_page,dest_page)
        if not hasattr(self, '_page_mapping'):
            self._page_mapping = {
                        # account
                        ((0, 0), 0):(self.worker.field_types[0], self.worker.field_types[0]),
                        ((0, 0), 1):(self.worker.field_types[0], self.worker.field_types[2]),
                        ((0, 0), 2):(self.worker.field_types[0], self.worker.field_types[4]),
                        # campaign
                        ((1, 0), 1):(self.worker.field_types[1], self.worker.field_types[1]),
                        ((1, 1), 1):(self.worker.field_types[2], self.worker.field_types[2]),
                        ((1, 0), 2):(self.worker.field_types[1], self.worker.field_types[4]),
                        ((1, 1), 2):(self.worker.field_types[2], self.worker.field_types[4]),
                        # adgroup
                        ((2, 0), 2):(self.worker.field_types[3], self.worker.field_types[3]),
                        ((2, 1), 2):(self.worker.field_types[4], self.worker.field_types[4]),
                        ((2, 0), 3):(self.worker.field_types[3], self.worker.field_types[6]),
                        ((2, 1), 3):(self.worker.field_types[4], self.worker.field_types[6]),
                        # keyword
                        ((3, 0), 3):(self.worker.field_types[5], self.worker.field_types[5]),
                        ((3, 1), 3):(self.worker.field_types[6], self.worker.field_types[6]),
                   }
        key = ((sour_index, sour_jump_status), curr_index)
        return self._page_mapping.get(key)

    def transfer_cache(self, sour_page, curr_page, id_dict):
        # (源页面索引,源页面跳转状态,目的页面索引
        curr_fields = (curr_page,)
        sour_fields = (sour_page,)
        self.worker.delete_cache(fields = curr_fields)

        curr_cache = self.worker(curr_fields).pop(curr_page)
        sour_cache = self.worker(sour_fields).pop(sour_page)
        sour_cache.pop('last_data')

        curr_cache.update(sour_cache)
        valid_key = self.get_cond_type_bypage(sour_page)
        curr_cache.update({'last_%s_ids' % valid_key: id_dict.get(valid_key, [])})

        self.save({curr_page:curr_cache})
        return True

    def get_name_mapping(self, cond_type, name_type = -1):
        # type : 0 数据库及缓存名称都要 1仅需要数据库名称 2仅需要缓存名称
        if name_type == -1:
            result_list = self._name_mapping[cond_type] # the bug need expose when happen error
        else:
            result_list = [ data[name_type] for data in self._name_mapping[cond_type] ]
        return result_list

    def get_last_level_idkey(self, cond_type):
        return self._last_level_mapping[cond_type] # the bug need expose when happen error

    def get_aggregate_scope(self, mark, valid_num):
        return self._cond_types[self._cond_types.index(mark):valid_num]

    def get_valid_cond_scope(self, mark):
        return self._cond_types[:self._cond_types.index(mark)]

    def get_last_cond_type(self, cond_type):
        last_index = self._cond_types.index(cond_type) - 1
        if last_index >= 0:
            return self._cond_types[last_index]
        return None

    def get_last_objids(self, page_data, cond_type):
        last_cond = self.get_last_cond_type(cond_type)
        if last_cond:
            return page_data.get('last_%s_ids' % (last_cond), [])
        return []

    def reset_ids_4search(self, page_data, cond_type, data):
        page_data.update({"last_%s_ids" % cond_type: data})
        return page_data

    def clear_ids_4search(self, page_data, invalid_scope):
        for cond_type in invalid_scope:
            self.reset_ids_4search(page_data, cond_type, [])
        return page_data

    def reset_condition_4search(self, page_data, cond_type, data):
        page_data.update({"last_%s_cond" % cond_type: data})
        return page_data

    def clear_condition_4search(self, page_data, invalid_scope):
        for cond_type in invalid_scope:
            self.reset_condition_4search(page_data, cond_type, {})
        return page_data

    def reset_last_data_4search(self, page_data, data):
        page_data.update({'last_data':data})
        return page_data

    def sync_condition(self, send_cond, page_data, valid_num):
        for cond_type in self._cond_types[:valid_num]:
            # 此处等待出错，理论上不应存在
            page_data['last_%s_cond' % cond_type] = send_cond[cond_type]
        return page_data

    def clear_invalid_cache(self, page_data, invalid_scope, clear_cond = False):
        if clear_cond:
            self.clear_condition_4search(page_data, invalid_scope)
        self.clear_ids_4search(page_data, invalid_scope)
        self.reset_last_data_4search(page_data, [])
        return page_data

    def check_condition(self, send_cond, cache_cond):
        is_same, cond_mark = True, None
        size = len(cache_cond)
        for cond_type in self._cond_types[:size]:
            cond_1 = cache_cond.get(cond_type, {})
            cond_2 = send_cond.get(cond_type, {})
            if cond_1 != cond_2:
                is_same = False
                cond_mark = cond_type
                break
        return is_same, cond_mark

    def get_condition(self, page_data):
        return self._generate_dict(page_data, mark = '_cond', index = 1)

    def get_ids(self, page_data):
        return self._generate_dict(page_data, mark = '_ids', index = 1)

    def get_last_data(self, page_data):
        return page_data.get('last_data', [])

    def get_valid_accounts(self, base_data):
        return base_data.get('valid_accounts', [])

    def get_statistics_ids(self, page_data, valid_num):
        return [ len(page_data.get('last_%s_ids' % cond_type, [])) \
                        for cond_type in self._cond_types[:valid_num]]

    def get_someone_last_data(self, page_index, is_jumped):
        source_page, _ = self.get_page_type(page_index, is_jumped, page_index)
        last_data = self.get_last_data_cache(source_page)
        return last_data

    def save(self, cache_dict):
        return self.worker.save_cache(cache_dict)

    def delete(self, fields = ()):
        if fields:
            return self.worker.delete_cache(fields)
        else:
            return self.worker.delete_cache()

    def __call__(self, page_type):
        # this function is same with _decide_tool,
        # they all need to ensure data consistency.
        if page_type in self.worker.base_types:
            return self.worker(self.worker.base_types)
        else:
            return self.worker(self.worker.base_types + (page_type,))


#     def sync_condition(self, send_cond, cache_cond, source_page, invalid_scope):
#         save_dict = {}
#         for key in cache_cond.keys():
#             if key in invalid_scope:
#                 new_val = send_cond.get(key, {})
#                 save_dict["last_%s_cond" % (key)] = new_val
#                 cache_cond[key] = new_val
#         self.worker.save_cache({source_page:save_dict}, fields = (source_page,))
#         return cache_cond
#
#     def sync_ids(self, cond_type, source_page, id_list):
#         return self.worker.save_cache({source_page:{"last_%s_ids" % (cond_type):id_list}}, \
#                                       fields = (source_page,))
#
#     def sync_multi_ids(self, source_page, sync_ids_dict):
#         for cond_type, id_list in sync_ids_dict.items():
#             self.sync_ids(cond_type, source_page, id_list)
#         return True
#
#     def sync_last_data(self, data, source_page):
#         return self.worker.save_cache({source_page:{'last_data':data}}, fields = (source_page,))


# 测试代码，用时需要导入 init_environ
# if __name__ == '__main__':
#     server = CrmCacheServer(user_id = 1132, group_id = 5)
#     source_page, _ = server.get_page_type(1, 1, 1)
#     last_filter_data = server.get_last_data_cache(source_page)
#     print last_filter_data
#     server.save_last_data_cache(source_page, [1, 2, 34, 5])
#     last_filter_data = server.get_last_data_cache(source_page)
#     print last_filter_data
