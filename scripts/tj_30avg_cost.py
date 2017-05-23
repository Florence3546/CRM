#!/uer/bin/env python
# -*- coding:utf-8 -*-
#===========================================================================
#功能：统计指定店铺等级的30天消耗
#用法：更改第33行的信用list
#by:钟进峰
#===========================================================================
# [
#      [0, 500, 0]
#    , [501, 1000, 0]
#    , [1001, 2000, 0]
#    , [2001, 5000, 0]
#    , [5001, 10000, 0]
#    , [10001, 20000, 0]
#    , [20001, 50000, 0]
#    , [50001, 100000, 0]
#    , [100001, 200000, 0]
#    , [200001, 500000, 0]
#    , [500001, 1000000, 0]
#    , [1000001, 2000000, 0]
#    , [2000001, 5000000, 0]
#    , [5000001, 10000000, 0]
#    , [10000001, 10000000000000, 0]
#]

import MySQLdb, sys, datetime
import pymongo
reload(sys)
sys.setdefaultencoding('gb2312')


#credit_list = [0, 500] #参照注释中的信誉等级

credit_list = [
      [0, 500, 0]
    , [501, 1000, 0]
    , [1001, 2000, 0]
    , [2001, 5000, 0]
    , [5001, 10000, 0]
    , [10001, 20000, 0]
    , [20001, 50000, 0]
    , [50001, 100000, 0]
    , [100001, 200000, 0]
    , [200001, 500000, 0]
    , [500001, 1000000, 0]
    , [1000001, 2000000, 0]
    , [2000001, 5000000, 0]
    , [5000001, 10000000, 0]
    , [10000001, 10000000000000, 0]
]

DB_host = 'localhost'
DB_user = 'root'
DB_passwd = 'zxcvbnhy6'

conn = MySQLdb.connect(host = DB_host, user = DB_user, passwd = DB_passwd, db = 'ztcjl4', port = 3306, charset = "utf8")
cur = conn.cursor()

connmongo = pymongo.Connection(host = '223.4.48.150', port = 30001)
ztcjl4 = connmongo.ztcjl4
ztcjl4.authenticate('PS_ztcjl4Admin', 'PS_managerZtcjl4')
account_coll = ztcjl4.subway_account

def main(credit_list):
    sql_acticle_nick = "select nick from router_articleusersubscribe where article_code='ts-25811' and deadline>'2014-05-27 00:00:00' group by nick"
    sql_auth = "select nick,shop_id from auth_user where credit>=%s and credit<%s" % (credit_list[0], credit_list[1])
    cur.execute(sql_acticle_nick)
    user_list = [n[0] for n in cur.fetchall()]
    cur.execute(sql_auth)
    auth_tuple = cur.fetchall()

    day_avg_cost = [
                  [0, 500, 0],
                  [500, 600, 0],
                  [600, 700, 0],
                  [700, 800, 0],
                  [800, 900, 0],
                  [900, 1000, 0],
                  [1000, 10000000, 0]
                  ]
    total_avg_cost = 0
    used_total = 0 #有报表的用户数
    fuwu_total = 0 #所在等级的用户数，不含过期
    total = 0 #所在等级的用户数，含过期
    for a in auth_tuple:
        total = total + 1
        if a[1] and a[0] in user_list:
            fuwu_total = fuwu_total + 1
            pipeline = [
                   {
                       '$match':{'_id':int(a[1])}

                   },
                {
                    '$unwind': '$rpt_list'
                },
                {
                    '$group': {
                        '_id': {'_id': '$_id'
                                },
                        'total_cost': {'$sum': '$rpt_list.cost'}
                    }
                }
            ]
            result = account_coll.aggregate(pipeline)['result']
            rpt_list = account_coll.find_one({'_id':int(a[1])}, {'rpt_list':1, '_id':0})
            if result and rpt_list and rpt_list['rpt_list']:
                used_total = used_total + 1
                total_cost = result[0]['total_cost']
                avg_cost = total_cost / len(rpt_list['rpt_list'])
                avg_cost_1 = avg_cost * 0.01
                avg_cost_30 = avg_cost * 0.3
                total_avg_cost = total_avg_cost + avg_cost_30
                for d in day_avg_cost:
                    if d[0] < avg_cost_1 <= d[1]:
                        d[2] = d[2] + 1
#                print '%s\t%s:\t total_rpt_count=%s,total_cost=%s,avg_cost=%s,avg_cost_30=%s' % (used_total, a[0], len(rpt_list['rpt_list']) , total_cost, avg_cost, avg_cost_30)
    if used_total:
        print day_avg_cost
        print '%s total=%s,fuwu_total=%s,used_total=%s,total_avg_cost=%s,avg=%s' % (credit_list, total, fuwu_total, used_total, total_avg_cost, float(total_avg_cost / (used_total * 1.0)))



if __name__ == "__main__":
    for c in credit_list:
        main(credit_list = c)
    raw_input()
