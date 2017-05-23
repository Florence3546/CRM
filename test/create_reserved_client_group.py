# coding=UTF-8
'''
初始化NCRM保留客户群：优先保留、优先剔除
'''


import init_environ
from apps.ncrm.models import ClientGroup, PSUser

def main():
    # psuser_list = PSUser.objects.filter(position__in=('CONSULTLEADER', 'CONSULT')).exclude(status='离职')
    psuser_list = PSUser.objects.filter(position__in=('CONSULTLEADER', 'CONSULT', 'RJJH', 'RJJHLEADER')).exclude(status='离职')
    for psuser in psuser_list:
        cgs = ClientGroup.objects.filter(create_user=psuser, group_type=1)
        if not cgs:
            ClientGroup.objects.create(
                title="优先保留",
                query="",
                id_list=[],
                create_user=psuser,
                note="",
                group_type=1
            )
        cgs = ClientGroup.objects.filter(create_user=psuser, group_type=2)
        if not cgs:
            ClientGroup.objects.create(
                title="优先剔除",
                query="",
                id_list=[],
                create_user=psuser,
                note="",
                group_type=2
            )
        cgs = ClientGroup.objects.filter(create_user=psuser, group_type=3)
        if not cgs:
            ClientGroup.objects.create(
                title="差评跟踪",
                query="",
                id_list=[],
                create_user=psuser,
                note="",
                group_type=3
            )

if __name__ == '__main__':
    main()