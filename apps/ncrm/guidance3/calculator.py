# coding=UTF-8

'''
Created on 2015-12-31

@author: YRK
'''
import datetime
from bson.objectid import ObjectId

from apps.ncrm.models import (
    Subscribe, Customer, PSUser, Contact, ReIntro, Comment, Unsubscribe, event_coll, ARTICLE_CODE_CHOICES
    )

class ViewerFactory(object):

    @classmethod
    def show_subscribe(cls, order_id_list, shop_id_list):
        customers = Customer.objects.filter(shop_id__in = shop_id_list).only('shop_id', 'nick')
        cust_dict = {obj.shop_id: obj.nick for obj in customers}
        psusers = PSUser.objects.all()
        psuser_dict = {obj.id: obj.name_cn for obj in psusers}

        objs = Subscribe.objects.filter(id__in = order_id_list)
        title_list = [
            u'创建人',
            u'创建时间',
            u'店铺',
            u'业务类型',
            u'应用码',
            u'应用名',
            u'订购码',
            u'订购版本',
            u'原价(元)',
            u'成交金额(元)',
            u'订购周期',
            u'订单类型',
            u'成交方式',
            u'服务开始日期',
            u'服务结束日期',
            u'操作人',
            u'客服'
            ]
        data_list = [title_list]
        for obj in objs:
            data_list.append([
                obj.psuser_id and psuser_dict[obj.psuser_id],
                obj.create_time.strftime('%Y-%m-%d %H:%M'),
                cust_dict[obj.shop_id],
                obj.get_category_display(),
                obj.get_article_code_display(),
                obj.article_name,
                obj.item_code,
                obj.item_name,
                obj.fee and round(obj.fee / 100.0, 2),
                obj.pay and round(obj.pay / 100.0, 2),
                obj.cycle,
                obj.get_biz_type_display(),
                obj.get_source_type_display(),
                obj.start_date,
                obj.end_date,
                obj.operater_id and psuser_dict[obj.operater_id],
                obj.consult_id and psuser_dict[obj.consult_id],
                ])
        return data_list, shop_id_list

    @classmethod
    def show_customers(cls, cust_id_list, shop_id_list):
        psusers = PSUser.objects.all()
        psuser_dict = {obj.id: obj.name_cn for obj in psusers}
        objs = Customer.objects.filter(shop_id__in = cust_id_list)
        title_list = [
            u'店铺名',
            u'店铺ID',
            u'天猫店',
            u'地址',
            u'开通短信提醒',
            u'联系人',
            u'手机号',
            u'QQ',
            u'旺旺',
            # u'用户来源',
            # u'用户状态',
            # u'信息爬取状态',
            u'创建时间',
            # u'最近更新时间',
            # u'创建人',
            u'当前签单人',
            u'当前操作人',
            u'当前客服',
            u'最新业务类型',
            u'最新到期日期',
            # u'暂停服务中',
            # u'推广效果等级',
            # u'联系不上',
            # u'打过差评',
            # u'水军',
            # u'订单来源未知',
            # u'当前订单联系次数',
            # u'最近联系日期',
            # u'最近操作日期',
            # u'对软件或服务不满的客户，问题客户，维护客户',
            # u'意向客户，潜在客户',
            ]
        data_list = [title_list]
        for obj in objs:
            data_list.append([
                obj.nick,
                obj.shop_id,
                obj.is_b2c and '是' or '否',
                obj.address,
                obj.remind and '是' or '否',
                obj.seller,
                obj.phone,
                obj.qq,
                obj.ww,
                # obj.source,
                # obj.get_acct_status_display(),
                # obj.get_info_status_display(),
                obj.create_time and obj.create_time.strftime('%Y-%m-%d %H:%M'),
                # obj.update_time and obj.update_time.strftime('%Y-%m-%d %H:%M'),
                # obj.creator_id and psuser_dict[obj.creator_id],
                obj.saler_id and psuser_dict[obj.saler_id],
                obj.operater_id and psuser_dict[obj.operater_id],
                obj.consult_id and psuser_dict[obj.consult_id],
                obj.get_latest_category_display(),
                obj.latest_end and obj.latest_end.strftime('%Y-%m-%d %H:%M'),
                # obj.is_pausing and '是' or '否',
                # obj.get_advertise_effect_display(),
                # obj.contact_fail and '是' or '否',
                # obj.bad_comment and '是' or '否',
                # obj.is_pawn and '是' or '否',
                # obj.unknown_subscribe and '是' or '否',
                # obj.contact_count,
                # obj.latest_contact and obj.latest_contact.strftime('%Y-%m-%d %H:%M'),
                # obj.latest_operate and obj.latest_operate.strftime('%Y-%m-%d %H:%M'),
                # obj.is_discontent and '是' or '否',
                # obj.is_potential and '是' or '否',
                ])
        return data_list, shop_id_list

    @classmethod
    def show_contact(cls, contact_id_list, shop_id_list):
        customers = Customer.objects.filter(shop_id__in = shop_id_list).only('shop_id', 'nick')
        cust_dict = {obj.shop_id: obj.nick for obj in customers}
        psusers = PSUser.objects.all()
        psuser_dict = {obj.id: obj.name_cn for obj in psusers}

        objs = Contact.objects.filter(id__in = contact_id_list)
        title_list = [
            u'创建时间',
            u'创建人',
            u'店铺名',
            u'事件类型',
            u'备注',
            u'联系方式',
            u'是否有效',
            ]
        data_list = [title_list]
        for obj in objs:
            data_list.append([
                obj.create_time.strftime('%Y-%m-%d %H:%M'),
                obj.psuser_id and psuser_dict[obj.psuser_id],
                cust_dict[obj.shop_id],
                obj.get_type_display(),
                obj.note,
                obj.get_contact_type_display(),
                obj.get_visible_display(),
                ])
        return data_list, shop_id_list

    @classmethod
    def show_reintro(cls, reintro_id_list, shop_id_list):
        customers = Customer.objects.filter(shop_id__in = shop_id_list).only('shop_id', 'nick')
        cust_dict = {obj.shop_id: obj.nick for obj in customers}
        psusers = PSUser.objects.all()
        psuser_dict = {obj.id: obj.name_cn for obj in psusers}

        objs = ReIntro.objects.filter(id__in = reintro_id_list)
        title_list = [
            u'创建时间',
            u'创建人',
            u'店铺名',
            u'事件类型',
            u'备注',
            u'接收人',
            u'转介绍类型',
            ]
        data_list = [title_list]
        for obj in objs:
            data_list.append([
                obj.create_time.strftime('%Y-%m-%d %H:%M'),
                obj.psuser_id and psuser_dict[obj.psuser_id],
                cust_dict[obj.shop_id],
                obj.get_type_display(),
                obj.note,
                obj.receiver_id and psuser_dict[obj.receiver_id],
                obj.get_reintro_type_display(),
                ])
        return data_list, shop_id_list

    @classmethod
    def show_comment(cls, comment_id_list, shop_id_list):
        customers = Customer.objects.filter(shop_id__in = shop_id_list).only('shop_id', 'nick')
        cust_dict = {obj.shop_id: obj.nick for obj in customers}
        psusers = PSUser.objects.all()
        psuser_dict = {obj.id: obj.name_cn for obj in psusers}

        # objs = Comment.objects.filter(id__in = comment_id_list) # 用这个有问题
        object_id_list = [ObjectId(comment_id) for comment_id in comment_id_list]
        commment_cur = event_coll.find({'type': 'comment', '_id': {'$in': object_id_list}})
        title_list = [
            u'创建时间',
            u'创建人',
            u'店铺名',
            u'事件类型',
            u'订购项',
            u'评价类型',
            u'踩评次数',
            u'改评价时间',
            ]
        data_list = [title_list]
        article_code_dict = dict(ARTICLE_CODE_CHOICES)
        comment_type_dict = dict(Comment.COMMENT_TYPE_CHOICES)
        for comment in commment_cur:
            data_list.append([
                comment['create_time'].strftime('%Y-%m-%d %H:%M'),
                comment['psuser_id'] and psuser_dict[comment['psuser_id']],
                cust_dict[comment['shop_id']],
                '评论事件',
                article_code_dict.get(comment.get('article_code', ''), '未知'),
                comment_type_dict.get(comment.get('comment_type', ''), '未知'),
                comment.get('top_comment_times', 0),
                comment['modify_comment_time'].strftime('%Y-%m-%d %H:%M') if 'modify_comment_time' in comment and comment['modify_comment_time'] else '未知',
                ])
        return data_list, shop_id_list

    @classmethod
    def show_unsubscribe(cls, unsubscribe_id_list, shop_id_list):
        customers = Customer.objects.filter(shop_id__in = shop_id_list).only('shop_id', 'nick')
        cust_dict = {obj.shop_id: obj.nick for obj in customers}
        psusers = PSUser.objects.all()
        psuser_dict = {obj.id: obj.name_cn for obj in psusers}
        object_id_list = [ObjectId(obj_id) for obj_id in unsubscribe_id_list]
        objs = Unsubscribe.objects.filter(id__in = object_id_list)
        title_list = [
            u'创建时间',
            u'创建人',
            u'店铺名',
            u'事件类型',
            u'退款金额(元)',
            u'退款日期',
            u'退款原因',
            # u'退款类型',
            u'退款方式',
            u'禁止使用软件',
            u'签单人',
            u'签单人分摊(元)',
            u'服务人',
            u'服务人分摊(元)',
            ]
        data_list = [title_list]
        for obj in objs:
            data_list.append([
                obj.create_time.strftime('%Y-%m-%d %H:%M'),
                obj.psuser_id and psuser_dict[obj.psuser_id],
                cust_dict[obj.shop_id],
                obj.get_type_display(),
                obj.refund and round(obj.refund / 100.0, 2),
                obj.refund_date.strftime('%Y-%m-%d %H:%M'),
                obj.refund_reason and obj.get_refund_reason_display(),
                # obj.refund_type and obj.get_refund_type_display(),
                obj.refund_style and obj.get_refund_style_display(),
                obj.frozen_kcjl and obj.get_frozen_kcjl_display(),
                obj.saler_id and psuser_dict[obj.saler_id],
                obj.saler_apportion and round(obj.saler_apportion / 100.0, 2) or 0,
                obj.server_id and psuser_dict[obj.server_id],
                obj.server_apportion and round(obj.server_apportion / 100.0, 2) or 0,
                ])
        return data_list, shop_id_list

class SumFactory(object):

    @classmethod
    def renew_order_count(cls, renew_orders):
        event_id_list = []
        shop_id_list = []
        for obj in renew_orders:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(renew_orders), event_id_list, shop_id_list

    @classmethod
    def renew_order_pay(cls, renew_orders):
        order_pay = 0
        event_id_list = []
        shop_id_list = []
        for obj in renew_orders:
            order_pay += obj.pay
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        total_pay = round(order_pay / 100.0, 2)
        return total_pay, event_id_list, shop_id_list

    @classmethod
    def new_people_count(cls, new_orders):
        event_id_list = []
        shop_id_list = []
        for obj in new_orders:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(new_orders), event_id_list, shop_id_list

    @classmethod
    def contact_people_count(cls, valid_contact_list):
        shop_id_list = list(set(contact.shop_id for contact in valid_contact_list))
        return len(shop_id_list), shop_id_list, shop_id_list

    @classmethod
    def avg_contact_count(cls, valid_contact_list):
        all_shop_size, shop_id_list, _ = cls.contact_people_count(valid_contact_list)
        contact_days_set = set()
        contact_list = []
        for contact in valid_contact_list:
            contact_list.append(contact.id)
            contact_days_set.add(datetime.datetime.strptime(contact.create_time, "%Y-%m-%d %H:%M:%S").date())
        avg_val = round(len(contact_days_set) * 1.0 / all_shop_size, 2) if all_shop_size > 0 else 0.0
        return avg_val, contact_list, shop_id_list

    @classmethod
    def expire_order_count(cls, expire_orders):
        event_id_list = []
        shop_id_list = []
        for obj in expire_orders:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(expire_orders), event_id_list, shop_id_list

    @classmethod
    def lost_customer_people(cls, lost_custoemrs):
        shop_id_list = list(set(customer.shop_id for customer in lost_custoemrs))
        return len(shop_id_list), shop_id_list, shop_id_list

    @classmethod
    def serving_people_count(cls, serving_customers):
        shop_id_list = list(set(customer.shop_id for customer in serving_customers))
        return len(shop_id_list), shop_id_list, shop_id_list

    @classmethod
    def extend_cycle(cls, increment_subscribes):
        event_id_list = []
        shop_id_list = []
        increment_mark = 0
        for subscribe in increment_subscribes:
            event_id_list.append(subscribe.id)
            shop_id_list.append(subscribe.shop_id)
            increment_mark += subscribe.mark

        return increment_mark, event_id_list, shop_id_list

    # @classmethod
    # def active_customer_count(cls, active_customers):
    #     shop_dict = {}
    #     date_list = []
    #     for shop_obj in active_customers:
    #         temp_dict = shop_dict.setdefault(shop_obj.shop_id, {'login_dates':[], 'cost':[]})
    #         if shop_obj.logined:
    #             temp_dict['login_dates'].append(shop_obj.date)
    #         temp_dict['cost'].append(shop_obj.cost)
    #         if shop_obj.date not in date_list:
    #             date_list.append(shop_obj.date)
    #     result_list = []
    #     avg_cost = 5000
    #     for shop_id, shop_info in shop_dict.items():
    #         if len(shop_info['login_dates'])*3 >= len(date_list): # 登录频率大于等于1/3
    #             result_list.append(shop_id)
    #         elif sum(shop_info['cost']) >= avg_cost*len(date_list): # 日均花费大于等于50元
    #             result_list.append(shop_id)
    #     return len(result_list), result_list, result_list

    @classmethod
    def active_customer_count(cls, active_customers):
        # shop_dict = {}
        # date_list = []
        # for shop_obj in active_customers:
        #     temp_dict = shop_dict.setdefault(shop_obj.shop_id, {'cost':[]})
        #     temp_dict['cost'].append(shop_obj.cost)
        #     if shop_obj.date not in date_list:
        #         date_list.append(shop_obj.date)
        # result_list = []
        # avg_cost = 5000
        # for shop_id, shop_info in shop_dict.items():
        #     if sum(shop_info['cost']) >= avg_cost * len(date_list): # 日均花费大于等于50元
        #         result_list.append(shop_id)
        # return len(result_list), result_list, result_list

        shop_id_list = list(set([obj.shop_id for obj in active_customers]))
        return len(active_customers), shop_id_list, shop_id_list

    @classmethod
    def reintro_count(cls, reintros):
        event_id_list = []
        shop_id_list = []
        for obj in reintros:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(reintros), event_id_list, shop_id_list

    @classmethod
    def good_comment_count(cls, good_comments):
        event_id_list = []
        shop_id_list = []
        for obj in good_comments:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(good_comments), event_id_list, shop_id_list

    @classmethod
    def change_comment_count(cls, change_comments):
        event_id_list = []
        shop_id_list = []
        for obj in change_comments:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(change_comments), event_id_list, shop_id_list

    @classmethod
    def renew_rate(cls, renew_rates):
        renew_all_customers = []
        expire_all_customers = []
        for renew_rate in renew_rates:
            renew_all_customers.extend(renew_rate.renew_customers)
            expire_all_customers.extend(renew_rate.expire_customers)

        rate = round(len(renew_all_customers) * 100.0 / len(expire_all_customers) , 2) \
            if expire_all_customers else 0.0
        return rate, [], []

    @classmethod
    def unknown_order_count(cls, serving_orders):
        event_id_list = []
        shop_id_list = []
        for obj in serving_orders:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(serving_orders), event_id_list, shop_id_list

    @classmethod
    def bad_comment_count(cls, bad_comments):
        event_id_list = []
        shop_id_list = []
        for obj in bad_comments:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(bad_comments), event_id_list, shop_id_list

    @classmethod
    def unsubscribe_count(cls, unsubscribes):
        event_id_list = []
        shop_id_list = []
        for obj in unsubscribes:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(unsubscribes), event_id_list, shop_id_list

    @classmethod
    def unsubscribe_pay(cls, unsubscribes):
        apportion = 0
        event_id_list = []
        shop_id_list = []
        for obj in unsubscribes:
            apportion += obj.get('apportion', 0)
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return round(apportion / 100.0, 2), event_id_list, shop_id_list

    @classmethod
    def unsubscribe_apportion(cls, unsubscribes):
        apportion = 0
        event_id_list = []
        shop_id_list = []
        for obj in unsubscribes:
            apportion += obj.get('apportion', 0)
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return apportion, event_id_list, shop_id_list

    @classmethod
    def count(cls, objs):
        event_id_list = []
        shop_id_list = []
        for obj in objs:
            event_id_list.append(obj.id)
            shop_id_list.append(obj.shop_id)
        return len(objs), event_id_list, shop_id_list

    @classmethod
    def expiring_renew_customer_count(cls, subscribes):
        sub_id_list = [sub.id for sub in subscribes]
        shop_id_list = list(set([sub.shop_id for sub in subscribes]))
        return len(shop_id_list), sub_id_list, shop_id_list

class CalculationFactory(object):

    @classmethod
    def renew_order_count(cls, cur_date, renew_orders):
        return [{'id':order.id, 'shop_id':order.shop_id} for order in renew_orders.get(cur_date, [])]

    @classmethod
    def renew_order_pay(cls, cur_date, renew_orders):
        return [{'id':order.id, 'shop_id':order.shop_id, 'pay':order.pay} for order in renew_orders.get(cur_date, [])]

    @classmethod
    def monthly50_subscribe_count(cls, cur_date, subscribes):
        return [sub for sub in subscribes.get(cur_date, []) if sub.monthly_pay >= 5000]

    @classmethod
    def expire_order_count(cls, cur_date, expire_orders):
        return [{'id':order.id, 'shop_id':order.shop_id} for order in expire_orders.get(cur_date, [])]

    @classmethod
    def new_people_count(cls, cur_date, new_orders):
        shop_set = set()
        cur_shop_list = []
        date_list = sorted(new_orders.keys())
        for temp_date in date_list:
            if temp_date < cur_date:
                order_list = new_orders.get(temp_date, [])
                for order in order_list:
                    shop_set.add(order.shop_id)
            elif temp_date == cur_date:
                cur_set = set(order.shop_id for order in new_orders.get(cur_date, []))
                cur_shop_list = list(cur_set - shop_set)
                break

        return [{'id':shop_id, 'shop_id':shop_id} for shop_id in cur_shop_list]

    @classmethod
    def contact_records(cls, cur_date, valid_contacts):
        return [{'id':contact._id.__str__(), 'shop_id':contact.shop_id, 'create_time':contact.create_time.strftime("%Y-%m-%d %H:%M:%S")}
                for contact in valid_contacts.get(cur_date, [])]

    @classmethod
    def lost_customer_people(cls, cur_date, lost_customers):
        return [{'id':shop_id, 'shop_id':shop_id} for shop_id in lost_customers.get(cur_date, [])]

    @classmethod
    def serving_people_count(cls, cur_date, serving_customers):
        return [{'id':customer.shop_id, 'shop_id':customer.shop_id} for customer in serving_customers.get(cur_date, [])]

    # @classmethod
    # def active_customer_count(cls, cur_date, active_customers):
    #     return [{'id': customer.shop_id, 'shop_id': customer.shop_id, 'logined': customer.logined, 'cost': customer.cost} for customer in active_customers.get(cur_date, [])]

    @classmethod
    def active_customer_count(cls, cur_date, active_customers):
        return [{'id': customer.shop_id, 'shop_id': customer.shop_id, 'cost': customer.cost} for customer in active_customers.get(cur_date, [])]

    @classmethod
    def extend_cycle(cls, cur_date, subscribes):
        return [{'id': subscribe.id, 'shop_id': subscribe.shop_id, 'mark':subscribe.mark} \
                for subscribe in subscribes.get(cur_date, [])]

    @classmethod
    def subscribe_month1_count(cls, cur_date, subscribes):
        return [{'id': subscribe.id, 'shop_id': subscribe.shop_id} for subscribe in subscribes.get(cur_date, []) if subscribe.cycle <= 2]

    @classmethod
    def subscribe_month3_count(cls, cur_date, subscribes):
        return [{'id': subscribe.id, 'shop_id': subscribe.shop_id} for subscribe in subscribes.get(cur_date, []) if 2 < subscribe.cycle <= 4]

    @classmethod
    def subscribe_month6_count(cls, cur_date, subscribes):
        return [{'id': subscribe.id, 'shop_id': subscribe.shop_id} for subscribe in subscribes.get(cur_date, []) if 4 < subscribe.cycle <= 7]

    @classmethod
    def subscribe_month12_count(cls, cur_date, subscribes):
        return [{'id': subscribe.id, 'shop_id': subscribe.shop_id} for subscribe in subscribes.get(cur_date, []) if subscribe.cycle > 7]

    @classmethod
    def reintro_count(cls, cur_date, reintros):
        return [{'id':reintro._id.__str__(), 'shop_id':reintro.shop_id} for reintro in reintros.get(cur_date, [])]

    @classmethod
    def good_comment_count(cls, cur_date, good_commonts):
        return [{'id':comment._id.__str__(), 'shop_id':comment.shop_id}
                for comment in good_commonts.get(cur_date, [])]

    @classmethod
    def change_comment_count(cls, cur_date, change_comments):
        return [{'id':comment._id.__str__(), 'shop_id':comment.shop_id}
                for comment in change_comments.get(cur_date, [])]

    @classmethod
    def renew_rate(cls, cur_date, renew_orders, expire_orders):
        renew_customers = list(set(order.shop_id for order in renew_orders.get(cur_date, [])))
        expire_customers = list(set(order.shop_id for order in expire_orders.get(cur_date, [])))
        return [{'renew_customers':renew_customers, 'expire_customers':expire_customers}]

    @classmethod
    def unknown_order_count(cls, cur_date, serving_orders):
        return [{'id':order.id, 'shop_id':order.shop_id} for order in serving_orders.get(cur_date, []) if order.biz_type == 6]

    @classmethod
    def bad_comment_count(cls, cur_date, bad_comments):
        return [{'id':comment._id.__str__(), 'shop_id':comment.shop_id} for comment in bad_comments.get(cur_date, [])]

    @classmethod
    def unsubscribe_count(cls, cur_date, unsubscribes):
        return [{'id':unsubscribe._id.__str__(), 'shop_id':unsubscribe.shop_id} for unsubscribe in unsubscribes.get(cur_date, [])]

    @classmethod
    def unsubscribe_pay(cls, cur_date, unsubscribes):
        return [{'id':unsubscribe._id.__str__(), 'shop_id':unsubscribe.shop_id, 'apportion':unsubscribe.apportion} for unsubscribe in unsubscribes.get(cur_date, [])]
