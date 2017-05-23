# coding=UTF-8

import pymongo

#=================================================================================
# 获取限价与类目平均PPC80%低的宝贝列表，并保存文件：statistics_lowprice_adg.csv
#=================================================================================
web_online_conn = pymongo.Connection(host = 'mongodb://PS_superAdmin:PS_managerAdmin@10.241.48.210:30001/')
kwlib_online_conn = pymongo.Connection(host = 'mongodb://PS_superAdmin:PS_managerAdmin@10.241.51.158:30001/')
web_db = web_online_conn.ztcjl4
kwlib_db = kwlib_online_conn.kwlib
web_adg_coll = web_db.subway_adgroup
kwlib_cat_info_coll = kwlib_db.kwlib_catinfo

def get_each_cat_ppc():
    """依次获取每一类目的平均CPC"""
    cat_ppc_mapping = {}
    cat_info_cursor = kwlib_cat_info_coll.find({}, {'cat_id':1, '_id':0, 'avg_cpc':1})
    for cat_info in cat_info_cursor:
        try:
            if cat_info.has_key('cat_id') and cat_info['cat_id']:
                if cat_info.has_key('avg_cpc') and cat_info['avg_cpc']:
                    cat_ppc_mapping.update({int(cat_info['cat_id']):cat_info['avg_cpc']})
                else:
                    cat_ppc_mapping.update({int(cat_info['cat_id']):0})
        except Exception, e:
            print 'convert error, e=%s' % (e)
            continue
    return cat_ppc_mapping

def get_adginfo_4lowprice(cat_ppc_dict, adg_type = 2, ratio = 0.8):
    """获取现网中存在的低限价的宝贝"""
    adg_cursor = web_adg_coll.find({'mnt_type':adg_type}, {'category_ids':1, 'limit_price':1, 'shop_id':1, 'campaign_id':1, 'item_id':1})
    no_limit_adg_list = []
    no_avg_ppc_list = []
    low_limit_adg_list = []
    normal_adg_list = []
    for adg in adg_cursor:
        adg_id = adg.get('_id', 0)
        category_ids = adg.get('category_ids', '')
        limit_price = adg.get('limit_price', 0)
        if adg_id and category_ids :
            category_list = category_ids.split()
            avg_ppc = 0
            cat_id = 0
            cat_len = len(category_list)
            for cat_index in xrange(cat_len - 1, -1, -1):
                try:
                    key = int(category_list[cat_index])
                    if cat_ppc_dict.has_key(key) and cat_ppc_dict[key]:
                        avg_ppc = cat_ppc_dict[key]
                        cat_id = key
                        break
                except Exception, e:
                    print 'convert error, e=%s' % (e)
                    continue
            if limit_price:
                if avg_ppc:
                    try:
                        adg.update({'avg_ppc':avg_ppc, 'cat_id':cat_id})
                        if int(limit_price) < int(avg_ppc) * ratio:
                            low_limit_adg_list.append(adg)
                        else:
                            normal_adg_list.append(adg)
                    except Exception, e:
                        print 'convert error, e=%s' % (e)
                        continue
                else:
                    no_avg_ppc_list.append(adg)
            else:
                no_limit_adg_list.append(adg)
    return low_limit_adg_list, no_limit_adg_list, no_avg_ppc_list, normal_adg_list


ratio = 0.8

adg_total = web_adg_coll.find().count()
zdtg_adg_total = web_adg_coll.find({'mnt_type':2}, {'category_ids':1, 'limit_price':1, 'shop_id':1, 'campaign_id':1, 'item_id':1}).count()
adg_title_one_list = ['现网所有宝贝总数', '重点托管宝贝总数']
adg_cotent_one_list = map(str, [adg_total, zdtg_adg_total])

cat_ppc_mapping = get_each_cat_ppc()
low_limit_adg_list, no_limit_adg_list, no_avg_ppc_list, normal_adg_list = get_adginfo_4lowprice(cat_ppc_mapping, ratio = ratio)
adg_title_two_list = ['未设置限价推广组', '无类目平均出价推广组', '正常限价推广组', '限价低推广组（%s%%）' % (int(ratio * 100))]
adg_cotent_two_list = map(str, [len(no_limit_adg_list) , len(no_avg_ppc_list) , len(normal_adg_list) , len(low_limit_adg_list)])

adg_title_three_list = ['限价低推广组列表如下:']
adg_title_five_list = ['推广组ID', '计划ID', '店铺ID', '当前限价(元)', '类目PPC(元)', '类目ID']

csv_text = ''
csv_text_list = [adg_title_one_list, adg_cotent_one_list, '', adg_title_two_list, adg_cotent_two_list, '', adg_title_three_list, adg_title_five_list]
for adg in low_limit_adg_list:
    csv_text_list.append(map(str, [adg.get('_id', 0), adg.get('campaign_id', 0), adg.get('shop_id', 0), adg.get('limit_price', 0) * 1.0 / 100, adg.get('avg_ppc', 0) * 1.0 / 100, adg.get('cat_id', 0)]))

for text_list in csv_text_list:
    csv_text += '%s\n' % ((','.join(text_list)))

f = open('statistics_lowprice_adg.csv', 'w')
try:
    f.write(csv_text.encode('GBK'))
except Exception, e:
    print 'write file error , e=%s' % (e)
finally:
    f.close()






