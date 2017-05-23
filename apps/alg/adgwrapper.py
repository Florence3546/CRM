# coding=UTF-8

import datetime
import math
import random
import copy
from mongoengine.errors import DoesNotExist
from apps.common.biz_utils.utils_dictwrapper import KeywordGlobal
from apps.common.biz_utils.utils_tapitools import get_kw_g_data, get_kw_g_data2
from apps.common.utils.utils_datetime import date_2datetime, time_is_ndays_interval
from apps.common.utils.utils_misc import trans_batch_dict_2document
from apps.common.utils.utils_log import log
from apps.common.models import Config
from apps.subway.models_report import PureReport, ReportDictWrapper
from apps.subway.models_adgroup import Adgroup, adg_coll
from apps.subway.models_item import Item, item_coll
from apps.subway.models_keyword import Keyword, kw_coll
from apps.subway.models_campaign import Campaign
from apps.mnt.models_mnt import MntCampaign
from apps.kwslt.models_cat import CatStatic
from apps.kwslt.analyzer import ChSegement
from apps.alg.models import OptimizeRecord, optrec_coll


class PlaceHolder:
    pass


class CampOptDiagnose():
    def __init__(self, shop_id, campaign_id):
        self.campaign = None
        self.mnt_campaign = None
        self.rpt_list = []
        try:
            self.campaign = Campaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
            self.mnt_campaign = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
            self.rpt_list = Campaign.Report.get_snap_list({'campaign_id':self.campaign.campaign_id, }, rpt_days = 3).get(self.campaign.campaign_id, [])
        except DoesNotExist, e:
            log.warn('could not get campaign/mnt_campaign: shop_id=%s, camp_id=%s, e=%s' % (shop_id, campaign_id, e))

    @property
    def bid_factor(self):
        if not self.mnt_campaign:
            return 1.1
        if self.mnt_campaign.mnt_type == 1 or self.mnt_campaign.mnt_type == 3:
            return 0.8 + 0.4 * self.mnt_campaign.mnt_bid_factor / 100
        elif self.mnt_campaign.mnt_type == 2 or self.mnt_campaign.mnt_type == 4:
            return 1.0 + 0.5 * self.mnt_campaign.mnt_bid_factor / 100
        return 1.1

    def check_cost(self):
        last_rpt = self.rpt_list[-1] if len(self.rpt_list) else None
        if not last_rpt:
            return 80
        if last_rpt.cost * 1.0 >= 0.95 * self.campaign.budget:
            return 100
        cost_boundary = 100 * min(15 + math.pow(self.campaign.budget * 0.01 - 20, 0.65), 50)
        if last_rpt.cost < cost_boundary:
            return 50
        cost_boundary2 = 100 * min(18 + math.pow(self.campaign.budget * 0.01 - 20, 0.80) * math.sqrt(self.bid_factor), 120)
        if last_rpt.cost < cost_boundary2:
            return 60
        return 80

    def get_optimize_flag(self):
        cost_score = self.check_cost()
        if cost_score == 80:
            return 2
        if not self.mnt_campaign:
            return 2
        return 1

    def opt_adg_count(self, date = datetime.datetime.now() - datetime.timedelta(days = 1)):
        return optrec_coll.find({'campaign_id':self.campaign.campaign_id,
                                 'create_time':{'$gte':date.replace(hour = 0, minute = 0, second = 0),
                                                '$lte':date.replace(hour = 23, minute = 59, second = 59),
                                                },
                                 }).count()


class AdgroupWrapper():
    def __init__(self, adgroup):
        self.last_opt_rec = None
        self.adgroup = adgroup
        self.shop = None
        self.shop_id = 0
        self.campaign = None
        self.mnt_campaign = None
        self.item = None
        self.kw_list = None
        self.category = PlaceHolder()
        self.cat_id = None
        self.analyze_result = {}
        self.can_upd_price = True
        self.can_upd_match = True
        self.can_add_kw = True
        self.can_del_kw = True
        self.adgroup.has_selected_word = False
        self.adgroup.add_kw_list = []

    def release(self):
        self.last_opt_rec = None
        self.adgroup = None
        self.shop = None
        self.campaign = None
        self.mnt_campaign = None
        self.item = None
        self.kw_list = None
        self.category = PlaceHolder()
        self.cat_id = None
        self.analyze_result = {}

    def init_report(self, force_sync_qscore = False):
        result = self.adgroup.ensure_kw_rpt()
        if not result:
            raise Exception('下载关键词报表失败')
        self.setup_cat_report(days = 7)
        self.setup_obj_report(obj = self.campaign)
        self.setup_obj_report(obj = self.adgroup)
        self.check_qscore(force_sync_qscore = force_sync_qscore)

        self.calc_adg_limit_price()
        query_dict = {'shop_id':self.shop_id, 'campaign_id':self.campaign.campaign_id, 'adgroup_id':self.adgroup.adgroup_id, }
        kw_list = kw_coll.find(query_dict)
        kw_list = trans_batch_dict_2document(src_dict_list = kw_list, class_object = Keyword) or []
        # self.kw_list = []
        self.init_kw_pc(kw_list)
        self.init_kw_mobile(kw_list)
        self.init_kw_all(kw_list)
        self.prepare_data_4optimize()

    def calc_adg_limit_price(self):
        self.adgroup.real_mobile_discount = self.adgroup.mobile_discount or self.campaign.platform.get('mobile_discount', 100)
        limit_price = 300
        mobile_limit_price = 300
        if self.mnt_campaign:
            if self.adgroup.use_camp_limit: # 重点，无线托管中使用计划限价的
                limit_price = self.mnt_campaign.max_price
                mobile_limit_price = self.mnt_campaign.real_mobile_max_price
            else: # 使用宝贝限价的托管宝贝和托管计划中的所有非托管宝贝
                limit_price = self.adgroup.limit_price
                mobile_limit_price = self.adgroup.real_mobile_limit_price
        else: # 非托管计划中的宝贝
            limit_price = self.adgroup.limit_price if self.adgroup.limit_price else 300
            mobile_limit_price = self.adgroup.real_mobile_limit_price if self.adgroup.real_mobile_limit_price else 300
        self.adgroup.user_limit_price_pc = limit_price if limit_price >= 5 else 300
        self.adgroup.user_limit_price_mobile = mobile_limit_price if mobile_limit_price >= 5 else 300

    def prepare_data_4optimize(self):
        self.kw_list = self.kw_list_all
        self.kw_list_valid = self.kw_list_all_valid
        self.adgroup.kwavg_price = sum([kw.max_price for kw in self.kw_list]) / len(self.kw_list) if len(self.kw_list) else 5
        self.setup_adgkw_report()
        self.init_opt_right()

    def prepare_data_4optimize_pc(self):
        self.kw_list = self.kw_list_pc
        self.kw_list_valid = self.kw_list_pc_valid
        self.adgroup.kwavg_price = sum([kw.max_price for kw in self.kw_list]) / len(self.kw_list) if len(self.kw_list) else 5
        self.setup_adgkw_report()
        self.init_opt_right()

    def prepare_data_4optimize_mobile(self):
        self.kw_list = self.kw_list_mobile
        self.kw_list_valid = self.kw_list_mobile_valid
        self.adgroup.kwavg_price = sum([kw.max_price for kw in self.kw_list]) / len(self.kw_list) if len(self.kw_list) else 5
        self.setup_adgkw_report()
        self.init_opt_right()

    def summarize_report(self, rpt = -1):
        kw_dict_pc = {kw.keyword_id:kw for kw in self.kw_list_pc}
        kw_dict_mobile = {kw.keyword_id:kw for kw in self.kw_list_mobile}
        # kw_dict_all = {kw.keyword_id:kw for kw in self.kw_list_all}
        if rpt == 0:
            self.kw_list = self.kw_list_mobile
        elif rpt == 1:
            self.kw_list = self.kw_list_pc
        elif rpt == -1:
            self.kw_list = self.kw_list_all
        for kw in self.kw_list:
            kw.max_price_pc = kw_dict_pc.get(kw.keyword_id).max_price
            kw.new_price_pc = kw_dict_pc.get(kw.keyword_id).new_price
            kw.is_delete_pc = kw_dict_pc.get(kw.keyword_id).is_delete
            kw.new_match_scope_pc = kw_dict_pc.get(kw.keyword_id).new_match_scope
            kw.max_price_mobile = kw_dict_mobile.get(kw.keyword_id).max_price
            kw.new_price_mobile = kw_dict_mobile.get(kw.keyword_id).new_price
            kw.is_delete_mobile = kw_dict_mobile.get(kw.keyword_id).is_delete
            kw.new_match_scope_mobile = kw_dict_mobile.get(kw.keyword_id).new_match_scope
            kw.is_delete = kw.is_delete_pc and kw.is_delete_mobile
            kw.new_price = 0
            kw.optm_reason = ';'.join([kw_dict_pc.get(kw.keyword_id).optm_reason, kw_dict_mobile.get(kw.keyword_id).optm_reason])
            # log.info('pc price %f, pc new price %f, mobile price %f, mobile new price %f' %
            #      (kw.max_price_pc, kw.new_price_pc, kw.max_price_mobile, kw.new_price_mobile))

    def init_kw_all(self, kw_list):
        self.kw_list_all = copy.deepcopy(kw_list)
        query_dict = {'shop_id':self.shop_id, 'campaign_id':self.campaign.campaign_id, 'adgroup_id':self.adgroup.adgroup_id, }
        kw_rpt_dict = Keyword.Report.get_snap_list(query_dict, rpt_days = 15)
        for kw in self.kw_list_all:
            kw.rpt_list = kw_rpt_dict.get(kw.keyword_id, [])
            self.setup_obj_report(obj = kw)
        self.kw_list_all_valid = True if kw_rpt_dict else False
        # qscore
        mobile_discount = self.adgroup.real_mobile_discount
        for kw in self.kw_list_all:
            qs_obj = kw.qscore_dict
            if qs_obj.get('wireless_qscore', 0) < 0:
                mobile_discount = 0
            kw.qscore = round((qs_obj.get('qscore', 0) * 100 + qs_obj.get('wireless_qscore', 0) * mobile_discount) * 1.0 / (100 + mobile_discount), 2)
            kw.creative_score = round((qs_obj.get('creativescore', 0) * 100 + qs_obj.get('wireless_creativescore', 0) * mobile_discount) * 1.0 / (100 + mobile_discount), 2)
            kw.rele_score = round((qs_obj.get('kwscore', 0) * 100 + qs_obj.get('wireless_relescore', 0) * mobile_discount) * 1.0 / (100 + mobile_discount), 2)
            kw.cvr_score = round((qs_obj.get('cvrscore', 0) * 100 + qs_obj.get('wireless_cvrscore', 0) * mobile_discount) * 1.0 / (100 + mobile_discount), 2)
            kw.cust_score = round((qs_obj.get('custscore', 0) * 100 + qs_obj.get('wireless_custscore', 0) * mobile_discount) * 1.0 / (100 + mobile_discount), 2)
        self.analyze_result.update({'mobile_discount':mobile_discount,
                                    'sync_qscore_flag':True,
                                    'sync_qscore_time':datetime.datetime.now(),
                                    })
        # g_data
        word_list = [kw.word for kw in self.kw_list_all]
        kw_g_data = get_kw_g_data(word_list)
        for kw in self.kw_list_all:
            g_data = kw_g_data.get(str(kw.word), KeywordGlobal())
            kw.g_click = g_data.g_click
            kw.g_pv = g_data.g_pv
            kw.g_cpc = g_data.g_cpc
            kw.g_competition = g_data.g_competition
            kw.g_coverage = g_data.g_coverage
            kw.g_roi = g_data.g_roi
            kw.g_paycount = g_data.g_paycount

    def init_kw_pc(self, kw_list):
        self.kw_list_pc = copy.deepcopy(kw_list)
        # report list
        query_dict = {'shop_id':self.shop_id, 'campaign_id':self.campaign.campaign_id, 'adgroup_id':self.adgroup.adgroup_id, }
        kwrpt_pc_dict = Keyword.Report.get_snap_list(query_dict = query_dict, rpt_days = 15, source = 11, search_type = 0)
        for kw in self.kw_list_pc:
            kw.rpt_list = kwrpt_pc_dict.get(kw.keyword_id, [])
            self.setup_obj_report(obj = kw)
        self.kw_list_pc_valid = True if kwrpt_pc_dict else False
        # qscore
        for kw in self.kw_list_pc:
            qs_obj = kw.qscore_dict
            kw.qscore = qs_obj.get('qscore', 0)
            kw.creative_score = qs_obj.get('creativescore', 0)
            kw.rele_score = qs_obj.get('kwscore', 0)
            kw.cvr_score = qs_obj.get('cvrscore', 0)
            kw.cust_score = qs_obj.get('custscore', 0)
        self.analyze_result.update({'mobile_discount':self.adgroup.mobile_discount,
                                    'sync_qscore_flag':True,
                                    'sync_qscore_time':datetime.datetime.now(),
                                    })
        # g_data
        word_list = [kw.word for kw in self.kw_list_pc]
        kw_g_data = get_kw_g_data2(word_list = word_list, sub_type = 1)
        for kw in self.kw_list_pc:
            g_data = kw_g_data.get(str(kw.word), KeywordGlobal())
            kw.g_click = g_data.g_click
            kw.g_pv = g_data.g_pv
            kw.g_cpc = g_data.g_cpc
            kw.g_competition = g_data.g_competition
            kw.g_coverage = g_data.g_coverage
            kw.g_roi = g_data.g_roi
            kw.g_paycount = g_data.g_paycount

    def init_kw_mobile(self, kw_list):
        self.kw_list_mobile = copy.deepcopy(kw_list)
        # report list
        query_dict = {'shop_id':self.shop_id, 'campaign_id':self.campaign.campaign_id, 'adgroup_id':self.adgroup.adgroup_id, }
        kwrpt_mobile_dict = Keyword.Report.get_snap_list(query_dict = query_dict, rpt_days = 15, source = 12, search_type = 0)
        for kw in self.kw_list_mobile:
            kw.rpt_list = kwrpt_mobile_dict.get(kw.keyword_id, [])
            self.setup_obj_report(obj = kw)
        self.kw_list_mobile_valid = True if kwrpt_mobile_dict else False

        for kw in self.kw_list_mobile:
            kw.max_price = kw.max_mobile_price if (kw.max_mobile_price and not kw.mobile_is_default_price) else int(kw.max_price * self.adgroup.real_mobile_discount / 100.0)

        # qscore
        for kw in self.kw_list_mobile:
            qs_obj = kw.qscore_dict
            kw.qscore = qs_obj.get('wireless_qscore', 0)
            kw.creative_score = qs_obj.get('wireless_creativescore', 0)
            kw.rele_score = qs_obj.get('wireless_relescore', 0)
            kw.cvr_score = qs_obj.get('wireless_cvrscore', 0)
            kw.cust_score = qs_obj.get('wireless_custscore', 0)
        self.analyze_result.update({'mobile_discount':self.adgroup.mobile_discount,
                                    'sync_qscore_flag':True,
                                    'sync_qscore_time':datetime.datetime.now(),
                                    })
        # g_data
        word_list = [kw.word for kw in self.kw_list_mobile]
        kw_g_data = get_kw_g_data2(word_list = word_list, sub_type = 0)
        for kw in self.kw_list_mobile:
            g_data = kw_g_data.get(str(kw.word), KeywordGlobal())
            kw.g_click = g_data.g_click
            kw.g_pv = g_data.g_pv
            kw.g_cpc = g_data.g_cpc
            kw.g_competition = g_data.g_competition
            kw.g_coverage = g_data.g_coverage
            kw.g_roi = g_data.g_roi
            kw.g_paycount = g_data.g_paycount

    def check_qscore(self, force_sync_qscore = False):
        sync_flag = False
        if not self.adgroup.qscore_sync_time:
            sync_flag = random.randint(10000, 50000) < 20000
        if time_is_ndays_interval(self.adgroup.qscore_sync_time, 8):
            sync_flag = True
        if force_sync_qscore or sync_flag:
            return self.adgroup.refresh_qscore()
        else:
            self.analyze_result.update({
                'sync_qscore_flag': False,
                'sync_qscore_time': self.adgroup.qscore_sync_time
            })
            return False

    def init_opt_right(self):
        if self.adgroup.mnt_type > 0 and self.adgroup.mnt_opt_type == 2:
            self.can_upd_match = False
            self.can_add_kw = False
            self.can_del_kw = False

    def cat_rpt_list(self, days = 7):
        return CatStatic.get_rpt_list_8id(cat_id = self.cat_id, rpt_days = days)

    def setup_cat_report(self, days = 7):
        rpt_list = self.cat_rpt_list(days = days)
        data_dict = {str(rpt.rpt_date): rpt for rpt in rpt_list}
        yesterday = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = 1))
        self.category.rpt1 = rpt_list and rpt_list[-1] or CatStatic(cat_id = self.cat_id, rpt_date = yesterday)
        for i in range(2, days + 1):
            if hasattr(self.category, 'rpt' + str(i)):
                continue
            start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = i))
            rpt = data_dict.get(str(start_time), CatStatic(rpt_date = start_time))
            rptj = getattr(self.category, 'rpt' + str(i - 1))
            rpti = CatStatic(cat_id = self.cat_id, rpt_date = start_time)
            rpti.impression = rptj.impression + rpt.impression
            rpti.click = rptj.click + rpt.click
            rpti.cost = rptj.cost + rpt.cost
            rpti.directtransaction = rptj.directtransaction + rpt.directtransaction
            rpti.indirecttransaction = rptj.indirecttransaction + rpt.indirecttransaction
            rpti.directtransactionshipping = rptj.directtransactionshipping + rpt.directtransactionshipping
            rpti.indirecttransactionshipping = rptj.indirecttransactionshipping + rpt.indirecttransactionshipping
            rpti.favitemtotal = rptj.favitemtotal + rpt.favitemtotal
            rpti.favshoptotal = rptj.favshoptotal + rpt.favshoptotal
            rpti.transactionshippingtotal = rptj.transactionshippingtotal + rpt.transactionshippingtotal
            rpti.transactiontotal = rptj.transactiontotal + rpt.transactiontotal
            rpti.favtotal = rptj.favtotal + rpt.favtotal
            rpti.competition = (rptj.competition * (i - 1) + rpt.competition) / i
            rpti.ctr = (rptj.ctr * (i - 1) + rpt.ctr) / i
            rpti.cpc = (rptj.cpc * (i - 1) + rpt.cpc) / i
            rpti.roi = (rptj.roi * (i - 1) + rpt.roi) / i
            rpti.coverage = (rptj.coverage * (i - 1) + rpt.coverage) / i
            setattr(self.category, 'rpt' + str(i), rpti)

    def setup_obj_report(self, obj, days = 7):
        if not obj.rpt_list:
            for i in range(1, days + 1):
                rpt = PureReport(date = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = i)))
                setattr(obj, 'rpt' + str(i), rpt)
            return
        data_dict = {str(rpt.date): rpt for rpt in obj.rpt_list[-days:]}
        yesterday = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = 1))
        obj.rpt1 = obj.rpt_list and obj.rpt_list[-1] or PureReport(date = yesterday)
        for i in range(2, days + 1):
            if hasattr(obj, 'rpt' + str(i)):
                continue
            start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = i))
            rptj = getattr(obj, 'rpt' + str(i - 1))
            rpt = data_dict.get(str(start_time), PureReport(date = start_time))
            rpti = PureReport(date = start_time)
            rpti.impressions = rptj.impressions + rpt.impressions
            rpti.click = rptj.click + rpt.click
            rpti.cost = rptj.cost + rpt.cost
            # rpti.avgpos = rptj.avgpos
            rpti.directpay = rptj.directpay + rpt.directpay
            rpti.indirectpay = rptj.indirectpay + rpt.indirectpay
            rpti.directpaycount = rptj.directpaycount + rpt.directpaycount
            rpti.indirectpaycount = rptj.indirectpaycount + rpt.indirectpaycount
            rpti.favitemcount = rptj.favitemcount + rpt.favitemcount
            rpti.favshopcount = rptj.favshopcount + rpt.favshopcount
            setattr(obj, 'rpt' + str(i), rpti)

    def setup_adgkw_report(self, days = 7):
        for i in range(1, days + 1):
            if hasattr(self.adgroup, 'kwrpt' + str(i)):
                continue
            rpt = PureReport(date = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = i)))
            for kw in self.kw_list:
                kwrpt = getattr(kw, 'rpt' + str(i))
                rpt.impressions += kwrpt.impressions
                rpt.click += kwrpt.click
                rpt.cost += kwrpt.cost
                rpt.avgpos = 0
                rpt.directpay += kwrpt.directpay # 保留细节供页面显示
                rpt.indirectpay += kwrpt.indirectpay
                rpt.directpaycount += kwrpt.directpaycount
                rpt.indirectpaycount += kwrpt.indirectpaycount
                rpt.favitemcount += kwrpt.favitemcount
                rpt.favshopcount += kwrpt.favshopcount
            setattr(self.adgroup, 'kwrpt' + str(i), rpt)

    def _calc_kw_limitprice(self, kw_g_cpc, limit_price):
        for kw in self.kw_list:
            kw.limit_price = self.adgroup.user_limit_price
            kw.proposed_max_price = self.adgroup.user_limit_price
            kw.regular_price = 100
            if self.adgroup.kwrpt7.cpc:
                kw.regular_price = self.adgroup.kwrpt7.cpc * math.sqrt(self.bid_factor)
            elif self.category.rpt7.cpc:
                kw.regular_price = self.category.rpt7.cpc * math.sqrt(self.bid_factor)
            if kw.g_cpc:
                k = self.bid_factor * 2
                max_price = max(kw.g_cpc * k, kw.g_cpc + (k - 1) * kw_g_cpc)
                if self.adgroup.mnt_type in [1, 2, 3, 4]: # 仅对托管宝贝计算推荐限价,非托管宝贝直接使用宝贝限价
                    kw.proposed_max_price = min(max_price, limit_price)
                kw.regular_price = kw.g_cpc * math.sqrt(self.bid_factor)
            kw.regular_price = max(5, min(kw.regular_price, kw.limit_price))
            kw.proposed_min_price = 5

    def calc_kw_limitprice_pc(self, kw_g_cpc):
        self.adgroup.user_limit_price = self.adgroup.user_limit_price_pc
        self._calc_kw_limitprice(kw_g_cpc, self.adgroup.user_limit_price)

    def calc_kw_limitprice_mobile(self, kw_g_cpc):
        self.adgroup.user_limit_price = self.adgroup.user_limit_price_mobile
        self._calc_kw_limitprice(kw_g_cpc, self.adgroup.user_limit_price)

    @property
    def bid_factor(self):
        if not self.mnt_campaign:
            return 1.1
        if self.mnt_campaign.mnt_type == 1 or self.mnt_campaign.mnt_type == 3:
            return 0.8 + 0.4 * self.mnt_campaign.mnt_bid_factor / 100
        elif self.mnt_campaign.mnt_type == 2 or self.mnt_campaign.mnt_type == 4:
            return 1.0 + 0.5 * self.mnt_campaign.mnt_bid_factor / 100
        return 1.1
        # return self.adgroup.mnt_bid_factor * 1.0 / 100.0

    def deal_price(self):
        if not hasattr(self, '_deal_price'):
            adg_rpt = self.adgroup.rpt7
            if adg_rpt.paycount > 0:
                self._deal_price = adg_rpt.pay / adg_rpt.paycount
            else:
                self._deal_price = self.item.price
        return self._deal_price

    def adg_noschrpt_sum(self, days = 7):
        attrname = 'nosch_rpt' + str(days)
        if not hasattr(self.adgroup, attrname):
            start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = days))
            rpt_obj = PureReport(date = start_time)
            for rpt in self.adgroup.nosch_rpt_list:
                if rpt.date >= start_time: # 报表日期在起始时间之后的
                    rpt_obj.impressions += rpt.impressions
                    rpt_obj.click += rpt.click
                    rpt_obj.cost += rpt.cost
                    rpt_obj.avgpos = rpt.avgpos
                    rpt_obj.directpay += rpt.directpay # 保留细节供页面显示
                    rpt_obj.indirectpay += rpt.indirectpay
                    rpt_obj.directpaycount += rpt.directpaycount
                    rpt_obj.indirectpaycount += rpt.indirectpaycount
                    rpt_obj.favitemcount += rpt.favitemcount
                    rpt_obj.favshopcount += rpt.favshopcount
            setattr(self.adgroup, attrname, rpt_obj)
        return getattr(self.adgroup, attrname)

    def adg_kwrpt_list(self, days = 7):
        max_days = 15
        start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = max_days + 1))
        if not hasattr(self.adgroup, 'kwrpt_list'):
            nosch_rpt_dict = {str(rpt.date):rpt for rpt in self.adgroup.nosch_rpt_list if rpt.date > start_time}
            rpt_list = [rpt for rpt in self.adgroup.rpt_list if rpt.date > start_time]
            kwrpt_list = []
            for rpt in rpt_list:
                kw_rpt = PureReport(date = rpt.date)
                nosch_rpt = nosch_rpt_dict.get(str(rpt.date), PureReport(date = rpt.date))
                kw_rpt.impressions = rpt.impressions - nosch_rpt.impressions
                kw_rpt.click = rpt.click - nosch_rpt.click
                kw_rpt.cost = rpt.cost - nosch_rpt.cost
                # kw_rpt.avgpos = rpt.avgpos - nosch_rpt.avgpos
                kw_rpt.directpay = rpt.directpay - nosch_rpt.directpay
                kw_rpt.indirectpay = rpt.indirectpay - nosch_rpt.indirectpay
                kw_rpt.directpaycount = rpt.directpaycount - nosch_rpt.directpaycount
                kw_rpt.indirectpaycount = rpt.indirectpaycount - nosch_rpt.indirectpaycount
                kw_rpt.favitemcount = rpt.favitemcount - nosch_rpt.favitemcount
                kw_rpt.favshopcount = rpt.favshopcount - nosch_rpt.favshopcount
                kwrpt_list.append(kw_rpt)
            setattr(self.adgroup, 'kwrpt_list', kwrpt_list)
        start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = days + 1))
        return [rpt for rpt in self.adgroup.kwrpt_list if rpt.date > start_time]

    def topclick_kwlist(self, days = 7):
        attrname = 'topclick_kwlist_' + str(days)
        if not hasattr(self, attrname):
            self.kw_list.sort(key = lambda kw:getattr(kw, 'rpt' + str(days)).click, reverse = True)
            topclick_list = sorted(self.kw_list, key = lambda kw:getattr(kw, 'rpt' + str(days)).click, reverse = True)[:10]
            topctr_list = sorted(self.kw_list, key = lambda kw:getattr(kw, 'rpt' + str(days)).ctr, reverse = True)[:10]
            eva_dict = {}
            for kw in topclick_list:
                rpt = getattr(kw, 'rpt' + str(days))
                eva_dict[kw.keyword_id] = {'score':rpt.click * rpt.ctr, 'kw':kw}
            for kw in topctr_list:
                rpt = getattr(kw, 'rpt' + str(days))
                eva_dict[kw.keyword_id] = {'score':rpt.click * rpt.ctr, 'kw':kw}
            eva_list = sorted(eva_dict.values(), key = lambda x:x['score'], reverse = True)
            kw_list = [el['kw'] for el in eva_list if el['score'] > 0][:10]
            setattr(self, attrname, kw_list)
        return getattr(self, attrname)

    def topconv_kwlist(self, days = 7):
        attrname = 'topconv_kwlist_' + str(days)
        if not hasattr(self, attrname):
            topconv_list = sorted(self.kw_list, key = lambda kw:getattr(kw, 'rpt' + str(days)).paycount, reverse = True)[:10]
            topcvr_list = sorted(self.kw_list, key = lambda kw:getattr(kw, 'rpt' + str(days)).conv, reverse = True)[:10]
            eva_dict = {}
            for kw in topconv_list:
                rpt = getattr(kw, 'rpt' + str(days))
                eva_dict[kw.keyword_id] = {'score':rpt.paycount * rpt.conv, 'kw':kw}
            for kw in topcvr_list:
                rpt = getattr(kw, 'rpt' + str(days))
                eva_dict[kw.keyword_id] = {'score':rpt.paycount * rpt.conv, 'kw':kw}
            eva_list = sorted(eva_dict.values(), key = lambda x:x['score'], reverse = True)
            kw_list = [el['kw'] for el in eva_list if el['score'] > 0][:10]
            setattr(self, attrname, kw_list)
        return getattr(self, attrname)

    def topclick7_kwlist(self):
        return self.topclick_kwlist(days = 7)

    def topconv7_kwlist(self):
        return self.topconv_kwlist(days = 7)

    def topclick_elementword(self, days = 7):
        attrname = 'topclick_ew' + str(days)
        if not hasattr(self, attrname):
            kw_list = self.topclick_kwlist(days = days)
            click_dict = {}
            for kw in kw_list:
                split_result = ChSegement.split_title_new_to_list(title = kw.word)
                kw.word_split = split_result
                for item in split_result:
                    click_dict.setdefault(item, {'s1':0, 'c1':0, 's2':0, 'c2':0, 'score':0})
            for k, v in click_dict.items():
                for kw in kw_list:
                    rpt = getattr(kw, 'rpt' + str(days))
                    if k in kw.word_split:
                        v['s1'] += rpt.click * rpt.ctr * math.sqrt(len(kw.word_split))
                        v['c1'] += 1
                    else:
                        v['s2'] += rpt.click * rpt.ctr * math.sqrt(len(kw.word_split))
                        v['c2'] += 1
            for k, v in click_dict.items():
                v['score'] = v['s1'] * v['c2'] * (0.9 + 0.1 * v['c1']) / (v['s2'] * v['c1']) if v['s2'] and v['c1'] else 10
            word_score_list = [{'word':k, 'score':v['score']} for k, v in click_dict.items()]
            word_score_list.sort(key = lambda x:x['score'], reverse = True)
            setattr(self, attrname, [item['word'] for item in word_score_list])
        return getattr(self, attrname)

    def topconv_elementword(self, days = 7):
        attrname = 'topconv_ew' + str(days)
        if not hasattr(self, attrname):
            kw_list = self.topconv_kwlist(days = days)
            conv_dict = {}
            for kw in kw_list:
                split_result = ChSegement.split_title_new_to_list(title = kw.word)
                kw.word_split = split_result
                for item in split_result:
                    conv_dict.setdefault(item, {'s1':0, 'c1':0, 's2':0, 'c2':0, 'score':0})
            for k, v in conv_dict.items():
                for kw in kw_list:
                    rpt = getattr(kw, 'rpt' + str(days))
                    if k in kw.word_split:
                        v['s1'] += rpt.paycount * rpt.conv * math.sqrt(len(kw.word_split))
                        v['c1'] += 1
                    else:
                        v['s2'] += rpt.paycount * rpt.conv * math.sqrt(len(kw.word_split))
                        v['c2'] += 1
            for k, v in conv_dict.items():
                v['score'] = v['s1'] * v['c2'] * (0.9 + 0.1 * v['c1']) / (v['s2'] * v['c1']) if v['s2'] and v['c1'] else 10
            word_score_list = [{'word':k, 'score':v['score']} for k, v in conv_dict.items()]
            word_score_list.sort(key = lambda x:x['score'], reverse = True)
            setattr(self, attrname, [item['word'] for item in word_score_list])
        return getattr(self, attrname)

    def topkw_list(self, days = 7):
        topconv_list = self.topconv_kwlist(days = days)
        topclick_list = self.topclick_kwlist(days = days)
        top_dict = {kw.keyword_id:kw for kw in topconv_list[:10]}
        for kw in topclick_list:
            if len(top_dict) >= 10:
                break
            elif kw.keyword_id not in top_dict:
                top_dict[kw.keyword_id] = kw
        return top_dict.values()

    def topkw_elementword(self, days = 7):
        attrname = 'topkw_ew' + str(days)
        if not hasattr(self, attrname):
            kw_list = self.topkw_list(days = days)
            conv_dict = {}
            for kw in kw_list:
                split_result = ChSegement.split_title_new_to_list(title = kw.word)
                kw.word_split = split_result
                for item in split_result:
                    conv_dict.setdefault(item, {'s1':0, 'c1':0, 's2':0, 'c2':0, 'score':0})
            for k, v in conv_dict.items():
                for kw in kw_list:
                    rpt = getattr(kw, 'rpt' + str(days))
                    if k in kw.word_split:
                        v['s1'] += rpt.paycount * rpt.conv * math.sqrt(len(kw.word_split))
                        v['c1'] += 1
                    else:
                        v['s2'] += rpt.paycount * rpt.conv * math.sqrt(len(kw.word_split))
                        v['c2'] += 1
            for k, v in conv_dict.items():
                v['score'] = v['s1'] * v['c2'] * (0.9 + 0.1 * v['c1']) / (v['s2'] * v['c1']) if v['s2'] and v['c1'] else 10
            word_score_list = [{'word':k, 'score':v['score']} for k, v in conv_dict.items()]
            word_score_list.sort(key = lambda x:x['score'], reverse = True)
            setattr(self, attrname, [item['word'] for item in word_score_list])
        return getattr(self, attrname)


def select_optimize_adgroups(mnt_campaign):

    if mnt_campaign.mnt_status == 1 and mnt_campaign.mnt_type:
        query_dict = {'shop_id':mnt_campaign.shop_id,
                      'campaign_id':mnt_campaign.campaign_id,
                      'online_status':'online',
                      'mnt_type':mnt_campaign.mnt_type,
                      }
        adg_cur = adg_coll.find(query_dict)
        adg_list = [adg for adg in adg_cur]
        try:
            max_opt_count = Config.get_value(key = 'mnt.MAX_MNT_OPT_COUNT', default = 50)
        except Exception, e:
            log.error('get_mnt_max_opt_count error, e=%s' % e)
            max_opt_count = 50
        if len(adg_list) > max_opt_count:
            adg_id_list = [adg['_id'] for adg in adg_list]
            query_dict = {'shop_id': mnt_campaign.shop_id, 'campaign_id': mnt_campaign.campaign_id,
                          'adgroup_id': {'$in': adg_id_list}}
            adg_rpt_dict = Adgroup.Report.get_summed_rpt(query_dict, rpt_days = 3)

            has_click_list = []
            no_click_list = []
            for adg in adg_list:
                adg_rpt = adg_rpt_dict.get(adg['_id'], None)
                if adg_rpt and adg_rpt.click > 0:
                    has_click_list.append(adg)
                else:
                    no_click_list.append(adg)
            no_click_count = max(20, max_opt_count - len(has_click_list))
            no_click_list.sort(key = lambda x: 'optm_submit_time' in x and x['optm_submit_time'] or datetime.datetime(2000, 1, 1))
            has_click_list.extend(no_click_list[:no_click_count])
            adg_list = has_click_list
        return adg_list
    return []

def build_datarpt_list(shop_id, campaign_id, adgroup_id_list = []):
    '''该接口主要针对 全自动任务中的 例行任务、快速任务 写的，所以会过滤掉未托管的宝贝'''
    rpt_days = 15
    try:
        campaign = Campaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
        mntcampaign = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
    except DoesNotExist, e:
        log.warn('could not get campaign/mnt_campaign: shop_id=%s, camp_id=%s, e=%s' % (shop_id, campaign_id, e))
        return []

    try:
        if adgroup_id_list:
            data_list = adg_coll.find({'shop_id':shop_id, 'campaign_id':campaign_id, '_id':{'$in':adgroup_id_list},
                                       'mnt_type': mntcampaign.mnt_type})
        else:
            data_list = select_optimize_adgroups(mnt_campaign = mntcampaign)
        adgroup_list = trans_batch_dict_2document(src_dict_list = data_list, class_object = Adgroup) or []
        if not adgroup_list:
            return []

        data_list = item_coll.find({'shop_id':shop_id, '_id':{'$in':[adg.item_id for adg in adgroup_list]}, })
        item_list = trans_batch_dict_2document(src_dict_list = data_list, class_object = Item) or []
        if not item_list:
            return []

        item_dict = {item.item_id:item for item in item_list}

        adgroup_id_list = [adgroup.adgroup_id for adgroup in adgroup_list]
        query_dict = {'shop_id': shop_id, 'campaign_id': campaign_id, 'adgroup_id': {'$in': adgroup_id_list}}
        adg_rpt_dict = Adgroup.Report.get_snap_list(query_dict, rpt_days = rpt_days)
        adg_nosch_rpt_dict = Adgroup.Report.get_snap_list(query_dict, search_type = 3, source = {'$in': [1, 2, 4, 5]})

        campaign.rpt_list = campaign.get_snap_list(rpt_days = rpt_days)
        report_list = []
        for adg in adgroup_list:
            adg.rpt_list = adg_rpt_dict.get(adg.adgroup_id, [])
            adg.nosch_rpt_list = adg_nosch_rpt_dict.get(adg.adgroup_id, [])
            adg_wrapper = AdgroupWrapper(adgroup = adg)
            adg_wrapper.shop_id = shop_id
            adg_wrapper.campaign = campaign
            adg_wrapper.mnt_campaign = mntcampaign
            adg_wrapper.item = item_dict.get(adg.item_id, None)
            adg_wrapper.cat_id = adg_wrapper.item.cat_id

            report_list.append(adg_wrapper)

        rec_dict = OptimizeRecord.get_last_rec_4adgroups(shop_id = shop_id,
                                                         campaign_id = campaign_id,
                                                         adgroup_id_list = [rpt.adgroup.adgroup_id for rpt in report_list])
        for rpt in report_list:
            rpt.last_opt_rec = rec_dict.get(rpt.adgroup.adgroup_id, None)

        return report_list
    except Exception, e:
        log.exception(e)
        raise Exception
    return []

def build_datarpt(shop_id, campaign_id, adgroup_id):
    try:
        campaign = Campaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
        adgroup = Adgroup.objects.get(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)
        item = Item.objects.get(shop_id = shop_id, item_id = adgroup.item_id)

        campaign.rpt_list = campaign.get_snap_list(rpt_days = 15)
        adgroup.rpt_list = adgroup.get_snap_list(rpt_days = 15)
        adgroup.nosch_rpt_list = adgroup.get_snap_list(search_type = 3, source = {'$in': [1, 2, 4, 5]}, rpt_days = 15)

        adg_wrapper = AdgroupWrapper(adgroup = adgroup)
        adg_wrapper.shop_id = shop_id
        adg_wrapper.campaign = campaign
        adg_wrapper.mnt_campaign = None
        adg_wrapper.item = item
        adg_wrapper.cat_id = adg_wrapper.item.cat_id
        adg_wrapper.last_opt_rec = OptimizeRecord.get_last_rec(shop_id = shop_id, campaign_id = campaign_id, adgroup_id = adgroup_id)

        if adgroup.mnt_type > 0:
            adg_wrapper.mnt_campaign = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)

        # adg_wrapper.init_report()
        return adg_wrapper
    except DoesNotExist, e:
        log.warn('could not get camp/mnt_camp/adg/item: shop_id=%s, camp_id=%s, adg_id=%s, e=%s' % (shop_id, campaign_id, adgroup_id, e))
        return None
    except Exception, e:
        log.exception(e)
    return None


class AdgRptAnalyze:
    def __init__(self):
        pass

    def analyze(self, adg_wrapper):
        analyze_result = {}
        analyze_list = ['analyze_kw7',
                        'analyze_tendency',
                        'analyze_camp_tendency',
                        'analyze_cat_tendency',
                        'analyze_qscore',
                        'analyze_kw_ppc',
                        'analyze_with_campaign',
                        ]
        try:
            for item in analyze_list:
                index_data = getattr(self, item)(adg_wrapper)
                analyze_result.update(index_data)
        except Exception, e:
            log.exception(e)
        return analyze_result

    def analyze_kw7(self, adg_wrapper):
        pv7 = 0
        click7 = 0
        conv7 = 0
        cost7 = 0
        g_cost7 = 0
        for kw in adg_wrapper.kw_list:
            pv7 += kw.rpt7.impressions
            click7 += kw.rpt7.click
            conv7 += kw.rpt7.paycount
            cost7 += kw.rpt7.cost
            g_cost7 += kw.rpt7.click * kw.g_cpc
            if kw.g_cpc == None:
                continue
        return {'kw_pv7':pv7,
                'kw_click7':click7,
                'kw_conv7':conv7,
                'kw_cost7':cost7,
                'kw_ctr7':click7 * 100.0 / pv7 if pv7 else 0,
                'kw_g_ctr7':adg_wrapper.category.rpt7.ctr,
                'kw_cvr7':conv7 * 100.0 / click7 if click7 else 0,
                'kw_g_cvr7':adg_wrapper.category.rpt7.coverage,
                'kw_ppc7':cost7 * 1.0 / click7 if click7 else 0,
                'kw_g_ppc7':g_cost7 * 1.0 / click7 if click7 else 0,
                }

    def analyze_kw3(self, adg_wrapper):
        pv3 = 0
        click3 = 0
        conv3 = 0
        cost3 = 0
        g_cost3 = 0
        for kw in adg_wrapper.kw_list:
            pv3 += kw.rpt3.impressions
            click3 += kw.rpt3.click
            conv3 += kw.rpt3.paycount
            cost3 += kw.rpt3.cost
            g_cost3 += kw.rpt3.click * kw.g_cpc
        return {'kw_pv3':pv3,
                'kw_click3':click3,
                'kw_conv3':conv3,
                'kw_cost3':cost3,
                'kw_ctr3':click3 * 100.0 / pv3 if pv3 else 0,
                'kw_g_ctr3':adg_wrapper.category.rpt3.ctr,
                'kw_cvr3':conv3 * 100.0 / click3 if click3 else 0,
                'kw_g_cvr3':adg_wrapper.category.rpt3.coverage,
                'kw_ppc3':cost3 * 1.0 / click3 if click3 else 0,
                'kw_g_ppc3':g_cost3 * 1.0 / click3 if click3 else 0,
                }

    @staticmethod
    def linear_regression(y_list, x_list = []):
        n = len(y_list)
        index_list = x_list if x_list else range(1, n + 1)
        ave_x = float(sum(index_list)) / n
        ave_y = float(sum(y_list)) / n
        list1 = [(index_list[x - 1] - ave_x) * (y_list[x - 1] - ave_y) for x in range(1, n + 1)]
        list2 = [(index_list[x - 1] - ave_x) * (index_list[x - 1] - ave_x) for x in range(1, n + 1)]
        k = sum(list1) / sum(list2)
        return (k, ave_y - k * ave_x)

    def analyze_tendency(self, adg_wrapper):
        rpt_list = adg_wrapper.adg_kwrpt_list(days = 7)
        if len(rpt_list) < 5:
            return {}
        kwpv_list = [rpt.impressions for rpt in rpt_list]
        kwclick_list = [rpt.click for rpt in rpt_list]
        kwpv_ave = sum(kwpv_list) / len(kwpv_list)
        kwclick_ave = sum(kwclick_list) / len(kwclick_list)
        k_pv, offset_pv = AdgRptAnalyze.linear_regression(y_list = kwpv_list, x_list = [])
        k_click, offset_click = AdgRptAnalyze.linear_regression(y_list = kwclick_list, x_list = [])
        return {'kwpv_list':kwpv_list,
                'kwpv_ave':kwpv_ave,
                'kwpv_k':k_pv,
                'kwpv_offset':offset_pv,
                'kwpv_tendency_ref':k_pv * 100.0 / kwpv_ave if kwpv_ave else 0,
                'kwclick_list':kwclick_list,
                'kwclick_ave':kwclick_ave,
                'kwclick_k':k_click,
                'kwclick_offset':offset_click,
                'kwclick_tendency_ref':k_click * 100.0 / kwclick_ave if kwclick_ave else 0,
                }

    def analyze_camp_tendency(self, adg_wrapper):
        start_time = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = 7))
        rpt_list = [rpt for rpt in adg_wrapper.campaign.rpt_list if rpt.date > start_time]
        if len(rpt_list) < 5:
            return {}
        kwpv_list = [rpt.impressions for rpt in rpt_list]
        kwclick_list = [rpt.click for rpt in rpt_list]
        kwpv_ave = sum(kwpv_list) / len(kwpv_list)
        kwclick_ave = sum(kwclick_list) / len(kwclick_list)
        k_pv, offset_pv = AdgRptAnalyze.linear_regression(y_list = kwpv_list, x_list = [])
        k_click, offset_click = AdgRptAnalyze.linear_regression(y_list = kwclick_list, x_list = [])
        return {'campv_list':kwpv_list,
                'campv_ave':kwpv_ave,
                'campv_k':k_pv,
                'campv_offset':offset_pv,
                'campv_tendency_ref':k_pv * 100.0 / kwpv_ave if kwpv_ave else 0,
                'campclick_list':kwclick_list,
                'campclick_ave':kwclick_ave,
                'campclick_k':k_click,
                'campclick_offset':offset_click,
                'campclick_tendency_ref':k_click * 100.0 / kwclick_ave if kwclick_ave else 0,
                }

    def analyze_cat_tendency(self, adg_wrapper):
        rpt_list = adg_wrapper.cat_rpt_list(days = 7)
        if len(rpt_list) < 5:
            return {}
        catpv_list = [rpt.impression for rpt in rpt_list]
        catclick_list = [rpt.click for rpt in rpt_list]
        catpv_ave = sum(catpv_list) / len(catpv_list)
        catclick_ave = sum(catclick_list) / len(catclick_list)
        k_pv, offset_pv = AdgRptAnalyze.linear_regression(y_list = catpv_list, x_list = [])
        k_click, offset_click = AdgRptAnalyze.linear_regression(y_list = catclick_list, x_list = [])
        return {'catpv_k':k_pv,
                'catpv_offset':offset_pv,
                'catpv_tendency_ref':k_pv * 100.0 / catpv_ave if catpv_ave else 0,
                'catclick_k':k_click,
                'catclick_offset':offset_click,
                'catclick_tendency_ref':k_click * 100.0 / catclick_ave if catclick_ave else 0,
                }

    def analyze_qscore(self, adg_wrapper):
        kw_list = adg_wrapper.kw_list
        topkw_list = adg_wrapper.topkw_list(days = 7)
        return {'kw_qscore':sum([kw.qscore for kw in kw_list]) * 1.0 / len(kw_list) if len(kw_list) else 0,
                'kw_score_rele':sum([kw.rele_score for kw in kw_list]) * 1.0 / len(kw_list) if len(kw_list) else 0,
                'kw_score_cvr':sum([kw.cvr_score for kw in kw_list]) * 1.0 / len(kw_list) if len(kw_list) else 0,
                'kw_score_cust':sum([kw.cust_score for kw in kw_list]) * 1.0 / len(kw_list) if len(kw_list) else 0,
                'kw_score_creative':sum([kw.creative_score for kw in kw_list]) * 1.0 / len(kw_list) if len(kw_list) else 0,
                'topkw_qscore':sum([kw.qscore for kw in topkw_list]) * 1.0 / len(topkw_list) if len(topkw_list) else 0,
                'topkw_score_rele':sum([kw.rele_score for kw in topkw_list]) * 1.0 / len(topkw_list) if len(topkw_list) else 0,
                'topkw_score_cvr':sum([kw.cvr_score for kw in topkw_list]) * 1.0 / len(topkw_list) if len(topkw_list) else 0,
                'topkw_score_cust':sum([kw.cust_score for kw in topkw_list]) * 1.0 / len(topkw_list) if len(topkw_list) else 0,
                'topkw_score_creative':sum([kw.creative_score for kw in topkw_list]) * 1.0 / len(topkw_list) if len(topkw_list) else 0,
                'topkw_ids':','.join([str(kw.keyword_id) for kw in topkw_list]),
                }

    def analyze_kw_ppc(self, adg_wrapper):
        kw_g_cost = 0
        kw_click = 0
        kw_cost = 0
        topkw_g_cost = 0
        topkw_click = 0
        topkw_cost = 0
        for kw in adg_wrapper.kw_list:
            if kw.g_cpc:
                kw_g_cost += kw.rpt7.click * kw.g_cpc
                kw_click += kw.rpt7.click
                kw_cost += kw.rpt7.cost
        for kw in adg_wrapper.topkw_list(days = 7):
            if kw.g_cpc:
                topkw_g_cost += kw.rpt7.click * kw.g_cpc
                topkw_click += kw.rpt7.click
                topkw_cost += kw.rpt7.cost
        return {'kw_ppc':kw_cost / kw_click if kw_click else 0,
                'kw_g_ppc':kw_g_cost * 1.0 / kw_click if kw_click else 0,
                'kw_ppc_factor':kw_cost / kw_g_cost if kw_g_cost else 1,
                'topkw_ppc':topkw_cost * 1.0 / topkw_click if topkw_click else 0,
                'topkw_g_ppc':topkw_g_cost / topkw_click if topkw_click else 0,
                'topkw_ppc_factor':topkw_cost / topkw_g_cost if topkw_g_cost else 1,
                }

    def analyze_with_campaign(self, adg_wrapper):
        adg_rpt7 = adg_wrapper.adgroup.kwrpt7
        camp_rpt7 = adg_wrapper.campaign.rpt7
        adg_rpt3 = adg_wrapper.adgroup.kwrpt3
        camp_rpt3 = adg_wrapper.campaign.rpt3
        return {'rpt7_roi_factor':adg_rpt7.roi * 1.0 / camp_rpt7.roi if camp_rpt7.roi else 1.0,
                'rpt7_click_factor':adg_rpt7.click * 1.0 / camp_rpt7.click if camp_rpt7.click else 1.0,
                'rpt3_roi_factor':adg_rpt3.roi * 1.0 / camp_rpt3.roi if camp_rpt3.roi else 1.0,
                'rpt3_click_factor':adg_rpt3.click * 1.0 / camp_rpt3.click if camp_rpt3.click else 1.0,
                'rel_bid_factor':min(0.5, 1 + (camp_rpt7.roi - adg_rpt7.roi) / camp_rpt7.roi) if camp_rpt7.roi else 1.0,
                }

