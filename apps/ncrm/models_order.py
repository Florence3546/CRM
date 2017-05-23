# coding=utf-8

from __future__ import unicode_literals

from mongoengine.fields import IntField, StringField, DateTimeField
from mongoengine.document import Document

from apps.common.utils.utils_datetime import string_2datetime
from apps.common.utils.utils_number import doublestr_2int
from apps.subway.models_parser import BaseParser, ParserField

from apps.engine.change_manager import ChangeManager
from apps.ncrm.models import ActivityCode

class FuwuOrderParser(BaseParser):

    biz_order_id = ParserField(field_name = u"biz_order_id", formatter = int)
    order_id = ParserField(field_name = u"order_id", formatter = int)
    activity_code = ParserField(field_name = u"activity_code", default = '')
    psuser_name_cn = ParserField(field_name=u"psuser_name_cn", default='')
    article_code = ParserField(field_name = u"article_code", default = '')
    article_name = ParserField(field_name = u"article_name", default = '')
    item_code = ParserField(field_name = u"item_code", default = '')
    item_name = ParserField(field_name = u"item_name", default = '')
    fee = ParserField(field_name = u"fee", formatter = doublestr_2int)
    nick = ParserField(field_name = u"nick")
    pay = ParserField(field_name = u"total_pay_fee", formatter = doublestr_2int)
    cycle = ParserField(field_name = u"order_cycle")
    biz_type = ParserField(field_name = u"biz_type", formatter = int)
    create_time = ParserField(field_name = u"create", formatter = string_2datetime)
    start_date = ParserField(field_name = u"order_cycle_start", formatter = string_2datetime)
    end_date = ParserField(field_name = u"order_cycle_end", formatter = string_2datetime)
    outer_trade_code = ParserField(field_name = u"outer_trade_code")
    order_status = ParserField(field_name = u"order_status", formatter = int)
    pay_status = ParserField(field_name = u"pay_status", formatter = int)
    version_no = ParserField(field_name = u"version_no", formatter = int)
    is_closed = ParserField(field_name = "is_closed", default = 0)


class FuwuOrder(Document):
    biz_order_id = IntField(verbose_name = "订单号")
    order_id = IntField(verbose_name = "子订单号id")
    activity_code = StringField(verbose_name = "活动代码")
    psuser_name_cn = StringField(verbose_name="所属人")
    article_code = StringField(verbose_name = "应用码")
    article_name = StringField(verbose_name = "应用名")
    item_code = StringField(verbose_name = "应用码")
    item_name = StringField(verbose_name = "应用名")
    fee = IntField(verbose_name = "原价")
    nick = StringField(verbose_name = "昵称")
    pay = IntField(verbose_name = "成交金额")
    cycle = StringField(verbose_name = "订购周期")
    biz_type = IntField(verbose_name = "订单类型", default = 1, choices = ((1, '新订'), (2, '续订'), (3, '升级'), (4, '后台赠送'), (5, '后台自动续订'), (6, '未知')))
    create_time = DateTimeField(verbose_name = "订单创建时间")
    start_date = DateTimeField(verbose_name = "服务开始日期")
    end_date = DateTimeField(verbose_name = "服务结束日期")
    outer_trade_code = StringField(verbose_name = "外部交易号")
    order_status = IntField(verbose_name = "订单状态", default = 1, choices = ((1, '订单合法'), (2, '订单非法'), (3, '订单完成'), (4, '订单确认')))
    pay_status = IntField(verbose_name = "付款状态", default = 0) # 1 代表已经付款
    version_no = IntField(verbose_name = "收费项目的版本序号")
    is_closed = IntField(verbose_name = "订单是否关闭", default = 0)

    note = StringField(verbose_name = "备注", default = "")
    note_time = DateTimeField(verbose_name = "备注时间")
    note_user = IntField(verbose_name = "备注人", default = 0)

    meta = {'db_alias': 'crm-db', 'collection': 'ncrm_fuwuorder', 'indexes': ['order_id', 'item_code', 'start_date', 'end_date', 'nick']}

    Parser = FuwuOrderParser

    @classmethod
    def save_order(cls, content):
        cls.insert_order(content)
        ChangeManager.notify('save_order', content)
        return True

    @classmethod
    def insert_order(cls, content):
        result_dict = cls.Parser.parse(content)
        activity_code = result_dict.get('activity_code')
        if activity_code:
            objs = ActivityCode.objects.filter(activity_code=activity_code)
            if objs:
                result_dict['psuser_name_cn'] = objs[0].name_cn
        cls._get_collection().insert(result_dict)
        return True

    @classmethod
    def order_paid(cls, order_id, content):
        # updated_result = cls._get_collection().update({'order_id': order_id }, {'$set': {'pay_status': 1}})
        # if updated_result['ok'] and updated_result['n'] > 0: # 数据库有记录，并且成功，则直接返回
        #     result = True
        # else: # 否则直接将获取到的数据写到db
        #     result = cls.insert_order(content)
        # ChangeManager.notify('order_paid', content)
        # return result
        cust = Customer.objects.filter(nick=content.nick)
        if cust:
            exist_sub = Subscribe.objects.filter(shop_id=cust[0].shop_id, article_code=content.article_code, create_time__gte=content.create_time)
            if exist_sub:
                cls._get_collection().remove({
                    'nick': content.nick,
                    'article_code': content.article_code,
                    'create_time': {'$lte': content.create_time}
                }, multi=True)
        return True


    @classmethod
    def order_closed(cls, order_id, content):
        updated_result = cls._get_collection().update({'order_id': order_id }, {'$set': {'is_closed': 1}})
        if updated_result['ok'] and updated_result['n'] > 0: # 数据库有记录，并且成功，则直接返回
            result = True
        else:
            content.is_closed = 1 # 默认取不到是0，这里将它置为1
            result = cls.insert_order(content)
        ChangeManager.notify('order_closed', content)
        return result