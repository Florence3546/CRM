# coding=UTF-8

import datetime
import copy

import xlrd
from django.db import models
from django.conf import settings
from django.db.models import Q, F
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

from bson.objectid import ObjectId
from apilib import tsapi, TopError, get_tapi
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import get_start_datetime, time_is_ndays_interval, time_is_someday, date_2datetime
from apps.common.utils.utils_collection import genr_sublist
from apps.common.utils.utils_mysql import bulk_insert_for_model, execute_manage_sql
from apps.common.utils.utils_json import json
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple
from apps.common.cachekey import CacheKey
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apps.common.biz_utils.utils_misc import get_credit_level
from apps.common.constant import Const
from apps.router.models import User, ArticleUserSubscribe, AdditionalPermission, NickPort
from apps.subway.models import Account, account_coll

EVENT_MARK_CHOICES = ((0, '默认隐藏'), (1, '默认可见'),)
OPER_TYPE_CHOICES = (('ztc', '直通车操作'), ('zz', '钻展操作'), ('rjjh', '人机操作'), ('zx', '装修'), ('others', '其他操作'))
ARTICLE_CODE_CHOICES = (('ts-25811', '开车精灵'), ('FW_GOODS-1921400', '无线精灵'), ('tp-001', '直通车托管'), ('tp-002', '钻展托管'), ('tp-003', '店铺装修'), ('tp-004', '代运营'), ('tp-005', '补单'), ('tp-006', 'seo'), ('tp-007', '客服外包'))
SUBSCRIBE_SOURCE_TYPE_CHOICES = ((1, '淘宝推广'), (2, '人工洽谈'), (3, '转介绍'), (4, '咨询转化'))
# 20160331 wuhuaqiao 注意订单类型先后顺序不能随意改变，按照重要优先级来定
CATEGORY_CHOICES = (('ztc', '直通车托管'), ('vip', 'VIP专家托管'), ('rjjh', '类目专家'), ('kcjl', '开车精灵'), ('qn', '千牛版'), ('zz', '钻展托管'), ('zx', '店铺装修'), ('dyy', '代运营'), ('seo', 'seo'), ('kfwb', '客服外包'), ('other', '补单'), ('zttk', '暂停退款'), ('ztbd', '暂停补单'))

PLATEFORM_TYPE_CHOICES = (('kcjl', '开车精灵'), ('qnyd', '千牛移动'), ('qnpc', '千牛PC'))
APPROVAL_STATUS_CHOICES = ((0, '未审核'), (1, '已通过'), (2, '未通过'), (3, '待再审'))
OPERATION_GROUPS = ['TGROUP1', 'TGROUP2', 'TGROUP3', 'TGROUP4', 'TGROUP5', 'TGROUP6', 'TGROUP7', 'BRAND', 'DESIGN']
GROUPS = ['GROUP1', 'GROUP2', 'GROUP3']

class PSUser(models.Model):
    POSITION_CHOICES = [('MKT', '软件推广'),
                       ('PRESELLER', '售前专员'),
                       # ('SELLER', '销售'),
                       # ('RJJH', '人机'),
                       ('TPAE', '操作专员'),
                       ('CONSULT', '销售顾问'),
                       ('VA_SALE', '增值销售'),
                       ('DESIGNER', '设计专员'),
                       ('OPTAGENT', '代运营'),
                       # ('TRAINER', '讲师'),
                       ('TRAINER1', '培训专员'),
                       ('TRAINER2', '培训中级专员'),
                       ('TRAINER3', '培训高级专员'),
                       ('SHOPMANAGER', '店长'),
                       ('SHOPASSISTANT', '店长助理'),

                       ('QC', 'QC专员'),
                       ('SEO', 'SEO专员'),
                       ('SEOLEADER', 'SEO组长'),
                       # ('SALELEADER', '销售组长'),
                       ('TPLEADER', '技术组长'),
                       ('CONSULTLEADER', '售后组长'),
                       # ('RJJHLEADER', '人机组长'),
                       ('COMMANDER', '指战员'),

                       ('DEV', '研发'),
                       ('HR', '行政'),
                       ('SMANAGER', '高管'),
                       ('SUPER', '超级用户'),
                       ('NONE', '无'),
                       ]
    POSITION_PERMS_CHOICES = [('MKT', '软件推广', '0aF'),
                       ('PRESELLER', '售前专员', '0'),
                       # ('SELLER', '销售', '0'),
                       ('TPAE', '操作专员', '0'),
                       # ('RJJH', '人机', '0'),
                       ('CONSULT', '销售顾问', '0'),
                       ('VA_SALE', '增值销售', '0'),
                       ('DESIGNER', '设计专员', '0'),
                       ('OPTAGENT', '代运营', '0'),
                       # ('TRAINER', '讲师', '0'),
                       ('TRAINER1', '培训专员', '0'),
                       ('TRAINER2', '培训中级专员', '0'),
                       ('TRAINER3', '培训高级专员', '0'),
                       ('SHOPMANAGER', '店长', '0'),
                       ('SHOPASSISTANT', '店长助理', '0'),
                       ('SEO', 'SEO专员', '0'),

                       ('QC', 'QC专员', '01B'),
                       ('SEOLEADER', 'SEO组长', '01'),
                       # ('SALELEADER', '销售组长', '01'),
                       ('TPLEADER', '技术组长', '01'),
                       ('CONSULTLEADER', '售后组长', '01'),
                       # ('RJJHLEADER', '人机组长', '01'),
                       ('COMMANDER', '指战员', '01'),

                       ('HR', '行政', '0CG'),
                       ('DEV', '研发', '012aABCEF'),
                       ('SMANAGER', '高管', '012aABCEF'),
                       ('SUPER', '超级用户', '012aABCEF'),
                       ]
    DEPARTMENT_CHOICES = [('DEV', '研发部'),
                          ('MKT', '市场部'),
                          ('QC', 'QC部'),
                          ('TRAIN', '培训部'),
                          ('HR', '行政部'),
                          ('OPTAGENT', '代运营部'),
                          ('GROUP1', '销服一部'),
                          ('GROUP2', '销服二部'),
                          ('GROUP3', '销服三部'),
                          # ('GROUP4', '销服四部'),
                          # ('GROUP5', '销服五部'),
                          ('TGROUP1', '技术一部'),
                          ('TGROUP2', '技术二部'),
                          ('TGROUP3', '技术三部'),
                          ('TGROUP4', '技术四部'),
                          ('TGROUP5', '技术五部'),
                          ('TGROUP6', '技术六部'),
                          ('TGROUP7', '技术七部'),
                          ('BRAND', '品牌部'),
                          ('DESIGN', '设计部'),
                          ('VABU', '增值事业部'),  # Value Added Business Unit
                          ('OTHERS', '其他'),
                          ]

    GENDER_CHOICES = [('男', '男'), ('女', '女')]
    STATUS_CHOICES = [('试用', '试用'), ('转正', '转正'), ('离职', '离职')]
    EDUCATION_CHOICES = [('小学', '小学'), ('初中', '初中'), ('高中', '高中'), ('中专', '中专'), ('大专', '大专'), ('本科', '本科'), ('硕士', '硕士'), ('博士', '博士')]

    name = models.CharField(verbose_name = "用户名", max_length = 30, unique = True)
    name_cn = models.CharField(verbose_name = '中文名', max_length = 30, blank = True, null = True, default = '')
    password = models.CharField(verbose_name = '密码', max_length = 128)
    position = models.CharField(verbose_name = "职位", max_length = 40, blank = True, null = True, default = '', choices = POSITION_CHOICES)
    perms = models.CharField(verbose_name = "权限码", max_length = 20, blank = True, null = True, default = '')
    ww = models.CharField(verbose_name = "旺旺ID", null = True, blank = True, max_length = 20)
    qq = models.CharField(verbose_name = "QQ号码", null = True, blank = True, max_length = 20)
    phone = models.CharField(verbose_name = "手机号码", max_length = 15, blank = True)
    tel = models.CharField(verbose_name = "办公电话", max_length = 20, blank = True)
    manager = models.CharField(verbose_name = '上级', max_length = 50, blank = True, default = '')

    cat_ids = models.CharField(verbose_name = "专长一级类目", max_length = 100, blank = True, null = True, default = '') # 自动与店铺专营类目匹配，多个以逗号分割
    now_load = models.IntegerField(verbose_name = "已服务用户数", null = True, default = 0)
    cycle_load = models.IntegerField(verbose_name = "本循环已分配用户数", null = True, default = 0)
    weight = models.IntegerField(verbose_name = "权重", null = False, default = 0)

    entry_date = models.DateField(verbose_name = "入职日期", default = datetime.date.today)
    contract_start = models.DateField(verbose_name = "合同开始日期", default = datetime.date.today)
    contract_end = models.DateField(verbose_name = "合同截止日期", null = True, blank = True)
    birthday = models.DateField(verbose_name = "生日", null = True, blank = True)
    id_no = models.CharField(verbose_name = "身份证号", max_length = 20, blank = True)
    residence = models.CharField(verbose_name = "户籍地址", max_length = 100, blank = True)
    education = models.CharField(verbose_name = "学历", max_length = 100, blank = True, choices = EDUCATION_CHOICES)
    school = models.CharField(verbose_name = "毕业院校", max_length = 50, blank = True)
    major = models.CharField(verbose_name = "专业", max_length = 50, blank = True)
    department = models.CharField(verbose_name = "部门", max_length = 50, blank = True, choices = DEPARTMENT_CHOICES)
    gender = models.CharField(verbose_name = "性别", max_length = 10, blank = True, choices = GENDER_CHOICES)
    status = models.CharField(verbose_name = "雇佣状态", max_length = 10, blank = True, choices = STATUS_CHOICES)
    note = models.TextField(verbose_name = "备注", blank = True, null = True)
    probation_date = models.DateField(verbose_name = "转正考核", default = None)

    def __str__(self):
        return '%s，%s' % (self.get_position_display(), self.name_cn)

    @property
    def client_group(self):
        """获取客户群"""
        if not hasattr(self, '_client_group'):
            self._client_group = ClientGroup.objects.filter(create_user__id = self.id)
        return self._client_group

    @property
    def mycustomers(self):
        if not hasattr(self, '_mycustomers'):
            self._mycustomers = self.__class__.bulk_hung_consult_mycustomers([self]).get(self.id, [])
        return self._mycustomers

    @property
    def mycustomers_withcat(self):
        """绑定cat_id"""
        if not hasattr(self, '_mycustomers_withcat'):
            shop_cat_dict = {acc['_id']:acc['cat_id'] for acc in account_coll.find({'_id':{'$in':[customer.shop_id for customer in self.mycustomers]}}, {'_id':True, 'cat_id':True})}
            for customer in self.mycustomers:
                customer.cat_id = shop_cat_dict.get(customer.shop_id) or 0
            self._mycustomers_withcat = self.mycustomers
        return self._mycustomers_withcat

    @classmethod
    def bulk_hung_consult_mycustomers(cls, psuser_list, reverse_hung = False):
        today = datetime.date.today()
        days_30ago = today - datetime.timedelta(days = 30) # 暂定到期时间大于30天前的客户为我们需要的数据
        _consult_list, _operater_list = [], []
        for psuser in psuser_list:
            if psuser.position in ("CONSULT", "CONSULTLEADER"):
                _consult_list.append(psuser)
            elif psuser.position in ("RJJH", "RJJHLEADER", "TPAE", "TPLEADER"):
                _operater_list.append(psuser)

        psuser_mapping = {}
        for customer in Customer.objects.filter(consult__in = _consult_list, current_highest_version__in = ("kcjl", "qn"), latest_end__gte = days_30ago):
            psuser_mapping.setdefault(customer.consult.id, []).append(customer)
        for customer in Customer.objects.filter(operater__in = _operater_list, current_highest_version__in = ("ztc", "vip", "rjjh"), latest_end__gte = days_30ago):
            psuser_mapping.setdefault(customer.operater.id, []).append(customer)

        if reverse_hung:
            for psuser in psuser_list:
                psuser._mycustomers = psuser_mapping.get(psuser.id, [])

        return psuser_mapping

    @classmethod
    def bulk_hung_consult_brief_mycustomers(cls, psuser_list):
        today = datetime.date.today()
        days_30ago = today - datetime.timedelta(days = 30) # 暂定到期时间大于30天前的客户为我们需要的数据
        _consult_list, _operater_list = [], []
        for psuser in psuser_list:
            if psuser.position in ("CONSULT", "CONSULTLEADER"):
                _consult_list.append(psuser)
            elif psuser.position in ("RJJH", "RJJHLEADER", "TPAE", "TPLEADER"):
                _operater_list.append(psuser)

        psuser_mapping = {}
        brief_fields = ["shop_id", "nick", "current_highest_version", "consult_id", "operater_id"]
        for customer in Customer.objects.values(*brief_fields).filter(consult__in = _consult_list, current_highest_version__in = ("kcjl", "qn"), latest_end__gte = days_30ago):
            customer = DictWrapper(customer)
            psuser_mapping.setdefault(customer.consult_id, []).append(customer)
        for customer in Customer.objects.values(*brief_fields).filter(operater__in = _operater_list, current_highest_version__in = ("ztc", "vip", "rjjh"), latest_end__gte = days_30ago):
            customer = DictWrapper(customer)
            psuser_mapping.setdefault(customer.operater_id, []).append(customer)

        for psuser in psuser_list:
            psuser._mycustomers = psuser_mapping.get(psuser.id, [])

        return psuser_mapping

    @staticmethod
    def get_allocate_consult(**kwargs):
        # 为用户分配顾问 ，weight=0的顾问不分配用户
        consult_list = PSUser.objects.filter(position__in = ['CONSULT', 'CONSULTLEADER', 'COMMANDER'], weight__gt = F('cycle_load'), **kwargs).exclude(status = '离职').order_by('cycle_load', '-weight')
        if not consult_list:
            consult_list = PSUser.objects.filter(position__in = ['CONSULT', 'CONSULTLEADER', 'COMMANDER'], weight__gt = 0, **kwargs).exclude(status = '离职')
            consult_list.update(cycle_load = 0)
        if consult_list:
            return consult_list[0]
        else:
            return None

    @staticmethod
    def allocate_consult(shop_id, history_orders):
        today = datetime.date.today()
        if len(history_orders) > 0:
            last_consult = history_orders[0].consult # 获取最后一个客服
            if last_consult:
                return last_consult

            last_consult = None
            for order in history_orders: # 获取最后在职一个操作人
                if order.consult:
                    last_consult = order.consult
                    break

            is_out = False # 判断是否转部门或离职
            if last_consult:
                if last_consult.status in ["离职", ""] or last_consult.position not in ["CONSULT", "CONSULTLEADER"]:
                    last_consult = PSUser.get_allocate_consult(department = last_consult.department)
                    is_out = True
            else:
                last_consult = PSUser.get_allocate_consult()

            if last_consult:
                is_counter = False if Subscribe.objects.filter\
                                            (consult = last_consult, shop = shop_id).count() > 0 else True

                for order in history_orders:
                    org_consult_id = order.consult_id if order.consult else 'None'
                    if is_out:
                        if order.end_date <= today:
                            continue
                    elif order.consult:
                        continue
                    order.consult = last_consult
                    order.save()
                    log.info('allocate_consult, shop_id=%s, subscribe_id=%s, org_consult_id=%s, new_consult_id=%s' % (order.shop_id, order.id, org_consult_id, last_consult.id))

                if is_counter:
                    last_consult.now_load = last_consult.now_load + 1
                    last_consult.cycle_load = last_consult.cycle_load + 1
                    last_consult.save()

                return last_consult
            else:
                pass # 是否考虑默认值

        return None

    @staticmethod
    def allocate_rjjh(valid_orders):
        tp_rjjh = None
        main_user_name = 'leiyan'

        if len(valid_orders) > 0:
            tp_rjjh = valid_orders[0].operater
            if tp_rjjh and tp_rjjh.position == 'RJJH':
                return tp_rjjh

            try:
                tp_rjjh = PSUser.objects.get(name = main_user_name)
            except Exception, e:
                log.error("staff name : %s is not existed, e=%s" % (main_user_name, e))
            else:
                for order in valid_orders:
                    if not order.operater:
                        order.operater = tp_rjjh
                        order.save(0)
                        log.info('allocate_rjjh, shop_id=%s, subscribe_id=%s, org_operater=None, new_operater=%s' % (order.shop_id, order.id, order.operater.id))

        return tp_rjjh

    @classmethod
    def refresh_now_load(cls):
        '''刷新所有客服的有效客户数'''
        try:
            cls.objects.all().update(now_load = 0) # 清空，再赋值
            sql = """
            update ncrm_psuser np join (
            select a.consult_id as consult_id, count(a.id) as shops from ncrm_subscribe a join (
            select max(id) as id from ncrm_subscribe where (article_code='ts-25811' or article_code='FW_GOODS-1921400') and consult_id is not null and start_date<=current_date group by shop_id
            ) b on a.id=b.id group by a.consult_id
            ) c on np.id=c.consult_id set np.now_load=c.shops;
            """
            execute_manage_sql(sql)
            return True
        except Exception, e:
            log.error('PSUser.refresh_now_load error, e=%s' % e)
            return False

    def get_mycustomers_balance(self):
        '''获取自己所持有效客户的余额'''
        result = {}
        shop_id_list = Customer.objects.filter(operater = self, latest_end__gt = datetime.date.today(), current_highest_version__in = ['rjjh', 'vip'], is_pausing=False).values_list('shop_id', flat = True)
        for shop_id in shop_id_list:
            try:
                tapi = get_tapi(shop_id = shop_id)
                # tobj = tapi.simba_account_balance_get()
                # result[unicode(shop_id)] = float(tobj.balance)
                balance = tapi.get_account_balance()
                result[unicode(shop_id)] = float(balance)
            except:
                continue
        return result

    @classmethod
    def refresh_common_group_statistic(cls):
        '''刷新通用客户群统计数据'''
        psuser_list = cls.objects.filter(department__in = OPERATION_GROUPS).exclude(status = '离职').exclude(position = 'COMMANDER')
        days3_ago = datetime.date.today() - datetime.timedelta(days = 3)
        for psuser in psuser_list:
            statistic_info = {}
            if psuser.position in ['CONSULT', 'CONSULTLEADER']:
                temp_flag = 1
                extra_str = "and latest_category in ('kcjl', 'qn') and consult_id=%s" % psuser.id
            elif psuser.position in ['RJJH', 'RJJHLEADER']:
                temp_flag = 2
                extra_str = "and latest_category='rjjh' and operater_id=%s" % psuser.id
            elif psuser.position in ['TPAE', 'TPLEADER']:
                temp_flag = 3
                extra_str = "and latest_category in ('vip', 'ztc', 'dyy') and operater_id=%s" % psuser.id
            else:
                temp_flag = 0
                extra_str = "and latest_end<=current_date and saler_id=%s" % psuser.id

            # # 意向客户
            # sql = "select count(*) from ncrm_customer where is_potential=1 %s" % extra_str
            # rows = execute_query_sql_return_tuple(sql)
            # statistic_info['is_potential'] = rows[0][0]

            # # 问题客户
            # sql = "select count(*) from ncrm_customer where is_discontent=1 %s" % extra_str
            # rows = execute_query_sql_return_tuple(sql)
            # statistic_info['is_discontent'] = rows[0][0]

            # # 待一访
            # if temp_flag > 0:
            #     sql = "select count(*) from ncrm_customer where contact_count=0 and latest_end>current_date and is_pawn=0 %s" % extra_str
            #     rows = execute_query_sql_return_tuple(sql)
            #     statistic_info['to_1st_contact'] = rows[0][0]

            # # 待二访
            # if temp_flag == 1:
            #     sql = "select count(*) from ncrm_customer where contact_count=1 and latest_end>current_date and is_pawn=0 %s" % extra_str
            #     rows = execute_query_sql_return_tuple(sql)
            #     statistic_info['to_2nd_contact'] = rows[0][0]

            if temp_flag == 2:
                # 取消过托管
                sql = "select count(*) from ncrm_customer where rjjh_unmnt>='%s' and latest_end>current_date %s" % (days3_ago, extra_str)
                rows = execute_query_sql_return_tuple(sql)
                statistic_info['unmnt_3days'] = rows[0][0]

                # 手操客户
                sql = "select count(*) from ncrm_customer where rjjh_frozen=1 and latest_end>current_date %s" % extra_str
                rows = execute_query_sql_return_tuple(sql)
                statistic_info['rjjh_frozen'] = rows[0][0]

            # 3天未操作
            if temp_flag > 1:
                sql = "select count(*) from ncrm_customer where latest_operate<='%s' and latest_end>current_date and is_pausing=0 %s" % (days3_ago, extra_str)
                rows = execute_query_sql_return_tuple(sql)
                statistic_info['unoperated_3days'] = rows[0][0]

            CacheAdpter.set(CacheKey.NCRM_COMMON_GROUP_STATISTIC % psuser.id, statistic_info, 'crm', 60 * 60 * 48)

    @classmethod
    def init_last_month_weight(cls):
        """根据上个月各顾问的活跃用户人天数重新分配他们的新客户权重"""
        psuser_list = cls.objects.filter(position__in = ['CONSULT', 'CONSULTLEADER']).exclude(status = '离职')

        # 获取上月各顾问的活跃用户人天数
        acc_dict = {obj.id:0 for obj in psuser_list}
        td = datetime.date.today()
        this_month_1st = datetime.date(td.year, td.month, 1)
        last_month_end = this_month_1st - datetime.timedelta(days = 1)
        last_month_1st = datetime.date(last_month_end.year, last_month_end.month, 1)
        sp_list = StaffPerformance.objects.filter(identify = 'active_customer_count', result_date__gte = last_month_1st, result_date__lt = this_month_1st)
        for sp in sp_list:
            if sp.psuser_id in acc_dict:
                data_json = json.loads(sp.data_json)
                if type(data_json) == list:
                    acc_dict[sp.psuser_id] += len(data_json)
        acc_list = acc_dict.items()
        acc_list.sort(lambda x, y:cmp(y[1], x[1]))

        # 初始化权重字典
        bonus_list = [6, 5, 4] # TOP3的额外奖励
        psuser_weight_dict = {obj.id:0 for obj in psuser_list}
        for psuser_id, acc in acc_list[:len(bonus_list)]:
            psuser_weight_dict[psuser_id] += bonus_list.pop(0)

        # 根据各部门分配额进行分配
        dept_weight_dict = {'GROUP1':32, 'GROUP2':32, 'GROUP3':32} # 各部门的分配额
        dept_psuser_dict = {}
        for obj in psuser_list:
            dept_psuser_dict.setdefault(obj.department, []).append(obj.id)
        for dept, weight_sum in dept_weight_dict.items():
            dept_psuser_list = dept_psuser_dict.get(dept, [])
            if dept_psuser_list:
                avg_weight = weight_sum / len(dept_psuser_list)
                for psuser_id in dept_psuser_list:
                    psuser_weight_dict[psuser_id] += avg_weight
                offset_weight = weight_sum - avg_weight * len(dept_psuser_list)
                if offset_weight > 0:
                    temp_list = [(psuser_id, acc_dict[psuser_id]) for psuser_id in dept_psuser_list]
                    temp_list.sort(lambda x, y:cmp(y[1], x[1]))
                    for psuser_id, acc in temp_list[:offset_weight]:
                        psuser_weight_dict[psuser_id] += 1

        # 保存权重分配
        for obj in psuser_list:
            obj.weight = psuser_weight_dict[obj.id]
            obj.save()


class Diary(models.Model):
    author = models.ForeignKey(PSUser, verbose_name = '日记 作者', related_name = 'diary_author', null = True)
    content = models.TextField(verbose_name = '今日日志')
    create_time = models.DateTimeField(verbose_name = '日期时间', default = datetime.datetime.now)
    todolist = models.TextField('明日计划')
    comment = models.TextField('点评', blank = True)
    commenter = models.ForeignKey(PSUser, verbose_name = '点评人', related_name = 'diary_commenter', default = '', null = True, blank = True)
    comment_time = models.DateTimeField(verbose_name = "点评时间", null = True, blank = True)

    def is_current(self):
        return not time_is_ndays_interval(self.create_time, 2)

    def is_today(self):
        return time_is_someday(self.create_time)

    def is_current_week(self):
        return not time_is_ndays_interval(self.create_time, 6)

    class Meta:
        ordering = ['-create_time']


class ClientGroup(models.Model):
    title = models.CharField(verbose_name = "客户群名称", max_length = 100)
    query = models.CharField(verbose_name = "查询范围", max_length = 200)
    id_list = models.TextField(verbose_name = "用户列表")
    create_time = models.DateTimeField(verbose_name = "创建时间", null = True, blank = True, default = datetime.datetime.now)
    create_user = models.ForeignKey(PSUser, null = False, blank = False)
    checked = models.SmallIntegerField(verbose_name = "在工作台选中", default = 1)
    note = models.TextField(verbose_name = "备注", blank = True, null = True)
    group_type = models.IntegerField(verbose_name = "系统保留群", default = 0, choices = ((0, '普通'), (1, '优先保留'), (2, '优先剔除'), (3, '差评跟踪')))

    @property
    def id_list_length(self):
        return self.id_list and len(eval(self.id_list)) or 0

    def save_id_list(self, add_id_list):
        """保存客户id"""
        old_id_list = self.id_list and eval(self.id_list) or []
        self.id_list = list(set(add_id_list + old_id_list))
        self.save()

    def delete_id_list(self, del_id_list):
        """删除客户id"""
        old_id_list = self.id_list and eval(self.id_list) or []
        for id in del_id_list:
            if old_id_list.count(id):
                old_id_list.remove(id)
        if old_id_list:
            self.id_list = old_id_list
        else:
            self.id_list = ''
        self.save()

    @classmethod
    def refresh_my_group(cls, psuser_id, group_type):
        """过滤系统保留群里的客户，只保留自己的客户"""
        if group_type in (1, 2):
            my_group = cls.objects.filter(create_user_id = psuser_id, group_type = group_type)
            if my_group:
                my_group = my_group[0]
                try:
                    id_list = eval(my_group.id_list)
                    if type(id_list) == list and id_list:
                        my_group.id_list = list(Customer.objects.filter(shop_id__in = id_list, consult_id = psuser_id).values_list('shop_id', flat = True))
                        my_group.save()
                except:
                    pass


class Plan(models.Model):
    title = models.CharField(verbose_name = "计划名称", max_length = 100)
    psuser = models.ForeignKey(PSUser, null = False, blank = False, related_name = "psuser")
    parent_id = models.IntegerField(verbose_name = "父级id", default = 0)
    related_id = models.IntegerField(verbose_name = "计划关联id", default = 0)
    event_list = models.TextField(verbose_name = "动作列表")
    target = models.TextField(verbose_name = "目标")
    note = models.TextField(verbose_name = "备注")
    progress = models.TextField(verbose_name = "进度")
    start_time = models.DateField(verbose_name = "开始时间", blank = True, null = True, default = None)
    end_time = models.DateField(verbose_name = "结束时间", blank = True, null = True, default = None)
    create_time = models.DateField(verbose_name = "创建时间", null = True, blank = True, default = datetime.datetime.now)
    create_user = models.ForeignKey(PSUser, null = False, blank = False, related_name = "create_user")

    def get_plan_recursive_info(self):
        """聚合用户列表 及 员工列表: 递归过去"""
        psuser_ids = [int(self.psuser.id)]

        plan_cursor = Plan.objects.filter(Q(related_id = self.id) | Q(parent_id = self.id))
        for plan in plan_cursor:
            temp_psuser_ids = plan.get_plan_recursive_info()
            psuser_ids.extend(temp_psuser_ids)

        return psuser_ids

    def generate_plan_process(self, is_force = False):
        return {}

    @staticmethod
    def generate_process(event_list, time_scope, psuser_list, is_force = False):
        return {}

    @property
    def lower_plans(self):
        """获取下属计划"""
        if not hasattr(self, '_lower_plan'):
            self._lower_plan = Plan.objects.filter(related_id = self.id)
        return self._lower_plan

    @property
    def relate_plan(self):
        """获取关联计划"""
        if not hasattr(self, '_relate_plan'):
            try:
                self._relate_plan = Plan.objects.get(id = self.related_id)
            except ObjectDoesNotExist:
                self._relate_plan = None
        return self._relate_plan

    @property
    def child_plan(self):
        """获取子计划"""
        if not hasattr(self, '_child_plan'):
            self._child_plan = None
            try:
                self._child_plan = Plan.objects.filter(parent_id = self.id).exclude(parent_id = 0)
            except Exception, e:
                log.info('get relate_plan Plan error, e=%s' % (e))
        return self._child_plan

    @property
    def parent_plan(self):
        """获取父计划"""
        if not hasattr(self, '_parent_plan'):
            self._parent_plan = None
            try:
                self._parent_plan = Plan.objects.get(id = self.parent_id)
            except Exception, e:
                log.info('get parent_plan Plan error, e=%s' % (e))
        return self._parent_plan


class Customer(models.Model):
    ACCT_STATUS_CHOICES = ((0, '正常'), (1, '死账户'), (2, '店铺关闭'))
    INFO_STATUS_CHOICES = ((0, '尚未爬取'), (1, '爬取中'), (2, '爬取成功'), (3, '爬取失败'))
    # TP_COOP_STATUS_CHOICES = [('unknonw', '未知'), ('ordering', '合作中'), ('paused', '暂停'), ('expired', '过期')]

    shop_id = models.IntegerField(verbose_name = "店铺ID", unique = True)
    nick = models.CharField(verbose_name = "淘宝主号", max_length = 30, null = True, unique = True, default = '', help_text = "必须是主号，不能有空格，否则读不出数据")
    is_b2c = models.SmallIntegerField(verbose_name = "是否天猫店", blank = True, null = True, default = 0)
#     level = models.SmallIntegerField(verbose_name = "信誉等级", blank = True, null = True, default = 0)
#     last_login = models.DateField(verbose_name = "最近登录日期", blank = True, null = True)
    is_goldmember = models.BooleanField(verbose_name='是否黄金会员',  default = False)
    category = models.CharField(verbose_name = "经营范围", max_length = 50, blank = True, null = True, default = '')
    # cat_id = models.IntegerField(verbose_name = "类目ID", blank = True, null = True)
    address = models.CharField(verbose_name = "地址", max_length = 50, blank = True, null = True, default = '')
    remind = models.SmallIntegerField(verbose_name = "是否开启短信提醒", blank = True, null = True, default = 0)

    seller = models.CharField(verbose_name = "联系人", max_length = 50, blank = True, null = True, default = '')
    phone = models.CharField(verbose_name = "手机号", max_length = 30, blank = True, null = True, default = '')
    qq = models.CharField(verbose_name = "QQ", max_length = 15, blank = True, null = True, default = '')
    ww = models.CharField(verbose_name = "旺旺", max_length = 30, blank = True, null = True, default = '')
    alipay = models.CharField(verbose_name = "支付宝账号", max_length = 50, blank = True, null = True, default = '')

    lz_name = models.CharField(verbose_name = "量子账号", max_length = 40, blank = True, null = True, default = '')
    lz_psw = models.CharField(verbose_name = "量子密码", max_length = 20, blank = True, null = True, default = '')
    zz_name = models.CharField(verbose_name = "钻展账号", max_length = 40, blank = True, null = True, default = '')
    zz_psw = models.CharField(verbose_name = "钻展密码", max_length = 20, blank = True, null = True, default = '')
    ztc_name = models.CharField(verbose_name = "直通车代理账号", max_length = 40, blank = True, null = True, default = '')
    ztc_psw = models.CharField(verbose_name = "直通车代理密码", max_length = 20, blank = True, null = True, default = '')
    acct_name = models.CharField(verbose_name = "店铺登录账号", max_length = 40, blank = True, null = True, default = '')
    acct_psw = models.CharField(verbose_name = "店铺登录密码", max_length = 20, blank = True, null = True, default = '')

    source = models.CharField(verbose_name = "用户来源", max_length = 30, blank = True, null = True, default = '')
    acct_status = models.SmallIntegerField(verbose_name = "用户状态", blank = True, null = True, default = 0, choices = ACCT_STATUS_CHOICES)
    info_status = models.SmallIntegerField(verbose_name = "信息爬取状态", blank = True, null = True, default = 0, choices = INFO_STATUS_CHOICES)
    # tp_coop_status = models.CharField(verbose_name = "合作状态", max_length = 30, default = "unknown", choices = TP_COOP_STATUS_CHOICES)

    create_time = models.DateTimeField(verbose_name = "创建时间", blank = True, null = True, default = datetime.datetime.now)
    update_time = models.DateTimeField(verbose_name = "最近更新时间", default = None, null = True)
    note = models.TextField(verbose_name = "备注", blank = True, null = True)

    creator = models.ForeignKey(PSUser, related_name = "+", blank = True, null = True, verbose_name = "创建人")
    saler = models.ForeignKey(PSUser, related_name = "+", blank = True, null = True, verbose_name = "当前签单人")
    operater = models.ForeignKey(PSUser, related_name = "+", blank = True, null = True, verbose_name = "当前操作人")
    consult = models.ForeignKey(PSUser, related_name = "+", blank = True, null = True, verbose_name = "当前客服")
    temp_flag = models.IntegerField(verbose_name="临时标记", default=0)  # 启用临时规则时用, 值为 PSUser.id

    # 针对通用客户群所需要添加的字段
    current_highest_version = models.CharField(verbose_name = "当前最高订单版本", max_length = 20, db_index = True, choices = CATEGORY_CHOICES) # 为销服组服务
    latest_category = models.CharField(verbose_name = "最新业务类型", max_length = 20, db_index = True, choices = CATEGORY_CHOICES) # 不包含钻展、店铺装修、其他
    latest_end = models.DateField(verbose_name = "最新到期日期", blank = True, null = True)
    is_pausing = models.BooleanField(verbose_name = "暂停服务中", default = False)
    advertise_effect = models.IntegerField(verbose_name = "推广效果等级", choices = [(0, '其他'), (1, '优质客户'), (2, '效果差')], default = 0)
    contact_fail = models.BooleanField(verbose_name = "联系不上", default = False)
    bad_comment = models.BooleanField(verbose_name = "差评跟踪", default = False)
    is_pawn = models.BooleanField(verbose_name = "水军", default = False)
    unknown_subscribe = models.BooleanField(verbose_name = "订单来源未知", default = False)
    contact_count = models.IntegerField(verbose_name = "当前订单联系次数", default = 0)
    latest_contact = models.DateField(verbose_name = "最近联系日期", blank = True, null = True)
    latest_operate = models.DateField(verbose_name = "最近操作日期", blank = True, null = True)
    rjjh_unmnt = models.DateField(verbose_name = "人机版中最近取消过重点托管的日期", blank = True, null = True)
    rjjh_frozen = models.BooleanField(verbose_name = "人机版但掌柜要求不许优化的店铺，手操客户", default = False)
#     balance = models.IntegerField(verbose_name = "直通车账户余额", blank = True, null = True)
    is_discontent = models.BooleanField(verbose_name = "对软件或服务不满的客户，问题客户，维护客户", default = False)
    is_potential = models.BooleanField(verbose_name = "意向客户，潜在客户", default = False)

    # 针对客户收货情况
    zip_code = models.CharField(verbose_name = "邮编", default = None, max_length = 10, null = True)
    receiver = models.CharField(verbose_name = "收货人", default = None, max_length = 30, null = True)
    receive_address = models.CharField(verbose_name = "收货地址", default = None, max_length = 100, null = True)

    @classmethod
    def refresh_latest_end(cls, shop_id):
        sub_list = Subscribe.objects.filter(shop = shop_id).exclude(category__in = ['zz', 'zx', 'other', 'seo', 'kfwb']).order_by('-end_date')
        if sub_list:
            cls.objects.filter(shop_id = shop_id).update(latest_end = sub_list[0].end_date)

    @classmethod
    def refresh_latest_end_category(cls, shop_id_list):
        '''更新Customer的latest_end, latest_category'''
        td = datetime.date.today()
        category_priority = ['qn', 'kcjl', 'rjjh', 'vip', 'ztc', 'dyy', 'ztbd']
        sub_dict = Subscribe.refresh_end_date(shop_id_list)
        for shop_id, article_code_dict in sub_dict.items():
            update_dict = {}
            temp_list0 = [max(temp_list, key = lambda x: x.create_time) for article_code, temp_list in article_code_dict.items() if temp_list]
            if temp_list0:
                temp_list1 = [sub for sub in temp_list0 if sub.end_date > td]
                if temp_list1:
                    latest_sub = temp_list1[0]
                    for sub in temp_list1[1:]:
                        if category_priority.index(sub.category) > category_priority.index(latest_sub.category):
                            latest_sub = sub
                    update_dict.update({'latest_category': latest_sub.category, 'latest_end': latest_sub.end_date})
                else:
                    latest_sub = max(temp_list0, key = lambda x: x.end_date)
                    update_dict.update({'latest_category': latest_sub.category, 'latest_end': latest_sub.end_date})
                cls.objects.filter(shop_id = shop_id).update(**update_dict)

    @classmethod
    def get_customer_byshopid(cls, shop_id):
        try:
            return cls.objects.get(shop_id = shop_id)
        except:
            return None

    @staticmethod
    def sync_customer_info(customer):
        # TODO: 杨荣凯 此处做兼容, 过度接口
        try:
            n_customer, _ = Customer.objects.get_or_create(shop_id = customer.shop_id)
            n_customer.nick = customer.nick
            n_customer.seller = customer.cname
            n_customer.phone = customer.phone
            n_customer.qq = customer.qq
            if not n_customer.ww:
                n_customer.ww = customer.ww
            if not n_customer.lz_name:
                n_customer.lz_name = customer.lz_id
            if not n_customer.lz_psw:
                n_customer.lz_psw = customer.lz_psw
            if not n_customer.ztc_name:
                n_customer.ztc_name = customer.ztc_id
            if not n_customer.ztc_psw:
                n_customer.ztc_psw = customer.ztc_psw
            n_customer.save()
            return n_customer
        except Exception, e:
            log.error("function sync_subscribe_info error, customer=%s, e=%s" % (customer, e))
            return None

    @property
    def ztcjl_login_url(self):
        if not hasattr(self, '_ztcjl_login_url'):
            self._ztcjl_login_url = {}
            users = User.objects.filter(nick = self.nick)
            sub_list = ArticleUserSubscribe.objects.filter(nick = self.nick, deadline__gt = datetime.datetime.now())
            if sub_list:
                self._ztcjl_login_url = users[0].get_backend_url(user_type = "staff")
        return self._ztcjl_login_url

    @property
    def valid_perfect_field(self):
        return ['phone', 'qq', 'receiver', 'receive_address', 'zip_code']

    @property
    def is_perfect_info(self):
        """是否已经完善信息"""
        if all(getattr(self, field) not in (None, "") for field in self.valid_perfect_field):
            return True, self
        else:
            return False, self

    @property
    def perfect_info(self):
        return {field: getattr(self, field) for field in self.valid_perfect_field \
                if getattr(self, field) not in (None, "")}

    def update_perfect_info(self, data_dict):
        self._bak = copy.deepcopy(self)
        for field in self.valid_perfect_field:
            setattr(self, field, data_dict.get(field, ""))

        try:
            self.save()
            del self._bak
            return True, ''
        except:
            # 保存有误，进行回滚操作
            for field in self.valid_perfect_field:
                setattr(self, field, getattr(self._bak, field))
            return False, '更新数据失败'

    @classmethod
    def get_or_create_servers(cls, shop_id_list, category = 'software', default_server_list = None):
        '''批量获取或分配订单中的服务人员，包括：签单人，人机，TP，客服，部门，操作人'''
        try:
            subscribes = Subscribe.get_subscribes_8catetory(shop_id_list, category)
            # 找出每个店铺各类订单最近一笔的服务人员，并检查每笔订单是否需要分配服务人员
            shop_servers_dict = {}
            today = datetime.date.today()
            days_30_ago = today - datetime.timedelta(days = 30)
            days_7_ago = today - datetime.timedelta(days = 7)
            GROUP_LIST = GROUPS
            if not default_server_list:
                default_server_list = [None, None, None, None, None, None]
            for sobj in subscribes:
                server_list = shop_servers_dict.setdefault(sobj.shop_id, default_server_list[:]) # [psuser, rjjh, tp, consult, department, operater_index]
                # 对每笔订单是否需要分配服务人员进行标记
                if sobj.end_date <= today:
                    sobj.allocate_flag = False
                else:
                    sobj.allocate_flag = True

                if sobj.psuser:
                    psuser = sobj.psuser
                    # if psuser.position in ['SELLER', 'SALELEADER'] and psuser.status != '离职':
                    if psuser.status != '离职':
                        if not server_list[0]:
                            server_list[0] = psuser
                    if not server_list[4] and psuser.department in GROUP_LIST:
                        server_list[4] = psuser.department
                if sobj.category == 'rjjh':
                    if sobj.operater:
                        operater = sobj.operater
                        # if operater.status != '离职':
                        # if operater.position in ['RJJH', 'RJJHLEADER'] and operater.status != '离职':
                        #     sobj.allocate_flag = False
                        if not server_list[1]:
                            server_list[1] = operater
                        if not server_list[4] and operater.department in GROUP_LIST:
                            server_list[4] = operater.department
                        if server_list[5] is None:
                            server_list[5] = 1
                elif sobj.category in ['vip', 'ztc']:
                    if sobj.operater:
                        operater = sobj.operater
                        # if operater.status != '离职':
                        # if operater.position in ['TPAE', 'TPLEADER', 'OPTAGENT', 'RJJH', 'RJJHLEADER', 'SHOPMANAGER', 'SHOPASSISTANT', 'QC', 'SEO'] and operater.status != '离职':
                        #     sobj.allocate_flag = False
                        if not server_list[2]:
                            server_list[2] = operater
                        if not server_list[4] and operater.department in GROUP_LIST:
                            server_list[4] = operater.department
                        if server_list[5] is None:
                            server_list[5] = 2
                if sobj.consult and sobj.end_date > days_7_ago and sobj.consult.name_cn != '技术部':
                    consult = sobj.consult
                    # if consult.position in ['CONSULT', 'CONSULTLEADER', 'SELLER', 'SALELEADER'] and consult.status != '离职':
                    if consult.status != '离职':
#                         sobj.allocate_flag = False
                        if not server_list[3]:
                            server_list[3] = consult
                    if not server_list[4] and consult.department in GROUP_LIST:
                        server_list[4] = consult.department

            # 检查订单并分配服务人员
            refresh_flag = False
            for sobj in subscribes:
                if sobj.allocate_flag:
                    _psuser, _rjjh, _tp, _consult, _department, _operater_index = shop_servers_dict.get(sobj.shop_id, [None, None, None, None, None, None])
                    if category == 'rjjh' and not _rjjh:
                        continue
                    elif category == 'vip' and not _tp:
                        continue

                    allocation_record = {
                        'is_changed': 0,
                        'psuser_id': 0,
                        'psuser_cn': '系统',
                        'shop_id': sobj.shop_id,
                        'subscribe_id': sobj.id,
                        'sub_time': sobj.create_time,
                        'category_cn': sobj.get_category_display(),
                        'pay': sobj.pay,
                        'create_time': datetime.datetime.now(),
                        'org_id_list': '%s, %s, %s' % (sobj.psuser.id if sobj.psuser else 0, sobj.operater.id if sobj.operater else 0, sobj.consult.id if sobj.consult else 0),
                        'org_cn_list': '%s, %s, %s' % (sobj.psuser.name_cn if sobj.psuser else '无', sobj.operater.name_cn if sobj.operater else '无', sobj.consult.name_cn if sobj.consult else '无')
                    }
                    if not _consult:
                        kwargs = {'department':_department} if _department else {}
                        _consult = PSUser.get_allocate_consult(**kwargs)
                        if sobj.category in ['kcjl', 'qn']:
                            _consult.cycle_load += 1
                            _consult.save()
                    if _consult:
                        _department = _consult.department
                        shop_servers_dict[sobj.shop_id][3] = _consult
                        shop_servers_dict[sobj.shop_id][4] = _department
                        if _consult != sobj.consult:
                            if not(sobj.consult and sobj.consult.name_cn == '技术部'):
                                # org_consult_id = sobj.consult_id if sobj.consult else None
                                sobj.consult = _consult
                                # log.info('Customer.get_or_create_servers change consult, shop_id=%s, subscribe_id=%s, org_consult_id=%s, new_consult_id=%s' % (sobj.shop_id, sobj.id, org_consult_id, _consult.id))
                                refresh_flag = True
                                allocation_record['is_changed'] = 1
                        sobj.consult_xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(_consult.id)
                        sobj.save()

                    if sobj.category == 'rjjh':
                        if not _rjjh or _rjjh.status == '离职':
                            leaders = PSUser.objects.filter(position = 'RJJHLEADER')
                            my_leader = [obj for obj in leaders if _rjjh and _rjjh.department == obj.department]
                            default_rjjh = list(PSUser.objects.filter(name = 'leiyan'))
                            if _rjjh:
                                _rjjhs = my_leader + default_rjjh
                            else:
                                _rjjhs = default_rjjh
                            if not (_rjjh and my_leader) and leaders:
                                # 邮件提醒
                                subject = '掌柜 %s 有新订单等待分配哟。。' % sobj.shop.nick
                                content = '开车精灵系统自动提醒邮件，勿回复。'
                                cc_list = ['%s@paithink.com' % obj.name for obj in leaders]
                                send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, cc_list)
                            if _rjjhs:
                                _rjjh = _rjjhs[0]


                        # if not _rjjh and _department:
                        #     # _rjjhs = PSUser.objects.filter(department = _department, position = 'RJJHLEADER')
                        #     _rjjhs = PSUser.objects.filter(name = 'leiyan')
                        #     if _rjjhs:
                        #         _rjjh = _rjjhs[0]
                        #     # 邮件提醒
                        #     leaders = PSUser.objects.filter(position = 'RJJHLEADER').values_list('name', flat = True)
                        #     if leaders:
                        #         subject = '掌柜 %s 有新订单等待分配哟。。' % sobj.shop.nick
                        #         content = '开车精灵系统自动提醒邮件，勿回复。'
                        #         cc_list = ['%s@paithink.com' % name for name in leaders]
                        #         send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, cc_list)
                        if _rjjh:
                            shop_servers_dict[sobj.shop_id][1] = _rjjh
                            if sobj.operater != _rjjh:
                                # org_operater_id = sobj.operater_id if sobj.operater else None
                                sobj.operater = _rjjh
                                sobj.save()
                                # log.info('Customer.get_or_create_servers change operater, shop_id=%s, subscribe_id=%s, org_operater_id=%s, new_operater_id=%s' % (sobj.shop_id, sobj.id, org_operater_id, _rjjh.id))
                                allocation_record['is_changed'] = 1
                    elif sobj.category == 'vip':
                        _tps = []
                        if not _tp:
                            if _department:
                                _tps = PSUser.objects.filter(department = _department, position = 'TPLEADER')
                        elif _tp.status == '离职':
                            _tps = PSUser.objects.filter(department = _tp.department, position = 'TPLEADER')
                        if _tps:
                            _tp = _tps[0]

                        # if not _tp and _department:
                        #     _tps = PSUser.objects.filter(department = _department, position = 'TPLEADER')
                        #     if _tps:
                        #         _tp = _tps[0]
                        if _tp:
                            shop_servers_dict[sobj.shop_id][2] = _tp
                            if sobj.operater != _tp:
                                # org_operater_id = sobj.operater_id if sobj.operater else None
                                sobj.operater = _tp
                                sobj.save()
                                # log.info('Customer.get_or_create_servers change operater, shop_id=%s, subscribe_id=%s, org_operater_id=%s, new_operater_id=%s' % (sobj.shop_id, sobj.id, org_operater_id, _tp.id))
                                allocation_record['is_changed'] = 1

                    if allocation_record.pop('is_changed'):
                        allocation_record.update({
                            'new_id_list': '%s, %s, %s' % (sobj.psuser.id if sobj.psuser else 0, sobj.operater.id if sobj.operater else 0, sobj.consult.id if sobj.consult else 0),
                            'new_cn_list': '%s, %s, %s' % (sobj.psuser.name_cn if sobj.psuser else '无', sobj.operater.name_cn if sobj.operater else '无', sobj.consult.name_cn if sobj.consult else '无')
                        })
                        ar_coll.insert(allocation_record)

            # 刷新customer的签单人、操作人和顾问
            if category == 'software':
                for shop_id, server_list in shop_servers_dict.items():
                    cls.objects.filter(shop_id = shop_id).update(saler = server_list[0], operater = server_list[server_list[5]] if server_list[5] is not None else None, consult = server_list[3])
            # 刷新所有客服的有效客户数，暂不刷新，容易导致数据库锁住
            # if refresh_flag:
            #     PSUser.refresh_now_load()
            return shop_servers_dict
        except Exception, e:
            log.error("Customer.get_or_create_servers error, shop_id_list=%s, category='%s', e=%s" % (json.dumps(shop_id_list), category, e))
            return {}

    def save_one(self):
        '''保存新的用户信息，如果用户已存在，则覆盖更新，用于手工录入'''
        try:
            exist_obj = Customer.objects.get(nick = self.nick)
        except ObjectDoesNotExist:
            if not self.shop_id:
                shop_id = Customer.get_shop_by_nick(self.nick)
                if shop_id:
                    self.shop_id = shop_id
                else:
                    return False
            self.save()
        else:
            exist_obj.is_b2c = self.is_b2c
#             exist_obj.level = self.level
            exist_obj.category = self.category
            # exist_obj.cat_id = self.cat_id
            exist_obj.address = self.address
            exist_obj.seller = self.seller
            exist_obj.phone = self.phone
            exist_obj.qq = self.qq
            exist_obj.ww = self.ww
            exist_obj.lz_name = self.lz_name
            exist_obj.lz_psw = self.lz_psw
            exist_obj.zz_name = self.zz_name
            exist_obj.zz_psw = self.zz_psw
            exist_obj.ztc_name = self.ztc_name
            exist_obj.ztc_psw = self.ztc_psw
            exist_obj.acct_name = self.acct_name
            exist_obj.acct_psw = self.acct_psw
            exist_obj.source = self.source
            exist_obj.acct_status = self.acct_status
            exist_obj.info_status = self.info_status
            exist_obj.acct_status = self.acct_status
            exist_obj.udpate_time = datetime.datetime.now()
            exist_obj.note = self.note
            exist_obj.save()
        return True

    @staticmethod
    def get_shop_by_nick(nick):
        try:
            tobj = tsapi.shop_get(nick = nick, fields = 'sid, nick, title, pic_path, created, shop_score')
            return tobj.shop.sid
        except TopError, e:
            log.error("get_shop_by_nick TopError, nick=%s, e=%s" % (nick, e))
        except Exception, e:
            log.error("get_shop_by_nick Error, nick=%s, e=%s" % (nick, e))
        return False

    @staticmethod
    def bulk_import_xls(filename, source):
        '''从excel文件批量导入用户信息，要固定列顺序、第三行开始录入数据'''
        try:
            bk = xlrd.open_workbook(filename)
            sh = bk.sheets()[0]
        except Exception, e:
            log.exception('bulk_import_xls error, %s' % (e))
            return 0, 0, 0, '读取文件失败，请检查文件格式'

        try:
            cust_dict = {}
            batch_count = 2000
            all_count, exist_count, new_count = 0, 0, 0
            for i in xrange(2, sh.nrows):
                row_data = sh.row_values(i)
                if not row_data[0].strip():
                    continue
                all_count += 1
                row_dict = {
                    "nick":row_data[0].strip(),
                    "shop_id":str(row_data[1]).strip(),
                    "is_b2c":row_data[2].strip() in ['B', '是'] and 1 or 0,
                    "credit":get_credit_level(row_data[3].strip()),
                    "category":row_data[4].strip(),
                    "address":row_data[5].strip(),
                    "seller":row_data[6].strip(),
                    "phone":row_data[7].strip(),
                    "qq":row_data[8].strip(),
                    "ww":row_data[9].strip(),
                    "lz_name":row_data[10].strip(),
                    "lz_psw":row_data[11].strip(),
                    "zz_name":row_data[12].strip(),
                    "zz_psw":row_data[13].strip(),
                    "ztc_name":row_data[14].strip(),
                    "ztc_psw":row_data[15].strip(),
                    "acct_name":row_data[16].strip(),
                    "acct_psw":row_data[17].strip(),
                    "note":row_data[18].strip()
                }
                cust_dict.update({row_data[0].strip():row_dict})

                if i % batch_count == 0 or i == (sh.nrows - 1):
                    tmp_exist, tmp_new = Customer.bulk_save(cust_dict, source)
                    exist_count += tmp_exist
                    new_count += tmp_new
                    cust_dict = {}
        except Exception, e:
            log.exception('bulk_import_xls error, %s' % (e))
            return all_count, exist_count, new_count, '解析和导入数据失败，请检查数据格式'
        return all_count, exist_count, new_count, ''

    @staticmethod
    def bulk_save(cust_dict, source):
        '''批量保存用户信息'''
        if not cust_dict:
            return 0, 0

        # 分组查询，区分需要更新和新增的用户
        exist_count, new_count = 0, 0
        for tmp_nick_list in genr_sublist(cust_dict.keys(), 2000):
            exist_list = Customer.objects.filter(nick__in = tmp_nick_list)

            # 处理已经存在的用户，只更新原来为空的属性，即默认已录入的信息是最新的
            exist_nick_list = []
            for exist_obj in exist_list:
                exist_nick_list.append(str(exist_obj.nick))
                row_dict = cust_dict[exist_obj.nick]
                # 原值为空，而且导入值不为空则更新
                need_save = False
                for key, value in row_dict.items():
                    if getattr(exist_obj, key) == None and value != None:
                        setattr(exist_obj, key, value)
                        need_save = True
                if need_save:
                    exist_obj.udpate_time = datetime.datetime.now()
                    exist_obj.save()
                exist_count += 1

            # 处理新用户
            new_obj_list = []
            new_nick_list = set(tmp_nick_list) - set(exist_nick_list)
            for new_nick in new_nick_list:
                row_dict = cust_dict[new_nick]
                shop_id = row_dict.get("shop_id", 0)
                if not shop_id:
                    shop_id = Customer.get_shop_by_nick(new_nick)
                    if shop_id:
                        row_dict.update({"shop_id":shop_id})
                    else:
                        continue
                # 导入值不为空则更新
                new_obj = Customer(nick = new_nick)
                for key, value in row_dict.items():
                    if hasattr(new_obj, key) and value != None:
                        setattr(new_obj, key, value)
                new_obj.source = source
                new_obj_list.append(new_obj)

            try:
                new_count = bulk_insert_for_model(new_obj_list, commit_number = 2000)
            except Exception, e:
                log.exception("bulk save customer error, e=%s" % (e))
                return exist_count, new_count
            return exist_count, new_count

    @staticmethod
    def get_cust_id_dict(nick_list, source = ''): # TODO: zhangyu 如果是在线订购的订单，则除了要同步customer表，还需要同步user表
        '''获取用户nick与id的字典信息'''
        nick_id_dict, failed_list = {}, []

        # 得到已存在用户的nick_id列表
        exist_list = Customer.objects.filter(nick__in = nick_list)
        for exist_obj in exist_list:
            nick_id_dict.update({exist_obj.nick:exist_obj.shop_id})

        # 处理新用户，不存在则批量插入
        new_obj_list = []
        new_nick_list = list(set(nick_list) - set(nick_id_dict.keys()))
        shop_nick_dict = {}
        for new_nick in new_nick_list:
            shop_id = Customer.get_shop_by_nick(new_nick)
            if not shop_id:
                failed_list.append(new_nick)
            else:
                shop_nick_dict[shop_id] = new_nick
        exist_shop_id_list = Customer.objects.filter(shop_id__in = shop_nick_dict.keys()).values_list('shop_id', flat = True)
        for shop_id, nick in shop_nick_dict.items():
            if shop_id not in exist_shop_id_list:
                new_obj_list.append(Customer(nick = nick, shop_id = shop_id, source = source))
            else:
                nick_id_dict[nick] = shop_id

        try:
            bulk_insert_for_model(new_obj_list, commit_number = 2000) # TODO: wangqi 20141210 这里建议调整一下，批量插入虽好，但是有可能失败导致整个失败！
        except Exception, e:
            log.exception("get_cust_id_dict error, e=%s" % (e))
            return nick_id_dict, failed_list

        # 得到新用户的nick_id列表
        exist_list = Customer.objects.filter(nick__in = new_nick_list)
        for exist_obj in exist_list:
            nick_id_dict.update({exist_obj.nick:exist_obj.shop_id})
        return nick_id_dict, failed_list

    # 用于绑定订购关系数据
    @staticmethod
    def binder_order_info(customer_list, subscribe_category = None):
        shop_id_list = [customer.shop_id for customer in customer_list]
        query_dict = {'shop__in':shop_id_list}
        if subscribe_category != 'all':
            if subscribe_category in Const.SUBSCRIBE_CATEGORY_SET:
                query_dict['category__in'] = Const.SUBSCRIBE_CATEGORY_SET[subscribe_category]
            else:
                query_dict['category'] = subscribe_category

        psuser_name_dict = dict(PSUser.objects.values_list('id', 'name_cn'))
        unsubscribe_list = event_coll.find({'shop_id': {'$in': shop_id_list}, 'type': 'unsubscribe'})
        order_unsubscribe_dict = {}
        for ul in unsubscribe_list:
            ul['psuser_name'] = psuser_name_dict.get(ul.get('saler_id', ''), '市场')

            # 退款原因 多选 判断是否是列表
            if(type(ul.get('refund_reason', '')) == list):
                resaon_cn = ''
                for resaon in ul.get('refund_reason'):
                    resaon_cn += dict(Unsubscribe.REFUND_REASON_CHOICES).get(int(resaon))
                    resaon_cn += '--'
                ul['refund_reason_cn'] = resaon_cn
            else:
                ul['refund_reason_cn'] = dict(Unsubscribe.REFUND_REASON_CHOICES).get(ul.get('refund_reason', ''))

            order_unsubscribe_dict.setdefault(ul['event_id'], []).append(ul)

        abo_list = Subscribe.objects.filter(**query_dict).order_by('-create_time')
        # if subscribe_category == 'all':
        #     abo_list = abo_list.exclude(category = 'other')
        abo_dic = {}
        order_statistic = {}
        for abo in abo_list:
            abo.unsubscribe_list = order_unsubscribe_dict.get(abo.id, [])
            temp_list = abo_dic.setdefault(abo.shop_id, [])
            temp_list.append(abo)
            temp_dict = order_statistic.setdefault(abo.shop_id, {'cycle':0, 'order_count':0, 'pay':0, 'pay2':0, 'unknown_count':0, 'unknown_pay':0})
            if abo.biz_type == 6:
                temp_dict['unknown_count'] += 1
                temp_dict['unknown_pay'] += abo.pay
            else:
                if abo.pay > 0:
                    temp_dict['order_count'] += 1
                    temp_dict['pay'] += abo.pay
                    if abo.category not in ['kcjl', 'qn']:
                        temp_dict['pay2'] += abo.pay
                    if abo.cycle:
                        try:
                            temp_dict['cycle'] += int(abo.cycle.replace('个月', '').replace('月', ''))
                        except:
                            pass

        for customer in customer_list:
            customer.order_info = abo_dic.get(customer.shop_id, [])
            customer.order_statistic = order_statistic.get(customer.shop_id, {'cycle':0, 'order_count':0, 'pay':0, 'unknown_count':0, 'unknown_pay':0})
        return customer_list

    @staticmethod
    def bind_user_info(customer_list):
        """绑定用户最后一次登录时间"""
        shop_id_list = [customer.shop_id for customer in customer_list]
        nick_list = [customer.nick for customer in customer_list]
        user_dict = {u.shop_id:u for u in User.objects.filter(shop_id__in = shop_id_list)}
        ad_perms_dict = {p.user_id:p.perms_code for p in AdditionalPermission.objects.filter(user_id__in = [u.id for u in user_dict.values()])}
        nick_port_dict = dict(NickPort.objects.select_related('port').filter(nick__in = nick_list).values_list('nick', 'port__domain'))
        for c in customer_list:
            c.user = user_dict.get(c.shop_id, None)
            if c.user:
                c.ad_perms = ad_perms_dict.get(c.user.id, '')
            c.domain = nick_port_dict.get(c.nick, '').split('.')[0]
        return customer_list

    @staticmethod
    def bind_ztcrpt(customer_list):
        """绑定直通车昨日报表"""
        from apps.subway.models_account import Account

        shop_id_list = [customer.shop_id for customer in customer_list]
        rpt_dict = Account.Report.get_summed_rpt({'shop_id': {'$in': shop_id_list}}, rpt_days = 1)
        for customer in customer_list:
            customer.rpt = rpt_dict.get(customer.shop_id, Account.Report())

    def bind_events(self):
        """绑定事件"""
        psuser_name_dict = dict(PSUser.objects.values_list('id', 'name_cn'))
        event_list = list(event_coll.find({'shop_id':self.shop_id}))
        for event in event_list:
            event['psuser_name'] = psuser_name_dict.get(event['psuser_id'], '')
            event['id'] = event.pop('_id')
            if event['type'] == 'contact':
                event['model_type'] = 'Contact'
                event['desc'] = dict(Contact.CONTACT_TYPE_CHOICES).get(event['contact_type'], '异常') + '联系'
            elif event['type'] == 'operate':
                event['model_type'] = 'Operate'
                event['desc'] = dict(OPER_TYPE_CHOICES).get(event['oper_type'], '异常操作')
            elif event['type'] == 'comment':
                event['model_type'] = 'Comment'
                comment_type = event['comment_type'] / 100
                if comment_type == 1:
                    event['desc'] = '好评'
                elif comment_type == 2:
                    event['desc'] = '差评未改'
                elif comment_type == 3:
                    event['desc'] = '差评已改'
                event['note'] = '【%s】%s' % (dict(Comment.COMMENT_TYPE_CHOICES).get(event['comment_type'], '异常评论'), event['note'])
            elif event['type'] == 'reintro':
                event['model_type'] = 'ReIntro'
                event['desc'] = '转介绍'
                event['psuser_name'] += ' 转 %s' % psuser_name_dict.get(event['receiver_id'], '')
            elif event['type'] == 'unsubscribe':
                event['model_type'] = 'Unsubscribe'
                event['desc'] = '退款(%.2f元)' % (event['refund'] / 100.0)
            elif event['type'] == 'pause':
                event['model_type'] = 'Pause'
                event['desc'] = '暂停订单'
        subscribe_list = Subscribe.objects.filter(shop = self.shop_id)
        for subs in subscribe_list:
            event = {}
            event['id'] = subs.id
            event['type'] = 'subscribe'
            event['model_type'] = 'Subscribe'
            event['psuser_id'] = subs.psuser.id if subs.psuser else ''
            event['psuser_name'] = psuser_name_dict.get(subs.psuser.id, '系统') if subs.psuser else '系统'
            event['create_time'] = subs.create_time
            event['category'] = subs.category
            event['note'] = subs.note
            event['desc'] = '订购'
            event_list.append(event)
        return event_list

    # 批量绑定事件
    @staticmethod
    def bulk_bind_events(customer_list):
        event_list = event_coll.find({'shop_id':{'$in':[customer.shop_id for customer in customer_list]}})
        psuser_name_dict = dict(PSUser.objects.values_list('id', 'name_cn'))
        shop_events_dict = {}
        for event in event_list:
            event['id'] = event['_id']
            event['psuser_name'] = psuser_name_dict.get(event['psuser_id'], '无名')
            events = shop_events_dict.setdefault(event['shop_id'], [[], [], [], [], [], []]) # contact, operate, comment, reintro, unsubscribe, pause
            if event['type'] == 'contact':
                event['desc'] = dict(Contact.CONTACT_TYPE_CHOICES).get(event['contact_type'], '其他')
                events[0].append(event)
            elif event['type'] == 'operate':
                events[1].append(event)
            elif event['type'] == 'comment':
                events[2].append(event)
            elif event['type'] == 'reintro':
                events[3].append(event)
            elif event['type'] == 'unsubscribe':
                events[4].append(event)
            elif event['type'] == 'pause':
                events[5].append(event)
                if not event.get('proceed_date'):
                    end_date = Subscribe.objects.get(id = event['event_id']).end_date
                    event['offset_days'] = max((min(end_date, datetime.date.today()) - event['create_time'].date()).days, 0)
                    # event['offset_days'] = min((end_date - event['create_time'].date()).days, (datetime.date.today() - event['create_time'].date()).days)
                    event['remain_days'] = max((end_date - event['create_time'].date()).days, 0)
        for c in customer_list:
            c.contact, c.operate, c.comment, c.reintro, c.unsubscribe, c.pause = shop_events_dict.get(c.shop_id, [[], [], [], [], [], []])
            c.event_list = c.contact + c.operate + c.unsubscribe + c.pause
            c.event_list.sort(lambda x, y:cmp(y['create_time'], x['create_time']))
            c.event_list = c.event_list[:7]

    @staticmethod
    def bind_client_group_ids(customer_list, all_client_group):
        client_group_dict = {}
        for a in all_client_group:
            client_group_dict[a.id] = a.id_list and eval(a.id_list) or []

        for k, v in client_group_dict.items():
            for c in customer_list:
                if v.count(c.shop_id):
                    if not hasattr(c, 'client_group_ids'):
                        c.client_group_ids = []
                    c.client_group_ids.append(k)

    # 绑定用户最新一笔订单
    @staticmethod
    def bind_last_subscribe(customer_list, subscribe_category = None):
        shop_id_list = [customer.shop_id for customer in customer_list]
        query_dict = {'shop__in':shop_id_list}
        if subscribe_category != 'all':
            if subscribe_category in Const.SUBSCRIBE_CATEGORY_SET:
                query_dict['category__in'] = Const.SUBSCRIBE_CATEGORY_SET[subscribe_category]
            else:
                query_dict['category'] = subscribe_category

        abo_list = Subscribe.objects.filter(**query_dict).order_by('-create_time')
        if subscribe_category == 'all':
            abo_list = abo_list.exclude(category__in = ['other', 'seo', 'kfwb'])
        abo_dic = {}
        for abo in abo_list:
            if abo.shop_id not in abo_dic:
                abo_dic[abo.shop_id] = abo
        for customer in customer_list:
            customer.order_info = abo_dic.get(customer.shop_id, [])
        return customer_list

    # 绑定7天报表数据
    @staticmethod
    def bind_7days_data(customer_list):
        shop_id_list = [customer.shop_id for customer in customer_list]
        rpt_dict = Account.Report.get_summed_rpt({'shop_id': {'$in':shop_id_list}}, rpt_days = 7)
        for customer in customer_list:
            account_rpt = rpt_dict.get(customer.shop_id, Account.Report())
            customer.rpt = account_rpt.to_dict()
        return customer_list

    @classmethod
    def refresh_current_category(cls, shop_id_list = None):
        try:
            log.info('start refresh current category')
            date_today = date_2datetime(datetime.datetime.today())
            if not shop_id_list:
                shop_id_list = cls.objects.filter(latest_end__gt = date_today).order_by('shop_id').values_list('shop_id', flat = True)
            for shop_id in shop_id_list:
                current_highest_version = Subscribe.get_current_highest_version(shop_id = shop_id)
                if current_highest_version:
                    cls.objects.filter(shop_id = shop_id).update(current_highest_version = current_highest_version)
            log.info('finished refresh current category, update_count=%s' % (len(shop_id_list)))
        except Exception, e:
            log.error('refresh current category error, e=%s' % (e))
        return

#===============================================================================
# 事件模型定义
#===============================================================================

class XiaoFuGroup(models.Model):
    '''销服组模型'''
    XFG_DEPARTMENT_CHOICES = [x for x in PSUser.DEPARTMENT_CHOICES if 'GROUP' in x[0]]
    IS_ACTIVE_CHOIES = ((True, '工作中'), (False, '已冻结'))

    department = models.CharField(verbose_name = "部门", choices = XFG_DEPARTMENT_CHOICES, max_length = 50, blank = False, null = False)
    consult = models.ForeignKey(PSUser, verbose_name = '顾问', related_name = 'xfgroup_consult')
    seller = models.ForeignKey(PSUser, verbose_name = '销售', related_name = 'xfgroup_seller')
    create_time = models.DateTimeField(verbose_name = '创建时间', default = datetime.datetime.now)
    start_time = models.DateTimeField(verbose_name = '服务开始时间', default = datetime.datetime.now)
    end_time = models.DateTimeField(verbose_name = '服务结束时间')
    is_active = models.BooleanField(verbose_name = '是否激活', choices = IS_ACTIVE_CHOIES, default = True) # 已废弃
    # freeze_time = models.DateTimeField(verbose_name = '冻结时间')
    name = models.CharField(verbose_name = '组名称', default = '', max_length = 30)

    def __str__(self):
        return '%s-%s' % (self.get_department_display(), self.name)

    @property
    def work_status(self):
        if not hasattr(self, '_work_status'):
            now = datetime.datetime.now()
            if self.start_time < now:
                if not self.end_time:
                    self._work_status = '工作中'
                elif self.end_time <= now:
                    self._work_status = '已废弃'
                else:
                    self._work_status = '待废弃'
            else:
                self._work_status = '待工作'
        return self._work_status

    @classmethod
    def get_xfgroupid_8psuserid(cls, psuser_id):
        now = datetime.datetime.now()
        xfgs = cls.objects.filter(start_time__lte = now, consult_id = psuser_id).filter(Q(end_time__isnull = True) | Q(end_time__gte = now)).order_by('create_time')
        if xfgs:
            return xfgs[0]
        xfgs = cls.objects.filter(start_time__lte = now, seller_id = psuser_id).filter(Q(end_time__isnull = True) | Q(end_time__gte = now)).order_by('create_time')
        if xfgs:
            return xfgs[0]
        else:
            return None

    @classmethod
    def get_involved_xfgroup(cls, start_date, end_date):
        xfgs = cls.objects.filter(start_time__lte = date_2datetime(end_date) + datetime.timedelta(days = 1)) \
            .filter(Q(end_time__isnull = True) | Q(end_time__gte = date_2datetime(start_date))) \
            .order_by('-department')
        return xfgs

    @classmethod
    def get_xfgroup_status(cls, query_dict, is_active = ''):
        now = datetime.datetime.now()
        query_reuslt = cls.objects.filter(**query_dict)
        if is_active is True:
            query_reuslt = query_reuslt.filter(Q(end_time__isnull = True) | Q(end_time__gte = now))
        elif is_active is False:
            query_reuslt = query_reuslt.filter(end_time__lte = now)
        return query_reuslt.select_related('consult', 'seller').order_by('-create_time', 'department')

class Event(models.Model):
    shop = models.ForeignKey(Customer, verbose_name = "店铺", to_field = 'shop_id')
    create_time = models.DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    psuser = models.ForeignKey(PSUser, verbose_name = "用户ID", null = True, blank = True)
    note = models.TextField(verbose_name = "备注，聊天记录等", null = True, blank = True)

    class Meta:
        abstract = True

    @classmethod
    def add_event(cls, shop_id, **args):
        try:
            return cls.objects.create(shop_id = shop_id, **args)
        except Exception, e:
            log.error("to generate event error, shop_id={}, event_class={}, e={}".format(shop_id, \
                                                                                         cls.__name__, e))
            return None

class PreSalesAdvice(Event): # 售前咨询
    BUSINESS_CHOICES = [('DECORATION', '装修咨询'),('SOFTWARE', '软件咨询'),('TP', 'TP咨询'),]
    business = models.CharField(verbose_name = "咨询业务", choices = BUSINESS_CHOICES, max_length = 50)


class Login(Event): # 登录
    plateform_type = models.CharField(verbose_name = "登陆平台", max_length = 10, choices = PLATEFORM_TYPE_CHOICES)

class Monitor(Event):
    plateform_type = models.CharField(verbose_name = "登陆平台", max_length = 10, choices = PLATEFORM_TYPE_CHOICES)

    @classmethod
    def add_event(cls, shop_id, psuser, plateform_type):
        today = datetime.datetime.now().replace(hour = 0, minute = 0, second = 0)
        if not cls.objects.filter(shop = shop_id, psuser = psuser, create_time__gt = today).count():
            return super(Monitor, cls).add_event(shop_id, psuser = psuser, plateform_type = plateform_type)
        return True


class Subscribe(Event):
    """用户的订购表，包含淘宝订单（自动同步）和非淘宝订单"""
    PAY_TYPE_CHOICES = (
        (1, '淘宝后台付款'),
        (2, '公司支付宝付款'),
        (3, '公司中国银行账户付款'),
        (4, '香花私人支付宝付款'),
        (5, '派生视觉支付宝付款'),
        (6, '现金付款'),
        (7, '技术一部支付宝付款'),
        (8, '技术二部支付宝付款'),
        (9, '技术三部支付宝付款'),

        (10, '技术四部支付宝付款'),
        (11, '技术五部支付宝付款'),
        (12, '技术六部支付宝付款'),
        (16, '技术七部支付宝付款'),
        (13, '销服一部支付宝付款'),
        (14, '销服二部支付宝付款'),
        (15, '销服三部支付宝付款'),
    )
    # 销服标记  售后标记于2017-05-10去除，但CHOICES保留为适应旧数据
    XF_FLAG_CHOICES = (
        (1, '销售'),
        (2, '售后'),
        (3, '市场'),
        (4, '增值事业'),
        (5, '技术')
    )
    order_id = models.BigIntegerField(verbose_name = "子订单号id", default = 0) # 软件订单用，人工单不用考虑该项
    category = models.CharField(verbose_name = "业务类型", max_length = 50, db_index = True, choices = CATEGORY_CHOICES)
    article_code = models.CharField(verbose_name = "应用码", max_length = 50, choices = ARTICLE_CODE_CHOICES)
    article_name = models.CharField(verbose_name = "应用名", max_length = 80, null = True, blank = True)
    item_code = models.CharField(verbose_name = "应用码", max_length = 50, null = True, blank = True) # TODO: 是否要保留，看需求，这里可以给服务分级，如TP，有专家版、普通版等；软件有四引擎、双引擎等
    item_name = models.CharField(verbose_name = "应用名", max_length = 80, null = True, blank = True)
    fee = models.IntegerField(verbose_name = "原价")
    refund_fee = models.IntegerField(verbose_name = "升级退款", default=0)
    pay = models.IntegerField(verbose_name = "成交金额")
    cycle = models.CharField(verbose_name = "订购周期", max_length = 30)
    biz_type = models.IntegerField(verbose_name = "订单类型", default = 1, choices = ((1, '新订'), (2, '续订'), (3, '升级'), (4, '后台赠送'), (5, '后台自动续订'), (6, '未知'), (7, '自我新订'), (8, '转介绍'), (9, '软件成交'), (10, '进账划分客户'), (11, '店铺提成')))
    source_type = models.IntegerField(verbose_name = "成交方式", default = 1, choices = SUBSCRIBE_SOURCE_TYPE_CHOICES)
    start_date = models.DateField(verbose_name = "服务开始日期")
    end_date = models.DateField(verbose_name = "服务结束日期", db_index = True)
    operater = models.ForeignKey(PSUser, related_name = "subscribe_operater", verbose_name = "操作人", null = True, blank = True) # FK，也是psuser的ID，上面的第一个对应的是销售人员，这个对应的服务人员（如人机、直通车车手、钻展等）
    consult = models.ForeignKey(PSUser, related_name = "subscribe_consult", verbose_name = "客服", null = True, blank = True)
    visible = models.IntegerField(verbose_name = "默认可见", choices = EVENT_MARK_CHOICES, default = 0)
    xf_flag = models.IntegerField(verbose_name = "岗位类型", choices = XF_FLAG_CHOICES)
    xfgroup = models.ForeignKey(XiaoFuGroup, verbose_name = "签单人销服组ID", related_name = "saler_xfgroup", null = True, blank = True)
    consult_xfgroup = models.ForeignKey(XiaoFuGroup, verbose_name = "顾问销服组ID", related_name = "consult_xfgroup", null = True, blank = True)
    pay_type = models.IntegerField(verbose_name = "付款方式", choices = PAY_TYPE_CHOICES, default = 1)
    pay_type_no = models.CharField(verbose_name = "付款信息(支付宝账号/银行账号)__户主姓名", max_length = 80, blank = True)
    approver = models.ForeignKey(PSUser, related_name = "subscribe_approver", verbose_name = "审批人", null = True, blank = True)
    approval_time = models.DateTimeField(verbose_name = "审批日期")
    approval_status = models.IntegerField(verbose_name = "审批状态", choices = APPROVAL_STATUS_CHOICES, default = 0)
    # to add 2017-05-11
    has_contract = models.BooleanField(verbose_name="是否有合同", default=False)
    chat_file_path = models.CharField(verbose_name="聊天文件路径", null=True, blank=True, max_length=500)
    pre_sales_advice = models.ForeignKey(PreSalesAdvice, related_name="subscribe_pre_sales_advice", verbose_name = "售前咨询记录")
    conversion_time = models.DateField(verbose_name = "咨询转化时间")
    # 字段映射top对象字段的字典
    TOP_MAPPING_DICT = {'create_time': 'create',
                        'start_date': 'order_cycle_start',
                        'end_date': 'order_cycle_end',
                        'biz_type':'biz_type',
                        'cycle':'order_cycle',
                        'fee':'fee',
                        'refund_fee':'refund_fee',
                        'pay':'total_pay_fee',
                        'article_code':'article_code',
                        'article_name':'article_name',
                        'item_code':'item_code',
                        'item_name':'article_item_name',
                        'order_id':'order_id',
                        'nick':'nick'}

    @property
    def serve_fee(self):
        """加上了升级退款的实付金额"""
        return self.refund_fee + self.pay

    @staticmethod
    def parse_category(item_code, create_time):
        '''根据订单的item_code和订购时间来确定他的类别'''
        try:
            create_time = create_time[:10]
            for start_date, end_date, category in Const.SUBSCRIBE_CATEGORY[item_code]:
                if start_date and start_date > create_time:
                    continue
                if end_date and end_date <= create_time:
                    continue
                return category
        except Exception, e:
            log.error('Subscribe.parse_category error, item_code=%s, create_time=%s, e=%s' % (item_code, create_time, e))
        else:
            log.error('Subscribe.parse_category error, no such category, item_code=%s, create_time=%s' % (item_code, create_time))
        return None

    @classmethod
    def get_subscribes_8catetory(cls, shop_id_list, category = 'software', is_valid = False):
        '''批量获取多个店铺中指定类别的订单'''
        if shop_id_list and category:
            kwargs = {}
            if len(shop_id_list) == 1:
                kwargs['shop'] = shop_id_list[0]
            else:
                kwargs['shop__in'] = shop_id_list
            if category != 'all':
                if category in Const.SUBSCRIBE_CATEGORY_SET:
                    kwargs['category__in'] = Const.SUBSCRIBE_CATEGORY_SET[category]
                else:
                    kwargs['category'] = category
            result = cls.objects.filter(**kwargs).order_by('-create_time')
            if category == 'all':
                result = result.exclude(category__in = ['seo', 'kfwb', 'other'])
            if is_valid:
                today = datetime.date.today()
                result = result.filter(start_date__lte = today, end_date__gt = today)
            return result
        return []

    @classmethod
    def refresh_end_date(cls, shop_id_list):
        '''自动调整各业务中存在周期重叠的订单的结束日期'''
        sub_dict = {}
        try:
            td = datetime.date.today()
            sub_list = cls.objects.filter(shop_id__in = shop_id_list, article_code__in = ['ts-25811', 'FW_GOODS-1921400', 'tp-001', 'tp-004']).only('shop_id', 'article_code', 'item_code', 'category', 'create_time', 'start_date', 'end_date')
            for sub in sub_list:
                sub_dict.setdefault(sub.shop_id, {}).setdefault(sub.article_code, []).append(sub)
            for shop_id, article_code_dict in sub_dict.items():
                for article_code, temp_list0 in article_code_dict.items():
                    temp_list0.sort(key = lambda x: x.start_date)
                    prev_sub = None
                    for i, sub in enumerate(temp_list0):
                        if sub.category != 'ztbd':
                            if prev_sub:
                                if prev_sub.end_date > sub.start_date:
                                    if prev_sub.create_time <= sub.create_time:
                                        prev_sub.end_date = sub.start_date
                                        prev_sub.save()
                                    else:
                                        sub.end_date = sub.start_date
                                        sub.save()
                                        continue
                            prev_sub = sub
                    # temp_list1 = [sub for sub in temp_list0 if sub.end_date > td]
                    # if temp_list1:
                    #     lastest_sub = max(temp_list1, key = lambda x: x.create_time)
                    #     for sub in temp_list1:
                    #         if sub.category != 'ztbd' and sub.item_code != lastest_sub.item_code:
                    #             sub.end_date = min(lastest_sub.start_date, sub.end_date)
                    #             sub.save()
        except Exception, e:
            log.error('Subscribe.refresh_end_date error, e=%s' % e)
        return sub_dict

    @classmethod
    def insert_new_subscribe(cls, top_abo_list, existed_orderid_list, **kwargs):
        # 1、同步订单
        # 2、同步用户
        # 3、分配顾问

        insert_list = []
        nick_list = []
        taobao_unique = {order.order_id:order for order in top_abo_list}
        tgroup_user = PSUser.objects.get(name_cn='技术部')
        for abo in taobao_unique.values():
            if abo.order_id not in existed_orderid_list:
                nick_list.append(abo.nick)
                temp_obj = cls()
                for attr_name, mapped_attr_name in cls.TOP_MAPPING_DICT.items():
                    setattr(temp_obj, attr_name, getattr(abo, mapped_attr_name))
                for k, v in kwargs.items():
                    print k, "   ", v
                    setattr(temp_obj, k, v)
                temp_obj.category = cls.parse_category(temp_obj.item_code, temp_obj.create_time) or ''
                if temp_obj.category in ['rjjh', 'vip']:
                    temp_obj.consult = tgroup_user
                temp_obj.approval_status = 1
                insert_list.append(temp_obj)
            else:
                continue

        insert_obj_list = []
        no_shop_id_list = []
        valid_shop_ids = []
        temp_subscribe_dict = {}
        if nick_list:
            nick_dict, failed_list = Customer.get_cust_id_dict(nick_list = nick_list)
            for insert_obj in insert_list:
                if insert_obj.nick in nick_dict:
                    insert_obj.shop_id = nick_dict.get(insert_obj.nick, 0)
                    del insert_obj.nick
                    insert_obj.xf_flag = 1
                    insert_obj.pay_type = 1
                    insert_obj_list.append(insert_obj)
                    temp_list = temp_subscribe_dict.setdefault(insert_obj.shop_id, [])
                    temp_list.append(insert_obj)
                    valid_shop_ids.append(insert_obj.shop_id)
                else:
                    no_shop_id_list.append(insert_obj.nick)

            if no_shop_id_list:
                log.error('sync order found lost shop_id nick list, nick_list=%s' % no_shop_id_list)

            if failed_list:
                log.error('sync order found invalid nick list, nick_list=%s' % failed_list)

        # 如果没有同步到 shop_id 我将调过这笔订单
        for temp_list in genr_sublist(insert_obj_list, 500):
            try:
                log.info('Subscribe.insert_new_subscribe.bulk_insert_for_model, order_id_list=%s' % (json.dumps([order.order_id for order in temp_list])))
                bulk_insert_for_model(temp_list)
            except Exception, e:
                log.error("Subscribe bulk_insert_for_model error, e=%s, order_id_list=%s" % (e, json.dumps([order.order_id for order in temp_list])))

        valid_shop_ids = list(set(valid_shop_ids))
        # 分配员工，更新customer的所属人
        Customer.get_or_create_servers(valid_shop_ids)
        # 更新Customer的统计字段
        # for shop_id, sub_list in temp_subscribe_dict.items():
        #     sub_list.sort(lambda x, y:cmp(y.end_date, x.end_date))
        #     if sub_list[0].pay > 0:
        #         Customer.objects.filter(shop_id = shop_id).update(latest_category = sub_list[0].category, latest_end = sub_list[0].end_date[:10], contact_count = 0)
        #         users = User.objects.filter(shop_id = shop_id)
        #         if users:
        #             AdditionalPermission.objects.filter(user = users[0]).delete()

        # 自动调整被升级或降级的订单的end_date，更新Customer的latest_end, latest_category
        Customer.refresh_latest_end_category(valid_shop_ids)
        # 更新Customer的contact_count, 清空额外权限码
        temp_list = [shop_id for shop_id, sub_list in temp_subscribe_dict.items() if sum([int(sub.pay) for sub in sub_list]) > 0]
        Customer.objects.filter(shop_id__in = temp_list).update(contact_count = 0)
        users = User.objects.filter(shop_id__in = temp_subscribe_dict.keys())
        if users:
            AdditionalPermission.objects.filter(user__in = users).delete()
        return True

    @classmethod
    def save_soft_subscribe(cls, top_abo_list):
        """保存软件订单"""
        existed_orderid_list = Subscribe.objects.filter(order_id__in = [order.order_id for order in top_abo_list]).values_list('order_id', flat = True)
        return cls.insert_new_subscribe(top_abo_list, existed_orderid_list)

    @classmethod
    def query_servicing_subscribe(cls, shop_id_list, category_list):
        today = datetime.date.today()
        subscribe_cursor = Subscribe.objects.filter(shop_id__in = shop_id_list, \
                                     category__in = category_list, end_date__gte = today , start_date__lte = today)
        return subscribe_cursor

    def payfee(self):
        return int(self.pay / 100)

    def display_biz_type(self):
        biz_type = self.biz_type
        if biz_type == 1:
            return '新订'
        elif biz_type == 2:
            return '续订'
        elif biz_type == 3:
            return '升级'
        elif biz_type == 4:
            return '后台赠送'
        elif biz_type == 5:
            return '后台自动续订'
        elif biz_type == 6:
            return '未知'
        else:
            return '未知来源'

    def article_version(self):
        article_type = None
        if 'ts' in self.article_code:
            article_type = 'web'
        if 'FW' in self.article_code:
            article_type = 'qn'
        return article_type

    def is_ending(self):
        return time_is_ndays_interval(self.end_date, -7)

    def is_ended(self):
        return get_start_datetime(self.end_date) < datetime.datetime.today()

    def is_future(self):
        return self.start_date > datetime.date.today()

    @classmethod
    def get_current_highest_version(cls, shop_id):
        result = ''
        try:
            date_today = date_2datetime(datetime.datetime.today())
            cat_list = cls.objects.filter(shop_id = shop_id, end_date__gte = date_today).order_by('category').values_list('category', flat = True)
            cat_level_dict = {k[0]: CATEGORY_CHOICES.index(k) for k in CATEGORY_CHOICES}
            if cat_list:
                min_index = len(CATEGORY_CHOICES)
                for category in cat_list:
                    cur_index = cat_level_dict[category]
                    if cur_index < min_index:
                        min_index = cur_index
                result = CATEGORY_CHOICES[min_index][0]
        except Exception, e:
            log.error('calc current_highest_version error, shop_id=%s, e=%s' % (shop_id, e))
        return result

    @classmethod
    def tj_global_pay(cls, start_date, end_date):
        result_dict = {}
        tj_department_list = OPERATION_GROUPS + GROUPS
        tj_position_list = ['CONSULT', 'SELLER', 'RJJH', 'TPAE', 'OPTAGENT', 'TPLEADER', 'RJJHLEADER']
        department_dict = dict(PSUser.DEPARTMENT_CHOICES)

        for dpt in tj_department_list:
            result_dict[dpt] = {
                'department': department_dict[dpt],
                'department_id': dpt,
                'kcjl_paycount': 0,
                'qn_paycount': 0,
                'position_dict': {p.lower(): 0 for p in tj_position_list},
                'total_pay': 0
            }

        extend_condition = " and approval_status > -1 "
        qs_string_1 = """
            select b.department, b.position, sum(a.sum_pay) from
            (select psuser_id, sum(pay) as sum_pay from ncrm_subscribe
                where psuser_id is not null %s and create_time>='%s' and create_time<='%s' and biz_type !=6 group by psuser_id
            ) a join (select id, position, department from ncrm_psuser where department in %s and position in %s) b
            on a.psuser_id = b.id group by b.department, b.position order by b.department
        """ % (extend_condition, start_date, end_date, tuple(tj_department_list), tuple(tj_position_list))
        query_tuple_1 = execute_query_sql_return_tuple(qs_string_1)
        for department, position, pay in query_tuple_1:
            result_dict[department]['position_dict'].update({position.lower(): int(pay)})
            result_dict[department]['total_pay'] += int(pay)

        qs_string_2 = """
            select b.department, a.article_code, sum(sub_count) from
            (select psuser_id, article_code, count(*) as sub_count from ncrm_subscribe
              where psuser_id is not null %s and create_time>='%s' and create_time<='%s' and article_code in ('ts-25811', 'FW_GOODS-1921400')
              group by psuser_id, article_code
            ) a join (select id, position, department from ncrm_psuser where department in %s and position in %s) b
            on a.psuser_id = b.id group by b.department, a.article_code
        """ % (extend_condition, start_date, end_date, tuple(tj_department_list), tuple(tj_position_list))
        query_tuple_2 = execute_query_sql_return_tuple(qs_string_2)
        for department, article_code, count in query_tuple_2:
            if article_code == 'ts-25811':
                result_dict[department]['kcjl_paycount'] += int(count)
            else:
                result_dict[department]['qn_paycount'] += int(count)

        for dpt, v_dict in result_dict.items():
            v_dict['position_dict']['rjjh'] += v_dict['position_dict']['rjjhleader']
            v_dict['position_dict']['tpae'] += v_dict['position_dict']['tpleader']

        return sorted(result_dict.values(), key = lambda k: k['department_id'])

    @classmethod
    def tj_global_pay1(cls, start_date, end_date):
        result_dict = {}
        tj_dpt_list = OPERATION_GROUPS + GROUPS
        dpt_choices = dict(PSUser.DEPARTMENT_CHOICES)

        for dpt in tj_dpt_list:
            result_dict[dpt] = {
                'dpt_id': dpt,
                'name_cn': dpt_choices.get(dpt, dpt),
                'psuser_dict': {},
                'data': {
                    'ztc_vip': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'rjjh': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'kcjl': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'qn': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'zz': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'zx': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'dyy': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'seo': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'other': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'total': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                },
            }

        sql1 = """
            select s.psuser_id, s.category, s.sub_pay, s.sub_count, p.department, p.name_cn from (
            select psuser_id, category, sum(pay) as sub_pay, count(1) as sub_count from ncrm_subscribe
            where psuser_id is not null and create_time>='%s' and create_time<='%s' and biz_type !=6 group by psuser_id, category
            ) s join ncrm_psuser p on s.psuser_id=p.id
        """ % (start_date, end_date)
        query_result1 = execute_query_sql_return_tuple(sql1)
        for psuser_id, cat, sub_pay, sub_count, dpt, name_cn in query_result1:
            if dpt not in result_dict:
                continue
            dpt_data = result_dict[dpt]['data']
            psuser_data = result_dict[dpt]['psuser_dict'].setdefault(psuser_id, {
                'name_cn': name_cn,
                'data': {
                    'ztc_vip': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'rjjh': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'kcjl': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'qn': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'zz': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'zx': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'dyy': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'seo': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'other': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                    'total': {'sub_pay': 0, 'sub_count': 0, 'shop_list': []},
                },
            })['data']
            if cat in ['ztc', 'vip']:
                cat = 'ztc_vip'
            if cat in dpt_data:
                dpt_data[cat]['sub_pay'] += int(sub_pay)
                dpt_data[cat]['sub_count'] += int(sub_count)
                dpt_data['total']['sub_pay'] += int(sub_pay)
                dpt_data['total']['sub_count'] += int(sub_count)
                psuser_data[cat]['sub_pay'] += int(sub_pay)
                psuser_data[cat]['sub_count'] += int(sub_count)
                psuser_data['total']['sub_pay'] += int(sub_pay)
                psuser_data['total']['sub_count'] += int(sub_count)

        sql2 = """
            select s.psuser_id, s.category, s.shop_id, p.department, p.name_cn from (
            select psuser_id, category, shop_id from ncrm_subscribe
            where psuser_id is not null and create_time>='%s' and create_time<='%s' and biz_type !=6
            ) s join ncrm_psuser p on s.psuser_id=p.id
        """ % (start_date, end_date)
        query_result2 = execute_query_sql_return_tuple(sql2)
        for psuser_id, cat, shop_id, dpt, name_cn in query_result2:
            if dpt not in result_dict:
                continue
            dpt_data = result_dict[dpt]['data']
            psuser_data = result_dict[dpt]['psuser_dict'][psuser_id]['data']
            if cat in ['ztc', 'vip']:
                cat = 'ztc_vip'
            if cat in dpt_data:
                dpt_data[cat]['shop_list'].append(shop_id)
                dpt_data['total']['shop_list'].append(shop_id)
                psuser_data[cat]['shop_list'].append(shop_id)
                psuser_data['total']['shop_list'].append(shop_id)

        for dpt_info in result_dict.values():
            for cat_data in dpt_info['data'].values():
                cat_data['shop_list'] = list(set(cat_data['shop_list']))
            for psuser_info in dpt_info['psuser_dict'].values():
                for cat_data in psuser_info['data'].values():
                    cat_data['shop_list'] = list(set(cat_data['shop_list']))

        result = [result_dict[dpt] for dpt in tj_dpt_list]
        return result

    @classmethod
    def tj_global_xiaofu_pay(cls, start_date, end_date):
        tj_department_list = GROUPS
        tj_position_list = ['CONSULT', 'SELLER']
        department_dict = dict(PSUser.DEPARTMENT_CHOICES)
        psuser_dict = {}

        extend_condition = " and approval_status > -1 "
        qs_string_1 = """
            select b.id, b.department, b.position, b.name_cn, a.sum_pay from
            (select psuser_id, sum(pay) as sum_pay from ncrm_subscribe
                where psuser_id is not null %s and create_time>='%s' and create_time<='%s' and biz_type !=6 group by psuser_id
            ) a join (select id, position, department, name_cn from ncrm_psuser where department in %s and position in %s) b
            on a.psuser_id = b.id order by b.department
        """ % (extend_condition, start_date, end_date, tuple(tj_department_list), tuple(tj_position_list))
        query_tuple_1 = execute_query_sql_return_tuple(qs_string_1)
        for psuser_id, department_id, position, name_cn, pay in query_tuple_1:
            psuser_dict[psuser_id] = {
                'psuser_name': name_cn,
                'total_pay': int(pay),
                'department_id': department_id,
                'position': position,
                'kcjl_paycount': 0,
                'qn_paycount': 0,
            }

        qs_string_2 = """
            select b.id, b.department, b.position, b.name_cn, a.article_code, a.sub_count from
            (select psuser_id, article_code, count(*) as sub_count from ncrm_subscribe
              where psuser_id is not null %s and create_time>='%s' and create_time<='%s' and article_code in ('ts-25811', 'FW_GOODS-1921400')
              group by psuser_id, article_code
            ) a join (select id, position, department, name_cn from ncrm_psuser where department in %s and position in %s) b
            on a.psuser_id = b.id
        """ % (extend_condition, start_date, end_date, tuple(tj_department_list), tuple(tj_position_list))
        query_tuple_2 = execute_query_sql_return_tuple(qs_string_2)
        for psuser_id, department_id, position, name_cn, article_code, count in query_tuple_2:
            if psuser_id not in psuser_dict:
                psuser_dict[psuser_id] = {
                    'psuser_name': name_cn,
                    'total_pay': 0,
                    'department_id': department_id,
                    'position': position,
                    'kcjl_paycount': 0,
                    'qn_paycount': 0,
                }
            if article_code == 'ts-25811':
                psuser_dict[psuser_id]['kcjl_paycount'] += int(count)
            else:
                psuser_dict[psuser_id]['qn_paycount'] += int(count)

        result_dict = {}
        for dpt in tj_department_list:
            result_dict[dpt] = {
                'department': department_dict.get(dpt, dpt),
                'department_id': dpt,
                'kcjl_paycount': 0,
                'qn_paycount': 0,
                'total_pay': 0,
                'user_list': []
            }
        psuser_list = sorted(psuser_dict.values(), key = lambda k: k['total_pay'])
        for user_pay_dict in psuser_list:
            result_dict[user_pay_dict['department_id']]['user_list'].append(user_pay_dict)
            for k in ['kcjl_paycount', 'qn_paycount', 'total_pay']:
                result_dict[user_pay_dict['department_id']][k] += user_pay_dict[k]

        return sorted(result_dict.values(), key = lambda k: k['department_id'])


class ContractFile(models.Model):
    create_time = models.DateTimeField(verbose_name = '创建时间', default = datetime.datetime.now)
    modify_time = models.DateTimeField(verbose_name = '修改时间', default = datetime.datetime.now)
    file_data = models.BinaryField(verbose_name = "文件内容")
    file_name = models.CharField(verbose_name = "文件名称", max_length = 100)
    subscribe_id = models.IntegerField(verbose_name = '订单ID', null = False)


class HumanRemindEmail(models.Model):
    '''人事提醒邮件model'''
    HUMAN_REMIND_TYPE = [('1', '生日提醒'), ('2', '试用期考核时间提醒'), ('3', '合同到期提醒')]
    HUMAN_REMIND_NODE = [('10', '提前10天提醒'), ('5', '提前5天提醒'), ('1', '提前1天提醒')]

    employee_id = models.IntegerField(verbose_name = '相关员工', null = True)
    email_time = models.DateTimeField(verbose_name = '邮件发送时间', default = datetime.datetime.now)
    remind_type = models.TextField(verbose_name = "提醒类型", choices = HUMAN_REMIND_TYPE)
    remind_node = models.TextField(verbose_name = "提醒节点", choices = HUMAN_REMIND_NODE)


class TreeTemplateContant(object):
    GENERAL_TEMPLATE = "GENERAL"
    CUSTOM_TEMPLATE = 'CUSTOM'
    CHOICES = ((GENERAL_TEMPLATE, "通用分类树"), (CUSTOM_TEMPLATE, "自定义分类树")) # 该部分可能需要根据需求，来决定是否是采用二级分类，还是按照部门分类

class TreeTemplate(models.Model):
    name = models.CharField(verbose_name = "树名称", max_length = 50)
    desc = models.CharField(verbose_name = "描述", max_length = 300)
    tree_json = models.TextField(verbose_name = "树json形式")
    tree_type = models.CharField(verbose_name = "树类型", max_length = 20, choices = TreeTemplateContant.CHOICES)
    creater = models.ForeignKey(PSUser, null = True, verbose_name = "创建人")
    create_time = models.DateTimeField(verbose_name = "创建时间", auto_now_add = True)
    modify_time = models.DateTimeField(verbose_name = "修改时间", auto_now = True)

    @classmethod
    def get_tree_byid(cls, tree_id):
        try:
            return cls.objects.get(id = tree_id)
        except Exception, e:
            print 'TreeTemplate.get_tree_byid error, tree_id=%s, e=%s' % (tree_id, e)
            return None

    @classmethod
    def query_trees_byuser(cls, user):
        return cls.objects.filter(Q(creater = user) | Q(tree_type = TreeTemplateContant.GENERAL_TEMPLATE)).order_by("-tree_type")

    @classmethod
    def create_tree(cls, name, desc, tree_json, tree_type, creater):
        try:
            return cls.objects.create(name = name, desc = desc, tree_json = tree_json, \
                                       tree_type = tree_type, creater = creater)
        except:
            print 'create tree error, name={name}, desc={desc} , tree_json= {tree_json} , tree_type={tree_type}'\
                .format(name = name, desc = desc, tree_json = tree_json, tree_type = tree_type)
            return None

    @classmethod
    def update_tree(cls, tree_id, name, desc, tree_json, tree_type):
        """一旦创建，就不应该出现更改人员问题"""
        tree_template = cls.get_tree_byid(tree_id)
        if tree_template:
            tree_template.name = name
            tree_template.desc = desc
            tree_template.tree_json = tree_json
            tree_template.tree_type = tree_type
            tree_template.save()
            return tree_template
        return None

    @classmethod
    def delete_tree(cls, tree_id):
        cls.objects.filter(id = tree_id).exclude(tree_type = TreeTemplateContant.GENERAL_TEMPLATE).delete()

class StaffPerformance(models.Model):
    psuser_id = models.IntegerField(verbose_name = "员工ID")
    identify = models.CharField(verbose_name = "指标", max_length = 50)
    data_json = models.TextField(verbose_name = "统计数据")
    result_date = models.DateField(verbose_name = "统计日期")
    create_time = models.DateTimeField(verbose_name = "创建时间", auto_now_add = True)
    modify_time = models.DateTimeField(verbose_name = "修改时间", auto_now = True)

    class Meta:
        unique_together = ['psuser_id', 'identify', 'result_date']

    @classmethod
    def query_staff_performance(cls, psuser_id_list, indicator_names, start_date, end_date = None):
        limit_date = datetime.date.today()
        end_date = limit_date if end_date is None or end_date > limit_date else end_date

        sp_qs = cls.objects.filter(psuser_id__in = psuser_id_list)\
                        .filter(result_date__gte = start_date, result_date__lte = end_date)\
                            .filter(identify__in = indicator_names)\
                                .order_by("result_date")
        return sp_qs


class XFGroupPerformance(models.Model):
    xfgroup_id = models.IntegerField(verbose_name = "员工ID")
    identify = models.CharField(verbose_name = "指标", max_length = 50)
    data_json = models.TextField(verbose_name = "统计数据")
    result_date = models.DateField(verbose_name = "统计日期")
    create_time = models.DateTimeField(verbose_name = "创建时间", auto_now_add = True)
    modify_time = models.DateTimeField(verbose_name = "修改时间", auto_now = True)

    class Meta:
        unique_together = ['xfgroup_id', 'identify', 'result_date']

    @classmethod
    def query_staff_performance(cls, xfgroup_id_list, indicator_names, start_date, end_date = None):
        limit_date = datetime.date.today()
        end_date = limit_date if end_date is None or end_date > limit_date else end_date

        sp_qs = cls.objects.filter(xfgroup_id__in = xfgroup_id_list) \
            .filter(result_date__gte = start_date, result_date__lte = end_date) \
            .filter(identify__in = indicator_names) \
            .order_by("result_date")
        return sp_qs


class XFGroup(models.Model):
    '''销服组模型, 即将被弃用'''
    consult = models.OneToOneField(PSUser, verbose_name = '顾问', related_name = 'xfg_consult', primary_key = True)
    seller = models.ForeignKey(PSUser, verbose_name = '销售', related_name = 'xfg_seller')


class ActivityCode(models.Model):
    """员工的活动代码表"""
    activity_code = models.CharField(verbose_name="活动代码", max_length=50, primary_key = True)
    name_cn = models.CharField(verbose_name='所属人', max_length=30, blank=True, null=True, default='')
    creater = models.ForeignKey(PSUser, null=True, verbose_name="创建人")
    create_time = models.DateTimeField(verbose_name="创建时间", default=datetime.datetime.now)


# Mongodb模型的引用，请勿随意改动位置，可能会引起mysql与mongodb模型类型引用异常。
from mongoengine import Document, StringField, IntField, DictField, DateTimeField, ObjectIdField, ListField, BooleanField, FloatField

class ShortMessageRecord(Document):
    """短信记录"""
    sender = StringField(verbose_name = "发信人", required = True) # 直接记录姓名
    title = StringField(verbose_name = "短信标题", required = True)
    content = StringField(verbose_name = "短信内容", required = True)
    send_count = IntField(verbose_name = "发送成功数量", required = True)
    condition = DictField(verbose_name = "过滤条件", default = {})
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now) # 也是短信发送时间

    meta = {'db_alias': 'crm-db', 'collection':'short_message'}

sm_coll = ShortMessageRecord._get_collection()


class ShortMessageReceiver(Document):
    """短信接收人"""
    sm_id = ObjectIdField(verbose_name = "短信记录ID", required = True)
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    phone = StringField(verbose_name = "联系电话", required = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now) # 也是短信发送时间

    meta = {'collection':'short_message_receiver', "shard_key":('shop_id',), }

smr_coll = ShortMessageReceiver._get_collection()

#===============================================================================
# 事件模型定义
#===============================================================================
EVENT_TYPE_CHOICES = (('contact', '联系事件'), ('operate', '操作事件'), ('comment', '评论事件'), ('reintro', '转介绍事件'), ('unsubscribe', '退款事件'), ('pause', '暂停事件'))

class BaseEvent(Document):
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    psuser_id = IntField(verbose_name = "录入人ID", required = True)
    note = StringField(verbose_name = "备注")
    type = StringField(verbose_name = "事件类型", default = "contact", choices = EVENT_TYPE_CHOICES)
    xf_flag = IntField(verbose_name = "岗位类型", choices = Subscribe.XF_FLAG_CHOICES)
    meta = {'db_alias': 'crm-db', 'abstract': True, 'collection':'ncrm_events', 'indexes':['shop_id', 'create_time', 'psuser_id', 'type']}

    @property
    def _qs(self):
        return super(BaseEvent, self)._qs.filter(type == self.type)

class Contact(BaseEvent):
    CONTACT_TYPE_CHOICES = (('qq', 'QQ'), ('phone', '电话'), ('ww', '旺旺'), ('weixin', '微信'), ('others', '其他'))
    contact_type = StringField(verbose_name = "联系方式", max_length = 30, choices = CONTACT_TYPE_CHOICES)
    visible = IntField(verbose_name = "默认可见", choices = EVENT_MARK_CHOICES, default = 1)

event_coll = Contact._get_collection()

class Operate(BaseEvent):
    oper_type = StringField(verbose_name = "操作对象", max_length = 30, choices = OPER_TYPE_CHOICES) # ztc, zz
    visible = models.IntegerField(verbose_name = "默认可见", choices = EVENT_MARK_CHOICES, default = 1)

class Comment(BaseEvent):
    COMMENT_TYPE_CHOICES = ((110, '日常好评'), (120, '踩好评'), (200, '差评'), (301, '5分无评语'), (302, '5分评语未去'), (303, '去评语评分未改'), (304, '未改全5分'), (305, '全5分好评'))
    article_code = models.CharField(verbose_name = "订购项码", max_length = 50, choices = ARTICLE_CODE_CHOICES)
    current_version = models.CharField(verbose_name = "当前版本", max_length = 20, choices = CATEGORY_CHOICES)
    duty_person_id = IntField(verbose_name = "责任人ID")
    comment_type = models.IntegerField(verbose_name = "评价类型", choices = COMMENT_TYPE_CHOICES)
    top_comment_times = models.IntegerField(verbose_name = "踩评名次")
    modify_comment_time = models.DateTimeField(verbose_name = "改评价时间")
    xfgroup_id = IntField(verbose_name = "录入人销服组ID")
    duty_xfgroup_id = IntField(verbose_name = "责任人销服组ID")

class ReIntro(BaseEvent):
    receiver_id = IntField(verbose_name = "接收人ID", required = True)
    reintro_type = StringField(verbose_name = "转介绍类型", choices = OPER_TYPE_CHOICES) # 转软件、转人工托管、转人机

class Unsubscribe(BaseEvent):
    # REFUND_TYPE_CHOICES = (
    #                        (1, '软件退款'), # 所有软件的不友好退款，差评/差评威胁/官方投诉/效果问题/态度问题/订错软件
    #                        (2, 'TP退款'), # 所有TP的不友好退款，官方投诉/效果问题/态度问题等
    #                        (3, '友情退款'), # 水军、友好客户等的友好退款
    #                        (4, '转店铺'), # 软件或TP客户转店铺继续服务的退款
    #                        (5, '积分兑换'),
    #                        (0, '其他') # 装修设计/代运营/钻展等退款
    #                        )
    REFUND_REASON_CHOICES = (
                           (1, '差评投诉'),
                           (2, '效果问题'),
                           (3, '软件缺陷'),
                           (4, '活动无理由'),
                           (5, '友情赠送'), # 补时间、转店铺、SD赠送、水军退款
                           (6, '积分兑换'),

                           # 100 差评投诉
                           (101, '差评'),
                           (102, '投诉淘宝/工商'),
                           # 200 效果不好
                           (201, '效果不好-操作数据差'),
                           (202, '效果不好-前期夸大效果'),
                           # 300 销售承诺
                           (301, '销售承诺-具体的数据承诺未达到'),
                           (302, '销售承诺-全额退款'),
                           # 400 沟通问题
                           (401, '沟通问题-操作人'),
                           (402, '沟通问题-服务人'),
                           # 900 其他
                           (901, '操作失误'),
                           (902, '客户自身原因'),
                           (903, '无合同'),
                           (904, '无理由'),


                           )
    PAY_TYPE_CHOICES = ((1, '淘宝后台退款'), (2, '支付宝退款'), (3, '对公银行退款'), (4, '对私银行退款'), (5, '现金退款'))
    REFUND_STATUS_CHOICES = ((1, '申请中'), (2, '已退款'))
    event_id = IntField(verbose_name = "订单事件ID") # Subscribe 的主键
    refund = IntField(verbose_name = "退款金额", default = 0)
    refund_date = DateTimeField(verbose_name = "经办日期")
    # refund_type = IntField(verbose_name = "退款类型", choices = REFUND_TYPE_CHOICES)
    refund_reason = IntField(verbose_name = "退款原因", choices = REFUND_REASON_CHOICES)
    refund_style = IntField(verbose_name = "退款方式", choices = PAY_TYPE_CHOICES)
    refund_info = StringField(verbose_name = "退款信息(支付宝账号/银行账号)__户主姓名")
    frozen_kcjl = IntField(verbose_name = "禁止使用软件", choices = ((0, '可以使用'), (1, '禁止使用')))
    saler_apportion = IntField(verbose_name = "签单人分摊") # 单位：分
    server_apportion = IntField(verbose_name = "服务人分摊") # 单位：分
    saler_dpt_apportion = IntField(verbose_name = "签单部门分摊") # 单位：分
    server_dpt_apportion = IntField(verbose_name = "服务部门分摊") # 单位：分
    other_apportion = IntField(verbose_name = "公司分摊") # 单位：分
    pm_apportion = IntField(verbose_name = "派美分摊") # 单位：分
    saler_id = IntField(verbose_name = "签单人ID")
    server_id = IntField(verbose_name = "服务人ID")
    duty_dpt = StringField(verbose_name = "责任部门")
    reimburse_dpt = StringField(verbose_name = "经办部门")
    nick = StringField(verbose_name = "店铺名")
    category = StringField(verbose_name = "业务类型", choices = CATEGORY_CHOICES)
    status = IntField(verbose_name = "退款状态", choices = REFUND_STATUS_CHOICES, default = 1)
    cashier_id = IntField(verbose_name = "经办人ID")
    img_list = ListField(verbose_name = "截图列表", field = StringField)
    xfgroup_id = IntField(verbose_name = "录入人销服组ID")
    saler_xfgroup_id = IntField(verbose_name = "签单人销服组ID")
    server_xfgroup_id = IntField(verbose_name = "服务人销服组ID")

    # @classmethod
    # def get_global_refund(cls, category_list, start_date, end_date):
    #     result_dict = {}
    #     tj_refund_reason_list = range(1, 7)
    #     tj_department_list = OPERATION_GROUPS
    #     department_dict = dict(PSUser.DEPARTMENT_CHOICES)
    #     init_dict = {
    #         'total_count': 0,
    #         'total_refund': 0,
    #         'refund_reason_dict': {'rr_%s' % r: {'refund': 0, 'count': 0} for r in tj_refund_reason_list}
    #         }
    #     for dpt in tj_department_list:
    #         result_dict[dpt] = {'id': dpt, 'department': department_dict[dpt], 'user_list': []}
    #         result_dict[dpt].update(copy.deepcopy(init_dict))
    #
    #     pipeline = [
    #         {'$match': {'type': 'unsubscribe', 'refund_reason': {'$in': tj_refund_reason_list}, 'duty_dpt': {'$in': tj_department_list}}},
    #         {'$match': {'status': 2, 'create_time': {'$gte': start_date, '$lte': end_date}, }},
    #         {'$match': {'category':{'$in': category_list}}},
    #         {'$group': {
    #             '_id': {'duty_dpt': '$duty_dpt', 'psuser_id': '$server_id', 'refund_reason': '$refund_reason'},
    #             'refund': {'$sum': '$refund'},
    #             'count': {'$sum': 1}
    #             }
    #          },
    #         {'$sort': {'refund':-1, '_id.duty_dpt': 1, }},
    #         {'$group': {
    #             '_id': '$_id.duty_dpt',
    #             'user_list': {'$push': {'psuser_id': '$_id.psuser_id', 'refund_reason': '$_id.refund_reason', 'refund': '$refund', 'count': '$count'}}
    #             }
    #          }
    #         ]
    #     result = event_coll.aggregate(pipeline)['result']
    #     psusers = PSUser.objects.all().only('id', 'name_cn', 'position')
    #     psuser_dict = {obj.id: obj for obj in psusers}
    #     for i_dict in result:
    #         dpt_refund_dict = result_dict.get(i_dict['_id'], {})
    #         if not dpt_refund_dict:
    #             continue
    #         user_dict = {}
    #         for j_dict in i_dict['user_list']:
    #             psuser_id = j_dict.get('psuser_id', -1)
    #             refund_reason_str = 'rr_%s' % j_dict['refund_reason']
    #             sub_dict = user_dict.get(psuser_id, {})
    #             if not sub_dict:
    #                 sub_dict = copy.deepcopy(init_dict)
    #                 sub_dict.update({
    #                     'psuser_id': psuser_id,
    #                     'psuser_name': psuser_id in psuser_dict and psuser_dict[psuser_id].name_cn or '其他',
    #                     'position':  psuser_id in psuser_dict and psuser_dict[psuser_id].get_position_display() or '其他',
    #                     })
    #             sub_dict['refund_reason_dict'].update({refund_reason_str: {'refund': j_dict['refund'], 'count': j_dict['count']}})
    #             sub_dict['total_count'] += j_dict['count']
    #             sub_dict['total_refund'] += j_dict['refund']
    #             user_dict.update({psuser_id: sub_dict})
    #             dpt_refund_dict['refund_reason_dict'][refund_reason_str]['refund'] += j_dict['refund']
    #             dpt_refund_dict['refund_reason_dict'][refund_reason_str]['count'] += j_dict['count']
    #             dpt_refund_dict['total_count'] += j_dict['count']
    #             dpt_refund_dict['total_refund'] += j_dict['refund']
    #         dpt_refund_dict['user_list'] = sorted(user_dict.values(), key = lambda k: k['total_refund'], reverse = True)
    #
    #     return sorted(result_dict.values(), key = lambda k: k['id'])

    @classmethod
    def get_global_refund(cls, start_date, end_date, category_list, refund_style_list):
        psusers = PSUser.objects.all().only('id', 'name_cn', 'position')
        psuser_dict = {obj.id: obj for obj in psusers}
        department_dict = dict(PSUser.DEPARTMENT_CHOICES)
        tj_dpt_list = OPERATION_GROUPS + GROUPS

        result_dict = {}
        for duty_dpt in tj_dpt_list:
            result_dict[duty_dpt] = {
                'id': duty_dpt,
                'department': department_dict.get(duty_dpt, duty_dpt),
                'user_list': {},
                'refund_reason_dict': {'rr_%s' % i: {'count': 0, 'refund': 0} for i in range(1, 7)},
                'total_count': 0,
                'total_refund': 0
            }

        unsub_set = event_coll.find({
            'type': 'unsubscribe',
            'status': 2,
            'create_time': {'$gte': start_date, '$lte': end_date},
            'category':{'$in': category_list},
            'refund_style':{'$in': refund_style_list}
        })
        for unsub in unsub_set:
            dpt_dict = result_dict.get(unsub['duty_dpt'])
            if not dpt_dict: continue
            dpt_dict['total_count'] += 1
            dpt_dict['total_refund'] += unsub['refund']
            refund_reason = unsub['refund_reason']
            dpt_reason_dict = dpt_dict['refund_reason_dict'].setdefault('rr_%s' % refund_reason, {'count': 0, 'refund': 0})
            dpt_reason_dict['count'] += 1
            dpt_reason_dict['refund'] += unsub['refund']
            duty_user = psuser_dict.get(unsub['saler_id'], None)
            if not(duty_user and duty_user.department in tj_dpt_list):
                duty_user = psuser_dict.get(unsub['server_id'], None)
            if duty_user:
                dpt_user_dict = dpt_dict['user_list'].setdefault(duty_user.id, {
                    'psuser_id': duty_user.id,
                    'psuser_name': duty_user.name_cn,
                    'position': duty_user.get_position_display(),
                    'refund_reason_dict': {'rr_%s' % i: {'count': 0, 'refund': 0} for i in range(1, 7)},
                    'total_count': 0,
                    'total_refund': 0
                })
                dpt_user_dict['total_count'] += 1
                dpt_user_dict['total_refund'] += unsub['refund']
                user_reason_dict = dpt_user_dict['refund_reason_dict'].setdefault('rr_%s' % refund_reason, {'count': 0, 'refund': 0})
                user_reason_dict['count'] += 1
                user_reason_dict['refund'] += unsub['refund']

        for duty_dpt, dpt_dict in result_dict.items():
            dpt_dict['user_list'] = dpt_dict['user_list'].values()
            dpt_dict['user_list'].sort(lambda x, y:cmp(y['total_refund'], x['total_refund']))

        # return sorted(result_dict.values(), key = lambda x: x['id'])
        return [result_dict[dpt] for dpt in tj_dpt_list]

class Pause(BaseEvent):
    event_id = IntField(verbose_name = "订单事件ID") # Subscribe 的主键
    proceeder_id = IntField(verbose_name = "开启人ID")
    proceed_date = DateTimeField(verbose_name = "开启日期")

class WorkReminder(Document):
    '''工作提醒'''
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    sender_id = IntField(verbose_name = "发送人ID", required = True) # 0表示系统提醒
    receiver_id = IntField(verbose_name = "接收人ID", required = True)
    department = StringField(verbose_name = "接收人部门", choices = PSUser.DEPARTMENT_CHOICES)
    position = StringField(verbose_name = "接收人职位", choices = PSUser.POSITION_CHOICES)
    handle_status = IntField(verbose_name = "处理状态", choices = [(-1, '未处理'), (1, '已处理')])
    content = StringField(verbose_name = "提醒内容")

    meta = {'db_alias': 'crm-db', 'collection':'ncrm_work_reminder', 'indexes':['create_time', 'sender_id', 'receiver_id', 'department', 'position', 'handle_status']}

reminder_coll = WorkReminder._get_collection()

class PrivateMessage(Document):
    ''' 私信 '''
    APP_ID_CHOICES = ((12612063, '开车精灵'), (21729299, '开车精灵Q牛')) # APP类型
    LEVEL_CHOICES = (('error', '错误(error)：系统出现故障时使用此消息通知用户'), ('success', '成功(success)：系统成功完成了某项任务'),
                     ('info', '信息(info)：需要用户关注的某些信息'), ('alert', '警告(alert)：需要用户避免危险操作的提示'))

    shop_id = IntField(verbose_name = "消息接收者ID", required = True)
    app_id = IntField(verbose_name = "APP类型", choices = APP_ID_CHOICES, default = 12612063, required = True)
    title = StringField(verbose_name = "标题", max_length = 500, default = None)
    content = StringField(verbose_name = '消息内容', default = None)
    level = StringField(verbose_name = "消息级别", choices = LEVEL_CHOICES, max_length = 10, default = 'info', required = True)
    start_time = DateTimeField(verbose_name = "有效期起", default = datetime.datetime.now)
    end_time = DateTimeField(verbose_name = "有效期止", default = datetime.datetime.now)
    last_modified = DateTimeField(verbose_name = "修改时间", default = datetime.datetime.now)
    is_show = BooleanField(verbose_name = "是否显示", default = True)
    is_read = BooleanField(verbose_name = "是否已读", default = False)

    meta = {'collection':'ncrm_message', 'indexes':[], 'shard_key':('shop_id',), }

    @staticmethod
    def need_2handle(shop_id):
        '''检查是否已有过目标对象的信息以及是否被处理过'''
        try:
            is_read = PrivateMessage.objects.filter(shop_id = shop_id, level = 'alert').order_by('-last_modified')[0].is_read
            return not is_read
        except:
            return False

    @staticmethod
    def get_unread_count(shop_id):
        '''获取未读消息数'''
        now = datetime.datetime.now()
        messages = PrivateMessage.objects.filter(shop_id = shop_id, is_show = True, is_read = False, start_time__lt = now, end_time__gt = now)
        if messages:
            return len(messages)
        else:
            return 0

    @staticmethod
    def read_message(shop_id, msg_id):
        '''用户阅读一条消息 ，将其置为已读'''
        result = True
        try:
            message = PrivateMessage.objects.get(id = msg_id, shop_id = shop_id, is_show = True)
            if message and not message.is_read:
                message.is_read = True
                message.save();
        except Exception, ex:
            log.error('read message error, shop_id = %s, e = %s' % (shop_id, ex))
            result = False
        return result

    @staticmethod
    def get_message_list(shop_id):
        '''获取某用户的消息列表'''
        result = []
        try:
            now = datetime.datetime.now()
            result = PrivateMessage.objects.filter(shop_id = shop_id, is_show = True, start_time__lt = now, end_time__gt = now).order_by('-last_modified')
        except Exception, ex:
            log.error('read message list error, shop_id = %s, e = %s' % (shop_id, ex))
            result = []
        return result

    @staticmethod
    def send_message(shop_id, title, content, app_id = 12612063, level = 'info', start_time = datetime.datetime.now, end_time = datetime.datetime.now):
        '''发送一条消息'''
        try:
            message = PrivateMessage(shop_id = shop_id,
                                     app_id = app_id,
                                     title = title,
                                     content = content,
                                     level = level,
                                     start_time = start_time,
                                     end_time = end_time,
                                     last_modified = datetime.datetime.now(),
                                     is_show = True,
                                     is_read = False)
            PrivateMessage.objects.insert(message)
            return True
        except Exception, ex:
            log.error('send message error, shop_id = %s, e = %s' % (shop_id, ex))
            return False

    @staticmethod
    def batch_send_message(title, content, shop_id_list = [], app_id = 12612063, level = 'info', start_time = datetime.datetime.now, end_time = datetime.datetime.now):
        '''批量发送多条消息'''
        try:
            if shop_id_list:
                message_list = []
                for shop_id in shop_id_list:
                    message = PrivateMessage(shop_id = shop_id,
                                             app_id = app_id,
                                             title = title,
                                             content = content,
                                             level = level,
                                             start_time = start_time,
                                             end_time = end_time,
                                             last_modified = datetime.datetime.now(),
                                             is_show = True,
                                             is_read = False)
                    message_list.append(message)
                PrivateMessage.objects.insert(message_list)
            return True
        except Exception, ex:
            log.error('batch send message error, shop_id = %s, e = %s' % (shop_id, ex))
            return False

private_msg_coll = PrivateMessage._get_collection()


class PlanTree(Document):
    """计划树"""
    GOAL_KEY_CHOICES = [
        ('renew_order_pay', '进账金额'),
        ('good_comment_count', '好评数'),
        ('unknown_order_count', 'SD单量'),
        # ('is_potential', '意向客户'),
    ]
    tree_id = ObjectIdField(verbose_name = "计划树ID", primary_key = True)
    name = StringField(verbose_name = "计划树名称", required = True)
    desc = StringField(verbose_name = "描述")
    goal = DictField(verbose_name = '预期目标')
    child_list = ListField(verbose_name = "子节点", field = DictField)
    cond_list = ListField(verbose_name = "条件列表", field = DictField)
    psuser_id = IntField(verbose_name = "创建人", required = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    start_time = DateTimeField(verbose_name = "开始时间")
    end_time = DateTimeField(verbose_name = "结束时间")
    status = IntField(verbose_name = "发布状态", choices = [(0, '未发布'), (1, '已发布')], default = 0)
    path = StringField(verbose_name = "节点路径", required = True)
    shop_count = IntField(verbose_name = "绑定店铺数")
    shop_id_list = ListField(verbose_name = "绑定店铺id列表", field = IntField)

    meta = {'db_alias': 'crm-db', 'collection':'ncrm_plan_tree'}

    @classmethod
    def get_tree_byid(cls, tree_id, remove_id=False):
        try:
            tree_data = pt_coll.find({'_id':ObjectId(tree_id)})[0]
            if remove_id:
                tree_data.pop('_id')
            return tree_data
        except Exception, e:
            print 'PlanTree.get_tree_byid error, tree_id=%s, e=%s' % (tree_id, e)
            return None

    @classmethod
    def get_tree_template(cls, tree_data):
        try:
            tree_data['id'] = tree_data.pop('_id')
            tree_data['tree_json'] = json.dumps(tree_data)
            return DictWrapper(tree_data)
        except Exception, e:
            print 'PlanTree.get_tree_template error, e=%s' % e
            return None

    @classmethod
    def query_trees_byuser(cls, user):
        result = {}
        doc_list = list(pt_coll.find({'psuser_id':user.id}, {'start_time':True, 'end_time':True, 'status':True}).sort('start_time', -1))
        td = datetime.date.today()
        for doc in doc_list:
            temp = result.setdefault(doc['status'], [])
            if len(temp) < 4:
                doc['id'] = doc['_id']
                if doc['start_time'].date() <= td:
                    doc['is_valid'] = True
                    if doc['end_time'].date() >= td:
                        doc['is_serving'] = True
                    else:
                        doc['is_serving'] = False
                else:
                    doc['is_valid'] = False
                temp.append(doc)
        return result

    @classmethod
    def create_tree(cls, tree_data, psuser_id):
        tree_data.update({
            'psuser_id':psuser_id,
            'create_time':datetime.datetime.now(),
            'status':0,
        })
        return pt_coll.insert(tree_data)

    @classmethod
    def update_tree(cls, tree_id, tree_data):
        pt_coll.update({'_id': ObjectId(tree_id)}, {'$set': tree_data})

    @classmethod
    def delete_tree(cls, tree_id):
        pt_coll.remove(ObjectId(tree_id))

pt_coll = PlanTree._get_collection()


class PlanTreeRecord(Document):
    """计划树目标记录"""
    tree_id = ObjectIdField(verbose_name = "计划树ID", required = True)
    path = StringField(verbose_name = "节点路径", required = True)
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    nick = StringField(verbose_name = "店铺名", required = True)
    rec_type = StringField(verbose_name = "记录类型", choices = PlanTree.GOAL_KEY_CHOICES, required = True)
    rec_value = IntField(verbose_name = "记录值", required = True)
    psuser_id = IntField(verbose_name = "创建人", required = True)
    psuser_cn = IntField(verbose_name = "创建人姓名", required = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)

    meta = {'db_alias': 'crm-db', 'collection':'ncrm_plan_tree_record'}

ptr_coll = PlanTreeRecord._get_collection()


class AllocationRecord(Document):
    """订单分配记录"""
    psuser_id = IntField(verbose_name = "分配人", required = True)
    psuser_cn = IntField(verbose_name = "分配人姓名", required = True)
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    subscribe_id = IntField(verbose_name = "订单ID", required = True)
    sub_time = DateTimeField(verbose_name = "订单订购时间", required = True)
    category_cn = StringField(verbose_name = "业务类型", required = True)
    pay = IntField(verbose_name = "成交金额", required = True)
    create_time = DateTimeField(verbose_name = "分配时间", default = datetime.datetime.now)
    org_id_list = StringField(verbose_name = "原人员ID列表")
    org_cn_list = StringField(verbose_name = "原人员姓名列表")
    new_id_list = StringField(verbose_name = "新人员ID列表")
    new_cn_list = StringField(verbose_name = "新人员姓名列表")

    meta = {'db_alias': 'crm-db', 'collection':'ncrm_allocation_record'}

    @staticmethod
    def get_category_cn_by_category(category):
        if category:
            for i in range(len(CATEGORY_CHOICES)):
                if CATEGORY_CHOICES[i][0] == category:
                    return CATEGORY_CHOICES[i][1]
ar_coll = AllocationRecord._get_collection()

