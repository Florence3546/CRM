# coding=UTF-8
import datetime

from apilib import get_tapi, TopError
from apps.common.utils.utils_log import log
from apps.subway.models_adgroup import adg_coll
from apps.subway.models_account import account_coll
from apps.subway.models_campaign import camp_coll
# from apps.ncrm.models import Customer

def batch_refresh_shopcatid(shop_id_list, is_force = False):
    # 批量刷新店铺的类目ID
    def get_shop_cat(category_ids_list):
        cat_id = 0
        if category_ids_list:
            tmp_dict = {}
            for category_ids in category_ids_list:
                tmp_cat_list = category_ids.split()[:1]
                for tmp_cat in tmp_cat_list:
                    if not tmp_dict.has_key(tmp_cat):
                        tmp_dict[tmp_cat] = 1
                    else:
                        tmp_dict[tmp_cat] += 1
            # 将字典排序成按出现次数最多的元组排序
            sorted_list = sorted(tmp_dict.iteritems(), key = lambda x:x[1], reverse = True)
            cat_id = sorted_list[0][0] # 只取第一个
        return cat_id

    temp_shop_dict = {}
    temp_cat_dict = {}

    if not is_force:
        shop_id_list = [ int(acc['_id'])  for acc in account_coll.find({'_id':{'$in':shop_id_list}, '$or':[{'cat_id':None}, {'cat_id':0}, {'cat_id':''}]}, {'_id':1}) ]

    if not shop_id_list:
        return {}, 0

    adg_cursor = adg_coll.find({'shop_id':{'$in':shop_id_list}}, {'category_ids':1, 'shop_id':1})
    for adg in adg_cursor:
        if adg:
            key = str(adg['shop_id'])
            if temp_shop_dict.has_key(key):
                temp_shop_dict[key].append(adg['category_ids'])
            else:
                temp_shop_dict[key] = [adg['category_ids']]

    for shop_id, category_ids_list in temp_shop_dict.items():
        cat_id = get_shop_cat(category_ids_list)
        key = str(cat_id)
        if temp_cat_dict.has_key(key):
            temp_cat_dict[key].append(int(shop_id))
        else:
            temp_cat_dict[key] = [int(shop_id)]

    count = 0
    result = {}
    for cat_id, shop_id_list in temp_cat_dict.items():
        result_dict = account_coll.update({'_id':{'$in':shop_id_list}}, {'$set':{'cat_id':int(cat_id)}}, upsert = False, multi = True)
        # Customer.objects.filter(shop_id__in = shop_id_list).update(cat_id = int(cat_id))
#         log.info('have already refreshed, cat_id = %s , shop_id_list = %s, result_dict=%s' % (cat_id, shop_id_list, json.dumps(result_dict)))
        if result_dict and result_dict.has_key('n'):
            count += result_dict['n']
            result_dict['cat_id'] = cat_id
            result = result_dict
    return result, count

# 获得shop所在的类目，粗略实现为点击最多的推广组所在类目
# 修改了这里了实现，通过推广的所有宝贝来获取到主推的类目
def refresh_shop_cat(shop_id, is_force = False):
    result, count = batch_refresh_shopcatid([shop_id], is_force = is_force)
    if count and result.has_key('cat_id'):
        return result['cat_id']
    return 0

def batch_refresh_budgetStatus(shop_id_list):
    """通过店铺来刷新日限额是否超出状态"""
    yestoday_time = datetime.datetime.now() - datetime.timedelta(days = 1)
    yestoday = datetime.datetime(yestoday_time.year, yestoday_time.month, yestoday_time.day)
    camp_cursor = camp_coll.find({ 'shop_id' : {'$in':shop_id_list} , 'rpt_list.date' : yestoday }, { '_id' : 1 , 'rpt_list.$' : 1 , 'budget' : 1 , 'budget_status' : 1 })

    # 初始化
    update_dict = { '0' : [] , '1' : [] }
    refresh_count = 0

    for camp in camp_cursor:
        if camp and camp.has_key('rpt_list') and camp[ 'rpt_list' ]  and camp[ 'budget' ]:
            camp_id = int(camp[ '_id' ])
            rpt = camp[ 'rpt_list' ][  -1 ]
            budget = camp[ 'budget' ]
            budget_statuts = camp.get('budget_status', None)

            store_mark = '0'
            if rpt['cost'] >= budget :
                store_mark = '1'

            if budget_statuts != store_mark:
                update_dict[ store_mark ].append(camp_id)

            refresh_count += 1

    # 更新数据
    for budget_status , camp_id_list in update_dict.items():
        if camp_id_list and budget_status:
            camp_coll.update({'_id' : { '$in' : camp_id_list } } , { '$set' : { 'budget_status' : budget_status } } , multi = True)

    if refresh_count:
        log.info('Updated  budget_status of campaign completed. ')
        return True
    else:
        log.info('Campaign reports is no download or no data. ')
        return False

def reflash_budget_status(shop_id):
    """刷新店铺的日限额是否超出状态"""
    return batch_refresh_budgetStatus(shop_id_list = [shop_id])

def reset_crm_opareter_status(shop_id):
    """重置CRM操作状态"""
    try:
        account_coll.update({'_id':shop_id, 'opar_status':{'$ne':0}}, {'$set':{'opar_status':0}}, multi = True)
        camp_coll.update({'shop_id':shop_id, 'opar_status':{'$ne':0}}, {'$set':{'opar_status':0}}, multi = True)
        adg_coll.update({'shop_id':shop_id, 'opar_status':{'$ne':0}}, {'$set':{'opar_status':0}}, multi = True)
    except Exception, e:
        log.error('reset crm opareter status error, error=%s' % e)
        return False
    return True

# 当前关键词的排名
class KeywordCurrentPos():
    # 查询Item关键词所在的排名位置。找不到自己，返回0；出现api异常，返回0
    @staticmethod
    def get_item_kw_current_order(user, item_id, word, ip):
        result_order = (word, 0, '', 0, 0, '')
        tapi = get_tapi(user)
        try:
            tobj = tapi.simba_tools_items_top_get(nick = user.nick, keyword = word, ip = ip) # 取得一个关键词的推广组排名列表
        except TopError, e:
            log.error("tapi.simba_tools_items_top_get TopError, item_id=%s, word=%s, e=%s" % (item_id, word, e))
            return (word, 0, '', 0, 0, '') # 在binder.py中，已重试多次，如果出来还失败，则直接返回错误

        # 匹配宝贝排名
        if tobj.rankeditems:
            item_list_top = tobj.rankeditems.ranked_item
            for item in item_list_top:
                if str(item_id) in item.link_url:
                    result_order = (word, item.order, item.link_url, item.title)
                    break
        # 返回结果
        return result_order

    # 批量查询单个宝贝关键词的当前排名,结果缓存在关键词的current_order属性中，并未持久化
    @staticmethod
    def get_item_kws_current_order_list(user, item_id, kw_list, ip):
        for kw in kw_list:
            current_order = KeywordCurrentPos.get_item_kw_current_order(user, item_id, kw.word, ip)
            kw.current_order = current_order[1]
