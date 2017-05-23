# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.models import strat_cfg_coll, StrategyConfig, CommandConfig
from apps.alg.strategy import StrategyFactory
from apps.alg.interface import build_datarpt
from apps.alg.adgwrapper import AdgRptAnalyze


class test_strategy_config(TestCase):

    def setUp(self):
        pass

    def test_config(self):
        shop_id = 71193535
        campaign_id = 33162349
        adgroup_id = 620645850

        CommandConfig.refresh_all_configs()
        StrategyConfig.refresh_all_configs()

        strat_cfgs = strat_cfg_coll.find({}, {'name': 1})
        strat_name_list = [sc['name'] for sc in strat_cfgs]
        strat_name_list.append('undefine')

        data = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)
        data.init_report()
        analyze_result = AdgRptAnalyze().analyze(adg_wrapper = data)
        # data.analyze_result = analyze_result
        data.analyze_result.update(analyze_result)
        data.calc_kw_limitprice(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))
        for strat_name in strat_name_list:
            print '=====================  start %s ====================' % strat_name
            strategy = StrategyFactory().get(name = strat_name)
            strategy.dry_run(data)
            print '=====================  test ok: %s ====================' % strat_name
