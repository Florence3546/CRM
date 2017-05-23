# coding=UTF-8
'''重新分配所有顾问的客户'''
import init_environ
from apps.ncrm.models import PSUser, ClientGroup, Customer

def main():
    psuser_list = ["金佩","汪锋","欧阳华宇","胡梦","姚远","王昆","薛尧","王洋","冯磊","王玥","丁雪琴","万明","杨勇","尚文蔚","向宇","瞿小凡","熊钰馨","邓雨晴","张志威","蒋雨娜","胡佳丽","桂维维","李雪琴"]
    psuser_list = PSUser.objects.filter(name_cn__in=psuser_list)
    for psuser in psuser_list:
        cgs = ClientGroup.objects.filter(create_user=psuser, group_type=1)
        if cgs:
            cg = cgs[0]
            try:
                id_list = eval(cg.id_list)
                if type(id_list)==list and id_list:
                    cg.id_list = list(Customer.objects.filter(shop_id__in=id_list, consult=psuser).values_list('shop_id', flat=True))
                    cg.save()
            except:
                pass

if __name__ == "__main__":
    print 'init psuser consults begin'
    main()
    print 'end'
