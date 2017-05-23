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
    def _serving_orders(cls, psuser, start_date, end_date, result_mapping):
        for subscribe in Subscribe.objects.values("id", 'shop_id', 'start_date', 'end_date')\
                    .filter(Q(start_date__lte = start_date, end_date__gte = start_date) \
                            | Q(start_date__lte = end_date, end_date__gte = end_date))\
                        .filter(consult = psuser) \
                            .filter(pay__gt = 0) \
                                .order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            for cur_date in result_mapping:
                if subscribe.start_date <= cur_date < subscribe.end_date:
                    result_mapping[cur_date].append(subscribe)
        return result_mapping

    @classmethod
    def _active_customers(cls, psuser, start_date, end_date, result_mapping):
        shop_id_list = [pu.shop_id for pu in psuser.mycustomers]
        # 托管计划日花费之和
        mcs_list = list(mcs_coll.find({'rpt_date':{'$gte':date_2datetime(start_date), \
                           '$lt':date_2datetime(end_date + datetime.timedelta(days = 1))}, \
                                'shop_id':{'$in':shop_id_list}, \
                                    'category': 'kcjl'}))
        shop_cost_dict = {} # {date:{shop_id:cost, ...}, ...}
        for mcs in mcs_list:
            temp_dict = shop_cost_dict.setdefault(mcs['rpt_date'].date(), {})
            temp_dict.setdefault(mcs['shop_id'], 0)
            temp_dict[mcs['shop_id']] += mcs['cost']

        for dt, temp_dict in shop_cost_dict.items():
            for shop_id, cost in temp_dict.items():
                if cost >= 5000: # 托管计划日花费之和大于等于50元
                    result_mapping[dt].append(DictWrapper({'shop_id':shop_id, 'cost':cost}))
        return result_mapping

#     @classmethod
#     def _active_customers(cls, psuser, start_date, end_date, result_mapping):
#         # shop_id_list = Subscribe.objects.filter(start_date__lte = end_date, end_date__gt = start_date, consult = psuser,
#         #                                         pay__gt = 0).values_list('shop_id', flat = True)
#         # shop_id_list = list(set(shop_id_list))
#         # # 日花费
#         # rpt_dict = Account.Report.get_snap_list({'shop_id':{'$in':shop_id_list}}, start_date = start_date.strftime('%Y-%m-%d'), end_date = end_date.strftime('%Y-%m-%d'))
#         # for shop_id, rpt_list in rpt_dict.items():
#         #     for obj in rpt_list:
#         #         cur_date = obj.date.date()
#         #         result_mapping[cur_date].append(DictWrapper({'shop_id':shop_id, 'cost':obj.cost}))
#
#         shop_id_list = Subscribe.objects.filter(start_date__lte = end_date, end_date__gt = start_date, consult = psuser, category__in = ['kcjl', 'qn'],
#                                                 pay__gt = 0).values_list('shop_id', flat = True)
#         shop_id_list = list(set(shop_id_list))
#         # 托管计划日花费之和
#         mcs_list = list(mcs_coll.find({'rpt_date':{'$gte':date_2datetime(start_date), '$lt':date_2datetime(end_date + datetime.timedelta(days = 1))}, 'shop_id':{'$in':shop_id_list}}))
#         shop_cost_dict = {} # {date:{shop_id:cost, ...}, ...}
#         for mcs in mcs_list:
#             temp_dict = shop_cost_dict.setdefault(mcs['rpt_date'].date(), {})
#             temp_dict.setdefault(mcs['shop_id'], 0)
#             temp_dict[mcs['shop_id']] += mcs['cost']
#         for dt, temp_dict in shop_cost_dict.items():
#             for shop_id, cost in temp_dict.items():
#                 if cost >= 5000: # 托管计划日花费之和大于等于50元
#                     result_mapping[dt].append(DictWrapper({'shop_id':shop_id, 'cost':cost}))
#         return result_mapping

#     @classmethod
#     def _user_cycle_increment(cls, psuser, start_date, end_date, result_mapping):
#         def calc_increment_days(last_end_date, cur_start_date, cur_end_date):
#             if last_end_date is None or cur_start_date >= last_end_date:
#                 return (cur_end_date - cur_start_date).days
#             elif cur_start_date < last_end_date:
#                 all_days = (cur_end_date - last_end_date).days
#                 return all_days if all_days > 0 else 0
#             return 0
#
#         start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
#         end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
#
#         last_end_date_mapping = {pu.shop_id:None for pu in psuser.mycustomers}
#         shop_id_list = last_end_date_mapping.keys()
#
#         for subscribe in Subscribe.objects.values('shop_id')\
#                     .filter(shop_id__in = shop_id_list)\
#                         .filter(create_time__lte = start_time)\
#                             .filter(category__in = ('kcjl', 'vip', 'rjjh'))\
#                                 .annotate(last_end_date = Max('end_date')):
#             subscribe = DictWrapper(subscribe)
#             last_end_date_mapping[subscribe.shop_id] = subscribe.last_end_date
#
#         for subscribe in Subscribe.objects.values("id", 'shop_id', 'create_time', 'start_date', 'end_date')\
#                     .filter(shop_id__in = shop_id_list)\
#                         .filter(create_time__gt = start_time, create_time__lte = end_time)\
#                             .filter(category__in = ('kcjl', 'vip', 'rjjh'))\
#                                 .order_by("create_time"):
#             subscribe = DictWrapper(subscribe)
#             last_end_date = last_end_date_mapping[subscribe.shop_id]
#             increment_days = calc_increment_days(last_end_date, subscribe.start_date, subscribe.end_date)
#             if increment_days > 0 :
#                 cur_date = subscribe.create_time.date()
#                 entity = DictWrapper({'id':subscribe.id, 'shop_id':subscribe.shop_id, 'increment_days':increment_days})
#                 result_mapping[cur_date].append(entity)
#                 last_end_date_mapping[subscribe.shop_id] = subscribe.end_date
#
#         return result_mapping

    @classmethod
    def _user_cycle_increment(cls, psuser, start_date, end_date, result_mapping):
        def check_mark(subscribe):
            total_days = (subscribe.end_date - subscribe.start_date).days
            cycle = int(round(total_days / 30.0))
            if cycle >= 12 :
                return 4
            elif cycle >= 6:
                return 2
            elif cycle >= 3:
                return 1
            return 0

        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for subscribe in Subscribe.objects.values("id", 'shop_id', 'start_date', 'end_date', "create_time")\
                                            .exclude(Q(biz_type = 6) | Q(category = "qn"))\
                                                .filter(create_time__gte = start_time, create_time__lte = end_time)\
                                                    .filter(psuser = psuser) \
                                                        .filter(pay__gt = 0) \
                                                            .order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            mark = check_mark(subscribe)
            if mark:
                entity = DictWrapper({'id':subscribe.id, 'shop_id':subscribe.shop_id, 'mark':mark})
                result_mapping[subscribe.create_time.date()].append(entity)

        return result_mapping

    @classmethod
    def _pay_subscribe(cls, psuser, start_date, end_date, result_mapping):
        def check_cycle(subscribe):
            total_days = (subscribe.end_date - subscribe.start_date).days
            cycle = round(total_days / 30.0, 1)
            if subscribe.pay / cycle < 3000:
                return 0
            return cycle

        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for subscribe in Subscribe.objects.values("id", 'shop_id', 'start_date', 'end_date', "create_time", "pay")\
                .exclude(Q(biz_type__in = [3, 6]) | Q(category = "qn"))\
                .filter(create_time__gte = start_time, create_time__lte = end_time)\
                .filter(psuser = psuser, approval_status = 1, pay__gte = 3000) \
                .order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            cycle = check_cycle(subscribe)
            if cycle:
                entity = DictWrapper({'id':subscribe.id, 'shop_id':subscribe.shop_id, 'cycle':cycle})
                result_mapping[subscribe.create_time.date()].append(entity)

        return result_mapping

    @classmethod
    def _free_pay_subscribe(cls, psuser, start_date, end_date, result_mapping):
        def check_cycle(subscribe):
            total_days = (subscribe.end_date - subscribe.start_date).days
            cycle = round(total_days / 30.0, 1)
            if subscribe.biz_type < 6 and subscribe.pay / cycle >= 3000:
                return 0
            return cycle

        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for subscribe in Subscribe.objects.values("id", 'shop_id', 'start_date', 'end_date', "create_time", "pay", "biz_type")\
                .exclude(Q(biz_type = 3) | Q(category = "qn"))\
                .filter(create_time__gte = start_time, create_time__lte = end_time)\
                .filter(psuser = psuser, approval_status = 1, pay__gt = 0) \
                .order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            cycle = check_cycle(subscribe)
            if cycle:
                entity = DictWrapper({'id':subscribe.id, 'shop_id':subscribe.shop_id, 'cycle':cycle})
                result_mapping[subscribe.create_time.date()].append(entity)

        return result_mapping

    @classmethod
    def _unknown_orders(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        for subscribe in Subscribe.objects.values("id", 'shop_id', 'create_time', 'biz_type')\
                                          .filter(biz_type = 6, create_time__gte = start_time, create_time__lte = end_time)\
                                          .filter(psuser = psuser) \
                                          .order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            result_mapping[subscribe.create_time.date()].append(subscribe)
        return result_mapping

    @classmethod
    def _renew_orders(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for subscribe in Subscribe.objects.values("id", 'shop_id', 'create_time', 'pay')\
                    .filter(create_time__gte = start_time, create_time__lte = end_time)\
                        .filter(psuser = psuser).exclude(biz_type__in = [6, 7]).order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            result_mapping[subscribe.create_time.date()].append(subscribe)
        return result_mapping

    @classmethod
    def _real_renew_orders(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for subscribe in Subscribe.objects.values("id", 'shop_id', 'create_time', 'pay')\
                    .filter(create_time__gte = start_time, create_time__lte = end_time, approval_status = 1)\
                        .filter(psuser = psuser).exclude(biz_type__in = [6, 7]).order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            result_mapping[subscribe.create_time.date()].append(subscribe)
        return result_mapping

    @classmethod
    def _expire_orders(cls, psuser, start_date, end_date, result_mapping):
        for subscribe in Subscribe.objects.values('id', 'shop_id', 'end_date')\
                    .filter(end_date__gte = start_date, end_date__lte = end_date)\
                        .filter(consult = psuser)\
                            .filter(pay__gt = 0)\
                                .order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            result_mapping[subscribe.end_date].append(subscribe)
        return result_mapping

    @classmethod
    def _unsubscribes(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        # temp_dict = {}
        # for unsubscribe in event_coll.find({'type':'unsubscribe', 'refund_date':{"$gte":start_time, "$lte":end_time}}, {'shop_id': 1, 'event_id': 1, 'refund_date': 1, 'refund': 1}):
        #     temp_dict[unsubscribe['event_id']] = DictWrapper(unsubscribe)
        # query_dict = {'create_time__lt':end_time, 'end_date__gt':start_date}
        # if psuser.position in ['CONSULT', 'CONSULTLEADER']:
        #     query_dict['consult'] = psuser
        # else:
        #     query_dict['operater'] = psuser
        # sub_id_list = Subscribe.objects.filter(**query_dict).values_list('id', flat = True)
        # for sub_id, unsubscribe in temp_dict.items():
        #     if sub_id in sub_id_list:
        #         result_mapping[unsubscribe.refund_date.date()].append(unsubscribe)
        unsub_cursor = event_coll.find({'type':'unsubscribe', 'refund_date':{"$gte":start_time, "$lte":end_time},
                                        '$or':[
                                            {'saler_id':psuser.id, 'saler_apportion':{'$gt':0}},
                                            {'server_id':psuser.id, 'server_apportion':{'$gt':0}}
                                        ], 'refund_reason':{'$lt':5} # , 'refund_type':{'$lt':3}
                                        }, {'shop_id': 1, 'refund_date': 1, 'saler_id':1, 'server_id':1, 'saler_apportion': 1, 'server_apportion':1})
        for unsub in unsub_cursor:
            apportion = 0
            if psuser.id == unsub['saler_id']:
                apportion += unsub.get('saler_apportion', 0)
            if psuser.id == unsub['server_id']:
                apportion += unsub.get('server_apportion', 0)
            result_mapping[unsub['refund_date'].date()].append(DictWrapper({
                '_id':unsub['_id'],
                'shop_id':unsub['shop_id'],
                'apportion':apportion
            }))
        return result_mapping

    @classmethod
    def _unsubscribes_apportion(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        unsub_cursor = event_coll.find(
            {'type':'unsubscribe', 'refund_date':{"$gte":start_time, "$lte":end_time},
             '$or':[{'saler_id':psuser.id}, {'server_id':psuser.id}, {'psuser_id':psuser.id}],
             'refund_reason':{'$lt':5} # , 'refund_type':{'$lt':3}
             },
            {'shop_id': 1, 'psuser_id': 1, 'refund_date': 1, 'saler_id':1, 'server_id':1, 'saler_apportion': 1, 'server_apportion':1}
            )
        for unsub in unsub_cursor:
            apportion = 0
            if 'psuser_id' in unsub and psuser.id == unsub['psuser_id']:
                apportion += 3
            if 'saler_id' in unsub and unsub['saler_id']:
                if psuser.id == unsub['saler_id']:
                    apportion += 7
            elif psuser.id == unsub['server_id']:
                apportion += 7
            result_mapping[unsub['refund_date'].date()].append(DictWrapper({
                '_id':unsub['_id'],
                'shop_id':unsub['shop_id'],
                'apportion':apportion
            }))
        return result_mapping

    @classmethod
    def _performance_unsubscribes(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        temp_dict = {}
        for unsubscribe in event_coll.find({'type':'unsubscribe', 'refund_date':{"$gte":start_time, "$lte":end_time}}, {'shop_id': 1, 'event_id': 1, 'refund_date': 1, 'refund': 1}):
            temp_dict[unsubscribe['event_id']] = DictWrapper(unsubscribe)
        query_dict = {'create_time__lt':end_time, 'end_date__gt':start_date, 'psuser':psuser}
        if psuser.position in ['CONSULT', 'CONSULTLEADER']:
            query_dict['consult'] = psuser
        else:
            query_dict['operater'] = psuser
        sub_id_list = Subscribe.objects.filter(**query_dict).values_list('id', flat = True)
        for sub_id, unsubscribe in temp_dict.items():
            if sub_id in sub_id_list:
                result_mapping[unsubscribe.refund_date.date()].append(unsubscribe)
        return result_mapping

    @classmethod
    def _lost_coustomers(cls, psuser, start_date, end_date, result_mapping, lost_days_limt = 1):
        result_mapping = cls._expire_orders(psuser, start_date, end_date, result_mapping)
        expire_customer_mapping = {order.shop_id:None for order_list in result_mapping.values()\
                                    for order in order_list}
        for subscribe in Subscribe.objects.values('shop_id')\
                    .filter(shop_id__in = expire_customer_mapping.keys())\
                        .annotate(expire_date = Max('end_date')):
            subscribe = DictWrapper(subscribe)
            expire_customer_mapping[subscribe.shop_id] = subscribe.expire_date

        for cur_date, order_list in result_mapping.iteritems():
            lost_user = set()
            for order in order_list:
                max_date = expire_customer_mapping[order.shop_id]
                if max_date is not None and\
                         max_date <= order.end_date + datetime.timedelta(days = lost_days_limt):
                    lost_user.add(order.shop_id)
            result_mapping[cur_date] = list(lost_user)

        return result_mapping

    @classmethod
    def _new_orders(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        subscribe_mapping = {}
        for subscribe in Subscribe.objects.values('id', 'shop_id', 'create_time')\
                    .filter(create_time__gte = start_time, create_time__lte = end_time)\
                        .filter(consult = psuser) \
                            .filter(pay__gt = 0) \
                                .order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            subscribe_mapping.setdefault(subscribe.shop_id, []).append(subscribe)

        shop_id_list = subscribe_mapping.keys()
        for subscribe_info in Subscribe.objects.values('shop_id')\
            .filter(shop_id__in = shop_id_list)\
                .filter(create_time__lt = start_time)\
                    .filter(pay__gt = 0):
            shop_id = subscribe_info["shop_id"]
            if shop_id in subscribe_mapping:
                subscribe_mapping.pop(shop_id)

        for subscribe_list in subscribe_mapping.values():
            for subscribe in subscribe_list:
                result_mapping[subscribe.create_time.date()].append(subscribe)

        return result_mapping

    @classmethod
    def _valid_contacts(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for contact in event_coll.find({'type':'contact', 'psuser_id':psuser.id, 'visible':1, \
                 'create_time':{"$gte":start_time, "$lte":end_time}}, {'shop_id':1, 'create_time':1}):
            contact = DictWrapper(contact)
            result_mapping[contact.create_time.date()].append(contact)
        return result_mapping

    @classmethod
    def _reintros(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for reintro in event_coll.find({'type':'reintro', 'psuser_id':psuser.id, \
                 'create_time':{"$gte":start_time, "$lte":end_time}}, {'shop_id':1, 'create_time':1}):
            reintro = DictWrapper(reintro)
            result_mapping[reintro.create_time.date()].append(reintro)
        return result_mapping

    @classmethod
    def _good_comments(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for comment in event_coll.find({'type':'comment', 'duty_person_id':psuser.id, \
                "comment_type":{"$in":[110, 120, 301, 305]}, \
                    'create_time':{"$gte":start_time, "$lte":end_time},
                    'article_code': 'ts-25811'}, \
                           {'shop_id':1, 'comment_type':1, 'create_time':1}):
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def _new_good_comments(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for comment in event_coll.find(
                {'type':'comment', 'duty_person_id':psuser.id,
                 'comment_type':{'$in':[110, 301, 305]},
                 'create_time':{'$gte':start_time, '$lte':end_time},
                 'article_code': 'ts-25811'
                 },
                {'shop_id':1, 'comment_type':1, 'create_time':1}):
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def _top_good_comments(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for comment in event_coll.find(
                {'type':'comment', 'duty_person_id':psuser.id,
                 'comment_type': 120, 'article_code': 'ts-25811',
                 'create_time': {'$gte':start_time, '$lte':end_time},
                 },
                {'shop_id':1, 'comment_type':1, 'create_time':1}):
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def _bad_comments(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for comment in event_coll.find({'type':'comment', 'duty_person_id':psuser.id, 'comment_type': 200,
                                        'current_version': 'kcjl', 'article_code': 'ts-25811',
                                        'create_time':{'$gte':start_time, '$lte':end_time}
                                        },
                                       {'shop_id':1, 'comment_type':1, 'create_time':1}
                                       ):
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def _change_comments(cls, psuser, start_date, end_date, result_mapping):
        start_time = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_time = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        for comment in event_coll.find({'type':'comment', 'psuser_id':psuser.id, \
                "comment_type":{"$in":[301, 302, 303, 304, 305]}, \
                    'create_time':{"$gte":start_time, "$lte":end_time}}, \
                           {'shop_id':1, 'comment_type':1, 'create_time':1}):
            comment = DictWrapper(comment)
            result_mapping[comment.create_time.date()].append(comment)
        return result_mapping

    @classmethod
    def load_unsubscribe(cls, psuser, start_date, end_date, result_mapping):
        return []
#         shop_id_list = customer_mapping.keys()
#
#         unsubscribe_mapping = {}
#         for unsubscribe in event_coll.find({'type':'unsubscribe', 'shop_id':{'$in':shop_id_list}}, \
#                                             {'shop_id':1, 'event_id':1, 'refund':1}):
#             unsubscribe = DictWrapper(unsubscribe)
#             unsubscribe_mapping = unsubscribe_mapping.setdefault(unsubscribe.shop_id, {})
#             unsubscribe_mapping[unsubscribe.event_id] = unsubscribe
#
# #         for unsubscribe in Unsubscribe.objects.values("shop_id", "event_id", "refund")\
# #                 .filter(shop_id__in = shop_id_list).order_by('create_time'):
# #             unsubscribe = DictWrapper(unsubscribe)
# #             unsubscribe_mapping = unsubscribe_mapping.setdefault(unsubscribe.shop_id, {})
# #             unsubscribe_mapping[unsubscribe.event_id] = unsubscribe
#
#         for shop_id, cust in customer_mapping.iteritems():
#             cust._unorder_mapping = unsubscribe_mapping.get(shop_id, {})
#         return customer_mapping

    @classmethod
    def load_monitor_Event(cls, psuser, start_date, end_date, result_mapping):
        return []

    @classmethod
    def load_account_report(cls, psuser, start_date, end_date, result_mapping):
        return []

class Loader(object):

    def __init__(self, psusers, start_time, end_time):
        self.psusers = psusers
        self.psuser_id_list = [ user.id for user in psusers]
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

        start_date = self.end_date + datetime.timedelta(days = 1) \
                        if calc_start_date is None else calc_start_date
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

    def hung_indicatore_sdata_byuser(self, psuser, indicatore, start_date, end_date):
        attr_list = []
        total_days = (end_date - start_date).days

        if not hasattr(psuser, "_load_data"):
            psuser._load_data = {}

        for load_func in indicatore.load_func:
            attr = load_func.__name__
            if callable(load_func) and attr not in psuser._load_data:
                result_mapping = { start_date + datetime.timedelta(days = index) :[] \
                                  for index in xrange(total_days + 1)}
                psuser._load_data[attr] = load_func(psuser, start_date, end_date, result_mapping)
            attr_list.append(attr)

        return attr_list, psuser

    def serialize_indicatore_data(self, indicatore, psuser, calc_args, start_date, end_date):
        total_days = (end_date - start_date).days
        indicatore_data = []
        for index in xrange(total_days):
            cur_date = start_date + datetime.timedelta(days = index)
            value_list = indicatore.calc_func(cur_date, *calc_args)
            entity = self.adpater.save(psuser, cur_date, indicatore, value_list)
            indicatore_data.append(entity)
        return indicatore_data

    def loading(self, indicators, is_force = False):
        staff_mapping = self.adpater.filter(self.psusers, self.start_time.date(), self.end_time.date(), indicators)
        today = datetime.date.today()
        limit_date = today
        PSUser.bulk_hung_consult_brief_mycustomers(self.psusers)
#         PSUser.bulk_hung_consult_mycustomers(self.psusers)
        for psuser in self.psusers:
            user_data = staff_mapping.setdefault(psuser, {})
            for indicatore in indicators:
                indicatore_data = user_data.setdefault(indicatore, [])

                if is_force:
                    start_date, end_date = (self.start_date, self.end_date)
                    end_date = limit_date if end_date > limit_date else end_date
                    is_real_time = today == end_date

                    attr_list, psuser = self.hung_indicatore_sdata_byuser(psuser, indicatore, start_date, end_date)
                    indicatore_data = self.clear_indicatore_bydate(indicatore_data, start_date, end_date)
                    calc_args = [psuser._load_data[attr] for attr in attr_list]
                    update_indicatore_data = self.serialize_indicatore_data(indicatore, psuser, calc_args, start_date, end_date)
                    indicatore_data.extend(update_indicatore_data)

                    if is_real_time:
                        value_list = indicatore.calc_func(today, *[psuser._load_data[attr] for attr in attr_list])
                        entity = DictWrapper({"psuser_id":psuser.id, "identify":indicatore.name, \
                                     "data_json" :json.dumps(value_list), 'result_date':limit_date})
                        indicatore_data.append(entity)
                    else:
                        delay_date = end_date + datetime.timedelta(days = 1)
                        update_indicatore_data = self.serialize_indicatore_data(indicatore, psuser, calc_args, end_date, delay_date)
                        indicatore_data.extend(update_indicatore_data)
                else:
                    start_date, end_date = self.calc_lost_timescope(indicatore_data)
                    end_date = limit_date if end_date > limit_date else end_date
                    is_real_time = today == end_date

                    if is_real_time:
                        attr_list, psuser = self.hung_indicatore_sdata_byuser(psuser, indicatore, start_date, end_date)

                        if start_date < end_date:
                            indicatore_data = self.clear_indicatore_bydate(indicatore_data, start_date, end_date)
                            calc_args = [psuser._load_data[attr] for attr in attr_list]
                            update_indicatore_data = self.serialize_indicatore_data(indicatore, psuser, calc_args, start_date, end_date)
                            indicatore_data.extend(update_indicatore_data)

                        value_list = indicatore.calc_func(today, *[psuser._load_data[attr] for attr in attr_list])
                        entity = DictWrapper({"psuser_id":psuser.id, "identify":indicatore.name, \
                                     "data_json" :json.dumps(value_list), 'result_date':limit_date})
                        indicatore_data.append(entity)
                    else:
                        if start_date <= end_date:
                            attr_list, psuser = self.hung_indicatore_sdata_byuser(psuser, indicatore, start_date, end_date)
                            indicatore_data = self.clear_indicatore_bydate(indicatore_data, start_date, end_date)
                            calc_args = [psuser._load_data[attr] for attr in attr_list]
                            delay_date = end_date + datetime.timedelta(days = 1)
                            update_indicatore_data = self.serialize_indicatore_data(indicatore, psuser, calc_args, start_date, delay_date)
                            indicatore_data.extend(update_indicatore_data)

                indicatore_data.sort(key = lambda entify:entify.result_date)

        return staff_mapping

