# coding=UTF-8

import init_environ
import datetime
from apps.common.utils.utils_sms import send_sms
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import date_2datetime
from apps.ncrm.models import PrivateMessage
from apps.ncrm.models import Customer
from apps.subway.models_account import Account
from apps.engine.models import ShopMngTask
from apps.subway.models_adgroup import Adgroup

def main():
    test_sms()

def send_cn_sms():
    list = ['13554112846', '18571552001']
    username = 'jack'
    content = '''亲，您的直通车帐户里有%s个宝贝可能违规，已被淘宝下架，请立即处理，以免被加大处罚甚至被停车''' % 3
    result = send_sms(list, content)
    if 'code' in result and result['code'] == 0:
        print '中文短信，发成功了！'
    else:
        print '络或者短信平台出问题'

def send_en_sms():
    list = ['13554112846', '18571552001']
    username = 'jack'
    content = 'This is a english sms,please dont reply.'
    result = send_sms(list, content)
    if 'code' in result and result['code'] == 0:
        print 'Send english sms successfull!'
    else:
        print '络或者短信平台出问题'


def test_sms():
    '''测试大任务执行时 有违规下架宝贝 发送短信功能'''
    task = ShopMngTask.objects.get(shop_id = 63518068)
    offline_adgroup_list = Adgroup.objects.filter(shop_id = task.shop_id, offline_type = 'audit_offline').values_list('adgroup_id')
#     account = Account.objects.get(shop_id = task.shop_id)
#     account.sms_send_time = datetime.datetime.now()
#     account.illegal_adgroup_list = offline_adgroup_list
#     account.save()
#     return
    sms_switch = task._sms_switch(offline_adgroup_list = offline_adgroup_list)
    is_need = PrivateMessage.need_2handle(shop_id = task.shop_id)
    if sms_switch and is_need:
        try:
            phone = Customer.objects.get(shop_id = task.shop_id).phone
            if phone:
                username = task.user.nick
                content = '开车精灵紧急提示：%s您好，贵店%s个直通车宝贝被判定违规下架，请立即处理，以免被加大处罚甚至停车。' % (username, len(offline_adgroup_list))
                result = send_sms([phone], content)
                if 'code' in result and result['code'] == 0:
                    account = Account.objects.get(shop_id = task.shop_id)
                    account.sms_send_time = datetime.datetime.now()
                    account.illegal_adgroup_list = offline_adgroup_list
                    account.save()
                    log.info('shopmng task check_adgroup_audit_status send_sms ok, shop_id=%s' % task.shop_id)
                else:
                    log.info('shopmng task check_adgroup_audit_status send_sms error, shop_id=%s, e=网络或者短信平台出问题' % task.shop_id)
            else:
                log.info('shopmng task check_adgroup_audit_status send_sms error, shop_id=%s, e=该用户还没录入手机号' % task.shop_id)
        except Exception, e:
            log.error('shopmng task check_adgroup_audit_status send_sms error, shop_id=%s, e=%s' % (task.shop_id, e))



if __name__ == '__main__':
    main()
