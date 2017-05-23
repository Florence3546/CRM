# coding=UTF-8
import init_environ, datetime
from django.db import connection, transaction

def main():
    try:
        c = connection.cursor()
        # 收集多余订单
        print u'%s 检查重复订单。。' % datetime.datetime.now()
        unique_order_dict = {} # 格式为{order_id_article_code_item_code:1, ...}
        duplicate_sub_id_list = []
        sql = '''
        select a.id, a.order_id, a.article_code, a.item_code from ncrm_subscribe a join (
        select order_id from ncrm_subscribe where order_id>0 group by order_id, article_code, item_code having count(order_id)>1
        ) b on a.order_id=b.order_id order by a.operater_id desc
        '''
        c.execute(sql)
        query_result = c.fetchall()
        for sub_id, order_id, article_code, item_code in query_result:
            k = '%s_%s_%s' % (order_id, article_code, item_code)
            if k in unique_order_dict:
                duplicate_sub_id_list.append(sub_id)
            else:
                unique_order_dict[k] = 1
        print u'%s 多余订单%s笔' % (datetime.datetime.now(), len(duplicate_sub_id_list))

        # 删除多余订单
        if duplicate_sub_id_list:
            print u'%s 删除多余订单。。。' % datetime.datetime.now()
            sql = 'delete from ncrm_subscribe where id in (%s)' % (','.join(map(str, duplicate_sub_id_list)))
            c.execute(sql)
        print u'%s END' % datetime.datetime.now()
    except Exception, e:
        log.exception('%s', e)

if __name__ == '__main__':
    main()
