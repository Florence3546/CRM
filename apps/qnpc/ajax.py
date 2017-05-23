# coding=UTF-8
from dajax.core import Dajax

from apps.common.utils.utils_log import log
from apps.qnyd.biz import set_attention_kw

def route_dajax(request):
    '''dajax路由函数'''
    auto_hide = int(request.POST.get('auto_hide', 1))
    dajax = Dajax()
    if auto_hide:
        dajax.script("PT.hide_loading();")
    function_name = request.POST.get('function')
    if function_name and globals().get(function_name, ''):
        dajax = globals()[function_name](request = request, dajax = dajax)
    else:
        dajax = log.exception("route_dajax: function_name Does not exist")
    return dajax

def auto_set_attention_kw(request, dajax):
    '''一键设置关键词'''
    shop_id = int(request.user.shop_id)
    set_attention_kw(shop_id = shop_id)
    dajax.script('PT.Attention.confirm_download_rpt();')
    return dajax
