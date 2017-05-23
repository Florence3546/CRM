# coding=UTF-8

import re
import math
import datetime
import collections
from bson.son import SON
from django.conf import settings
from pymongo.errors import BulkWriteError
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import IntField, DateTimeField, StringField, ListField, DictField, BooleanField

from apilib import TopError, ApiLimitError
from apps.common.utils.utils_log import log
from apps.common.utils.utils_misc import trans_batch_dict_2document
from apps.common.utils.utils_datetime import date_2datetime, string_2datetime, time_is_someday, string_2date
from apps.common.utils.utils_collection import genr_sublist
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_json import json
from apps.common.cachekey import CacheKey
from apps.common.biz_utils.utils_tapitools import get_kw_g_data
from apps.subway.models_adgroup import Adgroup, adg_coll
from apps.subway.models_item import Item
from apps.subway.models_parser import KeywordParser
from apps.subway.models_report import KeywordRpt
from apps.subway.download_boost.contractor import EnhancedDownloadContracter
from apps.subway.utils import (set_rpt_days, get_rpt_days, get_rpt_date, get_create_days,
                               get_rpt_date_list, get_rpt_yt, get_rpt_sum, get_snap_list)


class Qscore(Document):

    ad_type = StringField(verbose_name = "广告类型", help_text = "单品： 'tbuad' 店铺： 'addp'")
    catscore = IntField(verbose_name = "类目质量得分", default = 0)
    pscore = IntField(verbose_name = "属性得分", default = 0)

    creativescore = IntField(verbose_name = "PC创意质量得分", default = 0)
    custscore = IntField(verbose_name = "PC店铺质量(账户表现)", default = 0)
    cvrscore = IntField(verbose_name = "PC点击转化率(买家体验)", default = 0)
    kwscore = IntField(verbose_name = "PC相关性", default = 0)
    qscore = IntField(verbose_name = "PC质量得分", default = 0)
    # plflag = IntField(verbose_name = "词是否能够推左", default = 0) # 该字段由下面的字段代替
    pc_left_flag = IntField(verbose_name = "PC端关键词是否能在首页推左", default = 0)

    wireless_creativescore = IntField(verbose_name = "无线创意得分", default = 0)
    wireless_custscore = IntField(verbose_name = "无线店铺质量", default = 0)
    wireless_cvrscore = IntField(verbose_name = "无线买家体验", default = 0)
    wireless_relescore = IntField(verbose_name = "无线相关性分", default = 0)
    wireless_qscore = IntField(verbose_name = "无线质量得分", default = 0)
    wireless_matchflag = IntField(verbose_name = "无线词是否有首屏机会", default = 1) # 1:无机会  2：搜索有展示机会  3：有首屏展示机会

    meta = {'abstract': True}

    @classmethod
    def parse_qscore(cls, top_obj):
        return {field_name: field.to_python(getattr(top_obj, field_name, field.default) or field.default) for field_name, field in cls._fields.items()}



class KeywordPrice(object):

    def __init__(self, price, old_price, is_default = False, price_type = 1):
        self.price = price
        self.old_price = old_price
        self.is_default = is_default
        self.price_type = price_type

    def check_valid(self):
        if self.is_default:
            self.price = 0
            return True
        else:
            if self.price >= 5 and self.price <= 9999:
                return True
            else:
                return False

    def to_dict(self):
        if self.check_valid():
            is_default = self.is_default and 1 or 0
            if self.price_type == 1:
                result = {'maxPrice': self.price, 'isDefaultPrice': is_default}
            else:
                result = {'maxMobilePrice': self.price, 'mobileIsDefaultPrice': is_default}
            return result
        else:
            raise Exception("invalid-price")

    def to_history(self):
        desc = ""
        if self.old_price != self.price:
            desc += " %s由%.2f元修改为%.2f元" % (self.price_type == 1 and "PC端出价" or "移动端出价", self.old_price / 100.0, self.price / 100.0)
        return desc


class PriceFactory(object):

    match_scope_dict = {1:'精准匹配', 4:'广泛匹配'}

    def __init__(self, keyword_id, price_dict):
        pc_kp, mobile_kp = None, None
        if 'max_price' in price_dict:
            pc_kp = KeywordPrice(price = price_dict['max_price'], old_price = price_dict['old_price'], is_default = price_dict.get('is_default_price', False), price_type = 1)
        if 'max_mobile_price' in price_dict:
            mobile_kp = KeywordPrice(price = price_dict['max_mobile_price'], old_price = price_dict['mobile_old_price'], is_default = price_dict.get('mobile_is_default_price', False), price_type = 0)

        if 'match_scope' in price_dict:
            self.match_scope = price_dict['match_scope']
        else:
            self.match_scope = None

        self.keyword_id = keyword_id
        self.pc_kp = pc_kp
        self.mobile_kp = mobile_kp

    def to_dict(self):
        result_dict = {'keywordId': self.keyword_id}
        if self.pc_kp:
            result_dict.update(self.pc_kp.to_dict())
        if self.mobile_kp:
            result_dict.update(self.mobile_kp.to_dict())
        if self.match_scope in [1, 4]:
            result_dict.update({'matchScope': self.match_scope})
        return result_dict

    def to_history(self):
        desc = ""
        if self.pc_kp:
            desc += self.pc_kp.to_history()
        if self.mobile_kp:
            desc += self.mobile_kp.to_history()
        if self.match_scope:
            desc += " 匹配方式改为%s" % (self.match_scope_dict.get(self.match_scope, "广泛匹配"))
        return desc


class Keyword(Document):
    MNT_OPT_TYPE_CHOICES = ((0, "自动优化"), (1, "只改价"), (2, "不托管"))
    KW_TYPE_CHOICE = ((0, "实时"), (1, "重点"), (2, "潜力"), (3, "观察"), (4, "垃圾"))
    AUDIT_STATUS_CHOICE = (("audit_wait", "待审核"), ("audit_pass", "审核通过"), ("audit_reject", "审核拒绝"), ("audit_offline", "审核直接下线"))
    KW_RT_RANK_MAP = {
        'pc_rank': {
            '-2': '创意未投放',
            '-1': '计划未投放',
            '0': '首页左侧位置',
            '1': '首页右侧第1',
            '2': '首页右侧第2',
            '3': '首页右侧第3',
            '4': '首页(非前三)',
            '5': '第2页',
            '6': '第3页',
            '7': '第4页',
            '8': '第5页',
            '9': '5页以后'
        },
        'mobile_rank': {
            '-2': '创意未投放',
            '-1': '计划未投放',
            '0': '移动首条',
            '1': '移动前三',
            '2': '移动前三',
            '3': '移动4~6条',
            '4': '移动4~6条',
            '5': '移动4~6条',
            '6': '移动7~10条',
            '7': '移动7~10条',
            '8': '移动7~10条',
            '9': '移动7~10条',
            '10': '移动11~15条',
            '11': '移动16~20条',
            '12': '20条以后'
        }
    }
    RANK_START_DESC_MAP = {
        'pc': {
            '0': '首页左侧位置',
            '1': '首页右侧第1',
            '2': '首页右侧第2',
            '3': '首页右侧第3',
            '4': '首页(非前三)',
            '5': '第2页',
            '6': '第3页',
            '7': '第4页',
            '8': '第5页',
            '9': '5页以后'
        },
        'yd': {
            '0': '移动首条',
            '1': '移动前三',
            '3': '移动4~6条',
            '6': '移动7~10条',
            '10': '移动11~15条',
            '11': '移动16~20条',
            '12': '20条以后'
        }
    }
    RANK_START_DESC_REV_MAP = {
        'pc': {v: k for k, v in RANK_START_DESC_MAP['pc'].items()},
        'yd': {v: k for k, v in RANK_START_DESC_MAP['yd'].items()}
    }
    RANK_END_DESC_MAP = {
        'pc': {
            '0': '首页左侧位置',
            '1': '首页右侧第1',
            '2': '首页右侧第2',
            '3': '首页右侧第3',
            '4': '首页(非前三)',
            '5': '第2页',
            '6': '第3页',
            '7': '第4页',
            '8': '第5页',
            '9': '5页以后'
        },
        'yd': {
            '0': '移动首条',
            '1': '移动前三',
            '5': '移动4~6条',
            '9': '移动7~10条',
            '10': '移动11~15条',
            '11': '移动16~20条',
            '12': '20条以后'
        }
    }
    RANK_END_DESC_REV_MAP = {
        'pc': {v: k for k, v in RANK_END_DESC_MAP['pc'].items()},
        'yd': {v: k for k, v in RANK_END_DESC_MAP['yd'].items()}
    }

    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "计划ID", required = True)
    adgroup_id = IntField(verbose_name = "推广宝贝ID", required = True)
    keyword_id = IntField(verbose_name = "关键词ID", primary_key = True)
    word = StringField(verbose_name = "关键词", max_length = 100, required = True)
    max_price = IntField(verbose_name = "关键词出价") # 为0时，使用默认出价
    is_default_price = BooleanField(verbose_name = "是否使用宝贝默认出价", choices = ((True, '是'), (False, '否')))
    max_mobile_price = IntField(verbose_name = "关键词移动端出价") # 为0时，使用PC端出价*溢价
    mobile_is_default_price = IntField(verbose_name = "无线是否采用PC*无线溢价") # 为0时，使用移动端自定义出价；为1时，使用PC端出价*溢价

    qscore_dict = DictField(verbose_name = "质量得分字典", default = {})
    qscore = IntField(verbose_name = "质量得分", default = 0)
    rele_score = IntField(verbose_name = "相关性", default = 0)
    cvr_score = IntField(verbose_name = "买家体验分", default = 0)
    cust_score = IntField(verbose_name = "基础分", default = 0)
    creative_score = IntField(verbose_name = "创意得分", default = 0)
    match_scope = IntField(verbose_name = "匹配模式", default = 0) # 1.精准匹配  4.广泛匹配 # 2016.1.26 中心词匹配修改为广泛匹配
    audit_status = StringField(verbose_name = "审核状态", max_length = 20, choices = AUDIT_STATUS_CHOICE) # audit_reject 是因为关键词违规，audit_offline 是因为宝贝审核不通过或者暂停推广
    audit_desc = StringField(verbose_name = "审核拒绝原因描述")

    is_garbage = BooleanField(verbose_name = "是否是无展现词", choices = ((True, '是'), (False, '否')))
    is_freeze = BooleanField(verbose_name = "是否冻结", choices = ((True, '是'), (False, '否')))
    create_time = DateTimeField(verbose_name = "创建时间")
    modify_time = DateTimeField(verbose_name = "最后修改时间")
    manual_adjust_time = DateTimeField(verbose_name = "手动调整优化时间") # mnt相关
    rt_date = DateTimeField(verbose_name = "优化时间")
    mnt_opt_type = IntField(verbose_name = "托管优化类型", choices = MNT_OPT_TYPE_CHOICES, default = 0)

    snapshot_list = ListField() # 关键词的出价、质量得分记录，形如[{'max_price': 100, 'change_time': '2015-09-01 15:23:20'}]
    # 报表数据与行业数据
    # rpt_list = ListField(verbose_name = "关键词报表列表", field = EmbeddedDocumentField(Report))
    g_pv = IntField(verbose_name = "全网展现指数")
    g_click = IntField(verbose_name = "全网点击指数")
    g_cpc = IntField(verbose_name = "全网市场均价")
    g_competition = IntField(verbose_name = "全网竞争度")
    g_sync_time = DateTimeField(verbose_name = "全网数据同步时间")
    # 业务自定义字段
    is_locked = BooleanField(verbose_name = "是否锁排名", choices = ((True, '是'), (False, '否')), default = False)
    is_focus = BooleanField(verbose_name = "是否关注的词", choices = ((True, '是'), (False, '否')), default = False)
    # 算法分析字段
    kw_type = IntField(verbose_name = "关键词类型", default = 0, choices = KW_TYPE_CHOICE)
    new_price = IntField(verbose_name = "建议出价", default = 0) # 单位为分，不能小于5
    optm_type = IntField(verbose_name = "优化方式", default = 0) # 0:保留, 1:删除, 2:降价, 3:加价
    optm_score = IntField(verbose_name = "优化得分", default = 0) # 算法计算的关键词得分
    optm_rcode = StringField(verbose_name = "优化理由", max_length = 32) # 类似于+s1,+s2,+P1,R2的串
    # 报表属性
    # rpt_days = property(fget = get_rpt_days, fset = set_rpt_days)
    # rpt_date = property(fget = get_rpt_date)
    # rpt_date_list = property(fget = get_rpt_date_list)
    # rpt_yt = property(fget = get_rpt_yt)
    # rpt_sum = property(fget = get_rpt_sum)
    # snap_list = property(fget = get_snap_list)
    create_days = property(fget = get_create_days)

    Parser = KeywordParser
    Report = KeywordRpt

    meta = {'db_alias': 'keyword-db', 'collection':'subway_keyword', 'indexes':['shop_id', 'campaign_id', 'word'], "shard_key":('adgroup_id',)}

    def __unicode__(self):
        return '%s,%s,%s' % (self.keyword_id, self.word, self.max_price)

    @property
    def g_ctr(self):
        '''返回全网点击率'''
        if self.g_click and self.g_pv:
            return self.g_click * 100.0 / self.g_pv
        return 0.00

    @property
    def adgroup(self):
        """关键词连续推广的天数"""
        if not hasattr(self, '_adgroup'):
            self._adgroup = Adgroup.objects.get(shop_id = self.shop_id, campaign_id = self.campaign_id, adgroup_id = self.adgroup_id)
        return self._adgroup

    def get_mobile_price(self, adgroup, campaign):
        if self.max_mobile_price:
            mobile_price = self.max_mobile_price
        else:
            mobile_discount = adgroup.mobile_discount or campaign.platform['mobile_discount']
            mobile_price = int(self.max_price * mobile_discount / 100.0)
        self.mobile_price = mobile_price
        return self.mobile_price

    @classmethod
    def bulk_update_kw2db(cls, update_list): # update_list形如[({'_id':1024321654}, {'$set':{'max_price':24}}), ({'_id':1024321651}, {'$set':{'max_price':47}}),...]
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
    def remove_keyword(cls, query_dict):
        cls._get_collection().remove(query_dict)
        id_query = query_dict.pop('_id', None) # 关键词及其报表的查询条件，在于主键上有区别，这里区别对待一下
        if id_query is not None:
            query_dict.update({'keyword_id': id_query})
            cls.Report._get_collection().remove(query_dict)

    def set_g_data(self, g_data):
        '''设置全网数据'''
        if not g_data:
            self.g_pv = 0
            self.g_click = 0
            self.g_cpc = 0
            self.g_competition = 0
            self.g_coverage = 0
            self.g_roi = 0
            self.g_paycount = 0
        else:
            self.g_pv = getattr(g_data, 'pv', 0)
            self.g_click = getattr(g_data, 'click', 0)
            self.g_cpc = getattr(g_data, 'avg_price', 0)
            self.g_competition = getattr(g_data, 'competition', 0)
            self.g_coverage = getattr(g_data, 'g_coverage', 0)
            self.g_roi = getattr(g_data, 'g_roi', 0)
            self.g_paycount = getattr(g_data, 'g_paycount', 0)
        self.g_sync_time = datetime.datetime.now()

    @classmethod
    def get_keyword_count(cls, shop_id, adgroup_id_list = None):
        '''计算宝贝列表中每个宝贝的已有关键词数，静态函数'''
        result_dict = {}
        query_dict = {'shop_id':shop_id}
        if adgroup_id_list: # 不指定adgroup_id_list则默认是查询全部
            query_dict.update({'adgroup_id':{'$in':adgroup_id_list}})
        pipeline = [{'$match':query_dict}, {'$project':{'adgroup_id':1}}, {'$group':{'_id':'$adgroup_id', 'num':{'$sum':1}}}]
        result = cls._get_collection().aggregate(pipeline)
        if int(result['ok']) == 1 and result['result']:
            for temp_value in result['result']:
                result_dict.update({temp_value['_id']:temp_value['num']})
        return result_dict

    @classmethod
    def __update_keywords_inner(cls, shop_id, keywordid_prices, tapi):
        msg, upded_kw_dict = 'ok', {}
        try:
            top_objs = tapi.simba_keywords_pricevon_set(keywordid_prices = keywordid_prices)
            if top_objs and hasattr(top_objs.keywords, "keyword") and len(top_objs.keywords.keyword) > 0:
                for tmp_obj in top_objs.keywords.keyword:
                    upded_kw_dict.update({tmp_obj.keyword_id: cls.Parser.parse(tmp_obj, 'inc')})
                    # upded_kw_dict.update({tmp_obj.keyword_id:{'adgroup_id':int(tmp_obj.adgroup_id), 'max_price':tmp_obj.max_price, 'match_scope':int(getattr(tmp_obj, 'match_scope', 4)),
                    #                                           'is_default_price':bool(tmp_obj.is_default_price), 'modify_time':string_2datetime(tmp_obj.modified_time)
                    #                                           }})

        except TopError, e:
            error_msg = "simba_keywords_pricevon_set TopError(%%s), shop_id=%s" % (shop_id)
            if 'sub_msg":"包含了不属于该客户的关键词Id' in str(e):
                msg = 'has_dirty_kws'
                log.error("%s" % (error_msg % "包含无效的关键词Id"))
            elif 'sub_msg":"关键词不能为空' in str(e):
                msg = 'no_valid_kws'
                log.error(error_msg % "关键词ID全部无效")
            elif 'sub_msg":"This ban will last for' in str(e):
                msg = 'api_limit_control'
                log.error(error_msg % "淘宝API流控")
            else:
                msg = 'error'
                log.error("%s, error=%s" % (error_msg % "其它错误", e))
        except ApiLimitError, e:
            error_msg = "simba_keywords_pricevon_set ApiLimitError(%%s), shop_id=%s" % (shop_id)
            msg = "淘宝流量限制，非常抱歉，今天的次数已经用完，请在直通车后台操作，或明天再来提交。"
            log.error(error_msg % "淘宝API流控")

        return msg, upded_kw_dict

    @classmethod
    def bulk_update_keywords_inner(cls, shop_id, upd_kw_list, tapi):
        """用于长尾托管、或者其它地方进行大批量修改关键词出价"""
        total_updated_num = 0
        invalid_kw_id_list = []
        for temp_kw_list in genr_sublist(upd_kw_list, 100):
            try:
                keywordid_prices = []
                for keyword in temp_kw_list:
                    temp_dict = {'keywordId':keyword[0], 'maxPrice':keyword[1]}
                    if len(keyword) > 2 and keyword[2] in [1, 2, 4]:
                        temp_dict.update({'matchScope':keyword[2]})
                    keywordid_prices.append(temp_dict)
                keywordid_prices = json.dumps(keywordid_prices)
                msg, upd_kw_dict = cls.__update_keywords_inner(shop_id, keywordid_prices = keywordid_prices, tapi = tapi)
                if msg == 'no_valid_kws':
                    invalid_kw_id_list.extend([temp_kw[0] for temp_kw in temp_kw_list])
                if upd_kw_dict: # TODO: wangqi 20140630 这里有个取舍：先API改价，改完后，一把数据库提交；按100个关键词同步提交。实际比较好的是折衷的，分次提交500个关键词后，一把提交到数据库中。
                    update_list = []
                    for keyword_id, upd_dict in upd_kw_dict.items():
                        adg_id = upd_dict.pop('adgroup_id')
                        update_list.append(({'shop_id':shop_id, 'adgroup_id':adg_id, '_id':keyword_id}, {'$set':upd_dict}))
                    total_updated_num += cls.bulk_update_kw2db(update_list)
            except Exception, e:
                log.error('simba_keywords_pricevon_set TopError, shop_id=%s, e = %s' % (shop_id, e))
                continue
        if invalid_kw_id_list:
            cls.remove_keyword({'shop_id':shop_id, '_id':{'$in':invalid_kw_id_list}})

        return total_updated_num

    @classmethod
    def update_keywords_inner(cls, shop_id, kw_arg_list, tapi, opter, opter_name):
        """修改关键词价格"""
        """
        price_update_dict = {'max_price': 200, 'match_scope': 1, 'is_default_price': 0, 'max_mobile_price': 20, 'mobile_is_default_price': 200}
        {max_price, is_default_price, old_price} 为修改PC端出价必要的
        {max_mobile_price, mobile_is_default_price, mobile_old_price} 为修改移动端出价必要的
        match_scope可带可不带，可以跟随上面任意一组。

        kw_arg_list=[
            [campaign_id, adgroup_id, keyword_id, word, {update_dict}], ...
        ]
        """
        record_list = []
        upded_kw_dict = {}
        del_kw_id_list = []
        for temp_kw_list in genr_sublist(kw_arg_list, 200):
            temp_adg_id_list = []
            keywordid_price_list = []
            for kw_arg in temp_kw_list:
                temp_adg_id_list.append(kw_arg[1])
                kw_arg[4] = PriceFactory(kw_arg[2], kw_arg[4]) # 将原来的数据结构修改成类
                keywordid_price_list.append(kw_arg[4].to_dict())

            temp_adg_id_list = list(set(temp_adg_id_list))
            keywordid_prices = json.dumps(keywordid_price_list)
            result_msg, temp_upded_kw_dict = cls.__update_keywords_inner(shop_id = shop_id, keywordid_prices = keywordid_prices, tapi = tapi)
            if result_msg == 'ok':
                upded_kw_dict.update(temp_upded_kw_dict)
            elif result_msg == 'has_dirty_kws': # 有部分词无效，同步结构后，再取最新的结构的交集
                tobj_kw_list = []
                for adg_id in temp_adg_id_list:
                    tobj_kw_list.extend(cls.get_keywords_byadg(shop_id = shop_id, adgroup_id = adg_id, tapi = tapi))

                tobj_kw_id_list = [kw.keyword_id for kw in tobj_kw_list]
                temp_kwidprice_list = []
                for temp_kw in keywordid_price_list:
                    if int(temp_kw['keywordId']) in tobj_kw_id_list:
                        temp_kwidprice_list.append(temp_kw)
                    else: # 不在淘宝返回的最新结果中
                        del_kw_id_list.append(temp_kw['keywordId'])
                result_msg, temp_upded_kw_dict = cls.__update_keywords_inner(shop_id = shop_id, keywordid_prices = json.dumps(temp_kwidprice_list), tapi = tapi)
                upded_kw_dict.update(temp_upded_kw_dict)
            elif result_msg == 'no_valid_kws': # 关键词全部无效，直接删除
                del_kw_id_list.extend([kw['keywordId'] for kw in keywordid_price_list])
            else:
                return [], [], []

        adgroup_id_list = [arg[1] for arg in kw_arg_list]
        adgroup_qset = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adgroup_id_list).only('adgroup_id', 'item_id', 'campaign_id')
        adgroup_dict = {adgroup.adgroup_id: adgroup.item_id for adgroup in adgroup_qset}
        item_id_list = list(set([adgroup.item_id for adgroup in adgroup_qset]))
        item_title_dict = dict(Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('item_id', 'title'))

        for item_id in item_id_list:
            detail_list = []
            item_name = item_title_dict.get(item_id, '')
            for temp_kw in kw_arg_list:
                if upded_kw_dict.has_key(int(temp_kw[2])):
                    temp_item_id = adgroup_dict.get(temp_kw[1], '')
                    if temp_item_id and item_id == temp_item_id:
                        descr = '“%s”%s' % (temp_kw[3], temp_kw[4].to_history())
                        # descr = '“%s” 由%.2f元修改为%.2f元' % (temp_kw[3], temp_kw[6] / 100.0, temp_kw[4] / 100.0)
                        # if temp_kw[5]:
                        #     descr += ', 修改为“%s”' % (match_scope_dict.get(int(temp_kw[5]), '广泛匹配'))
                        detail_list.append(descr)
            if detail_list:
                record_list.append({'shop_id':shop_id, 'campaign_id':temp_kw[0], 'adgroup_id':temp_kw[1], 'item_name': item_name, 'detail_list':detail_list, 'op_type':4, 'data_type':405, 'opter':opter, 'opter_name':opter_name})
        update_list = []
        for keyword_id, upd_dict in upded_kw_dict.items():
            adg_id = upd_dict.pop('adgroup_id')
            update_list.append(({'shop_id':shop_id, 'adgroup_id':adg_id, '_id':keyword_id}, {'$set':upd_dict}))
        cls.bulk_update_kw2db(update_list)

        if del_kw_id_list:
            cls.remove_keyword({'shop_id':shop_id, '_id':{'$in':del_kw_id_list}})

        return upded_kw_dict.keys(), del_kw_id_list, record_list

    @classmethod
    def update_keywords_inner_old(cls, shop_id, kw_arg_list, tapi, opter, opter_name): # kw_arg_list = [(campaign_id, adgroup_id, keyword_id, word, new_price, match_scope, old_price),]
        """修改关键词价格"""
        """
        price_update_dict = {'max_price': 200, 'match_scope': 1, 'use_default_price': 0, 'max_mobile_price': 20, 'mobile_is_default_price': 200}
        {max_price, use_default_price, old_price} 为修改PC端出价必要的
        {max_mobile_price, mobile_is_default_price, mobile_old_price} 为修改移动端出价必要的
        match_scope可带可不带，可以跟随上面任意一组。

        kw_arg_list=[
            [campaign_id, adgroup_id, keyword_id, word, {update_dict}], ...
        ]
        """
        match_scope_dict = {1:'精准匹配', 4:'广泛匹配'}
        record_list = []
        upded_kw_dict = {}
        del_kw_id_list = []
        for temp_kw_list in genr_sublist(kw_arg_list, 100):
            temp_adg_id_list = []
            keywordid_price_list = []
            for kw_arg in temp_kw_list:
                temp_adg_id_list.append(kw_arg[1])
                if kw_arg[4] >= 5 and kw_arg[4] <= 9999:
                    temp_dict = {'keywordId':kw_arg[2], 'maxPrice':kw_arg[4]}
                    if kw_arg[5] and int(kw_arg[5]) in [1, 4]:
                        temp_dict.update({'matchScope':kw_arg[5]})
                    keywordid_price_list.append(temp_dict)

            temp_adg_id_list = list(set(temp_adg_id_list))
            keywordid_prices = json.dumps(keywordid_price_list)
            result_msg, temp_upded_kw_dict = cls.__update_keywords_inner(shop_id = shop_id, keywordid_prices = keywordid_prices, tapi = tapi)
            if result_msg == 'ok':
                upded_kw_dict.update(temp_upded_kw_dict)
            elif result_msg == 'has_dirty_kws': # 有部分词无效，同步结构后，再取最新的结构的交集
                tobj_kw_list = []
                for adg_id in temp_adg_id_list:
                    tobj_kw_list.extend(cls.get_keywords_byadg(shop_id = shop_id, adgroup_id = adg_id, tapi = tapi))

                tobj_kw_id_list = [kw.keyword_id for kw in tobj_kw_list]
                temp_kwidprice_list = []
                for temp_kw in keywordid_price_list:
                    if int(temp_kw['keywordId']) in tobj_kw_id_list:
                        temp_kwidprice_list.append(temp_kw)
                    else: # 不在淘宝返回的最新结果中
                        del_kw_id_list.append(temp_kw['keywordId'])
                result_msg, temp_upded_kw_dict = cls.__update_keywords_inner(shop_id = shop_id, keywordid_prices = json.dumps(temp_kwidprice_list), tapi = tapi)
                upded_kw_dict.update(temp_upded_kw_dict)
            elif result_msg == 'no_valid_kws': # 关键词全部无效，直接删除
                del_kw_id_list.extend([kw['keywordId'] for kw in keywordid_price_list])
            else:
                return [], [], []

        adgroup_id_list = [arg[1] for arg in kw_arg_list]
        adgroup_qset = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adgroup_id_list).only('adgroup_id', 'item_id', 'campaign_id')
        adgroup_dict = {adgroup.adgroup_id: adgroup.item_id for adgroup in adgroup_qset}
        item_id_list = list(set([adgroup.item_id for adgroup in adgroup_qset]))
        item_title_dict = dict(Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('item_id', 'title'))

        for item_id in item_id_list:
            detail_list = []
            item_name = item_title_dict.get(item_id, '')
            for temp_kw in kw_arg_list:
                if upded_kw_dict.has_key(int(temp_kw[2])):
                    temp_item_id = adgroup_dict.get(temp_kw[1], '')
                    if temp_item_id and item_id == temp_item_id:
                        descr = '“%s” 由%.2f元修改为%.2f元' % (temp_kw[3], temp_kw[6] / 100.0, temp_kw[4] / 100.0)
                        if temp_kw[5]:
                            descr += ', 修改为“%s”' % (match_scope_dict.get(int(temp_kw[5]), '广泛匹配'))
                        detail_list.append(descr)
            if detail_list:
                record_list.append({'shop_id':shop_id, 'campaign_id':temp_kw[0], 'adgroup_id':temp_kw[1], 'item_name': item_name, 'detail_list':detail_list, 'op_type':4, 'data_type':405, 'opter':opter, 'opter_name':opter_name})
        update_list = []
        for keyword_id, upd_dict in upded_kw_dict.items():
            adg_id = upd_dict.pop('adgroup_id')
            update_list.append(({'shop_id':shop_id, 'adgroup_id':adg_id, '_id':keyword_id}, {'$set':upd_dict}))
        cls.bulk_update_kw2db(update_list)

        if del_kw_id_list:
            cls.remove_keyword({'shop_id':shop_id, '_id':{'$in':del_kw_id_list}})

        return upded_kw_dict.keys(), del_kw_id_list, record_list

    @classmethod
    def update_kw_mntopt_type(cls, update_mnt_list): # update_mnt_dict形如 [{'adgroup_id':1234, 'keyword_id': 2345, 'mnt_opt_type': 0},...]
        update_id_list = []
        update_list = []
        for mnt_dict in update_mnt_list:
            update_list.append(({'adgroup_id': int(mnt_dict['adgroup_id']), '_id': int(mnt_dict['keyword_id'])}, {'$set': {'mnt_opt_type': int(mnt_dict['mnt_opt_type'])}}))
            update_id_list.append(mnt_dict['keyword_id'])
        cls.bulk_update_kw2db(update_list)
        return update_id_list

    @staticmethod
    def add_keywords_inner(shop_id, adgroup_id, kw_arg_list, tapi, opter, opter_name):
        record_list = []
        keyword_count = Keyword.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id).count()
        need_kwcount = 200 - keyword_count
        if need_kwcount > 2:
            group_scale = max(need_kwcount, 15)
            group_scale = min(int(group_scale * 4 / 2), 100)
        else:
            return "关键词已达到或接近200个", [], [], []

        # 循环添加关键词，并得到添加成功的关键词列表和重复词列表
        result_mesg, added_keyword_list, repeat_word_list = "", [], []
        for temp_arg_list in genr_sublist(kw_arg_list, group_scale):
            if need_kwcount <= 2:
                result_mesg = "关键词已达到或接近200个"
                break

            try:
                keyword_prices, temp_added_keyword_list = [], []
                for word_price in temp_arg_list:
                    if word_price[1] >= 5 and word_price[1] <= 9999:
                        if not word_price[2] or int(word_price[2]) not in [1, 2, 4]:
                            keyword_prices.append({'word':word_price[0], 'maxPrice':word_price[1], 'isDefaultPrice':0})
                        else:
                            keyword_prices.append({'word':word_price[0], 'maxPrice':word_price[1], 'isDefaultPrice':0, 'matchScope':word_price[2]})

                if keyword_prices:
                    keyword_prices = json.dumps(keyword_prices)
                    top_objs = tapi.simba_keywordsvon_add(adgroup_id = adgroup_id, keyword_prices = keyword_prices, retry_count = 1)
                    if top_objs and hasattr(top_objs.keywords, "keyword") and len(top_objs.keywords.keyword) > 0:
                        for kw in top_objs.keywords.keyword:
                            kw.create_time = getattr(kw, 'create_time', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                            kw.modified_time = getattr(kw, 'modified_time', kw.create_time)
                            temp_added_keyword_list.append(Keyword.Parser.parse(kw, trans_type = "init", extra_dict = {'shop_id': shop_id}))

                    need_kwcount = need_kwcount - len(temp_added_keyword_list)
                    added_keyword_list.extend(temp_added_keyword_list)

                    added_word_list = [kw['word'] for kw in temp_added_keyword_list]
                    repeat_word_list.extend([ kw_arg[0] for kw_arg in temp_arg_list if kw_arg[0] not in added_word_list])

            except TopError, e:
                str_error = str(e)
                error_msg = "simba_keywordsvon_add TopError(%%s), shop_id=%s, adgroup_id=%s" % (shop_id, adgroup_id)
                if '已有的关键词重复' in str_error:
                    repeat_word_list.extend(tmp_arg[0] for tmp_arg in temp_arg_list)
                    log.info(error_msg % "已有的关键词重复")
                    continue
                elif '已有关键词已经达到200' in str_error:
                    result_mesg = "关键词已满200个"
                    log.info(error_msg % "已有关键词已经达到200")
                    break
                elif '指定的推广组不存在' in str_error:
                    result_mesg = "推广宝贝已删除"
                    log.info(error_msg % "推广宝贝已删除")
                    break
                elif 'This ban will last for' in str_error:
                    result_mesg = "淘宝流量限制"
                    log.info(error_msg % "淘宝API流控")
                    p = re.compile('This ban will last for (?P<x>\d*) more seconds', re.M | re.U | re.I)
                    rst_set = p.findall(str_error)
                    if rst_set and rst_set[0]:
                        if int(rst_set[0]) <= 10:
                            result_mesg += "。每秒总调用频率过快，请稍候再试"
                        elif int(rst_set[0]) > 10:
                            result_mesg += "。非常抱歉，今天的次数已经用完，请拷贝到后台添加，或明天再来提交"
                    break
                else:
                    result_mesg = "淘宝返回错误"
                    log.error("%s, error=%s" % (error_msg % "其它错误", str_error))
                    break
            except ApiLimitError, e:
                error_msg = "simba_keywordsvon_add ApiLimitError(%%s), shop_id=%s, adgroup_id=%s" % (shop_id, adgroup_id)
                result_mesg = "淘宝流量限制，非常抱歉，今天的次数已经用完，请拷贝到后台添加，或明天再来提交。"
                log.error(error_msg % "淘宝API流控")
                break

        try:
            # 保存关键词到本地
            if added_keyword_list:
                adg = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
                detail_list = []
                match_scope_dict = {1:'精准匹配', 4:'广泛匹配'}
                for kw in added_keyword_list:
                    descr = '“%s” 出价:%.2f元, 匹配方式:%s' % (kw['word'], kw['max_price'] / 100.0, match_scope_dict.get(int(kw['match_scope']), '广泛匹配'))
                    detail_list.append(descr)
                if detail_list:
                    record_list.append({'shop_id':shop_id, 'campaign_id':kw['campaign_id'], 'adgroup_id':adgroup_id, 'item_name': adg.item.title, 'detail_list':detail_list, 'op_type':4, 'data_type':401, 'opter':opter, 'opter_name':opter_name})
                # Adgroup.get_qscore_byadgid(shop_id, adgroup_id, added_keyword_list, tapi)
                Adgroup.bind_added_kw_qscore(shop_id, adgroup_id, added_keyword_list)
                kw_coll.insert(added_keyword_list)
        except Exception, e:
            log.exception('add keywords to local db error,shop_id = %s, adgroup_id=%s, e=%s' % (shop_id, adgroup_id, e))
        return result_mesg, added_keyword_list, repeat_word_list, record_list

    @classmethod
    def delete_keywords_inner(cls, shop_id, campaign_id, kw_arg_list, tapi, data_type, opter, opter_name): # kw_arg_list = [[adgroup_id, keyword_id, word, word_type, word_from, op_reason]]
        fail_id_list, del_id_list, record_list = [], [], []
        for temp_kw_list in genr_sublist(kw_arg_list, 100):
            try:
                temp_id_list = [kw[1] for kw in temp_kw_list]
                keyword_ids = ','.join(map(str, temp_id_list))
                top_objs = tapi.simba_keywords_delete(campaign_id = campaign_id, keyword_ids = keyword_ids)
                if top_objs and hasattr(top_objs.keywords, "keyword") and len(top_objs.keywords.keyword) > 0:
                    del_id_list.extend([temp_obj.keyword_id for temp_obj in top_objs.keywords.keyword])
            except TopError, e:
                error_msg = "simba_keywords_delete TopError(%%s), campaign_id=%s" % (campaign_id)
                if 'sub_msg":"没有属于该客户下指定推广计划的有效关键词可删除' in str(e):
                    log.info(error_msg % "没有有效关键词可删除")
                else:
                    fail_id_list.extend(temp_id_list)
                    log.error("%s, error=%s" % (error_msg % "其它错误", e))
                continue

        if del_id_list:
            adgroup_id_list = [arg[0] for arg in kw_arg_list]
            adgroup_qset = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adgroup_id_list).only('adgroup_id', 'item_id', 'campaign_id')
            adgroup_dict = {adgroup.adgroup_id: adgroup.item_id for adgroup in adgroup_qset}
            item_id_list = list(set([adgroup.item_id for adgroup in adgroup_qset]))
            item_title_dict = dict(Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('item_id', 'title'))

            detail_list = []
            for temp_kw in kw_arg_list:
                if temp_kw[1] in del_id_list:
                    temp_item_id = adgroup_dict.get(temp_kw[0], '')
                    if temp_item_id:
                        detail_list.append(temp_kw[2].strip('\n').strip())
            if detail_list:
                item_name = item_title_dict.get(temp_item_id, '')
                record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'adgroup_id':temp_kw[0], 'item_name': item_name, 'detail_list':detail_list, 'op_type':4, 'data_type':data_type, 'opter':opter, 'opter_name':opter_name})
        need_del_id_list = [kw[1] for kw in kw_arg_list if kw not in fail_id_list]
        if need_del_id_list:
            cls.remove_keyword({'shop_id':shop_id, '_id':{'$in':need_del_id_list}})
        return need_del_id_list, record_list

    @classmethod
    def __delete_increase_keywords(cls, shop_id, last_sync_time, tapi):
        """
                        增量删除adgroup下面的keyword
        """
        page_no, page_size = 1, 200
        deleted_keyword_list, record_list = [], []
        while(True):
            try:
                tobjs = tapi.simba_keywordids_deleted_get(start_time = last_sync_time, page_size = page_size, page_no = page_no)
            except TopError, e:
                log.error('increase_deleted_keywords error, shop_id = %s, e = %s' % (shop_id, e))
                return False

            if tobjs and hasattr(tobjs.deleted_keyword_ids, "number"):
                deleted_keyword_list.extend(tobjs.deleted_keyword_ids.number)
                if len(tobjs.deleted_keyword_ids.number) < page_size:
                    break
                page_no += 1
            else:
                break
        kw_list = kw_coll.find({'shop_id':shop_id, '_id':{'$in':deleted_keyword_list}})
        adgroup_id_list = [kw['adgroup_id'] for kw in kw_list]
        adgroup_qset = Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adgroup_id_list).only('adgroup_id', 'item_id', 'campaign_id')
        adgroup_dict = {adgroup.adgroup_id: adgroup.item_id for adgroup in adgroup_qset}
        item_id_list = list(set([adgroup.item_id for adgroup in adgroup_qset]))
        item_title_dict = dict(Item.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('item_id', 'title'))
        for item_id in item_id_list:
            detail_list = []
            for kw in kw_list:
                temp_item_id = adgroup_dict.get(kw['adgroup_id'], '')
                if temp_item_id and item_id == temp_item_id:
                    detail_list.append(kw['word'].strip('\n').strip())
            if record_list:
                item_name = item_title_dict.get(item_id, '')
                record_list.append({'shop_id':shop_id, 'campaign_id':kw['campaign_id'], 'adgroup_id':kw['adgroup_id'], 'item_name': item_name, 'detail_list':detail_list, 'op_type':4, 'data_type':402, 'opter':0, 'opter_name':''})
        if record_list:
            from models_upload import UploadRecord
            rcd_list = [UploadRecord(**record) for record in record_list]
            UploadRecord.objects.insert(rcd_list)

        if deleted_keyword_list:
            cls.remove_keyword({'shop_id':shop_id, '_id':{'$in':deleted_keyword_list}})
            return True

    @classmethod
    def __change_increase_keywords(cls, shop_id, last_sync_time, tapi):
        """
                        增量更新更改过的关键词
        """
        page_no, page_size = 1, 200
        changed_kw_list = []
        illegal_kw_list = []
        try:
            tobjs = tapi.simba_keywords_changed_get(start_time = last_sync_time, page_size = page_size, page_no = page_no)
            if tobjs and hasattr(tobjs.keywords.keyword_list, 'keyword') and tobjs.keywords.keyword_list.keyword:
                total_item = tobjs.keywords.total_item
                page_count = int(math.ceil(float(total_item) / page_size))
                changed_kw_list.extend(tobjs.keywords.keyword_list.keyword)
                for i in xrange(2, page_count + 1):
                    tobjs = tapi.simba_keywords_changed_get(start_time = last_sync_time, page_size = page_size, page_no = i)
                    if tobjs and hasattr(tobjs.keywords.keyword_list, 'keyword') and tobjs.keywords.keyword_list.keyword:
                        changed_kw_list.extend(tobjs.keywords.keyword_list.keyword)
        except TopError, e:
            log.error('simba_adgroups_changed_get error, shop_id = %s, e = %s' % (shop_id, e))

        if changed_kw_list:
            tobj_kw_dict = {} # 淘宝返回的adgroup字典
            for tobj_kw in changed_kw_list:
                tobj_kw_dict.update({tobj_kw.keyword_id:tobj_kw.modified_time})

            from apps.subway.models_campaign import camp_coll
            local_camp_id_list = [camp['_id'] for camp in camp_coll.find({'shop_id':shop_id}, {'_id':1})] # 本地的计划ID列表，用于过滤非普通计划的关键词
            local_kw_dict = {} # 本地存在的adgroup字典
            mongo_cursor = kw_coll.find({'shop_id':shop_id, '_id':{'$in':tobj_kw_dict.keys()}}, {'modify_time':1})
            for local_kw in mongo_cursor:
                local_kw_dict.update({local_kw['_id']:str(local_kw['modify_time'])})

            kw_dict = {} # 对两个字典的综合，除去有相同时间修改的广告组
            for kw_id, modify_time in tobj_kw_dict.items():
                if local_kw_dict.has_key(kw_id):
                    if not modify_time == local_kw_dict[kw_id]:
                        kw_dict.update({kw_id:'changed'})
                else:
                    kw_dict.update({kw_id:'new'})

            kw_list = cls.__get_keywords_bykwids(shop_id = shop_id, keyword_id_list = kw_dict.keys(), tapi = tapi)
            new_kw_list, changed_kw_dict = [], {}
            for kw in kw_list:
                if kw.audit_status == "audit_reject":
                    illegal_kw_list.append(kw)
                else:
                    if kw_dict.get(kw.keyword_id, 'changed') == 'new':
                        if kw.campaign_id in local_camp_id_list:
                            new_kw_list.append(cls.Parser.parse(kw, trans_type = "init", extra_dict = {'shop_id': shop_id}))
                    else:
                        changed_kw_dict.update({kw.keyword_id:cls.Parser.parse(kw, trans_type = "inc")})
            if new_kw_list:
                kw_coll.insert(new_kw_list)
            if changed_kw_dict:
                update_list = []
                for kw_id, kw_value in changed_kw_dict.items():
                    adg_id = kw_value.pop('adgroup_id')
                    update_list.append(({'shop_id':shop_id, 'adgroup_id':adg_id, '_id':kw_id}, {'$set':kw_value}))
                Keyword.bulk_update_kw2db(update_list)

            if illegal_kw_list:
                IllegalKeyword.save_illegal_kwlist(shop_id, illegal_kw_list)


    @classmethod
    def __get_keywords_bykwids(cls, shop_id, keyword_id_list, tapi):
        """
                        根据关键词ID获取关键词
        """
        keyword_list = []
        for temp_kw_id_list in genr_sublist(keyword_id_list, 200):
            keyword_ids = ','.join(str(kw_id) for kw_id in temp_kw_id_list)
            try:
                top_objs = tapi.simba_keywordsbykeywordids_get(keyword_ids = keyword_ids)
                if top_objs and hasattr(top_objs.keywords, 'keyword') and top_objs.keywords.keyword:
                    keyword_list.extend(top_objs.keywords.keyword)
            except TopError, e:
                log.error('simba_keywordsbykeywordids_get TopError, shop_id = %s, e = %s' % (shop_id, e))
        return keyword_list

    @classmethod
    def get_keywords_byadg(cls, shop_id, adgroup_id, tapi):
        """根据广告组获取关键词"""
        keyword_list = []
        try:
            top_keywords = tapi.simba_keywordsbyadgroupid_get(adgroup_id = adgroup_id, retry_count = settings.TAPI_RETRY_COUNT * 2, retry_delay = 1)
            if top_keywords and hasattr(top_keywords, 'keywords') and top_keywords.keywords:
                keyword_list.extend(top_keywords.keywords.keyword)
        except TopError, e:
            log.error('simba_keywordsbyadgroupid_get by adgroup_id TopError, shop_id = %s, adgroup_id = %s, e = %s' % (shop_id, adgroup_id, e))
        return keyword_list

    @classmethod
    def struct_download(cls, shop_id, tapi):
        adg_id_list = [adg['_id'] for adg in adg_coll.find({'shop_id':shop_id}, {'_id':1})]
        return cls.struct_download_byadgs(shop_id = shop_id, adg_id_list = adg_id_list, tapi = tapi)

    @classmethod
    def struct_download_byadgs(cls, shop_id, adg_id_list, tapi):
        """初始化keywords"""
        try:
            illegal_kw_list = []
            words_count, update_words_count, del_kw_id_list = 0, 0, []
            for temp_adg_id_list in genr_sublist(adg_id_list, 30):
                top_keyword_list = []
                for adg_id in temp_adg_id_list:
                    top_keyword_list.extend(Keyword.get_keywords_byadg(shop_id = shop_id, adgroup_id = adg_id, tapi = tapi))

                local_kw_id_list = [kw['_id'] for kw in kw_coll.find({'shop_id':shop_id, 'adgroup_id':{'$in':temp_adg_id_list}}, {'_id':1})]
                upd_kw_dict, insert_kw_list, old_kw_id_list = {}, [], []
                for kw in top_keyword_list:
                    if kw.audit_status == "audit_reject":
                        illegal_kw_list.append(kw)
                    else:
                        if kw.keyword_id in local_kw_id_list:
                            upd_kw_dict.update({kw.keyword_id:cls.Parser.parse(kw, trans_type = 'inc')})
                            old_kw_id_list.append(kw.keyword_id)
                        else:
                            insert_kw_list.append(cls.Parser.parse(kw, trans_type = 'init', extra_dict = {'shop_id':shop_id}))

                del_kw_id_list.extend(list(set(local_kw_id_list) - set(old_kw_id_list))) # 删除可以一把做
                words_count += len(insert_kw_list)
                update_words_count += len(upd_kw_dict)
                for temp_insert_list in genr_sublist(insert_kw_list, 2000):
                    kw_coll.insert(temp_insert_list)

                update_list = []
                for kw_id, update_info in upd_kw_dict.items():
                    adg_id = update_info.pop('adgroup_id')
                    update_list.append(({'shop_id':shop_id, 'adgroup_id':adg_id, '_id':kw_id}, {'$set':update_info}))
                cls.bulk_update_kw2db(update_list)

            if del_kw_id_list:
                cls.remove_keyword({'shop_id':shop_id, '_id':{'$in':del_kw_id_list}})

            if illegal_kw_list:
                IllegalKeyword.save_illegal_kwlist(shop_id, illegal_kw_list)

            log.info('init keywords OK, shop_id = %s, get %s keywords, update %s keywords' % (shop_id, words_count, update_words_count))
            return True
        except Exception, e:
            log.error('init keywords FAILED, shop_id = %s, e = %s' % (shop_id, e))
            return False

    @classmethod
    def increase_download(cls, shop_id, tapi, last_sync_time):
        try:
            cls.__delete_increase_keywords(shop_id = shop_id, last_sync_time = last_sync_time, tapi = tapi)
            cls.__change_increase_keywords(shop_id = shop_id, last_sync_time = last_sync_time, tapi = tapi)
            log.info('sync keywords OK, shop_id = %s' % shop_id)
            return True
        except Exception, e:
            log.error('sync keywords FAILED, shop_id = %s, e = %s' % (shop_id, e))
            return False

    @classmethod
    def download_kwrpt_byadg(cls, shop_id, adgroup_id, campaign_id, token, time_scope, tapi):
        rpt_list = []
        for search_type, source in cls.Report.REPORT_CFG:
            base_list = cls.Report.download_kwrpt_base(shop_id, campaign_id, adgroup_id, token, time_scope[0], time_scope[1], search_type, source, tapi)
            if base_list:
                effect_list = cls.Report.download_kwrpt_effect(shop_id, campaign_id, adgroup_id, token, time_scope[0], time_scope[1], search_type, source, tapi)
                
            rpt_list.extend(cls.Report.merge_kwrpt(shop_id, campaign_id, adgroup_id, base_list, effect_list))

        if rpt_list:
            cls.Report.update_rpt_list({'shop_id':shop_id, 'adgroup_id': adgroup_id, 'date':{'$lte':date_2datetime(time_scope[1]), '$gte':date_2datetime(time_scope[0])}}, rpt_list)

        # 将同步时间及是否要验证写回adgroup
        sync_time = datetime.datetime.now() # 同步时间取当前
        valid_flag = False # 有效性设置为False
        if sync_time.hour < 6: # 时间早于6点，将同步时间设置为昨天
            sync_time = sync_time - datetime.timedelta(days = 1)
        if sync_time.hour >= 9: # 时间超过9点，设置有效性为True
            valid_flag = True
        adg_coll.update({'shop_id':shop_id, '_id':adgroup_id}, {'$set':{'kwrpt_sync_time':sync_time, 'kwrpt_valid': valid_flag}})
        return True

    @classmethod
    def download_kwrpt_byadg_bak(cls, shop_id, adgroup_id, campaign_id, token, time_scope, tapi):
        """下载单个广告组的所有报表数据"""
        page_size = 200
        rpt_list = []
        for search_type, source in cls.Report.REPORT_CFG:
            base_page_no , effect_page_no = 1, 1
            base_dict, effect_dict = collections.defaultdict(dict), collections.defaultdict(dict)
            while(True):
                try:
                    top_base_objs = tapi.simba_rpt_adgroupkeywordbase_get(campaign_id = campaign_id, adgroup_id = adgroup_id,
                                                                      start_time = time_scope[0], end_time = time_scope[1],
                                                                      search_type = search_type, source = source, subway_token = token,
                                                                      page_no = base_page_no, page_size = page_size,
                                                                      retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
                except TopError, e:
                    log.error('simba_rpt_adgroupkeywordbase_get TopError, shop_id=%s, adgroup_id=%s, time=%s, e=%s' % (shop_id, adgroup_id, time_scope, e))
                    return False

                if top_base_objs and hasattr(top_base_objs, 'rpt_adgroupkeyword_base_list') and top_base_objs.rpt_adgroupkeyword_base_list:
                    for base in top_base_objs.rpt_adgroupkeyword_base_list:
                        base_dict[base.keyword_id].update(cls.Report.parse_rpt(base, 'base'))

                    if len(top_base_objs.rpt_adgroupkeyword_base_list) < page_size:
                        break
                    base_page_no += 1
                else:
                    break

            if base_dict:
                while(True):
                    try:
                        top_effect_objs = tapi.simba_rpt_adgroupkeywordeffect_get(campaign_id = campaign_id, adgroup_id = adgroup_id,
                                                                            start_time = time_scope[0], end_time = time_scope[1],
                                                                            search_type = search_type, source = source, subway_token = token,
                                                                            page_no = effect_page_no, page_size = page_size,
                                                                            retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
                    except TopError, e:
                        log.error('simba_rpt_adgroupkeywordeffect_get TopError, shop_id=%s, adgroup_id=%s, time=%s, e=%s' % (shop_id, adgroup_id, time_scope, e))
                        return False

                    if top_effect_objs and hasattr(top_effect_objs, 'rpt_adgroupkeyword_effect_list') and top_effect_objs.rpt_adgroupkeyword_effect_list:
                        for effect in top_effect_objs.rpt_adgroupkeyword_effect_list:
                            effect_dict[effect.keyword_id].update(cls.Report.parse_rpt(effect, 'effect'))

                        if len(top_effect_objs.rpt_adgroupkeyword_effect_list) < page_size:
                            break
                        effect_page_no += 1
                    else:
                        break

                for kw_id, base_rpt_dict in base_dict.items():
                    rpt_list.extend(cls.Report.merge_rpt_dict(base_rpt_dict, effect_dict.get(kw_id, {}), {'shop_id': shop_id, 'campaign_id': campaign_id, 'adgroup_id':adgroup_id, 'keyword_id':kw_id}))

        if rpt_list:
            cls.Report.update_rpt_list({'shop_id':shop_id, 'adgroup_id': adgroup_id, 'date':{'$lte':date_2datetime(time_scope[1]), '$gte':date_2datetime(time_scope[0])}}, rpt_list)

        # 将同步时间及是否要验证写回adgroup
        sync_time = datetime.datetime.now() # 同步时间取当前
        valid_flag = False # 有效性设置为False
        if sync_time.hour < 6: # 时间早于6点，将同步时间设置为昨天
            sync_time = sync_time - datetime.timedelta(days = 1)
        if sync_time.hour >= 9: # 时间超过9点，设置有效性为True
            valid_flag = True
        adg_coll.update({'shop_id':shop_id, '_id':adgroup_id}, {'$set':{'kwrpt_sync_time':sync_time, 'kwrpt_valid': valid_flag}})
        return True

    @classmethod
    def download_kwrpt_byadgs_old(cls, shop_id, tapi, token, adg_tuple_list): # adg_tuple_list形如[(adgroup_id, campaign_id, last_sync_time)]
        """根据给定的adg_tuple_list来下载指定的adgroup_list下面的关键词"""
        try:
            init_start_date = datetime.date.today() - datetime.timedelta(days = cls.Report.INIT_DAYS)
            valid_rpt_days = datetime.datetime.now().hour < 6 and 2 or 1
            valid_rpt_days += 2
            end_date = datetime.date.today() - datetime.timedelta(days = valid_rpt_days)
            for adg in adg_tuple_list:
                last_date = adg[2].date()
                if last_date < init_start_date:
                    last_date = init_start_date
                elif last_date > end_date:
                    last_date = end_date
                if not time_is_someday(last_date):
                    cls.download_kwrpt_byadg(shop_id = shop_id, adgroup_id = adg[0], campaign_id = adg[1], token = token, time_scope = (last_date, end_date), tapi = tapi)
            return True, ''
        except Exception, e:
            return False, e

    @classmethod
    def bulk_download_kwrpt_byadgs(cls, shop_id, campaign_id, adg_date_dict, token, end_date):
        dc = EnhancedDownloadContracter(shop_id = shop_id, campaign_id = campaign_id, adg_date_dict = adg_date_dict, token = token, end_date = end_date)
        try:
            rpt_list = dc()
        except Exception as e:
            log.error("bulk download kwrpt failed, reason=%s" % e)
            return False

        if rpt_list:
            # 入库需要先清理数据库，然后再插入数据
            cls.Report.insert_rpt_list(shop_id, end_date, adg_date_dict, rpt_list)

        sync_time = datetime.datetime.now() # 同步时间取当前
        valid_flag = False # 有效性设置为False
        if sync_time.hour < 6: # 时间早于6点，将同步时间设置为昨天
            sync_time = sync_time - datetime.timedelta(days = 1)
        if sync_time.hour >= 9: # 时间超过9点，设置有效性为True
            valid_flag = True
        adg_coll.update({'shop_id':shop_id, '_id': {'$in': adg_date_dict.keys()}}, {'$set':{'kwrpt_sync_time':sync_time, 'kwrpt_valid': valid_flag}}, multi = True)
        return True


    @classmethod
    def download_kwrpt_byadgs(cls, shop_id, tapi, token, adg_tuple_list): # adg_tuple_list形如[(adgroup_id, campaign_id, last_sync_time)]
        """根据给定的adg_tuple_list来下载指定的adgroup_list下面的关键词"""
        try:
            download_group = collections.defaultdict(dict) # 将adgroup分组
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
                    download_group[adg[1]].update({adg[0]: last_date})

            total_result = True
            for campaign_id, adg_date_dict in download_group.items():
                single_result = cls.bulk_download_kwrpt_byadgs(shop_id, campaign_id, adg_date_dict, token, end_date)
                if not single_result:
                    total_result = False
            return total_result, ''
        except Exception, e:
            return False, e

    @classmethod
    def report_download(cls, shop_id, tapi, token, time_scope):
        """通过遍历广告组下载所有关键词，时间段通过保存在adgroup中的时间来自动补全 """
        init_start_time = datetime.datetime.today() - datetime.timedelta(days = cls.Report.INIT_DAYS)
        adg_tuple_list = [(adg['_id'], adg['campaign_id'], adg.get('kwrpt_sync_time', init_start_time)) for adg in adg_coll.find({'shop_id':shop_id}, {'_id':1, 'campaign_id':1, 'kwrpt_sync_time':1})]
        result, reason = cls.download_kwrpt_byadgs(shop_id = shop_id, tapi = tapi, token = token, adg_tuple_list = adg_tuple_list)
        if result:
            log.info('download keyword rpt OK, shop_id = %s' % (shop_id))
            return 'OK'
        else:
            log.error('download keyword rpt FAILED, shop_id = %s, e = %s' % (shop_id, reason))
            return 'FAILED'

    def get_snap_list(self, **kwargs):
        rpt_dict = self.Report.get_snap_list({'adgroup_id': self.adgroup_id, 'keyword_id': self.keyword_id}, **kwargs)
        return rpt_dict.get(self.keyword_id, [])

    def get_summed_rpt(self, **kwargs):
        rpt_dict = self.Report.get_summed_rpt({'adgroup_id': self.adgroup_id, 'keyword_id': self.keyword_id}, **kwargs)
        return rpt_dict.get(self.keyword_id, self.Report())

    @classmethod
    def force_download_rpt(cls, shop_id, tapi, token, time_scope):
        """给出时间区间，强制下载"""
        adg_tuple_list = [(adg['_id'], adg['campaign_id'], time_scope[0]) for adg in adg_coll.find({'shop_id':shop_id}, {'_id':1, 'campaign_id':1})]
        result, _ = cls.download_kwrpt_byadgs(shop_id = shop_id, tapi = tapi, token = token, adg_tuple_list = adg_tuple_list)
        return result

    @classmethod
    def snapshot_keyword(cls, shop_id, adgroup_id):
        update_list = []
        kw_cursor = cls._get_collection().find({'adgroup_id': adgroup_id, 'shop_id': shop_id}, {'_id':1, 'max_price':1, 'qscore':1, 'qscore_dict':1, 'snapshot_list':1})
        date_dict = {'date': date_2datetime(datetime.date.today())}
        for kw in kw_cursor:
            temp_dict = date_dict.copy()
            temp_dict.update({'max_price': kw['max_price'], 'qscore': kw['qscore']})
            update_list.append(({'shop_id': shop_id, 'adgroup_id': adgroup_id, '_id': kw['_id']}, {'$push': {'snap_list': temp_dict}}))
            # qscore_dict = kw.get('qscore_dict', {})
            # if qscore_dict:
            #     qscore_dict['qscore'], qscore_dict['wireless_qscore']

        cls.bulk_update_kw2db(update_list)
        return True

    @classmethod
    def __get_rt_kw_rank(cls, tapi, adg_id, price, kw_id):
        try:
            result = {}
            tobj = tapi.simba_keywords_realtime_ranking_get(ad_group_id = adg_id, bid_price = price, bidword_id = kw_id)
            if tobj:
                if hasattr(tobj, 'result') and tobj.result:
                    result = {'mobile_rank': getattr(tobj.result, 'mobile_rank', '').replace('计划', ''), 'pc_rank': getattr(tobj.result, 'pc_rank', '')}
                elif hasattr(tobj, 'key') and hasattr(tobj, 'message'):
                    raise Exception(tobj.key, tobj.message)
        except TopError, e:
            log.error('simba_keywords_realtime_ranking_get TopError, adg_id=%s, kw_id=%s, e=%s' % (adg_id, kw_id, e))
        except Exception, e:
            log.error('simba_keywords_realtime_ranking_get Error, adg_id=%s, kw_id=%s, e = %s' % (adg_id, kw_id, e))
        finally:
            return result

    @classmethod
    def get_rt_kw_rank(cls, tapi, adg_id, price, kw_id):
        '''新实时预估排名接口'''
        # 弃用缓存， 因为修改分时折扣、移动溢价时，同一个关键词相同出价排名应该是不同的。
        # key = CacheKey.SUBWAY_KEYWORD_RT_RANK % (kw_id, price)
        # rank_dict = CacheAdpter.get(key, 'web', {})
        # if not rank_dict:
        #     rank_dict = cls.__get_rt_kw_rank(tapi, adg_id, price, kw_id)
        #     if rank_dict:
        #         CacheAdpter.set(key, rank_dict, 'web', 60 * 15)
        # return rank_dict
        return cls.__get_rt_kw_rank(tapi, adg_id, price, kw_id)

    @classmethod
    def batch_get_rt_kw_rank(cls, tapi, nick, adg_id, kw_id_list):
        '''批量获取关键词实时排名接口'''
        result = {
            str(kw_id): {
                'bidwordid': str(kw_id),
                'pc_rank': '-9',
                'pc_rank_desc': '获取失败',
                'mobile_rank': '-9',
                'mobile_rank_desc': '获取失败'
            }
            for kw_id in kw_id_list
        }
        i, j = 0, 20
        while i < len(kw_id_list):
            try:
                bidword_ids = ','.join(map(str, kw_id_list[i:i + j]))
                tobj = tapi.simba_keywords_realtime_ranking_batch_get(nick = nick, ad_group_id = adg_id, bidword_ids = bidword_ids)
                if tobj:
                    if hasattr(tobj, 'result') and tobj.result:
                        if hasattr(tobj.result, 'realtime_rank_list') and tobj.result.realtime_rank_list:
                            if hasattr(tobj.result.realtime_rank_list, 'result') and tobj.result.realtime_rank_list.result:
                                for info in tobj.result.realtime_rank_list.result:
                                    _info = info.to_dict()
                                    for key in ['pc_rank', 'mobile_rank']:
                                        _info[key + '_desc'] = cls.KW_RT_RANK_MAP[key].get(_info.get(key, ''), '获取失败')
                                    result[_info['bidwordid']] = _info
                        elif hasattr(tobj.result, 'key') and hasattr(tobj.result, 'msg'):
                            raise Exception(tobj.result.key, tobj.result.message)
                    else:
                        raise Exception('淘宝接口异常')
            except TopError, e:
                log.error('simba_keywords_realtime_ranking_batch_get TopError, adg_id=%s, kw_ids=%s, e=%s' % (adg_id, bidword_ids, e))
            except Exception, e:
                log.error('simba_keywords_realtime_ranking_batch_get Error, adg_id=%s, kw_ids=%s, e = %s' % (adg_id, bidword_ids, e))
            finally:
                i += j
        return result

    @classmethod
    def __get_kw_rankingforecast(cls, tapi, shop_id, keyword_ids):
        result = []
        try:
            tobj = tapi.simba_keyword_rankingforecast_get(keyword_ids = keyword_ids)
            # result = tobj.keyword_ranking_forecast.Rankingforecast[0].prices.number
            if tobj:
                t_res = tobj.keyword_ranking_forecast.Rankingforecast[0]
                if t_res and hasattr(t_res, 'prices'):
                    result = t_res.prices.number
        except TopError, e:
            log.error('simba_keyword_rankingforecast_get TopError, shop_id = %s, keyword_id = %s, error = %s' % (shop_id, keyword_ids, e))
        except Exception, e:
            log.error('simba_keyword_rankingforecast_get Error, shop_id = %s, keyword_id = %s, error = %s' % (shop_id, keyword_ids, e))
        finally:
            return result

    # @classmethod
    # def get_keyword_rankingforecast(cls, tapi, shop_id, keyword_ids):
    #     try:
    #         result = CacheAdpter.get(CacheKey.KWLIB_FORECAST_KWRANK % keyword_ids, 'kwlib', 'no_cache')
    #         if result == 'no_cache':
    #             result = cls.__get_kw_rankingforecast(tapi, shop_id, keyword_ids)
    #             if result != []:
    #                 CacheAdpter.set(CacheKey.KWLIB_FORECAST_KWRANK % keyword_ids, result, 'kwlib', 60 * 30)
    #     except Exception, e:
    #         log.error('get_keyword_rankingforecast Error, shop_id = %s, keyword_id = %s, error = %s' % (shop_id, keyword_ids, e))
    #         result = []
    #     finally:
    #         return result

    @staticmethod
    def download_kwrpt_bycondition(shop_id, tapi, token, rpt_days, condition_tuple, adg_id_list = []): # condition_tuple  ('click',0)
        start_time = date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_days))
        init_start_time = datetime.datetime.today() - datetime.timedelta(days = Keyword.Report.INIT_DAYS)
        pipeline = [
                {'$match': {'shop_id':shop_id}},
                {'$unwind':'$rpt_list'},
                {'$match':{'rpt_list.date':{'$gte':start_time}}},
                {'$group':{'_id':'$_id', 'campaign_id':{'$first':'$campaign_id'}, 'kwrpt_sync_time':{'$first':'$kwrpt_sync_time'}, 'condition':{'$sum':'$rpt_list.%s' % (condition_tuple[0])}}},
                {'$match':{'condition':{'$gt':condition_tuple[1]}}},
            ]
        if adg_id_list:
            pipeline[0]['$match']['_id'] = {'$in':adg_id_list}

        adg_list = adg_coll.aggregate(pipeline)['result']
        adg_tuple_list = []
        for a in adg_list:
            if a.has_key('kwrpt_sync_time') and not a['kwrpt_sync_time']:
                a['kwrpt_sync_time'] = init_start_time
            adg_tuple_list.append((a['_id'], a['campaign_id'], a.get('kwrpt_sync_time', init_start_time)))
        result, reason = Keyword.download_kwrpt_byadgs(shop_id = shop_id, tapi = tapi, token = token, adg_tuple_list = adg_tuple_list)
        return result, reason, len(adg_list)

    @classmethod
    def download_kwrpt_bycond(cls, shop_id, cond, tapi, token, rpt_days, adg_id_list = []): # cond是impressions, 或者click等的过滤字段
        query_dict = {'shop_id': shop_id, 'date': {'$gte': date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_days))}}
        if adg_id_list:
            query_dict.update({'adgroup_id': {'$in': adg_id_list}})

        pipeline = [
            {'$match': query_dict},
            {'$group':{'_id':'$adgroup_id', 'condition':{'$sum':'$%s' % (cond)}}},
            {'$match':{'condition':{'$gt':0 }}},
        ]
        aggr_result = Adgroup.Report._get_collection().aggregate(pipeline)
        filtered_adgid_list = []
        if aggr_result['ok']:
            for temp_result in  aggr_result['result']:
                filtered_adgid_list.append(temp_result['_id'])

        if filtered_adgid_list:
            adg_tuple_list = []
            init_start_time = datetime.datetime.today() - datetime.timedelta(days = cls.Report.INIT_DAYS)
            cursor = adg_coll.find({'shop_id': shop_id, '_id': {'$in': filtered_adgid_list}}, {'campaign_id': 1, 'kwrpt_sync_time': 1})
            for i in cursor:
                adg_tuple_list.append((i['_id'], i['campaign_id'], i.get('kwrpt_sync_time', init_start_time)))
            return cls.download_kwrpt_byadgs(shop_id, tapi, token, adg_tuple_list)
        else:
            return True, ''

    @staticmethod
    def get_conv_words_8item(shop_id, item_id_list):
        """用于全自动加词"""

        def get_conv_words_8adg(shop_id, adg_id_list, rpt_days = 7):
            start_time = datetime.datetime.today() - datetime.timedelta(days = rpt_days)
            aggr_pipeline = [{'$match':{'shop_id':shop_id, 'adgroup_id': {'$in': adg_id_list}}},
                             {'$unwind':'$rpt_list'},
                             {'$match':{'rpt_list.date':{'$gte':start_time},
                                        '$or':[{'rpt_list.directpay':{'$gt':0}},
                                               {'rpt_list.indirectpay':{'$gt':0}}]
                                        }},
                             {'$group':{'_id': {'adgroup_id': '$adgroup_id', 'word': '$word'}, 'max_price': {'$first': '$max_price'}}},
                             {'$project': {'_id': 0, 'adgroup_id': '$_id.adgroup_id', 'word': '$_id.word', 'max_price': 1}},
                             {'$group':{'_id': '$adgroup_id', 'word_list':{'$push': {'word':'$word', 'max_price': '$max_price'}}}}
                             ]
            result = []
            try:
                result = kw_coll.aggregate(aggr_pipeline)['result']
            except Exception, e:
                log.error('aggregate pipeline fail,, shop_id=%s, e=%s' % (shop_id, e))
            return result

        result_dict = {}
        relate_adg_list = adg_coll.find({'shop_id': shop_id, 'item_id': {'$in': item_id_list}}, {'_id': 1, 'item_id': 1})
        if not relate_adg_list:
            return result_dict

        item_adg_dict = {adg['_id']: adg['item_id'] for adg in relate_adg_list}

        relate_word_list = get_conv_words_8adg(shop_id, item_adg_dict.keys())
        relate_word_dict = {}
        for rwl in relate_word_list:
            item_id = item_adg_dict[rwl['_id']]
            for word_dict in rwl['word_list']:
                relate_word_dict.setdefault(item_id, {})[word_dict['word']] = word_dict['max_price']

        from apilib.parsers import TopObjectParser
        for item_id, word_dict in relate_word_dict.iteritems():
            word_list = [{'word': k, 'new_price': v} for k, v in word_dict.iteritems()]
            result_dict[item_id] = TopObjectParser.json_to_object(word_list)

        return result_dict

    @staticmethod
    def get_conv_words(shop_id, item_id, camp_id_list = []):
        """获取其他计划中同一宝贝所对应的有转化词, 注：如果camp_id_list为空，将默认为当前店铺所有计划"""
        def get_valid_word_list(shop_id, item_id, adg_id_list, days = 7):
            """获取所需要的关键词"""
            aggr_pipeline = [{"$match":{"shop_id":shop_id, "adgroup_id":{"$in":adg_id_list}}},
                             {"$unwind":"$rpt_list"},
                             {"$match":{"$or":[{"rpt_list.directpay":{"$gt":0}},
                                               {"rpt_list.indirectpay":{"$gt":0}}]}},
                             {"$project":{'_id':0, "new_price":"$max_price", "word":"$word"}}
                             ]
            result = []
            try:
                result = kw_coll.aggregate(aggr_pipeline)['result']
            except Exception, e:
                log.error("aggregate pipeline fail,, shop_id=%s, item_id=%s, e=%s" % (shop_id, item_id, e))
            return result

        # TODO: yangrongkai 此处是否需要对 camp_id_list 为空时提供全店计划
        adg_list = Adgroup.get_adgroup_byitem(shop_id, item_id, camp_id_list)
        if not adg_list:
            return []

        adg_id_list = [adg.adgroup_id for adg in adg_list]
        result_list = get_valid_word_list(shop_id, item_id, adg_id_list)
        if not result_list:
            return []

        temp_dict = {}
        for result in result_list:
            try:
                word = result['word']
                new_price = result['new_price']
                temp_dict[word] = max(temp_dict.get(word, 0), new_price)
            except Exception, e:
                log.error('data is wrong, result=%s, e=%s' % (result, e))
                continue

        result_list = [{"word":key, "new_price":val * 1.15} for key, val in temp_dict.items()]
        from apilib.parsers import TopObjectParser
        kw_list = TopObjectParser.json_to_object(result_list)
        return kw_list

    @classmethod
    def get_hasrpt_list(cls, query_dict, rpt_days = 15):
        '''获取整店所有有报表的词 (有报表：15天内有展现量）'''
        base_query = {'source':-1, 'search_type':-1 }
        date_query = {'date': {'$gte': date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_days))}}

        base_query.update(date_query)
        base_query.update(query_dict)
        result = cls.Report._get_collection().aggregate([
			{'$match': base_query },
            {'$group': {
                '_id':{'keyword_id':'$keyword_id'},
                'impressions': {'$sum': '$impressions'}
                }
            },

        ])
        kw_id_list = []

        if result['ok']:
            for temp_result in result['result']:
                if temp_result['impressions'] > 0:
                    kw_id_list.append(temp_result['_id']['keyword_id'])
        return kw_id_list

    @classmethod
    def get_kwrpt_dict(cls, query_dict, rpt_days = 7):
        """获取重复关键词报表数据 by tianxiaohe 20151113"""
        base_query = {'source':-1, 'search_type':-1 }
        date_query = {'date': {'$gte': date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_days))}}

        base_query.update(date_query)
        base_query.update(query_dict)
        result = cls.Report.get_summed_rpt(base_query)
        return result

    @classmethod
    def get_kwrpt_sort_list(cls, query_dict, rpt_days = 7):
        """获取报表，根据ctr、impr降序排序"""
        base_query = {'source':-1, 'search_type':-1 }
        date_query = {'date': {'$gte': date_2datetime(datetime.date.today() - datetime.timedelta(days = rpt_days))}}

        base_query.update(date_query)
        base_query.update(query_dict)
        result = cls.Report._get_collection().aggregate([
			{'$match': base_query },
            {'$group': {
                '_id': {'keyword_id': '$keyword_id'},
                'impressions': {'$sum': '$impressions'},
                'click':{'$sum':'$click'}
                }
            },
            {'$project': {
                '_id': 0,
            	'keyword_id': '$_id.keyword_id',
                'impressions':'$impressions',
                'click':'$click',
            	'ctr':{'$cond':[{'$eq':['$impressions', 0]}, 0,
                                       {'$divide':['$click', '$impressions']}]
                             }
            	}
            },
            {'$sort':SON([('click', -1), ('impressions', -1), ('_id', -1)])},
            # $project，这里只传给adgroup_id，报表后面再取一遍
            {'$project':{
                '_id': '$keyword_id',
                'impressions': '$impressions',
                'click': '$click'
            }}
        ])
        if result['ok']:
            return result['result']

    @classmethod
    def get_garbage_words(cls, shop_id, mnt_campid_list = []):
        '''获取整店垃圾词 add by tianxiaohe 20151116'''

        query_dict = {
            'shop_id': shop_id,
            'is_garbage':True,
            'campaign_id':{'$nin':mnt_campid_list},
        }

        # 查询is_garbage==True，该字段由淘宝返回
        garbage_list = list(kw_coll.find(query_dict, {'_id':1, 'is_garbage':1, 'campaign_id':1, 'adgroup_id':1, 'word':1}))
        return garbage_list

    @classmethod
    def get_lowscore_words(cls, shop_id):
        '''获取低分词 add by tianxiaohe 20151120'''
        query_dict = {
            'shop_id': shop_id,
            'qscore_dict.wireless_qscore':{'$lte':3, '$gte':1},
            'qscore_dict.qscore':{'$lte':3, '$gte':1}
        }
        lowscore_kw_list = list(kw_coll.find(query_dict, {'_id':1}))
        lowscore_id_list = []
        for kw in lowscore_kw_list:
            lowscore_id_list.append(kw['_id'])
        return lowscore_id_list

kw_coll = Keyword._get_collection()


class Attention(Document):
    shop_id = IntField(verbose_name = "店铺ID", required = True, primary_key = True)
    keyword_id_list = ListField(verbose_name = "关键词ID列表", field = IntField())
    meta = {"collection":"attention", 'shard_key':('_id',), }

    @staticmethod
    def change_attention_state(shop_id, adgroup_id, keyword_id, is_focus):
        '''添加关注的关键词并且改变其关键词列表的状态'''
        try:
            if not attn_coll.find({'_id':shop_id}).count():
                if is_focus:
                    attn_coll.insert({'_id':shop_id, 'keyword_id_list':[keyword_id]})
                else:
                    return False
            else:
                update_kw = is_focus and '$push' or '$pull'
                attn_coll.update({'_id':shop_id}, {update_kw:{'keyword_id_list':keyword_id}})

            kw_coll.update({'shop_id':shop_id, 'adgroup_id':adgroup_id, '_id':keyword_id}, {'$set':{'is_focus':is_focus}})
            return True
        except Exception, e:
            log.error('get_or_create attention object or get keyword error err=%s' % (e))
            return False

    @staticmethod
    def get_attention_list(shop_id):
        keyword_id_list, full_kw_list, new_keyword_id_list = [], [], []
        attention = attn_coll.find_one({'_id':shop_id})
        if attention:
            keyword_id_list = attention['keyword_id_list']
        if keyword_id_list:
            kw_dict_list = kw_coll.find({'shop_id':shop_id, '_id':{'$in':keyword_id_list}})
            full_kw_list = trans_batch_dict_2document(kw_dict_list, Keyword)
            g_data_dict = get_kw_g_data([kw_obj.word for kw_obj in full_kw_list])
            for kw in full_kw_list:
                g_data = g_data_dict.get(str(kw.word), {})
                for k, v in g_data.items():
                    setattr(kw, k, v)
                new_keyword_id_list.append(kw.keyword_id)
            if set(keyword_id_list) ^ set(new_keyword_id_list):
                attn_coll.update({'_id':shop_id}, {'$set':{'keyword_id_list':new_keyword_id_list}}, upsert = True)
        return full_kw_list

attn_coll = Attention._get_collection()

class IllegalKeyword(Document):
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    root_parent_id = IntField(verbose_name = "一级类目ID")
    cat_id = IntField(verbose_name = "当前类目ID")
    cat_path = StringField(verbose_name = "当前类目路径", max_length = 100)
    word = StringField(verbose_name = "关键词", max_length = 100, required = True)
    is_handled = IntField(verbose_name = "是否已处理", default = 0)
    last_name = StringField(verbose_name = "店铺类型", max_length = 30)

    meta = {'collection':'illegal_keyword', "shard_key":('shop_id',), 'indexes':['cat_id']}

    # TODO: wangqi 20150928 这里可以利用贝叶斯分类算法，学习判断一个关键词是否是违禁词，在加词的时候就能避免类似的词被加入

    @classmethod
    def save_illegal_kwlist(cls, shop_id, illegal_kw_list): # illegal_kw_list中的keyword是top_object
        from apps.router.models import User
        from apps.kwslt.models_cat import Cat
        from apps.subway.upload import delete_keywords

        del_kw_dict = collections.defaultdict(list)
        adg_kw_dict = collections.defaultdict(list)

        try:
            shop_type = User.objects.get(shop_id = shop_id).shop_type
        except User.DoesNotExist:
            shop_type = "unknown"

        for kw in illegal_kw_list:
            del_kw_dict[kw.campaign_id].append([kw.adgroup_id, kw.keyword_id, kw.word, 1, 0, '删除违规词'])
            adg_kw_dict[kw.adgroup_id].append(kw)

        # 根据广告组ID获取广告组ID-->类目映射
        adg_cursor = adg_coll.find({'shop_id': shop_id, '_id': {'$in': adg_kw_dict.keys()}}, {'_id':1, 'category_ids':1})
        adg_cat_dict = {adg['_id']: adg['category_ids'] for adg in adg_cursor}

        # 加载本店已有违禁词，用于排重
        local_catword_dict = collections.defaultdict(list)
        local_cursor = local_illegal_kwlist = cls._get_collection().find({'shop_id':shop_id})
        for local_kw in local_cursor:
            local_catword_dict[local_kw['cat_id']].append(local_kw['word'])

        insert_illegal_kwlist = []

        for adg_id, kw_list in adg_kw_dict.items():
            category_ids = adg_cat_dict.get(adg_id, "")
            cat_id_list = category_ids.split()
            cat_id, parent_cat_id = int(cat_id_list[-1]), int(cat_id_list[0])

            cat_path_dict = Cat.get_cat_path_name(cat_id_list = [cat_id])
            cat_path_name = cat_path_dict.get(cat_id, '类目找不到？cat_id=%s' % cat_id)

            local_cat_word_list = local_catword_dict.get(cat_id, [])
            for illegal_kw in kw_list:
                if illegal_kw.word not in local_cat_word_list:
                    insert_illegal_kwlist.append({'shop_id': shop_id, 'root_parent_id': parent_cat_id,
                                                  'word': illegal_kw.word, 'cat_id': cat_id, 'cat_path': cat_path_name,
                                                  'is_handled':0, 'last_name':shop_type})
        # 新写入违禁词
        if insert_illegal_kwlist:
            cls._get_collection().insert(insert_illegal_kwlist)

        # 删除违禁词
        for campaign_id, del_kw_list in del_kw_dict.items():
            delete_keywords(shop_id = shop_id, campaign_id = campaign_id, kw_arg_list = del_kw_list, data_type = 403, opter = 3, opter_name = '')

illegal_kw_coll = IllegalKeyword._get_collection()
