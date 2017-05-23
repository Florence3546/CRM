# coding=UTF-8

import time
import init_environ
from apps.router.models import OrderSyncer

if __name__ == '__main__':
    while True:
        OrderSyncer.sync_order()
        time.sleep(60 * 3)
