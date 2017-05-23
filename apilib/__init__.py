# coding=UTF-8
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.
"""
top API library
"""
__version__ = '1.5'
__author__ = 'Joshua Roesslein'
__license__ = 'MIT'

import datetime

from apilib.error import TopError, ApiLimitError, DataNotExist
from apilib.parsers import TopObject, TopObjectParser
from apilib.auth import AuthHandler, JAuthHandler, TopAuthHandler
from apilib.app import QNApp
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_cacheadpter import CacheAdpter


def debug(enable = True, level = 1):
    import httplib
    httplib.HTTPConnection.debuglevel = level

class SessionCache(object):
    KEY = CacheKey.USER_SESSION

    @classmethod
    def load_cache(cls, shop_id):
        cached_session = cls.get_cache(shop_id)
        if cached_session and cached_session['expired'] and cached_session['expired'] > datetime.datetime.now():
            return cached_session
        else:
            return {}

    @classmethod
    def set_cache(cls, shop_id, data):
        # data 形如{'session': 'xxxxx', 'expired': datetime.datetime(2015, 6, 20)}
        CacheAdpter.set(cls.KEY % shop_id, data, 'web', timeout = 24 * 60 * 60 * 7)

    @classmethod
    def get_cache(cls, shop_id):
        return CacheAdpter.get(cls.KEY % shop_id, 'web', None)

    @classmethod
    def refresh(cls, shop_id, data):
        cls.del_cache(shop_id)
        cls.set_cache(shop_id, data)

    @classmethod
    def del_cache(cls, shop_id):
        CacheAdpter.delete(cls.KEY % (shop_id), 'web')


def get_tapi(user = None, shop_id = 0):
    if user is not None:
        shop_id = user.shop_id
    session_dict = SessionCache.load_cache(shop_id)
    session = session_dict.get('session')
    if not session:
        try:
            session, expired_time = QNApp.get_session(shop_id)
        except DataNotExist:
            return None # session从数据库取不到
        SessionCache.set_cache(shop_id = shop_id, data = {'expired': expired_time, 'session': session})
    return QNApp.init_tapi(session)

# 免session的API
tsapi = QNApp.init_tapi(None)
