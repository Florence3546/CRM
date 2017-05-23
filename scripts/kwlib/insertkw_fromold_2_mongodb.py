#-*- encoding: utf-8 -*-
'''
@author: Hugh
Created on 2013-5-20
'''
#import math
import pymongo, MySQLdb
#import re

#以下是mongodb连接
#pyconn = pymongo.Connection('127.0.0.1', 30001)
#kwlib = pyconn.kwlib
#cats = kwlib.cats_new

pyconn_remote = pymongo.Connection('192.168.2.166', 20004)
kwlib_remote = pyconn_remote.kwlib
kw_detail = kwlib_remote.kw_detail

#cat_dict = {}#保留每个类目所属的类目ID，如{16:16,50080:16}
#for cat in cats.find():
#    cat_id = cat['category_id']
#    if cat.get('parent_cid', ''):
#        first_cat_id = int(cat['parent_cid'].split(' ')[0])
#        cat_dict.update({cat_id:first_cat_id})
#    else:
#        cat_dict.update({cat_id:cat_id})

#以下是mysql连接
msconn = MySQLdb.Connect(host = '127.0.0.1', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl3')
cursor = msconn.cursor()

#以下是丢失的数据汇总文件
#full_file_path = u'D:/Mongodb Data/log/import_lose.log'
#f = open(full_file_path, 'w')

size = 3000 #一次导入数据量
start = 0   #起始索引
max_count = 11385640    #数据总量
page = 3796
#failed_count = 0
sql = 'select * from kwlib_keyworddetailinfo_20120730142335 limit %s, %s'
for p in range(page):
    cursor.execute(sql, (start, size))
    print 'now import data from %s, page = %s' % (start, p)
    start += size
    descr = cursor.description  #表头
    tmp_insert_list = []
    for result in cursor.fetchall():
        tmp_dict = {}
        for i in range(len(result)):
            tmp_dict.update({descr[i][0]:result[i]})
        tmp_dict['_id'] = tmp_dict['id']
        del tmp_dict['id']
        tmp_insert_list.append(tmp_dict)
#        try:
#            if tmp_dict['cat_id']:
#                tmp_first_cat_id = cat_dict.get(tmp_dict['cat_id'], None)
#                if tmp_first_cat_id:#首先通过类目字典来取一级类目
#                    tmp_dict['first_cat_id'] = tmp_first_cat_id
#                else:#取不到，再尝试通过类目名称取
#                    cat = cats.find_one({'category_name':re.compile(tmp_dict['cat_name'].split('>')[0].upper())})
#                    if cat:
#                        tmp_dict['first_cat_id'] = cat['category_id']
#                    else:#还是没取到，直接扔掉算了
#                        raise Exception('can not match cat_id')
#            else:
#                raise Exception('mysql data has no cat_id')
#        except Exception, e:
#            failed_count += 1
#            f.write('cat_id = %s,cat_name = %s, word = %s, error = %s\n' % (tmp_dict['cat_id'], tmp_dict['cat_name'], tmp_dict['word'], e))

    try:
        kw_detail.insert(tmp_insert_list)
#        print 'insert %s records.' % len(tmp_insert_list)
    except Exception, e:
        print 'insert error, e = %s' % e

#print 'total lose %s keywords' % failed_count

#f.close()
msconn.close()
#pyconn.close()
pyconn_remote.close()
