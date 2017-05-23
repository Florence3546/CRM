# coding=UTF-8
from django.conf.urls import patterns, url

from apps.toolkit.views import select_keyword_new
from apps.toolkit.ajax import route_ajax

urlpatterns = patterns('',
    url(r'^select_keyword_order/$', select_keyword_new, name = 'select_keyword_order'),
    url(r'^ajax/$', route_ajax),
    )
