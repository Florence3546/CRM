# coding=UTF-8

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response

from apps.subway.models_keyword import attn_coll
from apps.web.utils import get_isneed_phone
from apps.common.biz_utils.utils_permission import ORDER_VERSION_DICT

from apps.subway.models import Account

from mongoengine.errors import DoesNotExist

def router(request, template = "qnyd_main.html"):
    isneed_phone = get_isneed_phone(request.user)
    version_name = None
    item_code = request.session['item_code']
    if item_code in ORDER_VERSION_DICT:
        version_name = ORDER_VERSION_DICT[item_code][1]
    else:
        # 获取版本名称时，若出现KeyError，则给基础版本
        version_name = ORDER_VERSION_DICT['ts-25811-5'][1]      
    return render_to_response(template, {'isneed_phone':isneed_phone,'version_name':version_name}, context_instance = RequestContext(request))


# def index(request, template = "qnyd_index.html"):
#     shop_id = int(request.user.shop_id)
#     attention = attn_coll.find_one({'_id':shop_id})
#     if attention:
#         return HttpResponseRedirect(reverse('qnyd_keyword_manage'))
#     else:
#         return render_to_response(template, {}, context_instance = RequestContext(request))

def qnyd_redirect(request, template = "qnyd_redirect.html"):
    return render_to_response(template, {}, context_instance = RequestContext(request))

# def home(request, template = "qnyd_base.html"):
#     return render_to_response(template, {}, context_instance = RequestContext(request))
#
# def rob_rank(request, template = "qnyd_rob_rank.html"):
#     return render_to_response(template, {}, context_instance = RequestContext(request))