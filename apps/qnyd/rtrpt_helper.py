# coding=UTF-8

import datetime

from apps.subway.realtime_report import RealtimeReport
from mnt.models import MntCampaign
from subway.models import *

def get_hclick_adgrtrpt_byshopid(shop_id, min_click = 0):
    # 1、获取手动计划
    # 2、获取计划当下实时数据，并进行过滤赛选
    # 3、获取需要实时监控的宝贝列表

    # 暂时先按照计划做隔离
    # 考虑场景，当下一个重点宝贝，我刚刚取消托管，在有点击的情况下，变成了手动，是否可行？
    # 获取有效计划（注：如需要计划数据，可从campaign_rtrpt获取）
    # unmnt_campaigns = MntCampaign.get_unmnt_campaigns(shop_id)
    # camp_id_list = [camp.campaign_id for camp in unmnt_campaigns]
    campaign_rtrpt = RealtimeReport.get_summed_rtrpt(rpt_type = 'campaign', args_list = [shop_id])
    valid_camps = {int(camp_id): obj for camp_id, obj in campaign_rtrpt.items() if obj.click > min_click} # 计划过滤

    # 获取有效推广组
    valid_adgroups = {}
    for camp_id, camp in valid_camps.items():
        adgroup_rtrpt = RealtimeReport.get_summed_rtrpt(rpt_type = 'adgroup', args_list = [shop_id, camp_id])
        temp_adgs = {int(adg_id):obj for adg_id, obj in adgroup_rtrpt.items() if obj.click > min_click}
        valid_adgroups.update(temp_adgs)

#     import settings
#     import common.biz_utils.utils_dictwrapper as ud
#     if not valid_adgroups and settings.DEBUG:
#         # 测试模块 不考虑性能
#         size = 10
#         adgroup_list = Adgroup.objects.filter(shop_id = shop_id, mnt_type = 0)[:size]
#         for index , adg in enumerate(adgroup_list):
#             kw_rt_click = size - index
#             temp = ud.DictWrapper({
#                     'rt_click':kw_rt_click,
#                     'campaign_id':adg.campaign_id,
#                     'adgroup_id':adg.adgroup_id,
#             })
#             valid_adgroups[adg.adgroup_id] = temp
    return valid_adgroups

def get_hclick_kwrtrpt_byadgid(shop_id, camp_id, adg_id, min_limit = 0):
    def kw_filter(obj):
        return obj.impressions > min_limit

    kw_rtrpt = RealtimeReport.get_summed_rtrpt(rpt_type = 'keyword', args_list = [shop_id, camp_id, adg_id])
    kw_infos = {int(kw_id):obj for kw_id, obj in kw_rtrpt.items() if kw_filter(obj)} # 此处返回的是对象

#     import settings
#     import common.biz_utils.utils_dictwrapper as ud
#     if not kw_infos and settings.DEBUG:
#         # 测试模块 不考虑性能
#         size = 20
#         kw_list = Keyword.objects.filter(shop_id = shop_id, campaign_id = camp_id, adgroup_id = adg_id)[:size]
#         for index , kw in enumerate(kw_list):
#             kw_rt_click = size - index
#             temp = ud.DictWrapper({
#                     "kw_id":kw.keyword_id,
#                     'campaign_id':kw.campaign_id,
#                     'adgroup_id':kw.adgroup_id,
#                     "rt_cost":kw_rt_click * 100,
#                     "rt_click":kw_rt_click,
#                     "rt_pay_count":kw_rt_click / 2,
#             })
#             kw_infos[kw.keyword_id] = temp
    return kw_infos

def get_hclick_kwrtrpt_byshopid(shop_id):
    # 1、获取手动计划
    # 2、获取计划当下实时数据，并进行过滤赛选
    # 3、获取需要实时监控的宝贝列表
    min_click = 0

    # 暂时先按照计划做隔离
    # 考虑场景，当下一个重点宝贝，我刚刚取消托管，在有点击的情况下，变成了手动，是否可行？
    # 获取有效计划（注：如需要计划数据，可从campaign_rtrpt获取）
    unmnt_campaigns = MntCampaign.get_unmnt_campaigns(shop_id)
    camp_id_list = [camp.campaign_id for camp in unmnt_campaigns]
    campaign_rtrpt = RealtimeReport.get_summed_rtrpt(rpt_type = 'campaign', args_list = [shop_id])
    valid_camps = {int(camp_id): obj for camp_id, obj in campaign_rtrpt.items() if obj.click > min_click\
                   and int(camp_id) in camp_id_list} # 计划过滤

    # 获取有效推广组
    valid_adgroups = {}
    for camp in valid_camps.values():
        adgroup_rtrpt = RealtimeReport.get_summed_rtrpt(rpt_type = 'adgroup', args_list = [shop_id, camp.campaign_id])
        temp_adgs = {int(adg_id):obj for adg_id, obj in adgroup_rtrpt.items() if obj.click > min_click}
        valid_adgroups.update(temp_adgs)

    valid_keywords = [] # 以下代码可能需要考虑 协程 或 线程
    for adg in valid_adgroups.values():
        kw_rtrpt = RealtimeReport.get_summed_rtrpt(rpt_type = 'keyword', args_list = [shop_id, adg.campaign_id, adg.adgroup_id])
        temp_kws = [obj for kw_id, obj in kw_rtrpt.items() if obj.click > min_click] # 此处返回的是对象
        valid_keywords.extend(temp_kws)

    valid_keywords.sort(key = lambda obj: obj.click, reverse = True)

    for kw in valid_keywords:
        kw.adgroup_rtrpt = valid_adgroups.get(kw.adgroup_id, None)
        kw.compaign_rtrpt = valid_camps.get(kw.campaign_id, None)

#     from common.biz_utils.utils_dictwrapper import DictWrapper
#     from subway.models_keyword import Keyword
#     size = 10
#     kw_list = Keyword.objects.filter(adgroup_id = 637820447)[:size]
#     for index , kw in enumerate(kw_list):
#         kw_rt_click = size - index
#         temp = DictWrapper({
#                 'kw_id':kw.keyword_id,
#                 'campaign_id':kw.campaign_id,
#                 'adgroup_id':kw.adgroup_id,
#                 'rt_click':kw_rt_click,
#                 'rt_pay_count':kw_rt_click / 2,
#                 'rt_cost':kw_rt_click * 5,
#         })
#         valid_keywords.append(temp)
    return valid_keywords
