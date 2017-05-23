# coding=UTF-8
import sys
import os
reload(sys)
sys.setdefaultencoding('utf8')
from os.path import abspath, dirname, join
PROJECT_ROOT = abspath(dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, join(PROJECT_ROOT, "thirdapps"))
sys.path.insert(0, join(PROJECT_ROOT, "apps"))
sys.path.insert(0, join(PROJECT_ROOT, "scripts"))


TIME_ZONE = 'Asia/Shanghai'

DEBUG = False
TEMPLATE_DEBUG = True

ADMINS = (('zhongchao', 'zhongchao@paithink.com'),)
MANAGERS = ADMINS
ADMIN_URL = 'PS908'

DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s'
USE_I18N = False # 纯中文，不i18n
DEFAULT_CHARSET = "UTF-8"

# Absolute path to the directory that holds media. Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), "site_media")
# URL that handles the media served from MEDIA_ROOT. Example: "http://media.lawrence.com"
MEDIA_URL = '/site_media/'
# STATIC_URL = '/site_media/'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")

STATICFILES_DIRS = (os.path.join(PROJECT_ROOT, "site_media"),)
# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a trailing slash. Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = '/site_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'bk-e2zv3humar79nm=j*bwc=-ymeit132481113goq4dh71t%s'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    # 'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'crashlog.CrashLogMiddleware',
    'apps.web.middleware.SecurityMiddleware',
    'apps.web.middleware.NextUrlMiddleware',
)

ROOT_URLCONF = 'urls'
ALLOWED_HOSTS = ['*']

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
    # 'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    'django.contrib.messages.context_processors.messages',
    "apps.web.context_processors.file_version",
    "apps.web.context_processors.page_mark",
    "apps.web.context_processors.web_menu",
    'apps.web.context_processors.rjjh_worktime',
    'apps.web.context_processors.settings_arg'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'dajax',
    # 'crashlog',
    'apps.common',
    'apps.engine',
    'apps.mnt',
    'apps.kwlib',
    'apps.kwslt',
    'apps.crm',
    'apps.ncrm',
    'apps.router',
    'apps.web',
    'apps.subway',
    'apps.toolkit',
    'apps.qnyd',
    'apps.qnpc',
    'apps.alg',
)

AUTH_USER_MODEL = 'router.User'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "templates/jl6"),
    os.path.join(PROJECT_ROOT, "templates/select_ord"),
    os.path.join(PROJECT_ROOT, "templates/ncrm"),
    os.path.join(PROJECT_ROOT, "templates/ncrm/func_templates"),
    os.path.join(PROJECT_ROOT, "templates/crm"),
    os.path.join(PROJECT_ROOT, "templates/qnpc6"),
    os.path.join(PROJECT_ROOT, "templates/qnyd6"),
    os.path.join(PROJECT_ROOT, "site_media"),
)

# DISABLE_QUERYSET_CACHE = False 没用
HOME_DATA_CACHE = False

# registration setting
SESSION_EXPIRE_AT_BROWSER_CLOSE = True # TODO 在firefox中无效，request.session.set_expiry(0)对firefox也无效

LOGGING_OUTPUT_ENABLED = True
LOGGING_SHOW_METRICS = False
LOGGING_LOG_SQL = False

# Cache configuration here, now moved in settings_local.py

# if Django is running behind a proxy, we need to do things like use HTTP_X_FORWARDED_FOR instead of REMOTE_ADDR. This setting is used to inform apps of this fact
BEHIND_PROXY = True # TODO TO CONFIRM!

SITE_ID = 1
SITE_NAME = "开车精灵"
CONTACT_EMAIL = "zhongchao@paithink.com"
AUTO_TASK_EMAIL = "wuhuaqiao@paithink.com"

SERVER_EMAIL = "pskj@paithink.com"
EMAIL_PORT = "25"
EMAIL_HOST = "smtp.exmail.qq.com"
EMAIL_HOST_USER = "pskj@paithink.com"
EMAIL_HOST_PASSWORD = "ps123456"
DEFAULT_FROM_EMAIL = '''%s<%s>''' % ('派生科技', EMAIL_HOST_USER)
EMAIL_USE_TLS = None

SMS_USERID = 'speedhe'
SMS_PASSWORD = 'paithink0228'
SMS_BOSS_PHONE = 18571532288
SMSABLE = True

TAPI_RETRY_COUNT = 3
TAPI_RETRY_DELAY = 3
JAPI_RETRY_COUNT = 3
JAPI_RETRY_DELAY = 3

ACTIVITY_TYPE = 8 # 活动编号
ACCT_RPT_DAYS = 90 # 账户报表天数保留90天
RESERVED_RPT_DAYS = 35 # 报表保留天数

APP_KEY = '12612063'
APP_ARTICLE_CODE = 'ts-25811'
APP_SECRET = '401fe6f3ca9d095eceafe52639750f00'

MAIN_PORT_WEB = "http://www.ztcjl.com/main_port_web/"
MAIN_PORT_QNPC = "http://www.ztcjl.com/main_port_qnpc/"
MAIN_PORT_QNYD = "http://www.ztcjl.com/main_port_qnyd/"
JAPI_SECRET = "585bedd4e3d4a3cfa185f710914ad96c"
WEB_AUTH_URL = 'http://container.open.taobao.com/container?appkey=%s&encode=utf-8' % APP_KEY
LOGIN_URL = MAIN_PORT_WEB



# 加载Dajax配置
try:
    from settings_dajax import *
except ImportError:
    pass

# 加载个性化配置：用于配置正式服务器、本地调试时各不相同的配置，该文件不能上传到代码库，且必须写在加载settings_online之前
try:
    from settings_local import *
except ImportError:
    pass

# 加载线上正式版的配置，DEBUG环境下不加载该文件(DEBUG仍配置在settings_local.py中)，因此必须写在文件末尾
try:
    if not DEBUG:
        from settings_online import *
except ImportError:
    pass
