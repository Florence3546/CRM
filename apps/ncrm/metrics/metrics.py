# coding=UTF-8
from apps.ncrm.metrics.dbInterfaces import MyCustomersInterface, AllocationRecordInterface, EventInterface, SubscribeInterface


class MetricBase(object):
    '''度量基类'''
    def __init__(self):
        self.name = None
        self.details = None
        self.name_cn = None
        self.desc = None
        self.unit = None
        self.snapshot_order = None
        self.detail_titles = []

    def fetch(self, manager, psuser_id, date_obj):
        '''提取数据'''
        raise Exception('No implemented!')

    def snapshot(self, manager, psuser_id, date_obj):
        '''给数据打快照'''
        raise Exception('No implemented!')

    def get_details(self, psuser_dict=None, **kwargs):
        '''获取详细数据'''
        raise Exception('No implemented!')

    def aggregate(self, data_list):
        '''根据详细数据统计数值'''
        raise Exception('No implemented!')


class RjjhCustomerNumber(MetricBase):
    '''服务类目账户数'''
    def __init__(self):
        self.name = 'rjjh_cust_num'
        self.details = 'rjjh_sub'
        self.name_cn = '服务类目账户数'
        self.desc = '在指定日期范围内，提供服务的类目订单的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 0
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['rjjh_sub'] if mycust and 'rjjh_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        SubscribeInterface.get_rjjh_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class ZtcCustomerNumber(MetricBase):
    '''服务直通车账户数'''
    def __init__(self):
        self.name = 'ztc_cust_num'
        self.details = 'ztc_sub'
        self.name_cn = '服务直通车账户数'
        self.desc = '在指定日期范围内，提供服务的直通车订单的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 0
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['ztc_sub'] if mycust and 'ztc_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        SubscribeInterface.get_ztc_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class ZzCustomerNumber(MetricBase):
    '''服务钻展账户数'''
    def __init__(self):
        self.name = 'zz_cust_num'
        self.details = 'zz_sub'
        self.name_cn = '服务钻展账户数'
        self.desc = '在指定日期范围内，提供服务的钻展订单的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 0
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['zz_sub'] if mycust and 'zz_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        SubscribeInterface.get_zz_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class ZxCustomerNumber(MetricBase):
    '''服务装修账户数'''
    def __init__(self):
        self.name = 'zx_cust_num'
        self.details = 'zx_sub'
        self.name_cn = '服务装修账户数'
        self.desc = '在指定日期范围内，提供服务的店铺装修的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 0
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['zx_sub'] if mycust and 'zx_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        SubscribeInterface.get_zx_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class DyyCustomerNumber(MetricBase):
    '''服务代运营账户数'''
    def __init__(self):
        self.name = 'dyy_cust_num'
        self.details = 'dyy_sub'
        self.name_cn = '服务代运营账户数'
        self.desc = '在指定日期范围内，提供服务的代运营订单的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 0
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['dyy_sub'] if mycust and 'dyy_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        SubscribeInterface.get_dyy_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class SeoCustomerNumber(MetricBase):
    '''服务seo账户数'''
    def __init__(self):
        self.name = 'seo_cust_num'
        self.details = 'seo_sub'
        self.name_cn = '服务seo账户数'
        self.desc = '在指定日期范围内，提供服务的seo订单的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 0
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['seo_sub'] if mycust and 'seo_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        SubscribeInterface.get_seo_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class NewCustomerNumber(MetricBase):
    '''新增账户数'''
    def __init__(self):
        self.name = 'new_cust_num'
        self.details = 'new_cust_sub'
        self.name_cn = '新增账户数'
        self.desc = '在指定日期范围内，每天服务账户中比前一天多出的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 1
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['new_cust_sub'] if mycust and 'new_cust_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        MyCustomersInterface.get_new_cust_sub(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class PauseCustomerNumber(MetricBase):
    '''暂停账户数'''
    def __init__(self):
        self.name = 'pause_cust_num'
        self.details = 'pause_sub'
        self.name_cn = '暂停账户数'
        self.desc = '在指定日期范围内，录入了暂停事件的账户数（去重）'
        self.unit = '个'
        self.snapshot_order = 1
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['pause_sub'] if mycust and 'pause_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        EventInterface.get_pause_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class UnsubscribeCustomerNumber(MetricBase):
    '''退款账户数'''
    def __init__(self):
        self.name = 'unsub_cust_num'
        self.details = 'unsub_sub'
        self.name_cn = '退款账户数'
        self.desc = '在指定日期范围内，录入了退款事件的账户数（排除友情赠送和积分兑换的，去重）'
        self.unit = '个'
        self.snapshot_order = 1
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['unsub_sub'] if mycust and 'unsub_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        EventInterface.get_unsub_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class ExpireCustomerNumber(MetricBase):
    '''流失账户数'''
    def __init__(self):
        self.name = 'expire_cust_num'
        self.details = 'expire_sub'
        self.name_cn = '流失账户数'
        self.desc = '在指定日期范围内，停止所有服务的账户数（排除退款、暂停、转出的客户，去重）'
        self.unit = '个'
        self.snapshot_order = 1
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['expire_sub'] if mycust and 'expire_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        EventInterface.get_expire_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class ChangeCustomerNumber(MetricBase):
    '''转出账户数'''
    def __init__(self):
        self.name = 'change_cust_num'
        self.details = 'change_sub'
        self.name_cn = '转出账户数'
        self.desc = '在指定日期范围内，订单操作人由你改为他人的订单的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 1
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust['change_sub'] if mycust and 'change_sub' in mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        AllocationRecordInterface.get_change_sub_list(manager, psuser_id, date_obj)

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class RenewCustomerNumber(MetricBase):
    '''续签账户数'''
    def __init__(self):
        self.name = 'renew_cust_num'
        self.details = 'renew_sub'
        self.name_cn = '续签账户数'
        self.desc = '在指定日期范围内，同时是在前一笔订单流失30天内续订同类订单的账户数（排除友情赠送的，去重）'
        self.unit = '个'
        self.snapshot_order = 2
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        sub_list = SubscribeInterface.get_renew_sub_list(manager, psuser_id, date_obj)
        result = self.aggregate(sub_list)
        manager.feed_data(psuser_id, date_obj, {self.name: result})
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        return

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return len(set([doc['shop_id'] for doc in sub_list]))


class ServiceAmount(MetricBase):
    '''服务金额'''
    def __init__(self):
        self.name = 'service_amount'
        self.details = 'served_sub'
        self.name_cn = '服务金额'
        self.desc = '在指定日期范围内，每日服务金额（所有操作人是你的订单（包括人机、VIP、TP、钻展、代运营，排除友情赠送的）的单日服务金额之和）之和'
        self.unit = '元'
        self.snapshot_order = 2
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        mycust = MyCustomersInterface.get_data(manager, psuser_id, date_obj)
        sub_list = mycust.get('serving_sub_list', []) + mycust.get('pause_sub', []) + mycust.get('unsub_sub', []) if mycust else []
        result = self.aggregate(sub_list)
        _data = {
            self.details: sub_list,
            self.name: result
        }
        manager.feed_data(psuser_id, date_obj, _data)
        return result

    def snapshot(self, manager, psuser_id, date_obj):
        return

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return round(sum([doc['amount'] for doc in sub_list]) / 100.0, 2)


class Income(MetricBase):
    '''进账金额'''
    def __init__(self):
        self.name = 'income'
        self.details = 'income_sub'
        self.name_cn = '进账金额'
        self.desc = '在指定日期范围内，每日新进账的订单（包括人机、VIP、TP、钻展、代运营，不管审核通过与否，排除友情赠送的）的金额之和'
        self.unit = '元'
        self.snapshot_order = 2
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        return SubscribeInterface.get_income(manager, psuser_id, date_obj)

    def snapshot(self, manager, psuser_id, date_obj):
        return

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None, **kwargs):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return round(sum([doc['pay'] for doc in sub_list]) / 100.0, 2)


class ValidIncome(MetricBase):
    '''有效进账金额'''
    def __init__(self):
        self.name = 'valid_income'
        self.details = 'valid_income_sub'
        self.name_cn = '有效进账金额'
        self.desc = '在指定日期范围内，每日新进账的订单（包括人机、VIP、TP、钻展、代运营，且审核通过的，排除友情赠送的）的金额之和'
        self.unit = '元'
        self.snapshot_order = 2
        self.detail_titles = [title for field, title in SubscribeInterface.SUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        return SubscribeInterface.get_valid_income(manager, psuser_id, date_obj)

    def snapshot(self, manager, psuser_id, date_obj):
        return

    def get_details(self, date_str, shop_id, nick, sub_id, amount, psuser_dict=None, **kwargs):
        return SubscribeInterface.get_detail_data(date_str, shop_id, nick, sub_id, amount, psuser_dict)

    def aggregate(self, sub_list):
        return round(sum([doc['pay'] for doc in sub_list]) / 100.0, 2)


class UnsubscribeApportion(MetricBase):
    '''退款分摊金额'''
    def __init__(self):
        self.name = 'unsub_apportion'
        self.details = 'unsub_apportion_list'
        self.name_cn = '退款分摊金额'
        self.desc = '在指定日期范围内，所有已录退款事件（排除友情赠送和积分兑换的）中你需要承担的分摊金额之和'
        self.unit = '元'
        self.snapshot_order = 2
        self.detail_titles = [title for field, title in EventInterface.UNSUBSCRIBE_FIELD_CHOICES]

    def fetch(self, manager, psuser_id, date_obj):
        return EventInterface.get_unsub_apportion(manager, psuser_id, date_obj)

    def snapshot(self, manager, psuser_id, date_obj):
        return

    def get_details(self, date_str, psuser_dict=None, **kwargs):
        return EventInterface.get_detail_unsub(date_str, psuser_dict, **kwargs)

    def aggregate(self, psuser_id, unsub_apportion_list):
        unsub_apportion = 0
        for doc in unsub_apportion_list:
            if psuser_id == doc['saler_id']:
                unsub_apportion += doc['saler_apportion']
            if psuser_id == doc['server_id']:
                unsub_apportion += doc['server_apportion']
        unsub_apportion = round(unsub_apportion / 100.0, 2)
        return unsub_apportion


class NetIncome(MetricBase):
    '''净进账金额'''
    def __init__(self):
        self.name = 'net_income'
        self.details = 'net_income_sub'
        self.name_cn = '净进账金额'
        self.desc = '在指定日期范围内，你的“有效进账金额”减去“退款分摊金额”的差值'
        self.unit = '元'
        self.snapshot_order = 2
        self.detail_titles = []

    def fetch(self, manager, psuser_id, date_obj):
        return SubscribeInterface.get_net_income(manager, psuser_id, date_obj)

    def snapshot(self, manager, psuser_id, date_obj):
        return

    def get_details(self, date_str, psuser_dict=None, **kwargs):
        return []

    def aggregate(self, psuser_id, detail_dict):
        valid_income_sub = detail_dict.get('valid_income', [])
        valid_income = ValidIncome().aggregate(valid_income_sub)
        unsub_apportion_list = detail_dict.get('unsub_apportion', [])
        unsub_apportion = UnsubscribeApportion().aggregate(psuser_id, unsub_apportion_list)
        return valid_income - unsub_apportion

