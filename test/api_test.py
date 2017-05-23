# coding=UTF-8

import init_environ
from apilib import get_tapi

shop_id = 64377239
nick = '连氏设计'

#===============================================================================
# 清除session缓存
#===============================================================================
# from apps.common.cachekey import CacheKey
# from apps.common.utils.utils_cacheadpter import CacheAdpter

# CacheAdpter.delete(CacheKey.WEB_USER_TAPI % (1, shop_id), 'web')
# CacheAdpter.delete(CacheKey.WEB_USER_TAPI % (2, nick), 'web')

# from apps.router.models import AccessToken
# AccessToken.objects.filter(nick = nick).delete()

#===============================================================================
# 获取客户顾问
#===============================================================================
# from apps.ncrm.models import Customer
# tc = Customer.objects.get(shop_id = shop_id)
# consult = tc.init_consult()
# print consult.name

#===============================================================================
# 同步订单
#===============================================================================
# nick = 'cncys1'
# from apps.router.models import User
# user = User.objects.get(nick = nick)
# from apps.router.models import ArticleUserSubscribe
# ArticleUserSubscribe.sync_aus_byuser(user, 'web')

# 批量获取关键词实时排名
from apps.subway.models_keyword import Keyword
tapi = get_tapi(shop_id = 71193535)
result = Keyword.batch_get_rt_kw_rank(tapi, nick = '您乐诚品', adg_id = 502677342, kw_id_list = [222475302815, 222371433552, 222371433556])
print result
