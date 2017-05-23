# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.models import CommandConfig, StrategyConfig


class test_init_config:
    def setUp(self):
        pass

    def test_init(self):
        CommandConfig.refresh_all_configs()
        StrategyConfig.refresh_all_configs()
