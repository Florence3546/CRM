# coding=UTF-8
import types
import datetime

from django.conf import settings
from mongoengine.document import EmbeddedDocument, Document
from mongoengine.fields import (IntField, DateTimeField, StringField,
                                ListField, FloatField, EmbeddedDocumentField, BooleanField)

from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import date_2datetime, get_start_datetime
from apps.common.constant import Const
from apps.subway.models_report import AccountRpt
from apps.subway.utils import (get_msg_count_list, get_note_count, get_comment_count, save_msg_count)
from apps.kwslt.models_cat import CatStatic


class PersonCfg(EmbeddedDocument):
    """
    \基础数据列（展现量，点击量，点击率，总花费，平均花费，平均排名）：
    impressions, click, ctr, cost, cpc, avgpos
    \转化数据列（收藏量，成交量，成交额，转化率，投资回报）：
    favcount, paycount, pay, conv, roi
    \全网数据列（全网点击指数，全网点击率，全网市场均价，全网竞争度）：
    g_click, g_ctr, g_cpc, g_competition
    """

    custom_col = StringField(verbose_name = "自定义列配置", default = "")

class Account(Document):

    DEFAULT_COLUMN_LIST = ["cpm", "avgpos", "favcount", "favctr", "favpay", "s_favcount", "a_favcount", "carttotal", "z_paycount", "j_paycount", "z_pay", "j_pay", "g_pv", "g_click", "g_cpc", "g_ctr", "g_competition", "create_days", "g_paycount", "g_roi", "g_coverage"]

    shop_id = IntField(verbose_name = "店铺编号 ", primary_key = True)
    # nick = StringField(verbose_name = "卖家昵称", max_length = 30)
    cat_id = IntField(verbose_name = "店铺所属的类目编号", default = 0) # 类目ID通过算法来获取
    balance = FloatField(verbose_name = "账户余额", default = 0)

    person_cfg = EmbeddedDocumentField(PersonCfg, verbose_name = "个性化配置信息") # 废弃，使用下面的list列表
    custom_hide_column = ListField(verbose_name = "关键词列表定制隐藏列", default = DEFAULT_COLUMN_LIST)

    consult_id = IntField(verbose_name = "客服ID", default = 0) # TODO: wangqi 20141110 不再使用的话，将代码清除，并将数据库中字段清除
    consult_group_id = IntField(verbose_name = "客服组ID", default = 0)
    has_push = BooleanField(verbose_name = "是否已经推送关键词", default = False)
    msg_status = StringField(verbose_name = "消息状态", default = None) # 格式为 1_2 : 1条备注，2条留言

#     history_pay = IntField(verbose_name = "历史总花费", default = None)
#     history_pay_date = DateTimeField(verbose_name = "更新历史花费的时间", default = None)
#     receive_address = StringField(verbose_name = "收货地址", default = None)
#     receiver = StringField(verbose_name = "收货人", default = None)
#     receiver_phone = StringField(verbose_name = "收货人手机", default = None)
#     zip_code = StringField(verbose_name = "邮编", default = None)

    history_highest_point = IntField(verbose_name = "历史最高积分", default = 0) # 用来区分等级，以免消费积分后等级下降
    freeze_point_deadline = DateTimeField(verbose_name = "冻结积分的时间") # 用来判断软件过期后是否自动减去积分

    sms_send_time = DateTimeField(verbose_name = "短信发送时间")
    illegal_adgroup_list = ListField(verbose_name = "违规推广组列表", default = [])

    msg_count_list = property(fget = get_msg_count_list)
    note_count = property(fget = get_note_count) # 备注条数
    comment_count = property(fget = get_comment_count) # 留言条数
    set_msg_count = property(fget = save_msg_count)

    Report = AccountRpt

    opar_status = IntField(verbose_name = "CRM操作状态", choices = ((0, '未操作'), (1, '已操作')), default = 0)

    meta = {'collection':'subway_account'}

    @property
    def is_keep_stop(self):
        if not hasattr(self, '_is_keep_stop'):
            self._is_keep_stop = False
            if self.balance <= 0 and self.get_summed_rpt(rpt_days = 1).impressions == 0:
                self._is_keep_stop = True
        return self._is_keep_stop

    @staticmethod
    def get_record_list(start_index, prev_index, group_size, manager, query_condition, filter_condition):
        if start_index is None and prev_index is None:
            start_index = Account._get_collection().find({'has_push':{'$in':[None, False]}}, {'_id':1}).sort('_id')[0]['_id']
        if type(start_index) is types.UnicodeType or type(start_index) is types.StringType:
            start_index = int(start_index)
            if prev_index is not None:
                prev_index = int(prev_index)
        all_records = Account._get_collection().find({'_id':{'$gte':start_index}, 'has_push':{'$in':[None, False]}}, {'_id':1}).sort('_id').limit(group_size)
        result_list = [obj for obj in all_records] or [] # 为了避免eval加载queryset对象到执行的方法中，所以先把所有对象取出来存放到一个list当中，再传入到method中
        next_index = start_index
        if result_list:
            next_index = result_list[len(result_list) - 1]['_id']
        return result_list, str(next_index)

    @staticmethod
    def get_all_record_count():
        return Account._get_collection().find({'has_push':{'$in':[None, False]}}).count()

    @classmethod
    def struct_download(cls, shop_id, tapi):
        result = False
        try:
            account_dict = {'balance':100}
            try:
                # tobj_balance = tapi.simba_account_balance_get()
                # if tobj_balance and hasattr(tobj_balance, 'balance'):
                #     account_dict.update({'balance':tobj_balance.balance})
                balance = tapi.get_account_balance()
                account_dict.update({'balance': balance})
            except Exception, e:
                log.error('get balance error, shop_id=%s, error=%s' % (shop_id, e))

            if account_coll.find_one({'_id':shop_id}):
                account_coll.update({'_id':shop_id}, {'$set':account_dict})
            else:
                account_dict.update({'_id': shop_id, 'cat_id': 0, 'consult_group_id':0, 'consult_id':0})
                account_coll.insert(account_dict)
            log.info('sync account OK, shop_id=%s' % shop_id)
            result = True
        except Exception, e:
            log.error('sync account FAILED, shop_id=%s, e=%s' % (shop_id, e))

        return result

    @classmethod
    def increase_download(cls, shop_id, tapi, last_sync_time):
        return cls.struct_download(shop_id, tapi)

    @classmethod
    def report_download(cls, shop_id, tapi, token, time_scope):
        """下载店铺的报表"""
        result_flag = 'FAILED'
        try:
            rpt_list = []
            for _, source in cls.Report.REPORT_CFG:
                top_base_objs = tapi.simba_rpt_custbase_get(start_time = time_scope[0], end_time = time_scope[1], source = source, subway_token = token, retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
                base_dict, effect_dict = {}, {}
                if top_base_objs and hasattr(top_base_objs, 'rpt_cust_base_list') and top_base_objs.rpt_cust_base_list:
                    for base in top_base_objs.rpt_cust_base_list:
                        base_dict.update(cls.Report.parse_rpt(base, 'base'))
                    top_effect_objs = tapi.simba_rpt_custeffect_get(start_time = time_scope[0], end_time = time_scope[1], source = source, subway_token = token)
                    if top_effect_objs and hasattr(top_effect_objs, 'rpt_cust_effect_list') and top_effect_objs.rpt_cust_effect_list:
                        for effect in top_effect_objs.rpt_cust_effect_list:
                            effect_dict.update(cls.Report.parse_rpt(effect, 'effect'))

                if base_dict:
                    rpt_list.extend(cls.Report.merge_rpt_dict(base_dict, effect_dict, {'shop_id': shop_id}))

            if rpt_list:
                remove_query = {'shop_id': shop_id, 'date':{'$lte':date_2datetime(time_scope[1]), '$gte':date_2datetime(time_scope[0])}}
                cls.Report.update_rpt_list(remove_query, rpt_list)
                result_flag = 'OK'
            else:
                result_flag = 'EMPTY'
            log.info('download shop rpt OK, shop_id = %s' % (shop_id))
        except Exception, e:
            log.error('download shop rpt FAILED, shop_id = %s, e = %s' % (shop_id, e))
        return result_flag

#     @staticmethod
#     def udp_download(shop_id, tapi, date_scope = None):
#         from udp_download import UdpSyncer
#         udp_fields = [udp_field for udp_field in Const.SUBWAY_UDP_SHOP_MAPPING]
#         us = UdpSyncer(shop_id = shop_id, tapi = tapi)
#         return us.sync_shop_udp(udp_fields = udp_fields, date_scope = date_scope, flag = False)

    def get_snap_list(self, **kwargs): # wangqi 20151007 为啥不做成property？ 因为天数不同取的数据不一样，并且实际上，并没有使用property的场景[<--求例子]
        rpt_dict = self.Report.get_snap_list({'shop_id': self.shop_id}, **kwargs)
        return rpt_dict.get(self.shop_id, [])

    def get_summed_rpt(self, **kwargs):
        rpt_dict = self.Report.get_summed_rpt({'shop_id': self.shop_id}, **kwargs)
        return rpt_dict.get(self.shop_id, self.Report())

    @property
    def cat_data(self):
        """获取店铺的行业数据"""
        if not hasattr(self, '_cat_data'):
            self._cat_data = CatStatic.get_market_data_8id(self.cat_id)
        return self._cat_data

    @property
    def adgroup_count(self):
        """得到店铺的推广组总数"""
        if not hasattr(self, '_adgroup_count'):
            from apps.subway.models_adgroup import Adgroup
            try:
                self._adgroup_count = Adgroup.objects.filter(shop_id = self.shop_id).count()
            except Exception, e:
                log.error("can not find adgroup, shop_id=%s, e=%s" % (self.shop_id, e))
        return self._adgroup_count


    @classmethod
    def get_custom_col(cls, shop_id):
        acct = cls._get_collection().find_one({'_id': shop_id}, {'custom_hide_column': 1})
        if acct and 'custom_hide_column' in acct:
            col_list = acct['custom_hide_column']
        else:
            col_list = cls.custom_hide_column.default
        return col_list

    @classmethod
    def save_custom_col(cls, shop_id, custom_col_list):
        cls._get_collection().update({'_id': shop_id}, {'$set': {'custom_hide_column': custom_col_list}})

    @classmethod
    def get_history_highest_point(cls, shop_id):
        result = account_coll.find_one({'_id':int(shop_id)})
        if result and result.has_key('history_highest_point'):
            return result['history_highest_point']
        else:
            return 0

    @classmethod
    def update_history_highest_point(cls, shop_id, point):
        result = account_coll.update({'_id':int(shop_id)}, {'$set':{'history_highest_point':int(point)}})

        if result['ok'] and result['updatedExisting']:
            return True, ''
        else:
            log.error('update_history_highest_point error, shop_id = %s' % shop_id)
            return False, '更新数据失败'

    @classmethod
    def get_grade_display(cls, shop_id):
        point = cls.get_history_highest_point(shop_id = shop_id)

        grade, parcent = 1, 0
        next_grade = 10000 - point

        if 10000 < point <= 24999:
            grade = 2
            next_grade = 25000 - point
            parcent = ((point - 10000) / 15000.0) * 100 * (1 / 3.0) + 30
        if 25000 < point <= 49999:
            grade = 3
            next_grade = 50000 - point
            parcent = ((point - 25000) / 25000.0) * 100 * (1 / 3.0) + 60
        if point > 50000:
            grade = 4
            next_grade = -1
            parcent = 100
        return grade, next_grade, parcent

    @classmethod
    def freeze_point(cls, shop_id, nick):
        from apps.router.models import ArticleUserSubscribe
        sbuscribe = ArticleUserSubscribe.objects.filter(nick = nick, article_code = 'ts-25811', deadline__gte = get_start_datetime()).order_by('-deadline')

        current_sbuscribe = sbuscribe[0]
        freeze_point_deadline = current_sbuscribe.deadline + datetime.timedelta(days = 30 * 3)
        result = account_coll.update({'_id':int(shop_id)}, {'$set':{'freeze_point_deadline':freeze_point_deadline}})

        if result['ok'] and result['updatedExisting']:
            return True, freeze_point_deadline
        else:
            log.error('freeze_point error, shop_id = %s' % shop_id)
            return False, None

#     @classmethod
#     def init_history_pay(cls,shop_id):
#         account=Account.objects.filter(shop_id = shop_id)
#         sum_reports=account.sum_reports(rpt_days = 30)[0]
#
#         account_coll.update({'_id':shop_id},{"$set":{"history_pay":sum_reports.qr.pay,'history_pay_date':account[0].rpt_list[-1].date}})
#         return sum_reports.qr.pay
#
#     @classmethod
#     def calc_history_pay(cls,shop_id,history_pay_date):
#         rpt_days=datetime.date.today().day-history_pay_date.day
#         account=Account.objects.filter(shop_id = shop_id)
#         sum_reports=account.sum_reports(rpt_days = rpt_days)[0]
#
#         total_history_pay=account[0].history_pay+sum_reports.qr.pay
#         account_coll.update({'_id':shop_id},{"$set":{"history_pay":total_history_pay,'history_pay_date':account[0].rpt_list[-1].date}})
#         return total_history_pay
#
#     @classmethod
#     def get_history_pay(cls,shop_id):
#         """历史收益"""
#         account=account_coll.find_one({'_id':shop_id})
#         if account.has_key('history_pay_date'):
#             history_pay_date=account['history_pay_date']
#
#             if time_is_someday(history_pay_date,days=0):
#                 return account['history_pay']
#             else:
#                 return cls.calc_history_pay(shop_id,history_pay_date)
#         else:
#             return cls.init_history_pay(shop_id)


account_coll = Account._get_collection()
