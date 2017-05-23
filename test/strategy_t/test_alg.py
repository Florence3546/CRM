# coding=UTF-8

import init_environ

from django.test import TestCase

from apps.alg.interface import auto_optimize_campaign

class test_alg2(TestCase):
    def setUp(self):
        pass

    def test_exec_diagnose2(self):
        shop_id = 63518068 # 71193535 # raw_input('input shop id:')
        campaign_id = 4123069 # 7648334 # raw_input('input_campaign_id:')
        # adgroup_id = 622318033
        print 'execute start...'
        # print shop_id
        # print adgroup_id
        # task_execute(shop_id = shop_id, campaign_id = campaign_id)\
        auto_optimize_campaign(shop_id = shop_id, campaign_id = campaign_id)
        # datarpt_list = smart_optimize(shop_id = shop_id, campaign_id = campaign_id)
        print 'execute finished...'
