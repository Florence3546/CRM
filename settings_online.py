# coding=UTF-8
'''
注意：该文件仅用于线上正式版的通用配置，本地DEBUG不加载这些配置；
如果是本地DEBUG调试，请仍然在settings_local文件中配置这些属性。
配置内容：
1、MySQL数据库配置
2、Memcached缓存集群配置
3、Worker集群配置
'''

import pymongo
from mongoengine import register_connection

connect_web = {'alias':'default', 'db':'jl_ztcjl', 'host':['10.27.228.73', ], 'port':30001, 'username':'PS_ztcjlAdmin', 'password':'PS_managerZtcjl', 'max_pool_size':50}
connect_kwlib = {'alias':'kwlib-db', 'db':'kwlib', 'host':['10.27.228.73', ], 'port':30001, 'username':'PS_kwlibAdmin', 'password':'PS_managerKwlib', 'max_pool_size':50}
connect_keyword = {'alias':'keyword-db', 'db':'jl_keyword', 'host':['10.27.228.73', ], 'port':30001, 'username':'PS_keywordAdmin', 'password':'PS_managerKeyword', 'max_pool_size':50}
connect_crm = {'alias':'crm-db', 'db':'crm', 'host':['10.27.228.73', ], 'port':30001, 'username':'PS_crmAdmin', 'password':'PS_managerCrm', 'max_pool_size':50}
connect_mnt = {'alias':'mnt-db', 'db':'mnt', 'host':['10.27.228.73', ], 'port':30001, 'username':'PS_mntAdmin', 'password':'PS_managerMnt', 'max_pool_size':50}
def connect_database(connect_dict):
    for i in range(len(connect_dict['host'])):
        try:
            conn = pymongo.Connection(connect_dict['host'][i] + ':' + str(connect_dict['port']))
            register_connection(connect_dict['alias'], connect_dict['db'], host = connect_dict['host'][i], port = connect_dict['port'] , username = connect_dict['username'], password = connect_dict['password'], max_pool_size = connect_dict['max_pool_size'])
            conn.disconnect()
            break
        except:
            continue
connect_database(connect_web)
connect_database(connect_kwlib)
connect_database(connect_keyword)
connect_database(connect_crm)
connect_database(connect_mnt)


# MySQL数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ztcjl4',
        'USER': 'root',
        'PASSWORD': 'zxcvbnhy6',
        'HOST': '10.116.209.97',
        'PORT': '3306',
    },
}

APP_CONFIG = {
    'web':['localhost', '80', 'web'],
    'kwlib':['10.153.193.159', '30010', 'kwlib'],
}

# Memcached缓存集群配置
CACHES = {
    'default': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION': '53c4159907f111e4.m.jst.cnhzalicm10pub001.ocs.aliyuncs.com:11211',
        'TIMEOUT': 24 * 30 * 60 * 60,
        'OPTIONS': {
            'username': '53c4159907f111e4',
            'password': 'ghtu58OCS02'
        }
    },
    'web': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION': '53c4159907f111e4.m.jst.cnhzalicm10pub001.ocs.aliyuncs.com:11211',
        'TIMEOUT':60 * 60,
        'OPTIONS': {
            'username': '53c4159907f111e4',
            'password': 'ghtu58OCS02'
        }
    },
    'crm': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION': '120ac858f1f611e3.m.jst.cnhzalicm10pub001.ocs.aliyuncs.com:11211',
        'TIMEOUT': 8 * 60 * 60,
        'OPTIONS': {
            'username': '120ac858f1f611e3',
            'password': 'ghtu58OCS01'
        }
    },
    'download': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION': '120ac858f1f611e3.m.jst.cnhzalicm10pub001.ocs.aliyuncs.com:11211',
        'TIMEOUT': 8 * 60 * 60,
        'OPTIONS': {
            'username': '120ac858f1f611e3',
            'password': 'ghtu58OCS01'
        }
    },
    'g_data': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION': '120ac858f1f611e3.m.jst.cnhzalicm10pub001.ocs.aliyuncs.com:11211',
        'TIMEOUT': 24 * 60 * 60,
        'OPTIONS': {
            'username': '120ac858f1f611e3',
            'password': 'ghtu58OCS01'
        }
    },
    'kwlib': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION': 'c3e161b8912d4344.m.jst.cnhzalicm10pub001.ocs.aliyuncs.com:11211',
        'TIMEOUT': 24 * 60 * 60 * 30,
        'OPTIONS': {
            'username': 'c3e161b8912d4344',
            'password': 'ghtu58OCS05'
        }
    },
    'worker': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION': '531aba745dd045e3.m.jst.cnhzalicm10pub001.ocs.aliyuncs.com:11211',
        'TIMEOUT': 80,
        'OPTIONS': {
            'username': '531aba745dd045e3',
            'password': 'ghtu58OCS06'
        }
    },
}


# REDIS 配置文件

REDIS_CONF = {
                 'gdata':{'host':'10.153.198.20', 'port':6379, 'db':0, 'password':'PS_redis_access'}, # 存放有流量的关键词及关键词全网数据'红色连衣裙':'{pv:1,click:1,cmpt:1....}'
                 'gkeyword':{'host':'10.153.198.20', 'port':6379, 'db':1, 'password':'PS_redis_access'}, # 存放有流量的关键词的关键词 g_data_keyword_list_0....n  g_data_keyword_list_manager
                 'hkeyword':{'host':'10.153.198.20', 'port':6379, 'db':2, 'password':'PS_redis_access'}, # 存放所有关键词的hash以及其属性   '连衣裙红色':{'kw':'红色连衣裙','upt_tm':'2015-1-1',cat_list:'16,1601'}
                 'keyword':{'host':'10.153.198.20', 'port':6379, 'db':3, 'password':'PS_redis_access'}, # 存放所有的关键词 keyword_list_0...n  keyword_list_manager
                 'nkeyword':{'host':'10.153.198.20', 'port':6379, 'db':4, 'password':'PS_redis_access'}, # 存放所有的新加入的关键词 new_keyword_list_0...n new_keyword_list_manager
                 'wcdata':{'host':'10.153.198.20', 'port':6379, 'db':5, 'password':'PS_redis_access'}, # 存放有流量的类目关键词的数据 '16:红色连衣裙':'{pv:1,click:1cmpt:1....}'
                 'wcdkeyword':{'host':'10.153.198.20', 'port':6379, 'db':6, 'password':'PS_redis_access'}, # 存放有流量的类目关键词16_keyword_list_0...n 16_keyword_list_manager
                 'wckeyword':{'host':'10.153.198.20', 'port':6379, 'db':7, 'password':'PS_redis_access'}, # 存放类目下所有的关键词16_all_keyword_list_0...n 16_all_keyword_list_manager
                 'subkeyword':{'host':'10.153.198.20', 'port':6379, 'db':8, 'password':'PS_redis_access'}, # 存放关键词的细分数据，hash key :'连衣裙':{1:'',2:'',4:'',5:''}
                 }

REDIS_WORKER_QUEUE = {'host': '10.132.164.95', 'port': 6379, 'db': 0, 'password': 'PS_redis_access'} # 用于选词任务的worker队列
REDIS_RANK_CHANNEL = {'host':'10.132.164.95', 'port':6379, 'db': 1, 'password':'PS_redis_access'}

# celery 配置文件
CELERY = {
          'BROKER_URL': 'redis://:PS_redis_access@10.153.198.20/10',
          'CELERY_RESULT_BACKEND': 'redis://:PS_redis_access@10.153.198.20/11',
          'CELERY_TRANSPORT':'redis',
          'CELERY_TASK_SERIALIZER': 'json',
          'CELERY_RESULT_SERIALIZER':'json',
          'CELERY_ACCEPT_CONTENT': ['json'],
          'CELERY_TIMEZONE': 'Europe/Oslo',
          'CELERY_ENABLE_UTC': True
}
