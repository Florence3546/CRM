# coding=UTF-8

'''
Created on 2015-12-30

@author: YRK
'''
import collections
import itertools

from django.db.models import Q, Sum

from apps.ncrm.models import Customer
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apps.ncrm.models import Subscribe, Comment, Contact, Unsubscribe, ReIntro, event_coll
from apps.subway.models_account import Account

class LoadFactory(object):

    @classmethod
    def load_subscribe(cls, customer_mapping, start_time, end_time):
        shop_id_list = customer_mapping.keys()

        subscribe_mapping = {}
        for subscribe in Subscribe.objects.values("shop_id", 'create_time', "start_date", 'psuser_id', 'end_date', 'category', 'pay')\
                .filter(category__in = ('kcjl', 'qn'))\
                    .filter(shop_id__in = shop_id_list).order_by('-create_time'):
            subscribe = DictWrapper(subscribe)
            if subscribe.pay > 0:
                subscribe_mapping.setdefault(subscribe.shop_id, []).append(subscribe)

        for shop_id, cust in customer_mapping.iteritems():
            cust._order_list = subscribe_mapping.get(shop_id, [])
            order_list = filter(lambda order : order.pay > 0, cust._order_list)
            cust.pay_type = len(order_list) == 1
        return customer_mapping

    @classmethod
    def load_reintro(cls, customer_mapping, start_time, end_time):
        shop_id_list = customer_mapping.keys()

        reintro_mapping = {}
#         for reintro in ReIntro.objects.only('shop_id', 'create_time').filter(shop_id__in = shop_id_list)\
#                 .filter(create_time__gte = start_time, create_time__lte = end_time).order_by('create_time'):
#             reintro_mapping.setdefault(reintro.shop_id, []).append(reintro)

        for reintro in event_coll.find({'type':'reintro', 'shop_id':{'$in':shop_id_list}, \
                 'create_time':{"$gte":start_time, "$lte":end_time}}, {'shop_id':1, 'create_time':1}):
            reintro = DictWrapper(reintro)
            reintro_mapping.setdefault(reintro.shop_id, []).append(reintro)

        for shop_id, cust in customer_mapping.iteritems():
            cust._reintro_list = reintro_mapping.get(shop_id, [])
        return customer_mapping

    @classmethod
    def load_comment(cls, customer_mapping, start_time, end_time):
        shop_id_list = customer_mapping.keys()

        comment_mapping = {}
#         for comment in Comment.objects.only('shop_id', 'comment_type', 'create_time')\
#                 .filter(create_time__gte = start_time, create_time__lte = end_time)\
#                     .filter(shop_id__in = shop_id_list)\
#                         .order_by('create_time'):
#             comment_mapping.setdefault(comment.shop_id, []).append(comment)

        for comment in event_coll.find({'type':'comment', 'shop_id':{'$in':shop_id_list}, \
                'create_time':{"$gte":start_time, "$lte":end_time}}, \
                       {'shop_id':1, 'comment_type':1, 'create_time':1}):
            comment = DictWrapper(comment)
            comment_mapping.setdefault(comment.shop_id, []).append(comment)

        for shop_id, cust in customer_mapping.iteritems():
            cust._comment_list = comment_mapping.get(shop_id, [])
        return customer_mapping

    @classmethod
    def load_unsubscribe(cls, customer_mapping, start_time, end_time):
        shop_id_list = customer_mapping.keys()

        unsubscribe_mapping = {}
        for unsubscribe in event_coll.find({'type':'unsubscribe', 'shop_id':{'$in':shop_id_list}}, \
                                            {'shop_id':1, 'event_id':1, 'refund':1}):
            unsubscribe = DictWrapper(unsubscribe)
            unsubscribe_mapping = unsubscribe_mapping.setdefault(unsubscribe.shop_id, {})
            unsubscribe_mapping[unsubscribe.event_id] = unsubscribe

#         for unsubscribe in Unsubscribe.objects.values("shop_id", "event_id", "refund")\
#                 .filter(shop_id__in = shop_id_list).order_by('create_time'):
#             unsubscribe = DictWrapper(unsubscribe)
#             unsubscribe_mapping = unsubscribe_mapping.setdefault(unsubscribe.shop_id, {})
#             unsubscribe_mapping[unsubscribe.event_id] = unsubscribe

        for shop_id, cust in customer_mapping.iteritems():
            cust._unorder_mapping = unsubscribe_mapping.get(shop_id, {})
        return customer_mapping

    @classmethod
    def load_contact(cls, customer_mapping, start_time, end_time):
        shop_id_list = customer_mapping.keys()

        valid_contact_dict = {}
#         for event in Contact.objects.only('shop_id', 'create_time').filter(shop_id__in = shop_id_list)\
#                 .filter(create_time__gte = start_time, create_time__lte = end_time)\
#                     .filter(visible = 1).order_by('create_time'):
#             event = DictWrapper(event)
#             valid_contact_dict.setdefault(event.shop_id, []).append(event)

        for contact in event_coll.find({'type':'contact', 'shop_id':{'$in':shop_id_list}, 'visible':1, \
                 'create_time':{"$gte":start_time, "$lte":end_time}}, {'shop_id':1, 'create_time':1}):
            contact = DictWrapper(contact)
            valid_contact_dict.setdefault(contact.shop_id, []).append(contact)

        for shop_id, cust in customer_mapping.iteritems():
            cust._valid_contact_list = valid_contact_dict.get(shop_id, [])
            cust._valid_contact_count = len(set([contact.create_time.date() for contact in cust._valid_contact_list]))
        return customer_mapping

    @classmethod
    def load_monitor_Event(cls, customer_mapping, start_time, end_time):
        return customer_mapping

    @classmethod
    def load_account_report(cls, customer_mapping, start_time, end_time):
        return customer_mapping

class Loader(object):

    def __init__(self, time_scope, psusers, position = "CONSULT"):
        start_time , end_time = time_scope
        start_time = start_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        end_time = end_time.replace(hour = 23, minute = 59, second = 59, microsecond = 59)

        self.psusers = psusers
        self.psuser_id_list = [ user.id for user in psusers]
        self.timer_scope = (start_time , end_time)
        self.position = position

        self.staff_customer_mapping, self.customer_mapping = self.load_init_mapping()

    def loading(self, indicators):
        load_funcs = set(itertools.chain(*[ indicator.load_func for indicator in indicators ]))

        for load_func in load_funcs:
            if callable(load_func):
                load_func(self.customer_mapping, *self.timer_scope)

        return self.customer_mapping

    def load_customers_bystaff(self, psuser_id):
        return self.staff_customer_mapping.get(psuser_id, [])

    def load_init_mapping(self):
        start_time, end_time = self.timer_scope
        start_date = start_time.date()
        end_date = end_time.date()

        staff_customer_mapping = collections.defaultdict(list)
        customer_mapping = {}
        if self.position == "CONSULT":
            shop_staff_set = set([(sub_info['shop_id'], sub_info['consult_id']) \
                                  for sub_info in Subscribe.objects.values("shop_id", "consult_id")\
                                        .filter(consult__in = self.psuser_id_list)\
                                            .filter(Q(start_date__lte = start_date, end_date__gte = start_date) \
                                                    | Q(start_date__lte = end_date, end_date__gte = end_date))])

            # TODO: yangrongkai 请注意，为了保证引用点相同，请考虑 一个售后多个店铺，
            # 及一个店铺多个售后的情况, 此处编程需谨慎，很容易造成隐性bug
            customer_mapping = {shop_id : DictWrapper(shop_id = shop_id) \
                                for shop_id, _ in shop_staff_set}

            for shop_id, consult_id in shop_staff_set:
                cust = customer_mapping.get(shop_id, None)
                if cust is not None:
                    staff_customer_mapping[consult_id].append(cust)

        return staff_customer_mapping, customer_mapping

