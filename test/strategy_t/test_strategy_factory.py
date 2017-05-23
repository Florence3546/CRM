# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.strategy import StrategyFactory
from apps.alg.models import StrategyConfig, CommandConfig


class test_strategy_factory(TestCase):
    def setUp(self):
        CommandConfig.refresh_all_configs()
        StrategyConfig.refresh_all_configs()

    def test_get_strategy(self):
        strategy_name_list = ['ReduceCost', 'IncreaseClick', 'IncreaseCTR', 'IncreaseCVR', 'ReducePPC']
        # self.default_strategy = 'Default'
        for strategy_name in strategy_name_list:
            strategy = StrategyFactory().get(name = strategy_name)
            self.assertTrue(strategy, 'get strategy failed.')
            name = strategy.get_name()
            self.assertEqual(name, strategy_name, 'error strategy')



