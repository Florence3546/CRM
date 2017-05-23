# coding=UTF-8
import datetime, random

from mongoengine.document import Document
from mongoengine.fields import (IntField, DateTimeField, StringField, BooleanField,
                                ListField, EmbeddedDocumentField, DictField)

from apps.common.utils.utils_log import log
from apps.common.biz_utils.utils_permission import ORDER_VERSION_DICT
from apps.ncrm.models import Subscribe, Customer
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.models import Config

class UserLottery(Document):
    nick = StringField(verbose_name = "店铺名称")
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    lottery_num = IntField(verbose_name = "活动编号")
    awards_type = IntField(verbose_name = "奖品类型", default = -1)
    is_exchanged = BooleanField(verbose_name = "是否已兑换", choices = ((True, '已兑换'), (False, '未兑换')), default = False)
    is_remind = BooleanField(verbose_name = "提醒标识", choices = ((True, '需要提醒'), (False, '不需要提醒')), default = True)
    is_lottery = BooleanField(verbose_name = "抽奖标识", choices = ((True, '已抽奖'), (False, '未抽奖')), default = False)
    sale_url = StringField(verbose_name = '优惠链接', default = '')
    last_show_time = DateTimeField(verbose_name = "上次展示抽奖时间", default = datetime.datetime.now)

    meta = {'collection':'web_userlottery', 'indexes': ['nick', 'lottery_num']}

user_lottery_coll = UserLottery._get_collection()


class LotteryReport(Document):
    lottery_num = IntField(verbose_name = "活动编号", primary_key = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now())
    impressions = IntField(verbose_name = "展现量", default = 0)
    click = IntField(verbose_name = "点击量", default = 0)

    meta = {'collection': 'web_lotteryreport'}

    @classmethod
    def add_impressions(cls, lottery_num):
        obj, _ = cls.objects.get_or_create(lottery_num = lottery_num)
        obj.impressions += 1
        obj.save()

    @classmethod
    def add_click(cls, lottery_num):
        obj, _ = cls.objects.get_or_create(lottery_num = lottery_num)
        obj.click += 1
        obj.save()

lottery_rpt_coll = LotteryReport._get_collection()


class Lottery01(object):

    lottery_num = 1
    date_config_dict = {'start_time': datetime.datetime(2015, 12, 8), # 抽奖活动开始时间
                        'lottery_deadline': datetime.datetime(2015, 12, 16), # 抽奖活动结束时间
                        'exchange_deadline': datetime.datetime(2015, 12, 23) # 提醒兑换抽奖结果结束时间
                        }

    awards_config_dict = {'1':('20元软件抵价券', '2000', ''),
                          '2':('50元软件抵价券', '5000', ''),
                          '3':('1.2折季度优惠券', 'http://tb.cn/RdvWsex', '（90元/季度）'),
                          '4':('1.2折半年优惠券', 'http://tb.cn/gpZWsex', '（180元/半年）'),
                          '5':('2折季度优惠券', 'http://tb.cn/jDjrsfx', '（180元/季度）'),
                          '6':('2折半年优惠券', 'http://tb.cn/dlfrsfx', '（360元/半年）'),
                          }

    @classmethod
    def _get_current_subscribe(cls, user):

        def get_version_no(item_code):
            result = ORDER_VERSION_DICT.get(item_code, [])
            return result and result[0] or 0

        today = datetime.datetime.today()
        sub_list = Subscribe.objects.filter(shop_id = user.shop_id, article_code = 'ts-25811', start_date__lte = today.date(), end_date__gte = today.date(), category = 'kcjl')
        highest_version = 0
        current_subscribe = None
        for obj in sub_list:
            temp_version_no = get_version_no(obj.item_code)
            if temp_version_no > highest_version:
                highest_version = temp_version_no
                current_subscribe = obj
                current_subscribe.version_no = highest_version
        return current_subscribe

    @classmethod
    def _get_last_subscribe(cls, user):
        today = datetime.datetime.today()
        sub_list = Subscribe.objects.filter(shop_id = user.shop_id, article_code = 'ts-25811', start_date__lte = today.date(), end_date__gte = today.date(), category = 'kcjl').order_by('-create_time')[:1]
        if sub_list:
            return sub_list[0]
        else:
            return None

    @classmethod
    def _need_lottery(cls, user_lottery, user):
        today = datetime.datetime.now()
        if not (cls.date_config_dict['start_time'] < today < cls.date_config_dict['lottery_deadline']):
            return False, '不在抽奖活动期间'

        if not user_lottery:
            current_subscribe = cls._get_current_subscribe(user)
            if not current_subscribe:
                return False, '找不到订单'
            if current_subscribe.version_no == 5:
                return False, 'vip托管不参与活动'
            else:
                return True, '首次进入抽奖活动'

        if (not user_lottery.is_remind):
            return False, '用户已关闭提醒'

        if user_lottery.is_lottery:
            return False, '用户已抽过奖'
        else:
            if user_lottery.last_show_time.date() == today.date():
                return False, '今天已显示过抽奖，这次不再显示'
            else:
                return True, '历史未抽奖，今天首次显示'

    @classmethod
    def _need_exchange(cls, user_lottery, user):
        today = datetime.datetime.now()
        if not (cls.date_config_dict['start_time'] < today < cls.date_config_dict['exchange_deadline']):
            return False, '不在提醒用户兑奖期间'
        if not user_lottery or (not user_lottery.is_lottery):
            return False, '尚未抽奖'
        if user_lottery.is_exchanged is True:
            return False, '已兑奖'
        last_subscribe = cls._get_last_subscribe(user)
        if not last_subscribe:
            return True, '查不到订单，仍然提示兑奖'
        if last_subscribe.create_time >= user_lottery.create_time:
            user_lottery.is_exchanged = True
            user_lottery.save()
            return False, '经检查，已兑奖'
        else:
            return True, '检查后，仍未兑奖'

    @classmethod
    def _get_awards_detail(cls, user_lottery, user):
        result = {'awards_type': 0, 'awards_desc': '', 'sale_url': ''}
        if user_lottery and user_lottery.is_lottery:
            awards_desc, sale_url, price_str = cls.awards_config_dict[str(user_lottery.awards_type)]
            result.update({'awards_type': user_lottery.awards_type, 'awards_desc': awards_desc + price_str, 'sale_url': sale_url})
        return result

    @classmethod
    def _get_awards_type(cls, user, user_lottery):
        current_subscribe = cls._get_current_subscribe(user)
        is_before_3_1 = current_subscribe.end_date < datetime.date(year = 2016, month = 3, day = 1)
        last_cycle = current_subscribe.cycle
        current_version = current_subscribe.version_no
        if current_version == 1:
            return is_before_3_1 and 4 or 2
        if current_version == 2:
            if is_before_3_1:
                return last_cycle in ['1个月', '3个月'] and 3 or 4
            else:
                return 2
        if current_version == 3:
            if is_before_3_1:
                return last_cycle in ['1个月', '3个月'] and 5 or 6
            else:
                return 2
        return 1

    # 以下为对外接口
    @classmethod
    def get_winner_list(cls):
        cachekey = 'WEB_WINNERS_LIST'
        show_count = 60
        winner_list = CacheAdpter.get(cachekey, 'default', [])
        if not winner_list:
            winner_list = []
            objs = list(UserLottery.objects.filter(lottery_num = cls.lottery_num, awards_type__in = [1, 2, 3, 4, 5, 6]).order_by('-create_time')[:show_count])
            if show_count - len(objs) > 0: # 抽奖人数少时，伪造数据
                objs = list(Customer.objects.filter(is_b2c = 1).order_by('-create_time')[:show_count])

            # 按权重生成 奖项 list
            awards_list = [v[0] for v in cls.awards_config_dict.values()]
            awards_list.extend(['免费宝贝拍摄', '100元软件抵价券', '圣诞礼包'])
            random_cfg_list = [10 for i in range(len(cls.awards_config_dict))]
            random_cfg_list.extend([5, 7, 1])
            new_awards_list = []
            for i, awards_desc in enumerate(awards_list):
                temp_list = [awards_desc for j in range(random_cfg_list[i])]
                new_awards_list.extend(temp_list)

            for obj in objs:
                size = len(obj.nick)
                if size > 2:
                    new_user_name = '%s%s%s' % (obj.nick[0], '*' * (min(size - 2, 4)), obj.nick[-1])
                    awards_desc = random.choice(new_awards_list)
                    winner_list.append({'nick': new_user_name, 'awards_desc': awards_desc})
            CacheAdpter.set(cachekey, winner_list, 'default', 60 * 5)
        return winner_list

    @classmethod
    def get_user_lottery(cls, user):
        try:
            user_lottery = UserLottery.objects.get(lottery_num = cls.lottery_num, nick = user.nick)
        except Exception:
            user_lottery = None
        return user_lottery

    @classmethod
    def get_lottery(cls, user, is_backend = False):
        '''用于进入首页时，判断用户是否该抽奖，是否已兑换，是否提示用户领取奖励'''

        result = {'need_lottery': False, 'need_exchange': False, 'lottery_detail': None}
        try:
            today = datetime.datetime.now()
            blacklist = Config.get_value('web.LOTTERY_BACKLIST', default = [])
            if user.nick in blacklist:
                return result
            user_lottery = cls.get_user_lottery(user)
            if cls.date_config_dict['start_time'] < today < cls.date_config_dict['exchange_deadline']:
                need_lottery, lottery_desc = cls._need_lottery(user_lottery, user)
                need_exchange, exchange_desc = cls._need_exchange(user_lottery, user)
                lottery_detail = cls._get_awards_detail(user_lottery, user)
                result.update({'need_lottery': need_lottery, 'need_exchange': need_exchange, 'lottery_detail': lottery_detail})
                if need_lottery and not is_backend:
                    if not user_lottery:
                        UserLottery.objects.create(nick = user.nick, lottery_num = cls.lottery_num)
                    else:
                        user_lottery.last_show_time = datetime.datetime.today()
                        user_lottery.save()
                    LotteryReport.add_impressions(lottery_num = cls.lottery_num)
                log.info('nick=%s, need_lottery=%s,%s; need_exchange=%s,%s' % (user.nick, need_lottery, lottery_desc, need_exchange, exchange_desc))
        except Exception, e:
            log.error('get lottery error, nick=%s, e=%s' % (user.nick, e))
        return result

    @classmethod
    def lucky_draw(cls, user, is_backend = False):
        user_lottery = cls.get_user_lottery(user)
        if not user_lottery:
            user_lottery = UserLottery(lottery_num = cls.lottery_num, nick = user.nick) # 是否保存由后面逻辑决定
        awards_type = cls._get_awards_type(user, user_lottery)
        desc, sale_url, price_str = cls.awards_config_dict[str(awards_type)]
        if not is_backend: # 内部员工进入软件的，相关记录不保存
            LotteryReport.add_click(lottery_num = cls.lottery_num)
            user_lottery.awards_type = awards_type
            user_lottery.is_lottery = True
            user_lottery.sale_url = sale_url
            user_lottery.save()
        log.info('nick=%s, awards=%s, awards_type=%s' % (user.nick, desc, awards_type))
        return {'awards_type': awards_type, 'desc': desc, 'sale_url': sale_url}


Lottery = Lottery01 # 方便外部统一调用


if __name__ == '__main__':
    from apps.router.models import User
    nick = 'cncys1'
    user = User.objects.get(nick = nick)
    is_backend = True
    lottery_dict = Lottery.get_lottery(user, is_backend)
    winner_list = Lottery.get_winner_list()
    awards_detail = Lottery.lucky_draw(user, is_backend)
    print lottery_dict
    print winner_list
    print awards_detail
