# coding=UTF-8
import sys
import os

import django

reload(sys)
sys.setdefaultencoding('utf8')
from os.path import abspath, dirname, join
PROJECT_ROOT = abspath(dirname(dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, join(PROJECT_ROOT, "thirdapps"))
sys.path.insert(0, join(PROJECT_ROOT, "apps"))

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

os.environ.update({"DJANGO_SETTINGS_MODULE": "settings"})
django.setup()
