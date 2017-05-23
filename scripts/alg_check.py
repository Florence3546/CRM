# coding=UTF-8


import init_environ
from datetime import datetime, timedelta
from apps.alg.models import optrec_coll
from apps.subway.models_campaign import camp_coll, Campaign
from apps.subway.models_report import Report
from apps.subway.models_adgroup import adg_coll, Adgroup
import smtplib
from email.mime.text import MIMEText
from apps.common.utils.utils_misc import trans_batch_dict_2document


MAIL_TO_LIST = ['zhengjiankang@paithink.com']
CONFIG_SMTP_PAITHINK = {'ip':'smtp.exmail.qq.com',
                        'port':25,
                        'user_id':'pskj@paithink.com',
                        'password':'ps123456',
                        'sender':'testcase<pskj@paithink.com>',
                        }
def send_email(sub, content):
    config = CONFIG_SMTP_PAITHINK

    msg = MIMEText(content, _subtype = 'html', _charset = 'utf-8')
    msg['Subject'] = sub
    msg['From'] = config.get('sender')
    msg['to'] = ';'.join(MAIL_TO_LIST)

    try:
        smtp = smtplib.SMTP()
        smtp.connect(config.get('ip'), config.get('port'))
        smtp.login(config.get('user_id'), config.get('password'))
        smtp.sendmail(config.get('sender'), MAIL_TO_LIST, msg.as_string())
    except Exception as e:
        print (e)



def get_campaign_list(strategy_name, date):
    time1 = datetime(date.year, date.month, date.day, 0, 0, 0)
    time2 = datetime(date.year, date.month, date.day, 23, 59, 59)
    optrec_cur = optrec_coll.find({'strategy':strategy_name,
                                   'create_time':{'$gte':time1},
                                   'create_time':{'$lte':time2},
                                   })
    camp_id_set = set()
    for optrec in optrec_cur:
        camp_id_set.add(optrec['campaign_id'])
    camp_id_list = list(camp_id_set)
    camp_list = camp_coll.find({'_id':{'$in':camp_id_list}})
    temp_list = []
    for camp in camp_list:
        temp_list.append(camp)
        if len(temp_list) >= 2000:
            return temp_list # trans_batch_dict_2document(src_dict_list = temp_list, class_object = Campaign) or []
    return temp_list # trans_batch_dict_2document(src_dict_list = temp_list, class_object = Campaign) or []

def get_adgroup_list(strategy_name, date):
    time1 = datetime(date.year, date.month, date.day, 0, 0, 0)
    time2 = datetime(date.year, date.month, date.day, 23, 59, 59)
    optrec_cur = optrec_coll.find({'strategy':strategy_name,
                                   'create_time':{'$gte':time1},
                                   'create_time':{'$lte':time2},
                                   })
    adgroup_id_list = [optrec['adgroup_id'] for optrec in optrec_cur]
    adgroup_list = adg_coll.find({'_id':{'$in':adgroup_id_list}})
    temp_list = []
    for adgroup in adgroup_list:
        temp_list.append(adgroup)
        if len(temp_list) >= 4000:
            return temp_list # trans_batch_dict_2document(src_dict_list = temp_list, class_object = Adgroup) or []
    return temp_list # trans_batch_dict_2document(src_dict_list = temp_list, class_object = Adgroup) or []

def get_sum_rpt(date):
    time1 = datetime(date.year, date.month, date.day, 0, 0, 0)
    time2 = datetime(date.year, date.month, date.day, 23, 59, 59)
    optrec_cur = optrec_coll.find({'create_time':{'$gte':time1},
                                   'create_time':{'$lte':time2},
                                   })
    return


def get_accumulated_rpt(obj_list, date1, date2, date3):
    total_rpt_date1 = Report(date = date1)
    total_rpt_date2 = Report(date = date2)
    total_rpt_date3 = Report(date = date3)

    attr_list = ['impressions', 'click', 'cost', 'aclick',
                 'directpay', 'indirectpay', 'directpaycount', 'indirectpaycount', 'favitemcount', 'favshopcount']
    for camp in obj_list:
        rpt_dict = {rpt['date'].date():rpt for rpt in camp['rpt_list']}
        rpt1 = rpt_dict.get(date1.date(), {})
        rpt2 = rpt_dict.get(date2.date(), {})
        rpt3 = rpt_dict.get(date3.date(), {})
        if not rpt1 or not rpt2 or not rpt3:
            continue
        for attrname in attr_list:
            v1 = getattr(total_rpt_date1, attrname) + rpt1.get(attrname, 0) # getattr(rpt1, attrname)
            setattr(total_rpt_date1, attrname, v1)
            v2 = getattr(total_rpt_date2, attrname) + rpt2.get(attrname, 0) # getattr(rpt2, attrname)
            setattr(total_rpt_date2, attrname, v2)
            v3 = getattr(total_rpt_date3, attrname) + rpt3.get(attrname, 0) # getattr(rpt3, attrname)
            setattr(total_rpt_date3, attrname, v3)

    return total_rpt_date1, total_rpt_date2, total_rpt_date3

def alg_check(date):
    print 'alg check start...'
    date1 = date - timedelta(days = 1)
    date2 = date
    date3 = date + timedelta(days = 1)
    html = '<div>优化日期:%s</div>' % date2.strftime('%m-%d')

    # strategy_name = 'ReduceCost'
    camp_list = get_campaign_list(strategy_name = 'ReduceCost', date = date)
    rpt1, rpt2, rpt3 = get_accumulated_rpt(obj_list = camp_list, date1 = date1, date2 = date2, date3 = date3)
    check_attr_list = ['cost', 'cpc', 'click', 'paycount', 'roi']
    html += '<div>策略: 降低花费</div>'
    html += '<div>样本：%s个计划</div>' % len(camp_list)
    html += '<div>期望：PPC下降</div>'
    html += '<div>优化前后一天数据对比：</div>'
    html += '<table><tr><th>---</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (date1.strftime('%m-%d'), date2.strftime('%m-%d'), date3.strftime('%m-%d'))
    for attrname in check_attr_list:
        html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (attrname, getattr(rpt1, attrname), getattr(rpt2, attrname), getattr(rpt3, attrname))
    html += '</table>'
    html += '<b>'
    camp_list = []
    print 'check strategy <ReduceCost> finished.'

    # strategy_name = 'IncreaseClickSepcial'
    camp_list = get_campaign_list(strategy_name = 'IncreaseClickSepcial', date = date)
    rpt1, rpt2, rpt3 = get_accumulated_rpt(obj_list = camp_list, date1 = date1, date2 = date2, date3 = date3)
    check_attr_list = ['cost', 'click', 'cpc', 'paycount', 'roi']
    html += '<div>策略: 增加流量(计划流量很低)</div>'
    html += '<div>样本：%s个计划</div>' % len(camp_list)
    html += '<div>期望：点击量上升，花费上升</div>'
    html += '<div>优化前后一天数据对比：</div>'
    html += '<table><tr><th>---</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (date1.strftime('%m-%d'), date2.strftime('%m-%d'), date3.strftime('%m-%d'))
    for attrname in check_attr_list:
        html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (attrname, getattr(rpt1, attrname), getattr(rpt2, attrname), getattr(rpt3, attrname))
    html += '</table>'
    html += '<b>'
    camp_list = []
    print 'check strategy <IncreaseClickSepcial> finished.'

    # strategy_name = 'IncreaseClick'
    camp_list = get_campaign_list(strategy_name = 'IncreaseClick', date = date)
    rpt1, rpt2, rpt3 = get_accumulated_rpt(obj_list = camp_list, date1 = date1, date2 = date2, date3 = date3)
    check_attr_list = ['cost', 'click', 'cpc', 'paycount', 'roi']
    html += '<div>策略: 增加流量(计划流量较低)</div>'
    html += '<div>样本：%s个计划</div>' % len(camp_list)
    html += '<div>期望：点击量上升，花费上升</div>'
    html += '<div>优化前后一天数据对比：</div>'
    html += '<table><tr><th>---</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (date1.strftime('%m-%d'), date2.strftime('%m-%d'), date3.strftime('%m-%d'))
    for attrname in check_attr_list:
        html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (attrname, getattr(rpt1, attrname), getattr(rpt2, attrname), getattr(rpt3, attrname))
    html += '</table>'
    html += '<b>'
    camp_list = []
    print 'check strategy <IncreaseClick> finished.'

    # stragegy_name = 'IncreaseCVR'
    adgroup_list = get_adgroup_list(strategy_name = 'IncreaseCVR', date = date)
    rpt1, rpt2, rpt3 = get_accumulated_rpt(obj_list = adgroup_list, date1 = date1, date2 = date2, date3 = date3)
    check_attr_list = ['cost', 'click', 'paycount', 'conv', 'cpc', 'roi']
    html += '<div>策略: 增加转化率</div>'
    html += '<div>样本：%s个推广组</div>' % len(adgroup_list)
    html += '<div>期望：转化率提升，点击量不下降或者小幅下降</div>'
    html += '<div>优化前后一天数据对比：</div>'
    html += '<table><tr><th>---</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (date1.strftime('%m-%d'), date2.strftime('%m-%d'), date3.strftime('%m-%d'))
    for attrname in check_attr_list:
        html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (attrname, getattr(rpt1, attrname), getattr(rpt2, attrname), getattr(rpt3, attrname))
    html += '</table>'
    html += '<b>'
    camp_list = []
    print 'check strategy <IncreaseCVR> finished.'

    # strategy_name = 'ReducePPC'
    adgroup_list = get_adgroup_list(strategy_name = 'ReducePPC', date = date)
    rpt1, rpt2, rpt3 = get_accumulated_rpt(obj_list = adgroup_list, date1 = date1, date2 = date2, date3 = date3)
    check_attr_list = ['cost', 'cpc', 'click', 'paycount', 'roi']
    html += '<div>策略: 降PPC</div>'
    html += '<div>样本：%s个推广组</div>' % len(adgroup_list)
    html += '<div>期望：PPC下降，点击量不下降或者小幅下降</div>'
    html += '<div>优化前后一天数据对比：</div>'
    html += '<table><tr><th>---</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (date1.strftime('%m-%d'), date2.strftime('%m-%d'), date3.strftime('%m-%d'))
    for attrname in check_attr_list:
        html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (attrname, getattr(rpt1, attrname), getattr(rpt2, attrname), getattr(rpt3, attrname))
    html += '</table>'
    html += '<b>'
    camp_list = []
    print 'check strategy <ReducePPC> finished.'

    # strategy_name = 'IncreaseCTR'
    adgroup_list = get_adgroup_list(strategy_name = 'IncreaseCTR', date = date)
    rpt1, rpt2, rpt3 = get_accumulated_rpt(obj_list = adgroup_list, date1 = date1, date2 = date2, date3 = date3)
    check_attr_list = ['cost', 'click', 'ctr', 'cpc', 'paycount', 'roi']
    html += '<div>策略: 加点击率</div>'
    html += '<div>样本：%s个推广组</div>' % len(adgroup_list)
    html += '<div>期望：点击率上升，点击量不下降或者小幅下降</div>'
    html += '<div>优化前后一天数据对比：</div>'
    html += '<table><tr><th>---</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (date1.strftime('%m-%d'), date2.strftime('%m-%d'), date3.strftime('%m-%d'))
    for attrname in check_attr_list:
        html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (attrname, getattr(rpt1, attrname), getattr(rpt2, attrname), getattr(rpt3, attrname))
    html += '</table>'
    html += '<b>'
    camp_list = []
    print 'check strategy <IncreaseCTR> finished.'

    # strategy_name = 'Default'
    adgroup_list = get_adgroup_list(strategy_name = 'Default', date = date)
    rpt1, rpt2, rpt3 = get_accumulated_rpt(obj_list = adgroup_list, date1 = date1, date2 = date2, date3 = date3)
    check_attr_list = ['cost', 'click', 'ctr', 'cpc', 'paycount', 'roi']
    html += '<div>策略: 默认策略</div>'
    html += '<div>样本：%s个推广组</div>' % len(adgroup_list)
    html += '<div>期望：未知</div>'
    html += '<div>优化前后一天数据对比：</div>'
    html += '<table><tr><th>---</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (date1.strftime('%m-%d'), date2.strftime('%m-%d'), date3.strftime('%m-%d'))
    for attrname in check_attr_list:
        html += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (attrname, getattr(rpt1, attrname), getattr(rpt2, attrname), getattr(rpt3, attrname))
    html += '</table>'
    html += '<b>'
    camp_list = []
    print 'check strategy <Default> finished.'

    # total
    html += '<div>所有优化宝贝数据总合</div>'


    send_email(sub = 'alg_check_result', content = html)
    print 'alg check finished...'

if __name__ == '__main__':
    date_check = datetime.now() - timedelta(days = 5)
    alg_check(date = date_check)

