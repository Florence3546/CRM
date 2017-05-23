# coding=UTF-8
from apps.common.biz_utils.utils_permission import test_permission, check_perms
from permission_config import VIEW_PERMS_CONFIG, CRM_PERMS_CONFIG, AJAX_PERMS_CONFIG
# from apps.common.utils.utils_log import log


class SecurityMiddleware(object):

    """此处作为request的拦截器，做普遍性的登录校验和基本权限验证"""
    def process_request(self, request):
        # if not request.user.is_authenticated():
        #     log.info('SecurityMiddleware.process_request user: %s@%s:%s' % (request.session.get('psuser_name', 'Unknown'), request.META['REMOTE_ADDR'], request.path))

        # 根据请求类型，校验功能权限
        if request.is_ajax():
            try:
                path_list = request.META['HTTP_REFERER'].replace('http://', '').split('/')

                if 'crm' in path_list:
                    return None

                ajax_func = request.POST.get('function')

                perms_tuple = AJAX_PERMS_CONFIG.get(ajax_func, ('undefined', '', 0, ()))
                if (perms_tuple[0] != 'undefined' and perms_tuple[2]):
                    if perms_tuple[0] and not test_permission(perms_tuple[0], request.user):
                        if 'qnpc' in path_list: # TODO 2015.11.3 临时处理，千牛改版时再重新设计该模块
                            from dajax.core import Dajax
                            dajax = Dajax()
                            dajax.script("PT.confirm('您当前的版本需要升级后才能使用该功能，要升级吗？', function(){window.open('https://fuwu.taobao.com/ser/detail.html?spm=a1z13.1113643.51940006.43.RmTuNs&service_code=FW_GOODS-1921400&tracelog=category&scm=1215.1.1.51940006', '_blank');},[],this,null,[],this, ['升级'])")
                            return dajax
                        result = perms_tuple[1](request = request, perms_code = perms_tuple[0])
                        return result
                    else:
                        for i in perms_tuple[3]:
                            if i == 'href':
                                ajax_func = path_list[2] + '_' + ajax_func
                                continue
                            ajax_func = ajax_func + '_' + request.POST.get(i, '')

                if 'behavior_only' in ajax_func:
                    return perms_tuple[1]()
            except Exception:
                return None
            # TODO: wangqi 2013-12-29 ajax暂时不处理
            # ajax 请求权限验证
            # ajax_func = request.POST.get('function')暂时写死，全部以基础权限统一处理
#             try:
#                 ajax_path = request.path[1:-1].split('/')[-1]
#             except Exception:
#                 ajax_path = ''
#             perms_config = AJAX_PERMS_CONFIG.get(ajax_path, None)
#             if perms_config and not  test_permission(perms_config[0], request.user):
#                 return perms_config[1](request = request, perms_code = perms_config[0])
        else:
            # from 请求权限验证
            try:
                path_list = request.path[1:].split('/')
            except Exception:
                return None
            if path_list[0] in ['web', 'mnt']:
                perms_tuple = VIEW_PERMS_CONFIG.get(path_list[1], ('', '', 0))
                if perms_tuple[0] and not test_permission(perms_tuple[0], request.user):
                    return perms_tuple[1](request = request, perms_code = perms_tuple[0])
            elif path_list[0] == 'kwlib': # 建议将这几个功能也迁移到CRM中去
                from apps.common.utils.utils_render import render_to_limited
                if not request.user.is_superuser:
                    return render_to_limited(request, '亲，您没有权限使用该功能！')
            elif path_list[0] in ['crm', 'ncrm']:
                perms_tuple = CRM_PERMS_CONFIG.get(path_list[1], ('', ''))
                if perms_tuple[0] and not check_perms(perms_tuple[0], request):
                    return perms_tuple[1](request = request)

        return None

#             for path_part in path_list:
#                 if path_part and path_part in VIEW_PERMS_CONFIG:
#                     perms_config = VIEW_PERMS_CONFIG.get(path_part, None)
#                     if perms_config and not test_permission(perms_config[0], request.user):
#                         return perms_config[1](request = request, perms_code = perms_config[0])
#                     break
#                 elif path_part and path_part in KWLIB_URL_FILTER :
#                     kw_perms_config = KWLIB_URL_FILTER.get(path_part, None)
#                     if kw_perms_config and not request.user.is_staff :
#                         return kw_perms_config[1](request = request, perms_code = kw_perms_config[0])
#                     elif kw_perms_config and  not  request.user.is_superuser and KWLIB_URL_FILTER[path_part][0] != "is_staff" :
#                         return kw_perms_config[1](request = request, perms_code = kw_perms_config[0])
#         return None

class NextUrlMiddleware(object):
    """此类用于支持模拟跳转功能"""
    def process_response(self, request, response):
        """修改web session"""
        if request.REQUEST.get('next_url', ''):
            request.session['next_url'] = request.REQUEST['next_url']
            request.session.save()
        return response


