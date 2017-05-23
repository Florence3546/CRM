# coding=UTF-8
'''刷新员工的通用客户群缓存'''
import init_environ, datetime
from apps.ncrm.models import PSUser

if __name__ == "__main__":
    print 'refresh_psuser_common_group_cache begin'
    PSUser.refresh_common_group_statistic()
    print 'end at %s' % datetime.datetime.now()