# coding=UTF-8
import init_environ, settings, md5, httplib, urllib, random, simplejson as json
from datetime import *
from apps.common.utils.utils_log import log
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple, bulk_update_for_sql
from apps.common.utils.utils_datetime import date_2datetime
from apps.common.utils.utils_collection import genr_sublist
from apps.common.utils.utils_sms import send_sms
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.subway.download import dler_coll
from pymongo.errors import BulkWriteError
from apps.router.models import AccessToken
from apps.crm.models import Customer
from django.contrib.auth.models import get_hexdigest

def set_session_to_cache(key_type, key, platform, session):
    '''将session根据不同平台存到缓存中，格式{"web":(web_session, cached_date1), "qn":(qn_session, cached_date2)}'''
    sess_dict = CacheAdpter.get(CacheKey.WEB_USER_TAPI % (key_type, key), 'web', {})
    sess_dict.update({platform:(session, date.today())})
    CacheAdpter.set(CacheKey.WEB_USER_TAPI % (key_type, key), sess_dict, 'web', 60 * 60 * 24)

def bulk_update_mongodb(coll, update_list): # update_list形如[({'_id':1024321654}, {'$set':{'max_price':24}}), ({'_id':1024321651}, {'$set':{'max_price':47}}),...]
    total_updated_num = 0
    for temp_list in genr_sublist(update_list, 1000): # bulk一次最多1000个
        bulk = coll.initialize_unordered_bulk_op()
        for update_tuple in temp_list:
            bulk.find(update_tuple[0]).update(update_tuple[1])
        try:
            result = bulk.execute()
            total_updated_num += result['nModified']
        except BulkWriteError, e:
            log.error('bulk_update_mongodb, detail=%s' % e.details)
            total_updated_num += e.details['nModified']
    return total_updated_num

def send_short_message(nick):
    try:
        phone = Customer.objects.get(nick = nick).phone
        if phone:
            content = '开车精灵:%s,您好!您已至少一周未登录精灵,请及时登录,防止淘宝授权过期,无法自动优化!' % nick
            result = send_sms([phone], content)
            if 'code' in result and result['code'] == 0:
                log.info('refresh_token task send_sms ok, nick=%s' % nick)
            else:
                log.info('refresh_token task send_sms error, nick=%s, e=网络或者短信平台出问题' % nick)
        else:
            log.info('refresh_token task send_sms error, nick=%s, e=该用户还没录入手机号' % nick)
    except Exception, e:
        log.error('refresh_token task send_sms error, nick=%s, e=%s' % (nick, e))

def set_password(raw_password):
    salt = get_hexdigest('sha1', str(random.random()), str(random.random()))[:5]
    hsh = get_hexdigest('sha1', salt, raw_password)
    return '%s$%s$%s' % ('sha1', salt, hsh)

def main():
    # 找出在服务有效期内指定天数refresh_min_days未登录的用户信息
    refresh_min_days = 7
    today_datetime = date_2datetime(date.today())
    refresh_max_date = today_datetime - timedelta(days = refresh_min_days)
    sql1 = "SELECT nick FROM router_articleusersubscribe WHERE article_code='%%s' AND deadline>'%s'" % today_datetime
    sql2 = "SELECT nick, shop_id, session FROM auth_user WHERE nick IN (%s) AND last_login<'%s'" % (sql1, refresh_max_date)
#     sql2 = "SELECT username, shop_id, email FROM auth_user WHERE username IN (%s) AND last_login>'2014-08-11'" % sql1
    refresh_failed_nick = []

    #===========================================================================
    # TOP授权协议 web平台
    #===========================================================================
    platform = 'web'
    appkey = settings.APP_KEY
    appsecret = settings.APP_SECRET
    sql = sql2 % settings.APP_ARTICLE_CODE
#     sql = "SELECT username, shop_id, email FROM auth_user WHERE shop_id IN (%s)" % "'60605073'" # 修复指定用户用
    user_list = execute_query_sql_return_tuple(sql)
    # 从目标用户中过滤掉指定天数refresh_min_days内已经刷新过session的用户
    shop_id_list = [int(user_info[1]) for user_info in user_list]
    refresh_token_qs = dler_coll.find({'_id':{'$in':shop_id_list}, '$or':[{'top_refresh_time':{'$lte':refresh_max_date}}, {'top_refresh_time':None}]}, {'_id':1, 'top_refresh_token':1})
#     refresh_token_qs = dler_coll.find({'_id':{'$in':shop_id_list}}, {'_id':1, 'top_refresh_token':1}) # 修复指定用户用
    refresh_token_dict = {qs['_id']:qs.get('top_refresh_token', None) for qs in refresh_token_qs}

    update_session_list, update_refresh_list = [], []
    for nick, shop_id, session in user_list:
        shop_id = int(shop_id)
        if refresh_token_dict.has_key(shop_id):
            refresh_token = refresh_token_dict[shop_id]
            if not refresh_token:
                refresh_token = session
            sign = md5.new('appkey%srefresh_token%ssessionkey%s%s' % (appkey, refresh_token, session, appsecret)).hexdigest().upper()
            url_params = urllib.urlencode([('appkey', appkey), ('refresh_token', refresh_token), ('sessionkey', session), ('sign', sign)])
            resp = AccessToken.sync_from_top(url_params, host = 'container.api.taobao.com', method = 'GET', url = '/container/refresh', secure = False)
            if resp.has_key('top_session'):
                session = resp['top_session']
                password = set_password(session)
                if resp.has_key('refresh_token'):
                    refresh_token = resp['refresh_token']
                else:
                    refresh_token = session
                update_session_list.append((session, password, shop_id, nick))
                update_refresh_list.append(({'_id':shop_id}, {'$set':{'top_refresh_token':refresh_token, 'top_refresh_time':today_datetime}}))
                set_session_to_cache(1, shop_id, platform, session)
                set_session_to_cache(2, nick, platform, session)
                log.info('刷新session成功：%s' % nick)
            else:
                send_short_message(nick)
                refresh_failed_nick.append(nick)
                log.info('刷新session失败：%s' % nick)

    session_count = refresh_count = 0
    if update_session_list:
        sql = "UPDATE auth_user SET session=%s, password=%s WHERE shop_id=%s AND nick=%s" # 作为executemany参数时，内部的字符串参数会自动加上引号，所以不用再sql语句里加引号！
        session_count = bulk_update_for_sql(sql, update_session_list)
    log.info('自动刷新session脚本：成功批量刷新%s个web平台账户的session' % session_count)
    del update_session_list
    if update_refresh_list:
        refresh_count = bulk_update_mongodb(dler_coll, update_refresh_list)
    log.info('自动刷新session脚本：成功批量刷新%s个web平台账户的refresh_token' % refresh_count)
    del update_refresh_list

    #===========================================================================
    # oAuth2.0授权协议 qn平台
    #===========================================================================
    platform = 'qn'
    appkey = settings.APP_KEY
    appsecret = settings.APP_SECRET
    sql = sql2 % settings.APP_ARTICLE_CODE
#     sql = "SELECT username, shop_id, email FROM auth_user WHERE shop_id IN (%s)" % "'60605073'" # 修复指定用户用
    user_list = execute_query_sql_return_tuple(sql)
    # 从目标用户中过滤掉指定天数refresh_min_days内已经刷新过session的用户
    nick_list = [user_info[0] for user_info in user_list]
    nick_list = "('%s')" % ("','".join(nick_list))
    sql = "SELECT nick, access_token, refresh_token FROM router_accesstoken WHERE nick in %s AND platform='qn' AND (create_time<='%s' OR create_time is NULL)" % (nick_list, refresh_max_date)
#     sql = "SELECT nick, access_token, refresh_token FROM router_accesstoken WHERE nick in %s AND platform='qn'" % nick_list # 修复指定用户用
    user_list2 = execute_query_sql_return_tuple(sql)

    update_token_list = []
    for nick, access_token, refresh_token in user_list2:
        if not refresh_token:
            refresh_token = access_token
        url_params = urllib.urlencode([('client_id', appkey), ('client_secret', appsecret), ('grant_type', 'refresh_token'), ('refresh_token', refresh_token)])
        resp = AccessToken.sync_from_top(url_params, host = 'oauth.taobao.com', method = 'POST', url = '/token', secure = True)
        if resp.has_key('access_token'):
            access_token = resp['access_token']
            if resp.has_key('refresh_token'):
                refresh_token = resp['refresh_token']
            else:
                refresh_token = access_token
            update_token_list.append((access_token, refresh_token, today_datetime, nick))
            set_session_to_cache(1, shop_id, platform, access_token)
            set_session_to_cache(2, nick, platform, access_token)
            log.info('刷新access_token成功：%s' % nick)
        else:
            if nick not in refresh_failed_nick:
                send_short_message(nick)
                refresh_failed_nick.append(nick)
            log.info('刷新access_token失败：%s' % nick)

    token_count = 0
    if update_token_list:
        sql = "UPDATE router_accesstoken SET access_token=%s, refresh_token=%s, create_time=%s WHERE nick=%s AND platform='qn'"
        token_count = bulk_update_for_sql(sql, update_token_list)
    log.info('自动刷新access_token脚本：成功批量刷新%s个qn平台账户的access_token' % token_count)

    if refresh_failed_nick:
        log.info('自动刷新session&access_token脚本：共%s个用户刷新失败，分别是：%s' % (len(refresh_failed_nick), '，'.join(refresh_failed_nick)))

if __name__ == '__main__':
    main()
