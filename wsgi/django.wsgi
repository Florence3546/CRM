import os, sys
from os.path import dirname

PROJECT_ROOT = dirname(dirname(__file__))
sys.path.append(PROJECT_ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
