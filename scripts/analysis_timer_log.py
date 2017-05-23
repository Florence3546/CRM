# coding=UTF-8
# !/usr/bin/env python
import datetime
import pymongo
import logging
import os
from copy import deepcopy

LOG_SERVER_NAME = 'timer01'

host = '10.27.228.73'
port = 30001
uname = 'PS_ztcjlAdmin'
pwd = 'PS_managerZtcjl'

web_pyconn = pymongo.Connection(host, port)
web_db = web_pyconn.jl_ztcjl
web_db.authenticate(uname, pwd)
tlog_coll = web_db.timer_log

base_path = os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.split(base_path)[0]
conf_file = "logger.conf"
logging.config.fileConfig("%s/%s" % (parent_path, conf_file))
log = logging.getLogger()
log.setLevel(logging.INFO)


class AnalysisLog():
    """docstring for AnalysisLog"""

    date_fmt = '%Y-%m-%d %H'
    flag_str = '[timer]'
    type_list = ['info', 'error']
    log_opt_dict = {'get_task_list': 'get_task_count'}

    cur_time = ''
    init_log_dict = {k: {} for k in type_list}
    log_dict = deepcopy(init_log_dict)

    def __init__(self, level, msg):
        self.time_str = datetime.datetime.now().strftime(AnalysisLog.date_fmt)
        self.level = level
        self.msg = msg

    def get_task_count(self, log_desrc):
        '''当前有多少任务等待执行'''
        count = 0
        for items in log_desrc.split(','):
            k, v = items.split('=')
            if 'count' in k:
                count = int(v)
        return count

    def do_info_log(self):
        result_list = ['unknow_i', 'all', 1]
        try:
            type_desrc, log_desrc = self.msg.split(': ', 1)
            log_type_list = type_desrc[len(AnalysisLog.flag_str):-1].replace('][', '[').split('[')
            log_type_list = [i for i in log_type_list if i]
            info_type, sub_type = log_type_list[0], log_type_list[1]
            if info_type in AnalysisLog.log_opt_dict:
                try:
                    count = getattr(self, AnalysisLog.log_opt_dict[info_type])(log_desrc)
                    result_list[2] = count
                except Exception, e:
                    log.error('analysis log error, info_type=%s, e=%s' % (info_type, e))
            result_list[0] = info_type
            result_list[1] = sub_type
        except Exception, e:
            log.error('do info log error: msg="%s", e=%s' % (self.msg, e))
        finally:
            return result_list

    def do_error_log(self):
        result_list = ['unknow_e', 'null', 1]
        try:
            # 一般错误格式：{"error_response":{"code":27,"msg":"Invalid session:session-expired","sub_code":"session-expired","request_id":"ze1z2cy8hpd1"}}
            error_flag = 'error_response'
            start_index = self.msg.find(error_flag)
            if start_index == -1:
                isv_error = ['Failed to parse JSON payload', 'parse top result error', 'Failed to send request']
                for i in isv_error:
                    if i in self.msg:
                        result_list[0] = 'isp'
                        result_list[1] = i
                        return result_list

                result_list[0] = 'others'
                ignore_error = ['shopmng task download rpt failed', 'sync ALL struct FAILED',
                                'shopmng task download struct failed', 'run task error, e=(1062,'
                                'e=insertDocument :: caused by :: 11000 E11000 duplicate key',
                                "'NoneType' object has no attribute 'simba_account_balance_get'"]
                for i in ignore_error:
                    if i in self.msg:
                        result_list[2] = 0
            else:
                spilt_index = start_index + len(error_flag) + 2
                error_str = self.msg[spilt_index:-1]

                if error_str and error_str.count('{') == error_str.count('}'):
                    error_dict = eval(error_str)
                    result_list[0] = error_dict['msg']
                    if error_dict.has_key('sub_code'):
                        result_list[1] = error_dict['sub_code']
                else: # 日志格式不规范
                    log.warn('log unformart, msg=%s' % self.msg)
                    result_list[0] = 'unformart'
        except Exception, e:
            log.error('do error log error: msg="%s", e=%s' % (self.msg, e))
        finally:
            return result_list

    def analysis_sigle_log(self):
        result_list = []
        if AnalysisLog.flag_str in self.msg:
            info_result = self.do_info_log()
            info_result.insert(0, AnalysisLog.type_list[0])
            result_list.append(info_result)
        elif self.level == 'ERROR':
            error_result = self.do_error_log()
            error_result.insert(0, AnalysisLog.type_list[1])
            result_list.append(error_result)
        return result_list

    @classmethod
    def run(cls, obj):
        try:
            if obj.time_str != cls.cur_time:
                cls.save_2db()
                cls.cur_time = obj.time_str
            analysis_result = obj.analysis_sigle_log()
            for type, log_type, sub_type, count in analysis_result:
                cls.log_dict[type].setdefault(log_type, {}).setdefault(sub_type, 0)
                cls.log_dict[type][log_type][sub_type] += count
            return True
        except Exception, e:
            log.error('[analysis_timer_log error]: e=%s' % e)
            return False

    @classmethod
    def save_2db(cls):
        try:
            if cls.log_dict == cls.init_log_dict:
                return
            insert_list = []
            temp_dict = {}
            create_time = datetime.datetime.now()
            for type, l_dict in cls.log_dict.items():
                if not l_dict:
                    continue
                for log_type, ll_dict in l_dict.iteritems():
                    for sub_type, count in ll_dict.iteritems():
                        temp_dict = {'tj_time': cls.cur_time, 'type': type, 'log_type': log_type, 'sub_type': sub_type,
                                     'source': LOG_SERVER_NAME, 'count': count, 'create_time': create_time
                                     }
                        insert_list.append(temp_dict)
            if insert_list:
                tlog_coll.insert(insert_list)
        except Exception, e:
            raise Exception('save_2db error: %s' % e)
        finally:
            cls.cur_time = ''
            cls.log_dict = deepcopy(cls.init_log_dict)
