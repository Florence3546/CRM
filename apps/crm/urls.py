# coding=UTF-8
from django.conf.urls import patterns, url
from apps.crm.views import (user_list, crm_account, crm_campaign, crm_adgroup, crm_keyword, category_list, selection_word_manager,
                            manager_mntcfg, crm_url_redirect, test_select_words, kw_manage, crm_logout
                            )
# from apps.cf.views import designer_home, consult_home

urlpatterns = patterns('',

    url(r'^user_list/(?P<flag>[\w]*)/$', user_list, name = 'user_list'),
    url(r'^user_list/$', user_list, name = 'crm_user_list'),

    # url(r'^add_point/$', add_point, name = 'add_point'),

    url(r'^crm_account/$', crm_account, name = 'crm_account'),
    url(r'^crm_campaign/$', crm_campaign, name = 'crm_campaign'),
    url(r'^crm_adgroup/$', crm_adgroup, name = 'crm_adgroup'),
    url(r'^crm_keyword/$', crm_keyword, name = 'crm_keyword'),

    url(r'^crm_category_list', category_list, name = 'category_list'), # 待定
    url(r'^selection_word_manager', selection_word_manager),

    # 编辑全自动配置
    # url(r'^manager_mntcfg/$', manager_mntcfg, name = 'manager_mntcfg'),

    # crm URL 跳转
    url(r'^crm_redirect', crm_url_redirect),

    # CRM 选词预览
    url(r'^test_select_words/$', test_select_words),

    # kwlib 迁移过来
    url(r'^kw_manage', kw_manage, name = 'kw_manage'),

    url(r'crm_logout/$', crm_logout, name = 'crm_logout'),

    # 创意工厂
    # url(r'^cf_designer/$', designer_home, name = 'cf_designer_home'),
    # url(r'^cf_consult/$', consult_home, name = 'cf_consult_home'),
)
