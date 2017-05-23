# coding=UTF-8

# for view.py
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.template import RequestContext, loader, Context
from django.views.decorators.cache import cache_page, never_cache
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from datetime import datetime, timedelta, date

# for ajax.py
from django.http import QueryDict
from dajax.core import Dajax

# from apps.common.utils.utils_collection import *
# from apps.common.utils.utils_datetime import *
# from apps.common.utils.utils_mysql import *
# from apps.common.utils.utils_number import *
# from apps.common.biz_utils.utils_sorter import *
# from apps.common.utils.utils_string import *
# from apps.common.biz_utils.utils_permission import *
# from apps.common.biz_utils.utils_misc import *
# from apilib import *
# from apilib import tsapi
