# coding=UTF-8

'''
Created on 2015-12-30

@author: YRK
'''
import collections
import json
import datetime
import itertools

from django.db.models import Q, Sum, Max, Min
from apps.ncrm.models import Customer
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apps.common.utils.utils_datetime import date_2datetime
from apps.ncrm.models import PSUser, Subscribe, Login, Comment, Contact, Unsubscribe, ReIntro, event_coll
from apps.subway.models_account import Account
from apps.mnt.models_monitor import mcs_coll

from .store import adpater

class LoadFactory(object):

    @classmethod
    def _serving_orders(cls, xfgroup, start_date, end_date, result_mapping):
        sub_list = Subscribe.objects.values('id', 'shop_id', 'start_date', 'end_date') \
            .filter(Q(start_date__lte = start_date, end_date__gte = start_date)
                    | Q(start_date__lte = end_date, end_date__gte = end_date)) \
            .filter(consult_xfgroup = xfgroup, pay__gt = 0) \
            .order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            for cur_date in result_mapping:
                if subscribe.start_date <= cur_date < subscribe.end_date:
                    result_mapping[cur_date].append(subscribe)
        return result_mapping

    @classmethod
    def _active_customers(cls, xfgroup, start_date, end_date, result_mapping):
        # 托管计划日花费之和
        mcs_list = list(mcs_coll.find({
            'rpt_date': {
                '$gte': date_2datetime(start_date),
                '$lt': date_2datetime(end_date + datetime.timedelta(days = 1))
                },
            'xfgroup_id': xfgroup.id,
            'category': 'kcjl'}
            ))
        shop_cost_dict = {} # {date:{shop_id:cost, ...}, ...}
        for mcs in mcs_list:
            temp_dict = shop_cost_dict.setdefault(mcs['rpt_date'].date(), {})
            temp_dict.setdefault(mcs['shop_id'], 0)
            temp_dict[mcs['shop_id']] += mcs['cost']

        for dt, temp_dict in shop_cost_dict.items():
            for shop_id, cost in temp_dict.items():
                if cost >= 5000: # 托管计划日花费之和大于等于50元
                    result_mapping[dt].append(DictWrapper({'shop_id': shop_id, 'cost': cost}))
        return result_mapping

    @classmethod
    def _user_cycle_increment(cls, xfgroup, start_date, end_date, result_mapping):
        def check_mark(subscribe):
            total_days = (subscribe.end_date - subscribe.start_date).days
            cycle = int(round(total_days / 30.0))
            if cycle >= 12:
                return 4
            elif cycle >= 6:
                return 2
            elif cycle >= 3:
                return 1
            return 0

        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        sub_list = Subscribe.objects.values('id', 'shop_id', 'start_date', 'end_date', 'create_time')\
            .exclude(Q(biz_type = 6) | Q(category = 'qn')) \
            .filter(create_time__gte = start_time, create_time__lte = end_time) \
            .filter(xfgroup = xfgroup, pay__gt = 0) \
            .order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            mark = check_mark(subscribe)
            if mark:
                entity = DictWrapper({'id':subscribe.id, 'shop_id':subscribe.shop_id, 'mark':mark})
                result_mapping[subscribe.create_time.date()].append(entity)

        return result_mapping

    @classmethod
    def _pay_subscribe(cls, xfgroup, start_date, end_date, result_mapping):
        def check_cycle(subscribe):
            total_days = (subscribe.end_date - subscribe.start_date).days
            cycle = int(round(total_days / 30.0))
            if cycle == 0:
                return 0
            if subscribe.pay / cycle < 3000:
                return 0
            return cycle

        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        sub_list = Subscribe.objects.values('id', 'shop_id', 'start_date', 'end_date', 'create_time', 'pay') \
            .exclude(Q(biz_type = 6) | (Q(biz_type = 3) & Q(category__in = ['rjjh', 'vip']))) \
            .filter(pay_type = 1, category__in = ['rjjh', 'vip', 'kcjl']) \
            .filter(create_time__gte = start_time, create_time__lte = end_time) \
            .filter(xfgroup = xfgroup, approval_status = 1, pay__gte = 3000) \
            .order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            cycle = check_cycle(subscribe)
            if cycle:
                entity = DictWrapper({'id': subscribe.id, 'shop_id': subscribe.shop_id, 'cycle': cycle})
                result_mapping[subscribe.create_time.date()].append(entity)

        return result_mapping

    @classmethod
    def _monthly_pay_subscribe(cls, xfgroup, start_date, end_date, result_mapping):
        def get_monthly_pay(subscribe):
            total_days = (subscribe.end_date - subscribe.start_date).days
            cycle = int(round(total_days / 30.0))
            if cycle == 0:
                return 0
            else:
                return subscribe.pay / cycle

        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        sub_list = Subscribe.objects.values('id', 'shop_id', 'start_date', 'end_date', 'create_time', 'pay') \
            .exclude(Q(biz_type=6) | (Q(biz_type=3) & Q(category__in=['rjjh', 'vip']))) \
            .filter(pay_type=1, category__in=['rjjh', 'vip', 'kcjl']) \
            .filter(create_time__gte=start_time, create_time__lte=end_time) \
            .filter(xfgroup=xfgroup, approval_status=1) \
            .order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            monthly_pay = get_monthly_pay(subscribe)
            if monthly_pay >= 3000:
                entity = DictWrapper({'id': subscribe.id, 'shop_id': subscribe.shop_id, 'monthly_pay': monthly_pay})
                result_mapping[subscribe.create_time.date()].append(entity)

        return result_mapping

    @classmethod
    def _free_pay_subscribe(cls, xfgroup, start_date, end_date, result_mapping):
        def check_cycle(subscribe):
            total_days = (subscribe.end_date - subscribe.start_date).days
            cycle = int(round(total_days / 30.0))
            if cycle == 0:
                return 0
            if subscribe.biz_type < 6 and subscribe.pay / cycle >= 3000:
                return 0
            return cycle

        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        sub_list = Subscribe.objects.values('id', 'shop_id', 'start_date', 'end_date', 'create_time', 'pay', 'biz_type') \
            .exclude(biz_type = 3) \
            .filter(pay_type = 1, category__in = ['rjjh', 'vip', 'kcjl']) \
            .filter(create_time__gte = start_time, create_time__lte = end_time) \
            .filter(xfgroup = xfgroup, approval_status = 1, pay__gt = 0) \
            .order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            cycle = check_cycle(subscribe)
            if cycle:
                entity = DictWrapper({'id':subscribe.id, 'shop_id':subscribe.shop_id, 'cycle':cycle})
                result_mapping[subscribe.create_time.date()].append(entity)

        return result_mapping

    @classmethod
    def _unknown_orders(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        sub_list = Subscribe.objects.values('id', 'shop_id', 'create_time', 'biz_type') \
            .filter(xfgroup = xfgroup) \
            .filter(biz_type = 6, create_time__gte = start_time, create_time__lte = end_time) \
            .order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            result_mapping[subscribe.create_time.date()].append(subscribe)
        return result_mapping

    @classmethod
    def _renew_orders(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        sub_list = Subscribe.objects.values('id', 'shop_id', 'create_time', 'pay') \
            .filter(create_time__gte = start_time, create_time__lte = end_time) \
            .filter(xfgroup = xfgroup).exclude(biz_type = 6).order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            result_mapping[subscribe.create_time.date()].append(subscribe)
        return result_mapping

    @classmethod
    def _real_renew_orders(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        sub_list = Subscribe.objects.values('id', 'shop_id', 'create_time', 'pay') \
            .filter(xfgroup = xfgroup) \
            .filter(create_time__gte = start_time, create_time__lte = end_time, approval_status = 1) \
            .exclude(biz_type = 6) \
            .order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            result_mapping[subscribe.create_time.date()].append(subscribe)
        return result_mapping

    @classmethod
    def _expiring_renew_subscribe(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        start_month_1st = datetime.date(start_time.year, start_time.month, 1)
        if end_time.month == 12:
            end_month_1st = datetime.date(end_time.year + 1, 1, 1)
        else:
            end_month_1st = datetime.date(end_time.year, end_time.month + 1, 1)
        expiring_sub_list = Subscribe.objects.only('id', 'shop_id', 'end_date') \
            .filter(consult_xfgroup=xfgroup) \
            .filter(end_date__gte=start_month_1st, end_date__lt=end_month_1st)\
            .exclude(biz_type=6) \
            .order_by('-end_date')
        expiring_sub_dict = {sub.shop_id: sub for sub in expiring_sub_list}
        renew_sub_list = Subscribe.objects.values('id', 'shop_id', 'create_time') \
            .filter(xfgroup=xfgroup) \
            .filter(create_time__gte=start_time, create_time__lte=end_time) \
            .exclude(biz_type=6)
        for sub in renew_sub_list:
            sub = DictWrapper(sub)
            if sub.shop_id in expiring_sub_dict:
                expiring_sub = expiring_sub_dict[sub.shop_id]
                if expiring_sub.id != sub.id and expiring_sub.end_date.month == sub.create_time.month:
                    result_mapping[sub.create_time.date()].append(sub)
        return result_mapping

    @classmethod
    def _expire_orders(cls, xfgroup, start_date, end_date, result_mapping):
        sub_list = Subscribe.objects.values('id', 'shop_id', 'end_date') \
            .filter(consult_xfgroup = xfgroup, pay__gt = 0) \
            .filter(end_date__gte = start_date, end_date__lte = end_date) \
            .order_by('-create_time')
        for subscribe in sub_list:
            subscribe = DictWrapper(subscribe)
            result_mapping[subscribe.end_date].append(subscribe)
        return result_mapping

    @classmethod
    def _unsubscribes(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        unsub_cursor = event_coll.find(
            {
                'type': 'unsubscribe',
                'refund_date': {'$gte': start_time, '$lte': end_time},
                '$or': [
                    {'saler_xfgroup_id': xfgroup.id, 'saler_apportion': {'$gt': 0}},
                    {'server_xfgroup_id': xfgroup.id, 'server_apportion': {'$gt': 0}}
                    ],
                'refund_reason': {'$lt': 5},
                # 'refund_type':{'$lt':3}
            },
            {'shop_id': 1, 'refund_date': 1, 'saler_xfgroup_id': 1, 'server_xfgroup_id': 1, 'saler_apportion': 1, 'server_apportion': 1}
            )
        for unsub in unsub_cursor:
            apportion = 0
            if 'saler_xfgroup_id' in unsub and xfgroup.id == unsub['saler_xfgroup_id']:
                apportion += unsub.get('saler_apportion', 0)
            if 'server_xfgroup_id' in unsub and xfgroup.id == unsub['server_xfgroup_id']:
                apportion += unsub.get('server_apportion', 0)
            result_mapping[unsub['refund_date'].date()].append(DictWrapper({
                '_id':unsub['_id'],
                'shop_id':unsub['shop_id'],
                'apportion':apportion
            }))
        return result_mapping

    @classmethod
    def _market_unsubscribes(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        unsub_cursor = event_coll.find(
            {
                'type': 'unsubscribe',
                'refund_date': {'$gte': start_time, '$lte': end_time},
                '$or': [
                    {'saler_xfgroup_id': None},
                    {'saler_xfgroup_id': {'$exists': False}}
                    ],
                'server_xfgroup_id': xfgroup.id,
                'saler_apportion': {'$gt': 0},
                'refund_reason': {'$lt': 5},
            },
            {'shop_id': 1, 'refund_date': 1, 'saler_apportion': 1}
            )
        for unsub in unsub_cursor:
            result_mapping[unsub['refund_date'].date()].append(DictWrapper({
                '_id':unsub['_id'],
                'shop_id':unsub['shop_id'],
                'apportion':unsub.get('saler_apportion', 0)
            }))
        return result_mapping

    @classmethod
    def _unsubscribes_apportion(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        unsub_cursor = event_coll.find(
            {
                'type': 'unsubscribe',
                'refund_date': {'$gte': start_time, '$lte': end_time},
                '$or': [{'saler_xfgroup_id': xfgroup.id}, {'server_xfgroup_id': xfgroup.id}, {'xfgroup_id': xfgroup.id}],
                'refund_reason':{'$lt':5},
                # 'refund_type':{'$lt':3}
            },
            {'shop_id': 1, 'xfgroup_id': 1, 'refund_date': 1, 'saler_xfgroup_id':1, 'server_xfgroup_id':1, 'saler_apportion': 1, 'server_apportion':1}
            )
        for unsub in unsub_cursor:
            apportion = 0
            if 'xfgroup_id' in unsub and xfgroup.id == unsub['xfgroup_id']:
                apportion += 3
            if 'saler_xfgroup_id' in unsub and unsub['saler_xfgroup_id']:
                if xfgroup.id == unsub['saler_xfgroup_id']:
                    apportion += 7
            elif xfgroup.id == unsub['server_xfgroup_id']:
                apportion += 7
            result_mapping[unsub['refund_date'].date()].append(DictWrapper({
                '_id':unsub['_id'],
                'shop_id':unsub['shop_id'],
                'apportion':apportion
            }))
        return result_mapping

    @classmethod
    def _performance_unsubscribes(cls, xfgroup, start_date, end_date, result_mapping):
        # 被废弃，如使用，需整改
        return result_mapping

    @classmethod
    def _lost_coustomers(cls, xfgroup, start_date, end_date, result_mapping, lost_days_limt = 1):
        # 被废弃，如使用，需整改

        # result_mapping = cls._expire_orders(psuser, start_date, end_date, result_mapping)
        # expire_customer_mapping = {order.shop_id:None for order_list in result_mapping.values()\
        #                             for order in order_list}
        # for subscribe in Subscribe.objects.values('shop_id')\
        #             .filter(shop_id__in = expire_customer_mapping.keys())\
        #                 .annotate(expire_date = Max('end_date')):
        #     subscribe = DictWrapper(subscribe)
        #     expire_customer_mapping[subscribe.shop_id] = subscribe.expire_date

        # for cur_date, order_list in result_mapping.iteritems():
        #     lost_user = set()
        #     for order in order_list:
        #         max_date = expire_customer_mapping[order.shop_id]
        #         if max_date is not None and\
        #                  max_date <= order.end_date + datetime.timedelta(days = lost_days_limt):
        #             lost_user.add(order.shop_id)
        #     result_mapping[cur_date] = list(lost_user)
        return result_mapping

    @classmethod
    def _new_orders(cls, xfgroup, start_date, end_date, result_mapping):
        # 被废弃，如使用，需整改

        # start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        # end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        # subscribe_mapping = {}
        # for subscribe in Subscribe.objects.values('id', 'shop_id', 'create_time')\
        #             .filter(create_time__gte = start_time, create_time__lte = end_time)\
        #                 .filter(consult = psuser) \
        #                     .filter(pay__gt = 0) \
        #                         .order_by('-create_time'):
        #     subscribe = DictWrapper(subscribe)
        #     subscribe_mapping.setdefault(subscribe.shop_id, []).append(subscribe)

        # shop_id_list = subscribe_mapping.keys()
        # for subscribe_info in Subscribe.objects.values('shop_id')\
        #     .filter(shop_id__in = shop_id_list)\
        #         .filter(create_time__lt = start_time)\
        #             .filter(pay__gt = 0):
        #     shop_id = subscribe_info['shop_id']
        #     if shop_id in subscribe_mapping:
        #         subscribe_mapping.pop(shop_id)

        # for subscribe_list in subscribe_mapping.values():
        #     for subscribe in subscribe_list:
        #         result_mapping[subscribe.create_time.date()].append(subscribe)

        return result_mapping

    @classmethod
    def _valid_contacts(cls, xfgroup, start_date, end_date, result_mapping):
        # 被废弃，如使用，需整改

        # start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        # end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        # for contact in event_coll.find({'type':'contact', 'psuser_id':psuser.id, 'visible':1, \
        #          'create_time':{'$gte':start_time, '$lte':end_time}}, {'shop_id':1, 'create_time':1}):
        #     contact = DictWrapper(contact)
        #     result_mapping[contact.create_time.date()].append(contact)
        return result_mapping

    @classmethod
    def _reintros(cls, psuser, start_date, end_date, result_mapping):
        # 被废弃，如使用，需整改

        # start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        # end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        # for reintro in event_coll.find({'type':'reintro', 'psuser_id':psuser.id, \
        #          'create_time':{'$gte':start_time, '$lte':end_time}}, {'shop_id':1, 'create_time':1}):
        #     reintro = DictWrapper(reintro)
        #     result_mapping[reintro.create_time.date()].append(reintro)
        return result_mapping

    @classmethod
    def _good_comments(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        comment_cur = event_coll.find(
            {
                'type': 'comment',
                'duty_xfgroup_id': xfgroup.id,
                'comment_type': {'$in': [110, 120, 301, 305]},
                'create_time': {'$gte': start_time, '$lte': end_time},
                'article_code': 'ts-25811'
            },
            {'shop_id': 1, 'comment_type': 1, 'create_time': 1}
            )
        for comment in comment_cur:
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def _new_good_comments(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        comment_cur = event_coll.find(
            {
                'type': 'comment', 'duty_xfgroup_id': xfgroup.id,
                'comment_type': {'$in': [110, 301, 305]},
                'create_time': {'$gte': start_time, '$lte': end_time},
                'article_code': 'ts-25811'
            },
            {'shop_id': 1, 'comment_type': 1, 'create_time': 1}
            )
        for comment in comment_cur:
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def _top_good_comments(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        comment_cur = event_coll.find(
            {
                'type': 'comment',
                'duty_xfgroup_id': xfgroup.id,
                'comment_type': 120,
                'article_code': 'ts-25811',
                'create_time': {'$gte': start_time, '$lte': end_time},
            },
            {'shop_id':1, 'comment_type':1, 'create_time':1}
            )
        for comment in comment_cur:
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def _bad_comments(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        comment_cur = event_coll.find(
            {
                'type': 'comment',
                'duty_xfgroup_id': xfgroup.id,
                'comment_type': {'$in': [200, 302, 303, 304]},
                'current_version': 'kcjl',
                'article_code': 'ts-25811',
                'create_time': {'$gte': start_time, '$lte': end_time}
            },
            {'shop_id':1, 'comment_type':1, 'create_time':1}
            )
        for comment in comment_cur:
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def _change_comments(cls, xfgroup, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        comment_cur = event_coll.find(
            {
                'type': 'comment',
                'xfgroup_id': xfgroup.id,
                'comment_type': {'$in': [301, 302, 303, 304, 305]},
                'create_time': {'$gte': start_time, '$lte': end_time}
            },
            {'shop_id': 1, 'comment_type': 1, 'create_time': 1}
            )
        for comment in comment_cur:
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def load_unsubscribe(cls, xfgroup, start_date, end_date, result_mapping):
        return []
        # shop_id_list = customer_mapping.keys()

        # unsubscribe_mapping = {}
        # for unsubscribe in event_coll.find({'type':'unsubscribe', 'shop_id':{'$in':shop_id_list}}, \
        #                                     {'shop_id':1, 'event_id':1, 'refund':1}):
        #     unsubscribe = DictWrapper(unsubscribe)
        #     unsubscribe_mapping = unsubscribe_mapping.setdefault(unsubscribe.shop_id, {})
        #     unsubscribe_mapping[unsubscribe.event_id] = unsubscribe

        # # for unsubscribe in Unsubscribe.objects.values('shop_id', 'event_id', 'refund')\
        # #         .filter(shop_id__in = shop_id_list).order_by('create_time'):
        # #     unsubscribe = DictWrapper(unsubscribe)
        # #     unsubscribe_mapping = unsubscribe_mapping.setdefault(unsubscribe.shop_id, {})
        # #     unsubscribe_mapping[unsubscribe.event_id] = unsubscribe

        # for shop_id, cust in customer_mapping.iteritems():
        #     cust._unorder_mapping = unsubscribe_mapping.get(shop_id, {})
        # return customer_mapping

    @classmethod
    def load_monitor_Event(cls, xfgroup, start_date, end_date, result_mapping):
        return []

    @classmethod
    def load_account_report(cls, xfgroup, start_date, end_date, result_mapping):
        return []

class Loader(object):

    def __init__(self, xfgroups, start_time, end_time):
        self.xfgroups = xfgroups
        self.xfgroup_id_list = [xfgroup.id for xfgroup in xfgroups]
        self.start_time = start_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        self.end_time = end_time.replace(hour = 23, minute = 59, second = 59, microsecond = 59)
        self.start_date = self.start_time.date()
        self.end_date = self.end_time.date()

        self.adpater = adpater

    def calc_lost_timescope(self, indicatore_data):
        date_set = set(entify.result_date for entify in indicatore_data)
        size = (self.end_date - self.start_date).days

        calc_start_date = None
        for index in xrange(size + 1):
            temp_date = self.start_date + datetime.timedelta(days = index)
            if temp_date not in date_set:
                calc_start_date = temp_date
                break

        start_date = self.end_date + datetime.timedelta(days = 1) if calc_start_date is None else calc_start_date
        return (start_date, self.end_date)

    def clear_indicatore_bydate(self, indicatore_data, start_date, end_date):
        start_index = len(indicatore_data) - 1
        total_days = (end_date - start_date).days
        end_index = start_index - total_days if start_index - total_days > 0 else -1
        for index in xrange(start_index, end_index, -1):
            entity = indicatore_data[index]
            if start_date <= entity.result_date:
                indicatore_data.remove(entity)
        return indicatore_data

    def hung_indicatore_sdata_byuser(self, xfgroup, indicatore, start_date, end_date):
        attr_list = []
        total_days = (end_date - start_date).days

        if not hasattr(xfgroup, '_load_data'):
            xfgroup._load_data = {}

        for load_func in indicatore.load_func:
            attr = load_func.__name__
            if callable(load_func) and attr not in xfgroup._load_data:
                result_mapping = {start_date + datetime.timedelta(days = index):[]
                                  for index in xrange(total_days + 1)}
                xfgroup._load_data[attr] = load_func(xfgroup, start_date, end_date, result_mapping)
            attr_list.append(attr)

        return attr_list, xfgroup

    def serialize_indicatore_data(self, indicatore, xfgroup, calc_args, start_date, end_date):
        total_days = (end_date - start_date).days
        indicatore_data = []
        for index in xrange(total_days):
            cur_date = start_date + datetime.timedelta(days = index)
            value_list = indicatore.calc_func(cur_date, *calc_args)
            entity = self.adpater.save(xfgroup, cur_date, indicatore, value_list)
            indicatore_data.append(entity)
        return indicatore_data

    def loading(self, indicators, is_force = False):
        staff_mapping = self.adpater.filter(self.xfgroups, self.start_time.date(), self.end_time.date(), indicators)
        today = datetime.date.today()
        limit_date = today
        for xfgroup in self.xfgroups:
            user_data = staff_mapping.setdefault(xfgroup, {})
            for indicatore in indicators:
                indicatore_data = user_data.setdefault(indicatore, [])

                if is_force:
                    start_date, end_date = (self.start_date, self.end_date)
                    end_date = limit_date if end_date > limit_date else end_date
                    is_real_time = today == end_date

                    attr_list, xfgroup = self.hung_indicatore_sdata_byuser(xfgroup, indicatore, start_date, end_date)
                    indicatore_data = self.clear_indicatore_bydate(indicatore_data, start_date, end_date)
                    calc_args = [xfgroup._load_data[attr] for attr in attr_list]
                    update_indicatore_data = self.serialize_indicatore_data(indicatore, xfgroup, calc_args, start_date, end_date)
                    indicatore_data.extend(update_indicatore_data)

                    if is_real_time:
                        value_list = indicatore.calc_func(today, *[xfgroup._load_data[attr] for attr in attr_list])
                        entity = DictWrapper({
                            'xfgroup_id': xfgroup.id,
                            'identify': indicatore.name,
                            'data_json': json.dumps(value_list),
                            'result_date': limit_date
                            })
                        indicatore_data.append(entity)
                    else:
                        delay_date = end_date + datetime.timedelta(days = 1)
                        update_indicatore_data = self.serialize_indicatore_data(indicatore, xfgroup, calc_args, end_date, delay_date)
                        indicatore_data.extend(update_indicatore_data)
                else:
                    start_date, end_date = self.calc_lost_timescope(indicatore_data)
                    end_date = limit_date if end_date > limit_date else end_date
                    is_real_time = today == end_date

                    if is_real_time:
                        attr_list, xfgroup = self.hung_indicatore_sdata_byuser(xfgroup, indicatore, start_date, end_date)

                        if start_date < end_date:
                            indicatore_data = self.clear_indicatore_bydate(indicatore_data, start_date, end_date)
                            calc_args = [xfgroup._load_data[attr] for attr in attr_list]
                            update_indicatore_data = self.serialize_indicatore_data(indicatore, xfgroup, calc_args, start_date, end_date)
                            indicatore_data.extend(update_indicatore_data)

                        value_list = indicatore.calc_func(today, *[xfgroup._load_data[attr] for attr in attr_list])
                        entity = DictWrapper({
                            'xfgroup_id': xfgroup.id,
                            'identify': indicatore.name,
                            'data_json': json.dumps(value_list),
                            'result_date': limit_date
                            })
                        indicatore_data.append(entity)
                    else:
                        if start_date <= end_date:
                            attr_list, xfgroup = self.hung_indicatore_sdata_byuser(xfgroup, indicatore, start_date, end_date)
                            indicatore_data = self.clear_indicatore_bydate(indicatore_data, start_date, end_date)
                            calc_args = [xfgroup._load_data[attr] for attr in attr_list]
                            delay_date = end_date + datetime.timedelta(days = 1)
                            update_indicatore_data = self.serialize_indicatore_data(indicatore, xfgroup, calc_args, start_date, delay_date)
                            indicatore_data.extend(update_indicatore_data)

                indicatore_data.sort(key = lambda entify:entify.result_date)

        return staff_mapping
