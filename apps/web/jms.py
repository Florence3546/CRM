# coding=UTF-8

from apilib.app import QNApp
from apps.common.utils.utils_datetime import generate_timestamp
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.router.models import User
from apps.ncrm.models_order import FuwuOrder
from apps.subway.models_adgroup import Adgroup
from apps.subway.models_item import Item
from apps.subway.models_keyword import Keyword

class MsgManager(object):

    @classmethod
    def handle(cls, topic, data):
        # data是经过DictWrapper包装过的字典，可以直接通过.运算符取值
        return getattr(cls, topic, 'echo')(data)

    @staticmethod
    def echo(data):
        log.info(data)

    @staticmethod
    def taobao_fuwu_OrderCreated(data):
        """
        data-->sample
        {
            u'content': u'{
                "refund_fee": "0",
                "biz_type": 1,
                "order_cycle": "2",
                "article_name": "\u5f00\u8f66\u7cbe\u7075_\u5168\u81ea\u52a8\u62a2\u6392\u540d_\u6548\u679c",
                "article_code": "ts-25811",
                "order_id": 105156208250654,
                "create": "2015-12-24 10:10:04",
                "order_status": 1,
                "pay_status": 0,
                "activity_code": "ACT_836440495_140508171844",
                "biz_order_id": 105156208230654,
                "fee": "66000.0",
                "prom_fee": "39000.0",
                "order_cycle_end": "2016-03-24 00:00:00",
                "total_pay_fee": "27000.0",
                "item_code": "ts-25811-8",
                "nick": "\u5361\u54c7\u4f9d\u599e",
                "item_name": "\u4e13\u4e1a\u7248_\u53cc\u5f15\u64ce",
                "version_no": 3,
                "order_cycle_start": "2015-12-24 00:00:00",
                "outer_trade_code": ""
            }',
            u'topic': u'taobao_fuwu_OrderCreated',
            u'publish_time': 1450923004062,
            u'publisher_appkey': u'12497914',
            u'outgoing_id': 5100401188183883118
        }
        """
        return FuwuOrder.save_order(data.content)

    @staticmethod
    def taobao_fuwu_OrderClosed(data):
        """消息体格式如上，可能没有activity_code"""
        return FuwuOrder.order_closed(data.content.order_id, data.content)

    @staticmethod
    def taobao_fuwu_OrderPaid(data):
        """消息体格式如上"""
        return FuwuOrder.order_paid(data.content.order_id, data.content)

    #
    # @staticmethod
    # def fuwu_confirm_Success(data):
    #     pass
    #
    # @staticmethod
    # def fuwu_confirm_Fail(data):
    #     pass

    @staticmethod
    def taobao_item_ItemDelete(data):
        """
        data-->sample
        {
            "content": {"num_iid":525094586026},
            "topic": "taobao_item_ItemDelete",
            "outgoing_id": 5091501188142226555,
            "publish_time": 1450922371056,
            "user_id": 62073298,
            "user_nick": "zyz0455",
            "publisher_appkey": "12497914"
        }
        """


        item_id = data.content.num_iid
        try:
            user = User.objects.get(user_id = data['user_id'])
            Item.remove_item(user.shop_id, [item_id])
        except User.DoesNotExist: # 找不到就不管这个item
            pass
        return True

    @staticmethod
    def taobao_item_ItemPunishDelete(data):
        handle_reuslt = MsgManager.taobao_item_ItemDelete(data)
        # TODO: wangqi 这里可以通过短信知会用户？
        return handle_reuslt

    @staticmethod
    def taobao_item_ItemPunishDownshelf(data):
        """
        data-->sample
        {
            u'topic': u'taobao_item_ItemPunishDownshelf',
            u'publish_time': 1450253827872,
            u'user_id': 38352809,
            u'publisher_appkey': u'12497914',
            u'user_nick': u'\u56fd\u7389\u4e4b\u4e61',
            u'content': u'{
                "num_iid": 525078200576
            }',
            u'outgoing_id': 4162901165157287277
        }
        """
        item_id = data.content.num_iid
        try:
            user = User.objects.get(user_id = data['user_id'])
        except User.DoesNotExist:
            pass
        Adgroup._get_collection().update({'shop_id': user.shop_id, 'item_id':item_id},
                                         {'$set': {'online_status':'offline', 'offline_type':'audit_offline'}}, multi = True)
        return True


class ItemMsgManager():
    """
    .宝贝增删改消息管理,使用淘宝返回的topic作为函数名,作为属性直接获取到处理结果
    """
    cache_10s_dict = {}

    def __init__(self, item_id, shop_id, message):
        self.item_id = item_id
        self.shop_id = shop_id
        self.message = message

    @classmethod
    def check_dup_item_msg(cls, item_id):
        """
        .为解决商品因为不同的sku而发送重复update消息，这里设置一个10s缓存字典来过滤重复消息
        .如果10s内，重复发送2个item_id一样的消息，则直接过滤，否则将进行处理
        """
        if not cls.cache_10s_dict:
            key = generate_timestamp()
            cls.cache_10s_dict[key] = {item_id:1}
            return True
        else:
            key_old = cls.cache_10s_dict.keys()[0]
            key_new = generate_timestamp()
            if key_new - key_old >= 10:
                cls.cache_10s_dict = {}
                cls.cache_10s_dict[key_new] = {item_id:1}
                return True
            else:
                if item_id in cls.cache_10s_dict[key_old]:
                    return False
                else:
                    cls.cache_10s_dict[key_old][item_id] = 1
                    return True

    @classmethod
    def update_adgroups_byitem_id(cls, item_id, arg_dict):
        Adgroup._get_collection().update({'item_id':item_id}, {'$set':arg_dict}, multi = True)

    @classmethod
    def delete_all_relate_byitem(cls, item_id):
        Item.objects.filter(item_id = item_id).delete()
        adg_id_list = [adg.adgroup_id for adg in Adgroup.objects.filter(item_id = item_id)]
        Adgroup.objects.filter(adgroup_id__in = adg_id_list).delete()
        Keyword.objects.filter(adgroup_id__in = adg_id_list).delete()

    @classmethod
    def is_item_exist(cls, item_id):
        cursor = Item._get_collection().find({'_id':item_id})
        return cursor.count()

    @property
    def taobao_item_ItemDownshelf(self):
        """
        .宝贝下架之后,需要修改item的下架时间,直接修改adgroup的状态为offline
        """
        ItemMsgManager.update_adgroups_byitem_id(self.item_id, {'online_status':'offline'})

    @property
    def taobao_item_ItemDelete(self):
        """
        .宝贝删除之后,需要删除item,删除跟item相关的所有的adgroup,删除和adgroup所有相关的keyword
        """
        ItemMsgManager.delete_all_relate_byitem(self.item_id)

    @property
    def taobao_item_ItemUpdate(self):
        """
        .宝贝修改之后,需要调取taobao.item.get接口,重新获取到所有的宝贝信息,并且刷新到item表当中
        """
        Item.sync_item_byids(shop_id = self.shop_id, tapi = QNApp.get_tapi(self.shop_id), item_id_list = [self.item_id])
        Item.delete_item_cache_byitemid(self.item_id)

    @property
    def taobao_item_ItemUpshelf(self):
        """
        .宝贝上架之后,和下架一样,直接修改adgroup的状态为online
        """
        ItemMsgManager.update_adgroups_byitem_id(self.item_id, {'online_status':'online'})

    @property
    def taobao_item_ItemPunishDownshelf(self):
        """
        .小二下架商品消息,和用户下架商品一样,同步adgroup
        """
        ItemMsgManager.update_adgroups_byitem_id(self.item_id, {'online_status':'offline', 'offline_type':'audit_offline'})

    @property
    def taobao_item_ItemPunishDelete(self):
        """
        .小二删除商品消息,和用户删除商品消息一样,需要删除item,删除跟item相关的所有的adgroup,删除和adgroup所有相关的keyword
        """
        ItemMsgManager.delete_all_relate_byitem(self.item_id)

