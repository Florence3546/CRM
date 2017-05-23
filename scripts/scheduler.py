# coding=UTF-8

from apscheduler.schedulers.background import BlockingScheduler

import init_environ
from apps.common.utils.utils_log import log
from apps.web.api import cleanup_expired, reset_shop_task
from apps.router.models import OrderSyncer
from apps.kwslt.models_cat import CatStatic
from sync_app_comments import main as sync_comment
from tj_soft_rpt import tj_soft_rpt
from image_optimoze import main as rotate_creative
from apps.ncrm.models import PSUser, Customer
from apps.mnt.models_monitor import MntCostSnap
from apps.ncrm.metrics import MetricsManager
from apps.router.models import ArticleUserSubscribe

JOB_LIST = [{'func': sync_comment, 'trigger': 'cron', 'hour': '0,8-23', 'minute': 0},
            {'func': OrderSyncer.sync_order, 'trigger': 'interval', 'minutes': 3},
            {'func': cleanup_expired, 'trigger': 'cron', 'hour': 0, 'minute': 30},
            {'func': PSUser.refresh_common_group_statistic, 'trigger': 'cron', 'hour': 3, 'minute': 00},
            {'func': reset_shop_task, 'trigger': 'cron', 'hour': 5, 'minute': 50},
            {'func': CatStatic.update_cat_market_data, 'trigger': 'cron', 'hour': 6, 'minute': 30}, # 注意 CacheKey.KWLIB_CAT_STATIC_RPT 的过期时间应该在 此时间 之后。
            {'func': tj_soft_rpt, 'trigger': 'cron', 'hour': 23, 'minute': 00},
            {'func': rotate_creative, 'trigger': 'cron', 'hour': 0, 'minute': 0},
            {'func': MntCostSnap.save_rptsnap, 'trigger': 'cron', 'hour': 22, 'minute': 30},
            {'func': Customer.refresh_current_category, 'trigger': 'interval', 'hours': 4},
            # {'func': PSUser.init_last_month_weight, 'trigger': 'cron', 'day': 2, 'hour': 12, 'minute': 0},
            {'func': MetricsManager.daily_snapshot_data, 'trigger': 'cron', 'hour': 4, 'minute': 00},
            {'func': ArticleUserSubscribe.check_expiry_date, 'trigger': 'cron', 'hour': 15, 'minute': 00},
            ]

#
# 详细参数说明参考：http://apscheduler.readthedocs.org/en/latest/modules/schedulers/base.html#apscheduler.schedulers.base.BaseScheduler.add_job

def main():
    scheduler = BlockingScheduler()

    for job in JOB_LIST:
        if callable(job['func']):
            scheduler.add_job(**job)

    try:
        scheduler.start()
    except Exception, e:
        log.exception("scheduler quit with exception, e=%s" % e)

if __name__ == '__main__':
    main()
