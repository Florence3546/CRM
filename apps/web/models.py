# coding=UTF-8
import datetime

from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from mongoengine.document import Document, DynamicDocument
from mongoengine.fields import IntField, DateTimeField, StringField

from apps.common.utils.utils_log import log
from apps.common.biz_utils.utils_permission import ORDER_VERSION_DICT
from apps.ncrm.models import Customer, PSUser
from apps.router.models import User, ArticleUserSubscribe
from django.db.models.sql.constants import SINGLE

DESCR_DICT = {'home':'首页报表', 'gsw':'长尾托管', 'adg_optm':'宝贝优化', 'select_word':'宝贝选词', 'health_check':'健康检查', 'title_optm':'标题优化', 'impt':'重点托管', 'dupl_check':'重复词排查'}
class Feedback(models.Model):
    shop = models.ForeignKey(Customer, verbose_name = "店铺", to_field = 'shop_id')
    score_str = models.CharField(verbose_name = "评分字典", max_length = 500)
    content = models.TextField(verbose_name = "反馈内容", blank = True, null = True, default = '')
    consult = models.ForeignKey(PSUser, blank = True, null = True, verbose_name = "顾问")
    note = models.CharField(verbose_name = "备注", blank = True, max_length = 500)
    handle_status = models.IntegerField(verbose_name = "处理状态", blank = True, null = True, choices = [(-1, '未处理'), (1, '已处理')])
    create_time = models.DateTimeField(verbose_name = "录入时间", default = datetime.datetime.now)

    class Meta:
        ordering = ('-create_time',)

    def send_email(self):
        if self.consult:
            cc_list = ['%s@paithink.com' % self.consult.name, 'zy@paithink.com']
            # 除了给顾问及瑜哥发送邮件，还需要给QC部的指战员发送
            psuser_list = PSUser.objects.filter(position = 'COMMANDER', department = 'QC').exclude(status = '离职')
            for psuser in psuser_list:
                cc_list.append('%s@paithink.com' % psuser.name)
            score_list = eval(self.score_str)
            score_str = ''
            for i in score_list:
                score_str += '%s：%s分</br>' % (DESCR_DICT[i[0]], i[1])

            nick = self.shop.nick
            subject = "自动提醒：客户%s反馈意见" % (nick)
            content = "用户名：%s</br>联系旺旺: <a href=\'aliim:sendmsg?uid=cntaobao&touid=cntaobao%s&siteid=cntaobao\'>%s</a></br>\
                        （如果链接不起作用，请手动复制以下地址到地址栏：aliim:sendmsg?uid=cntaobao&touid=cntaobao%s&siteid=cntaobao）</br>\
                        %s反馈内容：%s</br>反馈时间：%s</br>" % (nick, nick, nick, nick, score_str, self.content, str(self.create_time)[:10])
            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, cc_list, html_message = content)

class IpLimit(Document):
    ip = StringField(verbose_name = "ip 登录选词预览")
    ip_count = IntField(verbose_name = "ip 登录次数")

    meta = {'collection':'kw_ord_iplimit'}

class HotZone(Document):
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    s1 = StringField(verbose_name = "dom本身id或者父级的索引id", max_length = 20)
    s2 = StringField(verbose_name = "dom根据父级id的xpath", max_length = 50)
    page = StringField(verbose_name = "记录的页面", max_length = 20)
    create_time = DateTimeField(verbose_name = "创建时间")
    meta = {'collection':'web_hotzone', "shard_key":('shop_id',)}

    @staticmethod
    def add_record(data):
        try:
            hz_coll.insert(data)
        except Exception, e:
            log.error('add_record hz_coll insert shop_id=%s, e=%s' % (data['shop_id'], e))
hz_coll = HotZone._get_collection()

class TempMonitor(Document):
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    func_name = StringField(verbose_name = "执行方法", max_length = 100)
    func_desc = StringField(verbose_name = "描述", max_length = 100)
    args = StringField(verbose_name = "参数")
    result = StringField(verbose_name = "结果")
    create_time = DateTimeField(verbose_name = "创建时间")
    meta = {'collection':'web_tempmonitor', "indexes":['shop_id', ]}

    @classmethod
    def generetor_record(cls, shop_id, func_name, func_desc, args, result):
        record = cls()
        record.shop_id = shop_id
        record.func_desc = func_desc
        record.func_name = func_name
        record.args = str(args)
        record.result = str(result)
        record.create_time = datetime.datetime.now()
        record.save()
        return record

tm_coll = TempMonitor._get_collection()

class PointActivity(Document):
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    nick = StringField(verbose_name = "店铺名")
    consult_id = IntField(verbose_name = "客服ID")
    consult_flag = IntField(verbose_name = "客服标记是否隐藏提示", choices = [(0, '不隐藏'), (1, '隐藏')])
    type = IntField(verbose_name = "活动类型", choices = [('appraise', '好评送积分'), ('virtual', '兑换虚拟物品'), ('gift', '兑换实物'), ('invited', '被邀请'), ('invited4shop', '被邀请2'), ('promotion', '邀请送积分'), ('promotion4shop', '邀请送积分2'), ('renewal', '续订软件'), ('discount', '换购软件'), ('sign', '签到积分'), ('pperfectphone', '添加手机号'), ('login', '登录送积分'), ('perfectinfo', '完善信息送积分'), ('expired', '用户过期扣积分')])
    point = IntField(verbose_name = "积分")
    is_freeze = IntField(verbose_name = "是否冻结")
    desc = StringField(verbose_name = "说明")
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)

    @classmethod
    def clean_outdated(cls):
        """清除过期好评积分数据"""
        cls._get_collection().remove({'is_freeze': 1, 'type': 'appraise', 'create_time': {'$lte': datetime.datetime.now() - datetime.timedelta(days = 30)}})
        return True

pa_coll = PointActivity._get_collection()

class SaleLink(models.Model):
    """用于生成推广链接的字符串"""
    link_name = models.CharField(verbose_name = "连接名称", max_length = 200)
    param_str = models.CharField(verbose_name = "接口参数", max_length = 200)
    desc = models.CharField(verbose_name = "说明", max_length = 200)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)

class Template_statistics(models.Model):
    """统计创意优化模板点击次数"""
    temp_id = models.CharField(verbose_name = "模板对应id", max_length = 20)
    click = models.IntegerField(verbose_name = "点击次数", default = 0)

    @classmethod
    def add(cls, temp_id):
        obj = cls.objects.get_or_create(temp_id = temp_id)[0]
        obj.click += 1
        obj.save()

'''首页广告管理模块=====start======add by tianxiaohe 20150909 '''
# 广告审核权限
class MainAd(Document):
    '''首页广告通用实体类 add by tianxiaohe 20150909'''
    AD_POSITION_CHOICES = [('charlink', ('文字链', ['DEV', 'MKT'])),
              ('rightnotice', ('右侧公告', ['DEV', 'MKT'])),
              ('mrwindow', ('右下弹窗', ['DEV'])),
              ('mcwindow', ('中间弹窗', ['DEV'])),
              ('mainbanner', ('主区横条', ['DEV'])),
              ('topbanner', ('顶部横条', ['DEV'])),
              ('bottombanner', ('底部横条', ['DEV'])),
              ('servermenu', ('服务中心', ['DEV', 'MKT']))]

    AD_FREQUENCY_CHOICES = [(1, '每次刷新'), (2, '每天一次')]
    LEVEL_CHOICES = [(0, '信息'), (1, '警告'), (2, '错误'), ]
    USER_TYPE_CHOICES = [('0', '开车精灵'), ('1', '无线Q牛'), ('2', 'CRM用户'), ]
    CLOSE_BTN_CHOICES = [(0, '关闭'), (1, '开启')]
    DISPLAY_CHOICES = [(0, '否'), (1, '是')]
    STATUS_CHOICES = [(0, '未审核'), (1, '已审核'), (2, '投放中')]

    id = IntField(verbose_name = "唯一标示id", default = 0, required = True, primary_key = True) # 唯一标示，请自己实现自增
    ad_position = StringField(verbose_name = "显示位置", required = True, choices = AD_POSITION_CHOICES)
    ad_url = StringField(verbose_name = "广告链接")
    ad_display = IntField(verbose_name = "是否显示", default = 0, choices = DISPLAY_CHOICES)
    ad_start_time = DateTimeField(verbose_name = "有效时间（起始）")
    ad_end_time = DateTimeField(verbose_name = "有效时间（结束）")
    ad_weight = IntField(verbose_name = "权重", default = 0)
    ad_frequency = StringField(verbose_name = "显示频率", choices = AD_FREQUENCY_CHOICES, default = 2)
    ad_show_times = IntField(verbose_name = "展现量", default = 0)
    ad_click_times = IntField(verbose_name = "点击量", default = 0)
    ad_create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now, required = True)
    ad_updater = StringField(verbose_name = "创建人/修改人", required = True)
    ad_update_time = DateTimeField(verbose_name = "修改时间", default = datetime.datetime.now, required = True)
    ad_check_limit = StringField(verbose_name = "审核权限")
    ad_checker = StringField(verbose_name = "审核人", required = True)
    ad_check_time = DateTimeField(verbose_name = "审核时间", default = datetime.datetime.now, required = True)
    ad_status = IntField(verbose_name = "投放状态", default = 0)
    ad_show_condition = StringField(verbose_name = "显示条件")
    ad_title = StringField(verbose_name = "广告标题")
    ad_content = StringField(verbose_name = "广告内容")
    ad_blacklist = StringField(verbose_name = "黑名单")
    ad_put_time = DateTimeField(verbose_name = "发布时间")

    '''右侧公告特有'''
    ad_level = IntField(verbose_name = "公告级别", choices = LEVEL_CHOICES)
    ad_user_type = StringField(verbose_name = "用户类型", choices = USER_TYPE_CHOICES)

    '''右下弹窗特有'''
    ad_delay_secs = IntField(verbose_name = "延时秒数")
    ad_show_secs = IntField(verbose_name = "显示秒数")

    '''顶部横条特有'''
    ad_close_btn = IntField(verbose_name = "关闭按钮", choices = CLOSE_BTN_CHOICES, default = 1)

    meta = {'collection':'web_main_ad', }

    @classmethod
    def add_record(cls, data):
        '''添加一条记录'''
        if not cls._get_collection().find().count():
            data['_id'] = 0
        else:
            last_record = list(cls._get_collection().find({}, {'_id': 1}).sort('_id', -1).limit(1))
            data['_id'] = int(last_record[0]['_id']) + 1
        result = cls._get_collection().insert(data)
        return result

    @classmethod
    def update_record(cls, a_id, data):
        '''修改记录'''
        result = cls._get_collection().update({'_id': a_id}, {'$set':data})
        return result

    @classmethod
    def del_record(cls, a_id):
        '''修改记录'''
        cls._get_collection().remove({'_id': a_id})

    @classmethod
    def add_show_times(cls, a_id):
        '''浏览次数加1'''
        cls._get_collection().update({'_id': a_id}, {'$inc':{'ad_show_times':1}})

    @classmethod
    def add_click_times(cls, a_id):
        '''点击次数加1'''
        cls._get_collection().update({'_id': a_id}, {'$inc':{'ad_click_times':1}})

main_ad_coll = MainAd._get_collection()

'''首页广告管理模块=====end=========================== '''


class BaseOrderTemplate(models.Model):
    """配置购买订单"""
    ORDER_CYCLE_CHOISE = ((1, u'一个月'), (3, u'一季度'), (6, u'半年'), (12, u'一年'))
    JOINED_STATUS_CHOISE = ((1, u'支持'), (0, u'不支持'))
    ORDER_TYPE_CHOISE = ((1, u'续订/升级优惠'), (2, u'会员商城'), (3, u'推荐有礼'),)
    ORDER_VERSION_CHOICES = ((k, v[1]) for k, v in ORDER_VERSION_DICT.items())

    name = models.CharField(verbose_name = "版本名称", max_length = 30)
    desc = models.CharField(verbose_name = "版本描述", max_length = 100)
    version = models.CharField(verbose_name = "订购版本", choices = ORDER_VERSION_CHOICES, max_length = 30)
    ori_price = models.IntegerField(verbose_name = "原价") # 单位：分
    discount = models.IntegerField(verbose_name = '优惠') # 单位：分
    cycle = models.IntegerField(verbose_name = "订购周期", choices = ORDER_CYCLE_CHOISE)
    param_str = models.TextField(verbose_name = "接口参数", help_text = """如：'{"param":{"aCode":"ACT_...","itemList":["..."],"promIds":[...],"type":1},"sign":"...."}'""")
    is_subscribe = models.IntegerField(verbose_name = "是否支持订购", choices = JOINED_STATUS_CHOISE)
    order_type = models.IntegerField(verbose_name = "订单类型", choices = ORDER_TYPE_CHOISE)

    class Meta:
        abstract = True

    @property
    def cur_price(self):
        return self.ori_price - self.discount

    @property
    def level(self):
        return self.__class__.get_version_level(self.version)

    @property
    def is_base(self):
        return self.order_type == self.__class__.ORDER_TYPE_CHOISE[0][0]

    @property
    def is_activity(self):
        return self.order_type == self.__class__.ORDER_TYPE_CHOISE[1][0]

    @property
    def is_recommond(self):
        return self.order_type == self.__class__.ORDER_TYPE_CHOISE[2][0]

    def generate_order_link(self, nick, tapi):
        """获取订单链接"""
        if tapi is None:
            raise Exception("tapi is invalid!")

        top_obj = tapi.fuwu_sale_link_gen(nick = nick, param_str = self.param_str)
        url = top_obj.url if top_obj and hasattr(top_obj, 'url') else ""
        return url

    @classmethod
    def get_version_level(cls, version):
        """获取版本等级"""
        return ORDER_VERSION_DICT.get(version, [0, ""])[0]

    @classmethod
    def get_least_discount(cls):
        """获取最小折扣"""
        return cls.objects.filter(is_base = cls.ORDER_TYPE_CHOISE[1][0])\
                .aggregate(models.Min('discount'))['discount__min']

    @classmethod
    def get_ordertemplate_byid(cls, template_id):
        try:
            return cls.objects.get(id = template_id)
        except :
            return None

    @classmethod
    def query_order_template(cls, version, cycle, order_types, discount = 0):
        """通过版本及周期来获取订购模板"""
        if not order_types:
            raise ValueError("order_types is empty!.")

        template_qs = cls.objects.filter(order_type__in = order_types)

        if version:
            template_qs = template_qs.filter(version = version)
        if cycle:
            template_qs = template_qs.filter(cycle = cycle)
        if discount:
            template_qs = template_qs.filter(discount = discount)

        return template_qs

    @classmethod
    def query_base_order_template(cls):
        return cls.query_order_template(None, None, \
                            order_types = (cls.ORDER_TYPE_CHOISE[0][0],))

    @classmethod
    def query_order_template_bydiscount(cls, discount):
        """通过优惠价位来获取有效订单"""
        order_types = (cls.ORDER_TYPE_CHOISE[1][0],)
        return cls.query_order_template(None, None, order_types, discount).order_by("discount")

    @classmethod
    def get_recommend_ordertemplate(cls, version, cycle, order_types = ()):
        """通过版本周期来获取有效订单"""
        if not order_types:
            order_types = (cls.ORDER_TYPE_CHOISE[2][0],)
        return cls.query_order_template(version, cycle, order_types)

    @classmethod
    def aggregate_version_infos_bydiscount(cls, template_list):
        """通过折扣，聚合"""
        result = {}
        for template in template_list:
            if template.version not in result:
                result[template.version] = []
            result[template.version].append(template)
        return result


class OrderTemplate(BaseOrderTemplate):
    pass


class LotteryOrder(BaseOrderTemplate):
    '''抽奖活动的临时表'''
    pass


class PointTemplate(models.Model):
    point = models.IntegerField(verbose_name = "兑换积分", help_text = "商品兑换需要的积分值")

    class Meta:
        abstract = True

class MemberStore(PointTemplate):
    class Const:
        TICKET = "ticket"
        GIFT = "gift"
        SERVER = "virtual"
        SHOP_TYPE_CHOICES = ((TICKET, "优惠券"), (GIFT, "礼物"), (SERVER, "服务"))

    name = models.CharField(verbose_name = "标题", max_length = 20, help_text = "图片下的主标题")
    desc = models.CharField(verbose_name = "描述", max_length = 100, help_text = "仅商品类型为优惠券的情况下，显示在标题下的内容")
    shop_type = models.CharField(verbose_name = "商品类型", choices = Const.SHOP_TYPE_CHOICES, max_length = 30, help_text = "优惠券：软件优惠券，服务：虚拟的服务，如：详情页设计，礼品：实物，需要邮寄")
    worth = models.IntegerField(verbose_name = "价值", help_text = "单位：分")
    limit_point = models.IntegerField(verbose_name = "最低兑换的积分值", default = 0, help_text = "值为0时，默认为没有限制")
    img_url = models.CharField(verbose_name = "图片链接", max_length = 200, help_text = "该链接可用网络图片链接")

    @classmethod
    def get_present_byid(cls, present_id):
        try:
            return cls.objects.get(id = present_id)
        except:
            return None

    @classmethod
    def get_ticket_bydiscount(cls, discount):
        spt_cursor = cls.objects.filter(worth = discount)
        if spt_cursor.count():
            return spt_cursor[0]
        return None

    @classmethod
    def query_present_templates(cls, shop_types = (Const.TICKET, Const.GIFT, Const.SERVER)):
        return cls.objects.filter(shop_type__in = shop_types).order_by('id')

    @classmethod
    def aggregate_version_infos(cls, shop_type = (Const.TICKET, Const.GIFT, Const.SERVER)):
        result = {}
        for template in cls.query_present_templates(shop_type):
            if template.shop_type not in result:
                result[template.shop_type] = []
            result[template.shop_type].append(template)
        return result

class TrialUser(DynamicDocument):
    trial_nick = StringField(verbose_name = "nick用户昵称")
    login_count = IntField(verbose_name = "登陆次数")
    use_time = DateTimeField(verbose_name = "首次使用选词预览的时间", default = datetime.datetime.now)

    meta = {'collection':'web_trialuser', 'indexes':['trial_nick'] }
trial_nick_coll = TrialUser._get_collection()

class SelectKeywordFellBack(Document):
    nick = StringField(verbose_name = "用户昵称")
    cat_id = IntField(verbose_name = '类目Id')
    cat_name = StringField(verbose_name = "类目名称")
    item_title = StringField(verbose_name = "宝贝标题")
    item_url = StringField(verbose_name = "宝贝链接")
    prblm_descr = StringField(verbose_name = "问题描述")
    fellback_source = IntField(verbose_name = '反馈来源，0来自选词预览，1来自选词', default = 1)
    meta = {'collection':'web_select_fellback', 'indexes':['nick', 'cat_id']}

class AppComment(models.Model):
    """用户评论"""
    IS_PAY_CHOICES = [(1, '实际付费'), (2, '实际未付费')]
    IS_RECOMMEND_CHOICES = [(1, '标记'), (0, '未标记')]

    id = models.IntegerField(verbose_name = '评价id', primary_key = True)
    avg_score = models.CharField(verbose_name = '平均分', max_length = 10, default = '0.0')
    suggestion = models.CharField(verbose_name = '评论内容', max_length = 1000, default = '', null = True)
    service_code = models.CharField(verbose_name = '服务code', max_length = 50, default = '', null = True)
    user_nick = models.CharField(verbose_name = '评价人nick', max_length = 50, default = '', null = True)
    gmt_create = models.DateTimeField(verbose_name = '评价时间', null = True)
    item_code = models.CharField(verbose_name = '服务规格code', max_length = 50, default = '', null = True)
    item_name = models.CharField(verbose_name = '服务规格名称', max_length = 50, default = '', null = True)
    is_pay = models.IntegerField(verbose_name = '是否实际付费', default = 1, choices = IS_PAY_CHOICES)
    is_recommend = models.IntegerField(verbose_name = '是否标记', default = 0, choices = IS_PAY_CHOICES)