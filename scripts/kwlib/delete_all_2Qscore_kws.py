# coding=UTF-8
import init_environ
from import_all import *
from import_for_models import *
from import_for_mongodb import *
from apps.subway.models import *
from apps.kwlib.select_base import *
from apps.kwslt.models_cat import cat_coll
from apps.mnt.models import *

# 删除所有自动化监控下的宝贝质量得分2分以下的关键词.包括：长尾托管，重点托管
camps = MntCampaign.objects.filter(mnt_type__gte = 1)
for c_camp in camps:
    all_adgroups = Adgroup.objects.filter(mnt_type__gte = 1, campaign_id = c_camp.campaign_id)
    del_list = []
    for adg in all_adgroups:
#         adg.sync_qscore() 慢
        kw_list = Keyword.objects.filter(shop_id = adg.shop_id, campaign_id = adg.campaign_id, adgroup_id = adg.adgroup_id, qscore = 2)
        for kw in kw_list:
            del_list.append([kw.adgroup_id, kw.keyword_id, kw.word, 0, 0, ''])
    if not del_list:
        continue
    try:
        delete_keywords(shop_id = adg.shop_id, campaign_id = c_camp.campaign_id, kw_arg_list = del_list, tapi = None, record_flag = False)
        print 'shop_id:%s,del_len:%s' % (adg.shop_id, len(del_list))
    except Exception, e:
        log.error('error=%s' % (e))
        continue

print 'game over'
