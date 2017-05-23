# coding=utf-8
import time
import random

from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.kwslt.select_words import ItemScorer, group_kwlist, ForbidWord, MemcacheAdpter
from apps.kwslt.models_cat import CatStatic
from apps.kwslt.base import sort_kwlist_by_click # 用于eval @UnusedImport

from apps.kwslt.models_queue import RedisQueue


# 下面几个描述有助于了解缓存的不同数据
# group_cache = 'kwlib' # 对每个类目下关键词分组情况，key形如  <cat_id>，e.g. 16类目下有300组
# task_cache = 'kwlib' # 即每个类目下对应的关键词，key形如 <cat_id>_<group_no>, e.g. 16_0
# result_cache = 'worker' # 即针对某个宝贝，对类目分组过的数据，进行匹配后的结果，key形如 <item_id>_<cat_id>_<group_no>， e.g. 20151123_16_0
# status_cache = 'worker' # 同上面的result_cache，这里只是一个标志位，做完了就打个tag，为了防止取数据重复，这里设置超时10时间为10s

class Contractor(object):

    def __init__(self, name, item, select_conf):
        self.name = name
        self.item_id = item.item_id

        self.label_conf_list = item.get_label_conf_list()
        # for label in self.label_conf_list:
        #     log.info(label[0] + ':' + ','.join(label[2]))
        self.cats = item.cat_ids
        self.remove_words = ','.join(set(item.get_exclude_list))
        self.select_conf = select_conf
        self.filter_list = [f.candi_filter for f in select_conf.select_conf_list]
        self.price_list = [{'candi_filter':p.candi_filter, 'init_price':p.init_price} for p in select_conf.price_conf_list]
        self.db_name = 'worker' # memcache_name

    def decompose_tasks(self):
        """任务分解"""
        result_list = []
        self.cats.reverse()
        default_cat_cpc = random.randint(45, 65) # 防止出价一样，给用户体验不好
        for cat_id in self.cats:
            group_count = MemcacheAdpter.get_list_count(cat_id, 'kwlib') # 缓存中数据不由这里保证
            if group_count:
                cat_data = CatStatic.get_market_data_8id(cat_id)
                cat_cpc = cat_data.get('cpc', default_cat_cpc)
                if cat_cpc <= 5:
                    cat_cpc = default_cat_cpc
                temp_list = [{'cats':self.cats, 'statu':'init', 'cat_cpc':cat_cpc, 'label_conf_list':self.label_conf_list,
                              'remove_words': self.remove_words, 'filter_conf':self.select_conf.candi_filter,
                              'filter_list':self.filter_list, 'price_list':self.price_list,
                              'item_id':str(self.item_id), 'from_db':'kwlib',
                              'from_key':'%s_%s' % (cat_id, ii), 'data_db':self.db_name,
                              'data_key':'%s_%s_%s' % (self.name, cat_id, ii)} for ii in range(group_count)]
                result_list.extend(temp_list)
        self.sub_prj_list = result_list[0:250]
        return True

    def publish_tasks(self):
        """任务发布"""
        try:
            RedisQueue.publish_tasks(self.sub_prj_list)
            return True
        except Exception, e:
            log.error("publish task error, e=%s" % e)
            return False

    def check_status(self):
        """检查完成进度"""
        key_list = ['%s_status' % sub_prj['data_key'] for sub_prj in self.sub_prj_list]
        value_dict = CacheAdpter.get_many(key_list, self.db_name)
        time_interval = 0.3
        time_out = 20
        start_time = time.time()
        ratio = float(len(value_dict)) / len(self.sub_prj_list)
        while ratio < 0.85:
            time.sleep(time_interval)
            if time.time() - start_time >= time_out:
                log.info('waiting for worker finishing time out!')
                break
            value_dict = CacheAdpter.get_many(key_list, self.db_name)
            ratio = float(len(value_dict)) / len(self.sub_prj_list)
        return True

    def sum_result(self):
        """汇总结果"""
        candi_kw_dict = {}
        key_list = []
        for prj in self.sub_prj_list:
            key_list.append(prj['data_key'])
        worker_result_dict = CacheAdpter.get_many(key_list, self.db_name)
        # 汇总农民工的结果数据
        for temp_dict in worker_result_dict.values():
            for k, v in temp_dict.items():
                if not candi_kw_dict.has_key(k):
                    candi_kw_dict[k] = []
                candi_kw_dict[k].extend(v)
        # 汇总排序
        result_list = []
        filter_index = 0
        for filter in self.select_conf.select_conf_list: # @ReservedAssignment
            filter_index += 1
            kw_list = candi_kw_dict.get(filter.candi_filter, [])[0:10000] # 卡死，某一类别最多10000，绝对够了
            if not kw_list:
                continue
            sort_func = 'kw_list.sort(sort_kwlist_by_%s)' % filter.sort_mode
            eval(sort_func)
            # 根据配置的数目获取
            range_list = filter.select_num.split('-')
            if float(range_list[0]) < 1.0: # 按照百分比
                start_index = int(len(kw_list) * float(range_list[0]))
                end_index = int(len(kw_list) * float(range_list[1]))
            else:
                start_index = int(range_list[0]) - 1
                end_index = int(range_list[1])
            temp_list = [kw + [str(filter_index)] for kw in kw_list[start_index: end_index - start_index]]
            result_list.extend(temp_list)

        return result_list

    def __call__(self):
        log.info('item %s select_words START!' % (self.item_id))
        self.decompose_tasks() # 任务收集、并分解
        if self.sub_prj_list:
            log.info('item %s decompose task OK, total task count=%s!' % (self.item_id, len(self.sub_prj_list)))
            self.publish_tasks() # 任务发布
            log.info('item %s publish task OK!' % (self.item_id))
            self.check_status() # 检查任务完成状态，不管超时与否，下面仍然会从结果缓存里取
            log.info('item %s check task status OK!' % (self.item_id))
            result = self.sum_result() # 汇总结果
            log.info('item %s select_words END, total keyword count=%s!' % (self.item_id, len(result)))
            return result
        else:
            return []


# worker计算的具体代码
def calc_match(prj_dict):
    prj_dict = prj_dict
    item_scorer = ItemScorer(prj_dict['label_conf_list'])
    cats = prj_dict['cats']
    filter_conf = prj_dict['filter_conf']
    filter_list = prj_dict['filter_list']
    price_list = prj_dict['price_list']
    remove_word_list = prj_dict['remove_words'] and prj_dict['remove_words'].split(',') or []
    cat_cpc = prj_dict['cat_cpc']

    log.info('worker start, item_id=%s, key=%s' % (prj_dict['item_id'], prj_dict['data_key']))
    kw_list = CacheAdpter.get(prj_dict['from_key'], prj_dict['from_db'], [])
    if not kw_list:
        log.error('can not get group from memcache and the group is = %s' % prj_dict['from_key'])
        kw_list = CacheAdpter.get(prj_dict['from_key'], prj_dict['from_db'], [])
    group_dict = {}
    if kw_list:
        if ('click > 0' not in filter_conf) and ('click>0' not in filter_conf) or kw_list[0][2] > 0:
            cat_id = prj_dict['from_key'].split('_')[0]
            try:
                group_dict = group_kwlist(kw_list, item_scorer, int(cat_id), cat_cpc, cats, remove_word_list, filter_conf, filter_list, price_list)
            except Exception, e:
                log.error('group_kwlist error: cat_id=%s, e=%s' % (cat_id, e))
    CacheAdpter.set(prj_dict['data_key'], group_dict, prj_dict['data_db'])
    log.info('worker finish, item_id=%s, key=%s' % (prj_dict['item_id'], prj_dict['data_key']))
    CacheAdpter.set('%s_status' % prj_dict['data_key'], True, prj_dict['data_db'], 10)
