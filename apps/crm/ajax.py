# coding=UTF-8
import datetime
import math
import urllib2
import re

from bson import ObjectId
from mongoengine.errors import DoesNotExist

from dajax.core import Dajax
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import format_datetime, date_2datetime, time_humanize
from apps.common.constant import Const
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.biz_utils.utils_misc import analysis_web_opter
from apps.mnt.models import MntTask, MntTaskMng, MntCampaign, MntMnger, mnt_camp_coll
from apps.router.models import User
from apps.kwslt.models_cat import Cat, cat_coll
from apps.kwslt.models_selectconf import SelectConf
from apps.kwslt.models_synonymword import SynonymWord, synoword_coll
from apps.kwslt.models_pointlessword import PointlessWord, pointless_coll
from apps.kwslt.select_words import select_words
from apps.web.utils import get_trend_chart_data
from apps.subway.models import Adgroup, Keyword, Item, Campaign, Account, account_coll, camp_coll, adg_coll, kw_coll
from apps.subway.models_report import acctrpt_coll, camprpt_coll, adgrpt_coll, kwrpt_coll
from apps.subway.download import Downloader
from apps.crm.views import ps_auth, get_psuser
from apps.crm.models import PsMessage, UserOrder
from apps.crm.utils import is_grammaticality, get_all_cache_data, check_syntax
from apps.crm.filter_utils import (filtrate_specific_condition, get_specific_statistics_parms,
                                   reset_client_data, filter_dimension, get_kw_count)
from apps.crm.service import CrmCacheServer, crm_cache, get_statictics_category_info
from apps.ncrm.models import Subscribe, PSUser, Customer
from apps.kwslt.analyzer import ChSegement, word_coll

# 保留
# dajax路由函数
@ps_auth
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
        log.exception("route_dajax error, psuser_id=%s, e=%s ,function_name=%s"  \
                % (request.session['psuser_id'], e, str(function_name)))
    return dajax

# 保留
def convert_cache_data(func):
    def _convert_data(request, dajax):
        args_dict = request.POST
        is_use_cache = False
        if args_dict.has_key('use_cache') and int(args_dict['use_cache']):
            # 因ps_auth装饰器已经校验过该操作，在此不作校验 yangrongkai
            try:
                psuser = get_psuser(request)
                index = int(args_dict['page_index'])
                is_jump = int(args_dict['is_jumped'])
            except Exception, e:
                log.error("convert paramters error, e=%s" % (e))
                dajax.script("PT.alert('传输的 page_index 或 is_jumped参数有误。');")
                return dajax
            request.cache_data = get_all_cache_data(psuser, index , is_jump)
            log.info('request 参数中 cache_data 参数可以应用了。')
            is_use_cache = True
        return func(request, dajax, is_use_cache)
    return _convert_data

# 保留
def get_filter_result(request, dajax):
    def is_show_noimpression(obj_condition_dict, type_field = 'rpt'):
        """是否需要去获取无展现数据"""
        if obj_condition_dict.has_key(type_field):
            if obj_condition_dict[type_field]:
                for cond_tuple in obj_condition_dict[type_field].values():
                    if float(cond_tuple[0]) > 0:
                        return False
            else:
                return True
        else:
            return True
        return True

    def is_show_nodata(rpt_cond_dict):
        is_show = True
        if not rpt_cond_dict:
            return is_show

        for min, max in rpt_cond_dict.values():
            if min > -1 or max > -1:
                is_show = False
                break

        return is_show

    def exec_thread_4assignation(filter_type_index, obj_list, public_parameter_dict, \
                                                            dw_coll, rpt_day, specific_dict = {}):
        """执行下载操作"""
        mapping = {
                    0 : "shop_id",
                    1 : "campaign_id",
                    2 : "adgroup_id",
                    3 : "keyword_id",
        }
        size = 3 # 为线程留作预留
        pepiline_size = 5000
        result_list = []
        is_over = False
        if obj_list:
            all_count = len(obj_list)
            max_index = int(math.ceil(all_count * 1.0 / pepiline_size))
            for index in xrange(max_index):
                new_obj_list = obj_list[index * pepiline_size:(index + 1) * pepiline_size]
                try:
                    result = filter_dimension(filter_type_index, {mapping[filter_type_index]:{'$in':new_obj_list}}, \
                            public_parameter_dict, dw_coll, rpt_day, specific_dict = specific_dict)
                    result_list.extend(result)
                    if len(result_list) > Const.CRM_MAX_RESULT_COUNT:
                        is_over = True
                        break
                except Exception, e:
                    log.exception('aggregate pipaline is error, obj_list=%s, collection_name=%s, e=%s' \
                        % (obj_list, dw_coll.name, e))
        return result_list, is_over

    psuser = get_psuser(request)
    server = CrmCacheServer(user_id = psuser.id)

    cond_dict = json.loads(request.POST.get('cond_dict'))
    base_dict = json.loads(request.POST.get('base_dict'))
    tree_path = request.POST.get('tree_path', "")
    filter_type_index = int(request.POST.get('filter_type_index'))
    page_no = int(request.POST.get('page_no'))

    page_size = (filter_type_index == 3 and 400 or 200) # 页面默认是每页200条记录

    cat_id = int(base_dict['cat_id'])
    rpt_day = int(base_dict['rpt_day'])
    consult_id = int(base_dict['consult_id'])
    is_jumped = int(base_dict.get('is_jumped', 0)) # 是否基于跳转前的过滤条件
    is_jumped = 0 if is_jumped < 0 else is_jumped

    source_page, _ = server.get_page_type(filter_type_index, is_jumped, filter_type_index)
    check_status = server.reload_cache(psuser.id, cat_id, \
                         consult_id, cur_page = source_page, rpt_day = rpt_day)

    cache_data = server(source_page)
    page_data = cache_data.get(source_page, {})
    base_data = cache_data.get('base', {})

    cache_cond = server.get_condition(page_data)
    valid_num = len(cache_cond)
    is_same, cond_mark = server.check_condition(cond_dict, cache_cond)

    primary_key_mapping = {
        'account':'shop_id',
        'campaign':'camp_id',
        'adgroup':'adg_id',
        'keyword':'kw_id'
    }

    coll_obj_mapping = {
        'account':account_coll,
        'campaign':camp_coll,
        'adgroup':adg_coll,
        'keyword':kw_coll
    }
    coll_mapping = {
        'account':acctrpt_coll,
        'campaign':camprpt_coll,
        'adgroup':adgrpt_coll,
        'keyword':kwrpt_coll
    }
    is_over = False
    try:
        if tree_path and source_page == 'account':
            server._clear_struct()

        if check_status == 0 and is_same :
            result_data_list = server.get_last_data(page_data)
        else:
            invalid_scope = server.get_aggregate_scope(cond_mark, valid_num)
            server.sync_condition(cond_dict, page_data, valid_num)
            server.clear_invalid_cache(page_data, invalid_scope)

            cache_cond = server.get_condition(page_data)

            result_data_list = []
            end_cond_type = invalid_scope[-1]
            for cond_type in invalid_scope:
                specific_dict = cache_cond.get(cond_type, {}).get('special')
                rpt_dict = cache_cond.get(cond_type, {}).get('rpt')

                obj_list = server.get_last_objids(page_data, cond_type)
                if not obj_list:
                    if tree_path:
                        import apps.ncrm.classify_tree as tree
                        obj_list = tree.read_tree_branch(tree_path, psuser)
                    else:
                        obj_list = server.get_valid_accounts(base_data)

                if not obj_list:
                    log.error('it is a bug, can`t get it.')

                primary_key = primary_key_mapping.get(cond_type)
                dw_coll = coll_mapping.get(cond_type)

                last_key = server.get_last_level_idkey(cond_type)
                curr_obj_list = filtrate_specific_condition(cond_type, obj_list[:], specific_dict, last_key)

                if len(curr_obj_list) > Const.CRM_MAX_RESULT_COUNT * 4:
                    is_over = True
                    page_data = server.clear_invalid_cache(page_data, (cond_type,), clear_cond = True)
                    break
                elif curr_obj_list:
                    specific_dict = get_specific_statistics_parms(specific_dict, cond_type == 'campaign')
                    result_rpt, is_over = exec_thread_4assignation(filter_type_index, \
                                                curr_obj_list, rpt_dict, dw_coll, rpt_day, specific_dict = specific_dict)

                    if is_show_nodata(rpt_dict):
                        # TODO yangrongkai 20140719
                        # 搜索框架需要等数据库升级后重构
                        # 此处暂仅作临时应用
                        name_mapping_list = server.get_name_mapping(cond_type)
                        project_dict = {db_name:'1' for db_name, _ in name_mapping_list}
                        valid_key = primary_key_mapping[cond_type]
                        result_ids = set([result[valid_key] for result in result_rpt if result.has_key(valid_key)])
                        norpt_ids = list(set(curr_obj_list) - result_ids)
                        obj_cursor = coll_obj_mapping[cond_type].find({'_id':{"$in":norpt_ids}}, project_dict)
                        for obj in obj_cursor:
                            result_rpt.append({cache_name:obj[db_name] \
                                                for db_name, cache_name in name_mapping_list})

                    if not result_rpt or is_over:
                        page_data = server.clear_invalid_cache(page_data, (cond_type,), clear_cond = True)
                        break

                    # 添加最近数据到缓存
                    obj_last_data = []
                    for row in result_rpt:
                        if end_cond_type == cond_type:
                            result_data_list.append(row)
                        if row.has_key(primary_key):
                            obj_last_data.append(int(row[primary_key]))

                    server.reset_ids_4search(page_data, cond_type, obj_last_data)
                else:
                    page_data = server.clear_invalid_cache(page_data, (cond_type,), clear_cond = True)
                    break

            server.reset_last_data_4search(page_data, result_data_list)
            server.save(cache_data)

            if is_over:
                dajax.script('PT.hide_loading();PT.alert("%s");' % ('查询结果已超过%s条，\
                    服务器暂不承受超过该数据量的显示操作，请重新进行过滤。'  \
                        % Const.CRM_MAX_RESULT_COUNT))
                return dajax

    except Exception, e:
        log.exception('func = get_filter_result , e = %s' % e)
        dajax.script('PT.hide_loading();PT.alert("%s")' % \
            ('亲，服务器请求失败，请尝试刷新浏览器或退出重新登录。'))
        return dajax

    # 分页处理
    name_space_list = ['CrmAccount', 'CrmCampaign', 'CrmAdgroup', 'CrmKeyword']
    statistics_list = server.get_statistics_ids(page_data, valid_num)
    page_info = {
        'page_no':1,
        'page_count':1,
        'total_count':0,
        'page_size':page_size,
        'statistics_list':statistics_list
    }

    opar_coll = coll_obj_mapping.get(server.get_cond_type_bypage(source_page))
    if result_data_list:
        page_count = int(math.ceil(len(result_data_list) * 1.0 / page_size))
        page_info.update({
            'page_no':page_no,
            'page_count':page_count,
            'total_count':len(result_data_list)
        })
        result_data_list = result_data_list[(page_no - 1) * page_size:(page_no * page_size)]
        cond_type = server.get_cond_type_bypage(source_page)
        result_data_list = reset_client_data(cond_type, result_data_list, [opar_coll], is_rpt = True)
    dajax.script('PT.%s.call_back(%s,%s)' % \
        (name_space_list[filter_type_index], json.dumps(result_data_list), json.dumps(page_info)))
    return dajax

# 保留
def get_base_user_info(request, dajax):
    department = request.POST.get('department', '')
    name_space = request.POST.get('name_space', "")

    if not name_space:
        dajax.script('PT.alert("异常，请联系管理员");')
        return dajax

    psuser = get_psuser(request)
    consult_id = CrmCacheServer(user_id = psuser.id)('base').get('base', {}).get('consult_id', -1)

    user_id = -1
    user_type = -1
    if consult_id > 0 :
        try:
            psuser = PSUser.objects.only('id', 'position').get(id = consult_id)
            user_id = psuser.id
            user_type = psuser.position
        except Exception, e:
            log.error('get psuser error, consult_id =%s, e=%s' % (consult_id, e))

    type_list = []
    temp_list = []
    if department == '-1':
        temp_list = PSUser.objects.filter()
    else:
        if not department:
            department = psuser.department
            type_list = PSUser.DEPARTMENT_CHOICES
        temp_list = PSUser.objects.filter(department = department)
        user_type = department

    user_list = [(user.id, user.name_cn) for user in temp_list \
                    if hasattr(user, 'id') and hasattr(user, 'name_cn')]
    dajax.script("PT.%s.get_group_back('%s','%s',%s,%s)" % (name_space, user_id, user_type, \
                                         json.dumps(type_list), json.dumps(user_list)))
    return dajax

# 保留
def update_adgs_status(request, dajax):
    '''广告组批量更新'''
    from apps.subway.upload import delete_adgroups, update_adgroups
    mode = request.POST.get('mode')
    adg_dict = json.loads(request.POST.get('adg_dict'))
    opter, opter_name = analysis_web_opter(request)
    if mode == 'del':
        del_id_list, cant_del_list, ztc_del_count, error_msg = [], [], [], ''
        for shop_id, adg_id_list in adg_dict.items():
            result = delete_adgroups(shop_id = shop_id, adgroup_id_list = adg_id_list, record_flag = False, opter = opter, opter_name = opter_name)
            del_id_list.extend(result[0])
            cant_del_list.extend(result[1])
            ztc_del_count.extend(result[2])
            if result.error_msg:
                error_msg = result.error_msg
                break

        dajax.script('PT.CrmAdgroup.update_adgs_back("del",%s,%s,%s,"%s")' \
                    % (del_id_list, cant_del_list, ztc_del_count, error_msg))
    else:
        for shop_id, adg_id_list in adg_dict.items():
            adg_arg_dict, success_id_list, ztc_del_list = {}, [], []
            for adg_id in adg_id_list:
                adg_arg_dict[adg_id] = {'online_status':mode == 'start' and 'online' or 'offline'}
            result = update_adgroups(shop_id = shop_id, adg_arg_dict = adg_arg_dict, record_flag = False, opter = opter, opter_name = opter_name)
            success_id_list.extend(result[0])
            ztc_del_list.extend(result[1])
        dajax.script('PT.CrmAdgroup.update_adgs_back("%s",%s)' % (mode, success_id_list))

    return dajax

# 保留
def curwords_submit(request, dajax):
    """提交关键词到直通车"""

    def get_keyword_limit_price(adg_id_list):
        """获取关键词限价"""
        limit_price_dict = {adg['_id']:adg['limit_price'] for adg in adg_coll.\
                                find({'_id':{'$in':adg_id_list}, 'limit_price':{'$gte':5, '$lte': 9999}, \
                             'mnt_type':2}, \
                         {'_id':1, 'limit_price':1}) \
                    if '_id' in adg and 'limit_price' in adg and adg['_id'] and adg['limit_price']}

        adg_keys = limit_price_dict.keys()
        adg_list = set(adg_id_list) - set(adg_keys)

        if adg_list:
            extend_dict = {adg['_id']:adg['campaign_id'] \
                                for adg in adg_coll.find({'_id':{'$in':adg_id_list}, 'mnt_type':1}, \
                            {'_id':1, 'campaign_id':1}) \
                        if '_id' in adg and adg['_id'] and adg['campaign_id']}

            cj_limit_dict = {mnt['_id']:mnt['max_price'] \
                            for mnt in mnt_camp_coll.find({'_id':{'$in':extend_dict.values()}, 'mnt_type':1, \
                        'max_price':{'$gte':5, '$lte':9999}, }, {'max_price':1}) \
                    if '_id' in mnt and 'max_price' in mnt and mnt['_id'] and mnt['max_price']}

            for adg_id, camp_id  in extend_dict.items():
                if camp_id in cj_limit_dict:
                    extend_dict[adg_id] = cj_limit_dict[camp_id]
                else:
                    extend_dict.pop(adg_id)

            limit_price_dict.update(extend_dict)

        return limit_price_dict

    try:
        shop_dict = json.loads(request.POST.get('shop_dict', '{}'))
        adg_id_list = json.loads(request.POST.get('adg_id_list', '[]'))
        adg_id_list = list(set(adg_id_list))
        is_jumped = int(request.POST.get('is_jumped', 0))
    except Exception, e:
        log.error('get parameters error, e=%s' % (e))
        dajax.script('PT.alert("异常，请联系管理员。");')
    else:
        updated_id_list, deleted_id_list, top_id_deleted_id_list, failed_id_list, \
            un_commit_list = [], [], [], [], []

        limit_price_dict = get_keyword_limit_price(adg_id_list)
        from apps.web.utils import update_kws_8shopid
        for shop_id, kw_info in shop_dict.items():
            try:
                kw_list = []
                for kw in kw_info:
                    if 'adgroup_id' in kw and 'new_price' in kw and int(kw['adgroup_id']) in limit_price_dict:
                        limit_price = limit_price_dict[int(kw['adgroup_id'])]
                        cur_price = kw['new_price'] * 100

                        if cur_price >= 5 and cur_price < 9999:
                            if limit_price < cur_price :
                                kw['new_price'] = limit_price / 100.0
                            kw_list.append(kw)
                        else:
                            # 传输无效的 关键词
                            continue
                    else:
                        # 无权限更改的关键词
                        un_commit_list.append(kw['keyword_id'])
                        continue

                if kw_list:
                    opter_name = request.session.get('psuser_name', 'unknown')
                    updated_list, deleted_list, top_deleted_id_list, failed_list = \
                        update_kws_8shopid(shop_id = int(shop_id), kw_list = kw_list, record_flag = True, optm_type = 3, opter = 2, opter_name = opter_name)

                    updated_id_list.extend(updated_list)
                    deleted_id_list.extend(deleted_list)
                    top_id_deleted_id_list.extend(top_deleted_id_list)
                    failed_id_list.extend(failed_list)
            except Exception, e:
                log.error('commit taobao keyword error, e=%s' % (e))

        if (deleted_id_list or top_id_deleted_id_list) and (not updated_id_list): # 更新缓存
            psuser = get_psuser(request)
            server = CrmCacheServer(user_id = psuser.id)
            page_type = 'kwbak' if is_jumped else 'keyword'
            old_last_data = server.get_last_data_cache(page_type)
            last_data = []
            for data in old_last_data:
                if 'kw_id' in data :
                    kw_id = data['kw_id']
                    if kw_id not in deleted_id_list and kw_id not in top_id_deleted_id_list:
                        last_data.append(data)
            server.save_last_data_cache(page_type, last_data)

            if last_data:
                page_no = 1
                page_size = 400
                cond_type = 'keyword'
                opar_coll = kw_coll

                page_count = int(math.ceil(len(last_data) * 1.0 / 400))
                page_info = {}
                page_info.update({
                    'page_no':1,
                    'page_count':page_count,
                    'total_count':len(last_data)
                })
                result_data_list = last_data[(page_no - 1) * page_size:page_no * page_size]
                result_data_list = reset_client_data(cond_type, result_data_list, [opar_coll], is_rpt = True)

            else:
                pass
        else:
            pass

        dajax.script('PT.instance_table.curwords_submit_call_back(%s,%s,%s)' % \
                             (json.dumps(updated_id_list), json.dumps(deleted_id_list), \
                                 json.dumps(top_id_deleted_id_list)))

        msg = '关键词 ：'
        if updated_id_list:
            msg += " 已更新 %s 个 " % (len(updated_id_list))
        if deleted_id_list:
            msg += " 删除 %s 个 " % (len(deleted_id_list))
        if top_id_deleted_id_list:
            msg += " 淘宝已删除 %s 个 " % (len(top_id_deleted_id_list))
        if failed_id_list:
            msg += " 失败 %s 个 " % (len(failed_id_list))
        if un_commit_list:
            msg += " 不能修改 %s 个 " % (len(un_commit_list))
        dajax.script("PT.alert('%s');" % (msg))
    return dajax

# 保留
def get_contact_info(request, dajax):
    """得到联系信息"""
    acc_ids = json.loads(request.POST.get('acc_ids', "[]"))
    if acc_ids:
        filed_mapping = {
#             'cname':"联系人",
            'seller':"联系人",
            'phone':"手机号",
#             'tel':"电话号",
            'qq':"QQ",
            'ww':"旺旺",
#             'lz_id':"量子号",
            'lz_name':"量子账号",
            'lz_psw':'量子密码'
        }
        shop_id_list = map(int, acc_ids)
        customer_cusor = Customer.objects.\
                                filter(shop_id__in = shop_id_list)
        data = {}
        for customer in customer_cusor:
            temp_dict = {}
            for field, title in filed_mapping.items():
                val = getattr(customer, field)
                if val:
                    temp_dict.update({title:val})
            if temp_dict:
                data[customer.shop_id] = temp_dict

        dajax.script('PT.CrmAccount.set_contact_info(%s);' % (json.dumps(data)))
    else:
        dajax.script('PT.alert("请点击 \“搜索\" 获取效账户数据。");')
    return dajax

# 保留
def statistical_summary(request, dajax):
    try:
        # login_user_id = request.user.id
        psuser = get_psuser(request)
        filter_type_index = int(request.POST.get('filter_type_index'))
        is_jumped = int(request.POST.get('is_jumped', 0))
    except Exception, e:
        log.error('func = statistical_summary , e = %s' % e)
        dajax.script('PT.hide_loading();PT.alert("%s");' \
                     % ('亲，服务端获取参数失败，请刷新浏览器重试。'))
        return dajax

    server = CrmCacheServer(user_id = psuser.id)
    last_filter_data = server.get_someone_last_data(filter_type_index, is_jumped)

    result_dict = {}
    if last_filter_data:
        impressions, aclick, click, cost, directpay, indirectpay = 0, 0, 0, 0, 0, 0
        directpaycount, indirectpaycount, favitemcount, favshopcount = 0, 0, 0, 0,
        size = len(last_filter_data)
        for filter_data in last_filter_data:
            impressions += filter_data.get('impressions', 0)
            aclick += filter_data.get('aclick', 0)
            click += filter_data.get('click', 0)
            cost += filter_data.get('cost', 0)
            directpay += filter_data.get('directpay', 0)
            indirectpay += filter_data.get('indirectpay', 0)
            directpaycount += filter_data.get('directpaycount', 0)
            indirectpaycount += filter_data.get('indirectpaycount', 0)
            favitemcount += filter_data.get('favitemcount', 0)
            favshopcount += filter_data.get('favshopcount', 0)

#        TODO: 杨荣凯 此处保留聚合总数据
#         summary_result = {
#                                     # 基础数据
#                                     'impressions':impressions,
#                                     'aclick':aclick,
#                                     'click':click,
#                                     'cost':round(cost / (100.0 * size), 2) ,
#                                     'directpay':round(directpay / (100.0 * size), 2),
#                                     'indirectpay':round(indirectpay / (100.0 * size), 2),
#                                     'directpaycount':directpaycount,
#                                     'indirectpaycount':indirectpaycount,
#                                     'favitemcount':favitemcount,
#                                     'favshopcount':favshopcount,
#
#                                     # 计算数据
#                                     'conv':round((indirectpaycount + directpaycount) * 100.0 / click, 2),
#                                     'cpc':round(cost / (click * 100.0) , 2),
#                                     'ctr':round(click * 100.0 / impressions, 2),
#                                     'pay':round((directpay + indirectpay) / 100.0, 2),
#                                     'paycount':directpaycount + indirectpaycount,
#                                     'profit':round((directpay + indirectpay - cost) / 100.0, 2),
#                                     'roi': cost and round((directpay + indirectpay) * 1.0 / cost, 2) or 0 ,
#                                     'favcount':favitemcount + favshopcount,
#                                     'fav_roi':click and round((favitemcount + favshopcount) * 100.0 / click, 2) or 0,
#                                     }
        avg_result = {
                                # 基础数据
                                'impressions':impressions / size,
                                'aclick':aclick / size,
                                'click':click / size,
                                'cost':round(cost / (100.0 * size), 2) ,
                                'directpay':round(directpay / (100.0 * size), 2),
                                'indirectpay':round(indirectpay / (100.0 * size), 2),
                                'directpaycount':directpaycount / size,
                                'indirectpaycount':indirectpaycount / size,
                                'favitemcount':favitemcount / size,
                                'favshopcount':favshopcount / size,

                                # 计算数据
                                'conv':click and round((indirectpaycount + directpaycount) * 100.0 / click, 2) or 0,
                                'cpc':click and round(cost / (click * 100.0) , 2) or 0,
                                'ctr':impressions and round(click * 100.0 / impressions, 2) or 0,
                                'pay':round((directpay + indirectpay) / (100.0 * size), 2),
                                'paycount':(directpaycount + indirectpaycount) / size,
                                'profit':round((directpay + indirectpay - cost) / (size * 100.0), 2),
                                'roi': cost and round((directpay + indirectpay) * 1.0 / cost, 2) or 0 ,
                                'favcount':(favitemcount + favshopcount) / size,
                                'fav_roi':click and round((favitemcount + favshopcount) * 100.0 / click, 2) or 0,
                                }
        result_dict = avg_result
        dajax.script('PT.CrmCondition.statistics_summary_back(%s,"")' % (json.dumps(result_dict)))
    else:
        log.error('crm cache data was lost. login_user_id=%s, filter_type_index=%s, is_send=%s ' \
                  % (psuser.id, filter_type_index, is_jumped))
        dajax.script('PT.CrmCondition.statistics_summary_back(%s,"%s")'  \
                     % (json.dumps(result_dict), '统计数据异常，请联系管理员。'))
    return dajax

# 保留
def repair_yestoday_kwrpt(request, dajax):
    send_dict = json.loads(request.POST.get('send_dict'))
    is_jumped = int(request.POST.get('is_jumped'))

    filter_type_index = 3
    cond_mark = "keyword"
    valid_num = 3

    opar_dict = {}
    yes_datetime = datetime.datetime.today() - datetime.timedelta(days = 1)
    reload_date = datetime.datetime(yes_datetime.year, yes_datetime.month, yes_datetime.day)
    for shop_id , camp_adg_list in send_dict.items():
        adg_list = []
        for  camp_adg in camp_adg_list:
            camp_id, adg_id = camp_adg.split()
            adg_list.append([int(adg_id), int(camp_id), reload_date])
        opar_dict[int(shop_id) ] = adg_list

    dler_cursor = Downloader.objects.filter(shop_id__in = opar_dict.keys())
    for dler in dler_cursor:
        if dler.tapi and dler.token:
            result, reason = Keyword.download_kwrpt_byadgs(shop_id = dler.shop_id, \
                                        tapi = dler.tapi, token = dler.token, adg_tuple_list = opar_dict[dler.shop_id])
            if not result:
                log.error('download kwrpt error, shop_id=%s, adgroup_id=%s, e=%s' % (dler.shop_id , \
                                                                                   opar_dict[1], reason))
    psuser = get_psuser(request)
    server = CrmCacheServer(user_id = psuser.id)

    source_page, _ = server.get_page_type(filter_type_index, is_jumped, filter_type_index)
    cache_data = server(source_page)
    page_data = cache_data.get(source_page, {})
    invalid_scope = server.get_aggregate_scope(cond_mark, valid_num)
    server.clear_invalid_cache(page_data, invalid_scope)
    server.reset_condition_4search(page_data, cond_mark, {"is_force":True})
    server.save(cache_data)

    dajax.script('PT.CrmKeyword.repair_yestoday_kwrpt_back()')
    return dajax

# 保留
def check_base_grammar(request, dajax):
    expression = request.POST.get('expr', "")
    if expression:
        if is_grammaticality(expression):
            dajax.script("PT.alert('基本语法正确')")
        else:
            dajax.script("PT.alert('语法存在错误，请检查！')")
    else:
        dajax.script("PT.alert('请输入条件表达式！')")
    return dajax

# 保留
def update_opar_status(request, dajax):
    """刷新计划操作状态，为人工干预提供便利"""
    try:
        shop_id = int(request.POST.get('shop_id'))
        camp_id = int(request.POST.get('camp_id'))
        opar_status = int(request.POST.get('opar_status'))
    except Exception, e:
        dajax.script('请求提交服务器失败，可能为网络原因，请刷新浏览器重试。')
        return dajax

    try:
        if opar_status:
            opar_status = 0
        else:
            opar_status = 1
        mnt_camp_coll.update({'shop_id':shop_id, '_id':camp_id}, {'$set':{'opar_status':opar_status}}, multi = True)
    except Exception, e:
        log.error('db update error, e=%s' % e)
        dajax.script('操作失败，请联系管理员查看日志。')
        return dajax

    dajax.script('PT.CrmCampaign.update_opar_status_end(%s,%s);' % (camp_id, opar_status))
    return dajax

# 保留
def get_log_records(request, dajax):
    """得到CRM操作日志"""
    try:
        camp_id = int(request.POST.get('camp_id'))
        log_days = int(request.POST.get('days'))
    except Exception, e:
        log.error('get paramters error, e=%s' % e)
        dajax.script('PT.hide_loading();PT.alert("服务端接收到错误参数，导致如下异常：e=%s ，\
            请联系CRM负责人检查。");' % (e))
        return dajax

    limit_date = date_2datetime(datetime.date.today() - datetime.timedelta(days = log_days))
    mnt_camp = MntCampaign.objects.only('shop_id', 'mnt_type').filter(campaign_id = camp_id)
    if mnt_camp:
        shop_id = mnt_camp[0].shop_id
        mnt_type = mnt_camp[0].mnt_type
        log_records = []
        mntlog_cursor = None
        if mntlog_cursor:
            log_records = [ {'opt_type':mntlog.get_opt_type_display(), \
                                        'opt_time':mntlog.opt_time.strftime('%Y%m%d %H:%M:%S'), \
                                            'opter':mntlog.opter, 'opt_desc':mntlog.opt_desc, \
                                                 'opter_name':mntlog.opter_name } \
                                                    for mntlog in mntlog_cursor]
        if log_records:
            dajax.script('PT.CrmCampaign.set_log_records(%s,%s,%s,%s)' \
                         % (shop_id, camp_id, mnt_type, json.dumps(log_records)))
        else:
            dajax.script('PT.alert("很抱歉,近%s天该计划暂无操作记录。");' % (log_days))
    else:
        dajax.script('PT.alert("托管计划中并不存在该计划ID，请确认该计划是否为广撒网计划或重点推广计划。");')
    return dajax

# 保留
def get_keword_count(request, dajax):
    """"批量获取关键词数量"""
    adg_list = json.loads(request.POST.get('adg_list', ''))
    if adg_list:
        adg_id_list = []
        shop_id_set = set()
        for data in adg_list:
            try:
                if data.has_key('adg_id') and data.has_key('shop_id'):
                    adg_id_list.append(int(data['adg_id']))
                    shop_id_set.add(int(data['shop_id']))
            except Exception, e:
                log.error('convert type error, data=%s, e=%s' % (data, e))
        adg_dict = get_kw_count(adg_id_list, list(shop_id_set))
        dajax.script('PT.CrmAdgroup.set_keyword_count(%s);' % (json.dumps(adg_dict)))
    else:
        dajax.script('PT.alert("获取参数异常，请来管理员");')
    return dajax

# 保留
def get_keyword_price_ratio(request, dajax):
    """获取某一出价范围内所有计划关键词对应的出价占比"""
    def is_up_to_standard(gte_val, lte_val, kw_price):
        if not gte_val and not lte_val:
            return False
        if gte_val and gte_val > kw_price:
            return False
        if lte_val and lte_val < kw_price:
            return False
        return True

    def calculate_custom_result(key, kw_cursor):
        result_dict = {}
        temp_id = 0
        temp_standard = 0
        temp_total = 0
        for kw in kw_cursor:
            if kw.has_key('max_price') and kw.has_key('_id'):
                if temp_id != kw[key]:
                    if temp_id:
                        if temp_total:
                            result_dict[temp_id] = round(temp_standard * 100.0 / temp_total, 2)
                        else:
                            result_dict[temp_id] = 0
                    temp_id = kw[key]
                    temp_standard = 0
                    temp_total = 0
                if is_up_to_standard(gte_val, lte_val, kw['max_price'] * 1.0 / 100):
                    temp_standard += 1
                temp_total += 1
        if temp_id:
            if temp_total and temp_id:
                result_dict[temp_id] = round(temp_standard * 100.0 / temp_total, 2)
            else:
                result_dict[temp_id] = 0
        return result_dict

    def calculate_ratio_result(key, kw_cursor, adg_mapping):
        result_dict = {}
        temp_id = 0
        temp_standard = 0
        temp_total = 0
        for kw in kw_cursor:
            if kw.has_key('max_price') and kw.has_key('_id'):
                if temp_id != kw[key]:
                    if temp_id:
                        if temp_total:
                            result_dict[temp_id] = round(temp_standard * 100.0 / temp_total, 2)
                        else:
                            result_dict[temp_id] = 0
                    temp_id = kw[key]
                    temp_standard = 0
                    temp_total = 0
                limit_price = adg_mapping.get(kw['adgroup_id'], 0)
                if is_up_to_standard(gte_val * limit_price * 1.0 / 10000, \
                        lte_val * limit_price * 1.0 / 10000, kw['max_price'] * 1.0 / 100):
                    temp_standard += 1
                temp_total += 1
        if temp_id:
            if temp_total and temp_id:
                result_dict[temp_id] = round(temp_standard * 100.0 / temp_total, 2)
            else:
                result_dict[temp_id] = 0
        return result_dict

    def exec_campaign_custom_operator(gte_val, lte_val, camp_id_list):
        result_dict = {}
        try:
            camp_id_list = map(int, camp_id_list)
        except Exception, e:
            return result_dict
        else:
            # TODO: yangrongkai 暂只支持重点托管计划，其他查询计划模式暂不提供
            adg_id_list = [ adg['_id'] for adg in \
                                    adg_coll.find({'campaign_id':{'$in':camp_id_list}, 'mnt_type':2}, {'_id':1})]
            kw_cursor = kw_coll.find({'adgroup_id':{'$in':adg_id_list}}, \
                                     {'max_price':1, 'campaign_id':1}).sort('campaign_id')
            result_dict = calculate_custom_result('campaign_id', kw_cursor)
        return result_dict

    def exec_campaign_ratio_operator(gte_val, lte_val, camp_id_list):
        result_dict = {}
        try:
            camp_id_list = map(int, camp_id_list)
        except Exception, e:
            return result_dict
        else:
            # TODO: yangrongkai 暂只支持重点托管计划，其他查询计划模式暂不提供
            adg_mapping = {adg['_id']:adg.get('limit_price', 0) for adg in \
                           adg_coll.find({'campaign_id':{'$in':camp_id_list}, 'mnt_type':2}, {'limit_price':1})}
            kw_cursor = kw_coll.find({'adgroup_id':{'$in':adg_mapping.keys()}}, \
                                     {'max_price':1, 'campaign_id':1, 'adgroup_id':1}).sort('campaign_id')
            result_dict = calculate_ratio_result("campaign_id", kw_cursor, adg_mapping)
        return result_dict

    def exec_adgroup_custom_operator(gte_val, lte_val, adg_id_list):
        result_dict = {}
        try:
            adg_id_list = map(int, adg_id_list)
        except Exception, e:
            return result_dict
        else:
            adg_mapping = {adg['_id']:adg.get('limit_price', 0) for adg in \
                           adg_coll.find({'_id':{'$in':adg_id_list}, 'mnt_type':2}, {'limit_price':1})}
            kw_cursor = kw_coll.find({'adgroup_id':{'$in':adg_mapping.keys()}}, \
                                     {'max_price':1, 'adgroup_id':1}).sort('adgroup_id')
            result_dict = calculate_custom_result("adgroup_id", kw_cursor)
        return result_dict

    def exec_adgroup_ratio_operator(gte_val, lte_val, adg_id_list):
        result_dict = {}
        try:
            adg_id_list = map(int, adg_id_list)
        except Exception, e:
            return result_dict
        else:
            adg_mapping = {adg['_id']:adg.get('limit_price', 0) for adg in \
                                adg_coll.find({'_id':{'$in':adg_id_list}, 'mnt_type':2}, {'limit_price':1})}
            kw_cursor = kw_coll.find({'adgroup_id':{'$in':adg_mapping.keys()}}, \
                                     {'max_price':1, 'adgroup_id':1}).sort('adgroup_id')
            result_dict = calculate_ratio_result("adgroup_id", kw_cursor, adg_mapping)
        return result_dict

    def exec_default_operator(gte_val, lte_val, camp_id_list, dajax):
        return {}

    try:
        search_type = request.POST['search_type']
        gte_val = float(request.POST['gte_val'])
        lte_val = float(request.POST['lte_val'])
        obj_list = json.loads(request.POST['obj_list'])
        obj_model = str(request.POST['obj_model'])
    except Exception, e:
        log.error('get paramters error, e=%s' % e)
        dajax.script('PT.hide_loading();PT.alert("服务端接收到错误参数，导致如下异常：e=%s ，请联系CRM负责人检查。");' % (e))
        return dajax

    name_mapping = {'campaign':'CrmCampaign', 'adgroup':'CrmAdgroup'}
    key = "%s_%s" % (obj_model, search_type)
    oper_mapping = {
                        'campaign_custom':exec_campaign_custom_operator,
                        'campaign_ratio':exec_campaign_ratio_operator,
                        'adgroup_custom':exec_adgroup_custom_operator,
                        'adgroup_ratio':exec_adgroup_ratio_operator
                    }
    result_dict = oper_mapping.get(key, exec_default_operator)(gte_val, lte_val, obj_list)
    model_name = name_mapping.get(obj_model, '')
    if model_name:
        dajax.script('PT.%s.set_kw_price_ratio(%s)' % (model_name, json.dumps(result_dict)))
    else:
        dajax.script('PT.alert("%s")' % "页面异常，请联系管理员.")
    return dajax

# 保留
def update_keyword_freeze_status(request, dajax):
    """更新关键词的冻结状态"""
    try:
        shop_id = int(request.POST['shop_id'])
        adg_id = int(request.POST['adg_id'])
        kw_id = int(request.POST['kw_id'])
        freeze_flag = int(request.POST['freeze_flag'])
    except Exception, e:
        log.error('get paramters error, e=%s' % e)
        dajax.script('PT.hide_loading();PT.alert("服务端接收到错误参数，导致如下异常：e=%s ，请联系CRM负责人检查。");' % (e))
        return dajax
    freeze_status = freeze_flag and True or False
    result_flag = 0 if freeze_flag else 1
    kw_coll.update({'shop_id':shop_id, 'adgroup_id':adg_id, '_id':kw_id}, {'$set':{'is_freeze':freeze_status}})
    dajax.script('PT.CrmKeyword.set_freeze_status(%s,%s)' % (kw_id, result_flag))
    return dajax

# 保留
def reset_source_status(request, dajax):
    """重置词元来源状态"""
    shop_id = int(request.POST.get('shop_id', 0))
    item_id = int(request.POST.get('item_id', 0))
    if shop_id and item_id:
        try:
            item = Item.objects.get(shop_id = shop_id, item_id = item_id)
        except Exception, e:
            log.error('get item error, shop_id=%s, item_id=%s, e=%s' % (shop_id, item_id, e))
            dajax.script("PT.alert('重置词元来源异常，请联系管理员。');")
        else:
            item.word_modifier = 0
            if item.save():
                item.delete_item_cache()
                dajax.script("PT.CRMSelectWordManager.reset_scource_status();")
            else:
                dajax.script("PT.alert('重置词元来源异常，请联系管理员。');")
    else:
        dajax.script("PT.alert('重置词元来源异常，请联系管理员。');")
    return dajax

# 保留
def system_item_analysis(request, dajax):
    """系统宝贝分析"""
    try:
        shop_id = int(request.POST['shop_id'])
        item_id = int(request.POST['item_id'])
    except Exception, e:
        log.error('get paramters error, e=%s' % e)
        dajax.script('PT.hide_loading();PT.alert("服务端接收到错误参数，导致如下异常：e=%s ，请联系CRM负责人检查。");' % (e))
        return dajax

    try:
        item = Item.objects.get(shop_id = shop_id, item_id = item_id)
    except Exception, e:
        log.error('get select conf info ! shop_id=%s, adgroup_id=%s, e=%s' % (shop_id, item_id, e))
        dajax.script('PT.hide_loading();PT.alert("后端获取返回参数失败，请联系管理员查看。");')
        return dajax

    try:
        pure_title_list, product_list, sale_list, decorate_list = item.get_preview_info(custome_word_dict = {})
        item_attrs = {
                        'ele_info':','.join(map(str, pure_title_list)),
                        'pro_info':','.join(map(str, product_list)),
                        'sale_info':','.join(map(str, sale_list)),
                        'deco_info':','.join(map(str, decorate_list))
                      }
    except Exception, e:
        log.error('to analyse item attrs error, shop_id=%s, item_id=%s, e=%s' % (shop_id, item_id, e))
        dajax.script('PT.alert("很抱歉，系统宝贝分析操作失败。");')
    else:
        dajax.script('PT.CRMSelectWordManager.set_system_item_info(%s)' % (json.dumps(item_attrs)))
    return dajax

# 保留
def get_test_cat_items(request, dajax):
    """获取类目下的宝贝信息"""
    try:
        cat_id = int(request.POST["cat_id"])
    except Exception, e:
        log.error("get cat_id fail or type conver error, %e" % (e))
        dajax.script("PT.alert('异常，请联系管理员。')")
    else:
        try:
            shop_id_dict = {}
            for item in Item.objects.filter(cat_id = cat_id)[:500]:
                if not shop_id_dict.has_key(item.shop_id):
                    shop_id_dict[item.shop_id] = []
                shop_id_dict[item.shop_id].append([item.shop_id, item.item_id, item.title, item.pic_url])

            item_list = []
            for temp_item_list in shop_id_dict.values():
                item_list.extend(temp_item_list[:3])
        except Exception, e:
            log.error("get cat items error, cat_id=%s, e=%s" % (cat_id, e))
            dajax.script("PT.alert('获取宝贝异常，请联系管理员。')")
        else:
            dajax.script("PT.CRMSelectWordManager.set_cat_items(%s);" % (json.dumps(item_list)))
    return dajax

# 保留
def test_select_words(request, dajax):
    """获取测试选词关键词"""
    try:
        shop_id = int(request.POST['shop_id'])
        item_id = int(request.POST['item_id'])
        adg_id = int(request.POST['adg_id'])
        conf_name = str(request.POST['conf_name'])
        conf_desc = str(request.POST['conf_desc'])
        candidate_words = str(request.POST['candidate_words'])
        label_define = eval(request.POST['label_define'])
        select_conf_list = eval(request.POST['select_conf_list'])
        price_conf_list = eval(request.POST['price_conf_list'])
        delete_conf = eval(request.POST['delete_conf'])
    except Exception, e:
        log.exception('get paremters error, conf_name=%s, e=%s' % (conf_name, e))
        dajax.script('PT.hide_loading();PT.alert("服务器获取参数失败，请联系管理员。");')
        return dajax

    label, row_index, desc = check_syntax(candidate_words, \
                                        label_define, select_conf_list, price_conf_list, delete_conf)
    if label:
        if row_index == -1:
            dajax.script('PT.alert("您输入的 %s 存在语法错误，请检查并重新输入！")' % (label))
            return dajax
        else:
            dajax.script('PT.alert("您的 %s 存在语法错误，请检查重新输入！（行：%s , %s列）")' \
                    % (label, row_index, desc))
            return dajax

    try:
        select_conf = SelectConf.pack_select_conf_object(SelectConf(), conf_desc, \
                                    candidate_words, label_define, select_conf_list, price_conf_list, delete_conf)
    except Exception, e:
        log.error("pack select conf error, e=%s" % e)
        dajax.script('PT.hide_loading();PT.alert("封装选词配置异常，请联系管理员");' % (conf_name))
        return dajax
    else:
        try:
            item = Item.objects.get(shop_id = shop_id, item_id = item_id)
            item.select_conf = select_conf
        except Exception, e:
            log.error('get adgroup or item error, shop_id=%s, e=%s' % (shop_id, e))
            dajax.script('PT.hide_loading();PT.alert("系统不存在该宝贝。");')
        try:
            adgroup = Adgroup.objects.get(shop_id = shop_id, item_id = item_id, adgroup_id = adg_id)
        except Exception, e:
            log.error('get adgroup or item error, shop_id=%s, e=%s' % (shop_id, e))
            dajax.script('PT.hide_loading();PT.alert("系统不存在该宝贝所对应任何推广。");')
        else:
            try:
                kw_list = select_words(adgroup, item, select_conf)
            except Exception, e:
                log.error('get keywords error, conf_name=%s, e=%s' % (conf_name, e))
                dajax.script('PT.hide_loading();PT.alert("获取关键词列表失败，可能存在配置问题，请检查您配置的参数。");')
            else:
                dajax.script('PT.CrmSelectWords.set_kw_list(%s)' % (json.dumps(kw_list)))
    return dajax

# 保留
def save_item_attr(request, dajax):
    """保存宝贝属性"""
    try:
        shop_id = int(request.POST["shop_id"])
        item_id = int(request.POST["item_id"])
        blackword_list = request.POST.get('blackword_list', None)
        saleword_list = request.POST.get('saleword_list', None)
    except Exception, e:
        log.error("type conver error, e=%s" % (e))
        dajax.script("PT.alert('类型转换异常，请联系管理员');")
    else:
        try:
            item = Item.objects.get(shop_id = shop_id, item_id = item_id)
        except Exception, e:
            log.error("get item error, shop_id=%s, item_id=%s, e=%s" % (shop_id, item_id, e))
            dajax.script("PT.alert('系统中不能存在该宝贝');")
        else:
            if not blackword_list is None :
                word_list = blackword_list.replace('，', ',').split(',')
                item.blackword_list = word_list

            if not saleword_list is None:
                word_list = saleword_list.replace('，', ',').split(',')
                item.saleword_list = word_list
                item.word_modifier = 2

            if item.save():
                dajax.script("PT.CRMSelectWordManager.set_item_attr_result('%s');" % ("AE"))
            else:
                dajax.script("PT.alert('保存失败');")
    return dajax

# 保留
def save_cat_conf(request, dajax):
    """保存宝贝属性"""
    try:
        cat_id = int(request.POST["cat_id"])
        product_conf = request.POST.get('product_conf', None)
        sale_conf = request.POST.get('sale_conf', None)
    except Exception, e:
        log.error("type conver error, e=%s" % (e))
        dajax.script("PT.alert('类型转换异常，请联系管理员');")
    else:
        try:
            cat_info = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat")
        except Exception, e:
            log.error("get cat_info error, cat_id=%s, e=%s" % (cat_id, e))
            dajax.script("PT.alert('系统中不能存在该宝贝');")
        else:
            if not product_conf is None :
                try:
                    match_word, product_word = product_conf.split(';')
                except Exception, e:
                    log.error("split production conf error, e=%s")
                    dajax.script("PT.alert('拆分异常，请联系管理员');")
                    return dajax
                is_success = Cat.save_and_reset(cat_id, product_dict = {'match':match_word, 'product':product_word})

            if not sale_conf is None:
                sale = cat_info.sale_dict
                if ';' in sale_conf:
                    match, sale = sale_conf.split(';')
                else:
                    match , sale = '', sale_conf
                is_success = Cat.save_and_reset(cat_id, sale_dict = {'match':match, 'sale':sale})

            if is_success:
                dajax.script("PT.alert('保存成功');")
            else:
                dajax.script("PT.alert('保存失败');")
    return dajax

# 待定
def search_category_list(request, dajax):
    """获取类目数据"""
    cat_name = request.POST.get('cat_name', '')
    cat_id = int(request.POST.get('cat_id', 0))
    contain_sub_cat = int(request.POST.get('is_contain', 0))

    search_list = []
    # TODO： yangrongkai 下面方法不做异常处理，此模块将被重构
    if cat_name:
        search_list.extend([ cat['cat_id'] for cat in \
            cat_coll.find({'cat_name':{'$regex':cat_name}}, {'cat_id':1, '_id':0}) ])

    if cat_id :
        search_list.extend([cat_id])

    if contain_sub_cat:
        sub_cat_list = []
        for cat_id in search_list:
            try:
                result = Cat.get_all_subcats(cat_id = cat_id)
                sub_cat_list.extend(result)
            except Exception, e:
                log.error('get kwlib api error, e=%s' % (e))
        search_list.extend(sub_cat_list)

    result_list = []
    cat_mapping = get_statictics_category_info()
    for cat_info in cat_coll.find({'_id':{'$in':search_list}}):
        key = cat_info['_id']
        cat_cache = cat_mapping.get(str(key), {})
        cat_all_name = cat_cache.get('cat_name') \
                                    if cat_cache.has_key('cat_name') \
                                        else cat_info['cat_name'] # 是否考虑无宝贝类目
        adgroup_total = cat_cache.get('adgroup_total') if cat_cache.has_key('adgroup_total') else 0
        base_dict = {
                                    'cat_id':key,
                                    'cat_name':cat_all_name,
                                    'all_pv':cat_info.get('all_pv', 0),
                                    'all_click':cat_info.get('all_click', 0),
                                    'all_cost':round(cat_info.get('all_cost', 0) / 100, 2),
                                    'avg_click':cat_info.get('avg_click', 0),
                                    'avg_cpc':round(cat_info.get('avg_cpc', 0) / 100, 2),
                                    'avg_ctr':round(cat_info.get('avg_ctr', 0) * 100, 2),
                                    'level':cat_info.get('level', 0),
                                    'words_num':cat_info.get('words_num', 0),
                                    'adgroup_total':adgroup_total
                                }
        result_list.append(base_dict)

    result_list.sort(cmp = lambda x, y: cmp(x['cat_name'], y['cat_name']))

    dajax.script('PT.CRMCategoryList.set_category_data(%s,"%s");' \
                            % (json.dumps(result_list), get_psuser(request).name))
    return dajax

# 待定
def get_assignable_user_bygroup(request, dajax):
    """获取可分配的有效用户"""
    group_id = int(request.POST.get('group_id', 0))
    if group_id:
        user_info = [{'id':user.id, 'name':user.name_cn} for user in \
                        PSUser.objects.only('id', 'name_cn').filter(consult_group__id = group_id)]
        dajax.script("PT.CRMCategoryList.set_assign_user(%s);" % (json.dumps(user_info)))
    else:
        dajax.script('PT.alert("加载信息异常，请联系管理员！");')
    return dajax

# 保留
def get_selectword_category_info(request, dajax):
    """得到选词类目信息"""
    cat_id = request.POST.get('cat_id', 0)
    result = {}
    if cat_id:
        try:
            sale = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "sale_dict")
            prdt = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "product_dict")
            result = Cat.get_full_name_path(cat_id = int(cat_id))
            result.update({
                            'cat_id':cat_id,
                            "sale_conf_match":sale and sale.match or "",
                            "sale_conf_absolute":sale and sale.sale or "",
                            "product_conf_match":prdt and prdt.match or "",
                            "product_conf_absolute":prdt and prdt.product or "",
                        })
        except Exception, e:
            log.error("get category info error, cat_id=%s, e=%s" % (cat_id, e))
            dajax.script("PT.alert('系统中没有该类目！');")
        else:
            dajax.script("PT.CRMSelectWordManager.set_category_info(%s);" % (json.dumps(result)))
    else:
        dajax.script("PT.alert('异常，系统为即受到类目参数！');")
    return dajax

# 保留
def get_selectword_item_info(request, dajax):
    """得到选词宝贝信息"""
    try:
        cat_id = request.POST.get('cat_id', 0)
        shop_id = request.POST.get('shop_id', 0)
        item_id = request.POST.get('item_id', 0)
        is_clear = int(request.POST.get('is_clear', 0))
    except Exception, e:
        log.error("get conver error, e=%s" % (e))
        dajax.script("PT.alert('转换异常，清联系管理员！');")
        return dajax
    try:
        if item_id and shop_id:
            item = Item.objects.get(shop_id = shop_id, item_id = item_id)
        elif cat_id:
            item = Item.objects.filter(cat_id = cat_id)[0]
        else:
            dajax.script("PT.alert('未能获取该类目下的宝贝！')")
            return dajax
        if is_clear:
            item.delete_item_cache()
    except Exception, e:
        log.error("get item error, e=%s" % (e))
        dajax.script("PT.alert('异常，请刷新重试或联系管理员！')")
        return dajax
    else:
        label_dict = item.get_label_dict
        product_word_list = label_dict.get('P', [])
        dcrt_word_list = label_dict.get('D', [])
        sale_word_list = label_dict.get('S', [])
        hot_word_list = label_dict.get('H', [])
        custom_words = ''
        for k, v in item.custome_word_dict.items():
            custom_words += (unicode(k) + ':' + ','.join(v) + '\n')
        blackword_list = item.blackword_list
        include_list = item.include_word_list
        element_words_list = item.pure_title_word_list
        word_modifier = item.get_word_modifier_display()
        if not word_modifier:
            word_modifier = "系统"
        item_attrs = {
                        'pic_url':item.pic_url,
                        'item_id':item.item_id,
                        'shop_id':item.shop_id,
                        'operator':word_modifier,
                        'title':item.title,
                        'ele_info':','.join(map(str, element_words_list)),
                        'pro_info':','.join(map(str, product_word_list)),
                        'sale_info':','.join(map(str, sale_word_list)),
                        'deco_info':','.join(map(str, dcrt_word_list)),
                        'black_info':','.join(map(str, blackword_list)),
                        'hot_info':','.join(map(str, hot_word_list)),
                        'word_modifier':item.get_word_modifier_display(),
                        'include_list':','.join(map(str, include_list)),
                        'custom_words':custom_words
                      }
        dajax.script('PT.CRMSelectWordManager.set_item_attr(%s);' % (json.dumps(item_attrs)))
    return dajax

# 保留
def get_selectword_conf_info(request, dajax):
    """得到选词配置信息"""
    def get_catname_conf(cat_id, model_type):
        result_cat_name = ""
        result_cat_id = 0
        cat_conf = ""
        try:
            cat_id = int(cat_id)
            cat_list = Cat.get_catid_path(cat_id = cat_id)
            cat_mapping = Cat.get_multi_cat_attr(cat_id_list = map(int, cat_list), field_list = ['selectconf_dict', 'cat_name'])
            for index in xrange(len(cat_list) - 1, -1, -1):
                temp_cat_id = int(cat_list[index])
                if cat_mapping.has_key(temp_cat_id) and cat_mapping[temp_cat_id]:
                    temp_cat_info = cat_mapping[temp_cat_id]
                    if temp_cat_info.selectconf_dict.has_key(model_type) \
                        and temp_cat_info.selectconf_dict[model_type]:
                        temp_cat_conf = temp_cat_info.selectconf_dict[model_type]
                        # 此处需要容错
                        if SelectConf.check_exist(temp_cat_conf):
                            result_cat_name = temp_cat_info.cat_name
                            result_cat_id = temp_cat_info.cat_id
                            cat_conf = temp_cat_conf
                            break
                        else:
                            temp_cat_info.selectconf_dict.pop(model_type)
                            temp_cat_info.save_single()

            if not result_cat_name or not cat_conf:
                cat_conf = 'default_' + model_type + '_conf'
                result_cat_name = "系统默认"
            elif cat_conf.startswith("default_"):
                result_cat_name = "系统绑定"
        except Exception, e:
            log.error("get category name and conf name error, cat_id=%s, e=%s " % (cat_id, e))
        return result_cat_id, result_cat_name, cat_conf

    cat_id = request.POST.get("cat_id", 0)
    shop_id = request.POST.get("shop_id", 0)
    item_id = request.POST.get("item_id", 0)
    model_type = request.POST.get("model_type", "")
    if cat_id and shop_id and item_id and model_type:
        cat_id, cat_name, cat_conf_name = get_catname_conf(cat_id, model_type)
        item_conf = ""
        try:
            item = Item.objects.get(shop_id = shop_id, item_id = item_id)
            item_conf_name = item.selectconf_dict.get(model_type, "")
        except Exception, e:
            log.error("get item error, shop_id=%s, item_id=%s" % (shop_id, item_id))
            dajax.script("PT.hide_loading();PT.alert('宝贝在系统中不存在！');")
        else:
            cat_conf = SelectConf.pack_select_word_conf(cat_conf_name)
            item_conf = SelectConf.pack_select_word_conf(item_conf_name)
            is_existed = 1 if item_conf else 0
            dajax.script("PT.CRMSelectWordManager.set_select_word_conf('%s','%s',%s,%s,%s);" \
                         % (cat_id, cat_name, json.dumps(cat_conf), json.dumps(item_conf), is_existed))
    else:
        dajax.script("PT.hide_loading();PT.alert('参数有误，请联系管理员！');")
    return dajax

# 保留
def add_new_model(request, dajax):
    """添加一个新的通用模板"""
    try:
        conf_name = str(request.POST['conf_name'])
        conf_desc = str(request.POST['conf_desc'])
        candidate_words = str(request.POST['candi_filter'])
        label_define = json.loads(request.POST['label_define_list'])
        select_conf_list = json.loads(request.POST['select_conf_list'])
        price_conf_list = json.loads(request.POST['price_conf_list'])
        delete_conf = json.loads(request.POST['delete_conf'])
    except Exception, e:
        log.eror("get parameters erro, e=%s" % (e))
        dajax.script("PT.alert('添加新模板异常，请联系管理员');")
        return dajax

    # 判定是否新模板名称是否存在
    if SelectConf.check_exist(conf_name):
        dajax.script("PT.alert('名称：%s 系统中已存在，请修改您要提交的模板名称。');" % (conf_name))
        return dajax

    # 检查语法
    label, row_index, desc = check_syntax(candidate_words, label_define, \
                                          select_conf_list, price_conf_list, delete_conf)
    if label:
        if row_index == -1:
            dajax.script('PT.alert("您输入的 %s 存在语法错误，请检查并重新输入！")' % (label))
            return dajax
        else:
            dajax.script('PT.alert("您的 %s 存在语法错误，请检查重新输入！（行：%s , %s列）")' \
                         % (label, row_index, desc))
            return dajax

    if SelectConf.save_select_conf(conf_name, conf_desc, candidate_words, label_define, \
                            select_conf_list, price_conf_list, delete_conf, conf_type = 1, new_create = True):
        dajax.script('PT.CRMSelectWordManager.set_add_model_end("%s");' % (conf_name))
    else:
        dajax.script('PT.alert("添加失败！")')
    return dajax

# 保留
def update_cat_conf(request, dajax):
    """用于校验语法"""
    try:
        conf_name = str(request.POST['conf_name'])
        conf_desc = str(request.POST['conf_desc'])
        candidate_words = str(request.POST['candi_filter'])
        label_define = json.loads(request.POST['label_define_list'])
        select_conf_list = json.loads(request.POST['select_conf_list'])
        price_conf_list = json.loads(request.POST['price_conf_list'])
        delete_conf = json.loads(request.POST['delete_conf'])
    except Exception, e:
        log.error('get paramters error, e=%s' % e)
        dajax.script('PT.alert("服务端接收到错误参数，导致如下异常：e="%s" ，请联系CRM负责人检查。");' % (e))
        return dajax

    # 检查语法
    label, row_index, desc = check_syntax(candidate_words, label_define, \
                                          select_conf_list, price_conf_list, delete_conf)
    if label:
        if row_index == -1:
            dajax.script('PT.alert("您输入的 %s 存在语法错误，请检查并重新输入！")' % (label))
            return dajax
        else:
            dajax.script('PT.alert("您的 %s 存在语法错误，请检查重新输入！（行：%s , %s列）")' \
                         % (label, row_index, desc))
            return dajax

    if SelectConf.check_exist(conf_name):
        conf_type = 2
        if conf_name.startswith("default_"):
            conf_type = 1
        if SelectConf.save_select_conf(conf_name, conf_desc, candidate_words, \
                    label_define, select_conf_list, price_conf_list, delete_conf, conf_type = conf_type):
            dajax.script('PT.alert("更新成功！")')
        else:
            dajax.script('PT.alert("更新失败！")')
    else:
        dajax.script('PT.alert("异常，更新失败，数据部没有该配置！")')
    return dajax

# 保留
def save_item_conf(request, dajax):
    """用于校验语法"""
    try:
        shop_id = int(request.POST['shop_id'])
        item_id = int(request.POST['item_id'])
        model_type = str(request.POST['model_type'])
        conf_name = str(request.POST['conf_name'])
        conf_desc = str(request.POST['conf_desc'])
        candidate_words = str(request.POST['candi_filter'])
        label_define = json.loads(request.POST['label_define_list'])
        select_conf_list = json.loads(request.POST['select_conf_list'])
        price_conf_list = json.loads(request.POST['price_conf_list'])
        delete_conf = json.loads(request.POST['delete_conf'])
    except Exception, e:
        log.error('get paramters error, e=%s' % e)
        dajax.script('PT.alert("服务端接收到错误参数，导致如下异常：e="%s" ，请联系CRM负责人检查。");' % (e))
        return dajax

    # 检查
    try:
        item = Item.objects.get(shop_id = shop_id, item_id = item_id)
    except Exception, e:
        log.error(" get item error, shop_id=%s, item_id=%s, e=%s" % (shop_id, item_id, e))
        dajax.script('PT.alert("异常，宝贝未在CRM系统中。");')
        return dajax

    if item.selectconf_dict.has_key(model_type) and item.selectconf_dict[model_type]:
        if conf_name != item.selectconf_dict[model_type]:
            dajax.script('PT.alert("该宝贝已有绑定的模板，不能进行新建。");')
            return dajax
    else:
        try:
            SelectConf.objects.get(conf_name = conf_name).delete()
        except Exception, e:
            log.error("conf_name=%s, e=%s" % (conf_name, e))

    # 检查语法
    label, row_index, desc = check_syntax(candidate_words, label_define, \
                                          select_conf_list, price_conf_list, delete_conf)
    if label:
        if row_index == -1:
            dajax.script('PT.alert("您输入的 %s 存在语法错误，请检查并重新输入！")' % (label))
            return dajax
        else:
            dajax.script('PT.alert("您的 %s 存在语法错误，请检查重新输入！（行：%s , %s列）")' \
                         % (label, row_index, desc))
            return dajax

    if SelectConf.save_select_conf(conf_name, conf_desc, candidate_words, label_define, \
                        select_conf_list, price_conf_list, delete_conf, conf_type = 3, new_create = True):
        item.selectconf_dict[model_type] = conf_name
        if item.save():
            dajax.script('PT.alert("保存成功！")')
        else:
            dajax.script('PT.alert("宝贝绑定失败！")')
    else:
        dajax.script('PT.alert("配置保存失败！")')
    return dajax

# 保留
def change_item(request, dajax):
    """"切换宝贝"""
    try:
        shop_id = int(request.POST['shop_id'])
        item_id = int(request.POST['item_id'])
        model_type = request.POST['model_type']
    except Exception, e:
        log.error('get paramters error, e=%s' % e)
        dajax.script('PT.alert("服务端接收到错误参数，导致如下异常：e="%s" ，请联系CRM负责人检查。");' % (e))
        return dajax

    try:
        item = Item.objects.get(shop_id = shop_id, item_id = item_id)
    except Exception, e:
        log.error("get item error, shop_id=%s, item_id=%s, e=%s" % (shop_id, item_id, e))
        dajax.script("PT.alert('未获取到宝贝信息！');")
    else:
        conf_name = item.selectconf_dict.get(model_type, '')
        item_conf = SelectConf.pack_select_word_conf(conf_name)
        is_existed = 1 if item_conf else 0

        product_word_list = item.product_word_list
        dcrt_word_list = item.get_decorate_word_list()
        sale_word_list = item.sale_word_list
        blackword_list = item.blackword_list
        include_list = item.include_word_list
        element_words_list = item.pure_title_word_list
        word_modifier = item.get_word_modifier_display()

        try:
            adg_id = Adgroup.objects.only('adgroup_id').\
                        filter(shop_id = shop_id, item_id = item_id)[0].adgroup_id
        except Exception, e:
            log.error("get adgroup error, e=%s" % e)
            dajax.script('PT.alert("该宝贝没有任何推广");')
        else:
            if not word_modifier:
                word_modifier = "系统"
            item_attrs = {
                            'pic_url':item.pic_url,
                            'adg_id':adg_id,
                            'item_id':item.item_id,
                            'shop_id':item.shop_id,
                            'operator':word_modifier,
                            'title':item.title,
                            'ele_info':','.join(map(str, element_words_list)),
                            'pro_info':','.join(map(str, product_word_list)),
                            'sale_info':','.join(map(str, sale_word_list)),
                            'deco_info':','.join(map(str, dcrt_word_list)),
                            'black_info':','.join(map(str, blackword_list)),
                            'word_modifier':item.get_word_modifier_display(),
                            'include_list':','.join(map(str, include_list))
                          }
            dajax.script("PT.CRMSelectWordManager.set_change_item_info(%s,%s,%s);" \
                         % (json.dumps(item_attrs), json.dumps(item_conf), is_existed))
    return dajax

# 保留
def show_trend(request, dajax):
    """获取计划趋势图数据"""
    def get_accout(shop_id, obj_id):
        return Account.objects.get(shop_id = shop_id), 'CrmAccount'
    def get_campaign(shop_id, obj_id):
        return Campaign.objects.get(shop_id = shop_id, campaign_id = obj_id), 'CrmCampaign'
    def get_adgroup(shop_id, obj_id):
        return Adgroup.objects.get(shop_id = shop_id, adgroup_id = obj_id), 'CrmAdgroup'
    def get_keword(shop_id, obj_id):
        return Keyword.objects.get(shop_id = shop_id, keyword_id = obj_id), 'CrmKeyword'
    def get_default(shop_id, obj_id):
        return None, ''

    try:
        shop_id = int(request.POST['shop_id'])
        obj_id = int(request.POST['obj_id'])
        get_type = int(request.POST['get_type'])
        rpt_days = int(request.POST.get('rpt_days', 7))
    except Exception, e:
        log.error('get paramiters error, e=%s' % (e))
        scripts = "PT.alert('服务器获取参数失败，请联系CRM管理员。');"
    else:
        try:
            obj_mapping = {
                                1:get_accout,
                                2:get_campaign,
                                3:get_adgroup,
                                4:get_keword
                           }
            obj, mark = obj_mapping.get(get_type, get_default)(shop_id, obj_id)
        except Exception, e:
            log.error('get campaign error, e=%s' % (e))
            scripts = "PT.alert('获取计划失败。');"
        else:
            if obj :
                limit_datetime = datetime.datetime.now() - datetime.timedelta(days = rpt_days + 1)
                snap_list = obj.get_snap_list(rpt_days = rpt_days)
                if snap_list:
                    category_list, series_cfg_list = get_trend_chart_data(data_type = get_type, rpt_list = snap_list)
                    scripts = "PT.%s.show_trend(%s,%s,%s)" % (mark, obj_id, json.dumps(category_list), json.dumps(series_cfg_list))
                else:
                    scripts = "PT.alert('未搜索到历史数据，请确认是否刚刚进行推广。');"
            else:
                scripts = "PT.alert('数据库获取数据失败，请联系管理员。');"
    dajax.script(scripts)
    return dajax

# 保留
def save_cat_select_conf(request, dajax):
    """另存为新的类目配置"""
    try:
        cat_id = int(request.POST.get('cat_id', 0))
        model_type = str(request.POST.get('model_type', ''))
        is_force = int(request.POST['is_force'])
        conf_name = str(request.POST['conf_name'])
        conf_desc = str(request.POST['conf_desc'])
        candidate_words = str(request.POST['candi_filter'])
        label_define = json.loads(request.POST['label_define_list'])
        select_conf_list = json.loads(request.POST['select_conf_list'])
        price_conf_list = json.loads(request.POST['price_conf_list'])
        delete_conf = json.loads(request.POST['delete_conf'])
    except Exception, e:
        log.error('get paramters error, e=%s' % e)
        dajax.script('PT.alert("异常，请联系CRM负责人检查。");')
        return dajax
    else:
        try:
            label, row_index, desc = check_syntax(candidate_words, label_define, select_conf_list, price_conf_list, delete_conf)
            if label:
                if row_index == -1:
                    dajax.script('PT.alert("您输入的 %s 存在语法错误，请检查并重新输入！")' % (label))
                    return dajax
                else:
                    dajax.script('PT.alert("您的 %s 存在语法错误，请检查重新输入！（行：%s , %s列）")' % (label, row_index, desc))
                    return dajax
        except Exception, e:
            log.error("get select info error, conf_name = %s, e=%s" % (conf_name , e))
            dajax.script("PT.alert('系统中不存在该配置，请检查您的配置名称是否正确');")
        else:
            try:
                cat_info = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat")
            except Exception, e:
                log.error("get cat_info error, cat_id = %s, e=%s" % (cat_id, e))
                dajax.script("PT.alert('系统中不存在该类目，请联系管理员！');")
            else:
                try:
                    if cat_info.selectconf_dict.has_key(model_type) and cat_info.selectconf_dict[model_type] and not is_force :
                        dajax.script("PT.alert('类目已绑定了自定义模板 \"%s\" ，如果非强制保存，该覆盖操作失败。');" % (cat_info.selectconf_dict[model_type]))
                    else:
                        if SelectConf.save_select_conf(conf_name, conf_desc, candidate_words, label_define, select_conf_list, price_conf_list, delete_conf, conf_type = 2, new_create = True):
                            cat_info.selectconf_dict[model_type] = conf_name
                            cat_info.save_single()
                            dajax.script("PT.CRMSelectWordManager.set_bind_end_status('%s','%s','%s');" % (cat_info.cat_id, cat_info.cat_name, conf_name))
                        else:
                            dajax.script("PT.alert('另存为类目操作失败');")
                except Exception, e :
                    log.error("bind select_conf to category logic error, e=%s" % e)
                    dajax.script("PT.alert('绑定出错，请联系管理员！');")
    return dajax

# 保留
def bind_cat_conf(request, dajax):
    """绑定类目配置"""
    try:
        cat_id = int(request.POST['cat_id'])
        conf_name = request.POST['conf_name']
        model_type = request.POST['model_type']
    except Exception, e:
        log.error("get parameters error! e=%s" % e)
        dajax.script("PT.alert('异常，请联系管理员。');")
    else:
        try:
            cat_info = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat")
        except Exception, e:
            log.error("get cat info error,cat_id=%s, e=%s" % (cat_id, e))
            dajax.script("PT.alert('没有该类目在系统中');")
        else:
            cat_info.selectconf_dict[model_type] = conf_name
            if cat_info.save_single(cat_info.selectconf_dict, "selectconf_dict"):
                dajax.script("PT.CRMSelectWordManager.set_bind_result();")
            else:
                dajax.script("PT.alert('绑定失败');")
    return dajax

# 保留
def get_default_select_conf(request, dajax):
    """获取默认模板"""
    try:
        conf_name = request.POST["conf_name"]
    except Exception, e:
        log.error("get parameters error, e=%s" % (e))
        dajax.script("PT.alert('异常，获取参数失败');")
    else:
        select_conf = SelectConf.pack_select_word_conf(conf_name)
        if select_conf:
            dajax.script("PT.CRMSelectWordManager.set_default_conf(%s);" % (json.dumps(select_conf)))
        else:
            dajax.script("PT.alert('获取失败，请尝试其他配置模板。');")
    return dajax

# 保留
def get_loading_info(request, dajax):
    """得到用于加载页面数据"""
    def get_loading_info_bycategory(obj_id):
        try:
            item_cursor = Item.objects.filter(cat_id = obj_id)
            item_obj = None
            adg_id = 0
            for item in  item_cursor:
                try:
                    tmp_id = Adgroup.objects.only('adgroup_id').filter(item_id = item.item_id)[0].adgroup_id
                    if tmp_id:
                        item_obj = item
                        adg_id = tmp_id
                        break
                except Exception, e:
                    # 此宝贝没有推广组
                    continue
        except Exception, e:
            log.error("exec error, cat_id=%s, e=%s" % (obj_id, e))
            return 0, 0, 0, 0, "该类目下无任何宝贝"
        else:
            if not item_obj:
                return 0, 0, 0, 0, "该类目的宝贝无任何推广"
        return item_obj.cat_id, item_obj.shop_id, item_obj.item_id, adg_id, ""

    def get_loading_info_byitem(obj_id):
        try:
            item = Item.objects.get(item_id = obj_id)
            adg_id = Adgroup.objects.only('adgroup_id').filter(item_id = item.item_id)[0].adgroup_id
        except Exception, e:
            log.error("get item error, item_id=%s, e=%s" % (obj_id, e))
            return 0, 0, 0, 0, "该宝贝在我们系统中不存在"
        return item.cat_id, item.shop_id, item.item_id, adg_id, ''

    def get_loading_info_byadgroup(obj_id):
        try:
            adgroup = Adgroup.objects.get(adgroup_id = obj_id)
            item = Item.objects.get(item_id = adgroup.item_id)
        except Exception, e:
            log.error("get item error, item_id=%s, e=%s" % (obj_id, e))
            return 0, 0, 0, 0, "该宝贝在我们系统中不存在"
        return item.cat_id, item.shop_id, item.item_id, adgroup.adgroup_id, ''

    try:
        search_type = request.POST['search_type']
        obj_id = int(request.POST["obj_id"])
    except Exception, e:
        log.error("get parameters error, e=%s")
        dajax.script("PT.alert('异常，获取参数失败。');")
    else:
        cat_id, shop_id, item_id, adg_id, reason = eval("get_loading_info_by%s(%s)" % (search_type, obj_id))
        if not reason:
            dajax.script("PT.CRMSelectWordManager.set_loading_info('%s','%s','%s','%s');" % (cat_id, shop_id, item_id, adg_id))
        else:
            dajax.script("PT.alert('%s');" % (reason))
    return dajax

#------------------------------------------------------------------------------------------------------------------------------

#===============================================================================
# customer_list功能对应的ajax-->end
#===============================================================================

#===============================================================================
# user_list功能对应的ajax-->start
#===============================================================================
# 保留
def get_perms_code(request, dajax):
    """获取权限码"""
    user_id = int(request.POST['user_id'])
    from apps.router.models import AdditionalPermission
    try:
        ap = AdditionalPermission.objects.get(user = user_id)
        perms_code = ap.perms_code
    except AdditionalPermission.DoesNotExist:
        log.info('ap is not found, user_id = %s' % (user_id))
        perms_code = ''
    dajax.script("PT.UserList.display_perms_info('%s', '%s');" % (perms_code, user_id))
    return dajax

# 保留
def update_perms_code(request, dajax):
    """修改额外权限码"""
    result = 'false'
    try:
        from apps.router.models import AdditionalPermission
        user_id = request.POST['uid']
        perms_code = request.POST['perms_code']
        if not perms_code:
            AdditionalPermission.objects.filter(user = user_id).delete()
        else:
            ap, _ = AdditionalPermission.objects.get_or_create(user_id = user_id)
            ap.perms_code = perms_code
            ap.save()
        result = 'true'
    except Exception, e:
        log.error('update perms code error, e=%s, user_id=%s' % (e, user_id))

    dajax.script("PT.UserList.update_perms_callback('%s','%s','%s');" % (result, perms_code, user_id))
    return dajax

# 保留
def exec_shopmngtask(request, dajax):
    """执行店铺任务"""
    from apps.engine.models import ShopMngTask
    result = False
    shop_id = int(request.POST.get('shop_id', 0))
    if shop_id:
        smt, _ = ShopMngTask.objects.get_or_create(shop_id = shop_id)
        result = smt.run_task()
    dajax.script("PT.alert('执行店铺任务%s!')" % (result and '成功' or '失败（原因可能是已过期，在运行，运行失败等）'))
    return dajax

# 保留
def reset_shopmngtask(request, dajax):
    """重置店铺任务状态"""
    shop_id = int(request.POST.get('shop_id', 0))
    try:
        from apps.engine.models import ShopMngTask
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

# 保留
def get_server(request, dajax):
    """获取用户所在服务器及服务器信息"""
    try:
        from apps.router.models import NickPort, Port
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
    dajax.script("PT.UserList.display_port_info('%s','%s', '%s');" % (nick, port_id, json.dumps(port_info_dict)))
    return dajax

# 保留
def update_server(request, dajax):
    """更改用户所在服务器"""
    result = 0
    nick = request.POST.get('nick', '')
    port_id = request.POST.get('port_id', 1)
    try:
        from apps.router.models import NickPort
        result = NickPort.objects.filter(nick = nick).update(port = port_id)
        if not result:
            raise Exception
        dajax.script("$.fancybox.close();")
    except Exception, e:
        log.error('update server error, e=%s, nick=%s, port_id=%s' % (e, nick, port_id))
    dajax.script("PT.alert('修改%s');" % (result and '成功' or '失败'))
    return dajax

# 保留
def run_mnt_task(request, dajax):
    """触发长尾托管任务运行"""
    dajax.script('PT.hide_loading();')
    task_id = ObjectId(request.POST['object_id'])
    try:
        mt = MntTask.objects.get(id = task_id)
    except MntTask.DoesNotExist:
        dajax.script('PT.alert("该任务不存在");')
        return dajax
    task_type = mt.get_task_type_display()
    result = MntTaskMng.run_task(mt, is_force = True)
    msg = '执行【%s】%s' % (task_type, result and '成功' or '失败，可能用户已经过期，或者该计划已被暂停或终止')
    dajax.script('PT.alert("%s");' % msg)
    return dajax

# 保留
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
                    task_info_dict.update({mnt_task.campaign_id:[]})
                task_info_dict[mnt_task.campaign_id].append({'_id':str(mnt_task.id), 'create_time':format_datetime(mnt_task.create_time), 'status':mnt_task.get_status_display(),
                                                             'failed_count':mnt_task.failed_count, 'task_type':mnt_task.get_task_type_display(), 'opt_list':mnt_task.opt_list,
                                                             'start_time':format_datetime(mnt_task.start_time), 'end_time':format_datetime(mnt_task.end_time)})

            camp_info_list = []
            for mnt_camp in mnt_camp_list:
                temp_task_list = task_info_dict.get(mnt_camp.campaign_id, [])
                camp_info_list.append({'camp_id':mnt_camp.campaign_id, 'start_time':format_datetime(mnt_camp.start_time), 'max_num':mnt_camp.max_num,
                                       'mnt_type':'%s: %s' % (mnt_camp.get_mnt_type_display(), camp_title_dict.get(mnt_camp.campaign_id, '')), 'task_list':temp_task_list})

            dajax.script('PT.UserList.display_mnt_info(%s)' % (json.dumps(camp_info_list)))
        else:
            dajax.script('PT.alert("亲，该用户未使用任何全自动计划！");')
        return dajax
    except Exception, e:
        log.exception('get_mnt_info error, shop_id=%s, e=%s' % (request.POST['shop_id'], e))
        dajax.script('PT.alert("亲，出错啦，请刷新页面重试！");')
        return dajax

# 保留
def update_mnt_max_num(request, dajax):
    """更改托管宝贝个数"""
    try:
        campaign_id = int(request.POST['camp_id'])
        max_num = int(request.POST.get('max_num', 0))
        MntCampaign.objects.filter(campaign_id = campaign_id).update(set__max_num = max_num)
        dajax.script("PT.alert('修改成功！');")
        return dajax
    except Exception, e:
        log.info('update_mnt_max_num error, shop_id=%s, e=%s' % (request.user.shop_id, e))
        dajax.script('PT.alert("亲，请刷新页面重试！");')
        return dajax

# 保留
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

# 保留
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

#===============================================================================
# user_list功能对应的ajax-->end
#===============================================================================

# ==============================================================================
# kwlib kw_manage 迁移 ajajx ---> start
#===============================================================================
# 保留
def get_sub_cat(request, dajax):
    cat_id = request.POST.get('cat_id')
    pt_obj = request.POST.get("pt_obj")
    result_list = []
    if cat_id or pt_obj:
        subcat_list = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat_child_list")
        for subcat_id in subcat_list:
            result_list.append({'cat_id':subcat_id, 'cat_name':Cat.get_cat_attr_func(cat_id = subcat_id, attr_alias = "cat_name")})
        dajax.script("PT.%s.set_sub_cat(%s)" % (pt_obj, json.dumps(result_list)))
    else:
        dajax.script("PT.alert('参数获取异常，请联系管理员。');")
    return dajax

# 保留
def save_word(request, dajax):
    keyword = request.POST.getlist('keyword[]')
    word_type = request.POST.get('word_type')
    kw_id = request.POST.get('kw_id', '') # kw_id 存在，则当前操作为修改记录后保存；若 kw_id 不存在，则当前操作添加记录

    msg = ''
    try:
        if word_type == 'prodword': # 类目内嵌对象, 1个类目:1条记录
            result = Cat.save_and_reset(kw_id, product_dict = {"match":keyword[2], "product":keyword[3]})
        elif word_type == 'saleword': # 类目内嵌对象, 1个类目:1条记录
            result = Cat.save_and_reset(kw_id, sale_dict = {"match":keyword[0], "sale":keyword[1]}, brand_is_mutex = int(keyword[2]))
        elif word_type in ['metaword', 'forbidword', 'includeword', 'brandword']: # 类目内嵌对象, 1个类目:n条记录
            cat_id = int(keyword[0])
            update_dict = {}
            cat = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat")
            if word_type == 'metaword':
                match_word, metaphor_word = keyword[2], keyword[3]
                has_exits = False
                if not kw_id:
                    for meta in cat.meta_list:
                        if meta.match == match_word:
                            has_exits = True
                            break
                if has_exits:
                    msg = '数据库中已存在该隐喻词，请重新输入'
                else:
                    old_dict = {'match': kw_id}
                    update_dict = {'match':match_word, 'metaphor':metaphor_word}
            elif word_type == 'forbidword':
                word, type = keyword[1], int(keyword[2])
                flag = False
                if not kw_id:
                    for brand in cat.forbid_list:
                        if brand.word == word:
                            flag = True
                if flag:
                    msg = '数据库中已存在该词，请重新输入'
                else:
                    old_dict = {'word': kw_id}
                    update_dict = {'word':word, 'type':type}
            elif word_type == 'brandword':
                word = keyword[1]
                flag = False
                if not kw_id:
                    for brand in cat.brand_list:
                        if brand.word == word:
                            flag = True
                if flag:
                    msg = '数据库中已存在该品牌词，请重新输入'
                else:
                    old_dict = {'word': kw_id}
                    update_dict = {'word': word}
            elif word_type == 'includeword':
                include, exclude = keyword[1], keyword[2]
                flag = False
                if not kw_id:
                    for el_word in cat.exclude_list:
                        if el_word.include == include:
                            flag = True
                if flag:
                    msg = '数据库中已存在该互斥词，请重新输入'
                else:
                    old_dict = {'include': kw_id}
                    update_dict = {'include': include, 'exclude': exclude.split(',')}

            if not msg:
                field_dict = {'metaword': 'meta_list', 'brandword': 'brand_list', 'forbidword': 'forbid_list', 'includeword': 'exclude_list'}
                field = field_dict[word_type]
                if kw_id:
                    result = Cat.update_embeded_array(cat_id, field, old_dict, update_dict)
                else:
                    result = Cat.add_embeded_array(cat_id, field, **update_dict)
                if not result:
                    msg = '操作失败，请联系管理员查看日志。'
        elif word_type == 'synoword':
            cat_id, cat_name = int(keyword[0]), keyword[1]
            old_cat_name = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat_path_name")
            cat = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat")
            if cat_id != 0 and (not old_cat_name or old_cat_name.upper() != cat_name.upper()):
                msg = '类目ID与类目名称不对应，请重新输入类目ID/类目名称'
            else:
                word_list = keyword[2]
                kw_dict = {'cat_id':cat_id, 'cat_name': cat_name, 'word_list': word_list}
                if kw_id:
                    synoword_coll.update({'_id':ObjectId(kw_id)}, {'$set':kw_dict})
                    SynonymWord.reload_single_cat_synoword(cat_id)
                elif synoword_coll.find_one({'cat_id':cat_id, 'word_list':word_list}):
                    msg = '数据库中已存在该同义词，请重新输入'
                else:
                    synoword_coll.insert(kw_dict)
                    SynonymWord.reload_single_cat_synoword(cat_id)
        elif word_type == 'meanword':
            word, level = keyword[0], int(keyword[1])
            kw_dict = {'word':word, 'level':level}
            if kw_id:
                pointless_coll.update({'_id':ObjectId(kw_id)}, {'$set':kw_dict})
                PointlessWord.update_memcache()
            elif pointless_coll.find_one(kw_dict):
                msg = '数据库中已存在该无意义词，请重新输入'
            else:
                pointless_coll.insert(kw_dict)
                PointlessWord.update_memcache()
        elif word_type == 'elemword':
            word, count = keyword[0], int(keyword[1])
            kw_dict = {'word':word, 'count':count}
            if kw_id:
                word_coll.update({'_id':ObjectId(kw_id)}, {'$set':kw_dict})
            else:
                word_coll.insert(kw_dict)
    except Exception, e:
        log.exception('e=%s' % (e))
        msg += '保存失败，请重新保存'

    dajax.script("PT.CrmKwManage.save_word_back('%s')" % msg)
    return dajax

# 保留
def test_prod_word(request, dajax):
    keyword = request.POST.getlist('keyword[]')
    if not keyword or not keyword[0]:
        dajax.script("PT.hide_loading();PT.alert('类目ID不能为空')")
        return dajax

    cat_id, cat_name, match_word, product_word = int(keyword[0]), keyword[1], keyword[2], keyword[3]

    try:
        # 根据类目爬宝贝标题
        req = urllib2.Request(url = 'http://list.taobao.com/itemlist/default.htm?_input_charset=utf-8&json=on&cat=%s' % cat_id)
        f = urllib2.urlopen(req)
        contain = json.loads(f.read().decode('gbk'))
    except Exception, e:
        log.error('e=%s, cat_id=%s' % (e, cat_id))
        contain = {'cat':None}

    if contain.has_key('cat') and contain['cat'] and contain['cat']['displayName'].upper() == cat_name.upper():
        item_list = contain['itemList']
        source_flag = 0
    else: # 从我们的数据库中读取该类目下的宝贝
        from apps.subway.models_item import item_coll
        item_cur = item_coll.find({'cat_id':cat_id}, {'_id':1, 'title':1}).limit(50)
        item_list = [{'title':i['title'], 'itemId':i['_id']} for i in item_cur]
        source_flag = 1

    result_list, match_list = [], []
    product_list = product_word and product_word.split(',') or []
    # 分解宝贝标题，从中找到可匹配到的产品词
    for item in item_list:
        title = item['title']
        try:
            if match_word:
                from apps.kwslt.base import get_match_word
                word_list = ChSegement.split_title_new_to_list(title = title)
                match_list = get_match_word(rule_list = match_word.split(','), words_list = word_list)
            match_str = ','.join(set(match_list) | set(product_list))
        except Exception, e:
            log.error('get match string error, item_titile=%s, e=%s' % (title, e))
            continue
        result_list.append({'title':title, 'item_id':item['itemId'], 'match_str':match_str})
    dajax.script("PT.CrmKwManage.test_result(%s,%s)" % (source_flag, json.dumps(result_list)))
    return dajax

# 保留
def refresh_elemword_mem(request, dajax):
    flag = 0
    try:
        ChSegement.update_memcache()
        ChSegement.load_to_mem(is_need_refresh = True)
        flag = 1
    except Exception, e:
        log.error("e=%s" % e)
    finally:
        dajax.script("PT.CrmKwManage.refresh_men_back(%s)" % flag)
        return dajax

# 保留
def get_kw_list(request, dajax):
    # TODO wuhuaqiao 20141113 改变数据库后该页面需要重新设计
    cat_id = int(request.POST.get('cat_id'))
    flag = Cat._get_collection().find_one({'_id':cat_id}) and 1 or 0
    # 验证 CatInfo 中是否存在 cat_id
    if not flag:
        log.info('can not find the cat from db and cat_id=%s' % (cat_id))
        dajax.script('PT.CrmKwManage.append_table_data(0,[],[])')
        return dajax

    word_type = request.POST.get('word_type')
    page_info = json.loads(request.POST.get('page_info', '{}'))
    search_word = page_info['sSearch']
    page_size = page_info['iDisplayLength']
    page_offset = page_info['iDisplayStart']

    json_kw_list = []
    filter_dict = {'cat_id':{'$in':[0, cat_id]}}
    if word_type == 'prodword':
        # 页面需要调整
        prodword = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "product_dict")
        page_count = prodword and 1 or 0
        if prodword:
            json_kw_list = [{'kw_id':str(cat_id)
                             , 'cat_id':cat_id
                             , 'cat_name':Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat_name")
                             , 'match_word':prodword.match
                             , 'product_word':prodword.product
                             }]
    elif word_type == 'saleword':
        # 页面需要调整
        filter_dict = {'cat_id':cat_id}
        saleword = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "sale_dict")
        brand_is_mutex = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "brand_is_mutex")
        page_count = 1
        match_word, sale_words = saleword.match, saleword.sale
        json_kw_list = [{'kw_id':str(cat_id)
                         , 'cat_id':cat_id
                         , 'cat_name':Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat_name")
                         , 'match_word':match_word
                         , 'sale_words':sale_words
                         , 'is_mutex':brand_is_mutex
                         }]
    elif word_type == 'metaword':
        obj_list = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "meta_list")
        page_count = len(obj_list)
        count = 0
        for obj in obj_list:
            json_kw_list.append({'kw_id':obj.match
                                 , 'cat_id':cat_id
                                 , 'cat_name':Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat_path_name")
                                 , 'match_word':obj.match
                                 , 'metaphor_word':obj.metaphor
                                 })
            count += 1
    elif word_type == 'elemword':
        filter_dict = {}
        if search_word:
            filter_dict.update({'word':re.compile(search_word)})
        elemword_list = word_coll.find(filter_dict).sort([('_id', -1)]).skip(page_offset).limit(page_size)
        page_count = word_coll.find(filter_dict).count()
        for ew in elemword_list:
            json_kw_list.append({'kw_id':str(ew['_id']), 'word':ew['word'], 'count':ew['count']})
    elif word_type == 'synoword':
        if search_word:
            filter_dict.update({'word_list':re.compile(search_word)})
        synoword_list = synoword_coll.find(filter_dict).sort([('_id', -1)]).skip(page_offset).limit(page_size)
        page_count = synoword_coll.find(filter_dict).count()
        for sw in synoword_list:
            json_kw_list.append({'kw_id':str(sw['_id'])
                                 , 'cat_id':sw['cat_id']
                                 , 'cat_name':sw['cat_name'] if sw.has_key('cat_name') else ''
                                 , 'word_list':sw['word_list']
                                 })
    elif word_type == 'forbidword':
        forbidword_list = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "forbid_list")
        common_list = Cat.get_cat_attr_func(cat_id = 0, attr_alias = "forbid_list")
        page_count = len(forbidword_list) + len(common_list)
        count = 0
        for fw in forbidword_list:
            json_kw_list.append({'kw_id':fw.word, 'cat_id':cat_id, 'word':fw.word, 'type':fw.type})
            count += 1
        for fw in common_list:
            json_kw_list.append({'kw_id':fw.word, 'cat_id':0, 'word':fw.word, 'type':fw.type})
            count += 1
    elif word_type == 'includeword':
        if search_word:
            filter_dict.update({'include_list':re.compile(search_word)})
        includeword_list = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "exclude_list")
        common_list = Cat.get_cat_attr_func(cat_id = 0, attr_alias = "exclude_list")
        page_count = len(includeword_list) + len(common_list)
        count = 0
        for iw in includeword_list:
            json_kw_list.append({'kw_id':iw.include, 'cat_id':cat_id, 'include_word':iw.include, 'exclude_word':','.join(iw.exclude)})
        for iw in common_list:
            json_kw_list.append({'kw_id':iw.include, 'cat_id':0, 'include_word':iw.include, 'exclude_word':','.join(iw.exclude)})
    elif word_type == 'brandword':
        top_cat_id = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "root_cat_id")
        brandword_list = Cat.get_cat_attr_func(cat_id = top_cat_id, attr_alias = "brand_list")
        page_count = len(brandword_list)
        count = 0
        for bw in brandword_list:
            json_kw_list.append({'kw_id':bw.word, 'cat_id':top_cat_id, 'word':bw.word})
    elif word_type == 'meanword':
        filter_dict = {}
        if search_word:
            filter_dict.update({'word':re.compile(search_word)})
        obj_cur = pointless_coll.find(filter_dict).sort([('_id', -1)]).skip(page_offset).limit(page_size)
        page_count = pointless_coll.find(filter_dict).count()
        for obj in obj_cur:
            json_kw_list.append({'kw_id':str(obj['_id']), 'word':obj['word'], 'level':obj.get('level', 1)})

    page_info['iTotalRecords'] = page_count
    page_info['iTotalDisplayRecords'] = page_count
    dajax.script('PT.CrmKwManage.append_table_data(1,%s,%s)' % (json.dumps(page_info), json.dumps(json_kw_list)))
    return dajax

# 保留
def delete_word(request, dajax):
    word_type = request.POST.get('word_type')
    kw_id = request.POST.get('kw_id')
    kw_list = request.POST.getlist('kw_list[]')
    result = False
    try:
        if word_type in ['prodword', 'metaword', 'forbidword', 'includeword', 'brandword']:
            if word_type == 'prodword':
                kwargs = {'match': kw_list[2], 'product': kw_list[3]}
            elif word_type == 'metaword':
                kwargs = {'match': kw_list[2], 'metaphor': kw_list[3]}
            elif word_type == 'forbidword':
                kwargs = {'word': kw_list[1], 'type': int(kw_list[2])}
            elif word_type == 'includeword':
                kwargs = {'include': kw_id, 'exclude': kw_list[2].split(',')}
            elif word_type == 'brandword':
                kwargs = {'word': kw_list[1]}
            cat_id = int(kw_list[0])
            field_dict = {'prodword': 'product_dict', 'metaword': 'meta_list', 'brandword': 'brand_list', 'forbidword': 'forbid_list', 'includeword': 'exclude_list'}
            field = field_dict[word_type]
            result = Cat.delete_embeded_array(cat_id, field, **kwargs)
        else:
            filter_dict = {'id': ObjectId(kw_id)}
            if word_type == 'elemword':
                ChSegement.objects.get(**filter_dict).delete()
                result = True
            elif word_type == 'synoword':
                obj = SynonymWord.objects.get(**filter_dict)
                cat_id = obj.cat_id
                obj.delete()
                SynonymWord.reload_single_cat_synoword(cat_id = cat_id)
                result = True
            elif word_type == 'meanword':
                PointlessWord.objects.filter(**filter_dict).delete()
                PointlessWord.update_memcache()
                result = True
    except Exception, e:
        log.exception('e=%s' % (e))
    dajax.script('PT.CrmKwManage.delete_word_back(%s)' % int(result))
    return dajax

# 保留
def check_cat_id(request, dajax):
    cat_id = int(request.POST.get('cat_id', 0))
    flag = cat_coll.find_one({'_id':cat_id}) and 1 or 0
    try:
        cat_path = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat_path_id")
#         cat_path = cat_list_str and '%s %s' % (cat_list_str, cat_id) or str(cat_id)
    except Exception, e:
        log.error('get cat parent ids error,cat_id=%s, e=%s' % (cat_id, e))
    dajax.script('PT.CrmKwManage.check_id_back(%s,%s,"%s")' % (flag, cat_id, cat_path))
    return dajax

# 保留
def clear_shop_items_cache(request, dajax):
    """真正对某一店铺进行所有宝贝缓存清理"""
    shop_id = int(request.POST.get('shop_id', 0))
    if shop_id > 0:
        try:
            item_cursor = Item.objects.only('item_id').filter(shop_id = shop_id)
        except Exception, e:
            log.error("get items error, shop_id=%s, e=%s" % (shop_id, e))
        else:
            del_list = []
            fail_list = []
            for item in item_cursor:
                if hasattr(item, 'item_id'):
                    Item.delete_item_cache_byitemid(item.item_id)
                    del_list.append(item.item_id)
                else:
                    fail_list.append(item.item_id)
        if fail_list:
            dajax.script('PT.alert("已清理%s个宝贝，存在%s个宝贝清理失败。");' \
                         % (len(del_list), len(fail_list)))
        else:
            dajax.script('PT.alert("已清理%s个宝贝，清理完成。");' % (len(del_list)))
    else:
        dajax.script('PT.alert("获取店铺ID出错，请联系管理员。");')
    return dajax

# 保留
@convert_cache_data
def submit_msg(request, dajax, is_use_cache = False):
    psuser_id = get_psuser(request).id
    obj_list = json.loads(request.POST.get('obj_list'))
    msg_type = int(request.POST.get('msg_type', 0))
    obj_type = int(request.POST.get('obj_type', 0))
    content = str(request.POST.get('content', ''))
    title = str(request.POST.get('title', ''))

    if is_use_cache:
        field_list = ['shop_id', 'camp_id', 'adg_id', 'kw_id']
        field_1 = field_list[0]
        field_2 = field_list[obj_type]
        obj_list = []
        for data in request.cache_data:
            if data.has_key(field_1) and data.has_key(field_2) :
                obj_list.append({'shop_id':data[field_1], 'obj_id':data[field_2]})

    flag = 0
    try:
        PsMessage.bulk_add_msg(psuser_id = psuser_id, msg_type = msg_type, obj_type = obj_type, title = title, content = content, obj_list = obj_list)
    except Exception, e:
        log.error("submit msg error, e = %s" % (e))
        flag = 1
    obj_id_list = [obj['obj_id'] for obj in obj_list]
    dajax.script("PT.CrmCondition.submit_msg_back(%s,%s)" % (flag, obj_id_list))
    return dajax

# 保留
def get_msg(request, dajax):
    shop_id = int(request.POST.get('shop_id', 0))
    obj_id = int(request.POST.get('obj_id'))
    obj_type = int(request.POST.get('obj_type', 0))

    error_flag, msg_list = 0, []
    try:
        msgs = PsMessage.objects.filter(shop_id = shop_id, object_id = obj_id, object_type = obj_type).order_by('-last_modified')
        for msg in msgs:
            read_status = msg.message_type and (msg.is_prompt and '未读' or '已读') or '-----'
            psuser = PSUser.objects.filter(id = msg.psuser_id)
            msg_list.append({'psuser':psuser and psuser[0].name_cn or '--------', 'last_modified':time_humanize(msg.last_modified),
                             'title':msg.title, 'content':msg.content, 'msg_type':msg.get_message_type_display(), 'read_status':read_status})
    except Exception, e:
        log.error("submit msg error, shop_id = %s, obj_id = %s, obj_type =%s, e = %s" % (shop_id, obj_id, obj_type, e))
        error_flag = 1
    finally:
        dajax.script("PT.CrmCondition.get_msg_back(%s,%s,%s)" % (error_flag, obj_id, json.dumps(msg_list)))
        return dajax

# 保留
def submit_sms(request, dajax):
    psuser_id = get_psuser(request).id
    phone_list = json.loads(request.POST.get('phone_list'))
    content = str(request.POST.get('content', ''))

    result = []
    # result = send_sms(receiver_list = phone_list, content = content)
    if 'code' in result and result['code'] == 0:
        log.info('crm send sms ok, psuser_id=%s' % psuser_id)
        result_dict = {'is_success':1, 'count':len(phone_list)}
    else:
        error_msg = "网络或者短信平台出问题"
        log.info('crm send sms error, psuser_id=%s, e=%s' % (psuser_id, error_msg))
        result_dict = {'is_success':0, 'error_msg':error_msg}
    dajax.script('PT.CrmAccount.submit_sms_back(%s)' % (json.dumps(result_dict)))
    return dajax

#===============================================================================
# new_customer_list 新版客户管理系统ajax->end
#===============================================================================
# 保留
def add_jlpoint(request, dajax):
    try:
        from apps.router.models import Point
        nick = request.POST.get('nick', '')
        point = int(request.POST.get('point', 0))

        Point.objects.create(type = True, nick_1 = nick, nick_2 = '活动赠送',
                                      point_1 = point, point_2 = 0)
        CacheAdpter.delete(CacheKey.WEB_JLB_COUNT % nick, 'web')

        dajax.script("PT.alert('添加成功!');")
        dajax.script("PT.AddPoint.append_history('%s', '%s');" % (nick, point))
    except Exception, e:
        log.error('add jlpoint error, e=%s, nick=%s' % (e, request.POST.get('nick', '')))
        dajax.script("PT.alert('添加精灵币失败！');")
    return dajax

# 保留
def get_camp_mntcfg(request, dajax):
    """打开计划的配置项，包括任务周期配置与策略配置"""
    try:
        shop_id = request.POST['shop_id']
        campaign_id = request.POST['campaign_id']
        mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
        mnt_cfg_list = []
        taskcfg_list = TaskConfig.objects.filter(cfg_type = 'mnt').order_by('-tag_name')
        for obj in taskcfg_list:
            is_current = 0
            if obj.tag_name in mnt_camp.mnt_cfg_list:
                is_current = 1
            temp_dict = {'name':obj.tag_name, 'cfg_detail':json.loads(obj.cfg_detail), 'is_current':is_current}
            mnt_cfg_list.append(temp_dict)

        result_dict = {'mnt_cfg_list':mnt_cfg_list, 'shop_id':shop_id, 'campaign_id':campaign_id}
        dajax.script("PT.CrmCampaign.display_cfg_dialog(%s);" % (json.dumps(result_dict)))
    except Exception, e:
        log.exception("open_cfg_dialog error, e=%s" % e)
        dajax.script("PT.alert('读取配置信息失败，请刷新重试！');")
    return dajax

# 保留
def save_cfg(request, dajax):
    """保存任务配置"""
    try:
        tag_name = request.POST['tag_name']
        cfg_detail = request.POST['cfg_detail']
        cfg_type = request.POST['cfg_type']
        try:
            tc = TaskConfig.objects.get(tag_name = tag_name)
            tc.cfg_detail = cfg_detail
            tc.save()
            TaskConfig.refresh_config(tag_name = tag_name) # 刷新缓存
        except DoesNotExist:
            TaskConfig.objects.create(tag_name = tag_name, cfg_type = cfg_type, cfg_detail = cfg_detail)
            dajax.script("PT.TaskCfgList.persistent_new_cfg('%s');" % cfg_type) # 将输入框等页面固定化
        msg = "保存成功！"
    except ValueError:
        msg = "亲，配置的格式不对，请检查重试！"
    except Exception, e:
        msg = "保存配置出错，请刷新重试！"
        log.exception("open_cfg_dialog error, e=%s" % e)
    dajax.script("PT.alert('%s');" % msg)
    return dajax

# 保留
def delete_cfg(request, dajax):
    """删除任务配置"""
    try:
        tag_name = request.POST['tag_name']
        TaskConfig.objects.filter(tag_name = tag_name).delete()
        msg = "删除成功！"
    except Exception, e:
        msg = "删除配置出错，请刷新重试！"
        log.exception("open_cfg_dialog error, e=%s" % e)
    dajax.script("PT.alert('%s');" % msg)
    return dajax

# 保留
def save_camp_cfg(request, dajax):
    """修改全自动计划相关联的配置项"""
    try:
        shop_id = int(request.POST['shop_id'])
        campaign_id = int(request.POST['campaign_id'])
        cfg_list = request.POST.getlist('cfg_list[]')
        MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id).update(set__mnt_cfg_list = cfg_list)
        # stgy_cfg = request.POST['stgy_cfg']
        # cycle_cfg = request.POST['cycle_cfg']
        # opt_cfg = request.POST['opt_cfg']
        # MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id).update(set__stgy_cfg = stgy_cfg, set__cycle_cfg = cycle_cfg, set__opt_cfg = opt_cfg)
        msg = "保存成功！"
        dajax.script("PT.light_msg('修改配置','%s');$('#modal_camp_cfg').modal('hide');" % msg)
    except Exception, e:
        msg = "保存配置出错，请刷新重试！"
        log.exception("open_cfg_dialog error, e=%s" % e)
        dajax.script("PT.alert('%s');" % msg)
    return dajax

# 保留
def open_command_dialog(request, dajax):
    try:
        instruction_list = []
        ic_list = []
        for ic in ic_list:
            instruction_list.append({'name':ic.name, 'create_time':ic.create_time, 'scope':ic.scope, 'cond':ic.cond, 'desc':ic.desc, 'operate':ic.operate})

        valid_conf_name = ['auto_change', 'auto_select']
        valid_conf_name.extend(list(SelectConf.objects.values_list('conf_name').order_by('conf_name')))

        opt_list = [{'name':'下载关键词报表', 'func':'download_kwrpt', 'args':{}},
                    {'name':'同步质量得分', 'func':'sync_qscore', 'args':{}},
                    {'name':'关键词改价删除', 'func':'optimize_keywords', 'args':{'instrcn_list':[], 'manual_flag':True}},
                    {'name':'修改限价外关键词', 'func':'modify_out_limit_price', 'args':{}},
                    {'name':'清空已删词', 'func':'clear_deletedwords', 'args':{}},
                    {'name':'加词', 'func':'add_keywords', 'args':{'min_num':140, 'conf_name':valid_conf_name}},
                    {'name':'宝贝换词', 'func':'init_new_adgroups', 'args':{}}, ]
        dajax.script("PT.CrmAdgroup.display_cmd_dialog(%s,%s);" % (json.dumps(instruction_list), json.dumps(opt_list)))
    except Exception, e:
        log.exception('open_command_dialog error, e=%s' % e)
        dajax.script("PT.alert('打开命令发送对话框失败，请联系系统管理员！');")
    return dajax

# 保留
@convert_cache_data
def send_cmd(request, dajax, is_use_cache = False):
    try:
        dajax.script("PT.alert('该功能不可用');")
        return dajax
        if is_use_cache:
            adg_data = [{'shop_id':data["shop_id"], 'campaign_id':data["camp_id"], 'adgroup_id':data['adg_id']} for data in request.cache_data if data.has_key('shop_id') and data.has_key('camp_id')]
        else:
            adg_data = json.loads(request.POST['adg_list'])

        opt_list = json.loads(request.POST['opt_list'])
        # 命令模型中要保存数据
        opter_dict = {}
        adg_dict = {}
        adg_id_list = []
        for adg in adg_data:
            temp_key = '%s-%s' % (adg['shop_id'], adg['campaign_id'])
            if temp_key not in adg_dict:
                opter_info = opter_dict.setdefault(adg['shop_id'], [])
                if not opter_info:
                    mnt_opter, opter_name = analysis_web_opter(request)
                    opter_dict[adg['shop_id']] = [mnt_opter, opter_name]
                else:
                    mnt_opter, opter_name = opter_info
                adg_dict[temp_key] = [[], mnt_opter, opter_name]
            adg_dict[temp_key][0].append(adg['adgroup_id'])
            adg_id_list.append(adg['adgroup_id'])

        cmd_list = []
        for opt in opt_list:
            args_list = []
            for arg, value in opt['args'].items():
                args_list.append('%s=%s' % (arg, value))

            cmd_list.append('%s(%s)' % (opt['func'], ','.join(args_list)))
        cmd_str = ';'.join(cmd_list)

        uo = UserOrder.create_order(psuser_id = get_psuser(request).id, command_detail = cmd_str, query_dict = "{'_id':{'$in':%s}}" % adg_id_list, from_source = 1)
        if not uo:
            dajax.script("PT.alert('命令已生成！');")
            return dajax
        uo.task_id_list = MntTaskMng.generate_task_bycmd(adg_dict = adg_dict, opt_list = opt_list, reporter = uo.id) # 注意：参数中一些int型的，页面上传回来是str，注意在函数中强转
        uo.save()
        dajax.script("PT.alert('保存成功！');")
    except Exception, e:
        log.exception("save_command error, e=%s" % e)
        dajax.script("PT.alert('保存命令失败，请刷新重试！');")
    return dajax

# 保留
def get_cmd_history(request, dajax):
    try:
        task_id_list = []
        uo_list = UserOrder.objects.filter(psuser_id = get_psuser(request).id, create_time__gte = datetime.datetime.now() - datetime.timedelta(days = 15)).order_by('-create_time')
        for uo in uo_list:
            task_id_list.extend(uo.task_id_list)

        task_dict = {}
        task_list = MntTask.objects.filter(id__in = task_id_list)
        for task in task_list:
            task_dict.update({task.id:{'_id':str(task.id), 'create_time':format_datetime(task.create_time), 'status':task.get_status_display(),
                                       'failed_count':task.failed_count, 'task_type':task.get_task_type_display(), 'opt_list':task.opt_list,
                                       'start_time':format_datetime(task.start_time), 'end_time':format_datetime(task.end_time)}})

        result_list = []
        for uo in uo_list:
            uo.task_list = []
            for task_id in uo.task_id_list:
                if task_id in task_dict:
                    uo.task_list.append(task_dict[task_id])

            result_list.append({'query_dict':uo.query_dict,
                                'create_time':format_datetime(uo.create_time),
                                'cmd_detail':uo.command_detail,
                                'task_list':uo.task_list,
                                'progress': '%s/%s' % (uo.success_count, len(uo.task_id_list))
                                })
        dajax.script("PT.CrmAdgroup.display_cmd_history(%s)" % json.dumps(result_list))
    except Exception, e:
        log.exception('get_cmd_history error, e=%s' % e)
        dajax.script("PT.alert('获取命令记录失败，请刷新重试！');")
    return dajax


# 保留
def get_dangerous_info(request, dajax):
    """获取 余额不足，下线计划，宝贝被排查信息"""
    def balance_lte_zero(shop_ids):
        return [acc.shop_id for acc in Account.objects.only('shop_id').\
                filter(shop_id__in = shop_ids, balance__lte = 10.00)]

    def budget_lte_zero(shop_ids):
        camp_list = [ mnt.campaign_id for mnt in MntCampaign.objects.\
                     only('campaign_id').filter(shop_id__in = shop_ids)]
        return list(set([camp.shop_id for camp in Campaign.objects.only('shop_id').\
                         filter(shop_id__in = shop_ids, campaign_id__in = camp_list, \
                                online_status = 'online', settle_status = 'offline')]))

    def item_vaolation(shop_ids):
        return list(set([ adg.shop_id for adg in Adgroup.objects.only('shop_id').\
                         filter(shop_id__in = shop_ids, mnt_type__in = [1, 2], \
                                offline_type = 'audit_offline', online_status = 'offline')]))

    def get_reset_cache(psuser_id):
        today = datetime.date.today()
        end_day = today - datetime.timedelta(days = 15)
#         article_codes = Const.COMMON_SUBSCRIBE_MAPPING['rjjh']
#         shop_list = [subscribe.shop_id for subscribe in \
#                 Subscribe.objects.only('shop_id').filter(start_date__lte = today, end_date__gt = end_day, \
#                                                            article_code__in = article_codes, operater = psuser_id)]
        shop_list = [subscribe.shop_id for subscribe in \
                Subscribe.objects.only('shop_id').filter(start_date__lte = today, end_date__gt = end_day, \
                                                           category = 'rjjh', operater = psuser_id)]
        shop_list = list(set(shop_list))

        success_list = []
        fail_list = []
        for shop_id in shop_list:
            if Downloader.download_all_struct(shop_id, False):
                success_list.append(shop_id)
            else:
                fail_list.append(shop_id)

        budget_zero_list = budget_lte_zero(success_list)
        balance_zero_list = balance_lte_zero(success_list)
        item_vaolation_list = item_vaolation(success_list)

        store_dict = {
            'budget_zero_list':budget_zero_list,
            'balance_zero_list':balance_zero_list,
            'item_vaolation_list':item_vaolation_list,
            'exec_time':cur_time
          }

        return store_dict

    def convert_nicks(*shop_ids_list):
        temp_list = []
        for shop_ids in shop_ids_list:
            temp_list.extend(shop_ids)

        nick_mappings = {int(user.shop_id):user.nick for user in \
                            User.objects.only('shop_id', 'nick').filter(shop_id__in = map(str, temp_list))}

        result_list = []
        for shop_ids in shop_ids_list:
            temp_list = []
            for shop_id in shop_ids:
                key = int(shop_id)
                if key in nick_mappings:
                    temp_list.append((shop_id, nick_mappings[key]))

            result_list.append(temp_list)

        return result_list

    psuser_id = get_psuser(request).id

    cache_key = CacheKey.CRM_RJJH_DANGEROUS_INFO % (psuser_id)
    cache_lock_key = CacheKey.CRM_RJJH_DANGEROUS_INFO_LOCK % (psuser_id)
    cache_data = crm_cache.get(cache_key)
    cache_lock = crm_cache.get(cache_lock_key)

    cur_time = datetime.datetime.now()
    two_hour_ago = cur_time - datetime.timedelta(seconds = 60 * 60)
    if not cache_data or two_hour_ago > cache_data['exec_time']:
        if not cache_lock :
            crm_cache.set(cache_lock_key, True)
            try:
                store_dict = get_reset_cache(psuser_id)
                crm_cache.set(cache_key, store_dict)
                cache_data = store_dict
            except Exception, e:
                log.error('get problem user error, psuser_id=%s, e=%s' % (psuser_id, e))
                cache_data = {}
            crm_cache.set(cache_lock_key, False)
        else:
            cache_data = {}

    balance_zero_list = cache_data.get('balance_zero_list', [])
    budget_zero_list = cache_data.get('budget_zero_list', [])
    item_vaolation_list = cache_data.get('item_vaolation_list', [])

    budget_zero_list, balance_zero_list, item_vaolation_list = \
        convert_nicks(budget_zero_list, balance_zero_list, item_vaolation_list)

    result = []
    if balance_zero_list:
       result.append({'title':'余额不足 (<10元)', 'val':balance_zero_list})
    if budget_zero_list:
       result.append({'title':'计划下线', 'val':budget_zero_list})
    if item_vaolation_list:
       result.append({'title':'宝贝被处罚', 'val':item_vaolation_list})

    dajax.script("PT.CrmCondition.get_dangerous_info_back('%s');" % (json.dumps(result)))
    return dajax

#===============================================================================
# # crm_adgroup、crm_campaign的计划配置、命令发送相关ajax-->end
#===============================================================================
# 保留
def get_creative_by_id(request, dajax):
    from apps.web.ajax import get_creative_by_id
    return get_creative_by_id(request = request, dajax = dajax)

# 保留
def update_creative(request, dajax):
    from apps.web.ajax import update_creative
    return update_creative(request = request, dajax = dajax)

# 保留
def add_creative(request, dajax):
    from apps.web.ajax import add_creative
    return add_creative(request = request, dajax = dajax)

# 保留
def generate_crt_title(request, dajax):
    from apps.web.ajax import generate_crt_title
    return generate_crt_title(request = request, dajax = dajax)

# 保留
def get_item_imgs(request, dajax):
    from apps.web.ajax import get_item_imgs
    return get_item_imgs(request = request, dajax = dajax)
