# coding=UTF-8

'''
Created on 2015-12-31

@author: YRK
'''
import collections

from .indicators import ConsultIndicator, NUMBER, RATE, AVG_NUMBER
from .loader import LoadFactory
from .calculator import CalculationFactory, SumFactory, ViewerFactory

class IndicatorManager(object):

    @classmethod
    def register(cls, indicator):
        if not hasattr(cls, "_indecator_mapping"):
            cls._indecator_mapping = collections.OrderedDict()
        cls._indecator_mapping[indicator.name] = indicator

        if not hasattr(cls, "_position_mapping"):
            cls._position_mapping = collections.defaultdict(list)
        cls._position_mapping[indicator.__class__.__name__].append(indicator)

        return True

    @classmethod
    def get_indicators_byposition(cls, position = "ConsultIndicator"):
        if not hasattr(cls, "_position_mapping"):
            raise Exception("IndicatorManager class have no any registrator")

        indicators = cls._position_mapping.get(position, None)
        if indicators is None:
            raise Exception("position : %s - have no any indicators.")
        return indicators

    @classmethod
    def get_indicator(cls, indicator_name):
        if not hasattr(cls, "_indecator_mapping"):
            raise Exception("IndicatorManager class have no any registrator")
        return cls._indecator_mapping.get(indicator_name, None)

register_indicator = [
    # ConsultIndicator(
    #     name = "contact_people_count",
    #     name_cn = "联系店铺数",
    #     val_type = NUMBER,
    #     unit = '个',
    #     load_func = LoadFactory._valid_contacts,
    #     calc_func = CalculationFactory.contact_records,
    #     sum_func = SumFactory.contact_people_count,
    #     show_func = ViewerFactory.show_contact
    # ),
    # ConsultIndicator(
    #     name = "avg_contact_count",
    #     name_cn = "有效联系平均数",
    #     val_type = AVG_NUMBER,
    #     unit = '个',
    #     load_func = LoadFactory._valid_contacts,
    #     calc_func = CalculationFactory.contact_records,
    #     sum_func = SumFactory.avg_contact_count,
    #     show_func = ViewerFactory.show_contact
    # ),
    # ConsultIndicator(
    #     name = "renew_order_count",
    #     name_cn = "单量",
    #     val_type = NUMBER,
    #     unit = '笔',
    #     load_func = LoadFactory._renew_orders,
    #     calc_func = CalculationFactory.renew_order_count,
    #     sum_func = SumFactory.renew_order_count,
    #     show_func = ViewerFactory.show_subscribe
    # ),
    # ConsultIndicator(
    #     name = "performance_unsubscribe_pay",
    #     name_cn = "业绩退款金额",
    #     val_type = NUMBER,
    #     unit = '元',
    #     load_func = LoadFactory._performance_unsubscribes,
    #     calc_func = CalculationFactory.unsubscribe_pay,
    #     sum_func = SumFactory.unsubscribe_pay,
    #     show_func = ViewerFactory.show_unsubscribe
    # ),
    # ConsultIndicator(
    #     name = "reintro_count",
    #     name_cn = "转介绍数",
    #     val_type = NUMBER,
    #     unit = '笔',
    #     load_func = LoadFactory._reintros,
    #     calc_func = CalculationFactory.reintro_count,
    #     sum_func = SumFactory.reintro_count,
    #     show_func = ViewerFactory.show_reintro
    # ),
    # ConsultIndicator(
    #     name = "change_comment_count",
    #     name_cn = "改评数",
    #     val_type = NUMBER,
    #     unit = '个',
    #     load_func = LoadFactory._change_comments,
    #     calc_func = CalculationFactory.change_comment_count,
    #     sum_func = SumFactory.change_comment_count,
    #     show_func = ViewerFactory.show_comment
    # ),
    # ConsultIndicator(
    #     name = "new_people_count",
    #     name_cn = "新订用户数",
    #     val_type = NUMBER,
    #     unit = '个',
    #     load_func = LoadFactory._new_orders,
    #     calc_func = CalculationFactory.new_people_count,
    #     sum_func = SumFactory.new_people_count,
    #     show_func = ViewerFactory.show_customers
    # ),
    # ConsultIndicator(
    #     name = "expire_order_count",
    #     name_cn = "到期订单数",
    #     val_type = NUMBER,
    #     unit = '笔',
    #     load_func = LoadFactory._expire_orders,
    #     calc_func = CalculationFactory.expire_order_count,
    #     sum_func = SumFactory.expire_order_count,
    #     show_func = ViewerFactory.show_subscribe
    # ),
    # ConsultIndicator(
    #     name = "lost_customer_people",
    #     name_cn = "流失人数",
    #     val_type = NUMBER,
    #     unit = '人',
    #     load_func = LoadFactory._lost_coustomers,
    #     calc_func = CalculationFactory.lost_customer_people,
    #     sum_func = SumFactory.lost_customer_people,
    #     show_func = ViewerFactory.show_customers
    # ),
    # ConsultIndicator(
    #     name = "renew_rate",
    #     name_cn = "续签率",
    #     val_type = RATE,
    #     unit = '%',
    #     load_func = [LoadFactory._renew_orders, LoadFactory._expire_orders],
    #     calc_func = CalculationFactory.renew_rate,
    #     sum_func = SumFactory.renew_rate,
    #     show_func = None
    # ),
    # ConsultIndicator(
    #     name = "unknown_order_count",
    #     name_cn = "未知单数",
    #     val_type = NUMBER,
    #     unit = '笔',
    #     load_func = LoadFactory._unknown_orders,
    #     calc_func = CalculationFactory.unknown_order_count,
    #     sum_func = SumFactory.unknown_order_count,
    #     show_func = ViewerFactory.show_subscribe
    # ),
    # ConsultIndicator(
    #     name = "unsubscribe_count",
    #     name_cn = "退款数",
    #     val_type = NUMBER,
    #     unit = '个',
    #     load_func = LoadFactory._unsubscribes,
    #     calc_func = CalculationFactory.unsubscribe_count,
    #     sum_func = SumFactory.unsubscribe_count,
    #     show_func = ViewerFactory.show_unsubscribe
    # ),
    ConsultIndicator(
        name = "renew_order_pay",
        name_cn = "进账金额",
        val_type = NUMBER,
        unit = '元',
        load_func = LoadFactory._renew_orders,
        calc_func = CalculationFactory.renew_order_pay,
        sum_func = SumFactory.renew_order_pay,
        show_func = ViewerFactory.show_subscribe,
        desc = "销服组所有订单（排除SD）的金额之和"
    ),
    ConsultIndicator(
        name = "real_renew_order_pay",
        name_cn = "有效进账金额",
        val_type = NUMBER,
        unit = '元',
        load_func = LoadFactory._real_renew_orders,
        calc_func = CalculationFactory.renew_order_pay,
        sum_func = SumFactory.renew_order_pay,
        show_func = ViewerFactory.show_subscribe,
        desc = "进账金额中已通过审批的部分"
    ),
    ConsultIndicator(
        name = "unsubscribe_pay",
        name_cn = "退款金额",
        val_type = NUMBER,
        unit = '元',
        load_func = LoadFactory._unsubscribes,
        calc_func = CalculationFactory.unsubscribe_pay,
        sum_func = SumFactory.unsubscribe_pay,
        show_func = ViewerFactory.show_unsubscribe,
        desc = "已录入的退款事件中销服组需要分摊的金额之和"
    ),
    ConsultIndicator(
        name = "good_comment_count",
        name_cn = "旧好评数",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._good_comments,
        calc_func = CalculationFactory.good_comment_count,
        sum_func = SumFactory.good_comment_count,
        show_func = ViewerFactory.show_comment,
        desc = "日常好评数 + 踩好评数 + 5分无评语改评数 + 全5分好评改评数"
    ),
    ConsultIndicator(
        name = "bad_comment_count",
        name_cn = "差评数",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._bad_comments,
        calc_func = CalculationFactory.bad_comment_count,
        sum_func = SumFactory.bad_comment_count,
        show_func = ViewerFactory.show_comment,
        desc = "差评数 + 5分评语未去 + 去评语评分未改 + 未改全5分"
    ),
    ConsultIndicator(
        name = "extend_cycle",
        name_cn = "用户存活增量",
        val_type = NUMBER,
        unit = '月',
        load_func = LoadFactory._user_cycle_increment,
        calc_func = CalculationFactory.extend_cycle,
        sum_func = SumFactory.extend_cycle,
        show_func = ViewerFactory.show_subscribe,
        desc = "订单周期（排除SD和千牛）的月数除以3得到的数字之和"
    ),
    ConsultIndicator(
        name = "active_customer_count",
        name_cn = "活跃用户人天",
        val_type = NUMBER,
        unit = '人天',
        load_func = LoadFactory._active_customers,
        calc_func = CalculationFactory.active_customer_count,
        sum_func = SumFactory.active_customer_count,
        show_func = ViewerFactory.show_customers,
        desc = "各店铺中满足托管计划日花费之和大于等于50元的天数之和"
    ),
    ConsultIndicator(
        name = "serving_people_count",
        name_cn = "服务中店铺数",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._serving_orders,
        calc_func = CalculationFactory.serving_people_count,
        sum_func = SumFactory.serving_people_count,
        show_func = ViewerFactory.show_customers,
        desc = "指定日期范围内有服务过，且是付费订单的店铺数之和"
    ),
    ConsultIndicator(
        name = "new_good_comment_count",
        name_cn = "好评数",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._new_good_comments,
        calc_func = CalculationFactory.good_comment_count,
        sum_func = SumFactory.good_comment_count,
        show_func = ViewerFactory.show_comment,
        desc = "日常好评数 + 5分无评语改评数 + 全5分好评改评数"
    ),
    ConsultIndicator(
        name = "top_good_comment_count",
        name_cn = "踩好评数",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._top_good_comments,
        calc_func = CalculationFactory.good_comment_count,
        sum_func = SumFactory.good_comment_count,
        show_func = ViewerFactory.show_comment,
        desc = "踩好评数"
    ),
    ConsultIndicator(
        name = "unsubscribe_apportion",
        name_cn = "退款责任分摊",
        val_type = NUMBER,
        unit = '分',
        load_func = LoadFactory._unsubscribes_apportion,
        calc_func = CalculationFactory.unsubscribe_pay,
        sum_func = SumFactory.unsubscribe_apportion,
        show_func = ViewerFactory.show_unsubscribe,
        desc = "每笔退款记录（排除现金退款）责任分摊总分为10分，录入人销服组占3分，签单人销服组占7分，若无签单人则服务人销服组占7分"
    ),
    ConsultIndicator(
        name = "pay_subscribe_month1_count",
        name_cn = "付费订购一个月",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._pay_subscribe,
        calc_func = CalculationFactory.subscribe_month1_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除类目升级、vip升级、SD和千牛的订单，已通过审批、月付费金额>=30元且服务时长<=60天的订单数"
    ),
    ConsultIndicator(
        name = "pay_subscribe_month3_count",
        name_cn = "付费订购一季度",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._pay_subscribe,
        calc_func = CalculationFactory.subscribe_month3_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除类目升级、vip升级、SD和千牛的订单，已通过审批、月付费金额>=30元且服务时长在90～120天的订单数"
    ),
    ConsultIndicator(
        name = "pay_subscribe_month6_count",
        name_cn = "付费订购半年",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._pay_subscribe,
        calc_func = CalculationFactory.subscribe_month6_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除类目升级、vip升级、SD和千牛的订单，已通过审批、月付费金额>=30元且服务时长在150～210天的订单数"
    ),
    ConsultIndicator(
        name = "pay_subscribe_month12_count",
        name_cn = "付费订购一年",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._pay_subscribe,
        calc_func = CalculationFactory.subscribe_month12_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除类目升级、vip升级、SD和千牛的订单，已通过审批、月付费金额>=30元且服务时长在240天及以上的订单数"
    ),
    ConsultIndicator(
        name = "free_pay_subscribe_month1_count",
        name_cn = "非付费订购一个月",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._free_pay_subscribe,
        calc_func = CalculationFactory.subscribe_month1_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除升级和千牛的订单，已通过审批、订单金额>0、非SD订单月付费金额<30元且服务时长<=60天的订单数"
    ),
    ConsultIndicator(
        name = "free_pay_subscribe_month3_count",
        name_cn = "非付费订购一季度",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._free_pay_subscribe,
        calc_func = CalculationFactory.subscribe_month3_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除升级和千牛的订单，已通过审批、订单金额>0、非SD订单月付费金额<30元且服务时长在90～120天的订单数"
    ),
    ConsultIndicator(
        name = "free_pay_subscribe_month6_count",
        name_cn = "非付费订购半年",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._free_pay_subscribe,
        calc_func = CalculationFactory.subscribe_month6_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除升级和千牛的订单，已通过审批、订单金额>0、非SD订单月付费金额<30元且服务时长在150～210天的订单数"
    ),
    ConsultIndicator(
        name = "free_pay_subscribe_month12_count",
        name_cn = "非付费订购一年",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._free_pay_subscribe,
        calc_func = CalculationFactory.subscribe_month12_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除升级和千牛的订单，已通过审批、订单金额>0、非SD订单月付费金额<30元且服务时长在240天及以上的订单数"
    ),
    ConsultIndicator(
        name = "expiring_renew_customer_count",
        name_cn = "到期当月续签用户",
        val_type = NUMBER,
        unit = '个',
        load_func = LoadFactory._expiring_renew_subscribe,
        calc_func = CalculationFactory.renew_order_count,
        sum_func = SumFactory.expiring_renew_customer_count,
        show_func = ViewerFactory.show_subscribe,
        desc = "在订单过期的那个月内成功续订了的用户数",
    ),
    ConsultIndicator(
        name = "monthly50_subscribe_count",
        name_cn = "月单价>=50元",
        val_type = NUMBER,
        unit = '笔',
        load_func = LoadFactory._monthly_pay_subscribe,
        calc_func = CalculationFactory.monthly50_subscribe_count,
        sum_func = SumFactory.count,
        show_func = ViewerFactory.show_subscribe,
        desc = "排除类目升级、vip升级、SD和千牛的订单，已通过审批、月付费金额>=50元的订单数",
    ),
    ConsultIndicator(
        name = "market_unsubscribe_pay",
        name_cn = "市场签单退款",
        val_type = NUMBER,
        unit = '元',
        load_func = LoadFactory._market_unsubscribes,
        calc_func = CalculationFactory.unsubscribe_pay,
        sum_func = SumFactory.unsubscribe_pay,
        show_func = ViewerFactory.show_unsubscribe,
        desc = "由市场签单的退款事件中销服组需要分摊的金额之和",
    ),
]
for indicator in register_indicator:
    IndicatorManager.register(indicator)
