#!/uer/bin/env python
# -*- coding:utf-8 -*-
#===========================================================================
# 功能：获取服务后台的评价，然后同步用户好评有礼的积分
# by:钟进峰
import init_environ
from apps.web.models import pa_coll
from apps.web.point import PointManager
from apilib import get_tapi
from apilib.tapi import *
import datetime, time

def get_appraise_by_date(date):
    """获取当天所有评价"""
    PAGE_SIZE = 100
    page = 1
    tapi = get_tapi(shop_id = 63518068)

    appraisal_list = []

    for i in range(10):
        result = tapi.fuwu_sale_scores_get(current_page = page, PAGE_SIZE = 100, date = date)
        if not result:
            break
        appraisal_dict = result.to_dict()
        temp = appraisal_dict['score_result']['score_result']
        if temp:
            appraisal_list.extend(temp)
        if len(temp) < PAGE_SIZE:
            break

        print 'Pause three seconds to continue...'
        time.sleep(3)

    return appraisal_list


def update_appraise_record(vaild_list):
    """跟新有用的记录"""
    for v in vaild_list:
        pa_coll.update({'_id':v['_id']}, {'$set':{'is_freeze':0, 'gmt_create':v['gmt_create']}})
        PointManager.refresh_points_4nick(v['nick'])

def main():
    from apps.common.utils.utils_datetime import get_start_datetime
    """获取用户点击好评有礼的记录并对比更新"""
    appraise_record = pa_coll.find({'type':'appraise', 'is_freeze':1, 'create_time':{'$gte':get_start_datetime()}})

    if appraise_record.count():
        vaild_list = []
        server_appraise_list = get_appraise_by_date(date = datetime.date.today())

        if server_appraise_list:
            for a in appraise_record:
                for s in server_appraise_list:
                    avg_score = s.get('avg_score', 0)
                    user_nick = s.get('user_nick', '')
                    print "%s:%s" % (user_nick, avg_score)

                    if user_nick == a['nick'] and int(float(avg_score)) == 5:
                        a['gmt_create'] = s.get('gmt_create', datetime.datetime.now())
                        vaild_list.append(a)

            if vaild_list:
                update_appraise_record(vaild_list)
        else:
            print '没有用户评价软件，%s' % (datetime.datetime.today())

    else:
        print '没有用户点击好评有礼，%s' % (datetime.datetime.today())

if __name__ == "__main__":
    main()
