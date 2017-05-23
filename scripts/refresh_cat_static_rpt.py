# coding=UTF-8
# !/usr/bin/env python

import datetime

import init_environ

from apps.kwslt.models_cat import CatStatic

def main():
    today = datetime.date.today()
    for i in xrange(15, 0, -1):
        rpt_date = today - datetime.timedelta(days = i)
        CatStatic.update_cat_market_data(rpt_date = rpt_date)
        print ('ok: %s, %s' % (rpt_date, datetime.datetime.now()))

if __name__ == '__main__':
    print 'start: %s' % datetime.datetime.now()
    main()
    print ' end : %s' % datetime.datetime.now()
