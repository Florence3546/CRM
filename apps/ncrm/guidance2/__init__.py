# coding=UTF-8

import json
import datetime
import itertools
import collections
from apps.common.utils.utils_log import log
from .utils import TimeSpliter
from .loader import Loader
from .register import IndicatorManager

from apps.common.biz_utils.utils_dictwrapper import DictWrapper

class StatisticsHelper(object):

    def __init__(self, psusers, indicators, start_time, end_time):
        self.psusers = psusers
        self.indicators = indicators
        self.start_time = start_time
        self.end_time = end_time
        self.result = None

    def __call__(self, staff_data):
        data = collections.OrderedDict()
        for psuser in self.psusers:
            user_data = staff_data.get(psuser, {})
            for indicator in self.indicators:
                inicator_data = user_data.get(indicator, [])
                data.setdefault(indicator, []).extend(inicator_data)

        size = (self.end_time - self.start_time).days + 1
        result = []
        for indicator in data:
            new_data = {}
            for entity in data.get(indicator, []):
                new_data.setdefault(entity.result_date, []).append(entity)

            values_list = []
            for index in xrange(size):
                cur_date = self.start_time.date() + datetime.timedelta(days = index)
                entity_list = new_data.get(cur_date, [])
                for entity in entity_list:
                    entity_data_list = json.loads(entity.data_json)
                    if entity_data_list:
                        for entity_data in entity_data_list:
                            entity_data = DictWrapper(entity_data)
                            entity_data.date = entity.result_date
                            values_list.append(entity_data)

            return_val, _, _ = indicator.sum_func(values_list)
#             result.append((indicator.name, return_val))
            result.append(return_val)
        self.result = result
        return self

    def to_dict(self):
        return {
            "name":','.join(psuser.name_cn for psuser in self.psusers),
            "timescope":(self.start_time.strftime("%m-%d"), self.end_time.strftime("%m-%d")),
            "report":self.result,
            }

class PerformanceStatistics(object):

    def _load_all_entity(self, psuser, indicator, time_scope, is_force = False):
        loader = Loader([psuser], *time_scope)
        staff_mapping = loader.loading([indicator], is_force)

        all_entity = []
        indicatore_data = staff_mapping.get(psuser)
        if indicator.show_func is not None:
            for indicator, entity_list in indicatore_data.iteritems():
                for entity in entity_list:
                    data_list = json.loads(entity.data_json)
                    if data_list:
                        for data in data_list:
                            data = DictWrapper(data)
                            data.date = entity.result_date
                            all_entity.append(data)
        return all_entity

    def performance_statistics_shopids(self, psuser, indicator_name, time_scope):
        indicator = IndicatorManager.get_indicator(indicator_name)
        all_entity = self._load_all_entity(psuser, indicator, time_scope)
        event_id_list, shop_id_list = [], []
        if callable(indicator.sum_func):
            _, event_id_list, shop_id_list = indicator.sum_func(all_entity)
        return indicator, event_id_list, shop_id_list

    def performance_statistics_detail(self, *args, **kargs):
        indicator, event_id_list, shop_id_list = self.performance_statistics_shopids(*args, **kargs)
        event_list, shop_list = [], []
        if callable(indicator.show_func):
            event_list, shop_list = indicator.show_func(event_id_list, shop_id_list)
        return event_list, shop_list

    def performance_statistics_sumval(self, psuser, indicator_name, time_scope):
        indicator = IndicatorManager.get_indicator(indicator_name)
        all_entity = self._load_all_entity(psuser, indicator, time_scope, True)
        sumval, _, _ = indicator.sum_func(all_entity)
        return sumval

    def rander_table_data(self, time_scope, cycle, indicators, psusers, is_force = False):
        all_result, time_scope_list, indicators = self(time_scope, cycle, indicators, psusers, is_force)
        column_list = [(' 至 '.join([time_scope[0].strftime("%m-%d"), time_scope[1].strftime("%m-%d")]), time_scope[0].strftime("%Y-%m-%d"), time_scope[1].strftime("%Y-%m-%d"))
                       for time_scope in time_scope_list]
        statistic_data = []
        for psuser, row_data in all_result.iteritems():
            result = {"name_cn":psuser.name_cn, 'psuser_id':psuser.id, 'metric_list':[]}
            matrix = [[] for _ in xrange(len(indicators))]
            for row_col_data in row_data:
                for row_index, val in enumerate(row_col_data.result):
                    matrix[row_index].append(val)
            change_data = zip(indicators, matrix)
            metric_list = [{"name":indicator.name, "name_cn":indicator.name_cn, 'unit':indicator.unit, 'data':row_all_data} \
                           for indicator, row_all_data in change_data]
            result['metric_list'] = metric_list
            statistic_data.append(result)
        return column_list, statistic_data

    def __call__(self, time_scope, cycle, indicators, psusers, is_force = False):
        psusers = list(psusers)
        indicators = [IndicatorManager.get_indicator(indicator_name) for indicator_name in indicators]
        time_scope_list = TimeSpliter(cycle)(time_scope)

        try:
            loader = Loader(psusers, *time_scope)
            staff_mapping = loader.loading(indicators, is_force)

            all_result = collections.OrderedDict()
            for psuser in psusers:
                statis_data = []
                if len(time_scope_list) > 1:
                    result = StatisticsHelper([psuser], indicators, *time_scope)(staff_mapping)
                    statis_data.append(result)

                for start_time, end_time in time_scope_list:
                    result = StatisticsHelper([psuser], indicators, start_time, end_time)(staff_mapping)
                    statis_data.append(result)

                all_result[psuser] = statis_data

            if len(time_scope_list) > 1:
                time_scope_list.insert(0, time_scope)
            return all_result, time_scope_list, indicators
        except Exception, e:
            log.exception('ncrm_guidance2 error, %s' % e)
            return {}, [], []

ps = PerformanceStatistics()
# 获取周期支持
get_split_cycle = TimeSpliter.get_time_cycle_infos
# 获取指标项接口
get_indicators_byposition = IndicatorManager.get_indicators_byposition
# 计算统计接口
get_performance_statistics = ps.rander_table_data
# 获取事件详情接口
get_ps_detail = ps.performance_statistics_detail
get_ps_shopid_list = ps.performance_statistics_shopids
# 刷新某一区间内的缓存值
refresh_ps_sumval = ps.performance_statistics_sumval
