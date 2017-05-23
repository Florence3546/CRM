# coding=UTF-8
import init_environ
from apps.kwlib.models import CatInfo
from apps.subway.models_item import Item
import datetime
import csv
from apps.kwslt.base import is_string_char_digit

'''
.统计不能够解析出产品词的类目
'''


now_time = datetime.date.today()
csvfile = file('D:/ztcdata/upload/%s_statistics_elem_by_item.csv' % now_time, 'wb')
writer = csv.writer(csvfile)
writer.writerow([u'类目ID', u'宝贝标题', u'长度大于等于5的字符串', u'拆分后排序标题'])
data = []

cat_id_list = [cat.cat_id for cat in CatInfo.objects.all()]
# cat_id_list = [121434005]

for cat_id in cat_id_list :
    for item in Item.objects.filter(cat_id = cat_id):
        item_list = item.pure_title_word_list
        item_list = sorted(item_list, key = len, reverse = True)
        tmp_list = []
        for word in item_list:
            word_len = len(word)
            if word_len >= 5 :
                if not is_string_char_digit(word):
                    tmp_list.append(word)
            elif word_len < 5:
                break
            else:
                break
        if tmp_list:
            data.append((cat_id, item.title, ','.join(tmp_list), ','.join(item_list)))

writer.writerows(data)
csvfile.close()
