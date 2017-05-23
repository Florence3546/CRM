# coding=UTF-8

import datetime
from threading import Thread

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from mongoengine.errors import DoesNotExist

from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import time_humanize, datetime_2string, time_is_someday, time_is_recent
from apps.mnt.models import MntCampaign, MNT_TYPE_CHOICES
from apps.web.forms import AdgroupSearchForm
from apps.web.utils import get_trend_chart_data, get_isneed_phone
from apps.subway.models import Account, Campaign
from apps.subway.models_keyword import Keyword, attn_coll
from apps.subway.download import Downloader
from apps.router.login import LoginQnpc
from apps.common.biz_utils.utils_permission import AUTO_RANKING_CODE, ATTENTION_CODE, test_permission
from apps.engine.models_corekw import CoreKeyword

@login_required
def qnpc_home(request, template = 'qnpc_home.html'):
    if hasattr(request, 'session') and request.session.get('next_url', ''):
        next_url = request.session['next_url']
        del request.session['next_url']
        return HttpResponseRedirect(next_url)

    shop_id = int(request.user.shop_id)
    try:
        account = Account.objects.get(shop_id = shop_id)
    except DoesNotExist:
        # return render_to_limited(request, '您的直通车账户不存在，请确认登陆账号是否正确')
        return LoginQnpc(request=None).redirect_2top_authorize()

    isneed_phone = get_isneed_phone(request.user)

    return render_to_response(template, {'account':account,'isneed_phone': isneed_phone },
                              context_instance = RequestContext(request)
                              )

@login_required
def campaign_list(request, template = 'qnpc_campaign_list.html'):
    return render_to_response(template, {}, context_instance = RequestContext(request))

@login_required
def adgroup_list(request, campaign_id = 0, template = 'qnpc_adgroup_list.html'):
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 1))
    search_list_form = AdgroupSearchForm(shop_id = shop_id, initial = {'campaign_id':campaign_id})
    try:
        campaign_id = int(campaign_id)
    except:
        campaign_id = 0
    if campaign_id:
        mnt_campaigns = MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id)
        if len(mnt_campaigns):
            mnt_type = mnt_campaigns[0].mnt_type
        else:
            mnt_type = 0
        no_mnt_campaigns = []
    else:
        mnt_type = 0
        mnt_campaign_list = list(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id'))
        no_mnt_campaigns = Campaign.objects.only('campaign_id', 'title').filter(shop_id = shop_id, campaign_id__nin = mnt_campaign_list)
    camp_dict = dict(Campaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'title'))
    return render_to_response(template, {'last_day':last_day,
                                                                   'camp_dict':camp_dict,
                                                                   'cur_camp_id':campaign_id,
                                                                   'mnt_type':mnt_type,
                                                                   'no_mnt_campaigns':no_mnt_campaigns,
                                                                   'add_item_flag':request.GET.get('add_item_flag', 0),
                                                                   }, context_instance = RequestContext(request))

@login_required
def attention_list(request, template = 'qnpc_attention_list.html'):
    shop_id = int(request.user.shop_id)
    attention_count = 0
    attention = attn_coll.find_one({'_id':shop_id})
    if attention:
        attention_count = len(attention['keyword_id_list'])

    if attention_count:
        dler_obj = Downloader.objects.get(shop_id = shop_id)
        dl_flag, _ = dler_obj.check_status_4rpt(klass = Keyword)
        if dl_flag and dler_obj.tapi:
            result, _ = Keyword.download_kwrpt_bycond(shop_id = shop_id, tapi = dler_obj.tapi, token = dler_obj.token, rpt_days = 15, cond = 'click')
            if result:
                status_str = '%s_OK' % datetime_2string()
                dler_obj.keywordrpt_status = status_str
                dler_obj.save()

    last_day = 7
    return render_to_response(template, {'last_day':last_day}, context_instance = RequestContext(request))

# @login_required
# def choose_mnt_campaign_old(request, mnt_index, template = 'qnpc_choose_mnt_campaign.html'):
#     shop_id = request.user.shop_id
#     if int(mnt_index) not in MntMnger.get_valid_indexes(user = request.user):
#         return HttpResponseRedirect(MntMnger.get_limited_url())
#     mnt_campaign = MntCampaign.objects.filter(shop_id = shop_id, mnt_index = mnt_index)
#     if mnt_campaign:
#         return HttpResponseRedirect(reverse('qnpc_mnt_campaign', kwargs = {'mnt_index':mnt_index}))
#     mnt_campaign_dict = dict(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'mnt_type'))
#     campaign_list = list(Campaign.objects.filter(shop_id = shop_id))

#     mnt_desc_dict = dict(MNT_TYPE_CHOICES)

#     for campaign in campaign_list:
#         mnt_type = mnt_campaign_dict.get(campaign.campaign_id, 0)
#         mnt_name = mnt_desc_dict.get(mnt_type, '')
#         campaign.mnt_type = mnt_type
#         campaign.mnt_name = mnt_name
#     max_price_recm = MntCampaign.get_gsw_recm_price(shop_id = shop_id)
#     return render_to_response(template, {'campaign_list': campaign_list, 'max_price_recm':max_price_recm, 'mnt_index':mnt_index}, context_instance = RequestContext(request))


@login_required
def choose_mnt_campaign(request, campaign_id = 0, template = 'qnpc_choose_mnt_campaign.html'):
    shop_id = int(request.user.shop_id)
    mnt_campaign = MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id)
    if mnt_campaign:
        return HttpResponseRedirect(reverse('qnpc_mnt_campaign', kwargs = {'campaign_id': campaign_id}))
    mnt_campaign_dict = dict(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'mnt_type'))
    campaign_list = list(Campaign.objects.filter(shop_id = shop_id))
    mnt_desc_dict = dict(MNT_TYPE_CHOICES)
    for campaign in campaign_list:
        campaign.mnt_type = mnt_campaign_dict.get(campaign.campaign_id, 0)
        campaign.mnt_name = mnt_desc_dict.get(campaign.mnt_type, '')
    campaign_list.sort(key = lambda x:x.mnt_type, reverse = False)
    max_price_recm = MntCampaign.get_gsw_recm_price(shop_id = shop_id)
    camp_dict = dict(Campaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'title'))
    return render_to_response(template, {'campaign_list': campaign_list,
                                         'max_price_recm':max_price_recm,
                                         'campaign_id': campaign_id,
                                         'camp_dict':camp_dict,
                                         'default_campaign':int(request.GET.get('campaign_id', 0))
                                         }, context_instance = RequestContext(request))


@login_required
def mnt_campaign(request, campaign_id, template = 'qnpc_mnt_campaign.html'):
    shop_id = int(request.user.shop_id)
    campaign_id = int(campaign_id)
    try:
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
        temp_camp = Campaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
    except DoesNotExist, e:
        log.error('get mnt campaign failed, shop_id=%s, camp_id=%s, e=%s' % (shop_id, campaign_id, e))
        # return render_to_error(request, '该托管计划不存在，请返回页面重新操作')
        return render_to_response('qnpc_error.html', {'msg': '该托管计划不存在，请返回页面重新操作'}, context_instance = RequestContext(request))
    mnt_camp.budget, mnt_camp.title, mnt_camp.online_status, mnt_camp.comment_count = \
        temp_camp.budget, temp_camp.title, temp_camp.online_status, temp_camp.comment_count

    if not mnt_camp.optimize_time:
        mnt_camp.optimize_time = '尚未优化'
    else:
        mnt_camp.optimize_time = time_humanize(mnt_camp.optimize_time)

    from apps.web.utils import get_trend_chart_data
    snap_list = temp_camp.get_snap_list(rpt_days = 15)
    category_list, series_cfg_list = get_trend_chart_data(data_type = 2, rpt_list = snap_list)

    return render_to_response(template, {'camp':mnt_camp, 'mnt_max_num':mnt_camp.max_num, 'mnt_type':mnt_camp.mnt_type, 'snap_list': snap_list,
                                         'category_list':category_list, 'series_cfg_list':json.dumps(series_cfg_list)}, context_instance = RequestContext(request))

# @login_required
# def mnt_campaign_old(request, campaign_id, template = 'qnpc_mnt_campaign.html'):
#     from apps.crm.models_psmsg import PsMessage
#     if int(mnt_index) not in MntMnger.get_valid_indexes(user = request.user):
#         return HttpResponseRedirect(MntMnger.get_limited_url())
#     shop_id = int(request.user.shop_id)
#     try:
#         mnt_camp = MntCampaign.objects.get(shop_id = shop_id, mnt_index = int(mnt_index))
#         temp_camp = Campaign.objects.get(shop_id = shop_id, campaign_id = mnt_camp.campaign_id)
#     except DoesNotExist, e:
#         log.error('get mnt campaign failed, shop_id=%s, mnt_index=%s, e=%s' % (shop_id, mnt_index, e))
#         return render_to_error(request, '该托管计划不存在，请返回页面重新操作')
#     temp_camp.rpt_days = 15
#     mnt_camp.budget, mnt_camp.title, mnt_camp.snap_list, mnt_camp.online_status, mnt_camp.comment_count = \
#         temp_camp.budget, temp_camp.title, temp_camp.snap_list, temp_camp.online_status, temp_camp.comment_count

#     mnt_camp.msg_count = PsMessage.objects.filter(shop_id = shop_id, object_id = mnt_camp.campaign_id, message_type = 1).count()

#     if not mnt_camp.optimize_time:
#         mnt_camp.optimize_time = '尚未优化'
#     else:
#         mnt_camp.optimize_time = time_humanize(mnt_camp.optimize_time)

#     from apps.web.utils import get_trend_chart_data
#     category_list, series_cfg_list = get_trend_chart_data(data_type = 2, rpt_list = mnt_camp.snap_list)

#     return render_to_response(template, {'camp':mnt_camp, 'mnt_max_num':mnt_camp.max_num, 'mnt_type':mnt_camp.mnt_type, 'category_list':category_list, 'series_cfg_list':json.dumps(series_cfg_list)}, context_instance = RequestContext(request))


@login_required
def auto_rob_rank(request, template = 'qnpc_auto_rob_rank.html'):
    """自动抢排名"""
    version_limit = True
    if test_permission(AUTO_RANKING_CODE, request.user):
        version_limit = False
    return render_to_response(template, {"version_limit":version_limit}, context_instance = RequestContext(request))


@login_required
def shop_core(request, template = "qnpc_shop_core.html"):
    """店铺核心词"""
    version_limit = True
    if test_permission(ATTENTION_CODE, request.user):
        version_limit = False
    resp_data = {"version_limit": version_limit}

    return render_to_response(template, resp_data, context_instance = RequestContext(request))

@login_required
def error(request, template = 'qnpc_error.html'):
    return render_to_response(template, {}, context_instance = RequestContext(request))
