# coding=UTF-8
import init_environ
import pymongo
from apps.common.utils.utils_log import log
from apps.kwlib.models import KeywordClawer, KeywordInfo
import datetime
import time
from apps.kwlib.base import init_keyword


conn1 = pymongo.Connection('192.168.1.210:2222')
conn2 = pymongo.Connection('192.168.1.210:12345')
kwlib = conn1.kwlib
ztcjl4 = conn2.ztcjl4
# kwlib.authenticate('PS_kwlibAdmin', 'PS_managerKwlib')
kwlib.authenticate('lsc', 'lsc')
# ztcjl4.authenticate('PS_ztcjl4Admin', 'PS_managerZtcjl4')
knkw_coll = kwlib.kwlib_keywordinfo
sa_coll = ztcjl4.subway_account
sk_coll = ztcjl4.subway_keyword
start_index = sa_coll.find({'has_push':{'$in':[None, False]}}, {'_id':1}).sort('_id')[0]['_id']
end_index = sa_coll.find({'has_push':{'$in':[None, False]}}, {'_id':1}).sort('_id', -1)[0]['_id']
prev_index = None
count = 0
now_time = datetime.datetime.now()
while prev_index != end_index:
    count += 10
    add_in_list = []
    log.info('start push %s shop keyword to kwlib_new_keywordinfo' % count)
    shop_list = [shop['_id'] for shop in sa_coll.find({'_id':{'$gte':start_index}, 'has_push':{'$in':[None, False]}}, {'_id':1}).sort('_id').limit(count)]
    for shop_id in shop_list:
        keyword_list = [kw['word'] for kw in sk_coll.find({'shop_id':shop_id}, {'word'})]
        add_in_list.extend(keyword_list)
    add_in_list = KeywordInfo.check_kw_2save_inDB(add_in_list)
    add_in_list = [init_keyword(kw, now_time) for kw in add_in_list]
    if len(add_in_list) > 10000:
        add_len = len(add_in_list)
        for i in range(add_len / 10000 + 1):
            try:
                knkw_coll.insert(add_in_list[i * 10000:i * 10000 + 10000], continue_on_error = True, safe = True)
            except:
                pass
    else:
        try:
            knkw_coll.insert(add_in_list, continue_on_error = True, safe = True)
        except:
            pass
    sa_coll.update({'_id':{'$in':shop_list}}, {'$set':{'has_push':True}}, multi = True)
    log.info('push in kwlib keyword len = %s' % len(add_in_list))
    prev_index = start_index
    start_index = shop_list[len(shop_list) - 1]




