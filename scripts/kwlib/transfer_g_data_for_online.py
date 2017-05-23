# coding=UTF-8

import math
import datetime

import init_environ
from apps.common.biz_utils.utils_cacheadapter import GDataCacheAdapter
from apps.common.biz_utils.utils_tapitools import get_kw_g_data
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from pymongo.connection import Connection

py_conn = Connection(host = '10.241.51.158', port = 30001)
db = py_conn.kwlib
db.authenticate('PS_kwlibAdmin', 'PS_managerKwlib')
keyword_coll = db.kwlib_keyword_gdata

def get_keyword_list(start_index = 0, read_size = 1000):
    index = 0
    is_end = False
    while not is_end:
        kw_cursor = keyword_coll.find().\
                                sort('word').skip(start_index + index * read_size).limit(read_size)
        yield_list = [DictWrapper(kw) for kw in kw_cursor]
        if yield_list:
            yield yield_list
        else:
            is_end = True
        index += 1

def export_keyword_gdata(start_index, read_size, cache_unit = 1000, is_overwrite = False):
    def get_gdata_cachekey(kw):
        mark = "G_%s"
        return mark % kw.replace(' ', '')

    cache_adapter = GDataCacheAdapter(size = cache_unit)

    total_count = keyword_coll.count()
    sum_export = start_index + 0
    deal_count = 0
    msg = 'Total kw count : %s , time is %s' % (total_count, datetime.datetime.now())
    log_info_to_file(msg)

    for kw_list in get_keyword_list(start_index, read_size = read_size):
        cur_total = len(kw_list)
        cycle = int(math.ceil(cur_total * 1.0 / cache_unit))
        for index in xrange(cycle):
            origin_dict = {}
            alas_dict = {}
            for kw in kw_list[index * cache_unit:(index + 1) * cache_unit]:
                word = str(kw.word)
                origin_dict.update({word:kw})
                alas_dict.update({get_gdata_cachekey(word):word})

            g_data_dict = {}
            if not is_overwrite:
                cache_dict = cache_adapter.get_many(alas_dict.keys())
                for als_kw, g_data in cache_dict.items():
                    real_key = str(alas_dict[als_kw])
                    g_data_dict[real_key] = g_data

            store_dict = {}
            for kw, ori_data in origin_dict.items():
                word = str(kw)
                if word in g_data_dict:
                    cache_data = DictWrapper(g_data_dict[ word ])
                    if cache_data.g_pv > 0:
                        continue

                c_cache = {
                                "g_pv":ori_data.g_pv,
                                "g_click":ori_data.g_click,
                                "g_competition":ori_data.g_competition,
                                "g_cpc":ori_data.g_cpc
                           }
                store_dict[ get_gdata_cachekey(word) ] = c_cache

            if store_dict:
                cache_adapter.set_many(store_dict)

            deal_count += len(store_dict)
            sum_export += len(origin_dict)

        msg = 'Has finished  :  %s%% , finished count: %s , deal count : %s' % (round(sum_export * 100.0 / total_count, 2), sum_export, deal_count)
        log_info_to_file(msg)

    msg = "has finished, current time is %s" % (datetime.datetime.now())
    log_info_to_file(msg)


def log_info_to_file(msg , file_path = "d:\\ztcdata\\logs\\reload_gdata.txt", encoding = "GBK"):
    print unicode(msg)
    path, postfix = file_path.rsplit('.', 1)
    date_time = datetime.datetime.now().strftime('%Y%m%d')
    file_path = '%s_%s.%s' % (path, date_time, postfix)
    with open(file_path, 'a') as f:
        f.write('%s\n' % (msg.encode(encoding)))

if __name__ == "__main__":
    start_index = 0
    cache_unit = 1000
    read_size = cache_unit * 10
    is_overwrite = False
    export_keyword_gdata(start_index, read_size, cache_unit, is_overwrite)
#     print keyword_coll.count()

#     print get_kw_g_data(['半身裙秋A字裙'])
#     print get_kw_g_data(['男式靴子 冬'])
