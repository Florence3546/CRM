# coding=UTF-8

from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import IntField, StringField, BooleanField, ListField, \
    EmbeddedDocumentField
from apps.kwslt.models_cat import  cat_coll
from apps.kwslt.base import  get_cat_property
from apps.kwslt.analyzer import ChSegement

class PropValue(EmbeddedDocument):
    vid = IntField(verbose_name = '属性值ID')
    name = StringField(verbose_name = '属性值名称')
    is_parent = BooleanField(verbose_name = '是否为父级，这里为淘宝反馈的接口目前没什么用，但是可以存着')

class DeriveWord(EmbeddedDocument):
    """
    .衍生词，配置{'condition':110cm,'derivewords':'小童'}
    .condition做一个基本的条件，如：if 110cm in 参考身高: return '小童'
    """
    condition = StringField(verbose_name = "属性包含条件内容")
    derivewords = StringField(verbose_name = "根据属性包含内容隐喻出的一些词,词根据英文逗号隔开，如：中童,中小童")

    @classmethod
    def get_metaphor_list(cls, cat_id, property_dict):
        derive_list = []
        derive_cnf_list = list(cat_prop_val_coll.find({'cat_id':cat_id, 'derive_cnf_list':{'$ne':[None, []]}}, {'derive_cnf_list':1, 'name':1}))
        for derive in derive_cnf_list:
            if derive['condition'] in property_dict.get(derive['name', '']):
                derive_list.extend(derive['derivewords'].split(','))
        return list(set(derive_list))

class CatPropInfo(Document):
    cat_id = IntField(verbose_name = "类目Id", required = True)
    pid = IntField(verbose_name = '属性Id', required = True)
    name = StringField(verbose_name = '属性名称')
    must = BooleanField(verbose_name = '是否为必须的属性')
    multi = BooleanField(verbose_name = '保留属性')
    is_join_brand = BooleanField(verbose_name = "是否加入到品牌词互斥行列，如：手机机型，汽车车型等", default = False)
    prop_value_list = ListField(verbose_name = '属性值', field = EmbeddedDocumentField(PropValue), default = [])
    derive_cnf_list = ListField(verbose_name = '隐喻词配置', field = EmbeddedDocumentField(DeriveWord), default = [])

    meta = {'collection':'kwlib_cat_propvalue', 'indexes':['pid', 'name', {
                                                                'fields':['cat_id', 'pid'],
                                                                'unique':True
                                                              }], "db_alias": "kwlib-db"}
    cat_prop_dict = {}
    brand_word_dict = {}

    @classmethod
    def download_cat_property(cls):
        cat_id_list = [cat['_id'] for cat in cat_coll.find({}, {'_id':1})]
        for cat_id in cat_id_list:
            property_list, prop_value_dict = [], {}
            for i in range(1, 3):
                result = get_cat_property(cat_id, i)
                if hasattr(result, 'item_props'):
                    item_props = result.item_props
                    if hasattr(item_props, 'item_prop'):
                        item_prop = item_props.item_prop
                        property_list = []
                        for prop in item_prop:
                            pid = prop.pid
                            property_list.append(pid)
                            prop_value_dict.setdefault(pid, {})
                            prop_value_dict.setdefault(str(pid), {'pid' : pid, 'name' : prop.name, 'must' : prop.must, 'multi' : prop.multi})
                            if hasattr(prop, 'prop_values'):
                                prop_value = prop.prop_values.prop_value
                                for prp_val in prop_value:
                                    prop_value_dict[pid].update({prp_val.vid:{'vid':prp_val.vid, 'name':prp_val.name, 'is_parent':getattr(prp_val, 'is_parent', False)}})
            for pid in prop_value_dict:
                if type(pid) is str:
                    continue
                property_dict = prop_value_dict[str(pid)]
                cat_prop_val_coll.update({'cat_id':cat_id, 'pid':pid}, {'$set':{'name' : property_dict['name'], 'must' : property_dict['must'], 'multi' : property_dict['multi'], 'prop_value_list' : prop_value_dict[pid].values()}}, upsert = True)
            cat_coll.update({'_id' : cat_id}, {'$set':{'property_list': property_list}})

    @classmethod
    def get_brand_list(cls, cat_id):
        word_list = []
        for prop in cls._get_collection().find({'$or':[{'cat_id':cat_id, 'pid':20000}, {'cat_id':cat_id, 'is_join_brand':True}]}):
            prop_value_list = prop['prop_value_list']
            for prop_value in prop_value_list:
                value_name = prop_value['name'].lower()
                word_list.extend(cls.get_brand_word(value_name))
        return list(set(word_list))

    @classmethod
    def get_brand_word(cls, brand_word):
        word_list = []
        brand_word = brand_word.lower()
        for splt_word in brand_word.split('/'):
            for word in ChSegement.split_by_cn_eng(splt_word):
                word = ChSegement.replace_unavailable_wd(word, sign_dict = 'all')
                if len(word) == 1:
                    continue
                if word:
                    word_list.append(word)
                if ' ' in word:
                    wd = word.replace(' ', '')
                    if wd:
                        word_list.append(wd)
        return word_list

    @classmethod
    def get_cat_brand_list(cls, cat_id):
        if not cat_id in cls.brand_word_dict:
            cls.brand_word_dict[cat_id] = cls.get_brand_list(cat_id)
        return cls.brand_word_dict[cat_id]


    @classmethod
    def load_cat_prop_dict(cls):
        cat_id_list = [cat['_id'] for cat in cat_coll.find({}, {'_id':1})]
        for cat_id in cat_id_list:
            cls.load_single_cat_prop(cat_id)

    @classmethod
    def load_single_cat_prop(cls, cat_id):
        cat_prop = cls._get_collection().find({'cat_id':cat_id}, {'cat_id':1, 'pid':1, 'name':1, 'must':1, 'is_join_brand':1, 'is_mask_prop':1})
        if cat_prop.count():
            cls.cat_prop_dict[cat_id] = cat_prop
        else:
            cls.cat_prop_dict[cat_id] = {}


    @classmethod
    def set_hot_property(cls, cat_id, property_name):
        cls._get_collection().update({'cat_id':cat_id, 'name':property_name}, {'$set':{'is_hot_prop':True}})

    @classmethod
    def set_mask_property(cls, cat_id, property_name):
        cls._get_collection().update({'cat_id':cat_id, 'name':property_name}, {'$set':{'is_mask_prop':True}})


cat_prop_val_coll = CatPropInfo._get_collection()

