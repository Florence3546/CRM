from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect

from dajax.core import DajaxRequest


def dajax_request(request, app_name, method):
	"""
	dajax_request
	Uses DajaxRequest to handle dajax request.
	Return the apropiate json according app_name and method.
	"""
	dr = DajaxRequest(request, app_name, method)
	return dr.process()

def js_core(request):
	"""
	Return the dajax JS code according settings.DAJAX_FUNCTIONS registered functions.
	"""
	def sanitize_js_names(name):
		name = name.rsplit('.',1)[0]
		return (name.replace('.','_'),name,)
	
	dajax_js_modules = [ sanitize_js_names(f.rsplit('.',1)[0]) for f in DajaxRequest.get_dajax_functions() ]
	dajax_js_functions_names = [ f.rsplit('.',1)[1] for f in DajaxRequest.get_dajax_functions() ]
	dajax_js_functions = zip(dajax_js_modules, dajax_js_functions_names)

	data = {'dajax_js_functions':dajax_js_functions, 'DAJAX_URL_PREFIX': DajaxRequest.get_media_prefix()}
	js_framework = DajaxRequest.get_dajax_js_framework().lower()
	
	try:
		return render_to_response('dajax/%s.dajax.core.js' % js_framework, data )
	except:
		raise Exception("This JS Framework isn't available.")

def dajax_error(request):
	"""
	Redirect if the url is invalid and settings.DAJAX_REDIRECT_ERROR exists.
	"""
	if DajaxRequest.get_dajax_redirect_error() != None:
		return HttpResponseRedirect( DajaxRequest.get_dajax_redirect_error() )
	else:
		raise Exception("Dajax URL is not valid.")