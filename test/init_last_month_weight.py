# coding=UTF-8
'''
刷新NCRM退款事件里的签单人、服务人、报账部门、责任部门
'''


import init_environ
from apps.ncrm.models import PSUser

def main():
    PSUser.init_last_month_weight()

if __name__ == '__main__':
    main()