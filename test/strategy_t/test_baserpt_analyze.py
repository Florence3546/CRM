# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.adgwrapper import AdgRptAnalyze
from apps.alg.interface import build_datarpt


class test_baserpt_analyze(TestCase):
    def setUp(self):
        # shop_id = 7317
        # campaign_id = 2947211
        # adgroup_id = 490060976
        shop_id = 71193535
        campaign_id = 7648334
        adgroup_id = 615482112
        self.datarpt = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)
        self.datarpt.init_report()

    def test_analyze(self):
        analyze_result = AdgRptAnalyze().analyze(adg_wrapper = self.datarpt)
        self.assertTrue(len(analyze_result))

    def test_analyze_kw7(self):
        analyze_result = AdgRptAnalyze().analyze_kw7(adg_wrapper = self.datarpt)
        self.assertTrue('kw_pv7' in analyze_result, 'error analyze_kw7, missing key kw_pv7')
        self.assertTrue('kw_click7' in analyze_result, 'error analyze_kw7, missing key kw_click7')
        self.assertTrue('kw_conv7' in analyze_result, 'error analyze_kw7, missing key kw_conv7')
        self.assertTrue('kw_cost7' in analyze_result, 'error analyze_kw7, missing key kw_cost7')
        self.assertTrue('kw_ctr7' in analyze_result, 'error analyze_kw7, missing key kw_ctr7')
        self.assertTrue('kw_g_ctr7' in analyze_result, 'error analyze_kw7, missing key kw_g_ctr7')
        self.assertTrue('kw_cvr7' in analyze_result, 'error analyze_kw7, missing key kw_cvr7')
        self.assertTrue('kw_g_cvr7' in analyze_result, 'error analyze_kw7, missing key kw_g_cvr7')
        self.assertTrue('kw_ppc7' in analyze_result, 'error analyze_kw7, missing key kw_ppc7')
        self.assertTrue('kw_g_ppc7' in analyze_result, 'error analyze_kw7, missing key kw_g_ppc7')

    def test_analyze_kw3(self):
        analyze_result = AdgRptAnalyze().analyze_kw3(adg_wrapper = self.datarpt)
        self.assertTrue('kw_pv3' in analyze_result, 'error analyze_kw3, missing key kw_pv3')
        self.assertTrue('kw_click3' in analyze_result, 'error analyze_kw3, missing key kw_click3')
        self.assertTrue('kw_conv3' in analyze_result, 'error analyze_kw3, missing key kw_conv3')
        self.assertTrue('kw_cost3' in analyze_result, 'error analyze_kw3, missing key kw_cost3')
        self.assertTrue('kw_ctr3' in analyze_result, 'error analyze_kw3, missing key kw_ctr3')
        self.assertTrue('kw_g_ctr3' in analyze_result, 'error analyze_kw3, missing key kw_g_ctr3')
        self.assertTrue('kw_cvr3' in analyze_result, 'error analyze_kw3, missing key kw_cvr3')
        self.assertTrue('kw_g_cvr3' in analyze_result, 'error analyze_kw3, missing key kw_g_cvr3')
        self.assertTrue('kw_ppc3' in analyze_result, 'error analyze_kw3, missing key kw_ppc3')
        self.assertTrue('kw_g_ppc3' in analyze_result, 'error analyze_kw3, missing key kw_g_ppc3')

    def test_analyze_tendency(self):
        analyze_result = AdgRptAnalyze().analyze_tendency(adg_wrapper = self.datarpt)
        self.assertTrue('kwpv_list' in analyze_result, 'error analyze_tendency, missing key kwpv_list')
        self.assertTrue('kwpv_ave' in analyze_result, 'error analyze_tendency, missing key kwpv_ave')
        self.assertTrue('kwpv_k' in analyze_result, 'error analyze_tendency, missing key kwpv_k')
        self.assertTrue('kwpv_offset' in analyze_result, 'error analyze_tendency, missing key kwpv_offset')
        self.assertTrue('kwpv_tendency_ref' in analyze_result, 'error analyze_tendency, missing key kwpv_tendency_ref')
        self.assertTrue('kwclick_list' in analyze_result, 'error analyze_tendency, missing key kwclick_list')
        self.assertTrue('kwclick_ave' in analyze_result, 'error analyze_tendency, missing key kwclick_ave')
        self.assertTrue('kwclick_k' in analyze_result, 'error analyze_tendency, missing key kwclick_k')
        self.assertTrue('kwclick_offset' in analyze_result, 'error analyze_tendency, missing key kwclick_offset')
        self.assertTrue('kwclick_tendency_ref' in analyze_result, 'error analyze_tendency, missing key kwclick_tendency_ref')

    def test_analyze_cat_tendency(self):
        analyze_result = AdgRptAnalyze().analyze_cat_tendency(adg_wrapper = self.datarpt)
        self.assertTrue('catpv_k' in analyze_result, 'error analyze_cat_tendency, missing key catpv_k')
        self.assertTrue('catpv_offset' in analyze_result, 'error analyze_cat_tendency, missing key catpv_offset')
        self.assertTrue('catpv_tendency_ref' in analyze_result, 'error analyze_cat_tendency, missing key catpv_tendency_ref')
        self.assertTrue('catclick_k' in analyze_result, 'error analyze_cat_tendency, missing key catclick_k')
        self.assertTrue('catclick_offset' in analyze_result, 'error analyze_cat_tendency, missing key catclick_offset')
        self.assertTrue('catclick_tendency_ref' in analyze_result, 'error analyze_cat_tendency, missing key catclick_tendency_ref')

    def test_analyze_qscore(self):
        analyze_result = AdgRptAnalyze().analyze_qscore(adg_wrapper = self.datarpt)
        self.assertTrue('kw_qscore' in analyze_result, 'error analyze_qscore, missing key kw_qscore')
        self.assertTrue('kw_score_rele' in analyze_result, 'error analyze_qscore, missing key kw_score_rele')
        self.assertTrue('kw_score_cvr' in analyze_result, 'error analyze_qscore, missing key kw_score_cvr')
        self.assertTrue('kw_score_cust' in analyze_result, 'error analyze_qscore, missing key kw_score_cust')
        self.assertTrue('kw_score_creative' in analyze_result, 'error analyze_qscore, missing key kw_score_creative')
        self.assertTrue('topkw_qscore' in analyze_result, 'error analyze_qscore, missing key topkw_qscore')
        self.assertTrue('topkw_score_rele' in analyze_result, 'error analyze_qscore, missing key topkw_score_rele')
        self.assertTrue('topkw_score_cvr' in analyze_result, 'error analyze_qscore, missing key topkw_score_cvr')
        self.assertTrue('topkw_score_cust' in analyze_result, 'error analyze_qscore, missing key topkw_score_cust')
        self.assertTrue('topkw_score_creative' in analyze_result, 'error analyze_qscore, missing key topkw_score_creative')
        self.assertTrue('topkw_ids' in analyze_result, 'error analyze_qscore, missing key topkw_ids')

    def test_analyze_kwppc(self):
        analyze_result = AdgRptAnalyze().analyze_kw_ppc(adg_wrapper = self.datarpt)
        self.assertTrue('kw_ppc' in analyze_result, 'error analyze_kwppc, missing key kw_ppc')
        self.assertTrue('kw_g_ppc' in analyze_result, 'error analyze_kwppc, missing key kw_g_ppc')
        self.assertTrue('kw_ppc_factor' in analyze_result, 'error analyze_kwppc, missing key kw_ppc_factor')
        self.assertTrue('topkw_ppc' in analyze_result, 'error analyze_kwppc, missing key topkw_ppc')
        self.assertTrue('topkw_g_ppc' in analyze_result, 'error analyze_kwppc, missing key topkw_g_ppc')
        self.assertTrue('topkw_ppc_factor' in analyze_result, 'error analyze_kwppc, missing key topkw_ppc_factor')

    def test_analyze_withcampaign(self):
        analyze_result = AdgRptAnalyze().analyze_with_campaign(adg_wrapper = self.datarpt)
        self.assertTrue('rpt7_roi_factor' in analyze_result, 'error analyze_withcampaign, missing key rpt7_roi_factor')
        self.assertTrue('rpt7_click_factor' in analyze_result, 'error analyze_withcampaign, missing key rpt7_click_factor')
        self.assertTrue('rpt3_roi_factor' in analyze_result, 'error analyze_withcampaign, missing key rpt3_roi_factor')
        self.assertTrue('rpt3_click_factor' in analyze_result, 'error analyze_withcampaign, missing key rpt3_click_factor')
        self.assertTrue('rel_bid_factor' in analyze_result, 'error analyze_withcampaign, missing key rel_bid_factor')
