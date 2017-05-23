# coding=utf-8

import os
import init_environ
from taskengine.manager import Manager

from apps.web.api import *

if __name__ == "__main__":

    cfg_list = [{'retrieve_items':  get_task_list_of_run_shop_task, 'consume': run_shop_task, 'consumer_count':2, 'working_time': [('00:00', '23:59')]},
                {'retrieve_items':  get_task_list_of_run_mnt_quick_task, 'consume': run_mnt_quick_task, 'consumer_count':2, 'working_time': [('00:00', '23:59')]},
                {'retrieve_items':  get_task_list_of_run_mnt_routine_task, 'consume': run_mnt_routine_task, 'consumer_count':2, 'working_time': [('00:00', '23:59')]}
                ]

    Manager.trigger(cfg_list)
