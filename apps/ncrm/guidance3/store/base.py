# coding=UTF-8

'''
Created on 2016-1-7

@author: YRK
'''

# import abc

# class BaseStore(abc.ABCMeta):
#
#     @abc.abstractmethod
#     def filter(self, psusers, start_date, end_date, indicators):
#         pass
#
#     @abc.abstractmethod
#     def get(self, psuer, some_date, indicator,):
#         pass
#
#     @abc.abstractmethod
#     def save(self, psuer, some_date, indicator, value_list):
#         pass

class BaseStore(object):

    def filter(self, psusers, start_date, end_date, indicators):
        pass

    def get(self, psuer, some_date, indicator,):
        pass

    def save(self, psuer, some_date, indicator, value_list):
        pass
