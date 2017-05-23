# coding=UTF-8
import init_environ
from apilib import kwlib_maintain_api
from apps.common.utils.utils_log import log

# function：从纯词表当中取关键词获取相关词，然后存入到纯词表当中
# usage：python.exe start_kwlib_claw_task.py

log.info("start find keyword from kwlib_keywordinfo and get related words")
kwlib_maintain_api().start_get_reteled_word()
log.info("All words has get related words in kwlib_keywordinfo ")
