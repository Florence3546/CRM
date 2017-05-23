# coding=UTF-8
'''
集合所有使用程序比较排序的排序函数
Created on 2012-04-05
@author: zhangyu
'''

def sort_by_impressions(x, y):
    '''根据rpt中的impressions排序'''
    if x.rpt.impressions > y.rpt.impressions:
        return -1
    elif x.rpt.impressions < y.rpt.impressions:
        return 1
    else:
        return 0

def sort_by_click(x, y):
    '''根据rpt中的click排序'''
    if x.rpt.click > y.rpt.click:
        return -1
    elif x.rpt.click < y.rpt.click:
        return 1
    else:
        return 0

def sort_by_click_impressions(x, y):
    '''根据rpt中的click、impressions排序'''
    if x.rpt.click > y.rpt.click:
        return -1
    elif x.rpt.click < y.rpt.click:
        return 1
    else:
        if x.rpt.impressions > y.rpt.impressions:
            return -1
        elif x.rpt.impressions < y.rpt.impressions:
            return 1
        else:
            return 0

def sort_by_order_time(x, y):
    '''按照用户的订购时间排序'''
    if x.order_info and y.order_info:
        if x.order_info[0].order_cycle_start > y.order_info[0].order_cycle_start:
            return -1
        elif x.order_info[0].order_cycle_start < y.order_info[0].order_cycle_start:
            return 1
        else:
            return 0
    else:
        return 0

def sort_by_adgroup_status(x, y):
    '''长尾托管选择宝贝页面排序，将是推广中的广告组优先显示'''
    if int(x.is_adgroup) > int(y.is_adgroup):
        return -1
    elif int(x.is_adgroup) < int(y.is_adgroup):
        return 1
    else:
        return 0

def sort_by_ztc_kw(x, y):
    '''按item里直通车关键词uv排序，并且直通车的要排在前面'''
    if x.is_ztc and not y.is_ztc:
        return -1
    elif not x.is_ztc and y.is_ztc:
        return 1
    elif x.is_ztc and y.is_ztc: # 直通车推广宝贝按直通车关键词降序排列
        if x.ztc_kw and not y.ztc_kw:
            return -1
        elif not x.ztc_kw and y.ztc_kw:
            return 1
        elif x.ztc_kw and y.ztc_kw:
            if x.ztc_kw[1] > y.ztc_kw[1]:
                return -1
            elif x.ztc_kw[1] < y.ztc_kw[1]:
                return 1
            elif x.id == 0:
                return -1
            else:
                return 0
        else:
            return 0
    else: # 非推广宝贝按自然关键词流量降序排列
        if x.zr_kw and not y.zr_kw:
            return -1
        elif not x.zr_kw and y.zr_kw:
            return 1
        elif x.zr_kw and y.zr_kw:
            if x.zr_kw[1] > y.zr_kw[1]:
                return -1
            elif x.zr_kw[1] < y.zr_kw[1]:
                return 1
            elif x.id == 0:
                return -1
            else:
                return 0
        else:
            return 0

def sort_by_ztc_kw2(x, y):
    '''按直通车关键词uv排序'''
    if sum(x[1][1]) > sum(y[1][1]):
        return -1
    elif sum(x[1][1]) < sum(y[1][1]):
        return 1
    else:
        return 0

def sort_by_cost(x, y):
    if (x.rpt.cost * x.rpt.click) > (y.rpt.cost * y.rpt.click):
        return -1
    elif (x.rpt.cost * x.rpt.click) < (y.rpt.cost * y.rpt.click):
        return 1
    else:
        return 0

def sort_by_pay(x, y):
    if (x.rpt.directpay + x.rpt.indirectpay) > (y.rpt.directpay + y.rpt.indirectpay):
        return -1
    elif (x.rpt.directpay + x.rpt.indirectpay) < (y.rpt.directpay + y.rpt.indirectpay):
        return 1
    else:
        return 0

def sort_by_max_price(x, y):
    if x.rpt.max_price > y.rpt.max_price:
        return -1
    elif x.rpt.max_price < y.rpt.max_price:
        return 1
    else:
        return 0

def sort_by_pay_count(x, y):
    if (x.rpt.directpaycount + x.rpt.indirectpaycount) > (y.rpt.directpaycount + y.rpt.indirectpaycount):
        return -1
    elif (x.rpt.directpaycount + x.rpt.indirectpaycount) < (y.rpt.directpaycount + y.rpt.indirectpaycount):
        return 1
    else:
        return 0

def sort_list_bystring(list_2sort, ref_str):
    """
    根据一个字符串ref_str，对组成他的词根列表list_2sort，按照词根在ref_str中出现的次序进行排序
    """
    str_clone = ref_str.upper()
    list_sorted = []
    list_2sort.sort(lambda x, y:cmp(len(y), len(x)))
    for word in list_2sort:
        word_clone = word.upper()
        word_index = str_clone.find(word_clone)
        str_clone = str_clone.replace(word_clone, '?' * len(word_clone.decode('utf8')), 1)
        if word_index != -1:
            list_sorted.append((word, word_index))
    list_sorted.sort(lambda x, y:cmp(x[1], y[1]))
    list_sorted = [word[0] for word in list_sorted]
    return list_sorted
