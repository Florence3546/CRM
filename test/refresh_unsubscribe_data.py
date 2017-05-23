# coding=UTF-8
'''
刷新NCRM退款事件里的签单人、服务人、报账部门、责任部门
'''


import init_environ
import datetime
from apps.ncrm.models import event_coll, Subscribe, PSUser

def main():
    psuser_dept_dict = dict(PSUser.objects.values_list('id', 'department'))
    unsub_list = list(event_coll.find({'type':'unsubscribe', 'create_time':{'$gte':datetime.datetime(2016,1,1)}}))
    i = 0
    j = len(unsub_list)
    for unsub in unsub_list:
        try:
            sub_obj = Subscribe.objects.select_related('shop').get(id=unsub['event_id'])
        except Exception, e:
            print e
            continue
        duty_dpt = ''
        if sub_obj.psuser_id:
            duty_dpt = psuser_dept_dict.get(sub_obj.psuser_id, '')
        elif sub_obj.operater_id:
            duty_dpt = psuser_dept_dict.get(sub_obj.operater_id, '')
        elif sub_obj.consult_id:
            duty_dpt = psuser_dept_dict.get(sub_obj.consult_id, '')
        reimburse_dpt = psuser_dept_dict.get(unsub['psuser_id'], '')
        if reimburse_dpt=='QC' and sub_obj.category=='rjjh':
            reimburse_dpt = duty_dpt
        event_coll.update({'_id':unsub['_id']}, {'$set':{
            'nick':sub_obj.shop.nick,
            'category':sub_obj.category,
            'saler_id':sub_obj.psuser_id,
            'server_id':sub_obj.operater_id or sub_obj.consult_id,
            'duty_dpt':duty_dpt,
            'reimburse_dpt':reimburse_dpt
        }})
        i += 1
        print i, j

if __name__ == '__main__':
    main()