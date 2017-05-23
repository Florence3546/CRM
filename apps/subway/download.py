# coding=UTF-8

import datetime

from mongoengine.document import Document
from mongoengine.fields import IntField, DateTimeField, StringField

from apilib import get_tapi, TopError, SessionCache
from apilib.app import QNApp
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import time_is_someday, format_datetime, datetime_2string, time_is_recent
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.common.biz_utils.utils_misc import set_cache_progress, get_cache_progress
from models_account import Account
from models_adgroup import Adgroup
from models_campaign import Campaign
from models_creative import Creative
from models_keyword import Keyword
from models_item import Item

def get_klass_name(klass):
    return klass.__name__.lower()

def get_klass(name):
    return globals()[name]

def check_sync_struct(dl, is_created):
    if is_created:
        return True
    elif dl.ok_time and dl.ok_time.date() < datetime.date.today():
        return True
    elif not dl.init_status or not dl.init_status:
        return True
    elif dl.init_status and dl.init_status != 'done':
        return True
    elif dl.init_status and dl.inc_status != 'done':
        return True
    return False

def check_global_mutual(dl_type):
    # TODO: wangqi 20140528 下载互斥还没想好互斥时的处理，后续再优化
    """全网如果有互斥缓存，则不下载，主要分结构与报表，可以将颗粒度细化"""
    def _is_mutual(fn):
        def __is_mutual(self = None, *args, **kwargs):
            key_name = CacheKey.SUBWAY_DOWNLOAD_MUTUAL_LOCK % (self.shop_id, dl_type)
            cached_lock = CacheAdpter.get(key_name, 'web')
            if cached_lock: # 没有缓存，直接下载
                return False
            else:
                CacheAdpter.set(key_name, True, 'web', 30 * 60)
                result = fn(self, *args, **kwargs)
                CacheAdpter.delete(key_name, 'web')
                return result
        return __is_mutual
    return _is_mutual

def parse_status(status_str):
    """
    parse_status('2013-7-30-15-20_OK')
    >>> ('OK',datetime.datetime(2013,7,30,15,20))
    parse_status('2013-7-30-15-20_2013-7-30-16-40_DOING')
    >>> ('OK',datetime.datetime(2013,7,30,15,20), datetime.datetime(2013,7,30,16,40))
    """
    if status_str:
        temp_list = status_str.split('_')
        status = temp_list[-1]
        result_list = [status, datetime.datetime.strptime(temp_list[0], '%Y-%m-%d-%H-%M')]
        if status == 'DOING':
            result_list.append(datetime.datetime.strptime(temp_list[1], '%Y-%m-%d-%H-%M'))
        return tuple(result_list)
    else:
        return None


DL_ORDER_LIST = ['Account', 'Campaign', 'Adgroup', 'Creative', 'Keyword', 'Item'] # 下载的顺序控制
class Downloader(Document):
    """记录了各个结构的整体状态（结构同步状态，报表同步状态）"""

    shop_id = IntField(verbose_name = '店铺ID', primary_key = True)

    init_status = StringField(verbose_name = "初始化状态", default = 'ready')
    inc_status = StringField(verbose_name = "增量状态", default = 'ready')
    ok_time = DateTimeField(verbose_name = "结构同步成功的时间")
    failed_time = DateTimeField(verbose_name = "增量结构同步失败的时间")

    accountrpt_status = StringField(verbose_name = '账户报表状态', db_field = 'acctrpt_status', default = '')
    campaignrpt_status = StringField(verbose_name = '计划报表状态', db_field = 'camprpt_status', default = '')
    adgrouprpt_status = StringField(verbose_name = '广告组报表状态', db_field = 'adgrpt_status', default = '')
    keywordrpt_status = StringField(verbose_name = '关键词报表状态', db_field = 'kwrpt_status', default = '') # 单个依赖于adgroup
    creativerpt_status = StringField(verbose_name = '创意报表状态', db_field = 'crtrpt_status', default = '') # 单个依赖于adgroup

    api_valid_time = DateTimeField(verbose_name = "API有效时间")
    top_refresh_token = StringField(verbose_name = "top的session刷新令牌")
    top_refresh_time = DateTimeField(verbose_name = "top的session刷新时间")

    meta = {'db_alias': "mnt-db", 'collection':'subway_downloader'}

    @property
    def tapi(self):
        if not hasattr(self, '_tapi'):
            tapi = get_tapi(shop_id = self.shop_id)
            if not time_is_someday(self.api_valid_time):
                is_ok, _ = QNApp.test_api(tapi)
                if not is_ok:
                    SessionCache.del_cache(self.shop_id)
                    tapi = get_tapi(shop_id = self.shop_id)
                    is_ok, reason = QNApp.test_api(tapi)
                    if not is_ok:
                        log.error("invalid tapi, error=%s" % reason)
                        tapi = None

                if tapi:
                    self.api_valid_time = datetime.datetime.now()
                    self.save()

            self._tapi = tapi
        return self._tapi

    @property
    def token(self):
        """获取淘宝的临时验证码"""
        if not hasattr(self, '_token'):
            cachekey = CacheKey.SUBWAY_TOKEN % self.shop_id
            token = CacheAdpter.get(cachekey, 'web')
            if not token:
                token = self._get_subway_token()
                CacheAdpter.set(cachekey, token, 'web', timeout = 60*60*2)
            self._token = token
        return self._token

    def _get_subway_token(self):
        temp_token = ''
        if self.tapi:
            try:
                top_obj = self.tapi.simba_login_authsign_get()
                if top_obj and hasattr(top_obj, "subway_token"):
                    temp_token = top_obj.subway_token
            except TopError, e:
                log.error('simba_login_authsign_get TopError, shop_id=%s, error=%s' % (self.shop_id, e))
        return temp_token

    # @property
    # def refresh_token(self, sessionkey):
    #     import settings, md5, requests
    #     from urllib import urlencode
    #     appkey = settings.APP['web']['APP_KEY']
    #     appsecret = settings.APP['web']['APP_SECRET']
    #     try:
    #         refresh_token = sessionkey
    #         sign = md5.new('appkey%srefresh_token%ssessionkey%s%s' % (appkey, refresh_token, sessionkey, appsecret)).hexdigest().upper()
    #         data = {
    #             'appkey':appkey,
    #             'refresh_token':refresh_token,
    #             'sign':sign,
    #             'sessionkey':sessionkey
    #             }
    #         url_data = urlencode(data)
    #         r = requests.post('http://container.api.taobao.com/container/refresh?%s' % url_data).json()
    #         if not 're_expires_in' in r or not r['re_expires_in']:
    #             return sessionkey
    #         return r['top_session']
    #     except Exception, e:
    #         log.error('get refresh token error and the error=%s' % e)
    #         return sessionkey

    def check_todayrpt_isok(self, need_detail = False): # 是否需要关键词详情
        """检查今天所有报表数据是否OK"""
        today = datetime.date.today()
        if self.ok_time.date() < today:
            return False
        check_class_list = ['account', 'campaign', 'adgroup']
        if need_detail:
            check_class_list.extend(['keyword', 'creative'])
        for cls_name in check_class_list:
            status_result = parse_status(getattr(self, '%srpt_status' % (cls_name)))
            if not status_result:
                return False
            elif status_result[0] not in ['OK', 'EMPTY']:
                return False
            elif status_result[1].date() < today:
                return False
            else:
                continue
        return True

    def check_rptstatus_isok(self, cls_name):
        """判断状态是否OK"""
        status_result = parse_status(getattr(self, '%srpt_status' % (cls_name)))
        if status_result:
            if status_result[0] in ['OK', 'EMPTY']:
                return True
        return False

    def check_struct_isok(self, cls_name):
        import copy
        temp_list = copy.deepcopy(DL_ORDER_LIST)
        temp_list.insert('ready')
        temp_list.append('done')
        try:
            return temp_list.index(self.init_status) > temp_list.index(cls_name)  and temp_list.index(self.inc_status) > temp_list.index(cls_name)
        except Exception, e:
            log.error('cls_name not found in DL_ORDER_LIST, cls_name=%s, e=%s' % (cls_name, e))
            return False
        finally:
            del temp_list

    def __delattr__(self, *args, **kwargs): # why? by wangqi 20150928
        super(Downloader, self).__delattr__(*args, **kwargs)

    def check_rpt_isok(self, need_detail = False): # 是否需要关键词详情
        """检查所有报表数据是否OK"""
        temp_result = self.check_rptstatus_isok('account') and self.check_rptstatus_isok('campaign') and self.check_rptstatus_isok('adgroup')
        if not need_detail:
            return temp_result
        else:
            return temp_result and self.check_rptstatus_isok('creative') and self.check_rptstatus_isok('keyword')

    def check_status_4rpt(self, klass, check_type = 'rpt'):
        """
        0.报表、UDP下载
        1.状态OK-->时间是否今天-->不必下载
                        | -->下载
        2.状态FAILED-->重新下载
        3.状态DOING -->检查上次成功时间是否是今天-->不必下载
                                    |---->检查运行时间是否在10分钟内--->等待
                                                        |------>重新下载
        4.状态是空-->初始化下载
        """
        # TODO: wangqi 20140711 下载报表的控制写的不够好，有空可以优化，没有利用好缓存的状态
        cls_name = get_klass_name(klass)
        status_result = parse_status(getattr(self, '%s%s_status' % (cls_name, check_type)))
        if status_result:
            status, last_time = status_result[0], status_result[1]
            if status in ('OK', 'EMPTY'):
                if time_is_someday(last_time):
                    return False, None
                else:
                    return True, last_time
            elif status == 'FAILED':
                return True, last_time
            elif status == 'DOING':
                if time_is_someday(last_time):
                    return False, None
                else:
                    if time_is_recent(status_result[2], minutes = cls_name == 'keyword' and 40 or 10): # 下载关键词报表时，这个时间限制可以大一些
                        return False, None
                    else:
                        return True, last_time
        else:
            # TODO: wangqi 20151102 这里先这样写吧，后期把status去掉，数据库只保存成功下载的时间即可
            return True, datetime.datetime.today() - datetime.timedelta(days = klass.Report.INIT_DAYS)

    def download_struct(self, klass):
        return klass.struct_download(shop_id = self.shop_id, tapi = self.tapi)

    def download_increase(self, klass, last_time):
        if not last_time:
            last_time = datetime.datetime.now()
        last_sync_time = last_time - datetime.timedelta(hours = 1)
        return klass.increase_download(shop_id = self.shop_id, tapi = self.tapi, last_sync_time = format_datetime(last_sync_time))

    def download_rpt(self, klass, last_time, is_force = False):
        attr_name = '%s%s_status' % (get_klass_name(klass), 'rpt')
        setattr(self, attr_name, '%s_%s_DOING' % (datetime_2string(last_time), datetime_2string()))
        self.save()

        # 报表的特殊时间处理：1，上次同步时间太久置为15天前；2，上次同步时间不能超过今天；3，当前时间小于6点，因淘宝数据尚未准备好只下载前天数据
        # 强制上次同步时间不超过前天，原因：1，淘宝报表效果数据经常延时，这样第2天会自动修复报表；2，历史数据为3天转化数据，比1天转化数据更可靠。
        last_date = last_time.date()

        init_start_date = datetime.date.today() - datetime.timedelta(days = klass.Report.INIT_DAYS)
        valid_rpt_days = datetime.datetime.now().hour < 6 and 2 or 1
        default_end_date = datetime.date.today() - datetime.timedelta(days = valid_rpt_days)
        default_start_date = default_end_date - datetime.timedelta(days = 2)
        if last_date < init_start_date:
            last_date = init_start_date
        elif last_date > default_start_date:
            last_date = default_start_date

        time_scope = last_date, default_end_date
        if is_force and get_klass_name(klass) in ['keyword', 'creative']:
            result = klass.force_download_rpt(shop_id = self.shop_id, tapi = self.tapi, token = self.token, time_scope = time_scope)
        else:
            result = klass.report_download(shop_id = self.shop_id, tapi = self.tapi, token = self.token, time_scope = time_scope)
        # TODO: wangqi 2014-4-14 同样，由于上面同步时间的不同，这里也要在此基础上作改动，后续考虑再优化
        record_datetime = valid_rpt_days == 1 and datetime.datetime.now() or datetime.datetime.now() - datetime.timedelta(days = 1)
        status_str = '%s_%s' % (result in ['OK', 'EMPTY'] and datetime_2string(record_datetime) or datetime_2string(last_time), result)
        setattr(self, attr_name, status_str)
        self.save()
        return result

    def auto_sync_struct(self, stop_status = "done"):
        """
        0.首先是下载顺序：['ready','Account','Campaign','Adgroup','Creative','Keyword','Item','done']
        1.有两个字段保存状态，一个是init_status、一个是inc_status，状态都在上面的列表中。
        2.自动下载时，首先根据init_status来判断，在init_status顺序之前的，就下增量，以之后的，就下载结构
        3.下载增量时，根据inc_status来判断，在inc_status之前的，下载时间是ok_time，之后的，就按failed_time来下载
        """
        init_date = datetime.datetime.now() - datetime.timedelta(days = 28)
        if (self.ok_time and self.ok_time <= init_date) or (self.failed_time and self.failed_time <= init_date) : # 只要ok_time与failed_time中有一个时间比较久，就初始化下载
            self.init_status = 'ready'
            self.inc_status = 'ready'

        try:
            init_index = DL_ORDER_LIST.index(self.init_status)
        except ValueError:
            if self.init_status == 'ready':
                init_index = -1
            elif self.init_status == 'done': # 如果已经OK，则全部下载增量？
                init_index = len(DL_ORDER_LIST)
            else:
                return False

        try:
            inc_index = DL_ORDER_LIST.index(self.inc_status)
        except ValueError:
            if self.inc_status in ['ready', 'done']:
                inc_index = len(DL_ORDER_LIST)
            else:
                return False

        try:
            for i, cls_name in enumerate(DL_ORDER_LIST):
                if cls_name == stop_status:
                    raise Exception(cls_name, i < init_index and "inc" or "init") # 状态跟其它状态一致
                set_cache_progress(self.shop_id, 'struct_' + cls_name.lower() + '_downing')
                if i < init_index:
                    if not self.download_increase(klass = get_klass(cls_name), last_time = i < inc_index and self.ok_time or self.failed_time):
                        raise Exception(cls_name, 'inc')
                else:
                    if not self.download_struct(klass = get_klass(cls_name)):
                        raise Exception(cls_name, 'init')
                set_cache_progress(self.shop_id, 'struct_' + cls_name.lower() + '_finished')
            self.init_status = 'done'
            self.inc_status = 'done'
            self.failed_time = None # 下载成功，失败时间记为空
            log.info('sync ALL struct OK, shop_id=%s' % self.shop_id)
            return True
        except Exception, e:
            log.error('sync ALL struct FAILED, shop_id=%s, stopped at %s, download %s' % (self.shop_id, e[0], e[1]))
            if e[1] == 'inc':
                self.failed_time = self.ok_time
                self.inc_status = e[0]
            else:
                self.init_status = e[0]
            return False
        finally:
            self.ok_time = datetime.datetime.now()
            self.save()

    def sync_rpt(self, klass, is_force = False, rpt_days = None):
        cls_name = get_klass_name(klass)
        if is_force: # 如果强制下载，则使用给定的rpt_days，或者使用该类自定的报表保留天数
            if rpt_days is None:
                rpt_days = klass.Report.INIT_DAYS
            flag, last_time = True, datetime.datetime.today() - datetime.timedelta(days = rpt_days)
        else:
            flag, last_time = self.check_status_4rpt(klass, check_type = 'rpt')
        set_cache_progress(self.shop_id, 'report_' + cls_name.lower() + '_downing')
        if flag:
            result = self.download_rpt(klass = klass, last_time = last_time, is_force = is_force)
            set_cache_progress(self.shop_id, 'report_' + cls_name.lower() + '_finished')
            return result
        else:
            set_cache_progress(self.shop_id, 'report_' + cls_name.lower() + '_finished')
            return True

    # @check_global_mutual('struct')
    def sync_all_struct(self, is_force = False):
        if self.tapi:
            if is_force: # 强制下载时，将字段重置即可重新下载
                self.init_status = 'ready'
                self.inc_status = 'ready'
                self.save()
            return self.auto_sync_struct()
        else:
            return False

    def sync_all(self):
        # 下载所有数据
        if self.sync_all_struct():
            self.sync_all_rpt()
            return True
        else:
            return False

    # @check_global_mutual('rpt')
    def sync_all_rpt(self, detail_flag = False, is_force = False, rpt_days = None, quick_flag = False):
        if self.tapi:
            acct_rpt_status = self.sync_rpt(klass = Account, is_force = is_force, rpt_days = rpt_days)
            if acct_rpt_status == 'EMPTY':
                if datetime.datetime.now().hour < 9: # TODO: wangqi 20140725 该特性很久没有用上了，是否考虑去掉。如果淘宝返回空并且时间是9点以前，将状态设置为FAILED
                    status_str = '%s_%s' % (datetime_2string(), 'FAILED')
                    self.accountrpt_status = status_str
                    self.save()
                    return False
                else:
                    return True
            else:
                self.sync_rpt(klass = Campaign, is_force = is_force, rpt_days = rpt_days)
                if quick_flag:
                    return True
                self.sync_rpt(klass = Adgroup, is_force = is_force, rpt_days = rpt_days)
                if detail_flag:
                    self.sync_rpt(klass = Creative, is_force = is_force, rpt_days = rpt_days)
                    self.sync_rpt(klass = Keyword, is_force = is_force, rpt_days = rpt_days)

            return self.check_rpt_isok(need_detail = detail_flag)
        else:
            return False

    @staticmethod
    def download_all_struct(shop_id, is_force = False):
        dl, _ = Downloader.objects.get_or_create(shop_id = shop_id)
        return dl.sync_all_struct(is_force = is_force)

    @staticmethod
    def download_all_rpt(shop_id, detail_flag = False, is_force = False, rpt_days = None):
        dl , is_created = Downloader.objects.get_or_create(shop_id = shop_id)
        if is_created:
            dl.sync_all_struct(is_force = is_force)
        return dl.sync_all_rpt(detail_flag = detail_flag, is_force = is_force, rpt_days = rpt_days)

    @staticmethod
    def quick_download(shop_id):
        dl, _ = Downloader.objects.get_or_create(shop_id = shop_id)
        if dl.tapi:
            dl.auto_sync_struct(stop_status = "Adgroup")
            dl.sync_all_rpt(quick_flag = True)

    @staticmethod
    def download_all(shop_id):
        dl, _ = Downloader.objects.get_or_create(shop_id = shop_id)
        if dl.tapi:
            dl.sync_all()

    @classmethod
    def often_sync_struct(cls, shop_id):
        dl, _ = Downloader.objects.get_or_create(shop_id = shop_id)
        if (not dl.ok_time) or dl.ok_time <= datetime.datetime.now() - datetime.timedelta(hours = 1):
            return dl.sync_all_struct()
        return True

dler_coll = Downloader._get_collection()
