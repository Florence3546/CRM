# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.interface import build_datarpt_list

class test_buildrpt(TestCase):
    def setUp(self):
        pass

    def test_exec_diagnose2(self):
        shop_id = 7317
        campaign_id = 2947211
        datarpt_list = build_datarpt_list(shop_id = shop_id, campaign_id = campaign_id)
        self.assertTrue(datarpt_list, 'build data report list failed')
        self.assertTrue(len(datarpt_list), 'build data report list failed')
