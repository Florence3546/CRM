# coding=UTF-8

'''
Created on 2015-12-31

@author: YRK
'''
import collections

from .indicators import Performancedicator, ServerIndicator, NUMBER, RATE, AVG_NUMBER
from .loader import LoadFactory
from .calculator import CalculationFactory

class IndicatorManager(object):

    @classmethod
    def register(cls, indicator):
        if not hasattr(cls, "_indecator_mapping"):
            cls._indecator_mapping = collections.OrderedDict()
        cls._indecator_mapping[indicator.name] = indicator

        if not hasattr(cls, "_position_mapping"):
            cls._position_mapping = collections.defaultdict(list)
        cls._position_mapping[indicator.position].append(indicator)

        return True

    @classmethod
    def get_indicators_byposition(cls, position = "CONSULT"):
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

IndicatorManager.register(ServerIndicator(name = "new_people_count", name_cn = "新用户数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_subscribe, calc_func = CalculationFactory.new_people_count))
IndicatorManager.register(ServerIndicator(name = "contact_people_count", name_cn = "联系店铺数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_contact, calc_func = CalculationFactory.contact_people_count))
IndicatorManager.register(ServerIndicator(name = "lost_people_count", name_cn = "流失人数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_subscribe, calc_func = CalculationFactory.lost_people_count))
IndicatorManager.register(Performancedicator(name = "renew_order_pay", name_cn = "续签金额", position = "CONSULT", val_type = NUMBER, load_func = [LoadFactory.load_subscribe, LoadFactory.load_unsubscribe], calc_func = CalculationFactory.renew_order_pay))
IndicatorManager.register(Performancedicator(name = "renew_order_count", name_cn = "续签笔数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_subscribe, calc_func = CalculationFactory.renew_order_count))
IndicatorManager.register(Performancedicator(name = "reintro_count", name_cn = "转介绍次数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_reintro, calc_func = CalculationFactory.reintro_count))
IndicatorManager.register(Performancedicator(name = "good_comment_count", name_cn = "好评数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_comment, calc_func = CalculationFactory.good_comment_count))

IndicatorManager.register(Performancedicator(name = "change_comment_count", name_cn = "改评数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_comment, calc_func = CalculationFactory.change_comment_count, default_indicator = False))
IndicatorManager.register(ServerIndicator(name = "server_people_count", name_cn = "服务中店铺数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_contact, calc_func = CalculationFactory.server_people_count, default_indicator = False))
IndicatorManager.register(ServerIndicator(name = "expire_people_count", name_cn = "到期人数", position = "CONSULT", val_type = NUMBER, load_func = LoadFactory.load_subscribe, calc_func = CalculationFactory.expire_people_count, default_indicator = False))
IndicatorManager.register(ServerIndicator(name = "renew_rate", name_cn = "续签率", position = "CONSULT", val_type = RATE, load_func = LoadFactory.load_subscribe, calc_func = CalculationFactory.renew_rate, default_indicator = False))
# IndicatorManager.register(ServerIndicator(name = "first_contact_rate", name_cn = "一访率", position = "CONSULT", val_type = RATE, load_func = [LoadFactory.load_subscribe, LoadFactory.load_contact], calc_func = CalculationFactory.first_contact_rate, default_indicator = False))
# IndicatorManager.register(ServerIndicator(name = "second_contact_rate", name_cn = "二访率", position = "CONSULT", val_type = RATE, load_func = [LoadFactory.load_subscribe, LoadFactory.load_contact], calc_func = CalculationFactory.second_contact_rate, default_indicator = False))
IndicatorManager.register(ServerIndicator(name = "avg_contact_count", name_cn = "有效联系平均数", position = "CONSULT", val_type = AVG_NUMBER, load_func = LoadFactory.load_contact, calc_func = CalculationFactory.avg_contact_count, default_indicator = False))