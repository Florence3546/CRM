# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.dryrun import validate_price

class test_validate_price(TestCase):
    def setUp(self):
        pass

    def test_validate_price(self):
        for i in range(0, 100):
            old_price = 100
            new_price = 120
            max_price = 110
            result = validate_price(new_price = new_price, old_price = old_price, max_limit_price = max_price)
            price = result[0]
            self.assertTrue(price >= old_price, 'error')
            self.assertTrue(price <= max_price, 'error')
