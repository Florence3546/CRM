# coding=UTF-8

import init_environ

from pymongo.connection import Connection
from apps.common.biz_utils.utils_dictwrapper import DictWrapper, AdgroupHelper
from apps.subway.upload import delete_adgroups

py_conn = Connection(host = '10.241.52.246', port = 30001)
db = py_conn.ztcjl4
db.authenticate('PS_ztcjl4Admin', 'PS_managerZtcjl4')
adg_coll = db.subway_adgroup

def statictics_double_adgroup_byitem():
    aggr_pipeline = [
                        {
                            '$group':{
                                          '_id':{'item_id':'$item_id','campaign_id':'$campaign_id','shop_id':"$shop_id"},
                                          'adgroup_total' : { '$sum': 1 },
                                        'adg_list':{'$addToSet':'_id'}
                                      }
                        },
                        {
                            '$match':{
                                            'adgroup_total':{
                                                                        "$gt":1
                                                             }
                                      }
                         }
             ]
    counter = 0
    camp_set = set()
    shop_set = set()
    for cur_adg in adg_coll.aggregate(aggr_pipeline, allowDiskUse= True)['result']:
        counter += 1
        camp_set.add(cur_adg['_id']['campaign_id'])
        shop_set.add(cur_adg['_id']['shop_id'])
    print 'shop counter : ',len(shop_set)
    print 'campaign counter : ',len(camp_set)
    print 'item counter : ',counter

def get_dadg_list(shop_id,camp_ids):
    aggr_pipeline = [
                        {
                            '$match':{
                                        'shop_id':shop_id,
                                        'campaign_id':{"$in":camp_ids}
                                      }
                         },
                        {
                            '$group':{
                                          '_id':{'item_id':'$item_id','campaign_id':'$campaign_id','shop_id':"$shop_id"},
                                          'adgroup_total' : { '$sum': 1 },
                                          'adg_list':{'$addToSet':'$_id'}
                                      }
                        },
                        {
                            '$match':{
                                            'adgroup_total':{
                                                                        "$gt":1
                                                             }
                                      }
                         }
             ]

    result_list = []
    for cur_adg in adg_coll.aggregate(aggr_pipeline, allowDiskUse= True)['result']:
        temp_dict = {}
        temp_dict.update(cur_adg['_id'])
        temp_dict.update({'adg_list':cur_adg['adg_list']})
        result_list.append(DictWrapper(temp_dict))
    return result_list # as : [{'item_id': 41277564918L, 'adg_list': [454551306, 453152777], u'shop_id': 69342483, u'campaign_id': 15054447}]

def get_del_adgs(shop_id,adgs):
#     print adgs
    adg_list = adg_coll.find({'shop_id':shop_id,'_id':{'$in':adgs}})
    best_adg = 0
    score = 0
    for adg in adg_list:
        tmp = AdgroupHelper(**adg)
        temp_score = tmp.roi7 * 10000 + tmp.click7 * 100 + tmp.impr7*1 # 100impr = 1 click = 1/100 成交
#         print temp_score,tmp.adgroup_id
        if temp_score > score:
            score = temp_score
            best_adg = tmp.adgroup_id

    adgs.remove(best_adg)
    delete_adgroups(shop_id,adgs)
#     print adgs

def del_adgs(adgs):
    for adg in adgs:
        delete_adgroups(adg.shop_id,adg.adgroup_ids)

if __name__ == "__main__":
    shop_id=69342483
    camp_ids = [15054447]

    counter = 0
    for data in get_dadg_list(shop_id,camp_ids):
#         print shop_id ,data.adg_list
        get_del_adgs(shop_id ,data.adg_list)
        print 'just has finished %s, they are %s'%(len(data.adg_list),data.adg_list)

