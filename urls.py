# coding=UTF-8
import os.path

from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin

from api_router import dispatch

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^api_router$', dispatch, name = 'api'),
    # url(r'^$', 'router.views.main_port', name = 'main_port0'),
    # TODO 服务后台写的旧入口，已改为新入口，但不是立即生效，所以先保留一段时间
    url(r'^main_port_new/$', 'router.views.main_port_qnpc', name = 'main_port_new'),
    url(r'^main_port_yd/$', 'router.views.main_port_qnyd', name = 'main_port_yd'),

    url(r'^main_port/$', 'router.views.main_port_web', name = 'main_port'),
    url(r'^main_port_web/$', 'router.views.main_port_web', name = 'main_port_web'),
    url(r'^main_port_pcww/$', 'router.views.main_port_web', name = 'main_port_pcww'),
    url(r'^main_port_qnpc/$', 'router.views.main_port_qnpc', name = 'main_port_qnpc'),
    url(r'^main_port_qnyd/$', 'router.views.main_port_qnyd', name = 'main_port_qnyd'),
    url(r'^sub_port/$', 'router.views.sub_port', name = 'sub_port'),
    url(r'^login/$', 'ncrm.views.login', name = 'login'),
    url(r'^agent_login/$', 'web.views.agent_login', name = 'agent_login'),
    url(r'^websocket/$', 'web.views.echo', name = 'websocket'),

    (r'^web/', include('web.urls')),
    (r'^mnt/', include('mnt.urls')),
    (r'^crm/', include('crm.urls')),
    (r'^ncrm/', include('ncrm.urls')),
    (r'^router/', include('router.urls')),
    (r'^toolkit/', include('toolkit.urls')),
    (r'^qnyd/', include('qnyd.urls')),
    (r'^qnpc/', include('qnpc.urls')),
    (r'^%s/' % settings.ADMIN_URL, include(admin.site.urls)),
    (r'^%s/' % settings.DAJAX_MEDIA_PREFIX, include('dajax.urls')),
)

if settings.DEBUG:
# if 1:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(os.path.dirname(__file__), "site_media")}),
    )
