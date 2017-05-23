# coding=UTF-8

from apps.common.biz_utils.utils_dictwrapper import DictWrapper, KeywordGlobal
from apps.kwlib.api import get_gdata_word, get_keyword_subdata
from apps.common.utils.utils_log import log
from apps.common.utils.utils_number import round_digit

def g_dict_2obj(result_dict, result, kw_list):
    if result:
        for key in result:
            tmp = result[key]
            result_dict[key] = KeywordGlobal(g_pv = tmp['pv'], g_click = tmp['click'], g_competition = tmp['cmpt'], g_cpc = tmp['cpc'], g_coverage = tmp['coverage'], g_roi = tmp['roi'], g_paycount = tmp['transactionshippingtotal'])
    else:
        for kw in kw_list:
            result_dict[kw] = KeywordGlobal()
    return result_dict

def get_gdata_by_redis(kw_list):
    result = {}
    try:
        result = get_gdata_word(word_list = kw_list).result.to_dict()
    except Exception, e:
        log.error('get gdata from redis error and the error is =%s' % e)
        pass
    return result

def get_kw_g_data(kw_list): # TODO liushengchuan 下个版本做调整的时候统一使用  pv,click...或者统一使用  g_pv,g_click.... 2015.06.08
    """
    在 python 2.X版本中
    该方法返回值的 key 是 str 类型，而非unicode
    请注意转换
    """
    result_dict = {}
    if kw_list:
        result_dict = g_dict_2obj(result_dict, get_gdata_by_redis(kw_list), kw_list)

    return result_dict

def get_kw_g_data2(word_list, sub_type):
    '''
    @param
    sub_type : 0 for moblie, 1 for pc, -1 for all
    '''
    result_dict = {}
    if word_list:
        result = get_keyword_subdata(word_list = word_list, sub_type = sub_type)
        for key, data in result.result.to_dict().items():
            # result_dict[key] = KeywordGlobal(g_pv = data['pv'],
            #                                  g_click = data['click'],
            #                                  g_competition = data['competition'],
            #                                  g_cpc = int(data['cpc']),
            #                                  g_coverage = round_digit(data['coverage'], 4),
            #                                  g_roi = round_digit(data['roi'], 2),
            #                                  g_paycount = data['transactionshippingtotal'])
            # ctr = data['pv'] and data['click'] * 1.0 / data['pv']
            # 因为数据库中有脏数据，这里重新计算。等待一周后脏数据清理后，再恢复使用之前的。
            cpc = data['click'] and data['cost'] * 1.0 / data['click']
            roi = data['cost'] and (data['directtransaction'] + data['indirecttransaction']) * 1.0 / data['cost']
            coverage = data['click'] and data['transactionshippingtotal'] * 1.0 / data['click']
            result_dict[key] = KeywordGlobal(g_pv = data['pv'],
                                             g_click = data['click'],
                                             g_competition = data['competition'],
                                             g_cpc = int(cpc),
                                             g_coverage = round_digit(coverage, 4),
                                             g_roi = round_digit(roi, 2),
                                             g_paycount = data['transactionshippingtotal'])
    return result_dict

def get_kw_gdata_4select_word(kw_list):
    # 主要用于选词，只是改了改了key的名称。
    kw_dict = get_gdata_by_redis(kw_list)
    result_dict = {}
    for key, kw_data in kw_dict.iteritems():
        if kw_data['pv']:
            result_dict[key.decode('utf8')] = DictWrapper({'pv': kw_data['pv'],
                                            'click': kw_data['click'],
                                            'competition': kw_data['cmpt'],
                                            'avg_price': kw_data['cpc'],
                                            'ctr': round(kw_data['ctr'], 2),
                                            'roi':kw_data['roi'],
                                            'coverage':kw_data['coverage'],
                                            'favtotal':kw_data['favtotal'],
                                            })
    return result_dict
