# coding=UTF-8
from __future__ import absolute_import # 防止celery Lib库和本地celery.py冲突
import os
from celery import Celery
import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings') # 加载settings文件

app = Celery('apps.kwlib') # 初始化apps.kwlib

app.config_from_object(settings.CELERY) # 加载配置文件

app.autodiscover_tasks(lambda : settings.INSTALLED_APPS) # 自动发现app下的任务



@app.task(bind = True)
def debug_task(self): # 测试
    print('Request: {0!r}'.format(self.request))