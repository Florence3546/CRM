# coding=UTF-8
import md5
import datetime, re
import hashlib
import requests

from django.conf import settings
from bson.objectid import ObjectId
from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDict
from django.db.models import F, Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from mongoengine.errors import DoesNotExist
from pyquery import PyQuery as pq
from urlparse import urlparse, parse_qsl

from dajax.core import Dajax
from apps.common.cachekey import CacheKey
from apps.common.constant import Const
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_json import json
from apps.common.utils.utils_log import log
from apps.common.utils.utils_sms import send_sms
from apps.common.utils.utils_datetime import string_2date, date_2datetime, string_2datetime, format_datetime
from apps.common.utils.utils_mysql import execute_query_sql, execute_manage_sql, execute_query_sql_return_tuple
from apps.common.templatetags.rates import truncatechars_ch

from apps.ncrm.views import get_psuser
from apps.ncrm.models import (
    PSUser, Contact, Diary, ClientGroup, Customer, sm_coll, smr_coll, pt_coll, ptr_coll, ar_coll, XiaoFuGroup, ActivityCode,
    Subscribe, Plan, Unsubscribe, event_coll, reminder_coll, TreeTemplate, Login, PLATEFORM_TYPE_CHOICES, PlanTree, PlanTreeRecord, PreSalesAdvice
    )
from apps.ncrm.utils_cache import get_consult_ids_bycache, get_consult_ids_byquerier
from apps.ncrm.workbench import WorkBenchConsult
from apps.ncrm.forms import PSUserForm
from apps.ncrm.classify_tree import build_tree, load_all_fields
from apps.ncrm.models_order import FuwuOrder
from apps.ncrm.models_performance import Performance, PerformanceConfig

from apps.kwlib.models_redis import RedisKeyManager, KeywordInfo
from apps.kwlib.base import get_words_gdata
from apps.kwslt.analyzer import ChSegement
from apps.kwslt.models_cat import cat_coll

from apps.subway.models_account import Account
from apps.subway.models_campaign import Campaign
from apps.subway.models_item import item_coll, Item
from apps.subway.models_adgroup import adg_coll
from apps.subway.models_keyword import Keyword
from apps.subway.download import Downloader
from apps.router.models import User, OrderSyncer, AdditionalPermission, ArticleUserSubscribe, NickPort, Port
from apps.web.models import pa_coll, SaleLink, MainAd, main_ad_coll, Feedback
from apps.web.utils import get_trend_chart_data
from apps.engine.models import ShopMngTask
from apps.mnt.models import MntCampaign, MntMnger, MntTask, MntTaskMng, mnt_camp_coll

from apps.alg.models import CommandConfig, StrategyConfig, strat_cfg_coll, cmd_cfg_coll
from apps.alg.interface import temp_strategy_optimize_adgroups_dryrun
from apps.ncrm.guidance3 import refresh_ps_sumval, get_ps_detail, get_indicators_byposition
from apps.kwslt.models_cat import Cat
from apps.ncrm.metrics import MetricsManager

from apps.common.utils.utils_file_updown import FileOperateUtil
from django.http import JsonResponse


def route_dajax(request):
    dajax = Dajax()
    if not request.POST.get('is_manual', None):
        dajax.script("PT.hide_loading();")
    function_name = request.POST.get('function')
    try:
        if function_name and globals().get(function_name, ''):
            dajax = globals()[function_name](request = request, dajax = dajax)
        else:
            dajax = log.exception("route_dajax: function_name Does not exist")
    except Exception, e:
        log.exception("route_dajax error, psuser_id=%s, e=%s ,function_name=%s"
                      % (request.session['psuser_id'], e, str(function_name)))
    return dajax


def psuser_name_list(request, dajax):
    call_back = request.POST.get('call_back')
    user_list = []
    ps_user = PSUser.objects.all()
    for u in ps_user:
        user_list.append(u.__str__() + ' [' + u.name + ']' + ':' + str(u.id))
    dajax.script('%s(%s)' % (call_back, json.dumps(user_list)))
    return dajax


def get_staffs_bydepartment(request, dajax):
    psuser_id = int(request.POST.get('psuser_id', 0))
    call_back = request.POST.get('call_back', "")
    error = ""
    psuser_list = []
    try:
        psuser = PSUser.objects.get(id = psuser_id)
    except Exception, e:
        log.error("get psuser error , psuser_id = %s, e = %s" % (psuser_id, e))
        error = "获取用户失败，请联系研发人员"
    else:
        staff_types = ["MKT", "PRESELLER", "SELLER", "TPAE", "RJJH", "CONSULT", "DESIGNER", "OPTAGENT"]
        if psuser.position in staff_types:
            psuser_cursor = PSUser.objects.filter(position = psuser.position).exclude(status = '离职')
        else:
            exclude_list = ["DEV", "HR", "SMANAGER", "SUPER"]
            psuser_cursor = PSUser.objects.exclude(position__in = exclude_list).exclude(status = '离职')
        psuser_list = [{ "psuser_id":psuser.id , "name_cn":psuser.name_cn}\
                      for psuser in psuser_cursor ]

    result = {"error":error, "psuser_list":psuser_list}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def save_contact(request, dajax):
    error = ""
    contact_data = json.loads(request.POST['contact'])
    call_back = request.POST.get('call_back', "")
    try:
        psuser = get_psuser(request)
        contact_data['note'] = contact_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**').replace('<body', '<p').replace('</body>', '</p>')
        contact_data.update({'psuser_id':psuser.id, 'create_time':datetime.datetime.now(), 'type':'contact'})
        contact_id = event_coll.insert(contact_data)
        contact_data.update({'psuser_name':psuser.name_cn, 'id':contact_id, 'contact_type':dict(Contact.CONTACT_TYPE_CHOICES).get(contact_data['contact_type'], '其他')})
        c_update = {'latest_contact':datetime.date.today(), 'contact_count':F('contact_count') + 1}
        if contact_data['visible']:
            c_update['contact_fail'] = False
        Customer.objects.filter(shop_id = contact_data['shop_id']).update(**c_update)
    except Exception, e:
        log.error('save_contact ERROR, e=%s' % e)
        error = "添加失败，请联系管理员！"

    result = {"error":error, "data":contact_data}
    if call_back:
        dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def editor_contact(request, dajax):
    error = ""
    try:
        psuser = get_psuser(request)
        contact_data = json.loads(request.POST['contact'])
        call_back = request.POST.get('call_back', "")
        contact_data['note'] = contact_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**').replace('<body', '<p').replace('</body>', '</p>')
        contact_data.update({'psuser_id':psuser.id, 'create_time':datetime.datetime.now()})
        contact_id = contact_data.pop('contact_id')
        event_coll.update({"_id":ObjectId(contact_id)}, {"$set":contact_data})
        contact_data.update({'psuser_name':psuser.name_cn, 'id':contact_id, 'contact_type':contact_data['contact_type']})
    except Exception, e:
        log.error('editor_contact ERROR, e=%s' % e)
        error = "添加失败，请联系管理员！"
    result = {"error":error, "data":contact_data}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def del_contact(request, dajax):
    try:
        contact_id = request.POST['contact_id']
        event_coll.remove({'_id':ObjectId(contact_id)})
        Customer.objects.filter(shop_id = int(request.POST['shop_id'])).update(contact_count = 0)
        dajax.script("$('#contact_box_%s').remove();PT.light_msg('提示', '删除成功！');" % contact_id)
    except Exception, e:
        log.error('editor_contact ERROR, e=%s' % e)
        dajax.script("PT.alert('删除失败，请联系管理员！');")
    return dajax


def editor_operate(request, dajax):
    error = ""
    operate_data = json.loads(request.POST['operate'])
    call_back = request.POST.get('call_back', "")
    try:
        psuser = get_psuser(request)
        operate_data.update({'psuser_id':psuser.id, 'create_time':datetime.datetime.now()})
        operate_id = operate_data.pop('operate_id')
        event_coll.update({"_id":ObjectId(operate_id)}, {"$set":operate_data})
        operate_data.update({'psuser_name':psuser.name_cn, 'id':operate_id})
    except Exception, e:
        log.error('editor_contact ERROR, e=%s' % e)
        error = "保存失败，请联系管理员！"
    if call_back:
        result = {"error":error, "data":operate_data}
        dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def del_operate(request, dajax):
    try:
        operate_id = request.POST['operate_id']
        event_coll.remove({'_id':ObjectId(operate_id)})
        dajax.script("$('#operate_box_%s').remove();PT.light_msg('提示', '删除成功！');" % operate_id)
    except Exception, e:
        log.error('editor_contact ERROR, e=%s' % e)
        dajax.script("PT.alert('删除失败，请联系管理员！');")
    return dajax


def editor_pause(request, dajax):
    error = ""
    pause_data = json.loads(request.POST['pause'])
    call_back = request.POST.get('call_back', "")
    try:
        pause_id = pause_data.pop('pause_id')
        pause_data['note'] = pause_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
        event_coll.update({"_id":ObjectId(pause_id)}, {"$set":pause_data})
        pause_data['id'] = pause_id
    except Exception, e:
        log.error('editor_pause ERROR, e=%s' % e)
        error = "保存失败，请联系管理员！"
    if call_back:
        result = {"error":error, "data":pause_data}
        dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def cancel_pause(request, dajax):
    psuser = get_psuser(request)
    error = ""
    pause_id = request.POST['pause_id']
    pause_date = request.POST['pause_date']
    proceed_date = request.POST['proceed_date']
    shop_id = int(request.POST['shop_id'])
    sub_id = int(request.POST['sub_id'])
    call_back = request.POST.get('call_back', "")
    is_pausing = 1
    try:
        proc_date = datetime.datetime.strptime(proceed_date, '%Y-%m-%d %H:%M:%S')
        today = proc_date.date()
        event_coll.update({"_id":ObjectId(pause_id)}, {"$set":{"proceed_date":proc_date, "proceeder_id":psuser.id}})
        # 退款 & 补单
        sub_obj = Subscribe.objects.get(id=sub_id)
        pause_date = datetime.datetime.strptime(pause_date, '%Y-%m-%d').date()
        temp_date = min(sub_obj.end_date, today)
        offset_days = (temp_date - pause_date).days
        if sub_obj.biz_type != 6 and offset_days > 0:
            offset_pay = int(round(float(sub_obj.pay) * offset_days / (sub_obj.end_date - sub_obj.start_date).days, 0))
            offset_refund_fee = int(round(float(sub_obj.refund_fee) * offset_days / (sub_obj.end_date - sub_obj.start_date).days, 0))
            if offset_pay > 0:
                sub_dict = {
                    'shop': sub_obj.shop,
                    'note': '开启暂停订单时，系统自动补单',
                    'order_id': sub_obj.order_id,
                    'fee': sub_obj.fee,
                    'cycle': sub_obj.cycle,
                    'biz_type': sub_obj.biz_type,
                    'source_type': sub_obj.source_type,
                    'operater': sub_obj.operater,
                    'visible': sub_obj.visible,
                    'xf_flag': sub_obj.xf_flag,
                    'pay_type': sub_obj.pay_type,
                    'pay_type_no': sub_obj.pay_type_no,
                    'approver': sub_obj.approver,
                    'approval_time': sub_obj.approval_time,
                    'approval_status': sub_obj.approval_status,
                }
                # 暂停退款
                sub_dict.update({
                    'create_time': datetime.datetime.now(),
                    'category': 'zttk',
                    'article_code': 'tp-005',
                    'item_code': 'tp-005',
                    'article_name': '暂停退款',
                    'item_name': '暂停退款',
                    'refund_fee': -offset_refund_fee,
                    'pay': -offset_pay,
                    'start_date': pause_date,
                    'end_date': temp_date,
                })
                Subscribe.objects.create(**sub_dict)
                # 暂停补单
                end_date = Subscribe.objects.filter(shop_id=shop_id, article_code=sub_obj.article_code).order_by('-end_date')[0].end_date
                new_start_date = max(today, end_date)
                sub_dict.update({
                    'create_time': datetime.datetime.now(),
                    'category': 'ztbd',
                    'article_code': sub_obj.article_code,
                    'item_code': sub_obj.item_code,
                    'article_name': '暂停补单',
                    'item_name': '暂停补单',
                    'refund_fee': offset_refund_fee,
                    'pay': offset_pay,
                    'start_date': new_start_date,
                    'end_date': new_start_date + datetime.timedelta(days=offset_days),
                })
                Subscribe.objects.create(**sub_dict)
                Customer.refresh_latest_end_category([shop_id])

        # 更新customer状态
        if event_coll.find({'type':'pause', 'shop_id':shop_id, 'proceed_date':{'$exists':False}}).count() == 0:
            Customer.objects.filter(shop_id = shop_id).update(is_pausing = False)
            is_pausing = 0
    except Exception, e:
        log.error('editor_pause ERROR, e=%s' % e)
        error = "保存失败，请联系管理员！"
    if call_back:
        result = {"error":error, "pause_id":pause_id, "shop_id":shop_id, "is_pausing":is_pausing, "proceed_date":proceed_date}
        dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def del_pause(request, dajax):
    try:
        pause_id = request.POST['pause_id']
        event_coll.remove({'_id':ObjectId(pause_id)})
        dajax.script("$('#pause_box_%s').remove();PT.light_msg('提示', '删除成功！');" % pause_id)
    except Exception, e:
        log.error('del_pause ERROR, e=%s' % e)
        dajax.script("PT.alert('删除失败，请联系管理员！');")
    return dajax


def del_proceed(request, dajax):
    error = ""
    pause_id = request.POST['pause_id']
    call_back = request.POST.get('call_back', "")
    try:
        event_coll.update({'_id': ObjectId(pause_id)}, {'$unset': {'proceed_date': ''}})
    except Exception, e:
        log.error('del_proceed ERROR, e=%s' % e)
        error = "操作失败，请联系管理员!"
    if call_back:
        result = {"error": error}
        dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def verify_psuser(request, dajax):
    user_name = request.POST.get('user_name', '').strip();
    call_back = request.POST.get('call_back', '')
    result = {'psuser_id':0}
    if user_name:
        try:
            psuser = PSUser.objects.only('id').get(name_cn = user_name)
            result = {'psuser_id':psuser.id}
        except:
            pass
    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def delete_subscribe(request, dajax):
    """删除订单"""
    psuser = get_psuser(request)
    subscribe_id = int(request.POST.get('subscribe_id', 0))
    try:
        subscribe = Subscribe.objects.get(id = subscribe_id)
        has_del_perms = False
        if subscribe.order_id == 0: # 手工录单
            dpt = subscribe.psuser.department if subscribe.psuser else 'None'
            if 'B' in psuser.perms or ('1' in psuser.perms and psuser.department == dpt):
                has_del_perms = True
        elif '2' in psuser.perms:
            has_del_perms = True
        if has_del_perms:
            org_psuser_id, org_operater_id = subscribe.psuser_id, subscribe.operater_id
            subscribe.delete()
            log.info('delete_subscribe, user=%s, subscribe_id=%s, psuser_operater=%s_%s' % (psuser.name_cn, subscribe_id, org_psuser_id, org_operater_id))
            # Customer.refresh_latest_end(subscribe.shop_id)
            Customer.refresh_latest_end_category([subscribe.shop_id])
            dajax.script("PT.%s(%s)" % (request.POST['call_back'], subscribe_id))
        else:
            dajax.script("PT.alert('无法删除，请联系QC或者部门管理员！');")
    except ObjectDoesNotExist:
        dajax.script("PT.alert('订单不存在，请刷新后重试！');")
    except Exception, e:
        log.error("delete subscribe error, e=%s, subscribe_id=%s" % (e, subscribe_id))
        dajax.script("PT.alert('删除失败，请联系管理员！');")
    return dajax


def end_subscribe(request, dajax):
    """终止订单"""
    subscribe_id = int(request.POST.get('subscribe_id', 0))
    frozen_kcjl = int(request.POST.get('frozen_kcjl', 0) or 0)
    unmnt_all = int(request.POST.get('unmnt_all', 0) or 0)
    try:
        psuser = get_psuser(request)
        subscribe = Subscribe.objects.get(id = subscribe_id)
        today = datetime.date.today()
#         dpt_1 = subscribe.operater.department if subscribe.operater else 'None'
#         dpt_2 = subscribe.consult.department if subscribe.consult else 'None'
        # 跟销售人员无关系
#         if subscribe.end_date > today and (psuser in [subscribe.operater, subscribe.consult] or ('1' in psuser.perms and psuser.department in (dpt_1, dpt_2))):
        if subscribe.end_date > today:
            temp_date = max(today, subscribe.start_date)
            msg = "【%s】将订单终止，原到期时间为【%s】，改为【%s】" % (psuser.name_cn, subscribe.end_date, temp_date)
            subscribe.end_date = temp_date
            subscribe.note = subscribe.note + msg  if subscribe.note else msg
            subscribe.visible = 1
            subscribe.save()
            # Customer.refresh_latest_end(subscribe.shop_id)
            Customer.refresh_latest_end_category([subscribe.shop_id])
            Customer.refresh_current_category(shop_id_list=[subscribe.shop_id])
            if frozen_kcjl:
                user = User.objects.get(shop_id = subscribe.shop_id)
                ad_perms, _ = AdditionalPermission.objects.get_or_create(user = user)
                ad_perms.perms_code = 'abcdefhijks'
                ad_perms.save()
            if unmnt_all:
                for doc in mnt_camp_coll.find({'shop_id':subscribe.shop_id}, {'_id':True}):
                    MntMnger.unmnt_campaign(shop_id = subscribe.shop_id, campaign_id = doc['_id'])

            dajax.script("PT.%s('%s','%s','%s')" % (request.POST['namespace'], subscribe_id, today, msg))
            log.info("ncrm_end_subscribe, shop_id=%s, subscribe_id=%s, frozen_kcjl=%s, unmnt_all=%s, %s" % (subscribe.shop_id, subscribe.id, frozen_kcjl, unmnt_all, msg))
        else:
            dajax.script("PT.alert('该订单已到期！');")
    except ObjectDoesNotExist:
        dajax.script("PT.alert('订单不存在，请刷新后重试！');")
    except Exception, e:
        log.error("end subscribe error, e=%s, subscribe_id =%s " % (e, subscribe_id))
        dajax.script("PT.alert('终止订单失败，请联系管理员！');")
    return dajax


def save_subscribe(request, dajax):
    flag = False
    data = None
    try:
        psuser = get_psuser(request)
        subscribe_data = json.loads(request.POST['subscribe'])
        subscribe_id = int(subscribe_data.pop('subscribe_id', 0))
        if 'psuser_id' in subscribe_data and subscribe_data['psuser_id']:
            xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = int(subscribe_data['psuser_id']))
        else:
            xfgroup = None
        subscribe_data['xfgroup'] = xfgroup
        if not xfgroup:
            log.warning('modify subscribe, psuser_id is not in xfgroup, psuser_id=%s, cur_psuser=%s' % (subscribe_data['psuser_id'], psuser.id))
        if 'consult_id' in subscribe_data and subscribe_data['consult_id']:
            consult_xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = int(subscribe_data['consult_id']))
        else:
            consult_xfgroup = None
        subscribe_data['consult_xfgroup'] = consult_xfgroup
        if not consult_xfgroup:
            log.warning('modify subscribe, consult_id is not in xfgroup, consult_id=%s, cur_psuser=%s' % (subscribe_data['consult_id'], psuser.id))
        if not subscribe_id: # id是0时就创建
            Subscribe.objects.create(**subscribe_data)
            flag = True
        else: # 否则更新
            subscribe = Subscribe.objects.get(id = subscribe_id)
            dpt_1 = subscribe.psuser.department if subscribe.psuser else 'None'
            dpt_2 = subscribe.operater.department if subscribe.operater else 'None'
            dpt_3 = subscribe.consult.department if subscribe.consult else 'None'
            # has_mng_perms = (('1' in psuser.perms or psuser.position in ['TPLEADER', 'RJJHLEADER']) and (psuser.department in (dpt_1, dpt_2, dpt_3) or (dpt_1==dpt_2==dpt_3=='None'))) or \
            #                 (psuser.position == 'RJJHLEADER' and subscribe.operater_id == 53)
            has_mng_perms = '1' in psuser.perms or psuser.position in ['TPLEADER', 'RJJHLEADER']

            if has_mng_perms:
                # 订单的签单人、操作人和顾问的指战员都只能修改对应的角色
                if not (dpt_1==dpt_2==dpt_3=='None' or 'B' in psuser.perms):
                    if (dpt_1 != 'None' and psuser.department != dpt_1) or (psuser.position in ['TPLEADER', 'RJJHLEADER'] and psuser != subscribe.psuser):
                        del subscribe_data['psuser_id']
                        if 'xfgroup' in subscribe_data:
                            del subscribe_data['xfgroup']
                    # if not (psuser.position == 'RJJHLEADER' and subscribe.operater_id == 53):
                    #     if dpt_2 != 'None' and psuser.department != dpt_2 and subscribe.operater_id != 53:
                    #         del subscribe_data['operater_id']
                    #     if dpt_3 != 'None' and psuser.department != dpt_3:
                    #         del subscribe_data['consult_id']
                    #         if 'consult_xfgroup' in subscribe_data:
                    #             del subscribe_data['consult_xfgroup']
                    if dpt_3 != 'None' and psuser.department != dpt_3:
                        del subscribe_data['consult_id']
                        if 'consult_xfgroup' in subscribe_data:
                            del subscribe_data['consult_xfgroup']

            elif 'B' not in psuser.perms:
                # 订单的签单人、操作人和顾问只能修改对应的角色
                if psuser != subscribe.psuser:
                    del subscribe_data['psuser_id']
                    if 'xfgroup' in subscribe_data:
                        del subscribe_data['xfgroup']
                if psuser != subscribe.operater:
                    del subscribe_data['operater_id']
                if psuser != subscribe.consult:
                    del subscribe_data['consult_id']
                    if 'consult_xfgroup' in subscribe_data:
                        del subscribe_data['consult_xfgroup']

            if 'B' in psuser.perms or has_mng_perms or psuser in (subscribe.psuser, subscribe.operater, subscribe.consult):
                log.info('crm_save_subscribe log, user_name=%s, shop_id=%s, subscribe_id=%s, org_psuser_operater_consult=%s_%s_%s, save_data=%s' % (request.session.get('psuser_name'), subscribe.shop_id, subscribe_id, subscribe.psuser_id, subscribe.operater_id, subscribe.consult_id, request.POST['subscribe']))
                allocate_flag = ('psuser_id' in subscribe_data and subscribe_data['psuser_id'] != unicode(subscribe.psuser_id or ''))\
                                or ('operater_id' in subscribe_data and subscribe_data['operater_id'] != unicode(subscribe.operater_id or ''))\
                                or ('consult_id' in subscribe_data and subscribe_data['consult_id'] != unicode(subscribe.consult_id or ''))
                if allocate_flag:
                    allocation_record = {
                        'psuser_id': psuser.id,
                        'psuser_cn': psuser.name_cn,
                        'shop_id': subscribe.shop_id,
                        'subscribe_id': subscribe_id,
                        'sub_time': subscribe.create_time,
                        'category_cn': subscribe.get_category_display(),
                        'pay': subscribe.pay,
                        'create_time': datetime.datetime.now(),
                        'org_id_list': '%s, %s, %s' % (subscribe.psuser_id or 0, subscribe.operater_id or 0, subscribe.consult_id or 0),
                        'org_cn_list': '%s, %s, %s' % (subscribe.psuser.name_cn if subscribe.psuser else '无', subscribe.operater.name_cn if subscribe.operater else '无', subscribe.consult.name_cn if subscribe.consult else '无')
                    }
                ptr_flag = 'psuser_id' in subscribe_data and subscribe_data['psuser_id'] and subscribe_data['psuser_id'] != unicode(subscribe.psuser_id or '')
                for attr, value in subscribe_data.items():
                    if value != "None":
                        setattr(subscribe, attr, value)
                # 处理新增的boolean值
                subscribe.has_contract = bool(int(subscribe.has_contract))
                subscribe.save()

                # 用来回显数据
                subscribe = Subscribe.objects.select_related('shop').get(id = subscribe_id)
                data = {
                    'id': subscribe_id,
                    'category': subscribe.get_category_display(),
                    'item_code': subscribe.item_code,
                    'create_time': subscribe.create_time,
                    'start_date': subscribe.start_date,
                    'end_date': subscribe.end_date,
                    'pay': format(subscribe.pay / 100.0, '.2f'),
                    'biz_type': subscribe.display_biz_type(),
                    'source_type': subscribe.get_source_type_display(),
                    'psuser': subscribe.psuser and subscribe.psuser.name_cn or '',
                    'operater': subscribe.operater and subscribe.operater.name_cn or '',
                    'consult': subscribe.consult and subscribe.consult.name_cn or '',
                    'approval_status': subscribe.get_approval_status_display()
                }
                if allocate_flag:
                    allocation_record.update({
                        'new_id_list': '%s, %s, %s' % (subscribe.psuser_id or 0, subscribe.operater_id or 0, subscribe.consult_id or 0),
                        'new_cn_list': '%s, %s, %s' % (subscribe.psuser.name_cn if subscribe.psuser else '无', subscribe.operater.name_cn if subscribe.operater else '无', subscribe.consult.name_cn if subscribe.consult else '无')
                    })
                    ar_coll.insert(allocation_record)
                if ptr_flag:
                    build_tree.auto_insert_record(**{
                        'psuser': subscribe.psuser,
                        'shop_id': subscribe.shop_id,
                        'nick': subscribe.shop.nick,
                        'rec_type': 'renew_order_pay',
                        'rec_value': subscribe.pay,
                        'create_time': subscribe.create_time
                    })
                flag = True
                # 刷新customer的签单人、操作人和顾问
                default_server_list = [None, None, None, None, None, None]
                if subscribe.operater:
                    # operater = subscribe.operater
                    # if operater.position in ['RJJH', 'RJJHLEADER'] and operater.status != '离职':
                    #     default_server_list[1] = operater
                    # elif operater.position in ['TPAE', 'TPLEADER', 'OPTAGENT'] and operater.status != '离职':
                    #     default_server_list[2] = operater
                    default_server_list[1] = default_server_list[2] = subscribe.operater
                if subscribe.consult:
                    consult = subscribe.consult
                    if consult.position in ['CONSULT', 'CONSULTLEADER', 'SELLER', 'SALELEADER'] and consult.status != '离职':
                        default_server_list[3] = consult
                # 更新customer的所属人
                if subscribe.category in ['qn', 'kcjl', 'rjjh', 'vip', 'ztc', 'dyy']:
                    Customer.get_or_create_servers([subscribe.shop_id], default_server_list = default_server_list)
                # Customer.refresh_latest_end(subscribe.shop_id)
                Customer.refresh_latest_end_category([subscribe.shop_id])
            else:
                flag = False
    except Exception, e:
        log.error('save_operate ERROR, e=%s' % e)

    result = {'flag': flag}
    if data:
        result['data'] = data
    dajax.script("PT.%s(%s);" % (request.POST['namespace'], json.dumps(result)))
    return dajax


def save_new_subscribe(request, dajax):
    """新增人工签单"""
    call_back = request.POST['call_back']
    subscribe_dict = json.loads(request.POST['subscribe'])
    result = {'status': False}
    try:
        subscribe = Subscribe()
        create_time = datetime.datetime.strptime(subscribe_dict['create_time'], "%Y-%m-%d")
        now = datetime.datetime.now()
        subscribe.create_time = datetime.datetime(create_time.year, create_time.month, create_time.day, now.hour, now.minute, now.second)
        subscribe.category = subscribe_dict['category']
        subscribe.article_code = subscribe_dict['article_code']
        subscribe.item_code = subscribe_dict['item_code']
        subscribe.biz_type = int(subscribe_dict['biz_type'])
        subscribe.source_type = int(subscribe_dict['source_type'])
        subscribe.shop_id = int(subscribe_dict['shop_id'])
        subscribe.note = subscribe_dict['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
        subscribe.pay = int(subscribe_dict['pay'])
        # if subscribe.pay == 0:
        #     raise Exception('subscribe.pay=0')
        subscribe.psuser_id = int(subscribe_dict['psuser_id'])
        xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(subscribe.psuser_id)
        if xfgroup:
            subscribe.xfgroup = xfgroup
        subscribe.start_date = datetime.datetime.strptime(subscribe_dict['start_date'], "%Y-%m-%d").date()
        subscribe.end_date = datetime.datetime.strptime(subscribe_dict['end_date'], "%Y-%m-%d").date()
        subscribe.cycle = "{}个月".format(int(round((subscribe.end_date - subscribe.start_date).days / 30.0)))
        subscribe.visible = int(subscribe_dict['visible'])
        subscribe.xf_flag = int(subscribe_dict['xf_flag'])
        subscribe.pay_type = int(subscribe_dict['pay_type'])
        subscribe.pay_type_no = subscribe_dict['pay_type_no']
        subscribe.has_contract = bool(int(subscribe_dict['has_contract']))
        subscribe.chat_file_path = subscribe_dict['chat_file_path']
        subscribe.save()
        result = {'status': True}
        if subscribe.category not in ('zz', 'zx', 'other', 'seo', 'kfwb'):
            Customer.objects.filter(shop_id = subscribe.shop_id).update(contact_count = 0)
            Customer.refresh_latest_end_category([subscribe.shop_id])
    except Exception, e:
        log.error('save subscribe event error, args=%s, e=%s' % (subscribe_dict, e))
    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def save_operate(request, dajax):
    error = ""
    operate_data = json.loads(request.POST['operate'])
    call_back = request.POST.get('call_back', "")
    try:
        psuser = get_psuser(request)
        operate_data['note'] = operate_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
        operate_data.update({'psuser_id':psuser.id, 'create_time':datetime.datetime.now(), 'type':'operate'})
        operate_id = event_coll.insert(operate_data)
        operate_data.update({'psuser_name': psuser.name_cn, 'id': operate_id})
        Customer.objects.filter(shop_id = operate_data['shop_id']).update(latest_operate = datetime.date.today())
    except Exception, e:
        log.error('save_operate ERROR, e=%s' % e)
        error = "添加失败，请联系管理员！"

    result = {"error": error, "data": operate_data}
    if call_back:
        dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def save_reintro(request, dajax):
    try:
        psuser = get_psuser(request)
        org_data = json.loads(request.POST['obj'])
        org_data['note'] = org_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd',
                                                                                                               '**')
        org_data.update({'psuser_id': psuser.id, 'create_time': datetime.datetime.now(), 'type': 'reintro'})
        event_coll.insert(org_data)
        dajax.script("$('#id_add_reintro_layout').modal('hide');")
        dajax.script("PT.light_msg('提醒','保存成功！');")
    except Exception, e:
        log.error('save_operate ERROR, e=%s' % e)
        dajax.script("PT.alert('添加失败，请联系管理员！');")
    return dajax


def save_comment(request, dajax):
    error = ""
    org_data = json.loads(request.POST['obj'])
    call_back = request.POST.get('call_back', "")
    try:
        psuser = get_psuser(request)
        org_data['note'] = org_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
        org_data['create_time'] = datetime.datetime.strptime(org_data['create_time'], '%Y-%m-%d %H:%M')
        org_data.update({'psuser_id': psuser.id, 'type': 'comment'})
        xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = int(psuser.id))
        org_data.update({'xfgroup_id': xfgroup and xfgroup.id})
        cust = Customer.objects.get(shop_id = int(org_data['shop_id']))
        if int(org_data['comment_type']) < 200:
            org_data.update({'duty_person_id': psuser.id})
            org_data.update({'duty_xfgroup_id': xfgroup and xfgroup.id})
            build_tree.auto_insert_record(**{
                'psuser': psuser,
                'shop_id': cust.shop_id,
                'nick': cust.nick,
                'rec_type': 'good_comment_count',
                'rec_value': 1,
                'create_time': org_data['create_time']
            })
        else:
            org_data.update({'duty_person_id': cust.consult.id})
            consult_xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = cust.consult.id)
            org_data.update({'duty_xfgroup_id': consult_xfgroup and consult_xfgroup.id})
        event_coll.insert(org_data)
    except Exception, e:
        log.error('save_comment ERROR, e=%s' % e)
        error = "添加失败，请联系管理员!"

    result = {"error": error, "data": org_data}
    if call_back:
        dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax

def delete_comment(request, dajax):
    error = ""
    comment_id = request.POST['comment_id']
    call_back = request.POST['call_back']
    try:
        event_coll.remove({'_id': ObjectId(comment_id), 'type': 'comment'})
    except Exception, e:
        log.error('delete_comment error, e=%s' % e)
        error = "删除失败，请联系管理员!"
    dajax.script("%s(%s);" % (call_back, error))
    return dajax

def demotion_comment(request, dajax):
    error = ""
    comment_id = request.POST['comment_id']
    call_back = request.POST['call_back']
    try:
        event_coll.update({'_id': ObjectId(comment_id), 'type': 'comment'}, {'$set': {'comment_type': 110, 'top_comment_times': None}})
    except Exception, e:
        log.error('demotion_comment error, e=%s' % e)
        error = "降为日常好评失败，请联系管理员!"
    dajax.script("%s(%s);" % (call_back, error))
    return dajax

def upgrade_comment(request, dajax):
    error = ""
    comment_id = request.POST['comment_id']
    top_comment_times = request.POST['top_comment_times']
    call_back = request.POST['call_back']
    try:
        event_coll.update({'_id': ObjectId(comment_id), 'type': 'comment'}, {'$set': {'comment_type': 120, 'top_comment_times': top_comment_times}})
    except Exception, e:
        log.error('upgrade_comment error, e=%s' % e)
        error = "升级为踩好评失败，请联系管理员!"
    dajax.script("%s(%s);" % (call_back, error))
    return dajax


def save_unsubscribe(request, dajax):
    error = ""
    try:
        psuser = get_psuser(request)
        org_data = json.loads(request.POST['obj'])
        org_data["unknown_subscribe_flag"] = request.POST.get('unknown_subscribe_flag', 0)
        call_back = request.POST.get('call_back', "")
        event_id = org_data['event_id']
        unmnt_all = int(request.POST.get('unmnt_all', 0) or 0)
        if org_data['unknown_subscribe_flag'] and event_coll.find({'type': 'unsubscribe', 'event_id': event_id, 'refund_reason':5}).count():
            error = "提醒: 该订单已被标记过赠送！"
        else:
            now = datetime.datetime.now()
            org_data['note'] = org_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
            sub_obj = Subscribe.objects.select_related('shop').get(id = event_id)
            if org_data["unknown_subscribe_flag"]:
                sub_obj.biz_type = 6
                if not sub_obj.psuser_id and org_data['saler_id']:
                    sub_obj.psuser_id = int(org_data['saler_id'])
                    sub_xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = sub_obj.psuser_id)
                    sub_obj.xfgroup = sub_xfgroup
                sub_obj.save()
                build_tree.auto_insert_record(**{
                    'psuser': sub_obj.psuser,
                    'shop_id': sub_obj.shop_id,
                    'nick': sub_obj.shop.nick,
                    'rec_type': 'unknown_order_count',
                    'rec_value': 1,
                    'create_time': sub_obj.create_time
                })

            psuser_dept_dict = dict(PSUser.objects.values_list('id', 'department'))
            duty_dpt = ''
            if sub_obj.psuser_id:
                duty_dpt = psuser_dept_dict.get(sub_obj.psuser_id, '')
            elif sub_obj.operater_id:
                duty_dpt = psuser_dept_dict.get(sub_obj.operater_id, '')
            elif sub_obj.consult_id:
                duty_dpt = psuser_dept_dict.get(sub_obj.consult_id, '')
            reimburse_dpt = psuser_dept_dict.get(int(org_data.get('cashier_id', 0) or 0), '')
            server_id = sub_obj.operater_id or sub_obj.consult_id
            org_data.update({
                'psuser_id':psuser.id,
                'create_time':now,
                'refund_date':now,
                'type':'unsubscribe',
                'saler_id':sub_obj.psuser_id,
                'server_id':server_id,
                'duty_dpt':duty_dpt,
                'reimburse_dpt':reimburse_dpt,
                'nick':sub_obj.shop.nick,
                'category':sub_obj.category,
            })
            xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = psuser.id)
            saler_xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = sub_obj.psuser_id)
            server_xfgroup = XiaoFuGroup.get_xfgroupid_8psuserid(psuser_id = server_id)
            org_data.update({
                'xfgroup_id': xfgroup and xfgroup.id,
                'saler_xfgroup_id': saler_xfgroup and saler_xfgroup.id,
                'server_xfgroup_id': server_xfgroup and server_xfgroup.id,
                })
            event_coll.insert(org_data)

            # 邮件通知
            if org_data['cashier_id']:
                cashier_commander_list = list(PSUser.objects.filter(Q(id = org_data['cashier_id']) | (Q(position = 'COMMANDER') & Q(department = org_data['reimburse_dpt']))).values_list('name', flat = True))
                if cashier_commander_list:
                    subject = '%s 将你设置为掌柜【%s】的退款事件中的经办人' % (psuser.name_cn, request.POST['nick'])
                    content = '开车精灵系统自动提醒邮件，勿回复。'
                    cc_list = ['%s@paithink.com' % name for name in cashier_commander_list]
                    send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, cc_list)

            org_data['psuser_name'] = psuser.name_cn
            if org_data['frozen_kcjl']:
                user = User.objects.get(shop_id = org_data['shop_id'])
                ad_perms, _ = AdditionalPermission.objects.get_or_create(user = user)
                ad_perms.perms_code = 'abcdefhijks'
                ad_perms.save()
                Subscribe.objects.filter(id = event_id).update(end_date = datetime.date.today())
                # Customer.refresh_latest_end(org_data['shop_id'])
                Customer.refresh_latest_end_category([org_data['shop_id']])
            if unmnt_all:
                for doc in mnt_camp_coll.find({'shop_id':org_data['shop_id']}, {'_id':True}):
                    MntMnger.unmnt_campaign(shop_id = org_data['shop_id'], campaign_id = doc['_id'])
    except Exception, e:
        log.error('save_unsubscribe ERROR, e=%s' % e)
        error = "添加失败，请联系管理员！"
    else:
        log.info('save_unsubscribe, psuser=%s, shop_id=%s, frozen_kcjl=%s, unmnt_all=%s' % (psuser.name_cn, org_data['shop_id'], org_data['frozen_kcjl'], unmnt_all))

    result = {"error": error, "data": org_data}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def modify_unsubscribe(request, dajax):
    error = ""
    modify_data = json.loads(request.POST['obj'])
    call_back = request.POST.get('call_back', "")
    try:
        myself = get_psuser(request)
        unsub_id = modify_data.pop('id')
        sub_id = modify_data.pop('sub_id')
        query = {'_id':ObjectId(unsub_id)}
        if not 'B' in myself.perms:
            query['psuser_id'] = myself.id
            query['status'] = 1
        modify_data['note'] = modify_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
        if modify_data['create_time']:
            modify_data['create_time'] = datetime.datetime.strptime(modify_data['create_time'], '%Y-%m-%d %H:%M')
        else:
            del modify_data['create_time']
        if modify_data['refund_date']:
            modify_data['refund_date'] = datetime.datetime.strptime(modify_data['refund_date'], '%Y-%m-%d %H:%M')
        else:
            del modify_data['refund_date']
        event_coll.update(query, {'$set':modify_data})
        modify_data['id'] = unsub_id

        # 同步Subscribe的biz_type
        # if modify_data['refund_type'] == 3:
        if modify_data['refund_reason'] == 5:
            Subscribe.objects.filter(id = sub_id).update(biz_type = 6)
        else:
            Subscribe.objects.filter(id = sub_id, biz_type = 6).update(biz_type = 1)

        # 邮件通知
        if modify_data['cashier_id'] and modify_data['cashier_id'] != int(request.POST['org_cashier_id'] or 0):
            cashier_commander_list = list(PSUser.objects.filter(Q(id = modify_data['cashier_id']) | (Q(position = 'COMMANDER') & Q(department = modify_data['reimburse_dpt']))).values_list('name', flat = True))
            if cashier_commander_list:
                subject = '%s 将你设置为掌柜【%s】的退款事件中的经办人' % (myself.name_cn, request.POST['nick'])
                content = '开车精灵系统自动提醒邮件，勿回复。'
                cc_list = ['%s@paithink.com' % name for name in cashier_commander_list]
                send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, cc_list)

    except Exception, e:
        log.error('save_unsubscribe ERROR, e=%s' % e)
        error = "保存失败，请联系管理员！"
    temp_list = modify_data['refund_info'].split('__', 1)
    if len(temp_list) == 2:
        modify_data['refund_info'], modify_data['receiver_cn'] = temp_list
    else:
        modify_data['receiver_cn'] = ''
    result = {"error": error, "data": modify_data}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def modify_unsubscribe_status(request, dajax):
    error = ""
    unsub = {}
    try:
        myself = get_psuser(request)
        call_back = request.POST.get('call_back', "")
        status = int(request.POST['status'])
        set_data = {'status':status, 'refund_date':datetime.datetime.now()}
        img_list = json.loads(request.POST.get('img_list', '[]'))
        if img_list:
            set_data['img_list'] = img_list
        event_coll.update({'_id':ObjectId(request.POST['id']), 'cashier_id':myself.id}, {'$set':set_data})

        unsub = list(event_coll.find({'_id':ObjectId(request.POST['id'])}))
        if unsub:
            unsub = unsub[0]
            unsub['status_cn'] = dict(Unsubscribe.REFUND_STATUS_CHOICES).get(unsub['status'], '未知')
            # 邮件通知
            psuser_commander_list = list(PSUser.objects.filter(Q(id = unsub['psuser_id']) | (Q(position = 'COMMANDER') & Q(department = unsub['reimburse_dpt']))).values_list('name', flat = True))
            if psuser_commander_list:
                subject = '%s 已将掌柜【%s】的退款事件设置为%s' % (myself.name_cn, unsub['nick'], unsub['status_cn'])
                content = '开车精灵系统自动提醒邮件，勿回复。'
                cc_list = ['%s@paithink.com' % name for name in psuser_commander_list]
                send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, cc_list)
        else:
            error = '未找到该退款记录'
    except Exception, e:
        log.error('save_unsubscribe ERROR, e=%s' % e)
        error = "保存失败，请联系管理员！"

    result = {"error": error, "data": unsub}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def save_pause(request, dajax):
    error = ""
    try:
        psuser = get_psuser(request)
        org_data = json.loads(request.POST['obj'])
        call_back = request.POST.get('call_back', "")
        event_id = org_data['event_id']
        sub = Subscribe.objects.get(id = event_id)
        if event_coll.find({'type':'pause', 'event_id':event_id, 'proceed_date':{'$exists':False}}).count():
            error = "提醒: 该订单已暂停！"
        else:
            pause_create_time = datetime.datetime.strptime(org_data['pause_create_time'], '%Y-%m-%d %H:%M:%S')
            org_data['note'] = org_data['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd', '**')
            org_data.update({'psuser_id': psuser.id, 'create_time': pause_create_time, 'type': 'pause'})
            pause_id = event_coll.insert(org_data)
            org_data.update({'psuser_name': psuser.name_cn, 'id': pause_id, 'remain_days':(sub.end_date - pause_create_time.date()).days})
            Customer.objects.filter(shop_id = org_data['shop_id']).update(is_pausing = True)
    except Exception, e:
        log.error('save_unsubscribe ERROR, e=%s' % e)
        error = "添加失败，请联系管理员！"

    result = {"error": error, "data": org_data}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def related_plane_list(request, dajax):
    def check_regular_plan(psuser_id):
        '''检查例行计划是否存在，不存在则创建空计划'''
        today = datetime.date.today()
        psuser_id_list = [3] # 李朝晖
        if psuser_id in psuser_id_list:
            if today.weekday() >= 4: # 周五到周日检查psuser的下周计划是否存在，没有则新建
                friday = today - datetime.timedelta(days = (today.weekday() - 4)) # 本周五
            else: # 周一到周四检查psuser的本周计划是否存在，没有则新建
                friday = today - datetime.timedelta(days = (today.weekday() + 3)) # 上周五
            plan_count = Plan.objects.filter(psuser = psuser_id, start_time__gt = friday).count()
            if plan_count == 0:
                this_month_1stday = datetime.date(today.year, today.month, 1)
                if today.month < 12:
                    next_month_1stday = datetime.date(today.year, today.month + 1, 1)
                else:
                    next_month_1stday = datetime.date(today.year + 1, 1, 1)
                month_plan_count = Plan.objects.filter(psuser = psuser_id, start_time__gte = this_month_1stday,
                                                       end_time__lte = next_month_1stday).count()
                arg_list = []
                if month_plan_count == 0:
                    arg_list.append(['【系统生成】%s计划' % this_month_1stday.strftime('%Y年%m月份'), this_month_1stday,
                                     next_month_1stday - datetime.timedelta(days = 1)])
                    arg_list.append(['【系统生成】%s第1周计划' % this_month_1stday.strftime('%Y年%m月'), this_month_1stday,
                                     this_month_1stday - datetime.timedelta(days = this_month_1stday.weekday() - 6)])
                elif month_plan_count < 5:
                    arg_list.append(['【系统生成】%s第%s周计划' % (this_month_1stday.strftime('%Y年%m月'), month_plan_count), today - datetime.timedelta(days = today.weekday()), today - datetime.timedelta(days = today.weekday() - 6)])
                else:
                    if next_month_1stday.month < 12:
                        next2_month_1stday = datetime.date(next_month_1stday.year, next_month_1stday.month + 1, 1)
                    else:
                        next2_month_1stday = datetime.date(next_month_1stday.year + 1, 1, 1)
                    month_plan_count2 = Plan.objects.filter(psuser = psuser_id, start_time__gte = next_month_1stday, end_time__lte = next2_month_1stday).count()
                    if month_plan_count2 < 2:
                        arg_list.append(['【系统生成】%s第1周计划' % next_month_1stday.strftime('%Y年%m月'), next_month_1stday, next_month_1stday - datetime.timedelta(days = next_month_1stday.weekday() - 6)])
                        if month_plan_count2 == 0:
                            arg_list.append(['【系统生成】%s计划' % next_month_1stday.strftime('%Y年%m月份'), next_month_1stday,
                                             next2_month_1stday - datetime.timedelta(days = 1)])
                for title, start_time, end_time in arg_list:
                    Plan.objects.create(
                        title = title,
                        psuser_id = psuser_id,
                        event_list = '',
                        target = '系统自动生成，待编辑',
                        note = '系统自动生成，待编辑',
                        progress = '',
                        start_time = start_time,
                        end_time = end_time,
                        create_user_id = psuser_id,
                    )

    plan_belong = request.POST.get('plan_belong', '')
    create_time = request.POST.get('create_time', '')
    call_back = request.POST.get('call_back', '')

    plan, result = [], []
    if plan_belong:
        check_regular_plan(int(plan_belong))
        #         psuser = PSUser.objects.filter(name_cn__contains = plan_belong)
        #         if psuser:
        plan = Plan.objects.filter(psuser = plan_belong)

    if create_time:
        if plan or plan_belong:
            plan = plan.filter(create_time = create_time)
        else:
            plan = Plan.objects.filter(create_time = create_time)

    for p in plan:
        result.append([p.psuser.name_cn, p.title, p.id, p.start_time, p.end_time])

    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def search_query(request, dajax):
    ''''查询语句'''
    query = request.POST.get('query', '')
    call_back = request.POST.get('call_back', '')

    id_list, err = [], ''
    if query:
        psuser = get_psuser(request)
        id_list, err = get_consult_ids_byquerier(psuser.id, query)

    result = {'id_list': id_list, 'error': err}
    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def save_query(request, dajax):
    ''''保存查询语句'''
    query = request.POST.get('query', '')
    client_group_id = request.POST.get('client_group_id', 0)
    call_back = request.POST.get('call_back', '')
    err = None
    if client_group_id:
        try:
            client = ClientGroup.objects.get(id = client_group_id)
            client.query = query
            client.save()
        except Exception, e:
            err = '计划不存在'
            log.error('save_query error client_group_id=%s, e=%s' % (client_group_id, e))
    else:
        err = '参数为空'
    result = {'error': err}
    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def generate_id_list(request, dajax):
    ''''生成用户id列表'''
    query = request.POST.get('query', '')
    client_group_id = request.POST.get('client_group_id', 0)
    call_back = request.POST.get('call_back', '')
    err = None
    if client_group_id:
        try:
            psuser = get_psuser(request)
            id_list, err = get_consult_ids_byquerier(psuser.id, query)
            if not err:
                client = ClientGroup.objects.get(id = client_group_id)
                client.id_list = id_list
                client.save()
            else:
                err = "生成用户列表失败"
        except Exception, e:
            err = '计划不存在'
            log.error('generate_id_list error client_group_id=%s, e=%s' % (client_group_id, e))
    else:
        err = '参数为空'
    result = {'error': err}
    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def save_id_list(request, dajax):
    '''保存用户id_list'''
    client_group_id = request.POST.get('client_group_id', 0)
    id_list = request.POST.get('id_list', '[]')
    call_back = request.POST.get('call_back', '')
    err = None
    if client_group_id:
        try:
            client = ClientGroup.objects.get(id = client_group_id)
            id_list = [int(i) for i in eval(id_list)]
            client.save_id_list(add_id_list = id_list)
        except Exception, e:
            err = '保存失败'
            log.error('save_id_list error client_group_id=%s, e=%s' % (client_group_id, e))
    else:
        err = "参数错误"
    result = {'error': err, 'id_list': id_list}
    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def manual_add_customers(request, dajax):
    '''手动批量添加客户群'''
    client_group_id = request.POST.get('client_group_id', 0)
    nick_list = json.loads(request.POST['nick_list'])
    call_back = request.POST.get('call_back', '')

    err = None
    data = []
    if client_group_id:
        try:
            client = ClientGroup.objects.get(id = client_group_id)
            old_id_list = eval(client.id_list) if client.id_list else []
            query = {'nick__in':nick_list}
            if client.group_type in (1, 2):
                query['consult'] = get_psuser(request)
            valid_list = [int(cust.shop_id) for cust in Customer.objects.only('shop_id').filter(**query)]

            new_len = len(nick_list)
            valid_len = len(valid_list)
            old_len = len(old_id_list)

            valid_list.extend(old_id_list)
            cur_list = list(set(valid_list))
            cur_len = len(cur_list)

            client.id_list = cur_list
            client.save()

            faild_count = new_len - valid_len # 无效客户
            exsited_count = valid_len + old_len - cur_len # 已存在客户
            success_count = cur_len - old_len # 成功客户
            data = (faild_count, exsited_count, success_count)
        except Exception, e:
            err = '保存失败'
            log.error('manual_add_customers error client_group_id=%s, e=%s' % (client_group_id, e))
    else:
        err = "参数错误"
    result = {'error': err, 'data': data}
    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def del_id_list(request, dajax):
    '''删除用户id_list'''
    client_group_id = request.POST.get('client_group_id', 0)
    id_list = request.POST.get('id_list', '[]')
    call_back = request.POST.get('call_back', '')
    err = None
    if client_group_id:
        try:
            client = ClientGroup.objects.get(id = client_group_id)
            id_list = [int(i) for i in eval(id_list)]
            client.delete_id_list(del_id_list = id_list)
        except Exception, e:
            err = '保存失败'
            log.error('del_id_list error client_group_id=%s, e=%s' % (client_group_id, e))
    else:
        err = "参数错误"
    result = {'error': err}
    dajax.script('%s(%s)' % (call_back, json.dumps(result)))
    return dajax


def get_psuser_list(request, dajax):
    try:
        result_list = []
        rows = PSUser.objects.all().values_list('id', 'name_cn', 'name', 'position').order_by('position')
        position_dict = dict(PSUser.POSITION_CHOICES)
        for row in rows:
            result_list.append(
                {'id': row[0], 'name_cn': row[1], 'name': row[2], 'position': position_dict.get(row[3], '未知'),
                 'true_position': row[3]})
        dajax.script("PT.%s(%s)" % (request.POST['namespace'], json.dumps(result_list)))
    except Exception, e:
        log.error('get_psuser_list error, e=%s' % e)
        dajax.script("PT.alert('获取用户失败！');")
    return dajax


def submit_order_allocate(request, dajax):
    try:
        order_id = request.POST['order_id']
        psuser_id = request.POST['psuser_id']
        psuser_type = request.POST['psuser_type']
        update_dict = {}
        key = psuser_type == 'saler' and 'psuser' or 'operater'
        update_dict.update({key: psuser_id})
        Subscribe.objects.filter(id = order_id).update(**update_dict)
        dajax.script("PT.%s('%s', '%s', '%s')" % (request.POST['namespace'], order_id, psuser_id, psuser_type))
    except Exception, e:
        log.error('get_psuser_list error, e=%s' % e)
        dajax.script("PT.alert('分配订单失败！');")
    return dajax


def check_nick(request, dajax):
    result = {}
    try:
        nick = request.POST['nick']
        is_exists = Customer.objects.filter(nick = nick).count() > 0 and True or False
        if not is_exists:
            shop_id = Customer.get_shop_by_nick(nick)
            if shop_id: # TODO: wangqi 20141204 爬取信息，如信誉等级、是否C店、地址、经营范围等
                result['shop_id'] = shop_id
            else:
                result['msg'] = "该nick不存在，请重新输入！"
        else:
            result['msg'] = "该nick已收录，请在用户列表搜索！"
    except Exception, e:
        result['msg'] = "nick检查失败，请联系管理员！"
        log.error('check_nick error, e=%s' % e)
    dajax.script("PT.%s(%s)" % (request.POST['namespace'], json.dumps(result)))
    return dajax


def save_customer(request, dajax):
    result = 'false'
    try:
        cust_dict = json.loads(request.POST['customer'])
        cust_dict['nick'] = cust_dict['nick'].strip()
        cust_dict['note'] = cust_dict['note'].replace('刷单', '**').replace('刷', '**').replace('SD', '**').replace('sd',
                                                                                                                 '**')
        shop_id = int(cust_dict.pop('shop_id'))
        customer, _ = Customer.objects.get_or_create(shop_id = shop_id, defaults = {'nick': cust_dict['nick'],
                                                                                'creator': get_psuser(request)})
        for attr, value in cust_dict.items():
            setattr(customer, attr, value)
        customer.update_time = datetime.datetime.now()
        customer.save()

        group_id = int(request.POST.get('group_id', 0))
        if group_id:
            client = ClientGroup.objects.get(id = group_id)
            client.save_id_list(add_id_list = [shop_id])
        result = 'true'
    except Exception, e:
        log.error('save customer error, e=%s' % e)
    dajax.script("PT.%s(%s)" % (request.POST['namespace'], result))
    return dajax


def update_customer(request, dajax):
    error = ""
    cust_dict = json.loads(request.POST['cust_dict'])
    shop_id = int(cust_dict.pop('shop_id'))
    call_back = request.POST['call_back']

    try:
        customer, _ = Customer.objects.get_or_create(shop_id = shop_id)
        for attr, value in cust_dict.items():
            setattr(customer, attr, value)
        customer.update_time = datetime.datetime.now()
        customer.save()
    except Exception, e:
        log.error('save customer error, e=%s' % e)
        error = "服务端出错，e=%s" % (e)

    result = {'shop_id': shop_id, 'error': error}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def get_client_group_info(request, dajax):
    """通过员工ID,获取客服组信息"""
    user_id = int(request.POST['user_id'])
    call_back = request.POST['call_back']
    client_groups_info = [{"id": cg.id, "title": cg.title} for cg in \
                          ClientGroup.objects.filter(create_user__id = user_id)]
    result = {'infos': client_groups_info, 'error': ""}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def creaete_client_group(request, dajax):
    ''''创建客户群列表'''
    psuser_id = int(request.POST.get('psuser_id', 0))
    title = request.POST.get('title', "")
    note = request.POST.get('note', "")
    call_back = request.POST.get('call_back', "")

    error = ""
    client_group = None
    try:
        client_group = ClientGroup.objects.create(title = title, note = note, create_user_id = psuser_id)
    except Exception, e:
        error = '创建群失败,e = %s' % (e)
        log.error('create client_group error, e=%s' % (e))

    result = {'data': {'id': client_group.id, 'title': client_group.title}, 'error': error}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def rename_client_group(request, dajax):
    '''重命名客户群'''
    client_id = int(request.POST.get('client_id', 0))
    title = request.POST.get('title', "")
    note = request.POST.get('note', "")
    call_back = request.POST.get('call_back', "")

    error = ""
    client_group = None
    try:
        client_group = ClientGroup.objects.get(id = client_id)
        client_group.title = title
        client_group.note = note
        client_group.save()
    except Exception, e:
        error = '修改客户群失败,e = %s' % (e)
        log.error('rename client_group error, e=%s' % (e))

    result = {'data': {'id': client_id, 'title': title, 'note': note}, 'error': error}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def get_client_list(request, dajax):
    ''''获取客户群列表'''
    psuer_id = request.POST.get('psuer_id', 0)
    call_back = request.POST.get('call_back')
    result = []
    if psuer_id:
        client_list = ClientGroup.objects.filter(create_user__id = psuer_id)

        for c in client_list:
            result.append({'id': c.id, 'name': c.title})

    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def switch_client(request, dajax):
    '''切换用户群'''
    client_id = request.POST.get('client_id', 0)
    shop_ids = request.POST.get('shop_ids', '[]')
    old_client_id = request.POST.get('old_client_id', 0)
    call_back = request.POST.get('call_back')

    err = ''
    if old_client_id and client_id:
        try:
            id_list = [int(i) for i in eval(shop_ids)]

            del_client = ClientGroup.objects.get(id = old_client_id)
            add_client = ClientGroup.objects.get(id = client_id)

            del_client.delete_id_list(del_id_list = id_list)
            add_client.save_id_list(add_id_list = id_list)
        except Exception, e:
            err = '获取客户组错误,%s' % (e)
            log.error('switch_client error err=%s' % (err))
    else:
        err = "参数错误"

    result = {'id_list': id_list, 'err': err}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def add_or_del_client(request, dajax):
    '''删除或添加客户群'''
    client_id = request.POST.get('client_id', 0)
    shop_ids = request.POST.get('shop_ids', '[]')
    mode = request.POST.get('mode', 'add')
    call_back = request.POST.get('call_back')
    err, id_list, title = '', [], ''
    if client_id:
        try:
            id_list = [int(i) for i in json.loads(shop_ids)]
            client_group = ClientGroup.objects.get(id = client_id)
            title = client_group.title
            if mode == 'add':
                if client_group.group_type in [1, 2]:
                    _id_list = list(Customer.objects.filter(shop_id__in = id_list, consult = get_psuser(request)).values_list('shop_id', flat = True))
                    if _id_list:
                        client_group.save_id_list(add_id_list = _id_list)
                    else:
                        err = '非本人客户不允许添加'
                else:
                    client_group.save_id_list(add_id_list = id_list)
            elif mode == 'del':
                client_group.delete_id_list(del_id_list = id_list)
        except Exception, e:
            err = '获取客户组错误,%s' % (e)
            log.error('add_or_del_client error err=%s' % (err))
    else:
        err = "参数错误"

    result = {'client_id':client_id, 'id_list': id_list, 'err': err, 'title': title, 'mode': mode}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def add_all_query_customer(request, dajax):
    psuser = get_psuser(request)
    client_group_id = int(request.POST.get('client_group_id', 0))
    call_back = request.POST.get('call_back')

    result = {'error': ""}
    try:
        client_group = ClientGroup.objects.get(id = client_group_id)
        old_id_list = eval(client_group.id_list) if client_group.id_list else []
        client_group.id_list = list(set(get_consult_ids_bycache(psuser.id) + old_id_list))
        client_group.save()
    except Exception, e:
        result['error'] = "保存失败，e=%s" % (e)

    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def add_all_unquery_customer(request, dajax):
    def get_customers(kwargs):
        mapping = {
            'shop_id': ('shop_id', int),
            'nick': ('nick__contains', str),
            'qq': ('qq__contains', str),
            'phone': ('phone__contains', str),
            'id_list_textarea': ('shop_id__in', lambda id_list_str: \
                map(int, id_list_str.strip().replace(' ', '').split(',')))
        }

        customer_cursor = Customer.objects.only('shop_id')
        filter_args = {}
        for key, val in kwargs.items():
            if key in mapping and val:
                attr, format_func = mapping[key]
                filter_args.update({attr: format_func(val)})

        return [cust.shop_id for cust in customer_cursor.filter(**filter_args)]

    client_group_id = int(request.POST.get('client_group_id', 0))
    call_back = request.POST.get('call_back')
    result = {'error': ""}
    try:
        client_group = ClientGroup.objects.get(id = client_group_id)
        client_group.id_list = list(set(get_customers(request.POST) + eval(client_group.id_list)))
        client_group.save()
    except Exception, e:
        result['error'] = "保存失败，e=%s" % (e)

    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def get_plan_list_info(request, dajax):
    """获取计划信息"""
    psuser = get_psuser(request)
    plan_id_list = json.loads(request.POST['plan_id_list'])
    start_time = request.POST.get('start_time', "").strip()
    end_time = request.POST.get('end_time', "").strip()
    call_back = request.POST.get('call_back')
    plan_id_list = map(int, plan_id_list)

    error = ""
    result = {'error': error, 'data': {}, 'describption': {}}
    try:
        plan_cursor = Plan.objects.filter(id__in = plan_id_list)

        data = {}
        for plan in plan_cursor:
            if start_time or end_time:
                event_list = plan.event_list.split(',')
                time_scope = (string_2date(start_time), string_2date(end_time))
                psuser_list = plan.get_plan_recursive_info()
                plan_statis = Plan.generate_process(event_list, time_scope, psuser_list)
            else:
                plan_statis = plan.generate_plan_process()

            temp_dict = {}
            for event_name, event_data in plan_statis.items():
                temp_dict.update({event_name: event_data['counter']})
            plan_data = [(e_name, e_data) for e_name, e_data in temp_dict.items()]
            plan_data.sort(key = lambda x: x[0])
            data.update({plan.id: plan_data})

        describption = get_event_describe()
        result.update({
            'data': data,
            'describption': describption,
        })
    except Exception, e:
        log.error('loading plan process error, plan_list=%s, e=%s' % (plan_id_list, e))
        error = "加载计划进展失败"

    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def get_event_num(request, dajax):
    """获取事件统计个数"""
    start_time = request.POST.get('start_time', "").strip()
    end_time = request.POST.get('end_time', "").strip()
    psuser_list = json.loads(request.POST.get('psuser_list', ""))
    event_list = json.loads(request.POST.get('event_list', []))
    call_back = request.POST.get('call_back')

    error = ""
    result = {'error': error, 'data': {}, 'describption': {}}
    try:
        data = {}
        time_scope = (string_2date(start_time), string_2date(end_time))
        plan_statis = Plan.generate_process(event_list, time_scope, psuser_list)

        temp_dict = {}
        for event_name, event_data in plan_statis.items():
            temp_dict.update({event_name: event_data['counter']})
        data = [(e_name, e_data) for e_name, e_data in temp_dict.items()]

        describption = get_event_describe()
        result.update({
            'data': data,
            'describption': describption,
        })
    except Exception, e:
        log.error('loading event_num error,  e=%s' % (e))
        error = "加载计划进展失败"

    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def sync_order(request, dajax):
    nick_list = json.loads(request.POST.get('nick_list', ""))
    call_back = request.POST.get('call_back', "")
    if nick_list:
        nick_list = [nick.strip() for nick in nick_list if nick.strip()]
        error = ""
        try:
            syncer_list = OrderSyncer.objects.all()
            result_data = []
            for syncer in syncer_list:
                data = syncer.sync_bizorder_bynick(nick_list)
                result_data.extend(data)
        except Exception, e:
            log.error("sync order error, e=%s" % e)
            error = "请联系开发人员, e=%s" % e
    else:
        error = "请求参数有误"

    result = {"error": error, 'data': result_data}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def get_plan_event_detail(request, dajax):
    """获取统计事件详情"""
    plan_id = int(request.POST.get("plan_id", 0))
    event_name = request.POST.get("event_name", 0)
    start_time = request.POST.get('start_time', "").strip()
    end_time = request.POST.get('end_time', "").strip()
    #     psuser_list = json.loads(request.POST.get('psuser_list', []))
    call_back = request.POST.get('call_back')

    #     re_match = re.compile(r"^201[0-9]-[01][0-9]-[0-3][0-9]$") # 此处有手动输入之嫌
    #     if re_match.match(start_time) and re_match.match(end_time) and psuser_list:
    error = ""
    data = []
    table_name = ""
    shop_counter = 0
    limit = 100
    try:
        if not plan_id:
            error = "服务器较忙，请刷新浏览器重试"
        else:
            plan = Plan.objects.get(id = plan_id)
            if plan and event_name:
                if start_time or end_time:
                    start_date = string_2date(start_time)
                    end_date = string_2date(end_time)
                else:
                    start_date, end_date = plan.start_time, plan.end_time
                psuser_list = plan.get_plan_recursive_info()
                if event_name in EVENT_CONF:
                    event_obj = EVENT_CONF[event_name]
                    sql = event_obj.get_detail_sql(start_date, end_date, psuser_list, limit)
                    shop_counter_sql = event_obj.get_shop_counter_sql(start_date, end_date, psuser_list)
                    table_name = event_obj.sql_dict.get("table_name")
                    data = execute_query_sql(sql)
                    shop_counter = execute_query_sql(shop_counter_sql)[0].get('num', 0)
                else:
                    error = "不能存在该事件统计指标，请联系开发人员"
            else:
                error = "参数出错，请联系开发人员"
    except Exception, e:
        error = e
    # else:
    #         error = "时间输入有误" if psuser_list else "无搜索人员，请联系管理员。"

    result = {'data': data, "shop_counter": shop_counter, 'mark': table_name, \
              'event_name': event_name, 'error': error}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def get_event_detail(request, dajax):
    """获取统计事件详情"""
    event_name = request.POST.get("event_name", 0)
    start_time = request.POST.get('start_time', "").strip()
    end_time = request.POST.get('end_time', "").strip()
    psuser_list = json.loads(request.POST.get('psuser_list', []))
    call_back = request.POST.get('call_back')

    #     re_match = re.compile(r"^201[0-9]-[01][0-9]-[0-3][0-9]$") # 此处有手动输入之嫌
    #     if re_match.match(start_time) and re_match.match(end_time) and psuser_list:
    error = ""
    data = []
    table_name = ""
    shop_counter = 0
    limit = 100
    try:
        if event_name:
            start_date = string_2date(start_time)
            end_date = string_2date(end_time)

            if event_name in EVENT_CONF:
                event_obj = EVENT_CONF[event_name]
                sql = event_obj.get_detail_sql(start_date, end_date, psuser_list, limit)
                shop_counter_sql = event_obj.get_shop_counter_sql(start_date, end_date, psuser_list)
                table_name = event_obj.sql_dict.get("table_name")
                data = execute_query_sql(sql)
                shop_counter = execute_query_sql(shop_counter_sql)[0].get('num', 0)
            else:
                error = "不能存在该事件统计指标，请联系开发人员"
        else:
            error = "参数出错，请联系开发人员"
    except Exception, e:
        error = e
    # else:
    #         error = "时间输入有误" if psuser_list else "无搜索人员，请联系管理员。"

    result = {'data': data[:100], "shop_counter": shop_counter, 'mark': table_name, \
              'event_name': event_name, 'error': error}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def delete_client_group(request, dajax):
    '''删除客户群'''
    client_id = int(request.POST.get('client_id', 0))
    call_back = request.POST.get('call_back')
    error = ''
    if client_id:
        try:
            ClientGroup.objects.get(id = client_id).delete()
        except Exception, e:
            error = "id不存在"
            log.error('delete_client_group error e=%s' % (e))
    else:
        error = "输入参数不完整"
    result = {'data': {'id': client_id}, 'error': error}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def delete_event(request, dajax):
    '''删除事件信息'''
    try:
        call_back = request.POST.get('call_back')
        event_id = request.POST.get('event_id')
        model_type = request.POST.get('model_type')
        error = ''
        if model_type == 'Subscribe':
            Subscribe.objects.filter(id = event_id).delete()
        else:
            event_coll.remove({'_id': ObjectId(event_id), 'type': model_type.lower()})
    except Exception, e:
        log.error('delete_event error e=%s' % (e))
        error = '异常，请联系开发人员'
    result = {'error': error, 'event_id': event_id}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax


def check_write_today(request, dajax):
    """检查今天是否写过日志，一天只允许写一篇"""
    try:
        me = get_psuser(request)
        has_written = Diary.objects.filter(create_time__gte = date_2datetime(datetime.date.today()), author = me).exists()
        dajax.script("PT.%s(%s);" % (request.POST['callback'], has_written and 'true' or 'false'))
    except Exception, e:
        msg = "出错了，请联系管理员！"
        log.error("check today write diary error, e=%s" % e)
        dajax.script("PT.alert('%s');" % msg)
    return dajax


def save_diary(request, dajax):
    """保存日志，这里兼容更改和新写"""
    try:
        me = get_psuser(request)
        diary_id = int(request.POST.get('diary_id', 0))
        content = request.POST.get('content', '').replace('<body', '<p').replace('</body>', '</p>').replace('id_diary_list', '')
        todolist = request.POST.get('todolist', '').replace('<body', '<p').replace('</body>', '</p>').replace('id_diary_list', '')
        if diary_id == 0:
            if Diary.objects.filter(create_time__gte = date_2datetime(datetime.date.today()), author = me).exists(): # 写过日志
                raise Exception("already_wrote")
            diary = Diary.objects.create(content = content, todolist = todolist, author = me)
        else:
            diary = Diary.objects.get(id = diary_id)
            if diary.author and diary.author != me:
                raise Exception("not_author")
            else:
                diary.content = content
                diary.todolist = todolist
                diary.save()
        dajax.script("PT.%s('%s', %s);" % (request.POST['callback'], diary_id, json.dumps({'content':content, 'todolist':todolist})))
    except Exception, e:
        reason = str(e)
        if reason == "already_wrote":
            msg = "今天已经写过日志，请刷新后重试哟！"
        elif reason == "not_author":
            msg = "您不是该日志的作者，无法编辑！"
        else:
            msg = "保存出错，请联系管理员！"
            log.error("save diary error, e=%s" % e)
        dajax.script("PT.alert('%s');" % msg)
    return dajax


def save_diary_comment(request, dajax):
    """日志点评"""
    try:
        me = get_psuser(request)
        diary_id = int(request.POST.get('diary_id', 0))
        comment = request.POST.get('comment', '').replace('<body', '<p').replace('</body>', '</p>').replace('id_diary_list', '')
        diary = Diary.objects.get(id = diary_id)
        if me.name_cn not in diary.author.manager:
            raise Exception("no_permission")
        else:
            diary.comment = comment
            diary.commenter = me
            diary.comment_time = datetime.datetime.now()
            diary.save()
        dajax.script("PT.%s('%s', %s);" % (request.POST['callback'], diary_id, json.dumps({'comment':comment, 'comment_time':datetime.datetime.strftime(diary.comment_time, '%Y年%m月%d日 %H:%M:%S'), 'name_cn':me.name_cn})))
    except Exception, e:
        reason = str(e)
        if reason == "no_permission":
            msg = "您无权点评TA的日志！"
        else:
            msg = "点评出错，请联系管理员！"
            log.error("save comment error, e=%s" % e)
        dajax.script("PT.alert('%s');" % msg)
    return dajax


def change_psw(request, dajax):
    try:
        me = get_psuser(request)
        old_psw = request.POST.get('old_psw', '')
        new_psw = request.POST.get('new_psw', '')
        if me.password == md5.new(old_psw).hexdigest():
            me.password = md5.new(new_psw).hexdigest()
            me.save()
            dajax.script("PT.alert('保存成功！');")
        else:
            dajax.script("PT.alert('当前密码输入有误！');")
    except Exception, e:
        log.error('change psw error, psuser=%s, e=%s' % (me.id, e))
        dajax.script("PT.alert('更改失败，请联系管理员！');")

    return dajax


def get_rpt_snap(request, dajax):
    from apps.mnt.models_monitor import ReportSnap
    today = datetime.date.today()
    start_time = datetime.datetime(year = today.year - 1, month = today.month, day = today.day)
    rpt_snaps = ReportSnap.objects.filter(date__gt = start_time).order_by('date')
    rpt_list = []
    for rpt in rpt_snaps:
        rpt_list.append({'obj_type': rpt.object_type, 'mnt_type': rpt.mnt_type,
                         'count': rpt.count, 'conv_days': rpt.conv_days,
                         'date': rpt.date.strftime('%Y-%m-%d'), 'sum_days': rpt.sum_days,
                         'impressions': rpt.impressions, 'click': rpt.click, 'cost': round(rpt.cost * 1.0 / 100, 2),
                         'pay': round(rpt.pay * 1.0 / 100, 2), 'paycount': rpt.paycount,
                         'ctr': round(rpt.ctr * 100, 2), 'cpc': round(rpt.cpc * 1.0 / 100, 2), 'roi': rpt.roi
                         })
    dajax.script('PT.RptSnap.get_data_back(%s)' % json.dumps(rpt_list))
    return dajax


def get_timer_log(request, dajax):
    def get_log_type(tj_type, tl):
        if tj_type == 'info':
            return '%s_%s' % (tl.log_type, tl.sub_type)
        else:
            return get_error_type(tl.log_type)

    def get_error_type(e_str):
        flag_list = [('Remote service error', 'isp'), ('session', 'session'), ('App Call limited', 'limited'), ('isp', 'isp')]
        for flag_str, type_str in flag_list:
            if flag_str in e_str:
                return type_str

        error_list = ['others', 'unknow_e', 'unformart']
        if e_str in error_list:
            return e_str

        return 'know_others'

    from apps.mnt.models_monitor import TimerLog
    today = datetime.date.today()
    start_time = datetime.datetime(year = today.year - 1, month = today.month, day = today.day)
    tls = TimerLog.objects.filter(create_time__gt = start_time).order_by('create_time')

    test_dict = {}
    for tl in tls:
        if tl.type == 'error':
            test_dict.setdefault(tl.log_type, 0)
            test_dict[tl.log_type] += tl.count

    # test_list = test_dict.items()
    # test_list.sort(key= lambda k:k[1])
    # print '=========== timer error log type ================'
    # import pprint
    # pprint.pprint(test_list)
    # print '================================================='

    result_dict = {'info': {}, 'error': {}}
    for tl in tls:
        l_type = get_log_type(tl.type, tl)
        result_dict[tl.type].setdefault(tl.tj_time, {}).setdefault(l_type, 0)
        result_dict[tl.type][tl.tj_time][l_type] += tl.count
    dajax.script('PT.TaskRpt.get_data_back(%s)' % json.dumps(result_dict))
    return dajax


def mark_virtual_record(request, dajax):
    """标记虚拟物品已经兑换"""
    callback = request.POST.get('callback')
    id = request.POST.get('id')

    result = pa_coll.update({'_id': ObjectId(id)}, {'$set': {'exchange_status': 1}})

    data = {'msg': ''}

    if not (result['ok'] and result['updatedExisting']):
        data = {'msg': 'fail'}

    dajax.script('%s(%s);' % (callback, json.dumps(data)))
    return dajax


def remove_gift_record(request, dajax):
    """删除兑换记录"""
    callback = request.POST.get('callback')
    id = request.POST.get('id')

    result = pa_coll.update({'_id': ObjectId(id)}, {'$set': {'is_freeze': 1}})

    data = {'msg': ''}

    if not (result['ok'] and result['updatedExisting']):
        data = {'msg': 'fail'}

    dajax.script('%s(%s);' % (callback, json.dumps(data)))
    return dajax


def perfect_logistics(request, dajax):
    """填写实物兑换的物流信息"""
    callback = request.POST.get('callback')
    id = request.POST.get('id')
    logistics_id = request.POST.get('logistics_id')
    logistics_name = request.POST.get('logistics_name')

    result = pa_coll.update({'_id': ObjectId(id)}, {'$set':{'logistics_state':1, 'logistics_id':logistics_id, 'logistics_name':logistics_name}})

    data = {'msg': ''}

    if not (result['ok'] and result['updatedExisting']):
        data = {'msg': 'fail'}

    dajax.script('%s(%s);' % (callback, json.dumps(data)))
    return dajax


def change_point(request, dajax):
    """自定义"""
    from apps.web.point import PointModify
    callback = request.POST.get('callback')
    shop_id = int(request.POST.get('shop_id', 0))
    point = int(request.POST.get('point'))
    desc = request.POST.get('desc')
    psuser = get_psuser(request)

    title = "派生科技：{} 修改积分".format(psuser.name_cn)
    desc = "{}, {}.".format(title, desc) if desc else title
    consult_id = psuser.id
    is_valid, msg, data = PointModify.add_point_record(shop_id = shop_id, \
                                                       consult_id = consult_id, point = point, desc = desc)
    data = {'data': data, 'msg': msg}

    dajax.script('%s(%s);' % (callback, json.dumps(data)))
    return dajax


def create_sale_link(request, dajax):
    """创建推广链接"""
    link_name = request.POST.get('link_name', None)
    param_str = request.POST.get('param_str', None)
    desc = request.POST.get('desc', None)

    if link_name and param_str:
        SaleLink.objects.create(link_name = link_name, param_str = param_str, desc = desc)
        dajax.script("window.location.reload()")
    else:
        dajax.script("PT.alert('错误：连接名称和参数接口不能为空!');")
    return dajax


def delete_sale_link(request, dajax):
    """创建推广链接"""
    sale_link_id = int(request.POST.get('sale_link_id', None))

    if sale_link_id:
        SaleLink.objects.filter(id = sale_link_id).delete()
        dajax.script("window.location.reload()")
    else:
        dajax.script("PT.alert('参数错误：id');")
    return dajax


# ===============================================================================
# consult_manager ajax-->start
# ===============================================================================
# 保留
def refresh_consult(request, dajax):
    if PSUser.refresh_now_load():
        dajax.script("PT.alert('刷新成功，即将刷新页面！', null, function () {window.location.reload();});")
    else:
        dajax.script("PT.alert('刷新失败，请联系管理员！');")
    return dajax


# 保留
def update_consult_weight(request, dajax):
    """修改顾问权重"""
    result = 0
    try:
        callback = request.POST['callback']
        psuser = get_psuser(request)
        if 'A' in psuser.perms or psuser.position == 'COMMANDER':
            weight_dict = json.loads(request.POST['weight_dict'])
            if weight_dict:
                PSUser.objects.all().update(weight=0)
                sql = "update ncrm_psuser set weight=case id "
                for _id, weight in weight_dict.items():
                    sql += "when %s then %s " % (int(_id), int(weight))
                sql += "else weight end where id in (%s)" % (','.join(weight_dict.keys()))
                execute_manage_sql(sql)
                result = 1
        else:
            result = 2
    except Exception, e:
        log.error('update_consult_weight error, e=%s' % e)
    dajax.script("%s(%s);" % (callback, result))
    return dajax


# 保留
def distribute_customer(request, dajax):
    """将一个顾问绑定的客户分发给其它顾问"""
    try:
        dis_dict = {}
        main_consult_id = int(request.POST['consult_id'])
        dis_list = json.loads(request.POST['dis_list'])
        customer_type = int(request.POST['customer_type'])
        for diser in dis_list:
            dis_dict.update({diser['consult_id']: diser['dis_count']})
        extra_sql_str = ''
        if customer_type == 1:
            extra_sql_str = 'and a.end_date>current_date'
        elif customer_type == 2:
            extra_sql_str = 'and a.end_date<=current_date'
        elif customer_type == 3:
            sp_group = ClientGroup.objects.filter(create_user_id = main_consult_id, group_type = 1)
            if sp_group:
                try:
                    id_list = eval(sp_group[0].id_list)
                    if type(id_list) == list and id_list:
                        extra_sql_str = 'and a.shop_id not in (%s)' % (','.join(map(str, id_list)))
                except:
                    pass
        elif customer_type == 4:
            sp_group = ClientGroup.objects.filter(create_user_id = main_consult_id, group_type = 2)
            if sp_group:
                try:
                    id_list = eval(sp_group[0].id_list)
                    if type(id_list) == list and id_list:
                        extra_sql_str = 'and a.shop_id in (%s)' % (','.join(map(str, id_list)))
                except:
                    pass
        for consult_id, customer_count in dis_dict.items():
            sql = """
            update ncrm_subscribe c join (
            select a.shop_id as shop_id, a.id as id from ncrm_subscribe a join (
            select max(id) as id from ncrm_subscribe where (article_code='ts-25811' or article_code='FW_GOODS-1921400') and consult_id is not null and start_date<=current_date group by shop_id
            ) b on a.id=b.id where a.consult_id=%s %s limit %s
            ) d on c.shop_id=d.shop_id join ncrm_customer e on c.shop_id=e.shop_id
            set c.consult_id=%s, e.consult_id=%s
            where (c.id>=d.id or c.end_date>current_date) and (c.article_code='ts-25811' or c.article_code='FW_GOODS-1921400') and c.consult_id is not null;
            """ % (main_consult_id, extra_sql_str, customer_count, consult_id, consult_id)
            execute_manage_sql(sql)

        PSUser.refresh_now_load()
        if customer_type != 3:
            ClientGroup.refresh_my_group(main_consult_id, 1)
        if customer_type == 4:
            ClientGroup.refresh_my_group(main_consult_id, 2)
        dajax.script("PT.alert('分发成功！', null, function () {PT.show_loading('正在刷新页面');window.location.reload();});")
    except Exception, e:
        log.error('distribute_customer error, e=%s' % e)
        dajax.script("PT.alert('分发失败，请联系管理员！');")

    return dajax


# ===============================================================================
# 短信管理
# ===============================================================================
def workbench_query(psuser, condition):
    '''模拟工作台的全局查询'''
    try:
        class _request(object):
            GET = MultiValueDict()
            GET.update(condition)
            GET.update({'search_type': 'query_global', 'has_phone': '1'})
            _psuser = psuser

        workbench = WorkBenchConsult(_request, None, None, 'consult')
        workbench.analysis_server_info()
        workbench.group_filter()
        workbench.do_query()
        return workbench
    except Exception, e:
        log.error('ncrm_workbench_query error, e=%s' % e)
        return None


def get_recv_count(request, dajax):
    """计算短信的目标客户数量"""
    try:
        workbench = workbench_query(get_psuser(request), request.POST.copy())
        if workbench:
            dajax.script('%s(%s, %s);' % (request.POST['callback'], json.dumps(workbench.shop_ids), json.dumps(workbench.request.GET)))
            return dajax
    except Exception, e:
        log.error('ncrm_get_recv_count error, e=%s' % e)
    dajax.script("PT.alert('发生异常，请联系研发！');")
    return dajax


def send_sm(request, dajax):
    """批量发送短信"""

    def batch_send_sm(shop_phone_dict, batch_no, content):
        result, _result = {}, {}
        while shop_phone_dict:
            _shop_phone_dict = {}
            while len(_shop_phone_dict) < batch_no and shop_phone_dict:
                shop_id, phone = shop_phone_dict.popitem()
                _shop_phone_dict[shop_id] = phone
            try:
                _result = send_sms(_shop_phone_dict.values(), content)
            except Exception, e:
                log.error('batch_send_sm error, e=%s' % e)
            else:
                if 'code' in _result:
                    if _result['code'] == 0:
                        result.update(_shop_phone_dict)
                    elif _result['code'] == -1: # 余额不足
                        break
        return result, _result.get('tmoney', 0)

    try:
        psuser = get_psuser(request)
        callback = request.POST['callback']
        sm_id = request.POST.get('sm_id', 0)
        if sm_id: # 重试
            sm_id = ObjectId(sm_id)
            condition = sm_coll.find_one({'_id': sm_id}).get('condition', {})
            shop_ids = workbench_query(psuser, condition).shop_ids
            existed_shop_ids = [doc['shop_id'] for doc in smr_coll.find({'sm_id': sm_id}, {'shop_id': 1})]
            shop_ids = list(set(shop_ids) - set(existed_shop_ids))
        else: # 新建
            if 'A' not in psuser.perms:
                dajax.script("PT.alert('没有权限发送新短信，联系部长处理！');")
                return dajax
            shop_ids = json.loads(request.POST['shop_ids'])
        shop_phone_dict = dict(
            Customer.objects.filter(shop_id__in = shop_ids).values_list('shop_id', 'phone')) if shop_ids else {}
        success_dict, tmoney = batch_send_sm(shop_phone_dict, 50, request.POST['content']) # 每50个用户电话调用一次API
        send_count = len(success_dict)
        if sm_id:
            sm_coll.update({'_id': sm_id}, {'$inc': {'send_count': send_count}})
        else:
            sm_id = sm_coll.insert({
                'sender': psuser.name_cn,
                'title': request.POST['title'],
                'content': request.POST['content'],
                'send_count': send_count,
                'condition': json.loads(request.POST['condition']),
                'create_time': datetime.datetime.now()
            })
    except Exception, e:
        log.error('send_sm error, e=%s' % e)
        dajax.script("PT.alert('发生异常，请联系研发！');")
    else:
        # 本地存储
        try:
            if success_dict:
                smr_list = [{'sm_id': sm_id, 'shop_id': shop_id, 'phone': phone, 'create_time': datetime.datetime.now()}
                            for shop_id, phone in success_dict.items()]
                insert_many_no = 100
                for i in range((send_count - 1) / insert_many_no + 1):
                    smr_coll.insert(smr_list[i * insert_many_no:(i + 1) * insert_many_no])
            else:
                tmoney = 'null'
        except Exception, e:
            log.error('send_sm error, e=%s, 短信记录存储失败' % e)
        finally:
            dajax.script('%s(%s, %s);' % (callback, send_count, tmoney))

    return dajax


# 保存员工信息的ajax方法
def save_psuser(request, dajax):
    field_list = [
        'name', 'name_cn', 'weight', 'tel', 'id_no', 'education', 'note', 'perms',
        'name_cn', 'contract_end', 'department', 'status', 'cycle_load', 'major',
        'birthday', 'cat_ids', 'contract_start', 'probation_date', 'qq', 'ww', 'entry_date',
        'school', 'phone', 'position', 'residence', 'manager', 'gender', 'now_load'
    ]
    post = request.POST
    psuser = PSUser()
    psuser_id = post.get('id')
    callback = request.POST.get('callback')

    form = PSUserForm(post)
    if form.is_valid():
        if psuser_id:
            psuser = PSUser.objects.get(id = psuser_id)
        else:
            psuser.password = hashlib.md5(Const.DEFAULT_LOGIN_PASS).hexdigest()
            if PSUser.objects.filter(name = post.get('name')):
                data = {'msg': '用户名【<font color=red>%s</font>】已存在，请重新输入' % post.get('name')}
                dajax.script('%s(%s);' % (callback, json.dumps(data)))
                return dajax
        temp_flag = psuser_id and psuser.position in ['RJJH', 'TPAE'] and psuser.status != '离职' and post.get('status') == '离职'
        for key in field_list:
            if key in ['contract_end', 'birthday', 'contract_start', 'entry_date', 'probation_date']:
                if post.get(key):
                    setattr(psuser, key, string_2date(str(post.get(key).encode('utf-8'))))
                else:
                    setattr(psuser, key, None)
            elif key in ['now_load', 'cycle_load', 'weight']:
                if post.get(key):
                    setattr(psuser, key, int(post.get(key).encode('utf-8')))
                else:
                    setattr(psuser, key, 0)
            else:
                setattr(psuser, key, post.get(key, '').strip())
        try:
            psuser.save()
            data = {'msg': '<font color=green>员工信息保存成功！</font>', 'result': 'success', 'psuser_id': psuser.id}
            dajax.script('%s(%s);' % (callback, json.dumps(data)))
            if temp_flag:
                shop_id_list = list(Customer.objects.filter(Q(operater__id=psuser_id) | Q(consult__id=psuser_id)).filter(latest_end__gt=datetime.date.today()).values_list('shop_id', flat=True))
                Customer.get_or_create_servers(shop_id_list)
        except Exception, e:
            log.error('save_contact ERROR, e=%s' % e)
            data = {'msg': '<font color=red>保存员工信息失败，请联系管理员！</font>'}
            dajax.script('%s(%s);' % (callback, json.dumps(data)))
        return dajax
    else:
        data = {'msg': '%s' % form.errors}
        dajax.script('%s(%s);' % (callback, json.dumps(data)))
        return dajax


# psuser用户名唯一性校验
def check_psuser_name_unique(request, dajax):
    post = request.POST
    callback = request.POST.get('callback')
    psuser_id = post.get('id')
    psuser = PSUser.objects.filter(name = post.get('name'))
    data = {'msg': 'none'}
    if psuser:
        if psuser_id == '':
            data = {'msg': '用户名【<font color=red>%s</font>】已存在，请重新输入' % post.get('name')}
    dajax.script('%s(%s);' % (callback, json.dumps(data)))
    return dajax


# 修改额外权限码
def update_perms_code(request, dajax):
    """修改额外权限码"""
    result = 'false'
    try:
        user_id = request.POST['uid']
        perms_code = request.POST['perms_code']
        ad_perms = AdditionalPermission.objects.filter(user = user_id)
        if ad_perms:
            if not perms_code:
                ad_perms.delete()
            else:
                ad_perms.update(perms_code = perms_code)
        elif perms_code:
            AdditionalPermission.objects.create(user_id = user_id, perms_code = perms_code)
        result = 'true'
    except Exception, e:
        log.error('update perms code error, e=%s, user_id=%s' % (e, user_id))

    dajax.script("PT.NcrmWorkbench.update_perms_callback('%s','%s','%s');" % (result, perms_code, user_id))
    return dajax


def reset_shopmngtask(request, dajax):
    """重置店铺任务状态"""
    shop_id = int(request.POST.get('shop_id', 0))
    try:
        if not shop_id:
            raise Exception
        smt, is_created = ShopMngTask.objects.get_or_create(shop_id = shop_id)
        if not is_created:
            smt.last_start_time = None
            smt.status = 1
            smt.run_times = 0
            smt.save()
        msg = '重置店铺任务成功！'
    except Exception, e:
        log.error('reset shopmngtask error, e=%s, shop_id=%s' % (e, shop_id))
        msg = '重置店铺任务失败，请联系系统管理员！'
    dajax.script("PT.alert('%s');" % msg)
    return dajax

def clear_token(request, dajax):
    """清除授权信息"""
    shop_id = int(request.POST.get('shop_id', 0))
    nick = request.POST.get('nick', 0)
    from apilib import SessionCache
    from apps.router.models import AccessToken
    SessionCache.del_cache(shop_id = shop_id)
    AccessToken.objects.filter(nick = nick, platform = 'web').delete()
    dajax.script("PT.alert('清除授权信息成功')")
    return dajax

def exec_shopmngtask(request, dajax):
    """执行店铺任务"""
    result = False
    shop_id = int(request.POST.get('shop_id', 0))
    if shop_id:
        smt, _ = ShopMngTask.objects.get_or_create(shop_id = shop_id)
        result = smt.run_task()
    dajax.script("PT.alert('执行店铺任务%s!')" % (result and '成功' or '失败（原因可能是已过期，在运行，运行失败等）'))
    return dajax


def get_mnt_info(request, dajax):
    """获取自动计划的信息"""
    try:
        shop_id = int(request.POST['shop_id'])
        camp_cur = Campaign.objects.filter(shop_id = shop_id).only('campaign_id', 'title')
        camp_title_dict = {camp.campaign_id: camp.title for camp in camp_cur}
        mnt_camp_list = MntCampaign.objects.filter(shop_id = shop_id).order_by('campaign_id')
        if mnt_camp_list:
            task_info_dict = {}
            mnt_task_list = MntTask.objects.filter(shop_id = shop_id).order_by('-create_time')
            for mnt_task in mnt_task_list:
                if mnt_task.campaign_id not in task_info_dict:
                    task_info_dict.update({mnt_task.campaign_id: []})
                task_info_dict[mnt_task.campaign_id].append(
                    {'_id': str(mnt_task.id), 'create_time': format_datetime(mnt_task.create_time),
                     'status': mnt_task.get_status_display(),
                     'failed_count': mnt_task.failed_count, 'task_type': mnt_task.get_task_type_display(),
                     'opt_list': mnt_task.opt_list,
                     'start_time': format_datetime(mnt_task.start_time),
                     'end_time': format_datetime(mnt_task.end_time)})

            camp_info_list = []
            for mnt_camp in mnt_camp_list:
                temp_task_list = task_info_dict.get(mnt_camp.campaign_id, [])
                camp_info_list.append(
                    {'camp_id': mnt_camp.campaign_id, 'start_time': format_datetime(mnt_camp.start_time),
                     'max_num': mnt_camp.max_num,
                     'mnt_type': '%s: %s' % (
                         mnt_camp.get_mnt_type_display(), camp_title_dict.get(mnt_camp.campaign_id, '')),
                     'task_list': temp_task_list})

            dajax.script('PT.NcrmWorkbench.display_mnt_info(%s)' % (json.dumps(camp_info_list)))
        else:
            dajax.script('PT.alert("亲，该用户未使用任何全自动计划！");')
        return dajax
    except Exception, e:
        log.exception('get_mnt_info error, shop_id=%s, e=%s' % (request.POST['shop_id'], e))
        dajax.script('PT.alert("亲，出错啦，请刷新页面重试！");')
        return dajax


def repair_lastrpt(request, dajax):
    """昨日报表重新下载一遍"""
    try:
        shop_id = int(request.POST['shop_id'])
        dler = Downloader.objects.get(shop_id = shop_id)
        dler.sync_all_struct()
        dler.sync_all_rpt(is_force = True, rpt_days = 1)
        dajax.script("PT.alert('修复成功！');")
    except Exception, e:
        log.error('repair_lastrpt error, e=%s' % e)
        dajax.script("PT.alert('修复数据失败，请联系管理员！');")
    return dajax


def update_mnt_max_num(request, dajax):
    """更改托管宝贝个数"""
    try:
        campaign_id = int(request.POST['camp_id'])
        max_num = int(request.POST.get('max_num', 0))
        MntCampaign.objects.filter(campaign_id = campaign_id).update(set__max_num = max_num)
        dajax.script("PT.alert('修改成功！');")
        return dajax
    except Exception, e:
        log.info('update_mnt_max_num error, shop_id=%s, e=%s' % (request.user.f2, e))
        dajax.script('PT.alert("亲，请刷新页面重试！");')
        return dajax


# 保留
def run_mnt_task(request, dajax):
    """触发长尾托管任务运行"""
    dajax.script('PT.hide_loading();')
    task_id = ObjectId(request.POST['object_id'])
    try:
        mt = MntTask.objects.get(id = task_id)
    except DoesNotExist:
        dajax.script('PT.alert("该任务不存在");')
        return dajax
    task_type = mt.get_task_type_display()
    result = MntTaskMng.run_task(mt, is_force = True)
    msg = '执行【%s】%s' % (task_type, result and '成功' or '失败，可能用户已经过期，或者该计划已被暂停或终止')
    dajax.script('PT.alert("%s");' % msg)
    return dajax


def stop_mnt_campaign(request, dajax):
    """手动终止全自动托管"""
    try:
        campaign_id = request.POST['campaign_id']
        camp = Campaign.objects.only('shop_id').get(campaign_id = campaign_id)
        MntMnger.unmnt_campaign(shop_id = camp.shop_id, campaign_id = campaign_id)
        # 终止成功之后，删除目录缓存
        CacheAdpter.delete(CacheKey.WEB_MNT_MENU % camp.shop_id, 'web')
        CacheAdpter.delete(CacheKey.WEB_ISNEED_PHONE % camp.shop_id, 'web')
        dajax.script("PT.alert('终止成功！');")
    except Exception, e:
        log.exception('unmnt_campaign error, shop_id=%s, e=%s' % (camp.shop_id, e))
        dajax.script("PT.alert('终止失败，请联系管理员！');")
    return dajax


def reset_password(request, dajax):
    """重置密码"""
    psuser_id = request.POST['user_id']
    callback = request.POST.get('callback')
    try:
        if psuser_id:
            psuser = PSUser.objects.get(id = psuser_id)
            psuser.password = hashlib.md5(Const.DEFAULT_LOGIN_PASS).hexdigest()
            psuser.save()
            data = {'msg': '密码初始化成功！'}
        else:
            data = {'msg': '操作异常！'}
        dajax.script('%s(%s);' % (callback, json.dumps(data)))
    except Exception, e:
        log.exception('reset_password error, psuser_id=%s, e=%s' % (psuser_id, e))
        data = {'msg': '密码重置失败，请联系管理员！'}
        dajax.script('%s(%s);' % (callback, json.dumps(data)))
    return dajax


def get_account_report_dict(request, dajax):
    """获取店铺7天报表数据"""
    shop_id_list = json.loads(request.POST['shop_id_list'])
    callback = request.POST['callback']
    account_report_dict = {}
    try:
        _rpt_dict = Account.Report.get_snap_list({'shop_id': {'$in': shop_id_list}}, rpt_days = 7)
        for shop_id, rpt_list in _rpt_dict.items():
            category_list, series_cfg_list = get_trend_chart_data(data_type = 6, rpt_list = rpt_list)
            sum_cost = sum(series_cfg_list[4]['value_list'])
            sum_click = sum(series_cfg_list[1]['value_list'])
            sum_impr = sum(series_cfg_list[0]['value_list'])
            sum_pay = sum(series_cfg_list[5]['value_list'])
            sum_paycount = sum(series_cfg_list[6]['value_list'])
            sum_report = {
                'cost': '%.2f' % sum_cost,
                'click': sum_click,
                'cpc': '%.2f' % (float(sum_cost) / sum_click if sum_click else 0),
                'ctr': '%.2f%%' % (float(sum_click) / sum_impr * 100) if sum_impr else '-',
                'pay': '%.2f' % sum_pay,
                'conv': '%.2f%%' % (float(sum_paycount) / sum_click * 100) if sum_click else '-',
                'roi': '%.2f' % (float(sum_pay) / sum_cost) if sum_cost else '-'
            }

            account_report_dict[shop_id] = [sum_report, category_list, series_cfg_list]
        dajax.script('%s(%s);' % (callback, json.dumps(account_report_dict)))
    except Exception, e:
        log.exception('get_account_report_dict error, shop_id_list=%s, e=%s' % (shop_id_list, e))
        dajax.script("PT.alert('获取店铺报表失败，请联系管理员！');")
    return dajax


def get_event_detail_byshopid(request, dajax):
    """获取事件详情数据"""

    log.info('==========CRM=====START=====get_event_detail_byshopid==========')
    shop_id = int(request.POST['shop_id'])
    psuser = get_psuser(request)
    if shop_id:
        try:
            customer = Customer.objects.get(shop_id = shop_id)
            event_list = customer.bind_events()
            event_list.sort(lambda x, y: cmp(y['create_time'], x['create_time']))
            if event_list and len(event_list) > 0:
                result_info = {
                    'all_event_count': len(event_list),
                    'unsubscribe_count': 0,
                    'comment_count': 0,
                    'software_subscribe_count': 0,
                    'tp_subscribe_count': 0,
                    'pause_count': 0,
                    'reintro_count': 0,
                    'visible_contact_count': 0,
                    'visible_operate_count': 0,
                    'invisible_event_count': 0
                }
                for event in event_list:
                    # if event['psuser_id'] == psuser.id:
                    if 'B' in psuser.perms:
                        event['button'] = '<a href="javascript:void(0);" event_id="%s" model_type="%s" class="btn btn-mini btn-danger delete_event_detail" >删除</a>' % (
                            event['id'], event['model_type'])
                    else:
                        event['button'] = '--'
                    if event['type'] == 'contact':
                        if event['visible']:
                            result_info['visible_contact_count'] += 1
                            event['type'] = 'visible_contact'
                        else:
                            result_info['invisible_event_count'] += 1
                            event['type'] = 'invisible_event'
                    elif event['type'] == 'operate':
                        if event['visible']:
                            result_info['visible_operate_count'] += 1
                            event['type'] = 'visible_operate'
                        else:
                            result_info['invisible_event_count'] += 1
                            event['type'] = 'invisible_event'
                    elif event['type'] == 'comment':
                        result_info['comment_count'] += 1
                    elif event['type'] == 'reintro':
                        result_info['reintro_count'] += 1
                    elif event['type'] == 'unsubscribe':
                        result_info['unsubscribe_count'] += 1
                        refund_style = int(event.get('refund_style', 0))
                        if refund_style == 1:
                            refund_style = '淘宝后台退款'
                        elif refund_style == 2:
                            refund_style = '支付宝退款'
                        elif refund_style == 3:
                            refund_style = '对公银行退款'
                        elif refund_style == 4:
                            refund_style = '对私银行退款'
                        elif refund_style == 5:
                            refund_style = '现金退款'
                        else:
                            refund_style = ''
                        # event['note'] = '【%s %s】%s' % (dict(Unsubscribe.REFUND_TYPE_CHOICES).get(int(event.get('refund_type', 0)), '退款'), refund_style, event['note'])
                        # 退款原因 多选 判断是否是列表
                        if (type(event.get('refund_reason', 0)) == list):
                            resaon_cn = ''
                            for resaon in event.get('refund_reason', 0):
                                resaon_cn += dict(Unsubscribe.REFUND_REASON_CHOICES).get(int(resaon))
                                resaon_cn += '--'
                            event['note'] = '【%s %s】%s' % (resaon_cn, refund_style, event['note'])
                        else:
                            event['note'] = '【%s %s】%s' % (dict(Unsubscribe.REFUND_REASON_CHOICES).get(int(event.get('refund_reason', 0)), '退款'), refund_style, event['note'])

                    elif event['type'] == 'pause':
                        result_info['pause_count'] += 1
                        if not event.get('proceed_date'):
                            event['button'] = '<a href="javascript:void(0);" class="btn btn-mini btn-success proceed" pause_id="%s" pause_date="%s" shop_id="%s" sub_id="%s">取消暂停</a>' % (event['id'], event['create_time'].strftime('%Y-%m-%d'), shop_id, event['event_id'])
                            end_date = Subscribe.objects.get(id = event['event_id']).end_date
                            event['note'] = '【待补%s天】%s' % (max((min(end_date, datetime.date.today()) - event['create_time'].date()).days, 0), event['note'])
                            # event['note'] = '【待补%s天】%s' % (min((end_date - event['create_time'].date()).days, (datetime.date.today() - event['create_time'].date()).days), event['note'])
                        else:
                            event['note'] = '【%s 已开启】%s' % (event['proceed_date'].strftime('%Y-%m-%d'), event['note'])
                            if psuser.id == 111:
                                event['button'] += '<a href="javascript:void(0);" class="btn btn-mini btn-info mt5 del_proceed" pause_id="%s">撤销开启</a>' % event['id']
                    elif event['type'] == 'subscribe':
                        if event['category'] in ['kcjl', 'qn', 'rjjh', 'vip']:
                            result_info['software_subscribe_count'] += 1
                            event['type'] = 'software_subscribe'
                            event['desc'] = '订购软件'
                            event['button'] = '--'
                        else:
                            result_info['tp_subscribe_count'] += 1
                            event['type'] = 'tp_subscribe'
                            event['desc'] = '人工签单'
                    event['create_time'] = event['create_time'].strftime('%Y-%m-%d %H:%M:%S')
                dajax.script('PT.NcrmWorkbench.get_event_detail_callback(%s, %s)' % (
                    json.dumps(event_list), json.dumps(result_info)))
            else:
                dajax.script('PT.alert("该店铺暂无任何事件！");')
        except Exception, e:
            log.exception('get_event_detail error, e=%s' % (e))
            dajax.script('PT.alert("亲，出错啦，请刷新页面重试！");')
    log.info('==========CRM=====END=====get_event_detail_byshopid==========')
    return dajax


def get_server(request, dajax):
    """获取用户所在服务器及服务器信息"""
    try:
        nick = request.POST.get('nick', '')
        port_info_dict = dict(Port.objects.filter(type = 'web').values_list('id', 'domain'))
        np = NickPort.objects.get(nick = nick)
        port_id = np.port.id
    except NickPort.DoesNotExist:
        port_id = 0
    except Exception, e:
        log.error('modify server error, e=%s, nick=%s' % (e, nick))
        dajax.script("PT.alert('获取服务器信息失败，请联系系统管理员！');")
        return dajax
    dajax.script("PT.NcrmWorkbench.display_port_info('%s','%s', %s);" % (nick, port_id, json.dumps(port_info_dict)))
    return dajax


def save_algcfg(request, dajax):
    try:
        cfg_id = request.POST.get('cfg_id', 0)
        update_dict = json.loads(request.POST['update_dict'])
        class_type = request.POST['class_type']
        class_type_dict = {'stg_cfg': (StrategyConfig, strat_cfg_coll),
                           'cmd_cfg': (CommandConfig, cmd_cfg_coll)}
        clss_list = class_type_dict[class_type]
        if update_dict:
            if cfg_id:
                clss_list[1].update({'_id': ObjectId(cfg_id)}, {'$set': update_dict})
            else:
                obj = clss_list[0](**update_dict)
                obj.save()
            clss_list[0].refresh_all_configs()
        dajax.script('PT.hide_loading();')
    except Exception, e:
        log.error(
            'save config error, e=%s, id=%s, class_type=%s, update_dict=%s' % (e, cfg_id, class_type, update_dict))
        dajax.script('PT.alert("保存失败：%s")' % e)
    return dajax


def del_algcfg(request, dajax):
    try:
        cfg_id = request.POST.get('cfg_id', 0)
        class_type = request.POST['class_type']
        class_type_dict = {'stg_cfg': (StrategyConfig, strat_cfg_coll),
                           'cmd_cfg': (CommandConfig, cmd_cfg_coll)}
        class_list = class_type_dict[class_type]
        error_str = ''
        if cfg_id:
            class_list[1].remove({'_id': ObjectId(cfg_id)})
            class_list[0].refresh_all_configs()

    except Exception, e:
        log.error('detele config error, e=%s, id=%s, class_type=%s' % (e, cfg_id, class_type))
        error_str = e
    finally:
        result = {'cfg_id': cfg_id, 'error_str': error_str}
        dajax.script('PT.NcrmStgCfg.del_cfg_back(%s)' % (json.dumps(result)))
        return dajax


def update_server(request, dajax):
    """更改用户所在服务器"""
    result = 0
    nick = request.POST.get('nick', '')
    port_id = request.POST.get('port_id', 2)
    try:
        result = NickPort.objects.filter(nick = nick).update(port = port_id)
        if not result:
            raise Exception('no nick_port record match nick')
        dajax.script("$('#id_edit_port_layer').modal('hide');")
    except Exception, e:
        log.error('update server error, e=%s, nick=%s, port_id=%s' % (e, nick, port_id))
    dajax.script("PT.light_msg('', '修改%s');" % (result and '成功' or '失败'))
    return dajax


def change_customer_info(request, dajax):
    """修改客户标记"""
    shop_id = int(request.POST['shop_id'])
    key = request.POST['key']
    value = int(request.POST['value'])
    call_back = request.POST["call_back"]
    if key != 'advertise_effect':
        value1 = True if value else False
    else:
        value1 = value
    result = Customer.objects.filter(shop_id = shop_id).update(**{key: value1})
    if call_back:
        dajax.script("%s('%s', %s, %s);" % (call_back, key, value, result))
    return dajax


def save_main_ad(request, dajax):
    '''保存首页广告的方法 add by tiansxiaohe 20150910'''
    callback = request.POST.get('callback')
    save_dict = json.loads(request.POST.get('main_ad'))
    try:
        if '_id' not in save_dict:
            save_dict['ad_create_time'] = datetime.datetime.now()
        save_dict['ad_updater'] = request.session.get('psuser_name')
        save_dict['ad_update_time'] = datetime.datetime.now()
        save_dict['ad_display'] = int(save_dict.get('ad_display', 0))
        save_dict['ad_frequency'] = int(save_dict.get('ad_frequency', 0))
        save_dict['ad_start_time'] = string_2datetime(save_dict['ad_start_time'], '%Y-%m-%d %H:%M')
        save_dict['ad_end_time'] = string_2datetime(save_dict['ad_end_time'], '%Y-%m-%d %H:%M')

        if save_dict.get('_id', 0):
            a_id = int(save_dict.pop('_id'))
            MainAd.update_record(a_id, save_dict)
        else:
            save_dict['ad_status'] = 0
            MainAd.add_record(save_dict)
        dajax.script('%s(%s);' % (callback, json.dumps({'result': True, 'msg': '保存成功！'})))
    except Exception, e:
        log.error('save_main_ad error, e=%s' % (e))
        dajax.script('%s(%s);' % (callback, json.dumps({'result': False, 'msg': '保存失败，请联系管理员!'})))
    return dajax


def del_main_ad(request, dajax):
    ''' 删除首页广告 add by tianxiaohe 20150911 '''
    callback = request.POST.get('callback')
    a_id = int(request.POST.get('_id', 0))
    try:
        MainAd.del_record(a_id)
        dajax.script('%s(%s);' % (callback, json.dumps({'result': True, 'obj_id': request.POST.get('_id', 0)})))
    except Exception, e:
        log.error('del_main_ad error, e=%s' % (e))
        dajax.script('%s(%s);' % (callback, json.dumps({'result': False, 'msg': '删除失败，请联系管理员！'})))
    return dajax


def check_main_ad(request, dajax):
    ''' 审核广告 add by tianxiaohe 20150911 '''
    callback = request.POST.get('callback')
    a_id = int(request.POST.get('_id', 0))
    save_dict = {'ad_checker': request.session.get('psuser_name'),
                 'ad_check_time': datetime.datetime.now(),
                 'ad_status': 1}
    try:
        MainAd.update_record(a_id, save_dict)
        dajax.script('%s(%s);' % (callback, json.dumps({'result': True, 'msg': '审核通过！'})))
    except Exception, e:
        log.error('check_main_ad error, e=%s' % (e))
        dajax.script('%s(%s);' % (callback, json.dumps({'result': False, 'msg': '审核失败！'})))
    return dajax


def put_main_ad(request, dajax):
    ''' 投放广告 add by tianxiaohe 20150911 '''
    callback = request.POST.get('callback')
    a_id = int(request.POST.get('_id', 0))
    save_dict = {'ad_status': 2, 'ad_put_time': datetime.datetime.now()}

    try:
        MainAd.update_record(a_id, save_dict)
        dajax.script('%s(%s);' % (callback, json.dumps({'result': True, 'msg': '投放成功！'})))
    except Exception, e:
        log.error('put_main_ad error, e=%s' % (e))
        dajax.script('%s(%s);' % (callback, json.dumps({'result': False, 'msg': '投放成功，请联系管理员！'})))
    return dajax


def add_reminder(request, dajax):
    '''添加提醒'''
    callback = request.POST['callback']
    err_msg = ''
    psuser = get_psuser(request)
    if psuser:
        try:
            receiver_id = int(request.POST['receiver_id'])
            content = request.POST['content']
            receiver = PSUser.objects.get(id = receiver_id)
            reminder_coll.insert({
                'create_time': datetime.datetime.now(),
                'sender_id': psuser.id,
                'receiver_id': receiver_id,
                'department': receiver.department,
                'position': receiver.position,
                'handle_status':-1,
                'content': content
            })
        except Exception, e:
            log.error('ncrm_add_reminder error, e=%s' % e)
            err_msg = '操作失败，请联系研发'
    else:
        err_msg = '请重新登录CRM再操作'
    dajax.script('%s(%s);' % (callback, err_msg))
    return dajax


def remove_reminder(request, dajax):
    '''删除提醒'''
    callback = request.POST['callback']
    reminder_id = request.POST['reminder_id']
    err_msg = ''
    psuser = get_psuser(request)
    if psuser:
        try:
            reminder = reminder_coll.find_one({'_id': ObjectId(reminder_id)})
            if reminder:
                if reminder['sender_id'] == psuser.id:
                    reminder_coll.remove({'_id': ObjectId(reminder_id)})
                else:
                    err_msg = '只有发送人才可以删除提醒'
        except Exception, e:
            log.error('ncrm_remove_reminder error, e=%s' % e)
            err_msg = '操作失败，请联系研发'
    else:
        err_msg = '请重新登录CRM再操作'
    dajax.script('%s(%s);' % (callback, json.dumps({'err_msg': err_msg, 'reminder_id': reminder_id})))
    return dajax


def mark_feedback_handled(request, dajax):
    '''标记提醒为已处理'''
    callback = request.POST['callback']
    feedback_id = int(request.POST['feedback_id'])
    feedback_note = request.POST['feedback_note']
    err_msg = ''
    psuser = get_psuser(request)
    if psuser:
        Feedback.objects.filter(id = feedback_id, consult = psuser).update(handle_status = 1, note = feedback_note)
    else:
        err_msg = '请重新登录CRM再操作'
    dajax.script('%s(%s);' % (callback, json.dumps({'err_msg': err_msg, 'feedback_id': feedback_id})))
    return dajax


def mark_reminder_handled(request, dajax):
    '''标记提醒为已处理'''
    callback = request.POST['callback']
    reminder_id = request.POST['reminder_id']
    err_msg = ''
    psuser = get_psuser(request)
    if psuser:
        try:
            reminder = reminder_coll.find_one({'_id': ObjectId(reminder_id)})
            if reminder:
                if reminder['receiver_id'] == psuser.id:
                    reminder_coll.update({'_id': ObjectId(reminder_id)}, {'$set': {'handle_status': 1}})
                else:
                    err_msg = '只有接收人才可以标记提醒为已处理'
        except Exception, e:
            log.error('ncrm_mark_reminder_handled error, e=%s' % e)
            err_msg = '操作失败，请联系研发'
    else:
        err_msg = '请重新登录CRM再操作'
    dajax.script('%s(%s);' % (callback, json.dumps({'err_msg': err_msg, 'reminder_id': reminder_id})))
    return dajax


def mark_pa_handled(request, dajax):
    '''隐藏好评和积分兑换提醒'''
    callback = request.POST['callback']
    pa_id = request.POST['pa_id']
    err_msg = ''
    psuser = get_psuser(request)
    if psuser:
        pa_coll.update({'_id': ObjectId(pa_id)}, {'$set': {'consult_flag': 1}})
    else:
        err_msg = '请重新登录CRM再操作'
    dajax.script('%s(%s);' % (callback, json.dumps({'err_msg': err_msg, 'pa_id': pa_id})))
    return dajax


def get_my_reminder(request, dajax):
    '''获取给我的提醒信息'''
    callback = request.POST['callback']
    psuser_id = request.session.get('psuser_id', 0)
    if psuser_id:
        crm_reminder = list(
            reminder_coll.find({'receiver_id': psuser_id, 'handle_status':-1}, {'create_time', 'content'}).sort('create_time', -1))
        for reminder in crm_reminder:
            reminder['content'] = truncatechars_ch(reminder['content'], 36)
        dajax.script('%s(%s);' % (callback, json.dumps(crm_reminder)))
    return dajax


def show_feedback(request, dajax):
    '''查看意见反馈'''
    callback = request.POST['callback']
    feedback_id = int(request.POST['feedback_id'])
    feedback = Feedback.objects.select_related('shop').get(id = feedback_id)
    feedback = {
        'id': feedback.id,
        'nick': feedback.shop.nick,
        'content': feedback.content,
        'create_time': feedback.create_time.strftime('%Y-%m-%d')
    }
    dajax.script('%s(%s);' % (callback, json.dumps(feedback)))
    return dajax


def show_ad(request, dajax):
    '''查看公告内容'''
    callback = request.POST['callback']
    ad_id = request.POST['ad_id']
    ad = main_ad_coll.find_one({'_id': int(ad_id)})
    dajax.script('%s(%s);' % (callback, json.dumps(ad)))
    return dajax


def show_reminder(request, dajax):
    '''查看提醒内容'''
    try:
        callback = request.POST['callback']
        reminder_id = request.POST['reminder_id']
        reminder = reminder_coll.find_one({'_id': ObjectId(reminder_id)})
        reminder['create_time'] = reminder['create_time'].strftime('%Y-%m-%d')
        if reminder['sender_id']:
            reminder['sender_name'] = PSUser.objects.get(id = reminder['sender_id']).name_cn
        else:
            reminder['sender_name'] = '系统'
    except Exception, e:
        log.error('ncrm_show_reminder error, e=%s' % e)
    else:
        dajax.script('%s(%s);' % (callback, json.dumps(reminder)))
    return dajax


def show_pa(request, dajax):
    '''查看好评及积分兑换内容'''
    try:
        callback = request.POST['callback']
        pa_id = request.POST['pa_id']
        pa = pa_coll.find_one({'_id': ObjectId(pa_id)})
        pa['create_time'] = pa['create_time'].strftime('%Y-%m-%d %H:%M:%S')
    except Exception, e:
        log.error('ncrm_show_pa error, e=%s' % e)
    else:
        dajax.script('%s(%s);' % (callback, json.dumps(pa)))
    return dajax


def get_login_users(request, dajax):
    '''获取用户登录信息'''
    callback = request.POST['callback']
    psuser_id = request.session.get('psuser_id', 0)
    user_list = CacheAdpter.get(CacheKey.LOGIN_USERS % (psuser_id, datetime.date.today()), 'crm',
                                {}).items() # 缓存值格式：{shop_id:[last_login, nick, phone, qq, is_hide, plateform_type]}
    user_list.sort(lambda x, y: cmp(y[1][0], x[1][0]))
    for _, login_info in user_list:
        login_info[0] = login_info[0].strftime('%Y-%m-%d %H:%M:%S')
        if len(login_info) > 5:
            login_info[5] = dict(PLATEFORM_TYPE_CHOICES).get(login_info[5], '')
    dajax.script('%s(%s);' % (callback, json.dumps({'user_list': user_list})))
    return dajax


def hide_login_info(request, dajax):
    '''隐藏用户登录信息'''
    shop_id = int(request.POST['shop_id'])
    psuser_id = request.session.get('psuser_id', 0)
    login_cache = CacheAdpter.get(CacheKey.LOGIN_USERS % (psuser_id, datetime.date.today()), 'crm', {})
    shop_cache = login_cache.setdefault(shop_id, [])
    if shop_cache:
        shop_cache[4] = shop_cache[4] ^ 1
        CacheAdpter.set(CacheKey.LOGIN_USERS % (psuser_id, datetime.date.today()), login_cache, 'crm', 24 * 60 * 60)
    return dajax


def get_category_tree(request, dajax):
    '''获取用户分类树数据'''

    log.info('==========CRM=====START=====get_category_tree==========')
    try:
        callback = request.POST['callback']
        tree_id = int(request.POST['tree_id'])
        copy_flag = int(request.POST.get('copy_flag', 0))
        is_stat = int(request.POST.get('is_stat', 1))
        psuser_id = int(request.POST.get('psuser_id') or 0)
        if psuser_id:
            psuser = PSUser.objects.get(id=psuser_id)
        else:
            psuser = get_psuser(request)
        if tree_id:
            all_cat_flag = int(request.POST.get('all_cat_flag', 1))
            if all_cat_flag:
                cat_id_list = []
            else:
                cat_id_list = json.loads(request.POST.get('cat_id_list', '[]'))
                cat_id_list = map(int, cat_id_list)
            tree_obj = TreeTemplate.get_tree_byid(tree_id)
            tree_data = build_tree(tree_obj, psuser, is_stat, cat_id_list)
            tree_data['creater'] = tree_obj.creater.name_cn if tree_obj.creater else '系统'
            tree_data['name'] = tree_obj.name
            tree_data['desc'] = tree_obj.desc
            tree_data['tree_type'] = 'CUSTOM' if copy_flag else tree_obj.tree_type
        else:
            tree_data = {
                'name': '我的客户',
                'child_list': [],
                'cond_list': [],
                'tree_type': 'CUSTOM',
                'desc': '',
                'creater': psuser.name_cn
            }
        dajax.script('%s(%s, %s);' % (callback, tree_id, json.dumps(tree_data)))
    except Exception, e:
        dajax.script('PT.alert("发生异常，联系研发");')
        log.error('ncrm_get_category_tree error, e=%s' % e)

    log.info('==========CRM=====END=====get_category_tree==========')
    return dajax


def get_plan_tree(request, dajax):
    '''获取用户计划树数据'''
    try:
        callback = request.POST['callback']
        tree_id = request.POST['tree_id']
        psuser = get_psuser(request)
        if tree_id:
            # tree_doc = PlanTree.get_tree_byid(tree_id)
            # if tree_doc:
            #     tree_obj = PlanTree.get_tree_template(tree_doc)
            #     tree_data = build_tree(tree_obj, psuser, plan_stat=True)
            #     tree_data['desc'] = tree_obj.desc
            #     tree_data['start_time'] = tree_obj.start_time
            #     tree_data['end_time'] = tree_obj.end_time
            # else:
            #     dajax.script('PT.alert("计划树不存在");')
            #     return dajax
            tree_data = PlanTree.get_tree_byid(tree_id, remove_id=True)
            if tree_data:
                build_tree.load_plan_tree_record(tree_id, tree_data['start_time'], tree_data)
            else:
                dajax.script('PT.alert("计划树不存在");')
                return dajax
        else:
            start_date = datetime.date.today() + datetime.timedelta(days=1)
            if start_date.month==12:
                end_date = datetime.date(start_date.year, 12, 31)
            else:
                next_1st = datetime.date(start_date.year, start_date.month+1, 1)
                end_date = next_1st - datetime.timedelta(days=1)
            tree_data = {
                'name': '我的计划',
                'desc': '',
                'shop_count': len(psuser.mycustomers),
                'shop_id_list': [],
                'goal': {},
                'child_list': [],
                'psuser_id': psuser.id,
                'start_time': start_date,
                'end_time': end_date,
                'status': 0,
                'cond_list': []
            }
        dajax.script('%s("%s", %s);' % (callback, tree_id, json.dumps(tree_data)))
    except Exception, e:
        dajax.script('PT.alert("发生异常，联系研发");')
        log.error('ncrm_get_plan_tree error, e=%s' % e)
    return dajax


def operate_category_tree(request, dajax):
    '''创建/修改用户分类树'''
    try:
        callback = request.POST['callback']
        tree_id = int(request.POST['tree_id'])
        tree_data = json.loads(request.POST['tree_data'])
        psuser = get_psuser(request)
        if tree_id == 0:
            tree_obj = TreeTemplate.create_tree(tree_data['name'], tree_data['desc'], json.dumps(tree_data['child_list']),
                                                tree_data['tree_type'], psuser)
            if tree_obj:
                tree_id = tree_obj.id
        else:
            TreeTemplate.update_tree(tree_id, tree_data['name'], tree_data['desc'], json.dumps(tree_data['child_list']),
                                     tree_data['tree_type'])
        dajax.script('%s(%s, %s, 1);' % (callback, tree_id, json.dumps(tree_data)))
    except Exception, e:
        dajax.script('PT.alert("发生异常，联系研发");')
        log.error('ncrm_operate_category_tree error, e=%s' % e)
    return dajax


def operate_plan_tree(request, dajax):
    '''创建/修改计划树'''
    try:
        callback = request.POST['callback']
        tree_id = request.POST['tree_id']
        tree_data = json.loads(request.POST.get('tree_data', '{}'))
        start_time = datetime.datetime.strptime(tree_data['start_time'], '%Y-%m-%d') if 'start_time' in tree_data else ''
        end_time = datetime.datetime.strptime(tree_data['end_time'], '%Y-%m-%d') if 'end_time' in tree_data else ''
        td_time = date_2datetime(datetime.date.today())
        time_is_valid = start_time and end_time and td_time < start_time <= end_time
        psuser = get_psuser(request)
        if tree_id:
            org_tree = PlanTree.get_tree_byid(tree_id)
            if org_tree:
                if request.POST.get('stop_tree_flag', None):
                    pt_coll.update({'_id':ObjectId(tree_id), 'end_time':{'$gt':td_time}}, {'$set':{'end_time': td_time}})
                    dajax.script(callback)
                elif org_tree['status'] == 1 and org_tree['start_time'] <= td_time:
                    dajax.script('PT.alert("已发布且在生效期内的计划树不允许修改！");')
                elif time_is_valid:
                    tree_data['start_time'] = start_time
                    tree_data['end_time'] = end_time
                    # PlanTree.update_tree(tree_id, tree_data)
                    build_tree.refresh_plan_tree(tree_id, tree_data, psuser)
                    dajax.script('%s("%s", %s, 1);' % (callback, tree_id, json.dumps(tree_data)))
                elif not start_time and not end_time:
                    if 'status' in tree_data and tree_data['status'] == 1 and org_tree['status'] == 0:
                        doc_list = list(pt_coll.find({'psuser_id':psuser.id, 'status':1}, {'end_time':True}).sort('end_time', -1).limit(1))
                        if doc_list and doc_list[0]['end_time'] >= org_tree['start_time']:
                            dajax.script('PT.alert("当前发布计划树时，开始日期必须大于%s");' % (doc_list[0]['end_time'].strftime('%Y-%m-%d')))
                            return dajax
                    # PlanTree.update_tree(tree_id, tree_data)
                    build_tree.refresh_plan_tree(tree_id, tree_data, psuser)
                    dajax.script(callback)
                else:
                    dajax.script('PT.alert("开始日期必须大于今天，小于等于结束日期");')
            else:
                dajax.script('PT.alert("计划树不存在");')
        else:
            if time_is_valid:
                tree_data['start_time'] = start_time
                tree_data['end_time'] = end_time
                tree_id = PlanTree.create_tree(tree_data, psuser.id)
                build_tree.refresh_plan_tree(tree_id, tree_data, psuser)
                dajax.script('%s("%s", %s, 1);' % (callback, tree_id, json.dumps(tree_data)))
            else:
                dajax.script('PT.alert("开始日期必须大于今天，小于等于结束日期");')
    except Exception, e:
        dajax.script('PT.alert("发生异常，联系研发");')
        log.error('ncrm_operate_plan_tree error, e=%s' % e)
    return dajax


def del_category_tree(request, dajax):
    '''删除用户分类树'''
    try:
        tree_id = int(request.POST['tree_id'])
        TreeTemplate.delete_tree(tree_id)
        dajax.script('window.location.reload();')
    except Exception, e:
        dajax.script('PT.alert("发生异常，联系研发");')
        log.error('ncrm_del_category_tree error, e=%s' % e)
    return dajax


def del_plan_tree(request, dajax):
    '''删除计划树'''
    try:
        tree_id = request.POST['tree_id']
        callback = request.POST['callback']
        PlanTree.delete_tree(tree_id)
        dajax.script(callback)
    except Exception, e:
        dajax.script('PT.alert("发生异常，联系研发");')
        log.error('ncrm_del_plan_tree error, e=%s' % e)
    return dajax


def save_plan_tree_record(request, dajax):
    '''添加计划树目标记录'''
    try:
        tree_id = request.POST['tree_id']
        nick = request.POST['nick']
        rec_type = request.POST['rec_type']
        rec_value = int(request.POST['rec_value'])
        callback = request.POST['callback']
        psuser = get_psuser(request)
        query = {}
        if nick.isdigit():
            query['shop_id'] = int(nick)
        else:
            query['nick'] = nick
        shop_list = Customer.objects.filter(**query).values_list('shop_id', 'nick')
        if shop_list:
            shop_id, nick = shop_list[0]
        else:
            dajax.script('PT.alert("店铺不存在");')
            return dajax
        if rec_type == 'is_potential' and rec_value == 1:
            ptr_count = ptr_coll.find({'tree_id': ObjectId(tree_id), 'shop_id': shop_id, 'rec_type': 'is_potential', 'rec_value': 1}).count()
            if ptr_count > 0:
                dajax.script('PT.alert("该店铺已经是意向客户");')
                return dajax
        path = None
        tree_data = PlanTree.get_tree_byid(tree_id, remove_id=True)
        if tree_data:
            # tree_obj = PlanTree.get_tree_template(tree_doc)
            # path = build_tree.get_path_by_shop_id(shop_id, tree_obj)
            path = build_tree.get_or_create_path_by_shop_id(shop_id, tree_id, tree_data)
        if path:
            ptr_coll.insert({
                'tree_id': ObjectId(tree_id),
                'path': path,
                'shop_id': shop_id,
                'nick': nick,
                'rec_type': rec_type,
                'rec_value': rec_value,
                'psuser_id': psuser.id,
                'psuser_cn': psuser.name_cn,
                'create_time': datetime.datetime.now()
            })
            # tree_data = build_tree(tree_obj, psuser, plan_stat=True)
            # tree_data['desc'] = tree_obj.desc
            # tree_data['start_time'] = tree_obj.start_time
            # tree_data['end_time'] = tree_obj.end_time
            build_tree.load_plan_tree_record(tree_id, tree_data['start_time'], tree_data)
            dajax.script('%s("%s", %s, "%s", "%s");' % (callback, tree_id, json.dumps(tree_data), path, rec_type))
        else:
            raise Exception("path为空")
    except Exception, e:
        dajax.script('PT.alert("发生异常，联系研发");')
        log.error('ncrm_save_plan_tree_record error, e=%s' % e)
    return dajax


def get_tree_record_list(request, dajax):
    callback = request.POST['callback']
    node_path = request.POST['node_path']
    error = 0
    record_list = []
    try:
        record_list = list(ptr_coll.find({'$or':[{'path': node_path}, {'path': re.compile('^%s_' % node_path)}]}).sort('create_time', -1))
        for doc in record_list:
            if doc['rec_type'] == 'renew_order_pay':
                doc['rec_desc'] = '进账金额 %.2f元' % (doc['rec_value'] / 100.0)
            elif doc['rec_type'] == 'good_comment_count':
                doc['rec_desc'] = '好评数 %s个' % doc['rec_value']
            elif doc['rec_type'] == 'unknown_order_count':
                doc['rec_desc'] = 'SD单量 %s笔' % doc['rec_value']
            elif doc['rec_type'] == 'is_potential':
                doc['rec_desc'] = '意向客户'
            else:
                doc['rec_desc'] = '未知记录，请联系研发'
    except Exception, e:
        log.error('ncrm_get_tree_record_list error, e=%s' % e)
        error = 1
    dajax.script('%s(%s, %s)' % (callback, error, json.dumps(record_list)))
    return dajax


def del_plan_tree_record(request, dajax):
    callback = request.POST['callback']
    record_id = request.POST['record_id']
    error = 0
    try:
        ptr_coll.remove(ObjectId(record_id))
    except Exception, e:
        log.error('ncrm_del_plan_tree_record error, e=%s' % e)
        error = 1
    dajax.script('%s(%s, "%s")' % (callback, error, record_id))
    return dajax


def get_login_records(request, dajax):
    '''获取用户登录记录'''
    callback = request.POST['callback']
    shop_id = int(request.POST['shop_id'])
    login_records = {}
    temp_data = Login.objects.only('create_time').filter(shop_id = shop_id).order_by('-create_time')[:50]
    for _data in temp_data:
        HMS_list = login_records.setdefault(_data.create_time.strftime('%Y-%m-%d'), [])
        HMS_list.append(_data.create_time.strftime('%H:%M:%S'))
    login_records = login_records.items()
    login_records.sort(lambda x, y: cmp(y[0], x[0]))
    login_records = login_records[:7]
    for _, HMS_list in login_records:
        HMS_list.sort()
    dajax.script('%s(%s, %s);' % (callback, shop_id, json.dumps(login_records)))
    return dajax


def common_opt_submit(request, dajax):
    strategy_name = request.POST['strategy_name']
    shop_id_list = request.POST.getlist("shop_id_list[]")
    psuser = get_psuser(request)
    shop_id_list = [int(shop_id) for shop_id in shop_id_list]
    shop_count, camp_count = MntTaskMng.bulk_generate_task_bycmd(shop_id_list = shop_id_list, psuser_id = psuser.id,
                                                                 opter_name = psuser.name_cn, strategy_name = strategy_name)
    # shop_count, camp_count = 1, 2
    dajax.script('PT.NcrmBulkOptimize.opt_submit_back(%s, %s)' % (shop_count, camp_count))
    return dajax


def custom_opt_submit(request, dajax):
    kw_cmd = json.loads(request.POST['kw_cmd'])
    shop_id_list = request.POST.getlist("shop_id_list[]")
    psuser = get_psuser(request)
    shop_id_list = [int(shop_id) for shop_id in shop_id_list]
    shop_count, camp_count = MntTaskMng.bulk_generate_task_bycmd(shop_id_list = shop_id_list, psuser_id = psuser.id,
                                                                 opter_name = psuser.name_cn, kw_cmd_list = [kw_cmd])
    dajax.script('PT.NcrmBulkOptimize.opt_submit_back(%s, %s)' % (shop_count, camp_count))
    return dajax


def submit_command(request, dajax):
    strategy_name = request.POST['strategy_name']
    kw_cmd = json.loads(request.POST['kw_cmd'])
    shop_id_list = request.POST.getlist("shop_id_list[]")
    psuser = get_psuser(request)
    shop_id_list = [int(shop_id) for shop_id in shop_id_list]
    shop_count, camp_count = MntTaskMng.bulk_generate_task_bycmd(shop_id_list = shop_id_list, psuser_id = psuser.id,
                                                                 opter_name = psuser.name_cn, strategy_name = strategy_name,
                                                                 kw_cmd_list = [kw_cmd])
    dajax.script('PT.NcrmBulkOptimize.opt_submit_back(%s, %s)' % (shop_count, camp_count))
    return dajax


def get_opt_camps(request, dajax):
    shop_id = int(request.POST['shop_id'])
    mnt_camps = MntCampaign.objects.filter(shop_id = shop_id)
    camps = Campaign.objects.filter(shop_id = shop_id, online_status = 'online')
    camp_dict = {camp.campaign_id: camp for camp in camps}

    result_list = []
    for mnt_camp in mnt_camps:
        camp = camp_dict.get(mnt_camp.campaign_id, None)
        if camp:
            result_list.append({'campaign_id': mnt_camp.campaign_id, 'title': camp.title})
    dajax.script('PT.NcrmBulkOptimize.opt_camps_back(%s)' % json.dumps(result_list))
    return dajax


def get_opt_adgs(request, dajax):
    shop_id = int(request.POST['shop_id'])
    campaign_id = int(request.POST['campaign_id'])
    adg_cur = adg_coll.find({'shop_id': shop_id, 'campaign_id': campaign_id, 'mnt_type': {'$gt': 0}, 'online_status': 'online'}, {'_id': 1, 'item_id': 1}).limit(10)
    adg_dict = {adg['_id']: adg['item_id'] for adg in adg_cur}
    item_id_list = list(set(adg_dict.values()))
    item_cur = item_coll.find({'shop_id': shop_id, '_id': {'$in': item_id_list}}, {'pic_url': 1, 'title': 1})
    item_dict = {item['_id']: item for item in item_cur}

    result_list = []
    for adg_id, item_id in adg_dict.iteritems():
        item = item_dict.get(item_id, None)
        if item:
            result_list.append({'adgroup_id': adg_id, 'pic_url': item['pic_url'], 'title': item['pic_url']})
    dajax.script('PT.NcrmBulkOptimize.opt_adgs_back(%s)' % json.dumps(result_list))
    return dajax


def get_kw_chart(request, dajax):
    shop_id = int(request.POST['shop_id'])
    campaign_id = int(request.POST['campaign_id'])
    adgroup_id = int(request.POST['adgroup_id'])
    keyword_id = int(request.POST['keyword_id'])

    snap_dict = Keyword.Report.get_snap_list({'shop_id': shop_id, 'campaign_id': campaign_id, 'adgroup_id': adgroup_id, 'keyword_id': keyword_id}, rpt_days = 15)
    snap_list = snap_dict.pop(keyword_id, [])
    category_list, series_cfg_list = get_trend_chart_data(data_type = 4, rpt_list = snap_list)
    dajax.script('PT.NcrmBulkOptimize.kw_chart_back(%s, %s)' % (json.dumps(category_list), json.dumps(series_cfg_list)))
    return dajax


def dryrun_adg(request, dajax):
    shop_id = int(request.POST['shop_id'])
    campaign_id = int(request.POST['campaign_id'])
    adgroup_id = int(request.POST['adgroup_id'])
    kw_cmd = json.loads(request.POST['kw_cmd'])
    strategy_name = request.POST['strategy_name']

    adg, kw_list = temp_strategy_optimize_adgroups_dryrun(shop_id = shop_id, campaign_id = campaign_id,
                                                          adgroup_id = adgroup_id,
                                                          strategy_name = strategy_name, kw_cmd_list = [kw_cmd])
    result_list = []
    optm_desc_dict = {0: '保留', 1: '删除', 2: '降价', 3: '加价', 4: '修改匹配'}
    match_dict = {1: '精准匹配', 4: '广泛匹配'}
    for kw in kw_list:
        match_change_desc = ''
        if kw.new_match_scope:
            kw.optm_type = 4
            match_change_desc = '由%s改为%s' % (match_dict[kw.match_scope], match_dict[kw.new_match_scope])
        temp_kw = {
            "keyword_id": kw.keyword_id,
            "adgroup_id": kw.adgroup_id,
            "campaign_id": kw.campaign_id,
            "word": kw.word,
            "mnt_opt_type": kw.mnt_opt_type or 0,
            "create_days": kw.create_days,
            "max_price": format(kw.max_price / 100.0, '.2f'),
            "new_price": format(kw.new_price / 100.0, '.2f'),
            "qscore": kw.qscore,
            "qscore_dict": kw.qscore_dict or {'qscore': 0},

            "cpm": format(kw.rpt7.cpm / 100.0, '.2f'),
            "avgpos": kw.rpt7.avgpos,
            "favctr": format(kw.rpt7.favctr, '.2f'),
            "favpay": format(kw.rpt7.favpay, '.2f'),

            "g_click": kw.g_click,
            "g_ctr": '%.2f' % kw.g_ctr,
            "g_cpc": format(kw.g_cpc / 100.0, '.2f'),
            "g_competition": kw.g_competition,
            "g_pv": kw.g_pv,
            "g_coverage": kw.g_coverage,
            "g_roi": kw.g_roi,
            "g_paycount": kw.g_paycount,
            "match_scope": kw.match_scope,
            "new_match_scope": kw.new_match_scope,
            "match_change_desc": match_change_desc,
            "optm_reason": kw.optm_reason,
            "optm_type": kw.optm_type,
            "optm_desc": optm_desc_dict[kw.optm_type],
            "is_focus": kw.is_focus and 1 or 0,
            "is_locked": kw.is_locked and 1 or 0,
        }
        temp_kw.update(kw.rpt7.to_dict())
        result_list.append(temp_kw)
    result_list.sort(key = lambda x: x['optm_type'], reverse = True)

    add_kw_list = []
    for kw in adg.add_kw_list:
        new_kw = {
            'word': kw.word,
            'keyword_score': kw.keyword_score,
            'cat_cpc': format(kw.cat_cpc / 100.0, '.2f'),
            'new_price': format(kw.new_price / 100.0, '.2f'),
            'cat_pv': kw.cat_pv,
            'cat_click': kw.cat_click,
            'cat_competition': kw.cat_competition,
            'cat_ctr': format(kw.cat_ctr, '.2f'),
            'coverage': format(kw.coverage / 100.0, '.2f'),
        }
        add_kw_list.append(new_kw)

    dajax.script('PT.NcrmBulkOptimize.dryrun_adg_back(%s, %s, %s)' % (json.dumps(result_list), json.dumps(add_kw_list), adg.user_limit_price))
    return dajax

def update_approval_status(request, dajax):
    try:
        obj_id = request.POST['obj_id']
        approval_status = request.POST['approval_status']
        psuser_id = request.session.get('psuser_id', 0)
        now = datetime.datetime.now()
        result = Subscribe.objects.filter(id = obj_id).update(approval_status = int(approval_status),
                                                              approval_time = now,
                                                              approver_id = psuser_id)
        dajax.script("PT.light_msg('','修改审批状态成功！');$('tr[id=%s] td.approval_time').html('%s')" % (obj_id, now.strftime('%Y-%m-%d %H:%M:%S')))
    except Exception, e:
        log.error('update approval_status error, obj_id=%s, approval_status=%s, e=%s' % (obj_id, approval_status, e))
        dajax.script("PT.alert('修改审批状态失败！')")
    return dajax

def refresh_metric_data(request, dajax):
    '''刷新单个度量维度数据'''
    psuser_id = int(request.POST['psuser_id'])
    psuser = PSUser.objects.get(id = psuser_id)
    metric_name = request.POST['metric_name']
    data_no = request.POST['data_no']
    start_date = request.POST['start_date']
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = request.POST['end_date']
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    callback = request.POST['callback']
    result = refresh_ps_sumval(psuser, metric_name, [start_date, end_date])
    dajax.script('%s(%s, "%s", %s, "%s")' % (callback, psuser_id, metric_name, data_no, result))
    return dajax

def refresh_metric_data_old(request, dajax):
    '''刷新单个度量维度数据'''
    psuser_id = int(request.POST['psuser_id'])
    psuser = PSUser.objects.get(id = psuser_id)
    metric_name = request.POST['metric_name']
    data_no = request.POST['data_no']
    start_date = request.POST['start_date']
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = request.POST['end_date']
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    callback = request.POST['callback']
    result = refresh_ps_sumval(psuser, metric_name, [start_date, end_date])
    dajax.script('%s(%s, "%s", %s, "%s")' % (callback, psuser_id, metric_name, data_no, result))
    return dajax

def get_export_metric_data(request, dajax):
    xfgroup_id = int(request.POST['xfgroup_id'])
    xfgroup = XiaoFuGroup.objects.get(id = xfgroup_id)
    metric_name = request.POST['metric_name']
    data_no = request.POST['data_no']
    start_date = request.POST['start_date']
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = request.POST['end_date']
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    callback = request.POST['callback']
    event_list, _ = get_ps_detail(xfgroup, metric_name, [start_date, end_date])
    dajax.script('%s(%s, "%s", %s, %s)' % (callback, xfgroup_id, metric_name, data_no, json.dumps(event_list)))
    return dajax

def get_metric_details(request, dajax):
    def feed_result(result, _metric_name, _details, psuser_dict):
        result.append(MetricsManager.get_metric_detail_titles(_metric_name))
        for kwargs in _details:
            result.append(MetricsManager.get_metric_detail(_metric_name, psuser_dict=psuser_dict, **kwargs))
        result.append([])

    callback = request.POST['callback']
    file_name = request.POST['file_name']
    result = []
    error = ''
    try:
        metric_name = request.POST['metric_name']
        details = json.loads(request.POST['details'])
        psuser_dict = {obj.id: obj.name_cn for obj in PSUser.objects.all().only('id', 'name_cn')}
        if type(details) == list:
            feed_result(result, metric_name, details, psuser_dict)
        elif type(details) == dict:
            for _metric_name, _details in details.items():
                feed_result(result, _metric_name, _details, psuser_dict)
    except Exception, e:
        error = '发生异常，联系研发'
        log.error('ncrm_get_metric_details error, e=%s' % e)
    dajax.script('%s("%s", "%s", %s)' % (callback, error, file_name, json.dumps(result)))
    return dajax

def get_export_metric_data_old(request, dajax):
    psuser_id = int(request.POST['psuser_id'])
    psuser = PSUser.objects.get(id = psuser_id)
    metric_name = request.POST['metric_name']
    data_no = request.POST['data_no']
    start_date = request.POST['start_date']
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = request.POST['end_date']
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    callback = request.POST['callback']
    event_list, _ = get_ps_detail(psuser, metric_name, [start_date, end_date])
    dajax.script('%s(%s, "%s", %s, %s)' % (callback, psuser_id, metric_name, data_no, json.dumps(event_list)))
    return dajax


def get_performance_income(request, dajax):
    log.info('==========CRM=====START=====get_performance_income==========')
    date_month = request.POST['date_month']
    cfg_dict = json.loads(request.POST.get('cfg_dict', '{}'))
    is_force = bool(int(request.POST.get('is_force', 0)))
    call_back = request.POST['call_back']
    is_success = 0
    xfgroup_list = []
    group_sum_list = []
    person_pay_list = []
    try:
        person_pay_dict = {}
        person_group_dict = {}
        group_dict = {}
        psusers = PSUser.objects.all().only('id', 'name_cn', 'department')
        psuser_dict = {obj.id: obj for obj in psusers}
        xfgroups = XiaoFuGroup.objects.all()
        xfgroup_dict = {obj.id: obj for obj in xfgroups}
        obj_list = Performance.execute(date_month = date_month, perf_cfg = cfg_dict, is_force = is_force)
        for obj in obj_list:
            if obj.xfgroup_id in xfgroup_dict:
                xfgroup_name = xfgroup_dict[obj.xfgroup_id].name
            else: # 兼容旧版销服组，旧版中没有保留销服组快照
                xfgroup_name = '%s组' % psuser_dict[obj.consult_id].name_cn
            person_pay_dict[obj.consult_id] = person_pay_dict.get(obj.consult_id, 0) + obj.consult_pay
            person_pay_dict[obj.seller_id] = person_pay_dict.get(obj.seller_id, 0) + obj.seller_pay
            person_group_dict.setdefault(obj.consult_id, []).append(xfgroup_name)
            person_group_dict.setdefault(obj.seller_id, []).append(xfgroup_name)
            xfgroup_list.append({
                'xfgroup_name': xfgroup_name,
                'xfgroup_id': obj.xfgroup_id,
                'department': obj.department,
                'order_pay': '%.2f' % obj.order_pay,
                'order_pay_rank': obj.order_pay_rank,
                'order_pay_level': obj.order_pay_level,
                'refund_pay': '%.2f' % obj.refund_pay,
                'score': obj.score,
                'score_rank': obj.score_rank,
                'score_level': obj.score_level,
                'team_royalty': '%.0f%%' % (obj.team_royalty * 100),
                'team_pay': '%.2f' % obj.team_pay,
                'consult_royalty': '%.2f%%' % (obj.consult_royalty * 100),
                'consult_pay': '%.2f' % obj.consult_pay,
                'seller_pay': '%.2f' % obj.seller_pay,
                'consult_name': psuser_dict[obj.consult_id].name_cn,
                'seller_name': psuser_dict[obj.seller_id].name_cn,
                'score_detail_list': obj.score_detail_list,
                })
            group_dict.setdefault(obj.department, []).append(obj)

        total_sum_dict = {'department': '全部'}
        sum_key_list = ['order_pay', 'refund_pay', 'score', 'team_pay', 'consult_pay', 'seller_pay']
        total_sum_dict.update({k: 0 for k in sum_key_list})
        for group, obj_list in group_dict.items():
            temp_dict = {'department': group}
            for key in sum_key_list:
                temp_sum = sum([getattr(obj, key) for obj in obj_list])
                temp_dict.update({key: temp_sum})
                total_sum_dict[key] += temp_sum
            group_sum_list.append(temp_dict)
        group_sum_list.insert(0, total_sum_dict)

        for psuser_id, pay in person_pay_dict.items():
            person_pay_list.append({'name': psuser_dict[psuser_id].name_cn,
                                    'department': psuser_dict[psuser_id].get_department_display(),
                                    'pay': '%.2f' % pay,
                                    'xfgroup_list': ','.join(list(set(person_group_dict[psuser_id])))
                                    })
        is_success = 1
    except Exception, e:
        log.error('get_performance_income error, date_month=%s, e=%s' % (date_month, e))
    dajax.script("%s(%s, %s, %s, %s)" % (call_back, is_success, json.dumps(xfgroup_list), json.dumps(person_pay_list), json.dumps(group_sum_list)))

    log.info('==========CRM=====END=====get_performance_income==========')
    return dajax


def save_performance_conf(request, dajax):
    if 'H' in request.session['perms']:
        cfg_dict = json.loads(request.POST['cfg_dict'])
        result = PerformanceConfig.save_perf_cfg(cfg_dict)
        dajax.script("PT.PerformanceIncome.save_cfg_back(%s)" % int(result))
    else:
        dajax.script("PT.alert('你没有权限修改绩效配置')")
    return dajax

def save_xfgroup_perf(request, dajax):
    if 'H' in request.session['perms']:
        date_month = request.POST['date_month']
        cfg_dict = json.loads(request.POST['cfg_dict'])
        score_level_dict = json.loads(request.POST['score_level_dict'])
        result = Performance.save_manual_setting(date_month = date_month, perf_cfg_dict = cfg_dict, score_level_dict = score_level_dict)
        dajax.script("PT.PerformanceIncome.save_xfgroup_perf(%s)" % int(result))
    else:
        dajax.script("PT.alert('你没有权限修改绩效配置')")
    return dajax

def get_cat_name_list(request, dajax):
    log.info('==========CRM=====START=====get_cat_name_list==========')
    try:
        result_list = []
        cat_cur = cat_coll.find({'cat_level': {'$in': [1, 2, 3]}}, {'_id': 1, 'cat_path_id': 1, 'cat_path_name': 1}).sort([('cat_level', 1), ('cat_path_name', 1)])
        result_list = [{'cat_id': cat['_id'], 'cat_path_id': cat['cat_path_id'], 'cat_path_name': cat['cat_path_name']} for cat in cat_cur]
        dajax.script("PT.%s(%s)" % (request.POST['namespace'], json.dumps(result_list)))
    except Exception, e:
        log.error('get_cat_name_list error, e=%s' % e)
        dajax.script("PT.alert('获取类目信息失败！');")
    log.info('==========CRM=====END=====get_cat_name_list==========')
    return dajax

def submit_order_note(request, dajax):
    try:
        psuser = get_psuser(request)
        order_id = int(request.POST.get('order_id'))
        note = request.POST.get("note")
        FuwuOrder._get_collection().update({'order_id': order_id}, {'$set': {
            'note_user': psuser.id,
            'note': note,
            'note_time': datetime.datetime.now()
        }})
        dajax.script("PT.OrderDunning.note_save_callback(%s, '%s');" % (order_id, note))
    except Exception, e:
        log.error("save order note error, e=%s" % e)
        dajax.script("PT.alert('添加备注失败，请联系管理员！');")
    return dajax


def close_fuwuorder(request, dajax):
    callback = request.POST['callback']
    order_id = int(request.POST['order_id'])
    error = ''
    try:
        FuwuOrder._get_collection().update({'order_id': order_id}, {'$set': {'is_closed': 1}})
    except Exception, e:
        log.error("ncrm_close_fuwuorder error, e=%s" % e)
        error = '操作失败，请联系管理员！'
    dajax.script("%s('%s', %s);" % (callback, error, order_id))
    return dajax


def clean_unpaid_order(request, dajax):
    order_coll = FuwuOrder._get_collection()
    result_list = list(order_coll.find({'pay_status': 0, 'is_closed': 0}))
    order_id_list = [i['order_id'] for i in result_list]

    sb_list = Subscribe.objects.filter(order_id__in = order_id_list)

    log.info("there are total %s orders unpaid, but %s are found paid already" % (len(result_list), len(sb_list)))

    for sb in sb_list:
        order_coll.update({'order_id': sb.order_id}, {'$set': {'pay_status': 1}})

    if len(result_list) > len(sb_list):
        # 将超过2天仍然未关注的
        order_coll.update({'pay_status': 0, 'is_closed': 0, 'create_time': {'$lte': date_2datetime(datetime.date.today() - datetime.timedelta(days = 2))}},
                          {'$set':{'is_closed':1, 'manual_close': True}}, multi = True)

    dajax.script("PT.alert('清理成功，请刷新页面!');")
    return dajax

def get_operating_rpt(request, dajax):
    log.info('==========CRM=====START=====get_operating_rpt==========')
    start_date = request.POST['start_date']
    end_date = request.POST['end_date']
    category_list = json.loads(request.POST['category_list'])
    refund_style_list = json.loads(request.POST['refund_style_list'])
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime('%s 23:59:59' % end_date, '%Y-%m-%d %H:%M:%S')
    pay_list = Subscribe.tj_global_pay(start_date, end_date)
    xiaofu_pay_list = Subscribe.tj_global_xiaofu_pay(start_date, end_date)
    refund_list = Unsubscribe.get_global_refund(start_date, end_date, category_list, refund_style_list)
    dajax.script("PT.OperatingRpt.get_rpt_back(%s, %s, %s)" % (json.dumps(pay_list), json.dumps(refund_list), json.dumps(xiaofu_pay_list)))
    log.info('==========CRM=====END=====get_operating_rpt==========')
    return dajax

def get_operating_rpt1(request, dajax):
    log.info('==========CRM=====START=====get_operating_rpt==========')
    start_date = request.POST['start_date']
    end_date = request.POST['end_date']
    category_list = json.loads(request.POST['category_list'])
    refund_style_list = json.loads(request.POST['refund_style_list'])
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime('%s 23:59:59' % end_date, '%Y-%m-%d %H:%M:%S')
    pay_list = Subscribe.tj_global_pay1(start_date, end_date)
    refund_list = Unsubscribe.get_global_refund(start_date, end_date, category_list, refund_style_list)
    dajax.script("PT.OperatingRpt1.get_rpt_back(%s, %s)" % (json.dumps(pay_list), json.dumps(refund_list)))
    log.info('==========CRM=====END=====get_operating_rpt==========')
    return dajax

def get_unsubscribe_img_list(request, dajax):
    call_back = request.POST['call_back']
    error = ""
    img_list = []
    try:
        unsub = list(event_coll.find({'_id':ObjectId(request.POST['unsub_id'])}, {'img_list':True}))
        if unsub:
            img_list = unsub[0]['img_list']
    except Exception, e:
        log.error('get_unsubscribe_img_list error, e=%s' % e)
        error = "发生异常，请联系管理员！"
    if not img_list:
        error = "未找到对应的图片！"
    result = {'error':error, 'img_list':img_list}
    dajax.script("%s(%s);" % (call_back, json.dumps(result)))
    return dajax

def freeze_xfgroup(request, dajax):
    xfgroup_id = request.POST['xfgroup_id']
    XiaoFuGroup.objects.filter(id = int(xfgroup_id)).update(is_active = False, end_time = datetime.datetime.now())
    dajax.script("PT.XFGroupManage.freeze_xfgroup_back(%s)" % (xfgroup_id))
    return dajax

def save_xfgroup_endtime(request, dajax):
    xfgroup_id = request.POST['xfgroup_id']
    end_time = request.POST['end_time']
    update_end_time = None
    if end_time:
        update_end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    XiaoFuGroup.objects.filter(id = int(xfgroup_id)).update(end_time = update_end_time)
    dajax.script("PT.XFGroupManage.save_xfgroup_endtime_back(%s)" % (xfgroup_id))
    return dajax

def get_allocation_record(request, dajax):
    callback = request.POST['callback']
    shop_id = int(request.POST['shop_id'])
    error = 0
    record_list = []
    try:
        record_list = ['%s　%s　将订单%s（%s订购，%s，%.2f元）的工作人员由（%s）改为（%s）' %
                       (doc['psuser_cn'], doc['create_time'].strftime('%Y-%m-%d %H:%M:%S'), doc['subscribe_id'], doc['sub_time'].date(), doc['category_cn'], doc['pay']/100.0, doc['org_cn_list'], doc['new_cn_list'])
                       for doc in ar_coll.find({'shop_id':shop_id}).sort('create_time', -1)]
    except Exception, e:
        error = 1
        log.error('ncrm_get_allocation_record error, shop_id=%s, e=%s' % (shop_id, e))
    dajax.script('%s(%s, %s)' % (callback, error, json.dumps(record_list)))
    return dajax

def get_modify_cus_memberorder(request, dajax):
    callback = request.POST['callback']
    shop_id = int(request.POST['shop_id'])
    is_goldmember = False
    error = 0
    msg = False
    try:
        is_goldmember = Customer.objects.filter(shop_id=shop_id).first().is_goldmember
        if is_goldmember:
            is_goldmember = False
        else:
            is_goldmember = True
        Customer.objects.filter(shop_id=shop_id).update(is_goldmember=is_goldmember)
        msg = True
    except Exception, e:
        error = 1
        log.error('ncrm_get_modify_cus_memberorder error, shop_id=%s, e=%s' % (shop_id, e))
    dajax.script('%s(%s, %s)' % (callback, error, json.dumps({'msg': msg, 'is_goldmember':is_goldmember, 'shop_id':shop_id})))
    return dajax

def search_item_byurl(request, dajax):
    def get_title(html, shop_type):
        tt = html.find('title')[-1].text.lower()
        split_index = tt.rfind('-')
        title = tt[:split_index]
        if u'天猫' in tt or 'tmall' in tt:
            st = shop_type[u'tmall.com天猫']
        elif u'淘宝网' in tt:
            st = shop_type[u'淘宝网']
        else:
            st = shop_type[tt[split_index + 1:]]
        return title, st

    def get_price_cat_id(html):
        if st:
            select_content = 'ul#J_AttrUL li'
            cat_content = 'script'
            cat_id, price = 0, 0
            for rr in html.find(cat_content):
                content = rr.text or ''
                if 'categoryId' in content and not cat_id:
                    start_index = content.find('categoryId') + len('categoryId')
                    try:
                        cat_id = int(content[start_index + 1 :content.find(',', start_index)])
                    except :
                        pass
                for price_str in ['price', 'defaultItemPrice']:
                    if (price_str in content) and not price:
                        start_index = content.find(price_str) + len(price_str)
                        try:
                            price = float(content[start_index + 3 :content.find(',', start_index) - 1])
                        except :
                            continue
                if cat_id and price:
                    break

        else:
            select_content = 'ul.attributes-list li'
            cat_content = 'div#detail-recommend-viewed'
            cat_id = int(html.find(cat_content)[-1].attrib.get('data-catid'))
            price = html.find('em.tb-rmb-num')[-1].text
            if '-' in price:
                try:
                    price = float(price.split('-')[0])
                except Exception, e:
                    log.error("float price error and the error is = %s and url is = %s" % (e, item_url))
                    price = 0
        return cat_id, price, select_content

    def get_shop_args(result_select, st, html):
        attr_list, element_list, property_dict = [], [], {}
        if not result_select:
            if not st:
                rr = html.find("script")
                for r in rr:
                    content = r.text or ''
                    if 'g_config.spuStandardInfo' in content:
#                                 start_index = content.find('g_config.spuStandardInfo')
                        json_list, r_dict = [], {}
                        for kw in content[content.find('{', content.find('g_config.spuStandardInfo')):content.rfind('}') + 1].split(';'):
                            if 'spuStandardInfoUnits' in kw :
                                json_list.append(kw)
                        if json_list:
                            r_dict = json_list[0]
                        for key in r_dict:
                            value = r_dict[key]
                            if value:
                                for vv in value:
                                    for v in vv['spuStandardInfoUnits']:
                                        key = v['propertyName']
                                        value = v['valueName']
                                        attr_list.append(key + ':' + value)
                                        element_list.append(value)
                                        property_dict[key] = value
                            break
                        break
        for li in result_select:
            value = li.text
            value = value.lower()
            attr_list.append(value)
            em_list = []
            for split_sign in split_sign_list:
                if split_sign in value:
                    em_list = value.split(split_sign)
            has_split = False
            if em_list:
                em = em_list[-1]
            property_dict[em_list[0]] = em
            for sl in elem_split_list:
                if sl in em:
                    element_list.extend(em.split(sl)[1:])
                    has_split = True
            if not has_split:
                element_list.append(em)
        return attr_list, element_list, property_dict

    def get_parent_id(cat_id):
        parent_cat_ids = Cat.get_parent_cids(cat_id)
        if not parent_cat_ids:
            parent_cat_id = 0
        else:
            parent_cat_id = parent_cat_ids[-1]
        return parent_cat_id

    def get_pic_url(html):
        pic_url = html.find('img#J_ImgBooth')[-1].attrib.get('data-src')
        if not pic_url:
            pic_url = html.find('img#J_ImgBooth')[-1].attrib.get('src')
        return pic_url

    def get_tmall_role_args(html, attr_list, element_list, property_dict):
        for tr in html.find('div#J_Attrs table tbody tr'):
            td = tr.find('td')
            if td is not None:
                key = tr.find('th').text
                value = td.text
                attr_list.append(key + ':' + value)
                element_list.append(value)
                property_dict[key] = value

        return attr_list, element_list, property_dict

    def get_user_nick(html, st):
        if st:
            return html.find('div#shopExtra div.slogo a strong').text()
        else:
            nick_text = html.find('script').text()
            nick_start_index = nick_text.find('shopName')
            nick_start_index = nick_text.find(':', nick_text.find('sellerNick')) + 1
            nick_end_index = nick_text.find(',', nick_start_index)
            nick = nick_text[nick_start_index:nick_end_index]
            nick = nick.replace("'", '').strip()
            return nick

    item_url = request.POST['item_url']
    callback = request.POST['callback']
    error = ''
    item_data = {}
    shop_type = {u'淘宝网':0, u'tmall.com天猫':1}
    elem_split_list = [u' ', u'\xa0', u'/']

    try:
        item_id = int(dict(parse_qsl(urlparse(item_url).query)).get('id', 0))
        if not item_id:
            error = '请检查宝贝链接是否可用'
        else:
            cachekey = CacheKey.SUBWAY_ITEM_DETAIL % item_id
            item_dict = CacheAdpter.get(cachekey, 'web', {})
            if not item_dict:
                try:
                    r = requests.get(item_url)
                except Exception, e:
                    error = '获取宝贝信息失败，请重试'
                    log.error('ncrm_search_item_byurl crawl item page error, e=%s' % e)
                else:
                    result = pq(r.text)
                    title , st = get_title(result, shop_type)
                    split_sign_list = [u': ', u':', u'\uff1a']
                    cat_id, price, select_content = get_price_cat_id(result)
                    result_select = result.find(select_content)
                    attr_list, element_list, property_dict = get_shop_args(result_select, st, result)
                    if st:
                        attr_list, element_list, property_dict = get_tmall_role_args(result, attr_list, element_list, property_dict)
                    cat_path, _ = Cat.get_cat_path(cat_id_list = [cat_id], last_name = ' ').get(str(cat_id), ['未获取到值', ''])
                    parent_cat_id = get_parent_id(cat_id)
                    pic_url = get_pic_url(result)
                    nick = get_user_nick(result, st)
                    item_dict = {
                               'item_id':item_id,
                               'nick':nick,
                               'pic_url' :'https:' + pic_url,
                               'title':title,
                               'cat_id':cat_id,
                               'parent_cat_id':parent_cat_id,
                               'item_price':price,
                               'property_dict':property_dict,
                               'cat_path':cat_path,
                               'property_list':attr_list
                               }
                    CacheAdpter.set(cachekey, item_dict, 'web')
            if item_dict:
                item = Item.get_item_dict_2_order(item_dict)
                # item._property_dict = {key:[value.replace(u'\xa0', '')] for key, value in item_dict.get('property_dict', {}).items()}
                item.mode = 'precise'
                item_data = {
                    'cat_id': item_dict['cat_id'],
                    'cat_path': item_dict['cat_path'],
                    'prdtword_list': item.get_label_dict.get('P', [])
                }
    except Exception, e:
        error = '发生异常，联系研发'
        log.error('ncrm_search_item_byurl error, item_url=%s, e=%s' % (item_url, e))
    dajax.script('%s("%s", %s)' % (callback, error, json.dumps(item_data)))
    return dajax


def sync_kw_gdata(request, dajax):
    str_string = request.POST['word']
    err_msg = ''
    if not str_string:
        err_msg = '请先输入关键词'
    else:
        try:
            sort_word = RedisKeyManager.get_sort_word(str_string)
            word = KeywordInfo.r_hkeyword.hget(sort_word, 'kw')
            KeywordInfo.r_hkeyword.hset(sort_word, 'kw', str_string)
            gdata_tb_list = str_string.split(',')
            timescope = KeywordInfo.get_gdata_timescope()
            word_dict = get_words_gdata(gdata_tb_list, timescope)
            result_dict = {}
            for word in gdata_tb_list:
                value = '0,0,0.0,0,0.0,0.0,0.0,0,0'
                tmp_word = ChSegement.replace_white_space(word)
                if word in word_dict:
                    result_dict[word] = KeywordInfo.format_gdata_2save_redis(word, word_dict[word])
                else:
                    sort_word = RedisKeyManager.get_sort_word(word)
                    result_dict[word] = {'pv':0, 'click':0, 'cpc':0.0, 'cmpt':0, 'ctr':0.0, 'roi':0.0, 'coverage':0.0, 'favtotal':0, 'transactionshippingtotal':0}
                    KeywordInfo.r_gdata.setex(tmp_word, value, 1 * 24 * 60 * 60)
                    KeywordInfo.r_hkeyword.hmset(sort_word, {'kw':tmp_word})
                    KeywordInfo.r_hkeyword.expire(sort_word, 1 * 24 * 60 * 60)
            KeywordInfo.insert_new_word_list(word_dict.keys())
        except Exception, e:
            log.error('word=%s, e=%s' % (str_string, e))
            err_msg = '同步失败，请联系研发'
    if err_msg:
        dajax.script("PT.alert('%s')" % err_msg)
    else:
        dajax.script("PT.alert('同步成功')")
    return dajax


def get_metric_list(request, dajax):
    start_time = request.POST['start_time']
    end_time = request.POST['end_time']
    callback = request.POST['callback']
    error = ''
    metric_list = []
    try:
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d')
        valid_metric_list = PerformanceConfig.get_metric_indicator_8date(start_time, end_time)
        valid_metric_list += ['renew_order_pay', 'real_renew_order_pay', 'unsubscribe_pay']
        metric_list = [x.to_dict() for x in get_indicators_byposition() if x.name in valid_metric_list]
        metric_list = [{'name': metric['name'], 'name_cn': metric['name_cn'], 'desc': metric['desc']} for metric in metric_list]
    except Exception, e:
        error = '发生异常，联系研发'
        log.error('ncrm_get_metric_list error, e=%s' % e)
    dajax.script('%s("%s", %s)' % (callback, error, json.dumps(metric_list)))
    return dajax


def get_metric_statistic_rjjh(request, dajax):
    callback = request.POST['callback']
    error = ''
    html = ''
    metric_dict = {}
    args = {}
    try:
        start_date = datetime.datetime.strptime(request.POST['start_date'], '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(request.POST['end_date'], '%Y-%m-%d').date()
        psuser_id_list = json.loads(request.POST['psuser_id_list'])
        metric_list = json.loads(request.POST['metric_list'])
        metric_manager = MetricsManager(start_date, end_date, psuser_id_list, metric_list)
        period_type = request.POST.get('period_type') or 'day'
        period_list = metric_manager.partition_period(period_type)
        metric_data = metric_manager.get_flat_data(period_list)
        html = render_to_string('metric_statistic_table.html', {
            'metric_manager': metric_manager,
            'period_list': period_list,
            'metric_data': metric_data,
        })
        for _data in metric_data:
            metric_dict.setdefault(_data['psuser_id'], {})[_data['metric_name']] = {
                'result': _data['result'],
                'details': _data['details'],
                'data_list': _data['data_list']
            }
        args = {
            'start_date': request.POST['start_date'],
            'end_date': request.POST['end_date'],
            'psuser_id_list': psuser_id_list,
            'metric_list': metric_list,
            'period_type': period_type
        }
    except Exception, e:
        error = '发生异常，联系研发'
        log.error('ncrm_get_metric_statistic_rjjh error, e=%s' % e)
    dajax.script('%s("%s", %s, %s, %s)' % (callback, error, json.dumps(html), json.dumps(metric_dict), json.dumps(args)))
    return dajax


def add_activity_code(request, dajax):
    callback = request.POST['callback']
    activity_code = request.POST['activity_code']
    psuser_name_cn = request.POST['psuser_name_cn']
    exists_objs = ActivityCode.objects.filter(activity_code=activity_code)
    psuser = get_psuser(request)
    error = ''
    try:
        if exists_objs:
            error = '该活动代码已经存在，请修改录入信息'
        else:
            new_obj = ActivityCode.objects.create(**{
                'activity_code': activity_code,
                'name_cn': psuser_name_cn,
                'creater': psuser,
            })
            FuwuOrder._get_collection().update({
                'activity_code': new_obj.activity_code
            }, {'$set': {'psuser_name_cn': new_obj.name_cn}}, multi=True)
    except Exception, e:
        log.error('ncrm_add_activity_code error, e=%s' % e)
        error = '发生异常，联系研发'
    dajax.script('%s("%s")' % (callback, error))
    return dajax


def del_activity_code(request, dajax):
    callback = request.POST['callback']
    activity_code = request.POST['activity_code']
    error = ''
    try:
        ActivityCode.objects.filter(activity_code=activity_code).delete()
        FuwuOrder._get_collection().update({
            'activity_code': activity_code
        }, {'$set': {'psuser_name_cn': ''}}, multi=True)
    except Exception, e:
        log.error('ncrm_del_activity_code error, e=%s' % e)
        error = '发生异常，联系研发'
    dajax.script('%s("%s", "%s")' % (callback, error, activity_code))
    return dajax

def save_pre_sales_advice(request, dajax):
    """ 保存售前咨询记录（新增 or 修改）"""
    callback = request.POST.get('callback', '')
    id = request.POST.get('id', '')
    nick = request.POST.get('nick', '')
    psuser_id = request.POST.get('psuser_id', '')
    note = request.POST.get('note', '')
    business = request.POST.get('business', '')
    msg = ''
    status = 0
    try:
        shop = Customer.objects.filter(nick=nick)
        if shop:
            shop_id = shop.first().shop_id
            if id:
                PreSalesAdvice.objects.filter(id=id).update(note=note, business=business)
                msg = '修改成功'
                status = 1
                result = {'msg': '修改成功', 'status': 1}
            else:
                PreSalesAdvice.objects.create(shop_id=shop_id, psuser_id=psuser_id, note=note, business=business).save()
                msg = '新增成功'
                status = 1
        else:
            msg = '根据店铺ID未找到店铺信息'
            status = 0
    except Exception, e:
        log.error('ncrm_del_activity_code error, e=%s' % e)
        msg = '发生异常，联系研发'
        status = 0
    dajax.script('%s("%s", "%s")' % (callback, msg, status))
    return dajax

def del_pre_sales_advice(request, dajax):
    """ 删除售前咨询记录 """
    callback = request.POST.get('callback', '')
    id = request.POST.get('id', '')
    msg = ''
    status = 0
    try:
        PreSalesAdvice.objects.filter(id=id).delete()
        msg = '删除成功'
        status = 1
    except Exception, e:
        log.error('ncrm_del_activity_code error, e=%s' % e)
        msg = '发生异常，联系研发'
        status = 0
    dajax.script('%s("%s", "%s", "%s")' % (callback, msg, status, id))
    return dajax

def show_conversion_box(request, dajax):
    """ 获取列表展示店铺的相关订单 """
    callback = request.POST.get('callback', '')
    pre_sales_advice_id = request.POST.get('pre_sales_advice_id', '')
    shop_id = request.POST.get('shop_id', '')
    msg = ''
    status = 0
    subscribeList = []
    try:
        subscribeSet = Subscribe.objects.filter(shop_id=shop_id)
        if subscribeSet:
            for subscribe in subscribeSet:
                subscribeJson = {"id": subscribe.id, "item_code": subscribe.item_code,
                                 "article_code": subscribe.article_code,
                                 "biz_type_display": subscribe.get_biz_type_display(), "cycle": subscribe.cycle,
                                 "create_time": subscribe.create_time, "start_date": subscribe.start_date, "source_type_display": subscribe.get_source_type_display(),
                                 "end_date": subscribe.end_date, "pay": subscribe.pay, "pre_sales_advice_id": subscribe.pre_sales_advice_id}
                if subscribe.pre_sales_advice_id:
                    pre_sales_advice = {
                        "id": subscribe.pre_sales_advice_id,
                        "psuser": subscribe.pre_sales_advice.psuser
                    }
                    subscribeJson["pre_sales_advice"] = pre_sales_advice
                subscribeList.append(subscribeJson)

            msg = '获取订单信息成功'
            status = 1
    except Exception, e:
        log.exception("show_conversion_box error:%s" % e)
        msg = '获取订单信息失败'
        status = 0
    result = {"msg": msg, "status": status, "pre_sales_advice_id": pre_sales_advice_id, "subscribeList": subscribeList}
    dajax.script('%s(%s)' % (callback, json.dumps(result)))
    return dajax

def conversion(request, dajax):
    """ 标记转化、撤销转化 """
    callback = request.POST.get('callback', '')
    pre_sales_advice_id = request.POST.get('pre_sales_advice_id', '')
    subscribe_id = request.POST.get('subscribe_id', '')
    msg = ''
    status = 0
    conversion_user = None
    source_type_display = None
    try:
        subscribe = Subscribe.objects.filter(id=subscribe_id)
        if subscribe:
            if pre_sales_advice_id: # 标记转化
                if subscribe.first().pre_sales_advice_id:
                    msg = '订单已转化'
                    status = 0
                else:
                    subscribe.update(pre_sales_advice_id=pre_sales_advice_id, conversion_time=datetime.datetime.now(), source_type=4)
                    conversion_user = subscribe.first().pre_sales_advice.psuser
                    source_type_display = subscribe.first().get_source_type_display()
                    msg = '标记转化成功'
                    status = 1
            else: # 撤销标记
                if subscribe.first().pre_sales_advice_id:
                    subscribe.update(pre_sales_advice_id=pre_sales_advice_id, conversion_time=None, source_type=1)
                    source_type_display = subscribe.first().get_source_type_display()
                    msg = '撤销转化成功'
                    status = 1
                else:
                    msg = '订单已是未转化状态'
                    status = 0
        else:
            msg = '订单信息异常'
            status = 1
    except Exception, e:
        log.exception("conversion error:%s" % e)
        msg = '标记转化失败'
        status = 0
    result = {"msg": msg, "status": status, "subscribe_id": subscribe_id, "pre_sales_advice_id": pre_sales_advice_id, "source_type_display": source_type_display, "conversion_user": conversion_user}
    dajax.script('%s(%s)' % (callback, json.dumps(result)))
    return dajax

def upload_chat_file(request):
    """上传聊天文件 up_file:上传文件关键字，up_path:文件在media下的文件夹路径"""
    try:
        if request.method == 'POST' and request.is_ajax():
            up_path = request.POST.get("up_path")
            file_list = request.FILES
            if file_list:
                file_obj = file_list.get("up_file")
                # 上传文件大小验证
                if file_obj.size > 1024 * 1024 * 10:
                    raise Exception('文件过大,大小不能超过10M')
                else:
                    # 调用上传文件方法，返回文件上传路径
                    path = FileOperateUtil.save_single_file(up_path, file_obj)
                    if path:
                        result = {
                            'status': 1,
                            'file_path': path,
                            'msg': '上传成功'
                        }
            else:
                raise Exception("文件上传失败，请稍后重试")
        else:
            raise Exception("请求异常，稍后重试")
    except Exception, e:
        log.error("upload_file error:%s" % e)
        result = {
            'status': 0,
            'msg': "发生异常，联系研发"
        }
    return JsonResponse(result)


def edit_sb_upload_file(request):
    """编辑人工签单时，上传图片"""
    try:
        if request.method == 'POST' and request.is_ajax():
            up_path = request.POST.get("up_path")
            file_list = request.FILES
            if file_list:
                file_obj = file_list.get("up_file")
                # 上传文件大小验证
                if file_obj.size > 1024 * 1024 * 10:
                    raise Exception('文件过大,大小不能超过10M')
                else:
                    # 调用上传文件方法，返回文件上传路径
                    path = FileOperateUtil.save_single_file(up_path, file_obj)
                    if path:
                        obj_id = request.POST.get("obj_id")
                        subscribe = Subscribe.objects.filter(id=obj_id).first()
                        if subscribe:
                            subscribe.chat_file_path = path
                            subscribe.save()
                            result = {
                                'status': 1,
                                'file_path': path,
                                'msg': '上传成功'
                            }
            else:
                raise Exception("文件上传失败，请稍后重试")
        else:
            raise Exception("请求异常，稍后重试")
    except Exception, e:
        log.error("upload_file error:%s" % e)
        result = {
            'status': 0,
            'msg': "发生异常，联系研发"
        }
    return JsonResponse(result)


def del_chat_file(request):
    """删除人工签单中的聊天文件"""
    try:
        if request.method =='POST' and request.is_ajax():
            obj_id = request.POST.get("obj_id")
            subscribe = Subscribe.objects.filter(id=obj_id).first()
            if subscribe:
                subscribe.chat_file_path = ''
                subscribe.save()
                result = {
                    'status': 1,
                    'msg': "操作完成"
                }
        else:
            raise Exception("请求错误")
    except Exception, e:
        log.error("del_chat_file error:%s" % e)
        result = {
            'status': 0,
            'msg': "发生异常，联系研发"
        }
    return JsonResponse(result)