# coding=UTF-8
import init_environ
import pymongo
from apps.common.utils.utils_log import log
from japi import JAPI
from apps.common.utils.utils_collection import genr_sublist


conn = pymongo.Connection("10.241.51.158:30001")
conn.admin.authenticate('PS_superAdmin', 'PS_managerAdmin')
shard_conn_ip = {
          'shard1':"10.241.51.158:30001",
          'shard2':"10.241.51.159:30001",
          'shard3':"10.241.51.160:30001",
          'shard4':"10.241.48.169:30001",
          }
worker_ip = {
           'shard1':"10.241.51.161:81",
           'shard2':"10.241.51.161:82",
           'shard3':"10.241.51.161:83",
           'shard4':"10.241.54.105:81",
           }
config = conn.config
chunk_coll = config.chunks
shard_dict = {'shard':[]}
for chk in chunk_coll.find({'ns':'kwlib.kwlib_wordcat'}):
    if not isinstance(chk['min']['cat_id'], int):
        continue
    if not isinstance(chk['max']['cat_id'], int):
        chk['max']['cat_id'] = 100000000
    if chk['min']['cat_id'] == chk['max']['cat_id']:
        if chk['min']['cat_id'] in shard_dict['shard']:
            continue
        shard_dict['shard'].append(chk['min']['cat_id'])
        continue
    min_max_list = [chk['min']['cat_id'], chk['max']['cat_id']]
    key = chk['shard']
    if shard_dict.has_key(key):
        shard_dict[key].append(min_max_list)
    else:
        shard_dict[key] = [min_max_list]
conn.disconnect()
shard_list = genr_sublist(shard_dict['shard'], 4)
del shard_dict['shard']
count = 0
index = 0
for key in shard_dict:
    conn = pymongo.Connection(shard_conn_ip[key])
    kwlib = conn.kwlib
    kwlib.authenticate('PS_kwlibAdmin', 'PS_managerKwlib')
    cat_coll = kwlib.kwlib_catinfo
    cat_list = []
    for max_min_list in  shard_dict[key]:
        for cat in cat_coll.find({'cat_id':{'$gte':max_min_list[0], '$lte':max_min_list[1]}}):
            if cat['cat_id'] in shard_dict['shard']:
                continue
            cat_list.append(cat['cat_id'])
    cat_list.extend(shard_list[index])
    index += 1
    count += len(cat_list)
    log.info('The cat_id length of %s  is %s' % (key, len(cat_list)))
    JAPI(host = worker_ip[key]).start_load_data_inmemcache(cat_list = cat_list, ip = shard_conn_ip[key], is_sync = False)
log.info('all cat count is %s' % count)
