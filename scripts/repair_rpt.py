# coding=UTF-8

import init_environ

from apps.engine.models import shopmng_task_coll
from apps.subway.download import dler_coll

print 'start'

status = '2015-03-13-00-00_OK'
dler_coll.update({'acctrpt_status': {'$gt': status}},
                 {'$set': {'acctrpt_status': status,
                           'camprpt_status': status,
                           'adgrpt_status': status
                           }
                  },
                 multi = True)

print 'update downloader finished'


shopmng_task_coll.update({}, {'$set': {'status': 1}}, multi = True)

print 'update shopmng task finished'

print 'ok'
