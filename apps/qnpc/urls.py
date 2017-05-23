# coding=UTF-8
from django.conf.urls import patterns, url

from apps.qnpc.views import (qnpc_home, adgroup_list, campaign_list, attention_list,
                             mnt_campaign, choose_mnt_campaign, error, auto_rob_rank,
                             shop_core)

urlpatterns = patterns('',
    url(r'^qnpc_home/$', qnpc_home, name = 'qnpc_home'),
    url(r'^adgroup_list/$', adgroup_list, name = 'qnpc_adgroup_list'),
    url(r'^adgroup_list/(?P<campaign_id>\d+)$', adgroup_list, name = 'qnpc_adgroup_list'),
    url(r'^campaign_list/$', campaign_list, name = 'qnpc_campaign_list'),
    url(r'^attention_list/$', attention_list, name = 'qnpc_attention_list'),
    url(r'^mnt_campaign/(?P<campaign_id>\d+)$', mnt_campaign, name = 'qnpc_mnt_campaign'),
    url(r'^choose_mnt_campaign/(?P<campaign_id>\d+)$', choose_mnt_campaign, name = 'qnpc_choose_mnt_campaign'),
    url(r'^error$', error, name = 'qnpc_error'),
    url(r'^auto_rob_rank/$', auto_rob_rank, name = 'qnpc_auto_rob_rank'),
    url(r'^shop_core/$', shop_core, name = 'qnpc_shop_core'),
)
