# coding=utf-8

from apps.alg.adgwrapper import build_datarpt_list, build_datarpt, CampOptDiagnose
from apps.alg.algorithm import auto_optimize2, custom_optimize2, temp_strategy_optimize, auto_optimize_dryrun, auto_optimize_dryrun2, check_price, temp_strategy_optimize_dryrun
from apps.alg.kwclassifier import KeywordClassifier
import datetime


# 全自动任务接口

def optimize_adgroups(shop_id, campaign_id, adgroup_id_list, strategy_name = ''):
    datarpt_list = build_datarpt_list(shop_id = shop_id, campaign_id = campaign_id, adgroup_id_list = adgroup_id_list)
    while len(datarpt_list):
        datarpt = datarpt_list.pop()
        if datarpt:
            if strategy_name:
                custom_optimize2(adg_wrapper = datarpt, strategy_name = strategy_name)
            else:
                auto_optimize2(adg_wrapper = datarpt)
    return

def temp_strategy_optimize_adgroups(shop_id, campaign_id, adgroup_id_list, strategy_name, kw_cmd_list, adg_cmd_list, opter_name):
    '''crm后台发送自定义指令时 生成的全自动任务 调该接口'''
    datarpt_list = build_datarpt_list(shop_id = shop_id, campaign_id = campaign_id, adgroup_id_list = adgroup_id_list)
    while len(datarpt_list):
        datarpt = datarpt_list.pop()
        if datarpt:
            temp_strategy_optimize(adg_wrapper = datarpt, strategy_name = strategy_name, kw_cmd_list = kw_cmd_list, adg_cmd_list = adg_cmd_list, opter_name = opter_name)
    return

def temp_strategy_optimize_adgroups_dryrun(shop_id, campaign_id, adgroup_id, strategy_name, kw_cmd_list, adg_cmd_list = []):
    '''crm 后台发送自定义指令前，预览宝贝将怎样改价'''
    adg_wrapper = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)
    temp_strategy_optimize_dryrun(adg_wrapper = adg_wrapper, strategy_name = strategy_name, kw_cmd_list = kw_cmd_list, adg_cmd_list = adg_cmd_list)
    start_date = str(datetime.date.today() - datetime.timedelta(days = 8))
    end_date = str(datetime.date.today() - datetime.timedelta(days = 1))
    KeywordClassifier(adg_wrapper.adgroup, adg_wrapper.kw_list, start_date, end_date).classify_keyword()
    return adg_wrapper.adgroup, adg_wrapper.kw_list

def check_price_4adgroups(shop_id, campaign_id, adgroup_id_list):
    datarpt_list = build_datarpt_list(shop_id = shop_id, campaign_id = campaign_id, adgroup_id_list = adgroup_id_list)
    while len(datarpt_list):
        datarpt = datarpt_list.pop()
        if datarpt:
            check_price(adg_wrapper = datarpt)
    return

def auto_optimize_campaign(shop_id, campaign_id):
    datarpt_list = build_datarpt_list(shop_id = shop_id, campaign_id = campaign_id)
    camp_diag = CampOptDiagnose(shop_id = shop_id, campaign_id = campaign_id)
    camp_opt_flag = camp_diag.get_optimize_flag()
    if camp_opt_flag == 2:
        while len(datarpt_list):
            datarpt = datarpt_list.pop()
            if datarpt:
                if datarpt.last_opt_rec and datarpt.last_opt_rec.next_optdate > datetime.datetime.now():
                    continue # 还没有到下次优化时间，不优化
                auto_optimize2(adg_wrapper = datarpt)
    else:
        # last_opt_count = camp_diag.opt_adg_count()
        # if last_opt_count > 0.6 * len(datarpt_list):
        #    return
        # 所有计划分成两批隔天优化(临时方案)
        # if campaign_id % 2 != datetime.datetime.now().day % 2:
        #     return
        while len(datarpt_list):
            datarpt = datarpt_list.pop()
            if datarpt:
                if datarpt.last_opt_rec and datarpt.last_opt_rec.next_optdate > datetime.datetime.now():
                    continue # 还没有到下次优化时间，不优化
                auto_optimize2(adg_wrapper = datarpt)
    return

# 页面使用的接口

def optimize_adgroup_dryrun(shop_id, campaign_id, adgroup_id, can_add_kw = False, strategy_name = ''):
    '''输入宝贝和策略，输出宝贝将怎样优化'''
    adg_wrapper = build_datarpt(shop_id, campaign_id, adgroup_id)
    adg_wrapper.can_add_kw = can_add_kw
    auto_optimize_dryrun(adg_wrapper = adg_wrapper, strategy_name = strategy_name)
    return adg_wrapper

def optimize_adgroup_dryrun2(shop_id, campaign_id, adgroup_id, can_add_kw = False, strategy_name = '', summary_rpt = -1):
    '''输入宝贝和策略，输出宝贝将怎样优化'''
    adg_wrapper = build_datarpt(shop_id, campaign_id, adgroup_id)
    adg_wrapper.can_add_kw = can_add_kw
    auto_optimize_dryrun2(adg_wrapper = adg_wrapper, strategy_name = strategy_name, summary_rpt = summary_rpt)
    return adg_wrapper

def smart_optimize_4adgroup(shop_id, campaign_id, adgroup_id, start_date, end_date, can_add_kw = False, strategy_name = ''):
    '''智能优化页面的接口'''
    adg_wrapper = optimize_adgroup_dryrun2(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id, can_add_kw = can_add_kw, strategy_name = strategy_name)
    KeywordClassifier(adg_wrapper.adgroup, adg_wrapper.kw_list, start_date, end_date).classify_keyword()
    return adg_wrapper.adgroup, adg_wrapper.kw_list

def bulk_optimize_4adgroup(shop_id, campaign_id, adgroup_id, start_date, end_date, strategy_name = ''):
    '''批量优化页面的接口'''
    adg_wrapper = optimize_adgroup_dryrun2(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id, can_add_kw = False, strategy_name = strategy_name)
    KeywordClassifier(adg_wrapper.adgroup, adg_wrapper.kw_list, start_date, end_date).create_search_list()
    return adg_wrapper.adgroup, adg_wrapper.kw_list

def bulk_optimize_4adgroup2(shop_id, campaign_id, adgroup_id, start_date, end_date, strategy_name = '', summary_rpt = -1):
    '''批量优化页面的接口'''
    adg_wrapper = optimize_adgroup_dryrun2(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id, can_add_kw = False, strategy_name = strategy_name, summary_rpt = summary_rpt)
    KeywordClassifier(adg_wrapper.adgroup, adg_wrapper.kw_list, start_date, end_date, summary_rpt).create_search_list()
    return adg_wrapper.adgroup, adg_wrapper.kw_list
