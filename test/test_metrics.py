# coding=UTF-8
import init_environ, datetime
from apps.ncrm.metrics import MetricsManager

psuser_id_list = []
metric_list = []
yesterday = datetime.date.today() - datetime.timedelta(days=1)
manager = MetricsManager(datetime.date(2016, 5, 1), yesterday, psuser_id_list, metric_list)
try:
    # MetricsManager.daily_snapshot_data()
    manager.snapshot_data()
    print 'snapshot finish'
except Exception, e:
    print e
