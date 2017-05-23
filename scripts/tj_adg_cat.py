# coding=UTF-8
import sys
import os, json, csv
import init_environ
import random
import math
from mongoengine.queryset.visitor import Q
from apps.common.utils.utils_datetime import date_2datetime, datetime
from apps.common.utils.utils_collection import genr_sublist
from apps.common.utils.utils_log import log
from apps.subway.download import dler_coll
from apps.subway.models_account import account_coll
from apps.subway.models_campaign import camp_coll, Campaign
from apps.subway.models_adgroup import adg_coll, Adgroup
from apps.mnt.models_mnt import mnt_camp_coll, MntCampaign
from apps.subway.models import Keyword, Item, item_coll
from apps.kwlib.models import Cat
from apps.common.biz_utils.utils_dictwrapper import CampaignHelper, AdgroupHelper
from apps.router.models import ArticleUserSubscribe
from apps.subway.models_account import Account
from apps.ncrm.models import Customer

''' 按维度统计宝贝各种问题 '''

if sys.platform == 'darwin':
    BASE_PATH = '/Users/Jacob/Documents/paithink/data/statistics/'
else:
    BASE_PATH = 'D:/ztcjingling/ztcdata/'

def check_file_path():
    if not os.path.isdir(BASE_PATH):
        os.mkdir(BASE_PATH)

def tj_adg_data():

    def export_to_file(tj_type, title, data):
        check_file_path()
        today = datetime.date.today()
        path = '%s%s_%s.csv' % (BASE_PATH, tj_type, today)
        csvfile = file(path, 'ab+')
        writer = csv.writer(csvfile)
        if title:
            writer.writerow(title)
        if data:
            writer.writerows(data)
        csvfile.close()

    def get_cat_click_8id(cat_id): # 根据行业类目ID获取数据
        click = None
        try:
            cat_data = Cat.get_cat_stat_info(cat_id_list = [cat_id])
            if cat_data:
                click = cat_data['result'][str(cat_id)]['all_click']
        except Exception, e:
            click = None
        return click

    def get_cat_avg_ctr(item, cat_data): # 行业类目平均点击率
        ctr = None
        try:
            if item and cat_data and item.cat_id:
                ctr = cat_data['result'][str(item.cat_id)]['avg_ctr']
        except Exception, e:
            ctr = None
        return ctr

    def get_cat_avg_conv(item, cat_data): # 行业类目平均点击转化率
        conv = None
        try:
            if item and cat_data and item.cat_id:
                conv = cat_data['result'][str(item.cat_id)]['avg_conv']
        except Exception, e:
            conv = None
        return conv

    def get_cat_avg_cpc(item, cat_data): # 行业类目平均PPC
        conv = None
        try:
            if item and cat_data and item.cat_id:
                conv = cat_data['result'][str(item.cat_id)]['avg_cpc']
        except Exception, e:
            conv = None
        return conv

    def get_cat_all_click(item, cat_data): # 行业类目总点击数
        click = None
        try:
            if item and cat_data and item.cat_id:
                click = cat_data['result'][str(item.cat_id)]['all_click']
        except Exception, e:
            click = None
        return click

    def get_cat_competition(item, cat_data): # 行业类目竞争度
        competition = None
        try:
            if item and cat_data and item.cat_id:
                competition = cat_data['result'][str(item.cat_id)]['competition']
        except Exception, e:
            competition = None
        return competition

    def get_avg_qscore(kw_list, adgroup_id): # 平均质量得分
        qscore = None
        try:
            # kw_list = Keyword.objects.only('qscore').filter(adgroup_id = adgroup_id)
            if kw_list:
                qscore = sum([kw.qscore for kw in kw_list]) / (len(kw_list) * 1.00)
                # print '%s / %s = %s' % (sum([kw.qscore for kw in kw_list]), len(kw_list), qscore)
        except Exception, e:
            qscore = None
        return qscore

    def get_qscore_rate(kw_list, adgroup_id): # 质量得分5分以下的占比
        rate = None
        try:
            # kw_list = Keyword.objects.only('qscore').filter(adgroup_id = adgroup_id)
            if kw_list:
                sub_list = [kw for kw in kw_list if kw.qscore < 5]
                if sub_list:
                    rate = len(sub_list) / (len(kw_list) * 1.00)
                    # print '%s / %s = %s' % (len(sub_list),len(kw_list),rate)
                else:
                    rate = 0
        except Exception, e:
            rate = None
        return rate

    def calc_kw_1(adgroup):
        result = None
        try:
            kw_list = Keyword.objects(adgroup_id = adgroup.adgroup_id).sum_reports(rpt_days = 30)
            if kw_list:
                num1 = sum([kw.qr.click * kw.qr.cpc for kw in kw_list])
                num2 = sum([kw.qr.click for kw in kw_list])
                if num2:
                    result = num1 / 100 / num2
                # print '%s / %s = %s' % (num1, num2, result)
        except Exception, e:
            result = None
        return result

    def write_csv_head():
        csv_title_1 = ['shop_id', 'camp_id', 'item_id', 'adg_id', 'kw_count']
        csv_title_2 = ['shop_id', 'camp_id', 'item_id', 'adg_id', 'kw_avg', 'kw_rate']
        csv_title_3 = ['shop_id', 'camp_id', 'item_id', 'adg_id', '3_day_impr', '3_day_click']
        csv_title_4 = ['shop_id', 'camp_id', 'item_id', 'adg_id', '7_day_avg_click', 'cat_click', 'example_cat_std_click', 'example_cat_click', 'current_cat_click', 'expression']
        csv_title_5 = ['shop_id', 'camp_id', 'item_id', 'adg_id', 'ppc', 'cat_avg_ppc', 'roi', 'cat_avg_conv', 'budget']
        csv_title_6 = ['shop_id', 'camp_id', 'item_id', 'adg_id', '7_day_ctr', 'cat_avg_ctr']
        csv_title_7 = ['shop_id', 'camp_id', 'item_id', 'adg_id', 'kw_count', '7_day_conv', 'cat_avg_conv']
        export_to_file('(check_case_1)', csv_title_1, None)
        export_to_file('(check_case_2)', csv_title_2, None)
        export_to_file('(check_case_3)', csv_title_3, None)
        export_to_file('(check_case_4)', csv_title_4, None)
        export_to_file('(check_case_5)', csv_title_5, None)
        export_to_file('(check_case_6)', csv_title_6, None)
        export_to_file('(check_case_7)', csv_title_7, None)

    def cut_list(org_list, slice_size):
        slice_count = int(math.ceil(org_list.count() / float(slice_size)))
        for i in xrange(slice_count):
            yield org_list[i * slice_size:(i + 1) * slice_size]

    def run_script():
        '''
            #查询模型时注意时带上片键
        '''
        example_cat_std_click = 100
        example_cat_click = get_cat_click_8id(150704)
        article_list = ArticleUserSubscribe.objects.filter(deadline__gt = datetime.datetime.now())
        valid_shop_list = []
        for article in article_list:
            try:
                customer = Customer.objects.get(nick = article.nick)
                if customer:
                    account = Account.objects.get(shop_id = customer.shop_id, balance__gt = 0)
                    if account:
                        valid_shop_list.append(account.shop_id)
                        print '%s %s' % (account.shop_id, len(valid_shop_list))
                        if(len(valid_shop_list) > 1000):
                            break
            except Exception, e:
                continue

        camp_list = Campaign.objects.filter(online_status = 'online', shop_id__in = valid_shop_list).order_by('campaign_id') # 查询所有开启的计划
        for temp_camp_list in cut_list(camp_list, 10):
            for camp in temp_camp_list:
                csv_data_list_1 = []
                csv_data_list_2 = []
                csv_data_list_3 = []
                csv_data_list_4 = []
                csv_data_list_5 = []
                csv_data_list_6 = []
                csv_data_list_7 = []

                local_adg_list = Adgroup.objects.filter(online_status = 'online', shop_id = camp.shop_id, campaign_id = camp.campaign_id).order_by('adgroup_id') # 查询所有开启的推广组
                adgroup_id_list = []
                item_id_list = []
                for adg in local_adg_list:
                    adgroup_id_list.append(adg.adgroup_id)
                    item_id_list.append(adg.item_id)
                adg_rpt_dict = {adg['_id']:AdgroupHelper(**adg) for adg in adg_coll.find({'online_status': 'online', '_id': {'$in': adgroup_id_list}})}
                item_dict = {item.item_id:item for item in Item.objects.filter(item_id__in = item_id_list)}
                for adg in local_adg_list:
                    adg_rpt_data = None
                    item = None
                    if adg.adgroup_id in adg_rpt_dict.keys():
                        adg_rpt_data = adg_rpt_dict[adg.adgroup_id]
                    if adg.item_id in item_dict.keys():
                        item = item_dict[adg.item_id]
                    if not adg_rpt_data:
                        continue;
                    cat_data = adg.cat_data
                    kw_list = Keyword.objects.only('word').filter(adgroup_id = adg.adgroup_id)
                    kw_count = len(kw_list)
                    avg = get_avg_qscore(kw_list, adg.adgroup_id)
                    rate = get_qscore_rate(kw_list, adg.adgroup_id)
                    avg_click_7_day = adg_rpt_data.click7 / 7
                    cat_click = get_cat_all_click(item, cat_data)
                    ppc = adg_rpt_data.cpc7
                    roi = adg_rpt_data.roi7
                    cat_avg_ppc = get_cat_avg_cpc(item, cat_data)
                    cat_avg_conv = get_cat_avg_conv(item, cat_data)
                    result = calc_kw_1(adg)
                    ctr = adg_rpt_data.ctr7
                    cat_avg_ctr = get_cat_avg_ctr(item, cat_data)
                    conv = adg_rpt_data.conv7
                    cat_avg_conv = get_cat_avg_conv(item, cat_data)

                    if kw_count < 100: # 词少， 关键词少于100个
                        csv_data_list_1.append([adg.shop_id, adg.campaign_id, adg.item_id, adg.adgroup_id, kw_count])
                        log.info('camp_id=%s   adg_id=%s   kw_count=%s' % (camp.campaign_id, adg.adgroup_id, kw_count))
                    if avg and rate and avg < 6.5 and rate > 0.4: # 质量得分低， 平均质量得分小于6.5，小于5分的词大于40%
                        csv_data_list_2.append([ adg.shop_id, adg.campaign_id, adg.item_id, adg.adgroup_id, avg, rate])
                        log.info('camp_id=%s   adg_id=%s   avg=%s   rate=%s' % (camp.campaign_id, adg.adgroup_id, avg, rate))

                    if adg_rpt_data.impressions3 > 0 and adg_rpt_data.click3 == 0: # 无点击， 连续3天有展现，点击为零
                        csv_data_list_3.append([ adg.shop_id, adg.campaign_id, adg.item_id, adg.adgroup_id, adg_rpt_data.impressions3, adg_rpt_data.click3])
                        log.info('camp_id=%s   adg_id=%s   qr.impr=%s   qr.click=%s' % (camp.campaign_id, adg.adgroup_id, adg_rpt_data.impressions3, adg_rpt_data.click3))
                    elif cat_click and example_cat_std_click and example_cat_click: # 点击少， 7日均点击少于 max(10,取某个行业点击做为参考值)
                        expression = example_cat_std_click * cat_click / example_cat_click
                        if avg_click_7_day < max(10, expression):
                            csv_data_list_4.append([ adg.shop_id, adg.campaign_id, adg.item_id, adg.adgroup_id, avg_click_7_day, cat_click, example_cat_std_click, example_cat_click, cat_click, expression])
                            log.info('camp_id=%s   adg_id=%s   qr.click=%s   cat.click=%s   example_cat_std_click=%s   example_cat_click=%s   expression=%s' % (camp.campaign_id, adg.adgroup_id, avg_click_7_day, cat_click, example_cat_std_click, example_cat_click, expression))
                    elif item and item.price and cat_avg_ppc and cat_avg_conv and result and roi and ppc: # PPC高, 高于市场均价的1.2倍，大于 min（客单价＊行业转化率/roi, 每个 关键词点击量＊行业ppc 的和/所有点击, 日限额/50）
                        if ppc > cat_avg_ppc * 1.2 and min(item.price * cat_avg_conv / roi, result, camp.budget / 50):
                            csv_data_list_5.append([ adg.shop_id, adg.campaign_id, adg.item_id, adg.adgroup_id, ppc, cat_avg_ppc, roi, cat_avg_conv, camp.budget])
                            log.info('camp_id=%s   adg_id=%s   ppc=%s   roi=%s   cat_avg_ppc=%s   cat_avg_conv=%s   budget=%s' % (camp.campaign_id, adg.adgroup_id, ppc, roi, cat_avg_ppc, cat_avg_conv, local_camp.budget))
                    elif cat_avg_ctr and ctr < cat_avg_ctr * 0.7: # 点击率低, 点击率低于市场点击率的70%
                        csv_data_list_6.append([ adg.shop_id, adg.campaign_id, adg.item_id, adg.adgroup_id, ctr])
                        log.info('camp_id=%s   adg_id=%s   ctr=%s   cat.avg_ctr=%s' % (camp.campaign_id, adg.adgroup_id, ctr, cat_avg_ctr))
                    elif cat_avg_conv and conv < cat_avg_conv * 1.0: # 点击转化率低, 点击转化率低于市场点击率的100%
                        csv_data_list_7.append([ adg.shop_id, adg.campaign_id, adg.item_id, adg.adgroup_id, conv, cat_avg_conv])
                        log.info('camp_id=%s   adg_id=%s   qr.conv=%s   cat.avg_conv=%s' % (camp.campaign_id, adg.adgroup_id, conv, cat_avg_conv))

            export_to_file('(check_case_1)', None, csv_data_list_1)
            export_to_file('(check_case_2)', None, csv_data_list_2)
            export_to_file('(check_case_3)', None, csv_data_list_3)
            export_to_file('(check_case_4)', None, csv_data_list_4)
            export_to_file('(check_case_5)', None, csv_data_list_5)
            export_to_file('(check_case_6)', None, csv_data_list_6)
            export_to_file('(check_case_7)', None, csv_data_list_7)

    def check_adgroup(adg_id):
        example_cat_std_click = 100
        example_cat_click = get_cat_click_8id(150704)
        adg = Adgroup.objects.get(adgroup_id = adg_id)
        camp = Campaign.objects.get(online_status = 'online', campaign_id = adg.campaign_id)
        adg_rpt_dict = {adg['_id']:AdgroupHelper(**adg) for adg in adg_coll.find({'online_status': 'online', '_id': adg_id})}
        item = adg.item
        adg_rpt_data = adg_rpt_dict[adg_id]

        cat_data = adg.cat_data
        kw_list = Keyword.objects.only('word').filter(adgroup_id = adg.adgroup_id)
        kw_count = len(kw_list)
        avg = get_avg_qscore(kw_list, adg.adgroup_id)
        rate = get_qscore_rate(kw_list, adg.adgroup_id)
        avg_click_7_day = adg_rpt_data.click7 / 7
        cat_click = get_cat_all_click(item, cat_data)
        ppc = adg_rpt_data.cpc7
        roi = adg_rpt_data.roi7
        cat_avg_ppc = get_cat_avg_cpc(item, cat_data)
        cat_avg_conv = get_cat_avg_conv(item, cat_data)
        result = calc_kw_1(adg)
        ctr = adg_rpt_data.ctr7
        cat_avg_ctr = get_cat_avg_ctr(item, cat_data)
        conv = adg_rpt_data.conv7
        cat_avg_conv = get_cat_avg_conv(item, cat_data)

        if kw_count < 100: # 词少， 关键词少于100个
            log.info('camp_id=%s   adg_id=%s   kw_count=%s' % (camp.campaign_id, adg.adgroup_id, kw_count))
            print '词少， 关键词少于100个'
        if avg and rate and avg < 6.5 and rate > 0.4: # 质量得分低， 平均质量得分小于6.5，小于5分的词大于40%
            log.info('camp_id=%s   adg_id=%s   avg=%s   rate=%s' % (camp.campaign_id, adg.adgroup_id, avg, rate))
            print '质量得分低， 平均质量得分小于6.5，小于5分的词大于40%'
        if adg_rpt_data.impressions3 > 0 and adg_rpt_data.click3 == 0: # 无点击， 连续3天有展现，点击为零
            log.info('camp_id=%s   adg_id=%s   qr.impr=%s   qr.click=%s' % (camp.campaign_id, adg.adgroup_id, adg_rpt_data.impressions3, adg_rpt_data.click3))
            print '无点击， 连续3天有展现，点击为零'
        if cat_click and example_cat_std_click and example_cat_click: # 点击少， 7日均点击少于 max(10,取某个行业点击做为参考值)
            expression = example_cat_std_click * cat_click / example_cat_click
            if avg_click_7_day < max(10, expression):
                log.info('camp_id=%s   adg_id=%s   qr.click=%s   cat.click=%s   example_cat_std_click=%s   example_cat_click=%s   expression=%s' % (camp.campaign_id, adg.adgroup_id, avg_click_7_day, cat_click, example_cat_std_click, example_cat_click, expression))
                print '点击少， 7日均点击少于 max(10,取某个行业点击做为参考值)'
        elif item and item.price and cat_avg_ppc and cat_avg_conv and result and roi and ppc: # PPC高, 高于市场均价的1.2倍，大于 min（客单价＊行业转化率/roi, 每个 关键词点击量＊行业ppc 的和/所有点击, 日限额/50）
            if ppc > cat_avg_ppc * 1.2 and min(item.price * cat_avg_conv / roi, result, camp.budget / 50):
                log.info('camp_id=%s   adg_id=%s   ppc=%s   roi=%s   cat_avg_ppc=%s   cat_avg_conv=%s   budget=%s' % (camp.campaign_id, adg.adgroup_id, ppc, roi, cat_avg_ppc, cat_avg_conv, local_camp.budget))
                print 'PPC高, 高于市场均价的1.2倍，大于 min（客单价＊行业转化率/roi, 每个 关键词点击量＊行业ppc 的和/所有点击, 日限额/50）'
        elif cat_avg_ctr and ctr < cat_avg_ctr * 0.7: # 点击率低, 点击率低于市场点击率的70%
            log.info('camp_id=%s   adg_id=%s   ctr=%s   cat.avg_ctr=%s' % (camp.campaign_id, adg.adgroup_id, ctr, cat_avg_ctr))
            print '点击率低, 点击率低于市场点击率的70%'
        elif cat_avg_conv and conv < cat_avg_conv * 1.0: # 点击转化率低, 点击转化率低于市场点击率的100%
            log.info('camp_id=%s   adg_id=%s   qr.conv=%s   cat.avg_conv=%s' % (camp.campaign_id, adg.adgroup_id, conv, cat_avg_conv))
            print '点击转化率低, 点击转化率低于市场点击率的100%'

    def check_case_1(): # 词少， 关键词少于100个
        csv_data_list = []
        csv_title = ['shop_id', 'camp_id', 'item_id', 'adg_id', 'kw_count']
        local_camp_list = Campaign.objects(online_status = 'online').order_by('+campaign_id') # 查询所有开启的计划
        for temp_camp_list in genr_sublist(local_camp_list, 10):
            for local_camp in temp_camp_list:
                local_adg_list = Adgroup.objects(online_status = 'online', campaign_id = local_camp.campaign_id).order_by('adgroup_id') # 查询所有开启的推广组
                for temp_adg_list in genr_sublist(local_adg_list, 10):
                    for local_adg in temp_adg_list:
                        local_kw_list = Keyword.objects.only('word').filter(adgroup_id = local_adg.adgroup_id)
                        kw_count = len(local_kw_list)
                        print 'camp_id=%s   adg_id=%s   kw_count=%s' % (local_camp.campaign_id, local_adg.adgroup_id, kw_count)
                        if kw_count < 100:
                            csv_data_list.append([local_adg.shop_id, local_adg.campaign_id, local_adg.item_id, local_adg.adgroup_id, kw_count])
        export_to_file('(check_case_1)', csv_title, csv_data_list)

    def check_case_2(): # 质量得分低， 平均质量得分小于6.5，小于5分的词大于40%
        csv_data_list = []
        csv_title = ['shop_id', 'camp_id', 'item_id', 'adg_id', 'kw_avg', 'kw_rate']
        local_camp_list = Campaign.objects(Q(online_status = 'online')).order_by('+campaign_id') # 查询所有开启的计划
        for temp_camp_list in genr_sublist(local_camp_list, 10):
            for local_camp in temp_camp_list:
                local_adg_list = Adgroup.objects(Q(online_status = 'online') & Q(campaign_id = local_camp.campaign_id)) # 查询所有开启的推广组
                for temp_adg_list in genr_sublist(local_adg_list, 10):
                    for local_adg in temp_adg_list:
                        avg = get_avg_qscore(local_adg.adgroup_id)
                        rate = get_qscore_rate(local_adg.adgroup_id)
                        print 'camp_id=%s   adg_id=%s   avg=%s   rate=%s' % (local_camp.campaign_id, local_adg.adgroup_id, avg, rate)
                        if avg and rate and avg < 6.5 and rate > 0.4:
                            csv_data_list.append([ local_adg.shop_id, local_adg.campaign_id, local_adg.item_id, local_adg.adgroup_id, avg, rate])
        export_to_file('(check_case_2)', csv_title, csv_data_list)

    def check_case_3(): # 无点击， 连续3天有展现，点击为零
        csv_data_list = []
        csv_title = ['shop_id', 'camp_id', 'item_id', 'adg_id', '3_day_impr', '3_day_click']
        local_camp_list = Campaign.objects(Q(online_status = 'online')).order_by('+campaign_id') # 查询所有开启的计划
        for temp_camp_list in genr_sublist(local_camp_list, 10):
            for local_camp in temp_camp_list:
                local_adg_list = Adgroup.objects(Q(online_status = 'online') & Q(campaign_id = local_camp.campaign_id)).sum_reports(rpt_days = 3) # 查询所有开启的推广组
                for temp_adg_list in genr_sublist(local_adg_list, 10):
                    for local_adg in temp_adg_list:
                        print 'camp_id=%s   adg_id=%s   qr.impr=%s   qr.click=%s' % (local_camp.campaign_id, local_adg.adgroup_id, local_adg.qr.impressions, local_adg.qr.click)
                        if local_adg.qr.impressions > 0 and local_adg.qr.click == 0:
                            csv_data_list.append([ local_adg.shop_id, local_adg.campaign_id, local_adg.item_id, local_adg.adgroup_id, local_adg.qr.impressions, local_adg.qr.click])
        export_to_file('(check_case_3)', csv_title, csv_data_list)

    def check_case_4(): # 点击少， 7日均点击少于 max(10,取某个行业点击做为参考值)
        example_cat_std_click = 100
        example_cat_click = get_cat_click_8id(150704)
        csv_data_list = []
        csv_title = ['shop_id', 'camp_id', 'item_id', 'adg_id', '7_day_avg_click', 'cat_click', 'example_cat_std_click', 'example_cat_click', 'current_cat_click', 'expression']
        local_camp_list = Campaign.objects(Q(online_status = 'online')).order_by('+campaign_id') # 查询所有开启的计划
        for temp_camp_list in genr_sublist(local_camp_list, 10):
            for local_camp in temp_camp_list:
                local_adg_list = Adgroup.objects(Q(online_status = 'online') & Q(campaign_id = local_camp.campaign_id)).sum_reports(rpt_days = 7) # 查询所有开启的推广组
                for temp_adg_list in genr_sublist(local_adg_list, 10):
                    for local_adg in temp_adg_list:
                        item = local_adg.item
                        cat_data = local_adg.cat_data
                        click = local_adg.qr.click / 7
                        cat_click = get_cat_all_click(local_adg)
                        if cat_click and example_cat_std_click and example_cat_click:
                            expression = example_cat_std_click * cat_click / example_cat_click
                            print 'camp_id=%s   adg_id=%s   qr.click=%s   cat.click=%s   example_cat_std_click=%s   example_cat_click=%s   expression=%s' % (local_camp.campaign_id, local_adg.adgroup_id, click, cat_click, example_cat_std_click, example_cat_click, expression)
                            if click < max(10, expression):
                                csv_data_list.append([ local_adg.shop_id, local_adg.campaign_id, local_adg.item_id, local_adg.adgroup_id, click, cat_click, example_cat_std_click, example_cat_click, cat_click, expression])
        export_to_file('(check_case_4)', csv_title, csv_data_list)

    def check_case_5(): # PPC高, 高于市场均价的1.2倍，大于 min（客单价＊行业转化率/roi, 每个 关键词点击量＊行业ppc 的和/所有点击, 日限额/50）
        csv_data_list = []
        csv_title = ['shop_id', 'camp_id', 'item_id', 'adg_id', 'ppc', 'cat_avg_ppc', 'roi', 'cat_avg_conv', 'budget']
        local_camp_list = Campaign.objects(Q(online_status = 'online')).order_by('+campaign_id') # 查询所有开启的计划
        for temp_camp_list in genr_sublist(local_camp_list, 10):
            for local_camp in temp_camp_list:
                local_adg_list = Adgroup.objects(Q(online_status = 'online') & Q(campaign_id = local_camp.campaign_id)).sum_reports(rpt_days = 7) # 查询所有开启的推广组
                for temp_adg_list in genr_sublist(local_adg_list, 10):
                    for local_adg in temp_adg_list:
                        item = local_adg.item
                        cat_data = local_adg.cat_data
                        ppc = local_adg.qr.cpc
                        roi = local_adg.qr.roi
                        cat_avg_ppc = get_cat_avg_cpc(item, cat_data)
                        cat_avg_conv = get_cat_avg_conv(item, cat_data)
                        result = calc_kw_1(local_adg)
                        if local_adg.item and local_adg.item.price and cat_avg_ppc and cat_avg_conv and result and roi and ppc:
                            print 'camp_id=%s   adg_id=%s   ppc=%s   roi=%s   cat_avg_ppc=%s   cat_avg_conv=%s   budget=%s' % (local_camp.campaign_id, local_adg.adgroup_id, ppc, roi, cat_avg_ppc, cat_avg_conv, local_camp.budget)
                            if ppc > cat_avg_ppc * 1.2 and min(local_adg.item.price * cat_avg_conv / roi, result, local_camp.budget / 50):
                                csv_data_list.append([ local_adg.shop_id, local_adg.campaign_id, local_adg.item_id, local_adg.adgroup_id, ppc, cat_avg_ppc, roi, cat_avg_conv, local_camp.budget])
        export_to_file('(check_case_5)', csv_title, csv_data_list)

    def check_case_6(): # 点击率低, 点击率低于市场点击率的70%
        csv_data_list = []
        csv_title = ['shop_id', 'camp_id', 'item_id', 'adg_id', '7_day_ctr', 'cat_avg_ctr']
        local_camp_list = Campaign.objects(Q(online_status = 'online')).order_by('+campaign_id') # 查询所有开启的计划
        for temp_camp_list in genr_sublist(local_camp_list, 10):
            for local_camp in temp_camp_list:
                local_adg_list = Adgroup.objects(Q(online_status = 'online') & Q(campaign_id = local_camp.campaign_id)).sum_reports(rpt_days = 7) # 查询所有开启的推广组
                for temp_adg_list in genr_sublist(local_adg_list, 10):
                    for local_adg in temp_adg_list:
                        item = local_adg.item_id
                        cat_data = local_adg.cat_data
                        ctr = local_adg.qr.ctr
                        cat_avg_ctr = get_cat_avg_ctr(item, cat_data)
                        print 'camp_id=%s   adg_id=%s   ctr=%s   cat.avg_ctr=%s' % (local_camp.campaign_id, local_adg.adgroup_id, ctr, cat_avg_ctr)
                        if cat_avg_ctr and local_adg.qr.ctr < cat_avg_ctr * 0.7:
                            csv_data_list.append([ local_adg.shop_id, local_adg.campaign_id, local_adg.item_id, local_adg.adgroup_id, ctr])
        export_to_file('(check_case_6)', csv_title, csv_data_list)

    def check_case_7(): # 点击转化率低, 点击转化率低于市场点击率的100%
        csv_data_list = []
        csv_title = ['shop_id', 'camp_id', 'item_id', 'adg_id', 'kw_count', '7_day_conv', 'cat_avg_conv']
        local_camp_list = Campaign.objects(Q(online_status = 'online')).order_by('+campaign_id') # 查询所有开启的计划
        for temp_camp_list in genr_sublist(local_camp_list, 10):
            for local_camp in temp_camp_list:
                local_adg_list = Adgroup.objects(Q(online_status = 'online') & Q(campaign_id = local_camp.campaign_id)).sum_reports(rpt_days = 7) # 查询所有开启的推广组
                for temp_adg_list in genr_sublist(local_adg_list, 10):
                    for local_adg in temp_adg_list:
                        item = local_adg.item
                        cat_data = local_adg.cat_data
                        conv = local_adg.qr.conv
                        cat_avg_conv = get_cat_avg_conv(item, cat_data)
                        print 'camp_id=%s   adg_id=%s   qr.conv=%s   cat.avg_conv=%s' % (local_camp.campaign_id, local_adg.adgroup_id, conv, cat_avg_conv)
                        if cat_avg_conv and conv < cat_avg_conv * 1.0:
                            csv_data_list.append([ local_adg.shop_id, local_adg.campaign_id, local_adg.item_id, local_adg.adgroup_id, conv, cat_avg_conv])
        export_to_file('(check_case_7)', csv_title, csv_data_list)

    write_csv_head()
    # check_adgroup(615082919)
    check_adgroup(621203265)
    # run_script()

if __name__ == '__main__':
    print 'start: %s' % datetime.datetime.now()
    check_file_path()
    tj_adg_data()
    print 'end : %s' % datetime.datetime.now()
