# coding=UTF-8
import datetime
from threading import Thread

from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response

from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_log import log
from apps.common.utils.utils_render import render_to_limited
from apps.common.utils.utils_misc import set_value_with_secret
from apps.common.utils.utils_datetime import datetime_2string
from apps.common.models import Config
from apps.common.cachekey import CacheKey
from apps.common.biz_utils.utils_misc import jl_check_sign_with_secret, get_cache_progress
from apps.common.biz_utils.utils_permission import BASE_CODE
from apps.engine.models import ShopMngTask
from apps.router.models import UserInfoTool, Shop, ArticleUserSubscribe, AccessToken
from apps.router.login import LoginWeb, LoginQnpc, LoginQnyd
from apps.ncrm.models import Customer
from apilib import SessionCache


def main_port_web(request):
    return LoginWeb(request).run()


def main_port_qnpc(request):
    return LoginQnpc(request).run()


def main_port_qnyd(request):
    return LoginQnyd(request).run()


def sub_port(request):
    top_dict = {}
    top_dict.update(request.REQUEST)

    # URL合法性校验
    if not top_dict:
        return render_to_limited(request, '您的登录方式有误，请重新登陆您的管理后台，然后点击开车精灵的图标')
    check_result = jl_check_sign_with_secret(top_dict, timeout = 60 * 6)
    if check_result == 'no_permission':
        return render_to_limited(request, '您没有使用权限，请订购后重新登录')
    elif check_result == 'timeout':
        return HttpResponse('请求超时，请重新进入')

    log.info("LOGIN sub_port, nick=%s, from=%s" % (top_dict['visitor_nick'], top_dict['visitor_from']))
    auth_logout(request)

    try: # 执行登陆
        visit_dict = {'nick': top_dict['visitor_nick'], 'session': top_dict['top_session'], 'visitor_from': top_dict['visitor_from']}
        return for_user_login(request, visit_dict)
    except Exception, e:
        log.exception("sub_port exception, nick=%s, session=%s, visitor_from=%s, error=%s" % (top_dict['visitor_nick'], top_dict['top_session'], top_dict['visitor_from'], e))
        return render_to_limited(request, '登陆开车精灵发生系统错误')


def backend_login(request):
    top_dict = {}
    top_dict.update(request.REQUEST)

    # URL合法性校验
    check_result = jl_check_sign_with_secret(top_dict, timeout = 60 * 60)
    if check_result == 'no_permission':
        return HttpResponse('非法访问，您没有访问权限')
    elif check_result == 'timeout':
        return HttpResponse('非法访问，请求超时')
    elif not top_dict.has_key('shop_id'):
        return HttpResponse('非法访问，请求参数错误')
    auth_logout(request)

    try: # 模拟登陆
        is_agent = (top_dict.get('user_type', 'staff') == 'agent')
        visit_dict = {'nick':top_dict['nick'], 'session':top_dict['session'], 'visitor_from':top_dict['visitor_from']}
        request.session['psuser_name'] = top_dict['psuser_name']
        request.session['user_type'] = top_dict['user_type']
        return for_user_login(request, visit_dict, is_backend = (not is_agent), is_agent = is_agent)
    except Exception, e:
        log.exception("backend_login exception, nick=%s, session=%s, visitor_from=%s, error=%s" % (top_dict['nick'], top_dict['session'], top_dict['visitor_from'], e))
        return render_to_limited(request, '模拟登陆开车精灵发生系统错误')


def for_user_login(request, visit_dict, is_backend = False, is_agent = False):
    # 获取和保存用户信息
    visitor_from = visit_dict['visitor_from'] # 访问来源，可能是web、qnyd、qnpc
    request.session['platform'] = visitor_from # 保存平台便于limited、error页面定位模板
    platform = (visitor_from == 'web' and 'web' or 'qn') # 访问平台，可能是web、qn
    uit = UserInfoTool(nick = visit_dict['nick'], session = visit_dict['session'])
    user = uit.user
    if not user:
        return render_to_limited(request, '您的登录方式有误，请重新登陆您的管理后台，然后点击开车精灵的图标')

    is_valid, reason = uit.test_api()
    if not is_valid:
        if is_backend:
            return render_to_limited(request, '登录失败，失败原因：%s' % reason)
        else:
            return render_to_limited(request, '请重新登陆您的管理后台，然后点击开车精灵的图标')

    # 校验权限和初始化店铺
    if not user.is_staff:
        if not uit.init_shop():
            return render_to_limited(request, '获取店铺信息失败，请重新登录淘宝之后，再登陆开车精灵')

        perms_code = user.sync_perms_code()
        request.session['perms_code'] = perms_code
        if BASE_CODE not in perms_code:
            return render_to_limited(request, '您的没有权限登录开车精灵，请购买后再重新尝试')

    # 模拟用户登陆
    # user.set_password(user.email)
    user_cache = authenticate(nick = user.nick, password = visit_dict['session'])
    # 同步用户店铺信息，确认用户是B店还是C店
    # try:
    #     last_login = user.last_login
    #     now = datetime.datetime.today()
    #     if (now - last_login).days >= 7:
    #         user.sync_user_shop_type(platform)
    # except Exception, e:
    #     log.error('fail to sync user shop type the shop_id=%s and error=%s' % (user.shop_id, e))
    #     pass
    request.session['login_from'] = 'backend' if is_backend else 'taobao' # 钟超 保存session获取来源
    try:
        auth_login(request, user_cache)
    except Exception, e:
        if "'AnonymousUser' object has no attribute 'backend'" in str(e):
            if visitor_from == 'web':
                return LoginWeb.redirect_2top_authorize()
            elif visitor_from == 'qnpc':
                return LoginQnpc.redirect_2top_authorize()
            elif visitor_from == 'qnyd':
                return LoginQnyd.redirect_2top_authorize()
        raise e

    # 更新用户信息
    if not user.shop_id:
        shop = Shop.objects.get(user = user)
        shop_id = int(shop.sid)
        log.error("for_user_login found shop_id is None, shop_id=%s" % shop_id)
    else:
        shop_id = user.shop_id
    SessionCache.del_cache(shop_id = shop_id)

    # 同步下customer
    customer, _ = Customer.objects.get_or_create(shop_id = user.shop_id, defaults = {'nick':user.nick})

    now = datetime.datetime.now()
    plateform_type = 'kcjl' if visitor_from == 'web' else visitor_from
    if not is_backend:
        # 用户每日6点后首次登陆时自动发送邮件提醒所属的顾问，并清空用户的选词预览使用次数，同步用户信息
        work_time = datetime.datetime(now.year, now.month, now.day, 6)
        if not user.last_login or (now >= work_time and user.last_login < work_time):
            # user.login_remind_8email()
            user = uit.sync_top_user()
            user.select_count = 0 # 重置当天选词预览次数
        user.last_login = now

        # 添加用户登陆事件
        try:
            from apps.ncrm.models import Login as LoginEvent
            LoginEvent(shop_id = int(user.shop_id), plateform_type = plateform_type).save()
        except:
            pass

        try:
            from apps.web.point import Login, Expired, Invited4Shop
            Login.add_point_record(shop_id = user.shop_id) # 每天登陆送积分
            Expired.add_point_record(shop_id = user.shop_id) # 软件过期再登录扣除过期期间的积分
            Invited4Shop.add_point_record(shop_id = user.shop_id, nick = user.nick) # 加入系统判断积分的方法
        except Exception, e:
            log.exception("router check point error e = %s" % (e))

    user.shop_id = shop_id
    user.save()

    # 本地测试时把下面两行打开
    from web.point import Login, Expired, Invited4Shop
    Invited4Shop.add_point_record(shop_id = user.shop_id, nick = user.nick) # 加入系统判断积分的方法

    # 读取用户的模板主题保存到session中
    if Config.get_value('router.SYS_THEMEM', default = False):
        request.session['theme'] = Config.get_value('router.SYS_THEMEM')
    else:
        request.session['theme'] = user.theme

    # 读取用户手机，是否开启短信提醒及昵称
    if customer:
        # customer = customer[0]
        request.session['remind'] = customer.remind
        request.session['phone'] = customer.phone
        request.session['seller'] = customer.seller
        # 写入CRM缓存
        if not is_backend and customer.consult_id:
            login_cache = CacheAdpter.get(CacheKey.LOGIN_USERS % (customer.consult_id, datetime.date.today()), 'crm', {})
            shop_cache = login_cache.setdefault(customer.shop_id, [now, customer.nick, customer.phone, customer.qq, 0, ''])
            shop_cache[0] = now
            shop_cache[5] = plateform_type
            CacheAdpter.set(CacheKey.LOGIN_USERS % (customer.consult_id, datetime.date.today()), login_cache, 'crm', 24 * 60 * 60)

    # 登陆时删除左侧菜单缓存
    CacheAdpter.delete(CacheKey.WEB_MNT_MENU % user.shop_id, 'web')
    CacheAdpter.delete(CacheKey.WEB_ISNEED_PHONE % user.shop_id, 'web')

    # 将剩余天数,订购版本等标记记录到session中
    left_days = user.get_left_days()
    if left_days < 0:
        left_days = 0
    request.session['left_days'] = left_days
    request.session['deadline'] = datetime_2string(datetime.datetime.now()+datetime.timedelta(days=left_days),'%Y-%m-%d')
    request.session['highest_version'] = ArticleUserSubscribe.get_highest_version(nick = user.nick)
    request.session['item_code'] = ArticleUserSubscribe.get_hightest_item_code(nick = user.nick)
    request.session['visitor_from'] = visitor_from

    # 无线推广活动临时代码记录到session中
    # if user.f5 and user.f5.isdigit() and int(user.f5) == 1:
    #     request.session['apply_passed'] = 1

    # 启动新线程下载数据和跳转
    smt, _ = ShopMngTask.objects.get_or_create(shop_id = user.shop_id)
    if smt.is_runnable(is_login = True):
        if not get_cache_progress(request.user.shop_id): # TODO: zhangyu 20140323 Bug 缓存时间2小时，如果服务被Stop再Start，或其他原因线程消失，而缓存还在，则用户2小时后才能进入
            bg_thread = Thread(target = smt.run_task, kwargs = {'is_login':True})
            bg_thread.start()
        rsp = HttpResponseRedirect(reverse('waiting', args = [visitor_from]))
    else:
        from apps.subway.download import Downloader
        bg_thread = Thread(target = Downloader.download_all_struct, kwargs = {'shop_id': user.shop_id})
        bg_thread.start()
        rsp = HttpResponseRedirect(reverse('%s_home' % visitor_from))
        rsp = HttpResponseRedirect(reverse('waiting', args = [visitor_from]))
    rsp.set_cookie('user_type', set_value_with_secret(is_agent and 1 or 0, 'AGENT_COOKIES')) # 根据用户类型，设置cookie
    return rsp


def waiting(request, prefix):
    # @add zhongjinfeng web端和千牛pc端融合，在这个此将千牛pc定位到web模板
    if prefix == 'qnpc':
        prefix = 'web'
    return render_to_response('%s_waiting.html' % prefix, {}, context_instance = RequestContext(request))


def top_logout(request, theme, template = 'top_logout.html'):
    auth_logout(request)
    return render_to_response(template, {'theme':theme}, context_instance = RequestContext(request))
