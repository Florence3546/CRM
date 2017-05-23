# coding=UTF-8
# 各种活动积分
# 钟进峰   2015.04.08
import datetime
import collections

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_log import log
from apps.common.biz_utils.utils_permission import ORDER_VERSION_DICT
from apps.common.utils.utils_datetime import get_start_datetime, get_end_datetime
from apps.ncrm.models import Subscribe, Customer
from apps.router.models import User, ArticleUserSubscribe
from apps.subway.models_account import Account, account_coll
from apps.web.models import pa_coll, MemberStore, OrderTemplate

class PointManager(object):

    TO_EMAIL = ("zhupeng@paithink.com",) # 兑换物品后发送邮箱

    _type_choices = collections.OrderedDict() # 临时代码，该部分需要重构
    _type_choices['gift'] = "实物兑换"
    _type_choices['virtual'] = "虚拟物品兑换"
    _type_choices['discount'] = "代金券换购"
    _type_choices['promotion'] = "分享邀请"
    _type_choices['invited'] = "分享购买"
    _type_choices['promotion4shop'] = "主动邀请"
    _type_choices['invited4shop'] = "邀请购买"
    _type_choices['appraise'] = "好评送分"
    _type_choices['pointmodify'] = "修改积分"

    _type_choices['sign'] = "签到送分"
    _type_choices['pperfectphone'] = "手机验证"
    _type_choices['login'] = "登陆送分"
    _type_choices['renewal'] = "续订软件"
    _type_choices['perfectinfo'] = "完善个人信息"
    _type_choices['perfectinfo'] = "完善个人信息"
    _type_choices['expired'] = "过期扣分"

    _invited_dict = {
                   u'1个月':1000,
                   u'3个月':1500,
                   u'6个月':2000,
                   u'12个月':2500,
                   }

    _promotion_dict = {
                '1000':1500,
                '1500':2500,
                '2000':4000,
                '2500':5000,
                }

    @classmethod
    def get_type_desc(cls, type_str):
        return cls._type_choices.get(type_str, "")

    @classmethod
    def get_types(cls):
        return cls._type_choices.keys()

    @classmethod
    def get_default_types(cls):
        return ['gift', 'virtual']

    @classmethod
    def get_filter_types(cls):
        return ['gift', 'virtual', 'discount', 'promotion', 'invited', 'promotion4shop', 'invited4shop', 'appraise', 'pointmodify']

    @classmethod
    def get_type_choices(cls, is_crm = False):
        if is_crm:
            return [(key, val) for key, val in cls._type_choices.items() if key in cls.get_filter_types() ]
        return [(key, val) for key, val in cls._type_choices.items()]

    @classmethod
    def add_point_record(cls, **args):
        """计算积分"""
        is_valid, msg, data = cls.calc_point(**args)

        if is_valid:
            data['type'] = cls.__name__.lower()
            data['create_time'] = datetime.datetime.now()

            shop_id = data['shop_id']
            cust = Customer.objects.get(shop_id = shop_id)
            data['nick'] = cust.nick
            data['consult_id'] = cust.consult_id
            data['consult_flag'] = 0
            if int(data['point']) < 0: # 小于0表示消费积分，要判断是否有足够的积分
                current_point = cls.get_point(shop_id = shop_id)
                if abs(int(data['point'])) > current_point:
                    return False, '您没有足够的积分', data

            result = pa_coll.insert(data)

            if result:
                if int(data['point']) > 0: # 大于0表示增加积分，此时与历史最高积分进行对比，如果大于历史积分则改写历史
                    current_point = cls.get_point(shop_id = shop_id)
                    history_highest_point = Account.get_history_highest_point(shop_id = shop_id)

                    if history_highest_point < current_point:
                        Account.update_history_highest_point(shop_id = data['shop_id'], point = current_point)

                if cls.__name__.lower() in ['gift', 'virtual']:
                    cls.send_email(data)

                cls.refresh_points_4shop(shop_id = shop_id) # 刷新缓存

                return True, '', data
            else:
                return False, '服务器出现了一点问题，请联系顾问,错误码【change point】', data
        else:
            log.info('add_point_record err_msg=%s type=%s, shop_id = %s' % (msg, cls.__name__.lower(), args.get('shop_id', 'None')))
            return False, msg, data

    @classmethod
    def calc_point(cls, **args):
        return False, '请重写该方法', {}

    @classmethod
    def get_point(cls, shop_id, condition = {}):
        """计算积分"""

        match_dict = {
                        'shop_id': int(shop_id),
                        'is_freeze': 0
                    }

        if condition:
            match_dict.update(condition)

        result = pa_coll.aggregate([{
                    "$match":match_dict
                },
                {
                    "$group": {
                        "_id": None,
                        "count": {
                            "$sum": '$point'
                        }
                    }
                }])

        if result['ok']:
            return result['result'] and result['result'][0]['count'] or 0
        else:
            return 0

    @classmethod
    def get_used_point(cls, shop_id):
        """计算已经使用的积分"""
        result = cls.get_point(shop_id = shop_id, condition = {'point':{'$lt':0}})
        return abs(result)

    @classmethod
    def get_freeze_point(cls, shop_id):
        """计算冻结的积分"""
        result = cls.get_point(shop_id = shop_id, condition = {'is_freeze':1})
        return result

    @classmethod
    def get_user(cls, condition):
        """获取用户"""
        try:
            if isinstance(condition, int) or isinstance(condition, long) or condition.isdigit():
                user = User.objects.get(shop_id = condition)
            else:
                user = User.objects.get(nick = condition)
            return user
        except ObjectDoesNotExist:
            return None

    @classmethod
    def get_subscribe(cls, shop_id):
        """获取订单"""
        subscribe = Subscribe.objects.filter(shop = shop_id, item_code__in = ORDER_VERSION_DICT.keys())
        return subscribe

    @classmethod
    def refresh_points_4shop(cls, shop_id):
        """刷新金领币缓存"""

        shop_id = int(shop_id)
        points = cls.get_point(shop_id)
        CacheAdpter.set(CacheKey.WEB_JLB_COUNT % shop_id, points, 'web', 60 * 30)
        return points

    @classmethod
    def refresh_points_4nick(cls, nick):
        """根据nick刷新金领币缓存"""
        shop_id = cls.get_user(nick).shop_id
        points = cls.get_point(shop_id)
        CacheAdpter.set(CacheKey.WEB_JLB_COUNT % shop_id, points, 'web', 60 * 30)
        return points

    @classmethod
    def get_point_detail(cls, shop_id):
        """获取可用金领币的使用详情"""
        result = pa_coll.find({'shop_id':int(shop_id), 'is_freeze':0}).sort("create_time", -1)
        return list(result)

#     @classmethod
#     def get_exchange_gift_count(cls, gift_type = None, type = None):
#         """获取兑换礼物的人数"""
#         if gift_type:
#             result = pa_coll.find({'is_freeze':0, 'gift_type':gift_type}).count()
#         if type:
#             result = pa_coll.find({'is_freeze':0, 'type':type}).count()
#         return result

    @classmethod
    def send_email(cls, data):

        if not settings.DEBUG:
            subject = '兑换物品：shop_id:%s,描述:%s' % (data['shop_id'], data['desc'])
        else:
            subject = '【本地测试】兑换物品：shop_id:%s,描述:%s' % (data['shop_id'], data['desc'])
        content = '兑换物品：shop_id:%s,描述:%s,请尽快为上帝发货，谢谢。该邮件自动发送，请勿回复。' % (data['shop_id'], data['desc'])
        send_email = send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, PointManager.TO_EMAIL)
        return send_email

class Sign(PointManager):
    """签到积分"""

    @classmethod
    def get_attendance_day(cls, shop_id):
        """获取连续签到天数"""
        yesterday = datetime.date.today() - datetime.timedelta(days = 1)
        result = pa_coll.find_one({'shop_id':int(shop_id), 'type':'sign', 'create_time':{'$gte':get_start_datetime(dt = yesterday), '$lte':get_end_datetime(dt = yesterday)}})
        if cls.is_sign_today(shop_id = shop_id):
            if result:
                return result['attendance_day'] + 1
            else:
                return 1
        else:
            if result:
                return result['attendance_day']
            else:
                return 0

    @classmethod
    def is_sign_today(cls, shop_id):
        result = pa_coll.find_one({'shop_id':int(shop_id), 'type':'sign', 'create_time':{'$gte':get_start_datetime()}})
        if result:
            return True
        else:
            return False

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])
        if not cls.is_sign_today(shop_id = shop_id):

            attendance_day = cls.get_attendance_day(shop_id = shop_id) + 1

            if attendance_day == 1: # 第一天签到2,第二天4
                point = 20
            elif attendance_day >= 2:
                point = 40

            data = {}
            data['shop_id'] = shop_id
            data['point'] = point
            data['is_freeze'] = 0
            data['attendance_day'] = attendance_day #
            data['desc'] = '签到送积分，连续第%s天' % (attendance_day)

            return True, '', data
        else:
            return False, '已经签过了', {}

class Promotion(PointManager):
    """邀请积分"""
    @classmethod
    def calc_point(cls, **args):

        user = cls.get_user(args['guide_name'])

        data = {}
        data['shop_id'] = int(user.shop_id)
#         if args['point'] == 1000: # 表示推荐人订购的是半年以下
#             args['point'] = 2000
#         if args['point'] == 2000: # 表示推荐人订购的是半年以上
#             args['point'] = 5000
        data['point'] = cls._promotion_dict[str(args['point'])]
        data['is_freeze'] = 0
        data['desc'] = '邀请【%s】' % (args['invited_name'])
        data['invited_name'] = args['invited_name']

        data['order_version'] = args['order_version']
        data['order_desc'] = args['order_desc']
        data['order_cycle'] = args['order_cycle']
        data['current_price'] = args['current_price']
        data['original_price'] = args['original_price']

        return True, '', data

class Invited(PointManager):
    """被邀请积分"""

    @classmethod
    def is_invited(cls, shop_id):
        """是否被邀请过"""
        result = pa_coll.find_one({"shop_id":shop_id, 'type':{'$in':['invited', 'invited4shop']}})
        if result:
            return True
        else:
            return False

    @classmethod
    def get_referrer_point(cls, shop_id):
        obj, point, msg = None, 0, ''
        subscribe = cls.get_subscribe(shop_id).order_by('create_time')
        if not subscribe:
            log.info('user has no artciclebizorder, shop_id = %s' % shop_id)
            msg = '您是今天刚订购精灵的吧？由于淘宝延时，我们还没有获取到您的订单，请24小时后再重试'
        elif subscribe[0].end_date < datetime.date.today():
            msg = '您已超过填写推荐人的期限（必须是在首次订购精灵期间填写推荐人）'
        elif cls.is_invited(shop_id):
            msg = '您已经被邀请过，不能再参加活动了'
        else:
            obj = subscribe[0]

            if (obj.cycle == "1个月" and obj.pay < 3000) or (obj.cycle == "3个月" and obj.pay < 8000) or \
               (obj.cycle == "6个月" and obj.pay < 15000) or (obj.cycle == "12个月" and obj.pay < 28000):
                msg = '您不是通过正常渠道订购开车精灵的'
            else:
#                 if obj.cycle == "1个月" or obj.cycle == "3个月":
#                     point = 1000
#                 if obj.cycle == "6个月" or obj.cycle == "12个月":
#                     point = 2000
                point = cls._invited_dict[obj.cycle]
        return msg, obj, point

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])
        subscribe = cls.get_subscribe(shop_id)
        last_subscribe = subscribe and subscribe.order_by('-create_time')[0] or None
        msg, obj, point = cls.get_referrer_point(shop_id)
        if msg:
            return False, msg, {}
        elif not cls.get_user(args['guide_name']):
            msg = "推广人不存在"
            return False, msg, {}
        elif not last_subscribe:
            msg = "订单不存在"
            return False, msg, {}
        else:
            data = {}
            data['shop_id'] = shop_id
            data['point'] = point
            data['is_freeze'] = 0
            data['desc'] = '来自【%s】邀请' % (args['guide_name'])
            data['guide_name'] = args['guide_name']

            data['order_version'] = last_subscribe.item_code
            data['order_desc'] = ORDER_VERSION_DICT[last_subscribe.item_code][1]
            data['order_cycle'] = last_subscribe.cycle
            data['current_price'] = last_subscribe.pay
            data['original_price'] = last_subscribe.fee

            return True, '', data

    @classmethod
    def add_point_record(cls, shop_id, guide_name):
        user = cls.get_user(shop_id)
        guide_user = cls.get_user(guide_name)

        if guide_user and guide_user.date_joined >= user.date_joined: # 此处加等于是避免自己推荐自己的情况
            return False, '亲，我掐指一算，发现不是该用户介绍您使用开车精灵的……', {}

        is_valid, msg, data = super(Invited, cls).add_point_record(shop_id = shop_id, guide_name = guide_name)
        if is_valid:
            data['invited_name'] = user.nick
            is_valid2, msg2, data2 = Promotion.add_point_record(**data)
            if not is_valid2:
                log.info('Promotion add_point_record error e=%s' % (msg2))

        return is_valid, msg, data

class ShopPointManager(object):
    _instance = None
    update_time = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance or (cls.update_time and \
               (cls.update_time - datetime.datetime.now()).total_seconds() > 60 * 60 * 24):
            cls._instance = {ms.id :ms \
                      for ms in MemberStore.query_present_templates()}
            cls.update_time = datetime.datetime.now()
        return cls._instance

class Discount(PointManager):
    """换购软件"""

    @classmethod
    def is_exist(cls, shop_id, order_version, order_cycle):
        """是否有重复的记录"""
        result = pa_coll.find_one({"shop_id":shop_id, 'type':'discount', 'is_freeze':1, 'order_version':order_version, 'order_cycle':order_cycle})
        if result:
            return True, result
        else:
            return False, {}

    @classmethod
    def calc_point(cls, shop_id , order_template):
        shop_id = int(shop_id)
        gift = MemberStore.get_ticket_bydiscount(order_template.discount)
        if not gift:
            return False, '兑换礼品以不存在，请联系客服', None

        is_exist, point_record = cls.is_exist(shop_id, order_template.version, order_template.cycle)
        if not is_exist:
            user = cls.get_user(shop_id)
            is_usable = ArticleUserSubscribe.check_is_usable(nick = user.nick, item_code = order_template.version)

            if is_usable:
                data = {}
                data['shop_id'] = shop_id
                data['point'] = -gift.point
                data['is_freeze'] = 0
                data['desc'] = '兑换开车精灵【%s】,订购时长%s个月' % (ORDER_VERSION_DICT[order_template.version][1], order_template.cycle)
                data['order_version'] = order_template.version
                data['order_cycle'] = order_template.cycle
                data['order_price'] = order_template.ori_price
                data['param_str'] = order_template.param_str
                return True, '', data
            else:
                return False, '根据淘宝规范，如果用户已购买一个产品的高级版本，则在该版本有效期内，不能购买该产品的低级版本 ,请订购四引擎版', {}
        else:
            return False, '已经存在该记录', point_record

    @classmethod
    def check_watting_point(cls, shop_id):
        """当用户续订了，检查订单开始时间在待等待减少的精灵币之后就减去精灵币"""

        subscribe = cls.get_subscribe(shop_id)
        last_subscribe = subscribe and subscribe.order_by('-create_time')[0] or None
        if last_subscribe:
            is_exist, point_record = cls.is_exist(shop_id, last_subscribe.item_code, last_subscribe.cycle.replace('个月', ''))

            if last_subscribe and is_exist and last_subscribe.start_date >= point_record['create_time'].date():
                result = pa_coll.update({"_id":point_record['_id']}, {"$set":{"is_freeze":0, "create_time":datetime.datetime.now()}})

                if result['ok'] and result['updatedExisting']:
                    cls.refresh_points_4shop(shop_id = shop_id) # 刷新缓存
                    return True
                else:
                    log.error('check_watting_point error, shop_id = %s' % shop_id)
                    return False
            else:
                return False
        else:
            return False

class Gift(PointManager):
    """实物礼品"""

    @classmethod
    def is_limit(cls, shop_id, gift):
        current_point = cls.get_point(shop_id = shop_id)
        if not gift.limit_point or current_point >= gift.limit_point:
            result = pa_coll.find({'shop_id':shop_id, 'type':'gift', 'gift_id':gift.id}).sort([('create_time', -1)])
            result = result.count() and result[0] or None
            if result:
                last_create_time = result['create_time']
                if (last_create_time + datetime.timedelta(days = 30)) < datetime.datetime.now():
                    return True, ''
                else:
                    return False, '您这个月已经兑换过啦，请下个月在来兑换吧！'
            else:
                return True, ''
        else:
            return False, '限制{}积分的用户才能兑换实物'.format(gift.limit_point)

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])
        gift_id = int(args['gift_id'])

        user = cls.get_user(shop_id)

        gift = ShopPointManager()[gift_id]
        is_valid, msg = cls.is_limit(shop_id = shop_id, gift = gift)
        if is_valid:

            data = {}
            data['shop_id'] = shop_id
            data['nick'] = user.nick
            data['point'] = -gift.point
            data['is_freeze'] = 0
            data['gift_id'] = gift_id
            data['logistics_id'] = '' # 物流单号
            data['logistics_name'] = '' # 物流公司
            data['logistics_state'] = 0 # 物流状态
            data['desc'] = '兑换【%s】' % (gift.name)

            return True, '', data
        else:
            return False, msg, {}

class Virtual(PointManager):
    """虚拟物品"""

    @classmethod
    def is_limit(cls, shop_id, gift):
        # 暂不进行重构操作，该行为理论上应与上面一致。
        current_point = cls.get_point(shop_id = shop_id)
        if not gift.limit_point or current_point >= gift.limit_point:
            result = pa_coll.find({'shop_id':shop_id, 'type':'virtual', 'gift_id':gift.id}).sort([('create_time', -1)])
            result = result.count() and result[0] or None
            if result:
                last_create_time = result['create_time']
                if (last_create_time + datetime.timedelta(days = 30)) < datetime.datetime.now():
                    return True, ''
                else:
                    return False, '您这个月已经兑换过啦，请下个月在来兑换吧！'
            else:
                return True, ''

        else:
            return False, '限制{}积分的用户才能兑换实物'.format(gift.limit_point)

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])
        gift_id = int(args['gift_id'])

        gift = ShopPointManager()[gift_id]
        # 如果是兑换话费则判断是否满足条件

        user = cls.get_user(shop_id)
        is_valid, msg = cls.is_limit(shop_id = shop_id, gift = gift)
        if is_valid:
            data = {}
            data['shop_id'] = shop_id
            data['nick'] = user.nick
            data['point'] = -gift.point
            data['is_freeze'] = 0
            data['gift_id'] = gift_id
            data['exchange_status'] = 0 # 兑换状态
            data['desc'] = '兑换【%s】' % (gift.name)
            return True, '', data
        else:
            return False, msg, {}

class PperfectPhone(PointManager):
    """添加手机号"""

    @classmethod
    def is_exist(cls, shop_id):
        """是否有重复的记录"""
        result = pa_coll.find_one({"shop_id":shop_id, 'type':'pperfectphone'})
        if result:
            return True, result
        else:
            return False, {}

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])

        is_exist, point_record = cls.is_exist(shop_id)

        if not is_exist:
            data = {}
            data['shop_id'] = shop_id
            data['point'] = 500
            data['is_freeze'] = 0
            data['desc'] = '完善联系方式'

            return True, '', data
        else:
            return False, '重复记录', point_record

class Login(PointManager):
    """登录送积分"""

    @classmethod
    def is_exist(cls, shop_id):
        """是否有重复的记录"""
        result = pa_coll.find_one({'shop_id':int(shop_id), 'type':'login', 'create_time':{'$gte':get_start_datetime()}})
        if result:
            return True, result
        else:
            return False, {}

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])

        is_exist, point_record = cls.is_exist(shop_id)

        if not is_exist:
            data = {}
            data['shop_id'] = shop_id
            data['point'] = 20
            data['is_freeze'] = 0
            data['desc'] = '登录送积分'

            return True, '', data
        else:
            return False, '重复记录', point_record

class Appraise(PointManager):
    """好评送积分"""

    @classmethod
    def is_exist(cls, shop_id):
        """是否有重复的记录"""
        result = pa_coll.find({'shop_id':int(shop_id), 'type':'appraise'}).sort("create_time", -1)
        if result.count() >= 1:
            last_create_time = result[0]['create_time']
            if (last_create_time + datetime.timedelta(days = 30)) > datetime.datetime.today(): # 过去了30天
                return True, result[0]
            else:
                return False, {}
        else:
            return False, {}

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])
        # appraise_time = args['appraise_time']

        is_exist, point_record = cls.is_exist(shop_id)

        user = cls.get_user(shop_id)

        if not is_exist:
            data = {}
            data['shop_id'] = shop_id
            data['nick'] = user.nick
            data['point'] = 500
#             data['point'] = 1000
            data['is_freeze'] = 1
            # data['appraise_time'] = appraise_time
            data['desc'] = '好评送积分'

            return True, '', data
        else:
            return False, '重复记录', point_record

class Renewal(Discount):
    """续订软件"""

    @classmethod
    def is_exist(cls, shop_id, order_version, order_cycle):
        """是否有重复的记录"""
        result = pa_coll.find_one({"shop_id":shop_id, 'type':'renewal', 'is_freeze':1, 'order_version':order_version, 'order_cycle':order_cycle})
        if result:
            return True, result
        else:
            return False, {}

    @classmethod
    def calc_point(cls, **args):

        template = OrderTemplate.objects.get(id = int(args['template_id']))

        shop_id = int(args['shop_id'])

        is_exist, point_record = cls.is_exist(shop_id, template.version, template.cycle)

        if not is_exist:
            user = cls.get_user(shop_id)
            is_usable = ArticleUserSubscribe.check_is_usable(nick = user.nick, item_code = template.version)

            if is_usable:
                data = {}
                data['shop_id'] = shop_id
                data['point'] = 1000 if int(template.cycle) <= 6 else 2500
                data['is_freeze'] = 1
                data['desc'] = '订购开车精灵【%s】,订购时长%s个月' % (ORDER_VERSION_DICT[template.version][1], template.cycle)
                data['order_version'] = template.version
                data['order_cycle'] = str(template.cycle)
                return True, '', data
            else:
                return False, '根据淘宝规范，如果用户已购买一个产品的高级版本，则在该版本有效期内，不能购买该产品的低级版本 ,请订购四引擎版', {}
        else:
            return False, '已经存在该记录', point_record

class PerfectInfo(PointManager):
    """完善信息送积分"""
    # 待废弃

    @classmethod
    def is_exist(cls, shop_id):
        """是否有重复的记录"""
        result = pa_coll.find_one({"shop_id":shop_id, 'type':'perfectinfo'})
        if result:
            return True, result
        else:
            return False, {}

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])

        is_exist, point_record = cls.is_exist(shop_id)

        # user = cls.get_user(shop_id)

        if not is_exist:
            data = {}
            data['shop_id'] = shop_id
            data['point'] = 200
            data['is_freeze'] = 0
            data['desc'] = '完善收货信息'

            return True, '', data
        else:
            return False, '重复记录', point_record

class Expired(PointManager):

    """用户过期扣积分"""

    base_point = 200 # 每天扣200积分

    @classmethod
    def is_exist(cls, shop_id, deadline):
        """是否有重复的记录"""
        result = pa_coll.find_one({"shop_id": shop_id, 'type': 'expired', 'deadline':deadline})
        if result:
            return True, result
        else:
            return False, {}

    @classmethod
    def is_freezed(cls, shop_id):
        """用户是否手动冻结积分"""
        result = account_coll.find_one({"_id": shop_id})
        if result and result.has_key('freeze_point_deadline'):
            if result['freeze_point_deadline'] > datetime.datetime.now():
                return True
            else:
                return False
        else:
            return False

    @classmethod
    def get_last_expired_subscribe(cls, nick):
        """获取最后一次过期订单"""
        sbuscribe = ArticleUserSubscribe.objects.filter(nick = nick, article_code = 'ts-25811', deadline__lte = get_start_datetime()).order_by('-deadline')
        return sbuscribe and sbuscribe[0] or None

    @classmethod
    def get_current_order(cls, shop_id, nick):
        """获取当前正在使用订单"""
        item_code = ArticleUserSubscribe.get_hightest_item_code(nick = nick)

        subscribes = cls.get_subscribe(shop_id = shop_id).order_by('-create_time')
        subscribes = subscribes.filter(start_date__lte = get_start_datetime(), end_date__gte = get_start_datetime(), item_code = item_code)
        return subscribes and subscribes[0] or None

    @classmethod
    def get_deduct_point(cls, shop_id):
        nick = cls.get_user(shop_id).nick

        is_freeze = cls.is_freezed(shop_id = shop_id)

        if not is_freeze:

            last_subscribe = cls.get_last_expired_subscribe(nick = nick)

            if last_subscribe:
                # 判断是否已存在记录
                is_exist, _ = cls.is_exist(shop_id, last_subscribe.deadline)

                if not is_exist:
                    current_order = cls.get_current_order(shop_id = shop_id, nick = nick)

                    if last_subscribe.deadline.date().strftime('%Y-%m-%d') >= '2015-04-29':
                        # 判断过期订单时间是否小于当前订单
                        if current_order and last_subscribe.deadline.date() < current_order.start_date:
                            past_day = (current_order.start_date - last_subscribe.deadline.date()).days
                            return cls.base_point * past_day, past_day, last_subscribe.deadline, ''
                        else:
                            return None, None, None, '不满足订单时间条件，或者未获取到订单'
                    else:
                        return None, None, None, '只针对4月29号之后的订单有效'
                else:
                    return None, None, None, '重复记录'
            else:
                return None, None, None, '没有过期订购关系'
        else:
            return None, None, None, '用户手动冻结积分'

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])

        current_point = cls.get_point(shop_id)
        if current_point > 0:
            point, past_day, deadline, msg = cls.get_deduct_point(shop_id = shop_id)

            if point:
                data = {}

                if current_point > point: # 避免积分扣成负数
                    data['point'] = -point
                else:
                    data['point'] = -current_point

                data['shop_id'] = shop_id
                data['is_freeze'] = 0
                data['past_day'] = past_day
                data['deadline'] = deadline
                data['desc'] = '软件过期%s天' % (past_day)
                return True, '', data
            return False, msg, {}
        else:
            return False, '没有足够的积分可以扣除', {}

class Others(PointManager):
    """其他途径改变积分"""
    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])
        point = int(args['point'])
        desc = args['desc']

        data = {}
        data['shop_id'] = shop_id
        data['point'] = point
        data['is_freeze'] = 0
        data['desc'] = desc
        return True, '', data

class Promotion4Shop(PointManager):
    """邀请方式2，指定店铺送积分，db中存入主推人的信息，积分置为冻结"""
    @classmethod
    def calc_point(cls, **args):
        data = {}
        data['shop_id'] = args['shop_id']
        data['point'] = 0 # 再更新的时候修改为相应的值
        data['is_freeze'] = 1
        data['desc'] = '邀请【%s】' % (args['invited_name'])
        data['invited_name'] = args['invited_name']
        data['order_version'] = args['order_version']
        data['order_cycle'] = args['order_cycle']
        data['current_price'] = args['current_price']
        data['original_price'] = args['original_price']
        data['url'] = args['url']
        data['type'] = 'promotion4shop'
        return True, '', data

    @classmethod
    def get_promotion_4shop(cls, shop_id):
        """获取用户推荐店铺的列表及推荐成功与否的状态"""
        result = pa_coll.find({'shop_id':int(shop_id), 'type':'promotion4shop'}).sort("create_time", -1)
        return list(result)

    @classmethod
    def is_exists(cls, shop_id, invited_name, order_version, order_cycle):
        """是否邀请过该店家"""
        result = pa_coll.find_one({"shop_id":shop_id, 'type':'promotion4shop', 'invited_name':invited_name, 'order_version':order_version, 'order_cycle':order_cycle})
        if result:
            return True
        else:
            return False

    @classmethod
    def promotion_record_exists(cls, shop_id, invited_name):
        result = pa_coll.find_one({"shop_id":shop_id, 'type':'promotion4shop', 'invited_name':invited_name})
        if result:
            return True
        else:
            return False


class Invited4Shop(PointManager):
    """邀请方式2，指定店铺送积分，较验被推人登陆系统后，db中是否包含与我相关的推荐，有的话，主推信息解冻，新建一条被推信息"""
    @classmethod
    def is_invited_4shop(cls, shop_id):
        """是否被邀请过"""
        result = pa_coll.find_one({"shop_id":shop_id, 'type':{'$in':['invited', 'invited4shop']}, 'is_freeze':0})
        if result:
            return True
        else:
            return False

    @classmethod
    def update_promotion_4shop(cls, shop_id , nick, point):
        """解冻主推人的积分"""
        result = pa_coll.update({'shop_id':shop_id , 'invited_name': nick, 'type':'promotion4shop', 'is_freeze':1}, {'$set':{'is_freeze':0, 'point':point}})
        if result['ok'] and result['updatedExisting']:
            cls.refresh_points_4shop(shop_id = shop_id) # 刷新缓存
            return True
        else:
            return False

    @classmethod
    def get_8nick(cls, nick):
        """根据名称获取一条记录"""
        result = pa_coll.find_one({'invited_name':nick, 'type':'promotion4shop', 'is_freeze':1})
        return result

    @classmethod
    def get_referrer_point(cls, shop_id):
        obj, point, msg = None, 0, ''
        subscribe = cls.get_subscribe(shop_id).order_by('create_time')
        if not subscribe:
            log.info('user has no artciclebizorder, shop_id = %s' % shop_id)
            msg = '您是今天刚订购精灵的吧？由于淘宝延时，我们还没有获取到您的订单，请24小时后再重试'
        elif subscribe[0].end_date < datetime.date.today():
            msg = '您已超过填写推荐人的期限（必须是在首次订购精灵期间填写推荐人）'
        elif cls.is_invited_4shop(shop_id):
            msg = '您已经被邀请过，不能再参加活动了'
        else:
            obj = subscribe[0]

            if (obj.cycle == "1个月" and obj.pay < 3000) or (obj.cycle == "3个月" and obj.pay < 8000) or \
               (obj.cycle == "6个月" and obj.pay < 15000) or (obj.cycle == "12个月" and obj.pay < 28000):
                msg = '您不是通过正常渠道订购开车精灵的'
            else:
#                 if obj.cycle == "1个月" or obj.cycle == "3个月":
#                     point = 1000
#                 if obj.cycle == "6个月" or obj.cycle == "12个月":
#                     point = 2000
                point = cls._invited_dict[obj.cycle]
        return msg, obj, point

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])
        guide_shop_id = int(args['guide_shop_id'])
        guide_user = cls.get_user(guide_shop_id)
        msg, obj, point = cls.get_referrer_point(shop_id)
        if msg:
            return False, msg, {}
        elif guide_user is None:
            msg = "推广人不存在"
            return False, msg, {}
        else:
            data = {}
            data['shop_id'] = shop_id
            data['point'] = point
            data['is_freeze'] = 0
            data['desc'] = '来自【%s】邀请' % (guide_user.nick)
            data['guide_name'] = guide_user.nick
            data['type'] = 'invited4shop'
            return True, '', data

    @classmethod
    def add_point_record(cls, shop_id, nick):
        """邀请方式2，指定店铺送积分,存入被推人信息，更新主推人信息"""
        info = Invited4Shop.get_8nick(nick) # 查询出我是否被推荐过
        if not info:
            return False, '您没有被推荐的记录', {}
        # 如果有一条非冻结的记录也返回
        is_valid, msg, data = super(Invited4Shop, cls).add_point_record(shop_id = shop_id, guide_shop_id = info['shop_id']) # 添加一条被推荐人的信息
        if is_valid is True:
            is_updated = Invited4Shop.update_promotion_4shop(shop_id = info['shop_id'], nick = nick, point = cls._promotion_dict[str(data['point'])]) # 更新推荐人的积分
        else:
            log.info('Invited4Shop add_point_record error e=%s' % (msg))
        return is_valid, msg, data

class PointModify(PointManager):

    @classmethod
    def calc_point(cls, **args):
        shop_id = int(args['shop_id'])
        consult_id = int(args['consult_id'])
        point = int(args['point'])
        desc = args['desc']

        data = {}
        data['shop_id'] = shop_id
        data['point'] = point
        data['consult_id'] = consult_id
        data['is_freeze'] = 0
        data['desc'] = desc
        return True, '', data
