# coding=UTF-8
from django.conf.urls import patterns, url

from apps.qnyd.views import router, qnyd_redirect
from apps.qnyd.najax import route_ajax

urlpatterns = patterns('',

    url(r'^home', router, name = 'qnyd_home'),
    # ajax方法，指定到新的方法
    url(r'^ajax/$', route_ajax),
)
