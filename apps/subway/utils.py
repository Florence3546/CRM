# coding=UTF-8
import datetime

from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import date_2datetime
from apps.subway.models_report import BaseReport


def accumulation_values(result_dict):
    """
      全区域或全时间段累加计算
    """
    try:
        sum = 0
        for value in result_dict.values():
            sum += int(value)
        return sum
    except Exception , e:
        return result_dict

def get_date_list(date_scope):
    """
      获取某一时间段内的所有以天为单位的时间列表（单位：天）
      参数要求：
          date_scope：
                  1. date类型的元祖，元祖大小为2，
                  2. 元祖第一个元素时间表示起始时间，
                  3. 元祖第二个元素表示终止时间
                      例：
                  date_scope =(datetime.date(2013, 7, 1),datetime.date(2013, 7, 5))
      返回参数：
                 列表， 例：
              [
                datetime.date(2013, 7, 1),
                datetime.date(2013, 7, 2),
                datetime.date(2013, 7, 3),
                datetime.date(2013, 7, 4),
                datetime.date(2013, 7, 5)
              ]
    """
    days = (date_scope[1] - date_scope[0]).days
    if not days:
        return [date_scope[0]]
    date_list = []
    for i in xrange(days + 1):
        date_list.append(date_scope[0] + datetime.timedelta(days = i))
    return date_list

def get_interval_date_list(date_list):
    """
      获得一段时间内的所有以天为范围的时间间隔片段元祖列表（单位：天）
      参数要求：
         date_list：
                 1.date类型的list对象
                 2.list对象需要是一段连续的时间片
                     例：
                [
                   datetime.date(2013, 7, 1),
                   datetime.date(2013, 7, 2),
                   datetime.date(2013, 7, 3)
                ]
      返回参数：
             元祖列表，例：
          [
               (datetime.date(2013, 7, 1, 0, 0, 0), datetime.date(2013, 7, 1, 23, 59, 59)),
               (datetime.date(2013, 7, 2, 0, 0, 0), datetime.date(2013, 7, 2, 23, 59, 59)),
               (datetime.date(2013, 7, 3, 0, 0, 0), datetime.date(2013, 7, 3, 23, 59, 59))
           ]
    """
    try:
        result_list = []
        for start_time in date_list:
            end_time = start_time + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)
            result_list.append((start_time, end_time))
        return result_list
    except Exception, e:
        log.exception('To slice date_list is error, e=%s' % e)
        return []

def transfer_type(data, data_tuple):
    """字符串转换与之所匹配的类型，UDP数据需要"""
    try:
        if data_tuple[1] == 'int':
            return int(float(data))
        elif data_tuple[1] == 'string':
            return data
        elif data_tuple[1] == 'float':
            return float(data)
        elif data_tuple[1] == 'dict':
            return {key:transfer_type(value, (data_tuple[0], data_tuple[2])) for key, value in data.items()}
    except:
        log.info('transfer field failed, field=%s ,transfer type=%s!' % (data_tuple[0], data_tuple[1]))
        return None

def get_create_days(self):
    '''property函数，返回对象创建天数'''
    if self.create_time:
        return (datetime.datetime.now() - self.create_time).days
    return '-'

def set_rpt_days(self, rpt_days):
    '''property函数，设置报表统计天数'''
    if hasattr(self, '_rpt_days'):
        if self._rpt_days == rpt_days:
            return True
    self._rpt_days = rpt_days
    for _attr in ['_rpt_date', '_rpt_date_list', '_rpt_sum', '_rpt_nosch', '_snap_list', '_nosch_list']:
        try:
            delattr(self, _attr)
        except:
            pass

def get_rpt_days(self):
    '''property函数，获取报表统计天数'''
    if not hasattr(self, '_rpt_days'):
        self._rpt_days = 7
    return self._rpt_days

def get_rpt_date(self):
    '''property函数，报表的开始日期'''
    if not hasattr(self, '_rpt_date'):
        self._rpt_date = date_2datetime(datetime.date.today() - datetime.timedelta(days = self.rpt_days))
    return self._rpt_date

def get_rpt_date_list(self):
    '''property函数，报表的[有效]日期列表'''
    if not hasattr(self, '_rpt_date_list'):
        self._rpt_date_list = []
        for rpt in self.rpt_list[-self.rpt_days:]:
            if rpt.date >= self.rpt_date:
                self._rpt_date_list.append(rpt.date)
    return self._rpt_date_list

def get_rpt_yt(self):
    '''property函数，昨日SUMMARY报表'''
    if not hasattr(self, '_rpt_yt'):
        yesterday = date_2datetime(datetime.date.today() - datetime.timedelta(days = 1))
        self._rpt_yt = BaseReport(date = yesterday)
        if self.rpt_list:
            temp_rpt = self.rpt_list[-1]
            if temp_rpt.date == yesterday:
                self._rpt_yt = temp_rpt
    return self._rpt_yt

def get_rpt_sum(self):
    '''property函数，N天SUMMARY报表之和'''
    if not hasattr(self, '_rpt_sum'):
        self._rpt_sum = BaseReport()
        sum_rpt_data(self._rpt_sum, self.rpt_date, self.rpt_list[-self.rpt_days:])
    return self._rpt_sum

def get_rpt_nosch(self):
    '''property函数，N天NOSEARCH报表之和'''
    if not hasattr(self, '_rpt_nosch'):
        self._rpt_nosch = BaseReport()
        sum_rpt_data(self._rpt_nosch, self.rpt_date, self.nosch_rpt_list[-self.rpt_days:])
    return self._rpt_nosch

def get_snap_list(self):
    '''property函数，N天SUMMARY历史明细，用于显示趋势图，可选7天、15天'''
    if not hasattr(self, '_snap_list'):
        self._snap_list = []
        for rpt in self.rpt_list[-self.rpt_days:]:
            if rpt.date >= self.rpt_date:
                self._snap_list.append(rpt)
    return self._snap_list

def get_nosch_list(self):
    '''property函数，N天NOSEARCH历史明细，用于显示定向推广的趋势图，可选7天、15天'''
    if not hasattr(self, '_nosch_list'):
        self._nosch_list = []
        for rpt in self.nosch_rpt_list[-self.rpt_days:]:
            if rpt.date >= self.rpt_date:
                self._nosch_list.append(rpt)
    return self._nosch_list

def sum_rpt_data(rpt_obj, rpt_date, rpt_list):
    '''对报表列表求和，放到一个rpt对象中'''
    if not rpt_list:
        rpt_obj.ndays_avgpos = 0
        return None
    avgpos_sum = 0
    for temp in rpt_list:
        if temp.date >= rpt_date:
            avgpos_sum += temp.avgpos * temp.impressions
            rpt_obj.impressions += temp.impressions
            rpt_obj.click += temp.click
            rpt_obj.cost += temp.cost
            rpt_obj.directpay += temp.directpay
            rpt_obj.indirectpay += temp.indirectpay
            rpt_obj.directpaycount += temp.directpaycount
            rpt_obj.indirectpaycount += temp.indirectpaycount
            rpt_obj.favitemcount += temp.favitemcount
            rpt_obj.favshopcount += temp.favshopcount
            rpt_obj.avgpos = temp.avgpos and temp.avgpos or 0 # 取昨日排名，即取最末尾元素
    rpt_obj.ndays_avgpos = (rpt_obj.impressions and avgpos_sum / rpt_obj.impressions or 0) # 取多天平均排名，即取平均数

def get_msg_count_list(self):
    if not hasattr(self, '_msg_count_list'):
        note_count, comment_count = self.msg_status and self.msg_status.split('_') or [0, 0]
        self._msg_count_list = [int(note_count), int(comment_count)]
    return self._msg_count_list

def get_note_count(self):
    if not hasattr(self, '_note_count'):
        self._note_count = self.msg_count_list[0]
    return self._msg_count

def get_comment_count(self):
    if not hasattr(self, '_comment_count'):
        self._comment_count = self.msg_count_list[1]
    return self._comment_count

def save_msg_count(self):
    def save_count(msg_type, add_count):
        count_list = self.msg_count_list
        count_list[msg_type] += add_count
        if count_list[msg_type] < 1:
            count_list[msg_type] = 0
        if count_list == [0, 0]:
            self.msg_status = ''
        else:
            self.msg_status = str(count_list[0]) + '_' + str(count_list[1])
        self.save()
    return save_count
