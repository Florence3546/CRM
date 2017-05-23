#!/uer/bin/env python
# -*- coding:utf-8 -*-

#===========================================================================
#功能：统计不同级别用户所占的数量
#用法：直接执行相应的bat
#by:钟进峰
#===========================================================================

import MySQLdb, sys, datetime
import pymongo
reload(sys)
sys.setdefaultencoding('gb2312')


DB_host = 'localhost'
DB_user = 'root'
DB_passwd = 'zxcvbnhy6'

conn = MySQLdb.connect(host = DB_host, user = DB_user, passwd = DB_passwd, db = 'ztcjl4', port = 3306, charset = "utf8")
cur = conn.cursor()

connmongo = pymongo.Connection(host = '223.4.48.150', port = 30001)
ztcjl4 = connmongo.ztcjl4
ztcjl4.authenticate('PS_ztcjl4Admin', 'PS_managerZtcjl4')
account_coll = ztcjl4.subway_account

sql_acticle_nick = "select nick from router_articleusersubscribe where article_code='ts-25811' and deadline>'2014-05-15 00:00:00' group by nick"
sql_auth = "select nick,credit from auth_user"
cur.execute(sql_acticle_nick)
user_list = [n[0] for n in cur.fetchall()]
cur.execute(sql_auth)
auth_tuple = cur.fetchall()

total = 0
credit = [
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


print 'total:%s' % len(user_list)
for a in auth_tuple:
    if a[0] in user_list:
        for c in credit:
            if c[0] <= a[1] <= c[1]:
                c[2] = c[2] + 1
                break
        user_list.remove(a[0])
        pass


for c in credit:
    print c
raw_input()


