# coding=UTF-8

import init_environ

from apps.mnt.models_mnt import mnt_camp_coll
from apps.engine.models import shopmng_task_coll

shop_dict = {}
mnt_cursor = mnt_camp_coll.find({'mnt_type':2}, {'shop_id':1})

for mnt_camp in mnt_cursor:
    count = shop_dict.setdefault(mnt_camp['shop_id'], 0)
    count += 1
    shop_dict.update({mnt_camp['shop_id']:count})

shopmng_task_coll.update({}, {'$set':{'priority':0}}, multi = True)
for shop_id, priority in shop_dict.items():
    shopmng_task_coll.update({'_id':shop_id}, {'$set':{'priority':priority}})
