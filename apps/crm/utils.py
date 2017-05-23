# coding=UTF-8

from apps.common.utils.utils_log import log
from apps.common.constant import Const
from apps.common.utils.utils_collection import genr_sublist
from apilib import get_tapi
from apps.engine.models import ShopMngTask
from apps.subway.models_keyword import kw_coll, Keyword
from apps.subway.upload import delete_keywords, add_keywords, modify_cmp_kw_price_log, del_cmp_kw_log

from apps.crm.service import CrmCacheServer
from apps.kwslt.models_cat import Cat

def crm_login_download(user_id, valid_accounts):
#     acct_cursor = account_coll.find({'consult_id':user_id})
#     shop_id_list = [acct['_id'] for acct in acct_cursor]

    shop_id_list = map(int, valid_accounts)

    runnable_list = []
    smt_list = ShopMngTask.objects.filter(shop_id__in = shop_id_list)
    for smt in smt_list:
        if smt.is_runnable() and smt.status != 0:
            runnable_list.append(smt)

    if runnable_list:
        import threading

        for temp_list in genr_sublist(runnable_list, 10): # 多少线程可斟酌调整
            thread_list = []
            for temp_smt in temp_list:
                thread = threading.Thread(target = temp_smt.run_task)
                thread.start()
                thread_list.append(thread)

            for thread in thread_list:
                thread.join()

    return True

def remame_dictionary_key(obj_dict, replace_dict):
    """修改字典中某些key的名字"""
    if replace_dict:
        for old_key, new_key in replace_dict.items():
            if obj_dict.has_key(old_key):
                value = obj_dict.pop(old_key)
                obj_dict.update({new_key:value})
    return obj_dict

def get_init_conditon(cond_type):
    try:
        cond_type = int(cond_type)
    except Exception, e:
        log.error('input paras error, e=%s')
        return [], []

    try:
        top_cats_list = Cat.get_subcat_list(cat_id = 0)
    except Exception, e:
        log.exception('e=%s' % e)
        top_cats_list = []

    cond_type_list = [
                                    ['account', '账户', Const.CRM_FILTER_REPORT_FIELDS[0]] ,
                                    ['campaign', '计划', Const.CRM_FILTER_REPORT_FIELDS[1]],
                                    ['adgroup', '宝贝', Const.CRM_FILTER_REPORT_FIELDS[2]],
                                    ['keyword', '关键词', Const.CRM_FILTER_REPORT_FIELDS[3]]
                                ]

#     init_conditon_dict = {'top_cats_list':top_cats_list, 'cond_type_list':cond_type_list[:cond_type + 1], 'rpt_cond_list':rpt_cond_list}
    return top_cats_list, cond_type_list[:cond_type + 1]

def record_crm_log(shop_id, camp_id, inc_num, low_num, del_num, user_name, mnt_type = 2, opter = 2):
    """记录crm日志"""
    if inc_num or low_num:
        opt_desc_list = []
        if inc_num:
            opt_desc_list.append('加价%s个' % (inc_num))
        if low_num:
            opt_desc_list.append('降价%s个' % (low_num))
        opt_desc = ', '.join(opt_desc_list)
        modify_cmp_kw_price_log(shop_id = shop_id, campaign_id = camp_id, opt_desc = opt_desc, opter = opter, opter_name = user_name)
    if del_num:
        del_cmp_kw_log(shop_id = shop_id, campaign_id = camp_id, opt_desc = '删除%s个' % (del_num), opter = opter, opter_name = user_name)

def rebuild_keyword_byadg(shop_id, camp_id, adg_id, tapi = None, opter = 2, opter_name = ''):
    """对已有关键词重新进行提交"""
    kw_cursor = kw_coll.find({'shop_id':shop_id, 'campaign_id':camp_id, 'adgroup_id':adg_id}, {'word':1, 'max_price':1, 'match_scope':1})
    if kw_cursor:
        kw_del_list = []
        kw_add_dict = {}
        for kw in kw_cursor:
            try:
                kw_del_list.append([adg_id, kw['_id'], kw['word'] , 0, 0, None])
                kw_add_dict[str(kw['_id'])] = [ kw['word'] , int(kw['max_price']), int(kw['match_scope']), None, None]
            except Exception, e:
                log.error('get key words error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, camp_id, e))
                continue

        if kw_del_list:
            if not tapi:
                tapi = get_tapi(shop_id = shop_id)
            # 删除淘宝已存在数据, 此处不清理本地数据
            del_id_list = delete_keywords(shop_id, camp_id, kw_del_list, tapi, opter = opter, opter_name = opter_name)
            # 获取需要进行更新的关键词
            if del_id_list:
                add_list = [ kw_add_dict[str(del_id)] for del_id in del_id_list if kw_add_dict.has_key(str(del_id))]
                # 提价需要进行更新的关键词
                if add_list:
                    result_mesg, added_keyword_list, _ = add_keywords(shop_id, adg_id, add_list, tapi, opter = opter, opter_name = opter_name)
                    if result_mesg:
                        log.info(result_mesg)
                    log.info('rebuil keywords : %s , local keywords : %s, shop_id=%s, camp_id=%s, adg_id=%s' % (len(added_keyword_list), len(kw_del_list), shop_id, camp_id, adg_id))
            # 同步下关键词
            return Keyword.struct_download_byadgs(shop_id, [adg_id], tapi)
    return True

def is_grammaticality(expression):
    try:
        if isinstance(expression, unicode):
            expression = str(expression)
        if isinstance(expression, str):
            eval(expression)
    except NameError:
        return True
    except Exception:
        return False
    return True

def check_syntax(candidate_words, label_define, select_conf_list, price_conf_list, delete_conf):
    def check_multi_conf(expression_list):
        mapping_dictionary = {
                                    'cond':'过滤条件',
                                    'sort':'排序',
                                    'price':'出价',
                                    'num':'数目'
                              }
        for index, obj in enumerate(expression_list):
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if not is_grammaticality(val):
                        return False, index + 1, mapping_dictionary.get(key, 'NAN')
            elif isinstance(obj, unicode):
                if not is_grammaticality(obj):
                    # TODO： yangrongkai 此处后期需要重构
                    return False, index + 1, '标签定义'
        return True, 0, ''

    # 检查语法
    single_expression_list = [(candidate_words, '候选词条件'), (delete_conf, '删除条件')]
    multi_expression_list = [(label_define, '标签定义'), (select_conf_list, '选词配置'), (price_conf_list, '初始出价配置')]
    for single_expression, label in single_expression_list:
        is_success = is_grammaticality(single_expression)
        if not is_success:
            return label, -1, -1
    for multi_expression, label in multi_expression_list:
        is_success, row_index , desc = check_multi_conf(multi_expression)
        if not is_success:
            return label, row_index, desc

    return '', 0, 0

def get_all_cache_data(psuser, index, is_jump):
    """获取缓存中存在的所有用户数据"""
    server = CrmCacheServer(user_id = psuser.id)
    cache_data = server.get_someone_last_data(index, is_jump)

    field_list = ['shop_id', 'camp_id', 'adg_id', 'kw_id']
    result_list = []
    iter_len = index + 1
    for data in cache_data:
        temp_dict = {}
        for i in xrange(iter_len):
            key = field_list[i]
            if data.has_key(key):
                temp_dict[key] = data[key]
            else :
                break
        if len(temp_dict) == iter_len:
            result_list.append(temp_dict)
    return result_list
