# coding=UTF-8
import math
import datetime

from pymongo.errors import BulkWriteError
from mongoengine.document import Document
from mongoengine.fields import (IntField, DateTimeField, StringField,
                                ListField, DictField)

from apilib import get_tapi, tsapi, TopError
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import string_2datetime, time_is_someday
from apps.common.utils.utils_collection import genr_sublist, list_to_string
from apps.common.biz_utils.utils_tapitools import get_kw_g_data
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.common.constant import Const
from apps.router.models import User
from apps.subway.models_adgroup import Adgroup, adg_coll
from apps.subway.models_parser import ItemParser
from apps.kwslt.analyzer import ChSegement
from apps.kwslt.select_words import ItemKeywordManager, WordFactory, \
    SelectConfManage
from apps.kwslt.models_cat import ProductWord, SaleWord, BrandWord, Cat, \
    IncludeWord, ForbidWord
from apps.kwslt.models_pointlessword import PointlessWord
from apps.kwslt.models_synonymword import SynonymWord
from apps.kwslt.models_property import DeriveWord, CatPropInfo
from apps.kwslt.base import is_string_char_digit


class Item(Document):
    """片键是shop_id"""
    item_id = IntField(verbose_name = "商品数字ID", primary_key = True)
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    cat_id = IntField(verbose_name = "子类目ID", required = True)
    title = StringField(verbose_name = "标题", max_length = 100)
    price = IntField(verbose_name = "商品价格")
    approve_status = StringField(verbose_name = "商品上传后状态", max_length = 20) # onsale：出售中，instock：库中
    pic_url = StringField(verbose_name = "商品图片地址", max_length = 512)
    delist_time = DateTimeField(verbose_name = "下架时间") # 格式：yyyy-MM-dd HH:mm:ss
    modify_time = DateTimeField(verbose_name = "商品修改时间")

    freight_payer = StringField(verbose_name = "运费承担方式", max_length = 20) # seller 卖家承担，buyer 买家承担
    props_name = StringField(verbose_name = "标准属性") # 格式为：20000:3275069:品牌:盈讯;1753146:3485013:型号:F908;30606:112030:上市时间:2008年
    property_alias = StringField(verbose_name = "自定义属性") # 格式为：20000:3275069:盈讯;1753146:3485013:F908;30606:112030:2008年

    title_optimize_time = DateTimeField(verbose_name = "最近标题优化时间")
    word_modifier = IntField(verbose_name = "词根修改人", choices = ((0, '系统'), (1, '用户'), (2, 'AE'))) # 0代表是系统初始生成的，1代表用户自己修改保存的，2代表是AE修改保存的
    prdtword_hot_list = ListField(verbose_name = "产品词热度列表", default = []) # 结构为 [[word, hot], ...]
    # propword_hot_list = ListField(verbose_name = "属性词热度列表", default = [])
    # dcrtword_hot_list = ListField(verbose_name = "修饰词热度列表", default = [])
    decorate_word_list = ListField(verbose_name = "修饰词列表", default = []) # 选词淘词专用，与标题优化不同，结构为 [word, ...]
    blackword_list = ListField(verbose_name = "屏蔽词列表", default = [])
    saleword_list = ListField(verbose_name = "卖点词列表", default = []) # 结构为 [word, ...]
    selectconf_dict = DictField(verbose_name = "选词的配置", default = {})

    meta = {'collection':'subway_item', 'indexes':[], "shard_key":('shop_id',)}

    Parser = ItemParser

    @classmethod
    def bulk_update_item2db(cls, update_list): # update_list形如[({'_id':1024321654}, {'$set':{'max_price':24}}), ({'_id':1024321651}, {'$set':{'max_price':47}}),...]
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
    def get_item_dict_2_order(cls, item_dict):
        item = Item()
        item.item_id = item_dict.get('item_id', 0)
        item.item_dict = item_dict
        item.cat_id = item_dict['cat_id']
        item.title = item_dict['title']
        item._property_list = item_dict.get('property_list', [])
        temp_property_dict = item_dict.get('property_dict', {})
        item._property_dict = ChSegement.get_element_word_dict(item.cat_id, temp_property_dict)
        return item

    @staticmethod
    def get_item_dict(item_id, fields = 'cid,title,property_alias,freight_payer,props_name,price,pic_url,nick,sku', force = False):
        cache_key = CacheKey.SUBWAY_ITEM_DETAIL % item_id
        item_dict = CacheAdpter.get(cache_key, 'web', {})
        item = Item()
        item.item_id = item_id
        if not item_dict:
            item_dict = item.get_item_property(fields, force = force)
        if item_dict:
            item.item_dict = item_dict
            CacheAdpter.set(cache_key, item_dict, 'web', 60 * 60 * 24)
            item.title = item_dict.get('title', '')
            item._property_list = item_dict.get('property_list', [])
            temp_property_dict = item_dict.get('property_dict', {})
            item.cat_id = item_dict.get('cat_id', 0)
            item._property_dict = ChSegement.get_element_word_dict(item.cat_id, temp_property_dict)
        else:
            item = None
        return item

    @staticmethod
    def get_item_image_byuser(user, item_id_list, tapi = None):
        if not tapi:
            tapi = get_tapi(user)
        item_list = Item.get_item_by_ids(shop_id = int(user.shop_id), item_id_list = item_id_list, tapi = tapi, fields = 'num_iid,item_img.url')
        item_dict = {str(top_obj.num_iid):getattr(top_obj.item_imgs, 'item_img', []) for top_obj in item_list if hasattr(top_obj, 'item_imgs')}
        for item_id, item_imgs in item_dict.items():
            item_dict[item_id] = [item_img.url for item_img in item_imgs]
        return item_dict

    @staticmethod
    def get_item_image_byshopid(shop_id, item_id_list, tapi = None):
        try:
            user = User.objects.get(shop_id = str(shop_id))
        except Exception, e:
            log.error('get user error, shop_id=%s, e=%s' % (shop_id, e))
            return {}
        return Item.get_item_image_byuser(user, item_id_list)

    @classmethod
    def get_item_by_ids(cls, shop_id, item_id_list, tapi, transfer_flag = False, fields = 'num_iid, title, cid, price, approve_status, pic_url, delist_time, created, modified, property_alias, freight_payer, props_name'):
        """通过item_id_list获取item"""
        temp_item_list = []
        for temp_item_id_list in genr_sublist(item_id_list, 20):
            num_iids = list_to_string(temp_item_id_list)
            try:
                top_objs = tapi.items_seller_list_get(fields = fields, num_iids = num_iids)
                if top_objs and hasattr(top_objs, "items") and hasattr(top_objs.items, "item") and top_objs.items.item:
                    temp_item_list.extend(top_objs.items.item)
            except TopError, e:
                log.error('items_seller_list_get error, shop_id = %s,num_iids=[%s], e = %s' % (shop_id, num_iids, e))

        if transfer_flag: # 是否需要将top_obj转成标准含所有信息的字典
            item_list = []
            for item in temp_item_list:
                item_list.append(cls.Parser.parse(item, trans_type = "init", extra_dict = {'shop_id': shop_id}))
            return item_list
        else:
            return temp_item_list

    @classmethod
    def sync_item_byids(cls, shop_id, tapi, item_id_list):
        """根据item_id_list来同步item数据"""
        if not item_id_list:
            return True, ''
        try:
            item_id_list = list(set(item_id_list))
            item_list = Item.get_item_by_ids(shop_id = shop_id, item_id_list = item_id_list, tapi = tapi)

            local_item_dict = {}
            for temp_item in item_coll.find({'shop_id':shop_id}, {'modify_time':1}):
                local_item_dict.update({temp_item['_id']:str(temp_item['modify_time'])})

            new_item_list, changed_item_dict = [], {}
            if item_list:
                for item in item_list:
                    modify_time = local_item_dict.get(item.num_iid, None)
                    if modify_time:
                        if modify_time != item.modified:
                            changed_item_dict.update({item.num_iid:cls.Parser.parse(item, trans_type = "inc")})
                    else:
                        new_item_list.append(cls.Parser.parse(item, trans_type = "init", extra_dict = {'shop_id': shop_id}))
            # FIXME: wangqi 20151123 如果淘宝有item已经删除掉了，这里没有做同步删除。原因是无法判断淘宝的item不存在，是真的不存在，还是接口异常，以前出现过淘宝接口异常返回为空，导致删除了所有本地item的事故

            if new_item_list:
                item_coll.insert(new_item_list)
            if changed_item_dict:
                update_list = []
                for item_id, item_value in changed_item_dict.items():
                    update_list.append(({'shop_id':shop_id, '_id':item_id}, {'$set':item_value}))
                cls.bulk_update_item2db(update_list)

            return True, ''
        except Exception, e:
            return False, e

    @classmethod
    def struct_download(cls, shop_id, tapi, remove_flag = True):
        """同步Item，每次同步时要先获取所有，再根据数据库来同步"""
        item_id_list = list(set([adg['item_id'] for adg in adg_coll.find({'shop_id':shop_id}, {'item_id':1})]))
        if remove_flag: # 是否要删除多余的item数据
            item_coll.remove({'shop_id':shop_id, '_id':{'$nin':item_id_list}})

        result, reason = cls.sync_item_byids(shop_id = shop_id, tapi = tapi, item_id_list = item_id_list)
        if result:
            log.info('init items OK, shop_id=%s' % (shop_id))
        else:
            log.error('init items FAILED, shop_id=%s, e=%s' % (shop_id, reason))
        return result

    @classmethod
    def increase_download(cls, shop_id, tapi, last_sync_time): # Item 的增量下载
#         item_inc_dwnld = True
#         try:
#             user = User.objects.get(shop_id = shop_id)
#             item_inc_dwnld = user.get_subs_msg_status()
#         except Exception, e:
#             log.error("can not get user by shop_id shop_id=%s and error=%s" % (e, shop_id))
#             return False
#         if not item_inc_dwnld:
        if True: # TODO 数据库刚替换的几天里暂时对所有用户的item替换开放
            if not time_is_someday(last_sync_time): # 每天全部同步一次
                return cls.struct_download(shop_id = shop_id, tapi = tapi, remove_flag = True)
            else: # 今天同步过直接忽略，增量的同步在新增adgroup已经做了
                log.info('sync items OK, shop_id=%s, synced today already' % (shop_id))
                return True
        return True

    @classmethod
    def remove_item(cls, shop_id, item_id_list):
        if not item_id_list:
            return True
        else:
            query_dict = {'shop_id': shop_id, '_id': {'$in': item_id_list}}
            remove_count = cls._get_collection().remove(query_dict)
            if remove_count.get('n', 0):
                adgroup_id_list = list(Adgroup.objects.filter(shop_id = shop_id, item_id__in = item_id_list).values_list('adgroup_id'))
                Adgroup.remove_adgroup(shop_id = shop_id, adgroup_id_list = adgroup_id_list)

    # @staticmethod
    # def download_udp_byids(shop_id, tapi, date_scope = None, item_id_list = None):
    #     from udp_download import UdpSyncer
    #     """下载指定的item_id_list对应的UDP数据，不指定则下载全部"""
    #     udp_fields = [udp_field for udp_field in Const.SUBWAY_UDP_ITEM_MAPPING]
    #     if not item_id_list:
    #         item_id_list = [item['_id'] for item in  item_coll.find({'shop_id':shop_id}, {'_id':1})]

    #     us = UdpSyncer(shop_id = shop_id, tapi = tapi)
    #     return us.sync_items_udp(item_id_list = item_id_list, date_scope = date_scope, udp_fields = udp_fields, flag = False)

    # def udp_download(self, tapi, date_scope = None, force_flag = False):
    #     """下载单个UDP数据"""
    #     from udp_download import UdpSyncer
    #     udp_fields = [udp_field for udp_field in Const.SUBWAY_UDP_ITEM_MAPPING]
    #     us = UdpSyncer(shop_id = self.shop_id, tapi = tapi)
    #     return us.sync_item_udp(item_id = self.item_id, date_scope = date_scope, udp_fields = udp_fields, flag = force_flag)

    def get_kw_list_byelemword(self, elemword_list):
        """根据标题词根获取相关关键词流量数据，数据结构为[(word,cat_click,rank_score,kw_traffic_score),...]"""
        # kw_list = []
        try:
            # kw_dict = ItemKeywordManager.get_kw_dict_byelemword(cat_id = self.cat_id, elemword_list = elemword_list)
            return ItemKeywordManager.get_kw_list_byelemword(cat_id = self.cat_id, elemword_list = elemword_list)
        except Exception, e:
            log.error('get kw dict by elemword error, item_id=%s, e=%s' % (self.item_id, e))
            return []
#         for word, values in kw_dict.items():
#             cat_click, cat_competition, hot = values
#             kw_list.append((word, cat_click, cat_competition, hot))
#         return kw_list

    def get_title_info_dict(self, title):
        """根据标题获取相关关键词流量数据，数据结构为{'kw_list':[(word,cat_click,rank_score,kw_traffic_score),...],'title_elemword_list':[word,...],}"""
        # kw_list = []
        try:
            return ItemKeywordManager.get_title_info_dict(cat_id = self.cat_id, title = title)
        except:
            return {'kw_list':[], 'title_elemword_list':[]}
        # for word, values in title_info_dict['kw_dict'].items():
        #     cat_click, cat_competition, hot = values
        #     kw_list.append((word, cat_click, cat_competition, hot))
        # title_info_dict['kw_list'] = kw_list
        # del title_info_dict['kw_dict']
        # return title_info_dict

    @staticmethod
    def update_item_title_inner(shop_id, item_id, title, shop_type, tapi):
        '''更新宝贝标题'''
        try:
            if shop_type == 'B':
                tapi.simba_tmall_item_schema_increment_update(item_id = item_id , xml_data = Const.SUBWAY_ITEM_UPDATE_TITLE_XML_DATA % title)
            else:
                tapi.item_update(num_iid = item_id, title = title)
            item_coll.update({'shop_id':shop_id, '_id':item_id}, {'$set':{'title':title, 'title_optimize_time':datetime.datetime.now()}})
            return True
        except TopError, e:
            log.error("update_item_title_inner TopError, shop_id=%s, item_id=%s, error=%s" % (shop_id, item_id, e))
            return e.humanized_reason

    @staticmethod
    def get_blackword_list(shop_id, item_id):
        """获取黑名单词"""
        item_existed = True
        blackword_list = []
        item_obj = item_coll.find_one({'shop_id':int(shop_id), '_id':int(item_id)}, {'blackword_list':1})
        if item_obj:
            blackword_list = item_obj.get('blackword_list', [])
        else:
            item_existed = False
        return item_existed, blackword_list

    @staticmethod
    def save_blackword_list(shop_id, item_id, word_list):
        """直接将word_list写回"""
        try:
            item_coll.update({'shop_id':int(shop_id), '_id':int(item_id)}, {'$set':{'blackword_list':list(set(word_list))}})
            return True
        except:
            return False

    @staticmethod
    def update_blackword_list(shop_id, item_id, word_list):
        """将新的黑名单关键词追加进去"""
        item_existed, blackword_list = Item.get_blackword_list(shop_id, item_id)
        if not item_existed:
            return False
        else:
            word_list.extend(blackword_list)
            word_list = list(set(word_list))
            Item.save_blackword_list(shop_id, item_id, word_list)
            return True

    @staticmethod
    def get_blackword_list_byids(shop_id, item_id_list):
        """获取一批宝贝的黑名单词"""
        item_cursor = item_coll.find({'shop_id':int(shop_id), '_id':{'$in':item_id_list}}, {'blackword_list':1})
        result_dict = {item['_id']:item.get('blackword_list', []) for item in item_cursor}
        return result_dict

    @staticmethod
    def analysis_item_property(item, fields):
        item_dict, property_dict = {}, {}
        field_list = [field for field in fields.split(',') if field]
        for field in field_list:
            if field == 'cid':
                category_id = item.cid
                strcids = str(category_id).decode()
                top_obj_p = tsapi.itemcats_get(cids = strcids, fields = "parent_cid")
                if not top_obj_p or not hasattr(top_obj_p, 'item_cats'): # 当一个宝贝本身就是一级类目下时，这里取不到父类目ID，导致bug
                    parent_catid = strcids
                else:
                    parent_catid = top_obj_p.item_cats.item_cat[0].parent_cid
                item_dict['parent_cat_id'] = parent_catid
                item_dict['cat_id'] = category_id
            elif field in ['pic_url', 'title', 'nick']:
                item_dict[field] = getattr(item, field)
            elif field == 'price':
                item_dict['item_price'] = item.price
            elif field == 'props_name':
                temp = ''
                temp_pname = ''
                property_list = []
                if 'freight_payer' in field_list:
                    if item.freight_payer == 'seller':
                        property_list.append(u'包邮免邮')
                        property_dict[u'包邮'] = u'包邮 免邮'
                    else:
                        property_dict[u'包邮'] = u''
                if item.props_name:
                    for prop in item.props_name.split(';'):
                        v_list = prop.split(':')
                        if len(v_list) < 4:
                            continue
                        str_name = v_list[2]
                        str_value = v_list[3]
                        if str_value and str_name and not (str_name in [u'主图来源', u'货号'] or str_value in Const.SUBWAY_NONSENSE_PROPERTY_WORDS):
                            if property_dict.has_key(str_name):
                                property_dict[str_name] = property_dict[str_name] + '/' + str_value.lower()
                            else:
                                property_dict[str_name] = str_value.lower()
                        str_temp1 = str_name.replace('/', '')
                        str_temp2 = str_value.replace('/', '')
                        if temp == str_temp1:
                            property_list[property_list.index(temp_pname)] += ' ' + str_temp2
                            temp_pname += ' ' + str_temp2
                            continue
                        temp = str_temp1
                        temp_pname = str_temp1 + ' : ' + str_temp2
                        property_list.append(temp_pname)
                if "property_alias" in fields and item.property_alias:
                    for prop in item.property_alias.split(';'):
                        v_list = prop.split(':')
                        if len(v_list) < 3:
                            continue
                        str_name = v_list[1]
                        str_value = v_list[2]
                        if not str_value or not str_name:
                            continue
                        property_dict[str_name] = str_value.lower()
                item_dict['property_list'] = property_list
                item_dict['property_dict'] = property_dict
            elif field == 'sku':
                try:
                    sku_list = [sku.quantity for sku in item.skus.sku]
                except Exception, e:
                    log.info('sku Error, shop_id=%s, e=%s' % (getattr(item, 'shop_id', 0), e))
                    sku_list = []
                item_dict['item_sku'] = sum(sku_list)
        return item_dict

    def get_item_property(self, fields = 'property_alias,freight_payer,props_name', force = False):
        '''根据ItemID获取宝贝的直属类目'''
        shop_id = getattr(self, 'shop_id', 0)
        item_id = self.item_id
        if force:
            try:
                top_obj = tsapi.item_seller_get(num_iid = item_id, fields = fields)
                item = top_obj.item
                data = {}
                for field in ['property_alias', 'freight_payer', 'props_name']:
                    value = getattr(item, field, '')
                    if value:
                        data[field] = value
                if shop_id > 0 and data:
                    Item.objects.filter(shop_id = shop_id, item_id = item_id).update(**data)
            except Exception, e:
                log.error("tsapi.item_seller_get Error, shop_id=%s, item_id=%s, e=%s" % (shop_id, item_id, e))
                return {}
        else:
            item = self
            fields = 'property_alias,freight_payer,props_name'

        try:
            item_dict = Item.analysis_item_property(item, fields)
        except Exception, e:
            log.error("get_item_property Error, shop_id=%s, item_id=%s, e=%s" % (shop_id, item_id, e))
            item_dict = {}
        return item_dict

    @property
    def pure_title_word_list(self):
        if hasattr(self, '_pure_title_word_list'):
            return self._pure_title_word_list
        cache_key = CacheKey.SUBWAY_ITEM_PURE_TIILE_WORD % self.item_id
        self._pure_title_word_list = CacheAdpter.get(cache_key, 'web', ['No'])
        if 'No' not in self._pure_title_word_list:
            return self._pure_title_word_list
        self._pure_title_word_list = ChSegement.split_title_new_to_list(self.title)
        CacheAdpter.set(cache_key, self._pure_title_word_list, 'web', 60 * 60 * 24)
        return self._pure_title_word_list

    @property
    def title_word_list(self):
        if hasattr(self, '_title_word_list'):
            return self._title_word_list
        self.title = self.title.lower()
        cache_key = CacheKey.SUBWAY_ITEM_TIILE_WORD % self.item_id
        self._title_word_list = CacheAdpter.get(cache_key, 'web', ['No'])
        if 'No' not in self._title_word_list:
            return self._title_word_list
        self._title_word_list = self.pure_title_word_list[:]
        self._title_word_list = WordFactory.get_extend_words(self.cat_id, self._title_word_list)
        CacheAdpter.set(cache_key, self._title_word_list, 'web', 60 * 60 * 24)
        return self._title_word_list

    def get_product_word_list(self):
        tmp_list, parent_tmp_list = ProductWord.get_prdt_list(self.title_word_list, self.cat_id)
        tmp_list.extend(parent_tmp_list)
        tmp_list = WordFactory.get_extend_words(self.cat_id, tmp_list)
        product_word_list = [word for word in tmp_list if word]
        return sorted(product_word_list, reverse = True)

    def get_prdtword_hot_list(self, update_flag = False, update_hot_flag = False): # 结构为 [[word, hot], ...]
        modifier = getattr(self, 'word_modifier', 0)
        cache_key = CacheKey.SUBWAY_ITEM_PRDTWORD_HOT % self.item_id
        if not update_flag:
            if modifier > 0 and self.prdtword_hot_list:
                if update_hot_flag:
                    word_list = [word for word, hot in self.prdtword_hot_list]
                    self.prdtword_hot_list = Item.get_word_hot(self.shop_id, self.cat_id, word_list)
                    self.save()
                    CacheAdpter.set(cache_key, self.prdtword_hot_list, 'web', 60 * 60 * 24)
                return self.prdtword_hot_list
            else:
                prdtword_hot_list = CacheAdpter.get(cache_key, 'web', ['No'])
                if 'No' not in prdtword_hot_list:
                    if prdtword_hot_list and update_hot_flag:
                        word_list = [word for word, hot in prdtword_hot_list]
                        prdtword_hot_list = Item.get_word_hot(self.shop_id, self.cat_id, word_list)
                        CacheAdpter.set(cache_key, prdtword_hot_list, 'web', 60 * 60 * 24)
                    return prdtword_hot_list
        prdtword_hot_list = Item.get_word_hot(self.shop_id, self.cat_id, self.get_product_word_list())
        CacheAdpter.set(cache_key, prdtword_hot_list, 'web', 60 * 60 * 24)
        return prdtword_hot_list

    @property
    def product_word_list(self):
        if hasattr(self, '_product_word_list'):
            return self._product_word_list
        modifier = getattr(self, 'word_modifier', 0)
        cache_key = CacheKey.SUBWAY_ITEM_PRDTWORD % self.item_id
        if modifier > 0 and self.prdtword_hot_list:
            self._product_word_list = [word for word, hot in self.prdtword_hot_list]
            return self._product_word_list
        else:
            self._product_word_list = CacheAdpter.get(cache_key, 'web', ['No'])
            if 'No' not in self._product_word_list:
                return self._product_word_list
        self._product_word_list = self.get_product_word_list()
        CacheAdpter.set(cache_key, self._product_word_list, 'web', 60 * 60 * 24)
        return self._product_word_list

    @property
    def sale_word_list(self):
        if not hasattr(self, '_sale_word_list'):
            modifier = getattr(self, 'word_modifier', 0)
            cache_key = CacheKey.SUBWAY_ITEM_SALEWORD % self.item_id
            if modifier > 0 and self.saleword_list:
                self._sale_word_list = self.saleword_list
            else:
                self._sale_word_list = CacheAdpter.get(cache_key, 'web', ['No'])
                if 'No' in self._sale_word_list:
                    try:
                        self._sale_word_list = self.cat_sale_words
                    except Exception, e:
                        log.info('can not get sale word by cat_id,and the error is = %s' % e)
                    CacheAdpter.set(cache_key, self._sale_word_list, 'web', 60 * 60 * 24)
                    self._sale_word_list.extend(SynonymWord.get_synonym_words(self.cat_id, self._sale_word_list))
        return sorted(set(self._sale_word_list), key = len, reverse = True)

    @property
    def cat_sale_words(self):
        if hasattr(self, '_cat_sale_words'):
            return self._cat_sale_words
        try:
            temp_list = self.get_decorate_word_list()
            temp_list.extend(self.product_word_list)
            self._cat_sale_words = SaleWord.get_sale_list(cat_id = self.cat_id, word_list = temp_list) or []
        except Exception, e:
            log.info('can not get cat_sale_words by cat_id,and the error is = %s' % e)
        return self._cat_sale_words

    def get_propword_hot_list(self, update_flag = False, update_hot_flag = False): # 结构为 [[word, hot], ...]
        cache_key = CacheKey.SUBWAY_ITEM_PROPWORD_HOT % self.item_id
        if not update_flag:
            propword_hot_list = CacheAdpter.get(cache_key, 'web', ['No'])
            if 'No' not in propword_hot_list:
                if update_hot_flag:
                    propword_list = [word for word, hot in propword_hot_list]
                    propword_hot_list = Item.get_word_hot(self.shop_id, self.cat_id, propword_list)
                    CacheAdpter.set(cache_key, propword_hot_list, 'web', 60 * 60 * 24)
                return propword_hot_list

        propword_list, propword_hot_list = [], []
        property_dict = self.get_item_property().get('property_dict', {})
        if property_dict:
            if u'品牌' in property_dict:
                del property_dict[u'品牌']
            temp_words = ''.join(property_dict.values())
            propword_list = ChSegement.split_title_new_to_list(temp_words)
            if propword_list:
                propword_hot_list = Item.get_word_hot(self.shop_id, self.cat_id, propword_list)
                propword_hot_list = [[word, hot] for word, hot in propword_hot_list if len(word) > 1 and hot > 0]
        CacheAdpter.set(cache_key, propword_hot_list, 'web', 60 * 60 * 24)
        return propword_hot_list

    @property
    def property_list(self):
        if hasattr(self, '_property_list'):
            return self._property_list
        self._property_list = self.get_item_property().get('property_list', [])
        return self._property_list

    @property
    def property_dict(self):
        if hasattr(self, '_property_dict'):
            return self._property_dict
        cache_key = CacheKey.SUBWAY_ITEM_PROP_DICT % self.item_id
        self._property_dict = CacheAdpter.get(cache_key, 'web', {'init':'init'})
        if not self._property_dict.has_key('init'):
            return self._property_dict
        temp_property_dict = self.get_item_property().get('property_dict', {})
        self._property_dict = temp_property_dict and ChSegement.get_element_word_dict(self.cat_id, temp_property_dict)
        CacheAdpter.set(cache_key, self._property_dict, 'web', 60 * 60 * 24)
        return self._property_dict

    @property
    def brandword_list(self):
        '''宝贝的品牌词'''
        if not hasattr(self, '_brandword_list'):
            self._brandword_list = self.property_dict.get(u'品牌', []) + self.property_dict.get(u'适用品牌', [])
            if 'other' in self._brandword_list or '其他' in self._brandword_list:
                self._brandword_list = []
        return self._brandword_list

    @property
    def include_brand_list(self):
        '''互斥的品牌词'''
        if hasattr(self, '_include_brand_list'):
            return self._include_brand_list
        cache_key = CacheKey.SUBWAY_ITEM_INCLUDE_BRAND % self.item_id
        self._include_brand_list = CacheAdpter.get(cache_key, 'web', ['No'])
        if 'No' not in self._include_brand_list:
            return self._include_brand_list

        is_mutex = Cat.get_cat_attr_func(cat_id = self.cat_id, attr_alias = 'brand_is_mutex')
        self._include_brand_list, brand_list = [], []
        if is_mutex:
            brand_list = CatPropInfo.get_brand_list(self.cat_id)
        for brand in brand_list: # 避免错杀，把标题包含的品牌给剔除掉
            if brand in self.title:
                continue
            self._include_brand_list.append(brand)
        CacheAdpter.set(cache_key, self._include_brand_list, 'web', 60 * 60 * 24)
        return self._include_brand_list

    @property
    def include_word_list(self):
        if hasattr(self, '_include_word_list'):
            return self._include_word_list
        cache_key = CacheKey.SUBWAY_ITEM_INCLUDE_WORD % self.item_id
        self._include_word_list = CacheAdpter.get(cache_key, 'web', ['No'])
        if 'No' not in self._include_word_list:
            return self._include_word_list
        temp_list = []
        for i in self.property_dict.itervalues():
            temp_list.extend(i)
        self._include_word_list = IncludeWord.get_include_list(temp_list + self.title_word_list, self.cat_id)
        self._include_word_list = list(set(self._include_word_list))
        CacheAdpter.set(cache_key, self._include_word_list, 'web', 60 * 60 * 24)
        return self._include_word_list

    @property
    def label_dict(self):
        '''
        供解析自定义标签使用
        '''
        if hasattr(self, '_label_dict'):
            return self._label_dict
        cache_key = CacheKey.SUBWAY_ITEM_LABEL_DICT % self.item_id
        self._label_dict = CacheAdpter.get(cache_key, 'web', {'init':'init'})
        if not self._label_dict.has_key('init'):
            return self._label_dict

        self._label_dict = dict(self.property_dict)
        self._label_dict['title'] = self.title_word_list
        self._label_dict['title_desc'] = self.title
        CacheAdpter.set(cache_key, self._label_dict, 'web', 60 * 60 * 24)
        return self._label_dict

    @property
    def cat_ids(self):
        if hasattr(self, '_cat_ids'):
            return self._cat_ids
        cat_id_list = Cat.get_cat_attr_func(cat_id = self.cat_id, attr_alias = "cat_path_id").split(' ') or []
        self._cat_ids = cat_id_list
        return self._cat_ids

    @property
    def catname_word_list(self):
        if hasattr(self, '_catname_word_list'):
            return self._catname_word_list
        self._catname_word_list = []
        self._catname_word_list.append(Cat.get_cat_attr_func(cat_id = self.cat_id, attr_alias = "cat_name") or '')
#         for cat_id in self.cat_ids:
#             cat_name = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat_name") or ''
#             if '/' in cat_name:
#                 continue
#             self._catname_word_list.append(cat_name)
        return self._catname_word_list

    @property
    def garbage_word_list(self): # 违禁词 + 屏蔽词 + 互斥词 + 品牌互斥词
        if not hasattr(self, '_garbage_word_list'):
            words = u'*,#,※,△,◇,★,▲,【,】,『,』,<,>,[,]'
            result_list = words.split(',')
            result_list.extend(ForbidWord.get_all_forbid_list(self.cat_id))
            result_list.extend(self.blackword_list)
            result_list.extend(self.include_word_list)
            result_list.extend(self.include_brand_list)
            self._garbage_word_list = list(set(result_list))
        return self._garbage_word_list

    def get_dcrtword_hot_list(self, update_flag = False, update_hot_flag = False): # TODO @wuhuaqiao 确认修改
        '''
        标题优化修饰词：暂定为从标题词根、卖点词、类目名称中去掉产品词、属性词、品牌词后的词根及其热度，
        后续会根据新的原子词表来获取宝贝类目下高词频的词根
        '''
        cache_key = CacheKey.SUBWAY_ITEM_DCRTWORD_HOT % self.item_id
        if not update_flag:
            dcrtword_hot_list = CacheAdpter.get(cache_key, 'web', ['No'])
            if 'No' not in dcrtword_hot_list:
                if update_hot_flag:
                    dcrtword_list = [word for word, hot in dcrtword_hot_list]
                    dcrtword_hot_list = Item.get_word_hot(self.shop_id, self.cat_id, dcrtword_list)
                    CacheAdpter.set(cache_key, dcrtword_hot_list, 'web', 60 * 60 * 24)
                return dcrtword_hot_list

        all_word_list, temp_word_list = [], []
        product_word_list = [unicode(word) for word, hot in self.get_prdtword_hot_list()]
        pure_property_word_list = [unicode(word) for word, hot in self.get_propword_hot_list()]
        temp_word_list.extend(product_word_list)
        temp_word_list.extend(pure_property_word_list)
        temp_word_list.extend(self.property_dict.get(u'品牌', []))
        # bigcount_word_list = Item.get_topcount_word_list(self.cat_id) # TODO 从类目下词频高的原子词中挑出的修饰词，待新版原子词表准备好后调用
        # all_word_list.extend(bigcount_word_list)
        all_word_list.extend(self.title_word_list)
        all_word_list.extend(self.catname_word_list)
        for pd_list in self.property_dict.values():
            all_word_list.extend(pd_list)
        decorate_word_list = list(set(all_word_list) - set(temp_word_list))
        tmp_list, dcrtword_hot_list = [], []
        for wd in decorate_word_list:
            for key in Const.COMMON_ALL_SIGN_DICT['all']:
                wd = wd.replace(key, ' ')
            wd_list = [kw for kw in wd.split() if len(kw) > 1]
            tmp_list.extend(wd_list)
        tmp_list = [word for word in list(set(tmp_list)) if word]
        tmp_list = WordFactory.extend_this_year(tmp_list)
        if tmp_list:
            dcrtword_hot_list = Item.get_word_hot(self.shop_id, self.cat_id, tmp_list)
            dcrtword_hot_list = [[word, hot] for word, hot in dcrtword_hot_list if len(word) > 1 and hot > 0]
        CacheAdpter.set(cache_key, dcrtword_hot_list, 'web', 60 * 60 * 24)
        return dcrtword_hot_list

    def _get_decorate_word_list(self, product_word_list, title_word_list, property_dict):
        property_word_list = []
        for pd_list in property_dict.values():
            property_word_list.extend(pd_list)
        all_word_list = list(set(self.catname_word_list) | set(title_word_list) | set(property_word_list))
        # 获取名词中的形容词，补充到修饰词中
        new_decorate_list = ProductWord.get_decorate_from_nouns(self.cat_id, all_word_list)
        add_sale_word = SaleWord.get_sale_list(word_list = [], cat_id = self.cat_id)
        # 删除多余的词
        decorate_word = set(all_word_list) | set(new_decorate_list) | set(add_sale_word) - set(product_word_list)
        tmp_list = []
        for wd in decorate_word:
            wd = wd.lower()
            for key in Const.COMMON_ALL_SIGN_DICT['all']:
                wd = wd.replace(key, ' ')
            wd_list = wd.split()
            tmp_list.extend(wd_list)
        tmp_list = WordFactory.get_extend_words(self.cat_id, tmp_list)
        tmp_list = WordFactory.extend_this_year(tmp_list)
        pointless_word_list = PointlessWord.get_pointlessword_list(level = 1)
        result_set = set(tmp_list) - set(pointless_word_list)
        return sorted(result_set, key = len, reverse = True)

    def get_decorate_word_list(self, update_flag = False):
        '''
        选词淘词专用，修饰词，不包含自定义标签词、产品词。
        '''
        modifier = getattr(self, 'word_modifier', 0)
        cache_key = CacheKey.SUBWAY_ITEM_DCRTWORD % self.item_id
        if not update_flag:
            if modifier > 0 and self.decorate_word_list:
                return self.decorate_word_list
            else:
                decorate_word_list = CacheAdpter.get(cache_key, 'web', ['No'])
                if 'No' not in decorate_word_list:
                    return decorate_word_list

        decorate_word_list = self._get_decorate_word_list(product_word_list = self.product_word_list,
                                                          title_word_list = self.title_word_list,
                                                          property_dict = self.property_dict)
        CacheAdpter.set(cache_key, decorate_word_list, 'web', 60 * 60 * 24)
        return decorate_word_list

#     def get_label_conf_list(self, custome_word_dict):
#         all_decorate_list = self.get_decorate_word_list()
#         for k, v in custome_word_dict.items():
#             all_decorate_list.extend(v)
#         all_decorate_list = list(set(all_decorate_list))
#         # label_conf_list 的顺序不能随意变动，否则导致关键词匹配标签不准
#         label_conf_list = [(k, 0, v) for k, v in custome_word_dict.iteritems()]
#         label_conf_list.extend([('S', 0, sorted(self.sale_word_list, key = len, reverse = True)),
#                                 ('P', 1, sorted(self.product_word_list, key = len, reverse = True)),
#                                 ('D', 1, sorted(all_decorate_list, key = len, reverse = True))
#                                 ])
#         return label_conf_list

    def get_label_conf_list(self):
#         all_decorate_list = self.get_decorate_word_list()
        all_label_dict = self.get_label_dict
#         for ky, val in custome_word_dict.items():
#             for key, value in all_label_dict.items():
#                 for v in val:
#                     if key == 'P':
#                         if v == value:
#                             custome_word_dict[ky].remove(v)
#                     else:
#                         if v == value:
#                             all_label_dict[key].remove(v)
        # label_conf_list 的顺序不能随意变动，否则导致关键词匹配标签不准
        label_conf_list = [('P', 1, all_label_dict.get('P', []))] + [(k, 1, v) for k, v in self.custome_word_dict.iteritems()] + [('S', 1, all_label_dict.get('S', [])),
                                ('H', 1, all_label_dict.get('H', [])),
                                ('D', 1, all_label_dict.get('D', []))
                                ]
        return label_conf_list

    def get_preview_info(self, custome_word_dict):
        '''CRM中测试预览，不保存到缓存或数据库'''
        pure_title_list = ChSegement.split_title_new_to_list(self.title)
        title_list = WordFactory.get_extend_words(self.cat_id, pure_title_list)
        product_list = self.get_product_word_list()
        temp_property_dict = self.get_item_property().get('property_dict', {})
        property_dict = temp_property_dict and ChSegement.get_element_word_dict(self.cat_id, temp_property_dict)
        decorate_list = self._get_decorate_word_list(product_word_list = product_list,
                                                     title_word_list = title_list,
                                                     property_dict = property_dict)
        temp_list = decorate_list[:]
        temp_list.extend(product_list)
        sale_list = SaleWord.get_sale_list(word_list = temp_list, cat_id = self.cat_id) or []
        return pure_title_list, product_list, sale_list, decorate_list

    def delete_item_cache(self):
        Item.delete_item_cache_byitemid(self.item_id)
        for prop in Const.SUBWAY_ITEM_PROPERTY_LIST:
            if hasattr(self, '_%s' % prop):
                delattr(self, '_%s' % prop)

    @staticmethod
    def delete_item_cache_byitemid(item_id):
        item_cache_list = [CacheKey.SUBWAY_ITEM_PURE_TIILE_WORD,
                           CacheKey.SUBWAY_ITEM_TIILE_WORD,
                           CacheKey.SUBWAY_ITEM_PRDTWORD_HOT,
                           CacheKey.SUBWAY_ITEM_PROPWORD_HOT,
                           CacheKey.SUBWAY_ITEM_DCRTWORD_HOT,
                           CacheKey.SUBWAY_ITEM_PRDTWORD,
                           CacheKey.SUBWAY_ITEM_DCRTWORD,
                           CacheKey.SUBWAY_ITEM_SALEWORD,
                           CacheKey.SUBWAY_ITEM_PROP_DICT,
                           CacheKey.SUBWAY_ITEM_LABEL_DICT,
                           CacheKey.SUBWAY_ITEM_INCLUDE_BRAND,
                           CacheKey.SUBWAY_ITEM_INCLUDE_WORD
                           ]
        for cache_key in item_cache_list:
            CacheAdpter.delete(cache_key % item_id, 'web')

    @staticmethod
    def get_word_hot(shop_id, cat_id, word_list):
        # 确定指定类目下词根热度
        result_list = []
        try:
            temp_dict = get_kw_g_data(word_list)
            for word, g_data in temp_dict.items():
                g_competition = g_data.g_competition or 1
                if not g_data.g_pv:
                    continue
                hot = round(math.log10(float(g_data.g_pv) ** 2 / g_competition), 2)
                result_list.append([str(word), hot])
            from operator import itemgetter
            result_list.sort(key = itemgetter(1), reverse = True)
            failed_word_list = list(set([str(word) for word in word_list]) - set([str(word) for word, hot in result_list]))
            result_list.extend([[word, 0] for word in failed_word_list])
        except Exception, e:
            result_list = [[word, 0] for word in word_list]
            log.exception("get_word_hot error, shop_id=%s, e=%s" % (shop_id, e))
        return result_list
    """
    .由此开始是新版选词item的各个标签解析方式，后期会替换掉原有的所有的方式
    """
    @property
    def get_P_label(self):
        """
        .首先对宝贝标题进行分词
        .解析产品词，产品词解析完成之后，将产品词从标题中替换成空格，组成一个新的标题
        .将解析出来的产品词，获取同义词
        """
        if hasattr(self, '_P_label'):
            return self._P_label
        title_list = self.title_word_list
        prdt_list, parent_prdt_list = ProductWord.get_prdt_list(title_list, self.cat_id)
        prop_prdt_list = Cat.get_cat_prop_prdt(self.cat_id, self.property_dict, self.title)
        prdt_list.extend([unicode(word) for word, _ in self.get_prdtword_hot_list()])
        self.prop_prdt_list = prop_prdt_list
        prdt_list.extend(prop_prdt_list)
        result = WordFactory.get_extend_words(self.cat_id, prdt_list + parent_prdt_list)
        self.new_title = self.title
        for word in sorted(result, key = len, reverse = True):
            if word in self.title:
                self.new_title = self.new_title.replace(word, ' ')
        self._P_label = list(set(result))
        return self._P_label

    @property
    def get_chseg_prop(self):
        """
        .获取宝贝的所有解析过后的标签
        .根据每一个属性去做分词
        .针对特有属性去解析，如：品牌、颜色
        """
        if hasattr(self, '_chseg_prop'):
            return self._chseg_prop
        prop_dict = {}
        property_dict = self.property_dict
        for key, value in property_dict.items():
            val = []
            for vv in value:
                if key == u'品牌':
                    if 'other' in vv or u'其他' in vv or u'其它' in vv:
                        rslt = []
                    else:
                        rslt = CatPropInfo.get_brand_word(vv)
                else:
                    rslt = ChSegement.split_title_new_to_list(vv)
                    for rl in rslt:
                        if u'色' == rl[-1]:
                            val.append(rl.replace(u'色', ''))
                val.extend(rslt)
            prop_dict[key] = WordFactory.get_extend_words(self.cat_id, val)
        prop_dict['title'] = [self.title]
        self._chseg_prop = prop_dict
        return prop_dict

    @property
    def get_D_label(self):
        if hasattr(self, '_D_label'):
            return self._D_label
        self._D_label = []
        D_dict = self.get_chseg_prop
        del D_dict['title']
        for val in D_dict.values():
            self._D_label.extend(val)
        for tt in self.title_word_list:
            if not is_string_char_digit(tt):
                self._D_label.extend(list(tt))
        self._D_label.extend(WordFactory.get_extend_words(self.cat_id, ChSegement.split_title_new_to_list(self.new_title)))
        return self._D_label

    @property
    def get_H_label(self):
        """
        .该条件必须优先级应该在解析完成D标签和P标签之后，避免因为包含关系剔除了产品词中的内容,如：女装和女
        .遍历属性词解析结果，将结果在标题中去匹配，如果匹配上并且长度大于1，那么将会将整个属性都放入到热属性词当中
        .调用原有系统卖点词接口获取热属性词
        .所有的热属性词获取同义词
        .将所有的热属性词替换成空格,组成新的标题
        """
        if hasattr(self, '_H_label'):
            return self._H_label
        hot_list = []
        new_title = getattr(self, "new_title", '')
        prop_dict = self.get_chseg_prop
        for key, val in prop_dict.items():
            if key == 'title':
                continue
            for v in val:
                if v in new_title:
                    if (len(v) == 1 and ord(v) < 127) or not v:
                        continue
                    hot_list.append(v)
        hot_list.extend(Cat.get_hot_property_list(self.cat_id, self.get_chseg_prop))
        hot_list.extend(SaleWord.get_sale_list(self.title_word_list, self.cat_id))
        hot_list = sorted(list(set(hot_list)), key = len, reverse = True)
        hot_list = WordFactory.get_extend_words(self.cat_id, hot_list)
        for hot in sorted(hot_list, key = len, reverse = True):
            self.new_title = new_title.replace(hot, ' ')
        self._H_label = hot_list
        return hot_list

    @property
    def get_Y_label(self):
        """
        .获取属性隐喻词的配置，读取隐喻词的配置，解析出该属性包含的隐喻意思
        .解析出来的隐喻词调用同义词接口
        """
        derive_list = DeriveWord.get_metaphor_list(self.cat_id, self.property_dict)
        return derive_list

    @property
    def get_S_label(self):
        """
        .根据用户输入的词作为卖点词，提供前端用户输入的方式（该方式暂时保留，是否对用户开放卖点词接口待定）
        .解析属性中的品牌作为卖点词，解析属性下的产品词之后，将其拆分作为卖点词
        .根据卖点词获取同义词
        """
        if hasattr(self, '_S_label'):
            return self._S_label
        result = []
        if getattr(self, 'prop_prdt_list', []):
            for prop_prdt in self.prop_prdt_list:
                result.extend(ChSegement.split_title_new_to_list(prop_prdt))
        result.extend(self.get_chseg_prop.get(u'品牌', []))
        result = WordFactory.get_extend_words(self.cat_id, result)
        self._S_label = result
        return result

    @property
    def get_forbid_brand(self):
        """
        .根据类目上标记是否品牌互斥，如果品牌互斥的话，那么则获取到当前类目下该属性的所有品牌，并且如果该类目下有其他属性需要互斥的话，同样会获取到其他类目的互斥属性
        """
        result = []
        if Cat.get_attr_by_cat(self.cat_id, 'brand_is_mutex'):
            result.extend(CatPropInfo.get_brand_list(self.cat_id))
            result = list(set(result) - set(self.get_chseg_prop.get(u'品牌', [])))
        return result

    @property
    def get_label_dict(self):
        """
        .获取到所有的标签解析结果，将结果封装成dict和list2种
        .list结果取set集合去重
        .根据dict标签标注结果，结果优先级按照， PSYHD的顺序来排优先级生成一个新的dict，该dict为最终结果
        .获取到没有重复并且不包含的标签词，每个标签的词按照词长进行排序，这个结果将要被用作选词以及生成选词配置
        """
        if hasattr(self, '_all_label_dict'):
            return self._all_label_dict
        mode = getattr(self, 'mode', 'precise')
        if not hasattr(self, 'select_conf'):
            self.select_conf = SelectConfManage.get_selectconf(self, mode)
        custome_word_dict = self.select_conf.analyse_label(self)
        self.custome_word_dict = custome_word_dict
        result_dict, label_dict, all_label_list = {}, {}, []
        label = ['P', 'S', 'H', 'D']
        for l in label:
            label_list = getattr(self, 'get_%s_label' % l)
            result_dict[l] = label_list + [','.join(label_list)]
            all_label_list.extend(label_list)
        if custome_word_dict:
            label = ['P', 'S'] + custome_word_dict.keys() + ['H', 'D']
            for key, value in custome_word_dict.items():
                result_dict[key] = value + [','.join(value)]
                all_label_list.extend(value)
        for wd in set(all_label_list):
            if not is_string_char_digit(wd) and len(wd) > 2:
                if wd in result_dict.get('S', []):
                    continue
                all_label_list.extend(list(wd))
        for word in sorted(set(all_label_list), key = len, reverse = True):
            if not word:
                continue
            for lbl in label:
                if word in result_dict[lbl]:
                    label_dict.setdefault(lbl, []).append(word.lower())
                    break
                if word in result_dict[lbl][-1] and not lbl in ['P', 'S']:
                    if not is_string_char_digit(word):
                        label_dict.setdefault(lbl, []).append(word.lower())
                        break
        for key, value in label_dict.items():
            label_dict[key] = sorted(value, key = len, reverse = True) # TODO
        self._all_label_dict = label_dict
        return label_dict

    @property
    def get_exclude_list(self):
        """
        .获取到所有的标签的结果集，根据这些结果集去获取到所有的互斥词
        .获取品牌互斥词
        .获取违禁词
        .获取用户设置的屏蔽词
        """
        result, tmp_list = [], []
        result.extend(self.get_forbid_brand)
        for ll in self.get_chseg_prop.values():
            tmp_list.extend(ll)
        result.extend(IncludeWord.get_include_list(tmp_list + self.title_word_list, self.cat_id))
        result.extend(self.blackword_list)
        return [wd for wd in result if wd]

    def clear_all_label(self):
        attr_list = ['_all_label_dict', '_S_label', '_H_label', '_D_label', '_chseg_prop', '_P_label' ]
        for attr in attr_list:
            if hasattr(self, attr):
                delattr(self, attr)
        self.delete_item_cache()
        Cat.reload_single_cat_2memcache(self.cat_id)
        Cat.clear_attr_by_cat(self.cat_id)


item_coll = Item._get_collection()
