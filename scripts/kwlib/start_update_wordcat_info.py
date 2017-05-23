# coding=UTF-8
import init_environ
from apilib import *
from apps.common.utils.utils_log import log

# function：获取关键词的类目数据，获取该关键词在该类目下的c_pv,c_click....
# usage：python.exe start_update_wordcat_info.py

log.info("start update wordcat data from taobao save in database ")
kwlib_maintain_api().start_update_wordcat()
log.info("finish update wordcat from taobao ")
