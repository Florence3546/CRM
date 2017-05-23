# coding=UTF-8
import init_environ
from apps.subway.models_keyword import IllegalKeyword
from apps.kwlib.models import ForbidWord, Cat
import csv
import datetime

'''
.收录当前违禁词表没有收录的违禁词，把已经收录过的违禁词标注为已处理：is_handled=1，把没有收录进来的违禁词标注：is_handled=2,导出is_handled=2到csv，根据日期来标明标题。
'''

now_time = datetime.date.today()
csvfile = file('D:/forbidword/%s.csv' % now_time, 'wb')
writer = csv.writer(csvfile)
writer.writerow([u'一级类目ID', u'当前类目名称', u'当前类目ID', u'关键词', u'店铺类型'])
ill_coll = IllegalKeyword._get_collection()
forbid_coll = ForbidWord._get_collection()
for kw in ill_coll.find({'is_handled':0}):
    is_forbid = False
    forbid_list = ForbidWord.get_forbidword_list(int(kw['cat_id']))
    for fbd in forbid_list:
        if fbd in kw['word']:
            is_forbid = True
            break
    if is_forbid:
        ill_coll.update({'_id':kw['_id']}, {'$set':{'is_handled':1}})
    else:
        ill_coll.update({'_id':kw['_id']}, {'$set':{'is_handled':2}})

data = []
for kw in ill_coll.find({'is_handled':2}):
    data.append((kw['root_parent_id'], Cat.get_cat_path(cat_id = int(kw['cat_id'])), kw['cat_id'], kw['word'], kw['last_name']))

ill_coll.update({'is_handled':2}, {'is_handled':1}, multi = True)

writer.writerows(data)
csvfile.close()
