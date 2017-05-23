# coding=UTF-8

import datetime
import operator

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from mongoengine.errors import DoesNotExist

from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_json import json
from apps.common.utils.utils_decorator import record_time
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import time_humanize, datetime_2string, days_diff_interval
from apps.common.utils.utils_render import render_to_error
from apps.common.biz_utils.utils_misc import analysis_web_opter
from apps.subway.models import Account, Campaign, Adgroup
from apps.mnt.models import MntCampaign, MntMnger, MNT_TYPE_CHOICES

@login_required
def choose_mnt_campaign(request, campaign_id = 0, template = 'choose_mnt_campaign.html'):
    shop_id = int(request.user.shop_id)
    mnt_campaign = MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id)
    if mnt_campaign:
        return HttpResponseRedirect(reverse('mnt_campaign', kwargs = {'campaign_id': campaign_id}))
    mnt_campaign_dict = dict(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'mnt_type'))
    campaign_list = list(Campaign.objects.filter(shop_id = shop_id))
    mnt_desc_dict = dict(MNT_TYPE_CHOICES)
    for campaign in campaign_list:
        campaign.mnt_type = mnt_campaign_dict.get(campaign.campaign_id, 0)
        campaign.mnt_name = mnt_desc_dict.get(campaign.mnt_type, '').replace('托管', '') if campaign.mnt_type else mnt_desc_dict.get(campaign.mnt_type, '')
    campaign_list.sort(key = lambda x:x.mnt_type, reverse = False)
    max_price_recm = MntCampaign.get_gsw_recm_price(shop_id = shop_id)
    camp_dict = dict(Campaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'title'))
    return render_to_response(template, {'campaign_list': campaign_list,
                                          'add_adgroup':1,
                                          'max_price_recm':max_price_recm,
                                          'campaign_id': int(campaign_id),
                                          'camp_dict':camp_dict,
#                                         'isneed_phone':isneed_phone,
                                          'default_campaign':int(request.GET.get('campaign_id', 0)),
                                          'no_more_mnt': 0 if MntMnger.check_create_mnt(shop_id) else 1
                                          }, context_instance = RequestContext(request))

# 自动托管计划页面
@login_required
def mnt_campaign(request, campaign_id, template = 'mnt_campaign.html'):
    shop_id = int(request.user.shop_id)
    campaign_id = int(campaign_id)
    mnt_list = []
    mnt_campaign_dict = dict(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'mnt_type'))
    campaign_list = list(Campaign.objects.filter(shop_id = shop_id))
    mnt_desc_dict = dict(MNT_TYPE_CHOICES)
    campaign = None
    for camp in campaign_list:
        camp.mnt_type = mnt_campaign_dict.get(camp.campaign_id, 0)
        camp.mnt_name = mnt_desc_dict.get(camp.mnt_type, '').replace('托管', '') if camp.mnt_type else '手动'
        mnt_list.append({'campaign_id':camp.id, 'name': camp.title, 'mnt_type_name':camp.mnt_name})
        if camp.id == campaign_id:
            campaign = camp
    if campaign is None:
        return render_to_error(request, "该计划不存在，请返回页面重新操作")

    snap_list = campaign.get_snap_list(rpt_days = 7)
    start_time = None
    mnt_days = 0
    try:
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
        campaign.optimize_time = mnt_camp.optimize_time and time_humanize(mnt_camp.optimize_time) or "0"
        campaign.mnt_type = mnt_camp.mnt_type
        campaign.max_num = mnt_camp.max_num
        campaign.max_price = '%.2f' % (mnt_camp.max_price / 100.0)
        campaign.mobile_max_price = '%.2f' % (mnt_camp.real_mobile_max_price / 100.0)
        campaign.mnt_desc = mnt_camp.get_mnt_type_display()
        campaign.is_active = mnt_camp.is_active
        campaign.quick_optime = mnt_camp.quick_optime
        campaign.mnt_bid_factor = mnt_camp.mnt_bid_factor
        campaign.mnt_rt = mnt_camp.mnt_rt
        start_time = datetime_2string(mnt_camp.start_time, '%Y年%m月%d日')
        mnt_days = days_diff_interval(mnt_camp.start_time.date())
    except DoesNotExist:
        campaign.mnt_type = 0
        campaign.max_num = 0
        campaign.max_price = 0.00
        campaign.mobile_max_price = 0.00
        campaign.mnt_desc = "未托管计划"
        campaign.is_active = False
        campaign.quick_optime = datetime.datetime.now()
        campaign.mnt_bid_factor = 50
        campaign.mnt_rt = 0

    is_smooth = campaign.is_smooth and 1 or 0
    budget = '%.0f' % (campaign.budget / 100.0)

    from apps.web.utils import get_trend_chart_data
    category_list, series_cfg_list = get_trend_chart_data(data_type = 2, rpt_list = snap_list)
    snap_list.reverse()
    camp_dict = dict(Campaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'title'))
    mnt_opter, _ = analysis_web_opter(request)
    return render_to_response(template, {'camp':campaign,
                                         'mnt_list': mnt_list,
                                         'snap_list': snap_list,
                                         'is_smooth':is_smooth,
                                         'budget':budget,
                                         'category_list':category_list,
                                         'series_cfg_list':json.dumps(series_cfg_list),
                                         'camp_dict':camp_dict,
                                         'mnt_opter':mnt_opter,
                                         'add_adgroup':campaign.mnt_type,
                                         'start_time': start_time,
                                         'mnt_days': mnt_days
                                         }, context_instance = RequestContext(request))

# 长尾托管查看宝贝详情
@login_required
def adgroup_data(request, adgroup_id, template = 'mnt_adgroup_data.html'):
    try:
        adgroup = Adgroup.objects.get(shop_id = request.user.shop_id, adgroup_id = adgroup_id)
        adgroup.get_mobile_status() # 获取当前的移动平台状态及折扣
    except DoesNotExist:
        return render_to_error(request, '该宝贝已经被删除，请返回页面重新操作')
    # 如果宝贝是长尾计划则查询关键词限价
    if adgroup.use_camp_limit:
        try:
            camp = MntCampaign.objects.get(shop_id = request.user.shop_id, campaign_id = adgroup.campaign_id)
            adgroup.limit_price = camp.max_price
            adgroup.yd_limit_price = camp.real_mobile_max_price
        except DoesNotExist, e:
            log.error('get mnt camp max_price error %s' % e)
    else:
        adgroup.yd_limit_price = adgroup.real_mobile_limit_price
    # 获取用户自定义列
    custom_column = Account.get_custom_col(shop_id = request.user.shop_id)
    return render_to_response(template, {'adg':adgroup, 'custom_column':custom_column}, context_instance = RequestContext(request))
