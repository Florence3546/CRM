# coding=UTF-8
from apps.subway.models_upload import UploadRecord
from apps.subway.models_keyword import Keyword
from apps.subway.models_campaign import Campaign
from apps.subway.models_adgroup import Adgroup
from apps.subway.models_creative import Creative, CustomCreative
from apps.subway.models_item import Item
from apilib import get_tapi

def update_campaign(shop_id, campaign_id, tapi = None, record_flag = True, opter = 1, opter_name = '', **para):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    result_list, msg_list, record_list = Campaign.update_campaign_inner(shop_id = int(shop_id), campaign_id = campaign_id, tapi = tapi, opter = opter, opter_name = opter_name, **para)
    if record_list and record_flag:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return result_list, msg_list

def update_adgroups(shop_id, adg_arg_dict, record_flag = True, tapi = None, opter = 1, opter_name = ''): # adg_dict形如{123456:{'online_status':'online'},231654:{'online_status':'offline'}}
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    updated_id_list, del_id_list, record_list = Adgroup.update_adgroups_inner(shop_id = int(shop_id), adg_arg_dict = adg_arg_dict, tapi = tapi, opter = opter, opter_name = opter_name)
    if record_list and record_flag:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return updated_id_list, del_id_list

def add_adgroups(shop_id, campaign_id, item_arg_list, tapi = None, opter = 1, opter_name = ''): # 这里的item_arg_list每个item是个字典，包含了标准的item键值，还有额外的adg_title这个键
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    added_id_list, error_msg_dict, record_list = Adgroup.add_adgroups_inner(shop_id = int(shop_id), campaign_id = campaign_id, item_arg_list = item_arg_list, tapi = tapi, opter = opter, opter_name = opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return added_id_list, error_msg_dict

def delete_adgroups(shop_id, adgroup_id_list, record_flag = True, tapi = None, opter = 1, opter_name = ''):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    deleted_id_list, cant_del_list, ztc_del_count, record_list, error_msg = Adgroup.delete_adgroups_inner(shop_id = int(shop_id), adgroup_id_list = adgroup_id_list, tapi = tapi, opter = opter, opter_name = opter_name)
    if record_list and record_flag:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return deleted_id_list, cant_del_list, ztc_del_count, error_msg

def update_keywords(shop_id, kw_arg_list, tapi = None, opter = 1, opter_name = ''): # kw_arg_list = [(campaign_id, adgroup_id, keyword_id, word, new_price, match_scope, old_price),]
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    updated_id_list, deleted_id_list, record_list = Keyword.update_keywords_inner(shop_id = int(shop_id), kw_arg_list = kw_arg_list, tapi = tapi, opter = opter, opter_name = opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return updated_id_list, deleted_id_list

def bulk_update_keywords(shop_id, upd_kw_list, tapi = None):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    return Keyword.bulk_update_keywords_inner(shop_id = int(shop_id), upd_kw_list = upd_kw_list, tapi = tapi)

# kw_arg_list格式为[[word, new_price, match_scope, opt_type, op_reason], ……]，如kw_arg_list = [["连衣裙", 50, 1, None, None], ["真丝雪纺", 5, 2, None, None]]
def add_keywords(shop_id, adgroup_id, kw_arg_list, tapi = None, opter = 1, opter_name = ''):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    result_mesg, added_keyword_list, repeat_word_list, record_list = Keyword.add_keywords_inner(shop_id = int(shop_id), adgroup_id = adgroup_id, kw_arg_list = kw_arg_list, tapi = tapi, opter = opter, opter_name = opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return result_mesg, added_keyword_list, repeat_word_list

def delete_keywords(shop_id, campaign_id, kw_arg_list, tapi = None, data_type = 402, opter = 1, opter_name = ''): # kw_arg_list = [[adgroup_id, keyword_id, word, word_type, word_from, op_reason]]
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    deleted_id_list, record_list = Keyword.delete_keywords_inner(shop_id = int(shop_id), campaign_id = campaign_id, kw_arg_list = kw_arg_list, tapi = tapi, data_type = data_type, opter = opter, opter_name = opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return deleted_id_list

def update_item_title(shop_id, item_id, title, shop_type, tapi = None):
    from apps.subway.models_item import Item
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    result = Item.update_item_title_inner(shop_id = int(shop_id), item_id = int(item_id), title = title, shop_type = shop_type, tapi = tapi)
    return result

def mnt_quick_oper_log(shop_id, campaign_id, adg_id_list, stgy_name, opter = 1, opter_name = ''):
    if adg_id_list: # 重点托管加大减小投入针对宝贝
        adg_list = Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id, adgroup_id__in = adg_id_list)
        record_list = []
        for adg in adg_list:
            item_name = adg.item.title
            detail_list = ['对托管的宝贝"%s"' % stgy_name]
            record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adg.adgroup_id, 'item_name': item_name, 'detail_list': detail_list, 'op_type':2, 'data_type':207, 'opter':opter, 'opter_name':opter_name})
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    else: # 长尾托管加大减小投入针对创意
        detail_list = ['对计划"%s"' % stgy_name]
        up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':109, 'opter':opter, 'opter_name':opter_name}
        up_obj = UploadRecord(**up_rec)
        UploadRecord.objects.insert([up_obj])

def set_camp_bword_log(shop_id, campaign_id, word_list, opter = 1, opter_name = ''):
    words = '、'.join([str(word) for word in word_list])
    detail_list = ['对计划设置屏蔽词:%s' % words]
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':111, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def change_mntcfg_type_log(shop_id, campaign_id, opt_desc, opter = 1, opter_name = ''):
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': [opt_desc], 'op_type':1, 'data_type':112, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def change_cmp_maxprice_log(shop_id, campaign_id, max_price, mobile_max_price, opter = 1, opter_name = ''):
    detail_list = ['设置PC端限价为:%.2f元，移动端限价为:%.2f元' % (max_price / 100.0, mobile_max_price / 100.0)]
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':110, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def udpate_cmp_budget_log(shop_id, campaign_id, opt_desc, opter = 1, opter_name = ''):
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': [opt_desc], 'op_type':1, 'data_type':103, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def modify_cmp_kw_price_log(shop_id, campaign_id, opt_desc, opter = 1, opter_name = ''):
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': [opt_desc], 'op_type':1, 'data_type':113, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def del_cmp_kw_log(shop_id, campaign_id, opt_desc, opter = 1, opter_name = ''):
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': [opt_desc], 'op_type':4, 'data_type':402, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def modify_cmp_adg_log(shop_id, campaign_id, adg_id_list, opt_desc = '', opter = 1, opter_name = ''):
    adg_list = Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id, adgroup_id__in = adg_id_list)
    detail_list = []
    for adg in adg_list:
        detail_list.append('%s,%s' % (adg.item.title, opt_desc))
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'item_name': '', 'detail_list': detail_list, 'op_type':2, 'data_type':206, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def set_cmp_mnt_status_log(shop_id, campaign_id, opt_desc, data_type, opter = 1, opter_name = ''):
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': [opt_desc], 'op_type':1, 'data_type':data_type, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def update_adg_mobdisct_log(shop_id, campaign_id, adg_id_list, discount, opter = 1, opter_name = ''):
    try:
        record_list = []
        adg_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list)
        if adg_list:
            for adg in adg_list:
                item_name = adg.item.title
                detail_list = ['移动端折扣设置为%s%%' % discount]
                record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adg.adgroup_id, 'item_name': item_name, 'detail_list': detail_list, 'op_type':2, 'data_type':205, 'opter':opter, 'opter_name':opter_name})
        if record_list:
            rcd_list = [UploadRecord(**record) for record in record_list]
            UploadRecord.objects.insert(rcd_list)
        return True
    except Exception, e:
        return False

def del_adg_mobdisct_log(shop_id, campaign_id, adgroup_id, discount, opter = 1, opter_name = ''):
    detail_list = ['使用计划折扣%s%%' % discount]
    adg = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adg.adgroup_id, 'item_name': adg.item.title, 'detail_list': detail_list, 'op_type':2, 'data_type':205, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def change_adg_maxprice_log(shop_id, campaign_id, adgroup_id, item_name, opt_desc, opter = 1, opter_name = ''):
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adgroup_id, 'item_name':item_name, 'detail_list': [opt_desc], 'op_type':2, 'data_type':208, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def change_adg_mnt_log(shop_id, campaign_id, adgroup_id, item_name, opt_desc, opter = 1, opter_name = ''):
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adgroup_id, 'item_name':item_name, 'detail_list': [opt_desc], 'op_type':2, 'data_type':206, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def update_creative(tapi, shop_id, adgroup_id, creative_id, title, img_url, opter = 1, opter_name = ''):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    result, msg, record_list = Creative.update_creative_inner(tapi = tapi, shop_id = int(shop_id), adgroup_id = adgroup_id, creative_id = creative_id, title = title, img_url = img_url, opter = opter, opter_name = opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return result, msg

def update_custom_creative(tapi, shop_id, campaign_id, adgroup_id, item_id, creative_id, title, file_item, opter = 1, opter_name = ''):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    result, msg, record_list = CustomCreative.update_creative(tapi = tapi, shop_id = int(shop_id), campaign_id = campaign_id, adgroup_id = adgroup_id, num_iid = item_id, creative_id = creative_id, title = title, file_item = file_item, opter = opter, opter_name = opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return result, msg

def add_custom_creative(tapi, shop_id, campaign_id, adgroup_id, num_iid, title, image, opter = 1, opter_name = ''):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    result, record_list = CustomCreative.add_creative(tapi, shop_id, campaign_id, adgroup_id, num_iid, title, image, opter, opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return result

def add_creative(tapi, shop_id, campaign_id, crt_arg_list = [], opter = 1, opter_name = ''):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    result, record_list = Creative.add_creative_inner(tapi = tapi, shop_id = int(shop_id), campaign_id = campaign_id, crt_arg_list = crt_arg_list, opter = opter, opter_name = opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return result

def delete_creative(tapi, shop_id, creative_id, opter = 1, opter_name = ''):
    if not tapi:
        tapi = get_tapi(shop_id = shop_id)
    result, record_list = Creative.delete_creative_inner(tapi = tapi, shop_id = int(shop_id), creative_id = creative_id, opter = opter, opter_name = opter_name)
    if record_list:
        rcd_list = [UploadRecord(**record) for record in record_list]
        UploadRecord.objects.insert(rcd_list)
    return result

def delete_custom_creative(shop_id, adgroup_id, creative_id, opter = 1, opter_name = ''):
    try:
        creative = CustomCreative.objects.get(shop_id = shop_id, id = creative_id)
        opt_desc = '删除创意:%s' % creative.title
        creative.delete();
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        up_rec = {'shop_id':shop_id, 'campaign_id':adgroup.campaign_id, 'adgroup_id':adgroup.adgroup_id, 'item_name':adgroup.item.title, 'detail_list': [opt_desc], 'op_type':3, 'data_type':302, 'opter':opter, 'opter_name':opter_name}
        up_obj = UploadRecord(**up_rec)
        UploadRecord.objects.insert([up_obj])
        return False, ''
    except Exception, e:
        return True, '删除创意失败'

def set_prod_word_log(shop_id, campaign_id , adgroup_id, title, word_list, opter = 1, opter_name = ''):
    words = '、'.join([str(word[0]) for word in word_list])
    detail_list = ['配置产品词:%s' % words]
    up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'item_name':title, 'detail_list': detail_list, 'op_type':2, 'data_type':209, 'opter':opter, 'opter_name':opter_name}
    up_obj = UploadRecord(**up_rec)
    UploadRecord.objects.insert([up_obj])

def set_adg_bword_log(shop_id, campaign_id, adgroup_id, item_id, word_list, opter = 1, opter_name = ''):
    try:
        item = Item.objects.get(shop_id = shop_id, item_id = item_id)
        up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adgroup_id, 'item_name':item.title, 'detail_list':word_list, 'op_type':2, 'data_type':211, 'opter':opter, 'opter_name':opter_name}
        up_obj = UploadRecord(**up_rec)
        UploadRecord.objects.insert([up_obj])
        return True
    except Exception, e:
        return False

def change_rt_engine_log(shop_id, campaign_id, opt_desc, opter = 1, opter_name = ''):
    try:
        up_rec = {'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': [opt_desc], 'op_type':1, 'data_type':114, 'opter':opter, 'opter_name':opter_name}
        up_obj = UploadRecord(**up_rec)
        UploadRecord.objects.insert([up_obj])
        return True
    except Exception, e:
        return False

def onekey_optimize_log(shop_id, adgroup_id, opt_desc, opter = 5, opter_name = ''):
    try:
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        title = adgroup.item.title
        up_rec = {'shop_id':adgroup.shop_id, 'campaign_id':adgroup.campaign_id, 'adgroup_id':adgroup.adgroup_id, 'item_name': title, 'detail_list': [opt_desc], 'op_type':2, 'data_type':212, 'opter':opter, 'opter_name':opter_name}
        up_obj = UploadRecord(**up_rec)
        UploadRecord.objects.insert([up_obj])
        return True
    except Exception, e:
        return False

def set_adg_follow_log(shop_id, campaign_id, adg_id, is_follow = 0, opter = 1, opter_name = ''):
    try:
        record_list = []
        adg_list = Adgroup.objects.filter(shop_id = shop_id, adgroup_id = adg_id)
        if adg_list:
            for adg in adg_list:
                item_name = adg.item.title
                detail_list = ['添加关注'] if is_follow else ['取消关注']
                data_type = 115 if is_follow else 116
                record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adg.adgroup_id, 'item_name': item_name, 'detail_list': detail_list, 'op_type':2, 'data_type':data_type, 'opter':opter, 'opter_name':opter_name})
        if record_list:
            rcd_list = [UploadRecord(**record) for record in record_list]
            UploadRecord.objects.insert(rcd_list)
        return True
    except Exception, e:
        return False

