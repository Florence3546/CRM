# coding=UTF-8
import re
import math
import time
import datetime
import random
import hashlib
from operator import itemgetter

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from mongoengine.errors import DoesNotExist

from dajax.core import Dajax
from apilib import get_tapi
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import time_humanize, time_is_someday, date_2datetime, datetime_2string
from apps.common.utils.utils_number import format_division, clean_to_number , round_digit
from apps.common.utils.utils_string import get_char_num
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_misc import get_custom_attr
from apps.common.constant import Const
from apps.common.cachekey import CacheKey
from apps.common.models import Config

from apps.common.biz_utils.utils_tapitools import get_kw_g_data
from apps.common.biz_utils.utils_misc import (del_cache_progress, get_cache_progress,
                                              analysis_web_opter, get_page_value_by_order, get_ip_for_rank)

from apps.ncrm.models import Customer
from apps.ncrm.utils import pagination_tool

from apps.subway.models import (Account, Campaign, camp_coll, Creative, Adgroup, adg_coll, Keyword,
                                crt_coll, Item, item_coll, kw_coll, Attention, attn_coll, CustomCreative,
                                ccrt_coll)
from apps.subway.download import Downloader
from apps.subway.models_upload import UploadRecord, uprcd_coll
from apps.subway.upload import (update_campaign, update_adgroups, delete_adgroups, add_keywords,
                                update_item_title, add_adgroups, update_creative, add_creative, delete_creative ,
                                set_camp_bword_log, set_prod_word_log, update_adg_mobdisct_log,
                                change_adg_maxprice_log, set_adg_bword_log, modify_cmp_adg_log)
from apps.subway.models_keyword import Qscore

from apps.router.models import User, Agent
from apps.crm.models_psmsg import PsMessage
from apps.mnt.models import MntCampaign, MntTaskMng
from apps.engine.models import ShopMngTask, TitleTransfer

from apps.kwslt.keyword_selector import KeywordSelector

from apps.web.utils import (bulk_del_blackword, update_kws_8shopid, get_duplicate_word, get_garbage_words,
                            get_dupl_word_info, filter_dupl_words, get_trend_chart_data, delete_keywords)
from apps.web.models import (HotZone, Feedback, Template_statistics, AppComment)
from apps.web.point import Sign, PerfectInfo, Gift, Virtual
from apps.subway.realtime_report import RealtimeReport

from apps.kwslt.analyzer import ChSegement
from apps.kwslt.models_cat import Cat

from apps.alg.interface import bulk_optimize_4adgroup


def route_dajax(request):
    '''dajax路由函数'''
    dajax = Dajax()
    if not request.user.is_authenticated():
        dajax.script("alert('您已经退出，请重新登录之后再试');")
        return dajax
    auto_hide = int(request.POST.get('auto_hide', 1))
    if auto_hide:
        dajax.script("PT.hide_loading();")
    function_name = request.POST.get('function')
    try:
        if function_name and globals().get(function_name, ''):
            dajax = globals()[function_name](request = request, dajax = dajax)
        else:
            dajax = log.exception("route_dajax: function_name Does not exist")
    except Exception, e:
        log.exception("route_dajax error, shop_id=%s, e=%s ,function_name=%s" % (request.user.shop_id, e, str(function_name)))
    return dajax

def is_data_ready(request, dajax):
    if not request.user.is_authenticated():
        dajax.script('window.location.href="%s";' % (settings.WEB_AUTH_URL)) # TODO: zhangyu 20140411 千牛用户跳转到了Web，需要跳转到一个公共的地方
        return dajax

    smt = ShopMngTask.objects.get(shop_id = request.user.shop_id)
    if not smt.status == 2:
        del_cache_progress(request.user.shop_id)
        dajax.script('set_progress({"redicrect":""})')
    else:
        ststus_dict = { 'struct_account_downing':['struct', 1, '正在下载账户报表数据'], 'struct_account_finished':['struct', 2, '账户报表下载完成'],
                        'struct_campaign_downing':['struct', 3, '正在下载计划结构数据'], 'struct_campaign_finished':['struct', 5, '计划结构数据下载完成'],
                        'struct_adgroup_downing':['struct', 7, '正在下载推广组结构数据'], 'struct_adgroup_finished':['struct', 15, '推广结构组数据下载完成'],
                        'struct_creative_downing':['struct', 20, '正在下载创意结构数据'], 'struct_creative_finished':['struct', 40, '创意结构数据下载完成'],
                        'struct_keyword_downing':['struct', 45, '正在下载关键词，数据较多，时间可能较长'], 'struct_keyword_finished':['struct', 80, '关键结构词数据下载完成'],
                        'struct_item_downing':['struct', 85, '正在下载宝贝结构数据'], 'struct_item_finished':['struct', 100, '宝贝结构数据下载完成'],
                        'report_account_downing':['report', 1, '正在下载账户报表数据'], 'report_account_finished':['report', 10, '账户报表下载完成'],
                        'report_campaign_downing':['report', 23, '正在下载计划报表数据'], 'report_campaign_finished':['report', 30, '计划报表下载完成'],
                        'report_adgroup_downing':['report', 35, '正在下载推广组报表数据'], 'report_adgroup_finished':['report', 100, '推广组报表下载完成'],
                        }

        key = get_cache_progress(request.user.shop_id)
        if key and ststus_dict.has_key(key):
            pclass, progress, msg = ststus_dict[key]
            progress = pclass == 'struct' and int(progress * 0.8) + 1 or int(progress * 0.2 + 80) + 1 # 向上取整
            dajax.script('set_progress(%s)' % (json.dumps({'progress':progress, 'msg':msg})))
    return dajax

def sync_data(request, dajax):
    """
    1. check click cache, is exists--(true)-->delete click cache, force download.
                            |--(false)-->set click cache, auto download.
    2. download use mutual cache to ensure one shop download once in the same time.
    """
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

    result, reason = download_data(shop_id = shop_id, is_force = is_force, rpt_days = 30)
    if result:
        dajax.script("PT.alert('数据同步成功！');")
        return dajax
    else:
        if str(reason) in ['dl_struct_failed', 'dl_rpt_failed']:
            msg = '同步数据失败，请刷新重试！'
        elif str(reason) == 'doing':
            msg = '数据正在同步中，请稍等！'
        else:
            msg = '同步数据失败，请联系顾问！'
        dajax.script("PT.alert('%s');" % msg)
        return dajax

def sync_increase_data(request, dajax):
    '''用户手动触发本店铺的增量下载'''
    try:
        shop_id = int(request.user.shop_id)
        result = Downloader.download_all_struct(shop_id = shop_id) and Downloader.download_all_rpt(shop_id = shop_id, detail_flag = False)
        msg = result and '同步直通车后台修改的数据成功。' or '后台正在增量下载结构或报表数据，请等5分钟左右，再刷新页面检查数据是否正常。'
    except Exception, e:
        log.exception("sync_increase_data by user error, shop_id=%s, e=%s" % (shop_id, e))
        msg = '同步直通车增量数据发生后台错误，请联系顾问。'
    finally:
        dajax.script("PT.Base.sync_result('%s')" % msg)

    return dajax

def sync_current_adg(request, dajax):
    '''手动触发当前宝贝的关键词、创意结构或报表数据下载'''
    try:
        # 建议使用缓存用于下载互斥，防止同一时间多个线程一起下载
        shop_id = int(request.user.shop_id)
        adg_id = int(request.POST['adg_id'])
        camp_id = int(request.POST['camp_id'])
        rpt_days = int(request.POST['rpt_days'])

        # 同步关键词结构数据
        dler, _ = Downloader.objects.get_or_create(shop_id = shop_id)

        dler.sync_all_struct()

        struct_result = Keyword.struct_download_byadgs(shop_id = shop_id, adg_id_list = [adg_id], tapi = dler.tapi)

        # 同步关键词报表数据和创意
        dl_args = {'shop_id':shop_id, 'tapi':dler.tapi, 'token':dler.token, 'adg_tuple_list':[(adg_id, camp_id, datetime.datetime.now() - datetime.timedelta(days = rpt_days))]}

        crtrpt_result, _ = Creative.download_crtrpt_byadgs(**dl_args)
        kwrpt_result, _ = Keyword.download_kwrpt_byadgs(**dl_args)
        msg = (crtrpt_result and kwrpt_result and struct_result) and "同步数据成功。" or "同步数据失败。"
    except Exception, e:
        log.exception("sync_current_adgroup by user error, shop_id=%s, adgroup_id=%s, e=%s" % (shop_id, adg_id, e))
        msg = '同步宝贝的关键词数据发生后台错误，请联系顾问。'
    try:
        # 同步关键词质量得分
        Adgroup.objects.get(shop_id = shop_id, adgroup_id = adg_id).sync_qscore(update_flag = True)
        # Adgroup.objects.get(shop_id = shop_id, adgroup_id = adg_id).refresh_qscore()
    except Exception, e:
        log.error('web_sync_current_adg`s qscore by user error, shop_id=%s, adgroup_id=%s, e=%s' % (shop_id, adg_id, e))

    dajax.script("PT.Base_adg.sync_adg_back('%s')" % (msg))
    return dajax

def sync_all_data(request, dajax):
    '''手动触发店铺级别的结构或报表数据下载 TODO zhangyu 20130424 建议该处下载添加用户行为分析(需要在行为表中加字段)'''
    shop_id = int(request.user.shop_id)
    data_type = int(request.POST['data_type'])

    try:
        if data_type == 1: # 下载直通车报表(不包含关键词报表)
            rpt_days = int(request.POST['rpt_days'])
            result = Downloader.download_all_rpt(shop_id = shop_id, detail_flag = False, is_force = True, rpt_days = rpt_days)
            msg = result and "下载%s天报表数据成功。" % rpt_days or "后台正在下载报表数据，请等5分钟左右，再刷新页面检查数据是否正常。"
        elif data_type == 2: # 下载直通车所有结构
            result = Downloader.download_all_struct(shop_id = shop_id, is_force = True)
            msg = result and "重新下载结构数据成功。" or "后台正在下载结构数据，请等5分钟左右，再刷新页面检查数据是否正常。"
        else:
            msg = "提交参数不正确，请重新选择。"
    except Exception, e:
        log.exception("sync_all_data by user error, shop_id=%s, e=%s" % (shop_id, e))
        msg = '同步直通车数据发生后台错误，请联系顾问。'
    finally:
        dajax.script("PT.Base.sync_result('%s')" % msg)

    return dajax

def get_title_traffic_score(request, dajax):
    title = request.POST.get("title")
    title_num = request.POST.get("title_num")
    title_elemword_list = request.POST.getlist("title_elemword_list[]")
    item_id = request.POST.get("item_id")
#     sales = request.POST.get("sales")
    if not(title and title_num and item_id):
        dajax.script('PT.alert("数据获取失败");')
        return dajax
    try:
        item_id = int(item_id)
#         sales = int(sales)
        item = Item.objects.get(shop_id = int(request.user.shop_id), item_id = item_id)
    except:
        dajax.script('PT.alert("数据获取失败");')
        return dajax

    if title_elemword_list:
        kw_list = json.dumps(item.get_kw_list_byelemword(title_elemword_list))
        title_elemword_list = json.dumps([])
    else:
        title_info_dict = item.get_title_info_dict(title)
        kw_list = json.dumps(title_info_dict['kw_list'])
        title_elemword_list = json.dumps(title_info_dict['title_elemword_list'])
    dajax.script('PT.TitleOptimize.show_title_traffic_score("%s", "%s", %s, %s);' % (title, title_num, kw_list, title_elemword_list))
    return dajax

def update_item(request, dajax):
    item_id = int(request.POST.get("item_id"))
    title = request.POST.get("title")
    title_num = request.POST.get("title_num")
    result = update_item_title(shop_id = request.user.shop_id, item_id = item_id, title = title, shop_type = request.user.shop_type)
    if result is True:
        item = Item.objects.get(shop_id = request.user.shop_id, item_id = item_id)
        item.delete_item_cache()
        dajax.script('PT.TitleOptimize.set_current_title("%s", "%s")' % (title, title_num))
    else:
        dajax.script('PT.alert("提交失败，%s");' % result)
    return dajax

def get_campaign_list(request, dajax):
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 0))
    campaign_list = Campaign.objects.filter(shop_id = shop_id)
    camp_rpt_dict = Campaign.Report.get_summed_rpt(query_dict = {'shop_id': shop_id}, rpt_days = last_day)
    mnt_list = MntCampaign.objects.only('campaign_id', 'mnt_type').filter(shop_id = shop_id)
    mnt_dict = {mnt.campaign_id:(mnt.mnt_type, mnt.get_mnt_type_display()) for mnt in mnt_list}
    adg_num_dict = Adgroup.get_adgroup_count(shop_id = shop_id)
    json_campaign_list = []
    init_mnt_list = (0, '')
    temp_rtrpt_dict = {}
    is_rt_camp = 0

    # if last_day == 0: #如果下拉框选择的是实时数据
    temp_rtrpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'campaign', args_list = [request.user.shop_id])
    if temp_rtrpt_dict:
        is_rt_camp = 1

    for camp in campaign_list:
        mnt_info = mnt_dict.get(camp.campaign_id, init_mnt_list)
        mnt_type, mnt_name = mnt_info
        temp_adg_num_tuple = adg_num_dict.get(camp.campaign_id, (0, 0, 0))
        rt_cost = rt_impression = rt_click = rt_ctr = rt_cpc = rt_transactiontotal = rt_transactionshippingtotal = rt_favtotal = rt_coverage = rt_roi = 0
        rt_directtransaction = rt_indirecttransaction = rt_directtransactionshipping = rt_indirecttransactionshipping = rt_favshoptotal = rt_favitemtotal = 0
        rt_limit_price = 0
        rt_date = ''

        tmp_rpt = camp_rpt_dict.get(camp.campaign_id, Campaign.Report())

        json_campaign_list.append({'campaign_id':camp.campaign_id, 'title':camp.title, 'budget':'%.0f' % (camp.budget / 100.0), 'online_status':camp.online_status, 'comment_count':camp.comment_count,
                                   'error_descr':camp.error_descr, 'is_smooth':camp.is_smooth and 1 or 0, 'total_cost':'%.2f' % (tmp_rpt.cost / 100.0),
                                   'impr':tmp_rpt.impressions, 'click':tmp_rpt.click, 'click_rate':'%.2f' % tmp_rpt.ctr, 'ppc':'%.2f' % (tmp_rpt.cpc / 100.0),
                                   'total_pay':'%.2f' % (tmp_rpt.pay / 100.0), 'paycount':tmp_rpt.paycount, 'favcount':tmp_rpt.favcount,
                                   'conv':'%.2f' % (tmp_rpt.conv), 'roi':'%.2f' % tmp_rpt.roi, 'adg_num':temp_adg_num_tuple[0],
                                   'directpay':'%.2f' % (tmp_rpt.directpay / 100.0), 'indirectpay':'%.2f' % (tmp_rpt.indirectpay / 100.0), 'directpaycount':tmp_rpt.directpaycount, 'indirectpaycount':tmp_rpt.indirectpaycount,
                                   'favshopcount':tmp_rpt.favshopcount, 'favitemcount':tmp_rpt.favitemcount, 'mnt_name':mnt_name, 'mnt_type':mnt_type,
                                   'rt_cost':'%.2f' % (rt_cost / 100.0), 'rt_impression':rt_impression, 'rt_click':rt_click, 'rt_ctr':'%.2f' % (rt_ctr * 100),
                                   'rt_cpc':'%.2f' % (rt_cpc / 100.0), 'rt_transactiontotal':'%.2f' % (rt_transactiontotal / 100.0), 'rt_transactionshippingtotal':rt_transactionshippingtotal,
                                   'rt_favtotal':rt_favtotal, 'rt_coverage':'%.2f' % (rt_coverage * 100), 'rt_roi':'%.2f' % rt_roi,
                                   'rt_directtransaction':'%.2f' % (rt_directtransaction / 100.0) , 'rt_indirecttransaction':'%.2f' % (rt_indirecttransaction / 100.0) , 'rt_directtransactionshipping':rt_directtransactionshipping,
                                   'rt_indirecttransactionshipping':rt_indirecttransactionshipping, 'rt_favshoptotal':rt_favshoptotal, 'rt_favitemtotal':rt_favitemtotal,
                                   'rt_limit_price':'%.2f' % rt_limit_price, 'rt_date': rt_date
                                   })

    dajax.script('PT.Campaign_list.append_table_data(%s, %s, %s)' % (json.dumps(json_campaign_list), last_day, is_rt_camp))
    return dajax

def set_camp_limit_price(request, dajax):
    '''设置计划限价 '''
    result = json_result_data = error_msg = ''
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    limit_price = float(request.POST['limit_price'])
    flag = int(request.POST['flag'])
    now = datetime.datetime.now()
    if flag == 1:
        result = camp_coll.update({'_id':int(camp_id) , 'shop_id':shop_id}, {'$set':{'rt_limit_price':round_digit(limit_price * 100), 'rt_date': now}})
    elif flag == 0:
        result = camp_coll.update({'_id':int(camp_id) , 'shop_id':shop_id}, {'$unset':{'rt_limit_price':1, 'rt_date': 1}})
    if result['ok'] and result['updatedExisting']:
        json_result_data = {'status':1, 'camp_id':camp_id, 'limit_price':limit_price , 'rt_date': now, 'flag':flag}
    else:
        json_result_data = {'status':0, 'err':'<br/>'.join(result)}
        log.info('set_camp_limit_price error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, camp_id, '<br/>'.join(result)))
    dajax.script("PT.Campaign_list.set_camp_limit_price_call_back(%s)" % (json.dumps(json_result_data)))
    return dajax

def update_camps_status(request, dajax):
    shop_id = int(request.user.shop_id)
    camp_id_list = request.POST.getlist('camp_id_list[]')
    mode = int(request.POST['mode'])
    name_space = request.POST['name_space']
    online_status = mode and 'online' or 'offline'
    opter, opter_name = analysis_web_opter(request)
    success_camp_ids, failed_camp_ids = [], []
    for camp_id in camp_id_list:
        result_list, _ = update_campaign(shop_id = shop_id, campaign_id = camp_id, online_status = online_status, opter = opter, opter_name = opter_name)
        if 'online_status' in result_list:
            success_camp_ids.append(str(camp_id))
        else:
            failed_camp_ids.append(str(camp_id))

    dajax.script("PT.%s.update_status_back(%s,%s)" % (name_space, mode, success_camp_ids))
    return dajax

def modify_camp_title(request, dajax):
    """设置计划名称"""
    shop_id = request.user.shop_id
    new_title = request.POST['new_title']
    campaign_id = int(request.POST['camp_id'])
    opter, opter_name = analysis_web_opter(request)
    # 判断计划名称长度
    if get_char_num(new_title) > 20:
        dajax.script("PT._alert('计划名称不能超过20个字');")
        return dajax

    # 修改名称
    result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = campaign_id, title = new_title, opter = opter, opter_name = opter_name)
    if 'title' in result_list:
        json_result_data = {'status':1, 'camp_id':campaign_id, 'new_title':new_title}
    else:
        json_result_data = {'status':0, 'err':'<br/>'.join(msg_list)}
        log.info('modify_camp_title error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, '<br/>'.join(msg_list)))
    dajax.script("PT.Campaign_list.modify_title_call_back(%s)" % (json.dumps(json_result_data)))
    return dajax

def modify_camp_budget(request, dajax):
    budget = int(request.POST['budget'])
    campaign_id = int(request.POST['camp_id'])
    use_smooth = request.POST['use_smooth']
    shop_id = int(request.user.shop_id)
    opter, opter_name = analysis_web_opter(request)
    result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = campaign_id, budget = budget, use_smooth = use_smooth, opter = opter, opter_name = opter_name)
    if 'budget' in result_list:
        json_result_data = {'status':1, 'camp_id':campaign_id, 'budget':budget, 'use_smooth':use_smooth}
    else:
        json_result_data = {'status':0, 'err':'<br/>'.join(msg_list)}
        log.info('modify_camp_budget error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, '<br/>'.join(msg_list)))

    dajax.script("PT.Campaign_list.modify_budget_call_back(%s)" % (json.dumps(json_result_data)))
    return dajax

def show_camp_trend(request, dajax):
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    snap_dict = Campaign.Report.get_snap_list({'shop_id': shop_id, 'campaign_id': camp_id}, rpt_days = 15)
    snap_list = snap_dict.get(camp_id, [])
    if snap_list:
        category_list, series_cfg_list = get_trend_chart_data(data_type = 2, rpt_list = snap_list)
        scripts = "PT.Campaign_list.show_camp_trend(%s,%s,%s)" % (camp_id, json.dumps(category_list), json.dumps(series_cfg_list))
    else:
        scripts = "PT.alert('没有趋势数据，请确认计划是否参与推广');"
    dajax.script(scripts)
    return dajax

def get_camp_platform(request, dajax):
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    camp = Campaign.objects.get(shop_id = shop_id, campaign_id = camp_id)
    dajax.script("PT.Platform.get_platform_back(%s, %s)" % (camp_id, json.dumps(camp.platform)))
    return dajax

def update_camp_platform(request, dajax):
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    platform_dict = json.loads(request.POST.get('platform_dict', ''))
    pt_dict = Campaign.fromat_platform(platform_dict)
    opter, opter_name = analysis_web_opter(request)
    result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = camp_id, opter = opter, opter_name = opter_name, **pt_dict)
    is_success = result_list and 1 or 0
    CacheAdpter.delete(CacheKey.WEB_CAMPAIGN_PLATFORM % camp_id, 'web')
    dajax.script("PT.Platform.update_platform_back(%s, %s, %s)" % (camp_id, is_success, json.dumps(msg_list)))
    return dajax

def get_camp_area(request, dajax):
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    camp = Campaign.objects.get(shop_id = shop_id, campaign_id = camp_id)
    area_str = camp.area
    dajax.script("PT.Area.get_area_back(%s, '%s')" % (camp_id, area_str))
    return dajax

def update_camp_area(request, dajax):
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    area_ids = request.POST.get('area_ids')
    opter, opter_name = analysis_web_opter(request)
    result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = camp_id, area = area_ids, opter = opter, opter_name = opter_name)
    is_success = result_list and 1 or 0
    dajax.script("PT.Area.update_area_back(%s, %s, %s)" % (camp_id, is_success, json.dumps(msg_list)))
    return dajax

def get_camp_schedule(request, dajax):
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    camp = Campaign.objects.get(shop_id = shop_id, campaign_id = camp_id)
    schedule_str = camp.schedule
    dajax.script("PT.Schedule.get_schedule_back(%s, '%s')" % (camp_id, schedule_str))
    return dajax

def update_camp_schedule(request, dajax):
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    schedule_str = request.POST.get('schedule_str', '')
    result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = camp_id, schedule = schedule_str)
    is_success = result_list and 1 or 0
    dajax.script("PT.Schedule.update_schedule_back(%s, %s)" % (is_success, json.dumps(msg_list)))
    return dajax

def show_creative_trend(request, dajax):
    shop_id = int(request.user.shop_id)
    creative_id = int(request.POST['creative_id'])
    creative = Creative.objects.filter(shop_id = shop_id, creative_id = creative_id)[0]
    creative.rpt_days = 7
    if creative.snap_list:
        category_list, series_cfg_list = get_trend_chart_data(data_type = 3, rpt_list = creative.snap_list)
        scripts = "PT.ImageOptimoze.show_creative_trend(%s,%s,%s)" % (creative_id, json.dumps(category_list), json.dumps(series_cfg_list))
    else:
        scripts = "PT.alert('没有趋势数据');"
    dajax.script(scripts)
    return dajax

def show_kw_trend(request, dajax):
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    keyword_id = int(request.POST['keyword_id'])
    keyword = Keyword.objects.get(shop_id = shop_id, adgroup_id = adgroup_id, keyword_id = keyword_id)
    keyword.rpt_days = 7
    if keyword.rpt_list:
        category_list, series_cfg_list = get_trend_chart_data(data_type = 4, rpt_list = keyword.snap_list)
        scripts = "PT.instance_table.show_trend(%s,%s,%s)" % (keyword_id, json.dumps(category_list), json.dumps(series_cfg_list))
    else:
        scripts = "PT.alert('没有趋势数据，请确认是否是新加词，否则请同步数据');"
    dajax.script(scripts)
    return dajax

def get_camp_history(request, dajax):
    shop_id = int(request.user.shop_id)
    page_info = json.loads(request.POST.get('page_info', '{}'))
    page_size = page_info['iDisplayLength']
    page_offset = page_info['iDisplayStart']

    result_list = []
    expire_date = date_2datetime(datetime.date.today() - datetime.timedelta(days = 30))
    condition_dict = {'shop_id':shop_id, 'op_type': {'$lt': 4}, 'opt_time':{'$gte':expire_date}}
    page_info['iTotalRecords'] = page_info['iTotalDisplayRecords'] = uprcd_coll.find(condition_dict).count()
    camp_cur = camp_coll.find({'shop_id': shop_id}, {'title': 1})
    camp_dict = {camp['_id']: camp['title'] for camp in camp_cur}
    uprcd_cur = uprcd_coll.find(condition_dict).sort([('opt_time', -1)]).skip(page_offset).limit(page_size)
    for rcd in uprcd_cur:
        try:
            opt_time = rcd['opt_time'].strftime("%Y-%m-%d %H:%M:%S")
            opter = UploadRecord.get_choices_text(UploadRecord.OPERATOR_CHOICES, rcd['opter'])
            op_type = int(rcd['op_type'])
            op_type_text = UploadRecord.get_choices_text(UploadRecord.OP_TYPE_CHOICES, op_type)
            data_type = UploadRecord.get_choices_text(UploadRecord.DATA_TYPE_CHOICES, rcd['data_type'])
            detail_list = []
            camp_title = camp_dict.get(rcd['campaign_id'], rcd['campaign_id'])
            if 'detail_list' in rcd and rcd['detail_list']:
                for detail in rcd['detail_list'][:1]:
                    if op_type == 1:
                        detail_list.append('%s' % (detail))
                    else:
                        detail_list.append('宝贝"%s",%s' % (rcd['item_name'], detail))
            result_list.append({'oper_time':opt_time, 'opter':opter, 'oper_type':op_type_text,
                                'data_type':data_type, 'camp_title':camp_title, 'detail':detail_list[0]})
        except Exception:
            continue

    dajax.script("PT.Camp_history.append_table_data(%s,%s);" % (json.dumps(page_info), json.dumps(result_list)))
    return dajax


def get_all_history(request, dajax):
    shop_id = int(request.user.shop_id)
    page_info = json.loads(request.POST.get('page_info', '{}'))
    page = page_info['sEcho']
    page_size = page_info['iDisplayLength']
    page_offset = page_info['iDisplayStart']

    camp_id = 0
    opter = 1
    op_type = 0
    days = 7
    search_word = page_info['sSearch']

    expire_date = date_2datetime(datetime.date.today() - datetime.timedelta(days = days))
    condition_dict = {'shop_id':shop_id, 'opt_time':{'$gte':expire_date}}

    if camp_id and camp_id > 0:
        condition_dict['campaign_id'] = camp_id
    if opter and opter > 0:
        condition_dict['opter'] = opter
    if op_type and op_type > 0:
        condition_dict['op_type'] = op_type
    if search_word:
        condition_dict['detail_list'] = re.compile(search_word)

    record_dict = uprcd_coll.find(condition_dict).sort([('opt_time', -1)]).skip(page_offset).limit(page_size)
    page_info['iTotalRecords'] = page_info['iTotalDisplayRecords'] = uprcd_coll.find(condition_dict).count()

    result_list = []
    for rcd in record_dict:
        try:
            opt_time = rcd['opt_time'].strftime("%Y-%m-%d %H:%M:%S")
            opter = UploadRecord.get_choices_text(UploadRecord.OPERATOR_CHOICES, rcd['opter'])
            op_type = UploadRecord.get_choices_text(UploadRecord.OP_TYPE_CHOICES, rcd['op_type'])
            data_type = UploadRecord.get_choices_text(UploadRecord.DATA_TYPE_CHOICES, rcd['data_type'])
            if 'detail_list' in rcd and rcd['detail_list']:
                for detail in rcd['detail_list']:
                    result_list.append({'oper_time':opt_time, 'opter':opter, 'op_type':op_type,
                                        'data_type':data_type, 'detail':detail})
        except:
            continue
    dajax.script("PT.All_history.append_table_data(%s,%s);" % (json.dumps(page_info), json.dumps(result_list)))
    return dajax

def get_adgroup_list_bak(request, dajax):
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 1))
    campaign_id = int(request.POST.get('campaign_id', 2))
    page_info = json.loads(request.POST.get('page_info', '{}'))
    search_keyword = request.POST.get('sSearch', '')
    # search_type = request.POST.get('search_type', 'all')
    page_size = int(request.POST.get('page_size', 100))
    page_no = int(request.POST.get('page_no', 1))
    # page_type = request.POST.get('page_type', 0)
    offline_type = request.POST.get('offline_type', '0')

    # 如果是全自动计划，计算托管宝贝个数
    mnt_info = {'is_mnt':0, 'mnt_type':0, 'mnt_num':0}

    condition_dict = {'shop_id':shop_id}

    mnt_camps = MntCampaign.objects.filter(shop_id = shop_id)
    mnt_camp_dict = {camp.campaign_id: camp.mnt_type for camp in mnt_camps}

    if campaign_id == 1: # 全部托管计划
        condition_dict['campaign_id'] = {'$in': mnt_camp_dict.keys()}
    elif campaign_id == 2: # 全部未托管计划
        condition_dict['campaign_id'] = {'$nin': mnt_camp_dict.keys()}
    elif campaign_id > 2:
        condition_dict['campaign_id'] = campaign_id
        if campaign_id in mnt_camp_dict:
            mnt_info['is_mnt'] = 1
            mnt_info['mnt_type'] = mnt_camp_dict.get(campaign_id, 0)
            mnt_info['mnt_num'] = Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id, mnt_type = mnt_info['mnt_type']).count()

    # if search_type == 'online':
    #     condition_dict['online_status'] = 'online'
    # elif search_type == 'offline':
    #     condition_dict['online_status'] = 'offline'
    # elif search_type == 'mnt':
    #     condition_dict['mnt_type'] = {'$in':[1, 2]}
    # elif search_type == 'unmnt':
    #     condition_dict['mnt_type'] = {'$in':[0, None]}

    if search_keyword:
        item_list = item_coll.find({'shop_id':shop_id, 'title': {"$regex":search_keyword}})
        item_id_list = [item['_id'] for item in item_list]
        condition_dict['item_id'] = {'$in': item_id_list}

    if offline_type == '1':
        condition_dict['offline_type'] = 'audit_offline'

    # 将分页信息返还给前台
    total_count = adg_coll.find(condition_dict).count()
    page_offset = (page_no - 1) * page_size
    page_count = int(math.ceil(total_count * 1.0 / page_size))
    page_info.update({'page_no':page_no, 'page_count':page_count, 'total_count':total_count})

    adgroup_list = Adgroup.objects.filter(__raw__ = condition_dict).skip(page_offset).limit(page_size).sum_reports(rpt_days = last_day)

    json_adgroup_list = []
    if adgroup_list:
        adgroup_id_list, campaign_id_list, item_id_list, campaign_dict, item_dict = [], [], [], {}, {}

        for adgroup in adgroup_list: # 获取其他查询所必要的条件
            adgroup_id_list.append(adgroup.adgroup_id)
            if adgroup.campaign_id not in campaign_id_list:
                campaign_id_list.append(adgroup.campaign_id)
            if adgroup.item_id not in item_id_list:
                item_id_list.append(adgroup.item_id)

        campaign_list = Campaign.objects.only('title', 'online_status', 'settle_status', 'settle_reason').filter(shop_id = shop_id, campaign_id__in = campaign_id_list)
        item_list = Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list)

        keyword_dict = {}
        # keyword_dict = Keyword.get_keyword_count(shop_id = shop_id, adgroup_id_list = adgroup_id_list) # 获取关键词个数

        # 获取计划名称
        campaign_dict = {camp.campaign_id:(camp.title, camp) for camp in campaign_list}
        # 获取宝贝标题，价格，图片路径
        item_dict = {item.item_id:{'title':item.title, 'price':item.price, 'pic_url':item.pic_url} for item in item_list}

        for adgroup in adgroup_list: # 附加item，campaign，keyword属性，统计报表
            adgroup_id = adgroup.adgroup_id
            item_id = adgroup.item_id
            campaign_id = adgroup.campaign_id
            is_quick_opered = 1 if adgroup.quick_optime and time_is_someday(adgroup.quick_optime) else 0

            if not item_dict.get(item_id):
                item_dict[item_id] = {'title':'该宝贝可能不存在或者下架，请尝试同步数据', 'price':0, 'pic_url':'/site_media/jl/img/no_photo'}
            json_adgroup_list.append({'campaign_id':campaign_id,
                                      'campaign_title':campaign_dict[campaign_id][0],
                                      'error_descr':adgroup.error_descr(campaign_dict[campaign_id][1]),
                                      'camp_mnt_type': mnt_camp_dict.get(campaign_id, 0),
                                      'mnt_opt_type': adgroup.mnt_opt_type,
                                      'item_id':item_id,
                                      'item_title':item_dict[item_id]['title'],
                                      'item_price':format(item_dict[item_id]['price'] / 100.0, '.2f'),
                                      'item_pic_url':item_dict[item_id]['pic_url'],
                                      'comment_count':adgroup.comment_count,
                                      'optm_submit_time':time_humanize(adgroup.optm_submit_time),
                                      'total_cost':format(adgroup.qr.cost / 100.0, '.2f'),
                                      'impr':adgroup.qr.impressions,
                                      'click':adgroup.qr.click,
                                      'click_rate':format_division(adgroup.qr.click, adgroup.qr.impressions),
                                      'ppc':format_division(adgroup.qr.cost, adgroup.qr.click, 0.01),
                                      'total_pay':format(adgroup.qr.pay / 100.0, '.2f'),
                                      'paycount':adgroup.qr.paycount,
                                      'favcount':adgroup.qr.favcount,
                                      'conv':format(adgroup.qr.conv / 1, '.2f'),
                                      'roi':format(adgroup.qr.roi / 1, '.2f'),
                                      'kw_num':keyword_dict.get(adgroup_id, 0),
                                      'online_status':adgroup.online_status,
                                      'offline_type':adgroup.offline_type,
                                      'adgroup_id':int(adgroup.adgroup_id),
                                      'mnt_type':adgroup.mnt_type,
                                      'directpay':format(adgroup.qr.directpay / 100.0, '.2f'),
                                      'indirectpay':format(adgroup.qr.indirectpay / 100.0, '.2f'),
                                      'directpaycount':adgroup.qr.directpaycount,
                                      'indirectpaycount':adgroup.qr.indirectpaycount,
                                      'favshopcount':adgroup.qr.favshopcount,
                                      'favitemcount':adgroup.qr.favitemcount,
                                      'is_quick_opered':is_quick_opered,
                                      'limit_price':format((hasattr(adgroup, 'limit_price') and adgroup.limit_price or 0) / 100.0, '.2f')
                                      })

    dajax.script('PT.Adgroup_list.append_table_data(%s,%s,%s)' % (json.dumps(page_info), json.dumps(json_adgroup_list), json.dumps(mnt_info)))
    return dajax

def get_adgroup_list(request, dajax):
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 1))
    campaign_id = int(request.POST.get('campaign_id', 2))
    page_info = json.loads(request.POST.get('page_info', '{}'))
    search_keyword = request.POST.get('sSearch', '')
    # search_type = request.POST.get('search_type', 'all')
    page_size = int(request.POST.get('page_size', 100))
    page_no = int(request.POST.get('page_no', 1))
    # page_type = request.POST.get('page_type', 0)
    offline_type = request.POST.get('offline_type', '0')
    sort = request.POST.get('sort', None)
    sort_field = ''

    # 处理排序参数
    if sort:
        try:
            sort_field, asc_desc = sort.rsplit('_', 1)
            if asc_desc not in ['-1', '1']:
                raise
        except:
            sort = None
            sort_field = ''
        else:
            sort = [(sort_field.encode('utf8'), int(asc_desc))]
            for field in ['pay', 'cost', 'click', 'impr']:
                if field != sort_field:
                    sort.append((field, -1))

    # 如果是全自动计划，计算托管宝贝个数
    mnt_info = {'is_mnt':0, 'mnt_type':0, 'mnt_num':0}

    condition_dict = {'shop_id':shop_id}

    mnt_camps = MntCampaign.objects.filter(shop_id = shop_id)
    mnt_camp_dict = {camp.campaign_id: camp.mnt_type for camp in mnt_camps}

    if campaign_id == 1: # 全部托管计划
        condition_dict['campaign_id'] = {'$in': mnt_camp_dict.keys()}
    elif campaign_id == 2: # 全部未托管计划
        condition_dict['campaign_id'] = {'$nin': mnt_camp_dict.keys()}
    elif campaign_id > 2:
        condition_dict['campaign_id'] = campaign_id
        if campaign_id in mnt_camp_dict:
            mnt_info['is_mnt'] = 1
            mnt_info['mnt_type'] = mnt_camp_dict.get(campaign_id, 0)
            mnt_info['mnt_num'] = Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id, mnt_type = mnt_info['mnt_type']).count()

    if search_keyword:
        item_list = item_coll.find({'shop_id':shop_id, 'title': {"$regex":search_keyword}})
        item_id_list = [item['_id'] for item in item_list]
        condition_dict['item_id'] = {'$in': item_id_list}

    if offline_type == '1':
        condition_dict['offline_type'] = 'audit_offline'

    adg_cur = adg_coll.find(condition_dict)
    adg_list, adg_id_list = [], []
    for adg in adg_cur:
        adg_list.append(adg)
        adg_id_list.append(adg['_id'])

    rpt_dict = {}
    if adg_id_list:
        rpt_dict = Adgroup.Report.get_summed_rpt(query_dict = {'shop_id': shop_id, 'adgroup_id': {'$in': adg_id_list}}, rpt_days = last_day)

    for adg in adg_list:
        adg['rpt'] = rpt_dict.get(adg['_id'], Adgroup.Report())

    adg_list.sort(key = lambda k: k['rpt'].cost, reverse = True)

    total_count = len(adg_id_list)
    page_count = int(math.ceil(total_count * 1.0 / page_size))
    page_info.update({'page_no':page_no, 'page_count':page_count, 'total_count':total_count})

    adg_list = adg_list[(page_no - 1) * page_size: page_no * page_size]
    result_list = []
    if adg_list:
        del_adg_list = []
        adg_id_list, camp_id_list, item_id_list, campaign_dict, item_dict = [], [], [], {}, {}
        for adg in adg_list:
            adg_id_list.append(adg['_id'])
            camp_id_list.append(adg['campaign_id'])
            item_id_list.append(adg['item_id'])

        campaign_list = Campaign.objects.filter(shop_id = shop_id, campaign_id__in = list(set(camp_id_list)))
        item_list = Item.objects.filter(shop_id = shop_id, item_id__in = list(set(item_id_list)))

        keyword_dict = {}
        # keyword_dict = Keyword.get_keyword_count(shop_id = shop_id, adgroup_id_list = adg_id_list) # 获取关键词个数

        # 获取计划名称
        campaign_dict = {camp.campaign_id:(camp.title, camp) for camp in campaign_list}
        # 获取宝贝标题，价格，图片路径
        item_dict = {item.item_id:[item.title, item.price, item.pic_url] for item in item_list}

        for adg in adg_list: # 附加item，campaign，keyword属性，统计报表
            item_id = adg['item_id']
            campaign_id = adg['campaign_id']
            is_quick_opered = 1 if 'quick_optime' in adg and time_is_someday(adg['quick_optime']) else 0
            if not item_dict.get(item_id):
                del_adg_list.append(adg['_id'])
                continue
            adg_rpt = adg['rpt']
            result_list.append({'campaign_title':campaign_dict[campaign_id][0],
                                'error_descr':Adgroup.get_error_descr(adg.get('offline_type', 'online'), campaign_dict[campaign_id][1]),
                                'camp_mnt_type':mnt_camp_dict.get(campaign_id, 0),
                                'item_title':item_dict[item_id][0],
                                'item_price':format(item_dict[item_id][1] / 100.0, '.2f'),
                                'item_pic_url':item_dict[item_id][2],
                                'optm_submit_time':time_humanize(adg.get('optm_submit_time', None)),
                                'cost':format(adg_rpt.cost / 100.0, '.2f'),
                                'click_rate':format(adg_rpt.ctr, '.2f'),
                                'ppc':format(adg_rpt.cpc / 100.0, '.2f'),
                                'pay':format(adg_rpt.pay / 100.0, '.2f'),
                                'conv':format(adg_rpt.conv, '.2f'),
                                'roi':format(adg_rpt.roi, '.2f'),
                                'paycount': adg_rpt.paycount,
                                'click': adg_rpt.click,
                                'indirectpaycount': adg_rpt.indirectpaycount,
                                'directpaycount': adg_rpt.directpaycount,
                                'favcount': adg_rpt.favcount,
                                'impr': adg_rpt.impressions,
                                'favshopcount': adg_rpt.favshopcount,
                                'favitemcount': adg_rpt.favitemcount,
                                'kw_num':keyword_dict.get(adg['_id'], 0),
                                'is_quick_opered':is_quick_opered,
                                'limit_price':format(int(adg.get('limit_price', 0) or 0) / 100.0, '.2f'),
                                'mnt_opt_type':adg.get('mnt_opt_type', 0),
                                'directpay':format(adg_rpt.directpay / 100.0, '.2f'),
                                'indirectpay':format(adg_rpt.indirectpay / 100.0, '.2f'),
                                'campaign_id': adg['campaign_id'],
                                'adgroup_id': adg['_id'],
                                'online_status': adg['online_status'],
                                'mobile_discount': adg['mobile_discount'],
                                'item_id': adg['item_id'],
                                'offline_type': adg['offline_type'],
                                'mnt_type': adg['mnt_type'],
                                })
        if del_adg_list:
            Adgroup._get_collection().remove({'_id':{'$in':del_adg_list}})
    dajax.script('PT.Adgroup_list.append_table_data(%s, %s, %s, "%s")' % (json.dumps(page_info), json.dumps(result_list), json.dumps(mnt_info), sort_field))
    return dajax

def modify_adg_title(request, dajax):
    '''更新推广标题'''
    script = 'PT.hide_loading();'
    shop_id = int(request.user.shop_id)
    try:
        crt_id = int(request.POST.get('crt_id', 0))
        adg_id = int(request.POST.get('adg_id', 0))
        title = request.POST.get('title')
        adg_obj = adg_coll.find_one({'shop_id':shop_id, '_id':adg_id}, {'item_id':1})
        item_obj = item_coll.find_one({'shop_id':shop_id, '_id':adg_obj['item_id']}, {'pic_url':1})
        tapi = get_tapi(request.user)
        result = tapi.simba_creative_update(adgroup_id = adg_id, creative_id = crt_id, title = title, img_url = item_obj['pic_url'])
        crt_coll.update({'shop_id':shop_id, '_id':crt_id}, {'$set':{'title':title}})
        script += 'PT.light_msg("修改宝贝推广标题","修改成功！");$("#creative_title_%s").text("%s");' % (crt_id, title)
    except Exception, e:
        log.info('update creative title error, e = %s, shop_id = %s, creative_id = %s' % (e, shop_id, crt_id))
        script += 'PT.alert("修改宝贝推广标题失败,请检查是否输入有误！");'
    dajax.script(script)
    return dajax

def update_creative(request, dajax):
    '''修改创意内容'''
    app = request.POST.get('app', 'web')
    if app == 'crm':
        shop_id = int(request.POST['shop_id'])
        user = User.objects.get(shop_id = str(shop_id))
        tapi = get_tapi(user)
    else:
        shop_id = int(request.user.shop_id)
        tapi = get_tapi(request.user)
    adgroup_id = int(request.POST['adgroup_id'])
    creative_id = int(request.POST['creative_id'])
    try:
        title = request.POST['title']
        img_url = request.POST['img_url']
        namespace = request.POST['namespace']
        opt_type = int(request.POST.get('opt_type'))
        opter, opter_name = analysis_web_opter(request)
        result, msg = update_creative(tapi = tapi, shop_id = shop_id, adgroup_id = adgroup_id, creative_id = creative_id, title = title, img_url = img_url, opter = opter, opter_name = opter_name)
        if result:
            try:
                adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
                if adgroup.mnt_type in [1, 2, 3, 4]:
                    opt_desc = ''
                    if opt_type == 13:
                        opt_desc = '修改创意标题'
                    elif opt_type == 14:
                        opt_desc = '修改创意图片'
            except Exception, e:
                log.error('%s_update_creative error, shop_id=%s, creative_id=%s, e=%s' % (app, shop_id, creative_id, e))
            dajax.script('PT.%s.update_creative_callback(%s, "%s", "%s", %s);' % (namespace, creative_id, title, img_url, opt_type))
        else:
            dajax.script('PT.alert("%s");' % msg)
    except Exception, e:
        log.error('%s_update_creative error, shop_id=%s, creative_id=%s, e=%s' % (app, shop_id, creative_id, e))
        dajax.script('PT.alert("修改创意失败[%s]，请联系客服");' % (e))
    return dajax

def update_waiting_creative(request, dajax):
    """修改等待中的创意标题"""
    from bson.objectid import ObjectId
    id = request.POST.get('id')
    title = request.POST.get('title')
    namespace = request.POST['namespace']

    try:
        ccrt_coll.update({'_id':ObjectId(id)}, {'$set':{'title':title}})
        dajax.script('PT.%s.update_test_title_callback("%s", "%s");' % (namespace, id, title))
    except Exception, e:
        log.error('update_waiting_creative error, shop_id=%s, id=%s, e=%s' % (request.user.shop_id, id, e))
        dajax.script('PT.alert("修改失败，请联系客服");')
    return dajax

def super_update_waiting_creative(request, dajax):
    """修改等待中的创意,主要用来修改图片"""
    from apilib.binder import FileItem

    id = request.POST.get('id')
    shop_id = int(request.user.shop_id)
    title = request.POST.get('title')
    img_str = request.POST.get('img_str')

    file_item = FileItem(title + '.jpg', img_str.split(',')[1].decode('base64'))

    try:
        if CustomCreative.update_waiting_creative(id, shop_id, title, file_item):
            dajax.script('window.location.reload()')
        else:
            dajax.script('PT.alert("修改失败，请联系客服");')
    except Exception, e:
        log.error('super_update_waiting_creative error, shop_id=%s, id=%s, e=%s' % (request.user.shop_id, id, e))
        dajax.script('PT.alert("修改失败，请联系客服");')
    return dajax

def add_creative(request, dajax):
    '''添加新创意'''
    app = request.POST.get('app', 'web')
    shop_id = int(request.POST.get('shop_id')) if app == 'crm' else int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    try:
        campaign_id = int(request.POST.get('campaign_id'))
        title = request.POST['title']
        img_url = request.POST['img_url']
        namespace = request.POST['namespace']
        tapi = get_tapi(shop_id = shop_id)
        opter, opter_name = analysis_web_opter(request)
        if add_creative(tapi, shop_id, campaign_id, [[adgroup_id, title, img_url]], opter, opter_name):
            dajax.script('PT.%s.add_creative_callback();' % (namespace))
        else:
            dajax.script('PT.alert("添加创意失败，直通车后台出错，请尝试到直通车后台添加创意是否成功。");')
    except Exception, e:
        log.error('%s_add_creative error, shop_id=%s, adgroup_id=%s, e=%s' % (app, shop_id, adgroup_id, e))
        dajax.script('PT.alert("添加创意失败，直通车后台出错，请尝试到直通车后台添加创意是否成功。");')
    return dajax

def super_add_creative(request, dajax):
    '''添加新创意,与add_creative不同的是此函数接受的图片是base64字符串'''
    from apilib.binder import FileItem

    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    campaign_id = int(request.POST.get('campaign_id'))
    item_id = int(request.POST.get('item_id'))
    title = request.POST.get('title')
    img_str = request.POST.get('img_str')
    opter, opter_name = analysis_web_opter(request)
    tapi = get_tapi(shop_id = shop_id)
    file_item = FileItem(title + '.jpg', img_str.split(',')[1].decode('base64'))

    try:
        if CustomCreative.add_creative(tapi, shop_id, campaign_id, adgroup_id, item_id, title, file_item, opter, opter_name):
            dajax.script('window.location.reload()')
        else:
            dajax.script('PT.alert("添加创意失败，直通车后台出错，请尝试到直通车后台添加创意是否成功。");')
    except Exception, e:
        log.error('super_add_creative error, shop_id=%s, adgroup_id=%s, e=%s' % (shop_id, adgroup_id, e))
        dajax.script('PT.alert("添加创意失败，直通车后台出错，请尝试到直通车后台添加创意是否成功。");')
    return dajax

def super_update_creative(request, dajax):
    '''修改创意，与update_creative不同的是此函数接受的图片是base64字符串'''
    from apilib.binder import FileItem

    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    campaign_id = int(request.POST.get('campaign_id'))
    item_id = int(request.POST.get('item_id'))
    creative_id = int(request.POST.get('creative_id'))
    callback = request.POST.get('callback', None)
    title = request.POST.get('title')
    img_str = request.POST.get('img_str')
    opter, opter_name = analysis_web_opter(request)

    tapi = get_tapi(shop_id = shop_id)

    if img_str.find('data:image/jpeg;base64') == -1:
        file_item = img_str
    else:
        file_item = FileItem(title + '.jpg', img_str.split(',')[1].decode('base64'))

    try:
        if CustomCreative.update_creative(tapi, shop_id, campaign_id, adgroup_id, item_id, creative_id, title, file_item, opter, opter_name):
            if callback:
                dajax.script("%s(%s, '%s');" % (callback, creative_id, title))
            else:
                dajax.script('window.location.reload()')
        else:
            dajax.script('PT.alert("修改创意失败，请联系客服");')
    except Exception, e:
        log.error('super_update_creative error, shop_id=%s, adgroup_id=%s, e=%s' % (shop_id, adgroup_id, e))
        dajax.script('PT.alert("修改创意失败，请联系客服");')
    return dajax

def delete_creative(request, dajax):
    '''删除创意'''
    shop_id = int(request.user.shop_id)
    creative_id = int(request.POST.get('creative_id', 0))
    opter, opter_name = analysis_web_opter(request)
    try:
        namespace = request.POST.get('namespace', '')
        tapi = get_tapi(shop_id = shop_id)
        if delete_creative(tapi, shop_id, creative_id, opter, opter_name):
            dajax.script('PT.%s.delete_creative_callback();' % (namespace))
        else:
            dajax.script('PT.alert("删除创意失败，请联系客服");')
    except Exception, e:
        log.error('delete_creative error, shop_id=%s, e=%s' % (shop_id, e))
        dajax.script('PT.alert("删除创意失败，请联系客服");')
    return dajax

def create_waiting_creative(request, dajax):
    '''创建等待创意'''
    from apilib.binder import FileItem

    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST.get('campaign_id', 0))
    item_id = int(request.POST.get('item_id', 0))
    adgroup_id = int(request.POST.get('adgroup_id', 0))
    title = request.POST.get('title', 0)
    img_str = request.POST.get('img_str', '')

    # 判断用户添加等待创意是否超限
    if CustomCreative.is_limited_waiting(shop_id = shop_id, item_id = item_id):
        dajax.script('PT.alert("最多只能添加四个等待创意");')
        return dajax

    file_item = FileItem(title + '.jpg', img_str.split(',')[1].decode('base64'))

    try:
        if CustomCreative.create_waiting_creative(shop_id = shop_id, campaign_id = campaign_id, num_iid = item_id, adgroup_id = adgroup_id, title = title, file_item = file_item):
            dajax.script('window.location.reload()')
        else:
            dajax.script('PT.alert("创建等待创意失败，请联系客服");')
    except Exception, e:
        log.error('create_waiting_creative error, shop_id=%s, e=%s' % (shop_id, e))
    return dajax

def delete_waiting_creative(request, dajax):
    '''删除等待投放的创意'''
    id = request.POST.get('id', 0)
    namespace = request.POST.get('namespace', '')
    CustomCreative.objects.filter(id = id).delete()
    dajax.script('PT.%s.create_waiting_creative_callback("%s");' % (namespace, id))
    return dajax

def update_adg_status(request, dajax):
    '''广告组批量更新'''
    shop_id = int(request.user.shop_id)
    adg_id_list = request.POST.getlist('adg_id_list[]')
    adg_id_list = [int(k) for k in adg_id_list]
    mode = request.POST.get('mode')
    namespace = request.POST.get('namespace')
    camp_id = request.POST.get('campaign_id')
    mnt_type = int(request.POST.get('mnt_type', 0))
    opter, opter_name = analysis_web_opter(request)
    adg_arg_dict = {}
    if mode == 'del':
        del_id_list, cant_del_list, ztc_del_count, error_msg = delete_adgroups(shop_id = shop_id, adgroup_id_list = adg_id_list, opter = opter, opter_name = opter_name)
        mnt_num = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
        result = {'success_id_list':del_id_list, 'cant_del_list':cant_del_list, 'ztc_del_count':ztc_del_count, 'error_msg':error_msg, 'mnt_num':mnt_num}
        dajax.script('PT.%s.update_adg_back("del",%s)' % (namespace, json.dumps(result)))
    else:
        for adg_id in adg_id_list:
            adg_arg_dict[adg_id] = {'online_status':mode == 'start' and 'online' or 'offline'}
        success_id_list, ztc_del_list = update_adgroups(shop_id = shop_id, adg_arg_dict = adg_arg_dict, opter = opter, opter_name = opter_name)
        result = {'success_id_list':success_id_list, 'ztc_del_list':ztc_del_list}
        dajax.script('PT.%s.update_adg_back("%s",%s)' % (namespace, mode, result))
    return dajax

def get_adg_history(request, dajax):
    shop_id = int(request.user.shop_id)
    adg_id = int(request.POST.get('adg_id'))
    page_info = json.loads(request.POST.get('page_info', '{}'))
    page = page_info['sEcho']
    search_word = page_info['sSearch']
    page_size = page_info['iDisplayLength']
    page_offset = page_info['iDisplayStart']

    condition_dict = {'shop_id':shop_id, 'adgroup_id':adg_id, 'op_type':{'$in':[2, 3, 4]}}
    if search_word:
        condition_dict['word'] = re.compile(search_word)

    record_dict = uprcd_coll.find(condition_dict).sort([('opt_time', -1)]).skip(page_offset).limit(page_size)
    page_info['iTotalRecords'] = page_info['iTotalDisplayRecords'] = uprcd_coll.find(condition_dict).count()

    result_list = []
    for rcd in record_dict:
        if rcd.has_key('detail_list') and rcd['detail_list']:
            for detail in rcd['detail_list']:
                result_list.append({'oper_time': rcd['opt_time'].strftime("%Y-%m-%d %H:%M:%S"),
                                    'detail': detail,
                                    'oper_type': UploadRecord.get_choices_text(UploadRecord.DATA_TYPE_CHOICES, rcd['data_type']),
                                    'word': detail
                                    })

    dajax.script("PT.Adg_history.append_table_data(%s,%s);" % (json.dumps(page_info), json.dumps(result_list)))
    return dajax

def add_items2(request, dajax):
    '''将宝贝添加为广告组'''

    opter, opter_name = analysis_web_opter(request)
    def add_items_common(shop_id, campaign_id, new_item_dict):
        """给定item_title_list来添加宝贝"""
        item_arg_list, added_id_list, failed_item_dict = [], [], {}
        if new_item_dict:
            tapi = get_tapi(request.user)
            item_list = Item.get_item_by_ids(shop_id = shop_id, item_id_list = new_item_dict.keys(), tapi = tapi, transfer_flag = True) # 从淘宝获取标准的item数据
            temp_item_dict = {} # 获取部分宝贝信息
            for item in item_list: # 绑定创意标题
                adg_crt = new_item_dict.get(item['_id'], [])
                if not adg_crt:
                    continue
                adg = adg_crt[0]
                adg['title'] = TitleTransfer.remove_noneed_words(adg['title'])
                item['adgroup'] = adg
                if len(adg_crt) >= 2:
                    crt = adg_crt[1]
                    crt['title'] = TitleTransfer.remove_noneed_words(crt['title'])
                    item['creative'] = crt
                item_arg_list.append(item)
                temp_item_dict.update({item['_id']:[item['pic_url'], item['title']]})

            if item_arg_list:
                # 导入宝贝
                added_id_list, error_msg_dict = add_adgroups(shop_id = shop_id, campaign_id = campaign_id, item_arg_list = item_arg_list, tapi = tapi, opter = opter, opter_name = opter_name)
                for item_id, error_msg in  error_msg_dict.items():
                    temp_item_info = temp_item_dict.get(item_id, ('', ''))
                    failed_item_dict.update({item_id:(temp_item_info[0], temp_item_info[1], error_msg)})
                del temp_item_dict
        return added_id_list, failed_item_dict

    def update_mnt_adgroup(shop_id, campaign_id, mnt_type, adg_id_list, mnt_max_num):
        """将adgroup添加到对应的全自动计划中，需要控制数量，并且更新任务队列"""
        exist_mnt_num = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
        left_count = mnt_max_num > exist_mnt_num and (mnt_max_num - exist_mnt_num)  or 0
        mnt_adg_id_list = adg_id_list[:left_count]
        use_camp_limit = mnt_type == 1 and 1 or 0
        if mnt_adg_id_list:
            Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = mnt_adg_id_list).update(set__mnt_type = mnt_type, set__mnt_time = datetime.datetime.now(),
                                                                                               set__use_camp_limit = use_camp_limit, set__mnt_opt_type = 1)
            descr = '加入托管'
            modify_cmp_adg_log(shop_id = shop_id, campaign_id = campaign_id, adg_id_list = mnt_adg_id_list, opt_desc = descr, opter = opter, opter_name = opter_name)
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = campaign_id, mnt_type = mnt_type, task_type = 1, adgroup_id_container = {'changed':[], 'added':mnt_adg_id_list})

    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    new_item_dict = json.loads(request.POST['new_item_dict'])
    new_item_dict = {int(item_id):adg_crt for item_id, adg_crt in new_item_dict.items()}
    namespace = request.POST.get('namespace', 'Add_items')
    mnt_type = int(request.POST.get('mnt_type', 0))
    mnt_max_num = MntCampaign.get_mnt_max_num(shop_id = shop_id, campaign_id = camp_id)

    # 回调函数列表
    callback_list = json.loads(request.POST.get('callback_list', '[]'))
    if callback_list:
        delay_return = True
        callback = callback_list.pop(0)
        # 上下文参数
        context = json.loads(request.POST.get('context', '{}'))
        ajax_func = 'web_add_items2'
        context[ajax_func] = {}
    else:
        delay_return = False

    try:
        success_adg_id_list, failed_item_dict = add_items_common(shop_id = shop_id, campaign_id = camp_id, new_item_dict = new_item_dict)
        msg = '添加成功 %s 个宝贝%%s，添加失败 %s 个宝贝！' % (len(success_adg_id_list), len(failed_item_dict))
        if delay_return:
            if failed_item_dict:
                context[ajax_func]['result'] = 2 # 表示存在错误
            else:
                context[ajax_func]['result'] = 1 # 执行成功
            context[ajax_func]['failed_item_dict'] = failed_item_dict
    except Exception, e:
        log.exception('add items2 error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, camp_id, e))
        ip_matched = re.search('[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', str(e))
        if ip_matched:
            msg = "未知错误"
        else:
            msg = "未知错误"
        if delay_return:
            context[ajax_func]['result'] = 0 # 执行失败
            context[ajax_func]['msg'] = msg
            dajax.script("%s(%s, %s);" % (callback, json.dumps(callback_list), json.dumps(context)))
        else:
            dajax.script("PT.%s.add_items_callback(0, '%s');" % (namespace, msg))
        return dajax

    if mnt_type in [1, 2]: # 要处理托管
        try:
            if success_adg_id_list:
                update_mnt_adgroup(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type, adg_id_list = success_adg_id_list, mnt_max_num = mnt_max_num)
                msg = msg % '，并托管成功'
            else:
                msg = msg % ''
        except Exception, e:
            log.exception('add items2 error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, camp_id, e))
            msg = msg % '，但托管失败'
            # msg += '<br/>托管失败原因：%s' % e.message
            if delay_return:
                context[ajax_func]['result'] = 2 # 表示存在错误
    else:
        msg = msg % ''

    if delay_return:
        context[ajax_func]['msg'] = msg
        dajax.script("%s(%s, %s);" % (callback, json.dumps(callback_list), json.dumps(context)))
    else:
        dajax.script("PT.%s.add_items_callback(1, %s, '%s');" % (namespace, json.dumps(failed_item_dict), msg))
    return dajax

def get_item_imgs(request, dajax):
    app = request.POST.get('app', 'web')
    if app == 'crm':
        shop_id = int(request.POST['shop_id'])
    else:
        shop_id = int(request.user.shop_id)
    try:
        item_id_list = json.loads(request.POST['item_id_list'])
        context = request.POST.get('context', '')
        namespace = request.POST['namespace']
        # 调API批量获取宝贝图片
        if app == 'crm':
            item_dict = Item.get_item_image_byshopid(shop_id, item_id_list)
        else:
            item_dict = Item.get_item_image_byuser(request.user, item_id_list)
        dajax.script('PT.%s.get_item_imgs_callback(%s, %s);' % (namespace, json.dumps(item_dict), context))
    except Exception, e:
        log.error('get_item_imgs error, shop_id=%s, error=%s' % (shop_id, e))
        dajax.script('PT.alert("获取宝贝信息失败，请联系客服");')
    return dajax

def get_account(request, dajax):
    last_day = int(request.POST.get('last_day', 1))
    shop_id = int(request.user.shop_id)
    data_account_list = []
    try:
        rpt_dict = Account.Report.get_summed_rpt({'shop_id': shop_id}, rpt_days = last_day)
        account_rpt = rpt_dict.get(shop_id, Account.Report())

        data_account_list = [{'cost':'%.2f' % (account_rpt.cost / 100.0), 'impr':account_rpt.impressions, 'click':account_rpt.click, 'ctr':'%.2f' % account_rpt.ctr, 'cpc':'%.2f' % (account_rpt.cpc / 100.0),
          'pay':'%.2f' % (account_rpt.pay / 100.0), 'paycount':account_rpt.paycount, 'favcount':account_rpt.favcount, 'roi':'%.2f' % account_rpt.roi, 'conv':'%.2f' % account_rpt.conv,
          'directpay':'%.2f' % (account_rpt.directpay / 100.0), 'indirectpay':'%.2f' % (account_rpt.indirectpay / 100.0), 'directpaycount':account_rpt.directpaycount,
          'indirectpaycount':account_rpt.indirectpaycount, 'favitemcount':account_rpt.favitemcount, 'favshopcount':account_rpt.favshopcount,
        }]
    except Exception, e:
        log.error("get account_rpt error, shop_id=%s, error=%s" % (shop_id, e))
        dajax.script('PT.hide_loading();PT.alert("获取店铺数据失败，请刷新页面");')
        return dajax

    dajax.script('PT.Home.append_account_data(%s)' % json.dumps(data_account_list))
    return dajax

# def open_feedback_dialog(request, dajax):
#     try:
#         fobj = Feedback.objects.get(user = request.user)
#     except ObjectDoesNotExist:
#         fobj = Feedback(user = request.user)
#     score_list = fobj.score_str and eval(fobj.score_str) or []

#     display_score_list, key_list = [], []
#     for sl in score_list:
#         if DESCR_DICT.has_key(sl[0]): # 当删除一些评分项后，读取数据库时过滤掉相应字段
#             key_list.append(sl[0])
#             sl.append(DESCR_DICT[sl[0]])
#             display_score_list.append(sl)
#     # 当增加一些评分项后，读取数据库数据时添加相应字段
#     add_key_list = set(DESCR_DICT.keys()) - set(key_list)
#     for k in add_key_list:
#         display_score_list.append([k, 0, DESCR_DICT[k]])

#     feedback_list_render = render_to_string('feedback_dialog.html', {'score_list':display_score_list, 'fobj':fobj})
#     html, scripts = feedback_list_render.split("==1234567890==")
#     dajax.assign("#id_feedback_template", 'innerHTML', html)
#     dajax.script(scripts)
#     return dajax

def submit_feedback(request, dajax):
    content = request.POST.get('content')
    result = 1

    fobj = Feedback(shop_id = request.user.shop_id, score_str = '[]', content = content)
    fobj.save()
    try:
        fobj.send_email()
    except Exception, e:
        log.error('e=%s' % e)
        result = 0
    finally:
        dajax.script("PT.Base.submit_feedback_back(%s);" % result)

    return dajax

def open_info_dialog(request, dajax):
    """打开用户输入信息的小窗口"""
    # TODO: wangqi 2014-3-5 这里可以优化，前端页面打开一次后，可以不用再发请求，直接将原有的数据显示即可
#     from apps.crm.forms import UserInfoForm, Customer
    from apps.ncrm.forms import UserInfoForm, Customer
    shop_id = int(request.user.shop_id)
    try:
        customer = Customer.objects.get(shop_id = shop_id)
        form = UserInfoForm(instance = customer)
    except ObjectDoesNotExist:
        form = UserInfoForm()

    html = render_to_string('info_dialog.html', {'form':form, 'username':request.user.nick, 'isneed_phone':int(request.POST.get('isneed_phone', 0))})
    dajax.assign('#id_info_template', 'innerHTML', html)
    dajax.script("$('#info_modal_dialog').modal();")
    return dajax

def get_phone_code(request, dajax):
    """获取手机验证码"""

    from apps.common.utils.utils_sms import send_sms

    def send_verify_code(phone):
        """发送验证码"""
        code = random.randint(10000, 99999)
        result = send_sms([phone], "%s:您好,您的验证码为%s." % (settings.SITE_NAME, code))
        if 'code' in result and result['code'] == 0: #
            return code
        else:
            return 0

    msg = ''

    phone = request.POST.get('phone', 0)

    # 测试代码
    # phone_info_dict = {'time': datetime.datetime.now(), 'code': 1234, 'count': 1}
    # CacheAdpter.set(CacheKey.WEB_PHONE_CODE % phone, phone_info_dict, 'web', 60 * 15)
    # dajax.script("PT.Spring.get_code_back('%s')" % msg)
    # return dajax

    try:
        phone_info_dict = CacheAdpter.get(CacheKey.WEB_PHONE_CODE % phone, 'web', {})
        if not phone_info_dict:
            code = send_verify_code(phone)
            if code == 0:
                raise Exception('send_failed')
            phone_info_dict.update({'time':datetime.datetime.now(), 'code':code, 'count':1})
            CacheAdpter.set(CacheKey.WEB_PHONE_CODE % phone, phone_info_dict, 'web', 60 * 15)
        else:
            if (datetime.datetime.now() - phone_info_dict['time']).seconds < 60:
                raise Exception('too often')
            if phone_info_dict['count'] > 5:
                raise Exception('over_count')
            code = send_verify_code(phone)
            phone_info_dict['count'] += 1
            if code == 0:
                raise Exception('send_failed')
            phone_info_dict.update({'time':datetime.datetime.now(), 'code':code})
            CacheAdpter.set(CacheKey.WEB_PHONE_CODE % phone, phone_info_dict, 'web', 60 * 15)
        log.info('send phone code: shop_id = %s, code = %s' % (request.user.shop_id, phone_info_dict))
        # msg = "验证码短信已发送,请查收，若10分钟内未收到,请重发！"
    except Exception, e:
        error_msg = str(e)
        if error_msg == 'send_failed':
            msg = "网络忙，请稍候重试，如果问题依旧，请联系顾问！"
        elif error_msg == 'verified':
            msg = "该号码已经验证！"
        elif error_msg == 'too often':
            msg = "验证码短信已经发送,若未接收到,请10分钟后再试！"
        elif error_msg == 'over_count':
            msg = "该号码因重发验证超过5次,已被锁定！"
        else:
            msg = "未知故障，请联系顾问！"

    dajax.script("PT.Spring.get_code_back('%s')" % msg)
    return dajax

# def verify_phone_code(request, dajax):
#     msg = ''
#     try:
# #         from apps.crm.models import Customer
# #         from apps.ncrm.models import Customer as NCustomer
#         from apps.ncrm.models import Customer
#         from settings import ACTIVITY_TYPE
#
#         phone = request.POST.get('phone', '')
#         code = request.POST.get('code', '0')
#
#         phone_info_dict = CacheAdpter.get(CacheKey.WEB_PHONE_CODE % phone, 'web', {})
#         if not phone_info_dict:
#             raise Exception('verify_failed')
#         else:
#             if str(phone_info_dict['code']) != code:
#                 raise Exception('verify_failed')
#
#         shop_id = int(request.user.shop_id)
# #         customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'user':request.user, 'nick':request.user.nick, 'tp_status':'untouched', 'jl_use_status':'using'})
#         customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'nick':request.user.nick})
#         customer.phone = int(phone)
#         customer.save()
# #         NCustomer.sync_customer_info(customer)
#         CacheAdpter.set(CacheKey.WEB_ISNEED_PHONE % shop_id, 0, 'web', 60 * 60 * 24 * 7)
#         lottery = LotteryInfo.objects.get(user = request.user, exec_model = ACTIVITY_TYPE)
#         lottery.last_show_time = datetime.datetime.now()
#         lottery.extraction_flag = True
#         lottery.save()
#     except Exception, e:
#         error_msg = str(e)
#         if error_msg == 'verify_failed':
#             msg = "验证码或手机号不正确，请确认手机号和验证码！"
#         else:
#             log.exception('submit userinfo error, e=%s, shop_id=%s' % (e, request.user.shop_id))
#             msg = "提交失败，请刷新浏览器重新操作！"
#     finally:
#         dajax.script("PT.Spring.verify_code_back('%s')" % msg)
#         return dajax


def submit_userinfo(request, dajax):
#     from apps.crm.models import Customer
#     from apps.ncrm.models import Customer as NCustomer
    try:
        phone = request.POST.get('phone', '')
#         code = request.POST.get('code', '0')
#
#         phone_info_dict = CacheAdpter.get(CacheKey.WEB_PHONE_CODE % phone, 'web', {})
#         if not phone_info_dict:
#             raise Exception('verify_failed')
#         else:
#             if str(phone_info_dict['code']) != code:
#                 raise Exception('verify_failed')

        shop_id = int(request.user.shop_id)
#         customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'user':request.user, 'nick':request.user.nick, 'tp_status':'untouched', 'jl_use_status':'using'})
        customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'nick':request.user.nick})
        ww = request.POST.get('ww', '')
        qq = request.POST.get('qq', '')
        cname = request.POST.get('cname', '')
        source = request.POST.get('source', '')
        if ww:
            try:
                tapi = get_tapi(request.user)
                tapi.user_seller_get(nick = ww, fields = 'nick')
                customer.ww = ww
            except Exception:
                raise Exception('invalid_nick')
        if qq:
            customer.qq = qq
        if cname:
#             customer.cname = cname
            customer.seller = cname
        customer.phone = phone
        customer.save()
#         NCustomer.sync_customer_info(customer)
        CacheAdpter.set(CacheKey.WEB_ISNEED_PHONE % shop_id, 0, 'web', 60 * 60 * 24 * 7)

        if source == 'vip':
            dajax.script("window.location.reload();")
        else:
#            dajax.script("$('#info_modal_dialog').modal('hide');")
            # 完善信息加80积分
            from apps.web.point import PperfectPhone
            PperfectPhone.add_point_record(shop_id = shop_id)
            dajax.script("PT.vipHome.submit_userinfo_back();")
    except Exception, e:
        error_msg = str(e)
        if error_msg == 'verify_failed':
            dajax.script("PT.alert('验证码或手机号不正确，请确认手机号和验证码！');")
        elif error_msg == 'invalid_nick':
            dajax.script("PT.alert('您输入的旺旺号不是淘宝账号！');")
        else:
            log.exception('submit userinfo error, e=%s, shop_id=%s' % (e, request.user.shop_id))
            dajax.script("PT.alert('提交失败，请刷新浏览器重新操作！');")

    return dajax

def get_sale_url(request, dajax):
    # from apps.router.models import ArticleUserSubscribe
    highest_version = int(request.POST.get('version', 0))
    param_dict = {1: '{"param":{"aCode":"ACT_836440495_141010101416","itemList":["ts-25811-8:6*2"],"promIds":[10503340],"type":1},"sign":"A493DF5A36CAD98AB7A45A78A7992F44"}',
                  2: '{"param":{"aCode":"ACT_836440495_141010101416","itemList":["ts-25811-1:6*2"],"promIds":[10503339],"type":1},"sign":"ACE6DA3634F4710FC476FC1F1CF3FB92"}',
                  }
    # highest_version = ArticleUserSubscribe.get_highest_version(nick = nick)

    if highest_version not in param_dict:
        dajax.script('PT.alert("亲，您使用的是「类目专家服务版」，没有对应的优惠链接")')
        return dajax
    param_str = param_dict[highest_version]
    url = request.user.gen_sale_link(param_str)
    dajax.script('window.location.href="%s"' % url)
    return dajax

def get_shop_report(request, dajax):
    try:
        shop_id = int(request.POST.get("shop_id"))
        account = Account.objects.get(shop_id = int(shop_id))
    except Exception, e:
        log.error('To get shop report is error, e=%s' % e)
        dajax.script('alert("提交失败！请求数据有误！");')
        return dajax

    # TODO zhangyu yangrongkai 20130815 1、不需要显示店铺报表，故该函数可以删除；2、类似格式化字符的内容，要放到模板文件中用过滤器解决，而不是写很多py代码
    data = {}
    yrpt = account.rpt_yday
    if yrpt:
        data['cost'] = format(yrpt.cost / 100.0, '.2f')
        data['impressions'] = yrpt.impressions
        data['click'] = yrpt.click
        data['ctr'] = format(yrpt.ctr, '.2f')
        data['cpc'] = format(yrpt.cpc / 100.0, '.2f')
        data['favcount'] = yrpt.favcount
        data['paycount'] = yrpt.paycount
        data['conv'] = format(yrpt.conv, '.2f')
        data['roi'] = format(yrpt.roi, '.2f')
        data['directpay'] = format(yrpt.directpay, '.2f')
        data['indirectpay'] = format(yrpt.indirectpay, '.2f')
        data['directpaycount'] = yrpt.directpaycount
        data['indirectpaycount'] = yrpt.indirectpaycount
        data['favshopcount'] = yrpt.favshopcount
        data['favitemcount'] = yrpt.favitemcount
        data['pay'] = format(yrpt.pay / 100.0, '.2f')
    else:
        data['mng'] = '很抱歉，昨天的数据还没有获取到！'
        pass
    dajax.script("PT.HealthCheck.set_report_result(%s);" % (json.dumps(data)))
    return dajax

def get_health_layout(request, dajax):
    """ 获取健康检查数据"""
    try:
        shop_id = int(request.user.shop_id)
        obj_id = int(request.POST.get('obj_id'))
        check_type = request.POST.get('check_type')
        flag = int(request.POST.get('flag'))
    except Exception, e:
        log.exception("%s", e)
        dajax.script("alert('页面出错")
        return dajax

    if check_type == 'account':
        account = Account.objects.filter(shop_id = obj_id).avg_reports(rpt_days = 7)[0]
        check_item_dict, list_total = CheckItem.health_check(account, flag, Const.CHECK_ACCOUNT_ORDER)
    elif check_type == 'adgroup':
        adgroup = Adgroup.objects.filter(shop_id = shop_id, adgroup_id = obj_id).avg_reports(rpt_days = 7)[0]
        check_item_dict, list_total = CheckItem.health_check(adgroup, flag, Const.CHECK_ITEM_ORDER)

    if check_type == 'account':
        check_order_list = Const.CHECK_ACCOUNT_ORDER
    else:
        check_order_list = Const.CHECK_ITEM_ORDER

    result_list = []
    for mark, title in check_order_list:
        result_dict = {}
        result_dict['mark'] = mark
        result_dict['title'] = title
        result_dict['size'] = len(check_item_dict.get(mark, []))
        result_list.append(result_dict)

    dajax.script("PT.HealthCheck.init_layout(%s,%s);" % (obj_id, json.dumps(result_list)))
    return dajax

def get_health_items(request, dajax):
    """获取健康检查检查结果"""
    def get_progess_size(curr_count, check_length_list):
        """获取进度条百分比"""
        temp_index = 0
        temp_count = curr_count
        for temp_length in check_length_list:
            temp_count -= temp_length
            if temp_count <= 0 :
                break
            temp_index += 1
            curr_count = temp_count
        last_length = check_length_list[temp_index]
#         size = len(check_length_list)
        # 源式 = 100 * temp_index/size + 100*curr_count / (size*last_length) 化简如下
        # return 100 * (temp_index * last_length + curr_count) / (size * last_length)
        return curr_count * 100 / last_length

    # 获取客户端请求数据
    cache_key = request.POST.get('cache_key')
    client_position = int(request.POST.get('client_position'))

    try:
        # 读取服务端缓存数据
        cache_dict = CacheAdpter.get(cache_key, 'web', {})
        server_position = int(cache_dict.get('server_position', -1))
        check_length_list = cache_dict.get('check_length_list', [])
        curr_count = cache_dict.get('curr_count', 0)
    except Exception, e:
        log.exception('the cache is error! shop_id=%e ,error=%s' % (request.user.shop_id, e))
        dajax.script("PT.alert('请求有误，请重新刷新浏览器！');")
        return dajax

    # 获取进度条进度

    best_dict = {
                 'cache_key':cache_key,
                 'client_position':client_position,
                 'server_position':server_position,
                 }
    result_dict = {}

    if check_length_list:
        ratio_of_hundred = get_progess_size(curr_count, check_length_list)
        result_dict['ratio_of_hundred'] = ratio_of_hundred

    # 获取数据 ,此处未做异常处理，如果上面的异常已经捕捉，则下面的
    if client_position <= server_position and server_position > -1:
        cache_data = cache_dict.get('cache_data')
        server_length = int(cache_dict.get('server_length'))
        result_dict['data'] = cache_data[client_position + 1:server_position + 1]
        if server_length == server_position:
            CacheAdpter.delete(cache_key, 'web')
    dajax.script("PT.HealthCheck.set_show_result(%s,%s);" % (json.dumps(best_dict), json.dumps(result_dict)))
    return dajax


# 进入重复词排查的一些提前验证
def to_duplicate_check(dajax, request = None):
    shop_id = int(request.user.shop_id)
    dler_obj, _ = Downloader.objects.get_or_create(shop_id = shop_id)
    rpt_flag, _ = dler_obj.check_status_4rpt(klass = Keyword) # TODO: wangqi 20151105 可以调整，不必全店关键词下载
    if rpt_flag:
        dajax.script("PT.Base.duplicate_check_confirm();")
    else:
        dajax.script('window.location.href="%s";' % (reverse('duplicate_check')))
    return dajax

def dupl_kw_list(request, dajax):
    """重复词排查中获取重复词列表"""
    shop_id = int(request.user.shop_id)
    page_info = json.loads(request.POST.get('page_info', '{}'))
    # 分页信息处理开始
    page = page_info['sEcho']
    page_size = page_info['iDisplayLength']
    page_offset = page_info['iDisplayStart']
#     page_sort = page_info['iSortCol_0']
    page_sort_model = page_info['sSortDir_0']


    json_duplicate_data = []
    duplicate_list = get_duplicate_word(shop_id = shop_id, sort_mode = page_sort_model, start = page_offset, end = page_offset + page_size)
    garbage_words_list = get_garbage_words(shop_id) # TODO: wangqi 20151102 因报表调整，该功能不work
    if duplicate_list:
        for kw in duplicate_list[1]:
            json_duplicate_data.append({'keyword':kw['word']
                                      , 'times':kw['count']
                                        })
        # 将分页信息返还给前台
        page_count = duplicate_list[0]
        page_info['iTotalRecords'] = page_count
        page_info['iTotalDisplayRecords'] = page_count
    else:
        page_info['iTotalRecords'] = 0
        page_info['iTotalDisplayRecords'] = 0

    dajax.script("PT.Duplicate_check.dupl_list(%s,%s,%s)" % (json.dumps(page_info), json.dumps(json_duplicate_data), len(garbage_words_list)))
    return dajax

def dupl_kw_detail(request, dajax):
    """重复词排查中获取重复关键词详细信息"""
    shop_id = int(request.user.shop_id)
    keyword = request.POST.get('keyword', '')

    json_dupl_data = []

    dupl_list = get_dupl_word_info(shop_id = shop_id, last_day = 7, word = keyword)

    if dupl_list:
        level = 0;
        for dupl in dupl_list:
            level += 1
            json_dupl_data.append({'kw_id':dupl['kw_id']
                                      , 'level':level
                                      , 'camp_title':dupl['camp_title']
                                      , 'item_id':dupl['item_id']
                                      , 'item_pic_url':dupl['pic_url']
                                      , 'item_title':dupl['item_title']
                                      , 'item_price':format(dupl['item_price'] / 100.0, '.2f')
                                      , 'max_price':format(dupl['max_price'] / 100.0, '.2f')
                                      , 'qscore':dupl['qscore']
                                      , 'impr':dupl['impr']
                                      , 'click':dupl['click']
                                      , 'pay':format(dupl['pay'] / 100.0, '.2f')
                                      , 'cpc':format(dupl['cpc'] / 100.0, '.2f')
                                        })
    dajax.script("PT.Duplicate_check.dupl_detail(%s);" % (json.dumps(json_dupl_data)))
    return dajax

def delete_dupl_word(request, dajax):
    '''提交删除重复词'''

    del_type = request.POST["del_type"]
    shop_id = int(request.user.shop_id)
    condition = json.loads(request.POST.get('condition', '{}'))
    kw_list = []
    opter, opter_name = analysis_web_opter(request)
    opter = 8
    if condition:
        word_list = request.POST.getlist('word_list[]') # 如果word_list 不为空，就是手动批量删除
        if del_type == 'advanced': # 高级删除
            duplicate_list = get_duplicate_word(shop_id = shop_id, sort_mode = 'desc', start = 0, end = 1000000)
            word_list = [d['word'] for d in duplicate_list[1]]

        try:
            kw_list = filter_dupl_words(shop_id = shop_id, condition = condition, word_list = word_list)
        except Exception, e:
            log.error("filter_dupl_words error, shop_id=%s, error=%s" % (shop_id, e))
            dajax.script('PT.alert("删除重复词失败，请同步数据结构后再操作")')

    elif del_type == 'manual': # 手动删除所选中的
        kw_id_list = request.POST.getlist('kw_id_list[]')
        kw_id_list = [int(i) for i in kw_id_list]
        kw_cur = kw_coll.find({'shop_id':shop_id, '_id':{'$in':kw_id_list}}, {'adgroup_id':1, 'campaign_id':1, 'word':1})
        for kw in kw_cur:
            kw_list.append({'kw_id':kw['_id'],
                            'adg_id':kw['adgroup_id'],
                            'camp_id':kw['campaign_id'],
                            'word':kw['word']
                            })
    elif del_type == 'smart': # 智能删除
        kw_list = get_garbage_words(shop_id)

    # 按照campaign_id分组
    camp_dict = {}
    for kw in kw_list:
        if camp_dict.has_key(kw['camp_id']):
            camp_dict[kw['camp_id']].append([kw['adg_id'], kw['kw_id'], kw['word'], 0, 0, ''])
        else:
            camp_dict[kw['camp_id']] = [[kw['adg_id'], kw['kw_id'], kw['word'], 0, 0, '']]

    del_kw_list = []
    for camp_id, kw_arg_list in camp_dict.items():
        result_list = delete_keywords(shop_id = shop_id, campaign_id = camp_id, kw_arg_list = kw_arg_list, tapi = None, opter = opter, opter_name = opter_name)
        del_kw_list.extend(result_list)

    del_count = len(del_kw_list)
    failed_count = len(kw_list) - del_count

    if del_type == 'manual':
        scripts = 'PT.Duplicate_check.delete_result("%s",%s,%s,%s,%s)' % (del_type, del_count, failed_count, json.dumps(del_kw_list), condition and 1 or 0)
    else:
        scripts = 'PT.Duplicate_check.delete_result("%s",%s,%s)' % (del_type, del_count, failed_count)
    dajax.script(scripts)
    return dajax

def select_keyword(request, dajax):
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    select_type = request.POST.get('select_type', 'quick')
    max_add_num = int(request.POST.get('max_add_num'))
    try:
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        item = adgroup.item
    except:
        dajax.script('PT.alert("请确认该宝贝是否已经删除或者下架!");')
        dajax.script("PT.hide_loading();")
        return dajax
    okay_count, temp_keyword_list, filter_field_list, candidate_keyword_list = 0, [], [], []
    if select_type == 'quick':
        select_arg = ''
        # 选词
        candidate_keyword_list = KeywordSelector.get_quick_select_words(item, adgroup)
    elif select_type == 'precise':
        select_arg = request.POST.get('word_filter', '').strip().lower()
        word_match = re.match(ur'^[\u4e00-\u9fa5\s,，a-zA-Z0-9]+$', select_arg)
        if not word_match:
            dajax.script("PT.alert('核心词不能为空，且只能包含中文、字母、数字、空格、中英文逗号');")
            dajax.script("PT.hide_loading();")
            return dajax
        candidate_keyword_list = KeywordSelector.get_precise_select_words(item, adgroup, select_arg)
    elif select_type == 'combine':
        prdtword_list = json.loads(request.POST.get('prdtword_list', '[]'))
        dcrtword_list = json.loads(request.POST.get('dcrtword_list', '[]'))
        prmtword_list = json.loads(request.POST.get('prmtword_list', '[]'))
        select_arg = {'prdtword_list':prdtword_list, 'dcrtword_list':dcrtword_list, 'prmtword_list':prmtword_list}
        candidate_keyword_list = KeywordSelector.get_combiner_words(adgroup, prdtword_list, dcrtword_list, prmtword_list)
    elif select_type == 'manual':
        select_arg = json.loads(request.POST.get('manword_list', '[]'))
        candidate_keyword_list = KeywordSelector.get_manual_word(select_arg, adgroup)

    if candidate_keyword_list:
        filter_cond_dict = {'keyword_score':{'weight':5, 'svl':[250, 500, 750, 1000], "from":0, 'limit':1000, 'series_name_cn':'匹配度', 'color':"blue"},
                                       'cat_competition':{'weight':4, 'svl':5, 'series_name_cn':'竞争度', 'color':"blue"},
                                       'cat_click':{'weight':3, 'svl':5, 'exclude':[0, None], 'series_name_cn':'点击指数', 'color':"blue"},
                                       # 'cat_pv':{'weight':2, 'svl':5, 'exclude':[0, None], 'series_name_cn':'展现指数', 'color':"blue"},
                                       'cat_cpc':{'weight':1, 'svl':5, 'exclude':[0, None], 'series_name_cn':'市场均价(元)', 'color':"blue"},
                                       }
        for field, cfg in filter_cond_dict.items():
            cfg['series_name'] = field

        # 执行选词算法
        okay_count, temp_keyword_list, filter_field_list = KeywordSelector.do_filter_keywords(candidate_keyword_list, max(max_add_num, 10), filter_cond_dict)
    filter_field_list = json.dumps([fl[1] for fl in filter_field_list])

    list_select_data = []
    for i in temp_keyword_list:
        list_select_data.append([i.word, float(format(i.cat_cpc / 100.0, '.2f')), i.cat_pv, i.cat_click, i.cat_ctr, i.cat_competition, i.keyword_score, int(i.is_deleted), hasattr(i, 'is_ok') and 1 or 0])
    dajax.script('PT.SelectKeyword.select_keyword_callback(%s, %s, %s, "%s")' % (json.dumps(list_select_data), okay_count, filter_field_list, select_type))
    return dajax

# def batch_remove_keywords(request, dajax):
#     all_keyword_list = json.loads(request.POST.get('all_keyword_list', '{}'))
#     item_id = int(request.POST.get('item_id', 0))
#     shop_id = request.user.shop_id
#     campaign_dict = {}
#     adgroup_dict = {}
#     adgroup_list = Adgroup.objects.filter(shop_id = shop_id, item_id = item_id)
#     for adg in adgroup_list:
#         adgroup_dict[adg.adgroup_id] = adg.campaign_id
#         campaign_dict[adg.campaign_id] = []
#     for kw_arg_list in all_keyword_list:
#         campaign_id = adgroup_dict[kw_arg_list[0]]
#         campaign_dict[campaign_id].append(kw_arg_list)
#     deleted_id_list = [] # [id, ...]
#     deleted_id_count = {} # 各个推广计划下被删除了关键词id列表 {adgroup_id:sum, ...}
#     for campaign_id, kw_arg_list in campaign_dict.items():
#         if kw_arg_list:
#             result = delete_keywords(shop_id = shop_id, campaign_id = campaign_id, kw_arg_list = kw_arg_list, tapi = None, record_flag = True)
#             deleted_id_list.extend(result)
#             adgroup_id = kw_arg_list[0][0]
#             deleted_id_count[str(adgroup_id)] = len(result)
#     # 如有修改，则需清理缓存
#     if deleted_id_list:
#         adgroup_id = request.POST.get('adgroup_id')
#         kw_list_key = 'kw_list_4add_' + str(adgroup_id)
#         CacheAdpter.delete(kw_list_key, 'web')
#     dajax.script('PT.SelectKeyword.remove_dataTable_keywords2(%s, %s)' % (json.dumps(deleted_id_list), json.dumps(deleted_id_count)))
#     return dajax

# def get_item_keywords(request, dajax):
#     item_id = int(request.POST.get('item_id'))
#     shop_id = request.user.shop_id
#     adgroup_id_list = Adgroup.objects.filter(shop_id = shop_id, item_id = item_id).only('adgroup_id').values_list('adgroup_id')
#     # 生成表格数据
#     keywords = Keyword.objects.filter(shop_id = shop_id, adgroup_id__in = adgroup_id_list).sum_reports(rpt_days = 3)
#     all_keyword_list = []
#     for keyword in keywords:
#         # 关键词数据为3天累计数据，数据结构为[关键词，关键词id，adgroup_id，展现量，点击量，总花费，成交金额，成交笔数]
#         all_keyword_list.append([keyword.word, keyword.keyword_id, keyword.adgroup_id , keyword.qr.impressions, keyword.qr.click, keyword.qr.cost, keyword.qr.pay, keyword.qr.paycount])
#     # 统计宝贝在各个推广计划下已推广多少关键词
#     adgroup_keyword_count = {}
#     for adgroup_id in adgroup_id_list:
#         adgroup_keyword_count[adgroup_id] = Keyword.objects.filter(shop_id = shop_id, audit_status = 'audit_pass', adgroup_id = adgroup_id).count()
#
#     dajax.script('PT.SelectKeyword.generate_table2(%s, %s);' % (json.dumps(all_keyword_list), json.dumps(adgroup_keyword_count)))
#     return dajax

def get_item_convword(request, dajax):
    '''
    获取一个宝贝的top5位直通车高转化词
    '''
    shop_id = int(request.user.shop_id)
    item_id = int(request.POST.get('item_id'))
    update_convwrod_flag = int(request.POST.get('update_convwrod_flag'))
    cache_key = CacheKey.SUBWAY_ITEM_CONV_WORD % item_id
    convword_list = CacheAdpter.get(cache_key, 'web', ['No'])
    if 'No' in convword_list or update_convwrod_flag == 1:
        convword_list = Keyword.get_top5_conv_keyword(shop_id = shop_id, item_id = item_id)
        convword_list = [word['_id'] for word in convword_list]
        CacheAdpter.set(cache_key, convword_list, 'web')
    dajax.script('PT.TitleOptimize.get_item_convword_callback(%s);' % (json.dumps(convword_list)))
    return dajax

# def check_danger_cats(request, dajax):
#     '''
#     检测是否是危险类目
#     '''
#     if request.method == 'POST':
#         cat_id_list = request.POST.getlist('cat_id_list[]')
#         result = check_danger_cat8id(cat_id_list, request.user.shop_type)
#         namespace = request.POST.get('namespace', 'AddItemBox2')
#         dajax.script('PT.%s.check_danger_cats_callback(%s);' % (namespace, json.dumps(result)))
#     return dajax

def adgroup_optimize(request, dajax):

    return dajax

def get_adgroup_trend(request, dajax):
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    from_page = request.POST.get('name_space', 'Adgroup_optimize')
    adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
    adgroup.rpt_days = 7
    category_list, series_cfg_list = get_trend_chart_data(data_type = 3, rpt_list = adgroup.snap_list)
    dajax.script("PT.%s.show_adgroup_trend(%s,%s)" % (from_page, json.dumps(category_list), json.dumps(series_cfg_list)))
    return dajax

def get_adgroup_by_id(request, dajax):
    '''根据推广组id获取相应的属性'''
    shop_id = request.user.shop_id
    adgroup_id = int(request.POST.get('adgroup_id'))
    rpt_days = int(request.POST.get('last_day', 7))
    data_str = request.POST.get('data', '') # {'adgroup':['adgroup_id'],'adgroup__rpt_sum':{click}}
    call_back = request.POST.get('call_back', '')
    json_data = {}
    if data_str:
        # 数据准备
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        item = Item.objects.get(shop_id = shop_id, item_id = adgroup.item_id)
        try:
            cat_path, danger_descr = Cat.get_cat_path(cat_id_list = [item.cat_id], last_name = request.user.shop_type).get(str(item.cat_id), ['未获取到值', ''])
        except Exception, e:
            cat_path = '未获取到值'
            danger_descr = ''
            log.error('web_get_adgroup_by_id get_cat_path error, shop_id=%s, cat_id=%s, e = %s' % (shop_id, item.cat_id, e))
            # cat_path = '<span class="r_color">%s<i class="icon-warning-sign tooltips red large marl_6" data-original-title="%s"></i></span>' % (cat_path, danger_descr)
        adgroup.rpt_days = rpt_days
        json_data = get_custom_attr(adgroup, data_str)
        json_data['cat_path'] = cat_path
        if danger_descr:
            json_data['danger_descr'] = danger_descr
        else:
            json_data['danger_descr'] = ''
        if call_back:
            dajax.script('%s(%s)' % (call_back, json.dumps(json_data)))
    return dajax

def get_forecast_order_list(request, dajax):
    '''预测排名'''
    kw_id_list = request.POST.getlist('kw_id_list[]')
    tapi = get_tapi(request.user)
    nick = request.user.nick
    for kw_id in kw_id_list:
        rank_data = Keyword.rank_1_100(tapi = tapi, keyword_id = kw_id)
        if not rank_data:
            dajax.script('PT.instance_table.row_cache[%s].set_forecast_order(1)' % (kw_id))
            continue

        order_dict, oder_list = {}, []
        for rank, data in rank_data.items():
            page_order = get_page_value_by_order(rank)
            data['page'] = page_order
            if not order_dict.has_key(page_order):
                order_dict[page_order] = data
            else:
                if order_dict[page_order]['price'] > data['price']:
                    order_dict[page_order] = data
        oder_list = order_dict.values()
        oder_list.sort(lambda x, y:cmp(x['rank'], y['rank']))
        dajax.script('PT.instance_table.row_cache[%s].set_forecast_order(2,%s)' % (kw_id, json.dumps({'kw_id':kw_id, 'result':oder_list})))
    return dajax

def get_keywords_rankingforecast(request, dajax):
    '''预测排名'''
    kw_id_list = request.POST.getlist('kw_id_list[]')
    tapi = get_tapi(request.user)
    shop_id = int(request.user.shop_id)
    # forecast_data = {}
    for kw_id in kw_id_list:
        prices = Keyword.get_keyword_rankingforecast(tapi, shop_id, int(kw_id))
        dajax.script('PT.instance_table.row_cache[%s].set_forecast_order(%s)' % (kw_id, json.dumps(prices)))
    #     forecast_data[kw_id] = prices
    # dajax.script('PT.instance_table.get_keywords_rankingforecast_callback(%s);' % (json.dumps(forecast_data)))
    return dajax

def get_kws_rtrank_forecast(request, dajax):
    '''新实时预测排名'''
    adg_id = int(request.POST['adg_id'])
    kw_id = int(request.POST['kw_id'])
    price = round(float(request.POST.get('price', 0)), 2)
    is_check_rank = int(request.POST.get('is_check_rank', 0))
    tapi = get_tapi(request.user)
    result_data = Keyword.get_rt_kw_rank(tapi = tapi, adg_id = adg_id, price = int(price * 100), kw_id = kw_id)
    dajax.script('PT.instance_table.row_cache[%s].get_rt_rank_data_back(%s, %s, %s)' % (kw_id, is_check_rank, price, json.dumps(result_data)))
    return dajax

# 获取宝贝的关键词的当前排名
def get_word_order(request, dajax):
    ip = get_ip_for_rank(request)
    keyword_id = int(request.POST['keyword_id'])
    adgroup_id = int(request.POST['adgroup_id'])
    item_id = int(request.POST['item_id'])

    kw_list = list(Keyword.objects.filter(shop_id = int(request.user.shop_id), adgroup_id = adgroup_id, keyword_id = keyword_id))
    if not kw_list:
        dajax.script('alert("该宝贝下无关键词，请点击“同步下载”菜单并检查是否有关键词，然后重试");')
        return dajax

    # 批量查询关键词排名
    KeywordLocker.get_item_kws_current_order_list(user = request.user, item_id = item_id, kw_list = kw_list, ip = ip)

    keyword = kw_list[0]
    show_str = keyword.current_order
    if keyword.current_order == 101:
        show_str = '100+'
    dajax.script('PT.instance_table.row_cache[%s].set_ranking("%s")' % (keyword_id, show_str))
    return dajax

def get_blackwords(request, dajax):
    """取得屏蔽词"""
    try:
        item_id = int(request.POST['item_id'])
        item_existed, blackword_list = Item.get_blackword_list(shop_id = int(request.user.shop_id), item_id = item_id)
        if not item_existed:
            dajax.script('PT.alert("请确认该宝贝是否已经删除或者下架!");')
            return dajax
        blackwords = json.dumps(','.join(blackword_list))
        dajax.script('PT.BlackwordDialog.get_blackwords_callback(%s);' % blackwords)
    except Exception, e:
        error_msg = str(e)
        if error_msg == 'item_not_exist':
            msg = "亲，宝贝找不到，请刷新页面重试！"
        else:
            log.exception(e)
            msg = "未知错误，请联系顾问！"
        dajax.script("PT.alert('%s');" % msg)
    return dajax

def save_bword(request, dajax):
    """保存黑名单关键词列表"""
    try:
        item_id = int(request.POST['item_id'])
        blackwords = request.POST['blackwords'].split(',')
        word_list = [word for word in blackwords if word]
        namespace = request.POST.get('namespace')
    except Exception, e:
        log.exception('save_bword error, shop_id=%s, e=%s' % (request.user.shop_id, e))
        dajax.script("PT.alert('保存失败，请联系顾问！');")
        return dajax
    try:
        Item.save_blackword_list(shop_id = int(request.user.shop_id), item_id = item_id, word_list = word_list)
        result = 1
    except Exception, e:
        log.exception('save_bword error, shop_id=%s, e=%s' % (request.user.shop_id, e))
        result = 0
    dajax.script("PT.%s.save_bword_callback(%s);" % (namespace, result))
    return dajax

def parse_keyword(request, dajax):
    """分解关键词"""
    try:
        word = request.POST['word']
        part_list = ChSegement.seg_string_2_words(word)
    except Exception, e:
        log.error('parse_keyword error, shop_id=%s, word=%s, e=%s' % (request.user.shop_id, word, e))
        part_list = []

    part_list.append(word)
    part_list = sorted(list(set(part_list)), key = len)
    dajax.script("PT.instance_table.display_word_parts('%s')" % (json.dumps({'part_list':part_list})))
    return dajax

def submit_bwords(request, dajax):
    """提交屏蔽词"""
    try:
        shop_id = int(request.user.shop_id)
        campaign_id = int(request.POST['campaign_id'])
        adgroup_id = int(request.POST['adgroup_id'])
        item_id = int(request.POST['item_id'])
        blackwords = request.POST['blackwords'].split(',')
        word_list = [word for word in blackwords if word]
        save_or_update = int(request.POST.get('save_or_update', 0))
        common_table_flag = int(request.POST.get('common_table_flag', 0))
        namespace = request.POST.get('namespace', 'ManageElemword')
        opter, opter_name = analysis_web_opter(request)
        # 首先将屏蔽词保存到item中
        if save_or_update == 0:
            result = Item.save_blackword_list(shop_id = shop_id, item_id = item_id, word_list = word_list)
            set_adg_bword_log(shop_id, campaign_id, adgroup_id, item_id, word_list, opter, opter_name)
        else:
            result = Item.update_blackword_list(shop_id = shop_id, item_id = item_id, word_list = word_list)
        if not result:
            raise Exception('item_not_eixst')

        # 然后删除店铺所有推广计划下该宝贝包含屏蔽词的关键词
        del_id_list = None
        if word_list:
            opter, opter_name = analysis_web_opter(request)
            adg_id_list = list(Adgroup.objects.filter(shop_id = shop_id, item_id = item_id).values_list('adgroup_id'))
            del_id_list = bulk_del_blackword(shop_id = shop_id, adg_id_list = adg_id_list, word_list = word_list, opter = opter, opter_name = opter_name)
        if common_table_flag and del_id_list:
            dajax.script("PT.ManageElemword.submit_bwords_callback('%s');" % json.dumps(del_id_list))
        else:
            dajax.script("PT.%s.submit_bwords_callback();" % namespace)
    except Exception, e:
        error_msg = str(e)
        if error_msg == 'item_not_exist':
            msg = '亲，当前宝贝找不到，请刷新页面后重试！'
        else:
            msg = '亲，请刷新页面重试！'
        log.exception('submit blackwords error, shop_id=%s, e=%s' % (request.user.shop_id, e))
        dajax.script("PT.alert('%s');" % msg)
    return dajax

# 提交关键词到直通车
def curwords_submit(request, dajax):
    shop_id = int(request.user.shop_id)
    kw_list = json.loads(request.POST.get('data', ''))
    optm_type = request.POST.get('optm_type', '')
    opter, opter_name = analysis_web_opter(request)

    updated_id_list, deleted_id_list, top_deleted_id_list, failed_id_list = update_kws_8shopid(shop_id, kw_list, optm_type = optm_type, opter = opter, opter_name = opter_name)
    dajax.script('PT.instance_table.curwords_submit_call_back(%s)' % (json.dumps({'del_kw':deleted_id_list, 'update_kw':updated_id_list, 'failed_kw':failed_id_list, 'top_del_kw':top_deleted_id_list})))
    return dajax

def get_creative_by_id(request, dajax):
    '''根据推广组id获取相应的属性'''
    app = request.POST.get('app', 'web')
    if app == 'crm':
        shop_id = int(request.POST['shop_id'])
    else:
        shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    try:
        rpt_days = int(request.POST.get('last_day', 3))
        data_str = json.loads(request.POST.get('data', [])) # {'adgroup':['adgroup_id'],'adgroup__rpt_sum':{click}}
        call_back = request.POST.get('call_back', '')

        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        adgroup.get_creative_rpt()

        json_datas = []
        if data_str:
            # 数据准备
            creatives = Creative.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id)
            for creative in creatives:
                snap_list = creative.get_snap_list(rpt_days = rpt_days)
                sum_info = creative.get_summed_rpt(rpt_days = rpt_days)
                category_list, series_cfg_list = get_trend_chart_data(data_type = 3, rpt_list = snap_list)
                json_data = {
                                'id' : creative.creative_id,
                                'title' : creative.title,
                                'img_url' : creative.img_url,

                                'qr_impressions' : sum_info.impressions,
                                'qr_click' : sum_info.click,
                                'qr_ctr' : sum_info.ctr,
                                'qr_cpc' : sum_info.cpc,
                                'qr_paycount' : sum_info.paycount,
                                'qr_favcount' : sum_info.favcount,
                                'qr_roi' : sum_info.roi,
                                'qr_cost' : sum_info.cost,
                                'qr_pay' : sum_info.pay,

                                'category_list' : category_list,
                                'series_cfg_list' : series_cfg_list,
                             }
                json_datas.append(json_data)
            if call_back:
                dajax.script('%s(%s, %s);' % (call_back, adgroup_id, json.dumps(json_datas)))
    except Exception, e:
        log.error('%s_get_creative_by_id error, shop_id=%s, adgroup_id=%s, e=%s' % (app, shop_id, adgroup_id, e))
    return dajax

def get_uploadrecord_by_id(request, dajax):
    '''根据adgroup_id获取相应的属性'''
    shop_id = request.user.shop_id
    adgroup_id = int(request.POST.get('adgroup_id'))

    data_str = request.POST.get('data', '') # {'adgroup':['adgroup_id'],'adgroup__rpt_sum':{click}}
    call_back = request.POST.get('call_back', '')

    if data_str:
        # 数据准备
        if data_str != 'count_only':
            json_datas = []
            upload_records = UploadRecord.full_del_kw(shop_id = shop_id, adgroup_id = adgroup_id)
            for upload_record in upload_records:
                json_data = get_custom_attr(upload_record, data_str)
                json_data['opt_time'] = json_data['opt_time'].strftime('%Y-%m-%d %H:%M') # 修复IE8下时间显示为NAN的bug
                json_datas.append(json_data)
        else:
            upload_record_count = UploadRecord.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id, data_type__in = [402, 403, 404]).count()
            json_datas = {'count':upload_record_count}
        if call_back:
            dajax.script('%s(%s)' % (call_back, json.dumps(json_datas)))
    return dajax

def history_add_keywords(request, dajax):
    shop_id = request.user.shop_id
    adgroup_id = int(request.POST.get('adgroup_id'))
    kw_arg_list = json.loads(request.POST.get('kw_arg_list'))
    opter, opter_name = analysis_web_opter(request)
    result_mesg, added_keyword_list, repeat_word_list = add_keywords(shop_id = shop_id, adgroup_id = adgroup_id, kw_arg_list = kw_arg_list, opter = opter, opter_name = opter_name)
    if result_mesg:
        dajax.script('PT.alert("加词失败,原因:%s")' % (result_mesg))
        return dajax
    added_keywords_list = [k['word'] for k in added_keyword_list]
    repeat_records = UploadRecord.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id, word__in = added_keywords_list + repeat_word_list)
    dajax.script('PT.instance_table.add_call_back(%s)' % json.dumps({'added_keyword_list':added_keywords_list, 'repeat_word_list':repeat_word_list}))
    return dajax

def rob_rank_kws(request, dajax):
    # 获取页面参数
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    rpt_days = int(request.POST.get('last_day', 7))

    # 准备数据，该处不需要捕捉DoesNotExist异常，因为进入View时已经校验过了
    adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
    adgroup.rpt_days = rpt_days
    adgroup.recover_kw_rpt()

    json_keyword_data = []
    for kw in adgroup.full_kw_list:
        kw.rpt_days = rpt_days
        if kw.qscore < 6:
            continue
        json_keyword_data.append({"keyword_id":kw.keyword_id,
                                  "word":kw.word,
                                  "create_days":kw.create_days,
                                  "max_price":format(kw.max_price / 100.0, '.2f'),
                                  "qscore":kw.qscore,
                                  "impressions":kw.rpt_sum.impressions,
                                  "click":kw.rpt_sum.click,
                                  "ctr":format(kw.rpt_sum.ctr, '.2f'),
                                  "cost":format(kw.rpt_sum.cost / 100.0, '.2f'),
                                  "cpc":format(kw.rpt_sum.cpc / 100.0, '.2f'),
                                  "avgpos":kw.rpt_sum.avgpos,
                                  "favcount":kw.rpt_sum.favcount,
                                  "paycount":kw.rpt_sum.paycount,
                                  "pay":format(kw.rpt_sum.pay / 100.0, '.2f'),
                                  "conv":format(kw.rpt_sum.conv, '.2f'),
                                  "roi":format(kw.rpt_sum.roi, '.2f'),
                                  # "g_click":format_division(kw.g_click , 1, 1, '0'),
                                  # "g_cpc":format(kw.g_cpc / 100.0, '.2f'),
                                  # "g_pv":kw.g_pv,
                                  "match_scope":kw.match_scope,
                                  "is_focus":kw.is_focus and 1 or 0
                                })

    dajax.script('PT.Rob_rank.table_callback(%s)' % (json.dumps(json_keyword_data)));
    return dajax

def get_forecast_data(request, dajax):
    '''预测排名'''
    kw_id = request.POST.get('kw_id')
    shop_id = int(request.user.shop_id)
    tapi = get_tapi(request.user)

    rank_data = Keyword.get_keyword_rankingforecast(tapi, shop_id, int(kw_id))
    if not rank_data:
        dajax.script('PT.instance_table.row_cache[%s].forecast_data_back(0)' % (kw_id))
    else:
        dajax.script('PT.instance_table.row_cache[%s].forecast_data_back(1,%s)' % (kw_id, json.dumps(rank_data)))
    return dajax

# 抢排名
def rob_ranking(request, dajax):
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    keyword_list = json.loads(request.POST.get('keyword_list'))
    ip = get_ip_for_rank(request)

    kws = list(Keyword.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id, keyword_id__in = keyword_list.keys()))
    adg = Adgroup.objects.only('campaign_id', 'item_id').get(shop_id = shop_id, adgroup_id = adgroup_id)
    for kw in kws:
        kw.rank_locker = KeywordLocker(keyword_id = kw.keyword_id,
                                       word = kw.word,
                                       exp_low_rank = keyword_list[str(kw.keyword_id)][0],
                                       exp_high_rank = keyword_list[str(kw.keyword_id)][1],
                                       limit_price = int(keyword_list[str(kw.keyword_id)][2] * 100),
                                       forecast_price = int(keyword_list[str(kw.keyword_id)][3] * 100),
                                       cur_rank = int(keyword_list[str(kw.keyword_id)][4]),
                                       old_price = kw.max_price
                                       )

    KeywordLocker.rob_rank(user = request.user, keyword_list = kws, campaign_id = adg.campaign_id,
                               item_id = adg.item_id, adgroup_id = adg.adgroup_id, ip = ip)

    result = []
    for kw in kws:
        locker = kw.rank_locker
        result.append({'kw_id':kw.keyword_id, 'rank':locker.cur_rank, 'new_price':locker.cur_price, 'state':locker.result_flag, 'tips': locker.get_tips_display()})
    dajax.script('PT.instance_table.rob_ranking_call_back(%s)' % (json.dumps(result)))
    return dajax

def save_custom_column(request, dajax):
    shop_id = int(request.user.shop_id)
    colum_list = json.loads(request.POST.get('column_str', []))

    account = Account.objects.get(shop_id = shop_id)
    account.save_custom_col(colum_list)

    return dajax

def get_attention_list(request, dajax):
    '''获取关注列表'''
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 15))

    full_kw_list = Attention.get_attention_list(shop_id)
    kw_id_list = [kw.keyword_id for kw in full_kw_list]
    kw_rpt_dict = Keyword.Report.get_summed_rpt({'shop_id': shop_id, 'keyword_id': {'$in': kw_id_list}}, rpt_days = last_day)

    adgroup_id_list, item_dict, campaign_id_list, campaign_dict = [], {}, [], {}
    for kw in full_kw_list:
        kw.rpt_sum = kw_rpt_dict.get(kw.keyword_id, Keyword.Report())
        if kw.adgroup_id not in adgroup_id_list:
            adgroup_id_list.append(kw.adgroup_id)
        if kw.campaign_id not in campaign_id_list:
            campaign_id_list.append(kw.campaign_id)

    adgroup_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adgroup_id_list)
    campaign_list = Campaign.objects.filter(shop_id = shop_id, campaign_id__in = campaign_id_list)

    for adgroup in adgroup_list:
        if adgroup.item:
            item_dict[adgroup.adgroup_id] = {'id':adgroup.item.item_id, 'title':adgroup.item.title, 'price':'%.2f' % (adgroup.item.price / 100.0), 'pic_url':adgroup.item.pic_url}
        else:
            full_kw_list = [kw for kw in full_kw_list if kw.adgroup_id != adgroup.adgroup_id]

    for campaign in campaign_list:
        campaign_dict[campaign.campaign_id] = {'title':campaign.title}

    adg_dict = {adg.adgroup_id: adg for adg in adgroup_list}
    json_keyword_data = []
    for kw in full_kw_list:
        # 新质量得分未全面使用，临时解决办法
        adg = adg_dict[kw.adgroup_id]
        adg.bind_qscore([kw])
        try:
            json_keyword_data.append({"keyword_id":kw.keyword_id,
                                      "adgroup_id":kw.adgroup_id,
                                      "campaign_id":kw.campaign_id,
                                      "campaingn_title":campaign_dict[kw.campaign_id]['title'],
                                      "item_id":item_dict[kw.adgroup_id]['id'],
                                      "item_pic_url":item_dict[kw.adgroup_id]['pic_url'],
                                      "item_price":item_dict[kw.adgroup_id]['price'],
                                      "item_title":item_dict[kw.adgroup_id]['title'],
                                      "word":kw.word,
                                      "create_days":kw.create_days,
                                      "max_price":format(kw.max_price / 100.0, '.2f'),
                                      "new_price":format(kw.new_price / 100.0, '.2f'),
                                      "qscore":kw.qscore,
                                      "rele_score":kw.rele_score,
                                      "cvr_score":kw.cvr_score,
                                      "cust_score":kw.cust_score,
                                      "creative_score":kw.creative_score,
                                      "qscore_dict":kw.qscore_dict or {},
                                      "impressions":kw.rpt_sum.impressions,
                                      "click":kw.rpt_sum.click,
                                      "ctr":format(kw.rpt_sum.ctr, '.2f'),
                                      "cost":format(kw.rpt_sum.cost / 100.0, '.2f'),
                                      "cpm":format(kw.rpt_sum.cpm / 100.0, '.2f'),
                                      "cpc":format(kw.rpt_sum.cpc / 100.0, '.2f'),
                                      "avgpos":kw.rpt_sum.avgpos,
                                      "favcount":kw.rpt_sum.favcount,
                                      "paycount":kw.rpt_sum.paycount,
                                      "pay":format(kw.rpt_sum.pay / 100.0, '.2f'),
                                      "conv":format(kw.rpt_sum.conv, '.2f'),
                                      "roi":format(kw.rpt_sum.roi, '.2f'),
                                      "g_click":kw.g_click or 0,
                                      "g_ctr":format_division(kw.g_click, kw.g_pv),
                                      "g_cpc":format_division(kw.g_cpc, 100, 1),
                                      "g_competition":kw.g_competition or 0,
                                      "g_pv":kw.g_pv or 0,
                                      "match_scope":kw.match_scope,
                                      "is_focus":kw.is_focus and 1 or 0,
                                      "favctr":kw.rpt_sum.click and format(kw.rpt_sum.favcount * 100.0 / kw.rpt_sum.click, '.2f') or '0.00',
                                      "favpay":kw.rpt_sum.favcount and format(kw.rpt_sum.cost / (kw.rpt_sum.favcount * 100.0), '.2f') or '0.00',
                                      })
        except KeyError:
            pass

    # 获取用户自定义列
    # custom_column = Account.get_custom_col(shop_id = request.user.shop_id)
    custom_column = [] # 千牛需要改版， 先不获取用户配置
    dajax.script('PT.Attention.table_callback(%s)' % (json.dumps({'keyword':json_keyword_data, 'custom_column':custom_column})))
    return dajax

def change_attention(request, dajax):
    '''改变关键词关注状态'''
    shop_id = int(request.user.shop_id)
    keyword_id = int(request.POST.get('keyword_id'))
    adgroup_id = int(request.POST.get('adgroup_id'))
    is_attention = int(request.POST.get('is_attention'))
    attention_count = 0
    is_focus = is_attention == 1 and True or False
    attention = attn_coll.find_one({'_id':shop_id})
    if attention:
        attention_count = len(attention.get('keyword_id_list', []))

    if is_focus:
        if attention_count > 200:
            dajax.script("PT.alert('最多只能关注200个关键词词')")
            return dajax

    Attention.change_attention_state(shop_id, adgroup_id, keyword_id, is_focus)
    dajax.script("PT.instance_table.row_cache[%s].attention_call_back(%s)" % (keyword_id, int(is_attention) ^ 1))
    return dajax

def to_attention_list(dajax, request = None):
    '''进入我的关注的一些提前验证'''
    shop_id = int(request.user.shop_id)
    dler_obj, _ = Downloader.objects.get_or_create(shop_id = shop_id)
    rpt_flag, _ = dler_obj.check_status_4rpt(klass = Keyword)
    attention_count = 0
    attention = attn_coll.find_one({'_id':shop_id})
    if attention:
        attention_count = len(attention['keyword_id_list'])

    if attention_count and rpt_flag:
        dajax.script("PT.Base.attention_check_confirm();")
    else:
        dajax.script('PT.Base.attention_check_redirect();')

    return dajax

def getorcreate_adg_title_list(request, dajax):
    def handle_img_url(img_url):
        # 处理图片链接
        suffix_list = ['.jpg', '.png', '.gif']
        for suffix in suffix_list:
            if suffix + '_' in img_url:
                img_url = img_url.split(suffix + '_', 1)[0] + suffix
                return img_url
        suffix_list2 = ['_100x100.jpg', '_160x160.jpg', '_sum.jpg']
        for suffix in suffix_list2:
            img_url = img_url.replace(suffix, '')
        return img_url

    if request.method == 'POST':
        try:
            shop_id = int(request.user.shop_id)
            item_title = request.POST.get('title', '')
            item_id = int(request.POST['item_id'])
            adgroup_id = int(request.POST.get('adgroup_id', 0))
            namespace = request.POST['namespace']
            if adgroup_id:
                type = 1
                adg_title_list = [{}, ''] # adg_title_list 由已有创意列表和新增创意标题组成
                creative_cursor = crt_coll.find({'shop_id':shop_id, 'adgroup_id':adgroup_id}, {'title':1, 'img_url':1})
                adg_title_list[0] = {str(cur['_id']):[cur['title'], handle_img_url(cur['img_url'])] for cur in creative_cursor}
                if len(adg_title_list[0]) == 1:
                    adg_title_list[1] = TitleTransfer.generate_adg_title(shop_id, item_id)
            else:
                type = 0
#                 adg_title = TitleTransfer.generate_adgtitle_by_title(item_title, flag).replace('\n', ' ')
                adg_title_list = TitleTransfer.generate_adg_title_list(shop_id, item_id, item_title)
        except Exception, e:
            adg_title_list = ['', '']
            log.error('generater title error, e = %s, shop_id = %s' % (e, shop_id))
        finally:
#             dajax.script('PT.%s.generate_adg_title_callback("%s", "%s")' % (namespace, adg_title, item_id))
            dajax.script('PT.%s.getorcreate_adg_title_list_callback(%s, "%s", %s)' % (namespace, json.dumps(adg_title_list), item_id, type))
    return dajax

def generate_crt_title(request, dajax):
    app = request.POST.get('app', 'web')
    if app == 'crm':
        shop_id = int(request.POST['shop_id'])
    else:
        shop_id = int(request.user.shop_id)
    item_id = int(request.POST['item_id'])
    creative_no = int(request.POST.get('creative_no', 1))
    context = request.POST['context']
    try:
        namespace = request.POST['namespace']
        crt_title = TitleTransfer.generate_adg_title(shop_id, item_id, creative_no)
    except Exception, e:
        log.error('%s_generate_crt_title error, shop_id=%s, item_id=%s, e=%s' % (app, shop_id, item_id, e))
        dajax.script('PT.alert("生成创意标题失败，请联系客服");\
                            var crt_title_input = $("#"+%s);\
                            crt_title_input.siblings().show();\
                            crt_title_input.siblings(".loading_tag").hide();\
                            crt_title_input.attr("disabled", false);' % context)
    else:
        dajax.script('PT.%s.generate_crt_title_callback("%s", %s);' % (namespace, crt_title, context))
    return dajax

def generate_rec_title(request, dajax):
    shop_id = int(request.user.shop_id)
    item_id = int(request.POST['item_id'])
    try:
        rec_title, title_elemword_list = TitleTransfer.generate_rec_title(shop_id, item_id)
    except Exception, e:
        log.error('web_generate_rec_title error, shop_id=%s, item_id=%s, e=%s' % (shop_id, item_id, e))
    else:
        if rec_title and title_elemword_list:
            dajax.script('PT.TitleOptimize.generate_rec_title_callback("%s", %s);' % (rec_title, json.dumps(title_elemword_list)))
    return dajax

def get_cat_path(request, dajax):
    cat_id_list = list(set(json.loads(request.POST.get('cat_id_list', '[]'))))
    cat_dict = {}
    try:
        cat_dict = Cat.get_cat_path(cat_id_list = cat_id_list, last_name = request.user.shop_type)
    except Exception, e:
        log.error('web_get_cat_path error, shop_id = %s, e = %s' % (request.user.shop_id, e))
    namespace = request.POST.get('namespace', 'AddItemBox3')
    dajax.script('PT.%s.get_cat_path_callback(%s);' % (namespace, json.dumps(cat_dict)))
    return dajax

# TODO zhangyu 20131215 临时代码，今后无线推广将作为全自动引擎
def record_hd_20131202(request, dajax):
    '''申请无线推广计划'''
    dajax.script("PT.hide_loading();")
    try:
        user = User.objects.get(shop_id = request.user.shop_id)
        if user and not user.f5:
            user.f5 = str(datetime.datetime.now())
            user.save()
            msg = '提交申请成功，请等待淘宝的审核结果'
    except:
        msg = '提交申请失败，请联系您的顾问'
    dajax.script("PT.alert('%s')" % msg)
    return dajax

# TODO zhangyu 20131215 临时代码，今后无线推广将作为全自动引擎
def set_mobile_campaign(request, dajax):
    '''开通无线推广计划'''
    flag, title = 1, ''
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST['campaign_id'])

    try:
        user = User.objects.get(shop_id = shop_id)
        if user and user.f5 and user.f5.startswith('10,'):
            title = '您已经开通过无线推广计划，暂时只能开通一个无线推广计划'
    except:
        title = '开通无线推广计划失败，请联系精灵顾问'

    if title:
        dajax.script('set_mobile_callback(0, %s, "%s")' % (campaign_id, title))
        return dajax

    # 删除session中的申请标记，并修改标记为开通成功
    title = '开车精灵-无线推广'
    set_dict = {'title':title, 'online_status':'online', 'search_channels':'8,16', 'nonsearch_channels':'8,16', 'outside_discount':'100', 'mobile_discount':'100'}
    result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = campaign_id, **set_dict)
    if result_list:
        if request.session.has_key('apply_passed'):
            del request.session['apply_passed']
        user.f5 = '10,' + str(campaign_id)
        user.save()
        flag, title = 1, title
    else:
        flag, title = 0, '开通无线推广计划失败，您可能没有开通权限，请联系精灵顾问'
    if msg_list:
        log.info('set_mobile_campaign error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, '<br/>'.join(msg_list)))

    # 设置后回调
    dajax.script('set_mobile_callback(%s, %s,"%s")' % (flag, campaign_id, title))
    return dajax

def set_adg_limit_price(dajax, request):
    '''保存用户设置关键词的最高限价'''
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    limit_price = int(round(float(request.POST.get('limit_price', 0)) * 100))
    mobile_limit_price = int(round(float(request.POST.get('mobile_limit_price', 0)) * 100))
    mnt_type = int(request.POST.get('mnt_type', 2))
    opter, opter_name = analysis_web_opter(request)
    try:
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        old_limit_price = adgroup.limit_price
        old_mobile_limit_price=adgroup.mobile_limit_price
        if old_limit_price != limit_price or old_mobile_limit_price!=mobile_limit_price:
            adgroup.limit_price = limit_price
            adgroup.mobile_limit_price = mobile_limit_price
            adgroup.use_camp_limit = 0 # 目前只有千牛调用该接口，临时处理
            adgroup.save()

            if old_limit_price != limit_price:
                if old_limit_price:
                    opt_desc = 'PC最高限价由%.2f元，改为%.2f元' % (float(old_limit_price) / 100, float(limit_price) / 100)
                else:
                    opt_desc = 'PC最高限价设置为%.2f元' % (float(limit_price) / 100)

            if old_mobile_limit_price!=mobile_limit_price:
                if old_limit_price:
                    opt_desc = '移动最高限价由%.2f元，改为%.2f元' % (float(old_limit_price) / 100, float(limit_price) / 100)
                else:
                    opt_desc = '移动最高限价设置为%.2f元' % (float(limit_price) / 100)
            change_adg_maxprice_log(shop_id, adgroup.campaign_id, adgroup_id, adgroup.item.title, opt_desc, opter = opter, opter_name = opter_name)
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = adgroup.campaign_id, mnt_type = mnt_type, task_type = 2, adgroup_id_list = [adgroup_id])
    except Exception, e:
        log.error('set_adg_limit_price exception err=%s' % (e))
    return dajax

def set_adg_mobdiscount(dajax, request):
    try:
        shop_id = int(request.user.shop_id)
        campaign_id = int(request.POST.get('campaign_id'))
        adgroup_id = int(request.POST.get('adgroup_id'))
        discount = int(request.POST.get('discount'))
        namespace = request.POST.get('namespace', 'Adgroup_list')
        opter, opter_name = analysis_web_opter(request)
        if discount > 400 or discount < 1 :
            raise Exception("bad_discount")
        Adgroup.update_adgroup_mobdiscount(shop_id, [adgroup_id], discount)
        update_adg_mobdisct_log(shop_id, campaign_id, [adgroup_id], discount, opter = opter, opter_name = opter_name)
        dajax.script("PT.%s.set_adg_mobdiscount_callback('%s', '%s');" % (namespace, adgroup_id, discount))
    except Exception, e:
        if str(e) == "bad_discount":
            msg = "移动折扣必须介于1%~400%之间！"
        else:
            log.error("set_adg_mobdiscount error, shop_id=%s, e=%s" % (request.user.shop_id, e))
            msg = "设置失败，请刷新后重试！"
        dajax.script("PT.alert('%s');" % msg)
    return dajax

def delete_adg_mobdiscount(dajax, request):
    try:
        shop_id = int(request.user.shop_id)
        adgroup_id = int(request.POST['adgroup_id'])
        campaign_id = int(request.POST['campaign_id'])
        namespace = request.POST.get('namespace', 'Smart_optimize')
        Adgroup.delete_adgroup_mobdiscount(shop_id, [adgroup_id])
        campaign = Campaign.objects.get(campaign_id = campaign_id)
        camp_mobdiscount = campaign.platform['mobile_discount']
        dajax.script("PT.%s.set_adg_mobdiscount_callback('%s', '%s');" % (namespace, adgroup_id, camp_mobdiscount))
    except Exception, e:
        log.error("set_adg_mobdiscount error, shop_id=%s, e=%s" % (request.user.shop_id, e))
        dajax.script("PT.alert('设置失败，请刷新后重试！');")

    return dajax

# def store_lottery_info(dajax, request):
#     """保存抽奖信息"""
#     try:
#         is_extract = int(request.POST.get('is_extract')) and True or False
#         is_remind = (int(request.POST.get('is_remind'))or is_extract) and True or False
#     except Exception, e:
#         log.error("get parameters error, e=%s" % (e))
#         dajax.script("服务端接收参数失败，请刷新浏览器重试...")
#         return dajax
#     try:
#         lottery = LotteryInfo.objects.filter(user__id = request.user.id, exec_model = settings.ACTIVITY_TYPE).order_by('-create_time')[0]
#         lottery.reminder_flag = is_remind
#         lottery.extraction_flag = is_extract
#         lottery.save()
#     except Exception, e:
#         log.error('lottery store faild, e=%s' % e)
#     return dajax

# def save_lottery_info(dajax, request):
#     """保存抽奖信息"""
#     try:
#         if request.session.get('login_from', '') != 'backend':
#             lottery = LotteryInfo.objects.filter(user__id = request.user.id, exec_model = settings.ACTIVITY_TYPE).order_by('-create_time')[0]
#             lottery.extraction_flag = True
#             lottery.save()
#     except Exception, e:
#         log.error('lottery store faild, e=%s' % e)
#     return dajax

# def close_lottery_info(dajax, request):
#     """不再提醒抽奖信息"""
#     try:
#         lottery = LotteryInfo.objects.filter(user__id = request.user.id, exec_model = settings.ACTIVITY_TYPE).order_by('-create_time')[0]
#         lottery.reminder_flag = True
#         lottery.save()
#     except Exception, e:
#         log.error('lottery store failed, e=%s' % e)
#     return dajax

def submit_agent(request, dajax):
    '''设置代理账号'''
    name = request.POST['name']
    password = request.POST['password']
    agent_id = request.POST['agent_id']
    if agent_id:
        agent = Agent.objects.get(id = agent_id)
        agent.name = name
        agent.password = hashlib.md5(password).hexdigest()
        agent.save()
        msg = '修改代理用户成功！'
    else:
        try:
            tapi = get_tapi(request.user)
            result = tapi.user_seller_get(nick = name, fields = 'nick')
        except Exception, e:
            # dajax.script("PT.alert('您输入的用户名不是淘宝账号！');")
            msg = "您输入的用户名不是淘宝账号！"
            dajax.script("submit_call_back(%s,'%s')" % (0, msg))
            return dajax
        Agent.objects.create(name = name, password = hashlib.md5(password).hexdigest(), principal = request.user)
        msg = '添加代理用户成功！'
    dajax.script("submit_call_back(%s,'%s')" % (1, msg))
    # dajax.script('location.reload();')
    return dajax

def delete_agent(request, dajax):
    '''删除代理账号'''
    agent_id = request.POST['agent_id']
    result = Agent.objects.filter(id = agent_id).delete()
    dajax.script("PT.alert('代理用户删除成功');")
    dajax.script('location.reload();')
    return dajax

def get_keyword_count(request, dajax):
    '''qnpc调用，获取宝贝的关键词个数'''
    adgroup_id_list = json.loads(request.POST.get('adg_id_list', []))
    namespace = request.POST.get('namespace', 'Adgroup_list')
    keyword_dict = Keyword.get_keyword_count(shop_id = int(request.user.shop_id), adgroup_id_list = adgroup_id_list)
    dajax.script('PT.%s.get_keyword_count_callback(%s);' % (namespace, json.dumps(keyword_dict)))
    return dajax

def get_adg_status(request, dajax):
    '''web端调用，获取宝贝的关键词/创意个数'''
    shop_id = int(request.user.shop_id)
    adgroup_id_list = json.loads(request.POST.get('adg_id_list', []))
    type = request.POST.get('type', 'keyword')
    namespace = request.POST.get('namespace', 'Adgroup_list')
    result_dict = getattr(globals()[type.capitalize()], 'get_%s_count' % type)(shop_id = shop_id, adgroup_id_list = adgroup_id_list)
    dajax.script('PT.%s.get_keyword_count_callback("%s", %s);' % (namespace, type, json.dumps(result_dict)))
    return dajax

def get_sigle_comment(request, dajax):
    shop_id = int(request.user.shop_id)
    obj_type = int(request.POST.get('obj_type', 0))
    obj_id = int(request.POST.get('obj_id'))
    name_space = request.POST.get('name_space')

    obj_type_list = ['帐户', '计划', '宝贝']
    if obj_type == 1:
        obj = Campaign.objects.get(shop_id = shop_id, campaign_id = obj_id)
        obj_title = obj.title
    elif obj_type == 2:
        obj = Adgroup.objects.get(shop_id = shop_id, adgroup_id = obj_id)
        obj_title = obj.item.title

    msgs = PsMessage.objects.filter(shop_id = shop_id, object_type = obj_type, object_id = obj_id, message_type = 1).order_by('-last_modified')
    msg_list = []
    for msg in msgs:
        msg_list.append({'msg_id':str(msg.id), 'content':msg.content, 'last_modified':time_humanize(msg.last_modified), 'is_prompt':msg.is_prompt })
    result = {'obj_id':obj_id, 'obj_type':obj_type_list[obj_type], 'obj_title':obj_title, 'msg_list':msg_list}
    dajax.script('PT.%s.get_sigle_comment_back(%s);' % (name_space, (json.dumps(result))))
    return dajax

def mark_comment_read(request, dajax):
    shop_id = int(request.user.shop_id)
    msg_id = request.POST.get('msg_id')
    PsMessage.close_msg(shop_id = shop_id, msg_id = msg_id)
    return dajax

def get_adgroup_sumrpt(request, dajax):
    last_day = int(request.POST.get('last_day', 1))
    shop_id = int(request.user.shop_id)
    adg_id = int(request.POST.get('adg_id'))

    adg = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adg_id)
    adg.rpt_days = last_day
    adg_dict = {'cost':'%.2f' % (adg.rpt_sum.cost / 100.0), 'impr':adg.rpt_sum.impressions, 'click':adg.rpt_sum.click, 'ctr':'%.2f' % adg.rpt_sum.ctr, 'cpc':'%.2f' % (adg.rpt_sum.cpc / 100.0),
                'pay':'%.2f' % (adg.rpt_sum.pay / 100.0), 'paycount':adg.rpt_sum.paycount, 'favcount':adg.rpt_sum.favcount, 'roi':'%.2f' % adg.rpt_sum.roi, 'conv':'%.2f' % adg.rpt_sum.conv,
                'directpay':'%.2f' % (adg.rpt_sum.directpay / 100.0), 'indirectpay':'%.2f' % (adg.rpt_sum.indirectpay / 100.0), 'directpaycount':adg.rpt_sum.directpaycount,
                'indirectpaycount':adg.rpt_sum.indirectpaycount, 'favitemcount':adg.rpt_sum.favitemcount, 'favshopcount':adg.rpt_sum.favshopcount,
                }
    dajax.script('PT.AdgroupDetails.append_adg_data(%s)' % json.dumps(adg_dict))
    return dajax

# def receive_recount(request, dajax):
#     nick = request.POST.get('nick')
#     namespace = request.POST.get('namespace')
#     result = Point.receive_recount(new_user = request.user, old_nick = nick)
#     dajax.script('PT.%s.receive_recount_back(%s);' % (namespace, json.dumps(result)))
#     return dajax

def receive_recount(request, dajax):
    """新用户填写推荐人"""
    from point import Invited
    guide_name = request.POST.get('nick')
    shop_id = request.user.shop_id
    namespace = request.POST.get('namespace')
    is_valid, msg, data = Invited.add_point_record(shop_id = shop_id, guide_name = guide_name)

    result = {'error_msg':msg, 'point_1':data and data['point'] or 0}
    dajax.script('PT.%s.receive_recount_back(%s);' % (namespace, json.dumps(result)))
    return dajax

# 20151029 杨荣凯注销
# def generate_wait_point(request, dajax):
#     '''记录一个待减少的point记录，待用户续订后真的减去精灵币'''
#     from point import Discount
#     shop_id = request.user.shop_id
#     nick = request.user.nick
#     discount_id = request.POST.get('discount_id')
#     is_valid, msg, result = Discount.add_point_record(shop_id = shop_id, discount_id = discount_id)
#     if is_valid or msg == '已经存在该记录':
#         sale_link = ''
#         try:
#             tapi = get_tapi(shop_id = request.user.shop_id)
#             top_obj = tapi.fuwu_sale_link_gen(nick = nick, param_str = result['param_str'])
#             if top_obj and hasattr(top_obj, 'url'):
#                 sale_link = top_obj.url
#         except Exception, e:
#             log.exception('fuwu_sale_link_gen, nick=%s, e=%s' % (nick, e))
#
#         if not sale_link:
#             dajax.script('PT.alert("根据淘宝规范，如果用户已购买一个产品的高级版本，则在该版本有效期内，不能购买该产品的低级版本 ,请订购四引擎版");');
#         else:
#             dajax.script('window.location.href="%s"' % (sale_link));
#     else:
#         dajax.script('PT.alert("%s");' % (msg));
#     return dajax

def save_elemword(request, dajax):
    '''保存产品词、卖点词'''
    try:
        shop_id = int(request.user.shop_id)
        item_id = int(request.POST.get('item_id'))
        elemword = request.POST['elemword'].split(',')
        wordtype = request.POST['wordtype']
        namespace = request.POST.get('namespace')
    except Exception, e:
        log.exception('save_elemword error, shop_id=%s, e=%s' % (shop_id, e))
        dajax.script("PT.alert('保存失败，请联系顾问！');")
        return dajax
    word_list = [word for word in elemword if word]
    try:
        item = Item.objects.get(shop_id = shop_id, item_id = item_id)
        if wordtype == 'prdtword':
            attrname = '%s_hot_list' % wordtype
            org_word_dict = dict(getattr(item, attrname))
            word_list = [[word, org_word_dict.get(word, 9999)] for word in word_list]
            word_list.sort(key = itemgetter(1), reverse = True)
            setattr(item, attrname, word_list)
            CacheAdpter.set(CacheKey.SUBWAY_ITEM_PRDTWORD_HOT % item_id, word_list, 'web')
        elif wordtype == 'saleword':
            item.saleword_list = item._sale_word_list = word_list
            CacheAdpter.set(CacheKey.SUBWAY_ITEM_SALEWORD % item_id, word_list, 'web')
        item.word_modifier = 1
        item.save()
        result = 1
    except Exception, e:
        log.exception('save_elemword error, shop_id=%s, e=%s' % (shop_id, e))
        result = 0
    dajax.script("PT.%s.save_elemword_callback(%s, '%s');" % (namespace, result, wordtype))
    return dajax

def save_all_elemword(request, dajax):
    '''保存产品词、卖点词'''
    try:
        shop_id = int(request.user.shop_id)
        item_id = int(request.POST.get('item_id'))
        adgroup_id = int(request.POST.get('adgroup_id'))
        campaign_id = int(request.POST.get('campaign_id'))
        elemword_dict = json.loads(request.POST.get('elemword_dict', '{}'))
        namespace = request.POST.get('namespace')
    except Exception, e:
        log.exception('save_all_elemword error, shop_id=%s, e=%s' % (shop_id, e))
        dajax.script("PT.alert('保存失败，请联系顾问！');")
        return dajax
    try:
        opter, opter_name = analysis_web_opter(request)
        item = Item.objects.get(shop_id = shop_id, item_id = item_id)
        for wordtype, elemword in elemword_dict.items():
            word_list = list(set([word for word in elemword.split(',') if word]))
            if wordtype == 'prdtword':
                attrname = '%s_hot_list' % wordtype
                org_word_dict = dict(getattr(item, attrname))
                word_list = [[word, org_word_dict.get(word, 9999)] for word in word_list]
                word_list.sort(key = itemgetter(1), reverse = True)
                setattr(item, attrname, word_list)
                CacheAdpter.set(CacheKey.SUBWAY_ITEM_PRDTWORD_HOT % item_id, word_list, 'web')
                item.word_modifier = 1
                set_prod_word_log(shop_id, campaign_id , adgroup_id, item.title, word_list, opter, opter_name)
            elif wordtype == 'saleword':
                item.saleword_list = item._sale_word_list = word_list
                CacheAdpter.set(CacheKey.SUBWAY_ITEM_SALEWORD % item_id, word_list, 'web')
                item.word_modifier = 1
            elif wordtype == 'blackword':
                item.blackword_list = word_list
        item.save()
        result = 1
    except Exception, e:
        log.exception('save_all_elemword error, shop_id=%s, e=%s' % (shop_id, e))
        result = 0
    dajax.script("PT.%s.save_all_elemword_callback(%s, %s);" % (namespace, result, json.dumps(elemword_dict.keys())))
    return dajax

def restore_elemword(request, dajax):
    '''恢复产品词,卖点词'''
    try:
        shop_id = int(request.user.shop_id)
        item_id = int(request.POST.get('item_id'))
        namespace = request.POST.get('namespace')
    except Exception, e:
        log.exception('restore_elemword error, shop_id=%s, e=%s' % (shop_id, e))
        dajax.script("PT.alert('保存失败，请联系顾问！');")
        return dajax
    try:
        item = Item.objects.get(shop_id = shop_id, item_id = item_id)

        item.word_modifier = 0
        # 获取数据
        prdtword_data = getattr(item, 'get_prdtword_hot_list')(update_flag = True)
        # sale_data = getattr(item, 'cat_sale_words')
        # 赋值
        setattr(item, 'prdtword_hot_list', prdtword_data)
        # setattr(item, 'saleword_list', sale_data)
        item.save()

        # CacheAdpter.set(CacheKey.SUBWAY_ITEM_SALEWORD % item_id, sale_data, 'web')

        result = 1
        prdtword_data_str = ','.join([word for word, hot in prdtword_data])
        # sale_data_str = ','.join(sale_data)
    except Exception, e:
        log.exception('save_elemword error, shop_id=%s, e=%s' % (shop_id, e))
        result = 0
    dajax.script("PT.%s.restore_elemword_callback(%s, '%s', '%s');" % (namespace, result, prdtword_data_str, ''))
    return dajax

def manage_elemword(request, dajax):
    '''获取宝贝词根'''
    try:
        item_id = int(request.POST['item_id'])
        item = Item.objects.get(shop_id = request.user.shop_id, item_id = item_id)
    except:
        dajax.script('PT.alert("该宝贝可能不存在或者下架，请尝试同步数据!")')
        return dajax

    data = {}
    data['prdtword'] = ','.join([word for word, hot in item.get_prdtword_hot_list()])
    # data['propword'] = ','.join([word for word, hot in item.get_propword_hot_list()])
    # data['dcrtword'] = ','.join([word for word, hot in item.get_dcrtword_hot_list()])
    # data['saleword'] = ','.join(item.saleword_list)
    data['blackword'] = ','.join(item.blackword_list)
    dajax.script('PT.ManageElemword.manage_elemword_callback(%s);' % json.dumps(data))
    return dajax

def hot_zone(request, dajax):
    """用户行为分析统计表"""
    shop_id = int(request.user.shop_id)
    data_dict = eval(request.POST.get('data', {}))
    if data_dict:
        HotZone.add_record({'shop_id':shop_id, 's1':data_dict.get('s1', ''), 's2':data_dict.get('s2', ''), 'page':data_dict.get('page', ''), 'create_time':datetime.datetime.now()})
    return dajax

def record_lottery_click(request, dajax):
    shop_id = int(request.user.shop_id)
    source = request.POST.get('source', '')
    from settings import ACTIVITY_TYPE
    HotZone.add_record({'shop_id':shop_id, 's1':'抽奖活动领取优惠', 's2':str(ACTIVITY_TYPE), 'page':source, 'create_time':datetime.datetime.now()})
    return dajax

def right_down_ad(request, dajax):
    from apps.web.models import ad_coll

    call_back = request.POST.get('call_back', '')
    ad = ad_coll.find({'type':'right_down_ad'})
    result = {}
    if ad.count() and ad[0].get('flag', 0):
        result = {'html':ad[0].get('html', ''), 'times':ad[0].get('times', ''), 'config':eval(ad[0].get('config', '{}'))}
        dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax

# def get_cp_status(request, dajax):
#     """页面呈现袜子状态"""
#     shop_id = int(request.user.shop_id)
#     christ_promotion = cp_coll.find_one({'shop_id':shop_id})
#     if not christ_promotion:
#         christ_promotion = {}
#         christ_promotion.update({'shop_id':shop_id, 'status':0, 'is_hide':0, 'reward':'E'})
#         cp_coll.insert(christ_promotion)
#
#     christ_status, christ_desc = ChristmasPromotion.get_status(christ_promotion['status'])
#     dajax.script("PT.HomeSnow.display_sock('%s', '%s', '%s');" % (christ_status, christ_desc, christ_promotion['is_hide']))
#     return dajax
#
# def hook_sock(request, dajax):
#     """挂袜子"""
#     shop_id = int(request.user.shop_id)
#     if datetime.datetime.now() <= datetime.datetime(2014, 12, 25):
#         cp_coll.update({'shop_id':shop_id}, {'$set':{'status':1}})
#         christ_status, christ_desc = ChristmasPromotion.get_status(1)
#     else:
#         christ_status, christ_desc = ChristmasPromotion.get_status(0)
#     dajax.script("PT.%s('%s','%s','%s');" % (request.POST['callback'], christ_status, christ_desc, 0))
#     return dajax
#
# def get_reward(request, dajax):
#     """领奖"""
#     shop_id = int(request.user.shop_id)
#     if datetime.datetime.now() <= datetime.datetime(2014, 12, 25):
#         reward_dict = {'desc':'亲，你太心急了哦！', 'type':'E'}
#     else:
#         reward_dict = ChristmasPromotion.get_reward(shop_id)
#     dajax.script("PT.%s(%s);" % (request.POST['callback'], json.dumps(reward_dict)))
#     return dajax

def get_yuandan_promotion(request, dajax):
    """元旦促销"""
    if request.session.get('yuandan_promotion', 0) or datetime.date.today() > datetime.date(2015, 1, 3):
        return dajax
    try:
        shop_id = int(request.user.shop_id)
        subscibe_list = execute_query_sql_return_tuple("select item_code, end_date from ncrm_subscribe where shop_id=%s and item_code in ('ts-25811-1', 'ts-25811-8') and create_time<'2015-01-01' order by end_date desc" % shop_id)
        if subscibe_list:
            if datetime.date.today() < subscibe_list[0][1] <= datetime.date(2015, 4, 1):
                today_order_count = execute_query_sql_return_tuple("select count(*) from ncrm_subscribe where ((item_code='ts-25811-1' and pay=9000) or (item_code='ts-25811-8' and pay=6000)) and cycle='3个月' and date(create_time)=current_date")[0][0]
                dajax.script('%s(%s, "%s")' % (request.POST['callback'], today_order_count, subscibe_list[0][0]))
            # 计入统计数据
            login_shop_list = CacheAdpter.get(CacheKey.WEB_YUANDAN_PROM_LOGIN_SHOP, 'web', [])
            if shop_id not in login_shop_list:
                login_shop_list.append(shop_id)
                CacheAdpter.set(CacheKey.WEB_YUANDAN_PROM_LOGIN_SHOP, login_shop_list, 'web', 60 * 60 * 24 * 7)
    except Exception, e:
        log.error('web_get_yuandan_promotion error, shop_id=%s, e=%s' % (request.user.shop_id, e))
    else:
        request.session['yuandan_promotion'] = 1
    return dajax

def yuandan_promotion_clicked(request, dajax):
    """元旦促销活动链接点击统计"""
    clicked_shop_list = CacheAdpter.get('YUANDAN_PROM_CLICK_SHOP', 'web', [])
    shop_id = int(request.user.shop_id)
    if shop_id not in clicked_shop_list:
        clicked_shop_list.append(shop_id)
        CacheAdpter.set('YUANDAN_PROM_CLICK_SHOP', clicked_shop_list, 'web', 60 * 60 * 24 * 7)
    return dajax

def sign_point(request, dajax):
    """签到"""
    shop_id = request.user.shop_id
    callback = request.POST.get('callback')

    is_valid, msg, data = Sign.add_point_record(shop_id = shop_id)

    result = {'data':data, 'msg':msg}
    dajax.script('%s(%s);' % (callback, json.dumps(result)))
    return dajax

# def perfect_info(request, dajax):
#     """完善信息"""
#     shop_id = request.user.shop_id
#     callback = request.POST.get('callback')
#
#     data_dict, add_pint_result = {}, {}
#     for data in request.POST:
#         data_dict[data] = request.POST.get(data, '')
#
#     is_valid, msg = Account.update_perfect_info(shop_id = shop_id, data_dict = data_dict)
#
#     if is_valid:
#         add_point_is_valid, add_point_msg, add_pint_data = PerfectInfo.add_point_record(shop_id = shop_id)
#
#     add_pint_data['add_point_is_valid'] = add_point_is_valid
#     result = {'data':add_pint_data, 'msg':msg}
#     dajax.script('%s(%s);' % (callback, json.dumps(result)))
#     return dajax

def convert_gift(request, dajax):
    """兑换实物"""
    shop_id = request.user.shop_id
    callback = request.POST.get('callback')
    gift_id = request.POST.get('gift_id')

    is_valid, msg, data = Gift.add_point_record(shop_id = shop_id, gift_id = gift_id)

    result = {'data':data, 'msg':msg}
    dajax.script('%s(%s);' % (callback, json.dumps(result)))
    return dajax

def convert_virtual(request, dajax):
    """兑换虚拟物品"""
    shop_id = request.user.shop_id
    callback = request.POST.get('callback')
    gift_id = request.POST.get('gift_id')

    is_valid, msg, data = Virtual.add_point_record(shop_id = shop_id, gift_id = gift_id)

    result = {'data':data, 'msg':msg}
    dajax.script('%s(%s);' % (callback, json.dumps(result)))
    return dajax

def freeze_point(request, dajax):
    """冻结积分"""
    shop_id = request.user.shop_id
    nick = request.user.nick
    result, freeze_point_deadline = Account.freeze_point(shop_id = shop_id, nick = nick)
    if result:
        dajax.script('PT.alert("操作成功，在%s之前系统将会保留您的积分。");' % (freeze_point_deadline.strftime('%Y-%m-%d')))
    return dajax

def get_praise(request, dajax):
    """获取评价词"""
    # callback = request.POST.get('callback')
    content = ''
    msg = ''
    try:
        # 获取随机好评
        appraises = AppComment.objects.filter(service_code = 'ts-25811', is_recommend = 1).order_by('?')
        if appraises and appraises[0] is not None:
            content = appraises[0].suggestion
        else:
            errMsg = '亲,系统有点小忙,请稍候再试试吧.'
    except Exception, e:
        msg = '亲,系统有点小忙,请稍候再试试吧.'
    result = {'data':content, 'msg':msg}
    # dajax.script('%s(%s);' % (callback, json.dumps(result)))
    dajax.addData(json.dumps(result), 'func')
    return dajax

def promotion_4shop(request, dajax):
    """邀请方式2，指定店铺送积分,存入主推人信息"""
    from web.point import Promotion4Shop
    shop_id = request.user.shop_id
    callback = request.POST.get('callback')
    invited_name = request.POST.get('invited_name')
    is_check = Promotion4Shop.is_exists(shop_id = shop_id, invited_name = invited_name)
    if is_check is False:
        is_valid, msg, data = Promotion4Shop.add_point_record(shop_id = shop_id, invited_name = invited_name)
        result = {'data':data, 'msg':msg}
        dajax.script('%s(%s);' % (callback, json.dumps(result)))
    else:
        result = {'data':'', 'msg':'亲，您已经推荐过这家店铺了，无需重复推荐。'}
        dajax.script('%s(%s);' % (callback, json.dumps(result)))
    return dajax

def invited_4shop(request, dajax):
    """邀请方式2，指定店铺送积分,存入被推人信息，更新主推人信息"""
    from web.point import Invited4Shop
    nick = request.user.nick
    shop_id = request.user.shop_id
    callback = request.POST.get('callback')
    info = Invited4Shop.get_8nick(nick) # 查询出我是否被推荐过
    if info:
        is_valid, msg, data = Invited4Shop.add_point_record(shop_id = shop_id, guide_shop_id = info['shop_id']) # 添加一条被推荐人的信息
        if is_valid is True:
            is_updated = Invited4Shop.update_promotion_4shop(shop_id = shop_id, nick = nick) # 更新推荐人的积分
        result = {'error_msg':msg, 'point_1':data and data['point'] or 0}
        dajax.script('%s(%s);' % (callback, json.dumps(result)))
    return dajax

def delete_main_pic(request, dajax):
    """删除商品主图"""
    msg = ""
    item_id = int(request.POST.get('item_id', ''))
    img_id = int(request.POST.get('img_id', ''))
    callback = request.POST.get('callback', '')

    shop_id = request.user.shop_id
    tapi = get_tapi(shop_id = shop_id)

    if img_id:
        if not CustomCreative.item_img_delete(tapi = tapi, shop_id = shop_id, num_iid = item_id, img_id = img_id):
            msg = "删除商品主图失败"
    else:
        msg = "商品主图不能删除"

    result = {'data':{'item_id':item_id, 'img_id':img_id}, 'msg':msg}
    dajax.script('%s(%s);' % (callback, json.dumps(result)))
    return dajax

def record_template_click(request, dajax):
    """记录创意优化的点击次数"""
    temp_id = request.POST.get('temp_id', '')
    if temp_id:
        Template_statistics.add(temp_id)
    return dajax
