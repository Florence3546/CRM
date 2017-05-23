# coding=utf-8

import csv
import MySQLdb
import sys
sys.path.append("../")
import init_environ
from apps.ncrm.models import Customer

"""
说一下总体思路，从S3上导出tp_tpcustomer与tp_order表
导到ncrm中的ncrm_customer与ncrm_subscribe

customer中缺少shop_id，并且原来的order表中与customer关联的是tpcustomer_id
而要导入的表中，customer与subscribe却关联的是shop_id
除此之外，订单表中，还涉及到员工，有些员工可能无法找到？或者有些数据问题

需要解决的问题是：
1，先导出tp_tpcustomer，tp_order，auth_user
2，tp_tpcustomer批量获取shop_id
3，将tp_order的关联由tpcustomer_id改成shop_id
4，根据auth_user旧表中的id换成nick
5，根据psuser表生成nick_to_id的字典
6，将旧表中的id绑定成新的id
4，将tp_customer的数据格式转成ncrm_customer并导入
5，将tp_order的数据格式转成ncrm_subscribe并导入
"""

# s3conn = MySQLdb.Connect(host = '10.200.175.246', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl3_tp')
# w3conn = MySQLdb.Connect(host = '10.200.175.246', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl4')

s3conn = MySQLdb.Connect(host = '127.0.0.1', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl3_tp')
w3conn = MySQLdb.Connect(host = '127.0.0.1', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl4')

writer_dict = {}

def get_writer(failed_type):
    global writer_dict
    writer = writer_dict.get(failed_type , None)
    if not writer:
        FILE_PATH = 'd:/ztcdata/failed_%s.csv' % failed_type
        try:
            writer = csv.writer(open(FILE_PATH, 'w'), lineterminator = '\n')
        except Exception, e:
            print e
            return None
        writer_dict.update({failed_type:writer})
    return writer

def get_data(cursor, sql):
    cursor.execute(sql)
    result_list = []
    for i in cursor.fetchall():
        result_list.append(i)
    return result_list

def get_tpcustomers():
    cursor = s3conn.cursor()
    sql = """select id,nick,cname,tel,qq,ww,ztc_id,ztc_psw,lz_id,lz_psw,
             status,note,edit_time,create_time from tp_tpcustomer"""
    return get_data(cursor, sql)

def get_tporders():
    cursor = s3conn.cursor()
    sql = "select tpcustomer_id,saler_id,money,start_date,end_date,note,create_time,operator_id from tp_order"
    return get_data(cursor, sql)


def get_newid_byoldid():
    cursor = s3conn.cursor()
    sql = "select id, username from auth_user" # TODO: wangqi 20141208 修改表名
    id_2nick_dict = dict(get_data(cursor, sql))

    w3cursor = w3conn.cursor()
    sql = "select name, id from ncrm_psuser"
    nick_2id_dict = dict(get_data(w3cursor, sql))

    oldid_2newid_dict = {}
    for old_id, nick in id_2nick_dict.items():
        oldid_2newid_dict.update({int(old_id): int(nick_2id_dict.get(nick, 0))})
    # TODO: wangqi 20141208 这里可以选择一个公共账户，将找不到客户的数据处理掉
    return oldid_2newid_dict


def get_nick2shop_dict():
    """找出目前已有的nick与shop_id字典"""
    cursor = w3conn.cursor()
    sql = "select nick, shop_id from ncrm_customer"
    return dict(get_data(cursor, sql))

def insert_customer(customer_dict):
    old_count, new_count, failed_list = 0, 0, []
    def setattr_4obj(obj, attr, value):
        if value != '':
            setattr(obj, attr, value)

    field_list = ['seller', 'phone', 'qq', 'ww', 'ztc_name', 'ztc_psw', 'lz_name', 'lz_psw', 'acct_status', 'note']
    insert_list = []
    for customer in customer_dict.values():
        try:
            if customer.pop('is_new'):
                new_count += 1
                insert_list.append(customer)
            else:
                old_count += 1
                cust_obj = Customer.objects.get(shop_id = customer['shop_id'])
                for field in field_list:
                    setattr_4obj(cust_obj, field, customer[field])
                cust_obj.save()
        except:
            pass

    if insert_list:
        insert_field_list = ['shop_id', 'nick', 'seller', 'phone', 'qq', 'ww', 'ztc_name', 'ztc_psw', 'lz_name', 'lz_psw', 'acct_status', 'note', 'update_time', 'create_time']
        insert_sql = """insert into ncrm_customer(shop_id, nick, seller, phone, qq, ww, ztc_name, ztc_psw, lz_name, lz_psw, acct_status, note, update_time, create_time)
                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        cursor = w3conn.cursor()

        for insert_obj in insert_list:
            try:
                insert_tuple = [insert_obj[field] for field in insert_field_list]
                cursor.execute(insert_sql, insert_tuple)
            except Exception, e:
                writer = get_writer('customer')
                if writer:
                    writer.writerow(insert_tuple)
                print e

        w3conn.commit()

    return old_count, new_count, failed_list


def insert_order(order_list):
    insert_count, failed_list = 0, []
    insert_field_list = ['shop_id', 'psuser_id', 'pay', 'cycle', 'biz_type', 'start_date', 'end_date', 'note', 'create_time', 'operater_id', 'article_code', 'article_name']
    if order_list:
        insert_sql = """insert into ncrm_subscribe(order_id, shop_id, psuser_id, pay, cycle, biz_type, start_date, end_date, note, create_time, operater_id, article_code, article_name)
                        values(0, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        cursor = w3conn.cursor()
        for insert_obj in order_list:
            try:
                insert_tuple = [insert_obj[field] for field in insert_field_list]
                cursor.execute(insert_sql, insert_tuple)
                insert_count += 1
            except Exception, e:
                writer = get_writer('order')
                if writer:
                    writer.writerow(insert_tuple)
                print e

        w3conn.commit()
    return insert_count, failed_list

def export_data_from_tpm_main():
    print u'1st, 获取新旧ID映射列表'
    id_dict = get_newid_byoldid()
    invalid_nick_list = []
    customer_dict = {}

    print u'2nd, 获取TPM客户'
    tpcustomer_list = get_tpcustomers()
    nick2shop_dict = get_nick2shop_dict()

    for tc in tpcustomer_list:
        is_new = False
        nick = tc[1].strip()
        shop_id = int(nick2shop_dict.get(nick, 0))
        if not shop_id:
            is_new = True
            shop_id = Customer.get_shop_by_nick(nick)
            if not shop_id:
                invalid_nick_list.append(nick)
                continue

        customer_dict.update({tc[0]:{'shop_id':shop_id, 'nick':tc[1], 'seller':tc[2],
                             'phone':tc[3], 'qq':tc[4], 'ww':tc[5], 'ztc_name':tc[6],
                             'ztc_psw':tc[7], 'lz_name':tc[8], 'lz_psw':tc[9],
                             'acct_status':tc[10] == 'dead' and 1 or 0, 'note':tc[11],
                             'update_time':tc[12], 'create_time':tc[13], 'is_new': is_new}})

    print u'3rd, 总客户数:%s, 需导入客户数：%s, 无效客户数：%s' % (len(tpcustomer_list), len(customer_dict), len(invalid_nick_list))

    invalid_order_list = []
    order_list = []
    tporder_list = get_tporders()
    for to in tporder_list:
        customer_obj = customer_dict.get(to[0], None)
        if not customer_obj:
            invalid_order_list.append(to)
        else:
            order_list.append({'shop_id': customer_obj['shop_id'], 'psuser_id':id_dict[to[1]], 'pay':int(to[2]) * 100, 'start_date':to[3], 'end_date':to[4],
                               'note':to[5], 'create_time':to[6], 'cycle':'', 'biz_type':1, 'operater_id':id_dict[to[7]], 'article_code':'tp-001', 'article_name':'直通车托管'})

    print u'4th, 总订单数：%s, 需导入数：%s, 无效订单数：%s' % (len(tporder_list), len(order_list), len(invalid_order_list))

    old_count, new_count, cust_failed_list = insert_customer(customer_dict)
    insert_count, order_failed_list = insert_order(order_list)
    print u'5th, 导入完成，customer新增%s个，更新%s个，失败%s个； subscribe新增%s个，失败%s个' % (new_count, old_count, len(cust_failed_list), insert_count, len(order_failed_list))


if __name__ == '__main__':
    export_data_from_tpm_main()
