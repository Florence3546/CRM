# coding=UTF-8
'''刷新客户的服务人员分配'''
import init_environ, datetime
from apps.ncrm.models import Customer

if __name__ == "__main__":
    print 'refresh_customer_consult begin'
    today = datetime.date.today()
    days_30ago = today - datetime.timedelta(days = 30) # 暂定到期时间大于30天前的客户为我们需要的数据
    shop_id_list = list(Customer.objects.filter(latest_end__gte = days_30ago).values_list('shop_id', flat=True))
    i, j, k = 0, 100, len(shop_id_list)
    while shop_id_list[i:i+j]:
        print '%s / %s' % (i+j, k)
        Customer.get_or_create_servers(shop_id_list[i:i+j])
        i += j
    print 'end at %s' % datetime.datetime.now()