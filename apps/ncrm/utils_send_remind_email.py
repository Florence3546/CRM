# coding=UTF-8
'''
Created on 2015年6月17日

@author: tianxiaohe
'''
from time import strftime, localtime

from apps.common.constant import Const
from apps.common.utils.utils_datetime import string_2date, days_diff_interval
from apps.common.utils.utils_email import send_html_email
from apps.common.utils.utils_log import log
from apps.ncrm.models import HumanRemindEmail
from settings import EMAIL_HOST_USER


def login_send_email(puser_id, puser_name_cn, puser_department, puser_department_display, puser_birthday, puser_probation_date, puser_contract_end):
    """
        用户登录时启动该线程，检查用户的生日，试用期考核时间、合同到期时间是否临近，
        若员工生日或合同到期时间临近，则给行政人员发送邮件
        若试用期考核时间临近，则需给主管临到发送邮件
        邮件发送时间为提前10天、提前5天、提前1天
    """
    if puser_birthday:
        send_birthday_remind_email(puser_id, puser_department, puser_department_display, puser_name_cn, puser_birthday)
    if puser_probation_date:
        send_probation_email(puser_id, puser_name_cn, puser_department, puser_probation_date)
    if puser_contract_end:
        send_contract_end_email(puser_id, puser_department_display, puser_name_cn, puser_department, puser_contract_end)

# 发送生日提醒邮件
def send_birthday_remind_email(puser_id, puser_department, puser_department_display, puser_name_cn, puser_birthday):
    try:
        birthday = string_2date(strftime("%Y", localtime()) + '-' + str(puser_birthday.month) + '-' + str(puser_birthday.day))
        diff_days = days_diff_interval(birthday)
        if diff_days>0 and diff_days<=10:
            if diff_days>5 and diff_days<=10:
                # 查询提醒记录，当前年该员工提前10天的生日提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, email_time__year = strftime("%Y", localtime()), remind_type = '1', remind_node = '10')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "1", remind_node = "10")
                    new_hremail.save()
                    send_html_email("员工生日提醒", ''.join([str(diff_days),"天之后是", puser_department_display, "员工", puser_name_cn, "的生日"]),
                                    EMAIL_HOST_USER, [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
            elif diff_days>1 and diff_days<=5:
                # 查询提醒记录，当前年该员工提前5天的生日提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, email_time__year = strftime("%Y", localtime()), remind_type = '1', remind_node = '5')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "1", remind_node = "5")
                    new_hremail.save()
                    send_html_email("员工生日提醒", ''.join([str(diff_days),"天之后是", puser_department_display, "员工", puser_name_cn, "的生日"]),
                                    EMAIL_HOST_USER, [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
            else:
                # 查询提醒记录，当前年该员工提前1天的生日提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, email_time__year = strftime("%Y", localtime()), remind_type = '1', remind_node = '1')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "1", remind_node = "1")
                    new_hremail.save()
                    send_html_email("员工生日提醒", ''.join(["明天是", puser_department_display, "员工", puser_name_cn, "的生日"]),
                                    EMAIL_HOST_USER, [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
    except Exception, e:
        log.error('send_birthday_remind_email error, puser_id=%s, e=%s' % (puser_id, e))

# 试用期考核时间提醒
def send_probation_email(puser_id, puser_name_cn, puser_department, puser_probation_date):
    try:
        diff_days = days_diff_interval(puser_probation_date)
        if diff_days>0 and diff_days<=10:
            if diff_days>5 and diff_days<=10:
                # 查询提醒记录，该员工提前10天的试用期考核时间提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, remind_type = '2', remind_node = '10')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "2", remind_node = "10")
                    new_hremail.save()
                    send_html_email("员工试用期考核提醒", ''.join([puser_name_cn, "的试用期考核时间还有",str(diff_days),"天"]), EMAIL_HOST_USER,
                                    [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
            elif diff_days>1 and diff_days<=5:
                # 查询提醒记录，该员工提前5天的试用期考核时间提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, remind_type = '2', remind_node = '5')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "2", remind_node = "5")
                    new_hremail.save()
                    send_html_email("员工试用期考核提醒", ''.join([puser_name_cn, "的试用期考核时间还有",str(diff_days),"天"]), EMAIL_HOST_USER,
                                    [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
            else:
                # 查询提醒记录，该员工提前1天的试用期考核时间提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, remind_type = '2', remind_node = '1')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "2", remind_node = "1")
                    new_hremail.save()
                    send_html_email("员工试用期考核提醒", ''.join([puser_name_cn, "的试用期考核时间明天结束"]), EMAIL_HOST_USER,
                                    [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
    except Exception, e:
        log.error('send_probation_email error, puser_id=%s, e=%s' % (puser_id, e))

# 发送合同到期提醒
def send_contract_end_email(puser_id, puser_department_display, puser_name_cn, puser_department, puser_contract_end):
    try:
        diff_days = days_diff_interval(puser_contract_end)
        if diff_days>0 and diff_days<=10:
            if diff_days>5 and diff_days<=10:
                # 查询提醒记录，该员工提前10天的合同到期提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, remind_type = '3', remind_node = '10')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "3", remind_node = "10")
                    new_hremail.save()
                    send_html_email("员工合同到期提醒", ''.join([puser_department_display, "员工", puser_name_cn, "的合同还有",str(diff_days),"天到期"]),
                                    EMAIL_HOST_USER, [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
            elif diff_days>1 and diff_days<=5:
                # 查询提醒记录，该员工提前5天的合同到期提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, remind_type = '3', remind_node = '5')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "3", remind_node = "5")
                    new_hremail.save()
                    send_html_email("员工合同到期提醒", ''.join([puser_department_display, "员工", puser_name_cn, "的合同还有",str(diff_days),"天到期"]),
                                    EMAIL_HOST_USER, [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
            else:
                # 查询提醒记录，该员工提前1天的合同到期提醒邮件是否已发
                hremail = HumanRemindEmail.objects.filter(employee_id = puser_id, remind_type = '3', remind_node = '1')
                if not hremail:
                    new_hremail = HumanRemindEmail(employee_id = puser_id, remind_type = "3", remind_node = "1")
                    new_hremail.save()
                    send_html_email("员工合同到期提醒", ''.join([puser_department_display, "员工", puser_name_cn, "的合同明天到期"]),
                                    EMAIL_HOST_USER, [Const.NCRM_DEPARTMENT_LEADER_EMAIL[puser_department]])
    except Exception, e:
        log.error('send_contract_end_email error, puser_id=%s, e=%s' % (puser_id, e))
