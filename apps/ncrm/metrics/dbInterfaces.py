# coding=UTF-8
import datetime
import re
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import date_2datetime
from apps.ncrm.metrics.models import mycust_coll
from apps.ncrm.models import event_coll, ar_coll, Subscribe, PSUser, CATEGORY_CHOICES


class MyCustomersInterface(object):
    '''mycust_coll 表的数据接口'''
    @classmethod
    def __load_data(cls, manager):
        '''加载数据'''
        if not hasattr(manager, '_raw_mycust_coll_data'):
            manager._raw_mycust_coll_data = list(mycust_coll.find({
                'date_str': {'$gte': (manager.start_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d'), '$lte': manager.end_date.strftime('%Y-%m-%d')},
                'psuser_id': {'$in': manager.psuser_id_list}
            }).sort('create_time', 1))
        return manager._raw_mycust_coll_data

    @classmethod
    def __handle_data(cls, manager):
        '''加工数据'''
        if not hasattr(manager, '_mycust_coll_data'):
            raw_mycust_coll_data = cls.__load_data(manager)
            _mycust_coll_data = {}
            for doc in raw_mycust_coll_data:
                doc['serving_sub_list'] = doc['rjjh_sub'] + doc['ztc_sub'] + doc['zz_sub'] + doc['dyy_sub']
                doc['shop_id_list'] = list(set([_doc['shop_id'] for _doc in doc['serving_sub_list']]))
                _mycust_coll_data.setdefault(doc['psuser_id'], {})[doc['date_str']] = doc
            manager._mycust_coll_data = _mycust_coll_data
        return manager._mycust_coll_data

    @classmethod
    def get_data(cls, manager, psuser_id, date_obj):
        '''获取数据'''
        mycust_coll_data = cls.__handle_data(manager)
        return mycust_coll_data.get(psuser_id, {}).get(date_obj.strftime('%Y-%m-%d'))

    @classmethod
    def store_data(cls, manager):
        '''存储数据'''
        try:
            doc_list = []
            for psuser_id, date_dict in manager.data_dict.items():
                date_obj = manager.start_date
                while date_obj <= manager.end_date:
                    doc = date_dict[date_obj]
                    doc_list.append({
                        'date_str': date_obj.strftime('%Y-%m-%d'),
                        'psuser_id': psuser_id,
                        'rjjh_sub': doc['rjjh_sub'],
                        'ztc_sub': doc['ztc_sub'],
                        'zz_sub': doc['zz_sub'],
                        'dyy_sub': doc['dyy_sub'],
                        'new_cust_sub': doc['new_cust_sub'],
                        'pause_sub': doc['pause_sub'],
                        'unsub_sub': doc['unsub_sub'],
                        'expire_sub': doc['expire_sub'],
                        'change_sub': doc['change_sub'],
                        'create_time': datetime.datetime.now(),
                    })
                    date_obj += datetime.timedelta(days=1)
            mycust_coll.remove({
                'date_str': {'$gte': manager.start_date.strftime('%Y-%m-%d'), '$lte': manager.end_date.strftime('%Y-%m-%d')},
                'psuser_id': {'$in': manager.psuser_id_list}
            }, multi=True)
            mycust_coll.insert(doc_list)
        except Exception, e:
            log.error('MyCustomersInterface.store_data error, e=%s' % e)

    @classmethod
    def get_new_cust_sub(cls, manager, psuser_id, date_obj):
        '''获取昨天没有，但今天新增的客户的对应订单'''
        new_cust_sub = manager.read_data(psuser_id, date_obj, 'new_cust_sub')
        if new_cust_sub is None:
            yest_cust = cls.get_data(manager, psuser_id, date_obj - datetime.timedelta(days=1))
            if yest_cust is None:
                yest_sub_list = SubscribeInterface.get_serving_sub_list(manager, psuser_id, date_obj - datetime.timedelta(days=1))
            else:
                yest_sub_list = yest_cust.get('serving_sub_list', [])
            yest_shop_id_list = list(set([doc['shop_id'] for doc in yest_sub_list]))

            today_cust = cls.get_data(manager, psuser_id, date_obj)
            if today_cust is None:
                today_sub_list = SubscribeInterface.get_serving_sub_list(manager, psuser_id, date_obj)
            else:
                today_sub_list = today_cust.get('serving_sub_list', [])

            new_cust_sub = [doc for doc in today_sub_list if doc['shop_id'] not in yest_shop_id_list]
            manager.feed_data(psuser_id, date_obj, {'new_cust_sub': new_cust_sub})
        return new_cust_sub

    @classmethod
    def get_lost_cust_sub(cls, manager, psuser_id, date_obj):
        '''获取昨天还在，但今天已经流失的客户的对应订单'''
        lost_cust_sub = manager.read_data(psuser_id, date_obj, 'lost_cust_sub')
        if lost_cust_sub is None:
            yest_cust = cls.get_data(manager, psuser_id, date_obj - datetime.timedelta(days=1))
            if yest_cust is None:
                yest_sub_list = SubscribeInterface.get_serving_sub_list(manager, psuser_id, date_obj - datetime.timedelta(days=1))
            else:
                yest_sub_list = yest_cust.get('serving_sub_list', [])

            today_cust = cls.get_data(manager, psuser_id, date_obj)
            if today_cust is None:
                today_sub_list = SubscribeInterface.get_serving_sub_list(manager, psuser_id, date_obj)
            else:
                today_sub_list = today_cust.get('serving_sub_list', [])
            today_sub_id_list = [doc['sub_id'] for doc in today_sub_list]
            # today_shop_id_list = list(set([doc['shop_id'] for doc in today_sub_list]))

            lost_cust_sub = [doc for doc in yest_sub_list if doc['sub_id'] not in today_sub_id_list]
            # lost_cust_sub = [doc for doc in yest_sub_list if doc['shop_id'] not in today_shop_id_list]
            manager.feed_data(psuser_id, date_obj, {'lost_cust_sub': lost_cust_sub})
        return lost_cust_sub


class AllocationRecordInterface(object):
    '''ar_coll 表的数据接口'''

    @classmethod
    def __load_allocation_record(cls, manager, psuser_id):
        '''加载订单分配记录'''
        _raw_allocation_record = getattr(manager, '_raw_allocation_record', {})
        if psuser_id not in _raw_allocation_record:
            _raw_allocation_record[psuser_id] = list(ar_coll.find({
                'create_time': {'$gte': date_2datetime(manager.start_date), '$lt': date_2datetime(manager.end_date + datetime.timedelta(days=1))},
                'org_id_list': re.compile('.*, %s, .*' % psuser_id),
                'new_id_list': {'$not': re.compile('.*, %s, .*' % psuser_id)}
            }, {'subscribe_id': True, 'create_time': True}))
            manager._raw_allocation_record = _raw_allocation_record
        return _raw_allocation_record[psuser_id]

    @classmethod
    def __handle_allocation_record(cls, manager, psuser_id):
        '''加工订单分配记录'''
        _allocation_record = getattr(manager, '_allocation_record', {})
        if psuser_id not in _allocation_record:
            raw_allocation_record = cls.__load_allocation_record(manager, psuser_id)
            result = {}
            for doc in raw_allocation_record:
                result.setdefault(doc['create_time'].date(), []).append(doc['subscribe_id'])
            _allocation_record[psuser_id] = result
            manager._allocation_record = _allocation_record
        return _allocation_record[psuser_id]

    @classmethod
    def get_change_sub_id_list(cls, manager, psuser_id, date_obj):
        '''获取转出(更换操作人)的订单ID列表'''
        allocation_record = cls.__handle_allocation_record(manager, psuser_id)
        return allocation_record.get(date_obj, [])

    @classmethod
    def get_change_sub_list(cls, manager, psuser_id, date_obj):
        '''获取转出(更换操作人)的订单'''
        change_sub = manager.read_data(psuser_id, date_obj, 'change_sub')
        if change_sub is None:
            change_sub_id_list = cls.get_change_sub_id_list(manager, psuser_id, date_obj)
            lost_cust_sub_list = MyCustomersInterface.get_lost_cust_sub(manager, psuser_id, date_obj)
            change_sub = [doc for doc in lost_cust_sub_list if doc['shop_id'] in change_sub_id_list]
            manager.feed_data(psuser_id, date_obj, {'change_sub': change_sub})
        return change_sub


class EventInterface(object):
    """event_coll 表的数据接口"""
    UNSUBSCRIBE_FIELD_CHOICES = [
        ('date_str', '统计日期'),
        ('create_time', '录入退款时间'),
        ('shop_id', '店铺ID'),
        ('nick', '店铺昵称'),
        ('event_id', '订单ID'),
        ('category', '业务类型'),
        ('refund', '退款金额(元)'),
        ('saler_id', '签单人'),
        ('saler_apportion', '签单人分摊'),
        ('server_id', '服务人'),
        ('server_apportion', '服务人分摊'),
    ]

    @classmethod
    def get_detail_unsub(cls, date_str, psuser_dict=None, **kwargs):
        """生成详细退款数据"""
        psuser_dict = psuser_dict or {}
        return [
            date_str,
            kwargs['create_time'][:19],
            kwargs['shop_id'],
            kwargs['nick'],
            kwargs['event_id'],
            dict(CATEGORY_CHOICES).get(kwargs['category'], '-'),
            round(kwargs['refund'] / 100.0, 2),
            psuser_dict.get(kwargs['saler_id'], kwargs['saler_id']),
            round(kwargs['saler_apportion'] / 100.0, 2),
            psuser_dict.get(kwargs['server_id'], kwargs['server_id']),
            round(kwargs['server_apportion'] / 100.0, 2),
        ]

    # ============================== 暂停事件 ==============================
    @classmethod
    def __load_pause_event(cls, manager):
        '''加载暂停事件'''
        if not hasattr(manager, '_raw_pause_event'):
            manager._raw_pause_event = list(event_coll.find({
                'type': 'pause',
                'create_time': {'$lt': date_2datetime(manager.end_date + datetime.timedelta(days=1))},
                '$or': [
                    {'proceed_date': {'$gte': date_2datetime(manager.start_date + datetime.timedelta(days=1))}},
                    {'proceed_date': {'$exists': False}}
                ]
            }, {'event_id': True, 'create_time': True, 'proceed_date': True}))
        return manager._raw_pause_event

    @classmethod
    def __handle_pause_event(cls, manager, date_obj):
        '''加工暂停事件'''
        _pause_subscribe = getattr(manager, '_pause_subscribe', {})
        if date_obj not in _pause_subscribe:
            raw_pause_event = cls.__load_pause_event(manager)
            result = []
            for doc in raw_pause_event:
                start_date = doc['create_time'].date()
                end_date = doc['proceed_date'].date() if 'proceed_date' in doc else manager.end_date + datetime.timedelta(days=1)
                if start_date <= date_obj < end_date:
                    result.append(doc['event_id'])
            _pause_subscribe[date_obj] = result
            manager._pause_subscribe = _pause_subscribe
        return _pause_subscribe[date_obj]

    @classmethod
    def get_pause_sub_id_list(cls, manager, date_obj):
        '''获取暂停的订单ID列表'''
        return cls.__handle_pause_event(manager, date_obj)

    @classmethod
    def get_pause_sub_list(cls, manager, psuser_id, date_obj):
        '''获取暂停的订单'''
        pause_sub = manager.read_data(psuser_id, date_obj, 'pause_sub')
        if pause_sub is None:
            pause_sub_id_list = cls.get_pause_sub_id_list(manager, date_obj)
            lost_cust_sub_list = MyCustomersInterface.get_lost_cust_sub(manager, psuser_id, date_obj)
            pause_sub = [doc for doc in lost_cust_sub_list if doc['sub_id'] in pause_sub_id_list]
            manager.feed_data(psuser_id, date_obj, {'pause_sub': pause_sub})
        return pause_sub

    # ============================== 退款事件 ==============================
    @classmethod
    def __load_unsub_event(cls, manager):
        '''加载退款事件'''
        if not hasattr(manager, '_raw_unsub_event'):
            manager._raw_unsub_event = list(event_coll.find({
                'type': 'unsubscribe',
                'create_time': {'$gte': date_2datetime(manager.start_date), '$lt': date_2datetime(manager.end_date + datetime.timedelta(days=1))},
                'refund_reason': {'$lt': 5},
            }, {'event_id': True, 'shop_id': True, 'nick': True, 'create_time': True, 'category': True, 'refund': True, 'saler_id': True, 'saler_apportion': True, 'server_id': True, 'server_apportion': True}))
        return manager._raw_unsub_event

    @classmethod
    def __handle_unsub_event(cls, manager):
        '''加工退款事件'''
        if not hasattr(manager, '_unsub_event'):
            raw_unsub_event = cls.__load_unsub_event(manager)
            _unsub_event = {}
            for doc in raw_unsub_event:
                _unsub_event.setdefault(doc['create_time'].date(), {}).setdefault(doc['server_id'], []).append(doc)
            manager._unsub_event = _unsub_event
        return manager._unsub_event

    @classmethod
    def get_unsub_sub_id_list(cls, manager, psuser_id, date_obj):
        '''获取退款的订单ID列表'''
        unsub_event = cls.__handle_unsub_event(manager)
        unsub_list = unsub_event.get(date_obj, {}).get(psuser_id, [])
        return [doc['event_id'] for doc in unsub_list]

    @classmethod
    def get_unsub_sub_list(cls, manager, psuser_id, date_obj):
        '''获取退款的订单'''
        unsub_sub = manager.read_data(psuser_id, date_obj, 'unsub_sub')
        if unsub_sub is None:
            unsub_sub_id_list = cls.get_unsub_sub_id_list(manager, psuser_id, date_obj)
            lost_cust_sub_list = MyCustomersInterface.get_lost_cust_sub(manager, psuser_id, date_obj)
            unsub_sub = [doc for doc in lost_cust_sub_list if doc['shop_id'] in unsub_sub_id_list]
            manager.feed_data(psuser_id, date_obj, {'unsub_sub': unsub_sub})
        return unsub_sub

    @classmethod
    def get_unsub_event(cls, manager, date_obj):
        '''获取退款事件列表'''
        unsub_event = cls.__handle_unsub_event(manager)
        temp_list = unsub_event.get(date_obj, {}).values()
        result = []
        for item in temp_list:
            result += item
        return result

    @classmethod
    def get_unsub_apportion_list(cls, manager, psuser_id, date_obj):
        '''获取当日退款分摊列表'''
        unsub_apportion_list = manager.read_data(psuser_id, date_obj, 'unsub_apportion_list')
        if unsub_apportion_list is None:
            unsub_event_list = cls.get_unsub_event(manager, date_obj)
            unsub_apportion_list = []
            for doc in unsub_event_list:
                if psuser_id == doc['saler_id'] or psuser_id == doc['server_id']:
                    unsub_apportion_list.append(doc)
            manager.feed_data(psuser_id, date_obj, {'unsub_apportion_list': unsub_apportion_list})
        return unsub_apportion_list

    @classmethod
    def get_unsub_apportion(cls, manager, psuser_id, date_obj):
        '''获取当日退款分摊金额'''
        unsub_apportion = manager.read_data(psuser_id, date_obj, 'unsub_apportion')
        if unsub_apportion is None:
            unsub_apportion_list = cls.get_unsub_apportion_list(manager, psuser_id, date_obj)
            unsub_apportion = 0
            for doc in unsub_apportion_list:
                if psuser_id == doc['saler_id']:
                    unsub_apportion += doc['saler_apportion']
                if psuser_id == doc['server_id']:
                    unsub_apportion += doc['server_apportion']
            unsub_apportion = round(unsub_apportion / 100.0, 2)
            manager.feed_data(psuser_id, date_obj, {'unsub_apportion': unsub_apportion})
        return unsub_apportion

    # ============================== 流失订单 ==============================
    @classmethod
    def get_expire_sub_list(cls, manager, psuser_id, date_obj):
        '''获取流失的订单'''
        expire_sub = manager.read_data(psuser_id, date_obj, 'expire_sub')
        if expire_sub is None:
            expire_sub = []
            lost_cust_sub_list = MyCustomersInterface.get_lost_cust_sub(manager, psuser_id, date_obj)
            if lost_cust_sub_list:
                pause_sub_list = cls.get_pause_sub_list(manager, psuser_id, date_obj)
                unsub_sub_list = cls.get_unsub_sub_list(manager, psuser_id, date_obj)
                change_sub_list = AllocationRecordInterface.get_change_sub_list(manager, psuser_id, date_obj)
                temp_sub_id_list = list(set([doc['sub_id'] for doc in pause_sub_list + unsub_sub_list + change_sub_list]))
                expire_sub = [doc for doc in lost_cust_sub_list if doc['sub_id'] not in temp_sub_id_list]
            manager.feed_data(psuser_id, date_obj, {'expire_sub': expire_sub})
        return expire_sub


class SubscribeInterface(object):
    """Subscribe 表的数据接口"""
    SUBSCRIBE_FIELD_CHOICES = [
        ('date_str', '统计日期'),
        ('create_time', '订购时间'),
        ('shop_id', '店铺ID'),
        ('nick', '店铺昵称'),
        ('id', '订单ID'),
        ('item_code', '应用码'),
        ('category', '业务类型'),
        ('cycle', '订购周期'),
        ('start_date', '开始日期'),
        ('end_date', '结束日期'),
        ('pay', '成交金额(元)'),
        ('amount', '当日服务金额(元)'),
        ('psuser', '签单人'),
        ('operater', '操作人'),
        ('consult', '客服'),
        ('pay_type', '付款方式'),
    ]

    @classmethod
    def get_detail_data(cls, date_str, shop_id, nick, sub_id, amount, psuser_dict=None):
        """生成详细数据"""
        sub_obj = Subscribe.objects.get(id=sub_id)
        psuser_dict = psuser_dict or {}
        return [
            date_str,
            sub_obj.create_time,
            shop_id,
            nick,
            sub_id,
            sub_obj.item_code,
            sub_obj.get_category_display(),
            sub_obj.cycle,
            sub_obj.start_date,
            sub_obj.end_date,
            round(sub_obj.pay / 100.0, 2),
            round(amount / 100.0, 2),
            psuser_dict.get(sub_obj.psuser_id, sub_obj.psuser_id),
            psuser_dict.get(sub_obj.operater_id, sub_obj.operater_id),
            psuser_dict.get(sub_obj.consult_id, sub_obj.consult_id),
            sub_obj.get_pay_type_display()
        ]

    # ============================== 服务订单 ==============================
    @classmethod
    def __load_operater_subscribe(cls, manager):
        '''加载服务订单'''
        if not hasattr(manager, '_raw_operater_subscribe'):
            manager._raw_operater_subscribe = list(Subscribe.objects.select_related('shop').filter(**{
                'operater_id__in': manager.psuser_id_list,
                'start_date__lte': manager.end_date,
                'end_date__gte': manager.start_date,  # **故意用 __gte ，为退款事件提供订单数据
                'category__in': ['ztc', 'vip', 'rjjh', 'zz', 'zx', 'dyy', 'seo', 'ztbd']
            }).exclude(biz_type=6).only('id', 'shop', 'operater', 'category', 'pay', 'start_date', 'end_date'))
        return manager._raw_operater_subscribe

    @classmethod
    def __handle_operater_subscribe(cls, manager):
        '''加工服务订单'''
        if not hasattr(manager, '_operater_subscribe'):
            raw_operater_subscribe = cls.__load_operater_subscribe(manager)
            _operater_subscribe = {}
            for obj in raw_operater_subscribe:
                _operater_subscribe.setdefault(obj.operater_id, []).append(obj)
            manager._operater_subscribe = _operater_subscribe
        return manager._operater_subscribe

    @classmethod
    def get_operater_subscribe(cls, manager, psuser_id):
        '''获取服务订单列表'''
        operater_subscribe = cls.__handle_operater_subscribe(manager)
        return operater_subscribe.get(psuser_id, [])

    @classmethod
    def get_serving_sub_dict(cls, manager, psuser_id, date_obj):
        '''获取当日服务中的订单'''
        serving_sub = manager.read_data(psuser_id, date_obj, 'serving_sub')
        if serving_sub is None:
            # 获取当天在服务日期内的订单
            sub_list = cls.get_operater_subscribe(manager, psuser_id)

            # 获取当天处于暂停状态的订单
            pause_sub_id_list = EventInterface.get_pause_sub_id_list(manager, date_obj)

            serving_sub = {}
            for obj in sub_list:
                if obj.id in pause_sub_id_list:
                    continue
                if obj.start_date <= date_obj < obj.end_date:
                    serving_sub.setdefault(obj.category, []).append({
                        'shop_id': obj.shop_id,
                        'nick': obj.shop.nick,
                        'sub_id': obj.id,
                        'amount': int(round(float(obj.serve_fee) / (obj.end_date - obj.start_date).days))
                    })
            manager.feed_data(psuser_id, date_obj, {'serving_sub': serving_sub})
        return serving_sub

    @classmethod
    def get_rjjh_sub_list(cls, manager, psuser_id, date_obj):
        '''获取服务中的人机订单'''
        rjjh_sub = manager.read_data(psuser_id, date_obj, 'rjjh_sub')
        if rjjh_sub is None:
            serving_sub_dict = cls.get_serving_sub_dict(manager, psuser_id, date_obj)
            rjjh_sub = serving_sub_dict.get('rjjh', [])
            manager.feed_data(psuser_id, date_obj, {'rjjh_sub': rjjh_sub})
        return rjjh_sub

    @classmethod
    def get_ztc_sub_list(cls, manager, psuser_id, date_obj):
        '''获取服务中的直通车托管订单（TP + VIP）'''
        ztc_sub = manager.read_data(psuser_id, date_obj, 'ztc_sub')
        if ztc_sub is None:
            serving_sub_dict = cls.get_serving_sub_dict(manager, psuser_id, date_obj)
            ztc_sub = serving_sub_dict.get('ztc', []) + serving_sub_dict.get('vip', [])
            manager.feed_data(psuser_id, date_obj, {'ztc_sub': ztc_sub})
        return ztc_sub

    @classmethod
    def get_zz_sub_list(cls, manager, psuser_id, date_obj):
        '''获取服务中的钻展订单'''
        zz_sub = manager.read_data(psuser_id, date_obj, 'zz_sub')
        if zz_sub is None:
            serving_sub_dict = cls.get_serving_sub_dict(manager, psuser_id, date_obj)
            zz_sub = serving_sub_dict.get('zz', [])
            manager.feed_data(psuser_id, date_obj, {'zz_sub': zz_sub})
        return zz_sub

    @classmethod
    def get_zx_sub_list(cls, manager, psuser_id, date_obj):
        '''获取服务中的店铺装修订单'''
        zx_sub = manager.read_data(psuser_id, date_obj, 'zx_sub')
        if zx_sub is None:
            serving_sub_dict = cls.get_serving_sub_dict(manager, psuser_id, date_obj)
            zx_sub = serving_sub_dict.get('zx', [])
            manager.feed_data(psuser_id, date_obj, {'zx_sub': zx_sub})
        return zx_sub

    @classmethod
    def get_dyy_sub_list(cls, manager, psuser_id, date_obj):
        '''获取服务中的代运营订单'''
        dyy_sub = manager.read_data(psuser_id, date_obj, 'dyy_sub')
        if dyy_sub is None:
            serving_sub_dict = cls.get_serving_sub_dict(manager, psuser_id, date_obj)
            dyy_sub = serving_sub_dict.get('dyy', [])
            manager.feed_data(psuser_id, date_obj, {'dyy_sub': dyy_sub})
        return dyy_sub

    @classmethod
    def get_seo_sub_list(cls, manager, psuser_id, date_obj):
        '''获取服务中的seo订单'''
        seo_sub = manager.read_data(psuser_id, date_obj, 'seo_sub')
        if seo_sub is None:
            serving_sub_dict = cls.get_serving_sub_dict(manager, psuser_id, date_obj)
            seo_sub = serving_sub_dict.get('seo', [])
            manager.feed_data(psuser_id, date_obj, {'seo_sub': seo_sub})
        return seo_sub

    @classmethod
    def get_serving_sub_list(cls, manager, psuser_id, date_obj):
        '''获取当日服务中的订单列表'''
        return cls.get_rjjh_sub_list(manager, psuser_id, date_obj) \
               + cls.get_ztc_sub_list(manager, psuser_id, date_obj) \
               + cls.get_zz_sub_list(manager, psuser_id, date_obj) \
               + cls.get_zx_sub_list(manager, psuser_id, date_obj) \
               + cls.get_dyy_sub_list(manager, psuser_id, date_obj) \
               + cls.get_seo_sub_list(manager, psuser_id, date_obj)

    # ============================== 进账订单 ==============================
    @classmethod
    def __load_psuser_subscribe(cls, manager):
        '''加载进账订单'''
        if not hasattr(manager, '_raw_psuser_subscribe'):
            manager._raw_psuser_subscribe = list(Subscribe.objects.select_related('shop').filter(**{
                'psuser_id__in': manager.psuser_id_list,
                'create_time__gte': date_2datetime(manager.start_date),
                'create_time__lt': date_2datetime(manager.end_date + datetime.timedelta(days=1)),
            }).exclude(biz_type=6).only('id', 'shop', 'psuser', 'category', 'pay', 'create_time', 'start_date', 'end_date', 'approval_status'))
        return manager._raw_psuser_subscribe

    @classmethod
    def __handle_psuser_subscribe(cls, manager):
        '''加工进账订单'''
        if not hasattr(manager, '_psuser_subscribe'):
            raw_psuser_subscribe = cls.__load_psuser_subscribe(manager)
            _psuser_subscribe = {}
            for obj in raw_psuser_subscribe:
                _psuser_subscribe.setdefault(obj.psuser_id, {}).setdefault(obj.create_time.date(), []).append(obj)
            manager._psuser_subscribe = _psuser_subscribe
        return manager._psuser_subscribe

    @classmethod
    def get_psuser_subscribe(cls, manager, psuser_id, date_obj):
        '''获取进账订单'''
        psuser_subscribe = cls.__handle_psuser_subscribe(manager)
        return psuser_subscribe.get(psuser_id, {}).get(date_obj, [])

    @classmethod
    def get_income_sub_list(cls, manager, psuser_id, date_obj):
        '''获取当日进账的订单'''
        income_sub = manager.read_data(psuser_id, date_obj, 'income_sub')
        if income_sub is None:
            sub_list = cls.get_psuser_subscribe(manager, psuser_id, date_obj)
            income_sub = [{
                'shop_id': obj.shop_id,
                'nick': obj.shop.nick,
                'sub_id': obj.id,
                'amount': int(round(float(obj.serve_fee) / (obj.end_date - obj.start_date).days)) if obj.end_date > obj.start_date else 0,
                'pay': obj.pay,
                'category': obj.category,
                'approval_status': obj.approval_status
            } for obj in sub_list if obj.end_date >= obj.start_date]
            manager.feed_data(psuser_id, date_obj, {'income_sub': income_sub})
        return income_sub

    @classmethod
    def get_income(cls, manager, psuser_id, date_obj):
        '''获取当日进账金额'''
        income = manager.read_data(psuser_id, date_obj, 'income')
        if income is None:
            sub_list = cls.get_income_sub_list(manager, psuser_id, date_obj)
            income = round(sum([obj['pay'] for obj in sub_list]) / 100.0, 2)
            manager.feed_data(psuser_id, date_obj, {'income': income})
        return income

    @classmethod
    def get_valid_income_sub_list(cls, manager, psuser_id, date_obj):
        '''获取当日有效进账的订单'''
        valid_income_sub = manager.read_data(psuser_id, date_obj, 'valid_income_sub')
        if valid_income_sub is None:
            sub_list = cls.get_psuser_subscribe(manager, psuser_id, date_obj)
            valid_income_sub = [{
                'shop_id': obj.shop_id,
                'nick': obj.shop.nick,
                'sub_id': obj.id,
                'amount': int(round(float(obj.serve_fee) / (obj.end_date - obj.start_date).days)) if obj.end_date > obj.start_date else 0,
                'pay': obj.pay,
                'category': obj.category
            } for obj in sub_list if obj.approval_status == 1 and obj.end_date >= obj.start_date]
            manager.feed_data(psuser_id, date_obj, {'valid_income_sub': valid_income_sub})
        return valid_income_sub

    @classmethod
    def get_valid_income(cls, manager, psuser_id, date_obj):
        '''获取当日有效进账金额'''
        valid_income = manager.read_data(psuser_id, date_obj, 'valid_income')
        if valid_income is None:
            sub_list = cls.get_valid_income_sub_list(manager, psuser_id, date_obj)
            valid_income = round(sum([obj['pay'] for obj in sub_list]) / 100.0, 2)
            manager.feed_data(psuser_id, date_obj, {'valid_income': valid_income})
        return valid_income

    @classmethod
    def get_net_income_sub_list(cls, manager, psuser_id, date_obj):
        '''获取当日净进账明细'''
        net_income_sub = manager.read_data(psuser_id, date_obj, 'net_income_sub')
        if net_income_sub is None:
            valid_income_sub = cls.get_valid_income_sub_list(manager, psuser_id, date_obj)
            unsub_apportion_list = EventInterface.get_unsub_apportion_list(manager, psuser_id, date_obj)
            # net_income_sub = valid_income_sub + unsub_apportion_list
            net_income_sub = {'valid_income': valid_income_sub, 'unsub_apportion': unsub_apportion_list}
            manager.feed_data(psuser_id, date_obj, {'net_income_sub': net_income_sub})
        return net_income_sub

    @classmethod
    def get_net_income(cls, manager, psuser_id, date_obj):
        '''获取当日净进账金额'''
        net_income = manager.read_data(psuser_id, date_obj, 'net_income')
        if net_income is None:
            cls.get_net_income_sub_list(manager, psuser_id, date_obj)
            valid_income = cls.get_valid_income(manager, psuser_id, date_obj)
            unsub_apportion = EventInterface.get_unsub_apportion(manager, psuser_id, date_obj)
            net_income = valid_income - unsub_apportion
            manager.feed_data(psuser_id, date_obj, {'net_income': net_income})
        return net_income

    # ============================== 续签订单 ==============================
    HOLD_DAYS = 30  # 流失 HOLD_DAYS 天内为保护期

    @classmethod
    def __load_prev_subscribe(cls, manager):
        '''加载客户流失保护期内的订单'''
        if not hasattr(manager, '_raw_prev_subscribe'):
            raw_psuser_subscribe = cls.__load_psuser_subscribe(manager)
            shop_id_list = list(set([obj.shop_id for obj in raw_psuser_subscribe]))
            manager._raw_prev_subscribe = list(Subscribe.objects.filter(**{
                'shop_id__in': shop_id_list,
                'create_time__lt': date_2datetime(manager.end_date + datetime.timedelta(days=1)),
                'end_date__gt': manager.start_date - datetime.timedelta(days=cls.HOLD_DAYS),
                'category__in': ['ztc', 'vip', 'rjjh', 'zz', 'dyy', 'ztbd']
            }).exclude(biz_type=6).only('id', 'shop', 'category', 'create_time', 'end_date').order_by('end_date'))
        return manager._raw_prev_subscribe

    @classmethod
    def __handle_prev_subscribe(cls, manager):
        '''加工客户流失保护期内的订单'''
        if not hasattr(manager, '_prev_subscribe'):
            raw_prev_subscribe = cls.__load_prev_subscribe(manager)
            _prev_subscribe = {}
            for obj in raw_prev_subscribe:
                # vip 和 ztc 视为一类
                temp_category = obj.category
                if temp_category == 'vip':
                    temp_category = 'ztc'
                _prev_subscribe.setdefault(obj.shop_id, {}).setdefault(temp_category, []).append(obj)
            manager._prev_subscribe = _prev_subscribe
        return manager._prev_subscribe

    @classmethod
    def get_prev_subscribe(cls, manager, shop_id, category):
        '''获取客户流失保护期内的订单'''
        prev_subscribe = cls.__handle_prev_subscribe(manager)
        return prev_subscribe.get(shop_id, {}).get(category, [])

    @classmethod
    def get_renew_sub_list(cls, manager, psuser_id, date_obj):
        '''获取当日续签的订单（流失保护期内再次续签是有效的）'''
        renew_sub = manager.read_data(psuser_id, date_obj, 'renew_sub')
        if renew_sub is None:
            # 获取当日自己签的订单
            sub_list = cls.get_psuser_subscribe(manager, psuser_id, date_obj)

            renew_sub = []
            for obj in sub_list:
                # 获取客户流失保护期内的订单
                temp_category = obj.category
                if temp_category == 'vip':
                    temp_category = 'ztc'
                prev_sub_list = cls.get_prev_subscribe(manager, obj.shop_id, temp_category)
                for prev_obj in prev_sub_list:
                    if (date_obj - prev_obj.end_date).days < cls.HOLD_DAYS and prev_obj.create_time < obj.create_time:
                        serve_days = (obj.end_date - obj.start_date).days
                        renew_sub.append({
                            'shop_id': obj.shop_id,
                            'nick': obj.shop.nick,
                            'sub_id': obj.id,
                            'amount': int(round(float(obj.serve_fee) / serve_days)) if serve_days > 0 else 0
                        })
                        break
            manager.feed_data(psuser_id, date_obj, {'renew_sub': renew_sub})
        return renew_sub
















