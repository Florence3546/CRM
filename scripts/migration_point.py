# coding=UTF-8
import init_environ
import time
from apps.router.models import Point
from apps.web.models import pa_coll
from apps.router.models import User
from django.core.exceptions import ObjectDoesNotExist

points = Point.objects.filter()

print '共有%s条数据' % (points.count())
# print points[0].nick_1
# print points[0].current_nick


def get_shop_id4nick(nick):
    try:
        user = User.objects.get(nick = nick)
        return user
    except ObjectDoesNotExist:
        return None

counter = 1
def save_point(data):
    global counter
    print '%s:%s' % (counter, data['desc'])
    counter = counter + 1
    pa_coll.insert(data)

def calc(point):
    return int(int(abs(point)) * 56.5)

def case1(obj): # 被邀请
    user = get_shop_id4nick(obj.nick_1)
    if user and user.shop_id:
        shop_id = user.shop_id
        data = {}
        data['shop_id'] = int(shop_id)
        data['type'] = 'invited'
        data['point'] = calc(obj.point_1)
        data['is_freeze'] = 0
        data['desc'] = '来自【%s】邀请' % (obj.nick_2)
        data['guide_name'] = obj.nick_2
        data['create_time'] = obj.create_time

        save_point(data)

def case2(obj): # 主动邀请
    user = get_shop_id4nick(obj.nick_2)
    if user and user.shop_id:
        shop_id = user.shop_id
        data = {}
        data['shop_id'] = int(shop_id)
        data['type'] = 'promotion'
        data['point'] = calc(obj.point_1)
        data['is_freeze'] = 0
        data['desc'] = '邀请【%s】' % (obj.nick_1)
        data['invited_name'] = obj.nick_1
        data['create_time'] = obj.create_time

        save_point(data)

def case3(obj): # 兑换优惠链接
    user = get_shop_id4nick(obj.nick_1)
    if user and user.shop_id:
        shop_id = user.shop_id
        data = {}
        data['shop_id'] = int(shop_id)
        data['type'] = 'discount'
        data['point'] = -calc(obj.point_1)
        data['is_freeze'] = 0
        data['order_version'] = obj.order_version
        data['order_cycle'] = obj.order_cycle
        data['order_price'] = 0
        data['desc'] = '兑换开车精灵【%s】,订购时长%s' % (obj.order_version, obj.order_cycle)
        data['create_time'] = obj.create_time

        save_point(data)

def case7(obj): # 系统待减少
#    user = get_shop_id4nick(obj.nick_1)
#     if user and user.shop_id:
#         shop_id=user.shop_id
#         data = {}
#         data['shop_id'] = int(shop_id)
#         data['type']='discount'
#         data['point'] = -int(obj.order_version)
#         data['is_freeze'] = 1
#         data['order_version'] = None
#         data['order_cycle'] = None
#         data['order_price'] = 0
#         data['desc'] = '兑换开车精灵'
#         data['create_time'] = obj.create_time
    pass

def case5(obj): # 砸金蛋活动
    user = get_shop_id4nick(obj.nick_1)
    if user and user.shop_id:
        shop_id = user.shop_id
        data = {}
        data['shop_id'] = int(shop_id)
        data['type'] = 'breakegg'
        data['point'] = calc(obj.point_1)
        data['is_freeze'] = 0
        data['desc'] = '砸金蛋活动'
        data['create_time'] = obj.create_time

        save_point(data)

def case6(obj): # 活动赠送
    user = get_shop_id4nick(obj.nick_1)
    if user and user.shop_id:
        shop_id = user.shop_id
        data = {}
        data['shop_id'] = int(shop_id)
        data['type'] = 'others'
        data['point'] = calc(obj.point_1)
        data['is_freeze'] = 0
        data['desc'] = '活动赠送'
        data['create_time'] = obj.create_time

        save_point(data)


for p in points:
    p.current_nick
    type = p.note_type

    if type == 2: # 插入两条数据
        case1(p) # 邀请       nick1是被邀请人nick2是邀请人
        case2(p) # 被邀请

    if type == 3: # 兑换优惠链接
        case3(p)
#     if type==4:  #没有该情况
#         case4(p)
    if type == 5: # 砸金蛋活动
        case5(p)
    if type == 6: # 系统默认增加
        case6(p)
    if type == 7: # 系统待减少
        case7(p)
    if type == 8: # 活动赠送
        case6(p)
