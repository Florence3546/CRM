# coding=UTF-8

'''
Created on 2015-12-31

@author: YRK
'''


class CalculationFactory(object):

    @classmethod
    def _check_is_sering_customer(cls, customer, start_date, end_date):
        for order in customer._order_list:
            if (order.start_date <= start_date <= order.end_date) \
                    or (order.start_date <= end_date <= order.end_date):
                return True
        return False

    @classmethod
    def _check_is_new_customer(cls, customer, start_time, end_time):
        if cls._check_is_sering_customer(customer, start_time.date(), end_time.date())and customer.pay_type:
            for order in customer._order_list:
                if start_time < order.create_time < end_time:
                    return True
        return False

    @classmethod
    def _check_is_renew(cls, customer, start_time, end_time):
        for order in customer._order_list:
            if order.psuser_id and order.psuser_id > 0 and start_time < order.create_time < end_time:
                return True
        return False

    @classmethod
    def _check_is_expire(cls, customer, start_date, end_date):
        for order in customer._order_list:
            if start_date <= order.end_date <= end_date:
                return True
        return False

    @classmethod
    def _check_is_lost(cls, customer, start_date, end_date):
        for order in customer._order_list:
            if order.end_date > end_date:
                return False
        return True

    @classmethod
    def _check_have_contact_customer(cls, customer, start_time, end_time):
        for contact in customer._valid_contact_list:
            if start_time < contact.create_time < end_time:
                return True
        return False



    @classmethod
    def _get_renew_pay(cls, customer, start_time, end_time):
        valid_order_list = filter(lambda order: order.psuser_id and order.psuser_id > 0 \
                                    and start_time < order.create_time < end_time , \
                                      customer._order_list)
        total_pay = sum([order.pay - customer._unorder_mapping.get(getattr(order, 'id', None), 0) for order in valid_order_list])
        return total_pay

    @classmethod
    def _get_reintro_count(cls, customer, start_time, end_time):
        valid_reintro_list = filter(lambda reintro: start_time < reintro.create_time < end_time , \
                                      customer._reintro_list)
        return len(valid_reintro_list)

    @classmethod
    def _get_change_comment_count(cls, customer, start_time, end_time):
        valid_comment_list = filter(lambda comment: comment.comment_type in (301, 302, 303, 304, 305) \
                                    and start_time < comment.create_time <= end_time , \
                                      customer._comment_list)
        return len(valid_comment_list)

    @classmethod
    def _get_good_comment_count(cls, customer, start_time, end_time):
        valid_comment_list = filter(lambda comment: comment.comment_type in (110, 120) \
                                    and start_time < comment.create_time <= end_time , \
                                      customer._comment_list)
        return len(valid_comment_list)

    @classmethod
    def _get_valid_contact_count(cls, customer, start_time, end_time):
        valid_contact_list = filter(lambda contact: start_time < contact.create_time <= end_time , \
                                      customer._valid_contact_list)
        return len(set([contact.create_time.date() for contact in valid_contact_list]))






    @classmethod
    def _calc_renew_count(cls, customers, start_time, end_time):
        return filter(lambda customer : cls._check_is_renew(customer, start_time, end_time) , customers)

    @classmethod
    def _calc_serving_customers(cls, customers, start_date, end_date):
        return filter(lambda customer : cls._check_is_sering_customer(customer, start_date, end_date) , customers)

    @classmethod
    def _calc_current_serving_customers(cls, customers, start_date, end_date):
        return filter(lambda customer : cls._check_have_contact_customer(customer, start_date, end_date) , customers)

    @classmethod
    def _calc_new_customers(cls, customers, start_time, end_time):
        return filter(lambda customer: cls._check_is_new_customer(customer, start_time, end_time) , customers)

    @classmethod
    def _calc_onlyone_contact_customers(cls, customers):
        return filter(lambda customer: customer._valid_contact_count == 1 , customers)

    @classmethod
    def _calc_second_contact_customers(cls, customers):
        return filter(lambda customer: customer._valid_contact_count > 1 , customers)

    @classmethod
    def _calc_expire_people(cls, customers, start_date, end_date):
        return filter(lambda customer: cls._check_is_expire(customer, start_date, end_date) , customers)

    @classmethod
    def _calc_lost_people(cls, customers, start_date, end_date):
        return filter(lambda customer: cls._check_is_lost(customer, start_date, end_date)  , customers)







    @classmethod
    def renew_order_pay(cls, customers, start_time, end_time):
        totle_order_pay = sum([ cls._get_renew_pay(customer, start_time, end_time) for customer in customers])
        return customers, round(totle_order_pay / 100.0, 2)

    @classmethod
    def renew_order_count(cls, customers, start_time, end_time):
        renew_customers = cls._calc_renew_count(customers, start_time, end_time)
        return renew_customers, len(renew_customers)

    @classmethod
    def reintro_count(cls, customers, start_time, end_time):
        totle_reintro_count = sum([ cls._get_reintro_count(customer, start_time, end_time) for customer in customers])
        return customers, totle_reintro_count

    @classmethod
    def change_comment_count(cls, customers, start_time, end_time):
        totle_change_comment_count = sum([ cls._get_change_comment_count(customer, start_time, end_time) for customer in customers])
        return customers, totle_change_comment_count

    @classmethod
    def good_comment_count(cls, customers, start_time, end_time):
        totle_comment_count = sum([ cls._get_good_comment_count(customer, start_time, end_time) for customer in customers])
        return customers, totle_comment_count

    @classmethod
    def expire_people_count(cls, customers, start_time, end_time):
        expire_customers = cls._calc_expire_people(customers, start_time.date(), end_time.date())
        return expire_customers , len(expire_customers)

    @classmethod
    def renew_rate(cls, customers, start_time, end_time):
        expire_people, expire_count = cls.expire_people_count(customers, start_time, end_time)
        renew_people, renew_count = cls.renew_order_count(customers, start_time, end_time)
        renew_rate = renew_count * 100.0 / expire_count if expire_count > 0 else 0.0
        return renew_people , round(renew_rate, 2)

    @classmethod
    def current_serving_people_count(cls, customers, start_time, end_time):
        serving_peoples = cls._calc_current_serving_customers(customers, start_time, end_time)
        people_count = len(serving_peoples)
        return serving_peoples, people_count

    @classmethod
    def server_people_count(cls, customers, start_time, end_time):
        serving_peoples = cls._calc_serving_customers(customers, start_time.date(), end_time.date())
        people_count = len(serving_peoples)
        return serving_peoples, people_count

    @classmethod
    def new_people_count(cls, customers, start_time, end_time):
        new_customers = cls._calc_new_customers(customers, start_time, end_time)
        return new_customers, len(new_customers)

    @classmethod
    def first_contact_rate(cls, customers, start_time, end_time):
        new_customer_list = cls._calc_new_customers(customers, start_time, end_time)
        first_contact_people = cls._calc_onlyone_contact_customers(new_customer_list)
        new_people_total = len(new_customer_list)
        first_contact_rate = round(len(first_contact_people) * 100.0 / new_people_total, 2) if new_people_total else 0.0
        return first_contact_people, first_contact_rate

    @classmethod
    def second_contact_rate(cls, customers, start_time, end_time):
        new_customer_list = cls._calc_new_customers(customers, start_time, end_time)
        second_contact_people = cls._calc_second_contact_customers(new_customer_list)
        new_people_total = len(new_customer_list)
        seond_contact_rate = round(len(second_contact_people) * 100.0 / new_people_total, 2) if new_people_total else 0.0
        return second_contact_people, seond_contact_rate

    @classmethod
    def contact_people_count(cls, customers, start_time, end_time):
        serving_peoples, people_count = cls.current_serving_people_count(customers, start_time, end_time)
        return serving_peoples, people_count

    @classmethod
    def avg_contact_count(cls, customers, start_time, end_time):
        serving_peoples, people_count = cls.contact_people_count(customers, start_time, end_time)
        totle_contact = sum([ cls._get_valid_contact_count(customer, start_time, end_time) for customer in customers])
        return serving_peoples, round(totle_contact * 1.0 / people_count, 2) if people_count > 0 else 0.0

    @classmethod
    def lost_people_count(cls, customers, start_time, end_time):
        expire_customers = cls._calc_expire_people(customers, start_time.date(), end_time.date())
        lost_customers = cls._calc_lost_people(expire_customers, start_time.date(), end_time.date())
        return lost_customers , len(lost_customers)