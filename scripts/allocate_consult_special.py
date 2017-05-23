# coding=UTF-8
import init_environ
from django.db import connection, transaction
from apps.common.utils.utils_log import log
# from apps.crm.models import Customer, PSUser

#===============================================================================
# 2014/12/04 将未分配顾问的web新客户和千牛客户平均分配给指定顾问
# 2015/04/22 Customer, PSUser结构已变，脚本废弃
#===============================================================================

def do_allocate(shop_id_list, consult_id_list):
    """作分配"""
    print '分配%s个客户' % len(shop_id_list)
    update_dict = {}
    while True:
        try:
            for consult_id in consult_id_list:
                shop_id = shop_id_list.pop(0)
                temp_list = update_dict.setdefault(consult_id, [])
                temp_list.append(shop_id)
            consult_id_list.reverse()
        except IndexError:
            break
        except Exception, e:
            continue
    return update_dict

def update_2db(update_dict):
    """按update_dict来更新到数据库中"""
#     for consult_id, shop_id_list in update_dict.items():
#         try:
#             Customer.objects.filter(shop_id__in = shop_id_list).update(consult = consult_id)
#         except Exception, e:
#             log.error('allocate_customer_2consult FAILED, e=%s, consult_id=%s.' % (e, consult_id))
    return True

def main():
    try:
        cursor = connection.cursor()
        # 指定顾问列表，按入职时间降序排序
        consult_name_list = ['李文杰', '徐开', '谢敏', '李婷', '冯磊', '夏薇', '熊英', '秦伟嘉', '王昆', '廖威', '胡梦']
        cursor.execute('SELECT id FROM crm_psuser WHERE type="CONSULT" AND name_cn in ("%s") ORDER BY create_time' % '","'.join(consult_name_list))
        consult_id_list = [row_data[0] for row_data in cursor.fetchall()]
        if not consult_id_list:
            print '没有找到可以分配的顾问'
            return

        sql = """select au.shop_id from auth_user au
                join (select nick, max(deadline) as deadline from router_articleusersubscribe where article_code='%s' group by nick having max(deadline)>now() ) as ra
                on au.username = ra.nick
                join crm_customer cc
                on au.username = cc.nick
                where cc.consult_id is null
                order by ra.deadline ,cast(au.level as signed) desc"""
        #=======================================================================
        # web端
        #=======================================================================
        cursor.execute(sql % 'ts-25811')
        shop_id_list = [int(row_data[0]) for row_data in cursor.fetchall() if row_data[0]]

        # 开始分配web客户
        update_dict = do_allocate(shop_id_list, consult_id_list)
        update_2db(update_dict)

        #=======================================================================
        # qn端
        #=======================================================================
        cursor.execute(sql % 'FW_GOODS-1921400')
        shop_id_list = [int(row_data[0]) for row_data in cursor.fetchall() if row_data[0]]

        # 开始分配qn客户
        update_dict = do_allocate(shop_id_list, consult_id_list)
        update_2db(update_dict)

        #=======================================================================
        # 刷新顾问表的已有客户数
        #=======================================================================
#         PSUser.objects.all().update(now_load = 0) # 清空，再赋值
        sql = """update crm_psuser cp
                 join (select consult_id,count(consult_id) as actual_load from crm_customer where consult_id is not null group by consult_id) a
                 on a.consult_id = cp.id
                 set cp.now_load = a.actual_load"""
#         cursor.execute(sql)
#         transaction.commit_unless_managed()
    except Exception, e:
        log.error('init_allocate_customers error, e=%s' % e)
    finally:
        cursor.close()

if __name__ == '__main__':
    main()
