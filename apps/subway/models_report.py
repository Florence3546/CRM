# coding=UTF-8
import datetime
import collections

from pymongo.errors import BulkWriteError
from mongoengine.document import Document
from mongoengine.fields import IntField, DateTimeField
from django.conf import settings

from apilib import TopError
from apps.common.utils.utils_log import log
from apps.common.utils.utils_number import fen2yuan
from apps.common.utils.utils_datetime import date_2datetime, string_2datetime
from apps.common.biz_utils.utils_dictwrapper import DictWrapper


class BaseRptProperty(object):
    """不保证数据来源，由子类保证，只提供几个基础方法"""

    @property
    def pay(self):
        return self.directpay + self.indirectpay

    @property
    def paycount(self):
        return self.directpaycount + self.indirectpaycount

    @property
    def favcount(self):
        return self.favitemcount + self.favshopcount

    @property
    def cpm(self):
        if self.impressions and self.cost:
            return self.cost * 1000.00 / self.impressions
        return 0.00

    @property
    def roi(self):
        if self.cost:
            return float(self.pay) / self.cost
        return 0.00

    @property
    def conv(self):
        if self.click:
            return self.paycount * 100.0 / self.click
        return 0.00

    @property
    def ctr(self):
        if self.click and self.impressions:
            return self.click * 100.0 / self.impressions
        return 0.00

    @property
    def cpc(self):
        if self.click:
            return float(self.cost) / self.click
        return 0

    @property
    def fav_roi(self):
        if self.favitemcount and self.click:
            return float(self.favitemcount) / self.click
        return 0.00

    @property
    def profit(self):
        return self.pay - self.cost

    @property
    def favctr(self):
        if self.click:
            return self.favcount * 100.0 / self.click
        return 0.00

    @property
    def favpay(self):
        if self.favcount:
            return self.cost / (self.favcount * 100.0)
        return 0.00

    @property
    def pay_cost(self):
        if self.paycount:
            return float(self.cost) / self.paycount
        return 0.00

    @property
    def avg_pay(self):
        if self.paycount:
            return float(self.pay) / self.paycount
        return 0.00

    def to_dict(self):
        return {
            'impr': self.impressions,
            'cost': fen2yuan(self.cost),
            'click': self.click,
            'ctr': '%.2f' % self.ctr,
            'cpc': fen2yuan(self.cpc),
            'pay': fen2yuan(self.pay),
            'directpay': fen2yuan(self.directpay),
            'indirectpay': fen2yuan(self.indirectpay),
            'paycount': self.paycount,
            'directpaycount': self.directpaycount,
            'indirectpaycount': self.indirectpaycount,
            'favcount': self.favcount,
            'favshopcount': self.favshopcount,
            'favitemcount': self.favitemcount,
            'roi': '%.2f' % self.roi,
            'conv': '%.2f' % self.conv,
            'carttotal': self.carttotal,
            'pay_cost': fen2yuan(self.pay_cost),
            'avg_pay': fen2yuan(self.avg_pay)
        }


class ReportDictWrapper(DictWrapper, BaseRptProperty):
    """用于对字典方法取数据，并且继承了上面的属性类"""

    KEY_LIST = ['impressions', 'click', 'cost', 'directpay', 'indirectpay', 'aclick',
                'directpaycount', 'indirectpaycount', 'favitemcount', 'favshopcount',
                'carttotal']

    def __add__(self, other): # 重载报表相加算法
        new_rpt = self.__class__()
        for key in self.KEY_LIST:
            setattr(new_rpt, key, getattr(self, key, 0) + getattr(other, key, 0))
        return new_rpt

    @classmethod
    def sum_rpt_list(cls, rpt_list):
        if not rpt_list:
            return PureReport()
        return reduce(cls.__add__, rpt_list)


class BaseReport(Document, BaseRptProperty):
    SOURCE_TYPE_CHOICES = ((-1, '汇总'), (1, '站内'), (2, '站外'), (4, '无线站内'), (5, '无线站外'), (6, '未知'), (11, '计算机'), (12, '移动端'))
    SEARCH_TYPE_CHOICES = ((-1, '汇总'), (0, '搜索'), (2, '定向'), (3, '店铺推广'), (4, '未知')) # 1是类目已经取消

    date = DateTimeField(verbose_name = "报表日期", required = True)
    search_type = IntField(verbose_name = "报表类型", default = 3, choices = SEARCH_TYPE_CHOICES)
    source = IntField(verbose_name = "数据来源", default = 3, choices = SOURCE_TYPE_CHOICES)
    # 基础数据
    impressions = IntField(verbose_name = "展现量", default = 0)
    click = IntField(verbose_name = "点击量", default = 0)
    cost = IntField(verbose_name = "总花费", default = 0)
    avgpos = IntField(verbose_name = "平均展现排名", default = 0) # 不一定有
    aclick = IntField(verbose_name = "点击量", default = 0)
    # 效果数据
    directpay = IntField(verbose_name = "直接成交金额", default = 0)
    indirectpay = IntField(verbose_name = "间接成交金额", default = 0)
    directpaycount = IntField(verbose_name = "直接成交笔数", default = 0)
    indirectpaycount = IntField(verbose_name = "间接成交笔数", default = 0)
    favitemcount = IntField(verbose_name = "宝贝收藏数", default = 0)
    favshopcount = IntField(verbose_name = "店铺收藏数", default = 0)
    carttotal = IntField(verbose_name = "购物车总数", default = 0)

    meta = {'abstract': True, 'indexes': ['date']}

    base_keys = ('impressions', 'click', 'cost', 'avgpos', 'aclick') # 报表基础属性
    effect_keys = ('directpay', 'indirectpay', 'directpaycount', 'indirectpaycount', 'favitemcount', 'favshopcount', 'carttotal') # 报表效果属性

    REPORT_CFG = (('SUMMARY', 'SUMMARY')) # 保存报表的下载配置，格式为[('search_type', 'source'), ...]
    IDENTITY = '' # 用于取报表的分组依据，子类必须要写清楚
    RESERVED_DAYS = 30 # 报表的保留天数
    INIT_DAYS = 90 # 初始化报表时，下载的报表天数

    @staticmethod
    def parse_source(top_obj):
        source = getattr(top_obj, 'source', 'SUMMARY')
        if source == 'SUMMARY':
            return -1
        elif source == 'SEARCH':
            return 0
        elif isinstance(source, int):
            return source
        else:
            try: # 异步下载会是字符串类型的，尝试强转一下
                return int(source)
            except ValueError:
                return 6

    @staticmethod
    def parse_search_type(top_obj):
        search_type = getattr(top_obj, 'search_type', 'SUMMARY')
        if search_type == 'SUMMARY':
            return -1
        elif search_type == 'SEARCH':
            return 0
        elif isinstance(search_type, int):
            return search_type
        else:
            return 4

    @classmethod
    def parse_rpt(cls, top_obj, rpt_type = "base"):
        """
        effect-sample --> 20150916
        {
            'favitemcount': u'77',
            'favshopcount': u'7',
            'directpay': u'24200',
            'source': u'SUMMARY',
            'indirectpay': u'111485',
            'nick': u'\u53ed\u53ed\u54d2\u54d2',
            'indirectcarttotal': u'82',
            'indirectpaycount': u'14',
            'date': u'2015-09-09',
            'carttotal': u'144',
            'directpaycount': u'4',
            'directcarttotal': u'62'
        }

        base-sample --> 20150916
        {
            'aclick': u'982',
            'cpm': u'662.24',
            'ctr': u'0.69',
            'nick': u'\u53ed\u53ed\u54d2\u54d2',
            'cpc': u'96.10',
            'source': u'SUMMARY',
            'cost': u'94368',
            'date': u'2015-09-15',
            'impressions': u'142499',
            'click': u'982'
        }
        """
        rpt_dict = {key: int(float(getattr(top_obj, key, 0))) or 0 for key in getattr(cls, "%s_keys" % rpt_type)}
        rpt_dict.update({'date': top_obj.date, 'source': cls.parse_source(top_obj), 'search_type': cls.parse_search_type(top_obj)})
        return {'%s_%s_%s' % (top_obj.date, rpt_dict['search_type'],  rpt_dict['source']): rpt_dict}

    @classmethod
    def merge_rpt_dict(cls, base_rpt_dict, effect_rpt_dict, extra_dict):
        default_effect = {k: getattr(cls, k).default for k in cls.effect_keys}
        result_list = []
        for key, base in base_rpt_dict.items():
            tmp_dict = extra_dict.copy()
            tmp_dict.update(base)
            tmp_dict.update(effect_rpt_dict.get(key, default_effect))
            tmp_dict.update({'date': datetime.datetime.strptime(base['date'], '%Y-%m-%d')})
            result_list.append(tmp_dict)
            del tmp_dict
        # result_list.sort(cmp = lambda x, y:cmp(x['date'], y['date']))
        return result_list

    @classmethod
    def get_snap_list(cls, query_dict, rpt_days = None, start_date = None, end_date = None, source = -1, search_type = -1):
        """
        :argument
            query_dict 查询条件
            rpt_days 报表天数 与下面的只用选择其一即可
            start_date 起始日期 字符串，形如'2015-10-12'
            end_date 结束日期 字符串，形如'2015-10-12'
            search_type 报表分类，目前可选(-1, 0, 2) 分别代表(汇总、搜索、定向)，这里也可以写query格式，如 {'$in': [0,2]}
            source 报表来源，可选(-1,1,2,4,5) 分别代表(汇总、PC站内、PC站外、移动站内、移动站外)，格式也同上
        :return
            {4258150:{'date':'2015-09-30', 'impressions': 300}}
        """
        result_dict = collections.defaultdict(list)
        base_query = {'source': source, 'search_type': search_type }
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
        cursor = cls._get_collection().find(base_query).sort([('date', 1)])
        for i in cursor:
            result_dict[i[cls.IDENTITY]].append(ReportDictWrapper(i))
        return result_dict

    @classmethod
    def aggregate_rpt(cls, query_dict, group_keys, rpt_days = None, start_date = None, end_date = None, source = -1, search_type = -1):
        """
        :argument
            query_dict 查询条件
            group_keys 类似mysql的group by字段，即分组的键，形如'adgroup_id,source,search_type'
            rpt_days 报表天数 与下面的只用选择其一即可
            start_date 起始日期 字符串，形如'2015-10-12'
            end_date 结束日期 字符串，形如'2015-10-12'
            search_type 报表分类，目前可选(-1, 0, 2) 分别代表(汇总、搜索、定向)，这里也可以写query格式，如 {'$in': [0,2]}
            source 报表来源，可选(-1,1,2,4,5) 分别代表(汇总、PC站内、PC站外、移动站内、移动站外)，格式也同上
        :return
            [{'_id':{group_key1: <value>, group_key2: <value>}, 'click': 200}]
        """
        base_query = {'source': source, 'search_type': search_type }
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
        group_key_dict = {key.strip(): '$%s' % key.strip() for key in group_keys.split(",")}
        pipeline = [{'$match': base_query},
                    {'$group': {'_id': group_key_dict,
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
                                'rpt_days': {'$sum': 1}
                                }
                     },
                    ]
        result = cls._get_collection().aggregate(pipeline)
        if result['ok']:
            return result['result']
        else:
            log.error("get_summed_detail_rpt error, result=%s" % result)
        return []

    @classmethod
    def get_summed_rpt(cls, query_dict, rpt_days = None, start_date = None, end_date = None, source = -1, search_type = -1):
        """aggregate_rpt的常用版
        :argument
            query_dict 查询条件
            rpt_days 报表天数 与下面的只用选择其一即可
            start_date 起始日期 字符串，形如'2015-10-12'
            end_date 结束日期 字符串，形如'2015-10-12'
            source 报表来源，默认给汇总
            search_type 报表类型，默认给汇总
        :return
            {<IDENTITY>: {'impressions':200, 'click': 20}} IDENTITY即定义的每个报表的结构主键
        """
        result_dict = {}
        result_list = cls.aggregate_rpt(query_dict, cls.IDENTITY, rpt_days, start_date, end_date, source, search_type)
        for result in result_list:
            temp_key = result.pop('_id')
            result_dict.update({temp_key[cls.IDENTITY]: ReportDictWrapper(result)})
        return result_dict

    @classmethod
    def get_platform_summed_rpt(cls, query_dict, rpt_days = None, start_date = None, end_date = None, platform = -1):
        platform_source_map = {-1: (-1, -1), 0: (12, 0), 1: (11, 0)}
        source, search_type = platform_source_map[platform]
        return cls.get_summed_rpt(query_dict = query_dict, rpt_days = rpt_days, start_date = start_date, end_date = end_date, source = source, search_type = search_type)

    @classmethod
    def get_split_rpt(cls, query_dict, group_keys, rpt_days = None, start_date = None, end_date = None, source = -1, search_type = -1):
        """aggregate_rpt的常用版
        :argument
            query_dict 查询条件
            rpt_days 报表天数 与下面的只用选择其一即可
            start_date 起始日期 字符串，形如'2015-10-12'
            end_date 结束日期 字符串，形如'2015-10-12'
            source 报表来源，默认给汇总
            search_type 报表类型，默认给汇总
        :return
            {<IDENTITY>: {'impressions':200, 'click': 20}} IDENTITY即定义的每个报表的结构主键
        """
        result_list = []
        temp_list = cls.aggregate_rpt(query_dict, group_keys, rpt_days, start_date, end_date, source, search_type)
        for result in temp_list:
            # temp_key = result['_id'][cls.IDENTITY]
            # source = result['_id']['source']
            # result.pop('_id')
            _id = result.pop('_id')
            temp_result = ReportDictWrapper(result)
            # temp_result['source'] = source
            # temp_result[cls.IDENTITY] = temp_key
            temp_result.update(_id)
            result_list.append(temp_result)
        return result_list

    @classmethod
    def update_rpt_list(cls, remove_query, insert_list):
        """更新报表，更新前先删除当前条件下的，以免重复"""
        coll = cls._get_collection()
        coll.remove(remove_query)
        return coll.insert(insert_list)

    @classmethod
    def clean_outdated(cls):
        """清除过期数据"""
        cls._get_collection().remove({'date': {'$lte': datetime.datetime.now() - datetime.timedelta(days = cls.RESERVED_DAYS)}})
        return True


class PureReport(BaseReport):
    KEY_LIST = ['impressions', 'click', 'cost', 'directpay', 'indirectpay', 'aclick',
                'directpaycount', 'indirectpaycount', 'favitemcount', 'favshopcount',
                'carttotal']
    """纯报表字段。"""
    def __add__(self, other): # 重载报表相加算法
        new_rpt = self.__class__()
        for key in self.KEY_LIST:
            setattr(new_rpt, key, getattr(self, key, 0) + getattr(other, key, 0))
        return new_rpt


class AccountRpt(BaseReport):

    shop_id = IntField(verbose_name = "店铺ID")

    meta = {'collection': 'account_report', "shard_key":('shop_id',)}

    # REPORT_CFG = (('SUMMARY', 'SUMMARY'),) # 保存报表的下载配置，格式为[('search_type', 'source'), ...]
    REPORT_CFG = (('', 'SUMMARY'), ('', '1,2,4,5')) # 保存报表的下载配置，格式为[('search_type', 'source'), ...]
    IDENTITY = "shop_id"
    RESERVED_DAYS = 90 # 清除数据时的报表保留天数
    INIT_DAYS = 30 # 初始化报表时，下载的报表天数


class CampaignRpt(BaseReport):

    shop_id = IntField(verbose_name = "店铺ID")
    campaign_id = IntField(verbose_name = "计划ID")

    meta = {'collection': 'campaign_report', 'indexes': ['campaign_id'], "shard_key":('shop_id',)}

    # REPORT_CFG = (('SUMMARY', 'SUMMARY'),)
    REPORT_CFG = (('SUMMARY', 'SUMMARY'), ('SEARCH,NOSEARCH', '1,2,4,5')) # 保存报表的下载配置，格式为[('search_type', 'source'), ...]
    IDENTITY = "campaign_id"
    RESERVED_DAYS = 90
    INIT_DAYS = 30


class AdgroupRpt(BaseReport):

    shop_id = IntField(verbose_name = "店铺ID")
    campaign_id = IntField(verbose_name = "计划ID")
    adgroup_id = IntField(verbose_name = "推广组ID")

    meta = {'collection': 'adgroup_report', 'indexes': ['campaign_id', 'adgroup_id'], "shard_key":('shop_id',)}

    # REPORT_CFG = (('SUMMARY', 'SUMMARY'), ('NOSEARCH', 'SUMMARY'))
    REPORT_CFG = (('SUMMARY', 'SUMMARY'), ('SEARCH,NOSEARCH', '1,2,4,5'))
    IDENTITY = "adgroup_id"
    RESERVED_DAYS = 90
    INIT_DAYS = 15


class CreativeRpt(BaseReport):

    shop_id = IntField(verbose_name = "店铺ID")
    campaign_id = IntField(verbose_name = "计划ID")
    adgroup_id = IntField(verbose_name = "推广组ID")
    creative_id = IntField(verbose_name = "创意ID")

    meta = {'collection': 'creative_report', 'indexes': ['campaign_id', 'adgroup_id', 'creative_id'], "shard_key":('shop_id',)}

    # REPORT_CFG = (('SUMMARY', 'SUMMARY'), ('SEARCH,NOSEARCH', '1,2,4,5'))
    REPORT_CFG = (('SUMMARY', 'SUMMARY'),)
    IDENTITY = "creative_id"
    RESERVED_DAYS = 30
    INIT_DAYS = 15


class KeywordRpt(BaseReport):

    shop_id = IntField(verbose_name = "店铺ID")
    campaign_id = IntField(verbose_name = "计划ID") # TODO: wangqi 20150918 这里是否需要保存shop_id与campaign_id，因为实际应用中应用较少？
    adgroup_id = IntField(verbose_name = "推广组ID")
    keyword_id = IntField(verbose_name = "关键词ID")

    meta = {'db_alias': 'keyword-db', 'collection': 'keyword_report', 'indexes': ['shop_id', 'campaign_id', 'keyword_id'], "shard_key":('adgroup_id',)}

    REPORT_CFG = (('SUMMARY', 'SUMMARY'), ('SEARCH', '1,2,4,5'))
    # REPORT_CFG = (('SUMMARY', 'SUMMARY'),)
    IDENTITY = "keyword_id"
    RESERVED_DAYS = 30
    INIT_DAYS = 15


    @classmethod
    def download_kwrpt_base(cls, shop_id, campaign_id, adgroup_id, token, start_time, end_time, search_type, source, tapi):
        """下载base报表"""
        page_size = 200
        page_no = 1
        base_list = []
        while(True):
            try:
                top_base_objs = tapi.simba_rpt_adgroupkeywordbase_get(campaign_id = campaign_id, adgroup_id = adgroup_id,
                                                                    start_time = start_time, end_time = end_time,
                                                                    search_type = search_type, source = source, subway_token = token,
                                                                    page_no = page_no, page_size = page_size,
                                                                    retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
            except TopError, e:
                log.error('simba_rpt_adgroupkeywordbase_get TopError, shop_id=%s, adgroup_id=%s, start_time=%s, end_time=%s, e=%s' % (shop_id, adgroup_id, start_time, end_time, e))
                raise e

            if top_base_objs and hasattr(top_base_objs, 'rpt_adgroupkeyword_base_list') and top_base_objs.rpt_adgroupkeyword_base_list:
                base_list.extend(top_base_objs.rpt_adgroupkeyword_base_list)
                if len(top_base_objs.rpt_adgroupkeyword_base_list) < page_size:
                    break
                page_no += 1
            else:
                break

        return base_list

    @classmethod
    def download_kwrpt_effect(cls, shop_id, campaign_id, adgroup_id, token, start_time, end_time, search_type, source, tapi):
        """下载effect报表"""
        page_no = 1
        page_size = 200
        effect_list = []
        while(True):
            try:
                top_effect_objs = tapi.simba_rpt_adgroupkeywordeffect_get(campaign_id = campaign_id, adgroup_id = adgroup_id,
                                                                    start_time = start_time, end_time = end_time,
                                                                    search_type = search_type, source = source, subway_token = token,
                                                                    page_no = page_no, page_size = page_size,
                                                                    retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
            except TopError, e:
                log.error('simba_rpt_adgroupkeywordeffect_get TopError, shop_id=%s, adgroup_id=%s, start_time=%s, end_time=%s, e=%s' % (shop_id, adgroup_id, start_time, end_time, e))
                raise e

            if top_effect_objs and hasattr(top_effect_objs, 'rpt_adgroupkeyword_effect_list') and top_effect_objs.rpt_adgroupkeyword_effect_list:
                effect_list.extend(top_effect_objs.rpt_adgroupkeyword_effect_list)
                if len(top_effect_objs.rpt_adgroupkeyword_effect_list) < page_size:
                    break
                page_no += 1
            else:
                break

        return effect_list

    @classmethod
    def merge_kwrpt(cls, shop_id, campaign_id, adgroup_id, base_list, effect_list):
        """合并base与effect报表"""
        rpt_list = []
        if base_list:
            base_dict, effect_dict = collections.defaultdict(dict), collections.defaultdict(dict)
            for base_rpt in base_list:
                base_dict[base_rpt.keyword_id].update(cls.parse_rpt(base_rpt, 'base'))

            for effect_rpt in effect_list:
                effect_dict[effect_rpt.keyword_id].update(cls.parse_rpt(effect_rpt, 'effect'))

            for kw_id, base_rpt_dict in base_dict.items():
                rpt_list.extend(cls.merge_rpt_dict(base_rpt_dict, effect_dict.get(kw_id, {}), {'shop_id': shop_id, 'campaign_id': campaign_id, 'adgroup_id':adgroup_id, 'keyword_id':kw_id}))

        return rpt_list


    @classmethod
    def insert_rpt_list(cls, shop_id, end_date, adg_date_dict, rpt_list):
        coll = cls._get_collection()

        bulk = coll.initialize_unordered_bulk_op()
        for adgroup_id, last_sync_time in adg_date_dict.items():
            bulk.find({'shop_id': shop_id, 'adgroup_id': adgroup_id,
                       'date': {'$lte':date_2datetime(end_date), '$gte':date_2datetime(last_sync_time)}}).remove()
        try:
            bulk.execute()
        except BulkWriteError as e:
            log.error("bulk remove keyword rpt error, e=%s" % e)

        # 这里可能还需要再作转义？将每个keyword的数据拆分成三份？
        coll.insert(rpt_list)

    @classmethod
    def simply_rpt(cls, rpt_list):
        result_dict = collections.defaultdict(list)
        conv_dict = {-1: -1, 1: 11, 2: 11, 4: 12, 5: 12}
        key_list = cls.base_keys + cls.effect_keys
        for temp_dict in rpt_list:
            k = '%s_%s_%s_%s' % (temp_dict['keyword_id'], temp_dict['date'], temp_dict['search_type'], conv_dict[temp_dict['source']])
            result_dict[k].append(temp_dict)
        result_list = []
        for k, r_list in result_dict.iteritems():
            source = int(k.split('_')[-1])
            new_rpt_dict = r_list.pop(0)
            new_rpt_dict['source'] = source
            for rpt_dict in r_list:
                for k in key_list:
                    new_rpt_dict[k] += rpt_dict[k]
            new_rpt_dict['avgpos'] = new_rpt_dict['avgpos'] / (len(r_list)+1)
            result_list.append(new_rpt_dict)
        return result_list

acctrpt_coll = AccountRpt._get_collection() # 不建议直接引用
camprpt_coll = CampaignRpt._get_collection()
adgrpt_coll = AdgroupRpt._get_collection()
crtrpt_coll = CreativeRpt._get_collection()
kwrpt_coll = KeywordRpt._get_collection()
