# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.models import StrategyConfig, CommandConfig
from apps.alg.adgwrapper import build_datarpt
from apps.alg.algorithm import auto_optimize, custom_optimize, auto_optimize_dryrun


class test_custom_optimize(TestCase):
    def setUp(self):
        CommandConfig.refresh_all_configs()
        StrategyConfig.refresh_all_configs()
        shop_id = 63518068
        campaign_id = 4123069
        adgroup_id = 627880001

        self.data = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)

    def test_custom_optimize(self):
        custom_optimize(adg_wrapper = self.data, strategy_name = 'Default')

    def test_auto_optimize(self):
        auto_optimize(adg_wrapper = self.data)

    def test_auto_optimize_dryrun(self):
        auto_optimize_dryrun(adg_wrapper = self.data)
