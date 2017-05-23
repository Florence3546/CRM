# coding=UTF-8

import pymongo
import datetime

#=================================================================================
# 获取省油宝，北斗计划的所对应的统计结果，并保存到：statistics_campaign_result.csv文件
#=================================================================================
web_online_conn = pymongo.Connection(host = 'mongodb://PS_superAdmin:PS_managerAdmin@223.4.49.56:30001/')
web_db = web_online_conn.ztcjl4
web_camp_coll = web_db.subway_campaign
web_mnt_camp_coll = web_db.mnt_campaign

def get_aggr_camp_dict(title_list):
    mnt_camp_cursor = web_mnt_camp_coll.find({'mnt_type':{'$in':[1, 2]}}, {'_id':1})
    mnt_camp_set = set()
    if mnt_camp_cursor:
        for mnt_camp in mnt_camp_cursor:
            if mnt_camp.has_key('_id'):
                try:
                    mnt_camp_set.add(int(mnt_camp['_id']))
                except Exception, e:
                    print 'type converted error, e=%s' % (e)
                    continue

    result_dict = {}
    for title in title_list:
        if not result_dict.has_key(title):
            camp_cursor = web_camp_coll.find({'_id':{'$nin':list(mnt_camp_set)}, 'title':{'$regex':title}}, {'_id':1})
            camp_set = set()
            if camp_cursor:
                for camp in camp_cursor:
                    if camp.has_key('_id'):
                        try:
                            camp_set.add(int(camp['_id']))
                        except Exception, e:
                            print 'type converted error, e=%s' % (e)
                            continue
            result_dict[title] = list(camp_set)
    return result_dict

def get_aggr_result(title_list, result_dict):
    aggr_result_dict = {}
    for title in title_list:
        if result_dict.has_key(title) and result_dict[title]:
            aggr_pipeline = [
                                        {
                                            '$match':{
                                                            '_id':{'$in':result_dict[title]},
                                                            'rpt_list.date':{'$lte':someday_time}
                                                      }
                                         },
                                        {
                                           '$unwind':'$rpt_list'
                                        },
                                        {
                                           '$match':{
                                                           'rpt_list.date':{'$gte':someday_time}
                                                     }
                                        },
                                        {
                                           '$group':{
                                                           '_id':1,
                                                           # 基础数据
                                                           'total_impressions':{'$sum':'$rpt_list.impressions'},
                                                           'total_click':{'$sum':'$rpt_list.click'},
                                                           'total_cost':{'$sum':'$rpt_list.cost'},
                                                           'total_aclick':{'$sum':'$rpt_list.aclick'},
                                                           # 效果数据
                                                           'total_directpay':{'$sum':'$rpt_list.directpay'},
                                                           'total_indirectpay':{'$sum':'$rpt_list.indirectpay'},
                                                           'total_directpaycount':{'$sum':'$rpt_list.directpaycount'},
                                                           'total_indirectpaycount':{'$sum':'$rpt_list.indirectpaycount'},
                                                           'total_favitemcount':{'$sum':'$rpt_list.favitemcount'},
                                                           'total_favshopcount':{'$sum':'$rpt_list.favshopcount'},

                                                           # 计划IDlist
                                                           'campaign_list':{'$addToSet':'$_id'}
                                                     }
                                         },
                                         {
                                           '$project':{
                                                           # 基础数据
                                                           'impressions':'$total_impressions',
                                                           'cost':'$total_cost',
                                                           'click':'$total_click',
                                                           'aclick':'$total_aclick',

                                                           # 效果数据
                                                           'directpay':'$total_directpay',
                                                           'indirectpay':'$total_indirectpay',
                                                           'directpaycount':'$total_directpaycount',
                                                           'indirectpaycount':'$total_indirectpaycount',
                                                           'favitemcount':'$total_favitemcount',
                                                           'favshopcount':'$total_favshopcount',

                                                           # 计算数据
                                                           # cpc 平均点击花费
                                                           'cpc':{
                                                                   '$cond' : [
                                                                                       { '$eq' : ['$total_click', 0] },
                                                                                       0,
                                                                                       {'$divide':['$total_cost', '$total_click']},
                                                                                   ]
                                                           },

                                                           # ctr 点击率
                                                           'ctr':{
                                                                   '$cond' : [
                                                                                       { '$eq' : ['$total_impressions', 0] },
                                                                                       0,
                                                                                       {'$divide':['$total_click', '$total_impressions']},
                                                                                   ]
                                                           },


                                                           # paycount 成交量
                                                           'paycount':{'$add':['$total_directpaycount', '$total_indirectpaycount']},

                                                           # conv 转化率
                                                           'conv':{
                                                                       '$cond':[
                                                                                       {'$eq':['$total_click', 0]},
                                                                                       0,
                                                                                       {
                                                                                            '$divide':[
                                                                                                           {'$add':['$total_directpaycount', '$total_indirectpaycount']},
                                                                                                           '$total_click'
                                                                                               ]
                                                                                        }
                                                                                ]

                                                                   },

                                                           # pay 成交金额
                                                           'pay':{'$add':['$total_directpay', '$total_indirectpay']},

                                                           # roi 投资回报比
                                                           'roi':{
                                                                    '$cond':[
                                                                                   {'$eq':['$total_cost', 0]},
                                                                                   0,
                                                                                   {
                                                                                        '$divide':[
                                                                                                       {'$add':['$total_directpay', '$total_indirectpay']},
                                                                                                       '$total_cost'
                                                                                       ]
                                                                                    }
                                                                             ]
                                                                   },

                                                           # favcount 收藏量
                                                           'favcount':{'$add':['$total_favitemcount', '$total_favshopcount']},

                                                           # fav_roi 收藏roi
                                                           'fav_roi':{
                                                                           '$cond':[
                                                                                           {'$eq':['$total_click', 0]},
                                                                                           0,
                                                                                           {
                                                                                                '$divide':[
                                                                                                               {'$add':['$total_favitemcount', '$total_favshopcount']},
                                                                                                               '$total_click'
                                                                                               ]
                                                                                            }
                                                                                    ]
                                                                   },

                                                           # profit 纯利润
                                                           'profit':{
                                                                     '$subtract':[
                                                                                       {'$add':['$total_directpay', '$total_indirectpay']},
                                                                                       '$total_cost'
                                                                                   ]
                                                                   },
                                                            'campaign_list':'$campaign_list'
                                                           }
                                          }

                             ]
            try:
                result_list = web_camp_coll.aggregate(aggr_pipeline)['result']
                if result_list:
                    aggr_result_dict[title] = result_list[0]
            except Exception, e:
                print 'aggregate error, e=%s' % e
    return aggr_result_dict


title_list = ['省油宝长尾', '省油宝加力', '北斗']
days = 7
file_name = 'statistics_campaign_result.csv'
someday = datetime.date.today() - datetime.timedelta(days = days)
someday_time = datetime.datetime(someday.year, someday.month, someday.day)

result_dict = get_aggr_camp_dict(title_list)
aggr_result_dict = get_aggr_result(title_list, result_dict)

field_list = [u'aclick', u'cpc', u'favshopcount', u'ctr', u'directpay', u'roi', u'conv', u'pay', u'indirectpay', u'fav_roi', u'profit', u'favitemcount', u'indirectpaycount', u'paycount', u'impressions', u'directpaycount', u'favcount', u'click', u'cost']
field_name_list = ['计划类型', '千次点击', '平均点击花费', '店铺收藏量', '点击率(非%)', '直接成交额(分)', 'ROI', '转化率(非%)', '总成交额(分)', '间接成交额(分)', '收藏ROI', '纯利润(分)', '收藏总量', '间接成交量', '总成交量', '展现量', '直接成交量', '收藏总量', '点击量', '花费(分)', '统计计划数']

f = open(file_name, 'w')
try:
    content = '%s\n' % (' ,'.join(field_name_list))
    for title, result in aggr_result_dict.items():
        content_list = ['%s计划' % (title)]
        for field in field_list:
            if result.has_key(field):
                content_list.append(result[field])
            else:
                content_list.append(0)
        if result.has_key('campaign_list'):
            content_list.append(len(result['campaign_list']))
        else:
            content_list.append(0)
        content += '%s\n' % (','.join(map(str, content_list)))
    f.write(content.encode('GBK'))
except Exception, e:
    print 'write file error , e=%s' % (e)
finally:
    f.close()






