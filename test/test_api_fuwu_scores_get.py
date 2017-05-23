# coding=UTF-8

import init_environ

from apilib import get_tapi
from apilib.tapi import *
import datetime

tapi = get_tapi(shop_id = 63518068)
    
result=tapi.fuwu_sale_scores_get(current_page=1,page_size=100,date=datetime.date.today())

print result
