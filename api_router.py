# coding=UTF-8
'''
所有 app中的api都是通过api_router.dispatch转发调用的。
app api 编写流程：
1.在app的api.py 中实现 def xxx(request): 函数。
2.在apilib的japi.py文件中添加    xxx = bind_api(app_name='app',method_name='xxx') 代码。
app api 编写完成后的调用方式，请参考：
import init_environ
from apilib import *

api = JAPI(host = '127.0.0.1:8000', retry_count = 3, retry_delay = 3)
jobj = api.get_download_services()
print vars(jobj)
sys.exit()
'''
import inspect

from django.utils.importlib import import_module
from django.http import HttpResponse

from apps.common.utils.utils_json import json
from apps.common.utils.utils_log import log
from apps.common.utils.utils_thread import NewThread
from apps.common.biz_utils.utils_misc import jl_check_sign_with_secret


api_function_dict = {}
def get_api_function_info(app, method):
    global api_function_dict
    func_name = app + method
    if not api_function_dict.has_key(func_name):
        api_function = getattr(import_module('%s.api' % (app)), method)
        arguments_info_tuple = inspect.getargspec(api_function)
        api_function_dict[func_name] = [api_function] + list(arguments_info_tuple)

    return api_function_dict[func_name]


def dispatch(request):
    if request.method == 'GET':
        req_data = request.GET
    else:
        req_data = request.POST

    param_dict = {}
    param_dict.update(request.REQUEST)
    check_result = jl_check_sign_with_secret(param_dict, timeout = 60 * 10)
    if check_result == 'no_permission':
        rst = {"error_response":{"code":25, "msg":"Invalid Signature", "sub_code":"isv.invalid-permission", "sub_msg":"have no permission"}}
        json_data = json.dumps(rst)
        return HttpResponse(json_data)
    elif check_result == 'timeout':
        rst = {"error_response":{"code":43, "msg":"Invalid Timestamp", "sub_code":"isv.invalid-parameter", "sub_msg":"timeout"}}
        json_data = json.dumps(rst)
        return HttpResponse(json_data)
    else:
        pass

    if req_data.has_key('method') and req_data.has_key('app'):
        app = req_data['app']
        method = req_data['method']
        if req_data.has_key('is_sync') and req_data['is_sync'] == 'False':
            is_sync = False
        else:
            is_sync = True
    else:
        json_data = json.dumps({"error_response":{"code":40, "msg":"Missing Required Arguments", "sub_code":"isv.missing-parameter", "sub_msg":"wrong request APP.METHOD(GET or POST)"}})
        return HttpResponse(json_data)

    try:
        api_function, args, varargs, varkw, defaults = get_api_function_info(app, method)
        kwargs = {}
        # 根据函数定义的默认参数和request中的数据 组装**kwargs
        if defaults: # 先填充默认参数
            for i in range(len(defaults)):
                kwargs[args[-1 - i]] = defaults[-1 - i]
        for arg in args: # 再填充request数据中有的参数
            if req_data.has_key(arg):
                if req_data.has_key(arg + '__eval'):
                    kwargs[arg] = eval(req_data[arg])
                else:
                    kwargs[arg] = req_data[arg]
        kwargs['request'] = request # api函数，必须包含了request参数
        # 检查是否有未赋值的参数：
        missing_args = [arg for arg in args if arg not in kwargs.keys()]
        if missing_args:
            json_data = json.dumps({"error_response":{"code":40, "msg":"Missing Required Arguments", "sub_code":"isv.missing-parameter", "sub_msg":"missing parameters (%s)" % (','.join(missing_args))}})
            return HttpResponse(json_data)
        if not is_sync:
            nt = NewThread(api_function, **kwargs)
            nt.start()
            rst = {'%s_response' % (method):{'result':True}}
            json_data = json.dumps(rst)
        else:
            rst = {'%s_response' % (method):api_function(**kwargs)}
            json_data = json.dumps(rst)
    except Exception, e:
        rst = {"error_response":{"code":15, "msg":"Remote service error", "sub_code":"isp.unknown-error", "sub_msg":"call %s.api.%s raise e=%s" % (app, method, e)}}
        log.error('api req_data=%s, rst=%s' % (req_data, rst))
        json_data = json.dumps(rst)

    return HttpResponse(json_data)
