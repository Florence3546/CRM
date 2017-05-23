# coding=UTF-8
import init_environ
import datetime
from apps.engine.models_corekw import CoreKeyword
from apps.subway.models_keyword import Keyword

shop_id = 63518068

kws = Keyword.objects.filter(shop_id=shop_id).limit(10)
kw_dict_list = []
for kw in kws:
    kw_dict_list.append({
        'keyword_id': kw.keyword_id,
        'adgroup_id': kw.adgroup_id,
        'campaign_id': kw.campaign_id
    })

ck, _ = CoreKeyword.objects.get_or_create(shop_id=shop_id)
ck.kw_dict_list = kw_dict_list
ck.update_time = datetime.datetime.now()
ck.report_sync_time = None
ck.qscore_sync_time = None
ck.save()
