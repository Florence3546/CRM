# coding=UTF-8
import redis
import datetime
import json
from apps.common.constant import Const
from apps.kwlib.langconv import Converter
import settings
from apps.kwslt.analyzer import ChSegement
from apps.kwslt.models_cat import Cat
from apps.kwlib.base import get_words_gdata, get_cats_forecast_new, \
    get_catsworddata, get_word_subdata
from apps.common.utils.utils_log import log
from apps.kwslt.base import remove_same_words
from apps.common.utils.utils_collection import genr_sublist
from apps.common.utils.utils_cacheadpter import CacheAdpter
# from apps.kwlib.models_mongodb import RequestAPIMonitor

class RedisConnectPool():
    connect_dict = {}
    conf_dict = settings.REDIS_CONF
    @classmethod
    def get_redis_connection(cls, *args, **kwargs):
        return redis.Redis(*args, **kwargs)

    @classmethod
    def get_redis(cls, conf):
        return cls.get_redis_connection(host = conf['host'], port = conf['port'], db = conf['db'], password = conf['password'])

    @classmethod
    def load_connect_dict(cls):
        if not cls.connect_dict:
            for key in cls.conf_dict:
                cls.connect_dict[key] = cls.get_redis(cls.conf_dict[key])
        return cls.connect_dict

    @classmethod
    def get_db_connect(cls, db_alias):
        if not db_alias in cls.conf_dict:
            log.error('please give 0-7 num to get db connect and you give db_alias = %s' % db_alias)
            return None
        cls.load_connect_dict()
        return cls.connect_dict[db_alias]

class RedisKeyManager():
    key_manager = 'keyword_list:manager'

    @classmethod
    def get_iter_len(cls, iter_list):
        tmp_list = []
        for iter_ in iter_list:
            if iter_.ready():
                continue
            else:
                tmp_list.append(iter_)
        return tmp_list

    @classmethod
    def get_key_manager(cls, prev_name = ''):
        return prev_name + cls.key_manager

    @classmethod
    def get_keyword_list_key(cls, db_alias , prev_name = ''):
        key_keyword_list = ''
        r = RedisConnectPool.get_db_connect(db_alias)
        key_list_manager = cls.get_key_manager(prev_name)
        left_key = r.lrange(key_list_manager, 0, 0)
        index = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S:%f')
        if left_key:
            key_keyword_list = left_key[0]
            list_size = r.llen(key_keyword_list)
            if list_size >= 10000:
                tmp_list = key_keyword_list.split('_')
#                 index = int(tmp_list[-1]) + 1
                key_keyword_list = '_'.join(tmp_list[:-1]) + '_' + str(index)
                r.lpush(key_list_manager, key_keyword_list)
        else:
            key_keyword_list = prev_name + 'keyword_list_' + index
            r.lpush(key_list_manager, key_keyword_list)
        return key_keyword_list

    @classmethod
    def clear_all_keyword_list(cls, db_alias, prev_name = ''):
        r = RedisConnectPool.get_db_connect(db_alias)
        cls.clear_all_keyword_by_db(r, prev_name)

    @classmethod
    def clear_all_keyword_by_db(cls, r, prev_name = ''):
        key_list_manager = cls.get_key_manager(prev_name)
        value_list = r.lrange(key_list_manager, 0, -1)
        if value_list:
            r.delete(*value_list)
        r.delete(key_list_manager)

    @classmethod
    def clear_single_keyword_list(cls, key, db_alias, prev_name = ''):
        r = RedisConnectPool.get_db_connect(db_alias)
        key_list_manager = cls.get_key_manager(prev_name)
        r.lrem(key_list_manager, key)
        r.delete(key)

    @classmethod
    def get_sort_word(cls, word):
        try:
            word_list = ChSegement.chsgm_keyword(word)
        except Exception, e:
            log.info("the error is = %s and the word is = %s" % (e, word))
            word_list = list(word)
        word_list.sort()
        return ''.join(word_list)

    @classmethod
    def redis_lpush(cls, r, key, args):
        if args:
            if not isinstance(args, list):
                args = [args]
            r.lpush(key, *args)

class KeywordInfo():

    GDATA_KW_LIST_PREV_KEY = 'g_data_'
    NEW_KW_LIST_PREV_KEY = 'new_'
    KW_LIST_PREV_KEY = ''

    GDATA_ALIAS = 'gdata'
    GKEYWORD_ALIAS = 'gkeyword'
    HKEYWORD_ALIAS = 'hkeyword'
    KEYWORD_ALIAS = 'keyword'
    NEWKEYWORD_ALIAS = 'nkeyword'
    SUBKEYWORD_ALIAS = 'subkeyword'

    r_gdata = RedisConnectPool.get_db_connect(GDATA_ALIAS)
    r_gkeyword = RedisConnectPool.get_db_connect(GKEYWORD_ALIAS)
    r_hkeyword = RedisConnectPool.get_db_connect(HKEYWORD_ALIAS)
    r_keyword = RedisConnectPool.get_db_connect(KEYWORD_ALIAS)
    r_nkeyword = RedisConnectPool.get_db_connect(NEWKEYWORD_ALIAS)
    r_skeyword = RedisConnectPool.get_db_connect(SUBKEYWORD_ALIAS)

    DATE_LIMIT = 7


    @classmethod
    def keyword_sort(cls, word):
        def sort_keyword(x, y):
            if x == y:
                return 1
            else:
                x_len, y_len = len(x), len(y)
                index = x_len >= y_len and y_len or x_len
                for i in range(index):
                    vv = cmp(x[i], y[i])
                    if vv == 0:
                        continue
                    elif vv == -1:
                        return -1
                    elif vv == 1:
                        return 1
                    else:
                        return 1
                return 1

        word_list = ChSegement.chsgm_keyword(word)
        word_list = sorted(word_list, cmp = sort_keyword)
        return ''.join(word_list)

    @classmethod
    def check_kw_2save_inDB(cls, word_list):
        add_kw_list = []
        check_word_dict = {}
        all_sign_dict = Const.COMMON_ALL_SIGN_DICT

        for word in word_list:
            if not word:
                continue
            conv = Converter("zh-hans") # 初始化字符集用于将繁体中文转化为简体中文
            try:
                word = conv.convert(word.decode('utf8')) # 将繁体中文转化为简体中文
                word = ChSegement.replace_white_space(word)
                if u'　'in word: # 去除一些带有特殊编码的字符
                    word = word.replace(u'　', ' ')
            except Exception, e:
                log.info('move words error is = %s,the word is=%s' % (e, word))
                continue
            if '<b>' in word: # 去除爬词获取到的b标签
                word = word.replace('<b>', '')
            if '</b>' in word:
                word = word.replace('</b>', ' ')
            if '",' in word: # 去除转换爬词结果的一些例外的格式
                wd_list = word.split('",') # 拆分这些结果
                wd_list = list(set(wd_list))
                if '' in wd_list:
                    wd_list.remove('')
                add_kw_list.extend(KeywordInfo.check_kw_2save_inDB(wd_list)) # 先自己审核一遍再往里面存
            if len(word) >= 15: # 如果关键词长度大于15则删除
                continue
            temp_word = ''
            for wd in word:
                if check_word_dict.has_key(wd):
                    temp_word += check_word_dict[wd]
                    continue
                # 如果改关键词做字符unicode编码范围内，并且属于有效字符，则加入到temp_word中
                if u'\u4e00' <= wd <= u'\u9fff' or u'0' <= wd <= u'9' or  u'a' <= wd <= u'z'  or  u'A' <= wd <= u'Z' or all_sign_dict['available_wd_dict'].has_key(wd):
                    temp_word += wd
                    check_word_dict[wd] = wd
                # 如果出现特殊字符则统一转换为空格
                elif all_sign_dict['unavailable_wd_dict'].has_key(wd):
                    temp_word += ' '
                    check_word_dict[wd] = ' '
                else:
                    check_word_dict[wd] = ''
            if not word or all_sign_dict['all'].has_key(temp_word) : # 如果清除完成只剩下一个字符或者同一个字符都属于特殊字符，如：.,....之类的关键词
                continue
            add_kw_list.append(temp_word.lower())
            # 返回过滤出来的结果
        return list(set(add_kw_list))

    @classmethod
    def alloc_task_keyword_list(cls, task_name = ''):
        if task_name == 'update_gdata':
            RedisKeyManager.clear_all_keyword_list(cls.GKEYWORD_ALIAS, cls.GDATA_KW_LIST_PREV_KEY)
        key_manager = 'keyword_list:manager'
        return cls.r_keyword.lrange(key_manager, 0, -1)

    @classmethod
    def alloc_task_new_keyword_list(cls):
        key_manager = 'new_keyword_list:manager'
        return cls.r_nkeyword.lrange(key_manager, 0, -1)

    @classmethod
    def load_redis_cat_new_word(cls, word_list):
        '''
        .导入新词有流量的数据做类目预测
        '''
        cat_dict = cls.update_local_cat_forcecats(word_list, WordCat.r_wckeyword)

        r = WordCat.r_wckeyword
        r.sadd('new_cat_word_set', *cat_dict.keys())

        for key in cat_dict:
            RedisKeyManager.redis_lpush(r, str(key) + '_new_word', cat_dict[key])

    @classmethod
    def load_redis_newcat_word_2memcache(cls):
        '''
        .实时导入新词数据到memcache
        '''
        from apps.kwslt.select_words import MemcacheAdpter
        r = WordCat.r_wckeyword
        for cat_id in r.smembers('new_cat_word_set'):
            count = MemcacheAdpter.get_list_count(str(cat_id), 'kwlib')
            word_list = [word.decode('utf8') for word in r.lrange('%s_new_word' % cat_id, 0, -1)]
            if  word_list:
                word_list = WordCat.get_wordcat_data_2memcache(word_list, cat_id)
                if count:
                    cache_word_list = CacheAdpter.get('%s_%s' % (cat_id, count - 1), 'kwlib')
                    if len(cache_word_list) < 4500:
                        word_list = cache_word_list + word_list
                        count = count - 1
                else:
                    count = 0
                for wl in genr_sublist(word_list, 4500):
                    CacheAdpter.set('%s_%s' % (cat_id, count), wl, 'kwlib')
                    count += 1

                CacheAdpter.set(str(cat_id), count, 'kwlib')
            r.delete('%s_new_word' % cat_id)
        r.delete('new_cat_word_set')

    @classmethod
    def format_gdata_2save_redis(cls, key, value_dict):
        ctr = value_dict['ctr']
        avg_pv, avg_cmpt = value_dict['pv'] / cls.DATE_LIMIT, value_dict['competition'] / cls.DATE_LIMIT
        pv, cmpt = (avg_pv == 0) and value_dict['pv']  or avg_pv, (avg_cmpt == 0) and value_dict['competition'] or avg_cmpt
        click = value_dict['click']
        if  click < cls.DATE_LIMIT:
            if  ctr:
                click = 1
                pv = int(1 / ctr * 100)
        else:
            click = click / cls.DATE_LIMIT
        value = ','.join([str(pv), str(click), str(value_dict['avg_price']), str(cmpt), str(ctr), str(value_dict['roi']), str(value_dict['coverage']), str(value_dict['favtotal']), str(value_dict['transactionshippingtotal'])])
        cls.r_gdata.setex(key, value, 60 * 24 * 60 * 60)
#         return {'pv':pv, 'click':click, 'cpc':value_dict['avg_price'], 'cmpt':cmpt, 'ctr':value_dict['ctr']}
        return {'pv':pv, 'click':click, 'cpc':value_dict['avg_price'], 'cmpt':cmpt, 'ctr':value_dict['ctr'], 'roi':value_dict['roi'], 'coverage':value_dict['coverage'], 'favtotal':value_dict['favtotal'], 'transactionshippingtotal':value_dict['transactionshippingtotal']}

    @classmethod
    def update_gdata(cls, word_list):
        '''
        .更新全网数据,数据压缩成'pv,click,cpc,cometition,ctr',取出数据时则需要替换一下
        '''
        today = datetime.date.today()
        time_scope = cls.get_gdata_timescope()
        word_dict = {}
        if word_list:
            word_dict = get_words_gdata(word_list, time_scope)
#             RequestAPIMonitor.insertDocument(len(word_list), len(word_dict), 1, u'更新全网数据地方')
        word_list = []
        for key in word_dict:
            cls.format_gdata_2save_redis(key, word_dict[key])
            cls.r_hkeyword.hset(RedisKeyManager.get_sort_word(key), 'upt_tm', str(today))
            word_list.append(key)
        if word_list:
            key_keyword_list = RedisKeyManager.get_keyword_list_key(cls.GKEYWORD_ALIAS, cls.GDATA_KW_LIST_PREV_KEY)
            RedisKeyManager.redis_lpush(cls.r_gkeyword, key_keyword_list, word_list)

        return word_list

    @classmethod
    def update_g_data_by_keyword(cls, key):
        '''
        .刷新所有关键词的全网数据
        '''
        word_list = [kw.split(':')[0].decode('utf8') for kw in cls.r_keyword.lrange(key, 0, -1)]
        cls.update_gdata(word_list)

    @classmethod
    def get_insert_list(cls, word_list):
        word_list = cls.check_kw_2save_inDB(word_list)
        forbid_list = [fbd.word for fbd in Cat.get_attr_by_cat(0, 'forbid_list')]
        today = str(datetime.date.today())
        insert_list = []
        for kw in word_list:
            if not kw:
                continue
            kw_list = ChSegement.chsgm_keyword(kw)
            if u'的' in kw_list: # 这里不去除kw_list中的"的" 这样如果出现包含"的"的关键词  取出数据是不包含"的"的数据
                kw = kw.replace(u'的', '')
            kw_list.sort()
            tmp_word = ''.join(kw_list)
            if cls.r_hkeyword.exists(tmp_word):
                continue
            else:
#                 is_forbid, out_of_order = False, False
                is_forbid = False
                for wd in kw_list:
                    if wd in forbid_list:
                        is_forbid = True
                        break
#                     if not wd in kw:
#                         out_of_order = True
                if is_forbid:
                    continue
#                 if out_of_order:
#                     kw = ' '.join(kw_list) #待验证
#                     kw = kw
                cls.r_hkeyword.hmset(tmp_word, {'kw':kw.strip(), 'upt_tm':today, 'cat_list':''})
                insert_list.append(kw)
        return insert_list

    @classmethod
    def insert_new_word_list(cls, word_list):
        '''
        .插入新的关键词
        '''
        insert_list = cls.get_insert_list(word_list)
        if insert_list:
            for word_list in genr_sublist(insert_list, 10000):
                key_keyword_list = RedisKeyManager.get_keyword_list_key(cls.NEWKEYWORD_ALIAS, cls.NEW_KW_LIST_PREV_KEY)
                RedisKeyManager.redis_lpush(cls.r_nkeyword, key_keyword_list, word_list)

    @classmethod
    def update_new_keyword(cls, key):
        '''
        .将新加入到词库的关键词刷新到词库
        '''
        insert_list = []
        word_list = [kw.decode('utf8') for kw in cls.r_nkeyword.lrange(key, 0, -1)]
        cls.update_gdata(word_list)
        for word in word_list:
            insert_list.append(word + ':' + RedisKeyManager.get_sort_word(word))
        key_keyword_list = RedisKeyManager.get_keyword_list_key(cls.KEYWORD_ALIAS)
        RedisKeyManager.redis_lpush(cls.r_keyword, key_keyword_list, insert_list)
        RedisKeyManager.clear_single_keyword_list(key, cls.NEWKEYWORD_ALIAS, cls.NEW_KW_LIST_PREV_KEY)

    @classmethod
    def update_keyword_tokenizer(cls):
        '''
        .关键词分词器修改之后,刷新整个数据
        '''
        key_list = cls.alloc_task_keyword_list()
        for key in key_list:
            word_list = cls.r_keyword.lrange(key, 0, -1)
            count = 0
            for word in word_list:
                word = word.decode('utf8')
                tmp_list = word.split(':')
                wd , sort_word = tmp_list[0], tmp_list[1]
                tmp_word = RedisKeyManager.get_sort_word(wd)
                if sort_word != tmp_word:
                    cls.r_keyword.lset(key, count, wd + ':' + tmp_word)
                    cls.r_hkeyword.rename(sort_word, tmp_word)
                count += 1

    @classmethod
    def clean_garbage_word(cls, key):
        '''
        .清除长时间没有获取到全网数据的关键词
        '''
        word_list = [kw.decode('utf8') for kw in cls.r_keyword.lrange(key, 0, -1)]
        insert_list, delete_list = [], []
        for word in word_list:
            tmp_list = word.split(':')
            wd, sort_word = tmp_list[0], tmp_list[1]
            min_update_time = datetime.datetime.now() - datetime.timedelta(days = 200)
            update_time = cls.r_hkeyword.hget(sort_word, 'upt_tm')
            if update_time == None:
                delete_list.append(sort_word)
                continue
            if not cmp(datetime.datetime.strptime(update_time, "%Y-%m-%d"), min_update_time):
                delete_list.append(sort_word)
                continue
            else:
                insert_list.append(wd + ':' + sort_word)

        cls.r_hkeyword.delete(*delete_list)
        cls.r_keyword.delete(key)
        for word_list in genr_sublist(insert_list, 10000):
            key_keyword_list = RedisKeyManager.get_keyword_list_key(cls.NEWKEYWORD_ALIAS, cls.NEW_KW_LIST_PREV_KEY)
            RedisKeyManager.redis_lpush(cls.r_nkeyword, key_keyword_list, word_list)

    @classmethod
    def clean_gdata_timescope(cls):
        cls.r_gkeyword.delete('start_date')
        cls.r_gkeyword.delete('end_date')

    @classmethod
    def get_gdata_timescope(cls):
        start_date = cls.r_gkeyword.get('start_date')
        end_date = cls.r_gkeyword.get('end_date')
        if not start_date or not end_date:
            today = datetime.date.today()
            start_date = str(today - datetime.timedelta(days = KeywordInfo.DATE_LIMIT))
            end_date = str(today - datetime.timedelta(days = 1))
            cls.r_gkeyword.set('start_date', start_date)
            cls.r_gkeyword.set('end_date', end_date)
        return (start_date, end_date)


    @classmethod
    def get_gdata_by_words(cls, word_list):
        '''
        .共享有流量的数据
        '''
        result_dict, value_list, kw_list = {}, [], []
        word_list = [word.decode('utf8') for word in word_list]
        for word in word_list:
            word = cls.r_hkeyword.hget(RedisKeyManager.get_sort_word(word), 'kw')
            if not word :
                word = ''
            kw_list.append(word.decode('utf8'))
        if kw_list:
            value_list = cls.r_gdata.mget(kw_list)
        count = 0
        gdata_tb_list = []
        word_dict = {}
        for value in value_list:
            if value:
                vl_list = value.split(',')
#                 value = ','.join([str(pv), str(click), str(value_dict['avg_price']), str(cmpt), str(ctr), str(value_dict['roi']), str(value_dict['coverage']), str(value_dict['favtotal']), str(value_dict['transactionshippingtotal'])])
                value = {'pv':int(vl_list[0]), 'click':int(vl_list[1]), 'cpc':float(vl_list[2]) or 30, 'cmpt':int(vl_list[3]), 'ctr':float(vl_list[4]), 'roi':float(vl_list[5]), 'coverage':float(vl_list[6]), 'favtotal':float(vl_list[7]), 'transactionshippingtotal':int(vl_list[8])}
            else:
                gdata_tb_list.append(word_list[count])
            result_dict[word_list[count]] = value
            count += 1
        timescope = cls.get_gdata_timescope()
        if gdata_tb_list:
            word_dict = get_words_gdata(gdata_tb_list, timescope)
#             RequestAPIMonitor.insertDocument(len(gdata_tb_list), len(word_dict), 1, u'全网数据共享位置')
        for word in gdata_tb_list:
            value = '0,0,0.0,0,0.0,0.0,0.0,0,0'
            tmp_word = ChSegement.replace_white_space(word)
            if word in word_dict:
                result_dict[word] = cls.format_gdata_2save_redis(word, word_dict[word])
            else:
                sort_word = RedisKeyManager.get_sort_word(word)
                result_dict[word] = {'pv':0, 'click':0, 'cpc':0.0, 'cmpt':0, 'ctr':0.0, 'roi':0.0, 'coverage':0.0, 'favtotal':0, 'transactionshippingtotal':0}
                cls.r_gdata.setex(tmp_word, value, 1 * 24 * 60 * 60)
                cls.r_hkeyword.hmset(sort_word, {'kw':tmp_word})
                cls.r_hkeyword.expire(sort_word, 1 * 24 * 60 * 60)
        cls.insert_new_word_list(word_dict.keys())
        return result_dict

    @classmethod
    def update_local_cat_forcecats(cls, word_list, r_wc):
        result_dict = get_cats_forecast_new(word_list)
        cat_dict = {}
        for key in result_dict:
            for cat_id in result_dict[key]:
                if cat_id in cat_dict:
                    cat_dict[cat_id].append(key)
                else:
                    cat_dict[cat_id] = [key]
        r_wc.sadd('cat_set', *cat_dict.keys())
        for cat_id in cat_dict:
            key_keyword_list = RedisKeyManager.get_keyword_list_key(WordCat.WCKW_ALIAS, str(cat_id) + '_')
            RedisKeyManager.redis_lpush(r_wc, key_keyword_list, cat_dict[cat_id])
        return cat_dict

    @classmethod
    def update_cat_forcecats(cls, key):
        '''
        .类目预测
        '''
        r_wc = WordCat.r_wckeyword
        word_list = [wd.decode('utf8') for wd in KeywordInfo.r_gkeyword.lrange(key, 0, -1)]
        cls.update_local_cat_forcecats(word_list, r_wc)
        return len(word_list)


    @classmethod
    def set_label_list(cls, label_list):
        cls.r_keyword.sadd('label_set', *label_list)

    @classmethod
    def get_subdata(cls, word_list, sub_type):
        redis_dict , tb_list = cls.get_subdata_by_redis(word_list, sub_type)
        taobao_dict = cls.get_subdata_by_taobao(tb_list, sub_type)
        redis_dict.update(taobao_dict)
        return redis_dict

    @classmethod
    def parse_tb_data_2ztcjl_data(cls, value):
        result = {}
        for vv in value:
            del vv['bidword']
            key = str(vv['network'])
            del vv['network']
            vv['pv'] = vv['impression']
            result[key] = vv
        return result

    @classmethod
    def multi_dict_value_addtion(cls, d1, d2):
        result = {}
        for key in d1.keys():
            result[key] = d1[key] + d2[key]
        # result['ctr'] = result['pv'] and result['click'] * 1.0 / result['pv']
        # result['cpc'] = result['click'] and result['cost'] * 1.0 / result['click']
        # result['roi'] = result['cost'] and (result['directtransaction'] + result['indirecttransaction']) * 1.0 / result['cost']
        # result['coverage'] = result['click'] and result['transactionshippingtotal'] * 1.0 / result['click']
        # 淘宝本身返回的站内报表，不是按照上面的数据计算的，所以废弃上面的计算方式。又因为站内报表占了大部分数据，以站内数据为准。
        result['ctr'] = d1['ctr']
        result['cpc'] = d1['cpc']
        result['roi'] = d1['roi']
        result['coverage'] = d1['coverage']

        return result

    @classmethod
    def get_default_dict(cls, d):
        default_dict = {
             "pv": int(d.get("pv", 1)),
             "click":int(d.get("click", 0)),
             "cost": int(d.get("cost", 0)),
             "directtransaction": int(d.get("directtransaction", 0)),
             "indirecttransaction":int(d.get("indirecttransaction", 0)),
             "directtransactionshipping":int(d.get("directtransactionshipping", 0)),
             "indirecttransactionshipping":int(d.get("indirecttransactionshipping", 0)),
             "favitemtotal":int(d.get("favitemtotal", 0)),
             "favshoptotal":int(d.get("favshoptotal", 0)),
             "transactionshippingtotal":int(d.get("transactionshippingtotal", 0)),
             "transactiontotal":int(d.get("transactiontotal", 0)),
             "favtotal":float(d.get("favtotal", 0)),
             "competition":int(d.get("competition", 0)),
             "ctr":float(d.get("ctr", 0.0)),
             "cpc":float(d.get("cpc", 0)),
             "roi":float(d.get("roi", 0.0)),
             "coverage":float(d.get("coverage", 0.0)),
             "mechanism":int(d.get("mechanism", 0)),
        }
        return default_dict

    @classmethod
    def get_sub_data_key(cls, word):
        kw = cls.r_hkeyword.hget(RedisKeyManager.get_sort_word(word), 'kw')
        if not kw:
            kw = word
        else:
            kw = kw.decode('utf8').strip()
        return kw + "_sub_data_pc", kw + "_sub_data_mobile"

    @classmethod
    def save_tb_data_2redis(cls, word, pc_data, mobile_data, time = 7 * 24 * 60 * 60):
        key_list = 'pv,click,cost,competition,ctr,cpc,roi,coverage,directtransaction,indirecttransaction,directtransactionshipping,indirecttransactionshipping,favitemtotal,favshoptotal,transactionshippingtotal,transactiontotal,favtotal,mechanism'.split(',')
        pc_list, mobile_list = [], []
        for key in key_list:
            p_data = pc_data.get(key, 0)
            m_data = mobile_data.get(key, 0)
            if not key in ['ctr', 'cpc', 'roi', 'coverage']:
                p_data = p_data / cls.DATE_LIMIT
                m_data = m_data / cls.DATE_LIMIT
                if key == 'pv':
                    if p_data == 0:
                        p_data = 1
                    if m_data == 0:
                        m_data = 1
            pc_list.append(str(p_data))
            mobile_list.append(str(m_data))
        pc_key, mobile_key = cls.get_sub_data_key(word)
        cls.r_skeyword.setex(pc_key, ','.join(pc_list), time)
        cls.r_skeyword.setex(mobile_key, ','.join(mobile_list), time)

    @classmethod
    def get_subdata_by_taobao(cls, word_list, sub_type):
        result = {}
        if not word_list:
            return result
        pc_data, mobile_data, result_dict = {}, {}, {}
        time = 0
        today = datetime.date.today()
        start_date = str(today - datetime.timedelta(days = KeywordInfo.DATE_LIMIT))
        end_date = str(today - datetime.timedelta(days = 1))
        if word_list:
            result_dict = get_word_subdata(word_list , start_date , end_date)
#             RequestAPIMonitor.insertDocument(len(word_list), len(result_dict), 2, u'细分数据共享位置')
        for word in word_list:
            if word in result_dict:
                tmp_dict = cls.parse_tb_data_2ztcjl_data(result_dict[word])
                pc_x = cls.get_default_dict(tmp_dict.get('1', {}))
                pc_y = cls.get_default_dict(tmp_dict.get('2', {}))
                mobile_x = cls.get_default_dict(tmp_dict.get('4', {}))
                mobile_y = cls.get_default_dict(tmp_dict.get('5', {}))
                pc_data = cls.multi_dict_value_addtion(pc_x, pc_y)
                mobile_data = cls.multi_dict_value_addtion(mobile_x, mobile_y)
                time = 7 * 24 * 60 * 60
            else:
                time = 7 * 24 * 60 * 60
                pc_data = cls.get_default_dict({})
                mobile_data = cls.get_default_dict({})
            if sub_type == 0:
                result[word] = mobile_data
            elif sub_type == 1:
                result[word] = pc_data
            else:
                result[word] = cls.multi_dict_value_addtion(pc_data, mobile_data)
            cls.save_tb_data_2redis(word, pc_data, mobile_data, time)
        cls.insert_new_word_list(result_dict.keys())
        return result

    @classmethod
    def get_subdata_by_key(cls, word_list, result_list):
        result = {}
        tb_list = []
        index = 0
        for rslt in result_list:
            word = word_list[index]
            if rslt:
                redis_dict = cls.parse_subdata_from_redis(rslt)
                result[word] = redis_dict
            else:
                tb_list.append(word)
            index += 1

        return result, tb_list

    @classmethod
    def get_total_subdata(cls, mobile_dict, pc_dict):
        result = {}
        for key in mobile_dict:
            if not key in pc_dict:
                pc_dict[key] = cls.get_default_dict({})
            result[key] = cls.multi_dict_value_addtion(pc_dict[key], mobile_dict[key])
        return result

    @classmethod
    def get_subdata_by_redis(cls, word_list, sub_type):
        result = {}
        tb_list = []
        pc_key_list , mobile_key_list = [], []
        pc_result_list, mobile_result_list = [], []
        for word in word_list:
            pc_key, mobile_key = cls.get_sub_data_key(word)
            pc_key_list.append(pc_key)
            mobile_key_list.append(mobile_key)
        try:
            if sub_type == 0:
                mobile_result_list = cls.r_skeyword.mget(mobile_key_list)
                result, tb_list = cls.get_subdata_by_key(word_list, mobile_result_list)
            elif sub_type == 1:
                pc_result_list = cls.r_skeyword.mget(pc_key_list)
                result, tb_list = cls.get_subdata_by_key(word_list, pc_result_list)
            else:
                mobile_result_list = cls.r_skeyword.mget(mobile_key_list)
                mobile_dict, mobile_list = cls.get_subdata_by_key(word_list, mobile_result_list)
                pc_result_list = cls.r_skeyword.mget(pc_key_list)
                pc_dict, pc_list = cls.get_subdata_by_key(word_list, pc_result_list)
                tb_list = list(set(mobile_list + pc_list))
                result = cls.get_total_subdata(mobile_dict, pc_dict)
        except Exception, e:
            log.error("get redis sub data error and the error=%s" % e)
            return result, word_list

        return result, tb_list

    @classmethod
    def parse_subdata_from_redis(cls, data):
        key_list = 'pv,click,cost,competition,ctr,cpc,roi,coverage,directtransaction,indirecttransaction,directtransactionshipping,indirecttransactionshipping,favitemtotal,favshoptotal,transactionshippingtotal,transactiontotal,favtotal,mechanism'.split(',')
        redis_dict = {}
        data_list = data.split(',')
        index = 0
        for key in key_list:
            redis_dict[key] = data_list[index]
            index += 1
        return cls.get_default_dict(redis_dict)

class WordCat():
    WCDATA_ALIAS = 'wcdata'
    WCDKEYWORD_ALIAS = 'wcdkeyword'
    WCKW_ALIAS = 'wckeyword'

    r_wcdata = RedisConnectPool.get_db_connect(WCDATA_ALIAS)
    r_wcdkeyword = RedisConnectPool.get_db_connect(WCDKEYWORD_ALIAS)
    r_wckeyword = RedisConnectPool.get_db_connect(WCKW_ALIAS)

    @classmethod
    def clean_wordcat_keyword(cls, db_alias):
        '''
        .清空所有的类目数据
        '''
        r_wc = RedisConnectPool.get_db_connect(db_alias)
        cat_set = r_wc.smembers('cat_set')
        for cat_id in cat_set:
            RedisKeyManager.clear_all_keyword_list(db_alias, str(cat_id) + '_')
        r_wc.delete('cat_set')

    @classmethod
    def get_task_4update(cls):
        '''
        .刷新类目数据时需要获取的key
        '''
        cat_set = cls.r_wckeyword.smembers('cat_set')
        cls.clean_wordcat_keyword(cls.WCDKEYWORD_ALIAS)
        key_list = []
        for cat_id in cat_set:
            key_list.extend(cls.r_wckeyword.lrange(str(cat_id) + '_keyword_list:manager', 0, -1))
        return key_list

    @classmethod
    def update_wordcat_data(cls, key):
        '''
        .刷新类目数据
        '''
        word_list = [wd.decode('utf8') for wd in cls.r_wckeyword.lrange(key, 0, -1)]
        cat_id_str = str(key.split('_')[0])
        today = datetime.date.today()
        cat_data_dict = get_catsworddata(cat_id_str, word_list, str(today - datetime.timedelta(days = 7)), str(today - datetime.timedelta(days = 1)))
        key_keyword_list = RedisKeyManager.get_keyword_list_key(cls.WCDKEYWORD_ALIAS, cat_id_str + '_')
        value_list = []
        for cat_data in cat_data_dict:
            value_dict = cat_data_dict[cat_data]
            value1 = {'pv':value_dict['pv'], 'click':value_dict['click'], 'cpc':value_dict['cpc'], 'cmpt':value_dict['competition'], 'ctr':value_dict['ctr'], 'word':value_dict['word']}
            value2 = (value_dict['word'], value_dict['pv'], value_dict['click'], value_dict['cpc'], value_dict['competition'], value_dict['ctr'],)
            value1 = json.dumps(value1)
            value2 = json.dumps(value2)
            value_list.append(value2)
            cls.r_wcdata.set(cat_id_str + ':' + cat_data, value1)
        RedisKeyManager.redis_lpush(cls.r_wcdkeyword, key_keyword_list, value_list)

    @classmethod
    def get_wordcat_data_2memcache(cls, word_list, cat_id):
        kw_list, count = [], 0
        result_list = KeywordInfo.r_gdata.mget(word_list)
        for result in result_list :
            if result :
                result = result.split(',')
                kw_list.append((word_list[count], int(result[0]), int(result[1]), float(result[2]), int(result[3]), float(result[4]), int(cat_id), float(result[5]), float(result[6]), int(result[7])))
            count += 1
        kw_list = remove_same_words(kw_list)
        return kw_list

    @classmethod
    def load_data_2memcache(cls):
        from apps.kwslt.select_words import  MemcacheAdpter
        '''
        .将数据导入到memcached当中
        .0:pv,1:click,2:cpc,3:cmpt,4:ctr,5:roi,6:coverage,7:favtotal,8:transactionshippingtotal
        '''
        cat_set = cls.r_wckeyword.smembers('cat_set')
        for cat_id in cat_set:
            log.info('start load cat data 2 memcache and the cat_id=%s' % cat_id)
            manager_key = '%s_keyword_list:manager' % cat_id
            word_list, kw_list = [], []
            for key in cls.r_wckeyword.lrange(manager_key, 0, -1):
                word_list.extend([word.decode('utf8') for word in cls.r_wckeyword.lrange(key, 0, -1)])
            kw_list = cls.get_wordcat_data_2memcache(word_list, cat_id)
            MemcacheAdpter.set_large_list(str(cat_id), kw_list, 'kwlib', 24 * 60 * 60 * 60)
            log.info('end load cat data 2 memcache and the cat_id=%s and len=%s' % (cat_id, len(kw_list)))
        return len(cat_set)

    @classmethod
    def get_wordcat_data(cls, cat_id, word_list):
        '''
        .共享类目有流量的数据
        '''
        result_dict = {}
        sort_list = [str(cat_id) + ':' + RedisKeyManager.get_sort_word(word) for word in word_list]
        result_list = cls.r_wcdata.mget(sort_list)
        count = 0
        for result in result_list:
            if result:
                result_dict[word_list[count]] = json.loads(result)
            else:
                result_dict[word_list[count]] = {}
            count += 1
        return result_dict

class SortLimit():
    def __init__(self, coll, start_index, prev_index, group_size, filter_dict, *args, **kwargs):
        if not start_index:
            start_index = coll.find(kwargs, filter_dict).sort(*args).limit(1)[0]['_id']
        self.coll = coll
        self.args = args
        self.start_index = start_index
        self.query_dict = kwargs
        self.filter_dict = filter_dict
        self.prev_index = prev_index
        self.group_size = group_size

    def get_record_list(self, rtn_attr, is_reverse = False):
        result_list = []
        record = None
        if is_reverse:
            str_order = '$lte'
        else:
            str_order = '$gte'
        self.query_dict['_id'] = {str_order:self.start_index}
        for record in self.coll.find(self.query_dict, self.filter_dict).sort(*self.args).limit(self.group_size):
            result_list.append(record[rtn_attr])
        self.prev_index = self.start_index
        if record:
            self.start_index = record['_id']
        return result_list
