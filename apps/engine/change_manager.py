# coding=utf-8

"""
观察者模式：

将数据变动与业务解耦合的一种模式，举例：

用户登录了开车精灵，需要知会对应的顾问，可能还需要更新会话。
用户新订了一条订单，需要分配顾问，更新用户版本信息，以及知会市场人员。
等等，不一而足，传统的方式是直接在原来的逻辑里增加，这里修改成由ChangeManager负责

有事件发生时，只需要知会changemanager即可，manager再知会这个数据项对应的观察者。
最后再由每个观察者各自处理自己的逻辑。

"""
from apps.common.utils.utils_json import json
from apps.engine.models_channel import OrderChannel

def order_save_notify(content):
    OrderChannel.publish(json.dumps({'content': content, 'opt_type': 'save'}))

def order_close_notify(content):
    OrderChannel.publish(json.dumps({'content': content, 'opt_type': 'close'}))

def order_paid_notify(content):
    OrderChannel.publish(json.dumps({'content': content, 'opt_type': 'paid'}))



class ChangeManager(object):

    MAPPING_DICT = {
        'save_order': [order_save_notify],
        'order_closed': [order_close_notify],
        'order_paid': [order_paid_notify],
    }

    @classmethod
    def notify(cls, subject, change_data):
        for observer in cls.MAPPING_DICT.get(subject, []):
            observer(change_data)
