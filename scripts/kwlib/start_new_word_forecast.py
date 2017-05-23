# coding=UTF-8
import init_environ
from apilib import *
from apps.common.utils.utils_log import log


# function：从数据库中取出每天入库的关键词，并对这些关键词进行类目预测
# usage：python.exe start_new_word_forecast.py

log.info("start find the new words in kwlib_keywordinfo and forcast these words into kwlib_wordcat ")
kwlib_maintain_api().start_new_word_forecast()
log.info("all word has get related word by every word ")
