# coding=UTF-8
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

import httplib
import urllib
import time
import re
import random
import mimetypes
import itertools

from apps.common.utils.utils_log import log
from apilib.error import TopError, ApiLimitError
from apilib.utils import convert_2utf8_str, convert_arg_2utf8_str

re_path_template = re.compile('{\w+}')

def bind_api(**config):
    class APIMethod(object):
        app_name = config.get('app_name', None)
        method_name = config.get('method_name', None)
        payload_type = config.get('payload_type', None)
        payload_list = config.get('payload_list', False)
        field_mapping = config.get('field_mapping', None)
        method = config.get('method', 'GET')
        require_auth = config.get('require_auth', False)
        multi_para = config.get('multi_para', None) # by:zhongjinfeng此字段是用来提交二进制数据的，比如上传图片的接口

        def __init__(self, api, args, kargs):
            # If authentication is required and no credentials are provided, throw an error.
            if self.require_auth and (not api.auth or not api.auth.session_key):
                raise TopError('Authentication required!')

            self.api = api
            self.post_data = kargs.pop('post_data', None)
            self.retry_count = kargs.pop('retry_count', api.retry_count)
            self.retry_delay = kargs.pop('retry_delay', api.retry_delay)
            self.retry_errors = kargs.pop('retry_errors', api.retry_errors)
            self.is_quick_send = kargs.pop('is_quick_send', api.is_quick_send)
            self.headers = kargs.pop('headers', {})
            self.build_parameters(args, kargs)
            # Pick correct URL root to use

            if api.secure:
                self.scheme = 'https://'
            else:
                self.scheme = 'http://'

            # Manually set Host header to fix an issue in python 2.5
            # or older where Host is set including the 443 port.
            # This causes Twitter to issue 301 redirect.
            # See Issue http://github.com/joshthecoder/tweepy/issues/#issue/12
            # 由于后面会使用到headers，因此这里并不需要，反而会造成connection与headers不一致（API流控）
            # 上面的英文说是修复Twitter的一个重定向bug，这里注释掉下面这句是可以的。
            # self.headers['Host'] = self.api.host

        def build_parameters(self, args, kargs):
            if args:
                raise TopError('argument name is necessary for API function!')
            self.parameters = {}
            for k, arg in kargs.items():
                # if arg is None: 最初代码是这样，不知道为什么，先注释掉吧
                #    continue
                if k == self.multi_para: # 如果是数据字段则不进行编码
                    self.parameters[k] = kargs[k]
                    continue

                if k in self.parameters:
                    raise TopError('Multiple values for parameter %s supplied!' % k)
                # self.parameters[k] = convert_2utf8_str(arg)
                is_str, self.parameters[k] = convert_arg_2utf8_str(arg)
                if not is_str and self.app_name: # 非字符串类型、并且是ztcjl的api
                    self.parameters[k + '__eval'] = convert_2utf8_str(1)
            if self.app_name: # added for ztcjl api_router
                self.parameters['app'] = self.app_name
            self.parameters['method'] = self.method_name

        def execute(self):
            # Build the request URL
            url = self.api.api_root
            parameters = {}
            parameters.update(self.parameters)
            if self.api.auth:
                if self.multi_para: # by:zhongjingfeng 此处如果是数据字段，则去除不参与签名
                    self.multi_para_data = parameters.pop(self.multi_para)
                self.api.auth.apply_auth(parameters = parameters)
            if len(parameters):
                if self.method == 'GET':
                    url = '%s?%s' % (url, urllib.urlencode(parameters))
                else:
                    self.headers.setdefault("User-Agent", "python")
                    if self.post_data is None:
                        self.headers.setdefault("Accept", "text/html")
                        self.headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
                        self.post_data = urllib.urlencode(parameters)

                    if self.multi_para:
                        form = MultiPartForm()
                        for key, value in parameters.items():
                            form.add_field(key, value)
                        fileitem = self.multi_para_data
                        if(fileitem and isinstance(fileitem, FileItem)):
                            form.add_file(self.multi_para, fileitem.filename, fileitem.content)
                        self.post_data = str(form)
                        self.headers["Content-Type"] = form.get_content_type()

            # Query the cache if one is available and this request uses a GET method.
            if self.api.cache and self.method == 'GET':
                cache_result = self.api.cache.get(url)
                # if cache result found and not expired, return it
                if cache_result:
                    # must restore api reference
                    if isinstance(cache_result, list):
                        for result in cache_result:
                            result._api = self.api
                    else:
                        cache_result._api = self.api
                    return cache_result

            # Continue attempting request until successful or maximum number of retries is reached.
            resp = None
            sTime = time.time()
            retries_performed = 0
#             API_LOG = Config.get_value('common.API_LOG_OUTPUT', default = 0)
            while retries_performed < self.retry_count + 1:
                # Open connection
                api_host = self.api.host
                if self.api.timeout:
                    if self.api.secure:
                        conn = httplib.HTTPSConnection(api_host, timeout = self.api.timeout)
                    else:
                        conn = httplib.HTTPConnection(api_host, timeout = self.api.timeout)
                else:
                    if self.api.secure:
                        conn = httplib.HTTPSConnection(api_host)
                    else:
                        conn = httplib.HTTPConnection(api_host)

#                 if API_LOG in [1, 3]:
#                 log.info('url=%s, headers=%s, retries_performed=%s, retry_delay=%s' % (url, self.headers, retries_performed, self.retry_delay))

                # Execute request
                try:
                    conn.request(self.method, url, headers = self.headers, body = self.post_data)
                    if self.is_quick_send:
                        return {'result': True}
                    resp = conn.getresponse()
                except Exception, e:
                    log.error('Failed to send request, host=%s, url=%s, headers=%s, retries_performed=%s, retry_delay=%s, e=%s' % (api_host, url, self.headers, retries_performed, self.retry_delay, e))
                    time.sleep(self.retry_delay)
                    retries_performed += 1
                    continue

                # Exit request loop if non-retry error code
                if self.retry_errors:
                    # if resp.status not in self.retry_errors: break
                    pass
                else:
                    if resp.status == 200:
                        break

                # Sleep before retrying request again
                time.sleep(self.retry_delay)
                retries_performed += 1

            # If an error was returned, throw an exception
            try:
                body = resp.read()
                conn.close()
            except Exception, e:
                conn.close()
                raise TopError('%s' % e)

#             if API_LOG in [2, 3]:
#             log.info('body=%s' % (body))

            self.api.last_response = resp
            if self.api.log is not None:
                post_data = ""
                requestUrl = "URL=http://" + self.api.host + url
                eTime = '%.0f' % ((time.time() - sTime) * 1000)
                if self.post_data is not None:
                    post_data = ", post=" + self.post_data[0:500]
                self.api.log.debug(requestUrl + ", time=" + str(eTime) + post_data + ", result=" + body)
            if resp.status != 200:
                error_msg = "API error response: status code=%s, len(body)=%s" % (resp.status, len(body))
                raise TopError(error_msg)

            # Parse the response payload
            try:
                result = self.api.parser.parse(self, body)
            except Exception, e:
                log.error('parse top result error, body=%s' % body)
                raise e

            # Store result into cache if one is available.
            if self.api.cache and self.method == 'GET' and result:
                self.api.cache.store(url, result)
            return result

    def _call(api, *args, **kargs):
        method = APIMethod(api, args, kargs)
        retries_performed = 0
        while 1:
            try:
                return method.execute()
            except TopError, e:
                str_error = str(e)
                if 'sub_code":"isp.' in str_error or 'msg":"Invalid signature' in str_error:
                    log.error('%s.%s => %s' % (api.auth.app_key, method.method_name, str_error))
                    time.sleep(method.retry_delay)
                    retries_performed += 1
                    if retries_performed > method.retry_count:
                        raise e
                    else:
                        continue
                elif 'sub_msg":"This ban will last for' in str_error:
                    log.error('%s.%s => %s' % (api.auth.app_key, method.method_name, str_error))
                    p = re.compile('This ban will last for (?P<x>\d*) more seconds', re.M | re.U | re.I)
                    rst_set = p.findall(str_error)
                    if rst_set and rst_set[0]:
                        wait_seconds = int(rst_set[0])
                        if wait_seconds < 3:
                            wait_seconds = random.randint(3, 7)
                        elif wait_seconds > 500: # 报流量用完的错误，调tapi的地方不捕获
                            raise ApiLimitError(api.auth.app_key, method.method_name, wait_seconds)
                        time.sleep(wait_seconds)
                        retries_performed += 1
                        if retries_performed > method.retry_count:
                            raise e
                        else:
                            continue
                elif '{"code":15' in str_error and '.lua:' in str_error: # 下载报表数据时出现的错误，重试多次一般会成功
                    time.sleep(method.retry_delay)
                    retries_performed += 1
                    if retries_performed > method.retry_count:
                        raise e
                    else:
                        continue
                elif str_error == '': # 下载报表时，出现的淘宝返回为空的异常，重试可能成功
                    time.sleep(method.retry_delay)
                    retries_performed += 1
                    if retries_performed > method.retry_count:
                        raise e
                    else:
                        continue
                elif 'service not available' in str(e): # 暂不特殊处理，淘宝会返回这种问题，可能是全网受影响。
                    raise e
                else:
                    raise e

    _call.APIMethod = APIMethod
    return _call

def mixStr(pstr):
    if(isinstance(pstr, str)):
        return pstr
    elif(isinstance(pstr, unicode)):
        return pstr.encode('utf-8')
    else:
        return str(pstr)

class FileItem(object):
    def __init__(self, filename = None, content = None):
        self.filename = filename
        self.content = content

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = "PYTHON_SDK_BOUNDARY"
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, str(value)))
        return

    def add_file(self, fieldname, filename, content, mimetype = None):
        """Add a file to be uploaded."""
        body = content
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((mixStr(fieldname), mixStr(filename), mixStr(mimetype), mixStr(body)))
        return

    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              'Content-Type: text/plain; charset=UTF-8',
              '',
              value,
            ]
            for name, value in self.form_fields
            )

        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              'Content-Transfer-Encoding: binary',
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)