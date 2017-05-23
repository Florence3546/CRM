
# coding=UTF-8
from django.conf.urls import patterns, url

from apps.ncrm.views import (
    crm_home, plan_list, child_plan, edit_plan, del_plan, create_plan, lower_detail, event_detail, order_manage,
    add_client, advance_query, generate_customer_csv_byquery, edit_customer, edit_subscribe, login_ztc, login_kcjl,
    login_test, myworkbench, workbench, diary_list, change_psw, psuser_contact, psuser_roster,
    ncrm_psuser_roster, ncrm_add_psuser, check_log, rpt_snap, task_rpt, point_manager,
    sale_link, short_message_manage, consult_manager, export_customer_data, event_statistic,
    main_ad_manage, create_main_ad, update_main_ad, strategy_cfg, work_reminder, login_users, subscribe_analyze,
    feedback,
    category_tree, edit_category_tree, bulk_optimize, metric_statistic, metric_statistic_rjjh, order_dunning, echo_msg,
    performance, unsubscribe_manage, approval_subscribe,
    export_contract_file, upload_contract_file, performance_income, adgroup_top, operating_rpt, operating_rpt1,
    edit_plan_tree, plan_tree,
    metric_statistic_old, xfgroup_manage, add_xfgroup, comment_manage,
    record_distribute, download_file, pre_sales_advice)

from apps.ncrm.ajax import upload_chat_file, edit_sb_upload_file, del_chat_file

urlpatterns = patterns('',
    url(r'^crm_home$', crm_home, name = 'crm_home'),
    url(r'^plan_list/$', plan_list, name = 'plan_list'),
    url(r'^plan_list/(?P<psuser_id>\d+)/$', plan_list, name = 'plan_list'),
    url(r'^child_plan/(?P<plan_id>\d+)/$', child_plan, name = 'child_plan'),
    url(r'^edit_plan/(?P<plan_id>\d+)/$', edit_plan, name = 'edit_plan'),
    url(r'^del_plan/(?P<plan_id>\d+)/$', del_plan, name = 'del_plan'),
    # url(r'^user_list/$', user_list, name = 'user_list'),
    # url(r'^user_list/(?P<page>\d+)/$', user_list, name = 'user_list'),
    url(r'^create_plan/$', create_plan, name = 'create_plan'),
    url(r'^create_plan/(?P<parent_id>\d+)/$', create_plan, name = 'create_plan'),
    url(r'^lower_detail/(?P<plan_id>\d+)/$', lower_detail, name = 'lower_detail'),
    url(r'^event_detail/$', event_detail, name = 'event_detail'),
    url(r'^event_statistic/$', event_statistic, name = 'event_statistic'),
    url(r'^order_manage/$', order_manage, name = 'order_manage'),
    # url(r'^client_group/$', client_group, name = 'client_group'),
    url(r'^add_client/(?P<id>\d+)/(?P<page>\d+)/$', add_client, name = 'add_client'),
    url(r'^advance_query/(?P<client_group_id>\d+)/(?P<page>\d+)/$', advance_query, name = 'advance_query'),
    url(r"generate_customer_csv_byquery", generate_customer_csv_byquery, name = "generate_customer_csv"),
    # url(r'^client_detial/(?P<id>\d+)/(?P<page>\d+)/$', client_detial, name = 'client_detial'),
    # url(r'^delete_client/(?P<id>\d+)/$', delete_client, name = 'delete_client'),
    url(r'^edit_customer/$', edit_customer, name = 'edit_customer'),
    url(r'^edit_subscribe/$', edit_subscribe, name = 'edit_subscribe'),
    url(r'^login_ztc/(?P<shop_id>\d+)/$', login_ztc, name = 'login_ztc'),
    url(r'^login_kcjl/(?P<mode>[a-z]+)/(?P<shop_id>\d+)/$', login_kcjl, name = 'login_kcjl'),
    url(r'^login_test/(?P<shop_id>\d+)/$', login_test),

    url(r'^myworkbench/$', myworkbench, name = 'myworkbench'),
    url(r'^workbench/(?P<work_type>[\w]+)/(?P<page>\d+)/$', workbench, name = 'workbench'),
    url(r'^export_customer_data/$', export_customer_data, name = 'export_customer_data'),

    url(r'^diary_list/(?P<name>[\w]+)/$', diary_list, name = 'diary_list'),
    url(r'^change_psw/$', change_psw, name = 'change_psw'),
    url(r'^psuser_contact/$', psuser_contact, name = 'psuser_contact'),
    url(r'^psuser_roster/$', psuser_roster, name = 'psuser_roster'),
    url(r'^ncrm_psuser_roster/$', ncrm_psuser_roster, name = 'ncrm_psuser_roster'),
    url(r'^ncrm_add_psuser/$', ncrm_add_psuser, name = 'ncrm_add_psuser'),

    # url(r'^logout/', 'django.contrib.auth.views.logout', {"template_name": "ncrm_logout.html"}, name = "ncrm_logout"),
    url(r'^logout/', 'django.contrib.auth.views.logout', {"next_page": "/login"}, name = "ncrm_logout"),

    # 人事检查日志URL
    url(r'^check_log/$', check_log, name = 'check_log'),

    # 统计分析报表
    url(r'^rpt_snap/$', rpt_snap, name = 'rpt_snap'),
    url(r'^task_rpt/$', task_rpt, name = 'task_rpt'),

    # 全自动算法策略配置页面
    url(r'^stg_cfg/$', strategy_cfg, name = 'strategy_cfg'),

    # 从TOP控制台收录开车精灵和千牛订单
    url(r'^point_manager/$', point_manager, name = 'crm_point_manager'),

    # 推广链接
    url(r'^sale_link/$', sale_link, name = 'sale_link'),
    # 短信管理
    url(r'^short_message_manage/$', short_message_manage, name = 'short_message_manage'),

    # 分发客户
    url(r'consult_manager/$', consult_manager, name = 'consult_manager'),

    # 广告管理
    url(r'^main_ad_manage/$', main_ad_manage, name = 'main_ad_manage'),

    # 创建广告
    url(r'^create_main_ad/$', create_main_ad, name = 'create_main_ad'),

    # 修改广告
    url(r'^update_main_ad/$', update_main_ad, name = 'update_main_ad'),

    # 工作提醒
    url(r'^work_reminder/$', work_reminder, name = 'work_reminder'),

    # 今日登录客户
    url(r'^login_users/$', login_users, name = 'login_users'),

    # 订单分析
    url(r'^subscribe_analyze/$', subscribe_analyze, name = 'subscribe_analyze'),

    # 客户反馈
    url(r'^feedback/$', feedback, name = 'ncrm_feedback'),

    # 客户分类树
    url(r'^category_tree/$', category_tree, name = 'category_tree'),
    url(r'^plan_tree/$', plan_tree, name = 'plan_tree'),

    # 新批量优化页面
    url(r'^bulk_optimize/$', bulk_optimize, name = 'ncrm_bulk_optimize'),

    # 编辑客户分类树
    url(r'^edit_category_tree/$', edit_category_tree, name = 'edit_category_tree'),
    url(r'^edit_plan_tree/$', edit_plan_tree, name = 'edit_plan_tree'),

    url(r'^operating_rpt/$', operating_rpt, name = 'operating_rpt'),
    url(r'^operating_rpt1/$', operating_rpt1, name = 'operating_rpt1'),
    url(r'^adgroup_top/$', adgroup_top, name = 'adgroup_top'),
    url(r'^performance/$', performance, name = 'performance'),
    url(r'^upload_contract_file/$', upload_contract_file, name = 'upload_contract_file'),
    url(r'^export_contract_file/(?P<subscribe_id>\d+)/$', export_contract_file, name = 'export_contract_file'),
    url(r'^performance_income/$', performance_income, name = 'performance_income'),
    url(r'^approval_subscribe/(?P<page_no>\d+)/$', approval_subscribe, name = 'approval_subscribe'),
    url(r'^approval_subscribe', approval_subscribe, name = 'approval_subscribe'),
    url(r'^comment_manage', comment_manage, name = 'comment_manage'),
    url(r'^metric_statistic/$', metric_statistic, name = 'metric_statistic'),
    url(r'^metric_statistic/rjjh/$', metric_statistic_rjjh, name = 'metric_statistic_rjjh'),
    url(r'^metric_statistic_old/$', metric_statistic_old, name = 'metric_statistic_old'),
    url(r'^order_dunning/$', order_dunning, name = 'order_dunning'),
    url(r'^record_distribute/$', record_distribute, name = 'record_distribute'),
    # url(r'^order_dunning/(?P<view_type>[\w]+)$', order_dunning, name = 'order_dunning'),
    url(r'^echo_msg/$', echo_msg, name = "echo_msg"),

    # 退款审计
    url(r'^unsubscribe_manage/$', unsubscribe_manage, name = "unsubscribe_manage"),
    url(r'^xfgroup_manage/$', xfgroup_manage, name = "xfgroup_manage"),
    url(r'^add_xfgroup/$', add_xfgroup, name = "add_xfgroup"),

    # 文件上传，下载
    url(r'^upload_file/$', upload_chat_file, name="upload_file"),
    url(r'^download_file/$', download_file, name="download_file"),
    # 编辑人工签单，上传图片
    url(r'^edit_sb_upload_file/$', edit_sb_upload_file, name="edit_sb_upload_file"),
    url(r'^del_chat_file/$', del_chat_file, name="del_chat_file"),
	# 售前咨询
	url(r'^pre_sales_advice/$', pre_sales_advice, name='pre_sales_advice'),
)
