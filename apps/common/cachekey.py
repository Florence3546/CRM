# coding=UTF-8
"""
全局缓存的Key管理类，避免在不同业务中产生重复的Key
Created on 2013-07-25
@author: zhangyu

CacheKey定义规范：
    1、CacheKey之间保持一行间隔
    2、属于app下的CacheKey前缀为APP名称，否则为COMMON
    3、同一个app下的CacheKey放在一起，COMMON放在最后面

CacheKey声明格式：
    '''CacheKey声明示例'''
    CacheKey.APP_CACHEKEY_NAME = 'APP_EXAMPLE_%s'

CacheKey引用方式：
    CacheAdpter.get(CacheKey.APP_CHOICES_NAME % shop_id,'web')
"""

from apps.common.constant import _Constant

CacheKey = _Constant()

# ==============================定义CacheKey Start=================================================


'''用户session对象缓存'''
CacheKey.USER_SESSION = 'WEB_USER_SESSION_%s' # 参数为shop_id


# crm

'''CRM 有效账户缓存'''
CacheKey.CRM_VALID_ACCOUNT_FLAG = "CRM_VALID_ACCOUNT_FLAG"

'''CRM 人机结合提示信息'''
CacheKey.CRM_RJJH_DANGEROUS_INFO = "CRM_RJJH_DANGEROUS_INFO_%s"

'''CRM 人机结合提示信息锁'''
CacheKey.CRM_RJJH_DANGEROUS_INFO_LOCK = "CRM_RJJH_DANGEROUS_INFO_LOCK_%s"

'''CRM 宝贝统计缓存标示'''
CacheKey.CRM_CAT_ADG_STATISTICS = "CRM_CAT_ADG_STATISTICS"
CacheKey.CRM_CAT_ADG_STATISTICS_LOCK = "CRM_CAT_ADG_STATISTICS_LOCK"


# crm


# engine

'''大任务timer的互斥缓存'''
CacheKey.ENGINE_SHOPMNG_TASK_MUTUAL_LOCK = 'SHOPMNG_TASK_MUTUAL_LOCK'

'''自动抢排名的互斥缓存'''
CacheKey.ENGINE_ROBRANK_TASK_MUTUAL_LOCK = 'ENGINE_ROBRANK_TASK_MUTUAL_LOCK'

'''实时优化任务进度缓存'''
CacheKey.ENGINE_REALTIME_OPTIMIZE_TASK = 'ENGINE_REALTIME_OPTIMIZE_TASK'


# kwlib

'''某个类目的同义词'''
CacheKey.KWLIB_SYNOWORD = 'KWLIB_SYNOWORD_%s' # 参数为cat_id

'''原子词表修改时间'''
CacheKey.KWLIB_ELEMWORD_MODIFI_TIME = 'KWLIB_ELEMWORD_MODIFI_TIME'

'''无意义词'''
CacheKey.KWLIB_POINTLESSWORD = 'KWLIB_POINTLESSWORD_NEW'

'''类目下top1000'''
CacheKey.KWLIB_CAT_TOP1000 = 'KWLIB_CAT_TOP1000_%s' # 参数为cat_id

'''类目对象信息'''
CacheKey.KWLIB_CAT_INFO = 'KWLIB_CAT_INFO_%s' # 参数为cat_id

'''类目对象的单个属性信息'''
CacheKey.KWLIB_CAT_ATTR = 'KWLIB_CAT_ATTR_%s_%s' # 参数为cat_id, attr_field

'''关键词预估排名'''
CacheKey.KWLIB_FORECAST_KWRANK = 'KWLIB_FORECAST_KWRANK_%s' # 参数为kw_id

'''类目15天报表'''
CacheKey.KWLIB_CAT_STATIC_RPT = 'KWLIB_CAT_STATIC_RPT15_%s' # 参数为 cat_id


# mnt

'''全自动计划timer的互斥缓存'''
CacheKey.MNT_MUTUAL_LOCK = 'MNT_MUTUAL_LOCK_%s' # 参数为task_type

'''MNT命令配置缓存'''
CacheKey.MNT_CMDCFG = "MNT_CMDCFG_%s" # 参数是配置名称

'''MNT策略配置缓存'''
CacheKey.MNT_STGCFG = "MNT_STGCFG"


# router

'''订单同步标记'''
CacheKey.ROUTER_SYNC_ORDER = 'ROUTER_SYNC_ORDER_BYDATA'

'''缓存的article及对应的权限码字典'''
CacheKey.ROUTER_ARTICLE_ITEM_CACHE = 'ROUTER_ARTICLE_ITEM_CACHE'

'''api超限的时间'''
CacheKey.ROUTER_API_LIMIT_TIME = 'ROUTER_API_LIMIT_TIME_%s_%s' # 参数为app_key, api_name

'''获取用户的nick或者shop_id的缓存，通过shop_id或者nick来获取到对应的nick和shop_id'''
CacheKey.ROUTER_GET_NICK_OR_SHOP_ID = 'ROUTER_GET_NICK_OR_SHOP_ID_%s'

'''获取店铺的类型是B店还是C店'''
CacheKey.ROUTER_SHOP_TYPE = 'ROUTER_SHOP_TYPE_%s'

# subway

'''推广组下的关键词质量得分'''
CacheKey.SUBWAY_ADGROUP_QSCORE = 'SUBWAY_ADGROUP_QSCORE_%s' # 参数为adgroup_id

'''推广组下的关键词新质量得分'''
CacheKey.SUBWAY_ADGROUP_NEW_QSCORE = 'SUBWAY_ADGROUP_NEW_QSCORE_%s' # 参数为adgroup_id

'''下载的全局互斥''' # TODO: wangqi 20140528 暂未用上
CacheKey.SUBWAY_DOWNLOAD_MUTUAL_LOCK = 'SUBWAY_DOWNLOAD_MUTUAL_LOCK_%s_%s' # 参数为shop_id与下载类型
CacheKey.SUBWAY_TOKEN = 'SUBWAY_TOKEN_%s' # 参数为shop_id

'''店铺大任务下载进度'''
CacheKey.SUBWAY_DOWNLOAD_TASK = 'SUBWAY_DOWNLOAD_TASK_%s' # 参数为shop_id

'''item详情'''
CacheKey.SUBWAY_ITEM_DETAIL = 'SUBWAY_ITEM_DETAIL_%s' # 参数为 item_id

CacheKey.SUBWAY_ITEM_TIILE_WORD = 'SUBWAY_ITEM_TIILE_WORD_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_PURE_TIILE_WORD = 'SUBWAY_ITEM_PURE_TIILE_WORD_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_PRDTWORD_HOT = 'SUBWAY_ITEM_PRDTWORD_HOT_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_PROPWORD_HOT = 'SUBWAY_ITEM_PROPWORD_HOT_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_DCRTWORD_HOT = 'SUBWAY_ITEM_DCRTWORD_HOT_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_DCRTWORD = 'SUBWAY_ITEM_DCRTWORD_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_SALEWORD = 'SUBWAY_ITEM_SALEWORD_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_PRDTWORD = 'SUBWAY_ITEM_PRDTWORD_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_PROP_DICT = 'SUBWAY_ITEM_PROP_DICT_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_LABEL_DICT = 'SUBWAY_ITEM_LABEL_DICT_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_INCLUDE_BRAND = 'SUBWAY_ITEM_INCLUDE_BRAND_%s' # 参数为 item_id
CacheKey.SUBWAY_ITEM_INCLUDE_WORD = 'SUBWAY_ITEM_INCLUDE_WORD_%s' # 参数为 item_id

CacheKey.SUBWAY_ITEM_CONV_WORD = 'SUBWAY_ITEM_CONV_WORD_%s' # 参数为 item_id

'''关键词的新实时预估结果'''
CacheKey.SUBWAY_KEYWORD_RT_RANK = 'SUBWAY_KEYWORD_RT_RANK_%s_%s' # 参数依次为 kw_id, price

'''实时报表缓存'''
CacheKey.SUBWAY_ACCOUNT_RTRPT = 'SUBWAY_ACCOUNT_RTRPTNEW_%s_%s' # 参数为 shop_id, date
CacheKey.SUBWAY_CAMPAIGN_RTRPT = 'SUBWAY_CAMPAIGN_RTRPT_%s_%s' # 参数为 shop_id, date
CacheKey.SUBWAY_ADGROUP_RTRPT = 'SUBWAY_ADGROUP_RTRPT_%s_%s' # 参数为 campaign_id, date
CacheKey.SUBWAY_KEYWORD_RTRPT = 'SUBWAY_KEYWORD_RTRPT_%s_%s' # 参数为 adgroup_id, date

# web

'''isv调用API的当日总计数'''
CacheKey.WEB_ISV_APICOUNT = 'WEB_APICOUNT_%s_%s' # 参数(%s_%s)对应(isv_key, api_name)，isv_key：是isv的appkey；api_name：是api的名称

'''软件左侧导航中全自动优化菜单'''
CacheKey.WEB_MNT_MENU = 'WEB_MNT_MENU_%s' # 参数为shop_id

'''软件左侧推广广告菜单'''
CacheKey.WEB_AD_MENU = 'WEB_AD_MENU'

'''服务中心推广广告'''
CacheKey.WEB_SERVER_MENU = 'WEB_SERVER_MENU'

'''人机结合注册服务'''
CacheKey.WEB_RJJH_CATEGORY_SERVICES = 'WEB_RJJH_CATEGORY_SERVICES_%s' # 参数为shop_id

'''软件导航中右上侧消息个数'''
CacheKey.WEB_MSG_COUNT = 'WEB_MSG_COUNT_%s' # 参数为shop_id

'''软件导航中右上侧精灵币个数'''
CacheKey.WEB_JLB_COUNT = 'WEB_JLB_COUNT_%s' # 参数为nick

'''是否需要填写手机号'''
CacheKey.WEB_ISNEED_PHONE = 'WEB_ISNEED_PHONE_%s' # 参数为shop_id

'''用户手机验证码'''
CacheKey.WEB_PHONE_CODE = 'WEB_PHONE_CODE_%s' # 参数为手机号(phone)

'''用户TAPI对象缓存key'''
CacheKey.WEB_USER_TAPI = 'WEB_TAPI_%s_%s' # 参数(%s_%s)对应(key_type, key)，key_type: 1 代表shop_id，2 代表username

'''用户点下载的缓存，保存5分钟，如果用户又点下载，则开始下载全部数据'''
CacheKey.WEB_SYNC_DATA_FLAG = 'WEB_SYNC_DATA_FLAG_%s' # 参数是shop_id

'''同一用户下载的互斥，如果多次点，则无效'''
CacheKey.WEB_SYNC_DATA_MUTUAL = 'WEB_SYNC_DATA_MUTUAL_%s' # 参数是shop_id

'''弹窗类绑定各种信息'''
CacheKey.WEB_POPUP_BIND_DATA_CACHE = "WEB_POPUP_BIND_DATA_CACHE_0804_%s" # 参数是配置名称 加了个数字强制刷新缓存，避免重启缓存

'''元旦活动'''
CacheKey.WEB_YUANDAN_PROM_LOGIN_SHOP = 'WEB_YUANDAN_PROM_LOGIN_SHOP'

'''web_home页面的实时帐户数据'''
CacheKey.WEB_HOME_RTRPT_CUST = 'WEB_HOME_RTRPT_CUST_%s' # 参数为shop_id

'''计划的平台设置缓存'''
CacheKey.WEB_CAMPAIGN_PLATFORM = 'WEB_CAMPAIGN_PLATFORM_%s' # 参数为campaign_id

'''计划的分时折扣缓存'''
CacheKey.WEB_CAMPAIGN_SCHEDULE = 'WEB_CAMPAIGN_SCHEDULE_%s' # 参数为campaign_id

'''计划的地域设置缓存'''
CacheKey.WEB_CAMPAIGN_AREA = 'WEB_CAMPAIGN_AREA_%s' # 参数为campaign_id

'''店铺的自定义类目'''
CacheKey.WEB_SHOP_SELLER_CIDS = 'WEB_SHOP_SELLER_CIDS_%s' # 参数为shop_id

'''店铺的宝贝列表'''
CacheKey.WEB_TOP_ITEM_LIST = 'WEB_TOP_ITEM_LIST_%s' # 参数是shop_id

'''店铺同步报表、获取TOP词的状态'''
CacheKey.WEB_CORE_KEYWORD_STATUS = 'WEB_CORE_KEYWORD_STATUS_%s' #参数shop_id

# ncrm

'''ncrm通用客户群'''
CacheKey.NCRM_COMMON_GROUP_STATISTIC = 'NCRM_COMMON_GROUP_STATISTIC_%s' # 参数为psuser_id {group:count, ...}

'''ncrm店铺余额'''
CacheKey.NCRM_SHOP_BALANCE = 'NCRM_SHOP_BALANCE_%s' # 参数为psuser_id

'''ncrm店铺余额2'''
CacheKey.NCRM_ACCOUNT_BALANCE = 'NCRM_ACCOUNT_BALANCE_%s' # 参数为session

'''ncrm业绩排行榜'''
CacheKey.NCRM_RANKING_LIST = 'NCRM_RANKING_LIST_%s' # 参数为 月份，如 2016-03

'''宝贝列表 一键优化'''
CacheKey.WEB_ONEKEY_OPTIMIZE = 'WEB_ONEKEY_OPTIMIZE_%s_%s' # 参数1为shop_id，参数2为adgroup_id

'''ncrm每日登录用户'''
CacheKey.LOGIN_USERS = 'LOGIN_USERS_%s_%s' # 参数1为psuser_id，参数2为日期，值的格式为{shop_id:[last_login, nick, phone, qq, is_hide, plateform_type], ...}
# ===============================定义CacheKey End==================================================
