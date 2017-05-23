# coding=UTF-8
import init_environ, datetime
from apps.mnt.models import MntCampaign
from apps.mnt.utils_wrapper import Wrapper
from apps.ncrm.models import Subscribe
from apps.subway.models import Campaign

def main(rpt_days = 15, attr_name = 'roi', cmp_value = 1):
    print 'begin...'
    attr = '%s%s' % (attr_name, rpt_days)
    count0, count1 = 0, 0
    start = datetime.datetime.now()
    # 收集托管计划和店铺信息
    campaign_id_list = [mnt_camp.campaign_id for mnt_camp in MntCampaign.objects.only('campaign_id')]
    campaign_set = Campaign.objects.filter(campaign_id__in = campaign_id_list)
    shop_camp_dict = {}
    for camp in campaign_set:
        camp_list = shop_camp_dict.setdefault(camp.shop_id, [])
        camp_list.append(camp)

    # 区分店铺的软件版本
    shop_camp_dict_web = {} # 当前有效订单中包含开车精灵web版的店铺
    shop_camp_dict_qn = {} # 当前有效订单中只包含开车精灵qn版的店铺
    camp_id_list = [] # 最终被修改的计划id列表
    today = datetime.date.today()
    subscribe_set = Subscribe.objects.filter(shop__in = shop_camp_dict.keys(), article_code__in = ['ts-25811', 'ts-25811-6', 'FW_GOODS-1921400'], start_date__lte = today, end_date__gt = today).values_list('shop_id', 'article_code')
    for shop_id, article_code in subscribe_set:
        if shop_id in shop_camp_dict_web:
            continue
        if shop_id in shop_camp_dict_qn:
            if article_code in ['ts-25811', 'ts-25811-6']:
                shop_camp_dict_web[shop_id] = shop_camp_dict[shop_id]
                del shop_camp_dict_qn[shop_id]
            continue
        if article_code == 'FW_GOODS-1921400':
            shop_camp_dict_qn[shop_id] = shop_camp_dict[shop_id]
            count0 += 1
        elif article_code in ['ts-25811', 'ts-25811-6']:
            shop_camp_dict_web[shop_id] = shop_camp_dict[shop_id]
            count0 += 1
        camp_id_list.extend([camp.campaign_id for camp in shop_camp_dict[shop_id]])

    for shop_id, camp_list in shop_camp_dict_web.items():
        for camp in camp_list:
            camp_rpt = Wrapper(camp, camp.rpt_list)
            attr_value = getattr(camp_rpt, attr, 0)
            if attr_value < cmp_value:
                camp.title = camp.title.replace('开车精灵-', '').replace('开車精灵-', '').replace('无线精灵-', '')
            else:
                camp.title = camp.title.replace('开車精灵-', '').replace('无线精灵-', '')
                if '开车精灵-' not in camp.title:
                    camp.title = '开车精灵-' + camp.title
            camp.save()
            count1 += 1
            print '【%s / %s  WEB】shop_id=%s, camp_id=%s, %s=%s, title=%s' % (count1, count0, shop_id, camp.campaign_id, attr, attr_value, camp.title)

    for shop_id, camp_list in shop_camp_dict_qn.items():
        for camp in camp_list:
            camp_rpt = Wrapper(camp, camp.rpt_list)
            attr_value = getattr(camp_rpt, attr, 0)
            if attr_value < cmp_value:
                camp.title = camp.title.replace('开车精灵-', '').replace('开車精灵-', '').replace('无线精灵-', '')
            else:
                camp.title = camp.title.replace('开车精灵-', '').replace('开車精灵-', '')
                if '无线精灵-' not in camp.title:
                    camp.title = '无线精灵-' + camp.title
            camp.save()
            count1 += 1
            print '【%s / %s  QN】shop_id=%s, camp_id=%s, %s=%s, title=%s' % (count1, count0, shop_id, camp.campaign_id, attr, attr_value, camp.title)

    MntCampaign.objects.filter(campaign_id__in = camp_id_list).update(set__modify_camp_title_time = datetime.datetime.now())
    print 'end time: %ss' % (datetime.datetime.now() - start).seconds

if __name__ == '__main__':
    main()

