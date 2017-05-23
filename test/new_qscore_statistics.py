# coding=UTF-8

import init_environ

import json
import datetime
from apilib import get_tapi
from apps.subway.models_adgroup import Adgroup


adg_data_dict = {289489:[386715578, 412668800], 33121618:[400320424]}
file_path = "C:/Users/Administrator/Desktop/qscore.txt"
export_file_path = "D:/ztcdata/statistics/qscore.csv"
rpt_file_path = "D:/ztcdata/statistics/temp_rpt.csv"

def get_lastest_qscore():
    save_dict = {}
    today = str(datetime.date.today())
    for shop_id, adg_id_list in adg_data_dict.items():
        tapi = get_tapi(shop_id = shop_id)

        for adg_id in adg_id_list:
            qscore_dict = Adgroup.get_new_qscore_byadgid(shop_id, adg_id, [], tapi)
            for _, qscore_info in qscore_dict.items():
                qscore_info.update({'date':today})

            save_dict.update({adg_id:qscore_dict})
    print 'get %s\'s qscore OK' % today
    return save_dict

def load_qscore():
    result_dict = {}
    try:
        with open(file_path, 'r+') as f:
            result = f.read()
            if result:
                result_dict = json.loads(result)
        print 'load qscore OK'
    except Exception, e:
        print 'load qscore failed, reason=%s' % e
    finally:
        return result_dict

def save_qscore():
    saved_qscore = load_qscore()
    lastest_qscore = get_lastest_qscore()
    if not saved_qscore:
        for _, kw_qscore_dict in lastest_qscore.items():
            for kw_id, qscore_dict in kw_qscore_dict.items():
                kw_qscore_dict.update({kw_id:[qscore_dict]})
        final_qscore_dict = lastest_qscore
    else:
        for adg_id, kw_qscore_dict in saved_qscore.items():
            lastest_kw_qscore = lastest_qscore.get(int(adg_id))
            for kw_id , kw_qscore_list in kw_qscore_dict.items():
                temp_dict = lastest_kw_qscore.get(int(kw_id), None)
                if temp_dict:
                    kw_qscore_list.append(temp_dict)
        final_qscore_dict = saved_qscore

    try:
        with open(file_path, 'w') as f:
            f.write(json.dumps(final_qscore_dict))
        print 'save qscore OK'
    except Exception, e:
        print 'saved qscore failed, reason=%s' % e


def output_qscore(saved_qscore):

    # TODO: wangqi 20140826 输出到csv中，然后通过图来表现
    from apps.common.utils.utils_log import log
    for adg_id, qscore_dict in saved_qscore.items():
        log.info('==========%s==========' % adg_id)
        for kw_id, qscore_list in qscore_dict.items():
            log.info('----------%s----------' % kw_id)
            for qscore in qscore_list:
                log.info('%s-%s-%s-%s==%s|||%s' % (qscore['rele_score'], qscore['creative_score'], qscore['cust_score'], qscore['cvr_score'], qscore['qscore'], qscore['date']))

def export_tocsv(saved_qscore):
    result_dict = {}
    total_date_set = set()
    for adg_id, qscore_dict in saved_qscore.items():
        new_qscore_list = result_dict.setdefault(adg_id, [])
        for kw_id, qscore_list in qscore_dict.items():
            kw_qscore_dict = {}
            temp_dict = kw_qscore_dict.setdefault(kw_id, {})
            for qscore in qscore_list:
                total_date_set.add(qscore['date'])
                temp_dict.update({qscore['date']:(qscore['rele_score'], qscore['creative_score'], qscore['cust_score'], qscore['cvr_score'], qscore['qscore'])})
            new_qscore_list.append(kw_qscore_dict)

    # export_file_path
    date_list = list(total_date_set)
    date_list.sort()

    export_list = []
    for adg_id, super_qscore_list in result_dict.items():
        for final_qscore_dict in super_qscore_list:
            for kw_id, date_dict in final_qscore_dict.items():
                if len(date_dict) == len(date_list):
                    kw_qscore_list = [adg_id, kw_id]
                    for date_str in date_list:
                        if date_dict.get(date_str, None):
                            kw_qscore_list.extend(date_dict[date_str])
                    export_list.append(kw_qscore_list)
                else:
                    break

    try:
        with open(export_file_path, 'w') as f:
            f.write('宝贝ID,关键词ID,%s \n' % ',,,,,'.join(date_list))
            for export_data in export_list:
                f.write('%s \n' % ','.join(map(str, export_data)))

        print 'export to csv OK'
    except Exception, e:
        print 'export to csv error, e=%s' % e

def load_rpt_data():
    from apps.subway.models_keyword import kw_coll
    # query_dict = {'shop_id':{'$in':adg_data_dict.keys()}, 'adgroup_id':{'$in':reduce(list.__add__, adg_data_dict.values())}}
    query_dict = {'_id':68480694686}
    cursor = kw_coll.find(query_dict)
    result_list = []
    for i in cursor:
        result_list.append(i)

    export_list = []
    for rpt in result_list[0]['rpt_list']:
        pay = rpt['directpay'] + rpt['indirectpay']
        cpc = rpt['click'] > 0 and rpt['cost'] / rpt['click'] or 0
        roi = rpt['cost'] > 0 and pay / float(rpt['cost']) or 0
        ctr = rpt['impressions'] > 0 and rpt['click'] / rpt['impressions']
        paycount = rpt['directpaycount'] + rpt['indirectpaycount']
        favcount = rpt['favitemcount'] + rpt['favshopcount']
        conv = rpt['click'] > 0 and paycount / rpt['click'] or 0
        export_list.append([rpt['date'], rpt['cost'], pay, roi, rpt['click'], rpt['impressions'], ctr, cpc, favcount, paycount, conv])

    try:
        with open(rpt_file_path, 'w') as f:
            for data in export_list:
                f.write('%s \n' % ','.join(map(str, data)))
        print 'save to file OK'
    except Exception, e:
        print 'save to file error, e=%s' % e




if __name__ == '__main__':
    # save_qscore()
    # output_qscore(load_qscore())
    # export_tocsv(load_qscore())
    load_rpt_data()
