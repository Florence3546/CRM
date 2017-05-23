# coding=UTF-8
import init_environ
from apps.kwlib.models import  ProductWord
import datetime
import csv


'''
.统计每个类目属于哪种类型，类型：max:大类目、middle：中类目、mini:小类目
'''


now_time = datetime.date.today()
csvfile = file('D:/ztcdata/upload/%s_statistics_prdt_len.csv' % now_time, 'wb')
writer = csv.writer(csvfile)
writer.writerow([u'类目ID', u'可确定产品词'])
data = []


prdt_coll = ProductWord._get_collection()
for prdt in prdt_coll.find():
    word = prdt['product_word']
    for wd in word.split(','):
        if len(wd) >= 4:
            data.append((prdt['cat_id'], word))
            break



writer.writerows(data)
csvfile.close()
