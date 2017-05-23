# coding=UTF-8

import init_environ

from apps.web.models import Feedback


def main():
    obj_list = Feedback.objects.select_related('shop', 'consult').filter(consult__name_cn=u'技术部')
    for obj in obj_list:
        obj.consult = obj.shop.operater
        obj.save()

if __name__ == '__main__':
    main()
