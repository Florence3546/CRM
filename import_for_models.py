# coding=UTF-8
#!/usr/bin/env python

# for models.py
from django.db import models
from django.db.models import F, Q, Sum, Avg
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site
# from apps.router.models import User
# from django.contrib.auth.models import Message
# from django.contrib import messages TODO: wangqi 20150521 Message�ƺ�û�õ��ˣ����Ҫ�������������滻
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from datetime import datetime, timedelta, date

# from apps.common.utils.utils_collection import *
# from apps.common.utils.utils_datetime import *
# from apps.common.utils.utils_mysql import *
# from apps.common.utils.utils_number import *
# from apps.common.utils.utils_render import *
# from apps.common.biz_utils.utils_sorter import *
# from apps.common.utils.utils_string import *
# from apps.common.biz_utils.utils_misc import *
# from apilib import *
# from apilib import tsapi
