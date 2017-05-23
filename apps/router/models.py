# coding=UTF-8



# coding=UTF-8

import time
import math
import datetime
import httplib
import urllib

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

from apilib import TopError, get_tapi, tsapi
from apilib.app import QNApp

from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_mysql import execute_query_sql, bulk_insert_for_dict
from apps.common.utils.utils_datetime import date_2datetime, format_datetime, get_start_datetime, get_end_datetime, \
    datetime_2string, date_2datetime
from apps.common.utils.utils_misc import topObject_to_modelObject
from apps.common.cachekey import CacheKey
from apps.common.constant import Const
from apps.common.biz_utils.utils_permission import ORDER_VERSION_DICT, QN_ORDER_VERSION_DICT, BASE_CODE, normalize_perms_code
from apps.common.biz_utils.utils_misc import jl_sign_with_secret
from apps.common.utils.utils_sms import send_sms

class UserInfoTool(object):
    """仅用于用户登录的时候获取信息，涉及到user的创建与修改；一些关于user的其它方法，则直接挂在User下面了"""

    def __init__(self, nick, session):
        self.nick = nick
        self.session = session

    @property
    def tapi(self):
        if not hasattr(self, '_tapi'):
            self._tapi = QNApp.init_tapi(self.session)
        return self._tapi

    def test_api(self):
        return QNApp.test_api(self.tapi)

    def get_top_user(self):
        if not self.nick or not self.session:
            return None
        try:
            tobj = self.tapi.user_seller_get(nick = self.nick,
                                      fields = 'nick,type,user_id,sex,seller_credit')
            return tobj.user
        except TopError, e:
            log.error("get_top_user TopError, nick=%s, session=%s, e=%s" % (
                self.nick, self.session, e))
            return None

    def sync_top_user(self):
        top_user = self.get_top_user()
        if not top_user:
            return None

        user, is_new = User.objects.get_or_create(user_id = top_user.user_id)
        user.is_active = 1
        user.nick = top_user.nick
        user.shop_type = top_user.type
        user.level = top_user.seller_credit.level
        user.credit = top_user.seller_credit.score

        if is_new:
            user.session = "" # 千牛端新用户直接置空
            user.set_password(self.session)
        user.save()
        return user

    def get_user(self):
        if not hasattr(self, '_user'):
            try:
                user = User.objects.get(nick = self.nick)
                user.set_password(self.session) # 如果是千牛直接更新session
            except ObjectDoesNotExist:
                user = self.sync_top_user()
            self._user = user
        return self._user

    user = property(fget = get_user)

    def init_shop(self):
        success = True
        try:
            self.shop = Shop.objects.get(user = self.user)
        except ObjectDoesNotExist:
            self.shop = Shop(user = self.user)
            if not self.shop.sync_from_top(self.tapi):
                success = False
        finally:
            if success:
                self.user.shop_id = str(self.shop.sid)
                self.user.save()
            return success

class UserManager(BaseUserManager):
    def create_user(self, nick, session, platform):
        pass

    def create_superuser(self, **kwargs):
        pass

class User(AbstractBaseUser):
    """其实不用自增id是比较好的，但是这里为了数据迁移方便，还是作保留，并从旧表迁移"""
    user_id = models.BigIntegerField(verbose_name = "用户ID")
    nick = models.CharField(verbose_name = "用户名", max_length = 30, unique = True, db_index = True)
    shop_id = models.IntegerField(verbose_name = "店铺ID", db_index = True, blank = True, null = True)
    session = models.CharField(verbose_name = "开车精灵的session", max_length = 80)

    location = models.CharField(verbose_name = "所在城市", max_length = 30, null = True, blank = True)
    gender = models.IntegerField(verbose_name = "性别", null = True, blank = True)
    shop_type = models.CharField(verbose_name = "店铺类型", max_length = 30, blank = True, default = "C")
    date_joined = models.DateTimeField(verbose_name = '加入时间', default = datetime.datetime.now)
    reg_date = models.DateTimeField(verbose_name = "注册时间", null = True, blank = True)
    perms_code = models.CharField(verbose_name = '权限码', max_length = 30, blank = True)
    level = models.CharField(verbose_name = 'level', max_length = 4, default = '0')
    credit = models.IntegerField(verbose_name = 'credit', default = 0)

    is_staff = models.BooleanField(verbose_name = 'staff status', default = False)
    is_active = models.BooleanField(verbose_name = "是否有效", default = True)
    is_superuser = models.BooleanField(verbose_name = 'superuser status', default = False)
    select_count = models.IntegerField(verbose_name = '选词次数', blank = True, null = True, default = 0)
    subs_msg = models.BooleanField(verbose_name = '是否订阅消息', default = False)
    theme = models.CharField(verbose_name = '主题', max_length = 20, default = 'orange')

    objects = UserManager()

    USERNAME_FIELD = "nick"
    REQUIRED_FIELDS = []

    @property
    def customer(self):
        if not hasattr(self, '_customer') or self._customer is None:
            try:
                from apps.ncrm.models import Customer
                self._customer = Customer.objects.get(shop_id = self.shop_id)
            except:
                self._customer = None
        return self._customer

    def __unicode__(self):
        return '%s, %s' % (self.shop_id, self.nick)

    # ↓ 【WARNING】下面四个方法必须有
    def get_full_name(self):
        return self.nick

    def get_short_name(self):
        return self.nick

    def has_perm(self, perm, obj = None):
        if self.is_superuser:
            return True
        postfix = perm.rsplit('.', 1)[-1]
        if self.is_staff and not postfix.startswith("delete_"):
            return True
        return False

    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True
        if self.is_staff and app_label in ['web', ]:
            return True
        return False

    def login_remind_8email(self):
        subject = '掌柜 %s 刚刚登录了，去打个招呼吧。。。O(∩_∩)O~    %s' % (
            self.nick, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        content = '开车精灵系统自动提醒邮件，勿回复。'
        try:
            from apps.ncrm.models import Customer
#             shop_id = int(self.shop_id)
#             consult, _, _, _ = Customer.get_or_create_servers([shop_id], category = "kcjl").get(shop_id, [None, None, None, None]) # [consult, rjjh, tp, department]
            consult = Customer.objects.select_related('consult').get(shop_id = self.shop_id).consult
            if consult:
                cc_list = ['%s@paithink.com' % consult.name]
                send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, cc_list)
        except Exception, e:
            log.error('login_remind_8email error, shop_id=%s, e=%s' % (self.shop_id, e))

    def calc_perms_code(self, perms_code = ""): # 根据额外权限码计算整体的权限码，默认只计算自己的
        if not perms_code:
            perms_code = self.perms_code

        try:
            if perms_code != '': # 权限码为空时，额外权限码不得凭空增加
                ap = self.additionalpermission
                if ap.effective:
                    perms_code = normalize_perms_code([perms_code, ap.perms_code])
        except ObjectDoesNotExist:
            pass
        return perms_code

    def get_left_days(self):
        '''获取用户的剩余天数，负数：已过期n天；0：当天过或订购想不存在；正数：还有n天过期'''
        newest_version = ArticleUserSubscribe.get_newest_version(self)
        deadline = (newest_version and newest_version.deadline or None)
        self.left_days = (deadline and (deadline - datetime.datetime.now()).days or 0)
        return self.left_days

    def get_subport(self, force_create = False):
        return NickPort.get_port_domain(nick = self.nick, force_create = force_create)

    def get_backend_url(self, user_type = "", psuser_name = "", next_url = "", visitor_from=""):

        def _create_login_url(domain, base_parm_dict, visitor_from):
            import copy
            sign_dict = copy.deepcopy(base_parm_dict)
            sign_dict.update({'visitor_from': visitor_from})
            jl_sign_with_secret(sign_dict)
            return u'%s%s?%s' % (domain, reverse('backend_login'), urllib.urlencode(sign_dict))

        try:
            # user = User.objects.get(shop_id = self.shop_id)
            # if BASE_CODE not in self.perms_code: # TODO: wangqi 权限码只处理两件事情，perms_code + 额外权限码汇总
            if BASE_CODE not in self.calc_perms_code():
                raise Exception("no permission")
            session, _ = QNApp.get_session(shop_id = self.shop_id)
            if not session:
                raise Exception("no session")
            domain = u'http://%s' % self.get_subport(force_create = True)
            base_parm_dict = {'nick': self.nick, 'shop_id': self.shop_id, 'session': session,
                         'user_type': user_type, 'psuser_name': psuser_name, 'next_url': next_url,
                         'visitor_from': ''}
            url_dict = {vf + '_url': _create_login_url(domain, base_parm_dict, vf) for vf in ['web', 'qnpc', 'qnyd']}
            return url_dict
        except Exception, e:
            log.error("get backend login url error, shop_id=%s, e=%s" % (self.shop_id, e))
            return {vf + '_url': '' for vf in ['web', 'qnpc', 'qnyd']}

    def gen_sale_link(self, param_str):
        '''获取该用户的优惠订购链接'''
        tapi = get_tapi(self) # 目前只有web版有优惠链接？
        try:
            top_obj = tapi.fuwu_sale_link_gen(nick = self.nick, param_str = param_str)
            if top_obj and hasattr(top_obj, 'url'):
                return top_obj.url
        except Exception, e:
            log.exception('fuwu_sale_link_gen, nick=%s, e=%s' % (self.nick, e))
            return ''

    def get_subs_msg_status(self):
        def save(self, subs_msg = True):
            self.subs_msg = subs_msg
            self.save()
        try:
            if self.subs_msg:
                return True
            else :
                if User.check_user_jushita(self.nick):
                    save(self)
                    return True
                else:
                    if ArticleUserSubscribe.get_newest_version(self):
                        if  User.add_user_jushita(self.shop_id):
                            save(self)
                        return False
        except Exception, e:
            log.error('get user error = %s and shop_id = %s' % (e, self.shop_id))
        return True

    def sync_perms_code(self):
        valid_item_list = ArticleUserSubscribe.get_valid_item_list(self, sync_from_top = True)
        perms_code_list = ArticleItem.compute_permission(valid_item_list)
        perms_code = normalize_perms_code(perms_code_list)
        if perms_code != self.perms_code:
            self.perms_code = perms_code
            self.save()
        return self.calc_perms_code(perms_code)

#     def sync_user_shop_type(self, platform):
#         tapi = Application(platform).get_tapi(self.shop_id)
#         top_user = tapi.user_seller_get(fields = 'type')
#         if hasattr(top_user, 'user'):
#             if self.shop_type != top_user.user.type:
#                 self.shop_type = top_user.user.type
#                 self.save()

    @classmethod
    def get_shopid_or_nick(cls, nick_or_shop_id):
        # 先从缓存内取
        cache_key = CacheKey.ROUTER_GET_NICK_OR_SHOP_ID % nick_or_shop_id
        result = CacheAdpter.get(cache_key, 'web', None)
        if not result:
            try:
                if type(nick_or_shop_id) is int:
                    user = cls.objects.get(shop_id = nick_or_shop_id)
                else:
                    user = cls.objects.only('nick', 'shop_id').get(nick = nick_or_shop_id)
                if user.shop_id == nick_or_shop_id:
                    result = user.nick
                else:
                    result = user.shop_id
                CacheAdpter.set(cache_key, result, 'web', 24 * 60 * 60 * 15)
            except Exception, e:
                log.error("can not get user , cause by the user has be expired and the nick_or_shop_id=%s and the error=%s" % (nick_or_shop_id, e))
        return result

    @classmethod
    def check_user_jushita(cls, nick):
        tobj = tsapi.simba_jshita_jms_user_get(user_nick = nick)
        if hasattr(tobj, 'ons_user'):
            if hasattr(tobj.ons_user, 'is_valid'):
                return True
        return False

    @classmethod
    def delete_user_jushita(cls, nick):
        tobj = tsapi.simba_jshita_jms_user_delete(user_nick = nick)
        if tobj.is_success:
            return True
        return False

    @classmethod
    def add_user_jushita(cls, shop_id):
        tapi = QNApp.get_tapi(shop_id)
        tobj = tapi.simba_jshita_jms_user_add()
        if tobj.is_success:
            return True
        return False

class Port(models.Model):
    domain = models.CharField(verbose_name = "域名", max_length = 50, null = True, default = '')
    back_domain = models.CharField(verbose_name = "备用域名", max_length = 50, null = True,
                                   default = None) # 当这个不为空时，说明当前服务器有问题，将它分流给其它服务器即可
    now_load = models.IntegerField(verbose_name = "当前服务期内用户数", default = 1)
    max_load = models.IntegerField(verbose_name = "最大服务期内用户数", null = True)
    all_load = models.IntegerField(verbose_name = "总负载量", null = True)
    type = models.CharField(verbose_name = "类型", max_length = 10, null = True, default = '') # router、web、kwlib
    note = models.CharField(verbose_name = "备注", max_length = 100, null = True, default = '')

    class Meta:
        ordering = ['now_load', ]

    def __str__(self):
        return '%s' % (self.domain)

    def get_valid_domain(self):
        """获取有效的域名，当备用域名不为空时，采用备用域名，否则采用正常域名"""
        return (not self.back_domain) and self.domain or self.back_domain

class NickPort(models.Model):
    nick = models.CharField(verbose_name = "卖家昵称", max_length = 30, primary_key = True)
    port = models.ForeignKey(Port, null = True)

    @staticmethod
    def allocate_port():
        """分配服务器"""
        port_list = Port.objects.filter(type = 'web').extra(select = {'can_add': 'max_load - now_load'},
                                                            order_by = ['-can_add', 'now_load'])
        if not port_list:
            raise Exception("亲，请联系开车精灵的顾问，无法给您分配服务器！")
        else:
            port = port_list[0]
            port.now_load += 1
            port.save()
            return port

    @staticmethod
    def get_port_domain(nick, force_create = False):
        """获取对应的服务器域名，如果没有数据，就要强制创建"""
        np_list = NickPort.objects.filter(nick = nick)
        if np_list:
            return np_list[0].port.get_valid_domain()
        else:
            if force_create:
                np = NickPort(nick = nick)
                np.port = NickPort.allocate_port()
                np.save()
                return np.port.get_valid_domain()
            else:
                return ''

class Shop(models.Model):
    user = models.OneToOneField(User)
    sid = models.BigIntegerField(verbose_name = "店铺编号 ", null = False, primary_key = True)
    cid = models.BigIntegerField(verbose_name = "店铺所属的类目编号", null = False, default = 0)
    nick = models.CharField(verbose_name = "卖家昵称", max_length = 30, null = False, db_index = True)
    title = models.CharField(verbose_name = "店铺标题", max_length = 128, null = True)
    pic_path = models.CharField(verbose_name = "店标地址", max_length = 255, null = True)
    item_score = models.CharField(verbose_name = "商品描述评分", max_length = 10, null = True)
    service_score = models.CharField(verbose_name = "服务态度评分", max_length = 10, null = True)
    delivery_score = models.CharField(verbose_name = "发货速度评分", max_length = 10, null = True)
    created = models.DateTimeField(verbose_name = "开店时间", null = True)

    def __str__(self):
        return '%s,%s' % (self.nick, self.sid)

    def sync_from_top(self, tapi):
        try:
            tobj = tapi.shop_get(nick = self.user.nick, fields = 'sid, nick, title, pic_path, created, shop_score')
            top_shop = tobj.shop
        except TopError, e:
            log.error("shop_get TopError, nick=%s, e=%s" % (self.user.nick, e))
            return False

        topObject_to_modelObject(Shop, top_shop, self)
        shop_score = tobj.shop.shop_score
        self.pic_path = tobj.shop.pic_path
        self.title = tobj.shop.title
        self.item_score = shop_score.item_score
        self.service_score = shop_score.service_score
        self.delivery_score = shop_score.delivery_score
        self.save()
        return True

class AccessToken(models.Model):
    '''记录OAuth2.0的用户授权token信息，今后可能把Web的授权机制也改为OAuth2.0，故可能同一用户存在多条记录'''
    uid = models.BigIntegerField(verbose_name = "用户ID", null = False, default = 0, db_index = True)
    nick = models.CharField(verbose_name = "卖家昵称", max_length = 30, null = False, db_index = True)
    platform = models.CharField(verbose_name = "Token对应平台", max_length = 10, null = False, default = 'web') # qn 千牛；web Web
    access_token = models.CharField(verbose_name = "授权Token", max_length = 75, null = False) # 授权的access_token
    refresh_token = models.CharField(verbose_name = "刷新Token", max_length = 75, null = True) # 用于刷新过期的access_token
    create_time = models.DateTimeField(verbose_name = "Token创建时间", default = datetime.datetime.now)
    expire_time = models.DateTimeField(verbose_name = "Token过期时间", default = datetime.datetime.now)

    def __str__(self):
        return '%s, %s' % (self.uid, self.nick)

    @staticmethod
    def get_access_token(**kwargs):
        '''获取用户的access_token对象'''
        token, token_objs = None, None
        try:
            if kwargs.has_key('uid'):
                token_objs = AccessToken.objects.filter(uid = kwargs['uid'], platform = 'web').order_by('-create_time')
            elif kwargs.has_key('nick'):
                token_objs = AccessToken.objects.filter(nick = kwargs['nick'], platform = 'web').order_by('-create_time')
            if token_objs:
                token = token_objs[0]
                now_time = datetime.datetime.now()
                if token.expire_time <= now_time: # session 过期
                    count = ArticleUserSubscribe.objects.filter(nick = token.nick, deadline__gt = now_time, \
                                                                article_code = settings.APP_ARTICLE_CODE).count()
                    if count > 0: # 存在有效订单
                        token = AccessToken.refresh_access_token(token)
                    else:
                        AccessToken.objects.filter(nick = kwargs['nick'], platform = 'web').delete()
                        token = None
        except Exception:
            return None
        return token

    @staticmethod
    def process_top_data(top_dict):
        # 如有新的需求，该方法重构
        expire_mark = 'expires_in'
        user_nick_mark = 'taobao_user_nick'

        if top_dict:
            if expire_mark in top_dict:
                try:
                    expire_time = datetime.datetime.now() + \
                                  datetime.timedelta(seconds = int(top_dict[expire_mark]))
                    top_dict['expire_time'] = expire_time
                except ValueError, e:
                    log.error('type convert error, e=%s' % (e))
                    return {}

            if user_nick_mark in top_dict:
                try:
                    top_dict[user_nick_mark] = urllib.unquote(str(top_dict[user_nick_mark]))
                except Exception, e:
                    log.error('user_nick to unquote error, e=%s' % (e))
                    return {}

            return top_dict
        return {}

    @staticmethod
    def sync_access_token(code):
        '''同步用户的access_token'''
        url_params = urllib.urlencode({
            "code": code,
            "grant_type": "authorization_code",
            "client_id": settings.APP_KEY,
            "client_secret": settings.APP_SECRET,
            "redirect_uri": settings.MAIN_PORT_WEB
            })
        top_dict = AccessToken.sync_from_top(url_params)
        token_dict = AccessToken.process_top_data(top_dict)

        token = None
        if token_dict:
            try:
                token = AccessToken()
                token.uid = long(token_dict['taobao_user_id'])
                token.nick = token_dict['taobao_user_nick']
                token.access_token = token_dict['access_token']
                token.refresh_token = token_dict['refresh_token']
                token.create_time = datetime.datetime.now()
                token.expire_time = token_dict['expire_time']
                token.platform = 'web'
                AccessToken.objects.filter(nick=token.nick, platform=token.platform).delete()
                token.save()
            except Exception, e:
                log.error('save token error , token_dict=%s, e=%s' % (token_dict, e))
                token = None
        return token

    @staticmethod
    def refresh_access_token(token):
        '''刷新用户的access_token，用于access_token过期后重新授权'''
        if token:
            url_params = urllib.urlencode({"grant_type": "refresh_token",
                                           "client_id": settings.APP_KEY,
                                           "client_secret": settings.APP_SECRET,
                                           "refresh_token": token.refresh_token})
            top_dict = AccessToken.sync_from_top(url_params)
            token_dict = AccessToken.process_top_data(top_dict)

            if token_dict:
                token.access_token = token_dict['access_token']
                token.refresh_token = token_dict['refresh_token']
                token.expire_time = token_dict['expire_time']
                token.save()
                return token
            else:
                token.delete()
                return None
        else:
            log.error('User have no token')
            return None

    @staticmethod
    def sync_from_top(url_params, host = 'oauth.taobao.com', method = 'POST', url = '/token', secure = True):
        '''同步淘宝的access_token对象'''
        resp = {}
        retries_performed = 0
        error_info = ''
        while retries_performed < settings.TAPI_RETRY_COUNT + 1:
            conn = (secure and httplib.HTTPSConnection(host) or httplib.HTTPConnection(host))
            try:
                if method == 'POST':
                    conn.request('POST', url,
                                 headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/html",
                                            "User-Agent": "python"}, body = url_params)
                elif method == 'GET':
                    conn.request('GET', '%s?%s' % (url, url_params),
                                 headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/html",
                                            "User-Agent": "python"})
                else:
                    break
                resp = conn.getresponse()
            except Exception, e:
                log.error('Failed to send request, retries_performed=%s, retry_delay=%s, e=%s' % (
                    retries_performed, settings.TAPI_RETRY_DELAY, e))
                time.sleep(settings.TAPI_RETRY_DELAY)
                retries_performed += 1
                continue

            if resp.status == 200:
                break

            error_info = resp.read()
            time.sleep(settings.TAPI_RETRY_DELAY)
            retries_performed += 1

        try:
            body = resp.read()
            conn.close()
        except Exception, e:
            conn.close()
            return {}

        if resp.status != 200:
            log.error(
                "API response error, status code=%s, len(body)=%s, info=%s" % (resp.status, len(body), error_info))
            return {}

        try:
            return json.loads(body)
        except Exception, e:
            log.error('Parse body to json error, body=%s' % body)
            return {}

    def test_api(cls, nick, tapi):
        is_valid, reason = QNApp.test_api(tapi)
        if not is_valid and reason == 'session过期':
            token = AccessToken.objects.filter(nick = nick, platform = 'web').order_by('-create_time')[0]
            is_valid = AccessToken.refresh_access_token(token)
        return is_valid


class ArticleItem(models.Model):
    '''我们定义的收费项目的配置,这里主要用于权限判断及更改'''
    article_name = models.CharField(verbose_name = "应用名称", max_length = 30, null = True)
    article_code = models.CharField(verbose_name = "应用收费代码", max_length = 30)
    item_name = models.CharField(verbose_name = "收费项目名称", max_length = 30, null = True, blank = True)
    item_code = models.CharField(verbose_name = "收费项目代码", max_length = 30)
    perms_code = models.CharField(verbose_name = "权限码", max_length = 50, null = True)
    note = models.CharField(verbose_name = "说明", max_length = 500, null = True, blank = True)

    cache_key = CacheKey.ROUTER_ARTICLE_ITEM_CACHE

    @classmethod
    def refresh_item_dict(cls):
        """刷新配置"""
        CacheAdpter.delete(cls.cache_key, 'web')

    @classmethod
    def get_articleitem_dict(cls):
        cached_dict = CacheAdpter.get(cls.cache_key, 'web', None)
        if not cached_dict:
            cached_dict = {}
            ai_list = cls.objects.all()
            for ai in ai_list:
                cached_dict.update({ai.item_code: ai.perms_code})
            CacheAdpter.set(cls.cache_key, cached_dict, 'web', 60 * 60 * 24)
        return cached_dict

    @classmethod
    def compute_permission(cls, valid_item_list):
        articleitem_dict = cls.get_articleitem_dict()
        perms_code_list = []
        for aus in valid_item_list:
            perms_code_list.append(articleitem_dict.get(aus.item_code, ''))
        return perms_code_list

class OrderSyncer(models.Model):
    """订单/订购关系同步模型"""
    article_code = models.CharField(verbose_name = "订购码", max_length = 30, db_index = True)
    article_name = models.CharField(verbose_name = "应用名称", max_length = 30)
    claw_time = models.DateTimeField(verbose_name = "爬取订单时间", default = datetime.datetime.now)
    sync_order_time = models.DateTimeField(verbose_name = "同步订单时间", default = datetime.datetime.now)

    @classmethod
    def init_data(cls):
        init_list = [{'article_code': 'ts-25811', 'article_name': '开车精灵', 'claw_time': datetime.datetime.now(),
                      'sync_order_time': datetime.datetime.now()},
                     {'article_code': 'FW_GOODS-1921400', 'article_name': '无线精灵', 'claw_time': datetime.datetime.now(),
                      'sync_order_time': datetime.datetime.now()}
                     ]

        table_name = cls._meta.db_table
        field_list = [field.name for field in cls._meta.fields]
        try:
            field_list.remove('id')
        except:
            pass
        bulk_insert_for_dict(table_name, init_list, field_list)

    def claw_order_list(self):
        """fuwu.taobao.com爬取订单"""

        def get_response(url):
            """发送请求"""
            from urllib2 import urlopen
            try:
                f = urlopen(url)
                content = f.read()
                f.close()
                return content
            except Exception, e:
                print 'get response with url=%s error, e=%s' % (url, e)
                if locals().get('f', None):
                    f.close()
                return None

        def get_end_index(data_list, sync_time):
            """根据时间取出列表中的指定位置"""
            if (data_list[-1]['pay_time']) >= sync_time:
                return len(data_list)
            else:
                for index, value in enumerate(data_list):
                    if value['pay_time'] <= sync_time:
                        return index

        def parse_clawed_data(s, article_code):
            import ast
            from pyquery import PyQuery as pq
            result_dict = {}

            replace_list = ['currentPage', 'pageCount', 'data', 'rateNum', 'planUrl', 'rateSum', 'isB2CSeller', 'nick',
                            'deadline', 'version', 'isTryoutSubed', 'isPlanSubed', 'payTime']
            json_str = s.decode('utf-8').lstrip()
            for place_word in replace_list:
                json_str = json_str.replace(place_word, '"%s"' % place_word)
            try:
                result = ast.literal_eval(json_str)
            except Exception: # 取值错误，这里可能有新增的key或者带标点符号？
                log.error("parse clawed txt error, txt=%s" % s)
            result_dict = {'page_no': result['currentPage'], 'page_count': result['pageCount']}
            data_list = []
            keys = result['data'][0].keys()
            # {rateNum:'1_2',rateSum:'1_2',isB2CSeller:'0',nick:'聚**屋',deadline:'3个月',version:'双引擎_季度限时特惠',isPlanSubed:'0',isTryoutSubed:0,payTime:'2014-09-26 10:53:57'}
            for order_data in result['data']:
                temp_dict = {key: order_data.get(key, None) for key in keys}
                # <font title="爱时裳风" >爱时裳风</font> ↓↓ 解决这种特例
                nick = pq(temp_dict['nick'].decode('utf-8'))
                nick = nick.is_('font') and nick.attr('title') or nick.text()

                data_list.append({'pay_time': datetime.datetime.strptime(temp_dict['payTime'], '%Y-%m-%d %H:%M:%S'),
                                  'deadline': temp_dict['deadline'].decode('utf-8'),
                                  'nick': nick,
                                  'version': temp_dict['version'].decode('utf-8'),
                                  'is_b2c_seller': int(temp_dict['isB2CSeller']),
                                  'is_plan_subed': int(temp_dict['isPlanSubed']),
                                  'is_tryout_subed': int(temp_dict['isTryoutSubed']),
                                  'article_code': article_code,
                                  'rate_sum': temp_dict['rateSum'],
                                  'rate_num': temp_dict['rateNum']
                                  })

            result_dict.update({'data_list': data_list})
            return result_dict

        order_list = []
        claw_url = 'http://fuwu.taobao.com/serv/rencSubscList.do?serviceCode=%s&currentPage=%s&pageCount=%s'
        for i in range(1, 16):
            try_count = 0
            while try_count < 3:
                try_count += 1
                content = get_response(claw_url % (self.article_code, i, i))
                if not content:
                    time.sleep(10)
                else:
                    break

            if not content:
                raise Exception('claw failed on %s, page=%s' % (self.article_code, i))
            page_data = parse_clawed_data(content, self.article_code)
            data_list = page_data['data_list']
            end_index = get_end_index(data_list, self.claw_time)
            if end_index < 0:
                end_index = 0
            order_list.extend(data_list[:end_index])
            if end_index != len(data_list):
                break
            time.sleep(2)

        if order_list:
            sync_time = order_list[0]['pay_time']
            insert_count = ClawOrder.insert_order_list(order_list = order_list, sync_time = self.claw_time,
                                                       article_code = self.article_code)
            return insert_count, sync_time
        else:
            return 0, ''

    def sync_bizorder_bynick(self, nick_list):
        from apps.ncrm.models import Subscribe

        def get_bizorder_list(page_size, nick_list, article_code):
            result_list = []
            for nick in nick_list:
                while True:
                    try:
                        tobjs = tapi.vas_order_search(nick = nick, page_size = page_size, article_code = article_code)
                        if hasattr(tobjs,
                                   'article_biz_orders') and tobjs.article_biz_orders and tobjs.article_biz_orders.article_biz_order:
                            result_list.extend(tobjs.article_biz_orders.article_biz_order)
                        break
                    except TopError, e:
                        log.error("vas_order_search TopError, nick_list=%s, e=%s" % (nick_list, e))
                        if 'accesscontrol.limited-by-api-access-count' in str(e):
                            time.sleep(10)
                            continue
                        else:
                            break
            return result_list

        tapi = QNApp.init_tapi(None)

        top_abo_list = []
        default_page_size = 200
        order_list = get_bizorder_list(default_page_size, nick_list, self.article_code)
        top_abo_list.extend(order_list)

        #         Subscribe.save_soft_subscribe_bynicks(top_abo_list, self.article_code, nick_list)
        log.info('sync_bizorder_bynick, order_id_list=%s' % (json.dumps([order.order_id for order in top_abo_list])))
        Subscribe.save_soft_subscribe(top_abo_list)
        return top_abo_list

    def sync_bizorder(self, start_time, end_time):
        """调用接口从淘宝同步订单数据"""
        from apps.ncrm.models import Subscribe

        def get_bizorder_list(page_no, page_size, start_time, end_time, article_code):
            result_list = []
            total_count = 0
            while True:
                try:
                    tobjs = tapi.vas_order_search(start_created = str(start_time - datetime.timedelta(hours = 12))[:19],
                                                  end_created = str(end_time)[:19], page_size = page_size,
                                                  page_no = page_no, article_code = article_code)
                    if hasattr(tobjs, 'article_biz_orders') and tobjs.article_biz_orders and tobjs.article_biz_orders.article_biz_order:
                        result_list.extend(tobjs.article_biz_orders.article_biz_order)
                    if page_no == 1:
                        total_count = tobjs.total_item
                    return result_list, total_count
                except TopError, e:
                    log.error(
                        "vas_order_search TopError, start_created=%s, end_created=%s, e=%s" % (start_time, end_time, e))
                    if 'accesscontrol.limited-by-api-access-count' in str(e):
                        time.sleep(10)
                        continue
                    else:
                        return result_list, total_count

        tapi = QNApp.init_tapi(None)

        top_abo_list = []
        default_page_size = 200
        order_list, total_count = get_bizorder_list(1, default_page_size, start_time, end_time, self.article_code)
        top_abo_list.extend(order_list)
        page_count = int(math.ceil(total_count / float(default_page_size)))
        for i in range(2, page_count + 1):
            order_list, _ = get_bizorder_list(i, default_page_size, start_time, end_time, self.article_code)
            top_abo_list.extend(order_list)

        # Subscribe.save_soft_subscribe(top_abo_list, start_time, end_time, self.article_code)
        log.info('sync_bizorder, order_id_list=%s' % (json.dumps([order.order_id for order in top_abo_list])))
        Subscribe.save_soft_subscribe(top_abo_list)
        return len(top_abo_list)

    @classmethod
    def sync_order(cls):
        syncer_list = cls.objects.all()
        if not syncer_list:
            cls.init_data()
            syncer_list = cls.objects.all()

        for syncer in syncer_list:
            try:
                log.info('【%s】clawing orders, start time=%s' % (syncer.article_code, syncer.claw_time))
                clawer_count, claw_time = syncer.claw_order_list()
                log.info('【%s】clawed %s orders, claw time in (%s, %s)' % (
                    syncer.article_code, clawer_count, syncer.claw_time, claw_time))
                if clawer_count: # TODO: wangqi 20141010 可能出现爬取成功，订单同步失败的问题，需要解决
                    syncer.claw_time = claw_time
                    log.info('【%s】syncing orders, sync time in (%s, %s)' % (
                        syncer.article_code, syncer.sync_order_time, claw_time))
                    sync_count = syncer.sync_bizorder(start_time = syncer.sync_order_time, end_time = syncer.claw_time)
                    log.info('【%s】synced %s orders, sync time in (%s, %s)' % (
                        syncer.article_code, sync_count, syncer.sync_order_time, claw_time))
                    syncer.sync_order_time = claw_time
                    syncer.save()
            except Exception, e:
                log.error('【%s】sync order error, sync time in (%s, --), e=%s' % (
                    syncer.article_code, syncer.sync_order_time, e))

class ClawOrder(models.Model):
    """fuwu.taobao.com后台爬取的订单"""
    is_plan_subed = models.IntegerField()
    is_tryout_subed = models.IntegerField()
    is_b2c_seller = models.IntegerField(verbose_name = "是否天猫卖家")
    nick = models.CharField(verbose_name = "淘宝会员ID", max_length = 30)
    deadline = models.CharField(verbose_name = "订购周期", max_length = 50)
    article_code = models.CharField(verbose_name = "订购码", max_length = 30)
    rate_sum = models.CharField(max_length = 30)
    rate_num = models.CharField(max_length = 30)
    pay_time = models.DateTimeField(verbose_name = "订购时间")

    @classmethod
    def insert_order_list(cls, order_list, sync_time, article_code):
        cls.objects.filter(article_code = article_code, pay_time__gt = sync_time).delete()
        table_name = cls._meta.db_table
        field_list = [field.name for field in cls._meta.fields]
        try:
            field_list.remove('id')
        except:
            pass
        return bulk_insert_for_dict(table_name, order_list, field_list)

class ArticleUserSubscribe(models.Model):
    '''用户与收费项目的订购关系，主要用于程序判断'''
    # TODO: wangqi 20141016 订购关系的详细数据是否必要？
    nick = models.CharField(verbose_name = "淘宝会员名", max_length = 30, null = True, db_index = True)
    article_code = models.CharField(verbose_name = "应用收费代码", max_length = 30, null = True)
    item_code = models.CharField(verbose_name = "收费项目代码", max_length = 30, null = True, help_text = '如：ts-123-1')
    deadline = models.DateTimeField(verbose_name = "订购周期结束时间", null = True)

    @property
    def version_no(self):
        if not hasattr(self, '_version_no'):
            result = ORDER_VERSION_DICT.get(self.item_code, [])
            self._version_no = result and result[0] or 0
        return self._version_no

    @classmethod
    def check_is_usable(cls, nick, item_code):
        now_version_no = cls.get_highest_version(nick = nick)
        new_version_no = ORDER_VERSION_DICT[item_code][0]
        return new_version_no >= now_version_no

    @classmethod
    def check_expiry_date(cls):
        """ 检查用户订购的过期时间，对于3天后到期的，需要发送提醒短信和软件消息 """
        try:
            from apps.ncrm.models import Customer
            from apps.ncrm.models import PrivateMessage

            today = datetime.date.today()
            days_3after = date_2datetime(today + datetime.timedelta(days=3))
            # 找出3天后过期的订单
            subscribe_list = cls.objects.filter(article_code=settings.APP_ARTICLE_CODE, deadline=days_3after)
            if subscribe_list:
                # 过滤掉已续费的用户
                nick_list = [subscribe.nick for subscribe in subscribe_list]
                temp_subscribe_list = cls.objects.filter(article_code=settings.APP_ARTICLE_CODE, nick__in=nick_list, deadline__gt=days_3after)
                for subscribe in temp_subscribe_list:
                    if subscribe.nick in nick_list:
                        nick_list.remove(subscribe.nick)

                message = "%s尊敬的%s，您的开车精灵软件将于3天后到期，过期后软件推广和自动抢排名" \
                                  "设置将被清空，请尽快续费以免影响账户推广。"

                customer_list = Customer.objects.filter(nick__in=nick_list)
                start_time = datetime.datetime.now()
                end_time = start_time + datetime.timedelta(3)
                for customer in customer_list:
                    # 发送软件消息
                    message_2ztcjl = message % ('', customer.nick)
                    try:
                        PrivateMessage.send_message(shop_id=customer.shop_id, title="软件到期提醒",
                                                    content=message_2ztcjl, app_id=12612063,
                                                    level='alert', start_time=start_time, end_time=end_time)
                    except Exception, e:
                        log.error('check_expiry_date task send_message 2 error, shop_id=%s, e=%s' % (customer.shop_id, e))

                    if customer.phone:
                        # 如果有手机号，还需要发送信息
                        message_2phone = message % ('【开车精灵】', customer.nick)
                        result = send_sms([customer.phone], message_2phone)
                        if 'code' not in result or result['code'] != 0:
                            log.info('check_expiry_date task send_sms error, shop_id=%s, e=网络或者短信平台出问题' % customer.shop_id)
        except Exception, e:
            log.info('check_expiry_date task error, e=%s' % e)

    @staticmethod
    def get_newest_version(user):
        '''获取用户当前APP下的最新版本'''
        try:
            aus_list = ArticleUserSubscribe.objects.filter(nick = user.nick, article_code = settings.APP_ARTICLE_CODE).order_by('-deadline')
            result = (aus_list and aus_list[0] or None)
        except Exception, e:
            log.exception('nick=%s, e=%s' % (user.nick, e))
            return None
        return result

    @staticmethod
    def get_highest_version(nick = ''):
        '''获取用户正在使用的最高版本'''
        # TODO:yangrongkai 此处暂不考虑通过 ncrm_subscribe 进行控制, 仍用订购关系处理，2014/12/27
        try:
            aus_list = ArticleUserSubscribe.objects.filter(
                nick = nick,
                article_code = settings.APP_ARTICLE_CODE,
                deadline__gt = date_2datetime(datetime.date.today()))
            highest_version = 0
            for aus in aus_list:
                if aus.version_no > highest_version:
                    highest_version = aus.version_no
        except Exception, e:
            log.exception('nick=%s, e=%s' % (nick, e))
            return 0
        return highest_version

    @classmethod
    def get_hightest_item_code(cls, nick = ''):
        """获取用户当前版本号"""
        highest_version = cls.get_highest_version(nick = nick)
        item_code = 'ts-25811-3'
        vaild_dict = ORDER_VERSION_DICT
        for code, desc in vaild_dict.items():
            if highest_version == desc[0]:
                item_code = code
                break
        return item_code

    @classmethod
    def get_valid_item_list(cls, user, sync_from_top = False):
        '''获取用户的收费项目订单，包含多个APP的数据，如Web和千牛'''
        cls.sync_aus_byuser(user)
        return cls.objects.filter(nick = user.nick, deadline__gt = datetime.date.today(), article_code = settings.APP_ARTICLE_CODE)

    @staticmethod
    def sync_aus_byuser(user, tapi = None):
        '''只同步当前APP下的收费项目'''
        if not tapi:
            tapi = get_tapi(user)

        if not tapi:
            log.warn('cannot get tapi: shop_id=%s' % user.shop_id)
            return []

        # 根据不同平台获取不同的ARTICLE_CODE
        article_code = settings.APP_ARTICLE_CODE

        try:
            tobjs = tapi.vas_subscribe_get(nick = user.nick, article_code = article_code)
        except TopError, e:
            log.error("vas_subscribe_get TopError, nick=%s, e=%s" % (user.nick, e))
            return []

        exist_aus_list = ArticleUserSubscribe.objects.filter(nick = user.nick,
                                                             article_code = article_code).order_by('deadline')
        aus_dict = {}
        for eas in exist_aus_list:
            aus_dict[eas.item_code] = eas
#         aus_list = []

        if tobjs.article_user_subscribes:
            new_aus_dict = {tobj.item_code:tobj for tobj in tobjs.article_user_subscribes.article_user_subscribe}
            for item_code, tobj in new_aus_dict.items():
                tobj.deadline = datetime.datetime.strptime(tobj.deadline, '%Y-%m-%d %H:%M:%S')
                if item_code in aus_dict:
                    aus = aus_dict[item_code]
                    if aus.deadline != tobj.deadline:
                        aus.deadline = tobj.deadline
                        aus.save()
                else:
                    aus = ArticleUserSubscribe()
                    topObject_to_modelObject(ArticleUserSubscribe, tobj, aus)
                    aus.article_code = article_code
                    aus.nick = user.nick
                    aus.save()
                aus_dict[item_code] = aus
            for item_code, aus in aus_dict.items():
                if item_code not in new_aus_dict:
                    aus.delete()
                    del aus_dict[item_code]
        else:
            if user.subs_msg:
                if User.delete_user_jushita(user.nick):
                    user.subs_msg = 0
                    user.save()
        return aus_dict.values()


#             for tobj in tobjs.article_user_subscribes.article_user_subscribe:
#                 if not aus_dict.has_key(tobj.item_code):
#                     aus = ArticleUserSubscribe()
#                     aus_dict[tobj.item_code] = aus
#                 else:
#                     aus = aus_dict[tobj.item_code]
#                 topObject_to_modelObject(ArticleUserSubscribe, tobj, aus)
#                 aus.article_code = article_code
#                 aus.nick = user.nick
#                 aus.status = 1 # 从top拿到的aus都是有效的
#                 aus.save() # TODO: zhangyu 20140323 应该可以对比article_code、item_code、deadline，相同则不再save
#                 aus_list.append(aus)
#         return aus_list

class Agent(models.Model):
    principal = models.ForeignKey(User, related_name = 'principal') # 委托人，即店铺主旺旺
    name = models.CharField(verbose_name = '用户名', max_length = 30) # 掌柜指定的代理人，必须是存在的淘宝旺旺号
    password = models.CharField(verbose_name = '密码', max_length = 128) # 掌柜指定的代理人登陆密码
    last_modified = models.DateTimeField(auto_now = True)

    class Meta:
        unique_together = ('principal', 'name')

class AdditionalPermission(models.Model):
    user = models.OneToOneField(User)
    perms_code = models.CharField(verbose_name = "权限码", max_length = 30, default = "", blank = True)
    effectline = models.DateTimeField(verbose_name = "开始生效时间", default = datetime.datetime.now)
    deadline = models.DateTimeField(verbose_name = "有效期结束时间", null = True, blank = True)
    last_modified = models.DateTimeField(auto_now = True)

    @property
    def effective(self):
        now_time = datetime.datetime.now()
        if self.deadline and self.effectline >= self.deadline:
            return False
        if self.effectline <= now_time:
            if not self.deadline or self.deadline >= now_time:
                return True
        return False

# class LotteryInfo(models.Model):
#     reminder_flag = models.BooleanField(verbose_name = "提醒标识", choices = ((True, '不需要提醒'), (False, '需要提醒')),
#                                         default = False)
#     exec_model = models.IntegerField(verbose_name = "活动批次编号")
#     extraction_flag = models.BooleanField(verbose_name = "抽奖标识", choices = ((True, '已抽奖'), (False, '未抽奖')),
#                                           default = False)
#     award_type = models.IntegerField(verbose_name = "奖品类型", default = 0)
#     create_time = models.DateTimeField(default = datetime.datetime.now)
#     last_show_time = models.DateTimeField(verbose_name = "上次展示抽奖时间", default = datetime.datetime.now)
#     user = models.ForeignKey(User)

class ApiLimitRecord(models.Model):
    app_key = models.CharField(verbose_name = 'APPKEY', max_length = "20", null = False)
    api_name = models.CharField(verbose_name = 'API名称', max_length = "100", null = False)
    limit_time = models.DateTimeField(verbose_name = 'API超限时间', default = datetime.datetime.now)

    @staticmethod
    def save_record(app_key, api_name):
        limit_time = CacheAdpter.get(CacheKey.ROUTER_API_LIMIT_TIME % (app_key, api_name), 'web', None)
        now_time = datetime.datetime.now()
        start_time = get_start_datetime()

        # 缓存中有，且超限时间大于今天，说明已记录，则直接返回
        if limit_time and limit_time > start_time:
            return True

        # 缓存中没有，或不是当天的记录，则保存当天的记录记录
        _, is_created = ApiLimitRecord.objects.get_or_create(app_key = app_key, api_name = api_name,
                                                             limit_time__gt = start_time,
                                                             defaults = {'app_key': app_key, 'api_name': api_name})

        # 更新缓存和API超限时间
        CacheAdpter.set(CacheKey.ROUTER_API_LIMIT_TIME % (app_key, api_name), now_time, 'web', timeout = 24 * 60 * 60)

        # 检查是否需要公告
        # limit_descr = Const.ROUTER_API_LIMIT_DESCRIPTION[app_key].get(api_name, '')
        # if not is_created or not limit_descr:
        #     return True

        # # 发布新公告 TODO

        # title_prefix = datetime_2string(start_time, '%m月%d日')
        # content = "<p style='margin:2px'>亲，由于今日（%s）淘宝接口超限，以致开车精灵部分功能使用不正常，详情如下：</p><ul style='margin:0px 30px'> %s </ul><p style='margin:2px'>今天过后系统会自动恢复正常，感谢亲的理解与支持！</p>"
        # index = notice.message.rfind('</li>')
        # if index == -1 or notice.last_modified <= start_time: # 全新的公告，或者昨天的公告，直接替换content
        #     notice.message = content % (title_prefix, '<li>%s</li>' % limit_descr)
        # else: # 今天已发的公告，只是追加content
        #     content = notice.message
        #     notice.message = "%s%s%s" % (content[0:index + 5], '<li>%s</li>' % limit_descr, content[index + 5:])
        # notice.title = '%s淘宝接口超限公告' % (title_prefix)
        # notice.level = 'error'
        # notice.type = 'TIMED'
        # notice.user_type = app_key
        # notice.is_show = True
        # notice.start_time = now_time
        # notice.end_time = get_end_datetime()
        # notice.save()

        return True
