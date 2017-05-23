# coding=UTF-8
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

from django.utils.importlib import import_module
from django.conf import settings

from apilib.binder import bind_api
from apilib.parsers import TopObjectParser
from apilib.auth import JAuthHandler


class JAPI(object):
    def __init__(self, auth_handler = None,
            host = '', api_root = '/api_router', # API_URL = 'http://gw.api.tbsandbox.com/router/rest',API_URL = 'http://gw.api.taobao.com/router/rest '
            cache = None, secure = False,
            retry_count = 0, retry_delay = 0, retry_errors = None,
            parser = None, log = None, timeout = None, is_quick_send = False):
        self.auth = auth_handler or JAuthHandler(settings.JAPI_SECRET)
        self.host = host
        self.api_root = api_root
        self.cache = cache
        self.secure = secure
        self.retry_count = retry_count or settings.JAPI_RETRY_COUNT
        self.retry_delay = retry_delay or settings.JAPI_RETRY_DELAY
        self.retry_errors = retry_errors
        self.is_quick_send = is_quick_send
        self.parser = parser or TopObjectParser()
        self.log = log
        self.timeout = timeout

    #=====================START:keyword library API interface=====================
    #===========================new kwlib api tidy================================

    # 通过方法名以及要获取的属性来获取类目下的数据
    get_cat_data_by_func = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'get_cat_data_by_func'
    )

    set_cat_data = bind_api(
        app_name = "kwlib",
        method = "POST",
        method_name = "set_cat_date"
    )

    get_danger_info = bind_api(
        app_name = "kwlib",
        method = "POST",
        method_name = "get_danger_info"
    )

    get_sale_word_list = bind_api(
        app_name = "kwlib",
        method = "POST",
        method_name = "get_danger_info"
    )

    check_cat_exist = bind_api(
        app_name = "kwlib",
        method = "POST",
        method_name = "check_cat_exist"
    )

    get_init_obj = bind_api(
        app_name = "kwlib",
        method = "POST",
        method_name = "get_init_obj"
    )

    cat_attr_save = bind_api(
        app_name = "kwlib",
        method = "POST",
        method_name = "cat_attr_save"
    )

    #===========================new kwlib api tidy================================

    # 获取词根热度
#     get_word_hot = bind_api(
#         app_name = 'kwlib',
#         method = 'POST',
#         method_name = 'get_word_hot'
#     )
    # 为长尾托管选词
    select_word_4gsw = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'select_word_4gsw'
    )
    # 农民工干活接口
    worker_work = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'worker_work'
    )
    # 获取宝贝的相关关键词，包括从大词库、淘宝推荐词、词扩展的方式获取
    get_relatedkeyword_from_kwlib = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'get_relatedkeyword_from_kwlib'
    )
    prepare_quick_select = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'prepare_quick_select'
    )
    # 通过item_id获取200个以内的关键词
    get_keyword_by_item_id = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'get_keyword_by_item_id'
    )

    # 获取类目中的名称
    get_cat_path = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_cat_path'
    )
    # 获取catid路径
    get_catid_path = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_catid_path'
    )
    # 获取类目全路径及其全ID
    get_full_name_path = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_full_name_path'
    )
    # 获取类目的根类目ID
    get_root_cat = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_root_cat'
    )
    # 获取一个类目的下一级子类目
    get_subcat_list = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_subcat_list'
    )
    # 获取一个类目下的所有子类目
    get_all_subcats = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_all_subcats'
    )
    # 获取所有类目的类目ID、类目名
    get_all_cats = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_all_cats'
    )
    # 获取某个类目的祖先类目，从父类目到根类目
    get_ancestral_cats = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_ancestral_cats'
    )
    # 获取危险类目
    get_danger_cat_list = bind_api(
            app_name = 'kwlib',
            method_name = 'get_danger_cat_list'
    )
    # 对宝贝批量铺关键词
    get_batch_words = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'get_batch_words'
    )

    # 对标题进行分解
    split_title_from_cat = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'split_title_from_cat'
    )
    # 将单个宝贝标题拆分成词根
    split_title_new_to_list = bind_api(
            app_name = 'kwlib',
            method = 'POST',
            method_name = 'split_title_new_to_list'
    )
    # 获取推广标题
    generate_adg_title = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'generate_adg_title'
    )
    # 获取双推广标题
    generate_adg_title_list = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'generate_adg_title_list'
    )
    # 获取宝贝的产品词和修饰词
    get_product_decorate_words = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'get_product_decorate_words'
    )
    # 查询某个类目下的统计数据
    get_cat_stat_info = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'get_cat_stat_info'
    )
    # 启用大词库更新禁用词数据
    register_forbidden_word_update = bind_api(
        method = 'POST',
        app_name = 'kwlib',
        method_name = 'register_forbidden_word_update'
    )
    # 获取宝贝词根
#     get_kw_dict_byelemword = bind_api(
#         app_name = 'kwlib',
#         method = 'POST',
#         method_name = 'get_kw_dict_byelemword'
#     )
    # 获取宝贝词根
#     get_title_info_dict = bind_api(
#         app_name = 'kwlib',
#         method = 'POST',
#         method_name = 'get_title_info_dict'
#     )
    # 获取类目大流量词根
    get_cat_elemword_dict = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'get_cat_elemword_dict'
    )
    # 从词库获取词到前台爬词
    get_wanna_claw_wds_list = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'get_wanna_claw_wds_list'
    )
    # 将前台爬来的词送回到词库（检验爬进来的词是否违规）
    check_clawed_wds = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'check_clawed_wds'
    )
    # 新版本的爬词从词库取词
    get_keyword_for_claw = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'get_keyword_for_claw'
    )
    # 将新版本的爬来的词和标签送回到词库
    save_new_claw_result = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'save_new_claw_result'
    )
    # 远程修改加载到内存当中的数据
    other_service_request_load_memery = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'other_service_request_load_memery'
    )
    #=====================词库维护======================================#
    start_load_data_inmemcache = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'start_load_data_inmemcache'
    )
    insert_word_2DB = bind_api(
        app_name = 'kwlib',
        method = 'POST',
        method_name = 'insert_word_2DB'
    )
    start_update_wordcat = bind_api(
        app_name = 'kwlib',
        method_name = 'start_update_wordcat'
    )
    start_update_keyword = bind_api(
        app_name = 'kwlib',
        method_name = 'start_update_keyword'
    )
    start_new_word_forecast = bind_api(
        app_name = 'kwlib',
        method_name = 'start_new_word_forecast'
    )
    start_get_word_forecast = bind_api(
        app_name = 'kwlib',
        method_name = 'start_get_word_forecast'
    )
    start_get_reteled_word = bind_api(
        app_name = 'kwlib',
        method_name = 'start_get_reteled_word'
    )
    #=====================START: web JAPI 定义开始=======================
    start_engine = bind_api(
        app_name = 'web',
        method_name = 'start_engine'
    )
    #=====================START: gsw JAPI 定义开始=======================
    clear_deleted_words = bind_api(
        app_name = 'web',
        method_name = 'clear_deleted_words'
    )
    # TODO： wangqi 2013-10-22 有些API可能用不上，因为web数据库共享了
    add_permission_at_web = bind_api(
        app_name = 'web',
        method_name = 'add_permission_at_web'
    )
    #===================提供给军哥的接口=================================
    ump_promotion_get = bind_api(
        app_name = 'kwlib',
        method_name = 'ump_promotion_get'
    )


    #=====================START: common JAPI 定义开始=======================
    get_new_thread_list = bind_api(
        app_name = 'common',
        method_name = 'get_new_thread_list'
    )
    trigger_thread = bind_api(
        app_name = 'common',
        method_name = 'trigger_thread'
    )

    #=====================START:crm API interface=======================
    run_crm_download = bind_api(
        app_name = 'crm',
        method_name = 'run_crm_download'
    )
    send_oparlog_2hh = bind_api(
        app_name = 'crm',
        method_name = 'send_oparlog_2hh'
    )

    #=====================START:for other isv API interface=======================
    isv_get_item = bind_api(
        app_name = 'web',
        method_name = 'isv_get_item',
        method = "POST"
    )
    isv_get_itemcats = bind_api(
        app_name = 'web',
        method_name = 'isv_get_itemcats'
    )
    isv_get_account_rpt = bind_api(
        app_name = 'web',
        method_name = 'isv_get_account_rpt'
    )
    isv_get_select_word = bind_api(
        app_name = 'web',
        method_name = 'isv_get_select_word'
    )
    isv_get_split_title = bind_api(
        app_name = 'web',
        method_name = 'isv_get_split_title'
    )
    isv_get_related_words = bind_api(
        app_name = 'web',
        method_name = 'isv_get_related_words'
    )
    isv_get_top_words = bind_api(
        app_name = 'web',
        method_name = 'isv_get_top_words'
    )

    #=====================START:for message  API interface=======================
    router_message = bind_api(
        app_name = 'web',
        method_name = 'router_message',
        method = 'POST'
    )

api_cfg = {}
def get_api_cfg():
    global api_cfg
    if len(api_cfg) == 0:
        host_cfg = settings.APP_CONFIG
        api_cfg = {
            'web':{'host':host_cfg['web'][0], 'port':host_cfg['web'][1], 'module':import_module('web.api'), 'log':None},
            'kwlib':{'host':host_cfg['kwlib'][0], 'port':host_cfg['kwlib'][1], 'module':import_module('kwlib.api'), 'log':None},
            'kwlib_maintain':{'host':host_cfg['kwlib'][0], 'port':host_cfg['kwlib'][1], 'module':import_module('kwlib.api'), 'log':None},
         }

        #=======================================================================
        # #host_cfg的配置格式：app_alias:[host, port, app_name]，app_alias可以任意设置，但app_name必须与apps下的目录相同
        # for module_name, module_cfg in host_cfg.items():
        #     api_cfg.update({module_name:{'host':module_cfg[0], 'port':module_cfg[1], 'module':import_module('%s.api' % module_cfg[2]), 'log':None}})
        #=======================================================================
    return api_cfg

class ApiCreator(object):
    """用于创建不同的api"""
    def __init__(self, module_name):
        self.module_name = module_name
        self.cfg = get_api_cfg()[self.module_name]

    def __call__(self, inner = False, host = ''):
        """执行api"""
        if inner:
            return self.cfg['module']
        else:
            return JAPI(host = (host and ':' in host) and host or '%s:%s' % (host or self.cfg['host'], self.cfg['port']), log = self.cfg['log'])

def web_api(inner = False, host = ''):
    return ApiCreator('web')(inner = inner, host = host)

def kwlib_api(inner = False, host = ''):
    return ApiCreator('kwlib')(inner = inner, host = host)

def kwlib_maintain_api(inner = False, host = ''):
    return ApiCreator('kwlib_maintain')(inner = inner, host = host)

def get_api(app_name, inner = False, host = ''):
    """原来有的接口保留，用于timer"""
    cfg = get_api_cfg()[app_name]
    if inner:
        return cfg['module']
    else:
        return JAPI(host = (host and ':' in host) and host or '%s:%s' % (host or cfg['host'], cfg['port']), log = cfg['log'])
