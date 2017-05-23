# coding=UTF-8
import datetime
import init_environ
from apps.mnt.models_monitor import MntCostSnap

def main():
    today = datetime.datetime.now()
    rpt_date_today = datetime.datetime(today.year, today.month, today.day)
    rpt_date_list = [rpt_date_today - datetime.timedelta(days = i) for i in range(1, 5)]
    for rpt_date in rpt_date_list:
        MntCostSnap.refresh_camp_cost(rpt_date = rpt_date)

if __name__ == '__main__':
    main()
