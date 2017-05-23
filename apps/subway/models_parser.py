# coding=utf-8

from apps.common.utils.utils_number import trans_price, doublestr_2int
from apps.common.utils.utils_datetime import string_2datetime, string_2datetime2


class ParserField(object):
    """字段的映射，用于解析、格式化淘宝对应的字段"""

    def __init__(self, field_name, default = None, formatter = None, need_update = False):
        self.field_name = field_name # 淘宝的字段名称，比如常见的modify_time 对应 modified_time；也可以给None，即本地初始化
        self.default = default # 默认值
        self.formatter = formatter # 格式器，常见于字符串转datetime类型，也能将一些字符串转int
        self.need_update = need_update # 是否需要更新

class BaseParser(object):
    """基类解析器"""

    @classmethod
    def field_dict(cls):
        if not hasattr(cls, '_field_dict'):
            cls._field_dict = {k: v for k, v in cls.__dict__.items() if isinstance(v, ParserField)}
        return cls._field_dict

    @classmethod
    def parse(cls, top_obj):
        result_dict = {}
        for name, field in cls.field_dict().items():
            if field.field_name:
                v = getattr(top_obj, field.field_name, field.default)
                if field.formatter:
                    v = field.formatter(v)
            else:
                v = field.default
            result_dict.update({name: v})
        return result_dict

class StructParser(BaseParser):
    """针对淘宝下载下来的结构数据，进行解析的对象，依赖于下面定义的解析字段"""

    @classmethod
    def update_field_dict(cls):
        if not hasattr(cls, '_update_field_dict'):
            cls._update_field_dict = {k: v for k, v in cls.field_dict().items() if v.need_update}
        return cls._update_field_dict

    @classmethod
    def parse(cls, top_obj, trans_type = "init", extra_dict = None):
        result_dict = {}
        if trans_type == "init":
            field_dict = cls.field_dict()
        elif trans_type == "inc": # 更新数据，只更新need_update的这些字段
            field_dict = cls.update_field_dict()

        for name, field in field_dict.items():
            if field.field_name:
                v = getattr(top_obj, field.field_name, field.default)
                if field.formatter:
                    v = field.formatter(v)
            else:
                v = field.default
            result_dict.update({name: v})

        if extra_dict:
            result_dict.update(extra_dict)

        return result_dict

# class AccountParser(StructParser):
#     shop_id = ParserField(field_name = "shop_id")
#     cat_id = ParserField(field_name = None, default = 0)

class CampaignParser(StructParser):
    # shop_id = ParserField(field_name = "shop_id")
    _id = ParserField(field_name = "campaign_id")
    title = ParserField(field_name = "title", need_update = True)
    create_time = ParserField(field_name = "create_time", formatter = string_2datetime)
    budget = ParserField(field_name = None, default = 3000)
    is_smooth = ParserField(field_name = None, default = 1)
    modify_time = ParserField(field_name = "modified_time", formatter = string_2datetime, need_update = True)
    online_status = ParserField(field_name = "online_status", need_update = True)
    settle_reason = ParserField(field_name = "settle_reason", default = '', need_update = True)
    settle_status = ParserField(field_name = "settle_status", need_update = True)

class AdgroupParser(StructParser):
    _id = ParserField("adgroup_id")
    campaign_id = ParserField("campaign_id")
    create_time = ParserField("create_time", formatter = string_2datetime)
    item_id = ParserField("num_iid")
    # shop_id = ParserField("shop_id")
    limit_price = ParserField(None, default = 0)
    mnt_type = ParserField(None, default = 0)
    mobile_discount = ParserField("mobile_discount", default = 0, need_update = True)
    category_ids = ParserField("category_ids", need_update = True)
    default_price = ParserField("default_price", need_update = True)
    modify_time = ParserField("modified_time", formatter = string_2datetime, need_update = True)
    online_status = ParserField("online_status", need_update = True)
    offline_type = ParserField("offline_type", need_update = True)
    nosearch_max_price = ParserField("nosearch_max_price", default = 50, need_update = True)
    isnonsearch_default_price = ParserField("is_nonsearch_default_price", need_update = True)


class ItemParser(StructParser):
    _id = ParserField("num_iid")
    title = ParserField("title", need_update = True)
    pic_url = ParserField("pic_url", default = '', need_update = True)
    cat_id = ParserField("cid", need_update = True)
    modify_time = ParserField("modified", need_update = True, formatter = string_2datetime)
    delist_time = ParserField("delist_time", need_update = True, formatter = string_2datetime)
    price = ParserField("price", need_update = True, formatter = trans_price)
    approve_status = ParserField("approve_status", need_update = True)
    property_alias = ParserField("property_alias", need_update = True)
    freight_payer = ParserField("freight_payer", need_update = True)
    props_name = ParserField("props_name", need_update = True)


class CreativeParser(StructParser):
    _id = ParserField("creative_id")
    # shop_id = ParserField("shop_id")
    campaign_id = ParserField("campaign_id")
    adgroup_id = ParserField("adgroup_id")
    create_time = ParserField("create_time", formatter = string_2datetime)
    img_url = ParserField("img_url", need_update = True)
    title = ParserField("title", need_update = True)
    modify_time = ParserField("create_time", need_update = True)
    audit_status = ParserField("audit_status", need_update = True)

class KeywordParser(StructParser):
    _id = ParserField("keyword_id")
    adgroup_id = ParserField("adgroup_id", need_update = True) # 这里的adgroup_id因为在update是必须，因此这里特殊处理
    campaign_id = ParserField("campaign_id")
    # shop_id = ParserField("shop_id")
    word = ParserField("word")
    create_time = ParserField("create_time", formatter = string_2datetime)
    qscore = ParserField("qscore", default = 0, formatter = int, need_update = True)
    match_scope = ParserField("match_scope", default = 4, formatter = int, need_update = True)
    modify_time = ParserField("modified_time", formatter = string_2datetime, need_update = True)
    is_default_price = ParserField("is_default_price", need_update = True)
    audit_status = ParserField("audit_status", need_update = True)
    audit_desc = ParserField("audit_desc", need_update = True)
    max_price = ParserField("max_price", need_update = True)
    is_garbage = ParserField("is_garbage", need_update = True)
    mobile_is_default_price = ParserField("mobile_is_default_price", default = 0, need_update = True)
    max_mobile_price = ParserField("max_mobile_price", default = 0, need_update = True)

class RealtimeReportParser(BaseParser):
    """针对淘宝下载下来的实时报表数据，进行解析的对象，依赖于下面定义的解析字段"""

    date = ParserField("thedate", formatter = string_2datetime2)
    search_type = ParserField('search_type', formatter = doublestr_2int, default = -1)
    source = ParserField('source', formatter = doublestr_2int, default = -1)
    impressions = ParserField('impression', formatter = doublestr_2int, default = 0)
    click = ParserField('click', formatter = doublestr_2int, default = 0)
    cost = ParserField('cost', formatter = doublestr_2int, default = 0)
    directpay = ParserField('directtransaction', formatter = doublestr_2int, default = 0)
    indirectpay = ParserField('indirecttransaction', formatter = doublestr_2int, default = 0)
    directpaycount = ParserField('directtransactionshipping', formatter = doublestr_2int, default = 0)
    indirectpaycount = ParserField('indirecttransactionshipping', formatter = doublestr_2int, default = 0)
    favitemcount = ParserField('favitemtotal', formatter = doublestr_2int, default = 0)
    favshopcount = ParserField('favshoptotal', formatter = doublestr_2int, default = 0)
    carttotal = ParserField('carttotal', formatter = doublestr_2int, default = 0)
    aclick = ParserField('aclick', formatter = doublestr_2int, default = 0)
    avgpos = ParserField('avgpos', formatter = doublestr_2int, default = 0)
