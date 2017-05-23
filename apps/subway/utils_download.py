# coding=UTF-8
import datetime

"""
下载的一些工具函数
"""
def trans_price(price_str):
    """
    trans_price('192.00')
    >>> 19200
    """
    return int(float(price_str) * 100)

# def merge_rpt_dict(base_dict, effect_dict):
#     """
#     merge_rpt_dict({datetime.datetime(2013,2,5):{'imp':25}},{datetime.datetime(2013,2,5):{'cost':26}})
#     >>> [{datetime.datetime(2013,2,5):{'imp':25,'cost':26}}]
#     """
#     result_list = []
#     for date, base in base_dict.items():
#         tmp_dict = base.copy()
#         tmp_dict.update(effect_dict.get(date, {'favshopcount':0, 'directpay':0, 'indirectpay':0, 'favitemcount':0, 'indirectpaycount':0, 'directpaycount':0}))
#         tmp_dict.update({'date':date})
#         result_list.append(tmp_dict.copy())
#         tmp_dict.clear()
#     result_list.sort(cmp = lambda x, y:cmp(x['date'], y['date']))
#     return result_list

def parse_rpt_schtype(obj):
    """解析淘宝返回的报表类型,这里统一保存为数字"""
    obj_attr = getattr(obj, 'search_type', 'SUMMARY')
    if obj_attr == 'SUMMARY':
        return 3
    elif obj_attr == 'SEARCH':
        return 0
    elif isinstance(obj_attr, int):
        return obj_attr
    else:
        return 4

def parse_rpt_source(obj):
    """解析淘宝返回的报表来源,这里统一保存为数字"""
    obj_attr = getattr(obj, 'source', 'SUMMARY') # TODO: wangqi 20140703 source目前分为5种：1--PC站内，2--PC站外，4--无线站内，5--无线站外，SUMMARY
    if obj_attr == 'SUMMARY':
        return 3
    elif isinstance(obj_attr, int):
        return obj_attr
    else:
        return 4

def trans_filed_value(obj, filed):
    value = getattr(obj, filed, 0) or 0 # 兼容返回字段值为 None
    return int(float(value))

def trans_rtrptobj_2dict(obj_type, obj):
    """将淘宝下载下来的实时数据转换成字典 """
    filed_dict = {'base': ('click', 'impressions', 'cost', 'aclick', 'avgpos'),
                  'effect': ('directtransaction', 'indirecttransaction', 'favshoptotal', 'favitemtotal', 'directtransactionshipping', 'indirecttransactionshipping')
                  }
    rpt_dict = {k: trans_filed_value(obj, k) for k in filed_dict[obj_type]}
    if obj_type == 'base':
        rpt_dict.update({'source':parse_rpt_source(obj), 'search_type':parse_rpt_schtype(obj)})
    result_dict = {datetime.datetime.strptime(obj.thedate, '%Y-%m-%d'): rpt_dict}
    return result_dict

def trans_tobj_2dict(top_obj, obj_dict, trans_type = 'init', extra_args = {}):
    """用于将淘宝返回的top_obj转化为数据库存储的字典"""
    result_dict = {}
    if trans_type == 'init': # 要全部获取，用于初始化
        for db_field, db_value in obj_dict.items():
            result_dict.update({db_field:len(db_value) > 2 and db_value[2](eval(db_value[0])) or eval(db_value[0]) })
    elif trans_type == 'inc': # 用于增量
        for db_field, db_value in obj_dict.items():
            if db_value[1] == 2:
                result_dict.update({db_field:len(db_value) > 2 and db_value[2](eval(db_value[0])) or eval(db_value[0])})
    return result_dict


# 下载报表的明细，source主要分三种：(站内1,站外2,汇总SUMMARY), search_type分三种(SEARCH,NOSEARCH,SUMMARY)
# REPORT_TYPE_DICT = { # 类型:((存储字段名,source,search_type),)
#     'account':(('rpt_list', 'SUMMARY', None),),
#     'campaign':(('rpt_list', 'SUMMARY', 'SUMMARY'),),
#     'adgroup':(('rpt_list', 'SUMMARY', 'SUMMARY'), ('nosch_rpt_list', 'SUMMARY', 'NOSEARCH')),
#     'creative':(('rpt_list', 'SUMMARY', 'SUMMARY'),),
#     'keyword':(('rpt_list', 'SUMMARY', 'SEARCH'),),
#     }


# REPORT_TYPE_DICT = { # 类型:((存储字段名,source,search_type),)
#     'account':(('rpt_list', 'SUMMARY', None),),
#     'campaign':(('rpt_list', 'SUMMARY', 'SUMMARY'),),
#     'adgroup':(('rpt_list', 'SUMMARY', 'SUMMARY'), ('nosch_rpt_list', 'SUMMARY', 'NOSEARCH')),
#     'creative':(('rpt_list', 'SUMMARY', 'SUMMARY'),),
#     'keyword':(('rpt_list', 'SUMMARY', 'SEARCH'), ('yd_insite_rpt_list', '4', 'SUMMARY'), ('yd_outsite_rpt_list', '5', 'SUMMARY'), ('pc_insite_rpt_list', '1', 'SUMMARY'), ('pc_outsite_rpt_list', '2', 'SUMMARY')),
#     }


