from django.conf.urls import patterns, url

urlpatterns = patterns('',
						url(r'^(.*)\.([^\.]*)/$', 'dajax.views.dajax_request'),
						url(r'^dajax.core.js$', 'dajax.views.js_core'),
						url(r'^.*$', 'dajax.views.dajax_error'),
						)