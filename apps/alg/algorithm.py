# coding=UTF-8

from datetime import datetime
import copy
from apps.common.utils.utils_datetime import time_is_ndays_interval, get_time_delta
from apps.alg.adgwrapper import AdgRptAnalyze
from apps.alg.diagnose import HighCostDiagnose, ClickDiagnose, CTRDiagnose, CVRDiagnose, PPCDiagnose
from apps.alg.strategy import StrategyFactory, CommandStrategy
from apps.alg.submit import KeywordSubmit
from apps.alg.check import AdgroupCheck
from apps.alg.models import OptimizeRecord

DEFAULT_NO_CLICK_STRATEGY = 'IncreaseClickSepcial'

def save_opt_record(adg_wrapper, diag_result, strategy, opt_type = 1):
    save_args = {'shop_id': adg_wrapper.shop_id,
                 'campaign_id': adg_wrapper.campaign.campaign_id,
                 'adgroup_id': adg_wrapper.adgroup.adgroup_id,
                 'opt_type': opt_type,
                 'analyze_result': adg_wrapper.analyze_result,
                 'cmd_count': adg_wrapper.cmd_count_dict,
                 'modify_kw_count': adg_wrapper.modify_kw_count_dict,
                 'diagnose': diag_result,
                 'strategy': strategy.get_name(),
                 'next_optdate': 2,
                 }
    return OptimizeRecord.create(**save_args)

def save_opt_record2(adg_wrapper, analyze_result, diag_result, strategy, cmd_dict, modify_dict, opt_type = 1):
    save_args = {'shop_id': adg_wrapper.shop_id,
                 'campaign_id': adg_wrapper.campaign.campaign_id,
                 'adgroup_id': adg_wrapper.adgroup.adgroup_id,
                 'opt_type': opt_type,
                 'analyze_result': analyze_result,
                 'cmd_count': cmd_dict,
                 'modify_kw_count': modify_dict,
                 'diagnose': diag_result,
                 'strategy': strategy.get_name(),
                 'next_optdate': 2,
                 }
    return OptimizeRecord.create(**save_args)

class Algorithm():
    def __init__(self):
        self.opt_type = 2

    def optimize(self, adg_wrapper):
        # analyze adgroup report data
        analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
        adg_wrapper.analyze_result.update(analyze_result)
        adg_wrapper.calc_kw_limitprice(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
        # check last optimize result

        # diagnose
        strategy_name, diag_result = self.diagnose(adg_wrapper = adg_wrapper)
        strategy = StrategyFactory().get(name = strategy_name)
        strategy.execute(data = adg_wrapper)

        save_opt_record(adg_wrapper, diag_result, strategy, opt_type = self.opt_type)
        return

    def optimize2(self, adg_wrapper):
        # adg_wrapper.init_report()
        # optimize by mobile report
        adg_wrapper.prepare_data_4optimize_mobile()
        # analyze mobile data
        strategy_mobile = StrategyFactory().get(name = DEFAULT_NO_CLICK_STRATEGY)
        analyze_result_mobile = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
        adg_wrapper.analyze_result.update(analyze_result_mobile)
        adg_wrapper.calc_kw_limitprice_mobile(kw_g_cpc = analyze_result_mobile.get('kw_g_ppc7', 500))
        diag_result_mobile = {}
        if adg_wrapper.kw_list_valid:
            #
            # diagnose
            strategy_name, diag_result_mobile = self.diagnose(adg_wrapper = adg_wrapper)
            strategy_mobile = StrategyFactory().get(name = strategy_name)
        strategy_mobile.dry_run(data = adg_wrapper)
        cmd_dict_mobile = copy.deepcopy(adg_wrapper.cmd_count_dict)
        # optimize by pc report
        adg_wrapper.prepare_data_4optimize_pc()
        # analyze pc data
        strategy_pc = StrategyFactory().get(name = DEFAULT_NO_CLICK_STRATEGY)
        analyze_result_pc = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
        adg_wrapper.analyze_result.update(analyze_result_pc)
        adg_wrapper.calc_kw_limitprice_pc(kw_g_cpc = analyze_result_pc.get('kw_g_ppc7', 500))
        diag_result_pc = {}
        if adg_wrapper.kw_list_valid:
            #
            # diagnose
            strategy_name, diag_result_pc = self.diagnose(adg_wrapper = adg_wrapper)
            strategy_pc = StrategyFactory().get(name = strategy_name)
        strategy_pc.dry_run(data = adg_wrapper)
        cmd_dict_pc = copy.deepcopy(adg_wrapper.cmd_count_dict)
        # summary changes
        adg_wrapper.summarize_report()
        # submit changes
        upd_kw_list, del_kw_list, add_kw_list = KeywordSubmit.alg_dry_run(adg_wrapper = adg_wrapper)
        # 如果是系统或者全自动的话， 防止一次性删除太多的词
        most_del_count = min(int(len(adg_wrapper.kw_list) * 0.2), 25)
        del_kw_list = del_kw_list[: most_del_count]
        KeywordSubmit.execute(
            shop_id = adg_wrapper.adgroup.shop_id,
            campaign_id = adg_wrapper.adgroup.campaign_id,
            adgroup_id = adg_wrapper.adgroup.adgroup_id,
            upd_kw_list = upd_kw_list,
            del_kw_list = del_kw_list,
            add_kw_list = add_kw_list,
            opter = 3,
            opter_name = '全自动优化'
            )
        # TODO 保存优化记录
        save_opt_record2(adg_wrapper = adg_wrapper,
                         analyze_result = analyze_result_mobile,
                         diag_result = diag_result_mobile,
                         strategy = strategy_mobile,
                         cmd_dict = cmd_dict_mobile,
                         modify_dict = adg_wrapper.modify_kw_count_dict,
                         opt_type = 1)
        save_opt_record2(adg_wrapper = adg_wrapper,
                         analyze_result = analyze_result_pc,
                         diag_result = diag_result_pc,
                         strategy = strategy_pc,
                         cmd_dict = cmd_dict_pc,
                         modify_dict = adg_wrapper.modify_kw_count_dict,
                         opt_type = 1)
        return

    def diagnose(self, adg_wrapper):
        return 'Default', {}

class Algorithm1(Algorithm):
    def __init__(self):
        self.opt_type = 1
        self.highcost_diag = HighCostDiagnose()
        self.highcost_strategy = 'ReduceCost'

        self.click_diag = ClickDiagnose()
        self.addkw_strategy = 'Default2'
        self.addinvestment_strategy = 'IncreaseClick'
        self.addinvestment_strategy2 = 'IncreaseClickSepcial'

        self.diag_strategy_dict = {CTRDiagnose():'IncreaseCTR',
                                   CVRDiagnose():'IncreaseCVR',
                                   PPCDiagnose():'ReducePPC',
                                   }
        self.default_strategy = 'Default'

    def diagnose(self, adg_wrapper):
        diag_result_dict = {}
        # 计算宝贝托管天数
        if adg_wrapper.adgroup.mnt_type > 0:
            mnt_days = get_time_delta(adg_wrapper.adgroup.mnt_time, datetime.now(), time_fmt = 'DAYS')
            adg_wrapper.adgroup.mnt_days = mnt_days
        else:
            adg_wrapper.adgroup.mnt_days = mnt_days = 100 # 非托管计划按已经托管多天的case处理

        # 检查计划流量
        diag_result = self.highcost_diag.diagnose(adg_wrapper = adg_wrapper)
        diag_result_dict[self.highcost_diag.name()] = diag_result
        if diag_result > 0 and adg_wrapper.adgroup.mnt_days > 1: # 第一次优化不考虑日限额用满的case
            return self.highcost_strategy, diag_result_dict # decrease investment here

        # 检查报表天数
        rpt_list = adg_wrapper.adg_kwrpt_list(days = 7)
        if len(rpt_list) < 5 and adg_wrapper.last_opt_rec:
            diag_result_dict['rpt_days'] = len(rpt_list)
            return self.addkw_strategy, diag_result_dict # just add kw if rpt days < 5

        # 检查宝贝流量
        diag_result = self.click_diag.diagnose(adg_wrapper = adg_wrapper)
        diag_result_dict[self.click_diag.name()] = diag_result
        if diag_result == 0:
            if adg_wrapper.adgroup.mnt_days < 3:
                return self.addinvestment_strategy2, diag_result_dict # first optimize for adgroup (no click)
            return self.addkw_strategy, diag_result_dict # no click
        elif diag_result == 60:
            return self.addinvestment_strategy, diag_result_dict # add investment for this adgroup
        elif diag_result == 50:
            return self.addinvestment_strategy2, diag_result_dict

        # check others
        score = 95
        opt_strategy = self.default_strategy
        for diagnostic, strategy in self.diag_strategy_dict.items():
            diag_result = diagnostic.diagnose(adg_wrapper = adg_wrapper)
            diag_result_dict[diagnostic.name()] = diag_result
            if diag_result < score and diag_result > 0:
                score = diag_result
                opt_strategy = strategy
        return opt_strategy, diag_result_dict

class Algorithm2(Algorithm1):
    def optimize(self, adg_wrapper):
        self.optimize2(adg_wrapper = adg_wrapper)
        return

class AlgorithmCheckPrice(Algorithm):
    def __init__(self):
        self.checkprice = 'CheckPrice'
        self.checkprice2 = 'CheckPrice2'
        self.checkprice3 = 'CheckPrice3'
        self.opt_type = 2

    def diagnose(self, adg_wrapper):
        diag_result_dict = {}
        click_diag = ClickDiagnose()
        diag_result = click_diag.diagnose(adg_wrapper = adg_wrapper)
        diag_result_dict[click_diag.name()] = diag_result
        if diag_result == 50:
            return self.checkprice2, diag_result_dict
        elif diag_result == 60:
            return self.checkprice3, diag_result_dict
        return self.checkprice, diag_result_dict

    def optimize(self, adg_wrapper):
        self.optimize2(adg_wrapper = adg_wrapper)
        return


def auto_optimize(adg_wrapper):
    adg_wrapper.init_report()
    alg = Algorithm1()
    alg.optimize(adg_wrapper = adg_wrapper)
    adg_wrapper.release()

def auto_optimize2(adg_wrapper):
    ''''''
    adg_wrapper.init_report()
    alg = Algorithm2()
    alg.optimize(adg_wrapper = adg_wrapper)
    adg_wrapper.release()

def check_price(adg_wrapper):
    adg_wrapper.init_report()
    alg = AlgorithmCheckPrice()
    alg.optimize(adg_wrapper = adg_wrapper)
    adg_wrapper.release()

def custom_optimize(adg_wrapper, strategy_name):
    adg_wrapper.init_report()
    analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
    adg_wrapper.analyze_result.update(analyze_result)
    adg_wrapper.calc_kw_limitprice(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
    strategy = StrategyFactory().get(name = strategy_name)
    strategy.execute(data = adg_wrapper)

def custom_optimize2(adg_wrapper, strategy_name):
    adg_wrapper.init_report()
    #
    adg_wrapper.prepare_data_4optimize_mobile()
    analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
    adg_wrapper.analyze_result.update(analyze_result)
    adg_wrapper.calc_kw_limitprice_mobile(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
    strategy_mobile = StrategyFactory().get(name = strategy_name)
    strategy_mobile.dry_run(data = adg_wrapper)

    adg_wrapper.prepare_data_4optimize_pc()
    analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
    adg_wrapper.analyze_result.update(analyze_result)
    adg_wrapper.calc_kw_limitprice_pc(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
    strategy_pc = StrategyFactory().get(name = strategy_name)
    strategy_pc.dry_run(data = adg_wrapper)

    adg_wrapper.summarize_report(rpt = -1)
    # submit changes
    upd_kw_list, del_kw_list, add_kw_list = KeywordSubmit.alg_dry_run(adg_wrapper = adg_wrapper)
    # 如果是系统或者全自动的话， 防止一次性删除太多的词
    most_del_count = min(int(len(adg_wrapper.kw_list) * 0.2), 25)
    del_kw_list = del_kw_list[: most_del_count]
    KeywordSubmit.execute(
        shop_id = adg_wrapper.adgroup.shop_id,
        campaign_id = adg_wrapper.adgroup.campaign_id,
        adgroup_id = adg_wrapper.adgroup.adgroup_id,
        upd_kw_list = upd_kw_list,
        del_kw_list = del_kw_list,
        add_kw_list = add_kw_list,
        opter = 3,
        opter_name = '全自动优化'
        )
    return

def temp_strategy_optimize(adg_wrapper, strategy_name, kw_cmd_list, adg_cmd_list, opter_name):
    adg_wrapper.init_report(force_sync_qscore = time_is_ndays_interval(adg_wrapper.adgroup.qscore_sync_time, 1))
    analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
    adg_wrapper.analyze_result.update(analyze_result)
    adg_wrapper.calc_kw_limitprice(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
    if strategy_name:
        strategy = StrategyFactory().get(name = strategy_name)
    else:
        adg_wrapper.can_add_kw = False
        strategy = CommandStrategy(cmd_cfg_name = 'temp')
        strategy.bind_temp_strategy(kw_cmd_list = kw_cmd_list, adg_cmd_list = adg_cmd_list)
    strategy.opter = 2
    strategy.opter_name = opter_name
    strategy.execute(data = adg_wrapper)

def temp_strategy_optimize_dryrun(adg_wrapper, strategy_name, kw_cmd_list, adg_cmd_list):
    adg_wrapper.init_report(force_sync_qscore = time_is_ndays_interval(adg_wrapper.adgroup.qscore_sync_time, 1))
    analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
    adg_wrapper.analyze_result.update(analyze_result)
    adg_wrapper.calc_kw_limitprice(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
    if strategy_name:
        strategy = StrategyFactory().get(name = strategy_name)
    else:
        adg_wrapper.can_add_kw = False
        strategy = CommandStrategy(cmd_cfg_name = 'temp')
        strategy.bind_temp_strategy(kw_cmd_list = kw_cmd_list, adg_cmd_list = adg_cmd_list)
    strategy.dry_run(data = adg_wrapper)

def auto_optimize_dryrun(adg_wrapper, strategy_name = ''):
    adg_wrapper.init_report(force_sync_qscore = time_is_ndays_interval(adg_wrapper.adgroup.qscore_sync_time, 1))
    analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
    adg_wrapper.analyze_result.update(analyze_result)
    adg_wrapper.calc_kw_limitprice(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
    alg = Algorithm1()
    if not strategy_name:
        strategy_name, _ = alg.diagnose(adg_wrapper = adg_wrapper)
    strategy = StrategyFactory().get(name = strategy_name)
    strategy.dry_run(data = adg_wrapper)
    return

def auto_optimize_dryrun2(adg_wrapper, strategy_name = '', summary_rpt = -1):
    adg_wrapper.init_report(force_sync_qscore = time_is_ndays_interval(adg_wrapper.adgroup.qscore_sync_time, 1))
    #
    adg_wrapper.prepare_data_4optimize_mobile()
    analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
    adg_wrapper.analyze_result.update(analyze_result)
    adg_wrapper.calc_kw_limitprice_mobile(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
    strategy_mobile_name = strategy_name
    if not strategy_name:
        if adg_wrapper.kw_list_valid:
            alg = Algorithm1()
            strategy_mobile_name, _ = alg.diagnose(adg_wrapper = adg_wrapper)
        else:
            strategy_mobile_name = DEFAULT_NO_CLICK_STRATEGY
    strategy_mobile = StrategyFactory().get(name = strategy_mobile_name)
    strategy_mobile.dry_run(data = adg_wrapper)

    adg_wrapper.prepare_data_4optimize_pc()
    analyze_result = AdgRptAnalyze().analyze(adg_wrapper = adg_wrapper)
    adg_wrapper.analyze_result.update(analyze_result)
    adg_wrapper.calc_kw_limitprice_pc(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
    strategy_pc_name = strategy_name
    if not strategy_name:
        if adg_wrapper.kw_list_valid:
            alg = Algorithm1()
            strategy_pc_name, _ = alg.diagnose(adg_wrapper = adg_wrapper)
        else:
            strategy_pc_name = DEFAULT_NO_CLICK_STRATEGY
    strategy_pc = StrategyFactory().get(name = strategy_pc_name)
    strategy_pc.dry_run(data = adg_wrapper)

    adg_wrapper.summarize_report(rpt = summary_rpt)
    return
