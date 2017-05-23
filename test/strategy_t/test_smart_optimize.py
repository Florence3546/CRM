# coding=UTF-8

import init_environ

from django.test import TestCase
from pprint import pprint
from apps.alg.interface import auto_optimize_campaign, optimize_adgroups, smart_optimize_4adgroup
from apps.alg.interface import build_datarpt_list



# class test_alg(TestCase):
#     def setUp(self):
#         pass
#
#     def test_auto_optimize(self):
#         shop_id = 107099405
#         campaign_id = 15211557
#         auto_optimize_campaign(shop_id = shop_id, campaign_id = campaign_id)

class test_optimize_adgroup(TestCase):
    def setUp(self):
        pass

    def test_optimize_adgroup(self):
        shop_id = 124528341
        campaign_id = 33438301
        adgroup_id_list = [692420803, ]
        optimize_adgroups(shop_id = shop_id, campaign_id = campaign_id, adgroup_id_list = adgroup_id_list)


#
# class test_alg2(TestCase):
#     def setUp(self):
#         pass
#
#     def test_exec_diagnose2(self):
#         while True:
#             # shop_id = 63518068 # 71193535 # raw_input('input shop id:')
#             # campaign_id = 4123069 # 7648334 # raw_input('input_campaign_id:')
#             shop_id = raw_input('input shop id:')
#             campaign_id = raw_input('input campaign id:')
#             adgroup_id = raw_input('input adgroup id:')
#             print 'execute start...'
#             # print shop_id
#             # print adgroup_id
#             # auto_optimize_campaign(shop_id = shop_id, campaign_id = campaign_id)\
#             adg_wrapper = build_datarpt(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)
#             if adg_wrapper:
#                 alg = Alg1()
#                 alg.optimize(adg_wrapper = adg_wrapper)
#                 pprint(adg_wrapper.analyze_report)
#             # datarpt_list = smart_optimize(shop_id = shop_id, campaign_id = campaign_id)
#             print 'execute finished...'


