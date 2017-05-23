# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.strategy import StrategyFactory


class test_strategy(TestCase):
    def setUp(self):
        pass

    def test_impact_factor(self):
        strategy = StrategyFactory().get(name = 'IncreaseClick')
        impact_factor = strategy.get_impact_factor()
        self.assertTrue('click' in impact_factor, 'missing click')
        self.assertTrue('ctr' in impact_factor, 'missing ctr')
        self.assertTrue('conv' in impact_factor, 'missing conv')
        self.assertTrue('ppc' in impact_factor, 'missing ppc')
