# coding=UTF-8
import math
import datetime
import collections

from django.conf import settings
from pymongo.errors import BulkWriteError
from mongoengine.document import Document
from mongoengine.fields import (IntField, DateTimeField, StringField,
                                ListField, EmbeddedDocumentField)

from apilib import TopError, get_tapi
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import date_2datetime, time_is_someday
from apps.common.utils.utils_collection import genr_sublist
from models_parser import CreativeParser
from models_report import CreativeRpt
from apps.subway.models_upload import UploadRecord
from apps.subway.models_adgroup import Adgroup, adg_coll
from apps.subway.utils import (set_rpt_days, get_rpt_days, get_rpt_date,
                               get_rpt_date_list, get_rpt_yt, get_rpt_sum, get_snap_list)

class Creative(Document):
    AUDIT_STATUS_CHOICES = (("audit_wait", "待审核"), ("audit_pass", "审核通过"), ("audit_reject", "审核拒绝"))

    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "计划ID", required = True)
    adgroup_id = IntField(verbose_name = "推广宝贝ID", required = True)
    creative_id = IntField(verbose_name = "创意ID", primary_key = True)
    title = StringField(verbose_name = "创意标题", max_length = 50, required = True)
    img_url = StringField(verbose_name = "创意图片地址", max_length = 255, required = True)
    audit_status = StringField(verbose_name = "审核状态", max_length = 20, choices = AUDIT_STATUS_CHOICES)
    create_time = DateTimeField(verbose_name = "创建时间")
    modify_time = DateTimeField(verbose_name = "最后修改时间")
    abtest_end_time = DateTimeField(verbose_name = "AB测试结束时间")
    # 报表数据
    # rpt_list = ListField(verbose_name = "创意报表列表", field = EmbeddedDocumentField(Report))
    # property
    # rpt_days = property(fget = get_rpt_days, fset = set_rpt_days)
    # rpt_date = property(fget = get_rpt_date)
    # rpt_date_list = property(fget = get_rpt_date_list)
    # rpt_yt = property(fget = get_rpt_yt)
    # rpt_sum = property(fget = get_rpt_sum)
    # snap_list = property(fget = get_snap_list)

    Parser = CreativeParser
    Report = CreativeRpt

    meta = {'collection':'subway_creative', 'indexes':['campaign_id', 'adgroup_id'], "shard_key":('shop_id',)}

    @classmethod
    def bulk_update_crt2db(cls, update_list): # update_list形如[({'_id':1024321654}, {'$set':{'max_price':24}}), ({'_id':1024321651}, {'$set':{'max_price':47}}),...]
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
    def remove_creative(cls, query_dict):
        cls._get_collection().remove(query_dict)
        # id_query = query_dict.pop('_id', None) # 这里历史报表要用于创意优化历史数据、因此不删除创意的报表
        # if id_query is not None:
        #     query_dict.update({'creative_id': id_query})
        #     cls.Report._get_collection().remove(query_dict)

    @classmethod
    def __get_creative_bycrtids(cls, shop_id, creative_id_list, tapi):
        """
                        通过creative_id获取创意
        """
        creative_list = []
        for temp_crt_id_list in genr_sublist(creative_id_list, 200):
            creative_ids = ','.join(str(creative_id) for creative_id in temp_crt_id_list)
            try:
                top_objs = tapi.simba_creatives_get(creative_ids = creative_ids, retry_count = settings.TAPI_RETRY_COUNT * 6, retry_delay = settings.TAPI_RETRY_DELAY)
                if top_objs and hasattr(top_objs, 'creatives') and hasattr(top_objs.creatives, 'creative') and top_objs.creatives.creative:
                    creative_list.extend(top_objs.creatives.creative)
            except TopError, e:
                log.error('simba_creatives_get TopError, shop_id = %s, e = %s' % (shop_id, e))
        return creative_list

    @classmethod
    def __get_creatives_byadg(cls, shop_id, adgroup_id, tapi):
        """
                        下载该宝贝的推广创意
        """
        creative_list = []
        try:
            top_creatives = tapi.simba_creatives_get(adgroup_id = adgroup_id, retry_count = settings.TAPI_RETRY_COUNT * 6, retry_delay = settings.TAPI_RETRY_DELAY)
            if top_creatives and hasattr(top_creatives, 'creatives') and top_creatives.creatives:
                creative_list.extend(top_creatives.creatives.creative)
        except TopError, e:
            log.error('simba_creatives_get by adgroup_id TopError, shop_id=%s, adgroup_id=%s, e=%s' % (shop_id, adgroup_id, e))
        return creative_list

    @classmethod
    def __delete_increase_creatives(cls, shop_id, last_sync_time, tapi):
        """
                        增量删除creative
        """
        page_no, page_size = 1, 200
        deleted_crt_id_list = []

        while(True):
            try:
                tobjs = tapi.simba_creativeids_deleted_get(start_time = last_sync_time, page_size = page_size, page_no = page_no)
            except TopError, e:
                log.error('increase_deleted_creatives error, shop_id = %s, e = %s' % (shop_id, e))
                return False

            if tobjs and hasattr(tobjs.deleted_creative_ids, "number"):
                deleted_crt_id_list.extend(tobjs.deleted_creative_ids.number)
                if len(tobjs.deleted_creative_ids.number) < page_size:
                    break
                page_no += 1
            else:
                break

        if deleted_crt_id_list:
            cls.remove_creative({'shop_id':shop_id, '_id':{'$in':deleted_crt_id_list}})
            return True

    @classmethod
    def __change_increase_creatives(cls, shop_id, last_sync_time, tapi):
        """
                        增量同步修改过的creative
        """
        page_no, page_size = 1, 200
        changed_crt_list = []
        try:
            tobjs = tapi.simba_creatives_changed_get(start_time = last_sync_time, page_size = page_size, page_no = page_no)
            if tobjs and hasattr(tobjs.creatives.creative_list, 'a_d_group') and tobjs.creatives.creative_list.a_d_group:
                total_item = tobjs.creatives.total_item
                page_count = int(math.ceil(float(total_item) / page_size))
                changed_crt_list.extend(tobjs.creatives.creative_list.a_d_group)
                for i in xrange(2, page_count + 1):
                    tobjs = tapi.simba_creatives_changed_get(start_time = last_sync_time, page_size = page_size, page_no = i)
                    if tobjs and hasattr(tobjs.creatives.creative_list, 'a_d_group') and tobjs.creatives.creative_list.a_d_group:
                        changed_crt_list.extend(tobjs.creatives.creative_list.a_d_group)
        except TopError, e:
            log.error('simba_creatives_changed_get TopError, shop_id = %s, e = %s' % (shop_id, e))


        if changed_crt_list:
            tobj_crtid_list = [] # 淘宝返回的creative_id列表
            for tobj_crt in changed_crt_list:
                tobj_crtid_list.append(tobj_crt.creative_id)

            local_crtid_list = [] # 本地存在的creative字典
            mongo_cursor = crt_coll.find({'shop_id':shop_id, '_id':{'$in':tobj_crtid_list}}, {'_id':1})
            for local_crt in mongo_cursor:
                local_crtid_list.append(local_crt['_id'])

            newid_list = list(set(tobj_crtid_list) - set(local_crtid_list)) # 新增的创意ID列表
            crt_list = Creative.__get_creative_bycrtids(shop_id = shop_id, creative_id_list = tobj_crtid_list, tapi = tapi)
            new_crt_list, changed_crt_dict = [], {}
            for crt in crt_list:
                if crt.creative_id in newid_list:
                    new_crt_list.append(cls.Parser.parse(crt, trans_type = "init", extra_dict = {'shop_id': shop_id}))
                else:
                    changed_crt_dict.update({crt.creative_id:cls.Parser.parse(crt, trans_type = 'inc')})

            if new_crt_list:
                crt_coll.insert(new_crt_list)
            if changed_crt_dict:
                update_list = []
                for crt_id, crt_value in changed_crt_dict.items():
                    update_list.append(({'shop_id':shop_id, '_id':crt_id}, {'$set':crt_value}))
                Creative.bulk_update_crt2db(update_list)

    @classmethod
    def get_creatives_byadgids(cls, shop_id, tapi, adg_id_list = None, transfer_flag = False):
        """通过adg_id_list获取对应的creative_list"""
        if not adg_id_list:
            adg_id_list = list(adg['_id'] for adg in adg_coll.find({'shop_id':shop_id}, {'_id':1}))
        creative_list = []
        for adg_id in adg_id_list:
            creative_list.extend(cls.__get_creatives_byadg(shop_id = shop_id, adgroup_id = adg_id, tapi = tapi))

        if transfer_flag: # 是否需要将top_obj转成标准含所有信息的字典
            temp_list = []
            for creative in creative_list:
                temp_list.append(cls.Parser.parse(creative, trans_type = 'init', extra_dict = {'shop_id':shop_id}))
            return temp_list
        else:
            return creative_list

    @classmethod
    def struct_download(cls, shop_id, tapi):
        """初始化creative"""
        try:
            top_creative_list = cls.get_creatives_byadgids(shop_id = shop_id, tapi = tapi)
            local_crt_id_list = [crt['_id'] for crt in crt_coll.find({'shop_id':shop_id}, {'_id':1})]
            upd_crt_dict, insert_crt_list, old_crt_id_list = {}, [], []
            for crt in top_creative_list:
                if crt.creative_id in local_crt_id_list:
                    upd_crt_dict.update({crt.creative_id:cls.Parser.parse(crt, trans_type = 'inc')})
                    old_crt_id_list.append(crt.creative_id)
                else:
                    insert_crt_list.append(cls.Parser.parse(crt, trans_type = 'init', extra_dict = {'shop_id': shop_id}))

            del_crt_id_list = list(set(local_crt_id_list) - set(old_crt_id_list))

            for temp_insert_list in genr_sublist(insert_crt_list, 50):
                crt_coll.insert(temp_insert_list)

            update_list = []
            for crt_id, update_info in upd_crt_dict.items():
                update_list.append(({'shop_id':shop_id, '_id':crt_id}, {'$set':update_info}))
            Creative.bulk_update_crt2db(update_list)

            if del_crt_id_list:
                cls.remove_creative({'shop_id':shop_id, '_id':{'$in':del_crt_id_list}})

            log.info('init creatives OK, shop_id = %s, get %s creatives' % (shop_id, len(top_creative_list)))
            return True
        except Exception, e:
            log.error('init creatives FAILED, shop_id = %s, e = %s' % (shop_id, e))
            return False

    @classmethod
    def increase_download(cls, shop_id, tapi, last_sync_time):
        try:
            cls.__delete_increase_creatives(shop_id = shop_id, last_sync_time = last_sync_time, tapi = tapi)
            cls.__change_increase_creatives(shop_id = shop_id, last_sync_time = last_sync_time, tapi = tapi)
            log.info('sync creatives OK, shop_id = %s' % shop_id)
            return True
        except Exception, e:
            log.error('sync creatives FAILED, shop_id=%s, e=%s' % (shop_id, e))
            return False

    @classmethod
    def download_crtrpt_byadg(cls, shop_id, campaign_id, adgroup_id, token, time_scope, tapi):
        """下载单个广告组下面的创意报表"""
        try:
            rpt_list = []
            for search_type, source in cls.Report.REPORT_CFG:
                base_dict, effect_dict = collections.defaultdict(dict), collections.defaultdict(dict)
                top_base_objs = tapi.simba_rpt_adgroupcreativebase_get(campaign_id = campaign_id, adgroup_id = adgroup_id, start_time = time_scope[0],
                                                                       end_time = time_scope[1], search_type = search_type, source = source, subway_token = token,
                                                                    retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
                if top_base_objs and hasattr(top_base_objs, 'rpt_adgroupcreative_base_list') and top_base_objs.rpt_adgroupcreative_base_list:
                    for base in top_base_objs.rpt_adgroupcreative_base_list:
                        base_dict[base.creative_id].update(cls.Report.parse_rpt(base, 'base'))

                    top_effect_objs = tapi.simba_rpt_adgroupcreativeeffect_get(campaign_id = campaign_id, adgroup_id = adgroup_id, start_time = time_scope[0],
                                                                               end_time = time_scope[1], search_type = search_type, source = source,
                                                                               subway_token = token, retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)

                    if top_effect_objs and hasattr(top_effect_objs, 'rpt_adgroupcreative_effect_list') and top_effect_objs.rpt_adgroupcreative_effect_list:
                        for effect in top_effect_objs.rpt_adgroupcreative_effect_list:
                            effect_dict[effect.creative_id].update(cls.Report.parse_rpt(effect, 'effect'))

                if base_dict:
                    for crt_id, base_rpt_dict in base_dict.items():
                        rpt_list.extend(cls.Report.merge_rpt_dict(base_rpt_dict, effect_dict.get(crt_id, {}), {'shop_id': shop_id, 'campaign_id':campaign_id, 'adgroup_id': adgroup_id, 'creative_id': crt_id}))

            if rpt_list:
                cls.Report.update_rpt_list({'shop_id': shop_id, 'adgroup_id': adgroup_id, 'date':{'$lte':date_2datetime(time_scope[1]), '$gte':date_2datetime(time_scope[0])}}, rpt_list)

            sync_time = datetime.datetime.now()
            if sync_time.hour < 6:
                sync_time = sync_time - datetime.timedelta(days = 1)
            adg_coll.update({'shop_id':shop_id, '_id':adgroup_id}, {'$set':{'crtrpt_sync_time':sync_time}})
            return True
        except TopError, e:
            log.error('download creative rpt FAILED, shop_id = %s, adgroup_id=%s, e = %s' % (shop_id, adgroup_id, e))
            return False

    @classmethod
    def download_crtrpt_byadgs(cls, shop_id, tapi, token , adg_tuple_list): # adg_tuple_list形如：[(adgroup_id, campaign_id, last_sync_time)]
        """根据adg_tuple_list来下载指定adgroup下对应的创意"""
        try:
            init_start_date = datetime.date.today() - datetime.timedelta(days = cls.Report.INIT_DAYS)
            valid_rpt_days = datetime.datetime.now().hour < 6 and 2 or 1
            end_date = datetime.date.today() - datetime.timedelta(days = valid_rpt_days)
            for adg in adg_tuple_list:
                last_date = adg[2].date()
                if last_date < init_start_date:
                    last_date = init_start_date
                elif last_date > end_date:
                    last_date = end_date
                if not time_is_someday(last_date):
                    Creative.download_crtrpt_byadg(shop_id = shop_id, campaign_id = adg[1], adgroup_id = adg[0] , token = token, time_scope = (last_date, end_date), tapi = tapi)
            log.info('download creative rpt OK, shop_id=%s' % shop_id)
            return True, ''
        except Exception, e:
            log.error('download creative rpt FAILED, shop_id=%s, e=%s' % (shop_id, e))
            return False, e

    @classmethod
    def report_download(cls, shop_id, tapi, token, time_scope):
        """通过遍历广告组下载所有创意报表"""
        init_start_time = datetime.datetime.today() - datetime.timedelta(days = cls.Report.INIT_DAYS)
        adg_tuple_list = [(adg['_id'], adg['campaign_id'], adg.get('crtrpt_sync_time', init_start_time))  for adg in adg_coll.find({'shop_id':shop_id}, {'_id':1, 'campaign_id':1, 'crtrpt_sync_time':1})]
        result, reason = cls.download_crtrpt_byadgs(shop_id = shop_id, tapi = tapi, token = token, adg_tuple_list = adg_tuple_list)
        if result:
            log.info('download creative rpt OK, shop_id = %s' % (shop_id))
            return 'OK'
        else:
            log.error('download creative rpt FAILED, shop_id = %s, e = %s' % (shop_id, reason))
            return 'FAILED'

    def get_snap_list(self, **kwargs):
        rpt_dict = self.Report.get_snap_list({'shop_id': self.shop_id, 'creative_id': self.creative_id}, **kwargs)
        return rpt_dict.get(self.creative_id, [])

    def get_summed_rpt(self, **kwargs):
        rpt_dict = self.Report.get_summed_rpt({'shop_id': self.shop_id, 'creative_id': self.creative_id}, **kwargs)
        return rpt_dict.get(self.creative_id, self.Report())

    @classmethod
    def force_download_rpt(cls, shop_id, tapi, token, time_scope):
        """给出时间区间，强制下载"""
        adg_tuple_list = [(adg['_id'], adg['campaign_id'], time_scope[0]) for adg in adg_coll.find({'shop_id':shop_id}, {'_id':1, 'campaign_id':1})]
        result, _ = cls.download_crtrpt_byadgs(shop_id = shop_id, tapi = tapi, token = token, adg_tuple_list = adg_tuple_list)
        return result

    @staticmethod
    def update_creative_inner(tapi, shop_id, adgroup_id, creative_id, title, img_url, opter, opter_name):
        record_list = []
        msg = '修改创意失败，请联系客服'
        adg = None
        try:
            tobj = tapi.simba_creative_update(adgroup_id = adgroup_id, creative_id = creative_id, title = title, img_url = img_url)
        except TopError, e:
            log.error("simba_creative_update TopError, shop_id=%s, creative_id=%s, e=%s" % (shop_id, creative_id, e))
            if '创意在待审核状态' in str(e):
                msg = '创意在待审核状态，不能修改'
            return False, msg, record_list
        except Exception, e:
            log.error("simba_creative_update Error, shop_id=%s, creative_id=%s, e=%s" % (shop_id, creative_id, e))
            if 'need to wait' in str(e):
                msg = '今日淘宝创意修改的API接口已调用完，请明天再做修改'
            return False, msg, record_list
        else:
            crt = Creative.objects.get(shop_id = shop_id, adgroup_id = adgroup_id, creative_id = creative_id)
            crt_coll.update({'shop_id':shop_id, '_id':creative_id}, {'$set':{'title':tobj.creativerecord.title, 'img_url':tobj.creativerecord.img_url, 'audit_status':tobj.creativerecord.audit_status, 'modify_time':datetime.datetime.now()}})
            if crt:
                adg = Adgroup.objects.get(shop_id = shop_id, adgroup_id = crt.adgroup_id)
                if adg:
                    if crt.title == tobj.creativerecord.title:
                        detail_list = ['修改创意:%s' % crt.title]
                    else:
                        detail_list = ['修改创意:%s --> %s' % (crt.title, title)]
                    record_list.append({'shop_id':shop_id, 'campaign_id':adg.campaign_id, 'adgroup_id':adgroup_id, 'item_name': adg.item.title, 'detail_list':detail_list, 'op_type':3, 'data_type':303, 'opter':opter, 'opter_name':opter_name})
            return True, '', record_list

    @staticmethod
    def add_creative_inner(tapi, shop_id, campaign_id, crt_arg_list = None, opter = 1, opter_name = ''): # arg_list = [[adgroup_id, title, img_url],...]
        record_list = []
        new_creative_list = []
        adgroup_id_list = []
        if crt_arg_list == None:
            crt_arg_list = []
        for crt in crt_arg_list:
            if crt[0] not in crt_arg_list:
                adgroup_id_list.append(crt[0])
        for adgroup_id in adgroup_id_list:
            detail_list = []
            for args in crt_arg_list:
                temp_adgroup_id, title, img_url = args
                if temp_adgroup_id and adgroup_id == temp_adgroup_id:
                    try:
                        tobj = tapi.simba_creative_add(adgroup_id = adgroup_id, title = title, img_url = img_url)
                        creative_list = Creative.__get_creative_bycrtids(shop_id, [tobj.creative.creative_id], tapi)

                    except TopError, e:
                        msg = str(e)
                        if "isv.toomany-entity" in msg:
                            # 如果返回创意数超过上限，则有可能是数据未同步，去同步adgroup数据
                            # case：adgroup有创意，但是数据未同步，添加计划内宝贝时，以为没有创意，自动生成两个创意
                            dl_args = {'shop_id':shop_id, 'tapi': tapi, 'adg_tuple_list':[(adgroup_id, campaign_id, datetime.datetime.now() - datetime.timedelta(days = 7))]}
                            Creative.download_crtrpt_byadgs(**dl_args)
                        log.error("simba_creative_add TopError, shop_id=%s, adgroup_id=%s, e=%s" % (shop_id, adgroup_id, e))
                    except Exception, e:
                        log.error("simba_creative_add Error, shop_id=%s, adgroup_id=%s, e=%s" % (shop_id, adgroup_id, e))
                    else:
                        crt = Creative.Parser.parse(creative_list[0], trans_type = "init", extra_dict = {'shop_id': shop_id})
                        new_creative_list.append(crt)
                        detail_list.append('添加创意:%s' % crt['title'])
            adg = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
            if adg and detail_list:
                record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':adgroup_id, 'item_name':adg.item.title, 'detail_list':detail_list, 'op_type':3, 'data_type':301, 'opter':opter, 'opter_name':opter_name})
        if new_creative_list:
            crt_coll.insert(new_creative_list, continue_on_error = True, safe = False)
        return len(new_creative_list), record_list, crt

    @classmethod
    def delete_creative_inner(cls, tapi, shop_id, creative_id, opter, opter_name):
        record_list = []
        adg = None
        try:
            tobj = tapi.simba_creative_delete(creative_id = creative_id)
            crt = Creative.objects.get(shop_id = shop_id, creative_id = creative_id)
            if crt:
                adg = Adgroup.objects.get(shop_id = shop_id, adgroup_id = crt.adgroup_id)
                if adg:
                    detail_list = ['删除创意:%s' % crt.title]
                    record_list.append({'shop_id':shop_id, 'campaign_id':adg.campaign_id, 'adgroup_id':adg.adgroup_id, 'item_name': adg.item.title, 'detail_list': detail_list, 'op_type':3, 'data_type':302, 'opter':opter, 'opter_name':opter_name})
        except TopError, e:
            log.error("simba_creative_delete TopError, shop_id=%s, creative_id=%s, e=%s" % (shop_id, creative_id, e))
            return None, []
        except Exception, e:
            log.error("simba_creative_delete Error, shop_id=%s, creative_id=%s, e=%s" % (shop_id, creative_id, e))
            return None, []
        else:
            cls.remove_creative({'shop_id':shop_id, '_id':tobj.creative.creative_id})
        return creative_id, record_list

    @staticmethod
    def get_creative_count(shop_id, adgroup_id_list = None):
        '''计算宝贝列表中每个宝贝的已有关键词数，静态函数'''
        result_dict = {}
        query_dict = {'shop_id':shop_id}
        if adgroup_id_list: # 不指定adgroup_id_list则默认是查询全部
            query_dict.update({'adgroup_id':{'$in':adgroup_id_list}})
        pipeline = [{'$match':query_dict}, {'$project':{'adgroup_id':1}}, {'$group':{'_id':'$adgroup_id', 'num':{'$sum':1}}}]
        result = crt_coll.aggregate(pipeline)
        if int(result['ok']) == 1 and result['result']:
            for temp_value in result['result']:
                result_dict.update({temp_value['_id']:temp_value['num']})
        return result_dict


crt_coll = Creative._get_collection()

class CustomCreative(Document):

    CSUTOM_CREATIVE_STATUS = ((0, "等待投放"), (1, "投放完成"))

    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "计划ID", required = True)
    num_iid = IntField(verbose_name = "商品数字ID", required = True)
    adgroup_id = IntField(verbose_name = "推广宝贝ID", required = True)
    creative_id = IntField(verbose_name = "创意id")
    title = StringField(verbose_name = "创意标题", max_length = 50, required = True)
    img_url = StringField(verbose_name = "创意图片地址", max_length = 255, required = True)
    img_id = IntField(verbose_name = "图片ID")
    status = IntField(verbose_name = "状态", choices = CSUTOM_CREATIVE_STATUS)
    start_time = DateTimeField(verbose_name = "创意开始投放时间")
    create_time = DateTimeField(verbose_name = "创建时间")
    # 报表数据
    # rpt_list = ListField(verbose_name = "创意报表列表", field = EmbeddedDocumentField(Report))
    Report = CreativeRpt

    meta = {'collection':'custom_creative', 'indexes':['campaign_id', 'adgroup_id'], "shard_key":('shop_id',)}

    def get_snap_list(self, **kwargs):
        rpt_dict = self.Report.get_snap_list({'shop_id': self.shop_id, 'creative_id': self.creative_id}, **kwargs)
        return rpt_dict.get(self.creative_id, [])

    @classmethod
    def is_limited_waiting(cls, shop_id, adgroup_id):
        if ccrt_coll.find({"shop_id":shop_id, "adgroup_id":adgroup_id, "status":0}).count() > 3:
            return True
        return False

    @classmethod
    def sync_complate_creative(cls, shop_id, adgroup_id, creative_id):
        '''创意投放完同步创意数据到当前表'''
        from apps.subway.models_item import Item
        creative = Creative.objects.get(shop_id = shop_id, creative_id = creative_id)

        # 通不过后就不再同步
        if ccrt_coll.find_one({"shop_id":shop_id, "creative_id":creative_id, 'status':1}):
            return None

        adgroup = adg_coll.find_one({"shop_id":shop_id, "_id":adgroup_id})
        if creative and adgroup:
            creative.num_iid = adgroup['item_id']
            return cls.create_complate_creative(creative)
        else:
            return None

    @classmethod
    def create_waiting_creative(cls, **args):
        '''创建一个等待投放的创意,img_ulr可以是一个图片地址，也可以是图片文件对象'''
        from apilib.binder import FileItem
        file_item = args['file_item']
        if isinstance(file_item, (str, unicode)):
            args['img_url'] = file_item
        else:
            # 将图片上传到图片空间
            shop_id = args['shop_id']
            tapi = get_tapi(shop_id = shop_id)
            _, picture_path = cls.upload_picture(tapi, shop_id, file_item)
            args['img_url'] = picture_path
        return cls.__create_waiting_creative(**args)

    @classmethod
    def __create_waiting_creative(cls, **args):
        try:
            field_list = ['shop_id', 'campaign_id', 'num_iid', 'adgroup_id', 'title', 'img_url']
            args_dict = {item:args[item] for item in field_list if item in args}

            args_dict['status'] = 0
            args_dict['create_time'] = datetime.datetime.now()
            custom_creative = cls.objects.create(**args_dict)
            adg_coll.update({'shop_id':args['shop_id'], '_id':args['adgroup_id']}, {'$set': {'creative_test_switch':True}})
            adgroup = Adgroup.objects.get(shop_id = args['shop_id'], adgroup_id = args['adgroup_id'])
            detail_list = ['添加创意:%s' % custom_creative.title]
            record_list = [{'shop_id':args['shop_id'], 'campaign_id':args['campaign_id'], 'adgroup_id':args['adgroup_id'], 'item_name':adgroup.item.title, 'detail_list':detail_list, 'op_type':3, 'data_type':301, 'opter':args['opter'], 'opter_name':args['opter_name']}]
            if record_list:
                rcd_list = [UploadRecord(**record) for record in record_list]
                UploadRecord.objects.insert(rcd_list)
            return custom_creative
        except Exception, e:
            log.exception(e)
            return False

    @classmethod
    def update_waiting_creative(cls, id, shop_id, title, file_item, opter, opter_name):
        """更新排队中的创意"""
        from apilib.binder import FileItem
        from bson.objectid import ObjectId

        try:
            # 将图片上传到图片空间
            tapi = get_tapi(shop_id = shop_id)
            _, picture_path = cls.upload_picture(tapi, shop_id, file_item)
            ccrt = ccrt_coll.find_one({ "_id":ObjectId(id)})
            ccrt_coll.update({'_id':ObjectId(id)}, {'$set': {'title':title, 'img_url':picture_path}})
            if ccrt['title'] != title:
                detail_list = ['修改创意:%s --> %s' % (ccrt['title'], title)]
            else:
                detail_list = ['修改创意:%s' % (title)]

            adgroup = Adgroup.objects.get(shop_id = ccrt['shop_id'], adgroup_id = ccrt['adgroup_id'])
            record_list = [{'shop_id':ccrt['shop_id'], 'campaign_id':ccrt['campaign_id'], 'adgroup_id':ccrt['adgroup_id'], 'item_name':adgroup.item.title, 'detail_list':detail_list, 'op_type':3, 'data_type':303, 'opter': opter, 'opter_name': opter_name}]
            if record_list:
                rcd_list = [UploadRecord(**record) for record in record_list]
                UploadRecord.objects.insert(rcd_list)
            return True
        except Exception, e:
            log.exception(e)
            return False

    @classmethod
    def create_complate_creative(cls, creative):
        '''创建一个投放完成的创意'''
        try:
            field_list = ['shop_id', 'campaign_id', 'num_iid', 'adgroup_id', 'creative_id', 'title', 'img_url', 'rpt_list']
            args_dict = {item:getattr(creative, item) for item in field_list if hasattr(creative, item)}

            args_dict['status'] = 1
            args_dict['start_time'] = creative.create_time
            args_dict['create_time'] = datetime.datetime.now()
            custom_creative = cls.objects.create(**args_dict)
            return custom_creative
        except Exception, e:
            log.exception(e)
            return False

#     @classmethod
#     def get_waiting_adgroupids(cls, shop_id):
#         '''获取有等待投放的店铺列表下所有的adgroup_id'''
#         adgroup_ids = []
#         custom_creatives = ccrt_coll.aggregate([
#                 {
#                     "$match":{
#                               'shop_id':shop_id,
#                                'status':0
#                     }
#                 },
#                 {
#                     "$group": {
#                         "_id": {
#                                 "adgroup_id":"$adgroup_id",
#                                 "shop_id":"$shop_id",
#                                 "campaign_id":"$campaign_id",
#                                 }
#                     }
#                 }])
#         for c in custom_creatives['result']:
#             adgroup_ids.append(c['_id'])
#         return adgroup_ids

    @classmethod
    def is_active(cls, shop_id, adgroup_id):
        '''判断推广组是否满足换创意的条件（1.有等待的创意，2.有创意的投放时间超过24小时）'''
        if(ccrt_coll.find({'shop_id':shop_id, 'adgroup_id':adgroup_id})):
            if(crt_coll.find({'shop_id':shop_id, 'adgroup_id':adgroup_id, 'abtest_end_time':{'$gte':datetime.datetime.now()}})):
                return True
        return False

    @classmethod
    def item_img_upload(cls, tapi, shop_id, num_iid, image, position = None, is_major = False):
        '''上传图片并返回图片地址,图片ID'''
        try:
            is_major = is_major and "true" or "false"
            if position:
                tobj = tapi.taobao_item_img_upload(num_iid = num_iid, image = image, position = position, is_major = is_major)
            else:
                tobj = tapi.taobao_item_img_upload(num_iid = num_iid, image = image, is_major = is_major)
        except TopError, e:
            log.error("item_img_upload TopError, num_iid=%s,  e=%s" % (num_iid, e))
            if "item-is-delete" in str(e):
                return None, '', '该商品已被删除'
            if "IC_ITEM_PIC_NUM_OVERFLOW" in str(e):
                return None, '', '宝贝图片数量超过限制'
            if "IC_ITEM_PIC_IS_TOO_LARGES" in str(e):
                return None, '', '商品图片太大'
            return None, '', '远程服务器错误'
        except Exception, e:
            log.error("product_img_upload Error, num_iid=%s, e=%s" % (num_iid, e))
            return None, '', '服务器内部错误'
        return tobj.item_img.id, tobj.item_img.url, None

    @classmethod
    def item_img_delete(cls, tapi, shop_id, num_iid, img_id):
        '''删除图片'''
        try:
            tobj = tapi.taobao_item_img_delete(num_iid = num_iid, id = img_id)
        except TopError, e:
            log.error("item_img_delete TopError, e=%s" % (e))
            return None
        except Exception, e:
            log.error("item_img_delete Error, e=%s" % (e))
            return None
        return tobj

    @classmethod
    def get_item_img_list(cls, tapi, shop_id, item_id_list):
        '''获取商品的图片列表'''
        from apps.subway.models_item import Item
        temp_item_list = Item.get_item_by_ids(shop_id, item_id_list, tapi, fields = 'num_iid,item_img.url,item_img.id,item_img.position')
        item_img_list = {}
        for item in temp_item_list:
            item_img_list[item.num_iid] = item.item_imgs.item_img
        return item_img_list

    @classmethod
    def get_vaild_img_info(cls, tapi, shop_id, item_id_list):
        '''获取主图的一个数据'''
        item_img_list = cls.get_item_img_list(tapi, shop_id, item_id_list)
        vaild_img_dict = {}
        for num_iid, item_img in item_img_list.items():
            item_img.reverse()
            for img_info in item_img:
#                 if not img_info.id and not img_info.position: # 主图id默认为0，且位置在第一位
                if img_info.position == 1:
                    return img_info.url, img_info.id
        return None, None

#     @classmethod
#     def super_img_upload(cls, tapi, shop_id, num_iid, image, is_major = False):
#         '''突破主图限制的上传'''
#         log.info("图片超过限制")
#         vaild_img_info = cls.get_vaild_img_info(tapi, shop_id, [num_iid, ])
#         if cls.item_img_delete(tapi, shop_id, num_iid, vaild_img_info[num_iid].id): # 删除其中一个主图
#             return cls.item_img_upload(tapi, shop_id, num_iid, image, is_major, recovery = vaild_img_info[num_iid].url)
#         else:
#             log.info("图片删除失败")

    @classmethod
    def get_or_create_pic_catid(cls, tapi, shop_id, picture_category_name = "开车精灵_创意优化"):
        '''获取图片分类'''
        try:
            tobj = tapi.taobao_picture_category_get(picture_category_name = picture_category_name)
        except TopError, e:
            log.error("get_picture_category TopError , shop_id=%s , e=%s" % (shop_id, e))
            return None
        except Exception, e:
            log.error("get_picture_category Error , shop_id=%s , e=%s" % (shop_id, e))
            return None
        else:
            if not tobj.picture_categories:
                tobj = cls.create_picture_category(tapi, shop_id)
                return tobj.picture_category.picture_category_id
        return tobj.picture_categories.picture_category[0].picture_category_id

    @classmethod
    def create_picture_category(cls, tapi, shop_id, picture_category_name = "开车精灵_创意优化"):
        '''创建图片分类'''
        try:
            tobj = tapi.taobao_picture_category_add(picture_category_name = picture_category_name)
        except TopError, e:
            log.error("create_picture_category TopError , shop_id=%s , e=%s" % (shop_id, e))
            return None
        except Exception, e:
            log.error("create_picture_category Error , shop_id=%s , e=%s" % (shop_id, e))
            return None
        return tobj

    @classmethod
    def fix_pic(cls, pic_url):
        """将图片链接修正为可以用于主图的链接"""
        import re
        p = re.compile('http.*(imgextra/|uploaded/)')

        pic_url = p.sub('', pic_url)
        return pic_url

    @classmethod
    def update_item_main_pic(cls, tapi, shop_id, pic_path, num_iid):
        """更新商品的 主推广图的第五个图片"""
        import urllib2
        from apilib.binder import FileItem
        try:
            if isinstance(pic_path, (str, unicode)):
                file = urllib2.urlopen(pic_path)
                file_item = FileItem('item_pic.jpg', file.read())
            else:
                file_item = pic_path

            img_id, img_url, err_msg = cls.item_img_upload(tapi, shop_id, num_iid, image = file_item, position = 1)
        except Exception, e:
            log.error("update_item_main_pic Error , shop_id=%s , e=%s" % (shop_id, e))
            return None
        return True

    @classmethod
    def upload_picture(cls, tapi, shop_id, img):
        """上传图片，和item_img_upload的区别是此函数上传的图片和商品没有关系，主要是创建等待投放的创意"""
        try:
            picture_category_id = cls.get_or_create_pic_catid(tapi, shop_id)
            tobj = tapi.taobao_picture_upload(picture_category_id = picture_category_id, img = img, image_input_title = img.filename)
        except TopError, e:
            log.error("upload_picture TopError , shop_id=%s , e=%s" % (shop_id, e))
            return None, None
        except Exception, e:
            log.error("upload_picture Error , shop_id=%s , e=%s" % (shop_id, e))
            return None, None
        return tobj.picture.picture_id, tobj.picture.picture_path

    @classmethod
    def add_creative_inner(cls, tapi, shop_id, campaign_id, adgroup_id, num_iid, title, file_item, opter, opter_name):
        """增加等待的创意,#fixed 3953 zhongjinfeng 20170321 当前直接调用add_creative_inner接口不能自定义创意，但是更新创意可以自定义，所以这里先上传一个生成一个坑位，然后再更新"""
        len, record_list = 0, []
        try:
            new_pic_url, img_id = cls.get_vaild_img_info(tapi, shop_id, [num_iid, ])
            len, record_list, crt = Creative.add_creative_inner(tapi, shop_id, campaign_id, crt_arg_list=[[adgroup_id, title, cls.fix_pic(new_pic_url)], ], opter=opter, opter_name=opter_name)
        except Exception, e:
            log.error("add_creative Error , shop_id=%s , e=%s" % (shop_id, e))
        cls.update_creative(tapi = tapi, shop_id = int(shop_id), campaign_id = campaign_id, adgroup_id = adgroup_id, num_iid = num_iid, creative_id = crt['_id'], title = title, file_item = file_item, opter = opter, opter_name = opter_name)
        return len, record_list

    @classmethod
    def add_creative(cls, tapi, shop_id, campaign_id, adgroup_id, num_iid, title, image, opter, opter_name):
        """增加一个创意，可以上传指定图片"""
        len, record_list = 0, []
        if isinstance(image, (str, unicode)): # 字符串表示为url
            len, record_list, crt = Creative.add_creative_inner(tapi, shop_id, campaign_id, crt_arg_list = [[adgroup_id, title, image]], opter = opter, opter_name = opter_name)
        else: # 文件类型
            len, record_list = cls.add_creative_inner(tapi, shop_id, campaign_id, adgroup_id, num_iid, title, image, opter, opter_name)
        return len, record_list

    @classmethod
    def update_creative(cls, tapi, shop_id, campaign_id, adgroup_id, num_iid, creative_id, title, file_item, opter, opter_name):
        """更新创意图片"""
        result, msg, record_list = False, '', []
        try:
            old_pic_url, old_pic_id = cls.get_vaild_img_info(tapi, shop_id, [num_iid, ])

            if isinstance(file_item, (str, unicode)):
                # 删除原有的商品图
                cls.item_img_delete(tapi, shop_id, num_iid, old_pic_id)
                # 将图片替换主图
                cls.update_item_main_pic(tapi, shop_id, file_item, num_iid)
                # 重新获取主图数据
                new_pic_url, img_id = cls.get_vaild_img_info(tapi, shop_id, [num_iid, ])
#                 pic_count = 6 # 设置为6主要是为了在finally中恢复主图
            else:
                if not old_pic_url: # 此处本可以统一使用图片替换的方法上传，但是为了节省获取商品信息的收费api，所有做了一次判定
                    img_id, new_pic_url, _ = cls.item_img_upload(tapi, image = file_item, num_iid = num_iid, shop_id = shop_id, position = 1)
                else:
                    # 将图片上传到图片空间
                    _, picture_path = cls.upload_picture(tapi, shop_id, file_item)
                    # 删除原有的商品图
                    cls.item_img_delete(tapi, shop_id, num_iid, old_pic_id)
                    # 上传商品图片
                    cls.update_item_main_pic(tapi, shop_id, picture_path, num_iid)
                    # 重新获取主图数据
                    new_pic_url, img_id = cls.get_vaild_img_info(tapi, shop_id, [num_iid, ])

            result, msg , record_list = Creative.update_creative_inner(tapi, shop_id, adgroup_id, creative_id, title, cls.fix_pic(new_pic_url), opter, opter_name)
        except Exception, e:
            log.error("update_creative Error , shop_id=%s , e=%s" % (shop_id, e))
        finally:
            # 删除上传的图片
            cls.item_img_delete(tapi, shop_id, num_iid, img_id)
            if old_pic_url:
                # 恢复主图
                if not cls.update_item_main_pic(tapi, shop_id, old_pic_url, num_iid):
                    log.error("recovery main_pic Error , shop_id=%s , pic_url=%s" % (shop_id, old_pic_url))
        return result, msg, record_list

ccrt_coll = CustomCreative._get_collection()
