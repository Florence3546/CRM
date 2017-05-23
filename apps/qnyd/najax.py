# coding=UTF-8
'''
Created on 2016-1-13

@author: Administrator
'''
import random
import math, re
import datetime, time
from threading import Thread

from django.http import HttpResponse
from apilib import get_tapi
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import datetime_2string, string_2datetime, days_diff_interval, time_is_someday, time_is_recent
from apps.common.biz_utils.utils_misc import analysis_web_opter
from apps.web.utils import (get_trend_chart_data, update_kws_8shopid)
from apps.common.biz_utils.utils_tapitools import get_kw_g_data
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.subway.realtime_report import RealtimeReport
from apps.subway.models import (Account, Campaign, Adgroup, Keyword, Item)
from apps.mnt.models_mnt import MntCampaign
from apps.engine.models_kwlocker import KeywordLocker
from apps.engine.models_channel import MessageChannel
from apps.engine.models_corekw import CoreKeyword
from apps.engine.rob_rank import (CustomRobRank, RobRankMng)
from apps.subway.download import Downloader
from apps.subway.upload import (update_campaign)
from apps.ncrm.models import Customer
from apps.web.models import Feedback

from apps.web.najax import is_data_ready as web_is_data_ready, submit_userinfo as web_submit_userinfo, get_shop_core_kwlist as web_shop_core_list, batch_get_rt_kw_rank as web_batch_get_kw_rank



def route_ajax(request):
    """ajax路由函数，返回数据务必返回字典的格式"""
    function_name = request.POST.get('function', '')
    call_back = request.GET.get('callback')

    try:
        if function_name and globals().get(function_name, ''):
            data = globals()[function_name](request = request)
        else:
            log.exception("route_ajax: function_name Does not exist")
            data = {'error': 'function_name Does not exist'}
    except Exception, e:
        log.exception("route_ajax error, e=%s ,request_data=%s" %
                      (e, request.POST))
        if 'AnonymousUser' in str(e):
            data = {'errMsg': '会话已过期，请重新登录！'}
        else:
            data = {'errMsg': '未知错误，请联系顾问！'}
    return HttpResponse('%s' % json.dumps(data))

def balance(request):
    """获取账户余额"""
    errMsg = ""
    balance = 0
    try:
        shop_id = int(request.user.shop_id)
        account = Account.objects.get(shop_id = shop_id)
        balance = account.balance
    except DoesNotExist:
        errMsg = "账户不存在"
        log.error('get balance error Account does not exist')
    return {'errMsg':errMsg, "balance":balance}

def account(request):
    """获取账户主要信息"""
    shop_id = int(request.user.shop_id)
    account_data_dict = {}
    update_cache = int(request.POST.get('update_cache', '0'))
    try:
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        errMsg = ''

        if start_date == end_date == datetime.date.today().strftime('%Y-%m-%d'): # 实时数据
            rpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'account', args_list = [shop_id], update_now = bool(update_cache)) # 从缓存取账户时实数据
            rtrpt_item = rpt_dict.get(shop_id, Account.Report())
            account_data_dict = {'cost':'%.2f' % (rtrpt_item.cost / 100.0), 'impr':rtrpt_item.impressions, 'click':rtrpt_item.click, 'ctr':'%.2f' % rtrpt_item.ctr, 'cpc':'%.2f' % (rtrpt_item.cpc / 100.0),
              'pay':'%.2f' % (rtrpt_item.pay / 100.0), 'paycount':rtrpt_item.paycount, 'favcount':rtrpt_item.favcount, 'roi':'%.2f' % rtrpt_item.roi, 'conv':'%.2f' % rtrpt_item.conv, 'avg_pay':'%.2f' % (rtrpt_item.avg_pay / 100.0),
              'directpay':'%.2f' % (rtrpt_item.directpay / 100.0), 'indirectpay':'%.2f' % (rtrpt_item.indirectpay / 100.0), 'directpaycount':rtrpt_item.directpaycount,
              'indirectpaycount':rtrpt_item.indirectpaycount, 'favitemcount':rtrpt_item.favitemcount, 'favshopcount':rtrpt_item.favshopcount, 'carttotal':rtrpt_item.carttotal, 'pay_cost':'%.2f' % (rtrpt_item.pay_cost / 100.0),
            }
        else: # 历史数据
            rpt_dict = Account.Report.get_summed_rpt({'shop_id': shop_id}, start_date = start_date, end_date = end_date)
            account_rpt = rpt_dict.get(shop_id, Account.Report())
            account_data_dict = account_rpt.to_dict()

    except Exception, e:
        log.error("get account_rpt error, shop_id=%s, error=%s" % (shop_id, e))
        errMsg = '获取店铺数据失败，请刷新页面'
    return {'errMsg':errMsg, 'account_data_dict':account_data_dict}

def show_chart(request):
    """获取账户图表"""
    shop_id = int(request.user.shop_id)
    chart_data = {}
    update_cache = int(request.POST.get('update_cache', '0'))
    try:
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        errMsg = ''
        rpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'account', args_list = [shop_id], update_now = bool(update_cache)) # 从缓存取账户时实数据
        rtrpt_item = rpt_dict.get(shop_id, Account.Report())
        snap_dict = Account.Report.get_snap_list(query_dict = {'shop_id': shop_id}, start_date = start_date, end_date = end_date)
        snap_list = snap_dict.get(shop_id, [])
        snap_list.append(rtrpt_item)
        category_list, series_cfg_list = get_trend_chart_data(data_type = 1, rpt_list = snap_list)
        chart_data = {'category_list': category_list, 'series_cfg_list': series_cfg_list}
    except Exception, e:
        log.error("get account_chart error, shop_id=%s, error=%s" % (shop_id, e))
        errMsg = '获取店铺数据失败，请刷新页面'
    return {'errMsg':errMsg, 'chart_data': chart_data}

def campaign_list(request):
    """获取计划数据"""
    shop_id = int(request.user.shop_id)
    campaign_list = Campaign.objects.filter(shop_id = shop_id).order_by('campaign_id')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    camp_rpt_dict = {}
    mnt_list = MntCampaign.objects.only('campaign_id', 'mnt_index', 'mnt_type', 'start_time').filter(shop_id = shop_id)
    mnt_dict = {mnt.campaign_id:(mnt.mnt_index, mnt.mnt_type, mnt.get_mnt_type_display(), days_diff_interval(mnt.start_time.date())) for mnt in mnt_list}
    adg_num_dict = Adgroup.get_adgroup_count(shop_id = shop_id)
    json_campaign_list = []
    init_mnt_list = (0, 0, '', 0)
    is_rt_camp = 0

    if start_date == end_date == datetime.date.today().strftime('%Y-%m-%d'):
        camp_rpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'campaign', args_list = [shop_id])
        if camp_rpt_dict:
            is_rt_camp = 1
    else:
        camp_rpt_dict = Campaign.Report.get_summed_rpt(query_dict = {'shop_id': shop_id}, start_date = start_date, end_date = end_date)

    for camp in campaign_list:
        tmp_rpt = camp_rpt_dict.get(camp.campaign_id, Campaign.Report())
        tmp_rpt_dict = tmp_rpt.to_dict()
        mnt_info = mnt_dict.get(camp.campaign_id, init_mnt_list)
        mnt_index, mnt_type, mnt_name, mnt_days = mnt_info
        temp_adg_num_tuple = adg_num_dict.get(camp.campaign_id, (0, 0, 0))

        yd_search = 0 # 是否在移动端推广
        if camp.platform['yd_outsite'] or camp.platform['yd_insite']:
            yd_search = 1

        schedule = 0
        now_date = time.mktime(datetime.datetime.now().timetuple())
        now_date_str = datetime_2string(None, '%Y-%m-%d')

        try:
            for _schedule in camp.schedule.split(';')[datetime.datetime.now().weekday()].split(','):
                start_time = string_2datetime(now_date_str + ' ' + _schedule[0:5], '%Y-%m-%d %H:%M')
                end_time = string_2datetime(now_date_str + ' ' + ('23:59' if _schedule[6:11] == '24:00' else _schedule[6:11]), '%Y-%m-%d %H:%M')
                if time.mktime(start_time.timetuple()) <= now_date and time.mktime(end_time.timetuple()) >= now_date:
                    schedule = _schedule[12:len(_schedule)]
                    break
        except:
            pass

        temp_camp = {
            'campaign_id':camp.campaign_id,
            'title':camp.title,
            'budget':'%.0f' % (camp.budget / 100.0),
            'online_status':camp.online_status,
            'comment_count':camp.comment_count,
            'error_descr':camp.error_descr,
            'is_smooth':camp.is_smooth and 1 or 0,
            'adg_num':temp_adg_num_tuple[0],
            'mnt_index':mnt_index,
            'mnt_name':mnt_name,
            'mnt_type':mnt_type,
            'schedule':schedule,
            'yd_search':yd_search,
            'mnt_days': mnt_days
        }
        temp_camp.update(tmp_rpt_dict)
        json_campaign_list.append(temp_camp)

    return {'errMsg':'', 'json_campaign_list':json_campaign_list, 'is_rt_camp':is_rt_camp}

def set_budget(request):
    """设置日限额"""
    budget = int(request.POST['budget'])
    campaign_id = int(request.POST['camp_id'])
    use_smooth = request.POST['use_smooth']
    shop_id = int(request.user.shop_id)
    errMsg = ''
    opter, opter_name = analysis_web_opter(request)
    try:
        result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = campaign_id, budget = budget, use_smooth = use_smooth, opter = opter, opter_name = opter_name)
        if 'budget' in result_list:
            json_result_data = {'camp_id':campaign_id, 'budget':budget, 'use_smooth':use_smooth}
        else:
            json_result_data = {}
            errMsg = '<br/>'.join(msg_list)
    except Exception, e:
        log.info('modify_camp_budget error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, e))
        errMsg = '修改日限额失败，请联系顾问'
    return {'errMsg':errMsg, 'json_result_data':json_result_data}

def set_online_status(request):
    """修改计划状态 """
    shop_id = int(request.user.shop_id)
    camp_id_list = request.POST.getlist('camp_id_list[]')
    mode = int(request.POST['mode'])
    online_status = mode and 'online' or 'offline'
    opter, opter_name = analysis_web_opter(request)
    success_camp_ids, failed_camp_ids = [], []
    try:
        for camp_id in camp_id_list:
            result_list, _ = update_campaign(shop_id = shop_id, campaign_id = camp_id, online_status = online_status, opter = opter, opter_name = opter_name)
            if 'online_status' in result_list:
                success_camp_ids.append(str(camp_id))
            else:
                failed_camp_ids.append(str(camp_id))
        return {'errMsg':'', 'mode':mode, 'success_camp_ids':success_camp_ids}
    except Exception, e:
        log.error('update_camps_status error,e=%s, shop_id=%s' % (e, shop_id))
        return {'errMsg':'修改失败：淘宝接口不稳定，请稍后再试'}

def get_rpt_detail(request):
    """获取报表明细"""
    def format_report(rpt):
        return {
                'impr':rpt.impressions,
                'click':rpt.click,
                'ctr':'%.2f' % rpt.ctr,
                'cpc':'%.2f' % (rpt.cpc / 100.0),
                'cost':'%.2f' % (rpt.cost / 100.0),
                'pay':'%.2f' % (rpt.pay / 100.0),
                'paycount':rpt.paycount,
                'favcount':rpt.favcount,
                'roi':'%.2f' % rpt.roi,
                'conv':'%.2f' % rpt.conv,
                'carttotal':rpt.carttotal,
                'pay_cost':'%.2f' % (rpt.pay_cost / 100.0),
                'avg_pay':'%.2f' % (rpt.avg_pay / 100.0)
               }

    shop_id = int(request.user.shop_id)
    errorMsg = ''
    rpt_list = []
    type_model_dict = {'account':[Account, 'shop_id', 0]}
    try:
        obj_type = 'account'
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        obj_args = type_model_dict[obj_type]
        query_dict = {"shop_id": shop_id}

        # 每日数据
        snap_list = obj_args[0].Report.get_snap_list(query_dict, start_date = start_date, end_date = end_date).values()
        if snap_list:
            snap_list = snap_list[0]
        snap_list.reverse()

        for rpt in snap_list:
            dt = rpt.pop('date').strftime('%Y-%m-%d')
            temp_dict = {'date':dt, 'summed':format_report(rpt)}
            rpt_list.append(temp_dict)

    except Exception, e:
        errorMsg = '未获取到数据，请联系顾问'
        log.exception("get_rpt_detail error, shop_id=%s, e=%s" % (shop_id, e))
    return {
            'errMsg':errorMsg,
            'data':{'rpt_list': rpt_list}
           }

# 同步全店数据
def sync_data(request):
    """下载数据"""
    def download_data(shop_id, is_force, **kwargs):
        cache_key = CacheKey.WEB_SYNC_DATA_MUTUAL % shop_id
        mutual_timeout = is_force and (60 * 40) or (60 * 10)
        is_mutual = CacheAdpter.get(cache_key, 'web')
        if not is_mutual:
            CacheAdpter.set(cache_key, True, 'web', mutual_timeout)
            try:
                dler = Downloader.objects.get(shop_id = shop_id)
                if not dler.sync_all_struct(is_force = is_force):
                    raise Exception('dl_struct_failed', is_force)

                args = is_force and {'is_force':True, 'rpt_days':kwargs['rpt_days']} or {}
                if not dler.sync_all_rpt(**args):
                    raise Exception('dl_rpt_failed', is_force)

                return True, ''
            except Exception, e:
                log.error('download data error,shop_id=%s, e=%s' % (shop_id, e.args))
                return False, e[0]

            finally:
                CacheAdpter.delete(cache_key, 'web')
        else:
            return False, 'doing'

    shop_id = int(request.user.shop_id)
    is_force = False
    cache_key = CacheKey.WEB_SYNC_DATA_FLAG % shop_id
    is_recent_clicked = CacheAdpter.get(cache_key, 'web')
    if is_recent_clicked:
        is_force = True
        CacheAdpter.delete(cache_key, 'web') # 强制下载时，将缓存删除，下次重新走自动同步路线
    else:
        CacheAdpter.set(cache_key, True, 'web', 60 * 5) # 自动下载时，标记缓存

    result, reason = download_data(shop_id = shop_id, is_force = is_force, rpt_days = None)
    if result:
        msg = '数据同步成功！'
    else:
        if str(reason) in ['dl_struct_failed', 'dl_rpt_failed']:
            msg = '同步数据失败，请刷新重试！'
        elif str(reason) == 'doing':
            msg = '数据正在同步中，请稍等！'
        else:
            msg = '同步数据失败，请联系顾问！'

    return {'errMsg': '', 'msg': msg}

def rob_list(request):
    """自动抢排名列表"""
    errMsg, kw_id_list, adg_id_list, word_list, keyword_locker_dict, item_id_set, campaign_id_set = "", [], [], [], {}, set(), set()
    shop_id = int(request.user.shop_id)
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    keyword_locker_list = list(KeywordLocker.objects.filter(shop_id = shop_id))

    for kll in keyword_locker_list:
        kw_id_list.append(kll.id)
        adg_id_list.append(kll.adgroup_id)
        word_list.append(kll.word)
        keyword_locker_dict[kll.id] = kll

    # 绑定关键词报表数据
    kw_rpt_dict = Keyword.Report.get_summed_rpt(query_dict = {'shop_id': shop_id, 'keyword_id': {'$in': kw_id_list}}, start_date = start_date, end_date = end_date)
    # 绑定关键词结构数据
    keyword_list = list(Keyword.objects.filter(shop_id = shop_id, keyword_id__in = kw_id_list))
    # 绑定关键词全网数据
    kw_g_data = get_kw_g_data(word_list)

    # 获取item_id_set
    for kw in keyword_list:
        kw.item_id = kw.adgroup.item_id
        campaign_id_set.add(kw.campaign_id)
        item_id_set.add(kw.item_id)

    campaign_dict = {camp.campaign_id: camp for camp in  Campaign.objects.filter(shop_id = shop_id, campaign_id__in = list(campaign_id_set))}
    item_dict = {item.item_id: [item.title, item.price, item.pic_url]for item in Item.objects.filter(shop_id = shop_id, item_id__in = list(item_id_set))}

    adg_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list).only('adgroup_id', 'item_id', 'mnt_type', 'mobile_discount')
    adg_dict = {obj.adgroup_id: obj for obj in adg_list}

    result_list, empty_rpt = [], Keyword.Report()
    for kw in keyword_list:
        kw.set_g_data(kw_g_data.get(str(kw.word), {}))

        kw.rpt = kw_rpt_dict.get(kw.id, empty_rpt)
        kw.locker = keyword_locker_dict.get(kw.keyword_id)
        kw.item = item_dict.get(kw.item_id)
        camp = campaign_dict.get(kw.campaign_id)
        adg = adg_dict.get(kw.adgroup_id, None)
        if not (camp and adg):
            continue

        kw_mnt_opt_type = 2 # 默认是不托管
        if adg.mnt_type != 0:
            kw_mnt_opt_type = kw.mnt_opt_type or 0

        temp_kw = {
            "keyword_id": kw.keyword_id,
            "adgroup_id": kw.adgroup_id,
            "campaign_id": kw.campaign_id,
            "mnt_opt_type": kw_mnt_opt_type,

            "word": kw.word,
            "create_days": kw.create_days,
            "max_price": format(kw.max_price / 100.0, '.2f'),
            "new_price": format(kw.new_price / 100.0, '.2f'),
            "qscore": kw.qscore,
            "qscore_dict": kw.qscore_dict or {'qscore': 0},

            "cpm": format(kw.rpt.cpm / 100.0, '.2f'),
            "avgpos": kw.rpt.avgpos,
            "favctr": format(kw.rpt.favctr, '.2f'),
            "favpay": format(kw.rpt.favpay, '.2f'),

            "g_click": kw.g_click,
            "g_ctr": '%.2f' % kw.g_ctr,
            "g_cpc": kw.g_cpc,
            "g_competition": kw.g_competition,
            "g_pv": kw.g_pv,
            "g_coverage": kw.g_coverage,
            "g_roi": kw.g_roi,
            "g_paycount": kw.g_paycount,
            "match_scope": kw.match_scope,

            "platform":kw.locker.platform,
            "exp_rank_start":kw.locker.exp_rank_range[0],
            "exp_rank_end":kw.locker.exp_rank_range[1],
            "limit_price":format(kw.locker.limit_price / 100.0, '.2f'),

            "title":kw.item[0],
            "price":format(kw.item[1] / 100.0, '.2f'),
            "pic_url":kw.item[2],

            "camp_title":camp.title,
            "max_mobile_price": format(kw.get_mobile_price(adg, camp) / 100.0, '.2f')
        }
        rank_key = 'pc_rank' if temp_kw['platform'] == 'pc' else 'mobile_rank'
        temp_kw.update({
            'exp_rank_start_desc': Keyword.KW_RT_RANK_MAP[rank_key][str(temp_kw['exp_rank_start'])],
            'exp_rank_end_desc': Keyword.KW_RT_RANK_MAP[rank_key][str(temp_kw['exp_rank_end'])],
        })
        temp_kw.update(kw.rpt.to_dict())
        result_list.append(temp_kw)

    custom_column = Account.get_custom_col(shop_id)
    return {'keyword_list': result_list, 'custom_column': custom_column, 'errMsg': errMsg}

def manual_rob_rank(request):
    """手动抢排名"""
    limitError = ""
    shop_id = int(request.user.shop_id)

    try:
        keyword_id = int(request.POST['keyword_id'])
        adgroup_id = int(request.POST['adgroup_id'])
        exp_rank_start = int(request.POST['exp_rank_start'])
        exp_rank_end = int(request.POST['exp_rank_end'])
        limit_price = int(request.POST['limit_price'])
        platform = request.POST['platform']
        nearly_success = int(request.POST['nearly_success'])

        keyowrd_list = Keyword.objects.filter(shop_id = shop_id, keyword_id = keyword_id)
        if keyowrd_list:
            kw_cfg_list = []
            upd_kw_list = []
            for kw in keyowrd_list:
                kw_cfg_list.append({'word': kw.word, 'keyword_id': kw.keyword_id, 'exp_rank_range': [exp_rank_start, exp_rank_end], 'limit_price': limit_price, 'platform': platform, 'nearly_success': nearly_success})
                upd_kw_list.append([kw.campaign_id, kw.adgroup_id, kw.keyword_id, kw.word, kw.max_price, None, kw.max_price])
            limitError = CustomRobRank.execute(user = request.user, adgroup_id = adgroup_id, kw_cfg_list = kw_cfg_list)
        else:
            limitError = "others"
    except Exception, e:
        log.error('manual_rob_rank error shop_id=%s e=%s request=%s' % (shop_id, request.POST, e))
        limitError = "others"
    return {"errMsg":"", "limitError":limitError}

def auto_rob_rank(request):
    """自动抢排名"""
    limitError = ""
    keyword_id = int(request.POST['keyword_id'])
    exp_rank_start = int(request.POST['exp_rank_start'])
    exp_rank_end = int(request.POST['exp_rank_end'])
    limit_price = int(request.POST['limit_price'])
    platform = request.POST['platform']
    start_time = request.POST['start_time']
    end_time = request.POST['end_time']
    nearly_success = int(request.POST['nearly_success'])

    limitError = RobRankMng.create_auto_robrank(user = request.user, keyword_id = keyword_id, exp_rank_range = [exp_rank_start, exp_rank_end],
                                                limit_price = limit_price, platform = platform, start_time = start_time, end_time = end_time, nearly_success = nearly_success)
    return {"errMsg":'', "limitError":limitError}

def rob_cancle(request):
    """取消自动抢排名"""
    errMsg = ""
    shop_id = int(request.user.shop_id)
    keyword_id = int(request.POST['keyword_id'])
    RobRankMng.consel_auto_robrank(shop_id, keyword_id)
    return {"errMsg":errMsg}

def rob_config(request):
    """获取抢排名配置"""
    errMsg, data = "", {}
    shop_id = int(request.user.shop_id)
    keyword_id = int(request.POST['keyword_id'])
    keyword_locker_list = KeywordLocker.objects.filter(shop_id = shop_id, keyword_id = keyword_id)
    if keyword_locker_list:
        keyword_locker = keyword_locker_list[0]
        data['platform'] = keyword_locker.platform
        rank_key = 'pc_rank' if data['platform'] == 'pc' else 'mobile_rank'
        data['rank_start'] = keyword_locker.exp_rank_range[0]
        data['rank_start_desc'] = Keyword.KW_RT_RANK_MAP[rank_key][str(data['rank_start'])]
        data['rank_end'] = keyword_locker.exp_rank_range[1]
        data['rank_end_desc'] = Keyword.KW_RT_RANK_MAP[rank_key][str(data['rank_end'])]
        data['limit'] = keyword_locker.limit_price
        data['nearly_success'] = keyword_locker.nearly_success
        data['start_time'] = keyword_locker.start_time
        data['end_time'] = keyword_locker.end_time
    return {"errMsg": errMsg,
            'data': data,
            'rank_start_desc_map': Keyword.RANK_START_DESC_REV_MAP if request.POST.get('login_from') == 'qnyd' else Keyword.RANK_START_DESC_MAP,
            'rank_end_desc_map': Keyword.RANK_END_DESC_REV_MAP if request.POST.get('login_from') == 'qnyd' else Keyword.RANK_END_DESC_MAP
            }

def rob_record(request):
    """获取抢排名记录"""
    errMsg, data = '', {}
    keyword_id = int(request.POST['keyword_id'])
    data = MessageChannel.get_history([keyword_id])
    result_data = {}
    for k, record_list in data.iteritems():
        temp_list = []
        for r_str in record_list:
            r_dict = json.loads(r_str)
            try:
                r_dict['exp_rank_range'][0] = Keyword.RANK_START_DESC_MAP[r_dict['platform']][str(r_dict['exp_rank_range'][0])]
                r_dict['exp_rank_range'][1] = Keyword.RANK_END_DESC_MAP[r_dict['platform']][str(r_dict['exp_rank_range'][1])]
            except Exception, e:
                r_dict['exp_rank_range'] = ['', '']
                log.error('kw_id=%s, e=%s' % (keyword_id, e))
            temp_list.append(json.dumps(r_dict))
        result_data.update({k: temp_list})

    return {"errMsg":'', 'data': result_data}

# def forecast_rt_rank(request):
#     """查排名"""
#     adg_id = int(request.POST['adgroup_id'])
#     keyword_id = int(request.POST['keyword_id'])
#     price = round(float(request.POST.get('price', 0)), 2)
#     times = 0
#     tapi = get_tapi(request.user)
#     while times < 2:
#         result_data = Keyword.get_rt_kw_rank(tapi = tapi, adg_id = adg_id, price = int(price * 100), kw_id = keyword_id)
#         if 'pc_rank' in result_data and 'mobile_rank' in result_data:
#             break
#         times = times + 1
#     # 如果还为空给个默认值
#     if not ('pc_rank' in result_data and 'mobile_rank' in result_data):
#         result_data['pc_rank'] = ">100"
#         result_data['mobile_rank'] = ">100"
#
#     return {'data': result_data, 'errMsg': ''}

def forecast_rt_rank(request):
    """查排名"""
    adg_id = int(request.POST['adgroup_id'])
    keyword_id = int(request.POST['keyword_id'])
    tapi = get_tapi(request.user)
    result_data = Keyword.batch_get_rt_kw_rank(tapi = tapi, nick = request.user.nick, adg_id = adg_id, kw_id_list = [keyword_id]).get(str(keyword_id), {})
    return {'data': result_data, 'errMsg': ''}

def keyword_attr(request):
    """获取关键词出价"""
    errMsg, data = "", {}
    shop_id = int(request.user.shop_id)
    kw_id_list = request.POST.getlist('kw_id_list[]', [])
    attr_list = request.POST.getlist('attr_list[]', [])
    if attr_list and kw_id_list:
        keyword_list = list(Keyword.objects.filter(shop_id = shop_id, keyword_id__in = kw_id_list))

        for kw in keyword_list:
            data[kw.id] = {}
            for attr in attr_list:
                if attr in ['max_price']:
                    data[kw.id][attr] = getattr(kw, attr, None)
    return {'data': data, 'errMsg': errMsg}

# def batch_forecast_rt_rank(request):
#     """批量查排名"""
#     adg_id = int(request.POST['adgroup_id'])
#     keyword_id_list = request.POST.getlist('keyword_list[]')
#     price = round(float(request.POST.get('price', 0)), 2)
#
#     result_data = {}
#     tapi = get_tapi(request.user)
#
#     for keyword_id in keyword_id_list:
#         rank = Keyword.get_rt_kw_rank(tapi = tapi, adg_id = adg_id, price = int(price * 100), kw_id = int(keyword_id))
#
#         if not ('pc_rank' in rank and 'mobile_rank' in rank):
#             rank['pc_rank'] = ">100"
#             rank['mobile_rank'] = ">100"
#
#         result_data[keyword_id] = rank
#
#     return {'data': result_data, 'errMsg': ''}

def batch_forecast_rt_rank(request):
    """批量查排名"""
    adg_id = int(request.POST['adgroup_id'])
    keyword_id_list = request.POST.getlist('keyword_list[]')
    tapi = get_tapi(request.user)
    result_data = Keyword.batch_get_rt_kw_rank(tapi = tapi, nick = request.user.nick, adg_id = adg_id, kw_id_list = keyword_id_list)
    return {'data': result_data, 'errMsg': ''}

def calc_shop_core(request):
    """
        计算店铺核心词
    :param request:
    :return:
    """
    shop_id = int(request.user.shop_id)
    ck, _ = CoreKeyword.objects.get_or_create(shop_id = shop_id, defaults = {'kw_dict_list': [], 'update_time': None})
    condition = "ok"
    if ck.status:
        condition = "doing"
    else:
        if time_is_recent(ck.update_time, days = 7):
            if not time_is_someday(ck.report_sync_time): # 如果当天也已经同步过报表了，则不再去同步
                Thread(target = ck.sync_current_report).start()
                condition = "ok"
            if ck.status:
                condition = "doing"
        else:
            Thread(target = ck.calc_top_keywords).start()
            condition = "doing"
    refresh_time = ck.update_time
    return {'errMsg': '', 'condition': condition, 'refresh_time': refresh_time}

def shop_core_list(request):
    """
            店铺核心词列表
            千牛端没有地方设置核心词，需要根据实时流量计算出一批核心词
    """
    return web_shop_core_list(request)

def submit_keyword(request):
    """提交关键词修改"""
    shop_id = int(request.user.shop_id)
    kw_list = json.loads(request.POST.get('submit_list', ''))
    opter, opter_name = analysis_web_opter(request)
    updated_id_list, _, _, failed_id_list = update_kws_8shopid(shop_id, kw_list, opter = opter, opter_name = opter_name)
    return {'update_kw':updated_id_list, 'failed_kw':failed_id_list, 'errMsg':''}

def add_suggest(request):
    '''保存用户反馈信息'''
    content = request.POST.get('suggest')
    error_msg = ''
    try:
        consult_id = Customer.objects.get(shop_id = request.user.shop_id).consult_id
        fobj = Feedback(shop_id = request.user.shop_id, score_str = '[]', content = content, consult_id = consult_id, handle_status = -1)
        fobj.save()
        fobj.send_email()
    except Exception, e:
        error_msg = '提交失败，请联系客服'
        log.error('e=%s' % e)
    return {'errMsg': error_msg}

def is_data_ready(request):
    '''数据是否准备好'''
    return web_is_data_ready(request)

def submit_userinfo(request):
    '''完善用户手机号'''
    return web_submit_userinfo(request)

def batch_get_rt_kw_rank(request):
    '''强排名模块查排名，调用web端的方法'''
    return web_batch_get_kw_rank(request)
