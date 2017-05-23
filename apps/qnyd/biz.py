# coding=UTF-8
import datetime

from apps.common.utils.utils_datetime import date_2datetime
from apps.subway.download import Downloader
from apps.subway.models_keyword import Keyword, Attention, kw_coll


def set_attention_kw(shop_id):
    '''一键设置重点关注词'''
    # 同步关键词报表
    rpt_days, good_kw_count, bad_kw_count = 7, 20, 10

    # 下载有adgroup有点击的关键词报表
    dler_obj = Downloader.objects.get(shop_id = shop_id)
    dl_flag, _ = dler_obj.check_status_4rpt(klass = Keyword)
    if dl_flag and dler_obj.tapi:
        Keyword.download_kwrpt_bycond(shop_id = shop_id, tapi = dler_obj.tapi, token = dler_obj.token, rpt_days = rpt_days, cond = 'click')

    # 获取效果最好、最差的关键词
    good_kw_list = get_top_roi_kw(shop_id = shop_id, rpt_days = rpt_days, kw_count = good_kw_count, sort_mode = -1)
    bad_kw_list = get_top_roi_kw(shop_id = shop_id, rpt_days = rpt_days, kw_count = bad_kw_count, sort_mode = 1)
    if not good_kw_list and not bad_kw_list: # 当没有报表时，根据“质量等分”、“关键词出价”来选取关键词
        good_kw_cur = kw_coll.find({'shop_id':shop_id, 'is_focus':{'$ne':True}}, {'qscore':1}).sort([('qscore', -1)]).limit(good_kw_count)
        bad_kw_cur = kw_coll.find({'shop_id':shop_id, 'is_focus':{'$ne':True}}, {'max_price':1}).sort([('max_price', -1)]).limit(bad_kw_count)
        good_kw_list = [kw['_id'] for kw in good_kw_cur]
        bad_kw_list = [kw['_id'] for kw in bad_kw_cur]

    # 更新 kw_coll,attn_coll 数据库
    kw_id_list = list(set(good_kw_list) | set(bad_kw_list))
    kw_coll.update({'shop_id':shop_id, '_id':{'$in':kw_id_list}}, {'$set':{'is_focus':True}}, multi = True)

    attn_obj, is_create = Attention.objects.get_or_create(shop_id = shop_id)
    if not is_create:
        kw_id_list.extend(attn_obj.keyword_id_list)
    attn_obj.keyword_id_list = kw_id_list
    attn_obj.save()

    return True


def get_top_roi_kw(shop_id, rpt_days, kw_count, sort_mode):
    '''sort_mode=-1 时，获取全店效果最好的关键词；sort_mode=1 时，获取全店效果最差的关键词'''

    start_time = date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_days))
    query_dict = {'shop_id': shop_id, 'cost': {'$gt': 0}, 'date': {'$gte': start_time}}
    # match_str = (sort_mode > 0 and '$lt' or '$gt')
    pipeline = [{'$match': query_dict},
                {'$group': {'_id': '$keyword_id',
                            'click':{'$sum':'$click'},
                            'cost':{'$sum':'$cost'},
                            'directpay':{'$sum':'$directpay'},
                            'indirectpay':{'$sum':'$indirectpay'},
                            'rpt_days': {'$sum': 1},
                            },
                 },
                # {'$project':{'_id':1, 'pay':{'$sum': ['$directpay', '$indirectpay']}, 'cost':1}},
                # {'$project':{'_id':1, 'roi':{'$divide':['$pay', '$cost']}, 'cost':1}},
                {'$project':{'_id':1, 'roi':{'$divide':[{'$add': ['$directpay', '$indirectpay']}, '$cost']}, 'cost':1}},
                # {'$match':{'roi':{match_str:1}}},
                {'$sort':{'roi':sort_mode, 'cost':-1}},
                {'$limit':kw_count},
                ]
    kw_list = Keyword.Report._get_collection().aggregate(pipeline)['result']
    kw_id_list = [kw['_id'] for kw in kw_list]
    return kw_id_list
