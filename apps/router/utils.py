# coding=UTF-8

from apilib import get_tapi, TopError
from apps.common.utils.utils_log import log
from apps.router.models import User

# TODO: wangqi 20150527 待移除
def get_top_agent_list(nick):
    '''获得店铺的淘宝直通车代理账号信息'''
    try:
        user = User.objects.get(nick = nick)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        return []

    try:
        agent_list = []
        tapi = get_tapi(user)
        top_objs = tapi.simba_customers_authorized_get(nick = nick)
        if hasattr(top_objs, 'nicks') and hasattr(top_objs.nicks, 'string'):
            for agent in top_objs.nicks.string:
                agent_list.append(agent)
    except TopError, e:
        log.info('e=%s' % e)
    return agent_list
