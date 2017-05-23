# coding=UTF-8

import math
import datetime

from mongoengine.errors import DoesNotExist

from apilib import TopError, tsapi as isv_tapi
from apilib.parsers import TopObjectParser
from apps.common.utils.utils_log import log
from apps.common.utils.utils_mysql import execute_query_sql
from apps.common.utils.utils_datetime import time_is_ndays_interval, date_2datetime, time_is_someday
from apps.common.utils.utils_collection import genr_sublist
from apps.common.models import Config
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_json import json
from apps.common.cachekey import CacheKey
from apps.router.models import User
from apps.engine.models import ShopMngTask, shopmng_task_coll
from apps.kwslt.select_words import ItemKeywordManager
from apps.mnt.models import MntTask, MntTaskMng
from apps.web.jms import ItemMsgManager, MsgManager



def get_task_list_of_run_shop_task(need_count):
    """获取店铺任务队列"""
    task_id_list = ShopMngTask.get_valid_task(need_count)
    log.info('[timer][get_task_list][shop_task]: count=%s' % len(task_id_list))
    return task_id_list

def run_shop_task(shop_id, call_info = '', is_login = False, thread = None):
    """执行店铺任务"""
    call_info = call_info + 'thread=%s' % (thread)
    smt, is_create = ShopMngTask.objects.get_or_create(shop_id = shop_id)
    if is_create:
        log.info('in shop_task, shop_id=%s, create ShopMngTask(), %s' % (shop_id, call_info))

    return smt.run_task(is_login)

def reset_shop_task(shop_id = None, thread = None):
    ShopMngTask.reset_task(shop_id)

# 重置指定店铺的大任务状态
def reset_shop_task_manual(shop_id, request = None):
    result = True
    if shop_id:
        result = reset_shop_task(shop_id = shop_id)
    return request and {'result':result} or TopObjectParser.json_to_object({'result':result})

def cleanup_expired(request = None):
    """清除过期数据，包括：
    1.清除掉过期15天内的用户所有数据
    2.部分表，根据时间清理数据（通常是30天）
    """
    def is_outservice(shop_id):
        expire_days = Config.get_value('web.clean_up.OUTSERVICE_EXPIRE_DAYS', default = 15)
        deadline_query_sql = "select deadline from router_articleusersubscribe where nick=(select nick from router_user where shop_id=%s) order by deadline desc limit 1"
        # 检查是否可删除
        deadline_list = execute_query_sql(deadline_query_sql % shop_id)
        for tmp_deadline in deadline_list:
            deadline = tmp_deadline["deadline"]
            if time_is_ndays_interval(deadline, expire_days):
                return True
        return False

    def remove_shopdata(shop_id_list):
        """移除多个店铺数据"""
        from apps.subway.models import account_coll, camp_coll, adg_coll, crt_coll, ccrt_coll, kw_coll, item_coll, attn_coll, uprcd_coll
        # 移除基本的结构（含报表）数据
        # account_coll.remove({'_id':{'$in':shop_id_list}}) # 店铺数据不清理
        camp_coll.remove({'shop_id':{'$in':shop_id_list}}) # 计划数据
        adg_coll.remove({'shop_id':{'$in':shop_id_list}}) # 推广级数据
        crt_coll.remove({'shop_id':{'$in':shop_id_list}}) # 创意数据
        ccrt_coll.remove({'shop_id':{'$in':shop_id_list}}) # 自定义创意
        kw_coll.remove({'shop_id':{'$in':shop_id_list}}) # 关键词数据
        item_coll.remove({'shop_id':{'$in':shop_id_list}}) # 宝贝数据

        # 移除报表数据
        from apps.subway.models_report import acctrpt_coll, camprpt_coll, adgrpt_coll, crtrpt_coll, kwrpt_coll
        # acctrpt_coll.remove({'shop_id': {'$in': shop_id_list}}) # 店铺报表不清理
        camprpt_coll.remove({'shop_id': {'$in': shop_id_list}})
        adgrpt_coll.remove({'shop_id': {'$in': shop_id_list}})
        crtrpt_coll.remove({'shop_id': {'$in': shop_id_list}})
        kwrpt_coll.remove({'shop_id': {'$in': shop_id_list}})

        # 移除算法/功能相关的数据
        attn_coll.remove({'_id':{'$in':shop_id_list}}) # 关注数据

        # 清除抢排名设置和历史记录
        from apps.engine.models_channel import MessageChannel
        from apps.engine.models_kwlocker import kw_locker_coll
        kw_cur = kw_locker_coll.find({'shop_id': {'$in': shop_id_list}}, {'_id': 1})
        kw_id_list = [kw['_id'] for kw in kw_cur]
        MessageChannel.delete_msg_history(kw_id_list)
        kw_locker_coll.remove({'shop_id':{'$in':shop_id_list}})

        from apps.engine.models import shopmng_task_coll
        shopmng_task_coll.remove({'_id':{'$in':shop_id_list}}) # 店铺大任务数据

        from apps.mnt.models import mnt_camp_coll, mnt_task_coll
        mnt_camp_coll.remove({'shop_id':{'$in':shop_id_list}}) # 全自动计划数据
        mnt_task_coll.remove({'shop_id':{'$in':shop_id_list}}) # 全自动任务数据

        uprcd_coll.remove({'shop_id':{'$in':shop_id_list}}) # 操作记录数据

        from apps.alg.models import optrec_coll
        optrec_coll.remove({'shop_id':{'$in':shop_id_list}}) #全自动优化分析记录

        from apps.subway.download import dler_coll
        dler_coll.remove({'_id':{'$in':shop_id_list}}) # 下载数据

        from apps.crm.models import psmsg_coll
        psmsg_coll.remove({'shop_id':{'$in':shop_id_list}}) # 留言信息

        try:
            user_list = User.objects.filter(nick__in = shop_id_list)
            user_id_list, uid_list, username_list = [], [], []
            for user in user_list:
                user_id_list.append(user.id)
                uid_list.append(user.first_name)
                username_list.append(user.nick)

            from apps.router.models import Agent, AccessToken, AdditionalPermission, NickPort, Shop
            Agent.objects.filter(principal__in = user_id_list).delete() # 用户代理
            AccessToken.objects.filter(uid__in = uid_list, platform = 'web').delete() # 千牛session
            AdditionalPermission.objects.filter(user__in = user_id_list).delete() # 额外授权
            NickPort.objects.filter(nick__in = username_list).delete() # 属服务器
            Shop.objects.filter(sid__in = shop_id_list).delete() # 店铺信息
        except Exception:
            pass

    def remove_outdated():
        last_date = datetime.date.today() - datetime.timedelta(30)
        default_deadline = date_2datetime(last_date)

        from django.contrib.sessions.models import Session
        Session.objects.filter(expire_date__lte = default_deadline).delete()

        from apps.subway.models_report import AccountRpt, CampaignRpt, AdgroupRpt, CreativeRpt, KeywordRpt
        AccountRpt.clean_outdated()
        CampaignRpt.clean_outdated()
        AdgroupRpt.clean_outdated()
        CreativeRpt.clean_outdated()
        KeywordRpt.clean_outdated()

        from apps.subway.models_upload import UploadRecord
        UploadRecord.clean_outdated()

        from apps.alg.models import OptimizeRecord
        OptimizeRecord.clean_outdated()

        # 删除冻结超过30天的积分数据
        from apps.web.models import PointActivity
        PointActivity.clean_outdated()

    smt_cursor = shopmng_task_coll.find({'status':0}, {'_id':1})
    deactived_shop_id_list = [smt['_id'] for smt in smt_cursor] # 无法执行店铺任务的
    expired_shop_id_list = []

    log.info('need to check %s shops' % len(deactived_shop_id_list))
    for temp_list in genr_sublist(deactived_shop_id_list, 100):
        expired_shop_id_list = []
        for shop_id in temp_list:
            if is_outservice(shop_id):
                expired_shop_id_list.append(shop_id)

        if expired_shop_id_list:
            remove_shopdata(expired_shop_id_list)

    log.info('start remove outdated data')
    remove_outdated()
    log.info('all data cleaned OK')

# ===============================================================================
# 迁自mnt.api-->begin
# ===============================================================================
def get_task_list_of_run_mnt_quick_task(need_count):
    """获取符合条件的快速调整任务队列"""
    task_id_list = MntTaskMng.get_valid_task(task_type = 1, need_count = need_count)
    log.info('[timer][get_task_list][mnt_quick_task]: count=%s' % len(task_id_list))
    return task_id_list

def run_mnt_quick_task(task_id): # 注意：task_id都是str类型的
    """执行快速调整任务"""
    try:
        mt = MntTask.objects.get(id = task_id)
        MntTaskMng.run_task(mt)
    except DoesNotExist:
        pass

def get_task_list_of_run_mnt_routine_task(need_count):
    """获取符合条件的例行优化任务队列"""
    task_id_list = MntTaskMng.get_valid_task(task_type = 0, need_count = need_count)
    log.info('[timer][get_task_list][mnt_routine_task]: count=%s' % len(task_id_list))
    return task_id_list

def run_mnt_routine_task(task_id):
    """执行例行优化任务"""
    try:
        mt = MntTask.objects.get(id = task_id)
        MntTaskMng.run_task(mt)
    except DoesNotExist:
        pass

def start_engine(task, consumer_size, queue_size, time_scope, request = None):
    from scripts.task_engine import TaskAllocator
    try:
        frun = globals()['run_%s_task' % task]
        fget = globals()['get_task_list_of_run_%s_task' % task]
        TaskAllocator.trigger(consumer_size = consumer_size, queue_size = queue_size, fget = fget, frun = frun, time_scope = time_scope)
    except Exception, e:
        log.error(e)
        return

def clear_deleted_words(shop_id, campaign_id, adgroup_id, request = None):
    """清除已经删除的关键词"""
    from apps.subway.models_upload import UploadRecord
    UploadRecord.objects.filter(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id, data_type = 402).delete()

#===============================================================================
# # 迁自mnt.api-->end
#===============================================================================

# 增加权限，请求来自旧版
def add_permission_at_web(nick, permission_code, type, request = None):
    from apps.router.models import AdditionalPermission
    try:
        user = User.objects.get(nick = nick)
        ap, created = AdditionalPermission.objects.get_or_create(user = user, defaults = {'perms_code':permission_code})
        if not created:
            if ap.perms_code != permission_code:
                ap.perms_code = permission_code
                ap.save()
        else:
            ap.save()
        log.info('add permission ok, nick=%s, permission=%s.' % (nick, permission_code))
    except Exception, e:
        log.error('add permission error, nick=%s, permission=%s, e=%s.' % (nick, permission_code, e))

#===============================================================================
# 以下是其他外部接口
#===============================================================================

def isv_get_itemcats(parent_cid = '', cids = '', fields = '', request = None):
    '''获取淘宝标准类目信息接口'''
    kwarg = {}
    if parent_cid:
        kwarg.update({'parent_cid':parent_cid})
    if cids:
        kwarg.update({'cids':cids})
    if fields:
        kwarg.update({'fields':fields})
    try:
        top_obj = isv_tapi.itemcats_get(**kwarg)
        result = top_obj.to_dict()
    except TopError, e:
        log.error('itemcats_get TopError, parent_cid=%s, cids=%s, fields=%s, e=%s' % (parent_cid, cids, fields, e))
        result = str(e)
    return request and result or TopObjectParser.json_to_object(result)

def isv_get_item(num_iid, fields, request = None):
    '''获取淘宝宝贝信息接口'''
    kwarg = {}
    if num_iid:
        kwarg.update({'num_iid':num_iid})
    if fields:
        kwarg.update({'fields':fields})
    try:
        top_obj = isv_tapi.item_seller_get(**kwarg)
        result = top_obj.to_dict()
    except TopError, e:
        log.error('item_seller_get TopError, num_iid=%s, fields=%s, e=%s' % (num_iid, fields, e))
        result = str(e)
    return request and result or TopObjectParser.json_to_object(result)

def isv_get_account_rpt(shop_id, rpt_days = 1, request = None):
    '''获取指定日期的直通车账户报表接口'''
    from apps.subway.models_account import Account

    result = {}
    try:
        shop_id = int(shop_id)
        rpt_days = int(rpt_days)
    except Exception, e:
        log.error('get account rpt error, shop_id=%s, e=%s' % (shop_id, e))
        result = {"error_response": {"code":41, "msg":"Invalid Arguments", "sub_code":"isv.invalid-parameter", "sub_msg":"店铺ID必须是整数"}}
        return result

    try:
        objs = Account.objects.filter(shop_id = shop_id)
        if not objs:
            result = {"error_response": {"code":15, "msg":"Remote service error", "sub_code":"isv.account-not-exist:%s" % shop_id, "sub_msg":"账户未开直通车或未订购软件"}}
        else:
            obj = objs[0]
            obj.rpt_days = rpt_days
            account_rpt_list = []
            for rpt in obj.snap_list:
                temp_dict = {'date': str(rpt.date.date()), 'search_type': rpt.search_type, 'source': rpt.source,
                             'impressions': rpt.impressions,
                             'click': rpt.click,
                             'cost': rpt.cost,
                             'avgpos': rpt.avgpos,
                             'aclick': rpt.aclick,
                             'directpay': rpt.directpay,
                             'indirectpay': rpt.indirectpay,
                             'directpaycount': rpt.directpaycount,
                             'indirectpaycount': rpt.indirectpaycount,
                             'favitemcount': rpt.favitemcount,
                             'favshopcount': rpt.favshopcount
                             }
                account_rpt_list.append(temp_dict)
            result = {'account_rpt_list': account_rpt_list}
    except Exception, e:
        log.error('get account rpt error, shop_id=%s, e=%s' % (shop_id, e))
        result = {"error_response":{"code":15, "msg":"Remote service error", "sub_code":"isp.unknown-error", "sub_msg":"其它错误, e=%s" % str(e)}}
    return result

def isv_get_select_word(item_id, request = None):
    '''获取指定宝贝的候选关键词接口'''
    from apps.subway.models_item import Item
    from apps.kwslt.keyword_selector import KeywordSelector

    try:
        item_id = int(item_id)
    except Exception:
        result = {"error_response": {"code":41, "msg":"Invalid Arguments", "sub_code":"isv.invalid-parameter", "sub_msg":"item_id必须是整数"}}
        return result

    result = {}
    item = Item.get_item_dict(item_id, force = True)
    if not item:
        result = {"error_response": {"code":15, "msg":"Remote service error", "sub_code":"isv.item-not-exist:%s" % item_id, "sub_msg":"item不存在"}}
    else:
        word_list = KeywordSelector.get_quick_select_words(item, None)
        result = {'word_list': word_list}
    return result

def isv_get_split_title(cat_id, item_id, title, request = None):
    '''获取指定宝贝的关键词拆分和宝贝流量来源词接口'''
    if not title.strip():
        return {"error_response": {"code":41, "msg":"Invalid Arguments", "sub_code":"isv.invalid-parameter", "sub_msg":"title不能为空"}}

    try:
        cat_id = int(cat_id <= 0 and 'False' or cat_id)
    except Exception:
        return {"error_response": {"code":41, "msg":"Invalid Arguments", "sub_code":"isv.invalid-parameter", "sub_msg":"cat_id必须是整数"}}

    try:
        item_id = int(item_id <= 0 and 'False' or item_id)
    except Exception:
        return {"error_response": {"code":41, "msg":"Invalid Arguments", "sub_code":"isv.invalid-parameter", "sub_msg":"item_id必须是整数"}}

    try:
        # 开始拆分宝贝标题和获取关键词信息
        kw_list = []
        title_info_dict = ItemKeywordManager.get_title_info_dict(cat_id = cat_id, title = title)
        for values in title_info_dict['kw_list']:
            kw_list.append({'word':values[0], 'impression':values[1], 'competition':values[2], 'hot':values[3], 'click':values[4]})
        split_title = ','.join([str(eleword) for eleword in title_info_dict['title_elemword_list']])
        result = {'split_title_result':{'item_id':item_id, 'split_title':split_title, 'split_word_list':{'insight_split_word':kw_list}}}
    except Exception, e:
        log.error('isv_get_split_title error, cat_id=%s, item_id=%s, title=%s, e=%s' % (cat_id, item_id, title, e))
        result = {"error_response":{"code":15, "msg":"Remote service error", "sub_code":"isp.unknown-error", "sub_msg":"其它错误, e=%s" % str(e)}}
    return result

def isv_get_related_words(words, page_size, request = None):
    '''获取指定的一批关键词的相关词接口'''
    from apps.common.biz_utils.utils_tapitools import get_kw_g_data
    if not words.strip():
        return {"error_response": {"code":41, "msg":"Invalid Arguments", "sub_code":"isv.invalid-parameter", "sub_msg":"words不能为空"}}

    try:
        page_size = int((page_size <= 0 or page_size > 100) and 40 or page_size)
    except Exception:
        page_size = 40

    # 开始获取相关词信息
    result = {}
    try:
        top_obj = isv_tapi.simba_insight_relatedwords_get(bidword_list = words, number = page_size)
        # 获取全网数据和引流能力
        if top_obj and hasattr(top_obj, 'related_words_result_list') and top_obj.related_words_result_list:
            for tmp_obj in top_obj.related_words_result_list.insight_related_words:
                related_word_list = []
                for inner_obj in tmp_obj.related_word_items_list.insight_related_word:
                    related_word_list.append(inner_obj.related_word)
                if related_word_list:
                    g_data_dict = get_kw_g_data(related_word_list)
                for inner_obj in tmp_obj.related_word_items_list.insight_related_word:
                    inner_word = str(inner_obj.related_word).strip()
                    if inner_word in g_data_dict.keys():
                        inner_obj.impression = g_data_dict[inner_word]['g_pv']
                        inner_obj.competition = g_data_dict[inner_word]['g_competition']
                        inner_obj.click = g_data_dict[inner_word]['g_click']
                        inner_obj.hot = round(math.log10(float(inner_obj.impression or 1) ** 2 / (inner_obj.competition or 1)), 2)
        result = top_obj.to_dict()
    except TopError, e:
        log.error('simba_insight_relatedwords_get TopError, words=%s, page_size=%s, e=%s' % (words, page_size, e))
        result = str(e)
    except Exception, e:
        log.error('isv_get_related_words error, words=%s, e=%s' % (words, e))
        result = {"error_response":{"code":15, "msg":"Remote service error", "sub_code":"isp.unknown-error", "sub_msg":"其它错误, e=%s" % str(e)}}
    return result

def isv_get_top_words(cat_id, dimension, page_size, request = None):
    '''获取指定类目的类目TOP词接口'''
#     limited_message = flow_control(request)
#     if limited_message:
#         return limited_message

    try:
        cat_id = int(cat_id <= 0 and 'False' or cat_id)
    except Exception:
        return {"error_response": {"code":41, "msg":"Invalid Arguments", "sub_code":"isv.invalid-parameter", "sub_msg":"cat_id必须是整数"}}

    try:
        page_size = int((page_size <= 0 or page_size > 20) and 20 or page_size)
    except Exception:
        page_size = 20

    if dimension not in ['impression', 'click', 'cost', 'ctr', 'cpc', 'coverage', 'transactiontotal', 'transactionshippingtotal', 'favtotal', 'roi']:
        dimension = 'click'

    # 开始获取类目TOP词信息
    result = {}
    delta_days = 7
    end_date = datetime.date.today()
    start_date = datetime.date.today() - datetime.timedelta(delta_days)
    try:
        top_obj = isv_tapi.simba_insight_catstopwordnew_get(cat_id = cat_id, start_date = start_date, end_date = end_date, dimension = dimension, page_size = page_size)
        if top_obj and hasattr(top_obj, 'topword_data_list') and top_obj.topword_data_list:
            for tmp_obj in top_obj.topword_data_list.insight_word_data_under_cat_d_t_o:
                # 删除不需要暴露的数据
                del tmp_obj.directtransaction
                del tmp_obj.directtransactionshipping
                del tmp_obj.favitemtotal
                del tmp_obj.favshoptotal
                del tmp_obj.indirecttransaction
                del tmp_obj.indirecttransactionshipping
                tmp_obj.click = int(tmp_obj.click / delta_days)
                tmp_obj.competition = int(tmp_obj.competition / delta_days) or 1
                tmp_obj.cost = int(tmp_obj.cost / delta_days)
                tmp_obj.favtotal = int(tmp_obj.favtotal / delta_days)
                tmp_obj.impression = int(tmp_obj.impression / delta_days)
                tmp_obj.transactionshippingtotal = int(tmp_obj.transactionshippingtotal / delta_days)
                tmp_obj.transactiontotal = int(tmp_obj.transactiontotal / delta_days)
                if tmp_obj.impression != 0:
                    tmp_obj.hot = round(math.log10(float(tmp_obj.impression) ** 2 / (tmp_obj.competition or 1)), 2)
                else:
                    tmp_obj.hot = 0.0
        result = top_obj.to_dict()
    except TopError, e:
        log.error('simba_insight_catstopwordnew_get TopError, cat_id=%s, start_date=%s, end_date=%s, dimension=%s, page_size=%s, e=%s' % (cat_id, start_date, end_date, dimension, page_size, e))
        result = str(e)
    except Exception, e:
        log.error('isv_get_top_words error, cat_id=%s, e=%s' % (cat_id, e))
        result = {"error_response":{"code":15, "msg":"Remote service error", "sub_code":"isp.unknown-error", "sub_msg":"其它错误, e=%s" % str(e)}}
    return result

def flow_control(request):
    '''对外部JAPI执行流控控制。因为api函数要调用api_router中的dispatch，貌似无法通过装饰器实现该逻辑'''
    if not request:
        return ''
    req_dict = request.REQUEST
    isv_key = req_dict.get('appkey', '')
    if isv_key:
        limit_count = Config.get_value('common.ISV_APICONTROL_%s' % isv_key, default = {}).get(req_dict['method'], None)
        if limit_count:
            call_count = CacheAdpter.get(CacheKey.WEB_ISV_APICOUNT % (isv_key, req_dict['method']), 'web', ())
            if not call_count:
                call_count = (1, datetime.datetime.now()) # TODO　缓存中没有，从数据库取调用数，每间隔1小时，写入数据库

            if call_count[0] >= limit_count and time_is_someday(dt = call_count[1], days = 0):
                return {"error_response":{"code":7, "msg":"App Call Limited", "sub_code":"accesscontrol.limited-by-api-access-count", "sub_msg":"This ban will last for 1 more seconds"}}
            else:
                CacheAdpter.set(CacheKey.WEB_ISV_APICOUNT % (isv_key, req_dict['method']), (call_count[0] + 1, datetime.datetime.now()), 'web', 60 * 60 * 24)
    return ''

#======================================================== message api ========================================================
def router_message(result, request = None):
    result_dict = {'result':{}}
    try:
        data = DictWrapper.load_dict(json.loads(result))
        data.content = DictWrapper.load_dict(json.loads(data.content))
        handle_result = MsgManager.handle(data.topic, data)
        log.info("handled %s by %s, result=%s" % (data, data.topic, handle_result))
        result_dict = {'result': {'result': handle_result}}
    except Exception, e:
        log.error('handle %s error, e=%s' % (result, e))
        result_dict = {'result':{'result':u'处理消息时出错'}}
    return request and result_dict or TopObjectParser.json_to_object(result_dict)
