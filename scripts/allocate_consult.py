# coding=UTF-8
import init_environ
from django.db import connection, transaction
from apps.common.utils.utils_log import log

#===============================================================================
# 【已废弃】初始化平均分配客户给每个顾问
#===============================================================================

def main():
    try:
        cursor = connection.cursor()
        sql = """select au.shop_id from auth_user au join
                (select nick, max(deadline) as deadline from router_articleusersubscribe where article_code = 'ts-25811' group by nick having max(deadline)>now() ) as ra
                on au.username = ra.nick
                order by ra.deadline ,cast(au.level as signed) desc"""
        cursor.execute(sql)
        shop_id_list = [int(row_data[0]) for row_data in cursor.fetchall() if row_data[0]]

        # 找出所有在职的顾问，按入职时间降序排序
        cursor.execute('SELECT id, weight FROM crm_psuser WHERE type="CONSULT" AND weight>0 ORDER BY create_time')
        consult_list = list(cursor.fetchall())
        if not consult_list:
            print '没有找到可以分配的顾问'
            return

        # 开始分配
        consult_dict = dict(consult_list)
        while shop_id_list:
            consult_id_list = [id for id, weight in consult_list if consult_dict[id] > 0]
            # 客服权重溢出时平均分配到每个人
            if not consult_id_list:
                consult_id_list = [id for id, weight in consult_list]

            for consult_id in consult_id_list:
                if shop_id_list:
                    shop_id = shop_id_list.pop(0)
                    cursor.execute('UPDATE crm_customer SET consult_id=%s WHERE shop_id=%s' % (consult_id, shop_id))
                    consult_dict[consult_id] -= 1
                    print 'psuser_id:%s, shop_id=%s' % (consult_id, shop_id)
                else:
                    break
            consult_list.reverse()
    except Exception, e:
        log.error('init_allocate_customers error, e=%s' % e)
    finally:
        cursor.close()

if __name__ == '__main__':
    main()
