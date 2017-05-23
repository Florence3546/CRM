# coding=UTF-8
from django.conf.urls import patterns, url

from apps.mnt.views import mnt_campaign, adgroup_data, choose_mnt_campaign
from apps.mnt.najax import route_ajax

urlpatterns = patterns('',
    url(r'^mnt_campaign/(?P<campaign_id>\d+)$', mnt_campaign, name = 'mnt_campaign'),
    url(r'^adgroup_data/(?P<adgroup_id>\d+)/$', adgroup_data, name = 'adgroup_data'),
    url(r'^choose_mnt_campaign/(?P<campaign_id>\d+)$', choose_mnt_campaign, name = 'choose_mnt_campaign'),

    # ajax方法，指定到新的方法
    url(r'^ajax/$', route_ajax),
)
