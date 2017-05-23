# coding=utf-8

import csv
import MySQLdb
# import init_environ
# from apps.ncrm.models import ClientGroup

"""
1.备份现网数据库ztcjl4
2.导出ztcjl4到本地
3.到tpm数据导本地到ztcjl3
4.拷贝ztcjl3的tp_tpcutomer，tp_order到ztcjl4
5.拷贝192.168.1.250的shop_information表到ztcjl4
6.执行该脚本
7.测试
8清空现网ncrm表
9.上传所有ncrm表到现网数据库
"""


conn = MySQLdb.Connect(host = '127.0.0.1', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl4')
cursor = conn.cursor()

def get_data(sql):
    cursor.execute(sql)
    result_list = []
    for i in cursor.fetchall():
        result_list.append(i)
    return result_list

def auto_submit(func):
    def commit():
        print 'current func is %s' % func.__name__
        sql = func()
        cursor.execute(sql)
        conn.commit()
    return commit

@auto_submit
def copy_crm_psuser():
    return """
        insert into ncrm_psuser (name,name_cn,password,type,perms,ww,qq,phone,manager,cat_ids,now_load,cycle_load,weight,create_time,note,consult_type)
        select
        name,name_cn,password,type,perms,ww,qq,phone,manager,cat_ids,now_load,cycle_load,weight,create_time,note,consult_type
        from crm_psuser"""


@auto_submit
def copy_crm_customer():
    return """insert into ncrm_customer (shop_id,nick,is_b2c,credit,address,seller,phone,qq,ww,lz_name,lz_psw,ztc_name,ztc_psw,create_time,source,acct_status,info_status)
             select c.shop_id as shop_id,c.nick as nick,if(a.last_name = 'c',0,1 ) as is_b2c,
                if(a.credit<=10,1,
                if(a.credit>=11 and a.credit<=40,2,
                if(a.credit>=41 and a.credit<=90,3,
                if(a.credit>=91 and a.credit<=150,4,
                if(a.credit>=151 and a.credit<=250,5,
                if(a.credit>=251 and a.credit<=500,6,
                if(a.credit>=501 and a.credit<=1000,7,
                if(a.credit>=1001 and a.credit<=2000,8,
                if(a.credit>=2001 and a.credit<=5000,9,
                if(a.credit>=5001 and a.credit<=10000,10,
                if(a.credit>=10001 and a.credit<=20000,11,
                if(a.credit>=20001 and a.credit<=50000,12,
                if(a.credit>=50001 and a.credit<=100000,13,
                if(a.credit>=100001 and a.credit<=200000,14,
                if(a.credit>=200001 and a.credit<=500000,15,
                if(a.credit>=500001 and a.credit<=1000000,16,
                if(a.credit>=1000001 and a.credit<=2000000,17,
                if(a.credit>=2000001 and a.credit<=5000000,18,
                if(a.credit>=5000001 and a.credit<=10000000,19,
                if(a.credit>=10000001,20,0
             ))))))))))))))))))))
              as credit,a.f6 as address,c.cname as seller,c.phone as phone,c.qq as qq,c.ww as ww,
                c.lz_id as lz_name,c.lz_psw as lz_psw,c.ztc_id as ztc_name,c.ztc_psw as ztc_psw,c.create_time as create_time,'' as source,0 as acct_status,0 as info_status
                 from crm_customer c left join auth_user a on c.nick=a.username"""

@auto_submit
def update_categoty():
    return """update ncrm_customer c,shop_information s set c.category=s.server where c.shop_id=s.shop_id"""

@auto_submit
def update_address():
    return """update ncrm_customer c,shop_information s set c.address=s.address where c.shop_id=s.shop_id and c.address is null and s.address<>''"""

@auto_submit
def update_address2():
    return """update ncrm_customer c,shop_information s set c.address=s.address where c.shop_id=s.shop_id and c.address='' and s.address<>''"""

@auto_submit
def update_seller():
    return """update ncrm_customer c,shop_information s set c.seller=s.seller_name where c.shop_id=s.shop_id and c.seller ='' and s.seller_name <>''"""

@auto_submit
def update_phone():
    return """update ncrm_customer c,shop_information s set c.phone=s.seller_tel where c.shop_id=s.shop_id and c.phone ='' and s.seller_tel <>''"""


@auto_submit
def insert_customer_4shop_info():
    return """insert into ncrm_customer (shop_id,nick,is_b2c,credit,address,seller,phone,qq,create_time,source,acct_status,info_status)
            select
            shop_id as shop_id,wangwang_id as nick,is_tm as is_b2c,
            if(credit='s_red_1',1,
            if(credit='s_red_2',2,
            if(credit='s_red_2',3,
            if(credit='s_red_3',4,
            if(credit='s_red_4',5,
            if(credit='s_blue_1',6,
            if(credit='s_blue_2',7,
            if(credit='s_blue_3',8,
            if(credit='s_blue_4',9,
            if(credit='s_blue_5',10,
            if(credit='s_cap_1',11,
            if(credit='s_cap_2',12,
            if(credit='s_cap_3',13,
            if(credit='s_cap_4',14,
            if(credit='s_cap_5',15,
            if(credit='s_crown_1',16,
            if(credit='s_crown_2',17,
            if(credit='s_crown_3',18,
            if(credit='s_crown_4',19,
            if(credit='s_crown_5',20,0
            ))))))))))))))))))))
            as credit,address as address,seller_name as seller,seller_tel as phone,qq as qq,create_time as create_time,'' as source,0 as acct_status,fetch_status as info_status
              from shop_information where shop_id not in (select shop_id from ncrm_customer) group by shop_id;"""

@auto_submit
def copy_soft_subscribe():
    return """insert into ncrm_subscribe(shop_id, order_id, article_name, article_code, item_code, item_name, create_time, start_date, end_date, `cycle`, biz_type, pay)
select cc.shop_id, ra.order_id, ra.article_name, ra.article_code, ra.item_code, ra.item_name, ra.`create`, ra.order_cycle_start, ra.order_cycle_end, ra.order_cycle, ra.biz_type, ra.total_pay_fee from router_articlebizorder ra
join ncrm_customer cc on cc.nick = ra.nick"""

@auto_submit
def update_rjjh_subscribe():
    return """insert into ncrm_subscribe (shop_id,create_time,psuser_id,note,order_id,article_code,article_name,
            item_code,item_name,pay,cycle,biz_type,start_date,end_date,operater_id)
            select shop_id,create_time,psuser_id,note,order_id,'ts-25811-6' as article_code,article_name,
            item_code,item_name,pay,cycle,biz_type,start_date,end_date,operater_id from ncrm_subscribe where item_code='ts-25811-6'"""

@auto_submit
def update_rjjh_subscribe2():
    return """update ncrm_subscribe set pay=0 where article_code='ts-25811' and item_code='ts-25811-6'"""

@auto_submit
def update_rjjh_subscribe3():
    return """update ncrm_subscribe s,(select n.id,c.shop_id from crm_customer c left join crm_psuser p on c.tp_rjjh_id=p.id left join ncrm_psuser n on p.name_cn=n.name_cn where c.tp_rjjh_id<>'') t
              set s.operater_id=t.id where s.article_code='ts-25811-6' and s.item_code='ts-25811-6' and s.shop_id=t.shop_id"""

@auto_submit
def copy_remark_to_contact():
    return """insert into ncrm_contact (shop_id,psuser_id,contact_type,create_time,is_initiative,note)
            select
             c.shop_id as shop_id,n.id as psuser_id,'ww' as contact_type,r.mark_time as create_time,
            1 as is_initiative,r.mark_content as note
             from crm_remark r left join crm_customer c on r.customer_id=c.id left join ncrm_psuser n on r.mark_author=n.name_cn"""

@auto_submit
def update_subscribe_operater():
    return """update ncrm_subscribe s,
            (select o.shop_id,p.id from
            (select c.shop_id,cp.name_cn from
            crm_customer c left join crm_psuser cp on c.consult_id=cp.id where c.consult_id<>'') o
             left join ncrm_psuser p on o.name_cn=p.name_cn) t
            set s.operater_id=t.id
             where s.shop_id=t.shop_id and s.order_id<>0"""

@auto_submit
def copy_refnud_to_unsubscribe():
    return """insert into ncrm_unsubscribe (shop_id,create_time,psuser_id,refund,note,refund_date,event_id)
            select  cc.shop_id as shop_id,cf.refund_time as create_time,cp.id as psuser_id,refund_fee as refund,refund_reason as note,cf.refund_time as refund_date,0 as event_id
             from crm_refund cf left join crm_customer cc on cf.customer_id=cc.id left join ncrm_psuser cp on cf.adviser=cp.name_cn where cf.refund_time is not null"""

@auto_submit
def copy_referrals_to_reintro():
    return """insert into ncrm_reintro (shop_id,create_time,psuser_id,receiver_id,reintro_type)
            select  cc.shop_id as shop_id,cr.referrals as create_time,cp.id as psuser_id,cp.id as receiver_id,'ztc' as reintro_type
             from crm_referrals cr left join crm_customer cc on cr.customer_id=cc.id left join ncrm_psuser cp on cr.adviser=cp.name_cn"""

@auto_submit
def init_client_gtoup():
    return """insert into ncrm_clientgroup (title,query,id_list,create_time,create_user_id,checked)
           select '默认' as title,'' as query,'' as id_list,now() as create_time,id as create_user,1 as checked from ncrm_psuser where type='TPSALES'"""

def init_client_gtoup2():

    sql = """select tp.nick,p.name_cn,p.id from
            (select c.nick,a.first_name from ztcjl3_tp.tp_order o left join ztcjl3_tp.tp_tpcustomer c on o.tpcustomer_id=c.id left join ztcjl3_tp.auth_user a on o.saler_id=a.id) tp
            left join ztcjl4.ncrm_psuser p on tp.first_name=p.name_cn"""

    data = get_data(sql)

    temp = {}

    for d in data:
        if not temp.has_key(d[2]):
            temp[d[2]] = []
        temp[d[2]].append("'" + d[0] + "'")
    # print temp[813]

    sql = """select id,create_user_id from ncrm_clientgroup"""

    data = get_data(sql)

    for d in data:
        try:
            sql = """select shop_id from ncrm_customer where nick in (%s)""" % (','.join(temp[d[1]]))
            data1 = get_data(sql)

            id_list = [i[0] for i in data1]
            # print id_list

            sql = """update ncrm_clientgroup set id_list="%s" where id=%s""" % (id_list, d[0])
            cursor.execute(sql)
        except Exception, e:
            print e
        conn.commit()

def clean_ncrm_table():
    drop_list = ['ncrm_unsubscribe', 'ncrm_subscribe', 'ncrm_reintro', 'ncrm_operate', 'ncrm_login',
                 'ncrm_comment', 'ncrm_contact', 'ncrm_plan', 'ncrm_clientgroup', 'ncrm_customer', 'ncrm_psuser']

    sql = "drop table %s"
    for d in drop_list:
        temp = sql % (d)
        try:
            cursor.execute(temp)
        except Exception, e:
            print e
        conn.commit()

    print 'clean table ok'


def sync_db():
    import os
    os.system('python ../manage.py syncdb')
    print 'sync_db ok'

if __name__ == '__main__':

    clean_ncrm_table() # 清空已有表

    sync_db() # syncdb

    copy_crm_psuser() # 导入psuser

    copy_crm_customer() # 导入crm_customer

    from export_data_from_tpm import export_data_from_tpm_main

    export_data_from_tpm_main() # 导入tpm 数据

    insert_customer_4shop_info() # 导入shop_info到customer

    update_categoty() # 更新主营类目

    update_address() # 更新地址
    update_address2()

    update_seller() # 跟新联系人

    update_phone() # 跟新电话

    copy_soft_subscribe() # 导入软件订单

    update_subscribe_operater() # 绑定原有custromer 中顾问到订单表

    update_rjjh_subscribe() # 生成人机结合的订单
    update_rjjh_subscribe2() # 更新原有订单的pay为0
    update_rjjh_subscribe3() # 跟新customer中人机结合的关系到订单表中

    copy_remark_to_contact() # 导入顾问备注

    copy_refnud_to_unsubscribe() # 导入退款记录


    copy_referrals_to_reintro() # 导入转介绍

    # 初始化网销客户群
    init_client_gtoup()
    init_client_gtoup2()


    print '======================finished============================'
