# coding=UTF-8
import init_environ
from apps.kwlib.models import WordCat, CatInfo
import datetime
from apps.kwlib.methods import get_catsworddata
import time
from apps.common.utils.utils_log import log


def update_word_cat(record_list, obj_id_list, wc_coll, count):
    word_list = [kw['word'] for kw in record_list]
    cat_word_data_dict = get_catsworddata(cat_id, word_list, datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days = 2), "%Y-%m-%d"), time.strftime("%Y-%m-%d"))
    for kw in record_list:
        if count % 10000 == 0:
            log.info('========================================================================finished count is = %s' % count)
        word = kw['word']
        if word in cat_word_data_dict:
            c_info = cat_word_data_dict[word]
            wc_coll.update({'_id':kw['_id']}, {'$set':{'c_pv':c_info['pv'], 'c_click':c_info['click'], 'c_ctr':c_info['ctr'], 'c_competition':c_info['competition'], 'c_cpc':c_info['cpc'], 'last_update_time':c_info['last_update_time']}})
        else:
            obj_id_list.append(kw['_id'])
        count += 1
    record_list = []
    if len(obj_id_list) >= 10000:
        wc_coll.update({'_id':{'$in':obj_id_list}}, {'$set':{'c_pv':0, 'c_click':0, 'c_ctr':0, 'c_competition':0, 'c_cpc':0}}, multi = True)
        obj_id_list = []
    return count, obj_id_list, record_list


cat_id_list = [cat['cat_id'] for cat in CatInfo._get_collection().find()]
record_list = []
obj_id_list = []
count = 0
wc_coll = WordCat._get_collection()
for cat_id in cat_id_list:
    log.info("start update cat_id is = %s" % cat_id)
    for kw in WordCat._get_collection().find({'cat_id':cat_id}).sort('_id'):
        cat_pv_ok_count = 0
        if len(record_list) < 5:
            record_list.append(kw)
            continue
        count, obj_id_list, record_list = update_word_cat(record_list, obj_id_list, wc_coll, count)
    count, obj_id_list, record_list = update_word_cat(record_list, obj_id_list, wc_coll, count)
    log.info("finished update cat_id is = %s" % cat_id)
