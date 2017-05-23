# coding=utf-8
import base64
import urllib
import time
import hashlib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_render import render_to_limited
from apps.common.utils.utils_misc import url_param_2dict
from apps.common.biz_utils.utils_misc import jl_sign_with_secret
from apps.router.models import AccessToken, NickPort

###
# TODO 20170103 wuhuaqiao 待改进点：
# 1、Qnpc, Qnyd，是否要做时间戳校验。
# 2、把 token 中的其他字段利用起来，参考文档：http://open.taobao.com/doc2/detail.htm?articleId=118&docType=1&treeId=null#s2
# 3、是否兼容子帐号登录
###


OAUTH_ERROR_LIST = [
    ("authorize reject", "用户拒绝授权"),
    ("authorize code expire", "authorize code失效,请退出后重新登录授权"),
    ("please authorize again", "authorize code失效,请退出后重新登录授权"),
    ("need purchase", "必须先订购才能使用"),
    ("taobao staff can't accredit", "淘宝小二不允许访问"),
    ("subuser can't access", "应用不支持子账号访问"),
    ("parent account forbid this sub account to access app", "父账号未授权此子账号访问应用"),
    ("parent account forbidden", "父账号未授权或授权已过期，请退出后重新登录授权"),
    ("session expire", "当前会话已经过期，可能用户浏览器暂停太久已经超时，请退出后重新登录授权"),
    ("OAUTH SERVER ERROR", "淘宝系统内部错误，请退出后重新登录授权"),
]


class Login(object):
    '''
    三个入口，有的步骤web、qnpc相同，有的步骤web、qnyd相同，有的步骤qnpc、ynyd相同，
    这里将两者相同的步骤提到了基类Login中，另一个不相同的在自己的类中实现
    '''

    def __init__(self, request):
        self.request = request
        self.app_key = settings.APP_KEY
        self.app_secret = settings.APP_SECRET
        self.oauth_view_type = ''
        self.visitor_from = ''
        self.main_port = ''
        self.token = ''
        self.nick = ''
        self.timestamp = 0
        self.top_dict = {}
        self.top_sign = ''
        self.top_access_token = ''

    def check_is_oauth_and_result(self):
        '''检查请求是否是 oauth 验证，及验证结果、失败原因'''
        if self.request.GET.get('code', '') and self.request.GET.get('state', ''):
            return True, True, ''
        elif self.request.GET.get('error', '') and self.request.GET.get('error_description', ''):
            error_desc = self.request.GET['error_description']
            error_str = '认证失败，原因：%s, 请退出后重新登录授权' % error_desc
            for ed, reason in OAUTH_ERROR_LIST:
                if ed in error_desc:
                    error_str = reason
            return True, False, error_str
        else:
            return False, False, ''

    def check_parms_integrity(self):
        return True

    def get_token(self):
        self.token = AccessToken.get_access_token(nick = self.nick)
        if not self.token:
            self.token = AccessToken(nick = self.nick, platform = 'web')
            token_dict = AccessToken.process_top_data(self.top_dict)
            self.token.access_token = self.top_access_token
            self.token.uid = long(self.top_dict.get('taobao_user_id', 0) or self.top_dict.get('visitor_id', 0))
            self.token.refresh_token = token_dict['refresh_token']
            self.token.expire_time = token_dict['expire_time']
            self.token.save()
        return True

    def check_sign(self):
        req_dict = {}
        req_dict.update(self.request.REQUEST)
        top_sign = urllib.unquote(req_dict.pop('sign', ''))
        src = self.app_secret + ''.join(["%s%s" % (k, v) for k, v in sorted(req_dict.items())]) + self.app_secret
        sign = hashlib.md5(src).hexdigest().upper()
        return sign == top_sign

    def check_timestamp(self):
        # 1分钟之前的请求不理会
        time_length = int(time.time()) - self.timestamp / 1000
        limit_time = (settings.DEBUG and 60 * 30 or 60 * 2)
        return time_length < limit_time

    def jump_limited_page(self, error):
        return render_to_limited(self.request, error)

    def redirect_2subport(self, domain):
        url_param_dict = {
            'uid': self.token.uid,
            'platform': self.token.platform,
            'refresh_token': self.token.refresh_token,
            'top_session': self.token.access_token,
            'visitor_nick': self.token.nick,
            'visitor_from': self.visitor_from
        }
        subport_login_url = 'http://%s%s?%s' % (domain, reverse('sub_port'), urllib.urlencode(jl_sign_with_secret(url_param_dict)))
        return HttpResponseRedirect(subport_login_url)

    def redirect_2top_authorize(self):
        url_params = urllib.urlencode({
            'response_type': 'code',
            'client_id': self.app_key,
            'redirect_uri': self.main_port,
            'view': self.oauth_view_type,
            'state': self.visitor_from
        })
        redirect_url = 'https://oauth.taobao.com/authorize?%s' % url_params
        return HttpResponseRedirect(redirect_url)

    def run(self):
        try:
            is_login_ok = False
            is_oauth_request, is_auth_ok, oauth_error = self.check_is_oauth_and_result()
            if is_oauth_request:
                if is_auth_ok:
                    self.token = AccessToken.sync_access_token(self.request.GET['code'])
                else:
                    return self.jump_limited_page(oauth_error)
            elif self.check_parms_integrity() \
                    and self.check_timestamp() \
                    and self.check_sign() \
                    and self.get_token():
                is_login_ok = True

            log.info("LOGIN main_port, nick=%s, from=%s" % (self.nick, self.visitor_from))
            if is_auth_ok or is_login_ok:
                domain = NickPort.get_port_domain(nick=self.nick, force_create=True)
                if not domain:
                    return self.jump_limited_page('服务器繁忙，请稍候再登录')
                else:
                    return self.redirect_2subport(domain)
            else:
                return self.redirect_2top_authorize()
        except Exception, e:
            log.error('Login error, e=%s, request=%s' % (e, self.request.get_full_path()))
            return self.jump_limited_page('登录失败，请联系客服')


class LoginWeb(Login):

    def __init__(self, request):
        super(LoginWeb, self).__init__(request)
        self.oauth_view_type = 'web'
        self.visitor_from = 'web'
        self.main_port = settings.MAIN_PORT_WEB

        self.top_parameters = ''

    def check_is_oauth_and_result(self):
        return False, False, ''

    def check_parms_integrity(self):
        self.top_parameters = self.request.GET.get('top_parameters', '')
        self.top_access_token = self.request.GET.get('top_session', '')
        self.top_sign = urllib.unquote(self.request.GET['top_sign'])
        if self.top_parameters and self.top_access_token and self.top_sign \
                and self.request.GET.get('top_appkey', '') == self.app_key:
            self.top_parameters = urllib.unquote(self.top_parameters)
            param = base64.decodestring(self.top_parameters)
            self.top_dict = url_param_2dict(param) # TODO: top_dict中的过期时间、刷新令牌等信息，但没保存利用起来
            self.timestamp = int(self.top_dict['ts'])
            nick_bak = self.top_dict['visitor_nick']
            try:
                top_encode = self.request.GET.get('encode', 'gbk')
                if top_encode.lower() in ['utf-8', 'utf8']:
                    self.nick = nick_bak.decode('utf8')
                else:
                    self.nick = nick_bak.decode('gbk')
            except:
                try:
                    self.nick = nick_bak.decode('gbk')
                except:
                    self.nick = nick_bak
            return True
        else:
            return False

    def check_sign(self):
        m = hashlib.md5(self.app_key + self.top_parameters + self.top_access_token + self.app_secret)
        sign = base64.encodestring(m.digest()).strip()
        return sign == self.top_sign

    def redirect_2top_authorize(self):
        return HttpResponseRedirect(settings.WEB_AUTH_URL)


class LoginQnpc(Login):

    def __init__(self, request):
        super(LoginQnpc, self).__init__(request)
        self.oauth_view_type = 'web'
        self.visitor_from = 'qnpc'
        self.main_port = settings.MAIN_PORT_QNPC
        self.is_agent = ''

    def check_parms_integrity(self):
        self.top_sign = self.request.GET.get('sign', '')
        self.timestamp = self.request.GET.get('timestamp')
        old_nick = self.request.GET.get('nick', '')
        if self.top_sign and self.timestamp and old_nick\
                and self.request.GET.get('sessionkey', '') \
                and self.request.GET.get('from', '') == 'qianniupc'\
                and self.request.GET.get('appkey', '') == self.app_key:
            self.nick = old_nick.rsplit(':', 1)[0]
            self.is_agent = self.nick != old_nick
            self.timestamp = int(self.timestamp)
            return True
        else:
            return False

    def get_token(self):
        self.token = AccessToken.get_access_token(nick = self.nick)
        return self.token and True or False

    def check_timestamp(self):
        return True


class LoginQnyd(Login):

    def __init__(self, request):
        super(LoginQnyd, self).__init__(request)
        self.oauth_view_type = 'wap'
        self.visitor_from = 'qnyd'
        self.main_port = settings.MAIN_PORT_QNYD

    def check_parms_integrity(self):
        self.top_dict = json.loads(self.request.GET['authString'])
        self.top_sign = self.request.GET.get('sign')
        self.timestamp = self.request.GET.get('timestamp')
        if self.top_dict and self.top_sign and self.timestamp \
                and self.request.GET.get('from', '') in ('qianniuAndroid', 'qianniuIphone'):
            self.timestamp = int(self.timestamp)
            self.nick = urllib.unquote(self.top_dict['taobao_user_nick'].encode())
            self.top_access_token = self.top_dict['access_token']
            return True
        else:
            return False

    def check_timestamp(self):
        return True
