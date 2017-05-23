# coding=UTF-8
from django.conf.urls import patterns, url

from apps.router.views import waiting, backend_login, top_logout

urlpatterns = patterns('',
    url(r'^waiting/(?P<prefix>\w+)/$', waiting, name = 'waiting'),
    url(r'^backend_login/$', backend_login, name = 'backend_login'),
#     url(r'^logout/$', 'django.contrib.auth.views.logout', {"template_name": "logout.html"}, name = "top_logout"),
    url(r'^top_logout/(?P<theme>\w+)/$', top_logout, name = "top_logout"),
    )
