#!/usr/bin/env python
# coding=UTF-8
import init_environ

def main():
    from apps.web.models import LotteryOrder
    cfg_list = [['ts-25811-6', '类目版', 69900, 2000, 1, 'http://tb.cn/G1UvNfx'],
                ['ts-25811-6', '类目版', 199900, 2000, 3, 'http://tb.cn/05FvNfx'],
                ['ts-25811-6', '类目版', 369900, 2000, 6, 'http://tb.cn/uGAvNfx'],
                ['ts-25811-6', '类目版', 699900, 2000, 12, 'http://tb.cn/TYsuNfx'],
                ['ts-25811-v9', 'VIP', 300000, 2000, 1, 'http://tb.cn/lTkuNfx'],
                ['ts-25811-v9', 'VIP', 600000, 2000, 3, 'http://tb.cn/LohuNfx'],
                ['ts-25811-v9', 'VIP', 1200000, 2000, 6, 'http://tb.cn/aVbuNfx'],
                ['ts-25811-v9', 'VIP', 2400000, 2000, 12, 'http://tb.cn/R9QuNfx'],
                ['ts-25811-5', '基础版', 15000, 5000, 1, 'http://tb.cn/qABuNfx'],
                ['ts-25811-5', '基础版', 15000, 5000, 3, 'http://tb.cn/vp1uNfx'],
                ['ts-25811-5', '基础版', 27000, 5000, 6, 'http://tb.cn/yTotNfx'],
                ['ts-25811-5', '基础版', 48000, 5000, 12, 'http://tb.cn/R0ktNfx'],
                ['ts-25811-8', '专业版', 22000, 5000, 1, 'http://tb.cn/2bitNfx'],
                ['ts-25811-8', '专业版', 33000, 5000, 3, 'http://tb.cn/MpbtNfx'],
                ['ts-25811-8', '专业版', 42000, 5000, 6, 'http://tb.cn/bVQtNfx'],
                ['ts-25811-8', '专业版', 72000, 5000, 12, 'http://tb.cn/YPRtNfx'],
                ['ts-25811-1', '旗舰版', 30000, 5000, 1, 'http://tb.cn/c9MtNfx'],
                ['ts-25811-1', '旗舰版', 48000, 5000, 3, 'http://tb.cn/KeDtNfx'],
                ['ts-25811-1', '旗舰版', 60000, 5000, 6, 'http://tb.cn/b0BtNfx'],
                ['ts-25811-1', '旗舰版', 108000, 5000, 12, 'http://tb.cn/uF4tNfx'],
                ['ts-25811-6', '类目版', 69900, 5000, 1, 'http://tb.cn/FIysNfx'],
                ['ts-25811-6', '类目版', 199900, 5000, 3, 'http://tb.cn/cRpsNfx'],
                ['ts-25811-6', '类目版', 369900, 5000, 6, 'http://tb.cn/FZdsNfx'],
                ['ts-25811-6', '类目版', 699900, 5000, 12, 'http://tb.cn/zdcsNfx'],
                ['ts-25811-v9', 'VIP', 300000, 5000, 1, 'http://tb.cn/3XOsNfx'],
                ['ts-25811-v9', 'VIP', 600000, 5000, 3, 'http://tb.cn/xwQsNfx'],
                ['ts-25811-v9', 'VIP', 1200000, 5000, 6, 'http://tb.cn/dNEsNfx'],
                ['ts-25811-v9', 'VIP', 2400000, 5000, 12, 'http://tb.cn/qIHsNfx'],
                ]

    for cfg in cfg_list:
        desc = '%s%s个月减%s' % (cfg[1], cfg[4], str(cfg[3]/100))
        LotteryOrder.objects.create(name = desc,
                                    desc = desc,
                                    version = cfg[0],
                                    ori_price = cfg[2],
                                    discount = cfg[3],
                                    cycle = cfg[4],
                                    param_str = cfg[5],
                                    is_subscribe = 1,
                                    order_type = 2
                                    )
    print 'add %s records' % len(cfg_list)

if __name__ == '__main__':
    main()
