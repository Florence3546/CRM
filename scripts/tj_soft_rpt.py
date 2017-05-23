# coding=UTF-8
import datetime
import init_environ
from copy import deepcopy

from django.core.mail import send_mail

import settings
from apps.subway.models_account import account_coll, Account
from apps.subway.models_campaign import camp_coll, Campaign
from apps.mnt.models_mnt import mnt_camp_coll
from apps.mnt.models_monitor import rs_coll, ReportSnap
from apps.common.utils.utils_log import log

TODAY = None
TJ_DAY = None
RPT_KEY_LIST = ['impressions', 'click', 'cost', 'directpay', 'indirectpay', 'directpaycount', 'indirectpaycount', 'carttotal']
MNT_CAMP_DICT = {}
INIT_RPT_DAYS = ReportSnap.SUM_DAYS_CHOICES[-1]

def format_data(fen_zi, fen_mu):
    return fen_mu and round(fen_zi * 1.0 / fen_mu, 4) or 0

def update_global_var():
    global TODAY, TJ_DAY, MNT_CAMP_DICT
    TODAY = datetime.datetime.now()
    TJ_DAY = datetime.datetime(year = TODAY.year, month = TODAY.month, day = TODAY.day - 1) # 今天统计时，统计的是昨天的报表

    mnt_camps = mnt_camp_coll.find({}, {'_id': 1})
    MNT_CAMP_DICT = {camp['_id']: 1 for camp in mnt_camps}

def del_global_var(): # supervisionctl 中的定时任务不会释放内存，所以需要手动释放。
    global MNT_CAMP_DICT
    MNT_CAMP_DICT = {}

def is_mnt_camp(camp_id):
    return camp_id in MNT_CAMP_DICT and 'mnt' or 'unmnt'

def is_include_kcjl(title):
    return '开车精灵' in title and 'has_kcjl' or 'has_no_kcjl'

def init_result_dict(mnt_type_list):
    result_dict = {}
    sum_rpt_list = []
    init_rpt_dict = {k: 0 for k in RPT_KEY_LIST}
    end_time = TJ_DAY - datetime.timedelta(days = 2)
    conv_days = 3
    for days in reversed(ReportSnap.SUM_DAYS_CHOICES): # 天数由大到小，方便后面提高遍历速度
        start_time = end_time - datetime.timedelta(days = (days - 1))
        sum_rpt_list.append([days, start_time, end_time, deepcopy(init_rpt_dict), conv_days])
    sum_rpt_list.append([1, TJ_DAY, TJ_DAY, deepcopy(init_rpt_dict), 1])
    for mnt_type in mnt_type_list:
        result_dict.update({mnt_type: {'rpt': deepcopy(sum_rpt_list), 'count': 0}})
    return result_dict

def add_rpt(result_dict, rpt_list, mnt_type):
    if not rpt_list:
        return
    result_dict[mnt_type]['count'] += 1
    for rpt in rpt_list:
        for days, start_time, end_time, sum_rpt_dict, conv_days in result_dict[mnt_type]['rpt']:
            if rpt['date'] < start_time:
                break
            if rpt['date'] > end_time:
                continue
            for k in RPT_KEY_LIST:
                sum_rpt_dict[k] += rpt[k]
    return

def change_rpt_field(rpt_dict):
    rpt_dict.update({'pay': rpt_dict['directpay'] + rpt_dict['indirectpay'],
                     'paycount': rpt_dict['directpaycount'] + rpt_dict['indirectpaycount'],
                     'ctr': format_data(rpt_dict['click'], rpt_dict['impressions']),
                     'cpc': format_data(rpt_dict['cost'], rpt_dict['click']),
                     'roi': format_data(rpt_dict['directpay'] + rpt_dict['indirectpay'], rpt_dict['cost']),
                     })
    rpt_dict.pop('directpay')
    rpt_dict.pop('indirectpay')
    rpt_dict.pop('directpaycount')
    rpt_dict.pop('indirectpaycount')
    return

def get_insert_list(object_type, result_dict):
    insert_list = []
    for mnt_type, temp_dict in result_dict.items():
        base_dict = {'object_type': object_type, 'date': TJ_DAY, 'mnt_type': mnt_type, 'count': temp_dict['count'], 'create_time': TODAY}
        for days, _, _, sr_dict, conv_days in temp_dict['rpt']:
            change_rpt_field(sr_dict)
            sr_dict.update(base_dict)
            sr_dict.update({'sum_days': days, 'conv_days': conv_days, 'date': TJ_DAY - datetime.timedelta(days = conv_days - 1)})
            insert_list.append(sr_dict)
    return insert_list

def tj_shop_rpt():
    print '%s: start tj shop rpt' % datetime.datetime.now()
    result_dict = init_result_dict(mnt_type_list = ['all'])
    accs = account_coll.find({}, {'_id': 1})
    for acc in accs:
        shop_id = acc['_id']
        rpt_dict = Account.Report.get_snap_list({'shop_id': shop_id}, rpt_days = INIT_RPT_DAYS)
        rpt_list = rpt_dict.get(shop_id, [])
        add_rpt(result_dict, rpt_list, 'all')

    insert_list = get_insert_list('shop', result_dict)
    rs_coll.insert(insert_list)
    print '%s: end tj shop rpt' % datetime.datetime.now()
    return

def tj_camp_rpt():
    print '%s: start tj camp rpt' % datetime.datetime.now()
    result_dict = init_result_dict(mnt_type_list = ['mnt', 'unmnt', 'has_kcjl', 'has_no_kcjl'])
    camps = camp_coll.find({}, {'title': 1, 'shop_id': 1})
    for camp in camps:
        camp_id = camp['_id']
        shop_id = camp['shop_id']
        camp_title = camp['title']
        mnt_type = is_mnt_camp(camp_id)
        rpt_dict = Campaign.Report.get_snap_list({'shop_id': shop_id, 'campaign_id': camp_id}, rpt_days = INIT_RPT_DAYS)
        rpt_list = rpt_dict.get(camp_id, [])
        add_rpt(result_dict, rpt_list, mnt_type)
        if mnt_type == 'mnt':
            is_include = is_include_kcjl(camp_title)
            add_rpt(result_dict, rpt_list, is_include)

    insert_list = get_insert_list('camp', result_dict)
    rs_coll.insert(insert_list)
    print '%s: end tj camp rpt' % datetime.datetime.now()
    return

def send_email(e):
    subject = '【脚本错误】全网报表统计脚本'
    content = e
    cc_list = ['wuhuaqiao@paithink.com']
    send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, cc_list)

def tj_soft_rpt():
    update_global_var()
    print '%s: start, tj_day = %s' % (datetime.datetime.now(), TJ_DAY)
    fun_list = [tj_shop_rpt, tj_camp_rpt]
    err_list = []
    for fun in fun_list:
        try:
            fun()
        except Exception, e:
            error = 'fun=%s, e=%s' % (fun.__name__, e)
            err_list.append(error)
            log.error('fun=%s, e=%s' % (fun.__name__, e))
    if err_list:
        err_str = '</br>'.join(err_list)
        send_email(err_str)
    del_global_var()
    print '%s: end, tj_day = %s' % (datetime.datetime.now(), TJ_DAY)

if __name__ == '__main__':
    tj_soft_rpt()
