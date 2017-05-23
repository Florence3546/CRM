#!/uer/bin/env python
# -*- coding:utf-8 -*-
import datetime, sys
reload(sys)
sys.setdefaultencoding('gb2312')

def l_iter(alist):
    for l in alist:
            yield l

def camp(x, y):
    if x[0] > y[0]:
        return 1
    if x[0] < y[0]:
        return -1

def get_result_list():
    lines = l_iter(open('../../../ztcdata/logs/ztcjl_socket.log', 'r'))
    data_list = []
    for l in lines:
        if not 'LOGIN' in l:
            continue
        key = l[1:5]
        nick = l[l.find('nick=') + 5:l.find('from') - 2]
        type = l[-4:-1]
        data_list.append('%s_%s_%s' % (key, nick, type))
    return data_list

def calc(mode = 'repeat'):
    temp_list = get_result_list()
    if mode != 'repeat':
        print '================unrepeat====================='
        temp_list = set(temp_list)
    else:
        print '================repeat====================='
    data_result = {}
    for t in temp_list:
        key = t[0:4]
        if data_result.has_key(key):
            if 'web' in t:
                data_result[key]['web'] = data_result[key]['web'] + 1
            if 'npc' in t:
                data_result[key]['qnpc'] = data_result[key]['qnpc'] + 1
            if 'nyd' in t:
                data_result[key]['qnyd'] = data_result[key]['qnyd'] + 1
        else:
            data_result[key] = {'web':0, 'qnpc':0, 'qnyd':0}
    return data_result

def main():

    data_result = calc('unrepeat')
    list_result = data_result.items()
    list_result.sort(camp)
    for r in list_result:
        print '%s==>web:%-5d\t qnpc:%s\t qnyd:%s ' % (r[0], r[1]['web'], r[1]['qnpc'], r[1]['qnyd'])

    data_result = calc('repeat')
    list_result = data_result.items()
    list_result.sort(camp)
    for r in list_result:
        print '%s==>web:%-5d\t qnpc:%s\t qnyd:%s ' % (r[0], r[1]['web'], r[1]['qnpc'], r[1]['qnyd'])



if __name__ == "__main__":
    main()
    raw_input()
