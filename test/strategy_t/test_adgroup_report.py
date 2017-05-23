# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.adgwrapper import AdgRptAnalyze
from apps.alg.interface import build_datarpt

from pprint import pprint


class test_baserpt_analyze(TestCase):
    def setUp(self):
        shop_id = 71193535
        campaign_id = 7648334
        adgroup_id = 615482112
        self.datarpt = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)

    def test_analyze(self):
        analyze_result = AdgRptAnalyze().analyze(adg_wrapper = self.datarpt)
        self.assertTrue(len(analyze_result))
        pprint(analyze_result)
        self.datarpt.analyze_result = analyze_result
        pprint(self.datarpt.topkw_elementword(days = 7))

    def test_init_report(self):
        self.datarpt.init_report()
        for i in range(1, 8):
            self.assertTrue(hasattr(self.datarpt.adgroup, 'rpt' + str(i)), 'error')
            self.assertTrue(hasattr(self.datarpt.campaign, 'rpt' + str(i)), 'error')
            for kw in self.datarpt.kw_list:
                self.assertTrue(hasattr(kw, 'rpt' + str(i)), 'error')
