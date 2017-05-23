# _*_ coding:utf-8 _*_
import re
import copy
import datetime
from operator import itemgetter

from apps.common.utils.utils_json import json
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.common.constant import Const
from apps.common.utils.utils_datetime import date_2datetime, datetime_2string
from apps.common.utils.utils_number import round_digit
from apps.mnt.models import MntCampaign, MntMnger
from apps.subway.models import Adgroup, kw_coll, adg_coll, camp_coll, item_coll
from apilib import get_tapi
from apps.subway.upload import delete_keywords, update_keywords
from apps.kwslt.models_cat import Cat
from apps.web.models import pa_coll, AppComment
from apps.web.point import PointManager

# def get_health_check_list(cache_key):
#     """通过缓存对象得到真实数据库对象"""
#     shop_id = int(request.user.shop_id)
#     result_list = []
#     if '_' in cache_key:
#         cache_list = cache_key.split('_')
#         obj_mark = cache_list[0]
#         obj_id = int(cache_list[1])
#         if obj_mark == 'account':
#             result_list = Account.objects.only('health_check_list').get(shop_id = obj_id).health_check_list
#         elif obj_mark == 'item':
#             result_list = Item.objects.only('health_check_list').get(shop_id = shop_id, item_id = obj_id).health_check_list
#         elif obj_mark == 'adgroup':
#             adgroup_obj = Adgroup.objects.only('health_check_list', 'item_id').get(shop_id = shop_id, adgroup_id = obj_id)
#             result_list = adgroup_obj.health_check_list
#             item_check_list = Item.objects.only('health_check_list').get(shop_id = shop_id, item_id = adgroup_obj.item_id).health_check_list
#             if item_check_list:
#                 result_list.extend(item_check_list)
#     return result_list

def update_kws_8shopid(shop_id, kw_list, record_flag = True, optm_type = '', opter = 1, opter_name = ''):
    '''更新关键词的出价，匹配模式'''
    tapi = get_tapi(shop_id = shop_id)
    total_id_list = [int(i['keyword_id']) for i in kw_list]
    # 根据操作分出关键词

    top_deleted_id_list = [] # 淘宝已经删除的关键词
    deleted_id_list, updated_id_list, camp_id_list, adg_id_list, camp_kw_dict_2del, kw_2update = [], [], [], [], {}, []
    for kw in kw_list:
        campaign_id = int(kw['campaign_id'])
        camp_id_list.append(campaign_id)
        adgroup_id = int(kw['adgroup_id'])
        adg_id_list.append(adgroup_id)
        if kw['is_del']:
            camp_kw_dict_2del.setdefault(campaign_id, [])
            camp_kw_dict_2del[campaign_id].append([adgroup_id, int(kw['keyword_id']), kw['word'], 0, 0, None])
        else:
            kw_2update.append([campaign_id,
                                adgroup_id,
                                int(kw['keyword_id']),
                                kw['word'],
                                {'max_price': int(format(float(kw['new_price']) * 100, '.0f')),
                                'match_scope': int(kw['match_scope']),
                                'old_price': int(format(float(kw['max_price']) * 100, '.0f')),
                                'max_mobile_price': int(format(float(kw['max_mobile_price']) * 100, '.0f')),
                                'mobile_is_default_price': int(kw['mobile_is_default_price']),
                                'mobile_old_price': int(format(float(kw['mobile_old_price']) * 100, '.0f'))
                                }])

    # # 按计划将关键词分组
    # del_kw_group_camp, deleted_id_list = {}, []
    # if del_kw_list:
    #     for kw in del_kw_list:
    #         if not del_kw_group_camp.has_key(kw['campaign_id']):
    #             del_kw_group_camp[kw['campaign_id']] = []
    #         del_kw_group_camp[kw['campaign_id']].append([kw['adgroup_id'], int(kw['keyword_id']), kw['word'], 0, 0, None])
    # 建立托管计划字典

    # 提交到直通车
    # for key, values in del_kw_group_camp.items():
    for campaign_id, kw_arg_list in camp_kw_dict_2del.items():
        temp_del_id_list = delete_keywords(shop_id = shop_id, campaign_id = campaign_id, kw_arg_list = kw_arg_list, tapi = tapi, opter = opter, opter_name = opter_name)
        deleted_id_list.extend(temp_del_id_list)

    # 更新关键词出价，匹配模式
    if kw_2update:
        temp_update_id_list, top_del_id_list = update_keywords(shop_id = shop_id, kw_arg_list = kw_2update, tapi = tapi, opter = opter, opter_name = opter_name)
        updated_id_list.extend(temp_update_id_list)
        top_deleted_id_list.extend(top_del_id_list)

    failed_id_list = list(set(total_id_list) - set(updated_id_list) - set(deleted_id_list) - set(top_deleted_id_list)) # 其它失败的，从总提交的中间减去修改成功的、删除成功的、淘宝已经删除的

    if updated_id_list or deleted_id_list:
        adg_id_list = list(set(adg_id_list))
        data = {'optm_submit_time':datetime.datetime.now()}
        try:
            data['optm_type'] = int(optm_type)
        except:
            pass
        adg_coll.update({'shop_id':shop_id, '_id':{'$in':adg_id_list}}, {'$set':data})

    return updated_id_list, deleted_id_list, top_deleted_id_list, failed_id_list

def bulk_del_blackword(shop_id, word_list, camp_id = None, adg_id_list = None, opter = 1, opter_name = ''):
    del_id_list = []
    if (not camp_id) and (not adg_id_list):
        return del_id_list

    word_list_escaped = []
    for word in word_list:
        for sign in Const.COMMON_RE_SIGN:
            word = word.replace(sign, '\%s' % sign)
        word_list_escaped.append(word)
    start_time = date_2datetime(datetime.date.today() - datetime.timedelta(15))
    filter_dict = {'shop_id':shop_id,
                   '$or':[{'word':re.compile(word)} for word in word_list_escaped],
                   'rpt_list':{'$not':{'$elemMatch':{'date':{'$gte':start_time},
                                                     '$or':[{'directpaycount':{'$gt':0}}, {'indirectpaycount':{'$gt':0}}]
                                                     }}}
                   }
    if adg_id_list:
        filter_dict.update({'adgroup_id':{'$in':adg_id_list}})
    elif camp_id:
        filter_dict.update({'campaign_id':camp_id})
    else:
        return del_id_list
    kw_cursor = kw_coll.find(filter_dict, {'campaign_id':1, 'adgroup_id':1, '_id':1, 'word':1})
    kw_arg_dict = {}
    for keyword in kw_cursor:
        campaign_id, adgroup_id, keyword_id, word = keyword['campaign_id'], keyword['adgroup_id'], keyword['_id'], keyword['word']
        if not kw_arg_dict.has_key(campaign_id):
            kw_arg_dict[campaign_id] = []
        kw_arg_list = kw_arg_dict[campaign_id]
        kw_arg_list.append([adgroup_id, keyword_id, word, 0, 0, '包含屏蔽词'])
    for campaign_id, kw_arg_list in kw_arg_dict.items():
        sub_del_id_list = delete_keywords(shop_id = shop_id, campaign_id = campaign_id, kw_arg_list = kw_arg_list, data_type = 404, opter = opter, opter_name = opter_name)
        del_id_list.extend(sub_del_id_list)
    return del_id_list

def get_duplicate_word(query_dict, sort_mode, start, end, count = 2):
    '''获取整店所有重复词和重复次数，且按降序/升序排序后，切片以方便分页'''
    sort_flag = (sort_mode == 'desc' and -1 or 1)
    pipeline = [{'$match': query_dict},
                {'$group': {'_id': '$word', 'count': {'$sum': 1}, 'kw_list': {'$addToSet': {'_id': '$_id', 'campaign_id': '$campaign_id', 'adgroup_id': '$adgroup_id', 'word': '$word'}}}},
                {'$match': {'count': {'$gt': count}, }},
                {'$project': {'word': '$_id', 'count': 1, 'kw_list': "$kw_list"}},
                {'$sort': {'count': sort_flag, 'word': sort_flag}},
                ]
    data_count = 0 # 记录总数
    if end:
        # 如果需要分页查询，则还需要获取记录总数
        pipeline += [{'$limit': end }, {'$skip': start}]
        count_pipeline = [
            {'$match': query_dict},
            {'$group': {'_id': '$word', 'count':{'$sum': 1}}},
            {'$match': {'count':{'$gt':count}, }},
            {'$project':{'word':'$_id'}},
        ]
        data_count = len(kw_coll.aggregate(count_pipeline)['result'])
    kw_list = kw_coll.aggregate(pipeline, allowDiskUse = True)['result']
    return data_count, kw_list

def get_dupl_word_count(shop_id, word_list, sort_mode = 'desc'):
    '''获取一批词的重复次数'''
    sort_flag = -1 if sort_mode == 'desc' else 1
    pipeline = [{'$match': {'shop_id':shop_id}},
                {'$match': {'shop_id':shop_id, 'word':{'$in':word_list}, }},
                {'$group': {'_id': '$word', 'count':{'$sum': 1}, }},
                {'$project':{'count':1, }},
                {'$sort': {'count':sort_flag}},
                ]
    kw_list = kw_coll.aggregate(pipeline)['result']
    kw_dict = {}
    for kw in kw_list:
        kw_dict[kw['_id']] = kw['count']
    return kw_dict

def get_dupl_word_info(shop_id, last_day, word):
    '''获取一个重复词的所有关键词信息'''
    mnt_campid_list = MntMnger.get_longtail_camp_ids(shop_id = shop_id)
    kw_list = list(kw_coll.find({'shop_id': shop_id, 'word': word, 'campaign_id':{'$nin':mnt_campid_list}}, {'rpt_list':{'$slice':-last_day}}))

    camp_id_list, adg_id_list = [], []
    for kw in kw_list:
        camp_id_list.append(kw['campaign_id'])
        adg_id_list.append(kw['adgroup_id'])

    camp_cur = camp_coll.find({'_id':{'$in':camp_id_list}}, {'title':1})
    camp_dict = {camp['_id']:camp['title'] for camp in camp_cur}

    adg_cur = adg_coll.find({'shop_id':shop_id, '_id':{'$in':adg_id_list}}, {'item_id':1})
    adg_dict = {adg['_id']:adg['item_id'] for adg in adg_cur}

    item_cur = item_coll.find({'shop_id':shop_id, '_id':{'$in':adg_dict.values()}}, {'title':1, 'pic_url':1, 'price':1})
    item_dict = {item['_id']:(item['title'], item['price'], item['pic_url']) for item in item_cur }

    result = []
    start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = last_day))
    no_item_tuple = ('该宝贝可能不存在或者下架，请尝试同步数据', 0, '/site_media/jl/img/no_photo') # 当item不存在时，使用默认

    for kw in kw_list:
        cost, impr, click, pay = 0, 0, 0, 0
        if kw.has_key('rpt_list'):
            for rpt in kw['rpt_list']:
                if rpt['date'] >= start_time:
                    cost += rpt['cost']
                    impr += rpt['impressions']
                    click += rpt['click']
                    pay += rpt['directpay'] + rpt['indirectpay']
        temp_key = kw['adgroup_id']
        if temp_key in adg_dict:
            item_id = adg_dict[kw['adgroup_id']]
            temp_item_info = item_dict.get(item_id, no_item_tuple)
            result.append({'kw_id':kw['_id'], 'max_price': kw['max_price'], 'qscore': kw['qscore'], 'impr': impr, 'click': click, 'pay': pay,
                           'cpc': click and cost / click, 'ctr': impr and click / impr, 'camp_title': camp_dict[kw['campaign_id']],
                           'item_title': temp_item_info[0], 'item_price':temp_item_info[1], 'pic_url': temp_item_info[2], 'item_id':item_id
                           })

    result = sorted(result, key = itemgetter('ctr', 'impr', 'qscore', 'max_price'), reverse = True) # 按点击率、展现量、质量得分、出价降序排序
    return result

def get_garbage_words(shop_id):
    '''获取整店所有无展现词 (无展现词定义：连续15天展现为0且未激活）'''
    start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = 15))
    result = []
    mnt_campid_list = MntMnger.get_longtail_camp_ids(shop_id = shop_id)
    kw_cur = kw_coll.find({'shop_id': shop_id, 'is_garbage':True, 'campaign_id':{'$ne':mnt_campid_list}}, {'campaign_id':1, 'adgroup_id':1, 'word':1, 'rpt_list': {'$slice':-15}})
    for kw in kw_cur:
        impr = 0
        if kw.has_key('rpt_list'):
            for rpt in kw['rpt_list']:
                if rpt['date'] >= start_time:
                    impr += rpt['impressions']
        if impr == 0:
            result.append({'kw_id':kw['_id'], 'word':kw['word'], 'camp_id':kw['campaign_id'], 'adg_id':kw['adgroup_id']})
    return result

def filter_dupl_words(shop_id, condition, word_list):
    '''获取一批重复词按条件过滤后的所有关键词信息'''
    del_day, del_level, statistics_type, del_offline = condition['del_day'], condition['del_level'], condition['del_statistics_type'], condition['del_offline']
    mnt_campid_list = MntMnger.get_longtail_camp_ids(shop_id = shop_id)
    if not word_list:
        return []
    kw_list = list(kw_coll.find({'shop_id': shop_id, 'campaign_id':{'$ne':mnt_campid_list}, 'word': {'$in':word_list}}, {'word':1, 'qscore':1, 'campaign_id':1, 'adgroup_id':1, 'rpt_list': {'$slice':-del_day}}).sort('word'))

    if del_offline:
        camp_id_list, adg_id_list = [], []
        for kw in kw_list:
            camp_id_list.append(kw['campaign_id'])
            adg_id_list.append(kw['adgroup_id'])
        camp_cur = camp_coll.find({'_id':{'$in':camp_id_list}}, {'online_status':1})
        camp_status_dict = {camp['_id']:camp['online_status'] for camp in camp_cur}
        adg_cur = adg_coll.find({'shop_id':shop_id, '_id':{'$in':adg_id_list}}, {'online_status':1})
        adg_status_dict = {adg['_id']:adg['online_status'] for adg in adg_cur}

    kw_list.append({'word':None})
    temp_word, temp_list, result, count = '', [], [], 0
    start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = del_day))
    for kw in kw_list:
        # 当一个重复词遍历完后，排序，过滤后加入到result, 并初始化temp_word, temp_list
        if temp_word != kw['word']:
            temp_list = sorted(temp_list, key = itemgetter('ctr', 'impr', 'qscore'), reverse = True) # 按点击率、展现量、质量得分降序排序
            count = 0
            for obj in temp_list:
                count += 1
                if count > del_level and (statistics_type == '0' or obj[statistics_type] == 0) and (del_offline == 0 or obj['camp_status'] == obj['adg_status'] == 'online'):
                    result.append({'kw_id':obj['kw_id'], 'word':temp_word, 'camp_id':obj['camp_id'], 'adg_id':obj['adg_id']})
            temp_word, temp_list = kw['word'], []

        # 将当前词的相关信息存入 temp_list
        if kw['word']:
            impr, click = 0, 0
            if del_offline and kw.has_key('rpt_list'):
                for rpt in kw['rpt_list']:
                    if rpt['date'] >= start_time:
                        impr += rpt['impressions']
                        click += rpt['click']
            temp_list.append({'kw_id': kw['_id'], 'impr': impr, 'click': click, 'camp_id': kw['campaign_id'], 'adg_id': kw['adgroup_id'], 'qscore':kw['qscore'],
                              'ctr': impr and click / impr,
                              'adg_status':del_offline and adg_status_dict[kw['adgroup_id']] or '',
                              'camp_status': del_offline and camp_status_dict[kw['campaign_id']] or '',
                              })

    return result

def get_trend_chart_data(data_type, rpt_list):
    '''
    /封装趋势图数据
    data_type=((1,customer),(2,campaign),(3,adgroup),(4,keyword),(5,qnyd_acount),(6,ncrm_account))
    '''

    def format_digit(i):
        return round_digit(i, 2)

    def div100(i):
        return round_digit(float(i) / 100, 2)

    def mul100(i):
        return round_digit(float(i) / 0.01, 2)

    series_cfg_dict = {
        'impr':{'name':'展现量', 'color':'#426ab3', 'func':None, 'unit':'次', 'field_name':'impressions', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':0},
        'click':{'name':'点击量', 'color':'#87CEFA', 'func':None, 'unit':'次', 'field_name':'click', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':1, 'yaxis':0},
        'cpc':{'name':'PPC', 'color':'#06B9D1', 'func':div100, 'unit':'元', 'field_name':'cpc', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':1, 'yaxis':1},
        'ctr':{'name':'点击率', 'color':'#005687', 'func':format_digit, 'unit':'%', 'field_name':'ctr', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':1, 'yaxis':2},
        'cost':{'name':'总花费', 'color':'#1E90FF', 'func':div100, 'unit':'元', 'field_name':'cost', 'value_list':[], 'visible':True, 'opposite':True, 'is_axis':1, 'yaxis':3},
        'pay':{'name':'成交额', 'color':'#FD5B78', 'func':div100, 'unit':'元', 'field_name':'pay', 'value_list':[], 'visible':True, 'opposite':True, 'is_axis':0, 'yaxis':3}, # 与花费共y坐标
        'paycount':{'name':'成交量', 'color':'#FF84BA', 'func':None, 'unit':'笔', 'field_name':'paycount', 'value_list':[], 'visible':False, 'opposite':True, 'is_axis':1, 'yaxis':4},
        'favcount':{'name':'收藏量', 'color':'#f3715c', 'func':None, 'unit':'次', 'field_name':'favcount', 'value_list':[], 'visible':False, 'opposite':True, 'is_axis':0, 'yaxis':4},
        'roi':{'name':'ROI', 'color':'#FF0090', 'func':format_digit, 'unit':'', 'field_name':'roi', 'value_list':[], 'visible':False, 'opposite':True, 'is_axis':1, 'yaxis':5},
        'conv':{'name':'转化率', 'color':'#BF0A10', 'func':format_digit, 'unit':'%', 'field_name':'conv', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':2},
        'shop_pv':{'name':'店铺总流量', 'color':'#5c7a29', 'func':None, 'unit':'次', 'field_name':'shop_pv', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':0},
        'shop_uv':{'name':'店铺访客数', 'color':'#7fb80e', 'func':None, 'unit':'次', 'field_name':'shop_uv', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':0},
        'shop_conv':{'name':'店铺转化率', 'color':'#00FF7F', 'func':mul100, 'unit':'%', 'field_name':'shop_conv', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':2},
        'item_pv':{'name':'宝贝自然流量', 'color':'#5c7a29', 'func':None, 'unit':'次', 'field_name':'item_pv', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':0},
        'item_uv':{'name':'宝贝访客数', 'color':'#7fb80e', 'func':None, 'unit':'次', 'field_name':'item_uv', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':0},
        'item_conv':{'name':'宝贝转化率', 'color':'#00FF7F', 'func':None, 'unit':'%', 'field_name':'item_conv', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':2}, # 与点击率共y坐标
        'avgpos':{'name':'昨日平均排名', 'color':'#614B36', 'func':None, 'unit':'', 'field_name':'avgpos', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':0},
        'carttotal':{'name':'购物车总数', 'color':'#663399', 'func':None, 'unit':'', 'field_name':'carttotal', 'value_list':[], 'visible':False, 'opposite':False, 'is_axis':0, 'yaxis':4},
        }

    if data_type == 1:
        key_list = ['impr', 'click', 'cpc', 'ctr', 'cost', 'pay', 'paycount', 'favcount', 'roi', 'conv', 'carttotal']
    elif data_type == 2:
        key_list = ['impr', 'click', 'cpc', 'ctr', 'cost', 'pay', 'paycount', 'favcount', 'roi', 'conv']
    elif data_type == 3:
        key_list = ['impr', 'click', 'cpc', 'ctr', 'cost', 'pay', 'paycount', 'favcount', 'roi', 'conv']
    elif data_type == 4:
        key_list = ['impr', 'click', 'cpc', 'ctr', 'cost', 'pay', 'paycount', 'favcount', 'roi', 'avgpos']
    elif data_type == 5:
        key_list = ['cost', 'pay', 'click', 'roi']
    elif data_type == 6:
        key_list = ['impr', 'click', 'cpc', 'ctr', 'cost', 'pay', 'paycount', 'roi', 'conv']
    else:
        key_list = []

    category_list = []
    series_cfg_list = [series_cfg_dict[k] for k in key_list]
    now = datetime_2string(fmt = '%m-%d')
    for rpt in rpt_list:
        item_date = datetime_2string(rpt.date, "%m-%d")
        if item_date == now:
            category_list.append('实时数据')
        else:
            category_list.append(item_date)
        for series_cfg in series_cfg_list:
            value = getattr(rpt, series_cfg['field_name'])
            value = value and series_cfg['func'] and series_cfg['func'](value) or value
            series_cfg['value_list'].append(value)

    for series_cfg in series_cfg_list:
        del series_cfg['func']
    return category_list, series_cfg_list

# 缓存危险类目信息
def load_danger_cats_info():
    cache_key = 'danger_cats'
    danger_cats = CacheAdpter.get(cache_key, 'web')
    if not danger_cats:
        jobj = Cat.get_danger_cat_list()
        danger_cats = json.loads(jobj)
        CacheAdpter.set(cache_key, danger_cats, 'web', 60 * 60 * 24)
    return danger_cats

def get_isneed_phone(user):
    shop_id = user.shop_id
    isneed_phone = CacheAdpter.get(CacheKey.WEB_ISNEED_PHONE % shop_id, 'web', 'no_cache')
    # isneed_phone = 'no_cache'
    if isneed_phone == 'no_cache':
        # 有手机号, 则放入缓存，避免多次访问数据库
#         from apps.crm.models import Customer
#         customer, _ = Customer.objects.get_or_create(shop_id = shop_id,
#                         defaults = {'user':user, 'nick':user.nick, 'tp_status':'untouched', 'jl_use_status':'using'})
        from apps.ncrm.models import Customer
        customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'nick':user.nick})
        if customer.phone:
            isneed_phone = 0
        else:
            isneed_phone = 1
        CacheAdpter.set(CacheKey.WEB_ISNEED_PHONE % shop_id, isneed_phone, 'web', 60 * 60 * 24 * 7)
    return isneed_phone

def get_is_vip(user):
    return 1 - get_isneed_phone(user)

def update_appraise_record(shop_id):
    """更新有用的好评记录的积分状态"""
    # 获取用户点击好评有礼的记录并对比更新
    appraise_list = list(pa_coll.find({'shop_id': shop_id, 'type':'appraise'}).sort("create_time", -1))
    # 取最新一条好评有礼记录
    if appraise_list:
        appraise = appraise_list[0]
        # 如果未解冻，则需判断时间是否在30天之前，若在30天之前，则不解冻
        if appraise['is_freeze']:
            last_create_time = appraise['create_time']
            # 如果在30天内，则需要判断在这段时间内是否有好评开车精灵，有则解冻
            if (last_create_time + datetime.timedelta(days = 30)) > datetime.datetime.today():
                comment_list = AppComment.objects.filter(user_nick = appraise['nick'], service_code = 'ts-25811', gmt_create__gte = appraise['create_time']).order_by('-id')
                if comment_list:
                    pa_coll.update({'_id':appraise['_id']}, {'$set':{'is_freeze':0, 'create_time':comment_list[0].gmt_create}})
                    # 解冻后需要刷新用户积分
                    PointManager.refresh_points_4nick(appraise['nick'])