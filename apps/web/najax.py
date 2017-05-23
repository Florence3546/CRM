# coding=UTF-8
import random
import math, re
import datetime, time
import hashlib
import collections

from bson.objectid import ObjectId
from operator import itemgetter
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from mongoengine.errors import DoesNotExist

from apilib import get_tapi
from apps.common.constant import Const
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import datetime_2string, string_2datetime, days_diff_interval
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.ncrm.utils import pagination_tool
from apps.common.biz_utils.utils_misc import analysis_web_opter
from apps.common.utils.utils_number import format_division, fen2yuan
from apps.web.utils import (get_trend_chart_data, update_kws_8shopid, get_duplicate_word)
from apps.common.utils.utils_datetime import time_humanize, time_is_someday, date_2datetime
from apps.common.utils.utils_string import get_char_num
from apps.common.biz_utils.utils_tapitools import get_kw_g_data, get_kw_g_data2
from apps.common.cachekey import CacheKey
from apps.common.biz_utils.utils_misc import del_cache_progress, get_cache_progress
from apps.common.biz_utils.utils_permission import test_permission, DUPICATE_CODE

from apps.ncrm.models import Customer, Subscribe
from apps.web.models import Feedback, AppComment, HotZone, MemberStore
from apps.web.models_lottery import Lottery
from apps.web.models import MainAd, Template_statistics, OrderTemplate, pa_coll, SelectKeywordFellBack
from apps.web.utils import bulk_del_blackword, delete_keywords
from apps.kwslt.models_cat import CatStatic

from apps.alg.interface import bulk_optimize_4adgroup2, optimize_adgroup_dryrun2
from apps.alg.submit import KeywordSubmit
from apps.alg.kwclassifier import BULK_TREE_LIST

from apps.mnt.models_task import MntTaskMng
from apps.mnt.models_mnt import MntMnger
from apps.router.models import Agent, User
from apps.mnt.models_mnt import MntCampaign
from apps.engine.models import TitleTransfer, ShopMngTask
from apps.engine.models_corekw import CoreKeyword
from apps.engine.rob_rank import CustomRobRank
from apps.subway.realtime_report import RealtimeReport
from apps.subway.upload import (delete_adgroups, update_adgroups, change_adg_maxprice_log, delete_creative,
                                update_item_title, set_prod_word_log, update_campaign, update_adg_mobdisct_log,
                                add_keywords, set_camp_bword_log, update_custom_creative, add_custom_creative,
                                delete_custom_creative, set_adg_bword_log, del_adg_mobdisct_log, onekey_optimize_log,
                                update_keywords, set_adg_follow_log)

from apps.subway.download import Downloader
from apps.subway.models import (Account, Campaign, Item, item_coll, CustomCreative, ccrt_coll,
                                Creative, Adgroup, adg_coll, UploadRecord, uprcd_coll,
                                Keyword, crt_coll, kw_coll, camp_coll)
from apps.web.point import Sign, PointManager, Gift, Virtual, Promotion4Shop, Invited, Discount, PperfectPhone
from apps.kwslt.keyword_selector import SelectKeywordPackage, KeywordSelector
from apps.engine.models_channel import MessageChannel
from apps.engine.models_kwlocker import KeywordLocker
from apps.engine.rob_rank import RobRankMng
from apps.ncrm.models import PSUser, reminder_coll
from apps.ncrm.models import PrivateMessage

def route_ajax(request):
    '''ajax路由函数，返回数据务必返回字典的格式'''
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
    return HttpResponse('%s(%s)' % (call_back, json.dumps(data)))

def is_authenticated(request):
    return {'errMsg':'', 'data':1 if request.user.is_authenticated() else 0}

# 同步全店数据
def sync_data(request):
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


# 同步当前推广组数据
def sync_current_adg(request):
    '''手动触发当前宝贝的关键词、创意结构和报表数据下载'''
    shop_id = int(request.user.shop_id)
    adg_id = int(request.POST['adg_id'])
    camp_id = int(request.POST['camp_id'])
    try:
        # 建议使用缓存用于下载互斥，防止同一时间多个线程一起下载
        rpt_days = Keyword.Report.INIT_DAYS # 由于keyword与Creative都是30天，因此这里可以这么写，否则还是分开写较好

        # 同步关键词结构数据
        dler, _ = Downloader.objects.get_or_create(shop_id = shop_id)
        dler.sync_all_struct()
        struct_result = Keyword.struct_download_byadgs(shop_id = shop_id, adg_id_list = [adg_id], tapi = dler.tapi)

        # 同步关键词报表数据和创意
        dl_args = {'shop_id':shop_id, 'tapi':dler.tapi, 'token':dler.token, 'adg_tuple_list':[(adg_id, camp_id, datetime.datetime.now() - datetime.timedelta(days = rpt_days))]}
        crtrpt_result, _ = Creative.download_crtrpt_byadgs(**dl_args)
        kwrpt_result, _ = Keyword.download_kwrpt_byadgs(**dl_args)

        # 同步关键词质量得分
        Adgroup.objects.get(shop_id = shop_id, adgroup_id = adg_id).refresh_qscore()
        msg = (crtrpt_result and kwrpt_result and struct_result) and "同步数据成功。" or "同步数据失败。"

    except Exception, e:
        log.exception("sync_current_adgroup by user error, shop_id=%s, adgroup_id=%s, e=%s" % (shop_id, adg_id, e))
        msg = '同步宝贝的关键词数据出错，请联系顾问。'
    return {'msg': msg, 'errMsg': ''}


#===========================================================================
# 广告浏览及点击模块
#===========================================================================
def add_show_times(request):
    '''广告预览次数加1 add by tianxiaohe 20150916'''
    try:
        # 不是从crm后台登陆的才记录
        if request.session.get('login_from', 'taobao') != 'backend':
            MainAd.add_show_times(int(request.POST.get('ad_id', 0)))
    except Exception, e:
        log.exception("add_show_times error, e=%s" % (e))
    return {'data': 'success', 'errMsg': ''}


def add_click_times(request):
    '''广告次数次数加1 add by tianxiaohe 20150916'''
    try:
        # 不是从crm后台request.session.get('login_from', 'taobao') is not 'backend'登陆的才记录
        if request.session.get('login_from', 'taobao') != 'backend':
            MainAd.add_click_times(int(request.POST.get('ad_id', 0)))
    except Exception, e:
        log.exception("add_click_times error, e=%s" % (e))
    return {'data': 'success', 'errMsg': ''}

#===========================================================
# 标题优化模块
#===========================================================
def get_title_traffic_score(request):
    '''获取引流数据 add by tianxiaohe 20150925'''
    title = request.POST.get("title")
    title_num = request.POST.get("title_num")
    title_elemword_list = request.POST.getlist("title_elemword_list[]")
    item_id = request.POST.get("item_id")
#     sales = request.POST.get("sales")
    if not(title and title_num and item_id):
        return {'errMsg': '数据获取失败'}
    try:
        item_id = int(item_id)
#         sales = int(sales)
        item = Item.objects.get(
            shop_id = int(request.user.shop_id), item_id = item_id)
    except:
        return {'errMsg': '数据获取失败'}

    if title_elemword_list and len(title_elemword_list) > 1:
        kw_list = json.dumps(item.get_kw_list_byelemword(title_elemword_list))
        title_elemword_list = json.dumps([])
    else:
        title_info_dict = item.get_title_info_dict(title)
        kw_list = json.dumps(title_info_dict['kw_list'])
        title_elemword_list = json.dumps(
            title_info_dict['title_elemword_list'])
    return {'errMsg': '', 'data': {'title': title,
                                   'title_num': title_num,
                                   'kw_list': kw_list,
                                   'title_elemword_list': title_elemword_list,
                                   'is_rec_title':int(request.POST.get('is_rec_title', 0))
                                   }}


def generate_rec_title(request):
    '''获取推荐标题'''
    shop_id = int(request.user.shop_id)
    item_id = int(request.POST['item_id'])
    try:
        rec_title, title_elemword_list = TitleTransfer.generate_rec_title(
            shop_id, item_id)
    except Exception, e:
        log.error('generate_rec_title error, shop_id=%s, item_id=%s, e=%s' % (
            shop_id, item_id, e))
        return {'errMsg': ''}
    else:
        if rec_title and title_elemword_list:
            return {'errMsg': '', 'rec_title': rec_title, 'title_elemword_list': json.dumps(title_elemword_list)}
    return {'errMsg': ''}

def update_item(request):
    """提交标题"""
    item_id = int(request.POST.get("item_id"))
    adgroup_id = int(request.POST.get("adgroup_id"))
    campaign_id = int(request.POST.get("campaign_id"))
    title = request.POST.get("title")
    title_num = request.POST.get("title_num")
    errMsg = ''
    item = Item.objects.get(shop_id = request.user.shop_id, item_id = item_id)
    old_title = item.title
    result = update_item_title(shop_id = request.user.shop_id, item_id = item_id, title = title, shop_type = request.user.shop_type)
    if result is True:
        opter, opter_name = analysis_web_opter(request)
        UploadRecord.objects.create(shop_id = item.shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id, item_name = old_title, op_type = 2, data_type = 213, detail_list = ['修改宝贝标题为："%s"' % title], opter = opter, opter_name = opter_name)
        item.delete_item_cache()
        return {'errMsg':errMsg, 'title':title, 'title_num':title_num}
    else:
        errMsg = '提交失败'
    return {'errMsg':errMsg}


#===========================================================
# 创意优化模块
#===========================================================


def delete_main_pic(request):
    """删除商品主图"""
    errMsg = ""
    item_id = int(request.POST.get('item_id', ''))
    img_id = int(request.POST.get('img_id', ''))

    shop_id = request.user.shop_id
    tapi = get_tapi(shop_id = shop_id)

    if img_id:
        if not CustomCreative.item_img_delete(tapi = tapi, shop_id = shop_id, num_iid = item_id, img_id = img_id):
            errMsg = "删除商品主图失败"
    else:
        errMsg = "商品主图不能删除"

    result = {'data': {'item_id': item_id, 'img_id': img_id}, 'errMsg': errMsg}
    return result


def del_creative(request):
    '''删除创意'''
    errMsg = ''
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id', 0))
    creative_id = int(request.POST.get('creative_id', 0))
    opter, opter_name = analysis_web_opter(request)
    try:
        tapi = get_tapi(shop_id = shop_id)
        if not delete_creative(tapi, shop_id, creative_id, opter, opter_name):
            errMsg = "删除创意失败，请联系客服"
    except Exception, e:
        log.error('delete_creative error, shop_id=%s, e=%s' % (shop_id, e))
        errMsg = "删除创意失败，请联系客服"
    return {'errMsg': errMsg}


def delete_waiting_creative(request):
    '''删除等待投放的创意'''
    shop_id = int(request.user.shop_id)
    creative_id = request.POST.get('creative_id', 0)
    adgroup_id = request.POST.get('adgroup_id', 0)
    opter, opter_name = analysis_web_opter(request)
    result, errMsg = delete_custom_creative(shop_id, adgroup_id, creative_id, opter = opter, opter_name = opter_name)
    return {'errMsg': errMsg, 'id': creative_id}


def super_update_creative(request):
    '''修改创意，与update_creative不同的是此函数接受的图片是base64字符串'''
    from apilib.binder import FileItem
    errMsg = ''
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    campaign_id = int(request.POST.get('campaign_id'))
    item_id = int(request.POST.get('item_id'))
    creative_id = int(request.POST.get('creative_id'))
    title = request.POST.get('title')
    img_str = request.POST.get('img_str')
    callback = request.POST.get('callback', None)
    opter, opter_name = analysis_web_opter(request)
    tapi = get_tapi(shop_id = shop_id)

    if img_str.find('data:image/jpeg;base64') == -1:
        file_item = img_str
    else:
        file_item = FileItem(
            title + '.jpg', img_str.split(',')[1].decode('base64'))

    try:
        result, errMsg = update_custom_creative(tapi, shop_id, campaign_id, adgroup_id, item_id, creative_id, title, file_item, opter, opter_name)
        if result:
            if callback:
                return {'creative_id': creative_id, 'title': title, 'errMsg': errMsg}
            else:
                return {'reload': True, 'title': title, 'errMsg': errMsg}
    except Exception, e:
        log.error('super_update_creative error, shop_id=%s, adgroup_id=%s, e=%s' % (
            shop_id, adgroup_id, e))
        errMsg = "修改创意失败，请稍候再试，或联系客服协助决解"
    return {'errMsg': errMsg}


def update_waiting_creative(request):
    """修改等待中的创意标题"""
    from bson.objectid import ObjectId
    id = request.POST.get('id')
    title = request.POST.get('title')
    errMsg = ''
    opter, opter_name = analysis_web_opter(request)
    try:
        ccrt = ccrt_coll.find_one({ "_id":ObjectId(id)})
        ccrt_coll.update({'_id': ObjectId(id)}, {'$set': {'title': title}})
        detail_list = ['修改创意:%s --> %s' % (ccrt['title'], title)]

        adgroup = Adgroup.objects.get(shop_id = ccrt['shop_id'], adgroup_id = ccrt['adgroup_id'])
        record_list = [{'shop_id':ccrt['shop_id'], 'campaign_id':ccrt['campaign_id'], 'adgroup_id':ccrt['adgroup_id'], 'item_name':adgroup.item.title, 'detail_list':detail_list, 'op_type':3, 'data_type':303, 'opter': opter, 'opter_name': opter_name}]
        if record_list:
            rcd_list = [UploadRecord(**record) for record in record_list]
            UploadRecord.objects.insert(rcd_list)
    except Exception, e:
        log.error('update_waiting_creative error, shop_id=%s, id=%s, e=%s' % (
            request.user.shop_id, id, e))
        errMsg = "修改创意失败，请稍候再试，或联系客服协助决解"
    return {'id': id, 'title': title, 'errMsg': errMsg}


def show_creative_trend(request):
    """显示趋势图"""
    shop_id = int(request.user.shop_id)
    creative_id = int(request.POST['creative_id'])
    creative = Creative.objects.filter(
        shop_id = shop_id, creative_id = creative_id)[0]
    creative.rpt_days = 7
    result = {}
    errMsg = ''
    if creative.get_snap_list():
        category_list, series_cfg_list = get_trend_chart_data(
            data_type = 3, rpt_list = creative.snap_list)
        result = {'creative_id': creative_id, 'category_list': json.dumps(
            category_list), 'series_cfg_list': series_cfg_list}
    else:
        errMsg = '没有趋势数据'
    result['errMsg'] = errMsg
    return result

def record_template_click(request):
    """记录创意优化的点击次数"""
    temp_id = request.POST.get('temp_id', '')
    errMsg = ''
    if temp_id:
        Template_statistics.add(temp_id)
    return {'errMsg':errMsg}

def super_add_creative(request):
    '''添加新创意,与add_creative不同的是此函数接受的图片是base64字符串'''
    from apilib.binder import FileItem
    errMsg = ''
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    campaign_id = int(request.POST.get('campaign_id'))
    item_id = int(request.POST.get('item_id'))
    title = request.POST.get('title')
    img_str = request.POST.get('img_str')
    opter, opter_name = analysis_web_opter(request)
    tapi = get_tapi(shop_id = shop_id)
    file_item = FileItem(title + '.jpg', img_str.split(',')[1].decode('base64'))

    result = {}
    try:
        if add_custom_creative(tapi, shop_id, campaign_id, adgroup_id, item_id, title, file_item, opter, opter_name):
            result['reload'] = True
        else:
            errMsg = '添加创意失败，直通车后台出错，请尝试到直通车后台添加创意是否成功。'
    except Exception, e:
        log.error('super_add_creative error, shop_id=%s, adgroup_id=%s, e=%s' % (shop_id, adgroup_id, e))
        errMsg = '添加创意失败，直通车后台出错，请尝试到直通车后台添加创意是否成功。'
    result['errMsg'] = errMsg
    return result

def create_waiting_creative(request):
    '''创建等待创意'''
    from apilib.binder import FileItem
    result = {}
    errMsg = ''
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST.get('campaign_id', 0))
    item_id = int(request.POST.get('item_id', 0))
    adgroup_id = int(request.POST.get('adgroup_id', 0))
    title = request.POST.get('title', 0)
    img_str = request.POST.get('img_str', '')
    opter, opter_name = analysis_web_opter(request)
    # 判断用户添加等待创意是否超限
    is_limited = CustomCreative.is_limited_waiting(shop_id = shop_id, adgroup_id = adgroup_id)
    if is_limited:
        errMsg = '最多只能添加四个等待创意'
    else:
        file_item = FileItem(title + '.jpg', img_str.split(',')[1].decode('base64'))
        try:
            if CustomCreative.create_waiting_creative(shop_id = shop_id, campaign_id = campaign_id, num_iid = item_id, adgroup_id = adgroup_id, title = title, file_item = file_item, opter = opter, opter_name = opter_name):
                result['reload'] = True
            else:
                errMsg = "创建等待创意失败，请联系客服"
        except Exception, e:
            log.error('create_waiting_creative error, shop_id=%s, e=%s' % (shop_id, e))
            errMsg = "创建等待创意失败，请联系客服"
    result['errMsg'] = errMsg
    return result

def super_update_waiting_creative(request):
    """修改等待中的创意,主要用来修改图片"""
    from apilib.binder import FileItem
    result = {}
    errMsg = ''
    id = request.POST.get('id')
    shop_id = int(request.user.shop_id)
    title = request.POST.get('title')
    img_str = request.POST.get('img_str')

    file_item = FileItem(title + '.jpg', img_str.split(',')[1].decode('base64'))
    opter, opter_name = analysis_web_opter(request)

    try:
        if CustomCreative.update_waiting_creative(id, shop_id, title, file_item, opter, opter_name):
            result['reload'] = True
        else:
            errMsg = "修改创意失败，请稍候再试，或联系客服协助决解"
    except Exception, e:
        log.error('super_update_waiting_creative error, shop_id=%s, id=%s, e=%s' % (request.user.shop_id, id, e))
        errMsg = "修改创意失败，请稍候再试，或联系客服协助决解"
    result['errMsg'] = errMsg
    return result

#============================================================
# 关键词设置
#============================================================
def manage_elemword(request):
    '''获取宝贝词根 add by tianxiaohe 20151006'''
    errMsg = ''
    try:
        item_id = int(request.POST['item_id'])
        item = Item.objects.get(shop_id = request.user.shop_id, item_id = item_id)
    except Exception, e:
        log.exception('manage_elemword error, shop_id=%s, e=%s' % (item_id, e))
        errMsg = '该宝贝可能不存在或者下架，请尝试同步数据!'
        return {'errMsg':errMsg}

    data = {}
    data['prdtword'] = ','.join([word for word, hot in item.get_prdtword_hot_list()])
    data['blackword'] = ','.join(item.blackword_list)
    return {'errMsg':errMsg, 'data':data}

def save_prdtword(request):
    '''保存产品词 add by tianxiaohe 20151006'''
    errMsg = ''
    result = 0
    try:
        shop_id = int(request.user.shop_id)
        item_id = int(request.POST.get('item_id'))
        adgroup_id = int(request.POST.get('adgroup_id'))
        campaign_id = int(request.POST.get('campaign_id'))
        prdtword = request.POST.get('prdtword', '')
    except Exception, e:
        log.exception('save_all_elemword error, shop_id=%s, e=%s' % (shop_id, e))
        errMsg = '保存失败，请联系顾问！'
    try:
        opter, opter_name = analysis_web_opter(request)
        item = Item.objects.get(shop_id = shop_id, item_id = item_id)
        word_list = list(set([word for word in prdtword.split(',') if word]))
        attrname = 'prdtword_hot_list'
        org_word_dict = dict(getattr(item, attrname))
        word_list = [[word, org_word_dict.get(word, 9999)] for word in word_list]
        word_list.sort(key = itemgetter(1), reverse = True)
        setattr(item, attrname, word_list)
        CacheAdpter.set(CacheKey.SUBWAY_ITEM_PRDTWORD_HOT % item_id, word_list, 'web')
        item.word_modifier = 1
        set_prod_word_log(shop_id, campaign_id , adgroup_id, item.title, word_list, opter, opter_name)

        item.save()
        result = 1
    except Exception, e:
        log.exception('save_prdtword error, shop_id=%s, e=%s' % (shop_id, e))
        errMsg = '保存失败，请联系顾问！'
    return {'errMsg':errMsg, 'result':result}

def restore_elemword(request):
    '''恢复产品词 add by tianxiaohe 20151006'''
    errMsg = ''
    result = 0
    prdtword_data_str = ''
    try:
        shop_id = int(request.user.shop_id)
        item_id = int(request.POST.get('item_id'))
    except Exception, e:
        log.exception('restore_elemword error, shop_id=%s, e=%s' % (shop_id, e))
        errMsg = '恢复失败，请联系顾问！'
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
        errMsg = '恢复失败，请联系顾问！'
    return {'errMsg':errMsg, 'result':result, 'prdtword_data_str':prdtword_data_str}

def save_bword(request):
    """保存屏蔽词列表 add by tianxiaohe 20151006"""
    errMsg = ''
    result = 1
    del_id_list = []

    """提交屏蔽词"""
    try:
        shop_id = int(request.user.shop_id)
        adgroup_id = int(request.POST['adgroup_id'])
        campaign_id = int(request.POST['campaign_id'])
        item_id = int(request.POST['item_id'])
        blackwords = request.POST['blackwords'].split(',')
        word_list = [word for word in blackwords if word]
        save_or_update = int(request.POST.get('save_or_update', 0))
        opter, opter_name = analysis_web_opter(request)

        item_existed, blackword_list = Item.get_blackword_list(shop_id = shop_id, item_id = item_id)
        # 首先将屏蔽词保存到item中
        if save_or_update == 0:
            temp_list = set(word_list) - set(blackword_list) # 新list减去旧的list 找出新增的
            if temp_list and  len(temp_list) > 0: # 新增
                set_adg_bword_log(shop_id, campaign_id, adgroup_id, item_id, temp_list, opter, opter_name)
            result = Item.save_blackword_list(shop_id = shop_id, item_id = item_id, word_list = word_list)
        else:
            # temp_list = set(blackword_list) - set(word_list) # 旧list减去新的list 找出修改的
            # if temp_list and  len(temp_list) > 0: # 修改
                # set_adg_bword_log(shop_id, campaign_id, adgroup_id, item_id, temp_list, opter, opter_name)
            result = Item.update_blackword_list(shop_id = shop_id, item_id = item_id, word_list = word_list)
        if not result:
            raise Exception('item_not_exist')

        # 然后删除店铺所有推广计划下该宝贝包含屏蔽词的关键词
        del_id_list = None
        if word_list:
            opter, opter_name = analysis_web_opter(request)
            adg_id_list = list(Adgroup.objects.filter(shop_id = shop_id, item_id = item_id).values_list('adgroup_id'))
            del_id_list = bulk_del_blackword(shop_id = shop_id, adg_id_list = adg_id_list, word_list = word_list, opter = opter, opter_name = opter_name)
    except Exception, e:
        error_msg = str(e)
        if error_msg == 'item_not_exist':
            errMsg = '亲，当前宝贝找不到，请刷新页面后重试！'
        else:
            errMsg = '亲，请刷新页面重试！'
        result = 0
        log.exception('submit blackwords error, shop_id=%s, e=%s' % (request.user.shop_id, e))
    return {'result':result, 'errMsg':'', 'del_id_list':del_id_list, 'error_msg':errMsg}

def get_camp_list(request):
    '''获取计划标题'''
    camp_list = [{"camp_id":-1, "camp_title": "全部"}]
    try:
        shop_id = int(request.user.shop_id)
        campaigns = Campaign.objects.only('campaign_id', 'title').filter(shop_id = shop_id)
        for camp in campaigns:
            camp_list.append({"camp_id": camp.campaign_id, "camp_title": camp.title})
    except Exception, e:
        log.error('get_camp_list error, shop_id=%s, e=%s' % (shop_id, e))
        return {'errMsg': ''}
    return {'errMsg': '', 'camp_list': camp_list}

#=============================================
# 代理设置
#=============================================
def submit_agent(request):
    '''设置代理账号 add by tianxiaohe 20151007'''
    errMsg = ''
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
            errMsg = "您输入的用户名不是淘宝账号！"
        Agent.objects.create(name = name, password = hashlib.md5(password).hexdigest(), principal = request.user)
        msg = '添加代理用户成功！'
    return {'errMsg':errMsg, 'msg':msg}

def delete_agent(request):
    '''删除代理账号 add by tianxiaoihe 20151007'''
    errMsg = ''
    try:
        agent_id = request.POST['agent_id']
        Agent.objects.filter(id = agent_id).delete()
    except:
        errMsg = "删除失败，！"
    return {'errMsg':errMsg}

#=============================================
# 操作记录
#=============================================
def get_history_list(request):
    """操作记录列表"""
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST.get('camp_id', -1))
    op_type = int(request.POST.get('op_type', -1))
    opter = int(request.POST.get('opter', -1))
    start_date = str(request.POST.get('start_date', ''))
    end_date = str(request.POST.get('end_date', ''))
    page_no = int(request.POST.get('pageIdx', 1))
    search_keyword = request.POST.get('search_word', '')
    up_list = []

    sdate = string_2datetime(start_date, fmt = '%Y-%m-%d')
    edate = string_2datetime(end_date, fmt = '%Y-%m-%d') - datetime.timedelta(days = -1)
    condition_dict = {'shop_id':shop_id, 'opt_time':{'$gte': sdate, '$lt': edate}}

    if camp_id > -1:
        if camp_id == 1:
            # 查询全部托管计划的操作日志
            condition_dict['campaign_id'] = {'$in': list(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id'))}
        elif camp_id == 2:
            # 查询全部未托管计划的操作日志
            mnt_camp_id_list = MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id')
            camp_id_list = Campaign.objects.filter(shop_id = shop_id).values_list('campaign_id')
            condition_dict['campaign_id'] = {'$in': list(set(camp_id_list) - set(mnt_camp_id_list))}
        else:
            # 查询指定计划的操作日志
            condition_dict['campaign_id'] = camp_id
    if opter > -1:
        condition_dict['opter'] = opter
    if op_type > -1:
        condition_dict['op_type'] = op_type
    if search_keyword:
        condition_dict['$or'] = [{'item_name':{'$regex':search_keyword}}, {'detail_list':{'$regex':search_keyword}}]

    cursor = uprcd_coll.find(condition_dict).sort('opt_time', -1)
    page_info, history_list = pagination_tool(page = page_no, record = cursor, page_count = 100)

    if page_info:
        page_json = page_info
    else:
        page_json = {"page_xrange": [0], "record_count": 0, "start_page": 0, "page_count": 0, "page": 0, "end_page": 0}

    campaign_list = Campaign.objects.filter(shop_id = shop_id)
    campaign_dict = {camp.campaign_id:camp.title for camp in campaign_list}

    for rcd in history_list:
        try:
            opter = ''
            detail_list = []
            rid = str(rcd['_id'])
            opt_time = rcd['opt_time'].strftime("%Y-%m-%d %H:%M:%S")
            if 'opter' in rcd:
                opter = UploadRecord.get_choices_text(UploadRecord.OPERATOR_CHOICES, rcd['opter'])
            op_type = int(rcd['op_type'])
            op_type_text = UploadRecord.get_choices_text(UploadRecord.OP_TYPE_CHOICES, op_type)
            data_type = UploadRecord.get_choices_text(UploadRecord.DATA_TYPE_CHOICES, rcd['data_type'])
            campaign_id = rcd.get('campaign_id', 0)
            campaign_name = ''
            if campaign_id in campaign_dict:
                campaign_name = campaign_dict[campaign_id]
            item_name = rcd.get('item_name', '')
            detail_length = 0
            if 'detail_list' in rcd and rcd['detail_list']:
                detail_length = len(rcd['detail_list'])
                for index, detail in enumerate(rcd['detail_list']):
                    if detail:
                        if op_type == 1:
                            detail_list.append('计划"%s"，%s' % (campaign_name, detail))
                        elif not item_name and op_type == 2:
                            if detail_length == 1:
                                detail_list.append('计划"%s"，%s' % (campaign_name, detail))
                            else:
                                if index == 0:
                                    detail_list.append('计划"%s"，%s个宝贝%s' % (campaign_name, detail_length, data_type))
                                    detail_list.append(detail)
                                else:
                                    detail_list.append(detail)
                        elif not item_name:
                            detail_list.append('计划"%s"，%s' % (campaign_name, detail))
                        elif detail_length == 1 and index == 0 and op_type == 4:
                            detail_list.append('计划"%s"，宝贝"%s"，%s1个：%s' % (campaign_name, item_name, data_type, detail))
                        elif detail_length > 1 and (op_type == 4 or op_type == 2):
                            if index == 0:
                                detail_list.append('计划"%s"，宝贝"%s"，%s%s个' % (campaign_name, item_name, data_type, detail_length))
                                detail_list.append(detail)
                            else:
                                detail_list.append(detail)
                        else:
                            detail_list.append('计划"%s"，宝贝"%s"，%s' % (campaign_name, item_name, detail))
                    else:
                        if op_type == 1:
                            detail_list.append('计划"%s"' % campaign_name)
                        elif not item_name:
                            detail_list.append('计划"%s"' % campaign_name)
                        else:
                            detail_list.append('计划"%s"，宝贝"%s"' % (campaign_name, item_name))
            up_list.append({'rid':rid , 'opt_time':opt_time, 'opter':opter, 'op_type':op_type_text,
                            'data_type':data_type, 'detail_list':detail_list, 'detail_length':detail_length})
        except Exception, e:
            log.error("parse opt history error, shop_id=%s, e=%s" % (shop_id, e))
            continue

    return {'errMsg': '', 'history_list': up_list, 'page_info': page_json}

def save_theme(request):
    '''保存用户主题'''
    errMsg = ''
    new_theme = request.POST.get('theme', None)
    if new_theme in ['orange', 'light_blue', 'dark_blue', 'green']:
        request.user.theme = new_theme
        request.user.save()
        request.session['theme'] = new_theme
    else:
        errMsg = '不是有效的主题'
    return {'errMsg': errMsg}

def check_user_phone(request):
    '''检查用户是否填写了手机号'''
    shop_id = int(request.user.shop_id)
    fill_user_info = False
    try:
        customer = Customer.objects.get(shop_id = shop_id, nick = request.user.nick)
        if customer and customer.phone:
            fill_user_info = True
    except DoesNotExist, e:
        fill_user_info = False
    return {'errMsg': '', 'fill_user_info': fill_user_info}

def submit_userinfo(request):
    '''保存用户信息，包括是否发生短信提醒异常，用户手机号，及昵称'''
    errMsg = ''
    remind = request.POST.get('remind', None)
    phone = request.POST.get('phone', '')
    nick = request.POST.get('nick', '')
    qq = request.POST.get('qq', '')

    try:
        shop_id = int(request.user.shop_id)
        customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'nick':request.user.nick})

        if remind:
            customer.remind = int(remind)
            request.session['remind'] = int(remind)

        if phone:
            customer.phone = phone
            request.session['phone'] = phone

        if nick:
            customer.seller = nick
            request.session['seller'] = nick

        if qq:
            customer.qq = qq

        customer.save()
        CacheAdpter.set(CacheKey.WEB_ISNEED_PHONE % shop_id, 0, 'web', 60 * 60 * 24 * 7)
        PperfectPhone.add_point_record(shop_id = shop_id)
    except Exception, e:
        errMsg = "提交失败，请刷新浏览器重新操作！"

    return {'errMsg': errMsg, 'remind':remind}

def add_suggest(request):
    '''保存用户反馈信息'''
    content = request.POST.get('suggest')
    error_msg = ''

    try:
        # consult_id = Customer.objects.get(shop_id = request.user.shop_id).consult_id
        customer = Customer.objects.select_related('consult').get(shop_id=request.user.shop_id)
        consult = customer.consult
        if consult.name_cn == u'技术部':
            consult = customer.operater
        fobj = Feedback(shop_id = request.user.shop_id, score_str = '[]', content = content, consult = consult, handle_status = -1)
        fobj.save()
        fobj.send_email()
    except Exception, e:
        error_msg = '提交失败，请联系客服'
        log.error('e=%s' % e)

    return {'errMsg': error_msg}

#==================================================
# 首页后台部分
#==================================================
def get_account(request):
    """获取账户信息 add by tianxiaohe 20151007"""
    shop_id = int(request.user.shop_id)
    account_data_dict = {}
    chart_data = {}
    update_cache = int(request.POST.get('update_cache', '0'))
    try:
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        errMsg = ''
        rpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'account', args_list = [shop_id], update_now = bool(update_cache)) # 从缓存取账户时实数据
        rtrpt_item = rpt_dict.get(shop_id, Account.Report())
        # args_dict = {'query_dict': {'shop_id': shop_id}, 'start_date': start_date, 'end_date': end_date}
        snap_dict = Account.Report.get_snap_list(query_dict = {'shop_id': shop_id}, start_date = start_date, end_date = end_date)
        snap_list = snap_dict.get(shop_id, [])
        snap_list.append(rtrpt_item)
        category_list, series_cfg_list = get_trend_chart_data(data_type = 1, rpt_list = snap_list)
        chart_data = {'category_list': category_list, 'series_cfg_list': series_cfg_list}

        if not (start_date == end_date == datetime.date.today().strftime('%Y-%m-%d')):
            rpt_dict = Account.Report.get_summed_rpt({'shop_id': shop_id}, start_date = start_date, end_date = end_date)
        account_rpt = rpt_dict.get(shop_id, Account.Report())
        account_data_dict = account_rpt.to_dict()

    except Exception, e:
        log.error("get account_rpt error, shop_id=%s, error=%s" % (shop_id, e))
        errMsg = '获取店铺数据失败，请刷新页面'
    return {'errMsg':errMsg, 'account_data_dict':account_data_dict, 'chart_data': chart_data}

def get_account_rtdata(request):
    """获取账户实时数据 add by tianxiaohe 20151217"""
    shop_id = int(request.user.shop_id)
    update_cache = int(request.POST.get('update_cache', '0'))
    rpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'account', args_list = [shop_id], update_now = bool(update_cache)) # 从缓存取账户时实数据
    rtrpt_item = rpt_dict.get(shop_id, Account.Report())
    # 当天实时数据
    account_data_dict = {'cost':'%.2f' % (rtrpt_item.cost / 100.0), 'impr':rtrpt_item.impressions, 'click':rtrpt_item.click, 'ctr':'%.2f' % rtrpt_item.ctr, 'cpc':'%.2f' % (rtrpt_item.cpc / 100.0),
      'pay':'%.2f' % (rtrpt_item.pay / 100.0), 'paycount':rtrpt_item.paycount, 'favcount':rtrpt_item.favcount, 'roi':'%.2f' % rtrpt_item.roi, 'conv':'%.2f' % rtrpt_item.conv,
      'directpay':'%.2f' % (rtrpt_item.directpay / 100.0), 'indirectpay':'%.2f' % (rtrpt_item.indirectpay / 100.0), 'directpaycount':rtrpt_item.directpaycount,
      'indirectpaycount':rtrpt_item.indirectpaycount, 'favitemcount':rtrpt_item.favitemcount, 'favshopcount':rtrpt_item.favshopcount, 'carttotal':rtrpt_item.carttotal, 'pay_cost':'%.2f' % (rtrpt_item.pay_cost / 100.0),
    }
    return {'errMsg':'', 'account_data_dict':account_data_dict}

def get_adgroup_list(request):
    '''查询宝贝列表'''
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 1))
    start_date = str(request.POST.get('start_date', ''))
    end_date = str(request.POST.get('end_date', ''))
    campaign_id = int(request.POST.get('campaign_id', 2))
    page_info = json.loads(request.POST.get('page_info', '{}'))
    search_keyword = request.POST.get('sSearch', '')
    page_size = int(request.POST.get('page_size', 100))
    page_no = int(request.POST.get('page_no', 1))
    opt_type = int(request.POST.get('opt_type', -1))
    sort_pair = request.POST.get('sort', None)
    status_type = str(request.POST.get('status_type', ''))
    is_follow = int(request.POST.get('is_follow', -1))
    # sort_field = ''

    # 处理排序参数
    try:
        sort_field, sort_order = sort_pair.split('_', 1)
        sort_order = int(sort_order)
    except:
        sort_field, sort_order = 'pay', -1
    sort_list = [(sort_field, sort_order)]

    # 如果是全自动计划，计算托管宝贝个数
    mnt_info = {'is_mnt':0, 'mnt_type':0, 'mnt_num':0}

    condition_dict = {'shop_id':shop_id}

    mnt_camps = MntCampaign.objects.filter(shop_id = shop_id)
    mnt_camp_dict = {camp.campaign_id: camp for camp in mnt_camps}

    campaign_list = Campaign.objects.filter(shop_id = shop_id)
    camp_id_list = [campaign.campaign_id for campaign in campaign_list]

    if is_follow == 1:
        condition_dict.update({'is_follow': is_follow})
    elif is_follow == 0:
        condition_dict.update({'$or': [{'is_follow': {'$exists': False}}, {'is_follow': is_follow}] })

    if campaign_id == 1: # 全部托管计划
        condition_dict['campaign_id'] = {'$in': mnt_camp_dict.keys()}
        camp_id_list = [mnt_camp_dict.keys()]
    elif campaign_id == 2: # 全部未托管计划
        condition_dict['campaign_id'] = {'$nin': mnt_camp_dict.keys()}
        camp_id_list = list(set(camp_id_list) - set(mnt_camp_dict.keys()))
    elif campaign_id > 2:
        condition_dict['campaign_id'] = campaign_id
        camp_id_list = [campaign_id]
        if campaign_id in mnt_camp_dict:
            temp_mnt_camp = mnt_camp_dict[campaign_id]
            mnt_info['is_mnt'] = 1
            mnt_info['mnt_type'] = temp_mnt_camp.mnt_type
            # mnt_info['mnt_type'] = mnt_camp_dict.get(campaign_id, None)
            mnt_info['mnt_num'] = adg_coll.find({'shop_id':shop_id, 'campaign_id':campaign_id, 'mnt_type':{'$ne':0}}).count()

    if search_keyword:
        item_list = item_coll.find({'shop_id':shop_id, 'title': {"$regex":search_keyword}})
        item_id_list = [item['_id'] for item in item_list]
        condition_dict['item_id'] = {'$in': item_id_list}

    if status_type in ['online', 'offline']:
        condition_dict['online_status'] = status_type
    elif status_type in ['audit_offline', 'crm_offline']:
        condition_dict['offline_type'] = status_type

    # 根据优化状态（托管类型）查询宝贝
    if opt_type > -1:
        # opt_type==0，表示查询为托管的宝贝
        if opt_type == 0:
            condition_dict['mnt_type'] = 0
        else:
            condition_dict['mnt_type'] = {'$gt': 0}
            if opt_type == 1:
                condition_dict.update({'$or': [{'mnt_opt_type': {'$exists': False}},
                                               {'mnt_opt_type': {'$in': [opt_type, str(opt_type), '']}},
                                               ]
                                       })
            elif opt_type == 2:
                condition_dict.update({'mnt_opt_type': opt_type})

    # 1. 根据条件过滤推广组，获取一个filtered_adgid_list<筛选的推广组ID列表>
    # 2. 根据<筛选的推广组列表>，对报表进行查询并排序，获取rpt_sorted_adgid_list<根据报表排序过的推广组ID列表>
    # 3. <根据报表排序过的推广组ID列表> + <剩下无报表的推广组ID列表(顺序无所谓？)> 组成ordered_adgid_list<有序的推广组ID列表>
    # 4. 对ordered_adgid_list分页获取
    # 5. 绑定各种数据...

    result_list = []

    filtered_adg_id_list = [adg['_id'] for adg in adg_coll.find(condition_dict, {'_id': 1})]
    if filtered_adg_id_list:
        if start_date == end_date == datetime.date.today().strftime('%Y-%m-%d'):
            rpt_sorted_adgid_list = Adgroup.sort_adg_by_rtrpt(shop_id = shop_id, camp_id_list = camp_id_list, sort_list = sort_list, filtered_adg_id_list = filtered_adg_id_list)
        else:
            rpt_sorted_adgid_list = Adgroup.sort_adg_byrpt({'shop_id': shop_id, 'adgroup_id': {'$in': filtered_adg_id_list}}, sort_list = sort_list, start_date = start_date, end_date = end_date)
        if sort_order == -1: # 降序时，有报表的排前
            ordered_adgid_list = rpt_sorted_adgid_list + list(set(filtered_adg_id_list) - set(rpt_sorted_adgid_list))
        else: # 反之则排在后面
            ordered_adgid_list = list(set(filtered_adg_id_list) - set(rpt_sorted_adgid_list)) + rpt_sorted_adgid_list
        page_json, paged_ordered_adgid_list = pagination_tool(page = page_no, record = ordered_adgid_list, page_count = page_size)

        item_id_set = set()
        campaign_id_set = set()
        del_adgid_list = []
        sorted_adgroup_list = []

        adgroup_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = paged_ordered_adgid_list)
        temp_adg_dict = {}
        for adgroup in adgroup_list:
            temp_adg_dict.update({adgroup.adgroup_id: adgroup})
            item_id_set.add(adgroup.item_id)
            campaign_id_set.add(adgroup.campaign_id)

        for adg_id in paged_ordered_adgid_list:
            temp_adg = temp_adg_dict.get(adg_id, None)
            if temp_adg:
                sorted_adgroup_list.append(temp_adg)
            else:
                del_adgid_list.append(adg_id)

        if start_date == end_date == datetime.date.today().strftime('%Y-%m-%d'):
            adg_rpt_dict = {}
            for camp_id in camp_id_list:
                adg_rpt_dict.update(RealtimeReport.get_summed_rtrpt(rpt_type = 'adgroup', args_list = [shop_id, camp_id], update_now = False))
        else:
            adg_rpt_dict = Adgroup.Report.get_summed_rpt(query_dict = {'shop_id': shop_id, 'adgroup_id': {'$in': paged_ordered_adgid_list}}, start_date = start_date, end_date = end_date)
        campaign_dict = {camp.campaign_id: camp for camp in  Campaign.objects.filter(shop_id = shop_id, campaign_id__in = list(campaign_id_set))}
        item_dict = {item.item_id: [item.title, item.price, item.pic_url]for item in  Item.objects.filter(shop_id = shop_id, item_id__in = list(item_id_set))}

        for adgroup in sorted_adgroup_list:
            temp_item = item_dict.get(adgroup.item_id, None)
            if not temp_item:
                del_adgid_list.append(adgroup.adgroup_id)
                continue
            temp_rpt = adg_rpt_dict.get(adgroup.adgroup_id, Adgroup.Report())
            temp_camp = campaign_dict[adgroup.campaign_id]
            adgroup.mob_enabled = bool(temp_camp.platform['yd_insite'] or temp_camp.platform['yd_outsite'])
            if adgroup.mob_enabled and adgroup.mobile_discount == 0:
                adgroup.mobile_discount = temp_camp.platform['mobile_discount']

            limit_price = adgroup.limit_price
            mobile_limit_price = adgroup.real_mobile_limit_price
            temp_mnt_camp = mnt_camp_dict.get(adgroup.campaign_id, None)

            if temp_mnt_camp:
                camp_mnt_type = temp_mnt_camp.mnt_type
                camp_max_price = temp_mnt_camp.max_price
                camp_max_mobile_price = temp_mnt_camp.real_mobile_max_price
                if adgroup.mnt_type > 0 and adgroup.use_camp_limit:
                    limit_price = temp_mnt_camp.max_price
                    mobile_limit_price = temp_mnt_camp.real_mobile_max_price
            else:
                camp_mnt_type = 0
                camp_max_price = 50
                camp_max_mobile_price = 50

            temp_adg = {
                'campaign_id': adgroup.campaign_id,
                'campaign_title': temp_camp.title,
                'camp_mnt_type': camp_mnt_type,
                'adgroup_id': adgroup.adgroup_id,
                'online_status': adgroup.online_status,
                'offline_type': adgroup.offline_type,
                'error_descr': adgroup.offline_descr,
                'mob_enabled': adgroup.mob_enabled,
                'mobile_discount' : adgroup.mobile_discount,
                'limit_price': fen2yuan(limit_price),
                'mobile_limit_price': fen2yuan(mobile_limit_price),
                'mnt_type': adgroup.mnt_type,
                'mnt_opt_type': adgroup.mnt_opt_type,
                'optm_submit_time':time_humanize(adgroup.optm_submit_time),
                'is_quick_opered': 1 if adgroup.quick_optime and time_is_someday(adgroup.quick_optime) else 0,
                'use_camp_limit':adgroup.use_camp_limit,
                'item_id': adgroup.item_id,
                'item_title': temp_item[0],
                'item_price': fen2yuan(temp_item[1]),
                'item_pic_url': temp_item[2],
                'cat_id':adgroup.direct_cat_id,
                'is_follow':adgroup.is_follow,
                'camp_max_price': fen2yuan(camp_max_price),
                'camp_max_mobile_price': fen2yuan(camp_max_mobile_price),
            }
            temp_adg.update(temp_rpt.to_dict())
            result_list.append(temp_adg)

        if del_adgid_list:
            Adgroup.remove_adgroup(shop_id = shop_id, adgroup_id_list = del_adgid_list)
    else:
        page_json = {"page_xrange": [0], "record_count": 0, "start_page": 0, "page_count": 0, "page": 0, "end_page": 0}

    return {"errMsg": "",
            "page_info": page_json,
            "adg_list": result_list,
            "mnt_info": mnt_info }

def update_adg_status(request):
    '''广告组批量更新'''
    shop_id = int(request.user.shop_id)
    adg_id_list = json.loads(request.POST.get('adg_id_list', []))
    mode = request.POST.get('mode')
    camp_id = request.POST.get('campaign_id')
    mnt_type = int(request.POST.get('mnt_type', 0))
    opter, opter_name = analysis_web_opter(request)
    adg_arg_dict = {}
    if mode == 'del':
        del_id_list, cant_del_list, ztc_del_count, error_msg = delete_adgroups(shop_id = shop_id, adgroup_id_list = adg_id_list, opter = opter, opter_name = opter_name)
        mnt_num = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
        return {'errMsg':error_msg, 'mode':mode, 'success_id_list':del_id_list, 'cant_del_list':cant_del_list, 'ztc_del_count':ztc_del_count, 'mnt_num':mnt_num}
    else:
        for adg_id in adg_id_list:
            adg_arg_dict[adg_id] = {'online_status':mode == 'start' and 'online' or 'offline'}
        success_id_list, ztc_del_list = update_adgroups(shop_id = shop_id, adg_arg_dict = adg_arg_dict, opter = opter, opter_name = opter_name)
        return {'errMsg':'', 'mode':mode, 'success_id_list':success_id_list, 'ztc_del_list':ztc_del_list}

def get_adg_status(request):
    '''获取宝贝的关键词/创意个数'''
    shop_id = int(request.user.shop_id)
    adgroup_id_list = json.loads(request.POST.get('adg_id_list', []))
    type = request.POST.get('type', 'keyword')
    result_dict = getattr(globals()[type.capitalize()], 'get_%s_count' % type)(shop_id = shop_id, adgroup_id_list = adgroup_id_list)
    return {'errMsg':'', 'type':type, 'result_dict':result_dict}

def set_adg_mobdiscount(request):
    try:
        shop_id = int(request.user.shop_id)
        campaign_id = int(request.POST.get('campaign_id'))
        adgroup_id = int(request.POST.get('adgroup_id'))
        discount = int(request.POST.get('discount'))
        opter, opter_name = analysis_web_opter(request)
        if discount > 400 or discount < 1 :
            raise Exception("bad_discount")
        Adgroup.update_adgroup_mobdiscount(shop_id, [adgroup_id], discount)
        update_adg_mobdisct_log(shop_id, campaign_id, [adgroup_id], discount, opter = opter, opter_name = opter_name)
        return {'errMsg':'', 'adgroup_id':adgroup_id, 'discount':discount}
    except Exception, e:
        if str(e) == "bad_discount":
            msg = "移动折扣必须介于1%~400%之间！"
        else:
            log.error("set_adg_mobdiscount error, shop_id=%s, e=%s" % (request.user.shop_id, e))
            msg = "设置失败，请刷新后重试！"
        return {'errMsg':msg}

def delete_adg_mobdiscount(request):
    try:
        shop_id = int(request.user.shop_id)
        adgroup_id = int(request.POST['adgroup_id'])
        campaign_id = int(request.POST['campaign_id'])
        opter, opter_name = analysis_web_opter(request)
        Adgroup.delete_adgroup_mobdiscount(shop_id, [adgroup_id])
        campaign = Campaign.objects.get(campaign_id = campaign_id)
        camp_mobdiscount = campaign.platform['mobile_discount']
        del_adg_mobdisct_log(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id, discount = camp_mobdiscount, opter = opter, opter_name = opter_name)
        return {'discount': camp_mobdiscount, 'errMsg': ''}
    except Exception, e:
        log.error("del_adg_mobdiscount error, shop_id=%s, e=%s" % (request.user.shop_id, e))
        return {'discount':0, 'errMsg':'设置失败，请刷新后重试！'}

def get_campaign_list(request):
    """获取计划列表"""
    shop_id = int(request.user.shop_id)
    campaign_list = Campaign.objects.filter(shop_id = shop_id).order_by('campaign_id')
    start_date = request.POST.get('start')
    end_date = request.POST.get('end')
    camp_rpt_dict = {}
    mnt_list = MntCampaign.objects.only('campaign_id', 'mnt_index', 'mnt_type', 'start_time').filter(shop_id = shop_id)
    mnt_dict = {mnt.campaign_id:(mnt.mnt_index, mnt.mnt_type, mnt.get_mnt_type_display(), days_diff_interval(mnt.start_time.date())) for mnt in mnt_list}
    adg_num_dict = Adgroup.get_adgroup_count(shop_id = shop_id)
    json_campaign_list = []
    init_mnt_list = (0, 0, '', 0)
    is_rt_camp = 0

    # if last_day == 0: #如果下拉框选择的是实时数据
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

def update_camps_status(request):
    '''修改计划状态 add by tianxiaohe 20151008'''
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

def modify_camp_title(request):
    """设置计划名称 add by tianxiaohe 20151008"""
    errMsg = ''
    shop_id = request.user.shop_id
    new_title = request.POST['new_title']
    campaign_id = int(request.POST['camp_id'])
    opter, opter_name = analysis_web_opter(request)
    # 判断计划名称长度
    if get_char_num(new_title) > 20:
        errMsg = '计划名称不能超过40个字符'
        return {'errMsg':errMsg}

    # 修改名称
    result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = campaign_id, title = new_title, opter = opter, opter_name = opter_name)
    if 'title' in result_list:
        json_result_data = {'status':1, 'camp_id':campaign_id, 'new_title':new_title}
        CacheAdpter.delete(CacheKey.WEB_MNT_MENU % shop_id, 'web')
    else:
        json_result_data = {'status':0, 'err':'<br/>'.join(msg_list)}
        log.info('modify_camp_title error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, '<br/>'.join(msg_list)))
    return {'errMsg':errMsg, 'json_result_data':json_result_data}

def modify_camp_budget(request):
    '''修改日限额 add by tianxiaohe 20151008'''
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

def sign_point(request):
    """签到"""
    shop_id = request.user.shop_id

    is_valid, msg, data = Sign.add_point_record(shop_id = shop_id)

    result = {'data':data, 'msg':msg, 'errMsg':''}
    return result

def show_camp_trend(request):
    """显示计划趋势数据 add by tianxiaohe 20151008"""
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    camp = Campaign.objects.filter(shop_id = shop_id, campaign_id = camp_id)[0]
    errMsg = ''
    rpt_list = camp.get_snap_list(rpt_days = 7)
    if rpt_list:
        category_list, series_cfg_list = get_trend_chart_data(data_type = 2, rpt_list = rpt_list)
        return {'errMsg':errMsg, 'category_list':category_list, 'series_cfg_list':series_cfg_list}
    else:
        errMsg = '没有趋势数据，请确认计划是否参与推广'
        return {'errMsg':errMsg}

def get_camp_schedule(request):
    """分时折扣设置 add by tianxiaohe 20151008"""
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    result = {'errMsg':'', 'camp_id':camp_id, 'schedule_str': ''}
    try:
        camp = Campaign.objects.get(shop_id = shop_id, campaign_id = camp_id)
        if camp:
            result.update({'schedule_str': camp.schedule})
    except:
        result.update({'errMsg': '获取分时折扣设置失败，请联系顾问！'})
    return result

def get_camp_platform(request):
    '''获取投放平台 add by tianxiaohe 20151009'''
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    camp = Campaign.objects.get(shop_id = shop_id, campaign_id = camp_id)
    can_set_nonsearch = 0
    if request.user.shop_type == 'B' or request.user.credit > 250:
        can_set_nonsearch = 1
    return {'errMsg':'', 'camp_id':camp_id, 'platform':camp.platform, 'can_set_nonsearch': can_set_nonsearch}

def update_camp_platform(request):
    '''设置投放平台 add by tianxiaohe 20151009'''
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    platform_dict = json.loads(request.POST.get('platform_dict', ''))
    opter, opter_name = analysis_web_opter(request)
    try:
        pt_dict = Campaign.fromat_platform(platform_dict)
        result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = camp_id, opter = opter, opter_name = opter_name, **pt_dict)
        is_success = result_list and 1 or 0
        CacheAdpter.delete(CacheKey.WEB_CAMPAIGN_PLATFORM % camp_id, 'web')
        return {'errMsg':'', 'is_success':is_success, 'msg_list':msg_list, 'result_list':result_list}
    except:
        return {'errMsg':'设置投放平台失败，请联系顾问！'}

def update_camp_schedule(request):
    """修改分时折扣数据"""
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    schedule_str = request.POST.get('schedule_str', '')
    opter, opter_name = analysis_web_opter(request)
    error_msg = ''
    try:
        result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = camp_id, schedule = schedule_str, opter = opter, opter_name = opter_name)
        error_msg = ','.join(msg_list)
        return {'errMsg':error_msg}
    except:
        return {'errMsg':'设置分时折扣失败，请联系顾问'}

def get_camp_area(request):
    '''获取投放地域 '''
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    camp = Campaign.objects.get(shop_id = shop_id, campaign_id = camp_id)
    area_str = camp.area
    return {'errMsg':'', 'camp_id':camp_id, 'area':camp.area}

def update_camp_area(request):
    '''设置投放地域 '''
    try:
        shop_id = int(request.user.shop_id)
        camp_id = int(request.POST['camp_id'])
        area_ids = request.POST.get('area_ids')
        area_names = request.POST.get('area_names')
        opter, opter_name = analysis_web_opter(request)
        result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = camp_id, area = area_ids, area_names = area_names, opter = opter, opter_name = opter_name)
        is_success = result_list and 1 or 0
        return {'errMsg':'', 'is_success':is_success, 'msg_list':msg_list}
    except:
        return {'errMsg':'设置投放地域失败，请联系顾问！'}

def get_aggregate_rpt(request):
    '''获取细分数据 add by tianxiaohe 20151009'''
    shop_id = int(request.user.shop_id)
    query_dict = {'shop_id': shop_id}
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    camp_id = int(request.POST.get('camp_id', 0))
    if request.POST.get('camp_id', 0):
        query_dict['campaign_id'] = camp_id
    source_list = [1, 2, 4, 5]
    camp_rpt_list = []
    if start_date == datetime.date.today().strftime('%Y-%m-%d'):
        rpt_dict = RealtimeReport.get_split_rtrpt(rpt_type = 'campaign', args_list = [shop_id])
        camp_rpt_list = rpt_dict.get(camp_id, [])
    else:
        camp_rpt_list = Campaign.Report.get_split_rpt(query_dict = query_dict, group_keys = 'campaign_id,source', start_date = start_date, end_date = end_date, source = {'$in':source_list}, search_type = {'$in':[0, 2]})

    result = []
    for tmp_rpt in camp_rpt_list:
        tmp_data = {'campaign_id': camp_id, 'source_id': tmp_rpt.source}
        tmp_data.update(tmp_rpt.to_dict())
        result.append(tmp_data)

    return {'errMsg':'', 'result':result}

def is_data_ready(request):
    '''等待页面查看数据是否已经准备好'''
    if not request.user.is_authenticated():
        # dajax.script('window.location.href="%s";' % (settings.WEB_AUTH_URL)) # TODO: zhangyu 20140411 千牛用户跳转到了Web，需要跳转到一个公共的地方
        return {'errMsg':'', 'redicrect':settings.WEB_AUTH_URL}

    smt = ShopMngTask.objects.get(shop_id = request.user.shop_id)
    if smt.status != 2:
        del_cache_progress(request.user.shop_id)
        return {'errMsg':'', 'finished':True}
    else:
        ststus_dict = { 'struct_account_downing':['struct', 1, '正在下载账户报表数据'], 'struct_account_finished':['struct', 10, '账户报表下载完成'],
                        'struct_campaign_downing':['struct', 11, '正在下载计划结构数据'], 'struct_campaign_finished':['struct', 20, '计划结构数据下载完成'],
                        'struct_adgroup_downing':['struct', 21, '正在下载推广组结构数据'], 'struct_adgroup_finished':['struct', 30, '推广结构组数据下载完成'],
                        'struct_creative_downing':['struct', 31, '正在下载创意结构数据'], 'struct_creative_finished':['struct', 40, '创意结构数据下载完成'],
                        'struct_keyword_downing':['struct', 41, '正在下载关键词，数据较多，时间可能较长'], 'struct_keyword_finished':['struct', 60, '关键结构词数据下载完成'],
                        'struct_item_downing':['struct', 61 , '正在下载宝贝结构数据'], 'struct_item_finished':['struct', 70, '宝贝结构数据下载完成'],
                        'report_account_downing':['report', 71, '正在下载账户报表数据'], 'report_account_finished':['report', 80, '账户报表下载完成'],
                        'report_campaign_downing':['report', 81, '正在下载计划报表数据'], 'report_campaign_finished':['report', 90, '计划报表下载完成'],
                        'report_adgroup_downing':['report', 91, '正在下载推广组报表数据'], 'report_adgroup_finished':['report', 100, '推广组报表下载完成'],
                        }

        key = get_cache_progress(request.user.shop_id)
        if key and ststus_dict.has_key(key):
            pclass, progress, msg = ststus_dict[key]
            return {'errMsg':'', 'msg':msg, 'progress':progress, 'finished': progress == 100 and True or False}
        return {'errMsg':'数据下载过程出错，请联系工作人员解决'}


# 关键词列表
def adgroup_optimize(request):
    # import time
    # st = time.time()
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST.get('campaign_id'))
    adgroup_id = int(request.POST.get('adgroup_id'))
    # rpt_days = int(request.POST.get('rpt_days', 7))
    stgy = request.POST.get('stgy', 'default') # ['default', 'plus', 'fall']
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    source = request.POST.get('source', 'all') # 汇总 all 计算机 pc 移动 mobile
    summary_rpt_dict = {'source':-1, 'mobile': 0, 'pc': 1}
    summary_rpt = summary_rpt_dict.get(source, -1)

    strategy_dict = {'plus': 'IncreaseCost', 'fall': 'ReduceCost2'}
    strategy_name = strategy_dict.get(stgy, '')

    adg, kw_list = bulk_optimize_4adgroup2(shop_id, campaign_id, adgroup_id, start_date, end_date, strategy_name, summary_rpt = summary_rpt)
    result_list = []
    for kw in kw_list:
        # setattr(kw, 'campaign', adg.campaign)
        # setattr(kw, '_adgroup', adg)
        temp_kw = {
            "keyword_id": kw.keyword_id,
            "adgroup_id": kw.adgroup_id,
            "campaign_id": kw.campaign_id,
            "word": kw.word,
            "mnt_opt_type": kw.mnt_opt_type or 0,
            "create_days": kw.create_days,
            "max_price": format(kw.max_price_pc / 100.0, '.2f'),
            "new_price": format((kw.new_price_pc or kw.max_price_pc) / 100.0, '.2f'),
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
            "label_code": kw.label_code,
            "tree_code": kw.tree_code,
            "optm_reason": kw.optm_reason,
            "optm_type": kw.optm_type,
            "optm_type_pc": kw.optm_type_pc,
            "optm_type_mobile": kw.optm_type_mobile,
            "is_focus": kw.is_focus and 1 or 0,
            "is_locked": kw.is_locked and 1 or 0,
            "max_mobile_price": format(kw.max_price_mobile / 100.0, '.2f'),
            "new_mobile_price": format((kw.new_price_mobile or kw.max_price_mobile) / 100.0, '.2f'),
            "is_default_price":kw.is_default_price,
            "mobile_is_default_price":kw.mobile_is_default_price
        }
        temp_kw.update(kw.rpt.to_dict())
        result_list.append(temp_kw)
    # result_list.sort(key = lambda x:x['optm_type'], reverse = True)
    result_list = sorted(result_list, key = itemgetter('optm_type', 'optm_type_pc', 'optm_type_mobile'), reverse = True)
    custom_column = Account.get_custom_col(shop_id)

    adg_nosch_rpt = adg.get_summed_nosch_rpt(start_date = start_date, end_date = end_date)
    nosearch_data = {
        "favctr":format(adg_nosch_rpt.favctr, '.2f'),
        "favpay":format(adg_nosch_rpt.favpay, '.2f'),
        "cpm": format(adg_nosch_rpt.cpm / 100.0, '.2f')
    }
    nosearch_data.update(adg_nosch_rpt.to_dict())
    # log.info("total cost %s" % (time.time() - st))
    # bulk_tree_list 参数可以去掉，现在没用到该参数
    return {'keyword_list': result_list, 'nosearch_rpt': nosearch_data, 'set_mnt_flag': adg.mnt_type != 0 and True or False, 'bulk_tree_list': [], 'bulk_search_list': adg.bulk_search_list, 'custom_column': custom_column, 'errMsg': ''}

def show_kw_trend(request):
    adgroup_id = int(request.POST['adgroup_id'])
    keyword_id = int(request.POST['keyword_id'])

    snap_dict = Keyword.Report.get_snap_list({'adgroup_id': adgroup_id, 'keyword_id': keyword_id}, rpt_days = 30)
    snap_list = snap_dict.pop(keyword_id, [])
    if snap_list:
        category_list, series_cfg_list = get_trend_chart_data(data_type = 4, rpt_list = snap_list)
        err_msg = ''
    else:
        category_list, series_cfg_list = [], []
        err_msg = "没有趋势数据"
    return {'category_list': category_list, 'series_cfg_list': series_cfg_list, 'errMsg': err_msg}


def forecast_realtime_rank(request):
    """根据关键词的出价，预测排名"""
    adg_id = int(request.POST['adgroup_id'])
    keyword_id = int(request.POST['keyword_id'])
    price = round(float(request.POST.get('price', 0)), 2)
    # is_check_rank = int(request.POST.get('is_check_rank', 0))
    times = 0
    tapi = get_tapi(request.user)
    while times < 2:
        result_data = Keyword.get_rt_kw_rank(tapi = tapi, adg_id = adg_id, price = int(price * 100), kw_id = keyword_id)
        if 'pc_rank' in result_data and 'mobile_rank' in result_data:
            break
        times = times + 1

    # 如果还为空给个默认值
    if not ('pc_rank' in result_data and 'mobile_rank' in result_data):
        result_data['pc_rank'] = ">100"
        result_data['mobile_rank'] = ">100"

    return {'data': result_data, 'errMsg': ''}


def set_adg_limit_price(request):
    '''保存用户设置关键词的最高限价'''
    err_msg = ''
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    limit_price = int(round(float(request.POST.get('limit_price', 0)) * 100))
    mobile_limit_price = int(round(float(request.POST.get('mobile_limit_price', 0)) * 100))
    mopter, opter_name = analysis_web_opter(request)
    try:
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        old_limit_price = adgroup.limit_price
        old_mobile_limit_price=adgroup.mobile_limit_price
        if limit_price or mobile_limit_price:
            if limit_price:
                adgroup.limit_price = limit_price
            if mobile_limit_price:
                adgroup.mobile_limit_price = mobile_limit_price
            adgroup.use_camp_limit = 0 # 目前只有千牛调用该接口，临时处理
            adgroup.save()

            if limit_price:
                if old_limit_price:
                    opt_desc = 'PC最高限价由%.2f元，改为%.2f元' % (float(old_limit_price) / 100, float(limit_price) / 100)
                else:
                    opt_desc = 'PC最高限价设置为%.2f元' % (float(limit_price) / 100)

            if mobile_limit_price:
                if old_mobile_limit_price:
                    opt_desc = '移动最高限价由%.2f元，改为%.2f元' % (float(old_mobile_limit_price) / 100, float(mobile_limit_price) / 100)
                else:
                    opt_desc = '移动最高限价设置为%.2f元' % (float(mobile_limit_price) / 100)
            change_adg_maxprice_log(shop_id, adgroup.campaign_id, adgroup_id, adgroup.item.title, opt_desc, opter = mopter, opter_name = opter_name)
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = adgroup.campaign_id, mnt_type = adgroup.mnt_type, task_type = 2, adgroup_id_list = [adgroup_id])
    except Exception, e:
        log.error('set_adg_limit_price exception err=%s' % (e))
        err_msg = "设置失败，请联系顾问！"
    return {'data': True, 'errMsg': err_msg}

def save_custom_column(request):
    shop_id = int(request.user.shop_id)
    try:
        column_list = map(str, request.POST.getlist('column[]'))
        if not column_list:
            column_list = ['all']
        Account.save_custom_col(shop_id, column_list)
        err_msg = ''
    except ValueError:
        err_msg = "设置失败，请刷新后重试"
    return {'data': True, 'errMsg': err_msg}


def submit_keyword_optimize(request):
    """提交关键词改动"""
    shop_id = int(request.user.shop_id)
    kw_list = json.loads(request.POST.get('submit_list', ''))
    update_mnt_list = json.loads(request.POST.get('update_mnt_list', ''))
    optm_type = request.POST.get('optm_type', '')
    opter, opter_name = analysis_web_opter(request)
    updated_id_list, deleted_id_list, top_deleted_id_list, failed_id_list = update_kws_8shopid(shop_id, kw_list, optm_type = optm_type, opter = opter, opter_name = opter_name)
    mnt_change_kwid_list = []
    if update_mnt_list:
        mnt_change_kwid_list = Keyword.update_kw_mntopt_type(update_mnt_list)
    return {'del_kw':deleted_id_list, 'update_kw':updated_id_list, 'failed_kw':failed_id_list, 'top_del_kw':top_deleted_id_list, 'mnt_change_kw':mnt_change_kwid_list, 'errMsg':''}

def get_praise(request):
    """获取评价词"""
    content, errMsg = '', ''
    try:
        # 获取随机好评
        appraises = AppComment.objects.filter(service_code = 'ts-25811', is_recommend = 1).order_by('?')
        if appraises and appraises[0] is not None:
            content = appraises[0].suggestion
        else:
            errMsg = '亲,系统有点小忙,请稍候再试试吧.'
    except Exception, e:
        errMsg = '亲,系统有点小忙,请稍候再试试吧.'

    return {'data':content, 'errMsg':errMsg}

def get_adg_split_rpt(request):
    '''获取细分数据 '''
    shop_id = int(request.user.shop_id)
    query_dict = {'shop_id': shop_id}
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    adgroup_id = int(request.POST.get('adgroup_id', 0))
    camp_id = int(request.POST.get('camp_id', 0))
    if request.POST.get('adgroup_id', 0):
        query_dict['adgroup_id'] = adgroup_id

    if start_date == end_date == datetime.date.today().strftime('%Y-%m-%d'):
        adg_rpt_dict = RealtimeReport.get_split_rtrpt(rpt_type = 'adgroup', args_list = [shop_id, camp_id])
        adg_rpt_list = adg_rpt_dict.get(adgroup_id, [])
    else:
        adg_rpt_list = Adgroup.Report.get_split_rpt(query_dict = query_dict, group_keys = 'adgroup_id,source', start_date = start_date, end_date = end_date, source = {'$in':[1, 2, 4, 5]}, search_type = {'$in':[0, 2]})
    result = []
    for tmp_rpt in adg_rpt_list:
        tmp_data = {'adgroup_id': adgroup_id, 'source_id': tmp_rpt.source}
        tmp_data.update(tmp_rpt.to_dict())
        result.append(tmp_data)
    return {'errMsg':'', 'result':result}

def show_adg_trend(request):
    """显示推广组趋势数据 """
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST['adgroup_id'])
    campaign_id = int(request.POST['campaign_id'])
    start_date = str(request.POST['start_date'])
    end_date = str(request.POST['end_date'])
    snap_dict = Adgroup.Report.get_snap_list({'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adgroup_id}, start_date = start_date, end_date = end_date)
    snap_list = snap_dict.pop(adgroup_id, [])
    if snap_list:
        category_list, series_cfg_list = get_trend_chart_data(data_type = 2, rpt_list = snap_list)
        return {'errMsg':'', 'category_list':category_list, 'series_cfg_list':series_cfg_list}
    else:
        return {'errMsg':'没有趋势数据，请确认宝贝是否参与推广'}

def get_recommend_price(request):
    """获取全自动托管的推荐日限额与最高限价"""

    def get_credit_ratio():
        credit = int(request.user.credit)
        credit_cfg_dict = [{'base': 50, 'rate': 1.0 },
                           {'base': 100, 'rate': 1.2 },
                           {'base': 200, 'rate': 1.5 },
                           {'base': 500, 'rate': 2.0 }]

        credit_level = [0, 250, 10000, 50000]
        index = 0
        for index, value in enumerate(credit_level):
            if credit > value:
                continue
            else:
                index -= 1
                break

        cfg_dict = credit_cfg_dict[index]

        if mnt_type in [2, 4]:
            return cfg_dict['base'] * cfg_dict['rate']
        else:
            return cfg_dict['base']

    def get_cat_cpc(shop_id):
        account = Account.objects.get(shop_id = shop_id)
        # acct_rpt = account.get_summed_rpt(rpt_days = 7)
        cat_stat_info = CatStatic.get_market_data(cat_id_list = [account.cat_id]).values()[0]
        cat_cpc = round(cat_stat_info['cpc'] * 0.01, 2)
        cat_cpc = cat_cpc or 1.0
        # camp_rpt = camp.get_summed_rpt(rpt_days = 7)
        # return max(acct_rpt.cpc / 100.0 * rate, cat_cpc * rate, camp_rpt.cpc / 100.0 * rate, default_max_price), cat_cpc
        return cat_cpc

    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST.get('campaign_id'))
    mnt_type = int(request.POST.get('mnt_type', 1))

    cat_cpc = get_cat_cpc(shop_id)
    camp = Campaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
    camp_budget = camp.budget == 2000000000 and 200000 or camp.budget # 日限额不限时，给2000
    budget = min(max(get_credit_ratio(), camp_budget / 100), 3000)
    return {'cat_cpc': cat_cpc, 'budget': budget, 'errMsg':''}

def get_item_imgs(request):
    '''获取宝贝图片'''
    app = request.POST.get('app', 'web')
    if app == 'crm':
        shop_id = int(request.POST['shop_id'])
    else:
        shop_id = int(request.user.shop_id)
    try:
        item_id_list = json.loads(request.POST['item_id_list'])
        context = request.POST.get('context', '')
        # 调API批量获取宝贝图片
        if app == 'crm':
            item_dict = Item.get_item_image_byshopid(shop_id, item_id_list)
        else:
            item_dict = Item.get_item_image_byuser(request.user, item_id_list)
        return {'errMsg':'', 'item_dict':item_dict, 'context':context}
    except Exception, e:
        log.error('get_item_imgs error, shop_id=%s, error=%s' % (shop_id, e))
        return {'errMsg':'获取宝贝信息失败，请联系客服'}

def getorcreate_adg_title_list(request):
    '''获取创意标题 add by tianxiaohe 20151015'''
    result = {}
    type = 1
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
            if adgroup_id:
                type = 1
                adg_title_list = [{}, ''] # adg_title_list 由已有创意列表和新增创意标题组成
                creative_cursor = crt_coll.find({'shop_id':shop_id, 'adgroup_id':adgroup_id}, {'title':1, 'img_url':1})
                adg_title_list[0] = {str(cur['_id']):[cur['title'], handle_img_url(cur['img_url'])] for cur in creative_cursor}
                if len(adg_title_list[0]) == 0:
                    type = 0
                    adg_title_list = TitleTransfer.generate_adg_title_list(shop_id, item_id, item_title)
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
            result = {'errMsg':'', 'adg_title_list':json.dumps(adg_title_list), 'item_id':item_id, 'type':type}
    return result

def point_detial(request):
    """积分详情"""
    page = request.POST.get('page', 1)
    shop_id = request.user.shop_id

    # 用户积分记录
    detial_list = PointManager.get_point_detail(shop_id = shop_id)

    page_info, detial_list = pagination_tool(page = page, record = detial_list, page_count = 10)

    # 挂在 type_desc
    for ac_info in detial_list:
        ac_info['type_desc'] = PointManager.get_type_desc(ac_info['type'])

    data = {
        'detial_list': detial_list,
        'page_info': page_info
    }

    return {'data':data, 'errMsg':''}

def perfect_info(request):
    """完善信息"""
    customer = request.user.customer
    _, errMsg = customer.update_perfect_info(data_dict = request.POST)
    # 更新session
    request.session['phone'] = customer.phone

    # todo yangrongkai 此处可能后期会考虑通过该接口，添加 “验证会员” 积分获取操作
    return {'errMsg':errMsg}

def user_info(request):
    """获取用户信息"""
    # 判断用户是否完善信息
    customer = request.user.customer
    is_perfect_info, perfect_info = False, {}
    if customer:
        is_perfect_info = customer.is_perfect_info
        perfect_info = customer.perfect_info
    return {'errMsg':'', 'is_perfect_info':is_perfect_info, 'info_dict':perfect_info}

def customer_info(request):
    """获取客户信息"""
    customer = Customer.objects.filter(shop_id = request.user.shop_id).only('phone', 'qq')
    return {'data':customer, 'errMsg':''}

def freeze_point(request):
    """冻结积分"""
    _, freeze_point_deadline = Account.freeze_point(shop_id = request.user.shop_id, nick = request.user.nick)
    return {'errMsg':'', 'freeze_point_deadline':freeze_point_deadline.strftime('%Y-%m-%d')}

def convert_virtual(request):
    """兑换虚拟物品"""
    shop_id = request.user.shop_id
    gift_id = int(request.POST.get('gift_id', 0))

    _, errMsg, data = Virtual.add_point_record(shop_id = shop_id, gift_id = gift_id)

    return {'data':data, 'remind':errMsg, 'errMsg':""}

def convert_gift(request):
    """兑换实物"""
    shop_id = request.user.shop_id
    gift_id = int(request.POST.get('gift_id', 0))

    _, errMsg, data = Gift.add_point_record(shop_id = shop_id, gift_id = gift_id)

    return {'data':data, 'remind':errMsg, "errMsg":""}

def generate_link(request):
    """生成兑换链接"""
    shop_id = request.user.shop_id
    nick = request.user.nick
    template_id = int(request.POST.get('temp_id', 0))

    order_temp = OrderTemplate.get_ordertemplate_byid(template_id)
    url , errMsg = "", ""
    if order_temp: # 下面代码注意顺序
        try:
            tapi = get_tapi(shop_id = shop_id)
            url = order_temp.generate_order_link(nick, tapi)
        except Exception, e:
            log.exception('recommend_link_gen, nick=%s, e=%s' % (nick, e))
            errMsg = "生成链接失败，请联系顾问"
        else:
            if url:
                is_valid, errMsg, result = Discount.add_point_record(shop_id = shop_id, order_template = order_temp)
                url = url if is_valid else ""
    else:
        errMsg = "不存在该版本"

    return {'errMsg':errMsg, 'url':url}

def recommend_link(request):
    """生成推荐链接"""
    shop_id = request.user.shop_id
    nick = request.POST.get('nick')
    order_version = request.POST.get('order_version')
    order_cycle = int(request.POST.get('order_cycle', 0))

    tp_cursor = OrderTemplate.get_recommend_ordertemplate(version = order_version, cycle = order_cycle)
    order_temp , errMsg , current_price, original_price = None, "", 0, 0
    if tp_cursor.count():
        order_temp = tp_cursor[0]

    url = ""
    if order_temp:
        current_price, original_price = order_temp.cur_price , order_temp.ori_price
        try:
            tapi = get_tapi(shop_id = shop_id)
            url = order_temp.generate_order_link(nick, tapi)
        except Exception, e:
            log.exception('recommend_link_gen, nick=%s, e=%s' % (nick, e))
            errMsg = "店铺主旺旺不存在，请关闭对话框，检查店铺主旺旺。"
    else:
        errMsg = "不存在该版本"

    return {'errMsg':errMsg, 'url':url,
            'current_price':"{0:.2f}".format(current_price / 100.0),
            'original_price':"{0:.2f}".format(original_price / 100.0)}

def check_link_permission(request):
    shop_id = int(request.user.shop_id)
    invited_nick = request.POST.get("nick", "")
    invited_shop_id = User.get_shopid_or_nick(invited_nick)

    error_info = ""
    if invited_shop_id:
        invited_shop_id = int(invited_shop_id)
        order_cursor = Subscribe.query_servicing_subscribe((invited_shop_id,), ('kcjl', 'rjjh', 'vip'))
        if order_cursor.count():
            error_info = "亲，该小伙伴已经是精灵服务中用户哦，还是推荐一个新用户吧！"

    if not error_info and Promotion4Shop.promotion_record_exists(shop_id, invited_nick) :
        error_info = "亲，该小伙伴之前的推荐链接还没有订购，请让他先订购哦！"

    return {'error_info':error_info, "errMsg":""}

def promotion_4shop(request):
    """邀请方式1，指定店铺送积分,存入主推人信息"""
    shop_id = request.user.shop_id
    invited_name = request.POST.get('invited_name')
    order_version = request.POST.get('order_version')
    order_cycle = request.POST.get('order_cycle')
    current_price = request.POST.get('current_price')
    original_price = request.POST.get('original_price')
    url = request.POST.get('url')

    errMsg, data = "", None

    is_check = Promotion4Shop.is_exists(shop_id = shop_id, invited_name = invited_name, order_version = order_version, order_cycle = order_cycle)
    if is_check is False:
        _, errMsg, data = Promotion4Shop.add_point_record(shop_id = shop_id, invited_name = invited_name, order_version = order_version, order_cycle = order_cycle, current_price = current_price, original_price = original_price, url = url)
    return {'errMsg':errMsg, 'data':data}

def point_records(request):
    """获取积分记录"""
    record_type = request.POST.get('type')
    result = pa_coll.find({'shop_id':int(request.user.shop_id), 'type':record_type}).sort("create_time", -1)
    return {'errMsg':'', 'data':list(result)}

def receive_recount(request):
    """新用户填写推荐人"""
    guide_name = request.POST.get('guide_name')
    shop_id = request.user.shop_id
    _, errMsg, data = Invited.add_point_record(shop_id = shop_id, guide_name = guide_name)

    return {'errMsg':errMsg, 'point':data and data['point'] or 0}

def select_keyword(request):
    """选词"""
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    select_type = request.POST.get('select_type', 'quick')
    max_add_num = int(request.POST.get('max_add_num'))
    errorMsg = ''
    try:
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        item = adgroup.item
    except:
        return {'errMsg':'请确认该宝贝是否已经删除或者下架!', 'data':{}}
    candidate_keyword_list = []
    if select_type == 'quick':
        select_arg = ''
        # 选词
        candidate_keyword_list = KeywordSelector.get_quick_select_words(item, adgroup)
    elif select_type == 'precise':
        select_arg = request.POST.get('word_filter', '').strip().lower()
        word_match = re.match(ur'^[\u4e00-\u9fa5\s,，a-zA-Z0-9]+$', select_arg)
        if not word_match:
            return {'errMsg':'核心词不能为空，且只能包含中文、字母、数字、空格、中英文逗号!', 'data':{}}
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



    okay_count, temp_keyword_list, filter_field_list = SelectKeywordPackage.recommand_by_system(max_add_num, candidate_keyword_list)
    keyword_list = KeywordSelector.get_all_package_keyword(candidate_keyword_list, temp_keyword_list)

    data = {
          'keyword_list':keyword_list,
          'okay_count':okay_count,
          'filter_field_list':filter_field_list,
          'select_type':select_type,
          }
    return {'errMsg':errorMsg, 'data':data}


def mobile_package(request):
    """
    .获取关键词的移动数据
    """
    keyword_list , errorMsg = [], ''
    word_list = eval(request.POST.get('word_list', '[]'))
    tmp_list = SelectKeywordPackage.mobile_package(word_list)
    okay_count, temp_keyword_list, filter_field_list = SelectKeywordPackage.recommand_by_system(200, tmp_list)
    for kw in temp_keyword_list:
        tmp_kw = [kw.word, kw.cat_cpc or 30, kw.cat_pv, kw.cat_click, kw.cat_ctr, kw.cat_competition, kw.keyword_score, kw.new_price or 30, kw.coverage, kw.is_delete, 0, []]
        tmp_kw[10] = getattr(kw, 'is_ok', 0)
        keyword_list.append(tmp_kw)
    data = {
      'keyword_list':sorted(keyword_list, key = lambda x:x[3], reverse = True)[:200],
      'okay_count':okay_count,
      'filter_field_list':filter_field_list,
      'select_type':'',
      }
    return {'errMsg':errorMsg, 'data':data}

def batch_add_keywords(request):
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    keyword_count = int(request.POST.get('keyword_count'))
    kw_arg_list = json.loads(request.POST.get('kw_arg_list', '[]'))
    # init_limit_price = int(float(request.POST.get('init_limit_price', 1)) * 100) # 选词时不保存该值
    errorMsg, added_keyword_count, remove_dataTable_keywords, result_mesg = '', 0, '', ''
    # 托管宝贝的关键词限价后台校验

    try:
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        if adgroup.mnt_type in [1, 2, 3, 4]:
            limit_price = adgroup.get_keyword_limit_price()
            for kw_arg in kw_arg_list:
                kw_arg[1] = min(limit_price, kw_arg[1])
    except DoesNotExist:
        errorMsg = "该宝贝可能不存在或者下架，请尝试同步数据"
    if not errorMsg:
        opter, opter_name = analysis_web_opter(request)
        # if init_limit_price > 5:
        #     try:
        #         adg_coll.update({'shop_id':shop_id, '_id':adgroup_id}, {'$set':{'limit_price':init_limit_price}})
        #     except Exception, e:
        #         log.error('set_adg_limit_price dose not exist err=%s' % e)
        #         pass

        result_mesg, added_keyword_list, repeat_word_list = add_keywords(shop_id, adgroup_id, kw_arg_list, opter = opter, opter_name = opter_name)
        added_keyword_count = len(added_keyword_list)
        if added_keyword_count > 0:
            kw_list_key = 'kw_list_4add_' + str(adgroup_id)
            CacheAdpter.delete(kw_list_key, 'web')
        if not result_mesg:
            result_mesg = u'已添加成功%s个%%s。' % added_keyword_count
            if added_keyword_count + keyword_count > 197:
                result_mesg = result_mesg % ''
            else:
                result_mesg = result_mesg % (u'，失败%s个(被判定为重复词)' % (len(kw_arg_list) - added_keyword_count))
        remove_dataTable_keywords = json.dumps([kw_arg[0] for kw_arg in kw_arg_list])
    data = {
      'added_keyword_count':added_keyword_count,
      'remove_dataTable_keywords':remove_dataTable_keywords,
      'result_mesg':result_mesg,
      }
    return {'errMsg':errorMsg, 'data':data}

def get_rpt_detail(request):
    '''获取报表明细'''
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

    shop_id = int(request.POST['shop_id'])
    source = request.POST.get('source', 'all') # 汇总 all 计算机 pc 移动 mobile
    errorMsg = ''
    category_list, series_cfg_list = [], []
    rpt_list = []
    tpl_type = 0
    type_model_dict = {
                      'account':[Account, 'shop_id', 0], # [模型，片键，主键，模板编号]
                      'campaign':[Campaign, 'shop_id', 'campaign_id', 0],
                      'adgroup':[Adgroup, 'shop_id', 'adgroup_id', 0],
                      'creative':[Creative, 'shop_id', 'creative_id', 1],
                      'keyword':[Keyword, 'adgroup_id', 'keyword_id', 1],
                      }
    try:
        obj_type = request.POST['type']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        obj_args = type_model_dict[obj_type]
        query_dict = {arg:int(request.POST[arg]) for arg in obj_args[1:-1]}
        tpl_type = obj_args[-1]

        # 每日数据
        snap_list = obj_args[0].Report.get_snap_list(query_dict, start_date = start_date, end_date = end_date).values()
        if snap_list:
            snap_list = snap_list[0]
        category_list, series_cfg_list = get_trend_chart_data(data_type = 1, rpt_list = snap_list)
        snap_list.reverse()

        # 每日细分数据
        split_dict = {}
        if tpl_type == 0:
            split_list = obj_args[0].Report.get_split_rpt(query_dict, 'date,source', start_date = start_date, end_date = end_date, source = {'$in':[1, 2, 4, 5]}, search_type = {'$in':[-1, 0, 2]})
            src_dict = {1:'pcin', 2:'pcout', 4:'ydin', 5:'ydout'}
            for rpt in split_list:
                dt, src = rpt.pop('date').strftime('%Y-%m-%d'), rpt.pop('source')
                _rpt_dict = split_dict.setdefault(dt, {'pcin':'', 'pcout':'', 'ydin':'', 'ydout':''})
                _rpt_dict[src_dict[src]] = format_report(rpt)

        for rpt in snap_list:
            dt = rpt.pop('date').strftime('%Y-%m-%d')
            temp_dict = {'date':dt, 'summed':format_report(rpt)}
            if tpl_type == 0:
                _rpt_dict = split_dict.get(dt, {'pcin':'', 'pcout':'', 'ydin':'', 'ydout':''})
                temp_dict.update(_rpt_dict)
            rpt_list.append(temp_dict)
    except Exception, e:
        errorMsg = '未获取到数据，请联系顾问'
        log.exception("get_rpt_detail error, shop_id=%s, e=%s" % (shop_id, e))
    return {
            'errMsg':errorMsg,
            'data':{
                    'category_list':category_list,
                    'series_cfg_list':series_cfg_list,
                    'rpt_list':rpt_list,
                    'tpl_type':tpl_type
                    }
            }


def get_rt_rpt(request):
    """获取计划实时报表数据 add by tianxiaohe 20151004"""
    update_cache = int(request.POST.get('update_cache', '0'))
    campaign_id = int(request.POST.get('campaign_id', 0))
    temp_rtrpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'campaign', args_list = [request.user.shop_id], update_now = bool(update_cache))
    rtrpt_item = temp_rtrpt_dict.get(campaign_id, Campaign.Report())
    result = rtrpt_item.to_dict()
    return {'errMsg':'', 'result':result}

def hot_zone(request):
    """用户行为分析事件统计"""
    if request.user.is_authenticated():
        shop_id = int(request.user.shop_id)
        data_dict = eval(request.POST.get('data', {}))
        if data_dict:
            HotZone.add_record({'shop_id':shop_id, 's1':data_dict.get('s1', ''), 's2':data_dict.get('s2', ''), 'page':data_dict.get('page', ''), 'create_time':datetime.datetime.now()})
    return {'errMsg':''}

def select_feedback(request):
    nick = request.POST.get('nick', '')
    cat_id = request.POST.get('cat_id', '')
    cat_name = request.POST.get('cat_name', '')
    item_title = request.POST.get('item_title', '')
    item_url = request.POST.get('item_url', '')
    prblm_descr = request.POST.get('prblm_descr', '')
    fellback_source = int(request.POST.get('fellback_source', 0))
    if not prblm_descr:
        return {'errMsg':'请正确填写反馈信息，谢谢', 'data':{}}
    if not(nick and cat_id and item_title and item_url):
        return {'errMsg':'反馈信息失败，请联系精灵客服！', 'data':{}}
    SelectKeywordFellBack(nick = nick, cat_id = cat_id, cat_name = cat_name, item_title = item_title, item_url = item_url, prblm_descr = prblm_descr, fellback_source = fellback_source).save()
    email_list = ['liushengchuan@paithink.com', 'zy@paithink.com', 'wangjin@paithink.com', 'wujie@paithink.com', 'qiumengxue@paithink.com', 'wuyang@paithink.com', 'liucaiyan@paithink.com']
    # 发送邮件提醒
    content = '''
    <a href="http://crm01.ztcjl.com/toolkit/select_keyword_order/" target="_blank">打开选词预览</a><br>
    来源：%s<br>
   备注：如果解决不了，请联系当前纵队的人机小组组长<br>
    店铺名称：%s<br>
    类目名称：%s<br>
    宝贝名称：%s<br>
    宝贝链接：%s<br>
    问题描述：%s
    ''' % ('选词' if fellback_source == 1 else '选词预览', nick, cat_name, item_title, item_url, prblm_descr)
    if  fellback_source:
        try:
            cst = Customer.objects.get(nick = nick)
            pu = PSUser.objects.get(id = cst.consult_id)
            email_list.append(pu.name + '@paithink.com')
        except Exception, e:
            log.error('get ps user error and cannot find the consult the error is = %s' % e)
    send_mail('掌柜 %s 刚刚填写了选词反馈意见' % nick, '', settings.DEFAULT_FROM_EMAIL, email_list , html_message = content)

    return {'errMsg':'感谢您对于精灵的意见反馈，我们会努力做好选词，谢谢！', 'data':{}}

def to_duplicate_check(request):
    """进入重复词排查的一些提前验证"""
    # 先验证是否有权限
    result = {'errMsg': ''}
    if test_permission(DUPICATE_CODE, request.user):
        shop_id = int(request.user.shop_id)
        dler_obj, _ = Downloader.objects.get_or_create(shop_id = shop_id)
        rpt_flag, _ = dler_obj.check_status_4rpt(klass = Keyword)
        result.update({'rpt_flag': rpt_flag})
    else:
        result.update({'no_limit': True})
    return result

def dupl_kw_list(request):
    """重复词排查中获取重复词列表 add by tianxiaohe 20151113"""
    shop_id = int(request.user.shop_id)
    page_size = int(request.POST.get('page_size', 50))
    page_no = int(request.POST.get('page_no', 1))
    sort_pair = request.POST.get('sort', 'desc')

    page_start = (page_no - 1) * page_size
    page_end = page_start + page_size
    duplicate_data_list = []
    adg_obj_list = Adgroup.objects.filter(shop_id = shop_id).only('adgroup_id')
    adg_id_list = [adg.adgroup_id for adg in adg_obj_list]
    query_dict = {'shop_id':shop_id}

    if adg_id_list:
        query_dict.update({'adgroup_id':{'$in':adg_id_list}})

    data_count, duplicate_list = get_duplicate_word(query_dict = query_dict, sort_mode = sort_pair, start = page_start, end = page_end, count = 2)
    # 获取重复词及重复次数
    if duplicate_list:
        duplicate_data_list = [{'keyword':kw['word'], 'times':kw['count']} for kw in duplicate_list]

    # 获取垃圾词
    garbage_id_list = Keyword.get_garbage_words(shop_id = shop_id)

    # 获取低分词
    lowscore_id_list = Keyword.get_lowscore_words(shop_id = shop_id)

    result = {"errMsg": "",
        "data_count": data_count,
        "duplicate_data_list": duplicate_data_list,
        "garbage_words_len": len(garbage_id_list),
        "lowscore_words_len": len(lowscore_id_list)}

    return result

def dupl_kw_detail(request):
    """重复词排查中获取重复关键词详细信息 add by tianxiaohe 20151113"""
    shop_id = int(request.user.shop_id)
    keyword = request.POST.get('keyword', '')
    kw_list = list(Keyword.objects.filter(shop_id = shop_id, word = keyword))

    camp_id_list, adg_id_list, kw_id_list = [], [], []
    for kw in kw_list:
        kw_id_list.append(kw.keyword_id)
        camp_id_list.append(kw.campaign_id)
        adg_id_list.append(kw.adgroup_id)
    kw_rptdetail_dict = Keyword.get_kwrpt_dict(query_dict = {'shop_id': shop_id, 'keyword_id': {'$in':kw_id_list}}, rpt_days = 7)

    camp_list = Campaign.objects.filter(shop_id = shop_id, campaign_id__in = camp_id_list)
    camp_dict = {camp.campaign_id: camp for camp in camp_list}

    adg_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list)
    adg_dict = {adg.adgroup_id: adg for adg in adg_list}
    item_id_list = [adg.item_id for adg in adg_list]

    item_list = item_coll.find({'shop_id':shop_id, '_id':{'$in': item_id_list}}, {'title':1, 'pic_url':1, 'price':1})
    item_dict = {item['_id']:(item['title'], item['price'], item['pic_url']) for item in item_list }

    result = []
    no_item_tuple = ('该宝贝可能不存在或者下架，请尝试同步数据', 0, '/site_media/jl6/static/images/no_photo') # 当item不存在时，使用默认

    for kw in kw_list:
        kw_rpt_dict = {'impr': 0, 'click': 0, 'pay': '0.00', 'cpc': 0.00}
        if kw.keyword_id in kw_rptdetail_dict:
            kw_rpt = kw_rptdetail_dict.get(kw.keyword_id, Keyword.Report())
            kw_rpt_dict = kw_rpt.to_dict()
        temp_key = kw.adgroup_id
        if temp_key in adg_dict:
            adg = adg_dict[kw.adgroup_id]
            item_id = adg.item_id
            temp_item_info = item_dict.get(item_id, no_item_tuple)
            adg.bind_qscore(kw_list = [kw]) # 这里重复词 kw_list 中每个关键词都属于不同的 adg.

            result.append({'kw_id': kw.keyword_id, 'max_price': '%.2f' % (kw.max_price / 100.0), 'max_mobile_price': '%.2f' % (kw.get_mobile_price(adg_dict[kw.adgroup_id], camp_dict[kw.campaign_id]) / 100.0),
                           'qscore': kw.qscore_dict.get('qscore', 0), 'wireless_qscore': kw.qscore_dict.get('wireless_qscore', 0), 'impr': kw_rpt_dict['impr'], 'click': kw_rpt_dict['click'],
                           'pay': kw_rpt_dict['pay'], 'cpc': kw_rpt_dict['cpc'], 'camp_id': camp_dict[kw.campaign_id].title, 'item_title': temp_item_info[0],
                           'item_price': temp_item_info[1], 'pic_url': temp_item_info[2], 'item_id': item_id
                           })

    result = sorted(result, key = itemgetter('click', 'impr', 'qscore', 'wireless_qscore', 'kw_id'), reverse = True) # 按点击量、展现量、出价降序排序、添加时间
    return {'errMsg':'', 'result':result}

def delete_dupl_word(request):
    '''删除满足条件的重复词 add by tianxiaohe tianxiaohe 20151120'''
    shop_id = int(request.user.shop_id)
    opter, opter_name = analysis_web_opter(request)
    opter = 8
    del_type = request.POST["del_type"]
    if del_type == 'smart':
        # 智能删除垃圾词
        kw_list = Keyword.get_garbage_words(shop_id)
    elif del_type == 'manual':
        # 删除重复详情下的选中项
        kw_id_list = request.POST.getlist('kw_id_list[]')
        kw_list = get_deldetail_list(shop_id, kw_id_list)
    else:
        # 按条件删除重复词(包括一键删除低分词、重复词和手动删除重复词)
        condition = dict(json.loads(request.POST.get('condition', '{}')))
        del_qscore = condition['del_qscore'] if 'del_qscore' in condition else 0
        del_level = condition['del_level'] if 'del_level' in condition else 0
        if del_qscore:
            # 删除低分词
            kw_list = get_dellow_list(shop_id, condition)
        if del_level:
            word_list = request.POST.getlist('word_list[]') # 如果word_list 不为空，就是手动批量删除
            kw_list = get_deldupl_list(shop_id, condition, word_list)

    # 按照campaign_id分组
    camp_dict = {}
    for kw in kw_list:
        camp_dict.setdefault(kw['campaign_id'], []).append([kw['adgroup_id'], kw['_id'], kw['word'], 0, 0, ''])

    del_kw_list = []
    for camp_id, kw_arg_list in camp_dict.items():
        result_list = delete_keywords(shop_id = shop_id, campaign_id = camp_id, kw_arg_list = kw_arg_list, tapi = None, opter = opter, opter_name = opter_name)
        del_kw_list.extend(result_list)

    del_count = len(del_kw_list)
    failed_count = len(kw_list) - del_count
    return {'errMsg':'', 'del_type':del_type, 'del_count':del_count, 'failed_count':failed_count}

def get_deldetail_list(shop_id, kw_id_list = []):
    '''获取需要删除的垃圾词 add by tianxiaohe 20151123'''
    kw_id_list = [int(i) for i in kw_id_list]
    kw_cur = kw_coll.find({'shop_id':shop_id, '_id':{'$in':kw_id_list}}, {'adgroup_id':1, 'campaign_id':1, 'word':1})
    kw_list = []
    for kw in kw_cur:
        kw_list.append({'_id':kw['_id'],
                        'adgroup_id':kw['adgroup_id'],
                        'campaign_id':kw['campaign_id'],
                        'word':kw['word']
                        })
    return kw_list

def get_dellow_list(shop_id, condition):
    """获取要删除的低分词"""
    del_qscore = condition['del_qscore']
    del_day = condition['del_day']
    statistics_type = condition['del_statistics_type']
    del_offline = condition['del_offline']
    del_longtail = condition['del_longtail']

    query_dict = {
        'shop_id': shop_id,
        'create_time': {'$lte': date_2datetime(datetime.date.today() - datetime.timedelta(days = condition['del_day']))},
        'qscore_dict.qscore': {'$lte':del_qscore, '$gte': 1},
        'qscore_dict.wireless_qscore': {'$lte': del_qscore, '$gte': 1}}


    ignore_camp_id_list = []
    if not del_offline:
        # 要排除计划或宝贝online_status为'offline'下的关键词
        temp_camp_list = list(camp_coll.find({'shop_id':shop_id, 'online_status':'offline'}, {'_id':1}))
        ignore_camp_id_list = [camp['_id'] for camp in temp_camp_list]

        temp_adg_list = list(adg_coll.find({'shop_id':shop_id, 'online_status':'offline'}, {'_id':1}))
        adg_id_list = [adg['_id'] for adg in temp_adg_list]
        if adg_id_list:
            query_dict.update({'adgroup_id':{'$nin':adg_id_list}})

    if not del_longtail:
        # 要排除长尾托管和roi托管计划下的关键词
        mnt_campid_list = MntMnger.get_longtail_camp_ids(shop_id = shop_id)
        ignore_camp_id_list.extend(mnt_campid_list)

    if ignore_camp_id_list:
        ignore_camp_id_list = list(set(ignore_camp_id_list))
        query_dict.update({'campaign_id': {'$nin': ignore_camp_id_list}})

    kw_list = list(kw_coll.find(query_dict, {'_id':1, 'adgroup_id':1, 'campaign_id':1, 'word':1}))
    temp_kwid_list = [kw['_id'] for kw in kw_list]

    query_dict = {'shop_id': shop_id, 'keyword_id':{'$in':temp_kwid_list}}
    kw_rptdetail_list = Keyword.get_kwrpt_sort_list(query_dict = query_dict, rpt_days = del_day)
    has_rpt_list = [kw_rpt['_id'] for kw_rpt in kw_rptdetail_list if kw_rpt[statistics_type]]
    del_list = [kw for kw in kw_list if kw['_id'] not in has_rpt_list]
    return del_list


def kwrpt_sort_func(x, y):
    if x['click'] != y['click']:
        return cmp(y['click'], x['click'])
    elif x['impressions'] != y['impressions']:
        return cmp(y['impressions'], x['impressions'])
    else:
        return cmp(y['_id'], x['_id'])


def get_deldupl_list(shop_id, condition, word_list = []):
    '''
      按条件获取需要删除的重复词
      1、先查询subway_keyword中满足条件的词
      2、查询不满足报表条件的词
      3、两个列表相减,得到满足删除条件的词
    '''
    del_level = condition['del_level']
    del_day = condition['del_day']
    statistics_type = condition['del_statistics_type']
    del_offline = condition.get('del_offline', 0)
    del_longtail = condition.get('del_longtail', 0)

    query_dict = {'shop_id':shop_id}

    # 获取需要过滤的campaign_id和adgroup_id
    ignore_camp_id_list = []
    if not del_offline:
        # 要排除计划或宝贝online_status为'offline'下的关键词
        temp_camp_list = list(camp_coll.find({'shop_id':shop_id, 'online_status':'offline'}, {'_id':1}))
        ignore_camp_id_list = [camp['_id'] for camp in temp_camp_list]

        temp_adg_list = list(adg_coll.find({'shop_id':shop_id, 'online_status':'offline'}, {'_id':1}))
        adg_id_list = [adg['_id'] for adg in temp_adg_list]
        if adg_id_list:
            query_dict.update({'adgroup_id':{'$nin':adg_id_list}})

    if not del_longtail:
        # 要排除长尾托管和roi托管计划下的关键词
        mnt_campid_list = MntMnger.get_longtail_camp_ids(shop_id = shop_id)
        ignore_camp_id_list.extend(mnt_campid_list)

    if ignore_camp_id_list:
        ignore_camp_id_list = list(set(ignore_camp_id_list))
        query_dict.update({'campaign_id': {'$nin': ignore_camp_id_list}})

    if word_list:
        query_dict['word'] = {'$in': word_list}

    # 获取满足条件的词及重复词id集合
    _, duplicate_list = get_duplicate_word(query_dict = query_dict, sort_mode = 'desc', start = 0, end = 0, count = del_level) # end = 0 表示返回所有
    temp_kw_list, temp_kw_dict, temp_kwid_list = [], {}, []
    for duplicate in duplicate_list:
        temp_kw_list += duplicate['kw_list']
        temp_kw_dict[duplicate['word']] = [kw['_id'] for kw in duplicate['kw_list']]
        temp_kwid_list += temp_kw_dict[duplicate['word']]

    # 获取以上满足报表条件的数据,除去这部分数据最终得到需要删除的词
    del_kw_list = []
    if temp_kwid_list:
        del_kwid_list = []
        query_dict = {'shop_id': shop_id, 'keyword_id': {'$in': temp_kwid_list}}
        kw_rptdetail_list = Keyword.get_kwrpt_sort_list(query_dict = query_dict, rpt_days = del_day)
        kw_rptdetail_dict = {kw_rpt['_id']: kw_rpt for kw_rpt in kw_rptdetail_list}
        # 获取每个关键词重复id的有序集合
        for word, kw_id_list in temp_kw_dict.items():
            # temp_sortid_list按顺序存满足报表条件的kw_id,temp_rptid_list存不满足报表条件的kw_id
            temp_rptid_list, temp_sort_list = [], []
            # for kw_rpt in kw_rptdetail_list:
            #     if kw_rpt['_id'] in kw_id_list:
            #         # 有报表的重复词中statistics_type>0的重复词不需要删除
            #         if kw_rpt[statistics_type] > 0:
            #             temp_rptid_list.append(kw_rpt['_id'])
            #         else:
            #             temp_sortid_list.append(kw_rpt['_id'])
            for kw_id in kw_id_list:
                if kw_id in kw_rptdetail_dict:
                    kw_rpt = kw_rptdetail_dict[kw_id]
                    # 有报表的重复词中statistics_type>0的重复词不需要删除
                    if kw_rpt[statistics_type] > 0:
                        temp_rptid_list.append(kw_id)
                    else:
                        temp_sort_list.append(kw_rpt)
            temp_sort_list.sort(cmp = kwrpt_sort_func)
            temp_sortid_list = [kw_rpt['_id'] for kw_rpt in temp_sort_list]

            # 得到重复词下没有报表的词,(所有id除去有报表的id)
            # 满足报表条件+没有报表的数据需要删除，满足报表的放在前面，因为这部分已经排好序,下面两行代码不能合并
            no_rptid_list = list(set(kw_id_list) - set((temp_sortid_list + temp_rptid_list)))
            temp_sortid_list = temp_sortid_list + no_rptid_list
            # 当重复次数与满足删除条件的总数之差大于等于del_level时，满足其他删除条件的词全部可以删掉
            sub_kw = len(kw_id_list) - len(temp_sortid_list)
            if sub_kw >= del_level:
                del_kwid_list = temp_sortid_list
            else:
                temp_index = del_level - sub_kw
                for kw_id in temp_sortid_list:
                    cur_index = temp_sortid_list.index(kw_id) + 1
                    # 当前索引+1，大于temp_index时，该数据需要删除
                    if cur_index > temp_index:
                        del_kwid_list.append(kw_id)

        del_kw_list = [del_kw for del_kw in temp_kw_list if del_kw['_id'] in del_kwid_list]
    return del_kw_list

def get_onekey_optimize(request):
    """获取一键优化方案"""
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST.get('campaign_id', 0))
    adgroup_id = int(request.POST.get('adgroup_id', 0))

    adg_wrapper = optimize_adgroup_dryrun2(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id, can_add_kw = True)
    upd_kw_list, del_kw_list, add_kw_list = KeywordSubmit.alg_dry_run(adg_wrapper = adg_wrapper)
    most_del_count = min(int(len(adg_wrapper.kw_list) * 0.2), 25)
    del_kw_list = del_kw_list[: most_del_count]

    temp_dict = {'shop_id': shop_id, 'campaign_id': campaign_id, 'adgroup_id': adgroup_id, 'add': add_kw_list, 'del': del_kw_list, 'update': upd_kw_list}
    CacheAdpter.set(CacheKey.WEB_ONEKEY_OPTIMIZE % (shop_id, adgroup_id), temp_dict, 'web', 60 * 5) # 缓存一键优化数据5分钟

    return {'kw_count': len(adg_wrapper.kw_list),
            'update_count': len(upd_kw_list),
            'del_count': len(del_kw_list),
            'add_count': len(add_kw_list),
            'adg_id': adgroup_id,
            'errMsg': ''}

def submit_onekey_optimize(request):
    """提交一键优化到直通车"""

    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    type = str(request.POST.get('type', ''))
    _, opter_name = analysis_web_opter(request)
    result = ''
    temp_dict = CacheAdpter.get(CacheKey.WEB_ONEKEY_OPTIMIZE % (shop_id, adgroup_id), 'web') # 从缓存取一键优化数据
    if temp_dict:
        try:
            kw_submit = KeywordSubmit(shop_id, temp_dict['campaign_id'], adgroup_id, opter = 5, opter_name = opter_name)
            if type == 'update':
                upd_kw_list = temp_dict['update']
                if upd_kw_list:
                    updated_num = kw_submit.sumbit_updated_keywords(upd_kw_list) # 先保证所有词在限价内
                    result = '提交成功'
                else:
                    result = '没有关键词被修改'
            elif type == 'add':
                add_kw_list = temp_dict['add']
                if add_kw_list:
                    added_num, repeat_num = kw_submit.submit_added_keywords(add_kw_list)
                    if added_num == 0 and repeat_num > 0:
                        result = '失败%s个（重复词）' % repeat_num
                    elif added_num > 0 and repeat_num == 0:
                        result = '加词成功%s个' % added_num
                    elif added_num == 0 and repeat_num == 0:
                        result = '加词失败'
                    else:
                        result = '加词成功%s个，失败%s个（重复词）' % (added_num, repeat_num)
                else:
                    result = '没有添加关键词'
            elif type == 'del':
                del_kw_list = temp_dict['del']
                if del_kw_list:
                    deled_num = kw_submit.submit_deleted_keywords(del_kw_list)
                    result = '提交成功'
                else:
                    result = '没有关键词被删除'
        except Exception, e:
            result = '提交失败'
            log.error('onekey optimize submit error, shop_id=%s, adg_id=%s, e=%s' % (shop_id, adgroup_id, e))
    return {'result':result, 'errMsg': ''}

def finish_onekey_optimize(request):
    """一键优化完毕，删除缓存"""
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    opter, opter_name = analysis_web_opter(request)
    opter = 5
    opt_desc, errMsg = '使用一键优化功能', ''
    try:
        dt = datetime.datetime.now()
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        adgroup.optm_submit_time = dt
        adgroup.save()
        onekey_optimize_log(shop_id = shop_id, adgroup_id = adgroup_id, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
        CacheAdpter.delete(CacheKey.WEB_ONEKEY_OPTIMIZE % (shop_id, adgroup_id), 'web')
    except Exception, e:
        errMsg = e
    return {'time': time_humanize(dt), 'errMsg': errMsg}

def check_exchange_condition(request):
    """判定是否可以进行兑换操作"""
    shop_id = int(request.user.shop_id)
    present_id = int(request.POST.get('present_id', 0))

    point_count = CacheAdpter.get(CacheKey.WEB_JLB_COUNT % shop_id, 'web', 'no_cache')
    if point_count == 'no_cache':
        point_count = PointManager.refresh_points_4shop(shop_id = request.user.shop_id)

    present = MemberStore.get_present_byid(present_id) if present_id else None

    is_allow = False
    if present and point_count:
        max_point = present.limit_point if present.limit_point else present.point
        if max_point <= point_count:
            is_allow = True
    return {'result': is_allow, "errMsg":""}

def keyword_locker_list(request):
    """自动抢排名列表"""
    errMsg, kw_id_list, adg_id_list, word_list, keyword_locker_dict, item_id_set, campaign_id_set = "", [], [], [], {}, set(), set()
    shop_id = int(request.user.shop_id)
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    source = request.POST.get('source', 'all') # 汇总 all 计算机 pc 移动 mobile
    source_type_dict = {'all':-1, 'mobile': 0, 'pc': 1}
    platform = source_type_dict.get(source, -1)

    keyword_locker_list = list(KeywordLocker.objects.filter(shop_id = shop_id))

    adg_camp_dict = {}
    for kll in keyword_locker_list:
        kw_id_list.append(kll.id)
        adg_id_list.append(kll.adgroup_id)
        word_list.append(kll.word)
        keyword_locker_dict[kll.id] = kll
        if kll.adgroup_id not in adg_camp_dict:
            adg_camp_dict[kll.adgroup_id] = kll.campaign_id

    # 绑定关键词报表数据
    if start_date == str(datetime.date.today()): # 取实时数据
        kw_rpt_dict = {}
        for adg_id, camp_id in adg_camp_dict.items():
            temp_rpt_dict = RealtimeReport.get_platformsum_rtrpt('keyword', args_list = [shop_id, camp_id, adg_id], platform = platform)
            kw_rpt_dict.update(temp_rpt_dict)
    else:
        kw_rpt_dict = Keyword.Report.get_platform_summed_rpt(query_dict = {'shop_id': shop_id, 'keyword_id': {'$in': kw_id_list}}, start_date = start_date, end_date = end_date, platform = platform)
    # 绑定关键词结构数据
    keyword_list = list(Keyword.objects.filter(shop_id = shop_id, keyword_id__in = kw_id_list))
    # 绑定关键词全网数据
    if platform == -1:
        kw_g_data = get_kw_g_data(word_list)
    else:
        kw_g_data = get_kw_g_data2(word_list, platform)

    # 获取item_id_set
    for kw in keyword_list:
        kw.item_id = kw.adgroup.item_id
        campaign_id_set.add(kw.campaign_id)
        item_id_set.add(kw.item_id)

    campaign_dict = {camp.campaign_id: camp for camp in Campaign.objects.filter(shop_id = shop_id, campaign_id__in = list(campaign_id_set))}
    item_dict = {item.item_id: [item.title, item.price, item.pic_url]for item in Item.objects.filter(shop_id = shop_id, item_id__in = list(item_id_set))}

    adg_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list).only('adgroup_id', 'mnt_type', 'mobile_discount')
    adg_dict = {obj.adgroup_id: obj for obj in adg_list}

    result_list, empty_rpt = [], Keyword.Report()
    for kw in keyword_list:
        kw.set_g_data(kw_g_data.get(str(kw.word), {}))

        kw.rpt = kw_rpt_dict.get(kw.id, empty_rpt)
        kw.locker = keyword_locker_dict.get(kw.keyword_id)
        kw.item = item_dict.get(kw.item_id)
        camp = campaign_dict.get(kw.campaign_id, None)
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
            "exp_rank_start":kw.locker.platform == 'pc' and Keyword.KW_RT_RANK_MAP['pc_rank'].get(str(kw.locker.exp_rank_range[0]), '--') or Keyword.KW_RT_RANK_MAP['mobile_rank'].get(str(kw.locker.exp_rank_range[0]), '--'),
            "exp_rank_end":kw.locker.platform == 'pc' and Keyword.KW_RT_RANK_MAP['pc_rank'].get(str(kw.locker.exp_rank_range[1]), '--') or Keyword.KW_RT_RANK_MAP['mobile_rank'].get(str(kw.locker.exp_rank_range[1]), '--'),
            "limit_price":format(kw.locker.limit_price / 100.0, '.2f'),

            "max_mobile_price": format(kw.get_mobile_price(adg, camp) / 100.0, '.2f'),
            "is_default_price":kw.is_default_price,
            "mobile_is_default_price":kw.mobile_is_default_price,
            "title":kw.item[0],
            "price":format(kw.item[1] / 100.0, '.2f'),
            "pic_url":kw.item[2],

            "camp_title": camp.title
        }
        temp_kw.update(kw.rpt.to_dict())
        result_list.append(temp_kw)

    custom_column = Account.get_custom_col(shop_id)

    return {'keyword_list': result_list, 'custom_column': custom_column, 'errMsg': errMsg}


def get_shop_core_kwlist(request):
    """店铺核心词列表"""
    source = request.POST.get('source', 'all') # 汇总 all 计算机 pc 移动 mobile
    shop_id = int(request.user.shop_id)
    ck, _ = CoreKeyword.objects.get_or_create(shop_id = shop_id)
    source_type_dict = {'all':-1, 'mobile': 0, 'pc': 1}
    platform = source_type_dict.get(source, -1)
    # ## ↑↑ WARNING: 这里不处理状态及异常，只在view里处理，这里只取数据
    if not ck.kw_dict_list: # 计算完了，但是仍然没有分析出核心词，说明这段时间没有开车
        return {'keyword_list': [], 'custom_column': [], 'errMsg': '亲，您最近七天没有报表数据，无法分析！'}
    else:
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        adgroup_id_list, campaign_id_list, keyword_id_list = [], [], []

        adg_camp_dict = {}
        for kw_dict in ck.kw_dict_list:
            adgroup_id_list.append(kw_dict['adgroup_id'])
            campaign_id_list.append(kw_dict['campaign_id'])
            keyword_id_list.append(kw_dict['keyword_id'])
            if kw_dict['adgroup_id'] not in adg_camp_dict:
                adg_camp_dict[kw_dict['adgroup_id']] = kw_dict['campaign_id']

        ck.sync_qscore()
        if start_date == str(datetime.date.today()): # 取实时数据
            kw_rpt_dict = {}
            for adg_id, camp_id in adg_camp_dict.items():
                temp_rpt_dict = RealtimeReport.get_platformsum_rtrpt('keyword', args_list = [shop_id, camp_id, adg_id], platform = platform)
                kw_rpt_dict.update(temp_rpt_dict)
        else:
            kw_rpt_dict = Keyword.Report.get_platform_summed_rpt(query_dict = {'shop_id': shop_id, 'keyword_id': {'$in': keyword_id_list}}, start_date = start_date, end_date = end_date, platform = platform)

        keyword_list = list(Keyword.objects.filter(shop_id = shop_id, keyword_id__in = keyword_id_list))
        adg_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adgroup_id_list).only('adgroup_id', 'item_id', 'mnt_type', 'mobile_discount')

        # adgid_mnt_dict, adgid_itemid_dict = {}, {}, {}
        # for adg in adg_list:
        #     adgid_itemid_dict.update({adg.adgroup_id: adg.item_id})
        #     adgid_mnt_dict.update({adg.adgroup_id: adg.mnt_type})

        adg_dict = {obj.adgroup_id: obj for obj in adg_list}
        item_id_list = list(set([obj.item_id for obj in adg_list]))

        item_dict = {item.item_id: [item.title, item.price, item.pic_url] for item in \
                     Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list)}
        adgid_iteminfo_dict = {}
        for adg_id, adg in adg_dict.items():
            item_info = item_dict.get(adg.item_id, ['', '100', ''])
            adgid_iteminfo_dict.update({adg_id: item_info})

        word_list = [keyword.word for keyword in keyword_list]
        if platform == -1:
            kw_g_data = get_kw_g_data(word_list)
        else:
            kw_g_data = get_kw_g_data2(word_list, platform)

        campaign_dict = {camp.campaign_id: camp for camp in Campaign.objects.filter(shop_id = shop_id, campaign_id__in = list(campaign_id_list))}

        result_list, empty_rpt = [], Keyword.Report()
        for kw in keyword_list:
            kw.set_g_data(kw_g_data.get(str(kw.word), {}))
            kw.rpt = kw_rpt_dict.get(kw.id, empty_rpt)
            adg = adg_dict.get(kw.adgroup_id, None)
            camp = campaign_dict.get(kw.campaign_id, None)
            kw.item = adgid_iteminfo_dict.get(kw.adgroup_id, None)

            if not (adg and camp and kw.item):
                continue

            kw_mnt_opt_type = 2 # 默认是不托管
            if adg.mnt_type != 0:
                kw_mnt_opt_type = kw.mnt_opt_type or 0

            for cfg in BULK_TREE_LIST:
                if eval(cfg['factor']):
                    kw.tree_code = cfg['id']
                    break

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
                "avgpos": getattr(kw.rpt, 'avgpos', 0),
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
                "mobile_is_default_price": kw.mobile_is_default_price or 0,

                "is_locked": kw.is_locked and 1 or 0,
                "tree_code": kw.tree_code,

                "title":kw.item[0],
                "price":format(kw.item[1] / 100.0, '.2f'),
                "pic_url":kw.item[2],

                "camp_title":camp.title,
                "max_mobile_price": format(kw.get_mobile_price(adg, camp) / 100.0, '.2f'),
                "new_mobile_price": format(kw.mobile_price / 100.0, '.2f')
            }

            temp_kw.update(kw.rpt.to_dict())
            result_list.append(temp_kw)

        custom_column = Account.get_custom_col(shop_id)
        return {'keyword_list': result_list, 'custom_column': custom_column, 'errMsg': '' }


def get_rankkw_rtrpt(request):
    shop_id = int(request.user.shop_id)
    kw_locker_list = KeywordLocker.objects.filter(shop_id = shop_id)
    result_dict = {}
    for kw_locker in kw_locker_list:
        temp_adg_dict = RealtimeReport.get_summed_rtrpt('keyword', args_list = [shop_id, kw_locker.campaign_id, kw_locker.adgroup_id])
        temp_kw_rpt = temp_adg_dict.get(kw_locker.keyword_id, Account.Report())
        temp_rpt_dict = {
                         "cpm": format(temp_kw_rpt.cpm / 100.0, '.2f'),
                         "avgpos": getattr(temp_kw_rpt, 'avgpos', 0),
                         "favctr": format(temp_kw_rpt.favctr, '.2f'),
                         "favpay": format(temp_kw_rpt.favpay, '.2f'),
                         }
        temp_rpt_dict.update(temp_kw_rpt.to_dict())
        result_dict.update({kw_locker.keyword_id: temp_rpt_dict})
    return {'result_dict': result_dict, 'errMsg': ''}

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
            setattr(kw, 'campaign', kw.adgroup.campaign)
            for attr in attr_list:
                if attr in ['max_price', 'mobile_price']:
                    data[kw.id][attr] = getattr(kw, attr, None)

    return {'data': data, 'errMsg': errMsg}

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
        data['rank_start'] = keyword_locker.exp_rank_range[0]
        data['rank_end'] = keyword_locker.exp_rank_range[1]
        data['limit'] = keyword_locker.limit_price
        data['nearly_success'] = keyword_locker.nearly_success
        data['start_time'] = keyword_locker.start_time
        data['end_time'] = keyword_locker.end_time

    return {"errMsg":errMsg, 'data':data}

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

def order_shop_check(request):
    """点击店铺预约诊断 发送邮件 添加提醒"""
    try:
        nick = request.user.nick
        consult_id = Customer.objects.get(shop_id = request.user.shop_id).consult_id
        receiver = PSUser.objects.get(id = consult_id)
        click_time = datetime.datetime.now()
        reminder_coll.insert({
                          'create_time': click_time,
                          'sender_id': 0,
                          'receiver_id': consult_id,
                          'department': receiver.department,
                          'position': receiver.position,
                          'handle_status':-1,
                          'content': "客户%s预约了专家免费诊断" % (nick)
                          })

        cc_list = ['%s@paithink.com' % receiver.name, Const.NCRM_DEPARTMENT_LEADER_EMAIL[receiver.department]]
        subject = "自动提醒：客户%s预约诊断" % (nick)
        content = "用户名：%s</br>联系旺旺: <a href=\'aliim:sendmsg?uid=cntaobao&touid=cntaobao%s&siteid=cntaobao\'>%s</a></br>" \
                  "（如果链接不起作用，请手动复制以下地址到地址栏：aliim:sendmsg?uid=cntaobao&touid=cntaobao%s&siteid=cntaobao）</br>" \
                  "点击时间：%s</br>" % (nick, nick, nick, nick, str(click_time)[:10])
        send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, cc_list, html_message = content)
    except Exception, e:
        log.error('e=%s' % e)

    return {'errMsg': ''}

def lucky_draw(request):
    """获取抽奖结果 add by tianxiaohe 20151208"""
    is_backend = request.session.get('login_from', 'taobao') == 'backend'
    awards_detail = Lottery.lucky_draw(request.user, is_backend)
    return {'errMsg': '', 'awards_detail': awards_detail}

def get_winner_list(request):
    """获取中奖名单 add by tianxiaohe 20151208"""
    winner_list = Lottery.get_winner_list()
    return {'errMsg': '', 'winner_list': winner_list}

def get_lottery_active(request):
    """获取抽奖活动 add by tianxiaohe 20151208"""
    is_backend = request.session.get('login_from', 'taobao') == 'backend'
    lottery_dict = Lottery.get_lottery(request.user, is_backend)
    return {'errMsg': '', 'lottery_dict': lottery_dict}

def agent_login_in(request):
    """代理校验 登录 add by tianxiaohe 20151211"""
    user_id = int(request.POST['user_id'])
    user = User.objects.get(id = user_id)
    login_url = user.get_backend_url(user_type = "agent").get('web_url')
    return {'errMsg':'', 'login_url':login_url}

def get_unread_message_count(request):
    '''获取未读私信个数'''
    try:
        shop_id = int(request.user.shop_id)
        count = PrivateMessage.get_unread_count(shop_id)
        return {'errMsg': '', 'count': count}
    except Exception, e:
        return {'errMsg': ''}


def get_message_list(request):
    ''''私信列表'''
    page = request.POST.get('page', 1)
    shop_id = int(request.user.shop_id)
    msg_list = PrivateMessage.get_message_list(shop_id = shop_id)
    page_info, msg_list = pagination_tool(page = page, record = msg_list, page_count = 10)
    json_list = []
    for msg in msg_list:
        json_list.append({'id': msg.id, 'app_id': msg.app_id, 'title': msg.title, 'content': msg.content,
                          'level': msg.level, 'last_modified': msg.last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                          'is_read': msg.is_read })
    return {'msg_list': json_list, 'page_info': page_info, 'errMsg': ''}

def read_message(request):
    '''读一条消息'''
    shop_id = int(request.user.shop_id)
    msg_id = request.POST.get('msg_id', None)
    errMsg = ''
    if not msg_id:
        errMsg = '消息读取失败，参数缺失。'
    result = PrivateMessage.read_message(shop_id, msg_id)
    if not result:
        errMsg = '消息读取失败。'
    return {'errMsg': errMsg}

def set_adg_follow(request):
    try:
        shop_id = int(request.user.shop_id)
        campaign_id = int(request.POST.get('campaign_id'))
        adgroup_id = int(request.POST.get('adgroup_id'))
        is_follow = int(request.POST.get('is_follow'))
        opter, opter_name = analysis_web_opter(request)
        if is_follow > 1 or is_follow < -1 :
            raise Exception("bad_discount")
        Adgroup.set_adgroup_is_follow(shop_id, adgroup_id, is_follow)
        set_adg_follow_log(shop_id, campaign_id, adgroup_id, is_follow, opter = opter, opter_name = opter_name)
        return {'errMsg':'', 'adgroup_id':adgroup_id, 'is_follow':is_follow}
    except Exception, e:
        msg = "操作失败，请刷新后重试！"
        return {'errMsg':msg}

def rank_desc_map(request):
    '''获取抢排名下拉列表'''

    result = {
            'pc_start': Keyword.RANK_START_DESC_MAP['pc'],
            'pc_end': Keyword.RANK_END_DESC_MAP['pc'],
            'yd_start': Keyword.RANK_START_DESC_MAP['yd'],
            'yd_end': Keyword.RANK_END_DESC_MAP['yd']
        }
    return {'errMsg':'', 'result':result}

def batch_get_rt_kw_rank(request):
    '''批量查询关键词排名'''
    keyword_id_list = json.loads(request.POST.get('keyword_id_list'), '[]')

    shop_id = int(request.user.shop_id)
    tapi = get_tapi(shop_id = shop_id)
    kw_group8_adg , rank_result = {}, {}

    for keyword in keyword_id_list:
        kw_group8_adg.setdefault(keyword['adgroup_id'], [])
        kw_group8_adg[keyword['adgroup_id']].append(keyword['keyword_id'])


    for adg_id, kw_id_list in kw_group8_adg.items():
        kw_rank_info_dict = Keyword.batch_get_rt_kw_rank(tapi = tapi, nick = request.user.nick, adg_id = adg_id, kw_id_list = kw_id_list)
        for kw_id, rank_info in kw_rank_info_dict.items():
#             rank_result.append({'keyword_id':kw_id, 'rank_info':rank_info})
            rank_result[kw_id] = rank_info

    return {'errMsg':'', 'rank_result':rank_result}

