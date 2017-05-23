# coding=UTF-8
import init_environ
from apps.common.utils.utils_log import log
from apps.ncrm.models import Subscribe, Customer
from apps.ncrm.models_order import FuwuOrder

def main():
    try:
        fw_coll = FuwuOrder._get_collection()
        fw_coll.remove({'pay_status': 1}, multi=True)
        all_count = fw_coll.find({}).count()
        i = 0
        del_count = 0
        for doc in fw_coll.find({}):
            i += 1
            nick = doc.get('nick')
            if nick:
                cust = Customer.objects.filter(nick=doc['nick'])
                if cust:
                    exist_sub = Subscribe.objects.filter(shop_id=cust[0].shop_id, article_code=doc['article_code'], create_time__gte=doc['create_time'])
                    if exist_sub:
                        fw_coll.remove(doc['_id'])
                        del_count += 1
                        print 'delelte id: ', doc['_id']
            print '进度：%s / %s，已删 %s' % (i, all_count, del_count)
    except Exception, e:
        log.exception('%s', e)

if __name__ == '__main__':
    main()
    print 'finished!'
