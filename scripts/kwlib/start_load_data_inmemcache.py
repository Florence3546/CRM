# coding=UTF-8
import init_environ
from apilib import *
from apps.common.utils.utils_log import log

# function：将数据库当中的有流量的关键词导入到memcached中，以类目id为key
# usage：python.exe start_kwlib_claw_task.py

log.info("start find keyword from kwlib_wordcat where keyword  c_pv $gt 1 and the cat count $gt 100000 ")
kwlib_maintain_api().start_load_data_inmemcache()
log.info("The large cat count word has set in default memcache ")

