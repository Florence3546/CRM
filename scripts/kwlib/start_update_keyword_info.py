# coding=UTF-8
import init_environ
from apilib import *
from apps.common.utils.utils_log import log

# function：启动获取每个关键词的全网点击数据，获取全网pv,click...
# usage：python.exe start_update_keyword_info.py

log.info("start update keywordinfo , get g_pv ,g_click ... from taobao save in database ")
kwlib_maintain_api().start_update_keyword()
log.info("finish update keywordinfo from taobao")
