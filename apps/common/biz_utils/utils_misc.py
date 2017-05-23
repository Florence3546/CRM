# coding=UTF-8
'''
其它混合工具类，不方便分类的公共函数写在该文件中
Created on 2011-09-09
@author: hehao
'''

import re, time, datetime, md5

from django.conf import settings

from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_log import log
from apps.common.utils.utils_misc import get_request_ip
from apps.common.biz_utils.utils_permission import CATEGORY_SERVER_CODE
from apps.common.cachekey import CacheKey

def get_duplicate_task(error_msg):
    '''获取异步接口的task_id'''
    task_id = 0
    try:
        sub_msg = (eval(error_msg))['error_response']['sub_msg']
        pattern = re.compile('TaskId=(?P<x>\d*)', re.M | re.U | re.I)
        match_list = pattern.findall(sub_msg)
        if match_list and match_list[0]:
            task_id = int(match_list[0])
    except Exception, e:
        log.exception("parse task_id failed, error_msg=%s, e=%s" % (error_msg, e))
    return task_id

def jl_sign_with_secret(param_dict, secret = None):
    if not secret:
        secret = settings.JAPI_SECRET
    param_dict['timestamp'] = str(int(time.time()))
    src = secret + ''.join(["%s%s" % (k, v) for k, v in sorted(param_dict.items())]) + secret
    sign = md5.new(src).hexdigest().upper()
    param_dict['sign'] = sign
    return param_dict

def jl_check_sign_with_secret(param_dict, secret = None, timeout = 0):
    '''
    \精灵md5参数加密解密机制使用方法：
    >>> param_dict = {'x':'aaa', 'y':'bbb'}
    >>> param_dict = jl_sign_with_secret(param_dict, secret = '1qtrew23')
    >>> param_dict.has_key('sign')
    True
    >>> time.sleep(3)
    >>> jl_check_sign_with_secret(param_dict, secret = '1qtrew23', timeout = 4)
    'ok'
    >>> jl_check_sign_with_secret(param_dict, secret = '1qtrew23', timeout = 2)
    'timeout'
    '''
    if not secret:
        secret = settings.JAPI_SECRET
    if not settings.DEBUG and timeout:
        dt = int(time.time()) - int(param_dict.get('timestamp', '0'))
        if dt > timeout:
            return 'timeout'
    sign1 = param_dict.pop('sign', '')
    src = secret + ''.join(["%s%s" % (k, v) for k, v in sorted(param_dict.items())]) + secret
    sign2 = md5.new(src).hexdigest().upper()
    if sign1 == sign2:
        return 'ok'
    else:
        return 'no_permission'

def get_forecast_scope(forecast):
    '''根据页面预估排名，获取排名范围'''
    forecast = int(forecast)
    if forecast < 1 or forecast > 100:
        return '101'
    elif forecast >= 1 and forecast <= 5:
        return '1-5'
    elif forecast >= 6 and forecast <= 8:
        return '6-8'
    elif forecast >= 9 and forecast <= 13:
        return '9-13'
    elif forecast >= 14 and forecast <= 21:
        return '14-21'
    elif forecast >= 22 and forecast <= 26:
        return '22-26'
    elif forecast >= 27 and forecast <= 39:
        return '27-39'
    elif forecast >= 40 and forecast <= 52:
        return '40-52'
    elif forecast >= 53 and forecast <= 65:
        return '53-65'
    elif forecast >= 66 and forecast <= 78:
        return '66-78'
    elif forecast >= 79 and forecast <= 91:
        return '79-91'
    elif forecast >= 92 and forecast <= 100:
        return '92-100'
    return '101'

def get_credit_gif(score):
    '''
    \信用级别划分，参考淘宝规则页面
    http://service.taobao.com/support/knowledge-847753.htm
    '''
    if score < 4:
        return "s_red_1"

    elif score <= 10:
        return "s_red_1"
    elif score <= 40:
        return "s_red_2"
    elif score <= 90:
        return "s_red_3"
    elif score <= 150:
        return "s_red_4"
    elif score <= 250:
        return "s_red_5"

    elif score <= 500:
        return "s_blue_1"
    elif score <= 1000:
        return "s_blue_2"
    elif score <= 2000:
        return "s_blue_3"
    elif score <= 5000:
        return "s_blue_4"
    elif score <= 10000:
        return "s_blue_5"

    elif score <= 20000:
        return "s_cap_1"
    elif score <= 50000:
        return "s_cap_2"
    elif score <= 100000:
        return "s_cap_3"
    elif score <= 200000:
        return "s_cap_4"
    elif score <= 500000:
        return "s_cap_5"

    elif score <= 1000000:
        return "s_crown_1"
    elif score <= 2000000:
        return "s_crown_2"
    elif score <= 5000000:
        return "s_crown_3"
    elif score <= 10000000:
        return "s_crown_4"
    else:
        return "s_crown_5"

def get_credit_level(icon):
    '''
    \信用级别划分，参考淘宝规则页面
    http://service.taobao.com/support/knowledge-847753.htm
    '''
    if not icon:
        return 0
    credit_dict = {
        '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10,
        '11':11, '12':12, '13':13, '14':14, '15':15, '16':16, '17':17, '18':18, '19':19, '20':20,
        '一心':1, '二心':2, '三心':3, '四心':4, '五心':5,
        '一钻':6, '二钻':7, '三钻':8, '四钻':9, '五钻':10,
        '一蓝冠':11, '二蓝冠':12, '三蓝冠':13, '四蓝冠':14, '五蓝冠':15,
        '一金冠':16, '二金冠':17, '三金冠':18, '四金冠':19, '五金冠':20,
        's_red_1':1, 's_red_2':2, 's_red_3':3, 's_red_4':4, 's_red_5':5,
        's_blue_1':6, 's_blue_2':7, 's_blue_3':8, 's_blue_4':9, 's_blue_5':10,
        's_cap_1':11, 's_cap_2':12, 's_cap_3':13, 's_cap_4':14, 's_cap_5':15,
        's_crown_1':16, 's_crown_7':17, 's_crown_3':18, 's_crown_4':19, 's_crown_5':20
    }
    return credit_dict.get(icon, 0)

def get_credit_icon(level):
    '''
    \信用级别划分，参考淘宝规则页面
    根据信誉级别反查称号
    http://service.taobao.com/support/knowledge-847753.htm
    '''
    if not level:
        return 0
    credit_dict = {
        '0':'', '1':'一心', '2':'二心', '3':'三心', '4':'四心', '5':'五心',
        '6':'一钻', '7':'二钻', '8':'三钻', '9':'四钻', '10':'五钻',
        '11':'一蓝冠', '12':'二蓝冠', '13':'三蓝冠', '14':'四蓝冠', '15':'五蓝冠',
        '16':'一金冠','17':'二金冠', '18':'三金冠', '19':'四金冠', '20':'五金冠'
    }
    return credit_dict.get(level, 0)

def can_download_rpt():
    '''当前是否可以下载报表、UDP数据或执行大任务'''
    from apps.common.models import Config
    (hour, minute) = Config.get_value('common.SHOP_TASK_TIME', default = (05, 30))
    if datetime.datetime.now().time() < datetime.time(hour, minute):
        return False
    return True

# TODO zhangyu 该函数中的代码应该放到download的get_date_scope函数中
def get_rpt_start_time():
    '''获取报表、UDP数据的下载时间'''
    interval_days = (can_download_rpt() and 1 or 2)
    return datetime.date.today() - datetime.timedelta(days = interval_days)


def set_cache_progress(shop_id, progress):
    '''根据shop_id设置一个缓存，用于记录下载进度'''
    download_task_key = CacheKey.SUBWAY_DOWNLOAD_TASK % shop_id
    CacheAdpter.set(download_task_key, progress, 'web', 60 * 60 * 2)

def get_cache_progress(shop_id):
    '''根据shop_id获取缓存信息，用于记录下载进度'''
    download_task_key = CacheKey.SUBWAY_DOWNLOAD_TASK % shop_id
    download_task_data = CacheAdpter.get(download_task_key, 'web', '')
    return download_task_data

def del_cache_progress(shop_id):
    '''删除缓存中的信息'''
    download_task_key = CacheKey.SUBWAY_DOWNLOAD_TASK % shop_id
    CacheAdpter.delete(download_task_key, 'web')


# 根据页面排名获取所在页数
def get_page_value_by_order(forecast_order):
    forecast_order = int(forecast_order)
    if forecast_order < 1 or forecast_order > 100:
        return '101'
    elif forecast_order >= 1 and forecast_order <= 5:
        return '1-5'
    elif forecast_order >= 6 and forecast_order <= 12:
        return '6-12'
    elif forecast_order >= 13 and forecast_order <= 17:
        return '13-17'
    elif forecast_order >= 18 and forecast_order <= 29:
        return '18-29'
    elif forecast_order >= 30 and forecast_order <= 34:
        return '30-34'
    elif forecast_order >= 35 and forecast_order <= 51:
        return '35-51'
    elif forecast_order >= 52 and forecast_order <= 68:
        return '52-68'
    elif forecast_order >= 69 and forecast_order <= 85:
        return '69-85'
    elif forecast_order >= 86 and forecast_order <= 100:
        return '86-100'
    return '101'

def get_ip_for_rank(request):
    ip = request.POST['ip']
    if ip == '' or ip == 'localhost' or ip == '127.0.0.1':
        ip = get_request_ip(request)
        if ip == 'localhost' or ip == '127.0.0.1':
            ip = '110.76.46.215'
    return ip

def analysis_web_opter(request, shop_id = 0):
    if request.session.get('login_from', 'taobao') == 'backend':
        opter = 2
        opter_name = request.session.get('psuser_name', 'unknown')
    else:
        opter = 1
        opter_name = ''
    return opter, opter_name
