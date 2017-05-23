# coding=utf-8
import os

from django.conf import settings

from dajax.core import Dajax
from apps.common.utils.utils_log import log

try:
    from django.utils import importlib
    DAJAX_MODERN_IMPORT = True
except:
    DAJAX_MODERN_IMPORT = False

class DajaxRequest:
    """
    DajaxRequest Class.
    """

    def __init__(self, request, app_name, method):
        self.app_name = app_name
        self.method = method
        self.request = request

        self.project_name = os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0]
        self.module = "%s.ajax" % self.app_name
        self.full_name = "%s.%s" % (self.module, self.method,)
        # self.module_import_name = "%s.%s" % ( self.project_name, self.module)
        self.module_import_name = "%s" % (self.module) # modify by hehao


    def is_callable(self):
        """
        Return if the request function was registered.
        """
        if self.full_name in settings.DAJAX_FUNCTIONS:
            return True
        return False

    @staticmethod
    def get_dajax_error_callback():
        return getattr(settings, 'DAJAX_ERROR_CALLBACK', None)

    @staticmethod
    def get_media_prefix():
        return getattr(settings, 'DAJAX_MEDIA_PREFIX', "dajax")

    @staticmethod
    def get_dajax_functions():
        return getattr(settings, 'DAJAX_FUNCTIONS', ())

    @staticmethod
    def get_dajax_js_framework():
        return getattr(settings, 'DAJAX_JS_FRAMEWORK', "Prototype")

    @staticmethod
    def get_dajax_redirect_error():
        return getattr(settings, 'DAJAX_REDIRECT_ERROR', None)

    @staticmethod
    def get_dajax_debug():
        return getattr(settings, 'DAJAX_DEBUG', True)

    def get_ajax_function(self):
        """
        Return a callable ajax function.
        This function should be imported according the Django version.
        """
        if DAJAX_MODERN_IMPORT:
            return self.__modern_get_ajax_function()
        else:
            return self.__old_get_ajax_function()

    def __old_get_ajax_function(self):
        """
        Return a callable ajax function.
        This function doesn't uses django.utils.importlib
        """
        mod = __import__(self.module_import_name , None, None, [self.method])

        try:
            thefunction = mod.__getattribute__(self.method)
            return thefunction
        except AttributeError:
            raise Exception("%s function doesn't exists inside %s" % (self.method, self.full_name,))
        except Exception:
            raise


    def __modern_get_ajax_function(self):
        """
        Return a callable ajax function.
        This function uses django.utils.importlib
        """
        from django.utils import importlib
        # mod = importlib.import_module(self.module_import_name) #move to try ... except...by hehao

        try:
            mod = importlib.import_module(self.module_import_name)
            thefunction = mod.__getattribute__(self.method)
            return thefunction
        except AttributeError:
            raise Exception("%s function doesn't exists inside %s" % (self.method, self.full_name,))
        except Exception, e:
            log.error("DajaxRequest.__modern_get_ajax_function raise error, %s" % e)
            raise


    def process(self):
        """
        Process the dajax request calling the apropiate method.
        """
        if self.is_callable():
            # 1. get the function
            thefunction = self.get_ajax_function()

            # 2. call the function
            try:
                response = thefunction(self.request)
                if isinstance(response, Dajax):
                    return response.render()
                else:
                    return response
            except Exception, e:
                log.exception("dajax error, e=%s" % (e)) # added by hehao
                # Development Server Debug
                if settings.DEBUG and DajaxRequest.get_dajax_debug():
                    import traceback
                    from dajax.utils import print_green_start, print_blue_start, print_clear, print_red

                    print_green_start()
                    print "#" * 50
                    print "uri:      %s" % self.request.build_absolute_uri()
                    print "function: %s" % self.full_name
                    print "#" * 50
                    print ""
                    print_red(str(e))
                    print_blue_start()
                    traceback.print_exc(e)
                    print_clear()

                # If it's an ajax request we need soft debug
                # http://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.is_ajax
                if self.request.is_ajax():
                    # If project was in debug mode, alert with Exception info
                    # if settings.DEBUG:#modified by hehao
                    if True:
                        response = Dajax()
                        # response.alert('Exception %s: Check %s manually for more information or your server log.' % (str(e), self.request.get_full_path()))
                        response.alert(u'亲，出错啦，请联系您的顾问！')
                        return response.render()
                    # If not, check DAJAX_ERROR_CALLBACK, if present call this function
                    # elif DajaxRequest.get_dajax_error_callback() != None:#modified by hehao
                    if DajaxRequest.get_dajax_error_callback() != None:
                        response = Dajax()
                        response.script(DajaxRequest.get_dajax_error_callback() % str(e))
                        return response.render()
                    # Otherside ... raise Exception
                    else:
                        raise
                # If it's a non-ajax request raise Exception, Django cares.
                else:
                    raise
        else:
            raise Exception("Function not callable.")
