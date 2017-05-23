# coding=UTF-8

from apps.ncrm.utils_datacollector import *

SPECIAL_CHARACTER_CONVERT_MAPPING = {
                                                    "‘":"'",
                                                    "’":"'",
                                                    "”":"'",
                                                    "“":"'",
                                     }

CUSTOMER_FIELDS = {
#                                         'shop_id':"店铺ID, 例： 1213 == shop_id ",
                                        'nick':"旺旺昵称, 例:  '神话' in nick (旺旺昵称中含有 ‘神话’ 的客户)",
                                        'is_b2c':"是否是天猫店，例：not is_b2c (不是天猫店) ",
                                        'category':"主营类目, 例 : ‘保健’ in category  (包含 '保健' 关键词的类目)",
                                        'address':"地址，例: '广州' in address (包含 '广州' 关键词的地址)",
                                        'phone':"电话号码，例: phone (含有手机号的用户)"
                                    }

CONFIG_MAPPING = {
                    'is_kcjl':IsKCJL(name = 'is_kcjl', description = '开车精灵客户 ,  例: is_kcjl (开车精灵客户)'),
                    'is_qn':IsQN(name = 'is_qn', description = '千牛客户,  例:  not is_qn (非牵牛客户)'),
                    'is_rjjh':IsRJJH(name = 'is_rjjh', description = '人机结合客户,  例:  is_rjjh (人机结合客户)'),
                    'surplus':Surplus(name = 'surplus', description = '剩余天数，例:  0 < surplus < 7 (剩余天数在七天以内的客户)'),
                    'subscribe':Subscribe(name = 'subscribe', description = '订购天数，例:  0 < subscribe < 7 (订购天数在七天以内的客户)'),
                    'last_order_status':OrderLastBizType(name = 'last_order_status', description = '最后订购状态(1、新订 2、续订  3、升级), 例: last_order_status == 2 (最后一笔订单是续订的客户)'),
                    'order_status_list':OrderExistBizType(name = 'order_status_list', description = '历史所有状态(1、新订 2、续订  3、升级), 例: 2 in order_status_list  (历史订单存在续订的客户)'),
                    'last_pay':OrderLastPay(name = 'last_pay', description = '最后订单支付金额, 例: last_pay > 100 (最后一笔订单支付金额大于 100 元的客户)'),
                    'total_pay':OrderTotalPay(name = 'total_pay', description = '历史总支付金额, 例:  100 < total_pay < 300  (历史所有订单总支付金额大于 100 元小于300元的客户)'),
                    'order_count':OrderCounter(name = 'order_count', description = '订单总数, 例:  1 <= order_count < 4  (历史所有订单总数大于等于 1笔小于4笔的客户)'),
                    'order_salers':OrderSalers(name = 'order_salers', description = '客户历史订单中涉及到的所有销售人员, 例:  12345 in order_operaters (ID为12345的员工 曾销售成功过的所有客户)'),
                    'order_operaters': OrderoOperators(name = 'order_operaters', description = '客户历史订单中涉及到的所有操作人员, 例:  12345 in order_operaters (ID为12345的员工 曾操作过的所有客户)'),
                    'create_time': CreateTime(name = 'create_time', description = '最后一笔软件订单订购时间, 例:  "2014-11-12"<= create_time < "2014-11-13" (2014-11-12 日订购软件的用户)'),
                    'start_date': StartDate(name = 'start_date', description = '最后一笔软件订单开始时间, 例:  "2014-11-12"<= start_date < "2014-11-13" (2014-11-12 日生效的软件用户)'),
                    'end_date': EndDate(name = 'end_date', description = '最后一笔软件订单结束时间, 例:  "2014-11-12"<= end_date < "2014-11-13" (2014-11-12 日到期的软件用户)'),
                    'roi':ROIHandler(name = 'roi', description = '近七天的ROI, 例: roi > 1 (店铺 近7天 的roi大于1的客户 -- 仅支持软件客户)', rpt_days = 7),
                }


