# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.interface import build_datarpt

class test_buildrpt(TestCase):
    def setUp(self):
        pass

    def test_exec_diagnose2(self):
        shop_id = 71193535
        campaign_id = 33162349
        adgroup_id = 620645850
        datarpt = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)
        self.assertTrue(datarpt, 'build data report failed')
        self.assertTrue(hasattr(datarpt, 'campaign'), 'error report, missing attr campaign')
        self.assertTrue(hasattr(datarpt, 'mnt_campaign'), 'error report, missing attr mnt_campaign')
        self.assertTrue(hasattr(datarpt, 'item'), 'error report, missing attr item')
        self.assertTrue(hasattr(datarpt, 'adgroup'), 'error report, missing attr adgroup')
