# coding=UTF-8
import datetime

import collections

from apps.common.constant import Const
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import date_2datetime
from apps.subway.models_account import account_coll
from apps.subway.models_campaign import camp_coll
from apps.subway.models_adgroup import adg_coll
from apps.subway.models_keyword import kw_coll
from apps.subway.models_creative import crt_coll
from apps.subway.models_item import item_coll
from apps.subway.models_report import kwrpt_coll
from apps.mnt.models import mnt_camp_coll
from apps.crm.utils import remame_dictionary_key
from apps.router.models import User
from apps.router.models import ArticleUserSubscribe
from apps.kwslt.models_cat import Cat, CatStatic


def get_adgroup_bycreate(level_key, obj_list, title_num):
    aggr_pipeline = []
    aggr_pipeline.append(
                                        {
                                         '$match':{
                                                level_key:{
                                                                        '$in':obj_list
                                                                  }
                                                }

                                         }
                                    )
    aggr_pipeline.append(
                                        {
                                            '$group':{
                                                          '_id':{'adgroup_id':'$adgroup_id'},
                                                          'create_count' : { '$sum': 1 },
                                                      }
                                        }
                                    )
    aggr_pipeline.append(
                                        {
                                            '$match':{
                                                            'create_count' :title_num
                                                      }
                                        }
                                    )
    aggr_pipeline.append(
                                        {
                                            '$project':{
                                                            '_id':0,
                                                            'adg_id':'$_id.adgroup_id',
                                                      }
                                        }
                                    )
    result = crt_coll.aggregate(aggr_pipeline)
#     from pprint import pprint
#     pprint(aggr_pipeline)
    return [ ctr['adg_id']  for ctr in result['result'] if ctr.has_key('adg_id')]

def get_kw_count(adg_id_list, shop_id_list = ()):
    aggr_pipeline = []
    if shop_id_list:
        aggr_pipeline.append(
                                            {
                                             '$match':{
                                                        'shop_id':{
                                                                            '$in':shop_id_list
                                                                      }
                                                    }

                                             }
                                    )
    aggr_pipeline.append(
                                        {
                                         '$match':{
                                                    'adgroup_id':{
                                                                        '$in':adg_id_list
                                                                  }
                                                }

                                         }
                                    )
    aggr_pipeline.append(
                                        {
                                            '$group':{
                                                          '_id':{'adgroup_id':'$adgroup_id'},
                                                          'kw_count' : { '$sum': 1 },
                                                      }
                                        }
                                    )
    aggr_pipeline.append(
                                        {
                                            '$project':{
                                                            '_id':0,
                                                            'adg_id':'$_id.adgroup_id',
                                                            'kw_count' :'$kw_count'
                                                      }
                                        }
                                    )
    result = kw_coll.aggregate(aggr_pipeline)
    adg_dict = {}
    if result.has_key('result'):
        result_list = result['result']
        for result in result_list:
            adg_dict.update({int(result['adg_id']):int(result['kw_count'])})
    else:
        pass
    return adg_dict

def reset_client_data(filter_type, aggr_result_list, aggr_coll_list, is_rpt):
    """得到返回数据的数据结构"""
    def get_new_result_list(aggr_result_list, primary_key, cond_tuple, aggr_coll, date_key_list = [u'start_date', u'end_date'], count_days_dict = {}, replace_dict = {}, is_udpate_date = True):
        obj_id_list = []
        temp_dict = {}
        result_list = []
        for aggr_result in aggr_result_list:
            if is_udpate_date:
                for date_key in date_key_list:
                    if aggr_result.has_key(date_key):
                        try:
                            date_time = aggr_result.pop(date_key)
                            aggr_result.update({date_key:date_time.strftime('%Y-%m-%d')})
                        except Exception, e:
                            pass

            if aggr_result.has_key(primary_key):
                temp_key = str(aggr_result[primary_key])
                if temp_dict.has_key(temp_key):
                    temp_dict[temp_key].append(aggr_result)
                else:
                    temp_dict[temp_key] = [aggr_result]
                    obj_id_list.append(int(aggr_result[primary_key]))

        cond_tuple[0].update({'_id':{'$in':obj_id_list}})
        obj_cursor = aggr_coll.find(cond_tuple[0], cond_tuple[1])
        for obj in obj_cursor:
            if obj.has_key('_id') and str(obj['_id']) in temp_dict:
                key = str(obj.pop('_id'))
                aggr_list = temp_dict[key]
                if count_days_dict:
                    for count_days_field, alse_name in count_days_dict.items():
                        if obj.has_key(count_days_field):
                            time_date = obj.pop(count_days_field)
                            if time_date:
                                try:
                                    days = (datetime.datetime.today().date() - time_date.date()).days
                                    obj.update({alse_name:days})
                                except Exception, e:
                                    log.error('statistics adgroup days error, e = %s' % e)
                                    obj.update({alse_name:None})
                for aggr in aggr_list:
                    aggr.update(obj)
                    result_list.append(remame_dictionary_key(aggr, replace_dict))
        return result_list

    def get_account_data(aggr_result_list, aggr_coll_list):
#         from apps.crm.models import Customer
        from apps.ncrm.models import Customer
        from apps.router.models import User

        cond_tuple = ({'_id':{'$in':[]}}, {'cat_id':1, 'balance':1, 'msg_status':1})
        result_list = get_new_result_list(aggr_result_list, 'shop_id', cond_tuple, aggr_coll_list[-1])
        shop_id_list = [r['shop_id'] for r in result_list]
        # 获取用户session信息
        shop_id_str_list = map(str, shop_id_list)
        user_cursor = User.objects.only('session', 'shop_id', 'nick').filter(shop_id__in = shop_id_str_list)

        nick_set = set()
        user_session_dict = {}
        for user in user_cursor:
            user_session_dict.update({int(user.shop_id) : (user.session , user.nick) })
            nick_set.add(user.nick)
        nick_list = list(nick_set)

        customer_list = Customer.objects.filter(shop_id__in = shop_id_list, phone__isnull = False)\
                                    .exclude(phone = '').only('shop_id', 'phone')
        phone_dict = {c.shop_id:c.phone for c in customer_list}

        sub_cursor = ArticleUserSubscribe.objects.filter(nick__in = nick_list, article_code = 'ts-25811')\
                                .order_by('-deadline')
        sub_dict = {}
        for sub in sub_cursor:
            if sub.nick not in sub_dict:
                sub_dict[sub.nick] = sub.deadline.strftime('%Y-%m-%d')

#         # 临时数据
#         rjjh_set = set([ rjjh.shop_id for rjjh in RJJHServer.objects\
#                             .filter(shop_id__in = shop_id_list)])

        cat_id_dict = {}
        for result in result_list:
            temp_cat_id = result['cat_id']
            if temp_cat_id in cat_id_dict:
                result[u'cat_name'] = cat_id_dict[temp_cat_id]
            else:
                try:
                    cat_id_dict[temp_cat_id] = Cat.get_cat_path(cat_id_list = [temp_cat_id], last_name = ' ').get(str(temp_cat_id), ['未获取到值', ''])[0]
                    result[u'cat_name'] = cat_id_dict[temp_cat_id]
                except Exception, e:
                    log.error("get category id error, ,cat_id = %s, e=%s" % (temp_cat_id, e))
                    result[u'cat_name'] = '未获取到值'
            if phone_dict.has_key(result['shop_id']):
                result['phone'] = phone_dict[result['shop_id']]
            if user_session_dict.has_key(result['shop_id']):
                result['session'] = user_session_dict[result['shop_id']][0]
                result['nick'] = user_session_dict[result['shop_id']][1]
                if result['nick'] in sub_dict:
                    result['dealline'] = sub_dict[result['nick']]
#                 if result['shop_id'] in rjjh_set:
#                     result['note_info'] = 0
        return result_list

    def get_campaign_data(aggr_result_list, aggr_coll_list):
        cond_tuple = ({'_id':{'$in':[]} }, {'title':1, 'budget':1, 'online_status':1, 'shop_id':1, 'msg_status':1})

        replace_dict = {}
        if not is_rpt:
            cond_tuple[1].update({'shop_id':1, 'adgroup_id':1, 'campaign_id':1})
            replace_dict = {'shop_id':'shop_id'}
        result_list = get_new_result_list(aggr_result_list, 'camp_id', cond_tuple, aggr_coll_list[-1], replace_dict = replace_dict)

        shop_id_list = [camp['shop_id'] for camp in aggr_result_list]
        mnt_camps = mnt_camp_coll.find({'shop_id':{'$in':shop_id_list}}, {'_id':1, 'mnt_type':1, 'opar_status':1, 'start_time':1})
        mnt_dict = {camp['_id']:camp for camp in mnt_camps}
        today_time = datetime.datetime.now()
        for camp in result_list:
            if mnt_dict.has_key(camp['camp_id']):
                camp[u'mnt_type'] = mnt_dict[camp['camp_id']].get('mnt_type', 0)
                camp[u'opar_status'] = mnt_dict[camp['camp_id']].get('opar_status', 0)
                camp[u'exec_days'] = 0
                if mnt_dict[camp['camp_id']].has_key('start_time'):
                    camp[u'exec_days'] = (today_time - mnt_dict[camp['camp_id']]['start_time']).days
        return result_list

    def get_adgorup_data(aggr_result_list, aggr_coll_list):
        cond_tuple = ({'_id':{'$in':[]} }, {'item_id':1, 'online_status':1, 'modify_time':1, 'mnt_time':1, 'create_time':1, 'is_focus':1, 'mnt_type':1, 'limit_price':1, 'msg_status':1, 'category_ids':1})

        replace_dict = {}
        if not is_rpt:
            cond_tuple[1].update({'shop_id':1, 'adgroup_id':1, 'campaign_id':1})
            replace_dict = {'shop_id':'shop_id', 'campaign_id':'camp_id'}

        aggr_result_list = get_new_result_list(aggr_result_list, 'adg_id', cond_tuple, aggr_coll_list[-1], count_days_dict = {u'create_time':u'create_days', 'mnt_time':'mnt_days'}, replace_dict = replace_dict)
        item_cond_tuple = ({'_id':{'$in':[]} }, {'title':1, 'price':1, 'pic_url':1, 'title_optimize_time':1})
        result_list = get_new_result_list(aggr_result_list, 'item_id', item_cond_tuple, item_coll, is_udpate_date = False)

#         adg_id_list = [ int(adg['adg_id']) for adg in result_list ]
#         adg_dict = get_kw_count(adg_id_list)
        adg_cat_dict = {}
        cat_id_list = []
        for result in result_list:
            adg_id = int(result['adg_id'])
#             if adg_dict.has_key(adg_id):
#                 result.update({'kw_count':adg_dict[adg_id]})
            cat_list = result.get('category_ids', '').split()
            if cat_list:
                adg_cat_dict[str(adg_id)] = cat_list
                cat_id_list.extend(map(int, cat_list))
                result.pop('category_ids')
            else:
                log.info('the adgroup not existed field of category_ids, adgroup_id = %s' % (adg_id))
        try:
            cat_id_list = list(set(cat_id_list))
            cat_list_info = CatStatic.get_market_data(cat_id_list = cat_id_list)
            for result in result_list:
                adg_id = str(result['adg_id'])
                cat_list = adg_cat_dict.get(adg_id, [])
                adg_cpc = 0
                for index in xrange(len(cat_list) - 1, -1, -1):
                    cat_id = int(cat_list[index])
                    temp_cpc = cat_list_info.get(cat_id, {}).get('cpc', 0)
                    if temp_cpc:
                        adg_cpc = round(temp_cpc * 0.01, 2)
                        break
                result.update({'adg_cpc':adg_cpc})
        except Exception, e:
            log.info('get cat cpc error, e=%s' % e)
        return result_list

    def get_keyword_data(aggr_result_list, aggr_coll_list):
        cond_tuple = ({'_id':{'$in':[]}}, {'max_price':1, 'word':1, 'qscore':1, 'create_time':1, 'match_scope':1, 'is_freeze':1, \
                                            'g_pv':1, 'g_click':1, 'g_cpc':1, 'g_competition':1, 'g_sync_time':1})

        replace_dict = {}
        if not is_rpt:
            cond_tuple[1].update({'shop_id':1, 'adgroup_id':1, 'campaign_id':1})
            replace_dict = {'shop_id':'shop_id', 'campaign_id':'camp_id', 'adgroup_id':'adg_id'}

        result_list = get_new_result_list(aggr_result_list, 'kw_id', cond_tuple, aggr_coll_list[-1], count_days_dict = {u'create_time':u'create_days'}, replace_dict = replace_dict)

        if is_rpt:
            # 获取昨日平均排名
            avgpos_dict = {}
            kw_id_list = [kw['kw_id'] for kw in result_list]
#             kw_cur = kw_coll.find({'_id':{'$in':kw_id_list}}, {'rpt_list':{'$slice':-1}, 'avgpos':1, 'date':1})
#             yesterday = datetime.date.today() - datetime.timedelta(days = 1)
#             for kw in kw_cur:
#                 if kw['rpt_list'] and kw['rpt_list'][0]['date'].date() == yesterday:
#                     avgpos_dict[kw['_id']] = kw['rpt_list'][0]['avgpos']
#                 else:
#                     avgpos_dict[kw['_id']] = 0

            yesterday = datetime.datetime.today() - datetime.timedelta(days = 1)
            before_yesterday = (yesterday - datetime.timedelta(days = 1))
            kw_cur = kwrpt_coll.find({'keyword_id':{'$in':kw_id_list}, 'date':{"$gt" : before_yesterday}})
            avgpos_dict = collections.defaultdict(int)
            for kw in kw_cur:
                if kw['date'].date() == yesterday.date():
                    avgpos_dict[kw['keyword_id']] = kw['avgpos']

            # 更新全网数据的关键词
            from apps.common.biz_utils.utils_tapitools import get_kw_g_data
            word_gpccp_dict = get_kw_g_data([result['word'] for result in result_list])
            # word_gpccp_dict = Keyword.get_and_save_gdata(result_list)
            for result in result_list:
                result.update({'avgpos':avgpos_dict[result['kw_id']]})
                temp_word = str(result['word'].lower())
                if word_gpccp_dict.has_key(temp_word):
                    g_data = word_gpccp_dict[temp_word]
                    g_data_dict = {'g_pv': g_data.g_pv, 'g_click':g_data.g_click, 'g_cpc':g_data.g_cpc,
                                   'g_competition':g_data.g_competition}
                    result.update(g_data_dict)

        return result_list

    def get_default_data(aggr_result_list, aggr_coll_list):
        return []

    if aggr_result_list:
        try:
            return_obj_dict = {
                                    'account':get_account_data,
                                    'campaign':get_campaign_data,
                                    'adgroup':get_adgorup_data,
                                    'keyword':get_keyword_data,
                                }
        except Exception, e:
            log.exception('get show data error, ' % (e))
        else:
            return return_obj_dict.get(filter_type, get_default_data)(aggr_result_list, aggr_coll_list)
    return []

def filtrate_specific_condition(filter_type, obj_list, sepecific_condition_dict, last_key):
    """通过特定的条件进行obj_id过滤"""
    def check_valid_condition(value):
        if type(value) == list or type(value) == tuple:
            count = 0
            for temp in value:
                if temp == '-1' or temp == -1:
                    count += 1
            if len(value) == count:
                return False
            return True
        elif value == '-1' or value == -1:
            return False
        return True

    def account_specific_filter(level_key, obj_list, sepecific_condition_dict):
        acc_filter_dict = {}
        new_obj_list = obj_list

        single_id = 0
        nick_list = []
        is_nick = False

        for cond_name, cond_value in sepecific_condition_dict.items():
            if check_valid_condition(cond_value):
                if cond_name == 'id' and cond_value :
                    single_id = int(cond_value)
                elif cond_name == 'opar_status'  :
                    acc_filter_dict.update({'opar_status':int(cond_value)})
                elif cond_name == 'nick' and cond_value:
                    user_cursor = User.objects.only("shop_id").filter(nick__contains = cond_value, perms_code__contains = "A")
                    nick_list = [int(user.shop_id) for user in user_cursor]
                    is_nick = True
                elif cond_name == 'is_dl' :
                    # TODO: yangrongkai 为了保证以后操作便捷，此处要重新设计
                    yestoday = date_2datetime(datetime.date.today() - datetime.timedelta(days = 1))
                    new_obj_list = obj_list[:]
                    account_cursor = account_coll.find({'_id':{'$in':obj_list}, 'date':yestoday}, {'_id':1})
                    dl_shop_list = []
                    if account_cursor:
                        dl_shop_list = [acc['_id'] for acc in account_cursor]
                    if int(cond_value) == 1:
                        new_obj_list = list(set(new_obj_list) & set(dl_shop_list))
                    elif int(cond_value) == 0:
                        new_obj_list = list(set(new_obj_list) - set(dl_shop_list))
                elif cond_name == 'is_gsw' :
                    mnt_shop_list = [mnt_camp['shop_id'] for mnt_camp in mnt_camp_coll.find({'mnt_type':1}, {'shop_id':1})]
                    if int(cond_value) == 1:
                        new_obj_list = list(set(new_obj_list) & set(mnt_shop_list))
                    elif int(cond_value) == 0:
                        new_obj_list = list(set(new_obj_list) - set(mnt_shop_list))
                elif cond_name == 'is_rjjh' :
                    mnt_shop_list = [mnt_camp['shop_id'] for mnt_camp in mnt_camp_coll.find({'mnt_type':2}, {'shop_id':1})]
                    if int(cond_value) == 1:
                        new_obj_list = list(set(new_obj_list) & set(mnt_shop_list))
                    elif int(cond_value) == 0:
                        new_obj_list = list(set(new_obj_list) - set(mnt_shop_list))
                elif cond_name == 'balance' and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({Const.CRM_LIMIT_FIELDS[index]:int(value)})
                    acc_filter_dict.update({'balance':sub_filter_dict})
#                 elif cond_name == 'attention_status':
#                     acc_filter_dict.update({'note_list.attention_status':str(cond_value)})
#                 elif cond_name == 'comment_status':
#                     acc_filter_dict.update({'note_list.comment_status':str(cond_value)})
#                 elif cond_name == 'refund_status':
#                     acc_filter_dict.update({'note_list.refund_status':str(cond_value)})
#                 elif cond_name == 'relation_status':
#                     acc_filter_dict.update({'note_list.relation_status':str(cond_value)})
#                 elif cond_name == 'introduce_status':
#                     acc_filter_dict.update({'note_list.introduce_status':str(cond_value)})
#                 elif cond_name == 'ban_status':
#                     acc_filter_dict.update({'note_list.ban_status':str(cond_value)})
#                 elif cond_name == 'dangerous_status':
#                     acc_filter_dict.update({'note_list.dangerous_status':str(cond_value)})
#                 elif cond_name == 'revisit_count':
#                     sub_filter_dict = {}
#                     for index, value in enumerate(cond_value):
#                         if value == '-1' or value == -1:
#                             continue
#                         else:
#                             sub_filter_dict.update({Const.CRM_LIMIT_FIELDS[index]:int(value)})
#                     acc_filter_dict.update({'revisit_count':sub_filter_dict})

        if single_id :
            if single_id in new_obj_list:
                acc_filter_dict.update({'_id':single_id})
            else:
                return []

            if is_nick:
                if nick_list:
                    if single_id not in nick_list:
                        return []
                else:
                    return []

        else:
            if is_nick:
                if nick_list:
                    new_obj_list = list(set(nick_list) & set(new_obj_list))
                else:
                    return []

            if not new_obj_list:
                return []

            acc_filter_dict.update({level_key:{'$in':new_obj_list}})

        if acc_filter_dict :
            account_cursor = account_coll.find(acc_filter_dict, {'_id':1}).max_scan(Const.CRM_MAX_RESULT_COUNT + 1)
            new_obj_list = [int(acc_cursor['_id']) for acc_cursor in account_cursor]
        return new_obj_list

    def campaign_specific_filter(level_key, obj_list, sepecific_condition_dict):
        init_filter_dict = {level_key:{'$in':obj_list}}
        camp_filter_dict = init_filter_dict.copy()
        mnt_filter_dict = {}
        rm_condition_dict = {}
        new_obj_list = []

        for cond_name, cond_value in sepecific_condition_dict.items():
            if check_valid_condition(cond_value):
                if cond_name == 'online_status'  :
                    online_status = 'online'
                    settle_status = 'online'
                    if int(cond_value) == 0:
                        camp_filter_dict.update({'$or':[{'online_status':{'$ne':online_status}}, {'settle_status':{'$ne':settle_status}}]})
                    else:
                        camp_filter_dict.update({'online_status':online_status, 'settle_status':settle_status})
                elif cond_name == 'budget_status'  :
                    camp_filter_dict.update({'budget_status':str(cond_value)})
                elif cond_name == 'opar_status'  :
                    camp_filter_dict.update({'opar_status':int(cond_value)})
                elif cond_name == 'opar_type'  :
                    extra_dict = {}
                    if int(cond_value) == 1:
                        extra_dict.update({'opar_status':1})
                    elif int(cond_value) == 0:
                        extra_dict.update({'opar_status':{'$in':[None, 0]}})
                    mnt_filter_dict.update(extra_dict)
                elif cond_name == 'mnt_type' :
                    if int(cond_value) == 0:
                        rm_condition_dict.update({'mnt_type':{'$nin':[0, None]}})
                    elif int(cond_value) == 1:
                        mnt_filter_dict.update({'mnt_type':1})
                    elif int(cond_value) == 2:
                        mnt_filter_dict.update({'mnt_type':2})
                    elif int(cond_value) == 3:
                        mnt_filter_dict.update({'mnt_type':3})
                    elif int(cond_value) == 4:
                        mnt_filter_dict.update({'mnt_type':4})
                    elif int(cond_value) == 5:
                        mnt_filter_dict.update({'mnt_type':{'$in':[1, 2, 3, 4]}})
                elif cond_name == 'mnt_status' :
                    mnt_filter_dict.update({'mnt_status':int(cond_value) })
                elif cond_name == 'budget' and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({Const.CRM_LIMIT_FIELDS[index]:int(value)})
                    camp_filter_dict.update({'budget':sub_filter_dict})
                elif cond_name == 'exec_days'  and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    crm_limit_fields = Const.CRM_LIMIT_FIELDS[:]
                    crm_limit_fields.reverse()
                    today = date_2datetime(datetime.datetime.now())
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({crm_limit_fields[-index]:(today - datetime.timedelta(days = int(value)))})
                    mnt_filter_dict.update({'start_time':sub_filter_dict})

        if camp_filter_dict:
            camp_cursor = camp_coll.find(camp_filter_dict, {'_id':1}).max_scan(Const.CRM_MAX_RESULT_COUNT + 1)
            if camp_cursor:
                new_obj_list = [ camp['_id'] for camp in camp_cursor ]

        if mnt_filter_dict and new_obj_list:
            mnt_set = set()
            mnt_filter_dict.update(init_filter_dict.copy())
            camp_cursor = mnt_camp_coll.find(mnt_filter_dict, {'_id':1}).max_scan(Const.CRM_MAX_RESULT_COUNT + 1)
            if camp_cursor :
                mnt_set = set(int(camp['_id']) for camp in camp_cursor)
            if not mnt_set:
                return []
            elif mnt_set and new_obj_list:
                new_obj_list = list(mnt_set & set(new_obj_list))

        if rm_condition_dict and new_obj_list :
            mnt_set = set()
            rm_condition_dict.update(init_filter_dict.copy())
            camp_cursor = mnt_camp_coll.find(rm_condition_dict, {'_id':1}).max_scan(Const.CRM_MAX_RESULT_COUNT + 1)
            if camp_cursor :
                mnt_set = set(int(camp['_id']) for camp in camp_cursor)
            if mnt_set and new_obj_list :
                new_obj_list = list(set(new_obj_list) - mnt_set)

        return new_obj_list

    def adgroup_specific_filter(level_key, obj_list, sepecific_condition_dict):
        adg_filter_dict = {level_key:{'$in':obj_list}}
        create_check = False
        valid_create_adgroups = []
        for cond_name, cond_value in sepecific_condition_dict.items():
            if check_valid_condition(cond_value):
                if cond_name == 'online_status'  :
                    online_status = 'online'
                    offline_type = 'online'
                    if int(cond_value) == 0:
                        adg_filter_dict.update({'$or':[{'online_status':{'$ne':'online'}}, {'offline_type':{'$ne':'online'}}]})
                    else:
                        adg_filter_dict.update({'online_status':online_status, 'offline_type':offline_type})
                elif cond_name == 'mnt_type' :
                    if int(cond_value) == 0:
                        adg_filter_dict.update({'$or':[{'mnt_type':int(cond_value)}, {'mnt_type':None}]})
                    elif int(cond_value) in [1, 2, 3, 4]:
                        adg_filter_dict.update({'mnt_type':int(cond_value)})
                    elif int(cond_value) == 9:
                        adg_filter_dict.update({'mnt_type':{'$in':[1, 2, 3, 4]}})
                elif cond_name == 'create_days' and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    crm_limit_fields = Const.CRM_LIMIT_FIELDS[:]
                    crm_limit_fields.reverse()
                    today_time = datetime.datetime.now()
                    today = datetime.datetime(today_time.year, today_time.month, today_time.day)
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({crm_limit_fields[-index]:(today - datetime.timedelta(days = int(value)))})
                    adg_filter_dict.update({'create_time':sub_filter_dict})
                elif cond_name == 'mnt_time' and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    crm_limit_fields = Const.CRM_LIMIT_FIELDS[:]
                    crm_limit_fields.reverse()
                    today_time = datetime.datetime.now()
                    today = datetime.datetime(today_time.year, today_time.month, today_time.day)
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({crm_limit_fields[-index]:(today - datetime.timedelta(days = int(value)))})
                    adg_filter_dict.update({'mnt_time':sub_filter_dict})
                elif cond_name == 'limit_price' and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    crm_limit_fields = Const.CRM_LIMIT_FIELDS[:]
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({crm_limit_fields[-index]:value})
                    adg_filter_dict.update({'limit_price':sub_filter_dict})
                elif cond_name == 'opar_status'  :
                    adg_filter_dict.update({'opar_status':int(cond_value)})
                elif cond_name == 'is_dl':
                    today = datetime.datetime.now().date()
                    if int(cond_value) == 1:
                        adg_filter_dict.update({'kwrpt_sync_time':{'$gte':datetime.datetime(today.year, today.month, today.day)}})
                    else:
                        adg_filter_dict.update({'$or':[{'kwrpt_sync_time':{'$lt':datetime.datetime(today.year, today.month, today.day)}}, {'kwrpt_sync_time':None}]})
                elif cond_name == 'cat_id' and cond_value:
                    adg_filter_dict.update({'category_ids':{'$regex':r'(.*\s%s\s.*|.*\s%s$|^%s\s.*)' % (cond_value, cond_value, cond_value) }})
                elif cond_name == 'title_num' and cond_value:
                    create_check = True
                    valid_create_adgroups = get_adgroup_bycreate(level_key, obj_list, int(cond_value))

        new_obj_list = []
        if create_check:
            valid_adgroups = adg_filter_dict.pop("_id", {}).pop('$in', [])
            if valid_adgroups:
                adg_filter_dict.update({"_id":{"$in":list(set(valid_create_adgroups) & set(valid_adgroups))}})
            else:
                adg_filter_dict.update({"_id":{"$in":valid_create_adgroups}})

        if adg_filter_dict:
            adg_cursor = adg_coll.find(adg_filter_dict, {'_id':1}).max_scan(Const.CRM_MAX_RESULT_COUNT + 1)
            for adg in adg_cursor:
                new_obj_list.append(int(adg['_id']))
        return new_obj_list

    def keyword_specific_filter(level_key, obj_list, sepecific_condition_dict):
        kw_filter_dict = {level_key:{'$in':obj_list}}
        for cond_name, cond_value in sepecific_condition_dict.items():
            if check_valid_condition(cond_value):
                if cond_name == 'is_focus'  :
                    if int(cond_value) == 1:
                        kw_filter_dict.update({'is_focus':True})
                elif cond_name == 'is_garbage' :
                    is_garbage = False
                    if int(cond_value) == 1:
                        is_garbage = True
                    kw_filter_dict.update({'is_garbage':is_garbage})
                elif cond_name == 'is_modify' :
                    today_time = datetime.datetime.now()
                    today = datetime.datetime(today_time.year, today_time.month, today_time.day)
                    if int(cond_value) == 1:
                        kw_filter_dict.update({'modify_time':{'$gte':today}})
                    else:
                        kw_filter_dict.update({'modify_time':{'$lt':today}})
                elif cond_name == 'is_freeze':
                    if int(cond_value) == 1:
                        kw_filter_dict.update({'is_freeze':True})
                    else:
                        kw_filter_dict.update({'is_freeze':{'$in':[False, None]}})
                elif cond_name == 'contain' :
                    kw_filter_dict.update({'word':{'$regex':str(cond_value)}})
                elif cond_name == 'is_dl':
                    today = datetime.datetime.now().date()
                    if int(cond_value) == 1:
                        sub_find_dict = {'kwrpt_sync_time':{'$gte':datetime.datetime(today.year, today.month, today.day)}}
                    else:
                        sub_find_dict = {'kwrpt_sync_time':{'$lt':datetime.datetime(today.year, today.month, today.day)}}

                    if level_key == 'adgroup_id':
                        sub_find_dict.update({'_id':{'$in':obj_list}})
                    else:
                        sub_find_dict.update({level_key:{'$in':obj_list}})

                    adg_cursor = adg_coll.find(sub_find_dict, {'_id':1})
                    adg_list = [ int(adg['_id']) for adg in adg_cursor]
                    kw_filter_dict.update({'adgroup_id':{'$in':adg_list}})
                elif cond_name == 'create_days' and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    crm_limit_fields = Const.CRM_LIMIT_FIELDS[:]
                    crm_limit_fields.reverse()
                    today_time = datetime.datetime.now()
                    today = datetime.datetime(today_time.year, today_time.month, today_time.day)
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({crm_limit_fields[-index]:(today - datetime.timedelta(days = int(value)))})
                    kw_filter_dict.update({'create_time':sub_filter_dict})
                elif cond_name == 'qscore' and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({Const.CRM_LIMIT_FIELDS[index]:int(value)})
                    kw_filter_dict.update({'qscore':sub_filter_dict})
                elif cond_name == 'is_default_price' :
                    is_default_price = False
                    if int(cond_value) == 1:
                        is_default_price = True
                    kw_filter_dict.update({'is_default_price':is_default_price})
                elif cond_name == 'match_scope'  :
                    kw_filter_dict.update({'match_scope':int(cond_value)})
                elif cond_name == 'max_price' and cond_value and len(cond_value) == 2:
                    sub_filter_dict = {}
                    for index, value in enumerate(cond_value):
                        if value == '-1' or value == -1:
                            continue
                        else:
                            sub_filter_dict.update({Const.CRM_LIMIT_FIELDS[index]:int(value)})
                    kw_filter_dict.update({'max_price':sub_filter_dict})

        new_obj_list = []
        if kw_filter_dict:
            kw_cursor = kw_coll.find(kw_filter_dict, {'_id':1}).max_scan(Const.CRM_MAX_RESULT_COUNT + 1)
            for kw in kw_cursor:
                new_obj_list.append(int(kw['_id']))
        return new_obj_list

    def default_specific_filter(level_key, obj_list, sepecific_condition_dict):
        raise Exception('specific filter is error')
        return []

    result_list = []
    if obj_list:
        filter_obj_dict = {
                                'account':lambda:account_specific_filter(last_key, obj_list, sepecific_condition_dict),
                                'campaign':lambda:campaign_specific_filter(last_key, obj_list, sepecific_condition_dict),
                                'adgroup':lambda:adgroup_specific_filter(last_key, obj_list, sepecific_condition_dict),
                                'keyword':lambda:keyword_specific_filter(last_key, obj_list, sepecific_condition_dict),
                            }
        start_time = datetime.datetime.now()
        result_list = filter_obj_dict.get(filter_type, default_specific_filter)()
        log.info('oparete obj=%s , rest numb=%s , exce time=%s' % (filter_type, len(result_list), datetime.datetime.now() - start_time))
    return result_list

def filter_dimension(filter_type_index, match_rule, parameter_dict, obj_coll, days = 1, group_key = '', specific_dict = {}):
    """
    / 过滤聚合操作公共方法抽出
    / 用途：通过对象ID集合，过滤条件及天数三维对进行对数据过滤，聚合，产生报表
    / 参数：
    /        match_rule : 匹配条件，应符合mongoDB查询语法的字典
    /        parameter_dict : 过滤条件，如下：（-1 代表不限制, tuple[0]代表最低，tuple[1]代表最高）
    /                         {
    /                                'impressions':(1000, 2000000),
    /                                'click':(-1, -1),
    /                                'cost':(-1, 2000000),
    /                                'pay':(1000, '-1),
    /                          }
    /                    暂定过滤条件如下 ['impressions', 'click', 'cost', 'ctr', 'pay', 'paycount', 'favcount', 'conv', 'roi']
    /                    此条件可依据返回结果进行适当的增加，删除。
    /        obj_coll: 执行操作的pymongo数据库连接（如：adg_coll)
    /        days: 需要聚合数据天数
    / 可返回结果：
    /        对象基本信息（如：adgroup即返回 account_id , campaign_id,adgroup_id)
    /        基础聚合数据 （ 'impressions', 'click', 'cost', ‘aclick’）
    /        效果聚合数据 （ 'directpay', 'indirectpay', 'directpaycount', 'indirectpaycount', 'favitemcount', 'favshopcount'）
    /        计算聚合数据 （ 'pay', 'paycount', 'favcount', 'roi', 'conv', 'ctr', 'cpc', 'fav_roi', 'profit'）
    """
    def get_filter_dimension(parameter_dict, filter_type_index):
        """获取公共过滤维度"""
        # 传入参数：
        #             {
        #                     'impressions':(1000, 2000000),
        #                     'click':(-1, -1),
        #                     'cost':(-1, 2000000),
        #                     'pay':(1000, '-1),
        #               }
        # 返回结果
        #             {
        #                    '$match':{
        #                                     # 基础过滤
        #                                     'impressions':{'$gte':1000, '$lte':2000000},
        #                                     'click':{'$gte':10, '$lte':1000000},
        #                                     'cost':{'$gte':1, '$lte':20000000},
        #                                     'ctr':{'$gte':0.002, '$lte':1},
        #                                     # 转化过滤
        #                                     'pay':{'$gte':0, '$lte':2000000},
        #                                     'paycount':{'$gte':0, '$lte':20000000},
        #                                     'favcount':{'$gte':0, '$lte':20000000},
        #                                     'conv':{'$gte':0, '$lte':1},
        #                                     'roi':{'$gte':1, '$lte':100},
        #                              }
        #                  }
        match_condition_dict = {}
        iter_list = [temp[1] for temp in Const.CRM_FILTER_REPORT_FIELDS[filter_type_index]]
        for field in iter_list:
            if parameter_dict.has_key(field) and parameter_dict[field]:
                temp_dict = {}
                for index, limit_field in enumerate(Const.CRM_LIMIT_FIELDS):
                    if parameter_dict[field][index] != -1:
                        temp_dict[limit_field] = parameter_dict[field][index]
                if temp_dict:
                    match_condition_dict[field] = temp_dict

        return match_condition_dict

    def get_match_byobj(obj_coll, obj_list_name, match_rule, specific_dict):
        """获取管道查询所需要的参数"""

        result_field_dict = {
                                        '_id':0,
                                    }
        result_field_dict.update({
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
                                                })

        if group_key:
            group_condition_dict = {
                                                    '_id':{group_key:'$%s' % (group_key)},
                                                    obj_list_name:{'$addToSet':'$%s' % (obj_list_name)},
                                                }
            result_field_dict.update(
                                                    {
                                                        group_key:'$_id.%s' % group_key,
                                                        obj_list_name:'$%s' % (obj_list_name),
                                                    }
                                                )
        else:
            base_table_list = [
                                                ('account_report', {'shop_id':'$shop_id'}, {'shop_id':'$shop_id'}, {'shop_id':'$_id.shop_id'}),
                                                ('campaign_report', {'campaign_id':'$campaign_id'}, {'campaign_id':'$campaign_id'}, {'camp_id':'$_id.campaign_id'}),
                                                ('adgroup_report', {'adgroup_id':'$adgroup_id'}, {'adgroup_id':'$adgroup_id'}, {'adg_id':'$_id.adgroup_id'}),
                                           ]
            special_table_list = [
                                                ('keyword_report', {'keyword_id':'$_id'}, {'keyword_id':'$keyword_id'}, {'kw_id':'$_id.keyword_id'}),
                                                ('creative_report', {'creative_id':'$_id'}, {'creative_id':'$creative_id'}, {'cre_id':'$_id.creative_id'}),
                                            ]

            is_ok = False
            group_primarykey_dict = {}
            for table_name, update_key_dict, update_main_dict, update_resultfield_dict in base_table_list:
                result_field_dict.update(update_resultfield_dict)
                if obj_coll.name == table_name:
                    specific_key = table_name.split('_')[0]
                    if specific_dict.has_key(specific_key):
                        obj_coll, match_key, cond_dict = specific_dict[specific_key]
                        replace_dict = {'_id':match_key}
                        match_rule = remame_dictionary_key(match_rule, replace_dict)
                        match_rule.update(cond_dict)
                        update_main_dict.update({match_key:'$%s' % match_key})
                        group_primarykey_dict.update(update_main_dict)
                    else:
                        group_primarykey_dict.update(update_main_dict)
                    is_ok = True
                    break
                group_primarykey_dict.update(update_key_dict)

            if not is_ok:
                for table_name, update_key_dict, update_main_dict, update_resultfield_dict in special_table_list:
                    if obj_coll.name == table_name:
                        group_primarykey_dict.update(update_main_dict)
                        result_field_dict.update(update_resultfield_dict)

            group_condition_dict = {
                                                        '_id':group_primarykey_dict,
                                                        'total_days':{'$sum':1},
                                                        'start_date':{'$min':'$date'},
                                                        'end_date':{'$max':'date'},
                                                  }
            result_field_dict.update(
                                                    {
                                                        'total_days':'$total_days',
                                                        'start_date':'$start_date',
                                                        'end_date':'$end_date',
                                                     }
                                                )

        group_condition_dict.update(
                                                        {
                                                            # 基础数据
                                                            'total_impressions':{'$sum':'$impressions'},
                                                            'total_click':{'$sum':'$click'},
                                                            'total_cost':{'$sum':'$cost'},
                                                            'total_aclick':{'$sum':'$aclick'},
                                                            # 效果数据
                                                            'total_directpay':{'$sum':'$directpay'},
                                                            'total_indirectpay':{'$sum':'$indirectpay'},
                                                            'total_directpaycount':{'$sum':'$directpaycount'},
                                                            'total_indirectpaycount':{'$sum':'$indirectpaycount'},
                                                            'total_favitemcount':{'$sum':'$favitemcount'},
                                                            'total_favshopcount':{'$sum':'$favshopcount'},
                                                         }
                                                    )
        return  group_condition_dict, result_field_dict, match_rule, obj_coll

    obj_list_name = ''
#     if obj_coll.name == 'statistics_campaign':
#         obj_list_name = 'camp_list'
#     elif obj_coll.name == 'statistics_shop':
#         obj_list_name = 'shop_list'

    group_condition_dict, result_field_dict, match_rule, obj_coll = get_match_byobj(obj_coll, obj_list_name, match_rule, specific_dict)
    filter_dict = get_filter_dimension(parameter_dict, filter_type_index)

    # TODO: 此处需要重构 yangrongkai
    # ===================================================================
    adg_ratio_flag = False
    if filter_type_index == 1:
        if obj_coll.name == 'subway_adgroup':
#             if filter_dict.has_key('cons_ratio'):
#                 cons_ratio_dict = filter_dict.pop('cons_ratio')
            adg_ratio_flag = True
        else:
            result_field_dict.update({'cons_ratio':{
                                                                      '$cond':[
                                                                                        {'$eq':['$yes_cost', 0]},
                                                                                        0,
                                                                                        {
                                                                                             '$divide':[
                                                                                                            '$yes_cost',
                                                                                                            '$yes_budget'
                                                                                            ]
                                                                                         },
                                                                                 ]
                                                                      }})
            group_condition_dict.update({
                                                                'yes_cost':{'$first':'$cost'},
                                                                'yes_budget':{'$first':'$budget'}
                                                           })
    # ===================================================================

    aggregate_datetime = datetime.datetime.now() - datetime.timedelta(days = 1 + days)
    try:
        filter_pipeline = []
        if match_rule:
            filter_pipeline.append(
                                                {
                                                    '$match':match_rule
                                                 }
                                                )

#         filter_pipeline.append(
#                                            {
#                                                 '$unwind':'$rpt_list'
#                                              }
#                                          )

        filter_pipeline.append(
                                           {
                                                '$match':{
                                                        'source':-1,
                                                        'date':{'$gt':aggregate_datetime}
                                                  }
                                             }
                                         )

        # date 现网没有建立索引，可能会很慢
#         filter_pipeline.append(
#                                            {
#                                                 '$sort':{
#                                                         'date':-1
#                                                   }
#                                              }
#                                          )

        filter_pipeline.append(
                                           {
                                                '$group':group_condition_dict
                                             }
                                         )

        filter_pipeline.append(
                                           {
                                                '$project':result_field_dict
                                             }
                                         )
        if filter_dict:
            filter_pipeline.append(
                                                {
                                                    '$match':filter_dict
                                                }
                                             )
            # 以下是用于统计报表用的，暂不开放
#         if group_key:
#             filter_pipeline.append(
#                                                {
#                                                     '$unwind':'$shop_list'
#                                                  }
#                                              )
#             filter_pipeline.append(
#                                                {
#                                                    '$group':{
#                                                                     '_id':{
#                                                                                  group_key:'$%s' % (group_key)
#                                                                             },
#                                                                     # 基本数据
#                                                                    'impressions':{'$first':'$impressions'},
#                                                                    'cost':{'$first':'$cost'},
#                                                                    'click':{'$first':'$click'},
#                                                                    'aclick':{'$first':'$aclick'},
#                                                                     # 效果数据
#                                                                    'directpay':{'$first':'$directpay'},
#                                                                    'indirectpay':{'$first':'$indirectpay'},
#                                                                    'directpaycount':{'$first':'$directpaycount'},
#                                                                    'indirectpaycount':{'$first':'$indirectpaycount'},
#                                                                    'favitemcount':{'$first':'$favitemcount'},
#                                                                    'favshopcount':{'$first':'$favshopcount'},
#                                                                     # 计算数据
#                                                                     'cpc':{'$first':'$cpc'},
#                                                                     'ctr':{'$first':'$ctr'},
#                                                                     'paycount':{'$first':'$paycount'},
#                                                                     'conv':{'$first':'$conv'},
#                                                                     'pay':{'$first':'$pay'},
#                                                                     'roi':{'$first':'$roi'},
#                                                                     'favcount':{'$first':'$favcount'},
#                                                                     'fav_roi':{'$first':'$fav_roi'},
#                                                                     'profit':{'$first':'$profit'},
#
#                                                                     obj_list_name:{'$addToSet':'$%s' % (obj_list_name)}
#                                                              }
#                                                  }
#                                              )

#         from pprint import pprint
#         pprint(filter_pipeline)
#         print obj_coll
        result_list = obj_coll.aggregate(filter_pipeline, allowDiskUse = True)['result']
        # TODO: 此处需要重构 yangrongkai 算法需要更改 有误
        # ===================================================================
        if adg_ratio_flag:
            new_result_list = []
#             camp_id_list = [ camp['camp_id'] for camp in result_list]
#             camp_budget_dict = { camp['_id']:camp['budget'] for camp in camp_coll.find({'_id':{'$in':camp_id_list}}, {'budget':1})}
            for camp in result_list:
#                 camp_id = camp['camp_id']
#                 if camp_budget_dict.has_key(camp_id):
#                     budget = camp_budget_dict[camp_id]
#                     cost = camp.get('cost', 0)
#                     cons_ratio = cost * 1.0 / budget
#                     gte_val = cons_ratio_dict.get('$gte', '')
#                     if gte_val and cons_ratio < gte_val:
#                         continue
#                     lte_val = cons_ratio_dict.get('$lte', '')
#                     if lte_val and cons_ratio > lte_val:
#                         continue
#                     camp.update({'cons_ratio':cons_ratio})
#                     new_result_list.append(camp)
                camp.update({'cons_ratio':-0.01})
                new_result_list.append(camp)
            return new_result_list
        # ===================================================================
#         for result in result_list:
#             log.error('---->   data :  %s' % (result))
        return result_list
    except Exception, e:
        log.exception('aggregate pipeline is error, e=%s' % e)
    return {}

def get_specific_statistics_parms(specific_parameter_dict, is_extends):
    """获取需要进行特别统计的参数"""
    return_dict = {}
    if not is_extends:
        return return_dict

    if specific_parameter_dict.has_key('stat_type') and specific_parameter_dict.has_key('mnt_type'):
        stat_type = int(specific_parameter_dict['stat_type'])
        mnt_type = int(specific_parameter_dict['mnt_type'])
        cond_dict = {}
        if stat_type == 0:
            if mnt_type > 0:
                cond_dict.update({'mnt_type':mnt_type})
            elif mnt_type > -1:
                cond_dict.update({'mnt_type':{'$in':[None, 0]}})
            else:
                cond_dict.update({'mnt_type':{'$in':[1, 2]}})
        elif stat_type == 1:
            cond_dict.update({'mnt_type':{'$nin':[1, 2]}})
        else:
            return return_dict
        return_dict['campaign'] = [adg_coll, 'campaign_id', cond_dict]
    return return_dict
