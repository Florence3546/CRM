# coding=UTF-8
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

class TopError(Exception):
    """api exception"""

    def __init__(self, reason):
        self.reason = reason.encode('utf-8')
        self.humanized_reason = '发生未知错误'
        if self.reason and self.reason.strip():
            if 'Invalid arg' in self.reason:
                self.humanized_reason = '输入的参数错误'
            else:
                try:
                    error_response = eval(self.reason).get('error_response', {})
                    sub_msg = error_response.get('sub_msg', '')
                    if sub_msg:
                        self.humanized_reason = sub_msg
                except:
                    pass

    def __str__(self):
        return self.reason

class ApiLimitError(Exception):
    """api used out"""

    def __init__(self, app_key, method_name, seconds):
        self.seconds = seconds
        if app_key and method_name:
            from apps.router.models import ApiLimitRecord
            ApiLimitRecord.save_record(app_key, method_name)


    def __str__(self):
        return 'need to wait %s seconds' % (self.seconds)

class DataNotExist(Exception):

    def __init__(self, query_cond, table):
        self.query_cond = query_cond
        self.table = table

    def __str__(self):
        return "data can`t be found in table %s with query %s" % (self.table, self.query_cond)
