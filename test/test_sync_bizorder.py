# coding=utf-8
import init_environ
import datetime, time
from apps.common.utils.utils_datetime import date_2datetime
from apps.router.models import OrderSyncer

# nick = "毛毛雨泽521"
# article_code = "ts-25811"
#
# syncer = OrderSyncer.objects.get(article_code = article_code)
#
#
#
# sync_count = syncer.sync_bizorder(start_time = syncer.sync_order_time, end_time = syncer.claw_time)
#
#
# print sync_count

kcjl_code = "ts-25811"
qn_code = "FW_GOODS-1921400"
def sync_bizorder(article_code, start_time, end_time):
    syncer = OrderSyncer(article_code=article_code)
    temp_count = syncer.sync_bizorder(start_time, end_time)
    print article_code, start_time - datetime.timedelta(hours=12), '至', end_time, 'count: ', temp_count

def __main__():
    now = datetime.datetime.now()
    days_90ago = now.date() - datetime.timedelta(days=89)
    start_time =date_2datetime(days_90ago)
    while start_time < now:
        end_time = start_time + datetime.timedelta(days=1)
        sync_bizorder(kcjl_code, start_time + datetime.timedelta(hours=12), end_time)
        time.sleep(60 * 1)
        sync_bizorder(qn_code, start_time + datetime.timedelta(hours=12), end_time)
        time.sleep(60 * 1)
        start_time = end_time

if __name__=='__main__':
    __main__()
