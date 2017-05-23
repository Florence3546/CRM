# coding=UTF-8
import init_environ
import datetime
from apps.mnt.models_task import MntTaskMng, MntTask
from apps.mnt.models_mnt import MntCampaign

strat_time = datetime.datetime(2016, 10, 12, 19, 30)
end_time = datetime.datetime(2016, 10, 13, 10, 30)

mnt_camps = MntCampaign.objects.filter(mnt_type__in = [1, 3])
print len(mnt_camps)
for mnt_campaign in mnt_camps:
    MntTaskMng.generate_quickop_task(shop_id = mnt_campaign.shop_id, campaign_id = mnt_campaign.campaign_id, mnt_type = mnt_campaign.mnt_type, stgy = 2)


def repair_longmnt():
    from apps.common.utils.utils_collection import genr_sublist
    from apps.subway.models_account import Account
    from apps.subway.models_adgroup import adg_coll
    shops = Account.objects.only('shop_id').all()
    shop_ids = [s.shop_id for s in shops]
    total_count = len(shop_ids)
    cur_count = 0
    for shop_id_list in genr_sublist(shop_ids, 50):
        adg_coll.update({'shop_id': {'$in': shop_id_list}, 'use_camp_limit': 0, 'mnt_type': {'$in': [1, 3]}}, {'$set': {'use_camp_list': 1}}, multi=True)
        cur_count += 50
        print 'total_count=%s, cur_count=%s, %s%%, last_shop_id=%s' % (total_count, cur_count, round(cur_count/total_count, 4) * 100, shop_id_list[-1])
    print 'ok'