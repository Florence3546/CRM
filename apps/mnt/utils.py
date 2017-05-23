# coding=UTF-8

from apilib import get_tapi, TopError
from apps.common.utils.utils_log import log
from apps.subway.models import Campaign, Adgroup, Item

def get_adgroup_4campaign(shop_id, campaign_id, rpt_days):
    adgroup_list = Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id)

    if not adgroup_list:
        return [], 0

    item_id_list, adgroup_id_list, json_adgroup_list, item_dict = [], [], [], {}

    for adgroup in adgroup_list: # 获取其他查询所必要的条件
        if adgroup.item_id not in item_id_list:
            item_id_list.append(adgroup.item_id)
        adgroup_id_list.append(adgroup.adgroup_id)

    item_list = Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list)
    camp = Campaign.objects.only('online_status', 'settle_status', 'settle_reason').get(shop_id = shop_id, campaign_id = campaign_id)

    adg_rpt_dict = Adgroup.Report.get_summed_rpt(query_dict = {'shop_id': shop_id, 'campaign_id': campaign_id}, rpt_days = rpt_days)

    for item in item_list: # 获取宝贝标题，价格，图片路径
        item_dict[item.item_id] = {'title':item.title, 'price':item.price, 'pic_url':item.pic_url}

    for adgroup in adgroup_list: # 附加item，keyword属性，统计报表
        item_id = adgroup.item_id
        limit_price = (adgroup.limit_price and adgroup.limit_price or 0)
        adg_rpt = adg_rpt_dict.get(adgroup.adgroup_id, Adgroup.Report())
        if not item_dict.get(item_id):
            item_dict[item_id] = {'title':'该宝贝可能不存在或者下架，请尝试同步数据', 'price':0, 'pic_url':'/site_media/jl/img/no_photo'}
        json_adgroup_list.append({'campaign_id':campaign_id,
                                  'item_id':item_id,
                                  'item_title':item_dict[item_id]['title'],
                                  'item_price':format(item_dict[item_id]['price'] / 100.0, '.2f'),
                                  'item_pic_url':item_dict[item_id]['pic_url'],
                                  'comment_count':adgroup.comment_count,
                                  'total_cost':format(adg_rpt.cost / 100.0, '.2f'),
                                  'impr':adg_rpt.impressions,
                                  'click':adg_rpt.click,
                                  'click_rate':format(adg_rpt.ctr, '.2f'),
                                  'ppc':format(adg_rpt.cpc / 100.0, '.2f'),
                                  'total_pay':format(adg_rpt.pay / 100.0, '.2f'),
                                  'paycount':adg_rpt.paycount,
                                  'favcount':adg_rpt.favcount,
                                  'conv':format(adg_rpt.conv, '.2f'),
                                  'roi':format(adg_rpt.roi, '.2f'),
                                  'online_status':adgroup.online_status,
                                  'error_descr':adgroup.error_descr(camp),
                                  'offline_type':adgroup.offline_type,
                                  'adgroup_id':int(adgroup.adgroup_id),
                                  'mnt_type':adgroup.mnt_type,
                                  'directpay':format(adg_rpt.directpay / 100.0, '.2f'),
                                  'indirectpay':format(adg_rpt.indirectpay / 100.0, '.2f'),
                                  'directpaycount':adg_rpt.directpaycount,
                                  'indirectpaycount':adg_rpt.indirectpaycount,
                                  'favshopcount':adg_rpt.favshopcount,
                                  'favitemcount':adg_rpt.favitemcount,
                                  'limit_price':format(limit_price / 100.0, '.2f')
                                  })

    mnt_num = Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id, mnt_type__gt = 0).count()
    return json_adgroup_list, mnt_num


def modify_campaign_schedule(shop_id, campaign_id, ratio):
    tapi = get_tapi(shop_id = shop_id)

    def get_campaign_schedule(shop_id, campaign_id, tapi):
        try:
            result = tapi.simba_campaign_schedule_get(campaign_id = campaign_id)
            return result.campaign_schedule.schedule
        except TopError, e:
            log.error('get schedule error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, e))
            return ''

    def update_campaign_schedule(shop_id, campaign_id, tapi, schedule):
        try:
            result = tapi.simba_campaign_schedule_update(campaign_id = campaign_id, schedule = schedule)
            return result.campaign_schedule.schedule
        except TopError, e:
            log.error('update schedule error, shop_id=%s, campaign_id=%s, e=%s' % (shop_id, campaign_id, e))
            return ''

    def parse_schedule(schedule_str):
        if schedule_str == 'all':
            return {0:[('00:00-24:00', 100)],
                    1:[('00:00-24:00', 100)],
                    2:[('00:00-24:00', 100)],
                    3:[('00:00-24:00', 100)],
                    4:[('00:00-24:00', 100)],
                    5:[('00:00-24:00', 100)],
                    6:[('00:00-24:00', 100)],
                    }

        result = {}
        schedule_list = schedule_str.split(';')[:7]
        for i, schedule in enumerate(schedule_list):
            if schedule == '0':
                result.update({i:[('00:00-24:00', 0)]})
            else:
                result.update({i:[]})
                for time_set in schedule.split(','):
                    time_scope, ratio = time_set.rsplit(':', 1)
                    result[i].append((time_scope, int(ratio)))

        return result

    setting_list = []
    parse_result = parse_schedule(get_campaign_schedule(shop_id = shop_id, campaign_id = campaign_id, tapi = tapi))

    try:
        for _, time_schedule_list in parse_result.items():
            temp_setting_list = []
            for time_schedule in time_schedule_list:
                old_ratio = time_schedule[1]
                if old_ratio:
                    new_ratio = int(old_ratio * (1 + ratio / 100.0))
                    if new_ratio < 30 or new_ratio > 250:
                        new_ratio = new_ratio < 30 and 30 or 250
                    temp_setting_list.append('%s:%s' % (time_schedule[0], new_ratio))
                else:
                    temp_setting_list.append('0')

            setting_list.append(','.join(temp_setting_list))

        schedule_str = ';'.join(setting_list)
        update_campaign_schedule(shop_id = shop_id, campaign_id = campaign_id, tapi = tapi, schedule = schedule_str)
    except Exception, e:
        log.exception('update campaign schedule error, e=%s' % e)

