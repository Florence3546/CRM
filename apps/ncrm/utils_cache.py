# coding=UTF-8

from apps.common.biz_utils.utils_cacheadapter import CrmCacheAdapter
from apps.ncrm.utils_query_builder import *

SHOP_IDS_SIZE = 1000
ncrm_cache = CrmCacheAdapter(size = SHOP_IDS_SIZE)

def get_consult_ids_byquerier(psuser_id, query_statement):
    """通过查询器获取到查询信息"""
    statement_key = "QUERIER_STATEMENT_%s" % (psuser_id)
    shop_ids_key = "QUERIER_SHOP_IDS_%s" % (psuser_id)

    query_statement = query_statement.strip()
    cache_query_statement = ncrm_cache.get(statement_key)
    is_reset = False if query_statement == cache_query_statement else True

    reason = ""
    if is_reset:
        shop_list, reason = query_enter(query_statement)
        if not reason:
            ncrm_cache.set_large_list(shop_ids_key, shop_list)
            ncrm_cache.set(statement_key, query_statement)
    else:
        shop_list = ncrm_cache.get_large_list(shop_ids_key)

    return shop_list, reason

def get_consult_ids_bycache(psuser_id):
    """通过查询器获取到查询信息"""
    shop_ids_key = "QUERIER_SHOP_IDS_%s" % (psuser_id)
    return ncrm_cache.get_large_list(shop_ids_key)

if __name__ == "__main__":
    query_statement = """
       is_kcjl and is_qn and surplus > 5 and subscribe > 30 and last_order_status == 2 and last_pay > 100 and total_pay>800 and order_count > 4 and roi_7 > 0
    """
    import time
    start = time.clock()
    psuser_id = 1132
    x, err = get_consult_ids_byquerier(psuser_id, query_statement)
    print len(x)
    print 'exec time  :  ', time.clock() - start
    print 'data : ', x
    print query_statement_info()
