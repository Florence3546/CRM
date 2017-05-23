# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.interface import build_datarpt
from apps.alg.diagnose import ClickDiagnose, CTRDiagnose, CVRDiagnose, HighCostDiagnose, PPCDiagnose


class test_diagnose(TestCase):
    def setUp(self):
        shop_id = 71193535
        campaign_id = 33162349
        adgroup_id = 620645850
        self.datarpt = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)
        self.datarpt.init_report()

    def test_diagnose_click(self):
        diag_result = ClickDiagnose().diagnose(adg_wrapper = self.datarpt)
        return None

    def test_diagnose_ctr(self):
        diag_result = CTRDiagnose().diagnose(adg_wrapper = self.datarpt)
        return None

    def test_diagnose_cvr(self):
        diag_result = CVRDiagnose().diagnose(adg_wrapper = self.datarpt)
        return None

    def test_diagnose_cost(self):
        diag_result = HighCostDiagnose().diagnose(adg_wrapper = self.datarpt)
        return None

    def test_diagnose_ppc(self):
        diag_result = PPCDiagnose().diagnose(adg_wrapper = self.datarpt)
        return None
