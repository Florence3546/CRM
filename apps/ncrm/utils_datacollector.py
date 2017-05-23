# coding=UTF-8

import datetime

from apps.common.constant import Const
from apps.common.utils.utils_log import log
from apps.common.utils.utils_mysql import execute_query_sql
from apps.subway.models_account import account_coll

KCJL_ITEM_CODE_TUPLE = ('ts-25811-1', 'ts-25811-8')
QN_ITEM_CODE_TUPLE = ('FW_GOODS-1921400-1', 'FW_GOODS-1921400-v2')
RJJH_ITEM_CODE_TUPLE = ('ts-25811-6',)

DATA_AGGR_CONFIG = {
                        'cost':{
                                    'group':{
                                             'cost':{'$sum':'$rpt_list.cost'}
                                             },
                                    'project':{
                                               'cost':'$cost'
                                               }
                                },
                        'impr':{
                                    'group':{
                                             'impr':{'$sum':'$rpt_list.impr'}
                                             },
                                    'project':{
                                               'impr':'$impr'
                                               }
                                },
                        'click':{
                                    'group':{
                                             'click':{'$sum':'$rpt_list.click'}
                                             },
                                    'project':{
                                               'click':'$click'
                                               }
                                },
                        'directpay':{
                                    'group':{
                                             'directpay':{'$sum':'$rpt_list.directpay'}
                                             },
                                    'project':{
                                               'directpay':'$directpay'
                                               }
                                },
                        'indirectpay':{
                                    'group':{
                                             'indirectpay':{'$sum':'$rpt_list.indirectpay'}
                                             },
                                    'project':{
                                               'indirectpay':'$indirectpay'
                                               }
                                },
                        'directpaycount':{
                                    'group':{
                                             'directpaycount':{'$sum':'$rpt_list.directpaycount'}
                                             },
                                    'project':{
                                               'directpaycount':'$directpaycount'
                                               }
                                },
                        'indirectpaycount':{
                                    'group':{
                                             'indirectpaycount':{'$sum':'$rpt_list.indirectpaycount'}
                                             },
                                    'project':{
                                               'indirectpaycount':'$indirectpaycount'
                                               }
                                },
                        'favitemcount':{
                                    'group':{
                                             'favitemcount':{'$sum':'$rpt_list.favitemcount'}
                                             },
                                    'project':{
                                               'favitemcount':'$favitemcount'
                                               }
                                },
                        'favshopcount':{
                                    'group':{
                                             'favshopcount':{'$sum':'$rpt_list.favshopcount'}
                                             },
                                    'project':{
                                               'favshopcount':'$favshopcount'
                                               }
                                },
                        'click_rate':{
                                    'group':{
                                            'cost':{'$sum':'$rpt_list.cost'},
                                            'impr':{'$sum':'$rpt_list.impr'}
                                            },
                                    'project':{
                                                     'click_rate':{'$cond':[{'$eq':['$impr', 0]},
                                                                          0,
                                                                          {'$divide':['$click', '$impr']}
                                                                          ]},
                                               }
                                },
                        'ppc':{
                                    'group':{
                                             'cost':{'$sum':'$rpt_list.cost'},
                                             'click':{'$sum':'$rpt_list.click'}
                                             },
                                    'project':{
                                               'ppc':{'$cond':[{'$eq':['$click', 0]},
                                                               0,
                                                               {'$divide':['$cost', '$click']}
                                                               ]}
                                               }
                                },
                        'pay':{
                                    'group':{
                                             'indirectpay':{'$sum':'$rpt_list.indirectpay'},
                                             'directpay':{'$sum':'$rpt_list.directpay'}
                                             },
                                    'project':{
                                               'pay':{'$add':['$directpay', '$indirectpay']}
                                               }
                                },
                        'paycount':{
                                    'group':{
                                             'indirectpaycount':{'$sum':'$rpt_list.indirectpaycount'},
                                             'directpaycount':{'$sum':'$rpt_list.directpaycount'}
                                             },
                                    'project':{
                                               'paycount':{'$add':['$directpaycount', '$indirectpaycount']},
                                               }
                                },
                        'favcount':{
                                    'group':{
                                             'favitemcount':{'$sum':'$rpt_list.favitemcount'},
                                             'favshopcount':{'$sum':'$rpt_list.favshopcount'}
                                             },
                                    'project':{
                                               'favcount':{'$add':['$favitemcount', '$favshopcount']},
                                               }
                                },
                        'conv':{
                                    'group':{
                                             'directpaycount':{'$sum':'$rpt_list.directpaycount'},
                                             'indirectpaycount':{'$sum':'$rpt_list.indirectpaycount'},
                                             'click':{'$sum':'$rpt_list.click'}
                                             },
                                    'project':{
                                               'conv':{'$cond':[{'$eq':['$click', 0]},
                                                                0,
                                                                {'$divide':[{'$add':['$directpaycount', '$indirectpaycount']}, '$click']}
                                                                ]},
                                               }
                                },
                        'roi':{
                                    'group':{
                                             'directpay':{'$sum':'$rpt_list.directpay'},
                                             'indirectpay':{'$sum':'$rpt_list.indirectpay'},
                                             'cost':{'$sum':'$rpt_list.cost'}
                                             },
                                    'project':{
                                               'roi':{'$cond':[{'$eq':['$cost', 0]},
                                                               0,
                                                               {'$divide':[{'$add':['$directpay', '$indirectpay']}, '$cost']}
                                                               ]},
                                               }
                                },
                    }

def customers_initialize_data(fields):
    shop_key = 'shop_id'
    if shop_key not in fields:
        fields.append(shop_key)

    nick_key = 'nick'
    if nick_key not in fields:
        fields.append(nick_key)

    sql = """
        select %s from ncrm_customer
    """ % (','.join(fields))

    return execute_query_sql(sql)

class DataCollector(object):

    @staticmethod
    def order_data_collector(db_fields, shop_nick_mapping):
        select_str = ""
        if db_fields:
            select_str = ",%s" % (','.join(db_fields))
        sql = """
            select shop_id %s
            from ncrm_subscribe
            order by  create_time desc
        """ % (select_str)

        result_list = execute_query_sql(sql)
        data_mapping = {}
        for result in result_list:
            shop_id = result['shop_id']
            if shop_id:
                if shop_id not in data_mapping:
                    data_mapping[shop_id] = {'shop_id':shop_id, 'order_list':[]}
                data_mapping[shop_id]['order_list'].append(result)

        return data_mapping.values()

    @staticmethod
    def account_data_collector(db_fields, days):
        # 耗性能
        group_dict = {'_id':'$_id'}
        project_dict = {'shop_id':'$_id', '_id':0}
        for field in db_fields:
            field_mapping = DATA_AGGR_CONFIG[field]
            group_dict.update(field_mapping['group'])
            project_dict.update(field_mapping['project'])

        date_time = datetime.datetime.now() - datetime.timedelta(days = days + 1)
        pipeline = [{'$project':{'shop_id':'$id',
                                            'rpt_list':{'$setUnion':['$rpt_list', [{'cost':0,
                                                                                                  'impressions':0,
                                                                                                  'click':0,
                                                                                                  'directpay':0,
                                                                                                  'indirectpay':0,
                                                                                                  'directpaycount':0,
                                                                                                  'indirectpaycount':0,
                                                                                                  'favitemcount':0,
                                                                                                  'favshopcount':0,
                                                                                                  'date':date_time,
                                                                                                   }]
                                                                                 ]},
                                            }
                         },
                        {'$unwind':'$rpt_list'},
                        {'$match':{'rpt_list.date':{'$gte':date_time}}},
                        {'$group':group_dict},
                        {'$project':project_dict}
                        ]
        try:
            return account_coll.aggregate(pipeline)['result']
        except Exception, e:
            log.error('account aggregate error, e=%s' % (e))
            return []

    @staticmethod
    def account_data_collector_7(db_fields, shop_nick_mapping):
        return DataCollector.account_data_collector(db_fields, 300)

class BaseHandler(object):

    def __init__(self, name, description):
        self.name = name
        self.description = description

    @property
    def collector_handler(self):
        raise Exception("collector_handler is need to Implement")

class OrderHandler(BaseHandler):

    def __init__(self, name, description):
        super(OrderHandler, self).__init__(name, description)

    @property
    def collector_handler(self):
        return DataCollector.order_data_collector

class IsHandler(OrderHandler):
    db_field = ['item_code']
    default = False

    def __init__(self, name, description, item_code_list):
        super(IsHandler, self).__init__(name, description)

    def data_handler(self, record):
        indicator = self.db_field[0]
        is_ok = self.default
        if 'order_list' in record:
            for order in record['order_list']:
                if order[indicator] in self.item_code_list:
                    is_ok = True
                    break
        return {self.name:is_ok}

class IsKCJL(IsHandler):

    def __init__(self, name, description):
        self.item_code_list = KCJL_ITEM_CODE_TUPLE
        super(IsKCJL, self).__init__(name, description, self.item_code_list)

class IsRJJH(IsHandler):

    def __init__(self, name, description):
        self.item_code_list = RJJH_ITEM_CODE_TUPLE
        super(IsRJJH, self).__init__(name, description, self.item_code_list)

class IsQN(IsHandler):

    def __init__(self, name, description):
        self.item_code_list = QN_ITEM_CODE_TUPLE
        super(IsQN, self).__init__(name, description, self.item_code_list)

class OrderTimeBase(OrderHandler):
    default = "1970.01.01"

    def __init__(self, name, description, db_field, \
                  article_list = Const.COMMON_SUBSCRIBE_MAPPING['software']):
        self.db_field = db_field
        self.db_field.append('article_code')
        self.article_list = article_list
        super(OrderTimeBase, self).__init__(name, description)

    def data_handler(self, record):
        indicator = self.db_field[0]
        date_time = self.default
        for order in record['order_list']:
            if order['article_code'] in self.article_list and order[indicator]:
                date_time = order[indicator].strftime("%Y-%m-%d")
                break

        return {self.name:date_time}

class CreateTime(OrderTimeBase):
    db_field = ['create_time']

    def __init__(self, name, description):
        super(CreateTime, self).__init__(name, description, self.db_field)

class StartDate(OrderTimeBase):
    db_field = ['start_date']

    def __init__(self, name, description):
        super(StartDate, self).__init__(name, description, self.db_field)

class EndDate(OrderTimeBase):
    db_field = ['end_date']

    def __init__(self, name, description):
        super(EndDate, self).__init__(name, description, self.db_field)

class Surplus(OrderHandler):
    db_field = ['end_date']
    default = -9999

    def __init__(self, name, description):
        super(Surplus, self).__init__(name, description)

    def data_handler(self, record):
        indicator = self.db_field[0]
        days = self.default
        if 'order_list' in record and len(record['order_list']) > 0:
            days = (record['order_list'][0][indicator] - datetime.date.today()).days
        return {self.name:days}

class Subscribe(OrderHandler):
    db_field = ['start_date']
    default = -9999

    def __init__(self, name, description):
        super(Subscribe, self).__init__(name, description)

    def data_handler(self, record):
        indicator = self.db_field[0]
        days = self.default
        if 'order_list' in record and len(record['order_list']) > 0:
            days = (datetime.date.today() - record['order_list'][0][indicator]).days
        return {self.name:days}

class OrderLastBizType(OrderHandler):
    db_field = ['biz_type']
    default = -1

    def __init__(self, name, description):
        super(OrderLastBizType, self).__init__(name, description)

    def data_handler(self, record):
        indicator = self.db_field[0]
        status = self.default
        if 'order_list' in record and len(record['order_list']) > 0:
            status = record['order_list'][0][indicator]
        return {self.name:status}

class OrderExistBizType(OrderHandler):
    db_field = ['biz_type']
    default = []

    def __init__(self, name, description):
        super(OrderExistBizType, self).__init__(name, description)

    def data_handler(self, record):
        indicator = self.db_field[0]
        type_list = self.default
        type_set = set()
        if 'order_list' in record :
            for order in record['order_list']:
                type_set.add(order[indicator])
            type_list = list(type_set)
        return {self.name:type_list}

class OrderLastPay(OrderHandler):
    db_field = ['pay']
    default = 0

    def __init__(self, name, description):
        super(OrderLastPay, self).__init__(name, description)

    def data_handler(self, record):
        indicator = self.db_field[0]
        last_pay = self.default
        if 'order_list' in record and len(record['order_list']) > 0:
            last_pay = record['order_list'][0][indicator]
        return {self.name:last_pay}

class OrderTotalPay(OrderHandler):
    db_field = ['pay']
    default = 0

    def __init__(self, name, description):
        super(OrderTotalPay, self).__init__(name, description)

    def data_handler(self, record):
        indicator = self.db_field[0]
        sum_pay = self.default
        if 'order_list' in record :
            for order in record['order_list']:
                sum_pay += order[indicator]
        return {self.name:sum_pay / 100.0}

class OrderCounter(OrderHandler):

    db_field = []
    default = 0

    def __init__(self, name, description):
        super(OrderCounter, self).__init__(name, description)

    def data_handler(self, record):
        order_count = self.default
        if 'order_list' in record :
            order_count = len(record['order_list'])
        return {self.name:order_count}

class OrderSalers(OrderHandler):

    db_field = ['psuser_id']
    default = []

    def __init__(self, name, description):
        super(OrderSalers, self).__init__(name, description)

    def data_handler(self, record):
        saler_list = self.default
        if 'order_list' in record :
            psuser_set = set()
            for order in record['order_list']:
                psuser_set.add(order['psuser_id'])
            saler_list = list(psuser_set)
        return {self.name:saler_list}

class OrderoOperators(OrderHandler):

    db_field = ['operater_id']
    default = []

    def __init__(self, name, description):
        super(OrderoOperators, self).__init__(name, description)

    def data_handler(self, record):
        saler_list = self.default
        if 'order_list' in record :
            psuser_set = set()
            for order in record['order_list']:
                psuser_set.add(order['operater_id'])
            saler_list = list(psuser_set)
        return {self.name:saler_list}

class AccountDataHandler(BaseHandler):

    def __init__(self, name, description, indicator):
        self.indicator = indicator
        super(AccountDataHandler, self).__init__(name, description)

    def data_handler(self, record):
        return {self.name:record[self.indicator]}

    @property
    def collector_handler(self):
        return DataCollector.account_data_collector

class AccountRptDaysHandler(AccountDataHandler):

    def __init__(self, name, description, indicator, rpt_days):
        self.rpt_days = rpt_days
        super(AccountRptDaysHandler, self).__init__(name, description, indicator)

    @property
    def collector_handler(self):
        func_name = super(AccountRptDaysHandler, self).collector_handler.__name__
        collector_handler_name = "%s_%s" % (func_name, self.rpt_days)
        collector_func = getattr(DataCollector, collector_handler_name)
        if collector_func:
            return collector_func
        else:
            raise Exception('funcion : %s is need to implement at DataCollector'\
                            % (collector_handler_name))

class ROIHandler(AccountRptDaysHandler):
    db_field = ['roi']
    default = 0.0

    def __init__(self, name, description, rpt_days):
        super(ROIHandler, self).__init__(name, description, self.db_field[0], rpt_days)
