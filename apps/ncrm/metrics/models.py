# coding=UTF-8
import datetime
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, StringField, IntField, DateTimeField, ListField


class SubscribeAmount(EmbeddedDocument):
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    nick = StringField(verbose_name = "店铺昵称", required=True)
    sub_id = IntField(verbose_name = "订单ID", required = True)
    amount = IntField(verbose_name = "当日服务金额（单位：分）", required = True)


class MyCustomers(Document):
    """每日度量数据快照"""
    date_str = StringField(verbose_name = "日期字符串", required=True)
    psuser_id = IntField(verbose_name = "员工ID", required = True)
    rjjh_sub = ListField(verbose_name = '当日服务类目订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    ztc_sub = ListField(verbose_name = '当日服务直通车订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    zz_sub = ListField(verbose_name = '当日服务钻展订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    zx_sub = ListField(verbose_name = '当日服务装修订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    dyy_sub = ListField(verbose_name = '当日服务代运营订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    seo_sub = ListField(verbose_name = '当日服务seo订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    new_cust_sub = ListField(verbose_name = '当日新增账户订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    pause_sub = ListField(verbose_name = '当日暂停订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    unsub_sub = ListField(verbose_name = '当日退款订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    expire_sub = ListField(verbose_name = '当日流失订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    change_sub = ListField(verbose_name = '当日更换操作人订单', field = EmbeddedDocumentField(SubscribeAmount), required = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)

    meta = {'collection': 'ncrm_my_customers', 'shard_key': ['date_str'], 'indexes': ['psuser_id']}

mycust_coll = MyCustomers._get_collection()


