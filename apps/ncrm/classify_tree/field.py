# coding=UTF-8

'''
Created on 2015-12-16

@author: YRK
'''
import copy
import datetime
import collections
import pymongo

from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apps.ncrm.models import Subscribe, Login, Monitor, event_coll
from apps.mnt.models_mnt import MntCampaign
from apps.mnt.models_task import UserOptimizeRecord
from apps.subway.models_account import Account
from apps.subway.models_campaign import camp_coll

ENUMERATE_ORDER_CATEGORYS = (('ztc', 'AE托管'), ('vip', 'VIP专家'), ('rjjh', '类目专家'), ('kcjl', '开车精灵'), ('qn', '千牛'))

class LoadManager(object):

    @classmethod
    def Load_subscribe(cls, customer_mapping):
#         def load_order_category(serving_orders, order_category_filter):
#             order_category = ""
#             if serving_orders:
#                 category_list = list(set([order.category for order in serving_orders]))
#                 temp_index = 99999
#                 for category in category_list:
#                     try:
#                         index = order_category_filter.index(category)
#                         if temp_index >= index:
#                             order_category = category
#                             temp_index = index
#                     except:
#                         pass
#             return order_category

        shop_id_list = customer_mapping.keys()

        for subscribe in Subscribe.objects.values("shop_id", "create_time", "start_date", 'end_date', 'category', 'pay')\
                .filter(shop_id__in = shop_id_list).order_by('create_time'):
            subscribe = DictWrapper(subscribe)
            customer = customer_mapping.get(subscribe.shop_id, None)
            if customer:
                if not hasattr(customer, '_subscribe_list'):
                    customer._subscribe_list = []
                customer._subscribe_list.append(subscribe)

        today = datetime.date.today()
        order_category_filter = [info[0] for info in ENUMERATE_ORDER_CATEGORYS]
        for customer in customer_mapping.values():
            if not hasattr(customer, '_subscribe_list'):
                customer._subscribe_list = []
                customer.first_order = None
                customer.last_order = None
                customer.serving_orders = []
                customer.server_cycle_days = 0
                customer.total_order_cycle_months = 0
                customer.serving_days = -1
                customer.latest_paid_days = None
                customer.surplus_days = -1
                customer.is_serving = False
                customer.order_pay = 0
                customer.order_serving_pay = 0
                customer.order_category = ""
            else:
                # 默认挂在基础数据
                customer.first_order = min(customer._subscribe_list, key = lambda order:order.start_date)
                customer.last_order = max(customer._subscribe_list, key = lambda order:order.end_date)
                customer.serving_orders = filter(lambda order: order.start_date <= today < order.end_date
                                                 and order.category in order_category_filter, customer._subscribe_list)
                target_orders = [order for order in customer._subscribe_list if order.category in order_category_filter]
                customer.server_cycle_days = (customer.latest_end - customer.first_order.start_date).days
                customer.total_order_cycle_months = (customer.latest_end - customer.first_order.start_date).days / 30
                customer.surplus_days = (customer.latest_end - today).days
                customer.is_serving = True if customer.surplus_days > 0 else False
                # customer.serving_days = (today - customer.first_order.start_date).days if customer.is_serving else customer.server_cycle_days
                temp_start_date = customer._subscribe_list[0].start_date
                for i, sub in enumerate(customer._subscribe_list):
                    if i + 1 < len(customer._subscribe_list) and sub.end_date < customer._subscribe_list[i + 1].start_date:
                        temp_start_date = customer._subscribe_list[i + 1].start_date
                customer.serving_days = (today - temp_start_date).days if customer.is_serving else (customer.latest_end - temp_start_date).days
                customer.latest_paid_days = (today - max(target_orders, key = lambda order:order.create_time).create_time.date()).days if target_orders else None
                customer.order_pay = sum([order.pay for order in customer._subscribe_list]) / 100.0
                customer.order_serving_pay = sum([order.pay for order in customer.serving_orders ]) / 100.0
                customer.order_category = customer.current_highest_version
                month_serving_pay_list = []
                for sub in customer.serving_orders:
                    months = round((sub.end_date - sub.start_date).days / 30.0, 0) or 1
                    month_serving_pay_list.append(sub.pay / months)
                customer.month_serving_pay = max(month_serving_pay_list) / 100.0 if month_serving_pay_list else 0

        return customer_mapping

    @classmethod
    def Load_Login(cls, customer_mapping):
        # 此处有点数据量较大，可以考虑 登陆时间按天来记录
        shop_id_list = customer_mapping.keys()

        for event in Login.objects.values('shop_id', 'create_time').filter(shop_id__in = shop_id_list)\
                .order_by('-create_time'):
            event = DictWrapper(event)
            customer = customer_mapping.get(event.shop_id, None)
            if customer:
                if not hasattr(customer, '_login_events'):
                    customer._login_events = []
                customer._login_events.append(event)

        today = datetime.datetime.now()
        for customer in customer_mapping.values():
            if not hasattr(customer, '_login_events'):
                customer._login_events = []
                customer.last_login = None
                customer.last_login_days = -1
                customer.login_counter = 0
            else:
                # 默认挂在基础数据
                customer.last_login = customer._login_events[0]
                customer.last_login_days = (today - customer.last_login.create_time).days
                customer.login_counter = len(set([event.create_time.date() for event in customer._login_events])) # 每天无论登陆多少次都算作一次
        return customer_mapping

    @classmethod
    def Load_contact_Event(cls, customer_mapping):
        shop_id_list = customer_mapping.keys()
        valid_contact_dict, invalid_contact_dict = {}, {}
        for contact in event_coll.find({'type':'contact', 'shop_id':{"$in":shop_id_list}}, {'shop_id':1, 'create_time':1, 'visible':1}).sort("create_time",pymongo.DESCENDING):
            contact = DictWrapper(contact)
            if contact.visible == 1:
                valid_contact_dict.setdefault(contact.shop_id, []).append(contact)
            else:
                invalid_contact_dict.setdefault(contact.shop_id, []).append(contact)

        today = datetime.datetime.now()
        for shop_id, customer in customer_mapping.iteritems():
            customer.valid_contact_events = valid_contact_dict.get(shop_id, [])
            customer.invalid_contact_counter = len(invalid_contact_dict.get(shop_id, []))
            
            if customer.valid_contact_events:
                customer.last_contact = customer.valid_contact_events[0]
                customer.last_contact_days = (today - customer.last_contact.create_time).days
                customer.contact_counter = len(set([event.create_time.date() for event in customer.valid_contact_events])) # 每天无论登陆多少次都算作一次
            else:
                customer.last_contact = None
                customer.last_contact_days = -1
                customer.contact_counter = 0
        return customer_mapping

    @classmethod
    def Load_operate_Event(cls, customer_mapping):
        shop_id_list = customer_mapping.keys()
        operate_dict = {}
        for operate in event_coll.find({'type':'operate', 'shop_id':{"$in":shop_id_list}}, {'shop_id':1, 'create_time':1}).sort("create_time",pymongo.DESCENDING):
            operate = DictWrapper(operate)
            operate_dict.setdefault(operate.shop_id, []).append(operate)

        today = datetime.datetime.now()
        for shop_id, customer in customer_mapping.iteritems():
            customer.operate_events = operate_dict.get(shop_id, [])
            if customer.operate_events:
                customer.last_operate_days = (today - customer.operate_events[0].create_time).days
            else:
                customer.last_operate_days = None
        return customer_mapping

    @classmethod
    def Load_monitor_Event(cls, customer_mapping):
        shop_id_list = customer_mapping.keys()

        for event in Monitor.objects.values('shop_id', 'create_time').filter(shop_id__in = shop_id_list)\
                .order_by('-create_time'):
            event = DictWrapper(event)
            customer = customer_mapping.get(event.shop_id, None)
            if customer:
                if not hasattr(customer, '_monitor_events'):
                    customer._monitor_events = []
                customer._monitor_events.append(event)

        today = datetime.datetime.now()
        for customer in customer_mapping.values():
            if not hasattr(customer, '_monitor_events'):
                customer._monitor_events = []
                customer.last_monitor = None
                customer.last_monitor_days = -1
                customer.monitor_counter = 0
            else:
                # 默认挂在基础数据
                customer.last_monitor = customer._monitor_events[0]
                customer.last_monitor_days = (today - customer.last_monitor.create_time).days
                customer.monitor_counter = len(set([event.create_time.date() for event in customer._monitor_events])) # 每天无论登陆多少次都算作一次

        return customer_mapping

    @classmethod
    def Load_account_report(cls, customer_mapping, rpt_days = 7):
        query_dict = {"shop_id":{"$in":customer_mapping.keys()}}
        account_sumrpt_dict = Account.Report.get_summed_rpt(query_dict = query_dict, rpt_days = rpt_days)
        for shop_id, customer in customer_mapping.iteritems():
            sum_rpt = account_sumrpt_dict.get(shop_id, Account.Report())
            customer.sum_account_7impr = sum_rpt.impressions
            customer.sum_account_7click = sum_rpt.click
            customer.sum_account_7cost = sum_rpt.cost / 100 # 暂不考虑小数
            customer.sum_account_7pay = sum_rpt.pay / 100
            customer.sum_account_7paycount = sum_rpt.paycount
            customer.sum_account_7ctr = round(sum_rpt.ctr, 2)
            customer.sum_account_7cpc = round(sum_rpt.cpc, 2)
            customer.sum_account_7roi = round(sum_rpt.roi, 2)
            customer.sum_account_7conv = round(sum_rpt.conv, 2)
        return customer_mapping

    @classmethod
    def Load_mntcampaign(cls, customer_mapping):
        mnt_camps = MntCampaign.objects.filter(shop_id__in = customer_mapping.keys())
        mnt_camp_dict = {}
        for mnt_camp in mnt_camps:
            mnt_camp_dict.setdefault(mnt_camp.shop_id, []).append(mnt_camp)
        for shop_id, customer in customer_mapping.iteritems():
            mnt_camp_list = mnt_camp_dict.get(shop_id, [])
            customer.is_mnt = True if mnt_camp_list else False
            # customer.mnt_camp_list = mnt_camp_list # 为以下留接口
        return customer_mapping

    @classmethod
    def Load_bulk_optimize(cls, customer_mapping):
        today = datetime.datetime.today()
        opt_records = UserOptimizeRecord.objects.filter(shop_id__in = customer_mapping.keys()).order_by('-create_time')
        opt_record_dict = {}
        for opt_record in opt_records:
            opt_record_dict.setdefault(opt_record.shop_id, []).append(opt_record)
        for shop_id, customer in customer_mapping.iteritems():
            opt_record_list = opt_record_dict.get(shop_id, [])
            if opt_record_list:
                customer.last_rggy_days = (today - opt_record_list[0].create_time).days
            else:
                customer.last_rggy_days = 365
        return customer_mapping

    # @classmethod
    # def Load_campaign_budget_list(cls, customer_mapping):
    #     campaign_list = camp_coll.find({'shop_id':{'$in':customer_mapping.keys()}}, {'shop_id':True, 'budget':True})
    #     campaign_budget_dict = {}
    #     for doc in campaign_list:
    #         campaign_budget_dict.setdefault(doc['shop_id'], []).append(doc['budget'] / 100)
    #     for shop_id, customer in customer_mapping.iteritems():
    #         customer.campaign_budget_list = campaign_budget_dict.get(shop_id, [])
    #     return customer_mapping

    @classmethod
    def Load_budget(cls, customer_mapping):
        campaign_list = camp_coll.find({'shop_id':{'$in':customer_mapping.keys()}, 'online_status':'online'}, {'shop_id':True, 'budget':True})
        budget_dict = {}
        for doc in campaign_list:
            if doc['shop_id'] in budget_dict:
                budget_dict[doc['shop_id']] += doc['budget']
            else:
                budget_dict[doc['shop_id']] = doc['budget']
        for shop_id, customer in customer_mapping.iteritems():
            customer.budget = budget_dict.get(shop_id, 0) / 100
        return customer_mapping

class DealManager(object):
    """
    三种情况会用到该类
    1、该参数加载存在性能问题
    2、该参数加载只能逐个加载
    3、该参数加载需要多模块配合（如：登陆频率，需要订单事件源及登陆事件源两部分）
    """

    @classmethod
    def order_category(cls, customer):
        if customer.serving_orders:
            category_list = list(set([order.category for order in customer.serving_orders]))
            customer.order_category = ""
            temp_index = 99999
            for index, category in enumerate(category_list):
                if temp_index >= index:
                    customer.order_category = category
                    temp_index = index
            return customer.order_category
        return ""

    @classmethod
    def avg_login_days(cls, customer):
        if customer.serving_days > 0:
            return int(round(customer.serving_days * 1.0 / customer.login_counter)) \
                if customer.login_counter > 0 else customer.serving_days
        return 0

    @classmethod
    def avg_contact_days(cls, customer):
        if customer.serving_days > 0:
            return int(round(customer.serving_days * 1.0 / customer.contact_counter)) \
                if customer.contact_counter > 0 else customer.serving_days
        return 0

    @classmethod
    def avg_monitor_days(cls, customer):
        if customer.serving_days > 0:
            return int(round(customer.serving_days * 1.0 / customer.monitor_counter)) \
                if customer.monitor_counter > 0 else customer.serving_days
        return 0

    @classmethod
    def valid_phone(cls, customer):
        if customer.phone:
            return True
        return False

class BaseField(object):

    def __init__(self, name, name_cn, load_func, custom_func = None):
        self.name = name
        self.name_cn = name_cn
        self.load_func = load_func if type(load_func) is list else [load_func, ]
        self.custom_func = custom_func

    def verify_condition(self, *args, **kwargs):
        raise Exception("this function is need to implements.....")

    def to_dict(self):
        filter_attrs = ['load_func', 'custom_func']
        result = {name:value for name, value in self.__dict__.items() if name not in filter_attrs}
        result.update({'type':self.__class__.__name__.lower()})
        return result

class CmpField(BaseField):

    def verify_condition(self, attr_val, gte_num, lte_num):
        if attr_val is not None:
            if (gte_num is not None) and (lte_num is not None):
                return gte_num <= attr_val <= lte_num
            elif lte_num is not None:
                return attr_val <= lte_num
            elif gte_num is not None:
                return gte_num <= attr_val
            return True
        else:
            return False

class ListCmpField(BaseField):

    def verify_condition(self, attr_val_list, gte_num, lte_num):
        if attr_val_list:
            if (gte_num is not None) and (lte_num is not None):
                for attr_val in attr_val_list:
                    if attr_val is not None:
                        if gte_num <= attr_val <= lte_num:
                            return True
                    else:
                        return False
                return False
            elif lte_num is not None:
                for attr_val in attr_val_list:
                    if attr_val is not None:
                        if attr_val <= lte_num:
                            return True
                    else:
                        return False
                return False
            elif gte_num is not None:
                for attr_val in attr_val_list:
                    if attr_val is not None:
                        if attr_val >= gte_num:
                            return True
                    else:
                        return False
                return False
            else:
                return True
        else:
            return False

class BoolField(BaseField):

    def verify_condition(self, attr_val, assert_val):
        if (attr_val and assert_val) or (not attr_val and not assert_val):
            return True
        return False

class EnumerateField(BaseField):

    def __init__(self, name, name_cn, load_func, enum_fields, custom_func = None):
        super(EnumerateField, self).__init__(name, name_cn, load_func, custom_func)
        self.enum_fields = enum_fields

    def verify_condition(self, attr_val, *enum_list):
        return attr_val in enum_list

class FieldManager(object):
    _instance = None

    @classmethod
    def register(cls, field):
        if cls._instance is None:
            cls._instance = collections.OrderedDict()
        cls._instance[field.name] = field

    @classmethod
    def read_field(cls, field_name):
        if cls._instance is None:
            return None
        return cls._instance.get(field_name, None)

    @classmethod
    def read_fields(cls, field_names):
        return [cls.read_field(field_name) for field_name in field_names if cls.read_field(field_name)]

    @classmethod
    def read_all_fields(cls):
        return [field for field in cls._instance.values() if field]

    @classmethod
    def read_allfields_mapping(cls):
        return copy.deepcopy(cls._instance)

FieldManager.register(BoolField(name = "valid_phone", name_cn = "有电话", load_func = None, custom_func = DealManager.valid_phone))
FieldManager.register(BoolField(name = "is_mnt", name_cn = "托管店铺", load_func = LoadManager.Load_mntcampaign))
FieldManager.register(BoolField(name = "is_pausing", name_cn = "是否暂停", load_func = None))
FieldManager.register(CmpField(name = "budget", name_cn = "店铺日限额", load_func = LoadManager.Load_budget))
FieldManager.register(EnumerateField(name = "order_category", name_cn = "订单类型", load_func = LoadManager.Load_subscribe, enum_fields = ENUMERATE_ORDER_CATEGORYS))
FieldManager.register(CmpField(name = "serving_days", name_cn = "当前服务天数", load_func = LoadManager.Load_subscribe))
FieldManager.register(CmpField(name = "surplus_days", name_cn = "剩余服务天数", load_func = LoadManager.Load_subscribe))
FieldManager.register(CmpField(name = "latest_paid_days", name_cn = "最新订单订购天数", load_func = LoadManager.Load_subscribe))
FieldManager.register(CmpField(name = "total_order_cycle_months", name_cn = "订单总周期（月）", load_func = LoadManager.Load_subscribe))
FieldManager.register(CmpField(name = "order_pay", name_cn = "订单总金额", load_func = LoadManager.Load_subscribe))
FieldManager.register(CmpField(name = "order_serving_pay", name_cn = "服务中订单总金额", load_func = LoadManager.Load_subscribe))
FieldManager.register(CmpField(name = "month_serving_pay", name_cn = "服务中订单月单价", load_func = LoadManager.Load_subscribe))
FieldManager.register(CmpField(name = "last_login_days", name_cn = "最后登陆距离天数", load_func = LoadManager.Load_Login))
FieldManager.register(CmpField(name = "avg_login_days", name_cn = "平均登录间隔天数", load_func = [LoadManager.Load_Login, LoadManager.Load_subscribe], custom_func = DealManager.avg_login_days))
FieldManager.register(CmpField(name = "login_counter", name_cn = "登录次数", load_func = LoadManager.Load_Login))
FieldManager.register(CmpField(name = "last_contact_days", name_cn = "最后有效联系距离天数", load_func = LoadManager.Load_contact_Event))
FieldManager.register(CmpField(name = "last_operate_days", name_cn = "最后操作距离天数", load_func = LoadManager.Load_operate_Event))
FieldManager.register(CmpField(name = "avg_contact_days", name_cn = "平均有效联系天数", load_func = [LoadManager.Load_contact_Event, LoadManager.Load_subscribe], custom_func = DealManager.avg_contact_days))
FieldManager.register(CmpField(name = "contact_counter", name_cn = "有效联系次数", load_func = LoadManager.Load_contact_Event))
FieldManager.register(CmpField(name = "invalid_contact_counter", name_cn = "无效联系次数", load_func = LoadManager.Load_contact_Event))
FieldManager.register(CmpField(name = "last_monitor_days", name_cn = "最后监控距离天数", load_func = LoadManager.Load_monitor_Event))
FieldManager.register(CmpField(name = "avg_monitor_days", name_cn = "平均有效监控天数", load_func = [LoadManager.Load_monitor_Event, LoadManager.Load_subscribe], custom_func = DealManager.avg_monitor_days))
FieldManager.register(CmpField(name = "monitor_counter", name_cn = "总监控次数", load_func = LoadManager.Load_monitor_Event))
FieldManager.register(CmpField(name = "last_rggy_days", name_cn = "最后人工干预间隔天数", load_func = LoadManager.Load_bulk_optimize))
FieldManager.register(CmpField(name = "sum_account_7impr", name_cn = "7天账户总展现", load_func = LoadManager.Load_account_report))
FieldManager.register(CmpField(name = "sum_account_7click", name_cn = "7天账户总点击", load_func = LoadManager.Load_account_report))
FieldManager.register(CmpField(name = "sum_account_7cost", name_cn = "7天账户总花费", load_func = LoadManager.Load_account_report))
FieldManager.register(CmpField(name = "sum_account_7pay", name_cn = "7天账户总成交金额", load_func = LoadManager.Load_account_report))
FieldManager.register(CmpField(name = "sum_account_7paycount", name_cn = "7天账户总成交笔数", load_func = LoadManager.Load_account_report))
FieldManager.register(CmpField(name = "sum_account_7ctr", name_cn = "7天账户点击率", load_func = LoadManager.Load_account_report))
FieldManager.register(CmpField(name = "sum_account_7cpc", name_cn = "7天账户PPC", load_func = LoadManager.Load_account_report))
FieldManager.register(CmpField(name = "sum_account_7roi", name_cn = "7天账户ROI", load_func = LoadManager.Load_account_report))
FieldManager.register(CmpField(name = "sum_account_7conv", name_cn = "7天账户转化率", load_func = LoadManager.Load_account_report))
# FieldManager.register(ListCmpField(name = "campaign_budget_list", name_cn = "计划日限额", load_func = LoadManager.Load_campaign_budget_list))

