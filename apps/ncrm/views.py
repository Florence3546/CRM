# coding=UTF-8

import datetime
import hashlib
import math
import re
import time
import urllib

import MySQLdb
from django.contrib.auth import logout as auth_logout
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse, Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from dwebsocket.decorators import require_websocket

from apps.alg.dryrun import AdgroupDryRun
from apps.alg.models import StrategyConfig, CommandConfig
from apps.common.cachekey import CacheKey
from apps.common.utils.util_expert_excel import export_excel
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_datetime import datetime_2string, date_2datetime
from apps.common.utils.utils_json import json
from apps.common.utils.utils_log import log
from apps.common.utils.utils_misc import get_methods_8class
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple
from apps.common.utils.utils_render import render_to_error, render_to_limited
from apps.crm.service import CrmCacheServer
from apps.crm.utils import crm_login_download
from apps.engine.models_channel import OrderChannel
from apps.kwslt.models_cat import Cat
from apps.mnt.models_task import UserOptimizeRecord
from apps.ncrm.classify_tree import FieldManager, read_tree_branch
from apps.ncrm.forms import LoginForm, OrderForm, CustomerForm, SubscribeForm, DateRangeForm, PSUserForm2, \
    RecordDistribute
from apps.ncrm.guidance3 import get_split_cycle, get_indicators_byposition, get_performance_statistics
from apps.ncrm.metrics import MetricsManager
from apps.ncrm.models import (
    PSUser, Diary, ClientGroup, Customer, Subscribe, Monitor, Plan, sm_coll, event_coll, reminder_coll,
    TreeTemplate, OPERATION_GROUPS, GROUPS, PLATEFORM_TYPE_CHOICES, ContractFile, Unsubscribe, PlanTree, XiaoFuGroup,
    CATEGORY_CHOICES, ARTICLE_CODE_CHOICES, Comment, ActivityCode,PreSalesAdvice,
    AllocationRecord)
from apps.ncrm.models_order import FuwuOrder
from apps.ncrm.models_performance import PerformanceConfig
from apps.ncrm.utils import pagination_tool
from apps.ncrm.utils_cache import get_consult_ids_bycache, get_consult_ids_byquerier, query_statement_info
from apps.ncrm.utils_send_remind_email import login_send_email
from apps.subway.download import Downloader
from apps.subway.models_adgroup import adg_coll, Adgroup
from apps.subway.models_campaign import Campaign
from apps.subway.models_item import item_coll, Item
from apps.web.models import pa_coll, main_ad_coll, SaleLink, MainAd, Feedback
from thirdapps.dajax.core import Dajax

from apps.common.utils.utils_file_updown import FileOperateUtil

def ps_auth(func):
    """装饰器，将没带指定参数的请求定向给login"""

    def _is_auth(request):
        if request.is_ajax():
            if request and request.session.get('psuser_id', ''):
                return True
            else:
                return False
        else:
            if request and request.session.get('psuser_id', ''):
                return True
            else:
                return False

    def _inner_check(request, *args, **kwargs):
        if _is_auth(request):
            return func(request, *args, **kwargs)
        else:
            redirect_url = reverse('login')
            if request.is_ajax():
                dajax = Dajax()
                dajax.script("alert('您尚未登录，即将跳转到登录页面！');")
                dajax.script("location.href='%s'" % redirect_url)
                return dajax
            else:
                return HttpResponseRedirect(redirect_url)

    return _inner_check

def get_psuser(request):
    """根据请求获取对应的用户"""
    if not hasattr(request, '_psuser'):
        psuser_id = request.session.get('psuser_id', 0)
        try:
            if psuser_id == 0:
                raise ObjectDoesNotExist
            psuser = PSUser.objects.get(id = psuser_id)
        except ObjectDoesNotExist:
            psuser = None
        request._psuser = psuser
    return request._psuser

def login(request, template = "ncrm_login.html"):
    errors = ""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['username']
            password = hashlib.md5(form.cleaned_data['password']).hexdigest()
            psusers = PSUser.objects.filter(name = name, password = password)
            if psusers:
                psuser = psusers[0]
                if psuser.status != '离职':
                    auth_logout(request)
                    if psuser.position in ['RJJH', 'RJJHLEADER', 'TPAE', 'TPLEADER']:
                        search_args = {}
                    else:
                        search_args = {'delay_search':1}
                    if psuser.position in ['SELLER', 'TPAE', 'RJJH', 'CONSULT', 'DESIGNER', 'OPTAGENT', 'SALELEADER', 'TPLEADER', 'CONSULTLEADER', 'RJJHLEADER']:
                        search_args.update({
                                     'serve_status':1,
                                     'server_id':psuser.id,
                                     'name_cn':'%s %s %s' % (psuser.name_cn, psuser.name, psuser.get_position_display()),
                                     })
                    search_args = urllib.urlencode(search_args)
                    request.session.update({
                                            'psuser_id':psuser.id,
#                                             'name':psuser.name_cn,
                                            'login_from':'backend',
                                            'psuser_name':psuser.name_cn,
                                            'perms':psuser.perms,
                                            'search_args':search_args,
                                            'psuser_dept':psuser.department
                                            })

                    if psuser.position == "RJJH":
                        server = CrmCacheServer(psuser.id)
                        server.clear_user_cache()
                        server.reload_cache(user_id = psuser.id, cat_id = -1, \
                                            cur_page = ['account'], consult_id = psuser.id)
                        valid_accounts = server('base').get('base', {}).get('valid_accounts', [])
                        crm_login_download(psuser.id, valid_accounts)
#                     elif psuser.position == 'DESIGNER':
# #                             return HttpResponseRedirect(reverse('cf_designer_home'))
#                         return HttpResponseRedirect(reverse('cf_consult_home'))
#                     elif psuser.position == 'DESCONSULT':
#                         return HttpResponseRedirect(reverse('cf_consult_home'))
#                   每次登陆检测给提醒节点，发送邮件
                    try:
                        login_send_email(psuser.id, psuser.name_cn, psuser.department, psuser.get_department_display(),
                                          psuser.birthday, psuser.probation_date, psuser.contract_end)
                    except Exception, e:
                        raise Exception("%s happend error, e=%s" % (e))
                    return HttpResponseRedirect('/ncrm/myworkbench/?%s' % search_args)
                else:
                    errors = "用户已离职！"
            else:
                errors = "用户名或者密码错误！"
    else:
        form = LoginForm(initial = {'username':'', 'password':''})
        errors = ""

    update_parms = {'form':form, 'errors':errors}
    return render_to_response(template, update_parms, context_instance = RequestContext(request))

@ps_auth
def crm_home(request, template = "ncrm_home.html"):
    return render_to_response(template, {}, context_instance = RequestContext(request))

@ps_auth
def plan_list(request, psuser_id = 0):
    title = request.POST.get('title', '')
    start_time = request.POST.get('start_time', '')
    end_time = request.POST.get('end_time', '')

    psuser = get_psuser(request)

    # 默认显示自己的计划
    current_plan_user = None
    if not psuser_id:
        psuser_id = psuser.id
    elif psuser.id != int(psuser_id):
        try:
            current_plan_user = PSUser.objects.get(id = psuser_id)
        except Exception, e:
            log.error('get relate_plan Plan error, e=%s' % (e))

    my_plan = Plan.objects.filter(psuser__id = psuser_id, parent_id = 0).order_by('-create_time')

    # 搜索
    if request.method == 'POST':
        if title:
            my_plan = my_plan.filter(title__icontains = title)
        if start_time:
            my_plan = my_plan.filter(start_time__gte = start_time)
        if end_time:
            my_plan = my_plan.filter(end_time__lte = end_time)

    # 关联子计划
    for m in my_plan:
        m.childs = Plan.objects.filter(parent_id = m.id).exclude(parent_id = 0)
    return render_to_response('plan_list.html', {'my_plan':my_plan, 'title':title, 'start_time':start_time, 'end_time':end_time, 'current_plan_user':current_plan_user}, context_instance = RequestContext(request))

@ps_auth
def create_plan(request, parent_id = 0):
    parent_plan, err = None, ''
    psuser = get_psuser(request)
    request.psuser = request._psuser
    if parent_id:
        try:
            parent_plan = Plan.objects.get(id = parent_id)
            parent_plan.responsible = PSUser.objects.get(id = parent_plan.psuser.id)
        except Exception, e:
            log.error('get parent_plan error, e=%s' % (e))
            return HttpResponseRedirect(reverse('plan_list'))

    event_list = []
    if request.method == 'POST':
        plan_title = request.POST.get('plan_title', '')
        psuser_id = int(request.POST.get('ps_id', psuser.id))
#         report_id = int(request.POST.get('report_id', 0))
        start_time = request.POST.get('start_time', '').strip()
        end_time = request.POST.get('end_time', '').strip()
        progress = request.POST.get('progress', '')
        target = request.POST.get('target', '').replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
        note = request.POST.get('mark', '').replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
        related_id = int(request.POST.get('related_id', 0))
        event_list = []

        try:
#             psUser = PSUser.objects.get(name_cn = report_name)
#             psUser2 = PSUser.objects.get(name_cn = responsible)
            if psuser_id :
                Plan.objects.create(title = plan_title, psuser_id = psuser_id, \
                                    parent_id = parent_id, related_id = related_id, target = target, note = note, \
                                    progress = progress, start_time = start_time, end_time = end_time, \
                                    create_user_id = request._psuser.id, event_list = ','.join(event_list))
                return HttpResponseRedirect(reverse('plan_list'))
            else:
                err = '责任人或汇报人不存在'
        except Exception, e:
            if 'YYYY' in str(e):
                err = '日期格式不正确，例:2014-12-15'
            else:
                err = '输入参数不全'
            log.exception('create Plan error, e=%s' % (e))

    event_all = []

    return render_to_response('ncrm_create_plan.html', {'parent_plan':parent_plan, 'event_all':event_all, 'err':err, 'psuser':psuser}, context_instance = RequestContext(request))

@ps_auth
def edit_plan(request, plan_id):
    try:
        plan = Plan.objects.get(id = plan_id)
        parent_plan = None
        event_all = []
        if plan.parent_id:
#             related_plan = Plan.objects.get(id = plan.related_id)
            parent_plan = Plan.objects.get(id = plan.parent_id)
#         ps_user = PSUser.objects.get(id = plan.report)
#         plan.ps_user = ps_user
#         plan.responsible = PSUser.objects.get(id = plan.psuser)

        psuser = get_psuser(request)
        request.psuser = request._psuser
        # 修改
        if request.method == 'POST':
            plan_title = request.POST.get('plan_title', '')
            psuser_id = int(request.POST.get('ps_id', 0))
#             report_id = int(request.POST.get('report_id', 0))
            start_time = request.POST.get('start_time', '').strip()
            end_time = request.POST.get('end_time', '').strip()
#             progress = request.POST.get('progress', '')
            target = request.POST.get('target', '')
            note = request.POST.get('mark', '')
            related_id = int(request.POST.get('related_id', 0))
            event_list = []

            plan.title = plan_title
            plan.psuser_id = psuser_id
#             plan.report_id = report_id
            plan.target = target
            plan.note = note
            plan.progress = ""
            plan.start_time = start_time
            plan.end_time = end_time
            plan.related_id = related_id
            plan.event_list = ','.join(event_list)
            plan.save()

            return HttpResponseRedirect(reverse('plan_list'))
    except Exception, e:
        log.error('edit_plan get objects error, e=%s' % (e))
    else:
        event_all = []
    return render_to_response('ncrm_create_plan.html', {'plan':plan, \
                                                        'event_all':event_all, 'mode':'edit', 'parent_plan':parent_plan}, \
                              context_instance = RequestContext(request))

@ps_auth
def del_plan(request, plan_id):
    try:
        Plan.objects.get(id = plan_id).delete()
        Plan.objects.filter(parent_id = plan_id).delete()
    except Exception, e:
        log.error('del_plan get Plan error, e=%s' % (e))
    return HttpResponseRedirect(reverse('plan_list'))

@ps_auth
def child_plan(request, plan_id):
    child_plan = None
    if plan_id:
            child_plan = Plan.objects.filter(parent_id = plan_id)
    return render_to_response('ncrm_child_plan.html', {'child_plan':child_plan}, context_instance = RequestContext(request))

@ps_auth
def lower_detail(request, plan_id):
    '''下属计划详情'''
    checked_event = []
    plan = Plan.objects.get(id = plan_id)
    event = []
    for i in event:
        for e in i[1]:
            if e['is_checked']:
                checked_event.append(e)
    return render_to_response('lower_detail.html', {'checked_event':checked_event, 'plan':plan}, context_instance = RequestContext(request))

@ps_auth
def event_detail(request):
    '''事件详情'''
    event_all = []
    event_list = [e[1] for e in event_all]
    return render_to_response('event_detial.html', {'event_list':event_list}, context_instance = RequestContext(request))

@ps_auth
def event_statistic(request):
    '''事件统计'''
    def event_statistic_sort(x, y):
        '''统计数据排序函数'''
        if x[1] < y[1]:
            return -1
        elif x[1] > y[1]:
            return 1
        elif x[2] < y[2]:
            return -1
        elif x[2] > y[2]:
            return 1
        elif x[3] < y[3]:
            return -1
        elif x[3] > y[3]:
            return 1
        else:
            return 0
    statistic_data = []
    if request.GET.get('load') == '1':
        server_id = request.GET.get('server_id', '')
        server_name = request.GET.get('server_name', '')
        event_type_list = request.GET.getlist('event_type')
        position_type = request.GET.get('position_type')
        department = request.GET.get('department')
        try:
            if server_id:
                server_id = int(server_id)
            start_time = datetime.datetime.strptime(request.GET.get('start_time'), '%Y-%m-%d')
            end_time = datetime.datetime.strptime(request.GET.get('end_time'), '%Y-%m-%d') + datetime.timedelta(days = 1)
        except:
            show_flag = 0
        else:
            # 确定过滤条件
            psuser_list, position_flag, department_flag, query_flag, show_flag = [], False, False, True, 0
            position_dict = {'1':['SELLER', 'SALELEADER'], '2':['TPAE', 'TPLEADER'], '3':['RJJH', 'RJJHLEADER'], '4':['CONSULT', 'CONSULTLEADER']}
            if server_id:
                psuser_list = PSUser.objects.filter(id = server_id)
            elif position_type in position_dict:
                position_list = position_dict.get(position_type)
                psuser_list = PSUser.objects.filter(position__in = position_list)
                if department:
                    psuser_list = psuser_list.filter(department = department)
                position_flag = True
                show_flag = 1
            else:
                if department:
                    psuser_list = PSUser.objects.filter(department = department)
                else:
                    psuser_list = PSUser.objects.all()
                    query_flag = False # 员工过滤标记
                position_flag = True # 统计职位标记
                department_flag = True # 统计部门标记
                show_flag = 2 # 页面展示标记
            psuser_list = psuser_list.only('id', 'position', 'department', 'name_cn')
            psuser_info = {}
            for psuser in psuser_list:
                position = psuser.position or 'NONE'
                if position == 'SALELEADER':
                    position = 'SELLER'
                elif position == 'TPLEADER':
                    position = 'TPAE'
                elif position == 'RJJHLEADER':
                    position = 'RJJH'
                elif position == 'CONSULTLEADER':
                    position = 'CONSULT'
                psuser_info[psuser.id] = [position, psuser.department or 'OTHERS', psuser.name_cn]
            psuser_id_list = psuser_info.keys()
            psuser_data, position_data, department_data = {}, {}, {}

            # mongodb事件
            query = {'create_time':{'$gte':start_time, '$lt':end_time}}
            if query_flag:
                query['psuser_id'] = {'$in':psuser_id_list}
            skip, limit = 0, 10000
            while 1:
                rows = list(event_coll.find(query, {'_id':False, 'shop_id':False, 'create_time':False, 'note':False}, skip = skip, limit = limit))
                skip += limit
                for row in rows:
                    data_list = []
                    position, department, name_cn = psuser_info[row['psuser_id']]
                    position_str = dict(PSUser.POSITION_CHOICES).get(position, position)
                    department_str = dict(PSUser.DEPARTMENT_CHOICES).get(department, department)
                    _data0 = psuser_data.setdefault(row['psuser_id'], {'psuser':name_cn, 'position':position_str, 'department':department_str})
                    data_list.append(_data0)
                    if position_flag:
                        __data1 = position_data.setdefault(position, {})
                        _data1 = __data1.setdefault(department, {'position':position_str, 'department':department_str})
                        data_list.append(_data1)
                    if department_flag:
                        _data2 = department_data.setdefault(department, {'department':department_str})
                        data_list.append(_data2)
                    for _data in data_list:
                        # 联系事件
                        if row['type'] == 'contact':
                            _contact = _data.setdefault('contact', {'sum':0, 'qq':0, 'phone':0, 'ww':0, 'weixin':0, 'visible':0})
                            _contact['sum'] += 1
                            if row['contact_type'] in _contact:
                                _contact[row['contact_type']] += 1
                            if row['visible'] == 1:
                                _contact['visible'] += 1
                        # 操作事件
                        if row['type'] == 'operate':
                            _operate = _data.setdefault('operate', {'sum':0, 'ztc':0, 'zz':0, 'rjjh':0, 'zx':0, 'visible':0})
                            _operate['sum'] += 1
                            if row['oper_type'] in _operate:
                                _operate[row['oper_type']] += 1
                            if row['visible'] == 1:
                                _operate['visible'] += 1
                        # 评论事件
                        if row['type'] == 'comment':
                            _comment = _data.setdefault('comment', {'sum':0, 'c100':0, 'c200':0, 'c300':0})
                            _comment['sum'] += 1
                            if row['comment_type'] >= 300:
                                _comment['c300'] += 1
                            elif row['comment_type'] >= 200:
                                _comment['c200'] += 1
                            else:
                                _comment['c100'] += 1
                        # 转介绍事件
                        if row['type'] == 'reintro':
                            _comment = _data.setdefault('reintro', {'sum':0})
                            _comment['sum'] += 1
                        # 退款事件
                        if row['type'] == 'unsubscribe':
                            refund = row.get('refund', 0)
                            refund_type = int(row.get('refund_type') or 0)
                            # refund_reason = int(row.get('refund_reason') or 0)
                            _unsubscribe = _data.setdefault('unsubscribe', {'sum':0, 'sum_money':0, 'software':0, 'software_money':0, 'tp':0, 'tp_money':0, 'friend':0, 'friend_money':0, 'migrate':0, 'migrate_money':0, 'other':0, 'other_money':0})
                            _unsubscribe['sum'] += 1
                            _unsubscribe['sum_money'] += refund
                            if refund_type == 0:
                                _unsubscribe['other'] += 1
                                _unsubscribe['other_money'] += refund
                            elif refund_type == 1:
                                _unsubscribe['software'] += 1
                                _unsubscribe['software_money'] += refund
                            elif refund_type == 2:
                                _unsubscribe['tp'] += 1
                                _unsubscribe['tp_money'] += refund
                            elif refund_type == 3:
                                _unsubscribe['friend'] += 1
                                _unsubscribe['friend_money'] += refund
                            elif refund_type == 4:
                                _unsubscribe['migrate'] += 1
                                _unsubscribe['migrate_money'] += refund
                if len(rows) < limit:
                    break

            # 订购事件
            query = {'create_time__gte':start_time, 'create_time__lt':end_time}
            if query_flag:
                query['psuser_id__in'] = psuser_info.keys()
            skip, limit = 0, 10000
            while 1:
                # 收集订单
                subscribe_list = Subscribe.objects.filter(create_time__gte = start_time, create_time__lt = end_time)
                if query_flag:
                    # subscribe_list = subscribe_list.filter(Q(psuser_id__in = psuser_id_list) | Q(operater_id__in = psuser_id_list) | Q(consult_id__in = psuser_id_list))
                    subscribe_list = subscribe_list.filter(psuser_id__in = psuser_id_list)
                subscribe_list = subscribe_list.only('psuser_id', 'operater_id', 'consult_id', 'category', 'biz_type', 'source_type', 'pay')[skip:skip + limit]
                skip += limit
                for sub in subscribe_list:
                    # 确定订单业绩所属人
                    if sub.psuser_id:
                        psuser_id = sub.psuser_id
                    else:
                        if sub.biz_type == 1:
                            continue
                        if sub.category in ('kcjl', 'qn'):
                            psuser_id = sub.consult_id
                        else:
                            psuser_id = sub.operater_id
                    if not psuser_id or (query_flag and psuser_id not in psuser_id_list):
                        continue

                    data_list = []
                    position, department, name_cn = psuser_info[psuser_id]
                    position_str = dict(PSUser.POSITION_CHOICES).get(position, position)
                    department_str = dict(PSUser.DEPARTMENT_CHOICES).get(department, department)
                    _data0 = psuser_data.setdefault(psuser_id, {'psuser':name_cn, 'position':position_str, 'department':department_str})
                    data_list.append(_data0)
                    if position_flag:
                        __data1 = position_data.setdefault(position, {})
                        _data1 = __data1.setdefault(department, {'position':position_str, 'department':department_str})
                        data_list.append(_data1)
                    if department_flag:
                        _data2 = department_data.setdefault(department, {'department':department_str})
                        data_list.append(_data2)
                    for _data in data_list:
                        _subscribe = _data.setdefault('subscribe', {'sum':0, 'sum_money':0, 'from_tb':0, 'from_tb_money':0, 'from_man':0, 'from_man_money':0, 'from_reintro':0, 'from_reintro_money':0,
                                                                    'new':0, 'new_money':0, 'renew':0, 'renew_money':0, 'upgrade':0, 'upgrade_money':0, 'unknown':0, 'unknown_money':0, 'kcjl':0, 'kcjl_money':0,
                                                                    'rjjh':0, 'rjjh_money':0, 'ztc':0, 'ztc_money':0, 'qn':0, 'qn_money':0, 'zz':0, 'zz_money':0, 'zx':0, 'zx_money':0, 'dyy':0, 'dyy_money':0, 'seo':0, 'seo_money':0, 'kfwb':0, 'kfwb_money':0})
                        _subscribe['sum'] += 1
                        _subscribe['sum_money'] += sub.pay
                        if sub.source_type == 1:
                            _subscribe['from_tb'] += 1
                            _subscribe['from_tb_money'] += sub.pay
                        elif sub.source_type == 2:
                            _subscribe['from_man'] += 1
                            _subscribe['from_man_money'] += sub.pay
                        elif sub.source_type == 3:
                            _subscribe['from_reintro'] += 1
                            _subscribe['from_reintro_money'] += sub.pay
                        if sub.biz_type == 1:
                            _subscribe['new'] += 1
                            _subscribe['new_money'] += sub.pay
                        elif sub.biz_type == 2:
                            _subscribe['renew'] += 1
                            _subscribe['renew_money'] += sub.pay
                        elif sub.biz_type == 3:
                            _subscribe['upgrade'] += 1
                            _subscribe['upgrade_money'] += sub.pay
                        if sub.category == 'kcjl':
                            _subscribe['kcjl'] += 1
                            _subscribe['kcjl_money'] += sub.pay
                        elif sub.category == 'rjjh':
                            _subscribe['rjjh'] += 1
                            _subscribe['rjjh_money'] += sub.pay
                        elif sub.category in ('vip', 'ztc'):
                            _subscribe['ztc'] += 1
                            _subscribe['ztc_money'] += sub.pay
                        elif sub.category == 'qn':
                            _subscribe['qn'] += 1
                            _subscribe['qn_money'] += sub.pay
                        elif sub.category == 'zz':
                            _subscribe['zz'] += 1
                            _subscribe['zz_money'] += sub.pay
                        elif sub.category == 'zx':
                            _subscribe['zx'] += 1
                            _subscribe['zx_money'] += sub.pay
                        elif sub.category == 'dyy':
                            _subscribe['dyy'] += 1
                            _subscribe['dyy_money'] += sub.pay
                        elif sub.category == 'other':
                            _subscribe['unknown'] += 1
                            _subscribe['unknown_money'] += sub.pay
                        elif sub.category == 'seo':
                            _subscribe['seo'] += 1
                            _subscribe['seo_money'] += sub.pay
                        elif sub.category == 'kfwb':
                            _subscribe['kfwb'] += 1
                            _subscribe['kfwb_money'] += sub.pay
                if len(subscribe_list) < limit:
                    break

            # 汇总结果
            for psuser_id, _data in psuser_data.items():
                position, department, _ = psuser_info[psuser_id]
                statistic_data.append([0, department, position, psuser_id, _data])
            for position, __data in position_data.items():
                for department, _data in __data.items():
                    statistic_data.append([1, department, position, None, _data])
            for department, _data in department_data.items():
                statistic_data.append([2, department, None, None, _data])
            statistic_data.sort(event_statistic_sort)
    else:
        psuser = get_psuser(request)
        if psuser.department in ['DESIGN', 'OPTAGENT', 'GROUP1', 'GROUP2', 'GROUP3', 'GROUP4', 'GROUP5'] and psuser.position != 'COMMANDER':
            server_id = psuser.id
            server_name = '%s %s %s' % (psuser.name_cn, psuser.name, dict(PSUser.POSITION_CHOICES).get(psuser.position))
        else:
            server_id = ''
            server_name = ''
        event_type_list = ['all', 'subscribe', 'contact', 'operate', 'comment', 'unsubscribe']
        show_flag = 0
    return render_to_response('event_statistic.html', {
                                                       'statistic_data':statistic_data,
                                                       'server_id':server_id,
                                                       'server_name':server_name,
                                                       'event_type_list':event_type_list,
                                                       'show_flag':show_flag,
                                                       }, context_instance = RequestContext(request))


@ps_auth
def myworkbench(request):
    psuser = get_psuser(request)
    mapping_dict = {
                    'CONSULT':'consult',
                    'CONSULTLEADER':'consult',
                    'MKT':'consult',
                    'PRESELLER':'consult',
                    'SELLER':'consult',
                    'SALELEADER':'consult',
#                     'TPAE':'operator',
#                     'TPLEADER':'operator',
                    'TPAE':'consult',
                    'TPLEADER':'consult',
                    'DEV':'consult',
                    'SUPER':'consult',
#                     'RJJH':'hmi',
#                     'RJJHLEADER':'hmi',
                    'RJJH':'consult',
                    'RJJHLEADER':'consult',
                    'OPTAGENT':'consult',
                    }

    return workbench(request, mapping_dict.get(psuser.position, 'consult'), page = 1)

@ps_auth
def workbench(request, work_type, page = 1):
    """路由函数？url改成这样？需要检查work_type是否合法
    /ncrm/workbench/operator/1
    /ncrm/workbench/saler/2
    /ncrm/workbench/consult/10
    /ncrm/workbench/phonesaler/10
    """
    from apps.ncrm.workbench import WorkBenchConsult
    if work_type == 'consult':
        return locals()['WorkBench%s' % (work_type.capitalize())](request, page, 'workbench_%s.html' % work_type, work_type)()
    else:
        return render_to_error(request, "出错啦！工作台类型不对？")

@ps_auth
def export_customer_data(request):
    """导出个人工作台"""
    raise Http404
    try:
        from apps.ncrm.workbench import WorkBenchExport
        result = locals()['WorkBenchExport'](request)()
        if 'total' in result:
            return render_to_response('download_error.html', result)
        else:
            return locals()['WorkBenchExport'](request)()
    except Exception, e:
        log.error('create export_customer_data error, e=%s' % (e))
        return render_to_error(request, "出错啦！数据导出异常，请联系管理员！")

@ps_auth
def order_manage(request):
    """订单管理"""
    psuser = get_psuser(request)
    page_size = 100
    # qs = Subscribe.objects.select_related()
    customer = None
    if request.method == 'POST':
        form = OrderForm(data = request.POST)
        if form.is_valid(): # TODO: wangqi 20141215 需要增加对订单细致数据的查询，如金额、版本、签单人等？
            nick = form.cleaned_data['nick'].strip()
            start_time = form.cleaned_data['start_date']
            end_time = form.cleaned_data['end_date']
            page_no = int(form.cleaned_data['page_no'])
#             article_code = form.cleaned_data['article_code']
            category = form.cleaned_data['category']
            source_type = form.cleaned_data['source_type']
            biz_type = form.cleaned_data['biz_type']
            approval_status = form.cleaned_data['approval_status']
            owner = form.cleaned_data['owner'] and int(form.cleaned_data['owner']) or None

            saler_id = form.cleaned_data['saler_id'] and int(form.cleaned_data['saler_id']) or None
            operater_id = form.cleaned_data['operater_id'] and int(form.cleaned_data['operater_id']) or None
            consult_id = form.cleaned_data['consult_id'] and int(form.cleaned_data['consult_id']) or None

            if nick != '':
                if nick.isdigit():
                    customer = Customer.objects.filter(shop_id = int(nick))
                else:
                    customer = Customer.objects.filter(nick__contains = nick)

            if customer and customer.count():
                qs = Subscribe.objects.filter(shop__in = [c for c in customer])
            else:
                qs = Subscribe.objects

            if start_time:
                qs = qs.filter(create_time__gte = start_time)
            if end_time:
                qs = qs.filter(create_time__lt = end_time + datetime.timedelta(days=1))
#             if article_code:
#                 qs = qs.filter(article_code = article_code)
            if category:
                qs = qs.filter(category = category)
            if owner:
                qs = qs.filter(Q(psuser = owner) | Q(operater = owner) | Q(consult = owner))
            if source_type:
                qs = qs.filter(source_type = source_type)
            if biz_type:
                qs = qs.filter(biz_type = int(biz_type))
            if approval_status:
                qs = qs.filter(approval_status = int(approval_status))

            if saler_id:
                qs = qs.filter(Q(psuser = saler_id))
            if operater_id:
                qs = qs.filter(Q(operater = operater_id))
            if consult_id:
                qs = qs.filter(Q(consult = consult_id))

    else:
        form = OrderForm({'nick':'', 'start_date':'', 'end_date':''})
        qs = Subscribe.objects.filter(psuser__isnull = True)
        page_no = 1

    total_count = qs.count()
    order_list = qs.order_by('-create_time')[page_size * (page_no - 1):page_size * page_no]
    return render_to_response('order_manage.html', {
                                                    'order_list':order_list,
                                                    'psuser':psuser,
                                                    'today':datetime.date.today(),
                                                    'form':form, 'total_count':total_count
                                                    }, context_instance = RequestContext(request))
@ps_auth
def order_dunning(request):
    latest_days = int(request.GET.get('latest_days') or 3)
    today_datetime = date_2datetime(datetime.date.today())
    view_type = request.GET.get('view_type', 'unpaid')
    try:
        query_dict = {"create_time__gte": today_datetime - datetime.timedelta(days=latest_days)}
        # week_ago = date_2datetime(datetime.date.today() - datetime.timedelta(days = 7)) # 默认给7天前的数据
        # start_date = request.GET.get("start_date", week_ago)
        # end_date = request.GET.get("end_date")
        # if start_date:
        #     query_dict.update({'create_time__gte': start_date})
        #
        # if end_date:
        #     query_dict.update({'create_time__lte': end_date})
        qs = FuwuOrder.objects.filter(**query_dict)
    except Exception, e:
        log.error("get data error, e=%s" % e)
        qs = FuwuOrder.objects

    if view_type == "unpaid":
        qs = list(qs.filter(pay_status=0, is_closed=0).order_by('-create_time'))
        list_desc = "未付款订单"
    # elif view_type == "paid":
    #     qs = list(qs.filter(pay_status=1))
    #     list_desc = "已付款订单"
    elif view_type == "closed":
        qs = list(qs.filter(is_closed=1).order_by('-create_time'))
        list_desc = "已关闭订单"
    else:
        qs = list(qs)
        list_desc = "所有订单"
    order_id_list = [obj.order_id for obj in qs]
    payed_order_id_list = list(Subscribe.objects.filter(order_id__in=order_id_list).values_list('order_id', flat=True))
    if payed_order_id_list:
        qs = [obj for obj in qs if obj.order_id not in payed_order_id_list]
        # FuwuOrder.objects.filter(order_id__in=payed_order_id_list).delete()
    FuwuOrder._get_collection().remove({'$or': [{'pay_status': 1}, {'note': '已订购'}, {'order_id': {'$in': payed_order_id_list}}]}, multi=True)
    activity_code_list = ActivityCode.objects.all().order_by('-activity_code')
    return render_to_response('order_dunning.html', {
        'order_list': qs,
        'list_desc': list_desc,
        'view_type': view_type,
        'activity_code_list': activity_code_list
    }, context_instance=RequestContext(request))

@ps_auth
def record_distribute(request):
    """订单分发"""
    psuser = get_psuser(request) #获取用户信息
    page_size = 100
    if request.method == 'POST':
        form = RecordDistribute(data=request.POST)
        if form.is_valid():
            psuser_id = form.cleaned_data['psuser_id']
            shop = form.cleaned_data['shop']
            subscribe_id = form.cleaned_data['subscribe_id']
            org_list_id = form.cleaned_data['org_list_id']
            new_list_id = form.cleaned_data['new_list_id']
            order_start_date = form.cleaned_data['order_start_date']
            order_end_date = form.cleaned_data['order_end_date']
            distribute_start_date = form.cleaned_data['distribute_start_date']
            distribute_end_date = form.cleaned_data['distribute_end_date']
            pay_start = form.cleaned_data['pay_start']
            pay_end = form.cleaned_data['pay_end']

            # 过滤页码
            page_no = int(form.cleaned_data['page_no'])

            category = form.cleaned_data['category']

            #过滤分配人
            if psuser_id:
                qs = AllocationRecord.objects.filter(psuser_id=int(psuser_id))
            else:
                qs = AllocationRecord.objects

            #过滤店铺
            if shop:
                if shop.isdigit():
                    qs = qs.filter(shop_id=int(shop))
                else:
                    # 这里可以做模糊查询，获取多个shop_id
                    shop_id = Customer.objects.filter(nick=shop).first().shop_id
                    if shop_id:
                        qs = qs.filter(shop_id=shop_id)
            #过滤订单ID
            if subscribe_id:
                qs = qs.filter(subscribe_id=subscribe_id)

            #过滤原人员列表
            if org_list_id:
                qs = qs.filter(org_id_list=org_list_id)

            #过滤新人员列表
            if new_list_id:
                qs = qs.filter(new_id_list=new_list_id)

            #过滤订购时间
            if order_start_date:
                qs = qs.filter(sub_time__gte = order_start_date)
            if order_end_date:
                qs = qs.filter(sub_time__lte = order_end_date + datetime.timedelta(days=1))

            #过滤分配时间
            if distribute_start_date:
                qs = qs.filter(create_time__gte=distribute_start_date)
            if distribute_end_date:
                qs = qs.filter(create_time__lte=distribute_end_date + datetime.timedelta(days=1))

            #过滤金额范围
            if pay_start:
                qs = qs.filter(pay__gte=int(pay_start)*100)
            if pay_end:
                qs = qs.filter(pay__lte=int(pay_end)*100)

            # 过滤业务类型
            if category:
                category_cn = unicode(AllocationRecord.get_category_cn_by_category(category.strip()), 'utf-8')
                qs = qs.filter(category_cn__contains=category_cn)
    else:
        form = OrderForm({'psuser': '','shop': '','org_list': '','new_list': '','subscribe_id': '', 'order_start_date': '', 'order_end_date': '','distribute_start_date': '', 'distribute_end_date': '','pay_start': '', 'pay_end': ''})
        qs = AllocationRecord.objects.all()
        page_no = 1

    total_count = qs.count()
    shop_id_list = []
    record_list = list(qs.order_by('-create_time')[page_size * (page_no - 1):page_size * page_no])

    for record in record_list:
        shop_id_list.append(record.shop_id)

    shop_dict = dict(Customer.objects.filter(shop_id__in=shop_id_list).values_list('shop_id', 'nick'))
    for record in record_list:
        record.nick = shop_dict.get(record.shop_id, record.shop_id)

    return render_to_response('record_distribute.html', {
        'record_list': record_list,
        'psuser': psuser,
        'today': datetime.date.today(),
        'form': form,
        'shop_dict':shop_dict,
        'page_size':page_size,
        'total_count': total_count
    }, context_instance=RequestContext(request))

@ps_auth
@require_websocket
def echo_msg(request):
    p = OrderChannel.subscribe()
    while True:
        msg = p.get_message()
        try:
            request.websocket.read()
        except (Exception, EOFError):
            break
        if msg and isinstance(msg['data'], str):
            request.websocket.send(msg['data'].encode('utf-8'))
        time.sleep(0.2)
    OrderChannel.unsubscribe(p)
    request.websocket.close()

# @ps_auth
# def client_group(request):
#     ''''客户群列表'''
#     get_psuser(request)
#     err = ''
#     if request.method == 'POST':
#         title = request.POST.get('title', '').strip()

#         if title:
#             try:
#                 ClientGroup.objects.create(title = title, create_user_id = request._psuser.id)
#                 return HttpResponseRedirect(reverse('client_group'))
#             except Exception, e:
#                 err = '创建群失败,e = %s' % (e)
#                 log.error('create client_group error, e=%s' % (e))
#         else:
#             err = '群名称不能为空'

#     group_list = ClientGroup.objects.filter(create_user__id = request._psuser.id)
#     for g in group_list:
#         g.id_list = g.id_list and eval(g.id_list) or []
#     return render_to_response('ncrm_client_group.html', {'group_list':group_list}, context_instance = RequestContext(request))

@ps_auth
def add_client(request, id, page = 1):
    '''客户群修改'''
    def get_vaid_ids_text(id_list_text):
        separator = ','
        separator_cn = '，'
        id_list_text = id_list_text.replace(' ', '').replace(separator_cn, separator)

        start, end = 0, len(id_list_text)
        if id_list_text[-1] == separator:
            end = -1
        if id_list_text[0] == separator:
            start = 1
        return id_list_text[start:end]

    err, customer, clients, page_info, help_dict = '', [], None, [], {}
    if id:
        try:
            clients = ClientGroup.objects.get(id = id)
            clients_id_list = clients.id_list and eval(clients.id_list) or []
        except Exception, e:
            err = "获取客户群失败,e=%s" % (e)
            log.error('create client_group error, e=%s' % (e))
    else:
        err = "id参数错误"

    # 查询
    search_type = request.POST.get('search_type', '')
    query = request.POST.get('query', '').strip()
    nick = request.POST.get('nick', '').strip()
    shop_id = int(request.POST['shop_id']) if request.POST.get('shop_id', 0) else 0
    qq = request.POST.get('qq', '').strip()
    ww = request.POST.get('ww', '').strip()
    phone = request.POST.get('phone', '').strip()

    id_list_text = request.POST.get('id_list_textarea', '').strip()

    if search_type == 'query':
        # 查询器查询
        if query:
            psuser = get_psuser(request)
            id_list, err = get_consult_ids_byquerier(psuser.id, query)

            page_info, id_list = pagination_tool(page = page, record = id_list)
            customer = Customer.objects.filter(shop_id__in = id_list)
        else:
            err = "查询条件为空"
    elif search_type == 'unquery':
        # 单个查询
        customer = Customer.objects.filter()

        if shop_id:
            customer = customer.filter(shop_id = shop_id)
        if nick:
            customer = customer.filter(nick__contains = nick)
        if phone:
            customer = customer.filter(phone = phone)
        if qq:
            customer = customer.filter(qq = qq)
        if ww:
            customer = customer.filter(ww = ww)
        if id_list_text:
            id_list_text = get_vaid_ids_text(id_list_text)
            search_list = map(int, id_list_text.split(','))
            customer = customer.filter(shop_id__in = search_list)

        page_info, customer = pagination_tool(page = page, record = customer)
    # if customer:
    #     page_info, customer = pagination_tool(page = page, record = customer)

    for i in clients_id_list:
        for c in customer:
            if c.shop_id == i:
                c.select = 1

    Customer.binder_order_info(customer)
    # 加载帮助文档
    help_dict = query_statement_info()
    return render_to_response('ncrm_add_client.html', {'customer':customer, 'error':err, 'clients':clients, 'page_info':page_info, 'help_dict':help_dict}, context_instance = RequestContext(request))

@ps_auth
def advance_query(request, client_group_id, page = 1):
    '''客户群修改'''
    def get_vaid_ids_text(id_list_text):
        separator = ','
        separator_cn = '，'
        id_list_text = id_list_text.replace(' ', '').replace(separator_cn, separator)

        start, end = 0, len(id_list_text)
        if id_list_text[-1] == separator:
            end = -1
        if id_list_text[0] == separator:
            start = 1
        return id_list_text[start:end]

    err, customer, clients, page_info, help_dict = '', [], None, [], {}

    # 查询
    search_type = request.POST.get('search_type', '')
    query = request.POST.get('query', '').strip()
    nick = request.POST.get('nick', '').strip()
    shop_id = int(request.POST['shop_id']) if request.POST.get('shop_id', 0) else 0
    qq = request.POST.get('qq', '').strip()
    ww = request.POST.get('ww', '').strip()
    phone = request.POST.get('phone', '').strip()

    id_list_text = request.POST.get('id_list_textarea', '').strip()
    psuser = get_psuser(request)
    if search_type == 'query':
        # 查询器查询
        if query:
            id_list, err = get_consult_ids_byquerier(psuser.id, query)

            page_info, id_list = pagination_tool(page = page, record = id_list)
            customer = Customer.objects.filter(shop_id__in = id_list)
        else:
            err = "查询条件为空"
    elif search_type == 'unquery':
        # 单个查询
        customer = Customer.objects.filter()

        if shop_id:
            customer = customer.filter(shop_id = shop_id)
        if nick:
            customer = customer.filter(nick__contains = nick)
        if phone:
            customer = customer.filter(phone = phone)
        if qq:
            customer = customer.filter(qq = qq)
        if ww:
            customer = customer.filter(ww = ww)
        if id_list_text:
            id_list_text = get_vaid_ids_text(id_list_text)
            search_list = map(int, id_list_text.split(','))
            customer = customer.filter(shop_id__in = search_list)

        page_info, customer = pagination_tool(page = page, record = customer)
    # if customer:
    #     page_info, customer = pagination_tool(page = page, record = customer)

    Customer.binder_order_info(customer)
    # 加载帮助文档
    help_dict = query_statement_info()
    return render_to_response('ncrm_advance_query.html', \
                               {'customer':customer, "client_group_id":client_group_id, 'psuser_id':psuser.id, \
                                'error':err, 'clients':clients, 'page_info':page_info, 'help_dict':help_dict}, \
                               context_instance = RequestContext(request))

@ps_auth
def generate_customer_csv_byquery(request, charset = "GBK"):

    def generator_shop_ids(size = 5000):
        shop_all = get_consult_ids_bycache(psuser.id)
        cycle = int(math.ceil(len(shop_all) * 1.0 / size))
        for index in xrange(cycle):
            yield shop_all[index * size:(index + 1) * size]

    psuser = get_psuser(request)

    file_name = "导出的所有客户"
    content = "昵称列表\n"
    try:
        for shop_ids in generator_shop_ids():
            nick_list = ["%s\n" % (cust.nick) for cust in Customer.objects.only("nick").\
                         filter(shop_id__in = shop_ids)]
            content += "".join(nick_list)
    except Exception, e:
        log.exception(e)
        content = ""
    response = HttpResponse(mimetype = "text/csv")
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % (file_name)
    response.write(content.encode(charset))
    return response


@ps_auth
def edit_customer(request):
    is_new = False
    try:
        cust_id = int(request.GET.get('cust_id', 0))
        if cust_id == 0:
            is_new = True
            raise ObjectDoesNotExist
        customer = Customer.objects.get(id = cust_id)
    except ObjectDoesNotExist:
        customer = None
    form = CustomerForm(instance = customer)
    now = datetime.datetime.now()
    has_contact_perm = False
    if customer:
        myself = get_psuser(request)
        if myself in [customer.saler, customer.operater, customer.consult] or myself.position == 'SMANAGER':
            has_contact_perm = True
        else:
            if customer.consult:
                department = customer.consult.department
            elif customer.operater:
                department = customer.operater.department
            elif customer.saler:
                department = customer.saler.department
            else:
                department = None
            commanders = list(PSUser.objects.filter(position='COMMANDER', status='转正', department=department))
            if commanders and myself in commanders:
                has_contact_perm = True
            elif customer.consult:
                xf_groups = XiaoFuGroup.objects.filter(consult = customer.consult, start_time__lte=now, end_time__gt=now)
                if xf_groups and myself == xf_groups[0].seller:
                    has_contact_perm = True

    return HttpResponse(render_to_string('edit_customer.html', {'form':form, 'is_new':is_new, 'has_contact_perm':has_contact_perm}, context_instance = RequestContext(request)))

@ps_auth
def edit_subscribe(request):
    subscribe_id = int(request.GET.get('subscribe_id', 0))
    try:
        if subscribe_id == 0:
            raise ObjectDoesNotExist
        subscribe = Subscribe.objects.select_related('psuser').get(id = subscribe_id)
    except ObjectDoesNotExist:
        subscribe = None
    form = SubscribeForm(instance = subscribe)
    myself = get_psuser(request)
    return HttpResponse(render_to_string('edit_subscribe.html', {
            'form':form,
            'subscribe_id':subscribe_id,
            'subscribe':subscribe,
            'nick':request.GET['nick'],
            'can_modify_approval_status':request.GET.get('approval_tag', '') and myself.position == 'COMMANDER' and
                                         subscribe and subscribe.approval_status == 2
                                         and subscribe.psuser and myself.department == subscribe.psuser.department,
        }, context_instance = RequestContext(request)))

@ps_auth
def login_ztc(request, shop_id):
    '''根据shop_id登录后台'''
    customer = None
    if shop_id:
        try:
            customer = Customer.objects.get(shop_id = shop_id)
        except Exception:
            customer = None

    content_str = render_to_string('ncrm_login_ztc.html', {"customer":customer})
    response = HttpResponse(content_str.decode('utf8').encode('gbk'), content_type = 'text/html;charset=gbk;')
    return response

@ps_auth
def login_kcjl(request, mode, shop_id):
    url, err, context = '', '', {}
    if shop_id:
        try:
            customer = Customer.objects.get(shop_id = shop_id)
            context['user'] = {}
            context['user']['username'] = customer.nick
        except Exception:
            customer = None

        if customer:
            url = customer.ztcjl_login_url.get('%s_url' % mode, '')
            if not url:
                err = '没有订购该服务'
        else:
            err = '用户不存在，或参数不正确'
    if url:
        psuser = get_psuser(request)
        Monitor.add_event(int(shop_id), psuser, mode)
        return HttpResponseRedirect(url)
    else:
        return render_to_error(request = request, msg = err, context = context)

def login_test(request, shop_id):
    try:
        shop_id = int(shop_id)
        if shop_id in [63518068]:
            customer = Customer.objects.get(shop_id = shop_id)
            url = customer.ztcjl_login_url['web_url']
            return HttpResponseRedirect(url)
        else:
            raise Exception("wrong_shop")
    except Exception:
        return HttpResponse("<html>非测试店铺哦</html>")

@ps_auth
def diary_list(request, name = "all", template = "diary_list.html"):
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days = 30)
    end_date = today + datetime.timedelta(days = 1)
    format_date = '%Y-%m-%d'
    if request.method == "POST":
        date_range_form = DateRangeForm(data = request.POST)
        if date_range_form.is_valid():
            start_date = date_range_form.cleaned_data['start_date']
            end_date = date_range_form.cleaned_data['end_date']
            request.session['start_date'] = start_date.strftime(format_date)
            request.session['end_date'] = end_date.strftime(format_date)
    else:
        if request.session.has_key('start_date'):
            start_date = datetime.datetime.strptime(request.session['start_date'], format_date).date()
            end_date = datetime.datetime.strptime(request.session['end_date'], format_date).date()
        date_range_form = DateRangeForm(initial = {'start_date':start_date, 'end_date':end_date})

    qs = Diary.objects.filter(create_time__gte = start_date, create_time__lte = end_date)

    me = get_psuser(request)
    if name == "mine":
        name = me.name
    from django.db.models.query_utils import Q
    psuser_list = PSUser.objects.filter(Q(manager__contains = me.name_cn) | Q(pk = me.pk)).exclude(status = '离职')
    name_dict = {psuser.name:psuser.name_cn for psuser in psuser_list}
    me.is_manager = False
    if len(psuser_list) >= 2: # 取出的user_list数量多于两个，说明是主管级别
        me.is_manager = True
        if name == "all":
            result = qs.filter(author__in = psuser_list)
        else:
            if name not in name_dict:
                name = name_dict.keys()[0]
            result = qs.filter(author__name = name)
    else: # 普通员工，只能看到自己的日志
        result = qs.filter(author = me)
    diary_owner = name_dict.get(name, '全部人')
    return render_to_response(template, {"date_range_form":date_range_form, "diary_list":result, 'user_list':psuser_list, 'name':name, 'diary_owner':diary_owner, 'me':me}, context_instance = RequestContext(request))


@ps_auth
def change_psw(request, template = "change_psw.html"):
    """更改密码"""
    return render_to_response(template, {}, context_instance = RequestContext(request))

@ps_auth
def psuser_contact(request, template = "psuser_contact.html"):
    """员工联系方式"""
    psuser = get_psuser(request)
    error_info = []
    if request.method == "POST":
        form = PSUserForm2(request.POST)
        if form.is_valid():
            psuser.name_cn = form.cleaned_data['name_cn']
            psuser.birthday = form.cleaned_data['birthday']
            psuser.gender = form.cleaned_data['gender']
            psuser.ww = form.cleaned_data['ww']
            psuser.qq = form.cleaned_data['qq']
            psuser.phone = form.cleaned_data['phone']
            psuser.save()
            return HttpResponseRedirect(reverse('plan_list'))
        else:
            psuser.name_cn = request.POST.get('name_cn')
            psuser.birthday = request.POST.get('birthday')
            psuser.gender = request.POST.get('gender')
            psuser.ww = request.POST.get('ww')
            psuser.qq = request.POST.get('qq')
            psuser.phone = request.POST.get('phone')
            error_info = form.errors
    return render_to_response(template, {'psuser':psuser, 'error_info':error_info}, context_instance = RequestContext(request))

@ps_auth
def psuser_roster(request, template = "psuser_roster.html"):
    """员工花名册"""
    me = get_psuser(request)
#     if me.position == "SUPER": # 超级账号可以查看离职人员
    if 'e' in me.perms:
        psuser_list = PSUser.objects.all()
    else:
        psuser_list = PSUser.objects.exclude(status = '离职')
    return render_to_response(template, {'psuser_list':psuser_list}, context_instance = RequestContext(request))

@ps_auth
def ncrm_psuser_roster(request, template = 'ncrm_psuser_roster.html'):
    me = get_psuser(request)
    if me.position in ['HR', 'COMMANDER', 'SMANAGER']:
        psuser_list = PSUser.objects.all()
    else:
        psuser_list = PSUser.objects.exclude(status = '离职')
    return_dict = {'position':PSUser.POSITION_CHOICES, 'department':PSUser.DEPARTMENT_CHOICES, 'psuser_list':psuser_list, 'me':me}
    return render_to_response(template, return_dict, context_instance = RequestContext(request))

@ps_auth
def ncrm_add_psuser(request, template = 'ncrm_add_psuser.html'):
    return_dict = {'position':PSUser.POSITION_PERMS_CHOICES, 'department':PSUser.DEPARTMENT_CHOICES, 'gender':PSUser.GENDER_CHOICES, 'status':PSUser.STATUS_CHOICES, 'education':PSUser.EDUCATION_CHOICES}
    psuser_id = request.GET.get('id')
    if psuser_id:
        psuser = PSUser.objects.get(id = psuser_id)
        return_dict['psuser'] = psuser
        return_dict['update'] = True
        return_dict['info'] = u'修改当前员工信息'
    else:
        return_dict['false'] = True
        return_dict['info'] = u'添加员工信息'
    return render_to_response(template, return_dict, context_instance = RequestContext(request))

@ps_auth
def check_log(request, template = "ncrm_check_log.html"):
    """检查日志"""
    def get_date_bytoday(days = 0):
        calc_time = datetime.datetime.now() - datetime.timedelta(days = days)
        return calc_time.strftime("%Y-%m-%d")

    def covert_datetime(date_time_str):
        return datetime.datetime.strptime(date_time_str, "%Y-%m-%d")

    start_time = request.POST.get("start_time", get_date_bytoday(30))
    end_time = request.POST.get("end_time", get_date_bytoday())
    psuser_id = int(request.POST.get("search_id", 0))

    result = {
                "start_time":start_time,
                "end_time":end_time,
                "psuser":None,
                "logs":[]
              }

    if request.method == "POST":
        if psuser_id:
            try:
                user = PSUser.objects.get(id = psuser_id)
                start_time = covert_datetime(start_time)
                end_time = covert_datetime(end_time)
                qs = Diary.objects.filter(create_time__gte = start_time, create_time__lt = end_time, author = user).order_by("create_time")
                result["logs"] = qs
                result["psuser"] = user
            except Exception, e:
                pass
        else:
            result["error"] = "搜索用户不能为空"

    return render_to_response(template, result, context_instance = RequestContext(request))

@ps_auth
def rpt_snap(request, template = 'ncrm_rpt_snap.html'):
    return render_to_response(template, {}, context_instance = RequestContext(request))

@ps_auth
def task_rpt(request, template = 'ncrm_task_rpt.html'):
    return render_to_response(template, {}, context_instance = RequestContext(request))

@ps_auth
def point_manager(request, template = 'ncrm_point_manager.html'):
    from apps.web.point import PointManager
    # 该函数仅仅是为了验证的临时代码，如果验证后期价值点高，则考虑重构。
    page = request.POST.get('page', 1)
    user_info = request.POST.get('user_info', "")
    server_id = request.POST.get('server_id')
    server_id = int(server_id) if server_id else 0

    is_freeze = request.POST.get("is_freeze", "")
    is_freeze = int(is_freeze) if is_freeze != "" else -1

    create_starttime = request.POST.get('create_starttime', "")
    create_endtime = request.POST.get('create_endtime', "")
    default_starttime = (datetime.datetime.now() - datetime.timedelta(days = 30)).strftime("%Y-%m-%d")
    check_types = [key for key, val in request.POST.items() if val == "on"]
    default_check_types = PointManager.get_default_types()

    if request.method == "GET":
        create_starttime = default_starttime
        check_types = default_check_types
        is_freeze = 0

#     result_list = pa_coll.find({'is_freeze':0, 'type':{'$in':['virtual', 'gift']}}).sort('create_time', -1)
    find_condition = {}
    if is_freeze > -1 :
        find_condition.update({'is_freeze':is_freeze})

    if user_info:
        shop_id_list = [ cust.shop_id for cust in Customer.objects.only('shop_id').\
                        filter(Q(nick__icontains = user_info) | Q(shop_id__contains = user_info))]
        find_condition.update({'shop_id':{'$in':shop_id_list}})

    if server_id:
        shop_id_list = [ cust.shop_id for cust in Customer.objects.filter(consult_id = server_id)]
        find_condition.update({'$or':[{'shop_id':{'$in':shop_id_list}}, {'consult_id':int(server_id)}]})

    if create_starttime:
        start_time = datetime.datetime.strptime(create_starttime, "%Y-%m-%d")
        start_time = start_time.replace(hour = 0, minute = 0, second = 0)
        if 'create_time' not in find_condition:
            find_condition.update({'create_time':{}})
        find_condition['create_time'].update({"$gte":start_time})

    if create_endtime:
        end_time = datetime.datetime.strptime(create_endtime, "%Y-%m-%d")
        end_time = end_time.replace(hour = 23, minute = 59, second = 59)
        if 'create_time' not in find_condition:
            find_condition.update({'create_time':{}})
        find_condition['create_time'].update({"$lte":end_time})

    if check_types:
        find_condition.update({'type':{"$in":check_types}})

    result_list = pa_coll.find(find_condition).sort('create_time', -1)

    page_info, result_list = pagination_tool(page = page, record = result_list)

    detial_list = []
    shop_list_set = set()
    for r in result_list:
        shop_list_set.add(int(r['shop_id']))
        detial_list.append(r)
    shop_list = list(shop_list_set)

    cust_mapping = {cust.shop_id:cust for cust in Customer.objects.select_related("consult")\
                        .filter(shop_id__in = shop_list)}
    type_choices = PointManager.get_type_choices(True)
    for ac_info in detial_list:
        shop_id = int(ac_info["shop_id"])
        customer = cust_mapping.get(shop_id, None)
        if customer:
            ac_info['id'] = ac_info['_id'].__str__()
            ac_info['nick'] = customer.nick
            ac_info['consult_name'] = customer.consult.name_cn if customer.consult else ''
            ac_info['type_desc'] = PointManager.get_type_desc(ac_info['type'])
            ac_info['phone'] = customer.phone

            if ac_info['type'] == 'gift':
                ac_info['receiver'] = customer.receiver
                ac_info['receive_address'] = customer.receive_address
                ac_info['zip_code'] = customer.zip_code

    return render_to_response(template, {'detial_list':detial_list,
                                'page_info':page_info,
                                'type_choices':type_choices,
                                'create_starttime':create_starttime,
                                'check_types':check_types,
                                'is_freeze':is_freeze,
                                }, context_instance = RequestContext(request))

@ps_auth
def sale_link(request):
    sale_links = SaleLink.objects.all()
    get_psuser(request)
    return render_to_response('sale_link.html', {'sale_links':sale_links, 'psuser':request._psuser}, context_instance = RequestContext(request))

# 保留
@ps_auth
def consult_manager(request):
    """分发客户"""
    consult_list = PSUser.objects.filter(Q(name_cn__in=['技术部', '李延']) | Q(Q(department__in = ['GROUP1', 'GROUP2', 'GROUP3']), ~Q(status = "离职")) | ~Q(now_load = 0)).order_by('department', 'position')
    sql = """
    select a.consult_id as consult_id, count(a.id) as shops from ncrm_subscribe a join (
    select max(id) as id from ncrm_subscribe where (article_code ='ts-25811' or article_code= 'FW_GOODS-1921400') and consult_id is not null and start_date<=current_date group by shop_id
    ) b on a.id=b.id where a.end_date>current_date group by a.consult_id;
    """
    inservice_count_dict = dict(execute_query_sql_return_tuple(sql))
    for consult in consult_list:
        consult.inservice_count = inservice_count_dict.get(consult.id, 0)
        consult.expired_count = consult.now_load - consult.inservice_count
        if consult.position not in ['COMMANDER', 'CONSULT', 'CONSULTLEADER'] or consult.status == '离职':
            consult.is_invalid = True
        consult.reserved_count = 0 # 保留客户数
        consult.to_distribute_count = 0 # 优先剔除客户数
        sp_group = ClientGroup.objects.filter(create_user = consult, group_type__in = [1, 2])
        for obj in sp_group:
            try:
                id_list = eval(obj.id_list)
                if type(id_list) == list and id_list:
                    if obj.group_type == 1:
                        consult.reserved_count = len(id_list)
                    elif obj.group_type == 2:
                        consult.to_distribute_count = len(id_list)
            except:
                pass
    return render_to_response('consult_manager.html', {'consult_list':consult_list, 'user':get_psuser(request)}, context_instance = RequestContext(request))

@ps_auth
def short_message_manage(request):
    """短信管理"""
    sm_list = list(sm_coll.find({}, {'filter_str':False, 'black_list':False}).sort('create_time', -1).limit(100)) # 目前只显示最近100条，后续有需求再分页
    for msg in sm_list:
        msg['id'] = msg['_id']
        msg['condition'] = json.dumps(msg.get('condition', {}))
    return render_to_response('short_message_manage.html', {'sm_list':sm_list}, context_instance = RequestContext(request))

@ps_auth
def export_customer(request):
    if request.method == 'GET':
        response = export_excel('客户列表', [{'key':'id', 'name':'店铺id'}, {'key':'name', 'name':'店铺名称'}, {'key':'qq', 'name':'qq'}, {'key':'ww', 'name':'ww'}])
        return response
    else:
        return None

@ps_auth
def strategy_cfg(request, template = 'strategy_cfg.html'):
    stg_cfgs = StrategyConfig.objects.all().order_by('name')
    stg_cfg_list = [sc for sc in stg_cfgs]
    stg_cfg_list.append(StrategyConfig(name = '添加配置'))
    cmd_cfgs = CommandConfig.objects.all().order_by('name')
    cmd_cfg_list = [cc for cc in cmd_cfgs]
    cmd_cfg_list.append(CommandConfig(name = '添加配置'))
    adg_cmd_dict = get_methods_8class(AdgroupDryRun)
    return render_to_response(template, {'stg_cfg_list': stg_cfg_list, 'adg_cmd_dict': adg_cmd_dict,
                                         'cmd_cfg_list': cmd_cfg_list}, context_instance = RequestContext(request))

# 首页广告管理（通用）
@ps_auth
def main_ad_manage(request):
    '''活动推广页管理 add by tianxiaohe 20150909'''
    result_list = main_ad_coll.find().sort([('_id', -1)])
    main_ad_list = []
    for result in result_list:
        data = { "a_id":result.get('_id', -1),
                 "ad_position":dict(MainAd.AD_POSITION_CHOICES).get(result.get('ad_position'))[0],
                 "ad_title":result.get('ad_title', ''),
                 "ad_display":MainAd.DISPLAY_CHOICES[result.get('ad_display', 0)][1],
                 "ad_start_time":datetime_2string(result.get('ad_start_time'), '%Y-%m-%d %H:%M'),
                 "ad_end_time":datetime_2string(result.get('ad_end_time'), '%Y-%m-%d %H:%M'),
                 "ad_weight":result.get('ad_weight', 0),
                 "ad_frequency":MainAd.AD_FREQUENCY_CHOICES[int(result.get('ad_frequency')) - 1][1] if result.get('ad_frequency') else '系统默认',
                 "ad_show_times":result.get('ad_show_times', 0),
                 "ad_click_times":result.get('ad_click_times', 0),
                 "ad_ctr":'%.2f' % ((result.get('ad_click_times', 0) / float(result.get('ad_show_times'))) * 100) if result.get('ad_show_times') else "0.00",
                 "ad_updater":result.get('ad_updater', ''),
                 "ad_update_time":result.get('ad_update_time', ''),
                 "ad_checker":result.get('ad_checker', 0),
                 "ad_check_time":result.get('ad_check_time', '')
        }
        try:
            current_date = datetime.datetime.now()
            if not result.get('ad_display', 0) \
                    or current_date < result.get('ad_start_time') \
                    or current_date > result.get('ad_end_time'):
                data['ad_status'] = '已屏蔽'
            else:
                data['ad_status'] = MainAd.STATUS_CHOICES[result.get('ad_status', 2)][1]
        except Exception, e:
            log.error('main_ad_manage error, e=%s' % (e))
            data['ad_status'] = '已屏蔽'

        main_ad_list.append(data)
    return render_to_response('main_ad_manage.html', {'ad_positions':MainAd.AD_POSITION_CHOICES, 'main_ad_list':main_ad_list}, context_instance = RequestContext(request))

# 创建广告
@ps_auth
def create_main_ad(request):
    ad_position = int(request.GET.get('ad_position', 1)) - 1
    return render_to_response('edit_main_ad.html', {'ad_positions':MainAd.AD_POSITION_CHOICES,
                                                    'edit_form':MainAd.AD_POSITION_CHOICES[ad_position][0] + "_form.html",
                                                    'ad_position':MainAd.AD_POSITION_CHOICES[ad_position][1][0],
                                                    'ad_levels':MainAd.LEVEL_CHOICES,
                                                    'current_time':datetime_2string(datetime.datetime.now(), "%Y-%m-%d %H:%M"),
                                                    'ad_user_types':MainAd.USER_TYPE_CHOICES,
                                                    'ad_frequencys':MainAd.AD_FREQUENCY_CHOICES, }, context_instance = RequestContext(request))

# 修改广告
@ps_auth
def update_main_ad(request):
    a_id = int(request.GET.get('id', -1))
    main_ad = main_ad_coll.find_one({"_id": a_id})
    # 该广告未发布，且当前用户拥有发布权限，则需显示发布按钮
    ad_position_dict = dict(MainAd.AD_POSITION_CHOICES)
    check_limit = True if request.session.get('psuser_dept') in ad_position_dict[main_ad.get('ad_position')][1]  \
                          and not main_ad.get('ad_checker', 0) else False
    main_ad['ad_start_time'] = datetime_2string(main_ad.get('ad_start_time'), '%Y-%m-%d %H:%M')
    main_ad['ad_end_time'] = datetime_2string(main_ad.get('ad_end_time'), '%Y-%m-%d %H:%M')

    put_out = True if main_ad.get('ad_status', 0) == 1 else False
    return render_to_response('edit_main_ad.html', {'ad_positions': MainAd.AD_POSITION_CHOICES,
                                                    'edit_form': main_ad.get('ad_position') + "_form.html",
                                                    'a_id': main_ad.get('_id'),
                                                    'check_limit': check_limit,
                                                    'put_out': put_out,
                                                    'ad_position': ad_position_dict[main_ad.get('ad_position')][0],
                                                    'ad_levels': MainAd.LEVEL_CHOICES,
                                                    'current_time': datetime_2string(datetime.datetime.now(), "%Y-%m-%d %H:%M"),
                                                    'main_ad': main_ad,
                                                    'ad_user_types': MainAd.USER_TYPE_CHOICES,
                                                    'ad_frequencys': MainAd.AD_FREQUENCY_CHOICES, }, context_instance = RequestContext(request))

# 工作提醒
@ps_auth
def work_reminder(request):
    query = {}
    start_time = request.GET.get('start_time', '')
    if start_time:
        try:
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
        except:
            pass
        else:
            query['create_time'] = {'$gte':start_time}

    end_time = request.GET.get('end_time', '')
    if end_time:
        try:
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(days = 1)
        except:
            pass
        else:
            temp_dict = query.setdefault('create_time', {})
            temp_dict['$lt'] = end_time

    try:
        psuser_id = int(request.GET['server_id'])
    except:
        psuser_id = ''
    else:
        psuser_type = request.GET.get('psuser_type', '')
        if psuser_type == '1':
            query['sender_id'] = psuser_id
        elif psuser_type == '2':
            query['receiver_id'] = psuser_id
        else:
            query['$or'] = [{'sender_id':psuser_id}, {'receiver_id':psuser_id}]

    department = request.GET.get('department', '')
    if department:
        query['department'] = department
    position_type = request.GET.get('position_type', '')
    position_dict = {'1':['SELLER', 'SALELEADER'], '2':['TPAE', 'TPLEADER'], '3':['RJJH', 'RJJHLEADER'], '4':['CONSULT', 'CONSULTLEADER']}
    if position_type and position_type in position_dict:
        query['position'] = {'$in':position_dict[position_type]}
    try:
        handle_status = int(request.GET['handle_status'])
    except:
        pass
    else:
        query['handle_status'] = handle_status

    reminder_list = list(reminder_coll.find(query).sort('create_time', -1))
    # 加载员工信息
    psuser_name_dict = dict(PSUser.objects.values_list('id', 'name_cn'))
    psuser_name_dict[0] = '系统'
    handle_status_dict = {-1:'未处理', 1:'已处理'}
    for reminder in reminder_list:
        reminder['id'] = reminder['_id']
        reminder['sender_name'] = psuser_name_dict.get(reminder['sender_id'], '无名')
        reminder['receiver_name'] = psuser_name_dict.get(reminder['receiver_id'], '无名')
        reminder['handle_status_cn'] = handle_status_dict.get(reminder['handle_status'], '')
    return render_to_response('work_reminder.html', {'reminder_list':reminder_list, 'psuser_name':psuser_name_dict.get(psuser_id, '')}, context_instance = RequestContext(request))

# 每日用户登录信息
@ps_auth
def login_users(request):
    psuser_id = request.session.get('psuser_id', 0)
    user_list = CacheAdpter.get(CacheKey.LOGIN_USERS % (psuser_id, datetime.date.today()), 'crm', {}).items() # 缓存值格式：{shop_id:[last_login, nick, phone, qq, is_hide, plateform_type]}
    user_list.sort(lambda x, y:cmp(y[1][0], x[1][0]))
    for _, login_info in user_list:
        if len(login_info) > 5:
            login_info[5] = dict(PLATEFORM_TYPE_CHOICES).get(login_info[5], '')
    return render_to_response('login_users.html', {'user_list':user_list}, context_instance = RequestContext(request))

# 订单分析
@ps_auth
def subscribe_analyze(request):
    log.info('==========CRM=====START=====subscribe_analyze==========')
    start_date = request.GET.get('start_date', datetime.datetime.now().strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', datetime.datetime.now().strftime('%Y-%m-%d'))
    article = request.GET.get('article', '0')

    start_time = start_date + " 00:00:00"
    end_time = end_date + " 23:59:59"

    if article == '0':
        ARTICLE_LIST = ['FW_GOODS-1921400', 'ts-25811']

    if article == '1':
        ARTICLE_LIST = ['ts-25811']

    if article == '2':
        ARTICLE_LIST = ['FW_GOODS-1921400']

    # 新定数量、金额
    sql = 'select consult_id,item_code,sum(pay),count(*) from ncrm_subscribe where biz_type=1'

    sql += ' and create_time>="%s" and create_time<="%s"' % (start_time, end_time)

    sql += ' and article_code in ("%s") group by consult_id,item_code' % ('","'.join(ARTICLE_LIST))

    new_order_tuple = execute_query_sql_return_tuple(sql)

    # 续订数量、金额
    sql = 'select consult_id,item_code,sum(pay),count(*) from ncrm_subscribe where biz_type=2'

    sql += ' and create_time>="%s" and create_time<="%s"' % (start_time, end_time)

    sql += ' and article_code in ("%s") group by consult_id,item_code' % ('","'.join(ARTICLE_LIST))

    renew_order_tuple = execute_query_sql_return_tuple(sql)

    # 升级的订单
    sql = 'select create_time,shop_id,article_code,item_code,pay from ncrm_subscribe where biz_type=3'

    sql += ' and create_time>="%s" and create_time<="%s"' % (start_time, end_time)

    sql += ' and article_code in ("%s")' % ('","'.join(ARTICLE_LIST))

    upgrade_tuple = execute_query_sql_return_tuple(sql)

    upgrade_dict = {}

    for upgrade in upgrade_tuple:
        sql = "select consult_id,item_code,pay from ncrm_subscribe where id=(select id from ncrm_subscribe where create_time<'%s' and shop_id=%s and article_code='%s' and biz_type!=3 order by create_time desc limit 1)" % (upgrade[0], upgrade[1], upgrade[2])
        temp = execute_query_sql_return_tuple(sql)

        if temp:
            key = str(temp and temp[0][0] or '') + '__' + temp[0][1]
            if not upgrade_dict.has_key(key):
                upgrade_dict[key] = {'pay':0, 'count':0}

            upgrade_dict[key]['pay'] = upgrade_dict[key]['pay'] + temp[0][2]
            upgrade_dict[key]['count'] = upgrade_dict[key]['count'] + 1


    # 统一数据格式
    upgrade_list = []
    for temp in upgrade_dict:
        key_list = temp.split('__')
        subscribe_temp = (key_list[0], key_list[1], upgrade_dict[temp]['pay'], upgrade_dict[temp]['count'])
        upgrade_list.append(subscribe_temp)

    # 获取所有的psuser_id
    psuser_list = []
    for temp in list(new_order_tuple) + list(renew_order_tuple) + upgrade_list:
        if temp[0]:
            psuser_list.append(int(temp[0]))

    # 去重
    psuser_list = list(set(psuser_list))

    item_list = []
    new_total_dict, renew_total_dict, upgrade_total_dict = {}, {}, {}
    new_total_pay_dict, renew_total_pay_dict, upgrade_total_pay_dict = {}, {}, {}

    class R():
        pass

    # 挂载psuser
    result_list = []
    for p in psuser_list:
        r = R()
        r.result = {}
        r.psuser = PSUser.objects.get(id = p)
        result_list.append(r)

    for r in result_list:
        for n in new_order_tuple:
            if n[0] == r.psuser.id:
                if not r.result.has_key(n[1]):
                    r.result[n[1]] = {}
                    item_list.append(n[1])
                r.result[n[1]]['new_pay'] = n[2]
                r.result[n[1]]['new_count'] = n[3]
                new_total_dict[n[1]] = new_total_dict.get(n[1], 0) + n[3]
                new_total_pay_dict[n[1]] = new_total_pay_dict.get(n[1], 0) + n[2]

        for re in renew_order_tuple:
            if re[0] == r.psuser.id:
                if not r.result.has_key(re[1]):
                    r.result[re[1]] = {}
                    item_list.append(re[1])
                r.result[re[1]]['renew_pay'] = re[2]
                r.result[re[1]]['renew_count'] = re[3]
                renew_total_dict[re[1]] = renew_total_dict.get(re[1], 0) + re[3]
                renew_total_pay_dict[re[1]] = renew_total_pay_dict.get(re[1], 0) + re[2]

        for u in upgrade_list:
            if u[0] and (int(u[0]) == r.psuser.id):
                if not r.result.has_key(u[1]):
                    r.result[u[1]] = {}
                    item_list.append(u[1])
                r.result[u[1]]['upgrade_pay'] = u[2]
                r.result[u[1]]['upgrade_count'] = u[3]
                upgrade_total_dict[u[1]] = upgrade_total_dict.get(u[1], 0) + u[3]
                upgrade_total_pay_dict[u[1]] = upgrade_total_pay_dict.get(u[1], 0) + u[2]

    for r in result_list:
        for k, v in r.result.items():
            v['total_pay'] = v.get('new_pay', 0) + v.get('renew_pay', 0) + v.get('upgrade_pay', 0)
            v['total_count'] = v.get('new_count', 0) + v.get('renew_count', 0) + v.get('upgrade_count', 0)
            v['new_percent'] = '%.2f' % (v.get('new_count', 0) * 100.00 / new_total_dict.get(k, 1))
            v['renew_percent'] = '%.2f' % (v.get('renew_count', 0) * 100.00 / renew_total_dict.get(k, 1))
            v['upgrade_percent'] = '%.2f' % (v.get('upgrade_count', 0) * 100.00 / upgrade_total_dict.get(k, 1))

    summary = {
             'item_list':list(set(item_list)),
             'new_total_dict':new_total_dict,
             'new_total_pay_dict':new_total_pay_dict,
             'renew_total_dict':renew_total_dict,
             'renew_total_pay_dict':renew_total_pay_dict,
             'upgrade_total_dict':upgrade_total_dict,
             'upgrade_total_pay_dict':upgrade_total_pay_dict
             }

    log.info('==========CRM=====END=====subscribe_analyze==========')
    return render_to_response('subscribe_analyze.html', {'result_list':result_list, 'summary':summary, 'start_date':start_date, 'end_date':end_date, 'article':article}, context_instance = RequestContext(request))

# 用户反馈信息
@ps_auth
def feedback(request):
    query_dict = {}
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    try:
        if start_time:
            query_dict['create_time__gte'] = datetime.datetime.strptime(start_time, '%Y-%m-%d')
        if end_time:
            query_dict['create_time__lt'] = datetime.datetime.strptime(end_time, '%Y-%m-%d') + datetime.timedelta(days = 1)
        if not (start_time or end_time):
            query_dict['create_time__gte'] = date_2datetime(datetime.date.today() - datetime.timedelta(days = 60))
            start_time = query_dict['create_time__gte'].strftime('%Y-%m-%d')
    except:
        pass
    psuser_id = request.GET.get('server_id', '')
    if psuser_id:
        query_dict['consult_id'] = int(psuser_id)
    feedback_list = Feedback.objects.select_related('shop', 'consult')
    handle_status = request.GET.get('handle_status', '')
    if handle_status:
        if handle_status == '-1':
            query_dict['handle_status'] = -1
        else:
            feedback_list = feedback_list.exclude(handle_status = -1)
    feedback_list = feedback_list.filter(**query_dict)
    return render_to_response('feedback.html', {'feedback_list':feedback_list, 'start_time':start_time}, context_instance = RequestContext(request))

# 客户分类树
@ps_auth
def category_tree(request):
    myself = get_psuser(request)
    member_dict = {}
    member_list = PSUser.objects.filter(position__in=['CONSULT', 'RJJH', 'RJJHLEADER']).exclude(status='离职').only('id', 'name_cn', 'position', 'department')
    for obj in member_list:
        sub_dict = member_dict.setdefault(obj.department, {})
        if obj.position == 'CONSULT':
            sub_dict.setdefault('CONSULT', []).append((obj.id, obj.name_cn))
        elif obj.position == 'RJJH':
            sub_dict.setdefault('RJJH', []).append((obj.id, obj.name_cn))
        elif obj.position == 'RJJHLEADER':
            sub_dict.setdefault('RJJH', []).insert(0, (obj.id, obj.name_cn))
    psuser_id = int(request.GET.get('psuser_id', '').strip() or 0)
    if psuser_id:
        psuser = PSUser.objects.get(id=psuser_id)
    else:
        psuser = myself

    my_trees = TreeTemplate.query_trees_byuser(psuser)
    general_trees, custom_trees = [], []
    for tree in my_trees:
        if tree.tree_type == 'GENERAL':
            general_trees.append(tree)
        else:
            custom_trees.append(tree)
    all_cond_fields = [field.to_dict() for field in FieldManager.read_all_fields()]
    cat_count_dict = {}
    for cust in psuser.mycustomers_withcat:
        if cust.cat_id in cat_count_dict:
            cat_count_dict[cust.cat_id] += 1
        else:
            cat_count_dict[cust.cat_id] = 1
    none_cat_list = [(0, cat_count_dict.pop(0), '未划分类目')] if 0 in cat_count_dict else []
    cat_name_dict = Cat.get_cat_path_name(cat_count_dict.keys())
    cat_list = [(cat_id, cat_count, cat_name_dict.get(str(cat_id)) or '未收录此类目') for cat_id, cat_count in cat_count_dict.items()]
    cat_list.sort(lambda x, y: cmp(x[2], y[2]))
    cat_list = none_cat_list + cat_list

    return render_to_response('category_tree.html', {
        'psuser': psuser,
        'my_trees': my_trees,
        'general_trees': general_trees,
        'custom_trees': custom_trees,
        'all_cond_fields': json.dumps(all_cond_fields),
        'cat_list': cat_list,
        'member_dict': member_dict,
        # 'has_extra_perms': 1 if 'B' in request.session['perms'] or ('1' in request.session['perms'] and psuser.department == request.session['psuser_dept']) else 0,
        'has_extra_perms': 1 if 'B' in myself.perms or (('1' in myself.perms or myself.position == 'RJJHLEADER') and psuser.department == myself.department) else 0,
    }, context_instance=RequestContext(request))

# 计划树
@ps_auth
def plan_tree(request):
    psuser_id = int(request.GET.get('psuser_id', '').strip() or 0)
    if psuser_id:
        psuser = PSUser.objects.get(id=psuser_id)
    else:
        psuser = get_psuser(request)
    my_trees = PlanTree.query_trees_byuser(psuser)
    all_cond_fields = [field.to_dict() for field in FieldManager.read_all_fields()]
    member_dict = {}
    member_list = PSUser.objects.filter(position='CONSULT').exclude(status='离职').only('id', 'name_cn', 'position', 'department')
    for obj in member_list:
        member_dict.setdefault(obj.department, []).append((obj.id, obj.name_cn))

    return render_to_response('plan_tree.html', {
        'psuser': psuser,
        'my_trees': my_trees,
        'all_cond_fields': json.dumps(all_cond_fields),
        'member_dict': member_dict,
        'has_extra_perms': 1 if 'B' in request.session['perms'] or ('1' in request.session['perms'] and psuser.department == request.session['psuser_dept']) else 0,
        }, context_instance=RequestContext(request))

# 编辑客户分类树
@ps_auth
def edit_category_tree(request):
    return render_to_response('edit_category_tree.html', {
                                                          'psuser': get_psuser(request),
                                                          'all_cond_fields': [field.to_dict() for field in FieldManager.read_all_fields()]
                                                          }, context_instance=RequestContext(request))

# 编辑计划树
@ps_auth
def edit_plan_tree(request):
    return render_to_response('edit_plan_tree.html', {
        'psuser': get_psuser(request),
        'all_cond_fields': [field.to_dict() for field in FieldManager.read_all_fields()]
    }, context_instance = RequestContext(request))

@ps_auth
def bulk_optimize(request):
    log.info('==========CRM=====START=====bulk_optimize==========')

    node_path = request.GET.get('node_path', None)
    shop_id = int(request.GET.get('shop_id', 0))
    value_type = request.GET.get('value_type', '')

    if node_path:
        psuser = get_psuser(request)
        shop_id_list = read_tree_branch(node_path, psuser)
    elif shop_id:
        shop_id_list = [shop_id]
    elif value_type == 'shop_id_list':
        if request.method == 'POST':
            shop_id_list = json.loads(request.POST.get('shop_id_list'))
            shop_id_list = [int(temp_shop_id) for temp_shop_id in shop_id_list]
        else:
            shop_id_list = []
    else:
        shop_id_list = []
    customers = Customer.objects.filter(shop_id__in = shop_id_list).only('shop_id', 'nick')

    downloaders = Downloader.objects.filter(shop_id__in = shop_id_list)
    check_rpt_dict = {dl.shop_id: dl.check_todayrpt_isok() for dl in downloaders}

    opted_shopid_list = UserOptimizeRecord.get_opted_shop_list(shop_id_list)
    camp_list = Campaign.objects.filter(shop_id__in = shop_id_list, online_status = 'online').values_list('campaign_id')
    adg_cur = adg_coll.find({'shop_id': {'$in': shop_id_list}, 'online_status': 'online', 'mnt_type': {'$gt': 0}}, {'shop_id': 1, 'campaign_id': 1})
    mnt_shopid_list = [adg['shop_id'] for adg in adg_cur if adg['campaign_id'] in camp_list]
    mnt_shopid_list = list(set(mnt_shopid_list))

    unopt_shopid_list = []
    customer_dict = {'waiting_opt': {'rpt_ok': [], 'rpt_failed': []},
                     'cannot_opt': {'has_opted': [], 'no_mnt_adg': []}
                     }
    for customer in customers:
        shop_id = customer.shop_id
        if shop_id in opted_shopid_list:
            customer_dict['cannot_opt']['has_opted'].append(customer)
        elif shop_id not in mnt_shopid_list:
            customer_dict['cannot_opt']['no_mnt_adg'].append(customer)
        else:
            check_result = check_rpt_dict.get(shop_id, False)
            unopt_shopid_list.append(customer.shop_id)
            if check_result:
                customer_dict['waiting_opt']['rpt_ok'].append(customer)
            else:
                customer_dict['waiting_opt']['rpt_failed'].append(customer)
    total_opt_count = len(customer_dict['waiting_opt']['rpt_ok']) + len(customer_dict['waiting_opt']['rpt_failed'])

    stg_cfg_name_list = ['IncreaseClick', 'IncreaseCTR', 'ReducePPC', 'IncreaseCVR', 'PureAddWord', 'PureOptQscore']
    stg_cfgs = StrategyConfig.objects.filter(name__in = stg_cfg_name_list)
    for stg_cfg in stg_cfgs:
        detail_desc_list = []
        for kw_cmd_name in stg_cfg.kw_cmd_list:
            kw_cmd = CommandConfig.get_config(name = kw_cmd_name)
            detail_desc_list.append(kw_cmd.desc)
        for adg_cmd in stg_cfg.adg_cmd_list:
            if adg_cmd == 'add_word':
                detail_desc_list.append('加词')
            elif adg_cmd == 'optm_qscore':
                detail_desc_list.append('优化质量得分,(PC质量得分+移动质量得分*移动端折扣)/(1+移动端折扣)＜５, 且７天无转化，７天点击量少于10且小于宝贝的10%。最多删除20%个词，且不超过15个词')
        stg_cfg.detail_desc_list = detail_desc_list

    stg_cfg_list = [[obj.name, obj.desc, obj.detail_desc_list] for obj in stg_cfgs]
    stg_cfg_list.sort(key = lambda k: stg_cfg_name_list.index(k[0]))

    log.info('==========CRM=====END=====bulk_optimize==========')
    return render_to_response('ncrm_bulk_optimize.html',
                              {'customer_dict': customer_dict,
                               'stg_cfg_list': stg_cfg_list,
                               'total_opt_count': total_opt_count,
                               'unopt_shopid_list': json.dumps(unopt_shopid_list),
                               },
                              context_instance = RequestContext(request))

@ps_auth
def performance(request):
    date_month = request.GET.get('tj_month', datetime.datetime.today().strftime('%Y-%m'))
    psuser_id = request.session.get('psuser_id', 0)
    if not psuser_id:
        return
    perf_cfg = PerformanceConfig.get_cfg_8month(date_month = date_month)
    return render_to_response('performance.html', {'date_month': date_month, 'is_modify': False, 'perf_cfg': perf_cfg},
                              context_instance = RequestContext(request))

@ps_auth
def performance_income(request):
    if 'H' not in request.session['perms']:
        return render_to_limited(request, '亲，您没有权限查看该页面，请联系系统管理员！')
    today = datetime.datetime.today()
    date_month = request.GET.get('tj_month', today.strftime('%Y-%m'))
    is_modify = 'H' in request.session['perms'] and datetime.datetime.strptime(date_month, '%Y-%m') + datetime.timedelta(days = 48) >= today
    perf_cfg = PerformanceConfig.get_cfg_8month(date_month = date_month)
    cur_metric_dict = {scc.indicator_name: scc.multiplier for scc in perf_cfg.score_calc_cfg_list}
    all_metric_list = get_indicators_byposition()
    metric_list = []
    for metric in all_metric_list:
        metric_list.append({'name': metric.name, 'name_cn': metric.name_cn, 'is_use': metric.name in cur_metric_dict, 'multiplier': cur_metric_dict.get(metric.name, 1)})
    return render_to_response('performance_income.html', {'date_month': date_month, 'perf_cfg': perf_cfg, 'is_modify': is_modify, 'metric_list': metric_list}, context_instance = RequestContext(request))

@ps_auth
def approval_subscribe(request):
    psuser = get_psuser(request)
    if psuser.id in [519, 86]:  # 何涛 梅玲
        log.info('==========CRM=====START=====approval_subscribe==========')
        is_export = int(request.POST.get('is_export', 0))
        page_no = request.POST.get('page_no', 1)
        page_no = page_no and int(page_no) or 1
        pay_type_no = request.POST.get('pay_type_no', '').strip()
        subscribe_psuser_id = request.POST.get('subscribe_psuser_id', '')
        exclude_market_order = request.POST.get('exclude_market_order', '')
        approval_status = request.POST.get('approval_status', '')
        nick = request.POST.get('nick', '').strip()
        order_create_starttime = request.POST.get('order_create_starttime', '')
        order_create_endtime = request.POST.get('order_create_endtime', '')
        approval_starttime = request.POST.get('approval_starttime', '')
        approval_endtime = request.POST.get('approval_endtime', '')
        pay_min = request.POST.get('pay_min', '')
        pay_max = request.POST.get('pay_max', '')
        category_list = request.POST.getlist('category', [])
        pay_type_list = request.POST.getlist('pay_type', [])
        biz_type_list = request.POST.getlist('biz_type', [])

        if request.method != 'POST':
            approval_status = '0'
            today = datetime.datetime.now()
            order_create_starttime = datetime.datetime(today.year, today.month, 1).strftime('%Y-%m-%d')
            order_create_endtime = today.strftime('%Y-%m-%d')
            category_list = ['ztc', 'vip', 'rjjh', 'kcjl', 'qn', 'zz', 'zx', 'dyy', 'seo', 'kfwb', 'other', 'zttk', 'ztbd']
            pay_type_list = [1, 2, 3, 4, 5, 6]
            biz_type_list = [1, 2, 3, 4, 5, 6]

        query_dict = {}
        pay_type_query_dict1 = {}
        pay_type_query_dict2 = {}

        pay_type_list = [int(pt) for pt in pay_type_list]
        pay_type_query_dict1 = {'pay_type__in': pay_type_list}
        if 1 in pay_type_list:
            pay_type_query_dict2 = {'pay_type': None}

        query_dict.update({'category__in': category_list})

        biz_type_list = [int(bt) for bt in biz_type_list]
        query_dict.update({'biz_type__in': biz_type_list})

        if pay_type_no:
            query_dict.update({'pay_type_no__contains': pay_type_no})
        if subscribe_psuser_id:
            query_dict.update({'psuser': int(subscribe_psuser_id)})
        if approval_status:
            query_dict.update({'approval_status': int(approval_status)})
        if order_create_starttime:
            query_dict.update({'create_time__gte': datetime.datetime.strptime(order_create_starttime + ' 00:00:00', '%Y-%m-%d %H:%M:%S')})
        if order_create_endtime:
            query_dict.update({'create_time__lte': datetime.datetime.strptime(order_create_endtime + ' 23:59:59', '%Y-%m-%d %H:%M:%S')})
        if approval_starttime:
            query_dict.update({'approval_time__gte': datetime.datetime.strptime(approval_starttime + ' 00:00:00', '%Y-%m-%d %H:%M:%S')})
        if approval_endtime:
            query_dict.update({'approval_time__lte': datetime.datetime.strptime(approval_endtime + ' 23:59:59', '%Y-%m-%d %H:%M:%S')})
        if pay_min:
            query_dict.update({'pay__gte': int(float(pay_min) * 100)})
        if pay_max:
            query_dict.update({'pay__lte': int(float(pay_max) * 100)})

        if nick:
            if nick.isdigit():
                customer_list = list(Customer.objects.filter(shop_id = int(nick)))
            else:
                customer_list = list(Customer.objects.filter(nick__contains = nick))
            if customer_list:
                query_dict.update({'shop__in': customer_list})
            else:
                query_dict.update({'shop__in': [None]})

        if pay_type_query_dict2:
            qs = Subscribe.objects.select_related('psuser').filter(**query_dict).filter(Q(**pay_type_query_dict1) | Q(**pay_type_query_dict2)).order_by('create_time')
        else:
            qs = Subscribe.objects.select_related('psuser').filter(**query_dict).filter(**pay_type_query_dict1).order_by('create_time')
        if exclude_market_order:
            qs = qs.exclude(psuser = None)

        log.info('==========CRM=====END=====approval_subscribe==========')
        if not is_export:
            page_info, subscribe_list = pagination_tool(page = page_no, record = qs, page_count = 20)
            subscribe_id_list = [obj.id for obj in subscribe_list]
            contract_subscribe_id_list = ContractFile.objects.filter(subscribe_id__in = subscribe_id_list).values_list('subscribe_id', flat = True)
            myself = get_psuser(request)
            for obj in subscribe_list:
                obj.has_contract = obj.id in contract_subscribe_id_list
                obj.can_modify = obj.approval_status == 2 and myself.position == 'COMMANDER' and obj.psuser and myself.department == obj.psuser.department
            return render_to_response('approval_subscribe.html', {
                'page_info': page_info, 'subscribe_list': subscribe_list,
                'order_create_starttime': order_create_starttime,
                'order_create_endtime': order_create_endtime,
                'approval_status': approval_status,
                'pay_sum': sum([sub.pay for sub in qs]),
                'pay_count': len(qs),
                'category_list': category_list,
                'pay_type_list': pay_type_list,
                'biz_type_list': biz_type_list,
                }, context_instance = RequestContext(request))
        else:
            raise Http404
        # else:
        #     title = "进账审计"
        #     columns = [
        #         {'key': 'department', 'name': '签单人部门'},
        #         {'key': 'nick', 'name': '店铺名'},
        #         {'key': 'name_cn', 'name': '签单人'},
        #         {'key': 'biz_type', 'name': '新/续'},
        #         {'key': 'category', 'name': '版本'},
        #         {'key': 'create_time', 'name': '订购时间'},
        #         {'key': 'end_date', 'name': '结束日期'},
        #         {'key': 'pay', 'name': '实付'},
        #         {'key': 'pay_type', 'name': '付款方式'},
        #         {'key': 'pay_type_no', 'name': '付款信息'},
        #         {'key': 'approval_status', 'name': '审批状态'},
        #         ]
        #     data_list = []
        #     try:
        #         for obj in qs:
        #             data_list.append({
        #                 'nick': obj.shop.nick,
        #                 'department': obj.psuser and obj.psuser.get_department_display() or '系统',
        #                 'name_cn': obj.psuser and obj.psuser.name_cn or '系统',
        #                 'biz_type': obj.get_biz_type_display(),
        #                 'category': obj.get_category_display(),
        #                 'create_time': obj.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        #                 'end_date': obj.end_date.strftime('%Y-%m-%d'),
        #                 'pay': obj.pay / 100.0,
        #                 'pay_type': obj.pay_type and obj.get_pay_type_display() or '淘宝后台付款',
        #                 'pay_type_no': obj.pay_type_no,
        #                 'approval_status': obj.get_approval_status_display()
        #                 })
        #     except Exception, e:
        #         log.exception(e)
        #     response = export_excel(title = title, columns = columns, data_list = data_list)
        #     return response
    else:
        raise Http404

# 度量统计
@ps_auth
def metric_statistic_old(request):
    td = date_2datetime(datetime.date.today())
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    if not start_time:
        start_time = td - datetime.timedelta(days = 7)
    else:
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    if not end_time:
        end_time = td
    else:
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d')
    period = request.GET.get('period', 'day')
    period_list = get_split_cycle()
    psuser_id_list = request.GET.getlist('server_id', [])
    if psuser_id_list:
        psuser_id_list = [int(_id) for _id in psuser_id_list]
        psuser_list = PSUser.objects.filter(id__in = psuser_id_list)
    else:
        psuser = get_psuser(request)
        psuser_id_list = [psuser.id]
        psuser_list = [psuser]
    position_type = request.GET.get('position_type', '4')
    # valid_metric_list = ['renew_order_pay', 'real_renew_order_pay', 'unsubscribe_pay']
    # metric_list = request.GET.getlist('metric', valid_metric_list)
    metric_list = request.GET.getlist('metric', [])
    valid_metric_list = PerformanceConfig.get_metric_indicator_8date(start_time, end_time)
    valid_metric_list += ['renew_order_pay', 'real_renew_order_pay', 'unsubscribe_pay', 'serving_people_count']
    all_metric_info = [x.to_dict() for x in get_indicators_byposition() if x.name in valid_metric_list or x.name in metric_list]
    metric_dict = {}
    temp_list = []
    for metric in all_metric_info:
        if metric['val_type'] == 'rate':
            metric_dict[metric['name']] = metric['name_cn'] + '（%）'
        else:
            metric_dict[metric['name']] = metric['name_cn']
        if metric_list:
            if metric['name'] in metric_list:
                metric['default_indicator'] = True
            else:
                metric['default_indicator'] = False
        else:
            if metric['default_indicator']:
                temp_list.append(metric['name'])
    if temp_list:
        metric_list = temp_list

    # 获取部门员工信息
    position_type_dict = {
                        'SELLER':'1',
                        'SALELEADER':'1',
                        'TPAE':'2',
                        'TPLEADER':'2',
                        'RJJH':'3',
                        'RJJHLEADER':'3',
                        'CONSULT':'4',
                        'CONSULTLEADER':'4',
                        }
    dept_list = GROUPS
    dept_user_list = [{'dept_name':dict(PSUser.DEPARTMENT_CHOICES)[dept], 'psuser_list':[]} for dept in dept_list]
    all_psuser_list = PSUser.objects.filter(department__in = dept_list).exclude(status = '离职').order_by('-position')
    for psuser in all_psuser_list:
        psuser.position_type = position_type_dict.get(psuser.position, '0')
        if psuser.id in psuser_id_list:
            psuser.is_checked = True
        else:
            psuser.is_checked = False
        dept_user_list[dept_list.index(psuser.department)]['psuser_list'].append(psuser)
    # 度量数据
#     statistic_data = [
#                    {'name_cn':'钟超', 'metric_list':[{'name_cn':'订单金额', 'data':[100, 25, 25, 25, 25, 25]}, {'name_cn':'订单笔数', 'data':[100, 25, 25, 25, 25, 25]}]},
#                    {'name_cn':'钟超', 'metric_list':[{'name_cn':'订单金额', 'data':[100, 25, 25, 25, 25, 25]}, {'name_cn':'订单笔数', 'data':[100, 25, 25, 25, 25, 25]}]},
#                    {'name_cn':'总计', 'metric_list':[{'name_cn':'订单金额', 'data':[100, 25, 25, 25, 25, 25]}, {'name_cn':'订单笔数', 'data':[100, 25, 25, 25, 25, 25]}]},
#                    ]
    refresh_flag = request.GET.get('refresh_flag', '')
    column_list, statistic_data = get_performance_statistics([start_time, end_time], period, metric_list, psuser_list, bool(refresh_flag))
    return render_to_response('metric_statistic.html', {
                                                        'start_time':start_time,
                                                        'end_time':end_time,
                                                        'all_metric_info':all_metric_info,
                                                        'dept_user_list':dept_user_list,
                                                        'statistic_data':statistic_data,
                                                        'period':period,
                                                        'period_list':period_list,
                                                        'column_list':column_list,
                                                        'position_type':position_type,
                                                        'has_export_perm':'2' in get_psuser(request).perms,
                                                        # 'valid_metric_list':valid_metric_list,
                                                        }, context_instance = RequestContext(request))

# 度量统计
@ps_auth
def metric_statistic(request):
    log.info('==========CRM=====START=====metric_statistic==========')
    today = date_2datetime(datetime.date.today())
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    if not start_time:
        start_time = today - datetime.timedelta(days = 7)
    else:
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    if not end_time:
        end_time = today
    else:
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d')
    period = request.GET.get('period', 'day')
    period_list = get_split_cycle()
    xfgroup_id_list = request.GET.getlist('server_id', [])
    xfgroup_list = []
    if xfgroup_id_list:
        xfgroup_id_list = [int(_id) for _id in xfgroup_id_list]
        xfgroup_list = XiaoFuGroup.objects.filter(id__in = xfgroup_id_list)
    else:
        psuser = get_psuser(request)
        xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = psuser.id)
        if xfgroup:
            xfgroup_list = [xfgroup]
            xfgroup_id_list = [obj.id for obj in xfgroup_list]
    # valid_metric_list = ['renew_order_pay', 'real_renew_order_pay', 'unsubscribe_pay']
    # metric_list = request.GET.getlist('metric', valid_metric_list)
    metric_list = request.GET.getlist('metric', [])
    valid_metric_list = PerformanceConfig.get_metric_indicator_8date(start_time, end_time)
    valid_metric_list += ['renew_order_pay', 'real_renew_order_pay', 'unsubscribe_pay', 'market_unsubscribe_pay']
    all_metric_info = [x.to_dict() for x in get_indicators_byposition() if x.name in valid_metric_list or x.name in metric_list]
    metric_dict = {}
    temp_list = []
    for metric in all_metric_info:
        if metric['val_type'] == 'rate':
            metric_dict[metric['name']] = metric['name_cn'] + '（%）'
        else:
            metric_dict[metric['name']] = metric['name_cn']
        if metric_list:
            if metric['name'] in metric_list:
                metric['default_indicator'] = True
            else:
                metric['default_indicator'] = False
        else:
            if metric['default_indicator']:
                temp_list.append(metric['name'])
    if temp_list:
        metric_list = temp_list

    dept_list = GROUPS
    dept_xfgroup_list = [{'dept_name':dict(PSUser.DEPARTMENT_CHOICES)[dept], 'xfgroup_list':[]} for dept in dept_list]
    all_xfgroup_list = XiaoFuGroup.get_involved_xfgroup(start_time, end_time)
    for xfgroup in all_xfgroup_list:
        if xfgroup.id in xfgroup_id_list:
            xfgroup.is_checked = True
        else:
            xfgroup.is_checked = False
        dept_xfgroup_list[dept_list.index(xfgroup.department)]['xfgroup_list'].append(xfgroup)
    # 度量数据

    refresh_flag = request.GET.get('refresh_flag', '')
    column_list, statistic_data = get_performance_statistics([start_time, end_time], period, metric_list, xfgroup_list, bool(refresh_flag))

    log.info('==========CRM=====END=====metric_statistic==========')
    return render_to_response('metric_statistic.html', {
        'start_time': start_time,
        'end_time': end_time,
        'all_metric_info': all_metric_info,
        'dept_xfgroup_list': dept_xfgroup_list,
        'statistic_data': statistic_data,
        'period': period,
        'period_list': period_list,
        'column_list': column_list,
        'has_export_perm': '2' in get_psuser(request).perms,
        # 'valid_metric_list':valid_metric_list,
        }, context_instance = RequestContext(request))

# # 人机度量统计
# @ps_auth
# def metric_statistic_rjjh(request):
#     # 获取度量维度
#     metric_choices = MetricsManager.METRIC_DICT.values()
#     metric_choices.sort(lambda x, y: cmp(x.snapshot_order, y.snapshot_order))
#     # 获取人员部门岗位信息
#     psuser_choices = []
#     psuser_data = {}
#     for obj in PSUser.objects.filter(position__in=['TPAE', 'TPLEADER', 'RJJH', 'RJJHLEADER'], department__in=GROUPS).exclude(status='离职').only('id', 'name_cn', 'position', 'department'):
#         if obj.position in ('RJJH', 'RJJHLEADER'):
#             position = '人机'
#         else:
#             position = '操作'
#         psuser_data.setdefault(position, {}).setdefault(obj.department, []).append(obj)
#     for position, info in psuser_data.items():
#         temp_list = info.items()
#         temp_list.sort(lambda x, y: cmp(x[0], y[0]))
#         for department, user_list in temp_list:
#             user_list.sort(lambda x, y: cmp(y.position, x.position))
#             psuser_choices.append({
#                 'department_position_cn': '%s - %s' % (dict(PSUser.DEPARTMENT_CHOICES).get(department, department), position),
#                 'user_list': user_list,
#             })
#
#     return render_to_response('metric_statistic_rjjh.html', {
#         'metric_choices': metric_choices,
#         'psuser_choices': psuser_choices,
#         }, context_instance=RequestContext(request))

# 人机度量统计
@ps_auth
def metric_statistic_rjjh(request):
    # 获取度量维度
    metric_choices = MetricsManager.METRIC_DICT.values()
    metric_choices.sort(lambda x, y: cmp(x.snapshot_order, y.snapshot_order))
    # 获取人员部门岗位信息
    department_dict = dict(PSUser.DEPARTMENT_CHOICES)
    department_psusers = {}
    for obj in PSUser.objects.filter(department__in=OPERATION_GROUPS).exclude(status='离职').only('id', 'name_cn', 'perms', 'department').order_by('-perms'):
        department_psusers.setdefault(obj.department, []).append(obj)
    psuser_choices = department_psusers.items()
    psuser_choices.sort(lambda x, y: cmp(x[0], y[0]))
    psuser_choices = [(department_dict.get(department, department), user_list) for department, user_list in psuser_choices]

    return render_to_response('metric_statistic_rjjh.html', {
        'metric_choices': metric_choices,
        'psuser_choices': psuser_choices,
        }, context_instance=RequestContext(request))

@ps_auth
def adgroup_top(request):
    log.info('==========CRM=====START=====adgroup_top==========%s' % request.session.get('psuser_name', 'Unknown'))
    adg_list = []
    item_prdtword_list = []
    if request.method == 'POST':
        cat_id = request.POST.get('cat_path_id', '')
        if cat_id:
            product_word = request.POST.get('product_word', '').strip()
            rpt_day = int(request.POST['rpt_day'])
            avg_pay_min = request.POST.get('avg_pay_min', '')
            cost_min = request.POST.get('cost_min', '')
            cost_max = request.POST.get('cost_max', '')
            avg_pay_max = request.POST.get('avg_pay_max', '')
            paycount_min = request.POST.get('paycount_min', '')
            paycount_max = request.POST.get('paycount_max', '')
            ctr_min = request.POST.get('ctr_min', '')
            ctr_max = request.POST.get('ctr_max', '')
            cnv_min = request.POST.get('cnv_min', '')
            cnv_max = request.POST.get('cnv_max', '')
            roi_min = request.POST.get('roi_min', '')
            roi_max = request.POST.get('roi_max', '')
            exclude_shop_id = None
            exclude_nick = request.POST.get('exclude_nick', '')
            if exclude_nick:
                if exclude_nick.isdigit():
                    exclude_shop_id = int(exclude_nick)
                else:
                    exclude_shop_id_list = list(Customer.objects.filter(nick = exclude_nick).values_list('shop_id', flat=True))
                    if exclude_shop_id_list:
                        exclude_shop_id = exclude_shop_id_list[0]
            # print product_word, avg_pay_min, avg_pay_max, cost_min, cost_max, ctr_min, ctr_max, cnv_min, cnv_max, roi_min, roi_max

            item_count_limit = 50000
            sub_cat_list = Cat.get_all_subcats(cat_id = int(cat_id))
            sub_cat_list.insert(0, int(cat_id))
            item_query_dict = {'cat_id': {'$in': sub_cat_list}}
            if product_word:
                item_query_dict.update({'title': re.compile(product_word)})
            if exclude_shop_id:
                item_query_dict.update({'shop_id':{'$ne':exclude_shop_id}})
            item_cur = item_coll.find(item_query_dict, {'_id': 1}).limit(item_count_limit)
            item_id_list = [item['_id'] for item in item_cur]
            adg_cur = adg_coll.find({'item_id': {'$in': item_id_list}}, {'_id': 1})
            adg_id_list = [adg['_id'] for adg in adg_cur]
            base_query = {'source':-1, 'search_type':-1,
                          'date': {'$gte': date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_day))},
                          'adgroup_id': {'$in': adg_id_list}
                          }

            rpt_query_dict = {}
            rpt_key_cfg = {'avg_pay': 100, 'cost': 100, 'ctr': 0.01, 'cnv': 0.01, 'roi': 1, 'paycount': 1}
            for rpt_key, num in rpt_key_cfg.items():
                min_value = eval('%s_min' % rpt_key)
                max_value = eval('%s_max' % rpt_key)
                temp_dict = {}

                if min_value:
                    temp_dict.update({'$gte': float(min_value) * num})
                if max_value:
                    temp_dict.update({'$lte': float(max_value) * num})
                if temp_dict:
                    rpt_query_dict.update({rpt_key: temp_dict})

            pipeline = [{'$match': base_query},
                        {'$group': {'_id': '$adgroup_id',
                                    'impressions': {'$sum': '$impressions'},
                                    'click': {'$sum': '$click'},
                                    'cost': {'$sum': '$cost'},
                                    'rpt_days': {'$sum': 1},
                                    'carttotal': {'$sum': '$carttotal'},
                                    'directpay':{'$sum':'$directpay'},
                                    'indirectpay':{'$sum':'$indirectpay'},
                                    'directpaycount':{'$sum':'$directpaycount'},
                                    'indirectpaycount':{'$sum':'$indirectpaycount'},
                                    'favitemcount':{'$sum':'$favitemcount'},
                                    'favshopcount':{'$sum':'$favshopcount'},
                                    'shop_id': {'$first': '$shop_id'},
                                    }
                         },
                        {'$match': {'$or': [{'directpaycount': {'$gt': 0}},
                                            {'indirectpaycount': {'$gt': 0}}
                                            ]
                                    }
                         },
                        {'$project': {'pay': {'$add': ['$directpay', '$indirectpay']},
                                      'paycount': {'$add': ['$directpaycount', '$indirectpaycount']},
                                      'favcount': {'$add': ['$favitemcount', '$favshopcount']},
                                      'impressions': 1,
                                      'carttotal': 1,
                                      'click': 1,
                                      'cost': 1,
                                      '_id': 1,
                                      'shop_id': 1,
                                      },
                         },
                        {'$project': {'ctr': {'$cond': [{'$eq': ['$impressions', 0]}, 0, {'$divide': ['$click', '$impressions']}]},
                                      'cnv': {'$cond': [{'$eq': ['$click', 0]}, 0, {'$divide': ['$paycount', '$click']}]},
                                      'roi': {'$cond': [{'$eq': ['$cost', 0]}, 0, {'$divide': ['$pay', '$cost']}]},
                                      'ppc': {'$cond': [{'$eq': ['$click', 0]}, 0, {'$divide': ['$cost', '$click']}]},
                                      'avg_pay': {'$cond': [{'$eq': ['$paycount', 0]}, 0, {'$divide': ['$pay', '$paycount']}]},
                                      'pay': 1,
                                      'paycount': 1,
                                      'favcount': 1,
                                      'impressions': 1,
                                      'carttotal': 1,
                                      'click': 1,
                                      'cost': 1,
                                      'adgroup_id': '$_id',
                                      'shop_id': 1,
                                      'paycount_roi': {'$multiply': [{'$add': ['$paycount', {'$multiply': ['$carttotal', 0.5]}]},
                                                                     {'$cond': [{'$eq': ['$cost', 0]}, 0, {'$divide': ['$pay', '$cost']}]}]}
                                      }
                         },
                        ]
            if rpt_query_dict:
                pipeline.append({'$match': rpt_query_dict})
            pipeline.append({'$sort': {'paycount_roi':-1}})
            pipeline.append({'$limit': 50})
            adg_rpt_list = Adgroup.Report._get_collection().aggregate(pipeline)['result']

            adg_id_list = [adg['adgroup_id'] for adg in adg_rpt_list]
            shop_id_list = [adg['shop_id'] for adg in adg_rpt_list]
            adgs = Adgroup.objects.filter(shop_id__in = shop_id_list, adgroup_id__in = adg_id_list)
            adg_dict = {obj.adgroup_id: obj for obj in adgs}
            item_id_list = [obj.item_id for obj in adgs]
            items = Item.objects.filter(shop_id__in = shop_id_list, item_id__in = item_id_list)
            item_dict = {obj.item_id: obj for obj in items}
            for adg_rpt in adg_rpt_list:
                adg = adg_dict.get(adg_rpt['adgroup_id'], None)
                item = item_dict.get(getattr(adg, 'item_id', None), None)
                if not item:
                    continue
                adg_list.append({'adgroup_id': adg_rpt['adgroup_id'],
                                 'shop_id': adg_rpt['shop_id'],
                                 'avg_pay': format(adg_rpt['avg_pay'] / 100.0, '.2f'),
                                 'cost': format(adg_rpt['cost'] / 100.0, '.2f'),
                                 'ppc': format(adg_rpt['ppc'] / 100.0, '.2f'),
                                 'pay': format(adg_rpt['pay'] / 100.0, '.2f'),
                                 'impressions': adg_rpt['impressions'],
                                 'click': adg_rpt['click'],
                                 'carttotal': adg_rpt['carttotal'],
                                 'paycount': adg_rpt['paycount'],
                                 'favcount': adg_rpt['favcount'],
                                 'roi': format(adg_rpt['roi'], '.2f'),
                                 'ctr': format(adg_rpt['ctr'] * 100.0, '.2f'),
                                 'cnv': format(adg_rpt['cnv'] * 100.0, '.2f'),
                                 'mnt_type': adg.mnt_type,
                                 'pic_url': item.pic_url,
                                 'item_id': item.item_id,
                                 'item_title': item.title,
                                 })
        item_prdtwords = request.POST.get('item_prdtwords')
        item_prdtword_list = item_prdtwords.split(',') if item_prdtwords else []
    log.info('==========CRM=====END=====adgroup_top==========')
    return render_to_response('adgroup_top.html', {'adg_list': adg_list, 'item_prdtword_list': item_prdtword_list}, context_instance = RequestContext(request))

@ps_auth
def upload_contract_file(request):
    is_create = False
    try:
        err_msg = ''
        file_obj = request.FILES['contract']
        subscribe_id = int(request.POST['subscribe_id'])
        # allow_file_type_list = ['application/pdf', 'application/msword', 'image/png', 'image/jpeg', 'image/gif', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if file_obj.size > 1024 * 1024 * 2: # 上传文件大小验证
            err_msg = '大小不能超过2M'
        # elif file_obj.content_type not in allow_file_type_list: # 上传文件类型验证
        #     err_msg = '只能上传PDF、word文档、图片'
        else:
            obj, is_create = ContractFile.objects.get_or_create(subscribe_id = subscribe_id)
            obj.file_name = file_obj.name
            obj.file_data = MySQLdb.Binary(file_obj.read())
            obj.modify_time = datetime.datetime.now()
            obj.save()
    except Exception, e:
        err_msg = '上传合同失败, 请注意文件名不要超过100个字符'
        if is_create:
            ContractFile.objects.filter(subscribe_id = subscribe_id).delete()
        log.error('upload_contract_file error, e=%s' % (e))
    return HttpResponse(json.dumps({'err_msg': err_msg}))

@ps_auth
def export_contract_file(request, subscribe_id):
    try:
        obj = ContractFile.objects.get(subscribe_id = int(subscribe_id))
    except Exception, e:
        raise e
    response = StreamingHttpResponse(obj.file_data)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename=%s' % (obj.file_name.decode('utf-8').encode('gb2312'))
    return response

@ps_auth
def operating_rpt(request):
    today = datetime.datetime.now()
    start_date = (today - datetime.timedelta(days = 8)).strftime('%Y-%m-%d')
    end_date = (today - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
    return render_to_response('operating_rpt.html', {
        'start_date': start_date,
        'end_date': end_date,
        "category_list": CATEGORY_CHOICES,
        'refund_style_list': Unsubscribe.PAY_TYPE_CHOICES,
    }, context_instance = RequestContext(request))

@ps_auth
def operating_rpt1(request):
    raise Http404
    today = datetime.datetime.now()
    start_date = (today - datetime.timedelta(days = 8)).strftime('%Y-%m-%d')
    end_date = (today - datetime.timedelta(days = 1)).strftime('%Y-%m-%d')
    tj_dpt_list = OPERATION_GROUPS + GROUPS
    dpt_choices = [(dpt, dict(PSUser.DEPARTMENT_CHOICES).get(dpt, dpt)) for dpt in tj_dpt_list]
    return render_to_response('operating_rpt1.html', {
        'start_date': start_date,
        'end_date': end_date,
        "category_list": CATEGORY_CHOICES,
        'refund_style_list': Unsubscribe.PAY_TYPE_CHOICES,
        'dpt_choices': dpt_choices,
    }, context_instance = RequestContext(request))

@ps_auth
def unsubscribe_manage(request):
    """退款审计"""
    log.info('==========CRM=====START=====unsubscribe_manage==========')
    is_export = int(request.POST.get('is_export', 0))
    if request.method == 'POST':
        nick = request.POST.get('nick', '').strip()
        creater_id = int(request.POST.get('creater_id', '') or 0)
        duty_user_id = int(request.POST.get('duty_user_id', '') or 0)
        category = request.POST.get('category', '')
        duty_dpt = request.POST.get('duty_dpt', '')
        reimburse_dpt = request.POST.get('reimburse_dpt', '')
        create_time_start = request.POST.get('create_time_start', '')
        if create_time_start:
            create_time_start = datetime.datetime.strptime(create_time_start, '%Y-%m-%d')
        create_time_end = request.POST.get('create_time_end', '')
        if create_time_end:
            create_time_end = datetime.datetime.strptime(create_time_end, '%Y-%m-%d') + datetime.timedelta(days = 1)
        refund_date_start = request.POST.get('refund_date_start', '')
        if refund_date_start:
            refund_date_start = datetime.datetime.strptime(refund_date_start, '%Y-%m-%d')
        refund_date_end = request.POST.get('refund_date_end', '')
        if refund_date_end:
            refund_date_end = datetime.datetime.strptime(refund_date_end, '%Y-%m-%d') + datetime.timedelta(days = 1)
        # start_date = request.POST.get('start_date', '')
        # if start_date:
        #     start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        # end_date = request.POST.get('end_date', '')
        # if end_date:
        #     end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days = 1)
        refund_style = int(request.POST.get('refund_style', '') or 0)
        # refund_type_list = request.POST.getlist('refund_type', [])
        # refund_type_list = [int(i) for i in refund_type_list]
        category_list = request.POST.getlist('category_list', [])
        refund_reason_list = request.POST.getlist('refund_reason', [])
        refund_reason_list = [int(i) for i in refund_reason_list]
        refund_info = request.POST.get('refund_info', '')
        status = int(request.POST.get('status', '') or 0)
        cashier_id = int(request.POST.get('cashier_id', '') or 0)
    else:
        create_time_end = date_2datetime(datetime.date.today() + datetime.timedelta(days = 1))
        create_time_start = create_time_end - datetime.timedelta(days = 7)
        nick = creater_id = duty_user_id = category = duty_dpt = reimburse_dpt = refund_style = status = cashier_id = refund_date_start = refund_date_end = refund_info = ''
        category_list = ['kcjl', 'rjjh', 'vip', 'qn', 'ztc', 'zz', 'zx', 'dyy', 'seo', 'kfwb', 'other']
        # refund_type_list = [0, 1, 2, 3, 4, 5]
        # refund_reason_list = [1, 2, 3, 4, 5, 6]
        # 退款原因
        refund_reason_list = [i[0] for i in Unsubscribe.REFUND_REASON_CHOICES]

    query = {'type':'unsubscribe'}
    if nick:
        if nick.isdigit():
            query['shop_id'] = int(nick)
        else:
            query['nick'] = re.compile(nick)
    if creater_id:
        query['psuser_id'] = creater_id
    if duty_user_id:
        query['$or'] = [{'saler_id': duty_user_id, 'saler_apportion': {'$gt': 0}}, {'server_id': duty_user_id, 'server_apportion': {'$gt': 0}}]
    if category:
        query['category'] = category
    if duty_dpt:
        query['duty_dpt'] = duty_dpt
    if reimburse_dpt:
        query['reimburse_dpt'] = reimburse_dpt
    if create_time_start:
        temp_dict = query.setdefault('create_time', {})
        temp_dict['$gte'] = create_time_start
    if create_time_end:
        temp_dict = query.setdefault('create_time', {})
        temp_dict['$lt'] = create_time_end
    if refund_date_start:
        temp_dict = query.setdefault('refund_date', {})
        temp_dict['$gte'] = refund_date_start
    if refund_date_end:
        temp_dict = query.setdefault('refund_date', {})
        temp_dict['$lt'] = refund_date_end
    # if start_date:
    #     temp_dict = query.setdefault('refund_date', {})
    #     temp_dict['$gte'] = start_date
    # if end_date:
    #     temp_dict = query.setdefault('refund_date', {})
    #     temp_dict['$lt'] = end_date
    if refund_style:
        query['refund_style'] = refund_style
    if refund_info:
        query['refund_info'] = re.compile(refund_info)
    # if len(refund_type_list)==0:
    #     query['refund_type'] = -1
    # elif len(refund_type_list)<6:
    #     query['refund_type'] = {'$in':refund_type_list}
    if len(category_list) == 0:
        query['category'] = -1
    elif len(category_list) < 11:
        query['category'] = {'$in':category_list}
    if len(refund_reason_list) == 0:
        query['refund_reason'] = -1
    # elif len(refund_reason_list) < 6:
    # 退款原因 搜索
    elif 1 <= len(refund_reason_list) < len(Unsubscribe.REFUND_REASON_CHOICES):
        query['refund_reason'] = {'$in': refund_reason_list}
    # elif len(refund_reason_list) > 1:
    #     query['$or'] = [{"refund_reason":{"$elemMatch":{"$in":refund_reason_list}}}, {"refund_reason":{"$in":refund_reason_list}}]
    if status:
        query['status'] = status
    if cashier_id:
        query['cashier_id'] = cashier_id
    unsub_result = list(event_coll.find(query))
    sub_id_list = list(set([obj['event_id'] for obj in unsub_result]))
    sub_dict = {obj.id:obj for obj in Subscribe.objects.filter(id__in = sub_id_list).only('id', 'create_time', 'pay', 'category', 'item_code')}
    unsubscribe_sum = 0
    psuser_dict = dict(PSUser.objects.values_list('id', 'name_cn'))
    result = []
    for unsub in unsub_result:
        if unsub['event_id'] in sub_dict:
            sub_obj = sub_dict[unsub['event_id']]
            unsub['id'] = unsub['_id']
            unsub['sub_create'] = sub_obj.create_time
            unsub['sub_pay'] = sub_obj.pay
            unsub['sub_category'] = sub_obj.get_category_display()
            unsub['sub_item_code'] = sub_obj.item_code
            unsub['refund_style_cn'] = dict(Unsubscribe.PAY_TYPE_CHOICES).get(unsub.get('refund_style'), '未知')

            # 退款原因 多选 判断是否是列表
            if(type(unsub.get('refund_reason', '')) == list):
                # resaon_cn = ''
                resaon_cn = []
                for resaon in unsub.get('refund_reason'):
                    # resaon_cn += dict(Unsubscribe.REFUND_REASON_CHOICES).get(int(resaon), '未知')
                    resaon_cn.append(str(resaon))
                unsub['refund_reason_cn'] = ', '.join(resaon_cn)
                # 转换
                refund_reason_int_list = [str(i) for i in unsub['refund_reason']]
                unsub['refund_reason'] = ','.join(refund_reason_int_list)
            else:
                # unsub['refund_reason_cn'] = dict(Unsubscribe.REFUND_REASON_CHOICES).get(unsub.get('refund_reason'), '未知')
                unsub['refund_reason_cn'] = unsub.get('refund_reason', '')

            # unsub['refund_type_cn'] = dict(Unsubscribe.REFUND_TYPE_CHOICES).get(unsub['refund_type'], '未知')
            unsub['creater_cn'] = psuser_dict.get(unsub['psuser_id'], '')
            unsub['saler_cn'] = psuser_dict.get(unsub.get('saler_id'), '市场')
            unsub['server_cn'] = psuser_dict.get(unsub.get('server_id'), '无')
            unsub['cashier_cn'] = psuser_dict.get(unsub.get('cashier_id'), '')
            unsub['status_cn'] = dict(Unsubscribe.REFUND_STATUS_CHOICES).get(unsub.get('status'), '未知')
            temp_list = unsub.get('refund_info', '').split('__', 1)
            if len(temp_list) == 2:
                unsub['refund_info'], unsub['receiver_cn'] = temp_list
            else:
                unsub['refund_info'] = ''
                unsub['receiver_cn'] = ''
            if duty_user_id:
                if unsub['saler_id'] == duty_user_id:
                    unsubscribe_sum += unsub['saler_apportion']
                if unsub['server_id'] == duty_user_id:
                    unsubscribe_sum += unsub['server_apportion']
            else:
                unsubscribe_sum += unsub['refund']
            result.append(unsub)
    log.info('==========CRM=====END=====unsubscribe_manage==========')
    myself = get_psuser(request)
    if not is_export:
        return render_to_response('unsubscribe_manage.html', {
            'result':result,
            'unsubscribe_sum':unsubscribe_sum,
            'can_modify':'B' in myself.perms,
            'myself':myself,
            'create_time_start':create_time_start and create_time_start.strftime('%Y-%m-%d'),
            'create_time_end':create_time_end and (create_time_end - datetime.timedelta(days = 1)).strftime('%Y-%m-%d'),
            'refund_date_start':refund_date_start and refund_date_start.strftime('%Y-%m-%d'),
            'refund_date_end':refund_date_end and (refund_date_end - datetime.timedelta(days = 1)).strftime('%Y-%m-%d'),
            # 'start_date':start_date and start_date.strftime('%Y-%m-%d'),
            # 'end_date':end_date and (end_date - datetime.timedelta(days = 1)).strftime('%Y-%m-%d'),
            'category_list':category_list,
            # 'refund_type_list':refund_type_list,
            'refund_reason_list': refund_reason_list,
            'refund_reason_checkbox': Unsubscribe.REFUND_REASON_CHOICES
        }, context_instance = RequestContext(request))
    else:
        title = "退款审计"
        columns = [{'key': 'nick', 'name': '店铺名'},
                   {'key': 'sub_category', 'name': '业务类型'},
                   {'key': 'sub_item_code', 'name': '业务码'},
                   {'key': 'sub_create', 'name': '订购时间'},
                   {'key': 'create_time', 'name': '退款录入时间'},
                   {'key': 'refund_reason_cn', 'name': '退款原因'},
                   # {'key': 'refund_type_cn', 'name': '退款类型'},
                   {'key': 'creater_cn', 'name': '录入人'},
                   {'key': 'cashier_cn', 'name': '经办人'},
                   {'key': 'status_cn', 'name': '退款状态'},
                   {'key': 'sub_pay', 'name': '订单金额'},
                   {'key': 'refund', 'name': '退款金额'},
                   {'key': 'saler_cn', 'name': '签单人'},
                   {'key': 'saler_apportion', 'name': '签单人分摊'},
                   {'key': 'server_cn', 'name': '服务人'},
                   {'key': 'server_apportion', 'name': '服务人分摊'},
                   {'key': 'saler_dpt_apportion', 'name': '签单部门分摊'},
                   {'key': 'server_dpt_apportion', 'name': '服务部门分摊'},
                   {'key': 'other_apportion', 'name': '公司分摊'},
                   {'key': 'pm_apportion', 'name': '派美分摊'},
                   {'key': 'refund_style_cn', 'name': '退款方式"'},
                   {'key': 'refund_info', 'name': '退款信息'},
                   {'key': 'receiver_cn', 'name': '退款人'}
                   ]
        for rl in result:
            rl['sub_pay'] /= 100.0
            rl['refund'] /= 100.0
            rl['saler_apportion'] = rl.get('saler_apportion', 0) / 100.0
            rl['server_apportion'] = rl.get('server_apportion', 0) / 100.0
            rl['saler_dpt_apportion'] = rl.get('saler_dpt_apportion', 0) / 100.0
            rl['server_dpt_apportion'] = rl.get('server_dpt_apportion', 0) / 100.0
            rl['other_apportion'] = rl.get('other_apportion', 0) / 100.0
            rl['pm_apportion'] = rl.get('pm_apportion', 0) / 100.0
            rl['nick'] = rl.get('nick', '')
            rl['sub_create'] = rl['sub_create'].strftime('%Y-%m-%d %H:%M:%S')
            rl['create_time'] = rl['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            rl['nick'] = rl.get('nick', '')
        response = export_excel(title = title, columns = columns, data_list = result)
        return response


@ps_auth
def comment_manage(request):

    nick = request.POST.get('nick', '')
    subscribe_psuser_id = request.POST.get('subscribe_psuser_id', '')
    duty_person_id = request.POST.get('duty_person_id', '')
    article_code = request.POST.get('article_code', '')
    create_time_start = request.POST.get('create_time_start', '')
    create_time_end = request.POST.get('create_time_end', '')
    comment_type_list = request.POST.getlist('comment_type', [-1])
    current_version_list = request.POST.getlist('current_version', [None])
    if request.method != 'POST':
        create_time_end = date_2datetime(datetime.date.today() + datetime.timedelta(days = 1))
        create_time_start = create_time_end - datetime.timedelta(days = 7)
        create_time_end = create_time_end.strftime('%Y-%m-%d')
        create_time_start = create_time_start.strftime('%Y-%m-%d')
        comment_type_list = [110, ]
        current_version_list = ['kcjl', ]
        article_code = 'ts-25811'

    query_dict = {'type': 'comment'}

    if nick:
        if nick.isdigit():
            customer_list = list(Customer.objects.filter(shop_id = int(nick)))
        else:
            customer_list = list(Customer.objects.filter(nick__contains = nick))
        if customer_list:
            shop_id_list = [obj.shop_id for obj in customer_list]
            query_dict.update({'shop_id': {'$in': shop_id_list}})
        else:
            query_dict.update({'shop_id': None})
    if subscribe_psuser_id:
        query_dict.update({'psuser_id': int(subscribe_psuser_id)})
    if duty_person_id:
        query_dict.update({'duty_person_id': int(duty_person_id)})
    if article_code:
        query_dict.update({'article_code': article_code})
    if create_time_start:
        start_time = datetime.datetime.strptime(create_time_start, "%Y-%m-%d")
        temp_dict = query_dict.setdefault('create_time', {})
        temp_dict['$gte'] = start_time
    if create_time_end:
        end_time = datetime.datetime.strptime(create_time_end, "%Y-%m-%d") + datetime.timedelta(days = 1)
        temp_dict = query_dict.setdefault('create_time', {})
        temp_dict['$lt'] = end_time
    if comment_type_list:
        comment_type_list = [int(ct) for ct in comment_type_list]
        query_dict.update({'comment_type': {'$in': comment_type_list}})
    if current_version_list:
        query_dict.update({'current_version': {'$in': current_version_list}})

    comment_list = []
    psusers = PSUser.objects.all()
    psuser_dict = {obj.id: obj for obj in psusers}
    xfgroups = XiaoFuGroup.objects.all()
    xfgroup_dict = {obj.id: obj for obj in xfgroups}

    comment_cur = event_coll.find(query_dict)
    article_code_dict = dict(ARTICLE_CODE_CHOICES)
    category_dict = dict(CATEGORY_CHOICES)
    comment_type_dict = dict(Comment.COMMENT_TYPE_CHOICES)

    shop_id_list = []
    for c in comment_cur:
        comment_list.append({
            'create_time': c['create_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'comment_id': c['_id'],
            'shop_id': c['shop_id'],
            'article_code_display': article_code_dict.get(c.get('article_code', ''), ''),
            'current_version_display': category_dict[c['current_version']],
            'comment_type_display': comment_type_dict[c['comment_type']],
            'comment_type': c['comment_type'],
            'psuser': psuser_dict[c['psuser_id']],
            'xfgroup': xfgroup_dict.get(c.get('xfgroup_id', ''), ''),
            'top_comment_times': c.get('top_comment_times', ''),
            'modify_comment_time': c.get('modify_comment_time', ''),
            'xfgroup': xfgroup_dict.get(c.get('xfgroup_id', ''), ''),
            'duty_person': psuser_dict[c['duty_person_id']],
            'duty_xfgroup': xfgroup_dict.get(c.get('duty_xfgroup_id', ''), ''),
            'note': c['note'],
            })
        shop_id_list.append(c['shop_id'])

    customer_dict = dict(Customer.objects.filter(shop_id__in = shop_id_list).values_list('shop_id', 'nick'))
    for c in comment_list:
        c['shop_nick'] = customer_dict.get(c['shop_id'], '')
    return render_to_response('comment_manage.html', {
        'comment_list': comment_list,
        'comment_type_list': comment_type_list,
        'current_version_list': current_version_list,
        'create_time_start': create_time_start,
        'create_time_end': create_time_end,
        }, context_instance = RequestContext(request))

@ps_auth
def xfgroup_manage(request):
    if request.method == 'POST':
        department = request.POST.get('department', '').strip()
        is_active = request.POST.get('is_active', '').strip()
        if is_active:
            is_active = bool(int(is_active))
    else:
        is_active = True
        department = ''

    valid_psuser_list = PSUser.objects.filter(position__in = ['CONSULT', 'SELLER'], ).exclude(status = '离职').order_by('department', '-position')

    query_dict = {}
    if department:
        query_dict.update({'department': department})
        valid_psuser_list = valid_psuser_list.filter(department = department)
    # xfgroups = XiaoFuGroup.objects.filter(**query_dict).select_related('consult', 'seller').order_by('-create_time', 'department')
    xfgroups = XiaoFuGroup.get_xfgroup_status(query_dict = query_dict, is_active = is_active)
    consult_id_list = []
    seller_id_list = []
    working_psuser_list = []
    warning_psuser_dict = {}
    for xfg in xfgroups:
        if xfg.work_status != '已废弃':
            consult_id_list.append(xfg.consult_id)
            seller_id_list.append(xfg.seller_id)
            if not xfg.end_time:
                working_psuser_list.extend([xfg.consult_id, xfg.seller_id])
            else:
                if xfg.consult_id not in warning_psuser_dict:
                    warning_psuser_dict[xfg.consult_id] = {'user': xfg.consult, 'end_time': xfg.end_time}
                elif xfg.end_time > warning_psuser_dict[xfg.consult_id]['end_time']:
                    warning_psuser_dict[xfg.consult_id]['end_time'] = xfg.end_time
                if xfg.seller_id not in warning_psuser_dict:
                    warning_psuser_dict[xfg.seller_id] = {'user': xfg.seller, 'end_time': xfg.end_time}
                elif xfg.end_time > warning_psuser_dict[xfg.seller_id]['end_time']:
                    warning_psuser_dict[xfg.seller_id]['end_time'] = xfg.end_time
    warning_psuser_list = [v for k, v in warning_psuser_dict.iteritems() if k not in working_psuser_list]

    valid_consult_list = [obj for obj in valid_psuser_list if obj.position == 'CONSULT']
    unuse_user_list = [obj for obj in valid_psuser_list if obj.id not in consult_id_list and obj.id not in seller_id_list]

    return render_to_response('xfgroup_manage.html', {
        'xfgroups': xfgroups,
        'department_choies': XiaoFuGroup.XFG_DEPARTMENT_CHOICES,
        'valid_psuser_list': valid_psuser_list,
        'valid_consult_list': valid_consult_list,
        'warning_psuser_list': warning_psuser_list,
        'unuse_user_list': unuse_user_list,
        }, context_instance = RequestContext(request))

@ps_auth
def add_xfgroup(request):
    if request.method == 'POST':
        department = request.POST['department']
        xfgroup_name = request.POST['xfgroup_name']
        start_time = request.POST['start_time']
        consult_id = int(request.POST['consult_id'])
        seller_id = int(request.POST['seller_id'])
        XiaoFuGroup.objects.create(department = department, name = xfgroup_name, consult_id = consult_id, seller_id = seller_id, start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
        return HttpResponseRedirect(reverse('xfgroup_manage'))

@ps_auth
def download_file(request):
    """下载文件"""
    file_path = request.GET.get("file_path")
    return FileOperateUtil.download_file_util(file_path)

@ps_auth
def pre_sales_advice(request):
    """售前咨询"""
    psuser = get_psuser(request)
    page_size = 100
    # qs = Subscribe.objects.select_related()
    customer = None
    if request.method == 'POST':
        form = OrderForm(data=request.POST)
        if form.is_valid():
            nick = form.cleaned_data['nick'].strip()
            start_time = form.cleaned_data['start_date']
            end_time = form.cleaned_data['end_date']
            page_no = int(form.cleaned_data['page_no'])
            owner = form.cleaned_data['owner']
            if nick != '':
                if nick.isdigit():
                    customer = Customer.objects.filter(shop_id=int(nick))
                else:
                    customer = Customer.objects.filter(nick__contains=nick)

            if customer and customer.count():
                qs = PreSalesAdvice.objects.filter(shop__in=[c for c in customer])
            else:
                qs = PreSalesAdvice.objects

            if start_time:
                qs = qs.filter(create_time__gte=start_time)
            if end_time:
                qs = qs.filter(create_time__lt=end_time + datetime.timedelta(days=1))
            if owner:
                qs = qs.filter(psuser_id=owner)
    else:
        form = OrderForm({'nick': '', 'start_date': '', 'end_date': '', 'name_cn': '', 'psuser_id': ''})
        qs = PreSalesAdvice.objects.filter()
        page_no = 1

    total_count = qs.count()
    pre_sales_advice_list = qs.order_by('-create_time')[page_size * (page_no - 1):page_size * page_no]
    return render_to_response('pre_sales_advice.html', {
        'pre_sales_advice_list': pre_sales_advice_list,
        'psuser': psuser,
        'today': datetime.date.today(),
        'form': form,
        'total_count': total_count
    }, context_instance=RequestContext(request))
