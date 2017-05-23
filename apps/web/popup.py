# coding=UTF-8
# 各种首页弹窗控制
# 钟进峰   2015.05.04

import re

from apps.common.utils.utils_datetime import get_start_datetime, datetime, string_2datetime, get_end_datetime, time_humanize, days_diff_interval
from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple
from apps.common.cachekey import CacheKey
from apps.web.models import main_ad_coll,MainAd


class LexicalAnalyze():
    """简单的词法分析，输入字符串和字典进行对比"""
    def __init__(self, data, condition_str):
        self.data = data
        self.condition_str = condition_str

    def calc_gt(self, k, v):
        return self.data[k] > v

    def calc_lt(self, k, v):
        return self.data[k] < v

    def calc_gte(self, k, v):
        return self.data[k] >= v

    def calc_lte(self, k, v):
        return self.data[k] <= v

    def calc_eq(self, k, v):
        return self.data[k] == v

    def calc_neq(self, k, v):
        return self.data[k] != v

    def analyze(self):
        """解析"""
        if '||' in self.condition_str:
            or_condition = re.split('\|\|', self.condition_str)
        else:
            or_condition = [self.condition_str, ]

        for o in or_condition:
            judge = True
            if '&&' in o:
                and_condition = re.split('\&\&', o)
            else:
                and_condition = [o, ]

            for a in and_condition:
                if self.calc_condition(a):
                    continue
                judge = False
                break

            if not judge: # 如果为假则继续下一次条件判断
                continue
            else:
                break

        return judge

    def calc_condition(self, condition):
        calc_dict = {
                   '>':self.calc_gt,
                   '<':self.calc_lt,
                   '>=':self.calc_gte,
                   '<=':self.calc_lte,
                   '==':self.calc_eq,
                   '!=':self.calc_neq
                   }

        condition_re = re.match('(.*)(>=|<=|<|>|==|!=)(.*)', condition)

        if condition_re:
            condition_tuple = condition_re.groups()

            is_vaild, key, value = self.get_vaild_condition(condition_tuple[0], condition_tuple[2]) # 获取有效的值，将字符串的值转换为有效值

            if is_vaild:
                return calc_dict[condition_tuple[1]](key, value)
            else:
                log.debug('key error data is 【%s】' % (condition))

        return False

    def get_vaild_condition(self, k, v):
        k = k.strip()
        v = v.strip()
        if self.data.has_key(k):
            if 'unicode' in str(type(self.data[k])):
                return True, k, v
            if 'int' in str(type(self.data[k])):
                return True, k, int(v)
            if 'datetime' in str(type(self.data[k])):
                return True, k, string_2datetime(v)
            if v.lower() == 'true':
                return True, k, True
            if v.lower() or v == 'False':
                return True, k, False
        return False, None, None

    def compar(self):
        return self.analyze()

class MainAds():
    def __init__(self, shop_id):
        self.user = self.get_user(shop_id)

        # 查询满足显示条件的广告1、需要显示，2、已投放的，3、在有效期内
        self.main_ads = get_main_ads()
        self.show_ads = {}

        if self.user:
            self.nick = self.user.nick
            self.shop_id = self.user.shop_id
            self.aus = self.get_aus()
            self.current_subscribe = self.get_current_subscribe()
            # 绑定各种数据
            self.data = {}
            try:
                self.data = CacheAdpter.get(CacheKey.WEB_POPUP_BIND_DATA_CACHE % self.shop_id, 'web', {})
                if not self.data:
                    for b in dir(self):
                        if 'bind_' in b:
                            eval('self.%s()' % b)
                    CacheAdpter.set(CacheKey.WEB_POPUP_BIND_DATA_CACHE % self.shop_id, self.data, 'web', 60 * 30)
            except Exception, e:
                log.error('bind datas error,e=%s, shop_id=%s' % (e, self.shop_id))

    def get_user(self, shop_id):
        """获取用户"""
        from django.core.exceptions import ObjectDoesNotExist
        from apps.router.models import User
        try:
            user = User.objects.get(shop_id = shop_id)
            return user
        except ObjectDoesNotExist:
            return None

    def filter_base_list(self, ad_list):
        """过滤基本数据 排除黑名单"""
        base_list = []
        for a in ad_list:
            if a.has_key('ad_blacklist') and self.user.nick in a['ad_blacklist'].split(','): # 黑名单判断
                log.debug('die width black_list id=%s' % a['_id'])
                continue
            base_list.append(a)
        return base_list

    def filter_senior_list(self, ad_list):
        """过滤高级条件"""
        senior_list = []
        base_list = self.filter_base_list(ad_list)
        for b in base_list:
            condition_type = b.get('condition_type','')
            if condition_type == 'condition': # 为指定条件
                la = LexicalAnalyze(self.data, b['ad_show_condition'])
                if la.analyze():
                    senior_list.append(b)
                else:
                    log.debug('die width analyze id=%s' % b['_id'])
            if condition_type == 'shop_list': # 为指定id
                if self.user.nick in b['ad_show_condition'].split(','):
                    senior_list.append(b)
                else:
                    log.debug('die width shop_list id=%s' % b['_id'])

        return senior_list

    def sort_ad_list(self, ad_list, senior = True):
        """排序并返回第一个"""
        senior_list = ad_list
        if senior:
            # '''如果有高级条件，还需过滤高级条件'''
            senior_list = self.filter_senior_list(ad_list)
        # 按权重排序
        senior_list.sort(cmp = lambda x, y: cmp(y['ad_weight'], x['ad_weight']))
        return senior_list and senior_list[0] or {}

    def get_senior_list(self, ad_position, senior = True):
        '''获取有高级条件的广告'''
        ad_list = []
        for main_ad in self.main_ads:
            if main_ad.get('ad_position','') == ad_position and ad_position != 'rightnotice':
                main_ad['obj_id'] = main_ad.get('_id', 0)
                ad_list.append(main_ad)
        return self.sort_ad_list(ad_list, senior)

    def get_right_notice(self):
        '''获取右侧公告'''
        mr_notices = []
        for main_ad in self.main_ads:
            try:
                if 'rightnotice' == main_ad.get('ad_position',''):
                    if '0' in main_ad.get('ad_user_type',''):
                        days = 0
                        if isinstance(main_ad['ad_put_time'], datetime.datetime):
                            dt = main_ad['ad_put_time'].date()
                            days = (datetime.date.today() - dt).days
                        main_ad['is_new'] = days <= 7
                        main_ad['ad_put_time'] = time_humanize(main_ad['ad_put_time'])
                        main_ad['obj_id'] = str(main_ad.get('_id', 0))
                        mr_notices.append(main_ad)
            except:
                pass
        mr_notices.sort(cmp = lambda x, y: cmp(y['ad_weight'], x['ad_weight']))
        return mr_notices or []

    def get_show_ad(self):
        ''' 获取需要显示的广告及公告 '''
        show_ad_dict = {}

        for ad_type in dict(MainAd.AD_POSITION_CHOICES):
            senior = True
            if ad_type in ['bottombanner','charlink']:
                senior = False
            show_ad_dict[ad_type] = self.get_senior_list(ad_type, senior)

        # 添加公告
        right_notice = self.get_right_notice()
        show_ad_dict['rightnotice'] = right_notice
        return show_ad_dict

    def get_showad_list(self):
        """获取当前用户展示的广告id列表"""
        adid_list = []
        for ad_type, ad in self.get_show_ad().items():
            if ad_type not in ['charlink','rightnotice']:
                adid_list.append(ad.get('_id', -1))
        return adid_list

    def get_aus(self):
        """获取用户订购关系"""
        from apps.router.models import ArticleUserSubscribe
        if not hasattr(self, '_aus'):
            self._aus = ArticleUserSubscribe.objects.filter(nick = self.nick, article_code = 'ts-25811').order_by('-deadline')
        return self._aus

    def get_current_subscribe(self):
        """获取用户订购关系"""
        from apps.ncrm.models import Subscribe

        if not hasattr(self, '_subscribe'):
            subscribes = Subscribe.objects.filter(shop = self.shop_id, start_date__lte = get_start_datetime(), end_date__gt = get_start_datetime(), article_code = 'ts-25811').order_by('-create_time')
            self._subscribe = subscribes and subscribes[0] or None
        return self._subscribe

    def bind_order_times(self):
        """订单够关系数量"""
        self.data['order_times'] = self.aus.count()

    def bind_used_days(self):
        """当前订购时间已经使用的天数"""
        if self.current_subscribe:
            self.data['used_days'] = (datetime.date.today() - self.current_subscribe.start_date).days

    def bind_item_code(self):
        """订购代码"""
        if self.current_subscribe:
            self.data['item_code'] = self.current_subscribe.item_code

    def bind_pay(self):
        """付款金额"""
        if self.current_subscribe:
            self.data['pay'] = self.current_subscribe.pay

    def bind_cycle(self):
        """订购周期"""
        if self.current_subscribe:
            self.data['cycle'] = int(self.current_subscribe.cycle.replace('个月', '').replace('月', ''))

    def bind_create_time(self):
        """订单创建时间"""
        if self.current_subscribe:
            self.data['create_time'] = self.current_subscribe.create_time

    def bind_start_date(self):
        """订单开始时间"""
        if self.current_subscribe:
            self.data['start_date'] = get_start_datetime(self.current_subscribe.start_date)

    def bind_end_date(self):
        """订单结束时间"""
        if self.current_subscribe:
            self.data['end_date'] = get_end_datetime(self.current_subscribe.end_date)

    def bind_deadline(self):
        """过期时间"""
        if self.aus:
            self.data['deadline'] = self.aus[0].deadline

    def bind_left_days(self):
        """剩余时间"""
        if self.aus:
            deadline = self.aus[0].deadline
            self.data['left_days'] = (deadline - datetime.datetime.now()).days

    def bind_is_invited(self):
        """【积分相关】是否被邀请过"""
        from apps.web.point import Invited
        self.data['is_invited'] = Invited.is_invited(shop_id = self.shop_id)

    # 加一个bind事件  判断是否是第二种推荐 方式进来的
    def bind_is_invited_4shop(self):
        """【积分相关】是否被第二种方式邀请过"""
        from web.point import Invited4Shop
        self.data['is_invited_4shop'] = Invited4Shop.is_invited_4shop(shop_id = self.shop_id)

    def bind_point(self):
        """【积分相关】积分数量"""

        point = 0
        try:
            point = CacheAdpter.get(CacheKey.WEB_JLB_COUNT % self.shop_id, 'web', 'no_cache')
            if point == 'no_cache':
                from apps.web.point import PointManager
                point = PointManager.refresh_points_4shop(shop_id = self.shop_id)
        except Exception, e:
            log.error('bind_point error,e=%s, shop_id=%s' % (e, self.shop_id))

        self.data['point'] = point

    def bind_freeze_point_deadline(self):
        """【积分相关】保留积分的日期"""
        from apps.subway.models import Account
        account = Account.objects.get(shop_id = self.shop_id)
        if hasattr(account, 'freeze_point_deadline'):
            self.data['freeze_point_deadline'] = account.freeze_point_deadline

    def bind_isneed_phone(self):
        """是否需要手机号"""
        from apps.web.utils import get_isneed_phone
        isneed_phone = get_isneed_phone(self.user)
        self.data['isneed_phone'] = isneed_phone and True or False

    def bind_department(self):
        """获取客户所属的顾问部门"""
        sql = """
        select np.department from ncrm_psuser np join (
        select consult_id from ncrm_subscribe where (article_code='ts-25811' or article_code='FW_GOODS-1921400') and consult_id is not null and start_date<=current_date and shop_id=%s order by create_time desc limit 1
        ) ns on np.id=ns.consult_id""" % self.shop_id
        result = execute_query_sql_return_tuple(sql)
        self.data['department'] = result[0][0] if result else ''


def get_main_ads():
    '''获取满足显示条件的广告'''
    current_time = datetime.datetime.now()
    main_ad_list = main_ad_coll.find({'ad_display':1, 'ad_status':2, 'ad_start_time':{"$lte": current_time}, 'ad_end_time':{"$gte": current_time}}).sort('id', -1).sort('ad_put_time', -1)
    return [main_ad for main_ad in main_ad_list]