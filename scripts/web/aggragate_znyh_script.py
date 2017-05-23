# coding=UTF-8

import pymongo
import datetime
import os

#=================================================================================
# 聚合近七天内所有用过智能优化操作的宝贝整体数据情况，并保存文件：statistics_result.csv
#=================================================================================
web_online_conn = pymongo.Connection(host = 'mongodb://PS_superAdmin:PS_managerAdmin@223.4.49.56:30001/')
online_db = web_online_conn.ztcjl4
online_adg_coll = online_db.subway_adgroup

days = 7
date_time = datetime.date.today() - datetime.timedelta(days = days)
date_day = datetime.datetime(year = date_time.year, month = date_time.month, day = date_time.day)
aggregate_pipeline = [
                                    {
                                        '$match':{
                                                'optm_type':1, # 此处可改变成 批量优化
                                                'optm_submit_time':{'$gte':date_day},
                                                'rpt_list.date':{'$lte':date_day}
                                        }
                                     },
                                    {
                                        '$unwind':'$rpt_list'
                                     },
                                     {
                                        '$match':{
                                                'rpt_list.date':{'$gte':date_day}
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
                                                            }
                                                    }
                                        }
                      ]

try:
    result_list = online_adg_coll.aggregate(aggregate_pipeline)['result']
except Exception, e:
    print 'aggragete error, e=%s' % (e)

field_list = [u'aclick', u'cpc', u'favshopcount', u'ctr', u'directpay', u'roi', u'conv', u'pay', u'indirectpay', u'fav_roi', u'profit', u'favitemcount', u'indirectpaycount', u'paycount', u'impressions', u'directpaycount', u'favcount', u'click', u'cost']
field_name_list = ['千次点击', '平均点击花费', '店铺收藏量', '点击率(非%)', '直接成交额(分)', 'ROI', '转化率(非%)', '总成交额(分)', '间接成交额(分)', '收藏ROI', '纯利润(分)', '收藏总量', '间接成交量', '总成交量', '展现量', '直接成交量', '收藏总量', '点击量', '花费(分)']
if result_list and result_list[0]:
    result = result_list[0]
    file_name = 'statistics_result.csv'
    try:
        if os.path.exists(file_name):
            os.remove(file_name)
    except Exception, e:
        print "脚本终止，请确认该文件是否为打开状态，或系统禁止删除。"
    else:
        f = open('statistics_result.csv', 'w')
        try:
            title = ' ,'.join(field_name_list)
            content_list = []
            for field in field_list:
                if result.has_key(field):
                    content_list.append(result[field])
            content = ','.join(map(str, content_list))
            f.write(('%s\n%s' % (title , content)).encode('GBK'))
        except Exception, e:
            print 'write file error , e=%s' % (e)
        finally:
            f.close()
