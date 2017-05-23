# coding=UTF-8
from __future__ import absolute_import
from celery import shared_task
from celery._state import current_task
import time
import datetime
import apps.kwlib.celery # @UnusedImport
from apps.subway.models_account import account_coll
from apps.subway.models_keyword import kw_coll # @UnresolvedImport
from apps.kwlib.models_redis import KeywordInfo, RedisKeyManager, WordCat
from apps.common.utils.utils_log import log
from apps.kwlib.base import get_cats_forecast_new, get_cat_top_word, \
    get_tb_recommend_keywords, get_relatewords_new
from apps.kwslt.models_character import Character
from apps.kwslt.analyzer import ChSegement
from apps.kwslt.select_words import KeywordCrawler
from apps.kwslt.models_cat import cat_coll, Cat
from apps.kwslt.base import get_catinfo_new
from apps.subway.models_adgroup import adg_coll


@shared_task
def add(x, y):
    print(current_task.backend)
    return x + y

@shared_task
def add_user_keyword(shop_id):
    word_list = []
    word_list.extend([kw['word'] for kw in kw_coll.find({'shop_id':shop_id}, {'word'})])
    KeywordInfo.insert_new_word_list(word_list)
    account_coll.update({'_id':shop_id}, {'$set':{'has_push':True}}, multi = True)
    return 1

@shared_task
def update_gdata_keyword(key):
    word_list = [kw.split(':')[0].decode('utf8') for kw in KeywordInfo.r_keyword.lrange(key, 0, -1)]
    KeywordInfo.update_gdata(word_list)
    return len(word_list)

@shared_task
def update_new_keyword(key):
    '''
    .将新加入到词库的关键词刷新到词库
    '''
    insert_list = []
    word_list = [kw.decode('utf8') for kw in KeywordInfo.r_nkeyword.lrange(key, 0, -1)]
    result_list = KeywordInfo.update_gdata(word_list)
    KeywordInfo.load_redis_cat_new_word(result_list)
    for word in word_list:
        insert_list.append(word + ':' + RedisKeyManager.get_sort_word(word))
    key_keyword_list = RedisKeyManager.get_keyword_list_key(KeywordInfo.KEYWORD_ALIAS)
    RedisKeyManager.redis_lpush(KeywordInfo.r_keyword, key_keyword_list, insert_list)
    RedisKeyManager.clear_single_keyword_list(key, KeywordInfo.NEWKEYWORD_ALIAS, KeywordInfo.NEW_KW_LIST_PREV_KEY)
    return len(word_list)

@shared_task
def update_keyword_tokenizer(key):
    '''
    .关键词分词器修改之后,刷新整个数据
    '''
    word_list = KeywordInfo.r_keyword.lrange(key, 0, -1)
    count = 0
    today = str(datetime.date.today())
    for word in word_list:
        word = word.decode('utf8')
        tmp_list = word.split(':')
        wd , sort_word = tmp_list[0], tmp_list[1]
        tmp_word = RedisKeyManager.get_sort_word(wd)
        if sort_word != tmp_word:
            KeywordInfo.r_keyword.lset(key, count, wd + ':' + tmp_word)
            try:
                KeywordInfo.r_hkeyword.rename(sort_word, tmp_word)
            except Exception, e: # @UnusedVariable
                log.info('miss key and word is = %s:%s' % (tmp_word, wd))
                KeywordInfo.r_hkeyword.hmset(tmp_word, {'kw':wd, 'upt_tm':today, 'cat_list':''})
                pass
        count += 1
    return len(word_list)

@shared_task
def update_cat_forcecats(key):
    '''
    .类目预测
    '''
    result = KeywordInfo.update_cat_forcecats(key)
    return result

@shared_task
def get_recommand_word(record_list):
    '''
    .获取宝贝推荐词
    '''
    word_list = []
    for  record in record_list:
        word_list.extend(get_tb_recommend_keywords(record['shop_id'], record['_id']))
        if len(word_list) >= 10000:
            KeywordInfo.insert_new_word_list(word_list)
            word_list = []
    return len(record_list)

@shared_task
def get_cat_top(cat_id):
    '''
    .获取类目top词
    '''
    start_date = datetime.date.today()
    word_list = get_cat_top_word(cat_id , str(start_date - datetime.timedelta(days = 7)), str(start_date - datetime.timedelta(days = 1)))
    KeywordInfo.insert_new_word_list(word_list)
    return len(word_list)



class TaskTools():

    @classmethod
    def monitor_result(cls, monitor_str, result_list):
        '''
        .监控执行任务的进度
        '''
        total_len = len(result_list)
        while result_list:
            for result in result_list:
                if result.ready():
                    result_list.remove(result)
                    log.info(monitor_str % (len(result_list), total_len))
            time.sleep(15)

    @classmethod
    def add_user_keyword(cls):
        '''
        .添加用户的关键词
        '''
        result_list = []
        shop_id_list = [acct['_id'] for acct in account_coll.find({'has_push':{'$in':[None, False]}}, {'_id':1})]
        for shop_id in shop_id_list:
            result_list.append(add_user_keyword.delay(shop_id))
        total = len(result_list)
        cls.monitor_result('add user keyword now len = %s and total len = %s', result_list)
        return total

    @classmethod
    def update_new_words(cls):
        '''
        .执行刷新新词数据
        '''
        result_list = []
        for key in KeywordInfo.r_nkeyword.lrange(RedisKeyManager.get_key_manager(KeywordInfo.NEW_KW_LIST_PREV_KEY), 0, -1):
            result_list.append(update_new_keyword.delay(key))
        total = len(result_list)
        cls.monitor_result('update new keyword now len = %s and total len = %s', result_list)
        KeywordInfo.load_redis_newcat_word_2memcache()
        return total

    @classmethod
    def update_words(cls):
        '''
        .执行刷新全网数据
        '''
        RedisKeyManager.clear_all_keyword_list(KeywordInfo.GKEYWORD_ALIAS, KeywordInfo.GDATA_KW_LIST_PREV_KEY)
        KeywordInfo.clean_gdata_timescope()
        KeywordInfo.get_gdata_timescope()
        result_list = []
        for key in  KeywordInfo.r_keyword.lrange(RedisKeyManager.get_key_manager(), 0, -1):
            result_list.append(update_gdata_keyword.delay(key))
        total = len(result_list)
        cls.monitor_result('update all keyword now len = %s and total len = %s', result_list)
        return total

    @classmethod
    def update_forcecats(cls):
        '''
        .执行类目预测
        '''
        WordCat.clean_wordcat_keyword(WordCat.WCKW_ALIAS)
        result_list = []
        for key in KeywordInfo.r_gkeyword.lrange(RedisKeyManager.get_key_manager(KeywordInfo.GDATA_KW_LIST_PREV_KEY), 0, -1):
            result_list.append(update_cat_forcecats.delay(key))
        total = len(result_list)
        cls.monitor_result('update cat forcecats now len = %s and total len = %s', result_list)
        return total

    @classmethod
    def backup_db3_all_keyword(cls):
        '''
        .备份db3当中的所有关键词,备份之前一定要删除原来备份的数据。
        '''
        import settings, redis
        conf = settings.REDIS_CONF['gdata']
        r = redis.Redis(host = conf['host'], port = conf['port'], db = 13, password = conf['password'])
        RedisKeyManager.clear_all_keyword_by_db(r)
        manager_list = KeywordInfo.r_keyword.lrange(RedisKeyManager.get_key_manager(), 0, -1)
        for key in manager_list :
            r.lpush(key, *[kw.decode('utf8') for kw in KeywordInfo.r_keyword.lrange(key, 0, -1)])

        r.lpush(RedisKeyManager.get_key_manager(), *manager_list)

    @classmethod
    def insert_word_list(cls, word_list):
        word_list = list(set(word_list))
        insert_list = KeywordInfo.get_insert_list(word_list)
        if insert_list:
#                 relate_word_list = get_relatewords_new(insert_list)
#                 log.info('get relate word from taobao and word_list len = %s ' % len(relate_word_list))
            KeywordInfo.insert_new_word_list(insert_list)

    @classmethod
    def crawl_by_character_or_elemword(cls):
        '''
        .根据汉字原子词进行爬词
        '''
        result_list = []
        ChSegement.get_word_dict()
        label_list = [word.decode('utf8') for word in KeywordInfo.r_keyword.smembers('label_set')]
        word_list = Character.get_all_character() + ChSegement.word_dict.keys() + label_list
        count, total = 0 , len(word_list)
        for word in word_list:
            count += 1
            result_list.extend(KeywordCrawler.crawl_word_by_word(word, True))
            if len(result_list) >= 10000:
                log.info('crawl word  index = %s and total len = %s' % (count, total))
                cls.insert_word_list(result_list)
                result_list = []
        cls.insert_word_list(result_list)

    @classmethod
    def crawl_by_elemword(cls):
        result_list = []
        ChSegement.get_word_dict()
        label_list = [word.decode('utf8') for word in KeywordInfo.r_keyword.smembers('label_set')]
        word_list = list(set(ChSegement.word_dict.keys() + label_list))
        count, total = 0 , len(word_list)
        for word in word_list:
            count += 1
            tmp_list = KeywordCrawler.crawl_words_by_word_list([word], 10000)
            log.info('crawl word  index = %s and total len = %s and word = %s and crawl_result_len = %s' % (count, total, word, len(tmp_list)))
            result_list.extend(tmp_list)
            if len(result_list) >= 10000:
                log.info('craw words more than 10000')
                cls.insert_word_list(result_list)
                result_list = []
        cls.insert_word_list(word_list)

    @classmethod
    def crawl_by_all_keyword(cls):
        '''
        .根据所有的关键词进行爬词
        '''
        result_list = []
        manager_list = KeywordInfo.r_keyword.lrange(RedisKeyManager.get_key_manager(), 0, -1)
        total_len, count = len(manager_list), 0
        for key in manager_list:
            count += 1
            word_list = [kw.split(':')[0].decode('utf8') for kw in KeywordInfo.r_keyword.lrange(key, 0, -1)]
            log.info('crawl word = %s count index = %s and total len = %s' % (len(word_list), count, total_len))
            for word in word_list:
                result_list.extend(KeywordCrawler.crawl_word_by_word(word, True))
                if len(result_list) >= 10000:
                    result_list = list(set(result_list))
                    KeywordInfo.insert_new_word_list(result_list)
                    result_list = []
        KeywordInfo.insert_new_word_list(result_list)

    @classmethod
    def import_keyword_2redis(cls, file_path):
        '''
        .从文本文件内导入数据到redis当中
        '''
        with open(file_path, 'r') as r_file:
            word_list = []
            while True:
                word = r_file.readline()
                if not word:
                    break
                word = word.decode('gbk').strip('\r\n')
                word_list.append(word)
            word_list = list(set(word_list))
            KeywordInfo.insert_new_word_list(word_list)

    @classmethod
    def get_cat_top_words(cls):
        '''
        .获取到类目下的top词
        '''
        result_list = []
        cat_id_list = WordCat.r_wckeyword.smembers('cat_set')
        if not cat_id_list or len(cat_id_list) < 10000:
            cat_id_list = [cat['_id']  for cat in cat_coll.find({}, {'_id':1})]
        for cat_id in cat_id_list:
            result_list.append(get_cat_top.delay(cat_id))
        cls.monitor_result('add cat top words now len = %s and total len = %s', result_list)

    @classmethod
    def update_all_cat(cls):
        '''
        .更新所有的类目脚本
        '''
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
        old_cat_id_list = [cat['_id'] for cat in cat_coll.find({}, {'_id':1})]
        new_cat_id_list, insert_list = [], []
        for cat in all_cat_list:
            cat_id = cat['cat_id']
            new_cat_id_list.append(cat_id)
            if cat_id in old_cat_id_list:
                cat_coll.update({'_id':cat_id}, {'$set':{
                                                           'cat_name':cat['cat_name'],
                                                           'parent_cat_id':cat['parent_cat_id'],
                                                           'cat_level':cat['cat_level'],
                                                           'cat_path_name':cat['cat_path_name'],
                                                           'cat_path_id':cat['cat_path_id'],
                                                           'last_sync_time':cat['last_sync_time']
                                                           }})
            else:
                insert_list.append({
                                    '_id':cat_id,
                                    'cat_name':cat['cat_name'],
                                    'parent_cat_id':cat['parent_cat_id'],
                                    'cat_level':cat['cat_level'],
                                    'cat_path_name':cat['cat_path_name'],
                                    'cat_path_id':cat['cat_path_id'],
                                    'last_sync_time':cat['last_sync_time']
                                    })
        remove_list = list(set(old_cat_id_list) - set(new_cat_id_list))
        if 0 in remove_list:
            remove_list.remove(0)
        try:
            cat_coll.insert(insert_list, continue_on_error = True, safe = True)
        except:
            pass
        cat_coll.remove({'_id':{'$in':remove_list}})
        Cat.compute_child_list()

    @classmethod
    def add_all_recommand_words(cls):
        word_list, count = [], 0
        for adg in adg_coll.find({'has_push':{'$in':[None, False]}}, {'shop_id':1}, timeout = False):
            adg_coll.update({'_id':adg['_id']}, {'$set':{'has_push':True}})
            try:
                word_list.extend([kw['word'] for kw in get_tb_recommend_keywords(adg['shop_id'], adg['_id'])])
            except Exception, e:
                log.error('can not get tapi and the error is =%s' % e)
                pass
            if len(word_list) >= 10000:
                log.info('now get recommand words index is = %s' % count)
                KeywordInfo.insert_new_word_list(word_list)
                word_list = []
            count += 1
        KeywordInfo.insert_new_word_list(word_list)

