# coding=UTF-8

import datetime

from django.conf import settings
from mongoengine.errors import DoesNotExist

from dajax.core import Dajax
from apilib import get_tapi
from apps.common.utils.utils_log import log
from apps.common.utils.utils_number import fen2yuan
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import date_2datetime, time_humanize, time_is_someday
from apps.common.utils.utils_number import format_division
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.biz_utils.utils_misc import get_ip_for_rank, get_page_value_by_order
from apps.common.cachekey import CacheKey
from apps.subway.models_account import Account
from apps.subway.models_campaign import Campaign
from apps.subway.models_item import Item
from apps.subway.models_adgroup import Adgroup, adg_coll
from apps.subway.models_creative import Creative
from apps.subway.models_keyword import Keyword, Attention
from apps.subway.upload import update_campaign
from apps.mnt.models import MntCampaign, MntMnger, MntTaskMng
from apps.web.models import TempMonitor
from apps.subway.upload import mnt_quick_oper_log, udpate_cmp_budget_log, change_cmp_maxprice_log
from apps.common.biz_utils.utils_misc import analysis_web_opter

from qnyd.rtrpt_helper import get_hclick_adgrtrpt_byshopid, get_hclick_kwrtrpt_byadgid

def route_dajax(request):
    '''dajax路由函数'''
    auto_hide = int(request.POST.get('auto_hide', 1))
    dajax = Dajax()
    if auto_hide:
        dajax.script("PTQN.hide_loading();")
    function_name = request.POST.get('function')
    if function_name and globals().get(function_name, ''):
        dajax = globals()[function_name](request = request, dajax = dajax)
    else:
        dajax = log.exception("route_dajax: function_name Does not exist")
    return dajax

def account_data(request, dajax):
    '''获取账户关键词和趋势图数据'''
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 7))

    account = Account.objects.get(shop_id = shop_id)
    rpt_sum = account.get_summed_rpt(rpt_days = last_day)
    account_table = {'total_cost':'%.2f' % (rpt_sum.cost / 100.0), 'click':rpt_sum.click, 'ctr':'%.2f' % rpt_sum.ctr, 'cpc':'%.2f' % (rpt_sum.cpc / 100.0),
                     'total_pay':'%.2f' % (rpt_sum.pay / 100.0), 'paycount':rpt_sum.paycount, 'roi':'%.2f' % rpt_sum.roi, 'conv':'%.2f' % rpt_sum.conv,
                     'balance':account.balance}

    result = {'account_table':account_table, 'common_message':[]}
    dajax.script("PTQN.account.call_back(%s)" % (json.dumps(result)))
    return dajax

def get_account_chart(request, dajax):
    from apps.web.utils import get_trend_chart_data
    shop_id = int(request.user.shop_id)
    snap_dict = Account.Report.get_snap_list({'shop_id': shop_id}, rpt_days = 7)
    category_list, series_cfg_list = get_trend_chart_data(data_type = 5, rpt_list = snap_dict.get(shop_id, []))
    series_list = [{'name':i['name'], 'data':i['value_list'], 'color': i['color']} for i in series_cfg_list]
    result = {'x':category_list, 'series':series_list}
    dajax.script("PTQN.account.chart_call_back(%s)" % (json.dumps(result)))
    return dajax

def keyword_manage_data(request, dajax):
    '''获取重点关注的关键词列表'''
    from apps.subway.download import Downloader

    shop_id = int(request.user.shop_id)
    page = int(request.POST.get('page', 1))
    page_count = int(request.POST.get('page_count', 20))

    json_kw_list = []
    kw_list = Attention.get_attention_list(shop_id)
    kw_id_list = [kw.keyword_id for kw in kw_list]
    kw_rpt_dict = Keyword.Report.get_summed_rpt({'shop_id': shop_id, 'keyword_id': {'$in': kw_id_list}}, rpt_days = 15)
    for kw in kw_list:
        kw.rpt = kw_rpt_dict.get(kw.keyword_id, Keyword.Report())
    kw_list.sort(key = lambda kw: kw.rpt.cost, reverse = True)

    adg_id_list, item_dict, camp_id_list, camp_dict = [], {}, [], {}
    for kw in kw_list:
        if kw.adgroup_id not in adg_id_list:
            adg_id_list.append(kw.adgroup_id)
        if kw.campaign_id not in camp_id_list:
            camp_id_list.append(kw.campaign_id)

    # 下载有展现的adgroup_id的关键词报表
    dler_obj, _ = Downloader.objects.get_or_create(shop_id = shop_id)
    dl_flag, _ = dler_obj.check_status_4rpt(klass = Keyword)
    if dl_flag and dler_obj.tapi:
        Keyword.download_kwrpt_bycond(shop_id = shop_id, tapi = dler_obj.tapi, token = dler_obj.token, rpt_days = 15, cond = 'impressions', adg_id_list = adg_id_list)

    adg_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list)
    camp_list = Campaign.objects.filter(shop_id = shop_id, campaign_id__in = camp_id_list)

    for adgroup in adg_list:
        if adgroup.item:
            item_dict[adgroup.adgroup_id] = {'id':adgroup.item.item_id, 'title':adgroup.item.title, 'price':'%.2f' % (adgroup.item.price / 100.0), 'pic_url':adgroup.item.pic_url}
        else:
            for kw in kw_list:
                if kw.adgroup_id == adgroup.adgroup_id:
                    kw_list.remove(kw)

    for camp in camp_list:
        camp_dict[camp.campaign_id] = {'title':camp.title}

    for kw in kw_list:
        json_kw_list.append({"keyword_id":kw.keyword_id,
                             "adgroup_id":kw.adgroup_id,
                             "campaign_id":kw.campaign_id,
                             "item_id":item_dict[kw.adgroup_id]['id'],
                             "item_pic_url":item_dict[kw.adgroup_id]['pic_url'],
                             # "item_price":item_dict[kw.adgroup_id]['price'],
                             # "item_title":item_dict[kw.adgroup_id]['title'],
                             "word":kw.word,
                             # "create_days":kw.create_days,
                             "max_price":format(kw.max_price / 100.0, '.2f'),
                             "qscore":kw.qscore,
                             "impressions":kw.rpt.impressions,
                             "click":kw.rpt.click,
                             "ctr":format(kw.rpt.ctr, '.2f'),
                             "cost":format(kw.rpt.cost / 100.0, '.2f'),
                             "cpc":format(kw.rpt.cpc / 100.0, '.2f'),
                             # "favcount":kw.rpt.favcount,
                             "paycount":kw.rpt.paycount,
                             "pay":format(kw.rpt.pay / 100.0, '.2f'),
                             "conv":format(kw.rpt.conv, '.2f'),
                             "roi":format(kw.rpt.roi, '.2f'),
                             "g_click":format_division(kw.g_click, 1, 1, '0'),
                             "g_cpc":format_division(kw.g_cpc, 100, 1),
                             # "g_ctr":format_division(kw.g_click , kw.g_pv),
                             # "g_competition":format_division(kw.g_competition , 1, 1, '0'),
                             # "g_pv":kw.g_pv,
                             "match_scope":kw.match_scope,
                             "is_focus":kw.is_focus and 1 or 0
                             })

    result = {'record_count':len(json_kw_list), 'page':page, 'record':json_kw_list[(page - 1) * page_count:page * page_count]}
    dajax.script("PTQN.keyword_manage.call_back(%s)" % (json.dumps(result)))
    return dajax

def adgroup_cost_data(request, dajax):
    '''获取有花费的宝贝'''
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 3))
    page = int(request.POST.get('page', 1))
    page_count = int(request.POST.get('page_count', 20))

    rpt_dict = Adgroup.Report.get_summed_rpt(query_dict = {'shop_id': shop_id, 'cost': {'$gt': 0}}, rpt_days = last_day)
    adg_cur = adg_coll.find({'shop_id': shop_id, 'mnt_type':{'$in':[0, None]}}, {'item_id': 1, 'campaign_id': 1})

    adg_list = []
    for adg in adg_cur:
        rpt = rpt_dict.get(adg['_id'], None)
        if rpt:
            adg['rpt'] = rpt
            adg_list.append(adg)

    adg_list.sort(key = lambda k: k['rpt'].cost, reverse = True)

    total_count = len(adg_list)
    adg_list = adg_list[(page - 1) * page_count: page * page_count]
    json_adgroup_list = []
    if adg_list:
        adg_id_list, camp_id_list, item_id_list, camp_dict, item_dict, crt_dict = [], [], [], {}, {}, {}

        for adg in adg_list: # 获取其他查询所必要的条件
            adg_id_list.append(adg['_id'])
            if not adg['campaign_id'] in camp_id_list:
                camp_id_list.append(adg['campaign_id'])
            if not adg['item_id'] in item_id_list:
                item_id_list.append(adg['item_id'])

        camp_list = Campaign.objects.only('title').filter(shop_id = shop_id, campaign_id__in = camp_id_list)
        item_list = Item.objects.only('title', 'price', 'pic_url').filter(shop_id = shop_id, item_id__in = item_id_list)
        create_list = Creative.objects.only('title', 'adgroup_id').filter(shop_id = shop_id, adgroup_id__in = adg_id_list)

        # 获取计划名称
        camp_dict = {camp.campaign_id:camp.title for camp in camp_list}
        # 获取宝贝标题，价格，图片路径
        item_dict = {item.item_id:{'title':item.title, 'price':item.price, 'pic_url':item.pic_url} for item in item_list}
        for crt in create_list:
            adg_id = crt['adgroup_id']
            if crt_dict.has_key(adg_id):
                crt_dict[adg_id].append(crt['title'])
            else:
                crt_dict[adg_id] = [crt['title']]

        for adg in adg_list: # 附加item，campaign

            adg_id, item_id, camp_id, adg_rpt = adg['_id'], adg['item_id'], adg['campaign_id'], adg['rpt']
            creative_title_1, creative_title_2 = '', ''
            if crt_dict.has_key(adg_id):
                creative_title_1 = crt_dict[adg_id][0]
                if len(crt_dict[adg_id]) == 2:
                    creative_title_2 = crt_dict[adg_id][1]
            if not item_dict.get(item_id):
                item_dict[item_id] = {'title':'该宝贝可能不存在或者下架，请尝试同步数据', 'price':0, 'pic_url':'/site_media/jl/img/no_photo'}

            json_adgroup_list.append({'adgroup_id':int(adg_id),
                                      'campaign_id':camp_id,
                                      'campaign_title':camp_dict[camp_id],
                                      'item_id':item_id,
                                      'item_title':item_dict[item_id]['title'],
                                      # 'item_price':format(item_dict[item_id]['price'] / 100.0, '.2f'),
                                      'item_pic_url':item_dict[item_id]['pic_url'],
                                      'creative_title_1':creative_title_1,
                                      'creative_title_2':creative_title_2,
                                      'total_cost':format(adg_rpt.cost / 100.0, '.2f'),
                                      'impr':adg_rpt.impressions,
                                      'click':adg_rpt.click,
                                      'click_rate':format(adg_rpt.ctr, '.2f'),
                                      'total_pay':format(adg_rpt.pay / 100.0, '.2f'),
                                      'paycount':adg_rpt.paycount,
                                      'conv':format(adg_rpt.conv, '.2f')
                                      })

    result = {'record_count':total_count, 'page':page, 'record':json_adgroup_list}
    dajax.script("PTQN.adgroup_cost.call_back(%s)" % (json.dumps(result)))
    return dajax

def word_order(request, dajax):
    '''获取关键词当前排名'''

    from apps.engine.models import KeywordLocker
    ip = get_ip_for_rank(request)

    keyword_id = int(request.POST['keyword_id'])
    adgroup_id = int(request.POST['adgroup_id'])
    item_id = int(request.POST['item_id'])

    kw_list = list(Keyword.objects.filter(shop_id = int(request.user.shop_id), adgroup_id = adgroup_id, keyword_id = keyword_id))
    if not kw_list:
        # dajax.script('alert("该宝贝下无关键词，请点击“同步下载”菜单并检查是否有关键词，然后重试");')# TODO wuhuaqiao 2014-02-25
        return dajax

    # 批量查询关键词排名
    KeywordLocker.get_item_kws_current_order_list(user = request.user, item_id = item_id, kw_list = kw_list, ip = ip)

    keyword = kw_list[0]
    show_str = keyword.current_order
    if keyword.current_order == 0:
        show_str = '100+'
    elif keyword.current_order >= 201:
        show_str = '200+'
    result = {'order':show_str, 'keyword_id':keyword_id}
    dajax.script("PTQN.keyword_manage.call_back_order(%s)" % (json.dumps(result)))
    return dajax

def forecast_order(request, dajax):
    '''预测排名，前段暂时还没有实现'''
    return dajax

def cancel_attention(request, dajax):
    '''取消关注'''

    shop_id = int(request.user.shop_id)
    keyword_id = int(request.POST.get('keyword_id'))
    adgroup_id = int(request.POST.get('adgroup_id'))

    try:
        Attention.change_attention_state(shop_id, adgroup_id, keyword_id, False)
        result = [keyword_id]
    except Exception, e:
        log.error('cancel attention error, shop_id=%s, keyword_id=%s, e=%s' % (shop_id, keyword_id, e))
        result = []
    finally:
        dajax.script("PTQN.keyword_manage.call_back_cancel_attention(%s)" % (json.dumps(result)))
        return dajax

    shop_id = int(request.user.shop_id)
    kw_list = json.loads(request.POST.get('data', []))
    opter, opter_name = analysis_web_opter(request)
    updated_id_list, _, _, fail_update_id_list = update_kws_8shopid(shop_id = shop_id, kw_list = kw_list, opter = opter, opter_name = opter_name)
    result = {'success':updated_id_list, 'fall':fail_update_id_list}
    dajax.script("PTQN.keyword_manage.call_back_submit(%s)" % (json.dumps(result)))
    return dajax

def auto_set_attention_kw(request, dajax):
    '''一键设置关键词'''
    from apps.qnyd.biz import set_attention_kw

    shop_id = int(request.user.shop_id)
    set_attention_kw(shop_id = shop_id)
    dajax.script('window.location.href="%s";' % ('./keyword_manage'))
    return dajax

def forecast_order_list(request, dajax):
    '''预估排名'''
    kw_id = request.POST.get('keyword_id')
    tapi = get_tapi(request.user)

    rank_data = Keyword.rank_1_100(tapi = tapi, keyword_id = kw_id)

    order_dict, order_list = {}, []
    for rank, data in rank_data.items():
        page_order = get_page_value_by_order(rank)
        data['page'] = page_order
        if not order_dict.has_key(page_order):
            order_dict[page_order] = data
        else:
            if order_dict[page_order]['price'] > data['price']:
                order_dict[page_order] = data
    order_list = order_dict.values()
    order_list.sort(lambda x, y:cmp(x['rank'], y['rank']))

    result = {"kw_id": kw_id, "result": order_list}
    dajax.script("PTQN.keyword_manage.call_back_forecast(%s)" % (json.dumps(result)))
    return dajax

def get_keywords_rankingforecast(request, dajax):
    '''预测排名'''
    kw_id_list = request.POST.getlist('kw_id_list[]')
    tapi = get_tapi(request.user)
    shop_id = int(request.user.shop_id)
    forecast_data = {}
    for kw_id in kw_id_list:
        prices = Keyword.get_keyword_rankingforecast(tapi, shop_id, int(kw_id))
        dajax.script('PTQN.keyword_manage.call_back_forecast(%s, %s)' % (kw_id, json.dumps(prices)))
    return dajax

def has_attention_keyword(request, dajax):
    '''判断是否有关注的词'''
    has_attention = 0
    shop_id = int(request.user.shop_id)
    attention = Attention.get_attention_list(shop_id)
    if attention:
        has_attention = 1
    dajax.script("PTQN.Base.attention_call_back(%s)" % (has_attention))
    return dajax

def mnt_campaign(request, dajax):
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST['campaign_id'])
    rpt_days = int(request.POST.get('rpt_days', 1))

    try:
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = int(campaign_id))

        if not mnt_camp.optimize_time:
            mnt_camp.optimize_time = '尚未优化'
        else:
            mnt_camp.optimize_time = time_humanize(mnt_camp.optimize_time)

        is_active = 1
        if mnt_camp.quick_optime and time_is_someday(mnt_camp.quick_optime):
            is_active = 0

        campaign = Campaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
        sum_rpt = campaign.get_summed_rpt(rpt_days = rpt_days)
        json_dict = {'total_cost':fen2yuan(sum_rpt.cost),
                     'imp':sum_rpt.impressions,
                     'click':sum_rpt.click,
                     'ctr':'%.2f' % sum_rpt.ctr,
                     'cpc':fen2yuan(sum_rpt.cpc),
                     'total_pay':fen2yuan(sum_rpt.pay),
                     'roi':'%.2f' % sum_rpt.roi,
                     'conv':'%.2f' % sum_rpt.conv,
                     'paycount':sum_rpt.paycount
                     }
        max_price = 0
        if hasattr(mnt_camp, 'max_price'):
            max_price = format(mnt_camp.max_price / 100.0, '.2f')

        result = {'set':{'campaign_id':campaign_id,
                         'title':campaign.title,
                         'optimize_time':mnt_camp.optimize_time,
                         'max_price':max_price,
                         'budget':format(campaign.budget / 100.0, '.0f'),
                         'is_active':is_active,
                         'mnt_status':mnt_camp.mnt_status,
                         'mnt_type':mnt_camp.mnt_type,
                         },
                  'rpt':json_dict,
                  }
        dajax.script("PTQN.mnt.mnt_campaign_back(%s)" % json.dumps(result))
    except Exception, e:
        log.error('missing args or campaign not exist, shop_id = %s, e = %s' % (shop_id, e))
        if 'query does not exist' in str(e): # 删除缓存
            from apps.common.cachekey import CacheKey
            CacheAdpter.delete(CacheKey.WEB_MNT_MENU % shop_id, 'web')
        dajax.script('PTQN.alert("亲，请刷新页面重新操作！");')
    return dajax

def mnt_adg(request, dajax):
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST['campaign_id'])
    rpt_days = int(request.POST.get('rpt_days', 1))
    page = int(request.POST.get('page', 1))
    page_count = int(request.POST.get('page_count', 20))

    try:
        from apps.mnt.utils import get_adgroup_4campaign
        adg_list, mnt_num = get_adgroup_4campaign(shop_id = shop_id, campaign_id = campaign_id, rpt_days = rpt_days)
        result = {'record_count':len(adg_list), 'page':page, 'record':adg_list[(page - 1) * page_count:page * page_count]}
        dajax.script("PTQN.mnt.mnt_adg_back(%s)" % (json.dumps(result)))
    except Exception, e:
        log.error('missing args or campaign not exist, campaign_id = %s, e = %s' % (request.POST['campaign_id'], e))
        dajax.script('PTQN.alert("亲，请刷新页面重新操作！");')
    return dajax

def update_cfg(request, dajax):
    error_msg = ''
    shop_id = int(request.user.shop_id)
    campaign_id = request.POST['campaign_id']
    submit_data = json.loads(request.POST['submit_data'])
    mnt_type = int(request.POST.get('mnt_type', 1))
    opter, opter_name = analysis_web_opter(request)
    try:
        if submit_data.has_key('budget'):
            try:
                campaign = Campaign.objects.exclude('rpt_list').get(shop_id = shop_id, campaign_id = campaign_id)
            except DoesNotExist, e:
                log.info('can not get campaign, campaign_id = %s' % campaign_id)
                dajax.script('PTQN.light_msg("亲，请刷新页面重新操作！","red");')
                return dajax
            old_budget = campaign.budget
            new_budget = submit_data['budget']

            try:
                result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = int(campaign_id), record_flag = False, budget = new_budget,
                                                        use_smooth = campaign.is_smooth and 'true' or 'false', opter = opter, opter_name = opter_name)
                if 'budget' in result_list:
                    display_budget = lambda x: x == 20000000 and '不限' or ('%s元' % x)
                    descr = '日限额由%s，修改为%s' % (display_budget(old_budget / 100), display_budget(new_budget))
                    udpate_cmp_budget_log(shop_id = shop_id, campaign_id = campaign_id, opt_desc = descr, opter = opter, opter_name = opter_name)
                else:
                    raise Exception('<br/>'.join(msg_list))
            except Exception, e:
                log.info('update campaign budget error, e = %s, shop_id = %s' % (e, shop_id))
                if 'sub_msg":"日限额不得小于推广计划实时扣款金额' in str(e):
                    dajax.script('PTQN.light_msg("日限额不得小于推广计划实时扣款金额！","red");')
                else:
                    dajax.script('PTQN.light_msg("修改日限额失败","red");')
                return dajax

        if submit_data.has_key('max_price'):
            try:
                mnt_campaign = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
            except DoesNotExist, e:
                log.info('can not get mnt_campaign, campaign_id = %s' % campaign_id)
                dajax.script('PTQN.light_msg("亲，请刷新页面重新操作！","red");')
                return dajax

            old_max_price = mnt_campaign.max_price
            new_max_price = int(float(submit_data.get('max_price', old_max_price / 100.0)) * 100)
            if new_max_price != old_max_price:
                mnt_campaign.max_price = new_max_price
                change_cmp_maxprice_log(shop_id = shop_id, campaign_id = campaign_id, max_price = new_max_price, opter = opter, opter_name = opter_name)
                MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = campaign_id, mnt_type = mnt_type, task_type = 2, adgroup_id_list = 'ALL')

            mnt_campaign.save()

        dajax.script('PTQN.mnt.submit_cfg_back("%s","%s");' % (submit_data.get('budget', ''), submit_data.get('max_price', '')))
    except Exception, e:
        log.info('submit MntCampaign cfg error,e = %s, campaign_id = %s' % (e, campaign_id))
        dajax.script('PTQN.alert("%s","red");' % (error_msg == '' and '修改失败，请刷新页面重新操作！' or error_msg))

    return dajax

def quick_oper(request, dajax):
    """触发页面上的“加大投入/减小投入”"""
    try:
        shop_id = int(request.user.shop_id)
        campaign_id = int(request.POST['campaign_id'])
        stgy = int(request.POST['stgy'])
        opter, opter_name = analysis_web_opter(request)
        mnt_campaign = MntCampaign.objects.get(campaign_id = campaign_id)
        if not mnt_campaign.quick_optime or not time_is_someday(mnt_campaign.quick_optime):
            MntTaskMng.generate_quickop_task(shop_id = mnt_campaign.shop_id, campaign_id = mnt_campaign.campaign_id, mnt_type = mnt_campaign.mnt_type, stgy = stgy)
            # 不管执行成功或者失败，都不让再操作
            mnt_campaign.quick_optime = datetime.datetime.now()
            mnt_campaign.save()
            dajax.script('PTQN.mnt.quick_oper_back(%s);' % (stgy))
        else:
            dajax.script('PTQN.mnt.quick_oper_back(0);')
        stgy_name = '加大投入' if stgy == 1 else '减小投入'
        opt_type = 15 if stgy == 1 else 16
        opt_desc = '对托管的宝贝%s' % (stgy_name)
        mnt_quick_oper_log(shop_id, campaign_id, [], opt_desc, opter = opter, opter_name = opter_name)
    except Exception, e:
        log.exception('mnt quick oper error, shop_id=%s, campaign_id=%s, e=%s' % (request.user.shop_id, campaign_id, e))
        dajax.script('PTQN.mnt.quick_oper_back(0);')
    return dajax

def update_prop_status(request, dajax):
    """修改托管状态，包含两个状态，计划是否暂停与托管是否暂停，一改同时改"""
    try:
        campaign_id = request.POST['campaign_id']
        status = bool(int(request.POST['status']))
        shop_id = int(request.user.shop_id)
        mnt_type = int(request.POST.get('mnt_type', 0))
        online_status, mnt_status, opt_desc = status and ('online', 1, '开启自动优化') or ('offline', 0, '暂停自动优化')
        opter, opter_name = analysis_web_opter(request)
        result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = campaign_id, online_status = online_status, opter = opter, opter_name = opter_name)
        if 'online_status'not in result_list:
            raise Exception('<br/>'.join(msg_list))
        MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id).update(set__mnt_status = mnt_status)
        dajax.script('PTQN.mnt.update_camp_back(%s)' % (status and 1 or 0))
    except Exception, e:
        log.info('update mnt campaign prop status error ,e = %s, shop_id = %s' % (e, request.user.shop_id))
        dajax.script("PTQN.alert('%s失败，请刷新页面重新操作！');" % (opt_desc))
    return dajax

def close_mnt(request, dajax):
    shop_id = int(request.user.shop_id)
    mnt_type = int(request.POST.get('mnt_type'))
    campaign_id = int(request.POST['campaign_id'])
    try:
        MntMnger.set_mnt_camp(campaign_id = campaign_id, flag = 0, mnt_type = mnt_type)
        dajax.script("window.location.reload()")
    except Exception, e:
        log.error('qnyd close mnt error, shop_id=%s, camp_id=%s, e=%s' % (shop_id, campaign_id, e))
        dajax.script("PTQN.alert('未知错误，5秒后刷新页面');setTimeout('window.location.reload()', 5000)")
    return dajax

def submit_phone(request, dajax):
    qq = request.POST.get('qq', '')
    phone = request.POST.get('phone', '')
    namespace = request.POST.get('namespace', 'PTQN')
    shop_id = int(request.user.shop_id)
    is_success = 0

    try:
        # from apps.crm.models import Customer
        # from apps.ncrm.models import Customer as NCustomer
        # customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'user':request.user, 'nick':request.user.nick, 'tp_status':'untouched', 'jl_use_status':'using'})
        from apps.ncrm.models import Customer
        customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'nick':request.user.nick})
        if qq:
            customer.qq = qq
        customer.phone = phone
        customer.save()
        # NCustomer.sync_customer_info(customer)
        CacheAdpter.set(CacheKey.WEB_ISNEED_PHONE % shop_id, 0, 'web', 60 * 60 * 24 * 7)
        is_success = 1
    except Exception, e:
        log.exception('submit userinfo error, e=%s, shop_id=%s' % (e, request.user.shop_id))

    dajax.script("%s.Base.submit_phone_back(%s)" % (namespace, is_success))
    return dajax

def query_hclick_keywords(request, dajax):
    """查询有点击关键词"""
    shop_id = int(request.user.shop_id)
    kw_list = get_hclick_kwrtrpt_byshopid(shop_id)

    kw_id_list = []
    adg_id_set = set()
    for kw in kw_list:
        kw_id = int(kw.kw_id)
        adg_id = int(kw.adgroup_id)
        kw_id_list.append(kw_id)
        adg_id_set.add(adg_id)
    adg_id_list = list(adg_id_set)

    kw_dict = {kw.keyword_id : kw for kw in Keyword.objects.filter(keyword_id__in = kw_id_list)}
    adg_dict = {adg.adgroup_id : adg for adg in Adgroup.objects.filter(adgroup_id__in = adg_id_list)}
    items_id_list = [ adg.item_id for adg in adg_dict.values()]
    item_dict = {item.item_id : item for item in Item.objects.filter(item_id__in = items_id_list)}

    result_data = []
    for kw in kw_list:
        kw_id = int(kw.kw_id)
        adg_id = int(kw.adgroup_id)
        kw_obj = kw_dict.get(kw_id, None)
        adg_obj = adg_dict.get(adg_id, None)
        if kw_obj and adg_obj :
            item_obj = item_dict.get(adg_obj.item_id, None)
            if item_obj:
                temp = {
                        "kw_id":kw_id,
                        "camp_id":kw.campaign_id,
                        "adg_id":kw.adgroup_id,
                        "kw_name":kw_obj.word,
                        "kw_scope":kw_obj.match_scope,
                        "kw_price":round(kw_obj.max_price / 100.0, 2),
                        "kw_rt_cost":round(kw.cost / 100.0, 2),
                        "kw_rt_click":kw.click,
                        "kw_rt_pay_count":kw.paycount,
                        'item_pic_url' : item_obj.pic_url,
                        'item_title' : item_obj.title,
                 }
                result_data.append(temp)

    dajax.script("PTQN.kw_monitor.call_back(%s)" % (json.dumps(result_data)))
    return dajax


def query_adgroups_rtclick(request, dajax):
    shop_id = int(request.user.shop_id)

    adg_rt_infos = get_hclick_adgrtrpt_byshopid(shop_id)
    adg_id_list = adg_rt_infos.keys()
    adg_dict = {adg.adgroup_id:adg for adg in Adgroup.objects.\
                    filter(shop_id = shop_id, adgroup_id__in = adg_id_list)}
    items_id_list = [ adg.item_id for adg in adg_dict.values()]
    item_dict = {item.item_id : item for item in Item.objects.filter(item_id__in = items_id_list)}

    result_data = []
    for adg_id, adg in adg_rt_infos.items():
        adg_obj = adg_dict.get(adg_id, None)
        if adg_obj:
            item_obj = item_dict.get(adg_obj.item_id, None)
            if item_obj:
                temp = {"adg_id":adg_id,
                        "camp_id":getattr(adg, 'campaign_id', None),
                        "adg_rt_click":getattr(adg, 'click', None),
                        'item_pic_url' : item_obj.pic_url,
                        }
                result_data.append(temp)
    result_data.sort(key = lambda obj : obj['adg_rt_click'], reverse = True)

    func_name = 'query_adgroups_rtclick'
    func_desc = '获取宝贝实时流量-（实时监控首页）'
    args = json.dumps({'shop_id':shop_id})
    result = len(result_data)
    TempMonitor.generetor_record(shop_id, func_name, func_desc, args, result)
    dajax.script("PTQN.kw_monitor.adgroup_rtrpt_callback(%s)" % (json.dumps(result_data)))
    return dajax

def query_keywords_rtclick(request, dajax):
    shop_id = int(request.user.shop_id)
    adg_id = int(request.POST.get("adg_id", 0))

    adgroup, adg_info, result_data = None , {}, []
    try:
        adgroup = Adgroup.objects.get(adgroup_id = adg_id)
    except :
        pass

    if adgroup:
        kw_dict = {kw.keyword_id : kw for kw in Keyword.objects.filter(shop_id = shop_id, \
                                                                        adgroup_id = adg_id)}
        kw_rt_infos = get_hclick_kwrtrpt_byadgid(adgroup.shop_id, adgroup.campaign_id, \
                                                  adgroup.adgroup_id)
        adg_info = {
                        'item_title' : adgroup.item.title,
                        'camp_title' : adgroup.campaign.title,
                    }
        for kw_id, kw in kw_rt_infos.items():
            kw_obj = kw_dict.get(kw_id, None)
            if kw_obj :
                temp = {
                        "kw_id":kw_id,
                        "camp_id":kw_obj.campaign_id,
                        "adg_id":kw_obj.adgroup_id,
                        "kw_name":kw_obj.word,
                        "kw_scope":kw_obj.match_scope,
                        "kw_price":round(kw_obj.max_price / 100.0, 2),
                        "kw_rt_impr":kw.impressions,
                        "kw_rt_cost":round(kw.cost / 100.0, 2),
                        "kw_rt_click":kw.click,
                        "kw_rt_pay_count":kw.paycount,
                        'item_pic_url' : adgroup.item.pic_url,
                 }
                result_data.append(temp)
        result_data.sort(key = lambda obj : (obj['kw_rt_click'], obj['kw_rt_impr']), reverse = True)
        result_data = result_data[:100] # top 100

    func_name = 'query_keywords_rtclick'
    func_desc = '获取某一宝贝关键词实时流量 -（宝贝关键词流量）'
    args = json.dumps({'shop_id':shop_id, 'adgroup_id':adg_id})
    result = len(result_data)
    TempMonitor.generetor_record(shop_id, func_name, func_desc, args, result)
    dajax.script("PTQN.kw_monitor.keyword_rtrpt_callback(%s,%s)" % (json.dumps(result_data), json.dumps(adg_info)))
    return dajax

def curwords_submit(request, dajax):
    '''提交关键词出价到直通车'''
    from apps.web.utils import update_kws_8shopid

    shop_id = int(request.user.shop_id)
    kw_list = json.loads(request.POST.get('data', []))
    updated_id_list, _, _, fail_update_id_list = update_kws_8shopid(shop_id = shop_id, kw_list = kw_list)
    result = {'success':updated_id_list, 'fall':fail_update_id_list}
    dajax.script("PTQN.keyword_manage.kw_submit_callback(%s)" % (json.dumps(result)))
    return dajax

def curwords_submit_4monitor(request, dajax):
    '''提交关键词出价到直通车'''
    from apps.web.utils import update_kws_8shopid
    shop_id = int(request.user.shop_id)
    kw_list = json.loads(request.POST.get('data', []))
    updated_id_list, _, _, fail_update_id_list = update_kws_8shopid(shop_id = shop_id, kw_list = kw_list)
    result_data = {'success':updated_id_list, 'fall':fail_update_id_list}

    func_name = 'curwords_submit_4monitor'
    func_desc = '获取某一宝贝关键词实时流量 -（宝贝关键词流量）'
    args = json.dumps(kw_list)
    result = json.dumps(result_data)
    TempMonitor.generetor_record(shop_id, func_name, func_desc, args, result)
    dajax.script("PTQN.kw_monitor.kw_submit_callback(%s)" % (json.dumps(result_data)))
    return dajax
