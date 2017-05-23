 # coding=utf-8

import datetime, re, base64

from django.shortcuts import render_to_response
from django.template.context import RequestContext
from apps.common.constant import Const
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple, execute_query_sql
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_datetime import date_2datetime
from apps.common.cachekey import CacheKey
from apps.ncrm.utils import pagination_tool
from apps.ncrm.models import ClientGroup, Customer, PSUser, reminder_coll, XiaoFuGroup, Unsubscribe, CATEGORY_CHOICES
from apps.ncrm.sql_generator import sql_generator, get_valid_args_dict, is_continue
from apps.ncrm.views import get_psuser
from apps.web.models import main_ad_coll, Feedback, pa_coll
from apps.ncrm.utils_export_excel import export_workbench_data
from apps.ncrm.classify_tree import read_tree_branch
from apps.ncrm.guidance3 import get_ps_shopid_list

class BaseWorkBench(object):

    def __init__(self, request, page_no, template, work_type, is_show_my_customers, search_type_default, subscribe_category):
        self.shop_ids = []
        self.request = request
        self.page_no = page_no
        self.template = template
        self.work_type = work_type
        self.is_show_my_customers = is_show_my_customers
        self.client_ids = map(int, self.request.GET.getlist('client_ids'))
        self.search_type = self.request.GET.get('search_type') or search_type_default
        self.myself = get_psuser(request)
        self.psuser_id = self.request.GET.get('psuser_id') or self.myself.id
        self.subscribe_category = subscribe_category
        self.subscribe_category_list = Const.SUBSCRIBE_CATEGORY_SET.get(subscribe_category, [subscribe_category])

    def group_filter(self):
        """对客户群进行过滤"""
        self.all_client_group = ClientGroup.objects.filter(create_user = self.psuser_id).order_by('-group_type')
        if self.client_ids:
            self.all_client_group.filter(id__in = self.client_ids).update(checked = 1)
            self.all_client_group.exclude(id__in = self.client_ids).update(checked = 0)
            self.check_client_ids = self.client_ids
        else:
#             self.check_client_ids = [cg.id for cg in self.all_client_group.filter(checked = 1)]
            self.all_client_group.update(checked = 0)
            self.check_client_ids = []

        return self.check_client_ids, self.all_client_group

    def get_shop_ids_byclientgroup(self):
        """获取所有操作客户"""
        shop_ids = ''
        if self.client_ids:
            client_groups = self.all_client_group.filter(id__in = self.client_ids, checked = 1)
        else:
            client_groups = self.all_client_group.filter(checked = 1)

        for c in client_groups:
            shop_ids += c.id_list

        if not shop_ids:
            id_list = []
        else:
            id_list = eval(shop_ids.replace('][', ','))

        return id_list

    def query_global(self):
        return {}

    def query_client_group(self):
        return {"ncr__shop_id__in":self.get_shop_ids_byclientgroup()}

    def query_mycustomers(self):
        raise Exception("function name : query_mycustomers need to implement")

    def get_extra_valid_args(self):
        return {}

    def replinsh_other_args(self, sql_args_dict):
        # 该处日后需要重构
        replinsh_dict = {}
        for key in sql_args_dict:
#             if 'nse' in key and "nse__article_code__in"  not in sql_args_dict:
#                 replinsh_dict.update({'nse__article_code__in':self.subscribe_list})
            if 'nse' in key and not ("nse__category__equal" in sql_args_dict or "nse__category__in" in sql_args_dict):
                if len(self.subscribe_category_list) == 1:
                    replinsh_dict.update({'nse__category__equal':self.subscribe_category_list[0]})
                else:
                    replinsh_dict.update({'nse__category__in':self.subscribe_category_list})

        return replinsh_dict

    def do_query(self):
        """查询的实际function，这里是一些基础数据的查询，可以自定义，可以继承"""
        if self.search_type == "query_client_group" and not self.check_client_ids:
            self.shop_ids = []
        else:
            field_mapping = {}
            if self.search_type == "query_global":
                field_mapping = self.query_global()
            elif self.search_type == "query_client_group":
                field_mapping = self.query_client_group()
            elif self.search_type == "query_mycustomers":
                field_mapping = self.query_mycustomers()

            if not is_continue(field_mapping):
                self.shop_ids = []
            else:
                kwargs = field_mapping
                kwargs.update(get_valid_args_dict(self.request.GET))
                kwargs.update(self.get_extra_valid_args())
                kwargs.update(self.replinsh_other_args(kwargs))
                reason, sql = sql_generator(kwargs)
                if reason:
                    raise Exception(reason)
                self.shop_ids = [cust['shop_id'] for cust in execute_query_sql(sql)]

    def get_customers(self, shop_id_list):
        customer_mapping = {cust.shop_id:cust for cust \
                         in Customer.objects.filter(shop_id__in = shop_id_list)}
        customer_list = [customer_mapping[shop_id] for shop_id in shop_id_list]
        return customer_list

    def do_bind(self, customer_list):
        """绑定额外的数据"""
        customer_list = Customer.binder_order_info(customer_list, self.subscribe_category)
        return customer_list

    def bind_client_group_ids(self, customer_list, all_client_group):
        """绑定客户群ids"""
        Customer.bind_client_group_ids(customer_list = customer_list, all_client_group = all_client_group)

    def bind_extra_data(self):
        return {}

    def analysis_server_info(self):
        '''解析登录员工的岗位和业务类型'''
        if self.myself.position in ['CONSULT', 'CONSULTLEADER']:
            self.myself_type = 'consult'
            self.myself_category_list = ('kcjl', 'qn')
        elif self.myself.position in ['RJJH', 'RJJHLEADER']:
            self.myself_type = 'operater'
            self.myself_category_list = ('rjjh',)
        elif self.myself.position in ['TPAE', 'TPLEADER']:
            self.myself_type = 'operater'
            self.myself_category_list = ('vip', 'ztc', 'dyy')
        else:
            self.myself_type = 'saler'
            self.myself_category_list = ()

    def bind_common_groups(self, customer_list):
        """绑定通用客户群"""
        today = datetime.date.today()
        for cus in customer_list:
            cus.balance = self.shop_balance_dict.get(unicode(cus.shop_id), None) # 绑定余额

            common_groups = [] # [('标记', '值', '是否可设置', '群名'), ...]
            settable = False
            if getattr(cus, self.myself_type) == self.myself:
                if not self.myself_category_list:
                    if not cus.latest_end or cus.latest_end <= today:
                        settable = True
                elif cus.latest_category in self.myself_category_list:
                    settable = True

            if cus.latest_end:
                if cus.latest_end > today:
#                     common_groups.append(('is_pausing', 1 if cus.is_pausing else 0, False, '暂停服务'))
#                     common_groups.append(('to_1st_contact', 0 if cus.contact_count or cus.is_pawn else 1, False, '待一访'))
#                     if cus.latest_category in ('kcjl', 'qn'):
#                         common_groups.append(('to_2nd_contact', 1 if cus.contact_count == 1 and not cus.is_pawn else 0, False, '待二访'))
                    if cus.latest_category in ('rjjh', 'vip', 'ztc'):
                        common_groups.append(('unoperated_3days', 1 if not cus.latest_operate or ((today - cus.latest_operate).days >= 3 and not cus.is_pausing) else 0, False, '3天未操作'))
                    if cus.latest_category == 'rjjh':
                        common_groups.append(('unmnt_3days', 1 if cus.rjjh_unmnt and (today - cus.rjjh_unmnt).days <= 3 else 0, False, '取消过托管'))
                        common_groups.append(('rjjh_frozen', 1 if cus.rjjh_frozen else 0, settable, '手操客户'))
            # common_groups.append(('bad_comment', 1 if cus.bad_comment else 0, True, '差评跟踪'))
#             common_groups.append(('unknown_subscribe', 1 if cus.unknown_subscribe else 0, False, '未知订单'))
#             common_groups.append(('is_potential', 1 if cus.is_potential else 0, settable, '意向客户'))
#             common_groups.append(('is_discontent', 1 if cus.is_discontent else 0, settable, '问题客户'))
#             common_groups.append(('advertise_effective', 1 if cus.advertise_effect == 1 else 0, settable, '优质客户'))
#             common_groups.append(('advertise_ineffective', 1 if cus.advertise_effect == 2 else 0, settable, '效果差'))
#             common_groups.append(('is_pawn', 1 if cus.is_pawn else 0, settable, '水军'))
#             common_groups.append(('contact_fail', 1 if cus.contact_fail else 0, settable, '联系不上'))
            cus.common_groups = common_groups

    def handle_customer_info(self, customer_list):
        dept_commander_dict = dict(PSUser.objects.filter(position='COMMANDER', status='转正').values_list('department', 'id'))
        for c in customer_list:
            c.qq_tip = ''
            c.phone_tip = ''
            if self.myself not in [c.saler, c.operater, c.consult]:
                dept = ''
                if c.consult:
                    dept = c.consult.department
                elif c.operater:
                    dept = c.operater.department
                elif c.saler:
                    dept = c.saler.department
                commander_id = dept_commander_dict.get(dept, None)
                if self.myself.id != commander_id:
                    if c.consult:
                        now = datetime.datetime.now()
                        xf_groups = XiaoFuGroup.objects.filter(consult=c.consult, start_time__lte=now, end_time__gt=now)
                        if xf_groups and self.myself == xf_groups[0].seller:
                            continue
                    c.qq_tip = c.qq and base64.b64encode(c.qq)
                    c.phone_tip = c.phone and base64.b64encode(c.phone)
                    c.qq = c.qq and '查看'
                    c.phone = c.phone and '查看'

    def __call__(self):
        """
        1，客户群过滤
        2，具体查询函数
        3，添加过滤器
        3，分页
        4，绑定特殊数据
        """
        self.analysis_server_info()
        client_id_list, all_client_group = self.group_filter()
        self.do_query()
        # 分页选择 50 100 150
        # page_info, shop_id_list = pagination_tool(page = self.page_no, record = self.shop_ids)
        page_count = self.request.GET.get('page_count', '50').strip()
        page_info, shop_id_list = pagination_tool(page=self.page_no, record=self.shop_ids, page_count=int(page_count))
        customer_list = self.get_customers(shop_id_list)
        self.do_bind(customer_list)
        self.bind_client_group_ids(customer_list, all_client_group)
        extra_data = self.bind_extra_data()
        common_groups = CacheAdpter.get(CacheKey.NCRM_COMMON_GROUP_STATISTIC % self.myself.id, 'crm', {})  # 通用客户群统计数
        self.shop_balance_dict = self.request.session.get(CacheKey.NCRM_SHOP_BALANCE % self.myself.id, {})  # 人机账户绑定余额
        if not self.shop_balance_dict and self.myself.position in ['RJJH', 'RJJHLEADER']:
            self.shop_balance_dict = self.myself.get_mycustomers_balance()
            self.request.session[CacheKey.NCRM_SHOP_BALANCE % self.myself.id] = self.shop_balance_dict
        common_groups['no_balance'] = [shop_id for shop_id, balance in self.shop_balance_dict.items() if balance <= 0]
#         common_groups['no_balance'] = [63518068, 123123]
        self.bind_common_groups(customer_list)
        self.handle_customer_info(customer_list)
        data_dict = {
                     'common_groups':common_groups,
                     'client_id_list':client_id_list,
                     'all_client_group': all_client_group,
                     'page_info':page_info,
                     'customer_list': customer_list,
                     'work_type':self.work_type,
                     'extra':extra_data,
                     'myself':self.myself,
                     'can_operate':self.myself.position in ['COMMANDER', 'RJJH', 'RJJHLEADER', 'TPAE', 'TPLEADER', 'DEV', 'DESIGNER', 'OPTAGENT', 'SHOPMANAGER', 'SHOPASSISTANT'],
                     "psuser_id":int(self.psuser_id),
                     'is_show_my_customers':self.is_show_my_customers,
                     'nick_list':self.request.GET.getlist('nick', [])
        }

        # 退款原因
        data_dict['refund_reason_checkbox'] = Unsubscribe.REFUND_REASON_CHOICES
        # 业务类型
        # data_dict['latest_category_choice'] = CATEGORY_CHOICES

        import settings
        redirect_url = "{}/{}/".format(settings.LOGIN_URL, settings.ADMIN_URL)
        data_dict['redirect_url'] = redirect_url
        # 绑定CRM公告、意见反馈、提醒、积分兑换及检查好评
        now = datetime.datetime.now()
        crm_ad = list(main_ad_coll.find({'ad_position':'rightnotice', 'ad_display':1, 'ad_status':2, 'ad_user_type':re.compile(r'.*2.*'), 'ad_start_time':{'$lte':now}, 'ad_end_time':{'$gt':now}}, {'ad_title':True}).sort('ad_put_time', -1))
        for ad in crm_ad:
            ad['id'] = ad['_id']
        data_dict['crm_ad'] = crm_ad
        crm_feedback = Feedback.objects.select_related('shop').filter(consult = self.myself, handle_status = -1).order_by('-create_time')
        data_dict['crm_feedback'] = crm_feedback
        crm_reminder = list(reminder_coll.find({'receiver_id':self.myself.id, 'handle_status':-1}, {'content':True}).sort('create_time', -1))
        for reminder in crm_reminder:
            reminder['id'] = reminder['_id']
        data_dict['crm_reminder'] = crm_reminder
        crm_pa = list(pa_coll.find({'consult_id':self.myself.id, 'consult_flag':0,
                                    '$or':[{'type':'appraise', 'is_freeze':1, 'create_time':{'$gte':now - datetime.timedelta(days = 7), '$lt':date_2datetime(datetime.date.today())}},
                                           {'type':'virtual', 'exchange_status':0},
                                           {'type':'gift', 'logistics_state':0}]
                                    }, {'nick':True, 'type':True}).sort('create_time', -1))
        for pa in crm_pa:
            pa['id'] = pa['_id']
        data_dict['crm_pa'] = crm_pa
        return render_to_response(self.template, data_dict, context_instance = RequestContext(self.request))


class ServerWorkBench(BaseWorkBench):
#     search_type_default = "query_mycustomers"
    search_type_default = "query_global"

    def __init__(self, request, page_no, template, work_type, subscribe_category, is_show_my_customers):
        super(ServerWorkBench, self).__init__(request, page_no, template, work_type, is_show_my_customers, self.search_type_default, subscribe_category)

    def reset_client_group(self):
        all_client_group = ClientGroup.objects.filter(create_user = self.psuser_id)
        all_client_group.update(checked = 0)
        return [], all_client_group

    def get_subscribe_valid_time(self):
        lt_time = datetime.date.today()
        gte_time = lt_time - datetime.timedelta(days = 15)
        return lt_time, gte_time

    def query_server_customers(self):
        today = datetime.date.today()
        return {
            "nse__operater_id__equal":self.psuser_id,
            "nse__category__in":self.subscribe_category_list,
            "nse__start_date__lte":today,
            "nse__end_date__gt":today
         }

    def query_mycustomers(self):
        lt_time, gte_time = self.get_subscribe_valid_time()
        return {
            "nse__operater_id__equal":self.psuser_id,
            "nse__category__in":self.subscribe_category_list,
            "nse__start_date__lte":lt_time,
            "nse__end_date__gte":gte_time,
            'nse__biz_type__nequal':6
         }

    def get_shop_ids_bysql(self, query_dict):
        reason, sql = sql_generator(query_dict)
        if reason:
            raise Exception(reason)
        return  [cust['shop_id'] for cust in execute_query_sql(sql)]

    def get_server_customer_ids(self):
        query_dict = self.query_server_customers()
        return self.get_shop_ids_bysql(query_dict)

    def get_myscustomer_ids(self):
        query_dict = self.query_mycustomers()
        return self.get_shop_ids_bysql(query_dict)

class WorkBenchConsult(ServerWorkBench):

    def __init__(self, request, page_no, template, work_type):
        super(WorkBenchConsult, self).__init__(request, page_no, template, work_type, 'all', False)

    def do_query(self):
        delay_search = self.request.GET.get('delay_search', '')
        if delay_search:
            self.shop_ids = []
            return

        self.shop_ids = get_query_result(self.request, self.search_type, self.myself_type, self.myself.id, self.myself.position, self.myself_category_list, self.get_shop_ids_byclientgroup())

    def do_bind(self, customer_list):
        customer_list = super(WorkBenchConsult, self).do_bind(customer_list)
        Customer.bind_user_info(customer_list)
        Customer.bulk_bind_events(customer_list)

class WorkBenchExport(ServerWorkBench):

    """工作台导出 add by tianxiaohe 20151126"""
    def __init__(self, request):
        super(WorkBenchExport, self).__init__(request, 0, None, None, 'all', False)
        self.export_type = self.request.GET.get('export_type', '0')

    def do_query(self):
        self.shop_ids = get_query_result(self.request, self.search_type, self.myself_type, self.myself.id, self.myself.position, self.myself_category_list, self.get_shop_ids_byclientgroup())

    def do_bind(self, customer_list):
        Customer.bind_user_info(customer_list)
        if self.export_type == '1':
            # 导出最新一笔订单
            Customer.bind_last_subscribe(customer_list, self.subscribe_category)
        elif self.export_type == '2':
            # 导出7天报表数据
            Customer.bind_7days_data(customer_list)
        elif self.export_type == '3':
            Customer.bind_last_subscribe(customer_list, self.subscribe_category)
            Customer.bind_7days_data(customer_list)
        for c in customer_list:
            if self.myself.position != 'SMANAGER':
                c.qq = c.phone = ''

    def __call__(self):
        self.analysis_server_info()
        self.group_filter()
        self.do_query()
        shop_id_list = self.shop_ids
        if len(shop_id_list) > 2000:
            return {'total':len(shop_id_list)}
        customer_list = self.get_customers(shop_id_list)
        self.do_bind(customer_list)
        return export_workbench_data(customer_list, self.export_type)


def get_query_result(request, search_type, myself_type, myself_id, myself_position, myself_category_list, id_list):
    """工作台 根据条件获取shop_id_list(公用)"""
    today = datetime.date.today()
    # 通用客户群参数
    is_potential = request.GET.get('is_potential', None)
    is_discontent = request.GET.get('is_discontent', None)
    to_1st_contact = request.GET.get('to_1st_contact', None)
    to_2nd_contact = request.GET.get('to_2nd_contact', None)
    unmnt_3days = request.GET.get('unmnt_3days', None)
    no_balance = request.GET.get('no_balance', None)
    rjjh_frozen = request.GET.get('rjjh_frozen', None)
    unoperated_3days = request.GET.get('unoperated_3days', None)

    # 普通搜索参数
    server_id = request.GET.get('server_id', '')
    saler_id = request.GET.get('saler_id', '')
    operater_id = request.GET.get('operater_id', '')
    consult_id = request.GET.get('consult_id', '')
    serve_status = request.GET.get('serve_status', '')
    advertise_effect = request.GET.get('advertise_effect', '')
    last_login_days = request.GET.get('last_login_days', '')
    no_contact_days = request.GET.get('no_contact_days', '')
    to_expire_days = request.GET.get('to_expire_days', '')
    contact_fail = request.GET.get('contact_fail', '')
    bad_comment = request.GET.get('bad_comment', '')
    is_pawn = request.GET.get('is_pawn', '')
    unknown_subscribe = request.GET.get('unknown_subscribe', '')

    # nick = request.GET.get('nick', '').strip()
    nick_list = list(set([v.strip() for v in request.GET.getlist('nick', []) if v.strip()]))
    credit_level = request.GET.get('credit_level', '')
    has_phone = request.GET.get('has_phone', '')
    phone = request.GET.get('phone', '').strip()
    qq = request.GET.get('qq', '').strip()
    shop_category = request.GET.get('shop_category', '').strip()
    is_goldmember = request.GET.get('is_goldmember', '').strip()

    order_create_starttime = request.GET.get('order_create_starttime', '')
    order_create_endtime = request.GET.get('order_create_endtime', '')
    order_end_starttime = request.GET.get('order_end_starttime', '')
    order_end_endtime = request.GET.get('order_end_endtime', '')
    pay_start = request.GET.get('pay_start', '').strip()
    pay_end = request.GET.get('pay_end', '').strip()
    category = request.GET.get('category', '').strip()

    qs_string = "select c.shop_id from ncrm_customer c"
    where_list = []
    subscribe_str = "exists (select max(date_format(create_time, '%%Y-%%m-%%d')) as ct from ncrm_subscribe where shop_id=c.shop_id %s group by shop_id %s)"
    sub_where_list = []
    sub_having_list = []
    cache_group_name = ''

    # 客户分类树节点查询
    node_path = request.GET.get('node_path', None)
    if node_path:
        tree_psuser_id = request.GET.get('tree_psuser_id', None)
        if tree_psuser_id:
            psuser = PSUser.objects.get(id = int(tree_psuser_id))
        else:
            psuser = get_psuser(request)
        shop_id_list = read_tree_branch(node_path, psuser)
        if shop_id_list:
            where_list.append("c.shop_id in (%s)" % (','.join(map(str, shop_id_list))))
        else:
            return []

    # 度量统计查询
    metric_statistic_args = request.GET.get('metric_statistic_args', None)
    if metric_statistic_args:
        xfgroup_id, metric_name, start_date, end_date = metric_statistic_args.split(',')
        xfgroup = XiaoFuGroup.objects.get(id = int(xfgroup_id))
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        _, _, shop_id_list = get_ps_shopid_list(xfgroup, metric_name, [start_date, end_date])
        if shop_id_list:
            where_list.append("c.shop_id in (%s)" % (','.join(map(str, shop_id_list))))
        else:
            return []

    # 度量统计查询
    metric_statistic_args_old = request.GET.get('metric_statistic_args_old', None)
    if metric_statistic_args_old:
        psuser_id, metric_name, start_date, end_date = metric_statistic_args_old.split(',')
        psuser = PSUser.objects.get(id = int(psuser_id))
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        _, _, shop_id_list = get_ps_shopid_list(psuser, metric_name, [start_date, end_date])
        if shop_id_list:
            where_list.append("c.shop_id in (%s)" % (','.join(map(str, shop_id_list))))
        else:
            return []

    if search_type == "query_client_group" or 1: # 20160108 开放 客户群+快速搜索 联合搜索
        group_str_list = []
        # 通用客户群搜索
        extra_str = " and c.%s_id=%s" % (myself_type, myself_id)
        if not myself_category_list:
            extra_str += " and c.latest_end<=current_date"
        elif len(myself_category_list) == 1:
            extra_str += " and c.latest_category='%s'" % myself_category_list[0]
        else:
            extra_str += " and c.latest_category in %s" % (myself_category_list,)
        days3_ago = datetime.date.today() - datetime.timedelta(days = 3)

        if is_potential:
            group_str_list.append("(c.is_potential=1 %s)" % extra_str)
            cache_group_name = "" if cache_group_name else "is_potential"
        if is_discontent:
            group_str_list.append("(c.is_discontent=1 %s)" % extra_str)
            cache_group_name = "" if cache_group_name else "is_discontent"
        if to_1st_contact:
            group_str_list.append("(c.contact_count=0 and c.latest_end>current_date %s)" % extra_str)
            cache_group_name = "" if cache_group_name else "to_1st_contact"
        if to_2nd_contact:
            group_str_list.append("(c.contact_count=1 and c.latest_end>current_date and c.latest_category in ('kcjl', 'qn') and c.consult_id=%s)" % myself_id)
            cache_group_name = "" if cache_group_name else "to_2nd_contact"
        if unmnt_3days:
            group_str_list.append("(c.rjjh_unmnt>='%s' and c.latest_end>current_date and c.latest_category='rjjh' and c.operater_id=%s)" % (days3_ago, myself_id))
            cache_group_name = "" if cache_group_name else "unmnt_3days"
        if no_balance is not None:
            if not no_balance:
                group_str_list.append("1=0")
            elif ',' in no_balance:
                group_str_list.append("c.shop_id in (%s)" % no_balance)
            else:
                group_str_list.append("c.shop_id=%s" % no_balance)
        if rjjh_frozen:
            group_str_list.append("(c.rjjh_frozen=1 and c.latest_end>current_date and c.latest_category='rjjh' and c.operater_id=%s)" % myself_id)
            cache_group_name = "" if cache_group_name else "rjjh_frozen"
        if unoperated_3days:
            group_str_list.append("(c.latest_operate<='%s' and c.latest_end>current_date and c.latest_category in ('rjjh', 'vip', 'ztc') and c.is_pausing=0 and c.operater_id=%s)" % (days3_ago, myself_id))
            cache_group_name = "" if cache_group_name else "unoperated_3days"

        # 自定义客户群搜索
        if id_list:
            if len(id_list) == 1:
                group_str_list.append("c.shop_id=%s" % id_list[0])
            else:
                group_str_list.append("c.shop_id in (%s)" % (','.join(map(str, id_list))))
        elif search_type == "query_client_group":
            group_str_list.append("1=0")

        if group_str_list:
            where_list.append("(%s)" % (" or ".join(group_str_list)))

    """ 2017-05-10 yw 拆分普通搜索（签单人/操作/顾问）为“签单人，操作，顾问”3个输入框，精确搜索 """

    # 普通搜索
    # if server_id:
    #     if str(myself_id) == server_id:
    #         position = myself_position
    #     else:
    #         try:
    #             position = PSUser.objects.get(id = int(server_id)).position
    #         except:
    #             position = ''
    #     if position:
    #         if position in ['SELLER', 'SALELEADER']:
    #             where_list.append("c.saler_id=%s" % server_id)
    #         elif position in ['RJJH', 'RJJHLEADER', 'TPAE', 'TPLEADER']:
    #             where_list.append("c.operater_id=%s" % server_id)
    #         elif position in ['CONSULT', 'CONSULTLEADER']:
    #             where_list.append("c.consult_id=%s" % server_id)
    #         else:
    #             sub_where_list.append(" and (psuser_id=%s or operater_id=%s or consult_id=%s)" % (server_id, server_id, server_id))

    if saler_id:
        where_list.append("c.saler_id=%s" % saler_id)

    if operater_id:
        where_list.append("c.operater_id=%s" % operater_id)

    if consult_id:
        where_list.append("c.consult_id=%s" % consult_id)

    """ END """

    if serve_status:
        if serve_status == '1': # 服务中
            temp_str = "c.latest_end>current_date and not c.is_pausing"
        elif serve_status == '2': # 暂停服务
            temp_str = "c.is_pausing=1"
        elif serve_status == '3': # 已流失
            temp_str = "c.latest_end<=current_date"
        where_list.append(temp_str)

    if advertise_effect:
        where_list.append("c.advertise_effect=%s" % advertise_effect)

    qs_string += " left join router_user u on c.shop_id=u.shop_id"
    if last_login_days.isdigit() or credit_level.isdigit():
        if last_login_days.isdigit():
            where_list.append("u.last_login>='%s'" % (today - datetime.timedelta(days = int(last_login_days))))
        if credit_level.isdigit():
            credit_level = int(credit_level)
            where_list.append("u.level>%s and u.level<=%s" % (credit_level * 5, (credit_level + 1) * 5))

    if no_contact_days.isdigit():
        where_list.append("c.latest_contact<='%s'" % (today - datetime.timedelta(days = int(no_contact_days))))

    if to_expire_days.isdigit():
        where_list.append("c.latest_end>current_date and c.latest_end<='%s'" % (today + datetime.timedelta(days = int(to_expire_days))))

    if contact_fail:
        where_list.append("c.contact_fail=1")

    if bad_comment:
        where_list.append("c.bad_comment=1")

    if is_pawn:
        where_list.append("c.is_pawn=1")

    if unknown_subscribe:
        where_list.append("c.unknown_subscribe=1")

    # if nick:
    #     if nick.isdigit():
    #         where_list.append("c.shop_id=%s" % nick)
    #     else:
    #         where_list.append("c.nick like '%%%s%%'" % nick)
    if nick_list:
        if len(nick_list)==1:
            if nick_list[0].isdigit():
                where_list.append("c.shop_id=%s" % nick_list[0])
            else:
                where_list.append("c.nick like '%%%s%%'" % nick_list[0])
        else:
            temp_list = []
            for v in nick_list:
                if v.isdigit():
                    temp_list.append("c.shop_id=%s" % v)
                else:
                    temp_list.append("c.nick='%s'" % v)
            where_list.append("(%s)"%(' or '.join(temp_list)))

    if has_phone == '0':
        where_list.append("(c.phone='' or c.phone='--' )")
    elif phone:
        where_list.append("c.phone like '%%%s%%'" % phone)
    elif has_phone == '1':
        where_list.append("c.phone!='' and c.phone!='--' ")

    if qq:
        where_list.append("c.qq like '%%%s%%'" % qq)

    if shop_category:
        where_list.append("c.category like '%%%s%%'" % shop_category)

    if is_goldmember:
        where_list.append("c.is_goldmember=1")

    if order_create_starttime:
        sub_having_list.append("ct>='%s'" % order_create_starttime)

    if order_create_endtime:
        sub_having_list.append("ct<='%s'" % order_create_endtime)

    if order_end_starttime:
        where_list.append("c.latest_end>='%s'" % order_end_starttime)

    if order_end_endtime:
        where_list.append("c.latest_end<='%s'" % order_end_endtime)

    if pay_start.isdigit():
        sub_where_list.append(" and pay>=%s" % (int(pay_start) * 100))

    if pay_end.isdigit():
        sub_where_list.append(" and pay<=%s" % (int(pay_end) * 100))

    # 业务类型
    if category:
        where_list.append("c.latest_category='%s'" % category)

    if sub_where_list or sub_having_list:
        sub_where_str, sub_having_str = '', ''
        if sub_where_list:
            sub_where_str = "".join(sub_where_list)
        if sub_having_list:
            sub_having_str = " having %s" % (" and ".join(sub_having_list))
        where_list.append(subscribe_str % (sub_where_str, sub_having_str))

    if where_list:
        qs_string += " where %s" % (" and ".join(where_list))
    qs_string += ' order by u.last_login desc'

    shop_id_tuple = execute_query_sql_return_tuple(qs_string)
    shop_id_list = [row[0] for row in shop_id_tuple]

    # 更新通用群缓存
    if cache_group_name and not (node_path or server_id or saler_id or operater_id or consult_id or serve_status or advertise_effect or last_login_days or no_contact_days or to_expire_days or contact_fail or bad_comment or is_pawn or unknown_subscribe or
            nick_list or credit_level or has_phone or phone or qq or shop_category or order_create_starttime or order_create_endtime or order_end_starttime or order_end_endtime or pay_start or pay_end or category):
        common_groups = CacheAdpter.get(CacheKey.NCRM_COMMON_GROUP_STATISTIC % myself_id, 'crm', {})
        common_groups[cache_group_name] = len(shop_id_list)
        CacheAdpter.set(CacheKey.NCRM_COMMON_GROUP_STATISTIC % myself_id, common_groups, 'crm', 60 * 60 * 48)

    return shop_id_list
