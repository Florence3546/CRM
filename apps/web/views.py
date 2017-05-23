# coding=UTF-8
import datetime
import re
from threading import Thread

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from mongoengine.errors import DoesNotExist

from apilib import get_tapi
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import date_2datetime, time_is_someday, datetime_2string, time_is_recent
from apps.common.utils.utils_misc import get_value_with_secret
from apps.common.utils.utils_render import render_to_limited, render_to_error
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.biz_utils.utils_permission import ORDER_VERSION_DICT
from apps.common.cachekey import CacheKey
from apps.common.constant import Const
from apps.common.biz_utils.utils_permission import AUTO_RANKING_CODE, ATTENTION_CODE, test_permission

from apps.web.forms import AdgroupSearchForm
from apps.web.utils import get_trend_chart_data, load_danger_cats_info, update_appraise_record
from apps.web.models import main_ad_coll, SaleLink, pa_coll, OrderTemplate, MemberStore, LotteryOrder
from apps.web.popup import MainAds
from apps.subway.models import Account, Campaign, Adgroup, Keyword, Creative, Item, attn_coll, CustomCreative
from apps.subway.download import Downloader, parse_status
from apps.mnt.models import MntCampaign, MNT_TYPE_CHOICES
from apps.router.models import Agent, User
from apps.kwslt.models_cat import Cat
from apps.web.models_lottery import Lottery

from dwebsocket.decorators import accept_websocket
from apps.engine.models_channel import MessageChannel
from apps.engine.models_corekw import CoreKeyword
from apps.ncrm.models import Customer

from apps.kwslt.models_cat import CatStatic

import time

@accept_websocket
def echo(request):
    try:
        if request.is_websocket():
            if request.user.is_anonymous():
                request.websocket.close()
            else:
                keyword_id = int(request.GET['keyword_id'])
#                 request.websocket.send("now start check rank...")
#                 p = MessageChannel.subscribe([keyword_id])
                p = MessageChannel.subscribe([keyword_id])
                request.websocket.send('ready')
                while True:
                    msg = p.get_message()
                    try:
                        request.websocket.read()
                    except Exception, EOFError:
                        break
                    if msg:
                        if isinstance(msg['data'], str):
                            request.websocket.send(msg['data'].encode('utf-8'))
                    time.sleep(0.1)
                MessageChannel.unsubscribe(p, [keyword_id])
                MessageChannel.delete_publish_history([keyword_id])
                request.websocket.close()
        else:
            return HttpResponse("<html><body>Just kidding...</body></html>")
    except Exception, e:
        log.error("error, e=%s" % e)
        return HttpResponse("<html>you should not see this content</html>")


@login_required
def web_home(request, template = 'web_home.html'):

    if hasattr(request, 'session') and request.session.get('next_url', ''):
        next_url = request.session['next_url']
        del request.session['next_url']
        return HttpResponseRedirect(next_url)

    shop_id = int(request.user.shop_id)
    try:
        account = Account.objects.get(shop_id = shop_id)
    except DoesNotExist, e:
        log.error('account limit error e=%s' % e)
        return render_to_limited(request, '您的直通车账户不存在，请确认登陆账号是否正确')

    from apps.web.point import Sign, Renewal

    # 检测用户通过续订兑换订购的链接
    Renewal.check_watting_point(shop_id = shop_id)
    # 判断用户是否签到
    is_sign_today = Sign.is_sign_today(shop_id = shop_id)
    # 获取用户当前等级
    grade, _, parcent = Account.get_grade_display(shop_id = shop_id)
    # 广告
    show_ad_dict = {}
    try:
        show_ad_dict = MainAds(shop_id = shop_id).get_show_ad()
    except Exception, e:
        log.error('get show_ads error,e=%s, shop_id=%s' % (e, shop_id))

    char_link = show_ad_dict.get('charlink', None)
    if char_link:
        request.session['char_link'] = {'obj_id':char_link.get('obj_id', ''), 'ad_title':char_link.get('ad_title', ''),
                                        'ad_url':char_link.get('ad_url', ''), 'ad_content':char_link.get('ad_content', '')}
    bottom_banner = show_ad_dict.get('bottombanner', None)
    if bottom_banner:
        request.session['bottom_banner'] = {'obj_id':bottom_banner.get('obj_id', ''), 'ad_content':bottom_banner.get('ad_content', '')}

    item_code = request.session['item_code']
    version_name = None
    if item_code in ORDER_VERSION_DICT:
        version_name = ORDER_VERSION_DICT[item_code][1]
    else:
        # 获取版本名称时，若出现KeyError，则给基础版本
        version_name = ORDER_VERSION_DICT['ts-25811-5'][1]

    # 判断有没有好评需要送分的
    try:
        update_appraise_record(shop_id)
    except Exception, e:
        log.exception('e = %s' % e)

    return render_to_response(template, {'account': account,
                                         "version_name": version_name,
                                         'right_notices': show_ad_dict.get('rightnotice', []),
                                         'char_link': char_link,
                                         'main_banner': show_ad_dict.get('mainbanner', None),
                                         'top_banner': show_ad_dict.get('topbanner', None),
                                         'bottom_banner': bottom_banner,
                                         'mr_window': show_ad_dict.get('mrwindow', None),
                                         'mc_window': show_ad_dict.get('mcwindow', None),
                                         'is_sign_today': is_sign_today, 'grade': grade,
                                         }, context_instance = RequestContext(request))

# @login_required
def adgroup_history(request, adgroup_id, template = 'adgroup_history.html'):
    shop_id = int(request.user.shop_id)
    try:
        adg = Adgroup.objects.get(shop_id = shop_id, adgroup_id = int(adgroup_id))
    except DoesNotExist:
        return render_to_error(request, '该宝贝已经被删除，请返回页面重新操作')
    return render_to_response(template, {'adg': adg}, context_instance = RequestContext(request))


# 检测是否是危险类目
@login_required
def check_danger_cats(request):
    if request.method == 'POST':
        cat_id_list = json.loads(request.POST['cat_id_list'])
        cat_id_list = list(set(cat_id_list)) # 先去重
        cat_id_list = [cat_id for cat_id in cat_id_list if int(cat_id) != 0]
        result = 'true'
        if cat_id_list:
            danger_cat_list = load_danger_cats_info()[request.user.shop_type]
            try:
                root_cat_dict = Cat.get_root_cat(cat_id_list = cat_id_list)
            except Exception, e:
                log.error('e = %s, cat_id_list = %s' % (e, cat_id_list))
                return HttpResponse('false')
            root_cat_id_list = list(set(root_cat_dict.values()))
            result = 'false' if list(set(root_cat_id_list) & set(danger_cat_list)) else 'true'

        return HttpResponse(result)

@login_required
def all_history(request, template = 'all_history.html'):
    shop_id = int(request.user.shop_id)
    campaigns = Campaign.objects.only('campaign_id', 'title').filter(shop_id = shop_id)
    camp_dict = {camp.campaign_id: camp.title for camp in campaigns}
    main_list = [(0, '全部计划')]
    main_list.extend(camp_dict.items())
    return render_to_response(template, {'main_list': main_list}, context_instance = RequestContext(request))

@login_required
def duplicate_check(request, template = 'duplicate_check.html'):
    shop_id = int(request.user.shop_id)
    dler_obj = Downloader.objects.get(shop_id = shop_id)

    def sync_data():
        dler_obj.auto_sync_struct() # 先同步结构，再同步关键词报表
        dler_obj.sync_rpt(Keyword)

    kwrtp_isok = False
    status_result = parse_status(dler_obj.keywordrpt_status)
    if status_result:
        if time_is_someday(status_result[1]):
            if status_result[0] == 'OK':
                kwrtp_isok = True
        else:
            Thread(target = sync_data).start()
    else:
        Thread(target = sync_data).start()
    return render_to_response(template, {'kwrtp_isok': kwrtp_isok}, context_instance = RequestContext(request))


@login_required
def attention_list(request, template = 'attention_list.html'):
    shop_id = int(request.user.shop_id)

    attention_count = 0
    attention = attn_coll.find_one({'_id': shop_id})
    if attention:
        attention_count = len(attention['keyword_id_list'])

    if attention_count:
        dler_obj = Downloader.objects.get(shop_id = shop_id)
        dl_flag, _ = dler_obj.check_status_4rpt(klass = Keyword)
        if dl_flag:
            dler_obj.auto_sync_struct() # 先同步结构，再同步关键词报表
            dler_obj.sync_rpt(Keyword)
    last_day = 7
    return render_to_response(template, {'last_day': last_day}, context_instance = RequestContext(request))

@login_required
def title_optimize(request, template = 'title_optimize.html'):
    shop_id = int(request.user.shop_id)
    try:
        adgroup_id = int(request.GET.get('adgroup_id', 0))
        adgroup = Adgroup.objects.get(shop_id = request.user.shop_id, adgroup_id = adgroup_id)
        item = Item.objects.get(shop_id = shop_id, item_id = adgroup.item_id)
        campaign = Campaign.objects.only('campaign_id', 'title').get(shop_id = shop_id, campaign_id = adgroup.campaign_id)
    except DoesNotExist:
        return render_to_error(request, '该宝贝可能不存在或者下架，请尝试同步数据')
    log.info('title_optimize shop_id=%s item_id=%s' % (request.user.shop_id, adgroup.item_id))

    update_flag = request.GET.get('update_flag') == "True"
    update_hot_flag = request.GET.get('update_hot_flag') == "True"

    # 品牌词
    item.brand_list = item.property_dict.get(u'品牌', [])

    # 属性词
    item.propword_hot_list = item.get_propword_hot_list(update_flag = update_flag, update_hot_flag = update_hot_flag)

    # 从缓存中取修饰词及其热度，并从中去掉促销词
    dcrtword_hot_list = item.get_dcrtword_hot_list(update_flag = update_flag, update_hot_flag = update_hot_flag)
    item.dcrtword_hot_list = [word_hot for word_hot in dcrtword_hot_list if word_hot[0] not in Const.WEB_PROMOTION_WORDS]

    # 产品词
    item.prdtword_hot_list = item.get_prdtword_hot_list(update_flag = update_flag, update_hot_flag = update_hot_flag)

    # 标题词根字符串
    title_word_str = ','.join(item.pure_title_word_list)

    # 标题优化周期为7天
    optimize_prompt = ''
    update_convwrod_flag = 0
    if item.title_optimize_time:
        delta_days = (datetime.date.today() - item.title_optimize_time.date()).days
        if delta_days == 0:
            optimize_prompt = u'亲，您今天已优化过标题，建议7天后再优化。'
        elif delta_days < 7:
            optimize_prompt = u'亲，您%s天前已优化过标题，建议%s天后再优化。' % (delta_days, 7 - delta_days)
        else:
            optimize_prompt = u'亲，您上次优化这个宝贝标题的时间是：%s。' % item.title_optimize_time.strftime('%Y-%m-%d %H:%I:%S')
            update_convwrod_flag = 1

    return render_to_response(template, {'adg': adgroup, 'item': item, 'campaign':campaign,
                                         'title_word_str': title_word_str,
                                         'optimize_prompt': optimize_prompt,
                                         'WEB_PROMOTION_WORDS': Const.WEB_PROMOTION_WORDS,
                                         'flagship_prmtwords': Const.WEB_FLAGSHIP_PROMOTION_WORDS,
                                         'update_convwrod_flag': update_convwrod_flag,
                                         }, context_instance = RequestContext(request))


@login_required
def select_keyword(request, select_type, template = 'select_keyword.html'):
    shop_id = int(request.user.shop_id)
    adgroup_id = int(request.GET.get('adgroup_id'))
    try:
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        if adgroup.mnt_type>0 and adgroup.use_camp_limit:
            adgroup.limit_price_max = MntCampaign.objects.get(shop_id = shop_id,
                                                              campaign_id = adgroup.campaign_id).max_price
        elif adgroup.limit_price and adgroup.limit_price > 5:
            adgroup.limit_price_max = adgroup.limit_price
        else:
            adgroup.limit_price_max = 500
        adgroup.init_limit_price = adgroup.limit_price_max
        item = Item.objects.get(shop_id = shop_id, item_id = adgroup.item_id)
        cat_id = item.cat_id
    except DoesNotExist:
        return render_to_error(request, '该宝贝可能不存在或者下架，请尝试同步数据')
    #     keyword_count = Keyword.objects.filter(shop_id = shop_id, audit_status = 'audit_pass', adgroup_id = adgroup_id).count()
    keyword_count = Keyword.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id).count()

    elemword_dict = {}
    prdtword_list = [word for word, hot in item.get_prdtword_hot_list()]
    decorate_word_list = item.get_decorate_word_list()
    decorate_word_list.extend(item.sale_word_list)
    decorate_word_list = [word for word in decorate_word_list if len(word) > 1]

    elemword_dict['prdtword_list'] = prdtword_list
    elemword_dict['dcrtword_list'] = decorate_word_list

    elemword_dict['prdtword_str'] = '\n'.join(prdtword_list[:5])
    decorate_word_list = list(set(decorate_word_list) - set(Const.WEB_PROMOTION_WORDS))
    elemword_dict['dcrtword_str'] = '\n'.join(decorate_word_list[:10])
    prmtword_list = []
    for prmtword in Const.WEB_PROMOTION_WORDS:
        if prmtword in item.title:
            prmtword_list.append(prmtword)
    elemword_dict['prmtword_str'] = '\n'.join(prmtword_list[:5])
    elemword_dict['brandword_list'] = item.get_S_label
    elemword_dict['sale_word_list'] = item.get_H_label

    data = {'adg': adgroup,
            'adgroup': adgroup,
            'cat_id': cat_id,
            'select_type': select_type,
            'keyword_count': keyword_count,
            'elemword_dict': elemword_dict,
            }

    # 为了提高选词的速度，这里直接通知worker赶紧准备数据,用户可能马上就要来选词了，请提前准备好
    return render_to_response(template, data, context_instance = RequestContext(request))


@login_required
def bulk_optimize(request, adgroup_id, inner = '', executor = '', cfg = '', template = 'bulk_optimize.html'):
    try:
        adgroup = Adgroup.objects.get(shop_id = request.user.shop_id, adgroup_id = adgroup_id)
        adgroup.get_mobile_status()
    except DoesNotExist:
        return render_to_error(request, '该宝贝已经被删除，请返回页面重新操作')
    if adgroup.mnt_type:
        return HttpResponseRedirect(reverse('adgroup_data', kwargs = {'adgroup_id': adgroup_id}))

    # 获取用户自定义列
    custom_column = Account.get_custom_col(shop_id = request.user.shop_id)
    return render_to_response(template, {'adg': adgroup, 'inner': inner, 'executor': executor, 'cfg': cfg,
                                         'body_class': 'like_table width100', 'custom_column': custom_column},
                              context_instance = RequestContext(request))


@login_required
def rob_rank(request, adgroup_id, template = 'rob_rank.html'):
    try:
        adgroup = Adgroup.objects.get(shop_id = request.user.shop_id, adgroup_id = adgroup_id)
    except DoesNotExist:
        return render_to_limited(request, '该宝贝已经被删除，请返回页面重新操作')
    if adgroup.error_descr(adgroup.campaign):
        return render_to_limited(request, '%s，不能进行极速排名操作' % adgroup.error_descr(adgroup.campaign))
    if adgroup.mnt_type:
        return render_to_limited(request, '该宝贝已经由系统自动托管，请选择其他宝贝')

    return render_to_response(template, {'adg': adgroup}, context_instance = RequestContext(request))


@login_required
def deleted_keyword(request, adgroup_id, template = 'deleted_keyword.html'):
    shop_id = int(request.user.shop_id)
    try:
        adgroup = Adgroup.objects.get(shop_id = request.user.shop_id, adgroup_id = adgroup_id)
        if adgroup.mnt_type in [1, 3]:
            adgroup.limit_price_max = MntCampaign.objects.get(shop_id = shop_id,
                                                              campaign_id = adgroup.campaign_id).max_price
        elif adgroup.limit_price and adgroup.limit_price > 5:
            adgroup.limit_price_max = adgroup.limit_price
        else:
            adgroup.limit_price_max = 500
        adgroup.init_limit_price = adgroup.limit_price_max
    except DoesNotExist:
        return render_to_error(request, '该宝贝已经被删除，请返回页面重新操作')
    #     if adgroup.mnt_type:
    #         return render_to_error(request, '该宝贝已经由系统自动托管，请选择其他宝贝')

    return render_to_response(template, {'adg': adgroup}, context_instance = RequestContext(request))


@login_required
def smart_optimize(request, adgroup_id, inner = '', executor = '', cfg = '', template = 'smart_optimize.html'):
    try:
        adgroup = Adgroup.objects.get(shop_id = request.user.shop_id, adgroup_id = adgroup_id)
        adgroup.get_mobile_status()
    except DoesNotExist:
        return render_to_error(request, '该宝贝已经被删除，请返回页面重新操作')
    if adgroup.mnt_type:
        return HttpResponseRedirect(reverse('adgroup_data', kwargs = {'adgroup_id': adgroup_id}))
    # 获取用户自定义列
    custom_column = Account.get_custom_col(shop_id = request.user.shop_id)
    return render_to_response(template, {'adg': adgroup, 'inner': inner, 'executor': executor, 'cfg': cfg,
                                         'body_class': 'like_table width100', 'custom_column': custom_column},
                              context_instance = RequestContext(request))


@login_required
def ztc_health_check(request):
    """直通车整体健康检查"""
    shop_id = int(request.user.shop_id)
    return render_to_response('ztc_health_check.html', {'shop_id': shop_id}, context_instance = RequestContext(request))


@login_required
def adgroup_health_check(request, adgroup_id = 0):
    """推广组健康检查"""
    try:
        adg = Adgroup.objects.get(shop_id = request.user.shop_id, adgroup_id = int(adgroup_id))
    except Exception, e:
        log.info('error is %s.' % e)
        return render_to_error(request, '系统未存在该推广宝贝。')
    return render_to_response('adgroup_health_check.html', {'adg': adg}, context_instance = RequestContext(request))

@login_required
def upgrade_suggest(request, template = 'upgrade_suggest.html'):
    """续订升级页面"""
    present_id = int(request.GET.get('present_id', 0)) # 此部分要考虑加密解密
    present = MemberStore.get_present_byid(present_id) if present_id else None
    if present:
        is_activity = True
        template_list = OrderTemplate.query_order_template_bydiscount(present.worth)
    else :
        is_activity = False
        template_list = OrderTemplate.query_base_order_template()

    template_infos = OrderTemplate.aggregate_version_infos_bydiscount(template_list)
    double_version = sorted(template_infos.get("ts-25811-8", []), key = lambda obj :-obj.cycle)
    four_version = sorted(template_infos.get("ts-25811-1", []), key = lambda obj :-obj.cycle)
    cate_version = template_infos.get("ts-25811-6", [])
    vip_version = template_infos.get("ts-25811-v9", [])
    version = request.session.get('item_code', 'ts-25811-8') # 默认给一个标准版算了
    return render_to_response(template, {
                "is_activity": is_activity,
                "cur_level": OrderTemplate.get_version_level(version),
                'double_version': double_version,
                'double_size': len(double_version) ,
                'four_version': four_version,
                'four_size': len(four_version),
                'cate_version': cate_version,
                'cate_size': len(cate_version),
                'vip_version': vip_version,
                'vip_size': len(vip_version) ,
    }, context_instance = RequestContext(request))


def lottery_coupon(request, template = 'lottery_coupon.html'):
    """抽奖优惠券领取页面"""
    user_lottery = Lottery.get_user_lottery(request.user)
    if not user_lottery:
        return render_to_limited(request, '亲，您没有优惠券:)')

    template_list = LotteryOrder.query_order_template_bydiscount(discount = int(user_lottery.sale_url))
    template_infos = LotteryOrder.aggregate_version_infos_bydiscount(template_list)
    double_version = sorted(template_infos.get("ts-25811-8", []), key = lambda obj:-obj.cycle)
    four_version = sorted(template_infos.get("ts-25811-1", []), key = lambda obj:-obj.cycle)
    cate_version = template_infos.get("ts-25811-6", [])
    vip_version = template_infos.get("ts-25811-v9", [])
    version = request.session['item_code']
    return render_to_response(template, {'cur_level': LotteryOrder.get_version_level(version),
                                         'double_version': double_version,
                                         'double_size': len(double_version),
                                         'four_version': four_version,
                                         'four_size': len(four_version),
                                         'cate_version': cate_version,
                                         'cate_size': len(cate_version),
                                         'vip_version': vip_version,
                                         'vip_size': len(vip_version),
                                         }, context_instance = RequestContext(request))

@login_required
def user_config(request, template = 'user_config.html'):
    """设置代理页面"""
    if get_value_with_secret(request.COOKIES.get('user_type', 'INVALID_VALUE'), 'AGENT_COOKIES') == '0':
        agent_list = Agent.objects.filter(principal = request.user).order_by('-last_modified')
        data = {'agent_list': agent_list}
        return render_to_response(template, data, context_instance = RequestContext(request))
    else:
        return render_to_limited(request, '亲，您没有权限使用该功能，请联系您代理的用户:)')


def agent_login(request, template = "agent_login.html"):
    '''代理用户登录'''
    from apps.router.forms import AgentLoginForm
    import hashlib

    errors = ""
    if request.method == "POST":
        form = AgentLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = hashlib.md5(form.cleaned_data['password']).hexdigest()
            agent_list = Agent.objects.filter(name = username, password = password)
            if agent_list:
                if len(agent_list) == 1:
                    user = agent_list[0].principal
                    login_url = user.get_backend_url(user_type = "agent", psuser_name = username)['web_url']
                    return HttpResponseRedirect(login_url)
                else:
                    return render_to_response('agent_list.html', {'agent_list': agent_list},
                                              context_instance = RequestContext(request))
            else:
                errors = "用户名不存在，或者用户名与密码错误"
        else:
            errors = "用户名和密码不能为空"
    else:
        form = AgentLoginForm(initial = {'username': '', 'password': ''})
    return render_to_response(template, {'form': form, 'errors': errors}, context_instance = RequestContext(request))


def agent_login_in(request):
    user_id = int(request.POST['user_id'])
    user = User.objects.get(id = user_id)
    login_url = user.get_backend_url(user_type = "agent")['web_url']
    return HttpResponse(json.dumps({'login_url': login_url}))


@login_required
def invite_friend(request, template = "invite_friend.html"):
    from apps.web.point import PointManager, Promotion4Shop

    shop_id = request.user.shop_id
    usable_point = PointManager.get_point(shop_id = shop_id)
    used_point = PointManager.get_used_point(shop_id = shop_id)

    # 用户推荐 方式2的记录
#     promotion_list = Promotion4Shop.get_promotion_4shop(shop_id = shop_id)

    # 用户推荐方式2
    promotion_list = list(pa_coll.find({'shop_id':int(request.user.shop_id), 'type':'promotion'}).sort("create_time", -1))
    data = {'usable_point':usable_point, 'used_point':used_point, 'promotion_list':promotion_list}
    return render_to_response(template, data, context_instance = RequestContext(request))


# @login_required
# def register_services(request):
#     shop_id = request.user.shop_id
#     phone = request.POST.get('phone')
#     qq = request.POST.get('qq')
#     ww = request.POST.get('ww')
#     lz_id = request.POST.get('lz_id', '')
#     lz_psw = request.POST.get('lz_psw', '')
#     if qq and ww and phone:
#         if Customer.register_server(shop_id, phone, qq, ww, lz_id, lz_psw):
#             return HttpResponseRedirect(reverse("web_home"))
#     return render_to_error(request, '注册类目专家服务失败！')

@login_required
def creative_optimization(request, adgroup_id, template = "creative_optimization.html"):

#     if request.user.shop_type == "C": # TODO zhongjinfeng 当B点的API搞定后全部切换回新版创意优化
#         return HttpResponseRedirect(reverse("image_optimoze", kwargs = {'adgroup_id': adgroup_id}))

    try:
        shop_id = request.user.shop_id
        adgroup = Adgroup.objects.exclude('rpt_list').get(shop_id = shop_id, adgroup_id = adgroup_id)
        adgroup.get_creative_rpt()
        creatives = Creative.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id).bind_data(rpt_days = 7)
        for creative in creatives:
            creative.rpt_days = 7
            category_list, series_cfg_list = get_trend_chart_data(data_type = 3, rpt_list = creative.snap_list)
            creative.category_list = category_list
            creative.series_cfg_list = json.dumps(series_cfg_list)
    except DoesNotExist:
        return render_to_error(request, '该宝贝已经被删除，请返回页面重新操作')
    #    if adgroup.mnt_type:
    #        return render_to_error(request, '该宝贝已经由系统自动托管，请选择其他宝贝')
    return render_to_response(template, {'adg': adgroup, 'creatives': creatives},
                              context_instance = RequestContext(request))


@login_required
def paithink_services(request, id, template = "paithink_services.html"):
    page = main_ad_coll.find_one({'_id': int(id)})
    message = ''
    if page:
        message = page.get('ad_content', '')
        if not page.get('ad_weight', 0):
            return HttpResponseRedirect(reverse('web_home'))
    return render_to_response(template, {'message': message, 'obj_id':page.get('_id')}, context_instance = RequestContext(request))


@login_required
def help_center(request, template = "help.html"):
    return render_to_response(template, context_instance = RequestContext(request))


def history(request, template = "history.html"):
    return render_to_response(template, context_instance = RequestContext(request))


def advertisement(request, ad_no):
    return render_to_response('ad%s.html' % ad_no, context_instance = RequestContext(request))


@login_required
def vip_home(request):
    from apps.web.point import PointManager, Sign
    from apps.web.utils import get_isneed_phone

    shop_id = request.user.shop_id
    customer = request.user.customer

    tapi = get_tapi(shop_id = shop_id)
    request.user.shop.sync_from_top(tapi)

    # 判断是否激活
    is_need_phone = get_isneed_phone(request.user)

    # 获取积分
    point_count = CacheAdpter.get(CacheKey.WEB_JLB_COUNT % shop_id, 'web', 'no_cache')
    if point_count == 'no_cache':
        point_count = PointManager.refresh_points_4shop(shop_id = request.user.shop_id)

    # 区分积分等级
    grade, next_grade, parcent = Account.get_grade_display(shop_id = shop_id)

    # 历史最高积分
    history_highest_point = Account.get_history_highest_point(shop_id = shop_id)

    # 判断今天是否签到
    is_sign_today = Sign.is_sign_today(shop_id = shop_id)
    get_attendance_day = Sign.get_attendance_day(shop_id = shop_id)

    # 判断并获取用户收货信息
    info_dict = customer.perfect_info if customer else {}

    # 改代码新版并没有用到，需要注销掉
    # 获取兑换话费的人数
#     phone_cost20_num = PointManager.get_exchange_gift_count(gift_type = 'phone_cost20') + 500 # 这里直接加了500
#     discount_num = PointManager.get_exchange_gift_count(type = 'discount')

    data = {
        'point_count': point_count,
        'grade': grade,
        'parcent':parcent,
        'next_grade': next_grade,
        'is_sign_today': is_sign_today,
        'get_attendance_day': get_attendance_day,
        'info_dict': info_dict,
#         'phone_cost20_num': phone_cost20_num,
#         'discount_num': discount_num,
        'is_need_phone': is_need_phone,
        'history_highest_point': history_highest_point
    }
    return render_to_response('vip_home.html', {'data': data}, context_instance = RequestContext(request))


# @login_required
# def point_detial(request):
#     """积分详情"""
# #     Todo zhongjinfeng 此函数主要功能将移动到ajax中,代码清理时可以清除掉
#     from apps.web.point import PointManager, Sign
#     from apps.web.utils import get_isneed_phone
#     from apps.ncrm.models import Customer
#     from apps.ncrm.utils import pagination_tool
#
#
#     page = request.GET.get('page', 1)
#     shop_id = request.user.shop_id
#     customer = request.user.customer
#
#     # 判断今天是否签到
#     is_sign_today = Sign.is_sign_today(shop_id = shop_id)
#
#     # 判断是否激活
#     is_need_phone = get_isneed_phone(request.user)
#
#     is_perfect_info, perfect_info = False , {}
#     if customer:
#         is_perfect_info = customer.is_perfect_info # 判断用户是否完善信息
#         perfect_info = customer.perfect_info
#
#     # 用户积分记录
#     detial_list = PointManager.get_point_detail(shop_id = shop_id)
#     page_info, detial_list = pagination_tool(page = page, record = detial_list)
#
#     data = {
#         'is_sign_today': is_sign_today,
#         'is_need_phone': is_need_phone,
#         'customer': customer,
#         'is_perfect_info': is_perfect_info,
#         'info_dict': perfect_info,
#         'detial_list': detial_list,
#         'page_info': page_info
#     }
#
#     return render_to_response('point_detial.html', {'data': data}, context_instance = RequestContext(request))


@login_required
def point_mall(request):
    """积分商城"""
    from apps.web.point import PointManager

    shop_id = request.user.shop_id
    customer = request.user.customer
    is_perfect_info = customer.is_perfect_info if customer else False
    # 获取积分
    point_count = CacheAdpter.get(CacheKey.WEB_JLB_COUNT % shop_id, 'web', 'no_cache')
    if point_count == 'no_cache':
        point_count = PointManager.refresh_points_4shop(shop_id = request.user.shop_id)

    shop_items = MemberStore.query_present_templates()
    return render_to_response('point_mall.html', {'is_perfect_info': is_perfect_info, "shop_items":shop_items, 'point_count': point_count},
                              context_instance = RequestContext(request))

@login_required
def point_praise(request):
    """好评送积分"""
    from apps.web.point import PointManager

    shop_id = request.user.shop_id
    # 获取积分
    point_count = CacheAdpter.get(CacheKey.WEB_JLB_COUNT % shop_id, 'web', 'no_cache')
    if point_count == 'no_cache':
        point_count = PointManager.refresh_points_4shop(shop_id = request.user.shop_id)

    # 获取随机好评
    # appraises = Appraise.objects.filter().order_by('?')
    # appraises = appraises[:5]
    # return render_to_response('point_praise.html', {'point_count':point_count, 'appraises':appraises}, context_instance = RequestContext(request))
    return render_to_response('point_praise.html', {'point_count':point_count}, context_instance = RequestContext(request))

@login_required
def point_record_appraise(request):
    """记录用户好评的点击，以便用户好评后将积分加上"""
    from apps.web.point import Appraise

    REDIRECT = "http://fuwu.taobao.com/serv/manage_service.htm?spm=a1z13.1113649.0.0.IJOxVX&service_code=ts-25811"
    shop_id = request.user.shop_id
    Appraise.add_point_record(shop_id = shop_id)
    return HttpResponseRedirect(REDIRECT)

@login_required
def redirect_generate_link(request):
    """生成推荐链接"""
    shop_id = request.user.shop_id
    nick = request.user.nick
    template_id = int(request.GET.get('temp_id', 0))

    order_temp = OrderTemplate.get_ordertemplate_byid(template_id)
    redirect_url = ""
    if order_temp:
        try:
            tapi = get_tapi(shop_id = shop_id)
            if order_temp.is_base:
                from apps.web.point import Renewal
                Renewal.add_point_record(shop_id = shop_id, template_id = order_temp.id)
            redirect_url = order_temp.generate_order_link(nick, tapi)
        except Exception, e:
            log.exception('fuwu_sale_link_gen, nick=%s, e=%s' % (nick, e))
            return render_to_error(request, '生成链接失败，请联系顾问')
    else:
        return render_to_limited(request, '亲，对不起，优惠链接已经失效！')

    return HttpResponseRedirect(redirect_url)

@login_required
def redirect_sale_link(request):
    """跳转到推广链接"""
    sale_link_id = int(request.GET.get('sale_link_id', -1))
    a_id = int(request.GET.get('a_id', -1))

    shop_id = request.user.shop_id
    nick = request.user.nick

    redirect_url = reverse('web_home')
    sale_link = SaleLink.objects.filter(id = sale_link_id)
    if sale_link:
        sale_link = sale_link[0]

        # 限制链接为指定活动
        if a_id != -1:
            vaild_id_list = MainAds(shop_id = shop_id).get_showad_list()
            if a_id not in vaild_id_list:
                return render_to_limited(request, '对不起，您不符合该活动的条件')
        try:
            tapi = get_tapi(shop_id = shop_id)
            top_obj = tapi.fuwu_sale_link_gen(nick = nick, param_str = sale_link.param_str)
            if top_obj and hasattr(top_obj, 'url'):
                redirect_url = top_obj.url
        except Exception, e:
            log.exception('fuwu_sale_link_gen, nick=%s, e=%s' % (nick, e))
            return render_to_error(request, '生成链接失败，请联系顾问')
    else:
        return render_to_limited(request, '亲，对不起，优惠链接已经失效！')

    return HttpResponseRedirect(redirect_url)

@login_required
def image_optimize(request, adgroup_id):
    shop_id = request.user.shop_id
    adgroup_id = int(adgroup_id)
    yesterday = datetime_2string(dt = datetime.datetime.today() - datetime.timedelta(days = 1), fmt = '%Y-%m-%d')
    seven_day = datetime_2string(dt = datetime.datetime.today() - datetime.timedelta(days = 7), fmt = '%Y-%m-%d')
    start_date = str(request.GET.get('s', seven_day))
    end_date = str(request.GET.get('e', yesterday))
    date_text = '%s&emsp;至&emsp;%s' % (start_date[5:], end_date[5:])
    if start_date == end_date:
        date_text = start_date[5:]

    try:
        adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
        adgroup.get_creative_rpt()
        adgroup.rpt_list = adgroup.Report.get_snap_list({'shop_id':shop_id, 'adgroup_id':adgroup_id}, start_date = start_date, end_date = end_date)
    except DoesNotExist:
        return render_to_error(request, '该宝贝已经被删除，请返回页面重新操作')

    creative_list = list(Creative.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id).order_by('create_time'))

    custom_creative_list = list(CustomCreative.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id).order_by('create-time'))
    crt_rpt_dict = Creative.Report.get_summed_rpt({'shop_id': shop_id, 'adgroup_id': adgroup_id}, start_date = start_date, end_date = end_date)


    # 获取类目点击率
    if adgroup.category_ids:
        g_cat_ctr = int(CatStatic.get_market_data_8id(cat_id = adgroup.category_ids.split(' ')[0]).get('ctr', '0'))

    cmp_ctr = g_cat_ctr * 0.8

    empty_rpt = Creative.Report()
    for creative in creative_list:
        creative.qr = crt_rpt_dict.get(creative.creative_id, empty_rpt)
        creative.show_ww_class = (int(creative.qr.ctr) == 0 or (cmp_ctr and creative.qr.ctr < cmp_ctr)) and 'dib' or 'hide'

    waiting_creative_list, complete_creative_list = [], []
    for custom_creative in custom_creative_list:
        if custom_creative.status == 0:
            waiting_creative_list.append(custom_creative)
        else:
            custom_creative.qr = crt_rpt_dict.get(custom_creative.creative_id, empty_rpt)
            custom_creative.show_ww_class = (int(custom_creative.qr.ctr) == 0 or (cmp_ctr and custom_creative.qr.ctr < cmp_ctr)) and 'dib' or 'hide'
            complete_creative_list.append(custom_creative)

    # 获取商品主图
    tapi = get_tapi(shop_id = shop_id)
    item_img_list = CustomCreative.get_item_img_list(tapi = tapi, shop_id = shop_id, item_id_list = [adgroup.item_id])
    img_list = item_img_list and item_img_list[adgroup.item_id] or None


    return render_to_response('image_optimize.html', {'adg': adgroup,
                                                      'creatives':creative_list,
                                                      'waiting_creatives':waiting_creative_list,
                                                      'complete_creatives':complete_creative_list,
                                                      'img_list':img_list,
                                                      'start_date':start_date,
                                                      'end_date':end_date,
                                                      'date_text': date_text
                                                      },
                              context_instance = RequestContext(request))

@login_required
def upload_item_img(request):
    """上传商品主图"""
    from apilib.binder import FileItem

    error = ""
    item_id = request.POST.get('item_id', None)
    callback = request.POST.get('callback', None)
    shop_id = int(request.user.shop_id)
    tapi = tapi = get_tapi(shop_id = shop_id)

    if request.method == 'POST':
        file = request.FILES.get("item_img", None)
        if file.size > 1024 * 1024 * 10:
            error = "文件大小不能超过10M"

        r = re.compile('^image/*')
        if not r.match(file.content_type):
            error = "只能上传图片，如:jpg,gif,png"

        if error:
            return HttpResponse('<script>require([]).%s(%s)</script>' % (callback, json.dumps({'error':error})))

        img_id, url = -1, ""

        if item_id and shop_id and tapi:
            try:
                file_item = FileItem(file.name, file.read())
                img_id, url, err = CustomCreative.item_img_upload(tapi = tapi, shop_id = shop_id, num_iid = item_id, image = file_item)
                if err:
                    error = err
            except Exception, e:
                error = "上传图片到淘宝服务器错误"
        else:
            error = "参数不全"

        return HttpResponse('<script>window.parent.%s(%s)</script>' % (callback, json.dumps({'error':error, 'img_id':img_id, 'url':url})))

@login_required
def hand_optimize(request, campaign_id = 0, template = 'hand_optimize.html'):
    shop_id = int(request.user.shop_id)
    last_day = int(request.POST.get('last_day', 1))
    try:
        campaign_id = int(campaign_id)
    except:
        campaign_id = 0
    mnt_type = 0
    mnt_campaigns = MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id)
    if campaign_id == 1:
        mnt_type = 1
    elif campaign_id > 2:
        if len(mnt_campaigns):
            mnt_type = mnt_campaigns[0].mnt_type

    mnt_campaign_dict = dict(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'mnt_type'))
    campaign_list = list(Campaign.objects.filter(shop_id = shop_id))
    mnt_desc_dict = dict(MNT_TYPE_CHOICES)
    for campaign in campaign_list:
        campaign.mnt_type = mnt_campaign_dict.get(campaign.campaign_id, 0)
        campaign.mnt_name = mnt_desc_dict.get(campaign.mnt_type, '').replace('托管', '') if campaign.mnt_type else '手动'
    campaign_list.sort(key = lambda x:x.mnt_type, reverse = True)

    main_list = [{'id':0, 'name':'全部计划', 'mnt_type':None},
                 {'id':1, 'name': '全部已托管计划', 'mnt_type':None},
                 {'id':2, 'name': '全部未托管计划', 'mnt_type':None}]
    for campaign in campaign_list:
        main_list.append({'id':campaign.id, 'name': campaign.title, 'mnt_type':campaign.mnt_name})
    return render_to_response(template, {'last_day': last_day,
                                         'camp_id': campaign_id,
                                         'mnt_type': mnt_type,
                                         'add_item_flag': request.GET.get('add_item_flag', 0),
                                         'offline_type': request.GET.get('offline_type', 0),
                                         'main_list': main_list,
                                         }, context_instance = RequestContext(request))

@login_required
def auto_rob_rank(request, template = 'auto_rob_rank.html'):
    """自动抢排名"""
    version_limit = True
    if test_permission(AUTO_RANKING_CODE, request.user):
        version_limit = False
    custom_column = Account.get_custom_col(shop_id = request.user.shop_id)
    return render_to_response(template, {"custom_column":custom_column, "version_limit":version_limit}, context_instance = RequestContext(request))

@login_required
def shop_core(request, template = "shop_core.html"):
    """店铺核心词"""
    custom_column = []
    refresh_time = None
    condition = "ok"
    version_limit = True
    if test_permission(ATTENTION_CODE, request.user):
        version_limit = False

        shop_id = int(request.user.shop_id)
        custom_column = Account.get_custom_col(shop_id = shop_id)
        ck, _ = CoreKeyword.objects.get_or_create(shop_id = shop_id, defaults = {'kw_dict_list': [], 'update_time': None})

        condition = "ok"
        if ck.status:
            condition = "doing"
        else:
            if time_is_someday(ck.update_time): # update_time为None的场景在时间判断里已经有了
                condition = "ok"
            elif time_is_recent(ck.update_time, days = 7):
                if not time_is_someday(ck.report_sync_time): # 如果当天也已经同步过报表了，则不再去同步
                    Thread(target = ck.sync_current_report).start()
                    condition = "doing"
                else:
                    condition = "ok"
            else:
                Thread(target = ck.calc_top_keywords).start()
                condition = "doing"
        refresh_time = ck.update_time

    resp_data = {"custom_column": custom_column,
                 "refresh_time": refresh_time,
                 "condition": condition,
                 "version_limit": version_limit}

    return render_to_response(template, resp_data, context_instance = RequestContext(request))

@login_required
def op_history(request, template = 'op_history.html'):
    shop_id = int(request.user.shop_id)
    mnt_campaign_dict = dict(MntCampaign.objects.filter(shop_id = shop_id).values_list('campaign_id', 'mnt_type'))
    campaign_list = list(Campaign.objects.filter(shop_id = shop_id))
    mnt_desc_dict = dict(MNT_TYPE_CHOICES)
    for campaign in campaign_list:
        campaign.mnt_type = mnt_campaign_dict.get(campaign.campaign_id, 0)
        campaign.mnt_name = mnt_desc_dict.get(campaign.mnt_type, '').replace('托管', '') if campaign.mnt_type else '手动'
    campaign_list.sort(key = lambda x:x.mnt_type, reverse = True)

    main_list = [{'id':-1, 'name':'全部计划', 'mnt_type':None},
                 {'id':1, 'name': '全部已托管计划', 'mnt_type':None},
                 {'id':2, 'name': '全部未托管计划', 'mnt_type':None}]
    for campaign in campaign_list:
        main_list.append({'id':campaign.id, 'name': campaign.title, 'mnt_type':campaign.mnt_name})

    start_date = datetime.datetime.now()
    end_date = start_date - datetime.timedelta(days = 2)
    return render_to_response(template, {"start_date":end_date, "end_date":start_date, "main_list":main_list}, context_instance = RequestContext(request))
