# coding=UTF-8
#===========================================================================
# 功能：从淘宝获取相应类目的标准属性，并比较我们的原子词数据库，统计出他们的包含关系。并生成csv
# 用法：请修改第25行，给出类目id
# 注意：类目id必须是叶子类目
# by:钟进峰
#===========================================================================

import init_environ
from import_all import *
from apilib import *
import pymongo
from apps.kwslt.models_cat import Cat

reload(sys)
sys.setdefaultencoding("utf-8")


conn = pymongo.Connection(host = '192.168.1.210', port = 2222)
kwlib = conn.kwlib
cat_coll = kwlib.kwlib_elementword

shop_id = 63518068

temp_cid = cid = 50003333
while 1:
    temp = Cat.get_cat_attr_func(cat_id = temp_cid, attr_alias = "parent_cids")
    if not temp:
        pid = temp_cid
        break
    temp_cid = temp
cat_name = Cat.get_cat_attr_func(cat_id = temp_cid, attr_alias = "cat_name")
user = User.objects.get(shop_id = shop_id)
tapi = get_tapi(user)

result_dict = tapi.itemprops_get(fields = "name,prop_values,name_alias", cid = cid).to_dict()
cat_list = result_dict['item_props']


local_cat_list = cat_coll.find({'cat_id':pid})

local_cat_list = [w['word'] for w in local_cat_list]

for cat in cat_list['item_prop']:
    if not cat.has_key('prop_values'):
        continue
    property, p_in_w, w_in_p = '', '', ''
    print '==============cat_name:' + cat['name'] + '================'
    for prop in cat['prop_values']['prop_value']:
        property = property + prop['name'] + ' '
        for w in local_cat_list:
            if prop['name'] in w:
                print 'p_in_w:\t' + str(w)
                if w not in p_in_w:
                    p_in_w = p_in_w + w + ' '
                local_cat_list.pop(local_cat_list.index(w))
                continue
            if w in prop['name']:
                print 'w_in_p:\t' + str(prop['name'])
                if w not in w_in_p:
                    w_in_p = w_in_p + w + ' '
                local_cat_list.pop(local_cat_list.index(w))
                continue
    cat['csv'] = (property, p_in_w, w_in_p)

fp = open('./%s.csv' % (str(cid) + '_' + str(pid) + '_' + cat_name.decode('utf-8').replace('/', '_')), 'w')

fp.writelines('类目id,属性名称,标准属性,原子词包含标准属性,标准属性包含原子词\n')
for c in cat_list['item_prop']:
    if not c.has_key('prop_values'):
        continue
    fp.writelines('%s,%s,%s,%s,%s\n' % (cid, c['name'], c['csv'][0], c['csv'][1], c['csv'][2]))

fp.writelines('标准属性不包含的原子词\n')
for c in local_cat_list:
    fp.writelines('%s\n' % (c))

print 'finish'
raw_input()
