# coding=UTF-8
import datetime
import init_environ

from apps.router.models import ArticleUserSubscribe
from apps.common.biz_utils.utils_permission import ORDER_VERSION_DICT
from apps.ncrm.models import Customer
from apps.subway.models_report import AccountRpt

COST_TYPE_LIST = [u'无消耗', u'日均消耗0-50', u'日均消耗50-100', u'日均消耗100以上']
RPT_DAYS = 3

def get_current_nick():
    today = datetime.datetime.now()
    item_code_list = ORDER_VERSION_DICT.keys()
    aus = ArticleUserSubscribe.objects.filter(item_code__in = item_code_list, deadline__gt = today)
    for au in aus:
        yield au.nick

def get_nick_dict():
    custs = Customer.objects.all().only('nick', 'shop_id')
    nick_dict = {obj.nick: obj.shop_id for obj in custs}
    return nick_dict

def get_cost_type(cost):
    cost = cost / RPT_DAYS
    if cost == 0:
        return COST_TYPE_LIST[0]
    if cost <= RPT_DAYS * 50 * 100: # 数据库中单位为分
        return COST_TYPE_LIST[1]
    if cost <= RPT_DAYS * 100 * 100:
        return COST_TYPE_LIST[2]
    return COST_TYPE_LIST[3]

def main():
    print '%s: start' % (datetime.datetime.now())
    cost_type_dict = {i: 0 for i in COST_TYPE_LIST}
    nick_yield = get_current_nick()
    nick_dict = get_nick_dict()
    for nick in nick_yield:
        shop_id = nick_dict.get(nick, 0)
        if not shop_id:
            continue
        sum_rpt = AccountRpt.aggregate_rpt(query_dict = {'shop_id': shop_id}, group_keys = AccountRpt.IDENTITY, rpt_days = RPT_DAYS)
        if not sum_rpt:
            sum_rpt = [{'cost': 0}]
        cost_type = get_cost_type(sum_rpt[0]['cost'])
        cost_type_dict[cost_type] += 1
    for cost_type, count in cost_type_dict.items():
        print cost_type, count
    print '%s: end' % (datetime.datetime.now())

if __name__ == '__main__':
    main()
