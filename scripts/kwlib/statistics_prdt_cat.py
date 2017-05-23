# coding=UTF-8
import init_environ
from apps.subway.models_item import Item
from apps.kwlib.models import CatInfo, ProductWord
import csv
import datetime


'''
.统计不能够解析出产品词的类目
'''


now_time = datetime.date.today()
csvfile = file('D:/ztcdata/upload/%s_statistics_prdt_cat.csv' % now_time, 'wb')
writer = csv.writer(csvfile)
writer.writerow([u'类目ID', u'类目名称'])
data = []

cat_coll = CatInfo._get_collection()
cat_id_list = [cat['cat_id'] for cat in cat_coll.find()]
data = []
index = 0
for cat_id in cat_id_list :
    print index
    index += 1
    prdt_list = []
    has_item = False
    for item in Item.objects.filter(cat_id = cat_id).limit(10):
        try:
            prdt_list.extend(item.get_product_word_list())
        except Exception, e:
            continue
        has_item = True
        if prdt_list :
            break
    if not prdt_list and has_item:
        data.append((cat_id , CatInfo.get_cat_path(cat_id = cat_id)))

writer.writerows(data)
csvfile.close()
