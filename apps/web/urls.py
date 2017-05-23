# coding=UTF-8
from django.conf.urls import patterns, url

from apps.web.views import (web_home, all_history, duplicate_check, echo,
                            attention_list, bulk_optimize, smart_optimize, check_danger_cats, title_optimize,
                            select_keyword, ztc_health_check, adgroup_health_check, upgrade_suggest, rob_rank, deleted_keyword,
                            vip_home, point_mall, point_praise, point_record_appraise, creative_optimization,
                            invite_friend, user_config, agent_login_in, advertisement, redirect_sale_link, image_optimize,
                            paithink_services, help_center, history, redirect_generate_link, op_history, lottery_coupon,
                            upload_item_img, hand_optimize, auto_rob_rank, shop_core)
from apps.web.najax import route_ajax

urlpatterns = patterns('',
    url(r'^echo/$', echo),
    url(r'^web_home/$', web_home, name = 'web_home'),
    url(r'^all_history/$', all_history, name = 'all_history'),
    url(r'^duplicate_check/$', duplicate_check, name = 'duplicate_check'),
    url(r'^attention_list/$', attention_list, name = 'attention_list'),
    url(r'^bulk_optimize/(?P<adgroup_id>\d+)/$', bulk_optimize, name = 'adgroup_optimize'),
    url(r'^bulk_optimize/(?P<adgroup_id>\d+)/(?P<inner>[\w]*)/$', bulk_optimize, name = 'adgroup_optimize'),
    url(r'^bulk_optimize/(?P<adgroup_id>\d+)/(?P<executor>[\w]*)/(?P<cfg>[\w]*)/$', bulk_optimize, name = 'adgroup_optimize'),
    url(r'^smart_optimize/(?P<adgroup_id>\d+)/$', smart_optimize, name = 'smart_optimize'),
    url(r'^smart_optimize/(?P<adgroup_id>\d+)/(?P<inner>[\w]*)/$', smart_optimize, name = 'smart_optimize'),
    url(r'^smart_optimize/(?P<adgroup_id>\d+)/(?P<executor>[\w]*)/(?P<cfg>[\w]*)/$', smart_optimize, name = 'smart_optimize'),

    url(r'^check_danger_cats/$', check_danger_cats, name = 'check_danger_cats'),

    url(r'^title_optimize/$', title_optimize, name = 'title_optimize'), # 测试URL：http://localhost/web/title_optimize/?item_id=18426453412
    url(r'^quick_add_keyword/$', select_keyword, {'select_type':'quick'}, name = 'quick_add_keyword'),
    url(r'^precise_tao_keyword/$', select_keyword, {'select_type':'precise'}, name = 'precise_tao_keyword'),
    url(r'^auto_combine_words/$', select_keyword, {'select_type':'combine'}, name = 'auto_combine_words'),
    url(r'^manual_add_words/$', select_keyword, {'select_type':'manual'}, name = 'manual_add_words'),
    url(r'^select_keyword/(?P<select_type>[\w]*)$', select_keyword, name = 'select_keyword'),

    url(r'^ztc_health_check/$', ztc_health_check, name = 'ztc_health_check'),
    url(r'^adgroup_health_check/(?P<adgroup_id>\d+)$', adgroup_health_check, name = 'adgroup_health_check'),

    url(r'^upgrade_suggest/$', upgrade_suggest, name = 'upgrade_suggest'),
    url(r'^lottery_coupon/$', lottery_coupon, name = 'lottery_coupon'),
    url(r'^rob_rank/(?P<adgroup_id>\d+)/$', rob_rank, name = 'rob_rank'),
    url(r'^deleted_keyword/(?P<adgroup_id>\d+)/$', deleted_keyword, name = 'deleted_keyword'),

    url(r'vip_home/$', vip_home, name = 'vip_home'),
    url(r'point_mall/$', point_mall, name = 'point_mall'),
    url(r'point_praise/$', point_praise, name = 'point_praise'),
#     url(r'point_record_renewal/$', point_record_renewal, name = 'point_record_renewal'),
    url(r'point_record_appraise/$', point_record_appraise, name = 'point_record_appraise'),
    url(r'invite_friend/$', invite_friend, name = 'invite_friend'),
    url(r'user_config/$', user_config, name = 'user_config'),
    url(r'agent_login_in/$', agent_login_in, name = 'agent_login_in'),
    # url(r'register/$', register_services, name = 'register_server'),
    url(r'creative_optimization/(?P<adgroup_id>\d+)/$', creative_optimization, name = 'creative_optimization'),
    url(r'paithink_services/(?P<id>\d+)$', paithink_services, name = 'paithink_services'),
    url(r'^help/$', help_center, name = 'help_center'),
    url(r'^history/$', history, name = 'history'),
    url(r'^ad/(?P<ad_no>\d+)/$', advertisement, name = 'advertisement'),
    url(r'^redirect_generate_link/$', redirect_generate_link, name = 'redirect_generate_link'),
    url(r'^redirect_sale_link/$', redirect_sale_link, name = 'redirect_sale_link'),
    url(r'^image_optimize/(?P<adgroup_id>\d+)/$', image_optimize, name = 'image_optimize'),
    url(r'^upload_item_img/$', upload_item_img, name = 'upload_item_img'),

    # ajax方法，指定到新的方法
    url(r'^ajax/$', route_ajax),

    # 手动优化宝贝页面
    url(r'^hand_optimize/$', hand_optimize, name = 'hand_optimize'),
    url(r'^hand_optimize/(?P<campaign_id>\d+)$', hand_optimize, name = 'hand_optimize'),

    # 操作记录页面
    url(r'^op_history/$', op_history, name = 'op_history'),
    url(r'^auto_rob_rank/$', auto_rob_rank, name = 'auto_rob_rank'),
    url(r'^shop_core/$', shop_core, name = 'shop_core'),
    )
