# coding=UTF-8
import json
import datetime

from mongoengine.fields import (StringField, IntField, ListField, FloatField,
                                EmbeddedDocumentField, DictField, DateTimeField)
from mongoengine.document import EmbeddedDocument, Document

from apps.common.constant import Const
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import date_2datetime
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.kwslt.base import (del_include_product_word, get_match_word,
                             get_match_attribut, get_catinfo_new, cat_data_list)


class CatStatic(Document):
    cat_id = IntField(verbose_name = '类目ID', required = True)
    rpt_date = DateTimeField(verbose_name = "报表日期", required = True)
    impression = IntField(verbose_name = '单个类目下所有的impression', default = 0)
    click = IntField(verbose_name = '单个类目下所有的click', default = 0)
    cost = IntField(verbose_name = '单个类目下所有的cost单位（分）', default = 0)
    directtransaction = IntField(verbose_name = '直接成交金额', default = 0)
    indirecttransaction = IntField(verbose_name = '间接成交金额', default = 0)
    directtransactionshipping = IntField(verbose_name = '直接成交笔数', default = 0)
    indirecttransactionshipping = IntField(verbose_name = '间接成交笔数', default = 0)
    favitemtotal = IntField(verbose_name = '宝贝收藏数', default = 0)
    favshoptotal = IntField(verbose_name = '店铺收藏数', default = 0)
    transactionshippingtotal = IntField(verbose_name = '总的成交笔数', default = 0)
    transactiontotal = IntField(verbose_name = '成交总金额', default = 0)
    favtotal = IntField(verbose_name = '总的收藏数，包括宝贝收藏和店铺收藏', default = 0)
    competition = IntField(verbose_name = '竞争度', default = 0)
    ctr = FloatField(verbose_name = '点击率', default = 0)
    cpc = FloatField(verbose_name = '平均点击花费（分）', default = 0)
    roi = FloatField(verbose_name = '投入产出比', default = 0)
    coverage = FloatField(verbose_name = '点击转化率', default = 0)

    meta = {'collection':"kwlib_catstatic", "db_alias": "kwlib-db", 'indexes':['cat_id', 'rpt_date'], "shard_key":('rpt_date',)}

    rpt_field_dict = {'impression': int, 'click': int, 'cost': int, 'directtransaction': int,
                      'indirecttransaction': int, 'directtransactionshipping': int,
                      'indirecttransactionshipping': int, 'favitemtotal': int,
                      'favshoptotal': int, 'transactionshippingtotal': int, 'transactiontotal': int,
                      'favtotal': int, 'competition': int, 'ctr': float, 'cpc': float,
                      'roi': float, 'coverage': float
                      }

    @classmethod
    def update_cat_market_data(cls, cat_id_list = [], rpt_date = None):
        """
        .更新类目下的大盘数据
        """
        log.info('skip update cat market_data')
        return True
        if not rpt_date:
            rpt_date = datetime.date.today() - datetime.timedelta(days = 1)
        if not cat_id_list:
            cat_cur = cat_coll.find({}, {'_id'})
            cat_id_list = [cat['_id'] for cat in cat_cur]

        rpt_date_str = datetime.datetime.strftime(rpt_date, '%Y-%m-%d')
        new_rpt_date = datetime.datetime.strptime(rpt_date_str, '%Y-%m-%d') # 数据库中不能存 date 类型
        result_dict = cat_data_list(cat_id_list, rpt_date_str, rpt_date_str)
        insert_list = []

        for cat_id, cat_data in result_dict.iteritems():
            cat_dict = {'cat_id': cat_id, 'rpt_date': new_rpt_date}
            for rpt_field, func in cls.rpt_field_dict.iteritems():
                cat_dict[rpt_field] = func(getattr(cat_data, rpt_field, 0)) # 注意单位转换
            insert_list.append(cat_dict)

        cat_static_coll.remove({'rpt_date': new_rpt_date, 'cat_id': {'$in': cat_id_list}})
        cat_static_coll.insert(insert_list)
        log.info('update cat market, cat_count=%s' % len(insert_list))
        return

    @classmethod
    def __get_rpt_list_8id(cls, cat_id):
        cachekey = CacheKey.KWLIB_CAT_STATIC_RPT % cat_id
        cat_data_list = CacheAdpter.get(cachekey, 'web', None)
        if cat_data_list is None: # 不能简写为 if not cat_data_list: 因为有可能 缓存中有值，但为 []
            rpt_day = 15
            now = datetime.datetime.now()

            # 淘宝接口下线维护，这里临时使用旧数据
            rpt_day = 7
            now = datetime.datetime(2017, 3, 12)

            start_date = date_2datetime(now - datetime.timedelta(days = rpt_day))
            objs = cls.objects.filter(cat_id = cat_id, rpt_date__gte = start_date).order_by('rpt_date')
            cat_data_list = [obj for obj in objs]
            # 缓存在第二天7点过期，因为此时数据库中已刷新昨日数据
            timeout = (date_2datetime(now) + datetime.timedelta(days = 1, hours = 7) - now).seconds
            CacheAdpter.set(cachekey, cat_data_list, 'web', timeout)
        return cat_data_list

    @classmethod
    def get_rpt_list_8id(cls, cat_id, rpt_days = 15):
        if rpt_days > 15: # 此接口为常用接口，限制在15天内
            rpt_days = 15

        rpt_list = cls.__get_rpt_list_8id(cat_id)
        return rpt_list # 淘宝接口下线维护，这里临时使用旧数据
        # start_date = date_2datetime(datetime.datetime.now() - datetime.timedelta(days = rpt_days))
        # result_list = [rpt for rpt in rpt_list if rpt.rpt_date >= start_date]
        # return result_list

    @classmethod
    def get_market_data_8id(cls, cat_id, rpt_days = 7):
        result_dict = {rf:0 for rf in cls.rpt_field_dict.iterkeys()}
        rpt_list = cls.get_rpt_list_8id(cat_id, rpt_days)
        for rpt in rpt_list:
            for k in result_dict.iterkeys():
                result_dict[k] += getattr(rpt, k, 0)
        if rpt_list:
            result_dict = {k: round(v / len(rpt_list), 2) for k, v in result_dict.iteritems()} # 取平均值
        return result_dict

    @classmethod
    def get_market_data(cls, cat_id_list, tj_day = 7):
        result_dict = {}
        for cat_id in cat_id_list:
            result_dict[cat_id] = cls.get_market_data_8id(cat_id, tj_day)
        return result_dict

cat_static_coll = CatStatic._get_collection()


class BrandWord(EmbeddedDocument):
    """品牌词"""
    word = StringField(verbose_name = "关键词", max_length = 100)

    @staticmethod
    def get_brandword_list(cat_id):
        syno_list, tmp_list = [], []
        try:
            brand_list = Cat.get_attr_by_cat(cat_id, "brand_list")
            brand_list = brand_list or []
            for brand in brand_list:
                if '/' in brand.word:
                    word_list = [w for w in brand.word.split('/') if w]
                    syno_list.append(word_list)
                    tmp_list.extend(word_list)
                else:
                    tmp_list.append(brand.word)
            syno_dict = {word:t_list for t_list in syno_list for word in t_list}
        except Exception, e:
            log.error("get brank list error and the error is = %s" % e)
        return tmp_list, syno_dict

    @staticmethod
    def get_related_word(word_list, all_word):
        related_list = []
        try:
            related_list = [x for x in all_word for y in word_list if (x in y) or (y in x)]
        except Exception, e:
            log.error("get_related_word error and the error = %s " % e)
        return list(set(word_list) | set(related_list))

    @staticmethod
    def get_syno_brand(word_list, syno_dict):
        syno_list = []
        try:
            for word in word_list:
                syno_list.extend(syno_dict.get(word, []))
        except Exception, e:
            log.error("get syno brand error and the error is = %s" % e)
        return list(set(word_list) | set(syno_list))

    @classmethod
    def get_extend_brand(cls, word_list, cat_id):
        top_cat_id = Cat.get_cat_attr_func(cat_id, 'root_cat_id')
        all_brand, syno_dict = cls.get_brandword_list(top_cat_id)
        word_list = cls.get_related_word(word_list, all_brand)
        word_list = cls.get_syno_brand(word_list, syno_dict)
        return word_list, [word for word in all_brand]

    @classmethod
    def get_brand_list(cls, cat_id, brandword_list):
        extend_brand, all_brand = BrandWord.get_extend_brand(brandword_list, cat_id)
        return list(set(all_brand) - set(extend_brand))

class MetaphorWord(EmbeddedDocument):
    match = StringField(verbose_name = '隐喻匹配词')
    metaphor = StringField(verbose_name = '隐喻词')

    @staticmethod
    def get_metaword_list(cat_id, word_list):
        '''
        .获取单个宝贝的隐喻词
        '''
        result_list = []
        try:
            cat_id_list = Cat.get_attr_by_cat(cat_id, "cat_path_id").split(' ') + [0]
            for cat_id in cat_id_list:
                for meta in Cat.get_attr_by_cat(cat_id, "meta_list"):
                    if meta.match in word_list:
                        result_list.extend(meta.metaphor.split(','))
        except Exception, e:
            log.error("get metaword list error and the error is = %s" % e)
        return result_list

class ForbidWord(EmbeddedDocument):
    word = StringField(verbose_name = '违禁词')
    type = IntField(verbose_name = '违禁词类型,1为C店违规,2为BC店都违规', default = 2)

    @staticmethod
    def get_all_forbid_list(cat_id):
        '''
        .获取单个类目的违禁词列表
        '''
        fobid_list = []
        try:
            cat_id_list = Cat.get_attr_by_cat(cat_id, "cat_path_id").split(' ') + [0]
            for cat_id in cat_id_list:
                fobid_list.extend([fbd.word for fbd in Cat.get_attr_by_cat(cat_id, "forbid_list")])
        except Exception, e:
            log.error("get forbid list error and the error = %s" % e)
        return fobid_list

class IncludeWord(EmbeddedDocument):
    include = StringField(verbose_name = '包含词')
    exclude = ListField(verbose_name = '互斥词')

    @staticmethod
    def get_include_list(word_list, cat_id, cat = None):
        '''
        .获取单个宝贝的互斥词列表
        '''
        include_list = []
        try:
            str_word_list = ','.join(word_list)
            cat_id_list = Cat.get_attr_by_cat(cat_id, "cat_path_id").split() + [0]
            for cat_id in cat_id_list:
                for include in Cat.get_attr_by_cat(cat_id, "exclude_list"):
                    in_ex_clude = True
                    if include.include in word_list or include.include in str_word_list:
                        for exclude in include.exclude:
                            if exclude in word_list or exclude in str_word_list:
                                in_ex_clude = False
                        if in_ex_clude:
                            include_list.extend(include.exclude)
        except Exception, e:
            log.error("get include list error and the error = %s" % e)
        return list(set(include_list))

class ProductWord(EmbeddedDocument):
    '''
    .产品词
    '''
    match = StringField(verbose_name = '产品匹配词')
    product = StringField(verbose_name = '产品确定词')

    @staticmethod
    def get_prdt_list(word_list, cat_id):
        '''
        .获取单个宝贝的产品词列表
        '''
        product_words, parents = set(), set()
        try:
            cur_conf = None # 当前类目使用的产品词规则
            cat_name_list = []
            cat_id_list = Cat.get_attr_by_cat(cat_id, "cat_path_id").split(' ')
            for c_id in cat_id_list:
                temp_conf = Cat.get_attr_by_cat(c_id, "product_dict")
                cat_name = Cat.get_attr_by_cat(c_id, "cat_name")
                cat_name_list.append(cat_name)
                if not temp_conf:
                    continue
                cur_conf = temp_conf
                if cat_id != int(float(c_id)) and temp_conf.product: # 获取父类目确定产品词
                    tmp_list = temp_conf.product.split(',')
                    parents.update(tmp_list)

            parents = [kw.lower() for kw in del_include_product_word(cat_name_list, parents)]

            # 获取当前类目匹配词
            if cur_conf:
                if cur_conf.product:
                    tmp_list = cur_conf.product.split(',')
                    product_words.update(tmp_list)
                if cur_conf.match:
                    tmp_list = get_match_word(cur_conf.match.split(','), word_list)
                    product_words.update(tmp_list)
        except Exception, e:
            log.error("get prdt list error, e = %s" % e)
        return sorted([kw.lower() for kw in product_words], reverse = True), sorted(parents, reverse = True)

    # 获取名词前的定语
    @staticmethod
    def get_decorate_from_nouns(cat_id, word_list):
        result_list = []
        try:
            root_cat_id = Cat.get_cat_attr_func(cat_id, "root_cat_id")
            p_conf = Cat.get_attr_by_cat(root_cat_id, "product_dict")
            if not p_conf:
                return result_list
            rule_list = p_conf.match and p_conf.match.split(',') or []
            result_list = get_match_attribut(rule_list, word_list)
        except Exception, e:
            log.error("get_decorate_from_nouns error and the error = %s" % e)
        return result_list

class SaleWord(EmbeddedDocument):
    match = StringField(verbose_name = '卖点匹配词')
    sale = StringField(verbose_name = '卖点确定词')

    @staticmethod
    def get_sale_list(word_list, cat_id):
        '''
        .获取单个宝贝的卖点词列表
        '''
        tmp_list = []
        try:
            sale = Cat.get_attr_by_cat(cat_id, "sale_dict")
            if sale:
                tmp_list = get_match_word(sale.match and sale.match.split(',') or [], word_list)
                if sale.sale:
                    tmp_list.extend(sale.sale.split(','))
        except Exception, e:
            log.error("get sale list error and the error = %s" % e)
        return list(set(tmp_list))

class DanagerInfo(EmbeddedDocument):
    danger_type = StringField(verbose_name = "危险类目店铺类型，1为C店违规,2为BC店都违规",)
    danger_descr = StringField(verbose_name = "危险类目描述",)

    @classmethod
    def check_danger_cats(cls, cat_id_list):
        '''检测类目是否为危险类目'''
        result = {}
        try:
            cat_id_list = list(set(cat_id_list))
            for cat_id in cat_id_list:
                cat_id = unicode(cat_id)
                danger_info = Cat.get_attr_by_cat(cat_id, "danger_info")
                if danger_info and danger_info.danger_descr:
                    result[cat_id] = danger_info.danger_descr
        except Exception, e:
            log.error("check dangaer cats error and the error = %s" % e)
        return result

    @classmethod
    def get_dange_cat_list(cls):
        c_danger_dict, b_danger_dict = {}, {}
        try:
            for cat in cat_coll.find({'danger_info':{'$ne':{}}}, {'cat_id', 'danger_info'}):
                cat_id = cat['cat_id']
                if cat['danger_info']['danger_type'] == 2:
                    b_danger_dict[cat_id] = cat['danger_info']['danger_descr']
                c_danger_dict[cat_id] = cat['danger_info']['danger_descr']
        except Exception, e:
            log.error("get_dange_cat_list error and the error = %s" % e)
        return c_danger_dict, b_danger_dict

class PropProduct(EmbeddedDocument):
    match = StringField(verbose_name = "属性产品词模糊匹配")
    prop_prdt = StringField(verbose_name = "可确定属性产品词")

class Cat(Document):
    cat_id = IntField(verbose_name = "类目ID", primary_key = True)
    cat_name = StringField(verbose_name = "类目名称",)
    cat_level = IntField(verbose_name = '类目层级',)
    parent_cat_id = IntField(verbose_name = '父类目Id',)
    cat_path_id = StringField(verbose_name = '路径Id 即 父类目ids ',)
    cat_path_name = StringField(verbose_name = '路径名称 ',)
    last_sync_time = StringField(verbose_name = '最后更新时间',)
    brand_is_mutex = IntField(verbose_name = '最后更新时间', default = 0)
    cat_child_list = ListField(verbose_name = '当前类目的一级子类目')
    danger_info = EmbeddedDocumentField(DanagerInfo, verbose_name = '危险信息', default = None)
    product_dict = EmbeddedDocumentField(ProductWord, verbose_name = '类目下的产品词,包含：match_word,product_word', default = None)
    sale_dict = EmbeddedDocumentField(SaleWord, verbose_name = '类目下的卖点词,包含：match_word,sale_word', default = None)
    selectconf_dict = DictField(verbose_name = '类目下的选词配置名称,包含：长尾加词,长尾换词,精准,快选,重点加词,重点换词')
    brand_list = ListField(verbose_name = '类目下的品牌词', field = EmbeddedDocumentField(BrandWord), default = None)
    meta_list = ListField(verbose_name = '类目下的隐喻词', field = EmbeddedDocumentField(MetaphorWord), default = [])
    forbid_list = ListField(verbose_name = '类目下的违禁词', field = EmbeddedDocumentField(ForbidWord), default = [])
    exclude_list = ListField(verbose_name = '类目下的互斥词', field = EmbeddedDocumentField(IncludeWord), default = [])
    hot_prop_list = ListField(verbose_name = '类目下的热属性名称', default = [])
    prop_product_dict = EmbeddedDocumentField(PropProduct, verbose_name = '类目下的属性产品词', default = None)

    meta = {'collection':"kwlib_cat", "db_alias": "kwlib-db"}

    cat_path_dict = {}

    set_key_list = ['product_dict',
                    'brand_list',
                    'sale_dict',
                    'meta_list',
                    'forbid_list',
                    'cat_child_list',
                    'selectconf_dict',
                    "exclude_list",
                    "brand_is_mutex",
                    'prop_product_dict',
                    'hot_prop_list'
                    ]

    get_attr_func_dict = {'parent_cids':('get_parent_cids', ''),
                          'brand_is_mutex':('get_attr_by_cat', 'brand_is_mutex'),
                          'root_cat_id':('get_root_cat_id', ''),
                          'cat_path_name':('get_attr_by_cat', 'cat_path_name'),
                          'cat_name':('get_attr_by_cat', 'cat_name'),
                          'cat_path_id':('get_attr_by_cat', 'cat_path_id'),
                          'product_dict':('get_attr_by_cat', 'product_dict'),
                          'brand_list':('get_attr_by_cat', 'brand_list'),
                          'sale_dict':('get_attr_by_cat', 'sale_dict'),
                          'meta_list':('get_attr_by_cat', 'meta_list'),
                          'forbid_list':('get_attr_by_cat', 'forbid_list'),
                          'cat_child_list':('get_attr_by_cat', 'cat_child_list'),
                          'selectconf_dict':('get_attr_by_cat', 'selectconf_dict'),
                          'cat': ('get_single_cat', ''),
                          'danager_info':('danager_info', ''),
                          'exclude_list':('get_attr_by_cat', 'exclude_list')
                          }

    def save_single(self, attr = None, key = ''):
        if key:
            if key not in Cat.set_key_list:
                return False
            attr_key = CacheKey.KWLIB_CAT_ATTR % (self.cat_id, key)
            setattr(self, key, attr)
            CacheAdpter.set(attr_key, attr, 'web', Const.KWLIB_ATTRIBUT_CACHE_TIME)
        self.save()
        CacheAdpter.set(CacheKey.KWLIB_CAT_INFO % str(self.cat_id), self, 'web', Const.KWLIB_CAT_CACHE_TIME)
        return True

    def save_multi(self, **kwargs):
        for key in kwargs:
            attr_key = CacheKey.KWLIB_CAT_ATTR % (self.cat_id, key)
            attr = kwargs[key]
            setattr(self, key, attr)
            CacheAdpter.set(attr_key, attr, 'web', Const.KWLIB_ATTRIBUT_CACHE_TIME)
        self.save()
        CacheAdpter.set(CacheKey.KWLIB_CAT_INFO % str(self.cat_id), self, 'web', Const.KWLIB_CAT_CACHE_TIME)
        return True

    @classmethod
    def reload_cat_path_dict(cls):
        log.info('start load all cat path to dict')
        for cat in cat_coll.find({}, {'cat_path_name':1}):
            cls.cat_path_dict[cat['_id']] = cat['cat_path_name']

    @classmethod
    def get_cat_path_name(cls, cat_id_list):
        result_dict = {}
        if not cls.cat_path_dict:
            cls.reload_cat_path_dict()
        for cat_id in cat_id_list:
            cat_id = unicode(cat_id)
            try:
                if cat_id in cls.cat_path_dict:
                    result_dict[cat_id] = cls.cat_path_dict[cat_id]
                else:
                    cat = cat_coll.find({'_id':int(cat_id)})
                    if cat.count():
                        cat = cat[0]
                        cat_path_name = cat['cat_path_name']
                    else:
                        cat_path_name = '未收录此类目'
                    result_dict[cat_id] = cat_path_name
                    cls.cat_path_dict[cat_id] = cat_path_name
            except Exception, e:
                log.error('can not get cat path by cat_id , the error=%s and cat_id=%s' % (e, cat_id))
                result_dict[cat_id] = '未收录此类目'
                continue
        return result_dict

    @classmethod
    def save_and_reset(cls, cat_id, **kwargs):
        cat_id = int(float(cat_id))
        for key in kwargs.keys():
            if not (key in cls.set_key_list):
                return False
        cat_coll.update({'_id':cat_id}, {'$set':kwargs})
        cls.reload_single_cat_2memcache(cat_id)
        cls.reload_cat_by_field(cat_id, kwargs.keys())
        return True

    @classmethod
    def get_all_record_count(cls,):
        return cls.objects.count()

    @classmethod
    def compute_child_list(cls):
        for cat in cls.objects.all():
            cat_id = cat.cat_id
            if cat_id == -1:
                continue
            child_list = [cat.cat_id for cat in cls.objects.filter(parent_cat_id = cat_id)]
            cat_coll.update({'_id':cat_id}, {'$set':{'cat_child_list':child_list}})

    @classmethod
    def get_cat_from_db(cls, cat_id):
        cat_id = int(float(cat_id))
        cat = None
        try:
            cat = cls.objects.get(cat_id = cat_id)
        except Exception, e:
            log.info('can not get cat info from db and the error is = %s' % e)
        return cat

    @classmethod
    def get_catinfo(cls, cat_id):
        cat = None
        if cat_id != 0 and not cat_id:
            return cat

        try:
            str_cat_id = str(cat_id)
            cat = CacheAdpter.get(CacheKey.KWLIB_CAT_INFO % str_cat_id, 'web', None)
            if not cat:
                cat = cls.get_cat_from_db(cat_id)
                if not cat:
                    tmp = get_catinfo_new(1, category_id_list = [str_cat_id])
                    if tmp:
                        tmp = tmp[int(cat_id)]
                        tmp['_id'] = tmp.pop('cat_id')
                        temp_dict = {'cat_child_list':[], 'danager_info':{}, 'product_dict':{}, 'sale_dict':{}, 'selectconf_dict':{}, 'brand_list':[], 'meta_list':[], 'forbid_list':[], 'exclude_list':[]}
                        cat_coll.insert(dict(tmp), **temp_dict)
                        cat = cls.get_cat_from_db(cat_id)
                CacheAdpter.set(CacheKey.KWLIB_CAT_INFO % str_cat_id, cat, 'web', Const.KWLIB_CAT_CACHE_TIME)
        except Exception, e:
            log.error("get cat error , can not get the cat by cat_id = %s and the error = %s" % (cat_id, e))
        return cat

    @classmethod
    def load_all_cat_2memcache(cls):
        for cat in cls.objects.all():
            CacheAdpter.set(CacheKey.KWLIB_CAT_INFO % str(cat.cat_id), cat, 'web', Const.KWLIB_CAT_CACHE_TIME)

    @classmethod
    def reload_single_cat_2memcache(cls, cat_id):
        cat = cls.get_cat_from_db(cat_id)
        CacheAdpter.set(CacheKey.KWLIB_CAT_INFO % str(cat_id), cat, 'web')

    @classmethod
    def reload_cat_by_field(cls, cat_id, field_list):
        cat = None
        try:
            cat = cls.objects.only(*field_list).get(cat_id = cat_id)
        except Exception, e:
            log.error("can not get cat from db and the error = %s" % e)
        if cat:
            for key in field_list:
                attr_key = CacheKey.KWLIB_CAT_ATTR % (cat.cat_id, key)
                CacheAdpter.set(attr_key, getattr(cat, key), 'web', Const.KWLIB_ATTRIBUT_CACHE_TIME)
#                 set_stat = True
#                 set_count = 5
#                 while set_stat:
#                     if not set_count:
#                         break
#                     old_data = CacheAdpter.get(attr_key, 'web')
#                     CacheAdpter.set(attr_key, getattr(cat, key), 'web', Const.KWLIB_ATTRIBUT_CACHE_TIME)
#                     new_data = CacheAdpter.get(attr_key, 'web')
#                     if old_data == new_data:
#                         set_stat = True
#                     else:
#                         set_stat = False
#                     set_count -= 1
#                 if (not set_count) or set_stat:
#                     log.error('set cat cache failed and set key = %s and set field = %s' % (attr_key, key))

    @classmethod
    def get_cat_attr_func(cls, cat_id, attr_alias):
        try:
            func_name, attr = cls.get_attr_func_dict[attr_alias]
            if attr:
                return getattr(cls, func_name)(str(cat_id), attr)
            return getattr(cls, func_name)(str(cat_id))
        except Exception, e:
            log.error("can't get attributer by cat key, cat_id = %s, attr_alias = %s, e = %s" % (e, cat_id, attr_alias))
            return None

    @classmethod
    def get_cat_by_attr(cls, cat_id, field_list):
        cat = None
        try:
            cat = Cat.objects.only(*field_list).get(cat_id = cat_id)
            CacheAdpter.set(CacheKey.KWLIB_CAT_INFO % str(cat_id), cat, 'web', Const.KWLIB_CAT_CACHE_TIME)
        except Exception, e:
            log.error("can not get cat and the error is = %s" % e)
        return cat

    @classmethod
    def get_multi_cat_attr(cls, cat_id_list, field_list):
        result = {}
        for cat in Cat.objects.only(*field_list).filter(cat_id__in = cat_id_list):
            result[cat.cat_id] = cat
        return result

    @classmethod
    def get_single_cat(cls, cat_id):
        return cls.get_catinfo(cat_id)

    @classmethod
    def get_root_cat_id(cls, cat_id):
        return cls.get_attr_by_cat(cat_id, "cat_path_id").split(' ')[0] or []

    @classmethod
    def get_parent_cids(cls, cat_id):
        return cls.get_attr_by_cat(cat_id, "cat_path_id").split(' ')[:-1] or []

    @classmethod
    def get_multi_attr(cls, cat_id, *args):
        result = []
        for arg in args:
            result.append({arg:cls.get_attr_by_cat(cat_id, arg)})

    @classmethod
    def get_all_cat_name(cls):
        result_dict = {cat.cat_id:cat.cat_name for cat in Cat.objects.only('cat_id', 'cat_name').all()}
        del result_dict[0]
        return result_dict

    @classmethod
    def get_attr_by_cat(cls, cat_id, key):
        """
        /通过属性key来获取该类目下的属性,属性key如下所示
        cat_path_name,
        cat_path_id,
        cat_name,
        danager_info,
        product_dict,
        brand_list,
        sale_dict,
        meta_list,
        forbid_list,
        cat_child_list,
        selectconf_dict
        prop_product_dict,
        hot_prop_list
        """
        attr_key = CacheKey.KWLIB_CAT_ATTR % (cat_id, key)
        value = CacheAdpter.get(attr_key, 'web', '')
        if not value:
            cat = cls.get_catinfo(cat_id)
            if cat:
                value = getattr(cat, key) or ''
            if value:
                CacheAdpter.set(attr_key, value, 'web', Const.KWLIB_ATTRIBUT_CACHE_TIME)
        return value

    @classmethod
    def set_attr_to_cat(cls, cat_id, key, value):
        """
        /通过属性key和value来更新该类目下的的属性,key值如下所示:
        product_dict,
        brand_list,
        sale_dict,
        meta_list,
        forbid_list,
        cat_child_list,
        selectconf_dict
        prop_product_dict,
        hot_prop_list
        """
        if key not in cls.set_key_list:
            log.error("Please check key , it is very dangerous")
            return False
        cat_coll.update({'_id':cat_id}, {'$set':{key:value}})
        cls.reload_single_cat_2memcache(cat_id)
        CacheAdpter.set(CacheKey.KWLIB_CAT_ATTR % (cat_id, key), value, 'web', Const.KWLIB_ATTRIBUT_CACHE_TIME)
        return True

    @classmethod
    def clear_attr_by_cat(cls, cat_id):
        cls.reload_cat_by_field(cat_id, cls.set_key_list)

    @classmethod
    def update_embeded_array(cls, cat_id, field, old_dict, update_dict):
        """
        old_dict  为原来document内任一一个可以查询的参数 比如:forbid_list  [{'word':1,'type':2}]  old_dict={'word':1}  update_dict={'word':2,'type':1} field 字段
        """
        set_dict = {}
        query_dict = {}
        for key in old_dict:
            query_dict[field + '.' + key] = old_dict[key]
        query_dict['_id'] = cat_id
        for key in update_dict.keys():
            set_dict[field + '.$.' + key] = update_dict[key]
        try:
            cat_coll.update(query_dict, {'$set':set_dict})
        except Exception, e:
            log.error("can't update embeded document and the error = %s and the cat_id = %s" % (e, cat_id))
            return False
        cls.reload_single_cat_2memcache(cat_id)
        cls.reload_cat_by_field(cat_id, [field])
        return True

    @classmethod
    def delete_embeded_array(cls, cat_id, field, **kwargs):
        """
        **kwargs  =  (word=1,type=2)  {'word':1,'type':2}
        """
        del_dict = {field:kwargs}
        query_dict = {'_id':cat_id}
        try:
            cat_coll.update(query_dict, {'$pull':del_dict})
        except Exception, e:
            log.error("can't delete embeded document and the error = %s and the cat_id = %s" % (e, cat_id))
            return False
        cls.reload_single_cat_2memcache(cat_id)
        cls.reload_cat_by_field(cat_id, [field])
        return True

    @classmethod
    def add_embeded_array(cls, cat_id, field, **kwargs):
        query_dict = {'_id':cat_id}
        add_dict = {field:kwargs}
        try:
            cat_coll.update(query_dict, {'$push':add_dict})
        except Exception, e:
            log.error("can't add embeded document and the error = %s and the cat_id = %s" % (e, cat_id))
            return False
        cls.reload_single_cat_2memcache(cat_id)
        cls.reload_cat_by_field(cat_id, [field])
        return True

    @classmethod
    def get_all_subcats(cls, cat_id):
        '''获取一个类目下的所有子类目'''
        def get_subcat(cat_id):
            result_list = []
            subcat_list = Cat.get_cat_attr_func(cat_id, "cat_child_list")
            for subcat_id in subcat_list:
                temp_list = get_subcat(subcat_id)
                result_list.append(subcat_id)
                result_list.extend(temp_list)
            return result_list
        return get_subcat(cat_id)

    @classmethod
    def get_full_name_path(cls, cat_id):
        return {"cat_path": Cat.get_cat_attr_func(cat_id, "cat_path_id"),
                "cat_full_name": Cat.get_cat_attr_func(cat_id, "cat_path_name")
                }

    @classmethod
    def get_catid_path(cls, cat_id):
        cat_ids = []
        cat_ids_str = Cat.get_cat_attr_func(cat_id, "cat_path_id")
        if cat_ids_str:
            cat_ids = cat_ids_str.split(' ')
        return cat_ids

    @classmethod
    def get_cat_path(cls, cat_id_list, last_name):
        result = {}
        danger_cats_dict = DanagerInfo.check_danger_cats(cat_id_list)
        cat_path_dict = Cat.get_cat_path_name(cat_id_list)
        for cat_id in cat_id_list:
            cat_id = unicode(cat_id)
            path = cat_path_dict[cat_id]
            danger_descr = danger_cats_dict.get(cat_id, '')
            result[cat_id] = [path, danger_descr]
        return result

    @classmethod
    def get_subcat_list(cls, cat_id):
        '''获取一个类目的下一级子类目。当cat_id为0时，获取的是一级类目'''
        from operator import itemgetter
        result = []
        if cat_id >= 0:
            subcat_list = Cat.get_cat_attr_func(cat_id, "cat_child_list")
            for subcat_id in subcat_list:
                result.append({'cat_id':subcat_id, 'cat_name':Cat.get_cat_attr_func(subcat_id, "cat_name")})
        return sorted(result, key = itemgetter('cat_name'))

    @classmethod
    def get_ancestral_cats(cls, cat_ids):
        '''
        .获取类目的所有上级类目,返回顺序从上级类目到下级类目，为元组(类目ID，类目名称)
        '''
        result_list = []
        cat_list = cat_ids.split(' ')
        # 容错处理，如果某个类目没有名称，就直接将下级的类目名称去掉子类目
        temp_name = ''
        for cat_id in cat_list:
            cat_name = Cat.get_cat_attr_func(cat_id, "cat_name")
            if temp_name:
                temp_name += '>' + cat_name
            else:
                temp_name = cat_name
            result_list.append((cat_id, temp_name))
        return result_list

    @classmethod
    def get_danger_cat_list(cls):
        '''获取危险类目清单'''
        b_danger_dict, c_danger_dict = DanagerInfo.get_dange_cat_list()

        result = {'B':b_danger_dict, 'C':c_danger_dict}
        return json.dumps(result)

    @classmethod
    def get_root_cat(cls, cat_id_list):
        result = {}
        for cat_id in cat_id_list:
            root_cat_id = Cat.get_cat_attr_func(cat_id, "root_cat_id")
            result[str(cat_id)] = root_cat_id
        return result

    @classmethod
    def get_cat_prop_prdt(cls, cat_id, property_dict, title):
        tmp_list, result = [], []
        try:
            prop_prdt = cls.get_attr_by_cat(cat_id, 'prop_product_dict')
            if prop_prdt:
                tmp_list = get_match_word(prop_prdt.match and prop_prdt.match.split(',') or [], property_dict.keys())
                if prop_prdt.prop_prdt:
                    tmp_list.extend(prop_prdt.prop_prdt.split(','))
            for tmp in tmp_list:
                value = property_dict[tmp][0].lower()
                result.append(value)
                if ' ' in value:
                    result.append(value.replace(' ', ''))
        except Exception, e:
            log.error("can not get propert product and the error is =%s" % e)
        return result

    @classmethod
    def get_hot_property_list(cls, cat_id, prop_dict):
        """
        .这里传入的是解析完成之后的prop_dict
        """
        result = []
        hot_prop_list = cls.get_attr_by_cat(cat_id, 'hot_prop_list')
        for hot_prop in hot_prop_list:
            result.extend(prop_dict.get(hot_prop, []))

        return result



cat_coll = Cat._get_collection()
