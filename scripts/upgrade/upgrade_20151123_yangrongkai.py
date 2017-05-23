# coding=UTF-8

'''
Created on 2015-11-23

@author: YRK
'''
import time
import datetime
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apps.subway.models_account import account_coll
from apps.web.models import pa_coll
from apps.ncrm.models import Customer



def load_upgrade_account():
    qs_cursor = account_coll.find({'$or':[
                                            {"receive_address":{"$nin":[None, ""]}},
                                            {"receiver":{"$nin":[None, ""]}},
                                            {"receiver_phone":{"$nin":[None, ""]}},
                                            {"zip_code":{"$nin":[None, ""]}}
                                          ]}, {
                                              "_id":1,
                                              "receive_address":1,
                                              "receiver":1,
                                              "receiver_phone":1,
                                              "zip_code":1,
                                        })
    return {info['_id']: DictWrapper(info) for info in qs_cursor}

def upgrade_customer(shop_id, shop_info):
    try:
        customer = Customer.objects.get(shop_id = shop_id)
    except:
        customer = None

    if customer :
        if not customer.receive_address or not customer.receiver or not customer.zip_code:
            if not customer.phone:
                customer.phone = shop_info.receiver_phone

            customer.receive_address = shop_info.receive_address
            customer.receiver = shop_info.receiver
            customer.zip_code = shop_info.zip_code
            customer.save()
        return True
    return False

def bulk_upgrade_account(size = 1000, seconds = 1):
    acc_mapping = load_upgrade_account()

    total_count = len(acc_mapping)
    rest_num = total_count % size
    total_cycle = total_count / size + 1if rest_num > 0 else total_count / size

    start_time = time.time()
    success_count = 0
    fail_count = 0
    all_shop = acc_mapping.keys()
    for index in xrange(total_cycle):
        temp_shops = all_shop[index * size:(index + 1) * size]
        for shop_id in temp_shops:
            shop_info = acc_mapping[shop_id]
            is_success = upgrade_customer(shop_id, shop_info)

            if is_success:
                success_count += 1
            else:
                fail_count += 1
            cur_time = time.time()
            if (cur_time - start_time) > seconds:
                start_time = cur_time
                print "【info】: upgreade customer data : {}%, success count : {} , fail count : {}"\
                    .format((success_count + fail_count) * 100 / total_count, success_count, fail_count)

    print u"【info】: upgreade customer data have finished."

def upgrede_crm_pointmodify():
    """升级crm管控的积分修改类型"""
    before_count = pa_coll.find({'type':'others'}).count()
    if before_count :
        print u'【info】: point record in current time ago, record count : {}'.format(before_count)
        pa_coll.update({'type':'others'}, {"$set":{'type':'pointmodify'}}, multi = True)
        rest_count = pa_coll.find({'type':'others'}).count()
        print u'【info】: point record to upgrede have finished, record count : {}'.format(rest_count)
    else:
        print u'【info】: no to execute upgrede_crm_pointmodify script ....'
    return True



def upgrade():
    bulk_upgrade_account()
    upgrede_crm_pointmodify()

def upgrade_timescope():
    return (datetime.datetime(2015, 11, 27) , datetime.datetime(2015, 12, 6))




