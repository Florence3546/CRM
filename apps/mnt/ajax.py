# coding=UTF-8
import datetime

from django.core.urlresolvers import reverse
from mongoengine.errors import DoesNotExist

from dajax.core import Dajax
from apilib import get_tapi
from apps.common.utils.utils_json import json
from apps.common.utils.utils_number import format_division
from apps.common.utils.utils_datetime import time_is_someday, date_2datetime
from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_number import fen2yuan
from apps.common.cachekey import CacheKey
from apps.common.biz_utils.utils_misc import analysis_web_opter
from apps.subway.models import Account, Campaign, Adgroup, Item, Creative, adg_coll, Keyword
from apps.subway.upload import (update_campaign, update_adgroups, update_creative, add_creative, mnt_quick_oper_log,
                                change_mntcfg_type_log, change_adg_mnt_log, change_cmp_maxprice_log, udpate_cmp_budget_log,
                                modify_cmp_adg_log, set_cmp_mnt_status_log)
from apps.subway.models_upload import UploadRecord, uprcd_coll
from apps.mnt.models import MntCampaign, MntTaskMng, MntMnger
from apps.mnt.models_mnt import MNT_TYPE_CHOICES
from apps.mnt.utils import get_adgroup_4campaign
from apps.kwslt.models_cat import Cat, CatStatic

# dajax路由函数
def route_dajax(request):
    auto_hide = int(request.POST.get('auto_hide', 1))
    dajax = Dajax()
    if auto_hide:
        dajax.script("PT.hide_loading();")
    if not request.user.is_authenticated():
        dajax.script("alert('您已经退出，请重新登录之后再试');")
        return dajax
    function_name = request.POST.get('function')
    if function_name and globals().get(function_name, ''):
        dajax = globals()[function_name](request = request, dajax = dajax)
    else:
        dajax = log.exception("route_dajax: function_name Does not exist")
    return dajax

# 设置托管计划
def mnt_campaign_setter(request, dajax):
    try:
        shop_id = int(request.user.shop_id)
        namespace = request.POST.get('namespace', 'MntAdg')
        mnt_type = int(request.POST.get('mnt_type'))
        campaign_id = int(request.POST['campaign_id'])
        set_flag = int(request.POST['set_flag']) and True or False # 设置为托管计划或者终止托管计划
        callback_list = json.loads(request.POST.get('callback_list', '[]'))
        opter, opter_name = analysis_web_opter(request)
        if callback_list:
            delay_return = True
            callback = callback_list.pop(0)
            # 上下文参数
            context = json.loads(request.POST.get('context', '{}'))
            ajax_func = 'mnt_mnt_campaign_setter'
            context[ajax_func] = {}
        else:
            delay_return = False
        if mnt_type not in [1, 2, 3, 4]:
            raise Exception()
        if set_flag:
            mnt_rt = int(request.POST['mnt_rt']) # 是否启用实时引擎
            max_price = int(float(request.POST['max_price']) * 100)
            budget = int(request.POST['budget'])
            mnt_index = int(request.POST['mnt_index'])
            more_setting_list = request.POST.getlist('more_setting_list[]')
            MntMnger.set_mnt_camp(campaign_id = campaign_id, flag = set_flag, mnt_index = mnt_index, opter = opter, opter_name = opter_name,
                                  mnt_type = mnt_type, max_price = max_price, budget = budget, mnt_rt = mnt_rt, more_setting_list = more_setting_list)
            if delay_return:
                context[ajax_func]['result'] = 1 # 执行成功
#                 # 首次例行优化任务完成时间
#                 if mnt_type == 1:
#                     context[ajax_func]['1st_optimize_time'] = datetime.now() + timedelta(3)
#                 elif mnt_type == 2:
#                     context[ajax_func]['1st_optimize_time'] = datetime.now() + timedelta(1)
                dajax.script("%s(%s, %s);" % (callback, json.dumps(callback_list), json.dumps(context)))
            else:
                dajax.script('window.location.href = "%s";' % (reverse('mnt_campaign', kwargs = {'mnt_index':mnt_index})))
        else:
            MntMnger.set_mnt_camp(campaign_id = campaign_id, flag = set_flag, mnt_type = mnt_type, opter = opter, opter_name = opter_name)
    except Exception, e:
        if str(e) == "no_permission":
            dajax.script("PT.confirm('您当前的版本需要升级后才可以开通该引擎，要升级吗？', function(){window.open('https://fuwu.taobao.com/ser/detail.html?spm=a1z13.1113643.51940006.43.RmTuNs&service_code=FW_GOODS-1921400&tracelog=category&scm=1215.1.1.51940006', '_blank');},[],this,null,[],this, ['升级'])")
            return dajax
        log.info('mnt_campaign_setter error: %s, mnt_type: %s, campaign_id: %s, shop_id: %s,' % (e, mnt_type, campaign_id, shop_id))
        try:
            result, error_msg = json.loads(e.message)
        except:
            result = 0
            if hasattr(e, 'reason'):
                error_msg = (eval(e.reason))['error_response'].get('sub_msg', '淘宝发生未知错误，请联系顾问')
            else:
                error_msg = e.message
                if 'need to wait' in error_msg:
                    error_msg = 'API接口超限'
        if delay_return:
            context[ajax_func]['result'] = result # 0 执行失败； 2 未全部成功，发生错误
            context[ajax_func]['msg'] = error_msg
            if result == 0:
                context['mnt_update_mnt_adg'] = {}
                context['mnt_update_mnt_adg']['result'] = -1 # 未执行
                context['web_add_items2'] = {}
                context['web_add_items2']['result'] = -1
                dajax.script("PT.ChooseMntcampaign.mnt_campaign_setter_callback(%s, %s);" % (json.dumps([]), json.dumps(context)))
            else:
                dajax.script("%s(%s, %s);" % (callback, json.dumps(callback_list), json.dumps(context)))
        else:
            dajax.script('PT.hide_loading();PT.alert("%s");' % error_msg)
    finally:
        CacheAdpter.delete(CacheKey.WEB_MNT_MENU % shop_id, 'web')
        if not set_flag:
            if namespace == 'MntAdg': # 兼容qnpc
                namespace = 'MntCampaign'
            dajax.script("PT.%s.close_redicet(%s)" % (namespace, campaign_id))
    return dajax

def get_item_list(request, dajax):
    if request.method == "POST":
        shop_id = int(request.user.shop_id)
        campaign_id = int(request.POST.get('campaign_id', 0))
        page_no = int(request.POST.get('page_no', 1))
        page_size = int(request.POST.get('page_size', 100))
        search_val = request.POST.get('sSearch', '').strip()

        # 取数据部分
        page_size_in = 200 # 淘宝取数据，按每页最大取，最多50*200个宝贝
        tapi = get_tapi(request.user)
        exclude_existed = int(request.POST.get('exclude_existed', 1))

        def binder_item_attr_4item(item_list, tapi):
            if not item_list:
                return []
            item_id_list = [item.num_id for item in item_list]
            item_camp_list = list(Adgroup.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('item_id', 'campaign_id'))
            item_camp_dict = {}
            for item_id, camp_id in item_camp_list:
                camp_list = item_camp_dict.get(item_id, [])
                if not camp_list:
                    item_camp_dict[item_id] = camp_list
                if camp_id not in camp_list:
                    camp_list.append(camp_id)
            # 调API批量获取宝贝图片和类目ID
            tapi = get_tapi(request.user)
            temp_item_list = Item.get_item_by_ids(shop_id = shop_id, item_id_list = item_id_list, tapi = tapi, fields = 'num_iid,cid,pic_url,item_img.url')
            no_photo_url = '/site_media/jl/img/no_photo'
            temp_item_dict = {str(top_obj.num_iid):[top_obj.cid, getattr(top_obj, 'pic_url', no_photo_url), getattr(top_obj.item_imgs, 'item_img', [])] for top_obj in temp_item_list if hasattr(top_obj, 'item_imgs')}
            for item in item_list:
#                 try:
#                     tapi_url = tapi.item_get(fields = "item_img.url,cid", num_iid = item.num_id)
#                     item.pic_url = tapi_url.item.item_imgs.item_img[0].url
#                     item.cat_id = tapi_url.item.cid
#                 except Exception, e:
#                     log.error('cannot get item pic_url, error: %s ' % e)
#                     item.pic_url = ''
#                     item.cat_id = 0
                item.cat_id, item.pic_url, item.item_imgs = temp_item_dict.get(str(item.num_id), [0, no_photo_url, []])
                if item.pic_url != no_photo_url:
                    item_imgs = [item_img.url for item_img in item.item_imgs if hasattr(item_img, 'url')]
                    if item.pic_url in item_imgs:
                        item_imgs.remove(item.pic_url)
                    item_imgs.insert(0, item.pic_url)
                    item.item_imgs = item_imgs
                item.camp_id_list = item_camp_dict.get(item.num_id, [])

        # 通过调用API获取该店铺的宝贝并缓存起来
        def get_item_list_8page(request, page_no = 1, page_size = 100):
            cache_key = 'item_list_%s' % shop_id
            try:
                item_list, total_item_count = CacheAdpter.get(cache_key, 'web', [[], 0])
            except:
                item_list, total_item_count = CacheAdpter.get(cache_key, 'web', []), 0
            reset_cache = False
            if not (item_list and total_item_count):
                reset_cache = True
                try:
                    item_list = []
                    top_objects = tapi.simba_adgroup_onlineitemsvon_get(nick = request.user.nick, order_field = 'bidCount', order_by = 'true', page_size = page_size_in, page_no = 1)
                    item_list.extend(top_objects.page_item.item_list.subway_item)
                    total_item_count = top_objects.page_item.total_item
                except Exception, e:
                    log.error('simba_adgroup_onlineitems_get TopError, shop_id=%s, error=%s' % (shop_id, e))
            try:
                if page_no == 0 or exclude_existed: # 0 代表全部取出
                    page_no = (total_item_count - 1) / page_size + 1
                page_no_in = (len(item_list) - 1) / page_size_in + 1
                item_list = item_list[:page_no_in * page_size_in]
#                 raw_total_count = total_item_count
                remain_item_count = page_no * page_size - page_no_in * page_size_in
                # 去掉该计划下的已推广宝贝
                exist_item_id_list = []
                tmp_list = []
                if exclude_existed:
                    exist_item_id_list = list(Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id).values_list('item_id'))
                    tmp_list = [item for item in item_list if item.num_id not in exist_item_id_list]
#                     total_item_count -= len(exist_item_id_list)
                    remain_item_count = page_no * page_size - len(tmp_list)
                while remain_item_count > 0 and page_no_in * page_size_in < total_item_count:
                    reset_cache = True
                    page_no_in += 1
                    top_objects = tapi.simba_adgroup_onlineitemsvon_get(nick = request.user.nick, order_field = 'bidCount', order_by = 'true', page_size = page_size_in, page_no = page_no_in)
                    item_list_inc = top_objects.page_item.item_list.subway_item
                    item_list.extend(item_list_inc)
                    if exclude_existed:
                        item_list_inc = [item for item in item_list_inc if item.num_id not in exist_item_id_list]
                        tmp_list.extend(item_list_inc)
                        remain_item_count -= len(item_list_inc)
                    else:
                        remain_item_count -= page_size_in
            except Exception, e:
                log.error('simba_adgroup_onlineitems_get TopError, shop_id=%s, error=%s' % (shop_id, e))
            if reset_cache:
                CacheAdpter.set(cache_key, [item_list, total_item_count], 'web', 60 * 30)
            if exclude_existed:
                return tmp_list, len(tmp_list)
            else:
                return item_list, total_item_count

        tmp_list = [] # 经过筛选或者切片的一部分宝贝列表

        # 要么根据关键词取，要么根据页码取
        has_more = 1
        if search_val:
            item_list, total_item_count = get_item_list_8page(request, page_no = 0, page_size = page_size)
            for item in item_list:
                if search_val in item.title:
                    tmp_list.append(item)
            if page_no * page_size >= len(tmp_list):
                has_more = 0
            tmp_list = tmp_list[page_no * page_size - page_size:page_no * page_size]
        else:
            item_list, total_item_count = get_item_list_8page(request, page_no = page_no, page_size = page_size)
            if page_no * page_size >= total_item_count:
                has_more = 0
            tmp_list = item_list[page_no * page_size - page_size:page_no * page_size]

        binder_item_attr_4item(tmp_list, tapi)
        data = []
        for item in tmp_list:
            data.append({'item_id':item.num_id, 'cat_id':item.cat_id, 'price':'￥%.2f' % float(item.price), 'title':item.title, 'pic_url':item.pic_url, 'item_imgs':item.item_imgs, 'camp_id_list':item.camp_id_list, 'sales_count':'%s笔' % item.extra_attributes.sales_count, 'stock':'%s件' % item.extra_attributes.quantity})
        namespace = request.POST.get('namespace', 'InitMntAdgroup')
        dajax.script('PT.%s.get_item_list_callback(%s, %s, %s)' % (namespace, json.dumps(data), has_more, total_item_count))
        return dajax

def get_adg_list(request, dajax):
    shop_id = int(request.user.shop_id)
    if request.method == "POST":
        campaign_id = int(request.POST.get('campaign_id', 0))
        page_no = int(request.POST.get('page_no', 1))
        page_size = int(request.POST.get('page_size', 100))
        rpt_days = int(request.POST.get('rpt_days', 7))
        search_val = request.POST.get('sSearch', '').strip()
        namespace = request.POST.get('namespace', 'MntAdgBox')

        def binder_adg_rpt_4item(item_list, rpt_days):
            item_id_list = [item.item_id for item in item_list]
            adgroup_list = Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id, item_id__in = item_id_list)
            adg_rpt_dict = Adgroup.Report.get_summed_rpt(query_dict = {'shop_id': shop_id, 'campaign_id': campaign_id}, rpt_days = rpt_days)
            rpt_dict = {}
            for adgroup in adgroup_list:
                adg_rpt = adg_rpt_dict.get(adgroup.adgroup_id, Adgroup.Report())
                rpt_dict[adgroup.item_id] = {'total_cost':format(adg_rpt.cost / 100.0, '.2f'),
                                             'click':adg_rpt.click,
                                             'ppc':format(adg_rpt.cpc / 100.0, '.2f'),
                                             'total_pay':format(adg_rpt.pay / 100.0, '.2f'),
                                             'paycount':adg_rpt.paycount,
                                             'roi':format(adg_rpt.roi / 1, '.2f'),
                                             'adgroup_id':adgroup.adgroup_id,
                                             'limit_price':adgroup.limit_price and format(adgroup.limit_price / 100.0, '.2f') or '',
                                             }
            data = []
            for item in item_list:
                temp_dict = {'item_id':item.item_id,
                             'cat_id':item.cat_id,
                             'price':'%.2f' % (item.price / 100.0),
                             'title':item.title,
                             'pic_url':item.pic_url
                             }
                temp_dict.update(rpt_dict[item.item_id])
                data.append(temp_dict)
            return data

        item_id_list = list(Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id).values_list('item_id'))
#         total_adg_count = len(item_id_list)
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
        dajax.script('PT.%s.get_adg_list_callback(%s, %s, %s, %s)' % (namespace, json.dumps(data), has_more, total_adg_count, into_next_step))
        return dajax

# 根据逻辑需求已被弃用 设置好重点托管后重置计划下的未托管宝贝暂停推广
def init_impt_adgroup(request, dajax):
    campaign_id = int(request.POST.get('campaign_id'))
    adgroups_2offline = list(Adgroup.objects.filter(shop_id = int(request.user.shop_id), campaign_id = campaign_id, mnt_type__ne = 2).values_list('adgroup_id'))
    adg_arg_dict = {}
    opter, opter_name = analysis_web_opter(request)
    for id in adgroups_2offline:
        adg_arg_dict[id] = {'online_status':'offline'}
    try:
        update_adgroups(shop_id = int(request.user.shop_id), adg_arg_dict = adg_arg_dict, opter = opter, opter_name = opter_name)
    except Exception, e:
        log.error('mnt init_impt_adgroup error,shop_id=%s, campaign_id = %s, e = %s' % (request.user.shop_id, request.POST['campaign_id'], e))
    return dajax

# 选计划时，用于在选择天数时刷新页面数据
def get_campaign_rpt_info(request, dajax):
    rpt_days = int(request.POST.get('rpt_days', 1))
    campaign_list = Campaign.objects.filter(shop_id = int(request.user.shop_id)).only('rpt_list').sum_reports(rpt_days = rpt_days)
    result_list = []
    for campaign in campaign_list:
        result_list.append({'campaign_id':campaign.campaign_id, 'cost':'%.2f' % (campaign.qr.cost / 100.0), 'imp':campaign.qr.impressions, 'click':campaign.qr.click, 'pay':'%.2f' % (campaign.qr.pay / 100.0), 'paycount':campaign.qr.paycount, 'fav':campaign.qr.favcount})
    # mnt_type = request.POST.get('mnt_type', 1)
    dajax.script("PT.ChooseMntcampaign.set_campaign_rpt_data('%s')" % json.dumps(result_list))
    return dajax

def get_mnt_adg(request, dajax):
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST['campaign_id'])
    rpt_days = int(request.POST.get('rpt_days', 1))
    try:
        adg_list, mnt_num = get_adgroup_4campaign(shop_id = shop_id, campaign_id = campaign_id, rpt_days = rpt_days)
        dajax.script("PT.MntAdg.get_adg_back(%s,%s)" % (json.dumps(adg_list), mnt_num))
    except Exception, e:
        log.error('missing args or campaign not exist, campaign_id = %s, e = %s' % (request.POST['campaign_id'], e))
        dajax.script('PT.alert("亲，请刷新页面重新操作！");')
    return dajax

def get_mnt_campaign(request, dajax):
    shop_id = int(request.user.shop_id)
    campaign_id = int(request.POST['campaign_id'])
    rpt_days = int(request.POST.get('rpt_days', 1))
    try:
        camp_rpt_dict = Campaign.Report.get_summed_rpt({'shop_id': shop_id, 'campaign_id': campaign_id}, rpt_days = rpt_days)
        camp_rpt = camp_rpt_dict.get(campaign_id, Campaign.Report())
        # campaign = Campaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id).only('rpt_list').sum_reports(rpt_days = rpt_days)[0]
        result_dict = {'cost':'%.2f' % (camp_rpt.cost / 100.0), 'impr':camp_rpt.impressions, 'click':camp_rpt.click, 'ctr':'%.2f' % camp_rpt.ctr,
                       'cpc':'%.2f' % (camp_rpt.cpc / 100.0), 'directpay':'%.2f' % (camp_rpt.directpay / 100.0), 'indirectpay':'%.2f' % (camp_rpt.indirectpay / 100.0), 'pay':'%.2f' % (camp_rpt.pay / 100.0), 'roi':'%.2f' % camp_rpt.roi,
                       'conv':'%.2f' % camp_rpt.conv, 'directpaycount':camp_rpt.directpaycount, 'indirectpaycount':camp_rpt.indirectpaycount, 'paycount':camp_rpt.paycount,
                       'favshopcount':camp_rpt.favshopcount, 'favitemcount':camp_rpt.favitemcount, 'favcount':camp_rpt.favcount
                       }
        dajax.script("PT.MntCampaign.get_campaign_back(%s)" % json.dumps(result_dict))
    except Exception, e:
        log.error('missing args or campaign not exist, campaign_id = %s, e = %s' % (request.POST['campaign_id'], e))
        dajax.script('PT.alert("亲，请刷新页面重新操作！");')
    return dajax

def update_single_adg_mnt(request, dajax):
    opt_desc = ''
    shop_id = int(request.user.shop_id)
    adg_id = int(request.POST['adg_id'])
    flag = int(request.POST['flag']) # 判断是加入托管还是取消托管
    mnt_type = int(request.POST.get('mnt_type', 1))
    camp_id = int(request.POST['camp_id'])
    limit_price = int(float(request.POST.get('limit_price', 0)) * 100)
    opter, opter_name = analysis_web_opter(request)

    try:
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type)
    except DoesNotExist, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, mnt_type = %s' % (e, shop_id, mnt_type))
        dajax.script('PT.alert("亲，请刷新页面重新操作！");')
        return dajax

    try:
        adg = Adgroup.objects.get(shop_id = shop_id, campaign_id = camp_id, adgroup_id = adg_id)
    except DoesNotExist, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, adg_id = %s' % (e, shop_id, adg_id))
        dajax.script('PT.alert("亲，该宝贝不存在，请刷新页面重新操作！");')
        return dajax

    desc_list = ['不托管', '自动优化', '只改价']
    opt_desc = '设置为:%s' % desc_list[flag]
    if flag == 0:
        adg.mnt_type = 0
        adg.mnt_time = None
        adg.mnt_opt_type = None
    else:
        adg.mnt_opt_type = flag
        if adg.mnt_type == 0: # 是新托管宝贝时，校验托管宝贝数，初始化托管时间
            exist_mnt_count = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
            if mnt_camp.max_num - exist_mnt_count <= 0:
                dajax.script('PT.alert("托管宝贝失败：您已经托管了%s个宝贝。");' % (mnt_camp.max_num))
                return dajax

            adg.mnt_time = datetime.datetime.now()
            adg.mnt_type = mnt_type
            if limit_price:
                adg.limit_price = limit_price
                opt_desc += '，最高限价设置为%.2f元' % (float(limit_price) / 100)
            # 触发任务
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type, task_type = 1, adgroup_id_container = {'changed': [adg_id], 'added':[]})
    adg.save()

    change_adg_mnt_log(shop_id = shop_id, campaign_id = camp_id, adgroup_id = adg_id, item_name = adg.item.title, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
    dajax.script("PT.Adgroup_list.update_mnt_back(%s, %s);" % (adg_id, flag)) # 作页面修改
    return dajax

def update_adg_mnt(request, dajax):
    try:
        adg_id_list = json.loads(request.POST['adg_id_list'])
        opter, opter_name = analysis_web_opter(request)
        if adg_id_list:
            opt_desc = ''
            flag = int(request.POST['flag']) # 判断是加入托管还是取消托管
            shop_id = int(request.user.shop_id)
            mnt_type = int(request.POST.get('mnt_type', 1))
            camp_id = int(request.POST['camp_id'])
            limit_price = int(float(request.POST.get('limit_price', 0)) * 100)
            use_camp_limit = int(request.POST.get('use_camp_limit', 0))
            try:
                mnt_campaign = MntCampaign.objects.get(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type)
            except DoesNotExist, e:
                log.info('set adgroups mnt status error, e= %s, shop_id = %s, mnt_type=%s' % (e, shop_id, mnt_type))
                dajax.script('PT.alert("亲，请刷新页面重新操作！");')
                return dajax

            mnt_desc_dict = dict(MNT_TYPE_CHOICES)
            mnt_desc = mnt_desc_dict.get(mnt_type, '长尾托管')
            if flag:
                exist_mnt_count = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
                mnt_max_count = mnt_campaign.max_num
                last_index = mnt_max_count - exist_mnt_count
                last_index = last_index > 0 and last_index or 0
                adg_id_list1 = adg_id_list[:last_index]
                if adg_id_list1:
                    if mnt_type in [1, 3]:
                        Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list1).update(set__mnt_type = mnt_type, set__mnt_time = datetime.datetime.now(), set__mnt_opt_type = 1)
                        opt_desc = '加入%s' % mnt_desc
                    elif mnt_type in [2, 4]:
                        if limit_price:
                            Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list1).update(set__mnt_type = mnt_type, set__mnt_time = datetime.datetime.now(),
                                                                                                            set__limit_price = limit_price, set__use_camp_limit = use_camp_limit,
                                                                                                            set__mnt_opt_type = 1)
                            opt_desc = '加入%s，最高限价设置为%.2f元' % (mnt_desc, float(limit_price) / 100)
                        else:
                            Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list1).update(set__mnt_type = mnt_type, set__mnt_time = datetime.datetime.now(), set__mnt_opt_type = 1)
                            opt_desc = '加入%s' % mnt_desc
                    adg_id_list_offline = list(Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list1, online_status = 'offline').values_list('adgroup_id'))
                    if adg_id_list_offline:
                        adg_arg_dict = {}
                        for id in adg_id_list_offline:
                            adg_arg_dict[id] = {'online_status':'online'}
                        try:
                            update_adgroups(shop_id = shop_id, adg_arg_dict = adg_arg_dict, opter = opter, opter_name = opter_name)
                        except Exception, e:
                            log.error('mnt update_adg_mnt error,shop_id=%s, campaign_id = %s, e = %s' % (request.user.shop_id, camp_id, e))
                    if opt_desc:
                        modify_cmp_adg_log(shop_id = shop_id, campaign_id = camp_id, adg_id_list = adg_id_list1, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
                if mnt_type in [2, 4]:
                    adg_id_list2 = adg_id_list[last_index:]
                    if adg_id_list2:
                        Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list2).update(set__mnt_type = 0, set__mnt_time = None)
            else:
                if mnt_type in [1, 3]:
                    Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list).update(set__mnt_type = 0, set__mnt_opt_type = 1, set__mnt_time = None)
                    opt_desc = '取消%s' % (len(adg_id_list), mnt_desc)
                elif mnt_type in [2, 4]:
                    Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list).update(set__mnt_type = 0, set__mnt_opt_type = 1, set__mnt_time = None)
                    opt_desc = '取消%s' % (mnt_desc)
                if opt_desc:
                    modify_cmp_adg_log(shop_id = shop_id, campaign_id = camp_id, adg_id_list = adg_id_list, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
            # 触发任务，或者更新任务并延时
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type, task_type = 1, adgroup_id_container = flag and {'changed':adg_id_list, 'added':[]} or adg_id_list)
            dajax.script("PT.Adgroup_list.update_mnt_back('%s', %s);" % (json.dumps(adg_id_list), flag)) # 作页面修改
        else:
            dajax.script("PT.alert('未选择任何宝贝！');")

    except Exception, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, mnt_type=%s' % (e, shop_id, mnt_type))
        dajax.script('PT.alert("亲，请等待页面加载完全再操作哦！");')
    return dajax

def update_mnt_adg(request, dajax):
    '''
    添加/取消托管adgroup
    '''
    def take_adg_online(adg_id_list):
        '''
        将adg_id_list中暂停推广的宝贝开启推广
        '''
        adg_id_list_offline = list(Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list, online_status = 'offline').values_list('adgroup_id'))
        if adg_id_list_offline:
            adg_arg_dict = {}
            for id in adg_id_list_offline:
                adg_arg_dict[id] = {'online_status':'online'}
            try:
                update_adgroups(shop_id = shop_id, adg_arg_dict = adg_arg_dict)
            except Exception, e:
                log.error('mnt update_adg_mnt error,shop_id=%s, campaign_id = %s, e = %s' % (request.user.shop_id, camp_id, e))
    try:
        shop_id = int(request.user.shop_id)
        camp_id = int(request.POST['camp_id'])
        namespace = request.POST.get('namespace', 'MntAdg')
        mnt_adg_dict = json.loads(request.POST['mnt_adg_dict'])
        adg_id_list = [int(adg_id) for adg_id in mnt_adg_dict]
        opter, opter_name = analysis_web_opter(request)

        # 回调函数列表
        callback_list = json.loads(request.POST.get('callback_list', '[]'))
        if callback_list:
            delay_return = True
            callback = callback_list.pop(0)
            # 上下文参数
            context = json.loads(request.POST.get('context', '{}'))
            ajax_func = 'mnt_update_mnt_adg'
            context[ajax_func] = {}
        else:
            delay_return = False

        flag = int(request.POST['flag']) # 1是加入托管, 0是取消托管, 2是将提交的宝贝批量加入托管并将剩下的宝贝取消托管
        if mnt_adg_dict:
            mnt_type = int(request.POST.get('mnt_type', 1))
            mnt_campaign = MntCampaign.objects.get(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type)

            if flag == 2:
                exist_mnt_adg_list = list(Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).values_list('adgroup_id'))
                # 将未选中的宝贝取消托管，长尾计划下的未托管宝贝交由定时优化任务删除
                adg_id_list_2remove = list(set(exist_mnt_adg_list) - set(adg_id_list))
                if adg_id_list_2remove:
                    Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list_2remove).update(set__mnt_type = 0, set__mnt_time = None)
                    descr = '取消托管'
                    modify_cmp_adg_log(shop_id = shop_id, campaign_id = camp_id, adg_id_list = adg_id_list_2remove, opt_desc = descr, opter = opter, opter_name = opter_name)
                    MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type, task_type = 1, adgroup_id_container = adg_id_list_2remove)
                # 将选中的宝贝加入托管
                adg_id_list = list(set(adg_id_list) - set(exist_mnt_adg_list))
                if adg_id_list:
                    if mnt_type in [1, 3]:
                        Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list).update(set__mnt_type = 1, set__mnt_time = datetime.datetime.now(), set__use_camp_limit = 1, set__mnt_opt_type = 1)
                    elif mnt_type in [2, 4]:
                        for adg_id, fields in mnt_adg_dict.items():
                            Adgroup.objects.filter(shop_id = shop_id, adgroup_id = int(adg_id)).update(set__mnt_type = 2, set__mnt_time = datetime.datetime.now(), set__limit_price = int(fields['limit_price']),
                                                                                                       set__use_camp_limit = 0, set__mnt_opt_type = 1)
                    take_adg_online(adg_id_list)
            elif flag == 1:
                exist_mnt_count = Adgroup.objects.filter(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type).count()
                mnt_max_count = mnt_campaign.max_num
                last_index = mnt_max_count - exist_mnt_count
                last_index = last_index > 0 and last_index or 0
                adg_id_list = adg_id_list[:last_index]
                if adg_id_list:
                    if mnt_type in [1, 3]:
                        Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list).update(set__mnt_type = 1, set__mnt_time = datetime.datetime.now(), set__use_camp_limit = 1, set__mnt_opt_type = 1)
                    elif mnt_type in [2, 4]:
                        for adg_id in adg_id_list:
                            Adgroup.objects.filter(shop_id = shop_id, adgroup_id = adg_id).update(set__mnt_type = 2, set__mnt_time = datetime.datetime.now(), set__limit_price = int(mnt_adg_dict[str(adg_id)]['limit_price']),
                                                                                                  set__use_camp_limit = 0, set__mnt_opt_type = 1)
                    take_adg_online(adg_id_list)
            elif flag == 0:
                Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list).update(set__mnt_type = 0, set__mnt_time = None)

            # 记下操作日志，看用户添加/取消了多少长尾托管宝贝
            descr = '%s托管' % (flag and '加入' or '取消')
            modify_cmp_adg_log(shop_id = shop_id, campaign_id = camp_id, adg_id_list = adg_id_list, opt_desc = descr, opter = opter, opter_name = opter_name)
            # 触发任务，或者更新任务并延时
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type, task_type = 1, adgroup_id_container = flag and {'changed':adg_id_list, 'added':[]} or adg_id_list)
            if not delay_return:
                dajax.script("PT.%s.update_mnt_back('%s',%s);" % (namespace, json.dumps(adg_id_list), flag)) # 作页面修改
        elif not delay_return:
            dajax.script("PT.alert('未选择任何宝贝！');")

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
        if delay_return:
            context[ajax_func]['result'] = 1 # 执行成功
            context[ajax_func]['msg'] = '将 %s 个宝贝%s托管' % (len(adg_id_list), (flag and '加入' or '取消'))
    except Exception, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, mnt_type=%s' % (e, shop_id, mnt_type))
        if delay_return:
            context[ajax_func]['result'] = 0 # 执行失败
            context[ajax_func]['msg'] = '托管宝贝失败，请与客服联系'
        else:
            dajax.script('PT.hide_loading();PT.alert("托管宝贝失败，请与客服联系！");')
    finally:
        if delay_return:
            dajax.script("%s(%s, %s);" % (callback, json.dumps(callback_list), json.dumps(context)))
    return dajax

def update_cfg(request, dajax):
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
                dajax.script('PT.alert("亲，请刷新页面重新操作！");')
                return dajax
            old_budget = campaign.budget
            new_budget = submit_data['budget']
            result_list, msg_list = update_campaign(shop_id = shop_id, campaign_id = int(campaign_id), record_flag = False, budget = new_budget,
                                                    use_smooth = campaign.is_smooth and 'true' or 'false', opter = opter, opter_name = opter_name)
            if 'budget' in result_list:
                display_budget = lambda x: x == 20000000 and '不限' or ('%s元' % x)
                opt_desc = '日限额由%s，修改为%s' % (display_budget(old_budget / 100), display_budget(new_budget))
                udpate_cmp_budget_log(shop_id = shop_id, campaign_id = campaign_id, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
            else:
                dajax.script('PT.alert("%s");' % ('<br/>'.join(msg_list)))
                return dajax

        if submit_data.has_key('max_price'):
            try:
                mnt_campaign = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
            except DoesNotExist, e:
                log.info('can not get mnt_campaign, campaign_id = %s' % campaign_id)
                dajax.script('PT.alert("亲，请刷新页面重新操作！");')
                return dajax

            old_max_price = mnt_campaign.max_price
            new_max_price = int(float(submit_data.get('max_price', old_max_price / 100.0)) * 100)
            if new_max_price != old_max_price:
                mnt_campaign.max_price = new_max_price
                change_cmp_maxprice_log(shop_id = shop_id, campaign_id = campaign_id, max_price = new_max_price, opter = opter, opter_name = opter_name)
                MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = campaign_id, mnt_type = mnt_type, task_type = 2, adgroup_id_list = 'ALL')

            mnt_campaign.save()

        dajax.script('PT.MntCampaign.submit_cfg_back("%s","%s");' % (submit_data.get('budget', ''), submit_data.get('max_price', '')))
    except Exception, e:
        log.info('submit MntCampaign cfg error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, e))
        dajax.script('PT.alert("%s");' % (error_msg == '' and '修改失败，请刷新页面重新操作！' or error_msg))

    return dajax

def quick_oper(request, dajax):
    """触发页面上的“加大投入/减小投入”"""
    try:
        shop_id = int(request.user.shop_id)
        campaign_id = int(request.POST['campaign_id'])
        adg_id_list = request.POST.getlist("adg_id_list[]")
        adg_id_list = [int(adg_id) for adg_id in adg_id_list]
        stgy = int(request.POST['stgy'])
        mnt_campaign = MntCampaign.objects.get(campaign_id = campaign_id, shop_id = shop_id)
        now = datetime.datetime.now()
        if adg_id_list:
            MntTaskMng.generate_quickop_task(shop_id = mnt_campaign.shop_id, campaign_id = mnt_campaign.campaign_id, mnt_type = mnt_campaign.mnt_type, stgy = stgy, adgroup_id_list = adg_id_list)
            adg_coll.update({'shop_id': shop_id, 'campaign_id':campaign_id, '_id':{'$in': adg_id_list}},
                            {'$set':{'quick_optime': now}}, multi = True
                            )
            dajax.script("PT.MntCampaign.quick_oper_adg_back(1, %s, '%s');" % (stgy, json.dumps(adg_id_list)))
        else:
            if not mnt_campaign.quick_optime or not time_is_someday(mnt_campaign.quick_optime):
                MntTaskMng.generate_quickop_task(shop_id = shop_id, campaign_id = mnt_campaign.campaign_id, mnt_type = mnt_campaign.mnt_type, stgy = stgy)
                # 不管执行成功或者失败，都不让再操作 TODO: wangqi 20140516 如果需要马上执行，这里可以用新线程执行
                mnt_campaign.quick_optime = now
                mnt_campaign.save()
                dajax.script('PT.MntCampaign.quick_oper_back(1, %s);' % stgy)
            else:
                dajax.script('PT.MntCampaign.quick_oper_back(2, %s);' % stgy)
        # 写入操作记录
        stgy_name = '加大投入' if stgy == 1 else '减小投入'
        opt_type = 15 if stgy == 1 else 16
        opter, opter_name = analysis_web_opter(request)
        adg_ids = '、'.join([str(adg_id) for adg_id in adg_id_list])

        mnt_quick_oper_log(shop_id, campaign_id, adg_id_list, stgy_name, opter = opter, opter_name = opter_name)
    except Exception, e:
        log.exception('mnt quick oper error, shop_id=%s, campaign_id=%s, e=%s' % (request.user.shop_id, campaign_id, e))
        dajax.script('PT.MntCampaign.quick_oper_back(0, %s);' % stgy)
    return dajax

def update_prop_status(request, dajax):
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
            raise Exception('<br/>'.join(msg_list))
        MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id).update(set__mnt_status = mnt_status)
        data_type = 108
        if mnt_status:
            data_type = 107
        set_cmp_mnt_status_log(shop_id = shop_id, campaign_id = campaign_id, opt_desc = opt_desc, data_type = data_type, opter = opter, opter_name = opter_name)

        # 同步任务状态，托管暂停、优化暂停；托管启动、优化启动
        MntTaskMng.trigger_task_status(shop_id = shop_id, campaign_id = campaign_id, trigger_flag = status)
        dajax.script('PT.MntCampaign.update_camp_back(%s)' % (status and 1 or 0))
    except Exception, e:
        log.info('update mnt campaign prop status error ,e = %s, shop_id = %s' % (e, shop_id))
        dajax.script("PT.alert('%s失败，请刷新页面重新操作！');" % (opt_desc))
    return dajax

# 获取托管计划操作记录
def get_opt_record(request, dajax):

    campaign_id = int(request.POST['campaign_id'])
    last_date = datetime.date.today() - datetime.timedelta(days = 15)
    result_list = []
    uprcd_list = uprcd_coll.find({'campaign_id':campaign_id, 'opt_time':{'$gte':date_2datetime(last_date)}}).sort([('opt_time', -1)])
    for uprcd in uprcd_list:
        try:
            opt_type = UploadRecord.get_choices_text(UploadRecord.DATA_TYPE_CHOICES, uprcd['data_type'])
            opter = UploadRecord.get_choices_text(UploadRecord.OPERATOR_CHOICES, uprcd['opter'])
            if uprcd.has_key('detail_list') and uprcd['detail_list']:
                for detail in uprcd['detail_list']:
                    result_list.append({'opter': opter, 'opt_time': datetime.datetime.strftime(uprcd['opt_time'], '%Y-%m-%d %H:%M:%S'), 'opt_type': opt_type, 'opt_desc':detail})
        except Exception, e:
            log.error(e)
    result_list.sort(key = lambda k: k['opt_time']) # 对时间排序
    dajax.script('PT.MntCampaign.opt_record_back(%s);' % json.dumps(result_list))
    return dajax

def get_adgroup_data(request, dajax):
    """查看长尾托管单个关键词详情"""
    # 获取页面参数
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.POST.get('adgroup_id'))
    rpt_days = int(request.POST.get('last_day', 3))

    # 准备数据，该处不需要捕捉DoesNotExist异常，因为进入View时已经校验过了
    adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
    adgroup.recover_kw_rpt()

    # 封装定向推广数据
    adgroup.rpt_days = rpt_days
    json_nosraech_data = {"impressions":adgroup.rpt_nosch.impressions,
                          "click":adgroup.rpt_nosch.click,
                          "ctr":format(adgroup.rpt_nosch.ctr, '.2f'),
                          "cost":format(adgroup.rpt_nosch.cost / 100.0, '.2f'),
                          "cpc":format(adgroup.rpt_nosch.cpc / 100.0, '.2f'),
                          "avgpos":adgroup.rpt_nosch.avgpos,
                          "favcount":adgroup.rpt_nosch.favcount,
                          "paycount":adgroup.rpt_nosch.paycount,
                          "pay":format(adgroup.rpt_nosch.pay / 100.0, '.2f'),
                          "conv":format(adgroup.rpt_nosch.conv, '.2f'),
                          "roi":format(adgroup.rpt_nosch.roi, '.2f'),
                          "favctr":adgroup.rpt_nosch.click and format(adgroup.rpt_nosch.favcount * 100.0 / adgroup.rpt_nosch.click, '.2f') or '0.00',
                          "favpay":adgroup.rpt_nosch.favcount and format(adgroup.rpt_nosch.cost / (adgroup.rpt_nosch.favcount * 100.0), '.2f') or '0.00',
                          }

    json_keyword_data = []
    # full_kw_list = Keyword.get_kw_g_bypymongo(shop_id, adgroup_id, rpt_days = rpt_days)
    full_kw_list = []
    for kw in full_kw_list:
        json_keyword_data.append({"keyword_id":kw.keyword_id,
                                  "word":kw.word,
                                  "create_days":kw.create_days,
                                  "max_price":format(kw.max_price / 100.0, '.2f'),
                                  "new_price":format(kw.new_price / 100.0, '.2f'),
                                  "qscore":kw.qscore,
                                  "impressions":kw.sum_rpts.impressions,
                                  "click":kw.sum_rpts.click,
                                  "ctr":format(kw.sum_rpts.ctr, '.2f'),
                                  "cost":format(kw.sum_rpts.cost / 100.0, '.2f'),
                                  "cpm":format(kw.sum_rpts.cpm / 100.0, '.2f'),
                                  "cpc":format(kw.sum_rpts.cpc / 100.0, '.2f'),
                                  "avgpos":kw.sum_rpts.avgpos,
                                  "favcount":kw.sum_rpts.favcount,
                                  "paycount":kw.sum_rpts.paycount,
                                  "pay":format(kw.sum_rpts.pay / 100.0, '.2f'),
                                  "conv":format(kw.sum_rpts.conv, '.2f'),
                                  "roi":format(kw.sum_rpts.roi, '.2f'),
                                  "g_click":format_division(kw.g_click , 1, 1, '0'),
                                  "g_ctr":format_division(kw.g_click , kw.g_pv),
                                  "g_cpc":format_division(kw.g_cpc , 100, 1),
                                  "g_competition":format_division(kw.g_competition , 1, 1, '0'),
                                  "g_pv":kw.g_pv,
                                  "match_scope":kw.match_scope,
                                  "favctr": format(kw.sum_rpts.favcount * 100.0 / kw.sum_rpts.click, '.2f') if kw.sum_rpts.click else '0.00',
                                  "favpay": format(kw.sum_rpts.cost / (kw.sum_rpts.favcount * 100.0), '.2f') if kw.sum_rpts.favcount else '0.00',
                                })

    # 获取用户自定义列
    custom_column = Account.get_custom_col(shop_id = shop_id)
    dajax.script('PT.Mnt_adgroup_data.table_callback(%s)' % (json.dumps({'nosraech':json_nosraech_data, 'keyword':json_keyword_data, 'custom_column':custom_column})))
    return dajax

def get_gsw_recm_price(request, dajax):
    '''获取长尾计划下关键词最高出价推荐值'''
    recm_price = MntCampaign.get_gsw_recm_price(int(request.user.shop_id))
    dajax.script("$('#max_price').val('%s');" % recm_price)
    return dajax

def get_cat_avg_cpc(request, dajax):
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
            log.error('mnt_get_cat_avg_cpc get_cat_path error, shop_id=%s, e = %s' % (shop_id, e))
        try:
            cat_stat_info = CatStatic.get_market_data(cat_id_list = cat_id_list).values()[0]
            avg_cpc = round(cat_stat_info['cpc'] * 0.01, 2)
            avg_cpc = avg_cpc or 0.50
            avg_cpc_flag = 1
        except Exception, e:
            avg_cpc = 1
            avg_cpc_flag = 0
            log.error('mnt_get_cat_avg_cpc get_cat_stat_info error, shop_id=%s, e = %s' % (shop_id, e))
        namespace = request.POST.get('namespace', 'AddItemBox3')
        dajax.script('PT.%s.get_cat_avg_cpc("%s", "%s", %s, %s);' % (namespace, cat_path, danger_descr, avg_cpc, avg_cpc_flag))
    except Exception, e:
        log.error('mnt_get_cat_avg_cpc get_cat_avg_cpc error, shop_id=%s, e = %s' % (shop_id, e))
        dajax.script('PT.alert("获取行业均价失败，请联系顾问！");')
    return dajax

def record_adg_keyword(request, dajax):
    dajax.script("PT.alert('监控失败，请联系管理员！');")
    return dajax


def get_snap_keyword_list(request, dajax):
    dajax.script("PT.alert('获取关键词失败！');")
    return dajax

def change_mntcfg_type(request, dajax):
    from apps.mnt.models_mnt import mnt_camp_coll

    shop_id = int(request.user.shop_id)
    camp_id = int(request.POST.get('camp_id', 0))
    mnt_type = int(request.POST.get('mnt_type', 1))
    cfg_type = request.POST.get('cfg_type', '')
    opter, opter_name = analysis_web_opter(request)

    mnt_dict = {'roi': ('zd_mnt_cfg', '投资回报导向'), 'pv': ('zd_pv_mnt_cfg', '流量导向')}
    if cfg_type not in mnt_dict:
        log.error("get mnt cfg type error: cfg_type = %s" % cfg_type)
        return dajax
    mnt_camp_coll.update({'shop_id': shop_id, '_id': camp_id}, {'$set': {'mnt_cfg_list': [mnt_dict[cfg_type][0]]}})

    opt_desc = '设置托管算法为：%s' % mnt_dict[cfg_type][1]
    change_mntcfg_type_log(shop_id = shop_id, campaign_id = camp_id, opt_desc = opt_desc, opter = opter, opter_name = opter_name)
    return dajax

def get_forecast_data(request, dajax):
    dajax.script('PT.MntForecast.table_callback(%s)' % (json.dumps({'keyword':[], 'cfg_dict': {}, 'instrcn_list': {}})))
    return dajax

def update_rt_engine_status(request, dajax):
    shop_id = int(request.user.shop_id)
    mnt_type = int(request.POST.get('mnt_type', 1))
    camp_id = int(request.POST['campaign_id'])
    status = int(request.POST['status'])
    try:
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = camp_id, mnt_type = mnt_type)
        mnt_camp.mnt_rt = status
        mnt_camp.save()
    except DoesNotExist, e:
        log.info('set adgroups mnt status error, e= %s, shop_id = %s, mnt_type = %s' % (e, shop_id, mnt_type))
        dajax.script('PT.alert("亲，请刷新页面重新操作！");')
        return dajax
    dajax.script('PT.MntCampaign.rt_engine_status_back(%s)' % (status))
    return dajax
