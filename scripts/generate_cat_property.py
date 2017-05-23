# coding=UTF-8
#===========================================================================
#功能：将指定类目下的属性关键词归类合并，在当前类目生成id的csv和统计个数的csv
#用法：暂时请更改main函数中的cat_id
#注意：生成文件请用wps打开否则可能会出现乱码
#by:钟进峰
#===========================================================================

import init_environ
from apps.common.utils.utils_datetime import *
from apps.subway.models_item import Item
import datetime, time, sys
import pymongo

reload(sys)
sys.setdefaultencoding("utf-8")

conn = pymongo.Connection(host = '223.4.48.150', port = 30001)
ztcjl4 = conn.ztcjl4
ztcjl4.authenticate('PS_ztcjl4Admin', 'PS_managerZtcjl4')
item_coll = ztcjl4.subway_item

def get_data_from_database(cat_id):
    result = item_coll.find({'cat_id':cat_id, '$or':[{ 'property_alias':{'$ne':None}}, {'props_name':{'$ne':None}}]}, {'property_alias':1, 'freight_payer':1, 'props_name':1})
    return result

def format_data(cat_id):
    props_dict = {}
    for item in get_data_from_database(cat_id):
        props_name_list = item['props_name'].split(';')
        for props_name in props_name_list:
            temp_list = props_name.split(':')
            if len(temp_list) < 4:
                continue
            if props_dict.has_key(temp_list[0]):
                props_dict[temp_list[0]]['value'].append(temp_list[3].lower())
                continue
            try:
                props_dict[temp_list[0]] = {'key':temp_list[2], 'props_id':temp_list[0], 'value':[temp_list[3].lower()], 'alias':[]}
            except Exception, e:
                print 'e=%s temp_list=%s' % (e, temp_list)


        property_alias_list = item['property_alias'].split(';')
        for property_alias in property_alias_list:
            temp_list2 = property_alias.split(':')
            if len(temp_list2) < 3:
                continue
            try:
                props_dict[temp_list2[0]]['alias'].append(temp_list2[2].lower())
            except Exception, e:
                print 'e=%s temp_list2=%s' % (e, temp_list2)

    #去重
    for k in props_dict:
        try:
            props_dict[k]['value'] = list(set(props_dict[k]['value']))
            props_dict[k]['alias'] = list(set(props_dict[k]['alias']))
            for a in props_dict[k]['alias']:#去除自定义中标准属性已经有的值
                if props_dict[k]['value'].count(a):
                    props_dict[k]['alias'].remove(a)
        except Exception, e:
            print 'e=%s' % e

    return props_dict

def get_csv(cat_id):
    props_dict = format_data(cat_id)
    fp = open('./%s.csv' % cat_id, 'w')
    fp1 = open('./%s_count.csv' % cat_id, 'w')
    fp.writelines('类目id,属性名称,属性值,是否标准\n')
    fp1.writelines('类目id,属性名称,标准属性个数,非标准属性个数\n')
    for p in props_dict:
        for s in props_dict[p]['value']:
            fp.writelines('%s,%s,%s,s\n' % (cat_id, props_dict[p]['key'], s.replace(',', ' ')))
        for a in props_dict[p]['alias']:
            fp.writelines('%s,%s,%s,n\n' % (cat_id, props_dict[p]['key'], a.replace(',', ' ')))

        fp1.writelines('%s,%s,%s,%s\n' % (cat_id, props_dict[p]['key'], len(props_dict[p]['value']), len(props_dict[p]['alias'])))



    print 'finished'

def main():
    get_csv(cat_id = 1623)

if __name__ == "__main__":
    main()
    raw_input()
