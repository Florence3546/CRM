# coding=UTF-8
import math
import random
import datetime
import time
import StringIO
import pycurl
import json
import re
import requests
from django.conf import settings
from django.core.cache import get_cache

from apilib.japi import JAPI
from apps.common.utils.utils_log import log
from apps.common.utils.utils_thread import NewThread
from apps.common.biz_utils.utils_tapitools import get_kw_g_data
from apps.common.utils.utils_string import get_ordered_str, check_duplicate_word
from apps.common.utils.utils_collection import genr_sublist
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.kwslt.analyzer import ChSegement
from apps.kwslt.base import group_kwlist, remove_same_words, get_word_num, transform_tuple_2tobj
from apps.kwslt.models_selectconf import SelectConf
from apps.kwslt.models_cat import MetaphorWord, Cat, CatStatic, ForbidWord
from apps.kwslt.models_synonymword import SynonymWord
from apps.kwslt.models_pointlessword import PointlessWord
from apps.kwslt.base import sort_kwlist_by_click
from apps.kwlib.api import save_lable_list, check_kw_2save_inDB, get_timescope

'''
选词相关的类以及API
'''
class MemcacheAdpter():
    '''
    Memcached缓存，为支持大数据（大于1M）存取
    '''
    @staticmethod
    def get_large_list(key, cache_name = 'kwlib'):
        use_cache = get_cache(cache_name)
        grp_num = use_cache.get(key)
        if grp_num is None:
            return None
        keys = [key + '_' + str(i) for i in range(grp_num)]
        value_dict = use_cache.get_many(keys)
        value_list = []
        # 按照key的顺序，一组组的将数据合并到结果中
        lack_count = 0
        for key in keys:
            if value_dict.has_key(key): # 可能存在中间某组不存在的情况，因为cache采用LRU算法，数据可能会被导出去
                value_list.extend(value_dict[key])
            else:
                lack_count += 1
        if lack_count > len(keys) * 0.1: # 10%的没有，就直接返回none
            log.info('memcached lost to much, return none')
            return None
        return value_list

    # 将valuelist分解成1w条数据一组，然后分别存入内存，最后记录组数
    @staticmethod
    def set_large_list(key, value_list, cache_name = 'kwlib', timeout = 24 * 60 * 60 * 30, count = 4500):
        use_cache = get_cache(cache_name)
        # 分解成多组
        value_map = {}
        i = 0
        for temp_sublist in genr_sublist(value_list, count):
            value_map.update({'%s_%s' % (key, i):temp_sublist})
            i += 1

        # 存入内存
        use_cache.set_many(value_map, timeout) # 存入数据
        use_cache.set(key, i, timeout) # 存入组数

    @staticmethod
    def get_list_count(key, cache_name = 'kwlib'):
        use_cache = get_cache(cache_name)
        group_count = use_cache.get(key)
        return group_count

# class CatWordLoader():
#     '''
#     根据类目ID找出该类目下的关键词类目统计数据，以tuple方式返回
#     '''
#     @staticmethod
#     def get_keywords_by_cat(cat_id, cache_name):
#         cat_key = str(cat_id)
#         result_list = MemcacheAdpter.get_large_list(cat_key, cache_name)
#         if not result_list:
#             log.info('get kw_list from db, cat_id = %s' % cat_id)
#             word_list = []
#             # 通过数据库关联查询
#             wc_coll = WordCat._get_collection()
#             kw_list = wc_coll.find({'cat_id':int(cat_id), 'c_pv':{'$gt':0}}, {'word':1, 'c_pv':1, 'c_click':1, 'c_cpc':1, 'c_competition':1, 'c_ctr':1, 'cat_id':1})
#             for kw in kw_list:
#                 word_list.append((kw['word'], int(kw['c_pv']), int(kw['c_click']), float(kw['c_cpc']), int(kw['c_competition']), float(kw['c_ctr']), int(kw['cat_id'])))
#
#             # 去掉多余的重复词
#             result_list = remove_same_words(word_list)
#             MemcacheAdpter.set_large_list(cat_key, result_list, cache_name)
#
#         log.info('get kw_list from memcache/db, cat_id=%s, word_len=%s' % (cat_id, len(result_list)))
#         return result_list
#
#     @staticmethod
#     def get_keywords_by_cats(cat_list, cache_name = 'kwlib'):
#         result_list = []
#         for cat_id in cat_list:
#             kw_list = CatWordLoader.get_keywords_by_cat(cat_id, cache_name)
#             result_list.extend(kw_list)
#         return result_list


class ItemScorer():

    def __init__(self, label_conf_list = None):
        self.product_words = '' # 用于处理分词后剩下的部分
        self.label_conf_list = label_conf_list or []
        self.pointless_word_list = PointlessWord.get_pointlessword_list(level = 2)
        for label, is_remove, word_list in self.label_conf_list:
            if label == 'P':
                self.product_words = ' '.join(word_list)

    def extract_labels(self, participles):
        result_label, part_count = '', 0

        # 根据卖点词、自定义词、产品词、修饰词**依次**进行匹配分解
        for label, is_remove, word_list in self.label_conf_list:
            if not participles.strip():
                break
            for word in word_list:
                if word in participles:
                    result_label += label
                    if is_remove:
                        participles = participles.replace(word, ' ')
                        part_count += 1

        return result_label, part_count, participles

    def score_participles_by_item(self, participles):
        labels, part_count, left_part = self.extract_labels(participles)

        # 因为下面还要匹配 self.product_words, 所以这里不能直接返回。
        # if part_count == 0:
        #     return 0, ''

        # 计算剩下分词个数以及总分
        left_list = set(left_part.split()) - set(self.pointless_word_list) # 注意split里不带任何参数 ，list.split() != list.split(' ')
        left_count = len(left_list)
        for word in left_list:
            if word in self.product_words:
                labels += "D"
                part_count += 1
                left_count -= 1
            elif len(word) > 3: # 如果剩余词的长度为4以上，则认为是2个词组成（简单处理）
                left_count += 1

        result_score = (left_count + part_count) and int(part_count * 1.0 / (left_count + part_count) * 1000.0) or 0
        return result_score, labels

class Combiner():

    # 根据类目以及关键词组合，然后按流量排序排好.不要超过一定的时间，防止淘宝调用超时，而无法获取到关键词
    @staticmethod
    def combine_words(cat_id, product_list, product_synonym_list, decorate_list, max_num = 300, timeout = 60):

        # 构建种子词，包括组合产品词和纯粹的产品词和产品同义词
        seed_list = []
        seed_list.extend(product_list)

        # 去掉没有流量的属性词
        seed_list.extend(decorate_list)
        temp_seed_list = Combiner.remove_noimp_same_wd2(cat_id, seed_list)
        imp_decorate_list = [wd[0] for wd in temp_seed_list]
        seed_list = [wd[0] for wd in temp_seed_list]

        # 开始和属性进行组合，最多3个分词。每次只保留有流量的关键词作为种子词，以减少关键词的数量
        # log.info('product words num:%s' % (len(seed_list)))
        keep_detail_list = []
        new_tmp_list = []
        new_tmp_list.extend(seed_list)
        try_set_list = [(set(word.replace(' ', '')), len(word.replace(' ', ''))) for word in seed_list]
        tt = 0
        while tt < 3:
            new_list = []
            for tl in seed_list:
                if tl.count(' ') != tt:
                    continue
                for wd in imp_decorate_list:
                    if tl == wd or wd in tl:
                        continue
                    new_word = tl + ' ' + wd
                    if new_word not in seed_list:
                        tmp_new_word = new_word.replace(' ', '')
                        if not check_duplicate_word(tmp_new_word, try_set_list):
                            new_tmp_list.append(new_word)
                            try_set_list.append((set(tmp_new_word), len(tmp_new_word)))
                        else: # 已经有了，不要重复添加
                            continue
                        # 装满，就取类目数据和全网数据，然后保留一部分
                        if len(new_tmp_list) >= max_num:
                            tmp_detail_list = Combiner.remove_noimp_same_wd2(cat_id, new_tmp_list)
                            keep_detail_list.extend(tmp_detail_list)
                            new_tmp_list = []
                            if len(keep_detail_list) >= max_num:
                                break

            if new_tmp_list:
                tmp_detail_list = Combiner.remove_noimp_same_wd2(cat_id, new_tmp_list)
                keep_detail_list.extend(tmp_detail_list)
                new_tmp_list = []

            # 只保留有流量的关键词作为种子词
            seed_list = [dl[0] for dl in keep_detail_list]

            # 刷新计数器
            tt += 1

        # 最后进行排序以及去重
        keep_detail_list = remove_same_words(keep_detail_list)
        # log.info('combine words,remove same and sort,result len:%s' % (len(keep_detail_list)))
        return keep_detail_list

    @staticmethod
    def combine_words2(prdtword_list, dcrtword_list, prmtword_list):
        from itertools import combinations
        kw_list = []
        # ==============================================================
        # 3个分词组词
        # -- 1个产品词
        temp_prdtword_list = prdtword_list[:]
        # -- -- 1个修饰词
        temp_dcrtword_list = dcrtword_list[:]
        # -- -- -- 1个促销词
        temp_prmtword_list = prmtword_list[:]
        for prdtword in temp_prdtword_list:
            for dcrtword in temp_dcrtword_list:
                for prmtword in temp_prmtword_list:
                    kw_list.append(' '.join([dcrtword, prmtword, prdtword]))
        # -- -- 2个修饰词 + 0个促销词
        temp_dcrtword_list = [' '.join(word_tuple) for word_tuple in combinations(dcrtword_list, 2)]
        for prdtword in temp_prdtword_list:
            for dcrtword in temp_dcrtword_list:
                kw_list.append(' '.join([dcrtword, prdtword]))
        # -- 2个产品词
        temp_prdtword_list = [' '.join(word_tuple) for word_tuple in combinations(prdtword_list, 2)]
        # -- -- 1个修饰词 + 0个促销词
        temp_dcrtword_list = dcrtword_list[:]
        for prdtword in temp_prdtword_list:
            for dcrtword in temp_dcrtword_list:
                kw_list.append(' '.join([dcrtword, prdtword]))
        # -- -- 0个修饰词 + 1个促销词
        for prdtword in temp_prdtword_list:
            for prmtword in temp_prmtword_list:
                kw_list.append(' '.join([prmtword, prdtword]))
        # ==============================================================
        # 2个分词组词
        # -- 1个产品词
        temp_prdtword_list = prdtword_list[:]
        # -- -- 1个修饰词 + 0个促销词
        for prdtword in temp_prdtword_list:
            for dcrtword in temp_dcrtword_list:
                kw_list.append(' '.join([dcrtword, prdtword]))
        # -- -- 0个修饰词 + 1个促销词
        for prdtword in temp_prdtword_list:
            for prmtword in temp_prmtword_list:
                kw_list.append(' '.join([prmtword, prdtword]))
        # ==============================================================
        # 1个分词组词
        # -- 1个产品词
        kw_list.extend(prdtword_list)
        return kw_list

    # 根据关键词，去掉没有流量以及重复关键词.返回keywordetailinfo list
    @staticmethod
    def remove_noimp_same_wd(wd_list):
        from apps.kwlib.base import get_words_gdata
        # 对这些关键词进行排序，去掉没有流量的关键词
        # log.info('combine words,new extended words num:%s' % len(wd_list))
        wd_list = check_kw_2save_inDB(wd_list)
        timescope = get_timescope()
        # 找出全网有流量的关键词
        pv_kw_list = get_words_gdata(wd_list, timescope)

        keyword_list = []
        for word, value in pv_kw_list.items():
            keyword_list.append((word, value.pv, value.click, value.avg_price, value.competition, value.ctr))

        # log.info('the num of pv words is=%s' % len(keyword_list))

        keyword_list = remove_same_words(keyword_list)
        return keyword_list

    # 根据关键词，去掉没有流量以及重复关键词.返回keywordetailinfo list
    @staticmethod
    def remove_noimp_same_wd2(cat_id, wd_list):
        # 对这些关键词进行排序，去掉没有流量的关键词
        log.info('combine words,new extended words num:%s' % len(wd_list))
        wd_list = check_kw_2save_inDB(wd_list)
        # wdcat_list = [{'word':word, 'cat_id':cat_id} for word in wd_list]
        keyword_list = []
        # 找出类目下有流量的关键词
        try:
            # temp_dict = get_catsworddata(cat_id, wd_list, datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days = 7), "%Y-%m-%d"), time.strftime("%Y-%m-%d"))
            temp_dict = get_kw_g_data(wd_list)
        except Exception, e:
            log.exception("remove_noimp_same_wd2 error, e=%s" % e)
            temp_dict = {}
        # for c_info in temp_dict.values():
        #     keyword_list.append((c_info['word'], c_info['pv'], c_info['click'], c_info['cpc'], c_info['competition']))
        for word, g_data in temp_dict.items():
            keyword_list.append((str(word), g_data.g_pv, g_data.g_click, g_data.g_cpc, g_data.g_competition))

        log.info('the num of pv words is=%s' % len(keyword_list))

        keyword_list = remove_same_words(keyword_list)
        return keyword_list

class ItemKeywordManager():

    @staticmethod
    def get_kw_list_byelemword(cat_id, elemword_list):
        from itertools import combinations
        kw_list, combine_words_list = [], []
        for i in range(1, 4):
            combine_words_list += combinations(elemword_list, i)
        combine_words_list = list(set([' '.join(word_list) for word_list in combine_words_list]))
        temp_dict = get_kw_g_data(combine_words_list)
        for word, g_data in temp_dict.items():
            g_competition = g_data.g_competition or 1
            if not g_data.g_pv:
                continue
            hot = round(math.log10(float(g_data.g_pv) ** 2 / g_competition), 2)
            if hot > 0:kw_list.append([word, g_data.g_pv, g_data.g_competition, hot, g_data.g_click])
        return kw_list

    @staticmethod
    def get_title_info_dict(cat_id, title):
        elemword_list = ChSegement.split_title_new_to_list(title)
        kw_list = ItemKeywordManager.get_kw_list_byelemword(cat_id, elemword_list)
        return {'title_elemword_list':elemword_list, 'kw_list':kw_list}


class Contractor():
    '''
    为了满足快速计算大量数据，采用分布式并行计算方式。包工负责接活，派活给农民工，检查农民工任务进度，最后汇总。类似map reduce的机制
    农民工可以部署到多个服务器上，统一通过memcached读写数据，农民工根据包工头的任务指示，到指定的memcached、取指定的数据，然后干活
    在把数据以及任务状态存放到指定的memcached中。memcached、农民工服务器都是可以配置的，不同的数据查询，可以写不同的包工头和农民工类
    '''
    def __init__(self, prj_name):
        self.prj_name = prj_name

    def get_workers(self):
        '''
        找农民工
        '''
        return settings.WORKER_LIST

    def get_prjdata_list(self):
        '''
        获取任务的数据清单
        '''
        return [{'from_db':'kwlib', 'from_key':'16_1', 'statu':'init', 'data_key':'1'}, {'from':'worker', 'key':'16_2', 'statu':'init'}]

    def allot_2_prjs(self, prj_list, worker_list):
        '''
        分任务
        '''
        sub_prj_list = []
        worker_weight_list = []
        all_weight = 0
        for worker in worker_list:
            for ii in range(worker['weight']):
                worker_weight_list.append(worker)
                all_weight += 1

        worker_info_dict = {}

        for prj in prj_list:
            # 根据权重找人
            worker_index = random.randint(0, all_weight - 1)
            worker = worker_weight_list[worker_index]
            prj['host'], prj['port'] = worker['host'], worker['port']
            sub_prj_list.append(prj)

            if prj['host'] in worker_info_dict:
                worker_info_dict[prj['host']] += 1
            else:
                worker_info_dict[prj['host']] = 1

        log.info('allot info = %s' % worker_info_dict)
        return sub_prj_list

    def allot_2_workers(self, sub_prj_list, db_name):
        log.info('start: send msgs to workers')
        # 先将各个任务状态为working
        prj_stat_dict = {}
        data_keys = []
        for prj in sub_prj_list:
            prj['statu'] = 'working'
            prj_stat_dict[prj['data_key'] + '_statu'] = 'working'
            data_keys.append(prj['data_key'])
        CacheAdpter.set_many(prj_stat_dict, db_name, 180)
        CacheAdpter.delete_many(data_keys, db_name)

        # 分发任务
        for prj in sub_prj_list:
            # 派活
            try:
                nt = NewThread(JAPI(host = '%s:%s' % (prj['host'], prj['port'])).worker_work, prj_dict = prj, is_sync = False)
                nt.setDaemon(True)
                nt.start()
            except Exception, e:
                log.error('error=%s,prj=%s' % (e, prj))
                continue
        log.info(' end : send msgs to workers')

    def is_prj_finished(self, sub_prj_list):
        working_count = 0
        for prj in sub_prj_list:
            if prj['statu'] == 'working':
                working_count += 1
        # 如果成功率有90%，就直接返回，因为存在网络丢包
        all_count = len(sub_prj_list)
        if all_count == 0:
            return True
        suc_count = all_count - working_count
        if suc_count * 1.0 / all_count < 0.75:
            return False
        return True

    def is_prj_started(self, sub_prj_list):
        ok_count = 0
        for prj in sub_prj_list:
            if prj['statu'] in ['working', 'finished']:
                ok_count += 1
        all_count = len(sub_prj_list)
        if all_count == 0:
            return True
        if ok_count * 1.0 / all_count < 0.95:
            return False
        return True

    def get_prj_statu(self, sub_prj_list, db_name):
        key_list = []
        server_dict = {}
        for prj in sub_prj_list:
            if prj['statu'] == 'finished':
                continue
            key_list.append(prj['data_key'] + '_statu')
            server_dict[prj['host'] + ':' + str(prj['port'])] = 1
        log.info('server is working, unfinished server is: %s' % (','.join(server_dict.keys())))
        value_dict = CacheAdpter.get_many(key_list, db_name)

        if not value_dict:
            return

        for prj in sub_prj_list:
            if prj['statu'] == 'finished':
                continue
            value = value_dict.get(prj['data_key'] + '_statu', None)
            if value:
                prj['statu'] = value

    def sum_prj_result(self, sub_prj_list, db_name):
        return []

    def get_db_name(self):
        return ''

    def do_self_work(self):
        return

    def start_prj(self, time_out = 30):
        '''
        开始工程
        '''
        db_name = self.get_db_name() # 得到数据仓库
        prj_list = self.get_prjdata_list(db_name) # 分任务
        worker_list = self.get_workers() # 得到一批工人
        sub_prj_list = self.allot_2_prjs(prj_list, worker_list) # 分工
        self.allot_2_workers(sub_prj_list, db_name)
        self.do_self_work() # 包工头自己做些自己的事情，比如选词包工头可以重写，自己组合关键词
        sum_time = 0
        start_time = datetime.datetime.now()
        time_interval = 0.7
        min_interval = 0.3
        # 轮询任务完成情况
        while not self.is_prj_finished(sub_prj_list):
            time.sleep(time_interval)
            now_time = datetime.datetime.now()
            sum_time += time_interval
            if (now_time - start_time).seconds >= time_out:
                log.info('waiting for worker finishing time out!')
                break
            self.get_prj_statu(sub_prj_list, db_name)
            time_interval = time_interval / 2 if time_interval / 2 > min_interval else min_interval

        prj_result = self.sum_prj_result(sub_prj_list, db_name) # 汇总结果

        return prj_result

    def prepare_data(self):
        '''
        准备数据
        '''
        db_name = self.get_db_name() # 得到数据仓库
        prj_list = self.get_prjdata_list(db_name) # 分任务
        worker_list = self.get_workers() # 得到一批工人
        sub_prj_list = self.allot_2_prjs(prj_list, worker_list) # 分工
        self.get_prj_statu(sub_prj_list, db_name)
        if not self.is_prj_started(sub_prj_list): # 如果没有开始，就通知工人开始干活
            self.allot_2_workers(sub_prj_list, db_name)

class Worker():
    def __init__(self, prj_dict):
        self.prj_dict = prj_dict

    def work(self):
        self.do_my_work()
        CacheAdpter.set(self.prj_dict['data_key'] + '_statu', 'finished', self.prj_dict['data_db'])
        # log.info('set statu data_db=%s,key=%s' % (self.prj_dict['data_db'], self.prj_dict['data_key']))


class NewSelectWordContractor(Contractor):
    '''
    根据条件选关键词
    '''
    def __init__(self, name, item, select_conf):
        garbage_word_list = set(item.garbage_word_list) - set(ForbidWord.get_all_forbid_list(0))
        self.name = name
        self.item_id = item.item_id

        custome_word_dict = select_conf.analyse_label(item)
        self.label_conf_list = item.get_label_conf_list(custome_word_dict)

        self.cats = item.cat_ids
        self.remove_words = ','.join(garbage_word_list)
        self.select_conf = select_conf
        self.filter_list = [f.candi_filter for f in select_conf.select_conf_list]
        self.price_list = [{'candi_filter':p.candi_filter, 'init_price':p.init_price} for p in select_conf.price_conf_list]

    def get_db_name(self):
        db_list = ['worker']
        db_count = len(db_list)
        return db_list[random.randint(0, db_count - 1)]

    def get_prjdata_list(self, db_name):
        '''
        获取所有任务
        '''
        result_list = []
        log.info('start: get project list,item_id=%s' % (self.item_id))
        self.cats.reverse()
        default_cat_cpc = random.randint(45, 65) # 防止出价一样，给用户体验不好
        for cat_id in self.cats:
            group_count = MemcacheAdpter.get_list_count(cat_id, 'kwlib')
            if not group_count:
                log.info('load cat data from database,item_id=%s,cat_id=%s' % (self.item_id, cat_id))
#                 CatWordLoader.get_keywords_by_cat(cat_id, 'kwlib')
                log.info('finish load cat data from database,item_id=%s,cat_id=%s' % (self.item_id, cat_id))
                group_count = MemcacheAdpter.get_list_count(cat_id, 'kwlib')
                if not group_count:
                    log.warn('get no cat data,cat_id=%s' % (cat_id))
                    continue
            cat_data = CatStatic.get_market_data_8id(cat_id)
            cat_cpc = cat_data.get('cpc', default_cat_cpc)
            if cat_cpc <= 5:
                cat_cpc = default_cat_cpc
            temp_list = [{'cats':self.cats, 'statu':'init', 'cat_cpc':cat_cpc, 'label_conf_list':self.label_conf_list,
                          'remove_words': self.remove_words, 'filter_conf':self.select_conf.candi_filter,
                          'filter_list':self.filter_list, 'price_list':self.price_list,
                          'item_id':str(self.item_id), 'type':'NewSelectWordWorker', 'from_db':'kwlib',
                          'from_key':'%s_%s' % (cat_id, ii), 'data_db':db_name,
                          'data_key':'%s_%s_%s' % (self.name, cat_id, ii)} for ii in range(group_count)]
            result_list.extend(temp_list)
        log.info(' end : get project list,item_id=%s' % (self.item_id))
        return result_list[0:250]

    def sum_prj_result(self, sub_prj_list, db_name):
        candi_kw_dict = {}
        key_list = []
        for prj in sub_prj_list:
            key_list.append(prj['data_key'])
        log.info('sum project result item_id=%s' % (self.item_id))
        worker_result_dict = CacheAdpter.get_many(key_list, db_name)
        # 汇总农民工的结果数据
        for temp_dict in worker_result_dict.values():
            for k, v in temp_dict.items():
                if not candi_kw_dict.has_key(k):
                    candi_kw_dict[k] = []
                candi_kw_dict[k].extend(v)
        # 汇总排序
        result_list = []
        filter_index = 0
        for filter in self.select_conf.select_conf_list:
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

        # result_list = remove_same_words(result_list) # 去除重复关键词 TODO wuhuaqiao 有问题，去重时重新排序，影响原来结果
        log.info('select keyword from kwlib,result=%s' % len(result_list))
        return result_list

def group_kwlist(kw_list, item_scorer, cat_id, cat_cpc, cats, remove_word_list, filter_conf, filter_list, price_list):
    group_dict = {}
    # 类目变量标准化
    c1, c2, c3, c4, c5, index = 0, 0, 0, 0, 0, 0
    for c_id in cats:
        if index == 0:
            c1 = int(c_id)
            index += 1
            continue
        elif index == 1:
            c2 = int(c_id)
            index += 1
            continue
        elif index == 2:
            c3 = int(c_id)
            index += 1
            continue
        elif index == 3:
            c4 = int(c_id)
            index += 1
            continue
        else:
            c5 = int(c_id)
    # 把条件表达式以及运算表达式编译好
    code_filter_conf = compile(filter_conf, '', 'eval')
    code_flter_list = []
    for filter in filter_list: # 初始化
        try:
            group_dict[filter] = []
            # 做类目预处理cat_id in (c1) and score=1000 and "P" in label，这种，如果类目对不上
            # 这条就不应该加入比较，只支持全and方式
            is_right = True
            if ('not' not in filter) and (' or ' not in filter) and ('cat_id' in filter): #
                test_list = filter.split('and')
                for tl in test_list:
                    if 'cat_id' in tl:
                        if not eval(tl):
                            is_right = False
                            break
            if is_right:
                code_flter_list.append(((compile(filter, '', 'eval')), filter))
        except Exception, e:
            log.error('select word filter error: filter=%s, e=%s' % (filter, e))
    if not code_flter_list:
        return group_dict
    code_price_list = []
    for p_conf in price_list:
        code_price_list.append({'candi_filter':compile(p_conf['candi_filter'], '', 'eval'), 'init_price':compile(p_conf['init_price'], '', 'eval')})

    # log.info('start group now ....')
    for kw in kw_list:
        word = kw[0]
        pure_word = word.replace(' ', '')
        is_need_remove = False
        for wd in remove_word_list:
            if wd in pure_word:
                is_need_remove = True
                break
        if is_need_remove:
            continue
        score, label = item_scorer.score_participles_by_item(pure_word) # 132000 2s
        pv, click, cpc, competition, ctr, roi, coverage, favtotal = kw[1], kw[2], kw[3], kw[4], kw[5], kw[7], kw[8], kw[9]
        # 根据配置判断是否满足海选条件
        if not eval(code_filter_conf):
            continue
        # 精选关键词
        default_kw_price = max(cpc * 0.8, 10) + random.randint(-5, 15)
        for filter in code_flter_list:
            if eval(filter[0]):
                new_price = default_kw_price
                for price_conf in code_price_list:
                    if eval(price_conf['candi_filter']):
                        new_price = eval(price_conf['init_price'])
                        break
                new_price = new_price or default_kw_price
                group_dict[filter[1]].append([word, pv, click, cpc, competition, ctr, cat_id, score, new_price, label, roi, coverage, favtotal])
                break
    # 去掉没有符合条件的k，v
    for k, v in group_dict.items():
        if not v:
            group_dict.pop(k)
    # log.info('group finish,len=%s' % len(kw_list))

    return group_dict


class NewSelectWordWorker(Worker):
    '''
    快速选词的农民工
    '''
    def __init__(self, prj_dict):
        self.prj_dict = prj_dict
        self.item_scorer = ItemScorer(prj_dict['label_conf_list'])
        self.cats = self.prj_dict['cats']
        self.filter_conf = self.prj_dict['filter_conf']
        self.filter_list = self.prj_dict['filter_list']
        self.price_list = self.prj_dict['price_list']
        self.remove_word_list = self.prj_dict['remove_words'] and self.prj_dict['remove_words'].split(',') or []
        self.cat_cpc = self.prj_dict['cat_cpc']

    def do_my_work(self):
        log.info('worker start, item_id=%s, key=%s' % (self.prj_dict['item_id'], self.prj_dict['data_key']))
        kw_list = CacheAdpter.get(self.prj_dict['from_key'], self.prj_dict['from_db'], [])
        if not kw_list:
            log.error('can not get group from memcache and the group is = %s' % self.prj_dict['from_key'])
            kw_list = CacheAdpter.get(self.prj_dict['from_key'], self.prj_dict['from_db'], [])
        group_dict = {}
        if kw_list:
            if ('click > 0' not in self.filter_conf) and ('click>0' not in self.filter_conf) or kw_list[0][2] > 0:
                cat_id = self.prj_dict['from_key'].split('_')[0]
                try:
                    group_dict = group_kwlist(kw_list, self.item_scorer, int(cat_id), self.cat_cpc, self.cats, self.remove_word_list, self.filter_conf, self.filter_list, self.price_list)
                except Exception, e:
                    log.error('group_kwlist error: cat_id=%s, e=%s' % (cat_id, e))
        CacheAdpter.set(self.prj_dict['data_key'], group_dict, self.prj_dict['data_db'])
        log.info('worker finish, item_id=%s, key=%s' % (self.prj_dict['item_id'], self.prj_dict['data_key']))

class SelectConfManage():
    @staticmethod
    def get_selectconf(item, select_type = '', conf_name = ''):
        '''
        根据item id以及选词场景获取选词的配置信息.依次从item、类目、父类、根类目、默认寻配置
        '''
        if not conf_name:
            conf_name = 'default_' + select_type + '_conf'
            if item.selectconf_dict.has_key(select_type):
                conf_name = item.selectconf_dict[select_type]
            else:
                cat_path_id = Cat.get_cat_attr_func(item.cat_id, "cat_path_id")
                if cat_path_id:
                    cat_list = cat_path_id.split(' ')
                    cat_list.reverse()
                    for cat_id in cat_list:
                        conf_dict = Cat.get_cat_attr_func(cat_id, "selectconf_dict")
                        if conf_dict and conf_dict.has_key(select_type):
                            conf_name = conf_dict[select_type]
                            break
                else:
                    log.error('can not find cat path id, cat_id = %s' % item.cat_id)
        try:
            conf = SelectConf.objects.get(conf_name = conf_name)
        except SelectConf.DoesNotExist:
            log.error('Can not find SelectConf! select_type=%s, conf_name=%s ' % (select_type, conf_name))
            return None

        return conf


def select_words(adgroup, item, select_conf, max_num = 600, is_mnt = False):
    '''
    选词。不同的配置，选择不同的词。select_conf为选词配置信息，analyse_conf为解析配置。adgroup、item支持各种标准信息获取方式
    '''
    from contractor import Contractor # 包比较乱，只能在这里导包
    result_list = []
    # 区分自定义标签词和修饰词(所有关键词排除产品词、卖点词、自定义词)
    if not select_conf:
        return result_list
    # contractor = NewSelectWordContractor(item.item_id, item, select_conf)
    # result_prj = contractor.start_prj()
    result_prj = Contractor(item.item_id, item, select_conf)()
    # 是否删除已有词、已删除词、重复词等
    needremove_dict, result_dict = {}, {}
    cur_count = 0
    if adgroup:
        if select_conf.delete_conf['remove_del'] == 1:
            for word in adgroup.deleted_word_list:
                needremove_dict[get_ordered_str(word)] = 1
        if select_conf.delete_conf['remove_cur'] == 1:
            for word in adgroup.select_word_list:
                needremove_dict[get_ordered_str(word)] = 1
        cur_count = len(adgroup.select_word_list)

    good_count = 0
    for kw in result_prj:
        temp_str = get_ordered_str(kw[0])
        if temp_str in needremove_dict or temp_str in result_dict:
            continue
        result_dict[temp_str] = 1
        if kw[7] == 1000:
            good_count += 1
        result_list.append(kw)

    better_count = get_word_num(is_mnt, good_count, cur_count)
    log.info('select word restult: adg_id:%s, item_id:%s, select_conf:%s, total_word:%s, after_rm_word:%s, good_count:%s, cur_count:%s, better_count:%s, max_num:%s'
             % (getattr(adgroup, 'adgroup_id', 0), getattr(item, 'item_id', 0), select_conf.conf_name, len(result_prj), len(result_list), good_count, cur_count, better_count, max_num))
    result_list = result_list[:min(max_num, better_count)]
    temp_list = transform_tuple_2tobj(result_list)
    return temp_list

class KeywordCrawler():

    @classmethod
    def crawl_word_by_word(cls, crawl_word, is_parse = False):
        '''
        .根据一个关键词进行爬词
        '''
        result_list, label_list, title = [], [], ''
        try:
            r = requests.get('https://suggest.taobao.com/sug?code=utf-8&q=%s&k=1&area=c2c&bucketid=7' % crawl_word)
            result = r.json()
            if 'result' in result:
                for word in result['result']:
                    wd = word[0]
                    wd = wd.replace('<b>', '')
                    wd = wd.replace('</b>', '')
                    result_list.append(wd)

                if is_parse and 'magic' in result and result_list:
                    magic = result['magic']
                    for mgc in magic:
                        wd = result_list[int(mgc['index']) - 1]
                        for dt in mgc['data']:
                            if type(dt) is list:
                                for d in dt:
                                    if d:
                                        title = d['title']
                                        result_list.append(wd + ' ' + d['title'])
                            else:
                                title = dt['title']
                                result_list.append(wd + ' ' + dt['title'])
                            if title:
                                label_list.append(title)
                    save_lable_list(label_list)

        except Exception, e:
            log.error('crawl word error and the error = %s' % e)
            return []

        return result_list

    @classmethod
    def crawl_words_by_word_list(cls, word_list, iter_max_len = 0):
        result_list, match_list, match_word = [], [], ''
        def iter_crawl_word(word):
            match_list.append(word)
            temp_list = cls.crawl_word_by_word(word, True)
            if temp_list:
                result_list.extend(temp_list)
                for temp in temp_list:
                    if temp in match_list:continue
                    if not match_word in temp: continue
                    if iter_max_len and len(result_list) >= iter_max_len:
                        break
                    iter_crawl_word(temp)

        for word in word_list:
            match_word = word
            iter_crawl_word(word)

        return list(set(result_list))


class WordFactory():

    @staticmethod
    def get_extend_words(cat_id, word_list):
        meta_word_list = MetaphorWord.get_metaword_list(cat_id, word_list)
        word_list.extend(meta_word_list)
        syno_word_list = SynonymWord.get_synonym_words(cat_id, word_list)
        word_list.extend(syno_word_list)
        return list(set(word_list))

    @staticmethod
    def extend_this_year(word_list, year_len = 3):
        this_year = datetime.date.today().year
        if str(this_year) not in word_list:
            for year in range(this_year - year_len, this_year):
                if str(year) in word_list:
                    word_list.append(str(this_year))
                    break
        return word_list
