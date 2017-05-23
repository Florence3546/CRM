# coding=utf-8

import datetime
import collections

from bson.son import SON
from mongoengine.document import Document
from mongoengine.fields import IntField, ListField, DateTimeField

from apps.common.cachekey import CacheKey
from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_datetime import time_is_recent, time_is_someday, date_2datetime
from apps.subway.download import Downloader
from apps.subway.models_keyword import Keyword
from apps.subway.models_adgroup import Adgroup

"""
店铺核心词
想像中的流程是这样的
1. 用户打开核心词功能
2. 检查刷新时间
3. 如果是当天的，则直接页面呈现
4. 如果是最近N天内的，则同步这些天的报表数据，在页面呈现
5. 如果不是最近的，则同步报表
6. 然后执行排序/推荐算法，取到前N个关键词
7. 删除之前的前N个关键词
8. 页面呈现

"""

class CoreKeyword(Document):

    shop_id = IntField(verbose_name = "店铺ID", primary_key = True)
    kw_dict_list = ListField(verbose_name = "关键词字典列表") # 修改成[{'campaign_id': campaign_id, 'adgroup_id': adgroup_id, 'keyword_id': keyword_id}]这样的结构好吗？
    update_time = DateTimeField(verbose_name = "更新时间")
    report_sync_time = DateTimeField(verbose_name = "关键词报表刷新时间")
    qscore_sync_time = DateTimeField(verbose_name = "关键词质量得分刷新时间")

    AGGR_DAYS = 7

    STATUS_KEY = CacheKey.WEB_CORE_KEYWORD_STATUS

    meta = {'db_alias': "mnt-db", 'collection': 'engine_corekeyword'}

    def get_status(self):
        return CacheAdpter.get(self.STATUS_KEY % self.shop_id, 'web', None)

    def set_status(self, status):
        return CacheAdpter.set(self.STATUS_KEY % self.shop_id, status, 'web', 60 * 30)

    def del_status(self):
        return CacheAdpter.delete(self.STATUS_KEY % self.shop_id, 'web')

    status = property(fget = get_status, fset = set_status, fdel = del_status) # 使用缓存保存状态，防止重复下载

    def sync_report(self, adg_id_list = None):
        """同步所有关键词的报表，后续可以考虑下载时的加速(event loop或者multi process都可以)"""
        dler, _ = Downloader.objects.get_or_create(shop_id = self.shop_id)
        dl_flag, _ = dler.check_status_4rpt(klass = Keyword)
        if dl_flag and dler.tapi:
            return Keyword.download_kwrpt_bycond(shop_id = self.shop_id, tapi = dler.tapi, token = dler.token, rpt_days = 7, cond = 'impressions', adg_id_list = adg_id_list)
        else:
            return True, ''

    def sync_qscore(self):
        if self.kw_dict_list:
            adg_id_list = [kw_dict['adgroup_id'] for kw_dict in self.kw_dict_list]
            adg_id_list = list(set(adg_id_list))

            adg_list = Adgroup.objects.filter(shop_id = self.shop_id, adgroup_id__in = adg_id_list)
            for adgroup in adg_list:
                if not time_is_recent(adgroup.qscore_sync_time, days = 1):
                    adgroup.refresh_qscore()
        return True

    def sync_current_report(self):
        """只同步当前计算出来过的关键词的报表"""
        self.status = 1
        adg_id_list = [temp_kw_dict['adgroup_id'] for temp_kw_dict in self.kw_dict_list]
        result = self.sync_report(adg_id_list)
        if result:
            self.report_sync_time = datetime.datetime.now()
            self.save()
        del self.status
        return result

    def get_top_keywords(self, limit_count = 50, rpt_days = 7):
        """取店铺TOP词，使用报表聚集取出来"""
        # TODO: wangqi 20151216 这里可以使用K均值聚类算法根据多个维度综合找出
        pipeline = [
            {'$match': {'shop_id': self.shop_id, 'date': {'$gte': date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_days))}}},
            {'$group': {
                '_id': '$keyword_id',
                'campaign_id': {'$first': '$campaign_id'},
                'adgroup_id': {'$first': '$adgroup_id'},
                # 'impressions': {'$sum': '$impressions'},
                # 'click':{'$sum':'$click'},
                'cost':{'$sum':'$cost'},
                # 'aclick':{'$sum':'$aclick'},
                # 'avgpos':{'$last':'$avgpos'},
                'directpay':{'$sum':'$directpay'},
                'indirectpay':{'$sum':'$indirectpay'},
                # 'directpaycount':{'$sum':'$directpaycount'},
                # 'indirectpaycount':{'$sum':'$indirectpaycount'},
                # 'favitemcount':{'$sum':'$favitemcount'},
                # 'favshopcount':{'$sum':'$favshopcount'},
                # 'carttotal': {'$sum': '$carttotal'},
                # 'rpt_days': {'$sum': 1}
                }
            },
            {'$project': {
                '_id': '$_id',
                'campaign_id': '$campaign_id',
                'adgroup_id': '$adgroup_id',
                'cost': '$cost',
                'pay':{'$add':['$directpay', '$indirectpay']},
            }},
            {'$sort':SON([('cost', -1), ('pay', -1)])},
            {'$project':{
                '_id': '$_id',
                'adgroup_id': '$adgroup_id',
                'campaign_id': '$campaign_id'
            }},
            {'$limit': limit_count}
        ]
        aggr_result = Keyword.Report._get_collection().aggregate(pipeline)

        kw_dict_list = []
        if aggr_result['ok']:
            for temp_result in aggr_result['result']:
                kw_dict_list.append({
                    'keyword_id': temp_result['_id'],
                    'adgroup_id': temp_result['adgroup_id'],
                    'campaign_id': temp_result['campaign_id']
                })


        self.update_core_kw(kw_dict_list)
        return kw_dict_list

    def update_core_kw(self, kw_dict_list):
        self.kw_dict_list = kw_dict_list
        self.update_time = datetime.datetime.now()
        self.report_sync_time = None
        self.qscore_sync_time = None
        self.save()
        return True

    def calc_top_keywords(self):
        log.info("now calc top_keywords, shop_id=%s" % self.shop_id)
        self.status = 1
        if self.sync_report():
            self.get_top_keywords()
        del self.status
        log.info("calc top_keywords OK, shop_id=%s" % self.shop_id)