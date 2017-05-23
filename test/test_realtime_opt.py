# coding=UTF-8

import init_environ
from apps.engine.realtime_opt import ScreenRealtimeAdgroup, RealtimeOptAdgroup

def main():
    shop_id = 107950512
    adg_list = ScreenRealtimeAdgroup(shop_id).execute()
    for adg in adg_list:
        RealtimeOptAdgroup(adg).execute()

if __name__ == '__main__':
    main()
