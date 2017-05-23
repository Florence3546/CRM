# coding=UTF-8

'''
Created on 2015-11-23

@author: YRK
'''

import sys
import argparse
import os
import re
import datetime
import os.path as op

def remove_myself(file_name):
    return file_name != op.basename(__file__)

def suffix_filter(file_name):
    return file_name.endswith(".py")

def upgrade_file_filter(file_name):
    return file_name.startswith('upgrade_')

def date_filter(start_date):
    """
        start_date : YYYYmmdd
    """
    def _date_filter(file_name):
        rm = re.match('upgrade_(?P<date_str>\d{8})_(\w+).py', file_name)
        if rm :
            date_str = rm.groupdict().get('date_str', "")
            if date_str:
                start_date = datetime.datetime.strptime(_date_filter.start_date, '%Y%m%d')
                cur_date = datetime.datetime.strptime(date_str, '%Y%m%d')
                return cur_date >= start_date
        return False

    _date_filter.start_date = start_date
    return _date_filter

def load_modules(file_names):
    module_names = map(lambda obj : obj.split('.')[0], file_names)
    all_modules = [ __import__(model_name) for model_name in module_names]
    return all_modules

def start_modules(all_modules, check_func = "upgrade_timescope", start_func = 'upgrade'):
    for module in all_modules:
        if start_func not in module.__dict__:
            print u'【Error】: module "{}"  is losted  "{}"  function, please to add it, then restart main.py.'.format(module.__name__, start_func)
        if start_func not in module.__dict__:
            print u'【Error】 : module "{}"  is losted  "{}"  function, please to add it, then restart main.py.'.format(module.__name__, check_func)
        else:
            start_time, end_time = module.upgrade_timescope()
            if start_time < datetime.datetime.now() < end_time:
                module.upgrade()
            else:
                print u"【Warning】 : to upgrade script file - \"{}\" can't  execute , the script have already exceed the time limit.".format(module.__name__)

def setup_environment():
    new_root_path = op.dirname(op.dirname(op.dirname(op.abspath(__file__))))
    sys.path.append(new_root_path)
    import init_environ

def import_models():
    base_dir = op.abspath(op.dirname(__file__))
    files = os.listdir(base_dir)

    # 脚本 不关心性能
    new_files = filter(remove_myself, files)
    new_files = filter(suffix_filter, new_files)
#     new_files = filter(date_filter(start_date), new_files)

    # 加载并启动模块，内置启动方法
    setup_environment()
    all_modules = load_modules(new_files)
    start_modules(all_modules)

if __name__ == "__main__":
    description = """
welcome to ztcjl production

script file name format : upgrade_{date}_{author}.py, example: upgrade_20151123_yangrongkai.py.
and 'upgrade' and 'upgrade_timescope' function is required in each script file.

"upgrade" function: execute upgrade operation
"upgrade_timescope" function: check executable permission.
"""
    parser = argparse.ArgumentParser(description = description)
    args = parser.parse_args()
    import_models()
