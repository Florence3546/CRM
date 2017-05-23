# coding=UTF-8
import init_environ
from apps.subway.models_account import account_coll

account_coll.update({}, {'$set':{'custom_hide_column':[]}}, multi = True)