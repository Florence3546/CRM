#!/usr/bin/env python
# coding=UTF-8

import datetime
from pprint import pprint

import init_environ
from apps.mnt.models_monitor import TimerLog

def get_log_type(tj_type, tl):
    if tj_type == 'info':
        return '%s_%s' % (tl.log_type, tl.sub_type)
    else:
        return get_error_type(tl.log_type)

def get_error_type(e_str):
    flag_list = [('Remote service error', 'isp'), ('session', 'session'), ('App Call limited', 'limited'), ('isp', 'isp')]
    for flag_str, type_str in flag_list:
        if flag_str in e_str:
            return type_str

    error_list = ['others', 'unknow_e', 'unformart']
    if e_str in error_list:
        return e_str

    return 'know_others'

def tj_timer_log():
    today = datetime.date.today()
    start_time = datetime.datetime(year = today.year, month = today.month, day = today.day - 7)
    tls = TimerLog.objects.filter(create_time__gt = start_time).order_by('create_time')

    test_dict = {}
    for tl in tls:
        if tl.type == 'error':
            test_dict.setdefault(tl.log_type, 0)
            test_dict[tl.log_type] += tl.count

    test_list = test_dict.items()
    test_list.sort(key= lambda k:k[1])
    print '=========== timer error log type ================'
    pprint(test_list)
    print '================================================='

    result_dict = {'info': {}, 'error': {}}
    for tl in tls:
        l_type = get_log_type(tl.type, tl)
        result_dict[tl.type].setdefault(tl.tj_time, {}).setdefault(l_type, 0)
        result_dict[tl.type][tl.tj_time][l_type] += tl.count
    pprint(result_dict)

def main():
    tj_timer_log()

if __name__ == '__main__':
    main()
