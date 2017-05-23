# coding=UTF-8

import init_environ
from apps.web.api import reset_shop_task
from apps.kwslt.models_cat import CatStatic
from image_optimoze import main as rotate_creative
from apps.ncrm.models import PSUser
from apps.mnt.models_monitor import MntCostSnap
from apps.ncrm.metrics import MetricsManager


def main():
    '''scheduler 在以下时间暂停后，启动前，执行以下相应的函数，注意：需要注释其他函数'''

    print 'start'

    # # 22:30
    # MntCostSnap.save_rptsnap()

    # # 00:00
    # rotate_creative()

    # # 03:00
    # PSUser.refresh_common_group_statistic()

    # # 04:00
    # MetricsManager.daily_snapshot_data()

    # # 05:50
    # reset_shop_task()

    # # 06:00
    # CatStatic.update_cat_market_data()

    print 'OK'


if __name__ == '__main__':
    main()
