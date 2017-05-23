# coding=UTF-8
import datetime

from django.conf import settings


def session(request):
    return {'session':request.session}

def file_version(request):
    return {'VERSION':'141029_1'}

def page_mark(request):
    return {'PAGE_MARK': request.path_info.count('/') >= 3 and request.path_info.split('/') or ''}

def settings_arg(request):
    return {'DEBUG':settings.DEBUG}

def web_menu(request):
    if request.user.is_superuser or not hasattr(request.user, 'shop_id') or not request.user.shop_id:
        return {}

    from apps.common.constant import Const
    from apps.common.utils.utils_cacheadpter import CacheAdpter
    from apps.common.cachekey import CacheKey
    from apps.common.biz_utils.utils_permission import test_permission, CATEGORY_SERVER_CODE, ATTENTION_CODE
    from apps.common.utils.utils_log import log

    from apps.ncrm.models import Customer

    def get_jlb_count(shop_id):
        """获取精灵币个数"""
        try:
            jlb_count = CacheAdpter.get(CacheKey.WEB_JLB_COUNT % shop_id, 'web', 'no_cache')
            if jlb_count == 'no_cache':
                from apps.web.point import PointManager
                jlb_count = PointManager.refresh_points_4shop(shop_id = request.user.shop_id)
            return jlb_count
        except Exception, e:
            log.error('get_jlb_count error,e=%s, shop_id=%s' % (e, shop_id))
            return 0

    def get_mnt_info(shop_id):
        """获取左侧导航全自动引擎菜单"""
        try:
            mnt_list = CacheAdpter.get(CacheKey.WEB_MNT_MENU % shop_id, 'web', [])
            if not mnt_list:
                from apps.subway.models_campaign import Campaign
                from apps.mnt.models import MntCampaign, MNT_TYPE_CHOICES
                campid_mnttype_dict = dict(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'mnt_type').order_by('start_time'))
                campid_title_dict = dict(Campaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'title'))
                mnt_desc_dict = dict(MNT_TYPE_CHOICES)
                for campaign_id, mnt_type in campid_mnttype_dict.items():
                    name = campid_title_dict[campaign_id]
                    mnt_type_name = mnt_desc_dict[mnt_type].replace('托管', '')
                    mnt_list.append({'name': name, 'campaign_id': campaign_id,'mnt_type_name':mnt_type_name})

                CacheAdpter.set(CacheKey.WEB_MNT_MENU % shop_id, mnt_list, 'web', 60 * 60 * 6)
            return mnt_list
        except Exception, e:
            log.error('get_mnt_info error,e=%s, shop_id=%s' % (e, shop_id))
            return []

    def get_server_menu():
        '''获取服务中心菜单 add by tianxiaohe 20151031'''
        try:
            server_menu_list = []
            if not server_menu_list:
                from apps.web.models import main_ad_coll
                page_list = main_ad_coll.find({'ad_position':'servermenu','ad_display':1,'ad_status':2}).sort('ad_weight', -1)

                for page in page_list:
                    server_menu_list.append({'id':str(page['_id']), 'obj_id':page.get('_id',0),'weight':page.get('ad_weight', ''), 'title':page.get('ad_title', '')})
                CacheAdpter.set(CacheKey.WEB_AD_MENU, server_menu_list, 'web', 60 * 60 * 6)
            return server_menu_list
        except Exception, e:
            log.error('get_server_menu error,e=%s, shop_id=%s' % (e, shop_id))
            return []

#     def get_rjjh_info(shop_id):
#         """获取人机结合旺旺信息"""
#         is_upgrade, server = True, None
#         try:
#             if test_permission(CATEGORY_SERVER_CODE, request.user):
#                 key = CacheKey.WEB_RJJH_CATEGORY_SERVICES % (shop_id)
#                 server = CacheAdpter.get(key, 'web', None)
#
#                 # 内部用户 及 正常订购用户
#                 if not server:
#                     try:
#                         _, operater, _, _ = Customer.get_or_create_servers([shop_id], category = "rjjh").get(shop_id, [None, None, None, None]) # [consult, rjjh, tp, department]
#
#                         if operater:
#                             server = {'ww':operater.ww}
#                             is_upgrade = False
#                         else:
#                             pass
#                     except Exception, e:
#                         log.error('get customer error, shop_id=%s, e=%s' % (shop_id, e))
#                 if server:
#                     CacheAdpter.set(key, server, 'web', 6 * 60 * 60)
#         except Exception, e:
#             log.error('get_mnt_info error,e=%s, shop_id=%s' % (e, shop_id))
#         return is_upgrade, server

    def get_rjjh_info(shop_id):
        """获取人机结合旺旺信息"""
        is_upgrade, server = True, None
        try:
            if test_permission(CATEGORY_SERVER_CODE, request.user):
                ww = request.session.get('rjjh_ww', None)
                if ww is None:
#                     _, rjjh, _, _ = Customer.get_or_create_servers([shop_id], category = "rjjh").get(shop_id, [None, None, None, None]) # [consult, rjjh, tp, department]
                    rjjh = Customer.objects.select_related('operater').get(shop_id = shop_id).operater
                    if rjjh:
                        ww = rjjh.ww
                        is_upgrade = False
                    else:
                        ww = ''
                    request.session['rjjh_ww'] = ww
                server = {'ww':ww}
        except Exception, e:
            log.error('get_mnt_info error,e=%s, shop_id=%s' % (e, shop_id))
        return is_upgrade, server

    def get_isvip(shop_id):
        from apps.web.utils import get_is_vip
        return get_is_vip(request.user)

    def get_consult_ww(request, shop_id):
        try:
            ww = request.session.get('consult_ww', None)
            if ww is None:
#                 consult, _, _, _ = Customer.get_or_create_servers([shop_id], category = "consult").get(shop_id, [None, None, None, None]) # [consult, rjjh, tp, department]
                consult = Customer.objects.select_related('consult').get(shop_id = shop_id).consult
                if consult:
                    ww = consult.ww
                else:
                    ww = ''
                request.session.update({'consult_ww':ww})
            return ww
        except Exception, e:
            log.error('get_consult_ww error,e=%s, shop_id=%s' % (e, shop_id))
        return ""

    result_dict = {}
    shop_id = int(request.user.shop_id)
    result_dict.update({'JLB_COUNT':get_jlb_count(shop_id),
                        'MNT_LIST':get_mnt_info(shop_id),
                        'IS_VIP':get_isvip(shop_id),
                        'CONSULT_WW':get_consult_ww(request, shop_id),
                        'SERVER_MENU_LIST':get_server_menu(),
                        'CAN_USE_ATTENTION':test_permission(ATTENTION_CODE, request.user), # 临时处理千牛权限问题
                        })
    is_upgrade, server = get_rjjh_info(shop_id)
    result_dict.update({'server':server,
                        'server_upgrade':is_upgrade})
    return result_dict


def rjjh_worktime(request):
    week_scope = [5, 6]
    time_scope = (datetime.time(9, 0, 0), datetime.time(18, 0, 0))

    today = datetime.datetime.now()
    week_day = today.weekday()
    today_time = today.time()
    if week_day not in week_scope and time_scope[0] <= today_time < time_scope[1]:
        return {'is_worktime':True}
    return {'is_worktime':False}
