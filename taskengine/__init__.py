# coding=utf-8

"""
usage:

from taskengine.manager import Manager

cfg_list = [{}]

Manager.trigger(**cfg_list)



worker_allocator
worker_consumer
是基于原来allocator与consumer修改的，主要调整了sleep时间

"""
