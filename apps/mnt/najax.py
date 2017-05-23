# coding=UTF-8
import re
import datetime
from mongoengine.errors import DoesNotExist
import math
import collections

from django.http import HttpResponse

from apilib import get_tapi, TopError
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_number import format_division, round_digit
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.common.biz_utils.utils_misc import analysis_web_opter
from apps.common.utils.utils_datetime import time_is_someday
from apps.mnt.models import MntCampaign, MntTaskMng, MntMnger, mnt_camp_coll
from apps.subway.models import (Campaign, Adgroup, adg_coll, Adgroup, Item)
from apps.subway.upload import (update_campaign, udpate_cmp_budget_log, change_cmp_maxprice_log,
                                change_mntcfg_type_log, mnt_quick_oper_log, set_cmp_mnt_status_log,
                                update_adgroups, update_creative, add_creative, modify_cmp_adg_log,
                                add_adgroups, change_adg_mnt_log, change_rt_engine_log)

from apps.engine.models import TitleTransfer
from apps.kwslt.models_cat import Cat, CatStatic
from apps.subway.realtime_report import RealtimeReport

def route_ajax(request):
    '''ajax路由函数，返回数据务必返回字典的格式'''
    if not request.user.is_authenticated():
        return {'errMsg':'您已经退出，请重新登录之后再试'}
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
    return HttpResponse('%s(%s)' % (call_back, json.dumps(data)))

# 设置托管计划
def mnt_campaign_setter(request):
    error_msg = None
    shop_id = int(request.user.shop_id)
    mnt_type = int(request.POST.get('mnt_type'))
    campaign_id = int(request.POST['campaign_id'])
    set_flag = int(request.POST['set_flag']) and True or False # 设置为托管计划或者终止托管计划
    opter, opter_name = analysis_web_opter(request)
    try:
        warn_msg_dict = {}
        if mnt_type not in [1, 2, 3, 4]:
            raise Exception("wrong_mnt_type")
        if set_flag:
            mnt_rt = int(request.POST.get('mnt_rt', 0)) # 是否启用实时引擎
            mnt_bid_factor = int(request.POST.get('mnt_bid_factor', 0))
            opt_wireless = int(request.POST.get('opt_wireless', 0))
            max_price = int(float(request.POST['max_price']) * 100)
            mobile_max_price = int(float(request.POST['mobile_max_price']) * 100)
            budget = int(request.POST['budget'])
            mnt_index = int(request.POST['mnt_index'])

            kwargs = {'area': int(request.POST.get('area', 0)),
                      'schedule': int(request.POST.get('schedule', 0)),
                      'platform': int(request.POST.get('platform', 0))}
            warn_msg_dict = MntMnger.set_mnt_camp(campaign_id = campaign_id, flag = set_flag, mnt_index = mnt_index,
                                                  mnt_type = mnt_type, opter = opter, opter_name = opter_name,
                                                  max_price = max_price, mobile_max_price = mobile_max_price, budget = budget,
                                                  mnt_rt = mnt_rt, mnt_bid_factor = mnt_bid_factor, opt_wireless = opt_wireless,
                                                  **kwargs)
        else:
            warn_msg_dict = MntMnger.set_mnt_camp(campaign_id = campaign_id, flag = set_flag, mnt_type = mnt_type, opter = opter, opter_name = opter_name)
    except Exception, e:
        log.info('mnt_campaign_setter error: %s, mnt_type: %s, campaign_id: %s, shop_id: %s,' % (e, mnt_type, campaign_id, shop_id))
        if str(e) == "no_permission":
            return {'errMsg':'', 'result':0, 'error_msg':'no_permission'}
        try:
            result, error_msg = json.loads(e.message)
        except:
            if hasattr(e, 'reason'):
                error_msg = (eval(e.reason))['error_response'].get('sub_msg', '淘宝发生未知错误，请联系顾问')
            else:
                error_msg = e.message
                if 'need to wait' in error_msg:
                    error_msg = 'API接口超限'
    finally:
        CacheAdpter.delete(CacheKey.WEB_MNT_MENU % shop_id, 'web')
    result = 0 if error_msg else 1
    return {'errMsg':'', 'error_msg':error_msg, 'result':result, 'warn_msg_dict': json.dumps(warn_msg_dict)}

def get_base_rpt(request):
    ''' MNT主页上的基础报表 '''
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST['campaign_id'])
    rpt_days = int(request.POST.get('rpt_days', 1))
    start_date = str(request.POST['start_date'])
    end_date = str(request.POST['end_date'])
    try:
        # camp_rpt_dict = Campaign.Report.get_summed_rpt({'shop_id': shop_id, 'campaign_id': campaign_id}, rpt_days = rpt_days)
        if start_date == end_date == datetime.date.today().strftime('%Y-%m-%d'):
            camp_rpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'campaign', args_list = [shop_id])
        else:
            camp_rpt_dict = Campaign.Report.get_summed_rpt({'shop_id': shop_id, 'campaign_id': campaign_id}, start_date = start_date, end_date = end_date)
        camp_rpt = camp_rpt_dict.get(campaign_id, Campaign.Report())
        result_dict = camp_rpt.to_dict()
        return {'errMsg': '', 'result_dict':result_dict}
    except Exception, e:
        log.error('missing args or campaign not exist, campaign_id = %s, e = %s' % (request.POST['campaign_id'], e))
        return {'errMsg': '亲，请刷新页面重新操作！'}

def update_cfg(request):
    error_msg = ''
    shop_id = int(request.user.shop_id)
    campaign_id = request.POST['campaign_id']
    submit_data = json.loads(request.POST['submit_data'])
    mnt_type = int(request.POST.get('mnt_type', 1))
    try:
        opter, opter_name = analysis_web_opter(request)
        if submit_data.has_key('budget'):
            try:
                campaign = Campaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
            except DoesNotExist, e:
                log.info('can not get campaign, campaign_id = %s' % campaign_id)
                return {'errMsg':'亲，请刷新页面重新操作！'}
            old_budget = campaign.budget
            new_budget = submit_data['budget']
            result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = int(campaign_id), record_flag = False, budget = new_budget,
                                                    use_smooth = campaign.is_smooth and 'true' or 'false', opter = opter, opter_name = opter_name)
            if 'budget' in result_list:
                display_budget = lambda x: x == 20000000 and '不限' or ('%s元' % x)
                opt_desc = '日限额由%s，修改为%s' % (display_budget(old_budget / 100), display_budget(new_budget))
                udpate_cmp_budget_log(shop_id = shop_id, campaign_id = campaign_id, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
            else:
                return {'errMsg':'<br/>'.join(msg_list)}
        if submit_data.has_key('max_price'):
            try:
                mnt_campaign = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
            except DoesNotExist, e:
                log.info('can not get mnt_campaign, campaign_id = %s' % campaign_id)
                return {'errMsg':'亲，请刷新页面重新操作！'}
            old_max_price = mnt_campaign.max_price
            old_mobile_max_price = mnt_campaign.real_mobile_max_price
            new_max_price = int(round(float(submit_data.get('max_price', old_max_price / 100.0)) * 100))
            new_mobile_max_price = int(round(float(submit_data.get('mobile_max_price', old_mobile_max_price / 100.0)) * 100))
            if new_max_price != old_max_price or new_mobile_max_price != old_mobile_max_price:
                mnt_campaign.max_price = new_max_price
                mnt_campaign.mobile_max_price = new_mobile_max_price
                change_cmp_maxprice_log(shop_id = shop_id, campaign_id = campaign_id, max_price = new_max_price, mobile_max_price = new_mobile_max_price,
                                        opter = opter, opter_name = opter_name)
                MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = campaign_id, mnt_type = mnt_type, task_type = 2, adgroup_id_list = 'ALL')
            mnt_campaign.save()
        return {'errMsg':'', 'budget':submit_data.get('budget', ''), 'max_price':submit_data.get('max_price', '')}
    except Exception, e:
        log.info('submit MntCampaign cfg error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, e))
        return {'errMsg':'修改失败，请刷新页面重新操作！'}

def quick_oper(request):
    '''触发页面上的“加大投入/减小投入”'''
    try:
        shop_id = int(request.user.shop_id)
        campaign_id = int(request.POST['campaign_id'])
        adg_id_list = request.POST.getlist("adg_id_list[]")
        adg_id_list = [int(adg_id) for adg_id in adg_id_list]
        stgy = int(request.POST['stgy'])
        opter, opter_name = analysis_web_opter(request)
        mnt_campaign = MntCampaign.objects.get(campaign_id = campaign_id, shop_id = shop_id)
        now = datetime.datetime.now()
        result = 1
        if adg_id_list:
            MntTaskMng.generate_quickop_task(shop_id = mnt_campaign.shop_id, campaign_id = mnt_campaign.campaign_id, mnt_type = mnt_campaign.mnt_type, stgy = stgy, adgroup_id_list = adg_id_list)
            adg_coll.update({'shop_id': shop_id, 'campaign_id':campaign_id, '_id':{'$in': adg_id_list}},
                            {'$set':{'quick_optime': now}}, multi = True)
        else:
            if not mnt_campaign.quick_optime or not time_is_someday(mnt_campaign.quick_optime):
                MntTaskMng.generate_quickop_task(shop_id = shop_id, campaign_id = mnt_campaign.campaign_id, mnt_type = mnt_campaign.mnt_type, stgy = stgy)
                mnt_campaign.quick_optime = now
                mnt_campaign.save()
            else:
                result = 2
        # 写入操作记录
        stgy_name = '加大投入' if stgy == 1 else '减小投入'
        opt_type = 15 if stgy == 1 else 16
        adg_ids = '、'.join([str(adg_id) for adg_id in adg_id_list])
        mnt_quick_oper_log(shop_id, campaign_id, adg_id_list, stgy_name, opter = opter, opter_name = opter_name)
        if adg_id_list:
            return {'errMsg':'', 'result':result, 'stgy':stgy, 'adg_id_list':adg_id_list}
        else:
            return {'errMsg':'', 'result':result, 'stgy':stgy}
    except Exception, e:
        log.exception('mnt quick oper error, shop_id=%s, campaign_id=%s, e=%s' % (request.user.shop_id, campaign_id, e))
        return {'errMsg':e, 'result':0, 'stgy':stgy}

def change_mntcfg_type(request):
    '''设置重点计划算法导向'''
    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST.get('campaign_id', 0))
    mnt_type = int(request.POST.get('mnt_type', 1))
    opter, opter_name = analysis_web_opter(request)
    mnt_bid_factor = float(request.POST.get('mnt_bid_factor', 0))
    mnt_camp_coll.update({'shop_id': shop_id, '_id': camp_id}, {'$set': {'mnt_bid_factor': mnt_bid_factor}})
    opt_desc = '设置托管宝贝推广意向'
    change_mntcfg_type_log(shop_id = shop_id, campaign_id = camp_id, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
    return {'errMsg':'', 'descr':opt_desc}

def get_adg_list(request):
    '''获取计划下宝贝列表 add by tianxiaohe 20151014'''
    shop_id = int(request.user.shop_id)
    errMsg = ''
    if request.method == "POST":
        campaign_id = int(request.POST.get('campaign_id', 0))
        page_no = int(request.POST.get('page_no', 1))
        page_size = int(request.POST.get('page_size', 100))
        rpt_days = int(request.POST.get('rpt_days', 7))
        search_val = request.POST.get('sSearch', '').strip()

        def binder_adg_rpt_4item(item_list, rpt_days):
            item_id_list = [item.item_id for item in item_list]
            # 获取列表
            adgroup_list = Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id, item_id__in = item_id_list)
            # 获取报表属性
            adgroup_rpt_dict = Adgroup.Report.get_summed_rpt(query_dict = {'shop_id':shop_id, 'campaign_id':campaign_id}, rpt_days = rpt_days)
            rpt_dict = {}
            for adgroup in adgroup_list:

                tmp_rpt = adgroup_rpt_dict.get(adgroup.campaign_id, Adgroup.Report())
                rpt_dict[adgroup.item_id] = {'total_cost':format(tmp_rpt.cost / 100.0, '.2f')
                                             , 'click':tmp_rpt.click
                                             , 'ppc':format_division(tmp_rpt.cost, tmp_rpt.click, 0.01)
                                             , 'total_pay':format(tmp_rpt.pay / 100.0, '.2f')
                                             , 'paycount':tmp_rpt.paycount
                                             , 'roi':format(tmp_rpt.roi / 1, '.2f')
                                             , 'adgroup_id':adgroup.adgroup_id
                                             # , 'limit_price':adgroup.limit_price and format(adgroup.limit_price / 100.0, '.2f') or ''
                                             }
            data = []
            no_photo_url = '/site_media/jl6_temp/static/images/no_photo'
            for item in item_list:
                temp_dict = {'item_id':item.item_id
                             , 'cat_id':item.cat_id
                             , 'price':'%.2f' % (item.price / 100.0)
                             , 'title':item.title
                             , 'has_pic':True if hasattr(item, 'pic_url') and item.pic_url else False
                             , 'pic_url':getattr(item, 'pic_url', ''),
                             }
                temp_dict.update(rpt_dict[item.item_id])
                data.append(temp_dict)
            return data

        item_id_list = list(Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id, mnt_type = 0).values_list('item_id'))
        total_adg_count = Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list).count()
        if search_val:
            item_list = list(Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list, title__icontains = search_val).skip(page_size * (page_no - 1)).limit(page_size + 1))
        else:
            item_list = list(Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list).skip(page_size * (page_no - 1)).limit(page_size + 1))
        if len(item_list) < page_size + 1:
            has_more = 0
        else:
            has_more = 1

        data = binder_adg_rpt_4item(item_list[:page_size], rpt_days)
        into_next_step = request.POST.get('into_next_step', 0)
        return {'errMsg':errMsg, 'data':data, 'has_more':has_more, 'total_adg_count':total_adg_count, 'into_next_step':into_next_step,
                'current_page':page_no, 'page_count':math.ceil(total_adg_count / float(page_size))}

def get_seller_cids(request):
    result_list = CacheAdpter.get(CacheKey.WEB_SHOP_SELLER_CIDS % request.user.shop_id, 'web', [])
    if not result_list:
        tapi = get_tapi(request.user)
        try:
            tobj = tapi.sellercats_list_get(nick = request.user.nick)
        except TopError, e:
            log.error("get_sellercats error, e=%s, shop_id=%s" % (e, request.user.shop_id))
            return {'errMsg': '', 'cat_list': result_list}

        cat_list = []
        # 有这些属性：cid, parent_cid, name, pic_url, sort_order, created, modified, type
        if hasattr(tobj, 'seller_cats') and hasattr(tobj.seller_cats, 'seller_cat'):
            for top_cat in tobj.seller_cats.seller_cat:
                cat_list.append({'cat_id': top_cat.cid, 'cat_name': top_cat.name, 'parent_cat_id': top_cat.parent_cid, 'sort_order': top_cat.sort_order})

        cat_dict = {}
        child_cat_dict = collections.defaultdict(list)

        for cat in cat_list:
            if cat['parent_cat_id'] != 0:
                child_cat_dict[cat['parent_cat_id']].append(cat)
            else:
                cat_dict.update({cat['sort_order']: cat})

        for order, cat in cat_dict.items():
            if cat['cat_id'] in child_cat_dict:
                cat['child_cat_list'] = child_cat_dict[cat['cat_id']]
            else:
                cat['child_cat_list'] = []
            result_list.append(cat)

        CacheAdpter.set(CacheKey.WEB_SHOP_SELLER_CIDS % request.user.shop_id, result_list, 'web', 60 * 10)

    # result_list的格式是这样的：[{'cat_id':1, 'cat_name': '短裤', 'child_cat_list': [{'cat_id':2, 'cat_name': '五分短裤'}]]
    return {'cat_list': result_list, 'errMsg': ''}

def get_item_list(request):
    """采用新的接口，item_onsale_get代替旧的接口，可以直接搜title与seller_cids"""

    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST.get('campaign_id', 0))
    page_no = int(request.POST.get('page_no', 1))
    page_size = int(request.POST.get('page_size', 50))
    search_title = request.POST.get('sSearch', '').strip()
    search_cid = request.POST.get('cids', '').strip()

    def get_top_items(tapi, shop_id, search_title, search_cid):
        """直接从淘宝取出所有的宝贝"""
        kwargs = {
            'fields': 'num_iid,title,cid,seller_cids,pic_url,num,price,sold_quantity',
            'order_by': 'sold_quantity',
            'page_size': 200,
        }
        if search_title or search_cid:
            kwargs['page_no'] = 1
            if search_title:
                kwargs['q'] = search_title
            if search_cid:
                kwargs['seller_cids'] = search_cid
            item_list = []
            top_objects = tapi.items_onsale_get(**kwargs)
            if top_objects and hasattr(top_objects, 'items') and hasattr(top_objects.items, 'item'):
                item_list = top_objects.items.item
        else:
            cache_key = CacheKey.WEB_TOP_ITEM_LIST % (shop_id)
            item_list = CacheAdpter.get_large_list(cache_key, 'web')
            if not item_list:
                item_list = []
                for i in range(1, 101): # TODO: wangqi 20151024 这里最多100页，遇到了确实是要下载半天
                    kwargs['page_no'] = i
                    top_objects = tapi.items_onsale_get(**kwargs)
                    temp_item_list = []
                    if top_objects and hasattr(top_objects, 'items') and hasattr(top_objects.items, 'item'):
                        temp_item_list = top_objects.items.item

                    item_list.extend(temp_item_list)
                    if len(temp_item_list) < kwargs['page_size']:
                        break

                CacheAdpter.set_large_list(cache_key, item_list, 2000, 'web', 60 * 60) # 2000个宝贝一组
        return item_list

    def get_unpromote_item_list(shop_id, campaign_id, item_list, search_title = '', search_cid = ''):
        """过滤出未推广的item_list"""
        existed_item_id_list = list(Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id).values_list('item_id'))
        unpromote_item_list = [item for item in item_list if item.num_iid not in existed_item_id_list]
        return unpromote_item_list

    # FIXME: wangqi 20151201 这里遇到超过2万宝贝的店铺，页面可以提供另一个方式来做，如增加一个输入item_url的方式
    tapi = get_tapi(request.user)
    item_list = get_top_items(tapi, shop_id, search_title, search_cid)
    unpromote_item_list = get_unpromote_item_list(shop_id, campaign_id, item_list, search_title, search_cid)
    if search_title or search_cid:
        page_no = 1
        page_count = 1
        paged_item_list = unpromote_item_list
    else:
        page_count = int(math.ceil(len(unpromote_item_list) / float(page_size)))
        paged_item_list = unpromote_item_list[(page_no - 1) * page_size: page_no * page_size]

    result_list = []
    if paged_item_list:
        item_id_list = [item.num_iid for item in paged_item_list]

        camp_dict = dict(Campaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'title'))
        item_camp_list = Adgroup.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('item_id', 'campaign_id')
        item_camp_dict = collections.defaultdict(list)
        for item_camp in item_camp_list:
             item_camp_dict[item_camp[0]].append(camp_dict.get(item_camp[1], '未'))

        for item in paged_item_list:
            result_list.append({
                'item_id': item.num_iid,
                'title': item.title,
                'cat_id': item.cid,
                'price': '%.2f' % float(item.price),
                'camp_id_list': item_camp_dict.get(item.num_iid, []),
                'has_pic':True if hasattr(item, 'pic_url') and item.pic_url else False,
                'pic_url': getattr(item, 'pic_url', ''),
                'sales_count': '%s笔' % item.sold_quantity,
                'stock': '%s件' % item.num
            })

    return {'errMsg':'', 'data':result_list, 'has_more': page_count > page_no and True or False, 'total_item_count':0, 'current_page':page_no, 'page_count':0}


def update_prop_status(request):
    """修改托管状态，包含两个状态，计划是否暂停与托管是否暂停，一改同时改"""
    try:
        campaign_id = int(request.POST['campaign_id'])
        status = bool(int(request.POST['status']))
        shop_id = int(request.user.shop_id)
        mnt_type = int(request.POST.get('mnt_type', 0))
        opter, opter_name = analysis_web_opter(request)
        online_status, mnt_status, opt_desc = status and ('online', 1, '开启自动优化') or ('offline', 0, '暂停自动优化')
        result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = campaign_id, online_status = online_status, opter = opter, opter_name = opter_name)
        if 'online_status'not in result_list:
            return {'errMsg':'<br/>'.join(msg_list)}
        MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id).update(set__mnt_status = mnt_status)
        data_type = 108
        if mnt_status:
            data_type = 107
        set_cmp_mnt_status_log(shop_id = shop_id, campaign_id = campaign_id, opt_desc = opt_desc, data_type = data_type, opter = opter, opter_name = opter_name)
        # 同步任务状态，托管暂停、优化暂停；托管启动、优化启动
        MntTaskMng.trigger_task_status(shop_id = shop_id, campaign_id = campaign_id, trigger_flag = status)
        return {'errMsg':'', 'status':status and 1 or 0}
    except Exception, e:
        log.info('update mnt campaign prop status error ,e = %s, shop_id = %s' % (e, shop_id))
        return {'errMsg':"%s失败，请刷新页面重新操作！" % opt_desc}


#=======================================================
# 托管流程
#=======================================================
def update_mnt_adg(request):
    '''添加/取消托管adgroup'''
    errMsg = ''
    result = {}
    opter, opter_name = analysis_web_opter(request)

    try:
        shop_id = int(request.user.shop_id)
        camp_id = int(request.POST['camp_id'])
        mnt_adg_dict = json.loads(request.POST['mnt_adg_dict'])
        adg_id_list = [int(adg_id) for adg_id in mnt_adg_dict]

        flag = int(request.POST['flag']) # 1是加入托管, 0是取消托管, 2是将提交的宝贝批量加入托管并将剩下的宝贝取消托管
        if mnt_adg_dict:
            if flag == 2:
                MntMnger.set_mnt_adgroup(shop_id, camp_id, mnt_adg_dict, opter, opter_name)
            elif flag == 1:
                MntMnger.set_mnt_adgroup(shop_id, camp_id, mnt_adg_dict, opter, opter_name)
            elif flag == 0:
                MntMnger.unmnt_adgroup(shop_id, camp_id, adg_id_list, opter, opter_name)

            result['adg_id_list'] = adg_id_list
            result['flag'] = flag
        else:
            result['msg'] = '还未选择任何宝贝'
        # 更改或添加创意
        tapi = get_tapi(request.user)
        update_creative_dict = json.loads(request.POST.get('update_creative_dict', '{}'))
        new_creative_list = json.loads(request.POST.get('new_creative_list', '[]'))
        for creative_id, data in update_creative_dict.items():
            creative_id = int(creative_id)
            adgroup_id, title, img_url = data
            update_creative(tapi = tapi, shop_id = shop_id, adgroup_id = adgroup_id, creative_id = creative_id, title = title, img_url = img_url, opter = opter, opter_name = opter_name)
        if new_creative_list:
            add_creative(tapi = tapi, shop_id = shop_id, campaign_id = camp_id, crt_arg_list = new_creative_list, opter = opter, opter_name = opter_name)
        result['success_msg'] = '将 %s 个宝贝%s托管' % (len(adg_id_list), (flag and '加入' or '取消'))
        result['success_count'] = len(adg_id_list)
    except Exception, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s' % (e, request.user.shop_id))
        errMsg = '托管宝贝失败，请与客服联系'
    result['errMsg'] = errMsg
    return result


def add_new_item(request):
    '''全自动将新宝贝添加为托管
    1. 将增加的宝贝添加为广告组
    2. 将添加成功的广告组，设置成托管宝贝[注意数量限制]，并且还要保存托管设置
    3. 添加成功的宝贝，只提示个数；添加失败的宝贝，要提示原因
    '''
    errMsg = ''
    msg = ''
    result = {}
    opter, opter_name = analysis_web_opter(request)
    def add_items_common(shop_id, campaign_id, new_item_dict):
        """给定item_title_list来添加宝贝"""
        item_arg_list, added_id_list, failed_item_dict = [], [], {}
        if new_item_dict:
            tapi = get_tapi(request.user)
            item_list = Item.get_item_by_ids(shop_id = shop_id, item_id_list = new_item_dict.keys(), tapi = tapi, transfer_flag = True) # 从淘宝获取标准的item数据
            temp_item_dict = {} # 获取部分宝贝信息
            for item in item_list: # 绑定创意标题
                added_item = new_item_dict.get(item['_id'], {})
                if not added_item:
                    continue
                item.update({'adgroup':
                                 {'title': TitleTransfer.remove_noneed_words(added_item['title1']),
                                  'img_url': added_item['img_url1']},
                             'creative':
                                 {'title': TitleTransfer.remove_noneed_words(added_item['title2']),
                                  'img_url': added_item['img_url2']},
                             })
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

    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST['camp_id'])
    new_item_dict = json.loads(request.POST['new_item_dict'])
    new_item_dict = {int(item_id):adg_crt for item_id, adg_crt in new_item_dict.items()}
    mnt_type = int(request.POST.get('mnt_type', 0))

    try:
        success_adg_id_list, failed_item_dict = add_items_common(shop_id = shop_id, campaign_id = camp_id, new_item_dict = new_item_dict)
        msg = '添加成功 %s 个宝贝%%s，添加失败 %s 个宝贝！' % (len(success_adg_id_list), len(failed_item_dict))
        result['success_count'] = len(success_adg_id_list)
        result['failed_count'] = len(failed_item_dict)
    except Exception, e:
        success_adg_id_list, failed_item_dict = [], {}
        log.exception('add items2 error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, camp_id, e))
        msg = '添加成功 %s 个宝贝%%s，添加失败 %s 个宝贝！' % (0, len(new_item_dict))
        errMsg = "未知错误"

    if mnt_type in [1, 2, 3, 4]: # 要处理托管
        try:
            if success_adg_id_list:
                adg_cfg_dict = {}
                adgid_itemid_dict = dict(Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = success_adg_id_list).values_list('adgroup_id', 'item_id'))
                for adg_id in success_adg_id_list:
                    try:
                        adg_cfg = new_item_dict[adgid_itemid_dict[adg_id]]
                        temp_dict = {
                            'mnt_opt_type': int(adg_cfg.get('mnt_opt_type', 1)),
                            'limit_price': int(adg_cfg.get('limit_price') or 200),
                            'mobile_limit_price': int(adg_cfg.get('mobile_limit_price') or 200),
                            'use_camp_limit': int(adg_cfg.get('use_camp_limit', 1))
                        }
                        adg_cfg_dict.update({adg_id: temp_dict})
                    except KeyError:
                        pass
                MntMnger.set_mnt_adgroup(shop_id = shop_id, campaign_id = camp_id, adg_cfg_dict = adg_cfg_dict, opter = opter, opter_name = opter_name)
                msg = msg % '，托管成功'
            else:
                msg = msg % ''
        except Exception, e:
            log.exception('add items2 error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, camp_id, e))
            msg = msg % '，托管失败'
            # msg += '<br/>托管失败原因：%s' % e.message
            errMsg = msg
    else:
        msg = msg % ''
    result['errMsg'] = errMsg
    result['msg'] = msg
    result['failed_item_dict'] = failed_item_dict
    return result

def get_cat_avg_cpc(request):
    '''获取宝贝行业平均值'''
    errMsg = ''
    try:
        shop_id = request.user.shop_id
        cat_id_list = request.POST.getlist('cat_id_list[]')
        cat_id_list = map(int, cat_id_list)
        if not cat_id_list:
            adg_id = int(request.POST.get('adg_id', 0))
            category_ids = Adgroup.objects.filter(shop_id = int(request.user.shop_id), adgroup_id = adg_id).values_list('category_ids')
            if len(category_ids):
                temp_list = category_ids[0].strip().split(' ')
                try:
                    cat_id_list.append(int(temp_list[-1]))
                except:
                    pass
        try:
            cat_path, danger_descr = Cat.get_cat_path(cat_id_list = cat_id_list, last_name = request.user.shop_type).values()[0]
        except Exception, e:
            cat_path = '未获取到值'
            danger_descr = ''
            log.error('mnt_get_cat_avg_cpc get_cat_path error, shop_id=%s, cat_id_list=%s, e = %s' % (shop_id, cat_id_list, e))
        try:
            cat_stat_info = CatStatic.get_market_data(cat_id_list = cat_id_list).values()[0]
            avg_cpc = round(cat_stat_info['cpc'] * 0.01, 2)
            avg_cpc = avg_cpc or 0.50
            avg_cpc_flag = 1
        except Exception, e:
            avg_cpc = 1
            avg_cpc_flag = 0
            log.error('mnt_get_cat_avg_cpc get_cat_stat_info error, shop_id=%s, e = %s' % (shop_id, e))
        return {'errMsg':errMsg, 'cat_path':danger_descr, 'avg_cpc':avg_cpc, 'avg_cpc_flag':avg_cpc_flag, 'cat_path':cat_path}
    except Exception, e:
        log.error('mnt_get_cat_avg_cpc get_cat_avg_cpc error, shop_id=%s, e = %s' % (shop_id, e))
        errMsg = "获取行业均价失败，请联系顾问！"
        return {'errMsg':errMsg}

def update_single_adg_mnt(request):
    '''单个宝贝托管设置'''
    errMsg = ''
    opt_desc = ''
    shop_id = int(request.user.shop_id)
    adg_id = int(request.POST['adg_id'])
    flag = int(request.POST['flag']) # 判断是加入托管还是取消托管
    mnt_type = int(request.POST.get('mnt_type', 1))
    camp_id = int(request.POST['camp_id'])
    use_camp_limit = int(request.POST.get('use_camp_limit', 1))
    limit_price = int(round_digit(float(request.POST.get('limit_price', 0)) * 100)) # 引入 round_digit 是为了解决 int(2.01*100) = 200 的 bug
    mobile_limit_price = int(round_digit(float(request.POST.get('mobile_limit_price', 0)) * 100))
    opter, opter_name = analysis_web_opter(request)

    try:
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type)
    except DoesNotExist, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, mnt_type = %s' % (e, shop_id, mnt_type))
        errMsg = '亲，请刷新页面重新操作！'
        return {'errMsg':errMsg}

    try:
        adg = Adgroup.objects.get(shop_id = shop_id, campaign_id = camp_id, adgroup_id = adg_id)
    except DoesNotExist, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, adg_id = %s' % (e, shop_id, adg_id))
        errMsg = '亲，该宝贝不存在，请刷新页面重新操作！'
        return {'errMsg':errMsg}

    desc_list = ['不托管', '自动优化', '只改价']
    opt_desc = '设置为:%s' % desc_list[flag]
    adg.use_camp_limit = use_camp_limit
    if flag == 0:
        adg.mnt_type = 0
        adg.mnt_time = None
        adg.mnt_opt_type = None
    else:
        adg.mnt_opt_type = flag
        if limit_price:
            adg.limit_price = limit_price
            opt_desc += '，PC端最高限价设置为%.2f元' % (float(limit_price) / 100)
        if mobile_limit_price:
            adg.mobile_limit_price = mobile_limit_price
            opt_desc += '，移动端最高限价设置为%.2f元' % (float(mobile_limit_price) / 100)
        if adg.mnt_type == 0: # 是新托管宝贝时，校验托管宝贝数，初始化托管时间
            exist_mnt_count = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
            if mnt_camp.max_num - exist_mnt_count <= 0:
                errMsg = '托管宝贝失败：您已经托管了%s个宝贝。' % (mnt_camp.max_num)
                return {'errMsg':errMsg}

            adg.mnt_time = datetime.datetime.now()
            adg.mnt_type = mnt_type
            # 触发任务
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type, task_type = 1, adgroup_id_container = {'changed': [adg_id], 'added':[]})
        elif adg.mnt_type > 0 and limit_price:
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type, task_type = 2, adgroup_id_list = [adg_id])
    adg.save()

    change_adg_mnt_log(shop_id = shop_id, campaign_id = camp_id, adgroup_id = adg_id, item_name = adg.item.title, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
    return {'opt_desc':opt_desc, 'errMsg':errMsg, 'adg_id':adg_id, 'flag':flag}

def update_adgs_mnt(request):
    '''批量设置宝贝优化'''
    errMsg = ''
    adg_id_list = request.POST.getlist("adg_id_list[]")
    adg_id_list = [int(adg_id) for adg_id in adg_id_list]
    shop_id = int(request.user.shop_id)
    flag = int(request.POST['flag']) # 判断是加入托管还是取消托管
    mnt_type = int(request.POST.get('mnt_type', 1))
    camp_id = int(request.POST['camp_id'])
    use_camp_limit = int(request.POST.get('use_camp_limit', 1))
    limit_price = int(float(request.POST.get('limit_price', 0)) * 100)
    mobile_limit_price = int(float(request.POST.get('mobile_limit_price', 0)) * 100)
    opter, opter_name = analysis_web_opter(request)

    try:
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type)
    except DoesNotExist, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, mnt_type = %s' % (e, shop_id, mnt_type))
        errMsg = '亲，请刷新页面重新操作！'
        return {'errMsg':errMsg}

    success_list = [] # 成功设置的宝贝list
    try:
        adg_list = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, adgroup_id__in = adg_id_list)
        no_adg_count = len(adg_id_list) - adg_list.count()
    except DoesNotExist, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s' % (e, shop_id))
        errMsg = '亲，请刷新页面重新操作！'
        return {'errMsg':errMsg}

    # 如果设置为自动优化或只改价，则需判断新托管宝贝个数是否超过上限
    if flag:
        new_mntadg_list = [adg for adg in adg_list if adg.mnt_type == 0]
        exist_mnt_count = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
        # 如果超过上限，则返回结果
        if mnt_camp.max_num - exist_mnt_count < len(new_mntadg_list):
            errMsg = '新增托管宝贝达到计划上限，请重新选择！'
            return {'errMsg':errMsg}

    desc_list = ['不托管', '自动优化', '只改价']
    new_mnt_id_list = []
    for adg in adg_list:
        opt_desc = '设置为:%s' % desc_list[flag]
        adg.use_camp_limit = use_camp_limit
        if flag == 0:
            adg.mnt_type = 0
            adg.mnt_time = None
            adg.mnt_opt_type = None
        else:
            adg.mnt_opt_type = flag
            if limit_price:
                adg.limit_price = limit_price
                opt_desc += '，PC端最高限价设置为%.2f元' % (float(limit_price) / 100)
            if mobile_limit_price:
                adg.mobile_limit_price = mobile_limit_price
                opt_desc += '，移动端最高限价设置为%.2f元' % (float(mobile_limit_price) / 100)
            if adg.mnt_type == 0: # 是新托管宝贝时，初始化托管时间
                adg.mnt_time = datetime.datetime.now()
                adg.mnt_type = mnt_type
                new_mnt_id_list.append(adg.id)
        adg.save()
        success_list.append(adg.id)
        change_adg_mnt_log(shop_id = shop_id, campaign_id = camp_id, adgroup_id = adg.id, item_name = adg.item.title, opt_desc = opt_desc, opter = opter, opter_name = opter_name)

    # 如果有新托管宝贝，需要触发任务
    if flag and new_mnt_id_list:
        MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type, task_type = 2, adgroup_id_list = new_mnt_id_list)

    mnt_count = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
    return {'errMsg':errMsg, 'success_list':success_list, 'flag':flag, 'no_adg_count': no_adg_count, 'mnt_count': mnt_count, 'max_num': mnt_camp.max_num}

def update_rt_engine_status(request):
    '''设置宝贝实时优化状态'''
    shop_id = int(request.user.shop_id)
    mnt_type = int(request.POST.get('mnt_type', 1))
    camp_id = int(request.POST['campaign_id'])
    status = int(request.POST['status'], 0)
    opter, opter_name = analysis_web_opter(request)
    errMsg = ''
    try:
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type)
        mnt_camp.mnt_rt = status
        mnt_camp.save()
        opt_desc = '关闭宝贝时实优化'
        if status:
            opt_desc = '开启宝贝实时优化'
        change_rt_engine_log(shop_id = shop_id, campaign_id = camp_id, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
    except DoesNotExist, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, mnt_type = %s' % (e, shop_id, mnt_type))
        errMsg = '亲，请刷新页面重新操作！'
    return {'errMsg':errMsg}
