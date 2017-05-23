# coding=UTF-8

'''
Created on 2015-12-30

@author: YRK
'''
import datetime

class TimeSpliter(object):
    _cycle = (('day', '天'), ('week', '周'), ('month', '月'))

    def __init__(self, cycle):
        func_suffix = '_spliter'
        func_name = "{}{}".format(cycle, func_suffix)
        if not hasattr(self, func_name):
            raise Exception("TimeSpliter is not implement {} function.".format(func_name))
        self.deal_func = getattr(self, func_name)

    def deal_limit_time_scope(self, start_time, end_time):
        s_time = start_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        e_time = end_time.replace(hour = 23, minute = 59, second = 59, microsecond = 59)
        return (s_time, e_time)

    def day_spliter(self, start_time, end_time):
        days = (end_time - start_time).days
        return [0] * (days + 1)

    def week_spliter(self, start_time, end_time):
        days = (end_time - start_time).days
        week_days = start_time.weekday()
        week_rest_days = 6 - week_days
        split_list = [week_rest_days]
        if days - week_rest_days > 0:
            week_cycle = 7
            interval_cycle = (days - week_rest_days) / week_cycle
            rest_days = (days - week_rest_days) % week_cycle
            for _ in xrange(interval_cycle):
                split_list.append(week_cycle - 1)
            split_list.append(rest_days)
        return split_list

    def month_spliter(self, start_time, end_time):
        split_list = []
        temp_start_time = start_time
        count = 0
        while True:
            cur_time = temp_start_time + datetime.timedelta(days = count)
            if temp_start_time.month != cur_time.month:
                temp_start_time = cur_time
                split_list.append(count - 1)
                count = -1

            if cur_time >= end_time:
                if count > 0:
                    split_list.append(count)
                break

            count += 1
        return split_list

    def __call__(self, time_scope):
        start_time, end_time = time_scope
        end_time = datetime.datetime.now() if time_scope is None else  end_time
        if start_time <= end_time:
            split_list = self.deal_func(start_time, end_time)
            result_list = []
            cur_time = start_time
            for index in split_list:
                calc_end_time = cur_time + datetime.timedelta(days = index)
                calc_end_time = end_time if calc_end_time > end_time else calc_end_time
                calc_time_scope = self.deal_limit_time_scope(cur_time, calc_end_time)
                result_list.append(calc_time_scope)
                cur_time = calc_end_time + datetime.timedelta(days = 1)
            return result_list
        raise Exception("start time gte end_time , this is error.")

    @classmethod
    def get_time_cycle_infos(cls):
        return cls._cycle