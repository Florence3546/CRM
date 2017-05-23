# coding=UTF-8

from functools import wraps
import time

from apps.common.utils.utils_log import log


def record_time(fn):
    """打印方法执行时间的装饰器"""
    @wraps(fn)
    def _record(*args, **kwargs):
        start_time = time.time()
        result = fn(*args, **kwargs)
        log.info('fn %s cost %s' % (fn.func_name, time.time() - start_time))
        return result
    return _record
