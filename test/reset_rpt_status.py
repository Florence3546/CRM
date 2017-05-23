# coding=UTF-8

import init_environ
from apps.common.utils.utils_datetime import datetime_2string, datetime
from apps.subway.download import dler_coll
from apps.web.api import reset_shop_task

reset_str = '%s_OK' % datetime_2string(datetime.datetime.now() - datetime.timedelta(days = 3))
dler_coll.update({}, {'$set':{'acctrpt_status':reset_str, 'camprpt_status':reset_str, 'adgrpt_status':reset_str}}, multi = True)

reset_shop_task()
