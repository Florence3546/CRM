# coding=UTF-8
# =======================================================================
# 人机、TP度量统计模块
# 组织结构：
#          入口  →  MetricsManager
#                    ↙         ↘
#               metrics.*  →  dbInterfaces.*
#                                 ↓
#                              models.*
# by 钟超
# 2016-06-15
# =======================================================================

import datetime
from apps.ncrm.models import PSUser, GROUPS, OPERATION_GROUPS
from apps.ncrm.metrics.metrics import *
from apps.ncrm.metrics.dbInterfaces import MyCustomersInterface


class MetricsManager(object):
    """metrics 模块对外接口类"""
    METRIC_DICT = {}

    def __init__(self, start_date, end_date, psuser_id_list=None, metric_list=None):
        self.start_date = start_date
        self.end_date = end_date
        if psuser_id_list:
            self.psuser_dict = {obj.id: obj.name_cn for obj in PSUser.objects.filter(id__in=psuser_id_list).only('id', 'name_cn')}
        else:
            self.psuser_dict = {obj.id: obj.name_cn for obj in PSUser.objects.filter(department__in=OPERATION_GROUPS).exclude(status='离职').only('id', 'name_cn')}
        self.psuser_id_list = self.psuser_dict.keys()
        self.metric_list = [self.METRIC_DICT[metric_name] for metric_name in metric_list if
                            metric_name in self.METRIC_DICT] \
            if metric_list else self.METRIC_DICT.values()
        self.data_dict = {}

    @classmethod
    def register(cls, metric):
        """注册 Metric
        :param metric:
        """
        if isinstance(metric, MetricBase):
            cls.METRIC_DICT[metric.name] = metric

    def __handle_data(self, name):
        """self.data_dict 构造函数
        :param name: ['fetch', 'snapshot']
        """
        for psuser_id in self.psuser_id_list:
            self.data_dict[psuser_id] = {}
            date_obj = self.start_date
            while date_obj <= self.end_date:
                self.data_dict[psuser_id][date_obj] = {}
                for metric in self.metric_list:
                    getattr(metric, name)(self, psuser_id, date_obj)
                date_obj += datetime.timedelta(days=1)
        return self.data_dict

    def read_data(self, psuser_id, date_obj, key=None):
        """从内存中的 self.data_dict 读取数据
        :param key:
        :param date_obj:
        :param psuser_id:
        """
        result = self.data_dict.get(psuser_id, {}).get(date_obj, {})
        if key:
            result = result.get(key)
        return result

    def feed_data(self, psuser_id, date_obj, _data):
        """往内存中的 self.data_dict 填充数据
        :param _data:
        :param date_obj:
        :param psuser_id:
        """
        self.data_dict.setdefault(psuser_id, {}).setdefault(date_obj, {}).update(_data)

    def fetch_data(self):
        """从快照中提取数据"""
        return self.__handle_data('fetch')

    def snapshot_data(self):
        """将数据写入快照"""
        self.metric_list = self.METRIC_DICT.values()
        self.metric_list.sort(lambda x, y: cmp(x.snapshot_order, y.snapshot_order))
        self.__handle_data('snapshot')
        MyCustomersInterface.store_data(self)

    def partition_period(self, period_type='day'):
        """根据周期类型划分时间段
        :param period_type: ['day', 'week', 'ps_week', 'month']
        """
        if period_type == 'month':
            months, weekday, days = 1, None, None
        elif period_type == 'week':
            months, weekday, days = None, 0, None
        elif period_type == 'ps_week':  # 派生周：上周六至本周五
            months, weekday, days = None, 5, None
        elif period_type == 'day':
            months, weekday, days = None, None, 1
        else:
            months, weekday, days = None, None, None
        period_list = []
        start_date = self.start_date
        while start_date <= self.end_date:
            if months:
                if start_date.month + months <= 12:
                    next_start_date = datetime.date(start_date.year, start_date.month + months, 1)
                else:
                    next_start_date = datetime.date(start_date.year + 1, start_date.month + months - 12, 1)
            elif weekday is not None:
                offset_days = weekday - start_date.weekday()
                if offset_days > 0:
                    next_start_date = start_date + datetime.timedelta(days=offset_days)
                else:
                    next_start_date = start_date + datetime.timedelta(days=offset_days + 7)
            elif days:
                next_start_date = start_date + datetime.timedelta(days=days)
            else:
                break
            end_date = min(self.end_date, next_start_date - datetime.timedelta(days=1))
            period_list.append((start_date, end_date))
            start_date = next_start_date
        return period_list

    def get_flat_data(self, period_list):
        """将 self.data_dict 里的数据根据划分的时间段扁平化处理
        :param period_list: [(start_date, end_date), ...], 可通过 self.partition_period(period_type) 获得
        """
        result = []
        data_dict = self.fetch_data()
        for psuser_id, psuser_name_cn in self.psuser_dict.items():
            for i, metric in enumerate(self.metric_list):
                psuser_metric_data = {
                    'psuser_id': psuser_id,
                    'psuser_name_cn': psuser_name_cn,
                    'metric_name': metric.name,
                    'metric_name_cn': metric.name_cn,
                    'metric_unit': metric.unit,
                    'metric_no': i,
                    'result': 0,
                    'details': {} if metric.name == 'net_income' else [],
                    'period_str': '%s 至 %s' % (period_list[0][0].strftime('%m-%d'), period_list[-1][-1].strftime('%m-%d')) if period_list[0][0] != period_list[-1][-1] else period_list[0][0].strftime('%m-%d'),
                    'data_list': []
                }
                for start_date, end_date in period_list:
                    metric_data = {
                        'result': 0,
                        'details': {} if metric.name == 'net_income' else [],
                        'period_str': '%s 至 %s' % (start_date.strftime('%m-%d'), end_date.strftime('%m-%d')) if start_date != end_date else start_date.strftime('%m-%d')
                    }
                    _date = start_date
                    while _date <= end_date:
                        if _date in data_dict[psuser_id]:
                            sub_data = data_dict[psuser_id][_date]
                            if metric.name == 'net_income':
                                for _name, _details in sub_data[metric.details].items():
                                    for doc in _details:
                                        doc['date_str'] = _date.strftime('%Y-%m-%d')
                                    metric_data['details'].setdefault(_name, []).extend(_details)
                                    psuser_metric_data['details'].setdefault(_name, []).extend(_details)
                            else:
                                _details = sub_data[metric.details]
                                for doc in _details:
                                    doc['date_str'] = _date.strftime('%Y-%m-%d')
                                metric_data['details'] += _details
                                psuser_metric_data['details'] += _details
                        _date += datetime.timedelta(days=1)
                    if metric.name in ('net_income', 'unsub_apportion'):
                        metric_data['result'] = metric.aggregate(psuser_id, metric_data['details'])
                    else:
                        metric_data['result'] = metric.aggregate(metric_data['details'])
                    psuser_metric_data['data_list'].append(metric_data)
                if metric.name in ('net_income', 'unsub_apportion'):
                    psuser_metric_data['result'] = metric.aggregate(psuser_id, psuser_metric_data['details'])
                else:
                    psuser_metric_data['result'] = metric.aggregate(psuser_metric_data['details'])
                result.append(psuser_metric_data)
        return result

    @classmethod
    def get_metric_detail_titles(cls, metric_name):
        """获取指定维度的详细数据表头
        :param metric_name:
        """
        if metric_name in cls.METRIC_DICT:
            return cls.METRIC_DICT[metric_name].detail_titles
        else:
            return []

    @classmethod
    def get_metric_detail(cls, metric_name, psuser_dict=None, **kwargs):
        """获取指定维度的详细数据
        :param psuser_dict:
        :param metric_name:
        """
        if metric_name in cls.METRIC_DICT:
            return cls.METRIC_DICT[metric_name].get_details(psuser_dict=psuser_dict, **kwargs)
        else:
            return []

    @classmethod
    def daily_snapshot_data(cls):
        """将前一天的数据写入快照"""
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        manager = cls(yesterday, yesterday)
        manager.snapshot_data()


MetricsManager.register(RjjhCustomerNumber())

MetricsManager.register(ZtcCustomerNumber())

MetricsManager.register(ZzCustomerNumber())

MetricsManager.register(ZxCustomerNumber())

MetricsManager.register(DyyCustomerNumber())

MetricsManager.register(SeoCustomerNumber())

MetricsManager.register(NewCustomerNumber())

MetricsManager.register(PauseCustomerNumber())

MetricsManager.register(UnsubscribeCustomerNumber())

MetricsManager.register(ExpireCustomerNumber())

MetricsManager.register(ChangeCustomerNumber())

MetricsManager.register(RenewCustomerNumber())

MetricsManager.register(ServiceAmount())

MetricsManager.register(Income())

MetricsManager.register(ValidIncome())

MetricsManager.register(UnsubscribeApportion())

MetricsManager.register(NetIncome())
