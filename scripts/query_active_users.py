# coding=UTF-8
import init_environ
from import_for_models import *
from apps.router.models import *

def query_active_users(days = 0):
    '''查询当前活动用户数目，用法：python.exe query_active_users days 没有输入时间就取当天'''
    today0 = datetime.date.today() - timedelta(days = int(days)) # 避免跨天问题
    try:
        user_count = 0
        sql = "SELECT DISTINCT table_name FROM information_schema.columns WHERE table_name LIKE 'upload_uploadrecord_%%'";
        result_dict_list = execute_query_sql(sql)
        # 将所有的数据库表中的数据清除掉
        for rd in result_dict_list:
            try:
                table_name = rd['table_name']
                temp_sql = "SELECT * FROM %s WHERE create_time > '%s'" % (table_name, str(today0))
                logs_result = execute_query_sql(temp_sql)
                if len(logs_result) > 0:
                    user_count += 1
                    shop_id = table_name.split('_')[2]
                    shop = Shop.objects.get(sid = shop_id)
                    log.info("NAME:%s, SHOP_ID:%s" % (shop.nick, shop.sid))
            except Exception, e:
                log.error("error:%s" % e)
                continue
    except Exception, e:
        log.error("error:%s" % (e))
    return user_count

days = 0
arg_lenth = len(sys.argv)
if arg_lenth > 1:
    days = sys.argv[1]

all_count = query_active_users(days = days)
log.info("ALL ACTIVE NUMBER:%s" % (all_count))
