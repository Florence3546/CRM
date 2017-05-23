# coding=UTF-8
'''刷新所有customer的客户群相关字段'''
import init_environ
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple
from apps.ncrm.models import Customer, event_coll

def main():
    sql = 'select shop_id from ncrm_customer order by create_time desc'
    cus_rows = execute_query_sql_return_tuple(sql)
#     cus_rows = [(66247950,)]
    i = 0
    for cus in cus_rows:
        shop_id = cus[0]
        i += 1
        print i, shop_id
        update_dict = {}
        # 订单来源未知
        sql = "select id from ncrm_subscribe where shop_id=%s and biz_type=6" % shop_id
        rows = execute_query_sql_return_tuple(sql)
        if rows:
            update_dict['unknown_subscribe'] = True
        # 最新业务类型、到期日期
        sql = "select category, create_time, end_date from ncrm_subscribe where shop_id=%s and category not in ('zz', 'zx', 'other', 'seo', 'kfwb') order by create_time desc" % shop_id
        rows = execute_query_sql_return_tuple(sql)
        if rows:
            update_dict['latest_category'] = rows[0][0]
            update_dict['latest_end'] = rows[0][2]
            # 当前订单联系次数
            update_dict['contact_count'] = event_coll.find({'shop_id':shop_id, 'type':'contact', 'create_time':{'$gte':rows[0][1]}}).count()

#         # 打过差评
#         bad_comment_count = event_coll.find({'shop_id':shop_id, 'type':'comment', 'comment_type':{'$gte':200}}).count()
#         if bad_comment_count > 0:
#             update_dict['bad_comment'] = True
        # 最近联系日期
        cur = list(event_coll.find({'shop_id':shop_id, 'type':'contact'}, {'create_time':True}, sort = [('create_time', -1)]))
        if cur:
            update_dict['latest_contact'] = cur[0]['create_time'].date()
        # 最近操作日期
        cur = list(event_coll.find({'shop_id':shop_id, 'type':'operate'}, {'create_time':True}, sort = [('create_time', -1)]))
        if cur:
            update_dict['latest_operate'] = cur[0]['create_time'].date()

        # 更新数据库
        if update_dict:
            Customer.objects.filter(shop_id = shop_id).update(**update_dict)

if __name__ == "__main__":
    print 'refresh_customer_group_info begin'
    main()
    print 'end'