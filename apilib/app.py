# coding=utf-8
import datetime

from django.conf import settings
from apilib.auth import TopAuthHandler
from apilib.tapi import TAPI
from apilib.error import DataNotExist
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey


class QNApp(object):
    app_key = settings.APP_KEY
    article_code = settings.APP_ARTICLE_CODE
    app_secret = settings.APP_SECRET

    @classmethod
    def get_session(cls, shop_id):
        user_sql = "select nick from router_user where shop_id=%s" % shop_id
        user_nick_result = execute_query_sql_return_tuple(user_sql)
        if user_nick_result:
            nick = user_nick_result[0][0]
            token_sql = "select access_token, expire_time from router_accesstoken where platform='web' and nick='%s' order by create_time desc limit 1;" % nick
            result = execute_query_sql_return_tuple(token_sql)
            if result:
                return result[0][0], result[0][1]
            else:
                raise DataNotExist(query_cond = "nick=%s" % nick, table = "router_accesstoken")
        else:
            raise DataNotExist(query_cond = "shop_id=%s" % shop_id, table = "router_user")

    @classmethod
    def init_tapi(cls, session = None):
        auth = TopAuthHandler(cls.app_key, cls.app_secret, session)
        return TAPI(auth, retry_count = settings.TAPI_RETRY_COUNT, retry_delay = settings.TAPI_RETRY_DELAY)

    @classmethod
    def get_tapi(cls, shop_id = None):
        if shop_id:
            session, _ = cls.get_session(shop_id)
        else:
            session = None
        return cls.init_tapi(session)

    @classmethod
    def test_api(cls, tapi):
        if not tapi:
            return False, 'tapi为空'
        session = tapi.auth.session_key
        if session:
            balance = CacheAdpter.get(CacheKey.NCRM_ACCOUNT_BALANCE % session, 'web', None)
            if balance is None:
                try:
                    tobj_balance = tapi.simba_account_balance_get()
                    CacheAdpter.set(CacheKey.NCRM_ACCOUNT_BALANCE % session, tobj_balance.balance, 'web', 60 * 5)
                    return True, ''
                except Exception, e:
                    error_msg = str(e)
                    if 'Call only from jst' in error_msg:
                        msg = "聚石塔调用限制"
                    elif 'session-expired' in error_msg:
                        msg = "session过期"
                    elif 'Missing session' in error_msg:
                        msg = "缺少session"
                    elif 'session-not-exist' in error_msg:
                        msg = "session不存在"
                    elif 'Invalid session' in error_msg:
                        msg = "session过期"
                    elif 'need to wait' in error_msg:
                        msg = "今日淘宝API接口已调用完"
                        return True, '' # 流控错误放过
                    else:
                        msg = "其他错误"
                    return False, msg
            else:
                return True, ''
        else:
            return False, '缺少session'
