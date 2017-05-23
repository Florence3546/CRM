# coding=UTF-8
import init_environ
from apilib import *
from apps.common.utils.utils_log import log


# function：从数据库中取出关键词，针对这些关键词做类目预测，数据保存到wordcat表当中
# usage：python.exe start_new_word_forecast.py

log.info("start find the  words in kwlib_keywordinfo and forecast these words into kwlib_wordcat ")
kwlib_maintain_api().start_get_word_forecast()
log.info("all word has get forecast and save in kwlib_wordcat  by every word ")
