# coding=UTF-8

'''
Created on 2015-12-30

@author: YRK
'''

RATE = "rate"
NUMBER = "num"
AVG_NUMBER = 'avg_num'
INDICATOR_VALUE_TYPE = ((NUMBER, "数值"), (AVG_NUMBER, '平均值'), (RATE, '率'))
class BaseIndicator(object):

    def __init__(self, name, name_cn, val_type, unit, load_func, calc_func, sum_func, \
                 show_func, default_indicator = True):
        self.name = name
        self.name_cn = name_cn
        self.val_type = val_type
        self.unit = unit
        self.default_indicator = default_indicator

        self.load_func = load_func if type(load_func) is list else [load_func, ]
        self.calc_func = calc_func
        self.sum_func = sum_func
        self.show_func = show_func

    def to_dict(self):
        return { key:val for key , val in self.__dict__.items() \
                 if not key.startswith('_') and not callable(getattr(self, key))}

class ConsultIndicator(BaseIndicator):
    pass





