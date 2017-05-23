# coding=UTF-8

from .utils import TimeSpliter
from .report import Report
from .loader import Loader
from .register import IndicatorManager


class PerformanceStatistics(object):

    def __call__(self, time_scope, cycle, indicators, psusers):
        psusers = list(psusers)
        indicators = [IndicatorManager.get_indicator(indicator_name) for indicator_name in indicators]
        time_scope_list = TimeSpliter(cycle)(time_scope)

        # 注：此处有三种实现方式
        # 方式一：考虑少部分性能：采用数据加载的方式，一次性将所有数据加载到web端，然后通过函数计算
        # 方式二：每天定时生成历史统计信息表，将数据写入到临时表中，供第二天读取计算
        # 暂采用第一种方式
        loader = Loader(time_scope, psusers)
        loader.loading(indicators)

        root_report = Report(psusers, time_scope)
        for psuser in psusers:
            staff_report = Report(psuser, time_scope)
            for cur_time_scope in time_scope_list:
                staff_time_report = Report(psuser, cur_time_scope)
                staff_report.add(staff_time_report)
            root_report.add(staff_report)
        root_report.hung_on_report(indicators, loader)
        return root_report


# 获取周期支持
get_split_cycle = TimeSpliter.get_time_cycle_infos
# 获取指标项接口
get_indicators_byposition = IndicatorManager.get_indicators_byposition
# 计算统计接口
get_performance_statistics = PerformanceStatistics()

