# coding=UTF-8

import math
import datetime
import collections

from operator import itemgetter
from bson.son import SON
from django.conf import settings
from pymongo.errors import BulkWriteError
from mongoengine.document import EmbeddedDocument, Document
from mongoengine.errors import DoesNotExist
from mongoengine.fields import (IntField, DateTimeField, StringField,
                                ListField, EmbeddedDocumentField, BooleanField)

from apilib import get_tapi, TopError
from apilib.error import ApiLimitError
from apps.common.constant import Const
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import string_2datetime, date_2datetime, time_is_someday, string_2date
from apps.common.utils.utils_collection import genr_sublist
from apps.common.biz_utils.utils_tapitools import get_kw_g_data
from apps.subway.models_upload import UploadRecord, uprcd_coll
from apps.subway.models_campaign import camp_coll
from apps.subway.realtime_report import RealtimeReport
from models_parser import AdgroupParser
from models_report import AdgroupRpt
from apps.subway.utils import (get_msg_count_list, get_note_count, get_comment_count, save_msg_count)
from apps.kwslt.models_cat import Cat, CatStatic


class MntWordInfo(EmbeddedDocument):
    """全自动加词记录"""
    date = DateTimeField(verbose_name = "")
    cur_word_count = IntField(verbose_name = "当前词数量")
    new_word_count = IntField(verbose_name = "选词数量")


class Adgroup(Document):
    ONLINE_STATUS_CHOICES = (("offline", "已暂停"), ("online", "推广中"))
    OFFLINE_TYPE_CHOICES = (("online", "上线"), ("audit_offline", "审核下线"), ("crm_offline", "CRM下线"))
    MNT_TYPE_CHOICES = ((0, "普通"), (1, "长尾托管"), (2, "重点托管"), (3, "ROI托管"), (4, "无线托管"))
    MNT_OPT_TYPE_CHOICES = ((1, "自动优化"), (2, "只改价"))

    # 以下是基础结构数据
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "计划ID", required = True)
    item_id = IntField(verbose_name = "宝贝ID", required = True)
    adgroup_id = IntField(verbose_name = "推广宝贝ID", primary_key = True)
    category_ids = StringField(verbose_name = "商品类目IDS", max_length = 100)
    default_price = IntField(verbose_name = "默认出价")
    max_price = IntField(verbose_name = "非搜索出价")
    isnonsearch_default_price = BooleanField(verbose_name = "非搜索是否用默认出价", choices = ((True, '使用'), (False, '不用')))
    online_status = StringField(verbose_name = "上下线状态", max_length = 10, choices = ONLINE_STATUS_CHOICES)
    offline_type = StringField(verbose_name = "下线类型", max_length = 20, choices = OFFLINE_TYPE_CHOICES)
    create_time = DateTimeField(verbose_name = "创建时间")
    modify_time = DateTimeField(verbose_name = "最后修改时间")
    mobile_discount = IntField(verbose_name = "移动折扣", default = 0) # 默认给0，即没有开启；使用计划的折扣

    # 报表数据
    # rpt_list = ListField(verbose_name = "报表列表", field = EmbeddedDocumentField(Report))
    # nosch_rpt_list = ListField(verbose_name = "定向报表列表", field = EmbeddedDocumentField(Report))

    # 以下是自定义数据
    crtrpt_sync_time = DateTimeField(verbose_name = "创意报表同步时间")
    kwrpt_sync_time = DateTimeField(verbose_name = "关键词报表同步时间")
    kwrpt_valid = BooleanField(verbose_name = "关键词报表是否下载正确", default = False)
    qscore_sync_time = DateTimeField(verbose_name = "质量得分同步时间")
    optm_submit_time = DateTimeField(verbose_name = "优化提交时间")
    optm_type = IntField(verbose_name = "优化类型") # 1：智能优化 2：批量优化 3：类目专家优化

    # 托管配置
    mnt_time = DateTimeField(verbose_name = "加入托管时间")
    quick_optime = DateTimeField(verbose_name = "加大投入/减少投入操作时间")
    mnt_type = IntField(verbose_name = "监控类型", choices = MNT_TYPE_CHOICES, default = 0) # 仍然只保留两种类型
    mnt_opt_type = IntField(verbose_name = "托管优化类型", choices = MNT_OPT_TYPE_CHOICES, default = 1)
    limit_price = IntField(verbose_name = "用户自定义PC端关键词最高限价", default = 200) # 单位为分
    mobile_limit_price = IntField(verbose_name = "用户自定义移动端关键词最高限价", default = 0) # 单位为分
    mnt_rt = IntField(verbose_name = "是否开启实时优化", default = 0)
    opt_wireless = IntField(verbose_name = "是否优化无线折扣", default = 1)
    use_camp_limit = IntField(verbose_name = "使用计划限价", default = 1) # 是否使用计划限价

    mnt_word_info = ListField(verbose_name = "托管加词信息", field = EmbeddedDocumentField(MntWordInfo)) # TODO zhangyu 2013-9-14 记录长尾托管的加词位置

    no_recmd_word_time = DateTimeField(verbose_name = "上次获取淘宝推荐词为空的时间") # 不能赋默认值
    creative_test_switch = BooleanField(verbose_name = "是否开启创意自动测试") # 在添加排队的创意时会自动打开

    msg_status = StringField(verbose_name = "消息状态", default = None) # 格式为 1_2 : 1条备注，2条留言
    opar_status = IntField(verbose_name = "CRM操作状态", choices = ((0, '未操作'), (1, '已操作')), default = 0)
    is_follow = IntField(verbose_name = "是否关注", default = 0)

    msg_count_list = property(fget = get_msg_count_list)
    note_count = property(fget = get_note_count) # 备注条数
    comment_count = property(fget = get_comment_count) # 留言条数
    set_msg_count = property(fget = save_msg_count)

    Parser = AdgroupParser
    Report = AdgroupRpt

    meta = {'collection':'subway_adgroup', 'indexes':['campaign_id'], "shard_key":('shop_id',)}

    @property
    def real_mobile_limit_price(self):
        return self.mobile_limit_price or self.limit_price

    @property
    def online_status_cn(self):
        if not hasattr(self, '_online_status_cn'):
            self._online_status_cn = dict(self.ONLINE_STATUS_CHOICES).get(self.online_status, '')
        return self._online_status_cn

    @property
    def mnt_opt_type_cn(self):
        if not hasattr(self, '_mnt_opt_type_cn'):
            if self.mnt_type > 0:
                self._mnt_opt_type_cn = dict(self.MNT_OPT_TYPE_CHOICES).get(self.mnt_opt_type, '')
            else:
                self._mnt_opt_type_cn = '不托管'
        return self._mnt_opt_type_cn

    @property
    def cat_data(self): # TODO 返回值已经修改，调用的时候需要确认返回值类型 刘声传 2015.07.30
        """获取推广组的行业数据"""
        if not hasattr(self, '_cat_data'):
            cat_id = self.category_ids.split()[-1]
            self._cat_data = CatStatic.get_market_data_8id(cat_id)
        return self._cat_data

    @property
    def cat_path(self):
        '''获取推广组的所属类目列表'''
        if not hasattr(self, '_cat_path'):
            self._cat_path = ''
            try:
                cat_id = self.category_ids.split(' ')[-1]
                cats_path_dict = Cat.get_cat_path(cat_id_list = [cat_id], last_name = ' ')
                self._cat_path = cats_path_dict.get(cat_id, ['未获取到值'])[0]
            except Exception, e:
                log.error('e=%s' % (e))
        return self._cat_path

    @property
    def campaign(self):
        """获取当前推广组的所属计划"""
        if not hasattr(self, '_campaign'):
            from apps.subway.models_campaign import Campaign
            self._campaign = Campaign.objects.get(shop_id = self.shop_id, campaign_id = self.campaign_id)
        return self._campaign

    @property
    def mnt_campaign(self):
        if not hasattr(self, '_mnt_campaign'):
            try:
                from apps.mnt.models_mnt import MntCampaign
                self._mnt_campaign = MntCampaign.objects.get(shop_id = self.shop_id, campaign_id = self.campaign_id)
            except DoesNotExist:
                self._mnt_campaign = None
        return self._mnt_campaign

    @property
    def item(self):
        """获取当前推广组的所属宝贝"""
        if not hasattr(self, '_item'):
            from apps.subway.models_item import Item
            try:
                self._item = Item.objects.get(shop_id = self.shop_id, item_id = self.item_id)
            except DoesNotExist:
                log.error('can`t get item, shop_id=%s, item_id=%s' % (self.shop_id, self.item_id))
                self._item = None
        return self._item

    @property
    def direct_cat_id(self):
        '''得到宝贝的直属类目ID'''
        if not self.category_ids:
            return ''
        return self.category_ids.split(' ')[-1]

    @property
    def parent_cat_id(self):
        '''得到宝贝的直属类目ID，以及倒数第二级类目ID'''
        if not self.category_ids:
            return '', ''
        temp_list = self.category_ids.split(' ')
        if len(temp_list) == 1:
            return temp_list[0], temp_list[0]
        else:
            return temp_list[-1], temp_list[-2]

    def get_snap_list(self, **kwargs):
        rpt_dict = self.Report.get_snap_list({'shop_id': self.shop_id, 'adgroup_id': self.adgroup_id}, **kwargs)
        return rpt_dict.get(self.adgroup_id, [])

    def get_summed_rpt(self, **kwargs):
        rpt_dict = self.Report.get_summed_rpt({'shop_id': self.shop_id, 'adgroup_id': self.adgroup_id}, **kwargs)
        return rpt_dict.get(self.adgroup_id, self.Report())

    def get_summed_nosch_rpt(self, **kwargs):
        rpt_dict = self.Report.get_summed_rpt({'shop_id': self.shop_id, 'adgroup_id': self.adgroup_id},
                                               search_type = 2, source = {'$in': [1, 2, 4, 5]}, **kwargs)
        return rpt_dict.get(self.adgroup_id, self.Report())


    def get_mobile_status(self):
        platform = self.campaign.platform
        self.mob_enabled = bool(platform['yd_insite'] or platform['yd_outsite'])
        if self.mob_enabled and self.mobile_discount == 0:
            self.mobile_discount = platform['mobile_discount']
        return self.mob_enabled

    # def get_limit_price(self):
    #     if self.mnt_type == 1:
    #         from apps.mnt.models import MntCampaign
    #         mnt_camp = MntCampaign.objects.get(campaign_id = self.campaign_id)
    #         return mnt_camp.limit_price
    #     else:
    #         return (self.limit_price>0) and self.limit_price or 500

    def error_descr(self, camp):
        '''宝贝异常状态描述，结合campaign的状态'''
        if not hasattr(self, '_error_descr'):
            descr = ""
            if camp.online_status == "offline":
                descr = "计划手工暂停"
            elif camp.settle_status == "offline":
                descr = "计划强制下线"
                if camp.settle_reason:
                    if "1" in camp.settle_reason:
                        descr = "账户余额不足"
                    elif "2" in camp.settle_reason:
                        descr = "达到日限额，下线"
                    elif "3" in camp.settle_reason:
                        descr = "不在投放时间"
            if self.offline_type == "audit_offline":
                descr = "宝贝违规下架"
            elif self.offline_type == "crm_offline":
                descr = "宝贝CRM下线"
            self._error_descr = descr
        return self._error_descr

    def offline_descr(self):
        '''宝贝异常状态描述，结合campaign的状态'''
        if not hasattr(self, '_error_descr'):
            descr = ""
            if self.offline_type == "audit_offline":
                descr = "宝贝违规下架"
            elif self.offline_type == "crm_offline":
                descr = "宝贝CRM下线"
            self._offline_descr = descr
        return self._offline_descr
    offline_descr = property(fget = offline_descr)

    @staticmethod
    def get_error_descr(offline_type, camp):
        '''宝贝异常状态描述，结合campaign的状态'''
        # TODO 待清理的代码
        descr = ""
        if camp.online_status == "offline":
            descr = "计划手工暂停"
        elif camp.settle_status == "offline":
            descr = "计划强制下线"
            if camp.settle_reason:
                if "1" in camp.settle_reason:
                    descr = "账户余额不足"
                elif "2" in camp.settle_reason:
                    descr = "达到日限额，下线"
                elif "3" in camp.settle_reason:
                    descr = "不在投放时间"
        if offline_type == "audit_offline":
            descr = "宝贝违规下架"
        elif offline_type == "crm_offline":
            descr = "宝贝CRM下线"
        return descr

    @property
    def select_word_list(self):
        if not hasattr(self, '_select_word_list'):
            from models_keyword import kw_coll
            kw_list = kw_coll.find({'shop_id':self.shop_id,
                                    'campaign_id':self.campaign_id,
                                    'adgroup_id':self.adgroup_id
                                    },
                                   {'word':1, '_id':0}
                                   )
            self._select_word_list = [kw['word'] for kw in kw_list]
        return self._select_word_list

    @property
    def deleted_word_list(self):
        if hasattr(self, '_deleted_word_list'):
            return self._deleted_word_list
        self._deleted_word_list = []
        condition_dict = {'shop_id':self.shop_id, 'adgroup_id':self.adgroup_id, 'data_type':402}
        record_dict = uprcd_coll.find(condition_dict, {'detail_list':1})
        for rcd in record_dict:
            if 'detail_list' in rcd and rcd['detail_list']:
                for detail in rcd['detail_list']:
                    self._deleted_word_list.append(detail.strip('\n').strip())
        return self._deleted_word_list

    @property
    def sale_price(self):
        '''获取宝贝的售卖价格，如果有成交，就直接用成交额/成交笔数，否则直接用item price'''
        if hasattr(self, '_sale_price'):
            return self._sale_price
        self._sale_price = 3000
        if self.rpt_sum.pay and self.rpt_sum.paycount:
            self._sale_price = self.rpt_sum.pay / self.rpt_sum.paycount
        else:
            self._sale_price = self.item.price
        return self._sale_price

    def get_keyword_limit_price(self):
        if self.mnt_type > 0 and self.use_camp_limit == 1:
            from apps.mnt.models_mnt import MntCampaign
            try:
                mnt_camp = MntCampaign.objects.get(shop_id = self.shop_id, campaign_id = self.campaign_id)
                limit_price = min(mnt_camp.max_price, mnt_camp.mobile_max_price)
            except DoesNotExist:
                limit_price = 200
        else:
            limit_price = min(self.limit_price, self.real_mobile_limit_price)
        return limit_price or 200

    @classmethod
    def bulk_update_adg2db(cls, update_list):
        total_updated_num = 0
        for temp_list in genr_sublist(update_list, 1000): # bulk一次最多1000个
            bulk = cls._get_collection().initialize_unordered_bulk_op()
            for update_tuple in temp_list:
                bulk.find(update_tuple[0]).update(update_tuple[1])
            try:
                result = bulk.execute()
                total_updated_num += result['nModified']
            except BulkWriteError, e:
                log.error('bulk_update_kw2db, detail=%s' % e.details)
                total_updated_num += e.details['nModified']
        return total_updated_num

    @classmethod
    def remove_adgroup(cls, shop_id, adgroup_id_list):
        """移除广告组、需要移除自身及其下面对应的创意及关键词"""
        if not adgroup_id_list:
            return True
        else:
            from models_keyword import Keyword
            from models_creative import Creative
            query_dict = {'shop_id': shop_id, '_id': {'$in': adgroup_id_list}}
            cls._get_collection().remove(query_dict)
            id_query = query_dict.pop('_id', None) # 结构与其报表的查询条件，在于主键上有区别，这里区别对待一下
            if id_query is not None:
                query_dict.update({'adgroup_id': id_query})
                cls.Report._get_collection().remove(query_dict)

            Keyword.remove_keyword({'shop_id': shop_id, 'adgroup_id':{'$in': adgroup_id_list}})
            Creative.remove_creative({'shop_id': shop_id, 'adgroup_id':{'$in': adgroup_id_list}})

    @classmethod
    def sort_adg_byrpt(cls, query_dict, sort_list, rpt_days = None, start_date = None, end_date = None):
        """目前仅用于宝贝列表，根据给定的条件，对报表进行排序，并分页"""
        base_query = {'source':-1, 'search_type':-1 }
        if rpt_days:
            date_query = {'date': {'$gte': date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_days))}}
        elif start_date:
            date_query = {'date': {'$gte': string_2datetime(start_date, fmt = '%Y-%m-%d')}}
            if end_date:
                date_query['date'].update({'$lte': string_2datetime(end_date, fmt = '%Y-%m-%d')})
        else:
            date_query = {}

        base_query.update(date_query)
        base_query.update(query_dict)
        result = cls.Report._get_collection().aggregate([
			{'$match': base_query },
            {'$group': {
                '_id': {'adgroup_id': '$adgroup_id'},
                'impressions': {'$sum': '$impressions'},
                'click':{'$sum':'$click'},
                'cost':{'$sum':'$cost'},
                'aclick':{'$sum':'$aclick'},
                'avgpos':{'$last':'$avgpos'},
                'directpay':{'$sum':'$directpay'},
                'indirectpay':{'$sum':'$indirectpay'},
                'directpaycount':{'$sum':'$directpaycount'},
                'indirectpaycount':{'$sum':'$indirectpaycount'},
                'favitemcount':{'$sum':'$favitemcount'},
                'favshopcount':{'$sum':'$favshopcount'},
                'carttotal': {'$sum': '$carttotal'},
                }
            },
            {'$project': {
            	'_id': 0,
            	'adgroup_id': '$_id.adgroup_id',
            	'cost':'$cost',
                'impressions':'$impressions',
                'click':'$click',
                'directpay':'$directpay',
                'indirectpay':'$indirectpay',
                'directpaycount':'$directpaycount',
                'indirectpaycount':'$indirectpaycount',
                'favitemcount':'$favitemcount',
                'favshopcount':'$favshopcount',
                'carttotal': '$carttotal',
            	'pay':{'$add':['$directpay', '$indirectpay']},
                'paycount':{'$add':['$directpaycount', '$indirectpaycount']},
			    'favcount':{'$add':['$favitemcount', '$favshopcount']},
            	'ctr':{'$cond':[{'$eq':['$impressions', 0]}, 0,
                                       {'$divide':['$click', '$impressions']}]
                             },
				'cpc':{'$cond':[{'$eq':['$click', 0]}, 0,
								     {'$divide':['$cost', '$click']}]
                           },
				'conv':{'$cond':[{'$eq':['$click', 0]}, 0,
                                      {'$divide':[{'$add':['$directpaycount', '$indirectpaycount']}, '$click']}]
                            },
			    'roi':{'$cond':[{'$eq':['$cost', 0]}, 0,
                                     {'$divide':[{'$add':['$directpay', '$indirectpay']}, '$cost']}]
                           },
            	}
            },
            {'$sort': sort_list and SON(sort_list) or SON([('cost', -1)])},
            # $project，这里只传给adgroup_id，报表后面再取一遍
            {'$project':{
                '_id': '$adgroup_id'
            }}
        ])
        adg_id_list = []

        if result['ok']:
            for temp_result in result['result']:
                adg_id_list.append(temp_result['_id'])
        return adg_id_list

    @classmethod
    def sort_adg_by_rtrpt(cls, shop_id, camp_id_list, sort_list, filtered_adg_id_list):
        adg_rpt_dict = {}
        for camp_id in camp_id_list:
            adg_rpt_dict.update(RealtimeReport.get_summed_rtrpt(rpt_type = 'adgroup', args_list = [shop_id, camp_id]))
        adg_rpt_list = sorted(adg_rpt_dict.items(), key = lambda k: getattr(k[1], sort_list[0][0]), reverse = True if sort_list[0][1] else False)
        adg_id_list = [adg_item[0] for adg_item in adg_rpt_list if adg_item[0] in filtered_adg_id_list]
        return adg_id_list

    def get_creative_rpt(self):
        """获取广告组下面的创意报表详情"""
        from apps.subway.download import Downloader, Creative
        dler = Downloader.objects.get(shop_id = self.shop_id)
        adg_tuple_list = [(self.adgroup_id, self.campaign_id, self.crtrpt_sync_time or (datetime.datetime.today() - datetime.timedelta(days = Creative.Report.INIT_DAYS)))]
        result, reason = Creative.download_crtrpt_byadgs(shop_id = self.shop_id, tapi = dler.tapi, token = dler.token, adg_tuple_list = adg_tuple_list)
        if result:
            log.info('download adgroup creative rpt OK, shop_id=%s, adgroup_id=%s' % (self.shop_id, self.adgroup_id))
        else:
            log.error('download adgroup creative rpt FAILED, shop_id=%s, adgroup_id=%s, e=%s' % (self.shop_id, self.adgroup_id, reason))
        return result

    def check_kw_rpt(self):
        if self.kwrpt_valid:
            return True
        else:
            from apps.subway.models_keyword import kw_coll
            result = kw_coll.find({'shop_id':self.shop_id, 'adgroup_id':self.adgroup_id, 'rpt_list.date':{'$gte':date_2datetime(datetime.date.today() - datetime.timedelta(days = 1))}}).count() > 0 and True or False
            adg_coll.update({'shop_id':self.shop_id, '_id':self.adgroup_id}, {'$set':{'kwrpt_valid':result}})
            return result

    def kwrpt_isok_today(self):
        adgs = Adgroup.objects.filter(shop_id = self.shop_id, adgroup_id = self.adgroup_id).sum_reports(rpt_days = 1)
        if time_is_someday(self.kwrpt_sync_time) and self.check_kw_rpt(adg = adgs[0]):
            return True
        else:
            return False

    def recover_kw_rpt(self):
        """
        1.首先看adgroup有无报表，无报表则直接跳过（有淘宝数据未准备好的问题）
        2.取时间，看是否今天下载过，下载过则对比报表；未下载过则进行下载
        3.对比报表有误，同样下载一次。
        """
        reload_flag = False
        if not adg_coll.find({'shop_id':self.shop_id, '_id':self.adgroup_id, 'rpt_list.date': {'$gte':date_2datetime(datetime.date.today() - datetime.timedelta(days = 1))}}).count():
            return True
        else:
            from apps.subway.download import Downloader, Keyword
            if time_is_someday(self.kwrpt_sync_time):
                if self.check_kw_rpt():
                    return True
                else:
                    reload_flag = True
                    reload_date = datetime.datetime.now() - datetime.timedelta(days = 1)
            else:
                reload_flag = True
                reload_date = self.kwrpt_sync_time or (datetime.datetime.now() - datetime.timedelta(days = Keyword.Report.INIT_DAYS))

        if reload_flag:
            dler = Downloader.objects.get(shop_id = self.shop_id)
            if dler.tapi and dler.token:
                result, reason = Keyword.download_kwrpt_byadgs(shop_id = self.shop_id, tapi = dler.tapi, token = dler.token, adg_tuple_list = [(self.adgroup_id, self.campaign_id, reload_date)])
                log.info('download adgroup keyword rpt %s, shop_id=%s, adgroup_id=%s' % (result and 'OK' or ('FAILED, %s' % reason), self.shop_id, self.adgroup_id))
                return result

    def ensure_kw_rpt(self):
        if time_is_someday(self.kwrpt_sync_time):
            return True
        else:
            from apps.subway.download import Downloader, Keyword
            reload_date = self.kwrpt_sync_time or (datetime.datetime.now() - datetime.timedelta(days = Keyword.Report.INIT_DAYS))
            dler = Downloader.objects.get(shop_id = self.shop_id)
            if dler.tapi and dler.token:
                result, reason = Keyword.download_kwrpt_byadgs(shop_id = self.shop_id, tapi = dler.tapi, token = dler.token, adg_tuple_list = [(self.adgroup_id, self.campaign_id, reload_date)])
                # result, reason = Keyword.download_kwrpt_byadgs_old(shop_id = self.shop_id, tapi = dler.tapi, token = dler.token, adg_tuple_list = [(self.adgroup_id, self.campaign_id, reload_date)])
                log.info('download adgroup keyword rpt %s, shop_id=%s, adgroup_id=%s' % (result and 'OK' or ('FAILED, %s' % reason), self.shop_id, self.adgroup_id))
                return result
            return False

    # bind_qscore为后台优化/算法优化使用
    # bind_added_kw_qscore为新加词使用，但是由于后台加词较多，调用接口较多，因此该接口实际没有应用
    # update_qsocre为数据库更新数据
    # get_all_qscore实际上与get_qscore_bykwids重合，一个是所有关键词，一个是部分关键词
    # refresh_qscore 取数据并更新到数据库

    def bind_qscore(self, kw_list):
        """确保所有关键词都绑定质量得分"""
        noqscore_kwid_list = []
        for kw in kw_list:
            if len(kw.qscore_dict) == 0:
                noqscore_kwid_list.append(kw.keyword_id)

        if noqscore_kwid_list:
            from apps.subway.models_keyword import Qscore
            qscore_dict = self.get_qscore_bykwids(shop_id = self.shop_id, adgroup_id = self.adgroup_id, kw_id_list = noqscore_kwid_list)
            for kw in kw_list:
                if kw.keyword_id in noqscore_kwid_list:
                    kw.qscore_dict = qscore_dict.get(kw.keyword_id, Qscore.parse_qscore(None))

            # 没有质量得分的词，保存到数据库中
            return self.update_qscore(qscore_dict)

    @classmethod
    def bind_added_kw_qscore(cls, shop_id, adgroup_id, added_kw_list):
        """新加词绑定质量得分数据，暂时不调用，由上面的接口保证数据"""
        kw_id_list = [kw['_id'] for kw in added_kw_list]
        qscore_dict = cls.get_qscore_bykwids(shop_id = shop_id, adgroup_id = adgroup_id, kw_id_list = kw_id_list)
        for kw in added_kw_list:
            kw['qscore_dict'] = qscore_dict.get(kw['_id'], {})

    def get_all_qscore(self):
        """获取该宝贝下所有关键词的质量得分"""
        from apps.subway.models_keyword import kw_coll
        qscore_dict = {}
        kw_id_list = [kw['_id'] for kw in kw_coll.find({'adgroup_id': self.adgroup_id, 'shop_id': self.shop_id}, {'_id':1})]
        if kw_id_list:
            qscore_dict = Adgroup.get_qscore_bykwids(shop_id = self.shop_id, adgroup_id = self.adgroup_id, kw_id_list = kw_id_list)
        return qscore_dict

    def update_qscore(self, qscore_dict):
        """质量得分更新到数据库，并且更新状态"""
        from apps.subway.models_keyword import Keyword
        update_list = []
        for keyword_id, qscore in qscore_dict.items():
            update_list.append(({'_id':keyword_id, 'adgroup_id': self.adgroup_id, 'shop_id': self.shop_id}, {'$set': {'qscore_dict': qscore}}))
        updated_num = Keyword.bulk_update_kw2db(update_list)
        adg_coll.update({'shop_id': self.shop_id, '_id': self.adgroup_id}, {'$set': {'qscore_sync_time': datetime.datetime.now()}})
        return updated_num

    def refresh_qscore(self):
        """刷新质量得分"""
        qscore_dict = self.get_all_qscore()
        return self.update_qscore(qscore_dict)

    @staticmethod
    def update_adgroups_inner(shop_id, adg_arg_dict, tapi, opter, opter_name):
        """更改广告组，最常见的是推广状态
        adg_dict形如{123456:{'online_status':'online'},231654:{'online_status':'offline'}}
        """
        from apps.subway.models_item import Item # 函数内导包，避免和models_item 互相导包进入死循环
        record_dict = {}
        local_upd_dict, del_id_list = {}, [] # 需要本地修改的字典、淘宝提示已经删除的宝贝ID列表、临时保存的操作记录字典
        adgroups = adg_coll.find({'shop_id':shop_id, '_id':{'$in':adg_arg_dict.keys()}}, {'campaign_id':1})
        adg_dict = {adg['_id']:adg['campaign_id'] for adg in adgroups}

        adgroup_qset = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_arg_dict.keys()).only('adgroup_id', 'item_id', 'campaign_id')
        adgroup_dict = {adgroup.adgroup_id:adgroup.item_id for adgroup in adgroup_qset}
        item_id_list = list(set([adgroup.item_id for adgroup in adgroup_qset]))
        item_title_dict = dict(Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('item_id', 'title'))

        for adgroup_id, update_dict  in adg_arg_dict.items():
            item_name = ''
            item_id = adgroup_dict.get(adgroup_id, '')
            if item_id:
                item_name = item_title_dict.get(item_id, '')
            temp_upd_dict = {}
            if update_dict.has_key('online_status'):
                temp_upd_dict.update({'online_status':update_dict['online_status']})
                detail_list = ['将宝贝%s推广' % (update_dict['online_status'] == 'online' and '参与' or '暂停')]
                record_dict.update({adgroup_id:{'shop_id':shop_id, 'campaign_id':adg_dict[adgroup_id], 'adgroup_id':adgroup_id, 'item_name': item_name, 'detail_list':detail_list, 'op_type':2, 'data_type':203, 'opter':opter, 'opter_name': opter_name}})
            if update_dict.has_key('default_price'):
                temp_upd_dict.update({'default_price':update_dict['default_price']})
                detail_list = '宝贝默认出价修改为%s' % update_dict['default_price']
                record_dict.update({adgroup_id:{'shop_id':shop_id, 'campaign_id':adg_dict[adgroup_id], 'adgroup_id':adgroup_id, 'item_name': item_name, 'detail_list':detail_list, 'op_type':2, 'data_type':204, 'opter':opter, 'opter_name': opter_name}})
            #===================================================================
            # 以下代码暂时用不到，以后考虑
            # if update_dict.has_key('nonsearch_max_price'):
            #     temp_upd_dict.update({'nonsearch_max_price':update_dict['nonsearch_max_price']})
            # elif update_dict.has_key('is_nonsearch_default_price'):
            #     temp_upd_dict.update({'is_nonsearch_default_price':update_dict['is_nonsearch_default_price']})
            #===================================================================

            if temp_upd_dict:
                try:
                    top_obj = tapi.simba_adgroup_update(adgroup_id = adgroup_id, **temp_upd_dict)
                    temp_dict = {'online_status':top_obj.adgroup.online_status}
                    if hasattr(top_obj.adgroup, 'default_price'):
                        temp_dict.update({'default_price': top_obj.adgroup.default_price})
                    local_upd_dict.update({adgroup_id: temp_dict})
                except TopError, e:
                    if '指定的推广组不存在' in str(e):
                        del_id_list.append(adgroup_id)
                    log.error('update adgroup ERROR,shop_id = %s, adgroup_id = %s, e = %s' % (shop_id, adgroup_id, e))

        record_list = []
        update_list = []
        for adgroup_id, rcd_dict in record_dict.items():
            if local_upd_dict.has_key(adgroup_id):
                record_list.append(rcd_dict)
                update_list.append(({'shop_id':shop_id, '_id':adgroup_id}, {'$set':local_upd_dict[adgroup_id]}))
        Adgroup.bulk_update_adg2db(update_list)

        # 删除淘宝提示已删除的宝贝
        Adgroup.remove_adgroup(shop_id, del_id_list)
        return local_upd_dict.keys(), del_id_list, record_list


    @staticmethod
    def add_adgroups_inner(shop_id, campaign_id, item_arg_list, tapi, opter, opter_name): # 这里的item_arg_list每个item是个字典，包含了标准的item键值，还有额外的adgroup键和creatvie键
        """批量添加宝贝"""
        from apps.subway.models_creative import Creative, crt_coll
        from apps.subway.models_item import item_coll

        record_list = []
        error_msg_dict = {}

        added_item_list, added_adg_list, added_adg_id_list = [], [], []
        default_price = 25
        current_time_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        for item in item_arg_list:
            try:
                # 提交adgroup，自动生成第一个创意
                tobj = tapi.simba_adgroup_add(campaign_id = campaign_id, item_id = item['_id'], default_price = default_price, title = item['adgroup']['title'], img_url = item['adgroup']['img_url'])
                tobj.adgroup.create_time = current_time_str
                tobj.adgroup.modified_time = current_time_str # 淘宝返回的adgroup对象不包含create_time与modified_time，因此这里赋个值，后续增量会同步过来
                limit_price = item['adgroup'].get('limit_price', 0)
                temp_adgroup_id = tobj.adgroup.adgroup_id
                added_adg_id_list.append(temp_adgroup_id)
                temp_result = Adgroup.Parser.parse(tobj.adgroup, trans_type = "init", extra_dict = {'shop_id': shop_id})
                temp_result.update({'limit_price':limit_price})
                added_adg_list.append(temp_result)
                del item['adgroup']

                # 提交第二个创意
                if item.has_key('creative'):
                    try:
                        tapi.simba_creative_add(adgroup_id = temp_adgroup_id, title = item['creative']['title'], img_url = item['creative']['img_url'])
                    except TopError, e:
                        log.error("simba_creative_add TopError, shop_id=%s, adgroup_id=%s, e=%s" % (shop_id, temp_adgroup_id, e))
                    except Exception, e:
                        log.error("simba_creative_add Error, shop_id=%s, adgroup_id=%s, e=%s" % (shop_id, temp_adgroup_id, e))
                    finally:
                        del item['creative']

                added_item_list.append(item)
                detail_list = ['添加宝贝']
                record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':temp_adgroup_id, 'item_name':item['title'], 'detail_list':detail_list, 'op_type':2, 'data_type':201, 'opter':opter, 'opter_name': opter_name})
            except TopError, e:
                log.error("simba_adgroup_add TopError, shop_id=%s, item_id=%s, e=%s" % (shop_id, item['_id'], e))
                msg = str(e)
                if "isv.entity-exist" in msg:
                    error_msg = "该宝贝已在推广中" # TODO: wangqi 要想办法同步，但是没有提供adgroup_id，只有item_id
                elif "isv.break-the-rule-of-business" in msg:
                    error_msg = "该宝贝可能因为类目、资质限制无法推广，请参考直通车规范"
                elif "isv.entity-not-exist" in msg:
                    error_msg = "该宝贝可能已下线，无法推广"
                else:
                    error_msg = "宝贝添加失败，请联系顾问"
                error_msg_dict.update({item['_id']:error_msg})
            except Exception, e:
                log.error("simba_adgroup_add Error, shop_id=%s, item_id=%s, e=%s" % (shop_id, item['_id'], e))
                error_msg = e.message
                if "has no attribute 'pic_url'" in error_msg:
                    error_msg = '宝贝没有图片'
                elif 'need to wait' in error_msg:
                    error_msg = 'API接口超限'
                else:
                    error_msg = '宝贝添加失败，请联系顾问'
                error_msg_dict.update({item['_id']:error_msg})

        if added_adg_list:
            adg_coll.insert(added_adg_list)
        if added_item_list:
            item_coll.insert(added_item_list, continue_on_error = True, safe = False)
        if added_adg_id_list:
            crt_list = Creative.get_creatives_byadgids(shop_id = shop_id, tapi = tapi, adg_id_list = added_adg_id_list, transfer_flag = True)
            if crt_list:
                crt_coll.insert(crt_list, continue_on_error = True, safe = False) # 可能会有用户也在下载，这边也在下载，造成重复下载的问题，这里设置continue_on_error，直接跳过已有的

        return added_adg_id_list, error_msg_dict, record_list

    @staticmethod
    def delete_adgroups_inner(shop_id, adgroup_id_list, tapi, opter, opter_name):
        from apps.subway.models_item import Item # 函数内导包，避免和models_item 互相导包进入死循环
        del_id_list, cant_del_list, error_str = [], [], ''
        record_list = []
        ztc_del_count = 0
        adgroup_qset = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adgroup_id_list).only('adgroup_id', 'item_id', 'campaign_id')
        adgroup_dict = {adgroup.adgroup_id:[adgroup.item_id, adgroup.campaign_id] for adgroup in adgroup_qset}
        item_id_list = list(set([adgroup.item_id for adgroup in adgroup_qset]))
        item_title_dict = dict(Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('item_id', 'title'))
        for adgroup_id in adgroup_id_list:
            try:
                top_obj = tapi.simba_adgroup_delete(adgroup_id = adgroup_id)
                del_id_list.append(top_obj.adgroup.adgroup_id)
                temp_list = adgroup_dict.get(adgroup_id, [])
                if temp_list:
                    item_id, campaign_id = temp_list
                    title = item_title_dict.get(item_id, '')
                    detail_list = ['删除宝贝']
                    record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adgroup_id, 'item_name':title, 'detail_list':detail_list, 'op_type':2, 'data_type':202, 'opter':opter, 'opter_name': opter_name})
            except TopError, e:
                error_msg = "simba_adgroup_delete TopError(%%s), shop_id=%s, adgroup_id=%s" % (shop_id, adgroup_id)
                if '推广组不存在' in str(e) or '推广组未找到' in str(e):
                    log.info(error_msg % "指定的推广组不存在")
                    del_id_list.append(adgroup_id)
                    ztc_del_count += 1
                elif '该推广组正在参加活动无法删除' in str(e):
                    log.info(error_msg % "该推广组正在参加活动无法删除")
                    cant_del_list.append(adgroup_id)
                else:
                    log.error("%s, error=%s" % (error_msg % "其它错误", e))
                    error_str = "调用淘宝接口发生错误，请过稍后重试"
                    cant_del_list = list(set(adgroup_id_list) - set(del_id_list))
                    break
            except ApiLimitError, e:
                error_str = "淘宝删除宝贝接口已超限，请明天再删除宝贝（或者到直通车后台删除该宝贝）"
                cant_del_list = list(set(adgroup_id_list) - set(del_id_list))
                break

        Adgroup.remove_adgroup(shop_id, del_id_list)
        return del_id_list, cant_del_list, ztc_del_count, record_list, error_str

    @staticmethod
    def update_adgroup_mobdiscount(shop_id, adg_id_list, discount = 100):
        tapi = get_tapi(shop_id = shop_id)
        adg_ids = ','.join(map(str, adg_id_list))
        tobjs = tapi.simba_adgroup_mobilediscount_update(adgroup_ids = adg_ids, mobile_discount = discount)
        if tobjs and hasattr(tobjs, 'result'):
            adg_coll.update({'shop_id': shop_id, '_id': {'$in': adg_id_list}}, {'$set': {'mobile_discount': discount}})
            return True
        else:
            return False

    @staticmethod
    def delete_adgroup_mobdiscount(shop_id, adg_id_list):
        tapi = get_tapi(shop_id = shop_id)
        adg_ids = ','.join(map(str, adg_id_list))
        tobjs = tapi.simba_adgroup_mobilediscount_delete(adgroup_ids = adg_ids)
        if tobjs and hasattr(tobjs, 'result'):
            adg_coll.update({'shop_id': shop_id, '_id': {'$in': adg_id_list}}, {'$set': {'mobile_discount': 0}})
            return True
        else:
            return False

    @staticmethod
    def __get_adgroup_list_bycamp(shop_id, campaign_id, tapi):
        """
                        下载该计划下的所有宝贝
        """
        page_size = 200
        adgroup_list = []
        try:
            top_objs = tapi.simba_adgroupsbycampaignid_get(campaign_id = campaign_id, page_no = 1, page_size = page_size)
            if top_objs and hasattr(top_objs.adgroups.adgroup_list, 'a_d_group') and top_objs.adgroups.adgroup_list.a_d_group:
                adgroup_list.extend(top_objs.adgroups.adgroup_list.a_d_group)
                total_item_count = top_objs.adgroups.total_item
                page_sum = int(math.ceil(float(total_item_count) / page_size))
                for page_no in xrange(2, page_sum + 1): # 根据页数循环取数据
                    top_objs = tapi.simba_adgroupsbycampaignid_get(campaign_id = campaign_id, page_no = page_no, page_size = page_size)
                    if top_objs and hasattr(top_objs.adgroups.adgroup_list, 'a_d_group') and top_objs.adgroups.adgroup_list.a_d_group:
                        adgroup_list.extend(top_objs.adgroups.adgroup_list.a_d_group)
        except TopError, e:
            log.error('get adgroup by campaign failed, shop_id = %s, campaign_id = %s, e = %s' % (shop_id, campaign_id, e))
        return adgroup_list

    @classmethod
    def get_adgroup_list_byadgids(cls, shop_id, adgroup_id_list, tapi):
        """下载给定的adgroup_id列表的adgroup"""
        adgroup_list = []
        for temp_adg_id_list in genr_sublist(adgroup_id_list, 200):
            adgroup_ids = ','.join(str(adgroup_id) for adgroup_id in temp_adg_id_list)
            try:
                top_objs = tapi.simba_adgroupsbyadgroupids_get(adgroup_ids = adgroup_ids, page_size = 200, page_no = 1)
                if top_objs and hasattr(top_objs.adgroups.adgroup_list, "a_d_group") and top_objs.adgroups.adgroup_list.a_d_group:
                    adgroup_list.extend(top_objs.adgroups.adgroup_list.a_d_group)
            except TopError, e:
                log.error('simba_adgroupsbyadgroupids_get TopError, shop_id=%s, e=%s' % (shop_id, e))
        return adgroup_list

    @classmethod
    def __change_increase_adgroups(cls, shop_id, last_sync_time, tapi):
        """增量同步adgroup，包含新增、修改过的"""
        page_no, page_size = 1, 200
        changed_adg_list = []
        try:
            tobjs = tapi.simba_adgroups_changed_get(start_time = last_sync_time, page_size = page_size, page_no = page_no)
            if tobjs and hasattr(tobjs.adgroups.adgroup_list, 'a_d_group') and tobjs.adgroups.adgroup_list.a_d_group:
                total_item = tobjs.adgroups.total_item
                page_count = int(math.ceil(float(total_item) / page_size))
                changed_adg_list.extend(tobjs.adgroups.adgroup_list.a_d_group)
                for i in xrange(2, page_count + 1):
                    tobjs = tapi.simba_adgroups_changed_get(start_time = last_sync_time, page_size = page_size, page_no = i)
                    if tobjs and hasattr(tobjs.adgroups.adgroup_list, 'a_d_group') and tobjs.adgroups.adgroup_list.a_d_group:
                        changed_adg_list.extend(tobjs.adgroups.adgroup_list.a_d_group)
        except TopError, e:
            log.error('simba_adgroups_changed_get error, shop_id=%s, e=%s' % (shop_id, e))
            return False

        if changed_adg_list:
            tobj_adg_dict = {} # 淘宝返回的adgroup字典
            for tobj_adg in changed_adg_list:
                tobj_adg_dict.update({tobj_adg.adgroup_id:tobj_adg.modified_time})

            # 淘宝的接口偶尔会返回奇怪的adgroup，不在已知的计划中，因此这里要利用这个过滤一下
            local_camp_id_list = [camp['_id'] for camp in camp_coll.find({'shop_id':shop_id}, {'_id':1})]
            local_adg_dict = {} # 本地存在的adgroup字典
            mongo_cursor = adg_coll.find({'shop_id':shop_id, '_id':{'$in':tobj_adg_dict.keys()}}, {'modify_time':1})
            for local_adg in mongo_cursor:
                local_adg_dict.update({local_adg['_id']:str(local_adg['modify_time'])})

            adg_dict = {} # 对两个字典的综合，除去有相同时间修改的广告组
            for adg_id, modify_time in tobj_adg_dict.items():
                if local_adg_dict.has_key(adg_id):
                    if not modify_time == local_adg_dict[adg_id]:
                        adg_dict.update({adg_id:'changed'})
                else:
                    adg_dict.update({adg_id:'new'})

            adg_list = Adgroup.get_adgroup_list_byadgids(shop_id = shop_id, adgroup_id_list = adg_dict.keys(), tapi = tapi)
            new_adg_list, changed_adg_dict = [], {}
            for adg in adg_list:
                if adg_dict.get(adg.adgroup_id, 'changed') == 'new':
                    if adg.campaign_id in local_camp_id_list:
                        new_adg_list.append(cls.Parser.parse(adg, trans_type = "init", extra_dict = {'shop_id': shop_id}))
                else:
                    changed_adg_dict.update({adg.adgroup_id:cls.Parser.parse(adg, trans_type = "inc")})

            if new_adg_list:
                from apps.subway.models_item import Item
                new_item_id_list = [adg['item_id'] for adg in new_adg_list] # 根据新增的adgroup同步新增的item数据
                result, reason = Item.sync_item_byids(shop_id = shop_id, tapi = tapi, item_id_list = new_item_id_list)
                if not result:
                    log.error('sync new items ERROR, shop_id=%s, item_id_list=%s, reason=%s' % (shop_id, new_item_id_list, reason))
                else:
                    log.info('sync new items OK, shop_id=%s' % (shop_id))
                adg_coll.insert(new_adg_list)
            if changed_adg_dict:
                update_list = []
                for adg_id, adg_value in changed_adg_dict.items():
                    update_list.append(({'shop_id':shop_id, '_id':adg_id}, {'$set':adg_value}))
                Adgroup.bulk_update_adg2db(update_list)

    @staticmethod
    def __delete_increase_adgroups(shop_id, last_sync_time, tapi):
        """增量删除Adgroup"""
        page_no, page_size = 1, 200
        del_adg_id_list = []
        while(True):
            try:
                tobjs = tapi.simba_adgroupids_deleted_get(start_time = last_sync_time, page_size = page_size, page_no = page_no)
            except TopError, e:
                log.error('simba_adgroupids_delted_get error, shop_id = %s, e = %s' % (shop_id, e))
                return False

            if tobjs and hasattr(tobjs.deleted_adgroup_ids, "number"):
                del_adg_id_list.extend(tobjs.deleted_adgroup_ids.number)
                if len(tobjs.deleted_adgroup_ids.number) < page_size:
                    break
                page_no += 1
            else:
                break

        if del_adg_id_list:
            Adgroup.remove_adgroup(shop_id, del_adg_id_list)
            return True

    @classmethod
    def struct_download(cls, shop_id, tapi):
        """初始化店铺的所有宝贝"""
        try:
            top_adgroup_list = []
            for camp in camp_coll.find({'shop_id':shop_id}, {'_id':1}):
                top_adgroup_list.extend(cls.__get_adgroup_list_bycamp(shop_id = shop_id, campaign_id = camp['_id'], tapi = tapi))

            local_adg_id_list = [adg['_id'] for adg in adg_coll.find({'shop_id':shop_id}, {'_id':1})]
            upd_adg_dict, insert_adg_list, old_adg_id_list = {}, [], []
            for adg in top_adgroup_list:
                if adg.adgroup_id in local_adg_id_list: # 本地有，淘宝有，更新
                    upd_adg_dict.update({adg.adgroup_id:cls.Parser.parse(adg, trans_type = "inc")})
                    old_adg_id_list.append(adg.adgroup_id) # 淘宝与本地的交集
                else: # 本地无，淘宝有，新增
                    insert_adg_list.append(cls.Parser.parse(adg, trans_type = 'init', extra_dict = {'shop_id': shop_id}))
            del_adg_id_list = list(set(local_adg_id_list) - set(old_adg_id_list)) # 本地有，淘宝无，删除

            # 分页插入新的Adgroup
            insert_count = 0
            for temp_insert_list in genr_sublist(insert_adg_list, 50):
                temp_id_list = adg_coll.insert(temp_insert_list)
                insert_count += len(temp_id_list)

            # 更新已有Adgroup
            update_list = []
            for adg_id, update_info in upd_adg_dict.items():
                update_list.append(({'shop_id':shop_id, '_id':adg_id}, {'$set':update_info}))
            Adgroup.bulk_update_adg2db(update_list)

            # 删除不存在的Adgroup
            if del_adg_id_list:
                cls.remove_adgroup(shop_id, del_adg_id_list)
            log.info('init adgroups OK, shop_id = %s, get %s adgroups' % (shop_id, len(top_adgroup_list)))
            return True
        except Exception, e:
            log.error('init adgroups FAILED, shop_id = %s, e = %s' % (shop_id, e))
            return False

    @classmethod
    def increase_download(cls, shop_id, tapi, last_sync_time):
        try:
            cls.__delete_increase_adgroups(shop_id = shop_id, last_sync_time = last_sync_time, tapi = tapi)
            cls.__change_increase_adgroups(shop_id = shop_id, last_sync_time = last_sync_time, tapi = tapi)
            log.info('sync adgroups OK, shop_id = %s' % shop_id)
            return True
        except Exception, e:
            log.error('sync adgroups FAILED, shop_id = %s, e = %s' % (shop_id, e))
            return False

    @classmethod
    def download_adgrpt_bycampids(cls, shop_id, camp_id_list, tapi, token, time_scope):
        """通过遍历计划，下载计划下所有广告组的报表"""
        page_size = 200
        try:
            remove_dict = {'date':{'$lte':date_2datetime(time_scope[1]), '$gte':date_2datetime(time_scope[0])}}
            for camp_id in camp_id_list:
                rpt_list = []
                for search_type, source in cls.Report.REPORT_CFG:
                    base_page_no , effect_page_no = 1, 1
                    base_dict, effect_dict = collections.defaultdict(dict), collections.defaultdict(dict)
                    while(True):
                        try:
                            top_base_objs = tapi.simba_rpt_campadgroupbase_get(campaign_id = camp_id, start_time = time_scope[0], end_time = time_scope[1],
                                                                               search_type = search_type, source = source, subway_token = token,
                                                                               page_no = base_page_no, page_size = page_size, retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
                        except TopError, e:
                            log.error('simba_rpt_campadgroupbase_get TopError, shop_id=%s, campaign_id=%s, time=%s, search_type=%s, e=%s' % (shop_id, camp_id, time_scope, search_type, e))
                            return 'FAILED'
                        if top_base_objs and hasattr(top_base_objs, 'rpt_campadgroup_base_list') and top_base_objs.rpt_campadgroup_base_list:
                            for base in top_base_objs.rpt_campadgroup_base_list:
                                base_dict[base.adgroup_id].update(cls.Report.parse_rpt(base, 'base'))

                            if len(top_base_objs.rpt_campadgroup_base_list) < page_size:
                                break
                            base_page_no += 1
                        else:
                            break

                    if base_dict:
                        while(True):
                            try:
                                top_effect_objs = tapi.simba_rpt_campadgroupeffect_get(campaign_id = camp_id, start_time = time_scope[0], end_time = time_scope[1],
                                                                                   search_type = search_type, source = source, subway_token = token,
                                                                                   page_no = effect_page_no, page_size = page_size, retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
                            except TopError, e:
                                log.error('simba_rpt_campadgroupeffect_get TopError, shop_id=%s, campaign_id=%s, time=%s, search_type=%s, e=%s' % (shop_id, camp_id, time_scope, search_type, e))
                                return 'FAILED'
                            if top_effect_objs and hasattr(top_effect_objs, 'rpt_campadgroup_effect_list') and top_effect_objs.rpt_campadgroup_effect_list:
                                for effect in top_effect_objs.rpt_campadgroup_effect_list:
                                    effect_dict[effect.adgroup_id].update(cls.Report.parse_rpt(effect, 'effect'))

                                if len(top_effect_objs.rpt_campadgroup_effect_list) < page_size:
                                    break
                                effect_page_no += 1
                            else:
                                break

                        for adg_id, base_rpt_dict in base_dict.items():
                            rpt_list.extend(cls.Report.merge_rpt_dict(base_rpt_dict, effect_dict.get(adg_id, {}), {'shop_id': shop_id, 'campaign_id': camp_id, 'adgroup_id': adg_id}))

                if rpt_list:
                    remove_query = {'shop_id': shop_id, 'campaign_id': camp_id}
                    remove_query.update(remove_dict)
                    cls.Report.update_rpt_list(remove_query, rpt_list)

            log.info('download adgroup rpt OK, shop_id = %s, camp_list=%s' % (shop_id, camp_id_list))
            return 'OK'
        except Exception, e:
            log.error('download adgroup rpt FAILED, shop_id = %s, e = %s' % (shop_id, e))
            return 'FAILED'

    @classmethod
    def report_download(cls, shop_id, tapi, token, time_scope):
        """通过遍历计划，下载计划下所有广告组的报表"""
        camp_id_list = [int(camp['_id']) for camp in camp_coll.find({'shop_id':shop_id}, {'_id':1})]
        return cls.download_adgrpt_bycampids(shop_id, camp_id_list, tapi, token, time_scope)


    @staticmethod
    def get_qscore_bykwids(shop_id, adgroup_id, kw_id_list = None, tapi = None):
        """通过adgroup_id与对应的关键词ID列表取关键词"""
        qscore_dict = {}
        if kw_id_list:
            if not tapi:
                tapi = get_tapi(shop_id = shop_id)

            from models_keyword import Qscore
            for tmp_kwid_list in genr_sublist(kw_id_list, 20): # 一次只能调用20个，太少了！
                bidword_ids = ",".join(map(str, tmp_kwid_list))
                try:
                    tobjs = tapi.simba_keywords_qscore_split_get(ad_group_id = adgroup_id, bidword_ids = bidword_ids)
                    if hasattr(tobjs, 'result') and hasattr(tobjs.result, 'result') and hasattr(tobjs.result.result, 'word_score_list') \
                        and hasattr(tobjs.result.result.word_score_list, 'wordscorelist'):
                        for qscore in tobjs.result.result.word_score_list.wordscorelist:
                            qscore_dict.update({qscore.keyword_id: Qscore.parse_qscore(qscore)})

                except TopError, e:
                    log.error("get_qscore_bykwids TopError, e=%s, adgroup_id=%s, kw_id_list=%s" % (e, adgroup_id, kw_id_list))
                except Exception, e:
                    log.error("get_qscore_bykwids error, e=%s, adgroup_id=%s, kw_id_list=%s" % (e, adgroup_id, kw_id_list))

        return qscore_dict

    @staticmethod
    def del_local_adgroups(shop_id, adgroup_id_list): # 废弃警告 dreprecated!! use "Adgroup.remove_adgroup" instead!
        from models_creative import crt_coll, ccrt_coll
        from models_keyword import kw_coll
        """通过ID删除本地的adgroup"""
        if not adgroup_id_list:
            return True
        adg_coll.remove({'shop_id':shop_id, '_id':{'$in':adgroup_id_list}})
        crt_coll.remove({'shop_id':shop_id, 'adgroup_id':{'$in':adgroup_id_list}})
        ccrt_coll.remove({'shop_id':shop_id, 'adgroup_id':{'$in':adgroup_id_list}})
        kw_coll.remove({'shop_id':shop_id, 'adgroup_id':{'$in':adgroup_id_list}})

    @staticmethod
    def get_adgroup_count(shop_id, campaign_id_list = None):
        '''group by campaign_id，获取计划下的宝贝总个数、推广中个数、暂停中个数'''
        query_dict = {'shop_id':shop_id}
        if campaign_id_list:
            query_dict.update({'campaign_id':{'$in':campaign_id_list}})
        pipeline = [{'$match':query_dict}, {'$project':{'campaign_id':1, 'online_status':1}}, {'$group':{'_id':{'campaign_id':'$campaign_id', 'online_status':'$online_status'}, 'num':{'$sum':1}}}]
        result = adg_coll.aggregate(pipeline)
        temp_result_dict = {}
        if int(result['ok']) == 1 and result['result']:
            for temp_value in result['result']:
                temp_dict = temp_value['_id']
                if not temp_result_dict.has_key(temp_dict['campaign_id']):
                    temp_result_dict.update({temp_dict['campaign_id']:{}})
                temp_result_dict[temp_dict['campaign_id']].update({temp_dict['online_status']:temp_value['num']})

        result_dict = {}
        for campaign_id, info_dict in temp_result_dict.items():
            online_num = info_dict.get('online', 0)
            offline_num = info_dict.get('offline', 0)
            result_dict.update({campaign_id:(online_num + offline_num, online_num, offline_num)})

        return result_dict

    @staticmethod
    def get_adgroup_byitem(shop_id, item_id, camp_id_list = []):
        """在指定的计划ID中,通过宝贝ID获取到相应的推广组"""
        cursor = None
        adgroup_list = []
        try:
            if not camp_id_list :
                cursor = Adgroup.objects.only("adgroup_id").filter(shop_id = shop_id, item_id = item_id)
            else:
                cursor = Adgroup.objects.only("adgroup_id").filter(shop_id = shop_id, campaign_id__in = camp_id_list, item_id = item_id)
        except DoesNotExist , e:
            log.error("get adgroup error by item, shop_id=%s, item_id=%s, camp_id_list=%s,  e=%s" % (shop_id, item_id, camp_id_list, e))
        else:
            if cursor:
                adgroup_list = [ adg for adg in cursor]
        return adgroup_list

    @staticmethod
    def set_adgroup_is_follow(shop_id, adg_id, is_follow = 0):
        try:
            adg_coll.update({'shop_id': shop_id, '_id': adg_id}, {'$set': {'is_follow': is_follow}})
            return True
        except:
            return False

adg_coll = Adgroup._get_collection()
