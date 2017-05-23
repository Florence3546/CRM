# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.models import CommandConfig
from apps.alg.interface import build_datarpt
from apps.alg.adgwrapper import AdgRptAnalyze
from apps.alg.dryrun import KeywordDryRun


class test_strategy_config(TestCase):

    def setUp(self):
        pass

    def test_config(self):
        shop_id = 71193535
        campaign_id = 33162349
        adgroup_id = 620645850

        data = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)
        data.init_report()
        analyze_result = AdgRptAnalyze().analyze(adg_wrapper = data)
        # data.analyze_result = analyze_result
        data.analyze_result.update(analyze_result)
        data.calc_kw_limitprice(kw_g_cpc = analyze_result.get('kw_g_ppc7', 500))

        cmd_cfgs = CommandConfig.objects.filter()
        for kw in data.kw_list:
            kw.is_delete = False
            kw.new_price = None
            kw.new_match_scope = None
            kw.optm_reason = ''
            kw.cmd = ''

            kw_dryrun = KeywordDryRun(kw)

            item = data.item
            adg = data.adgroup
            camp = data.campaign
            mnt_camp = data.mnt_campaign
            cat = data.category
            kw_dryrun.test_run_cmd(cmd_cfgs, data)
