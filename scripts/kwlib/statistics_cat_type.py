# coding=UTF-8
import init_environ
from apps.kwlib.models import CatInfo, SelectConf
from apps.subway.models_item import Item
from apps.kwlib.select_words import select_words
import datetime
import csv



'''
.统计每个类目属于哪种类型，类型：max:大类目、middle：中类目、mini:小类目
'''


now_time = datetime.date.today()
csvfile = file('D:/ztcdata/upload/%s_statistics_cat_type.csv' % now_time, 'wb')
writer = csv.writer(csvfile)
writer.writerow([u'类目ID', u'类目名称', u'类目类型', u'平均个数'])
data = []

# select_conf = {
#   "_id" : "test_check_type_conf",
#   "candi_filter" : "score == 1000",
#   "conf_desc" : "精准淘词默认配置",
#   "delete_conf" : {
#     "remove_dupli" : 0,
#     "remove_del" : 0,
#     "remove_cur" : 0
#   },
#   "label_define_list" : [],
#   "price_conf_list" : [],
#   "select_conf_list" : [{
#       "candi_filter" : "score==1000",
#       "sort_mode" : "click",
#       "select_num" : "0-1"
#     }]
# }

select_conf = SelectConf.objects.get(conf_name = 'test_check_type_conf')
cat_coll = CatInfo._get_collection()
cat_id_list = [cat['cat_id'] for cat in cat_coll.find()]
adgroup = None
count = 0
for cat_id in cat_id_list :
    print count
    count += 1
    score_count, item_count, cat_type = 0, 0, ''
    for item in Item.objects.filter(cat_id = cat_id).limit(5):
        item_count += 1
        result_list = select_words(adgroup, item, select_conf)
        score_count += len(result_list)
    if not item_count:
        continue
    cat_count = score_count / item_count
    if cat_count >= 300:
        cat_type = 'max'
    elif 100 < cat_count < 300:
        cat_type = 'middle'
    else:
        cat_type = 'mini'
#     cat_coll.update({'cat_id':cat_id}, {'$set':{'cat_type':cat_type}})
    data.append((cat_id, CatInfo.get_cat_path(cat_id = cat_id), cat_type, cat_count))

writer.writerows(data)
csvfile.close()
