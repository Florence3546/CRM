# coding=UTF-8

import datetime, time

from apilib.parsers import TopObjectParser
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_log import log
from apps.kwlib.models_redis import KeywordInfo
from apps.kwslt.analyzer import ChSegement
from apps.kwslt.models_cat import cat_coll, Cat, CatStatic, cat_static_coll
from apps.kwslt.base import cat_data_list, get_catinfo_new

"""
新版api调用函数接口
"""

def worker_work(prj_dict, request = None):
    '''
    农民工工作
    '''
    try:
        from apps.kwslt.select_words import NewSelectWordWorker
        worker = eval(prj_dict['type'])(prj_dict)
        worker.work()
    except Exception, e:
        log.error('error=%s' % e)


def update_all_cats_new(record_list, manager):
    """

    """
    all_cat_list = []
    cat_dict = get_catinfo_new(0)
    all_cat_list.extend(cat_dict.values())

    def get_sub_cats_new(cat_id_list):
        cat_sub_dict = get_catinfo_new(2, [str(cat_id) for cat_id in cat_id_list])
        if cat_sub_dict:
            cat_id_list = cat_sub_dict.keys()
            all_cat_list.extend(cat_sub_dict.values())
            get_sub_cats_new(cat_id_list)

    get_sub_cats_new(cat_dict.keys())
    old_cat_id_list = [cat['cat_id'] for cat in record_list]
    new_cat_id_list, insert_list = [], []
    for cat in all_cat_list:
        cat_id = cat['cat_id']
        new_cat_id_list.append(cat_id)
        if cat_id in old_cat_id_list:
            cat_coll.update({'_id':cat_id}, {'$set':{
                                                       'cat_name':cat['cat_name'],
                                                       'parent_cat_id':cat['parent_cat_id'],
                                                       'cat_level':cat['cat_level']
                                                       }})
        else:
            insert_list.append({
                                '_id':cat_id,
                                'cat_name':cat['cat_name'],
                                'parent_cat_id':cat['parent_cat_id'],
                                'cat_level':cat['cat_level']
                                })
    remove_list = list(set(old_cat_id_list) - set(new_cat_id_list))
    try:
        cat_coll.insert(insert_list, continue_on_error = True, safe = True)
    except:
        pass
    cat_coll.remove({'_id':{'$in':remove_list}})

    manager.write_log('update_all_cats success, total %s cats' % (len(new_cat_id_list)))
    return len(record_list)


def get_gdata_word(word_list, request = None):
    """
    .共享数据api接口
    """
    result_dict = {'result':{}}
    if word_list:
        try:
            log.info('start get  gdata by word and word_len = %s' % (len(word_list)))
            result_dict['result'] = KeywordInfo.get_gdata_by_words(word_list)
            log.info('end get  gdata by word and return word_list ,result_dict len = %s' % len(result_dict['result']))
        except Exception, e:
            log.error('get share gdata error , the error is = %s,words=%s' % (e, ','.join(word_list)))
    return request and result_dict or TopObjectParser.json_to_object(result_dict)

def get_keyword_subdata(word_list, sub_type = 0, request = None):
    """
    args:
        word_list : [u'连衣裙',u'红色连衣裙'......]
        sub_type : 0 无线     1  PC   -1 汇总

    return
        {
             pv: 展现量
             click：点击量
             cost： 花费，单位（分）
             directtransaction： 直接成交金额
             indirecttransaction：间接成交金额
             directtransactionshipping：直接成交笔数
             indirecttransactionshipping：间接成交笔数
             favitemtotal：宝贝搜藏数
             favshoptotal：店铺搜藏数
             transactionshippingtotal：总的成交笔数
             transactiontotal：成交总金额
             favtotal：总的收藏数，包括宝贝收藏和店铺收藏
             competition：竞争度
             ctr：点击率
             cpc：平均点击花费
             roi：投入产出比
             coverage：点击转化率
             mechanism：投放机制:0:关键词推广 2：定向推广 3：通用定向
        }
    """
    result_dict = {'result':{}}
    try:
        log.info('start get  subdata by word and word_len = %s' % (len(word_list)))
        result_dict['result'] = KeywordInfo.get_subdata(word_list, sub_type)
        log.info('end get  subdata by word and return word_list ,result_dict len = %s' % len(result_dict['result']))
    except Exception, e:
        log.error('get subdata gdata error , the error is = %s,words=%s' % (e, ','.join(word_list)))
    return request and result_dict or TopObjectParser.json_to_object(result_dict)



def analyzer_words(words, item_id = 0, shop_id = 0, request = None):
    result_dict, word_list = {}, []
    try:
        word_list = ChSegement.chsgm_words(words)
    except Exception, e:
        log.error('analyze words error , the error is = %s and the item_id = %s , shop_id = %s' % (e, item_id, shop_id))
    result_dict['result'] = word_list
    return request and result_dict or TopObjectParser.json_to_object(result_dict)


def check_kw_2save_inDB(word_list):
    return KeywordInfo.check_kw_2save_inDB(word_list)

def save_lable_list(label_list):
    if label_list:
        KeywordInfo.set_label_list(label_list)

def get_timescope():
    return KeywordInfo.get_gdata_timescope()
