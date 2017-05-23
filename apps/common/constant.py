# coding=UTF-8
"""
全局常量管理类，避免在程序中使用魔鬼数字。
Created on 2013-07-25
@author: zhangyu

常量定义规范：
    1、常量之间保持一行间隔
    2、属于app下的常量前缀为APP名称，否则为COMMON
    3、同一个app下的常量放在一起，COMMON放在最后面

常量声明格式：
    '''常量声明示例'''
    Const.APP_CONSTANT_NAME = '这是示例'

常量引用方式：
    print Const.TEST_CONSTANT
"""

class _Constant(object):
    class _ConstantError(TypeError):
        pass

    def __setattr__(self, name, value):
        if self.__dict__.has_key(name):
            raise self._ConstantError, "Can't rebind constant(%s)" % name
        self.__dict__[name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            raise self._ConstantError, "Can't unbind constant(%s)" % name
        raise NameError, name

Const = _Constant()

#==============================定义常量 Start=================================================

'''常量声明示例'''
Const.APP_CONSTANT_NAME = '这是示例'

# 公共
Const.COMMON_WEEK_DATE_NAME = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期天'] # 一般直接用 date_obj.strftime('%A') 获取

'''所有的特殊字符串'''
Const.COMMON_ALL_SIGN_DICT = {'unavailable_wd_dict':{u'~':u'~', u'!':u'!', u'@':u'@', u'$':u'$', u'＇':u'＇', u'＆':u'＆', u'·':u'·', u'．':u'．',
                                                     u'%':u'%', u'^':u'^', u'&':u'&', u'*':u'*', u'(':u'(',
                                                     u')':u')', u'=':u'=', u'，':u'，', u',':u',',
                                                     u'《':u'《', u'》':u'》', u';':u';', u'；':u'；', u'|':u'|',
                                                     u'{':u'{', u'}':u'}', u'[':u'[', u']':u']', u'<':u'<',
                                                     u'>':u'>', u'。':u'。', u'"':u'"', u'、':u'、', u'‘':u'’',
                                                     u'？':u'？', u'?':u'?', u'\\':u'\\', u'/':u'/', u'：':u'：',
                                                     u':':u':', u"'":u"'", u'（':u'（', u'）':u'）', u'—':u'—',
                                                     u'－':u'－', u'～':u'～', u'【':u'【', u'】':u'】', u'！':u'！'
                                                     },
                              'available_wd_dict':{'-':'-',
                                                   ' ':' ',
                                                   '.':'.',
                                                   '°':'°',
                                                   '+':'+',
                                                   '#':'#',
                                                   '_':'_',
                                                   u'℃':u'℃'
                                                   },
                              'last_wd_dict':{u'°':u'°', u'℃':u'℃'},
                              'all':{u'~':u'~', u'!':u'!', u'@':u'@', u'$':u'$', u'＇':u'＇', u'＆':u'＆', u'·':u'·', u'．':u'．',
                                     u'%':u'%', u'^':u'^', u'&':u'&', u'*':u'*', u'(':u'(',
                                     u')':u')', u'=':u'=', u'，':u'，', u',':u',',
                                     u'《':u'《', u'》':u'》', u';':u';', u'；':u'；', u'|':u'|',
                                     u'{':u'{', u'}':u'}', u'[':u'[', u']':u']', u'<':u'<',
                                     u'>':u'>', u'。':u'。', u'"':u'"', u'、':u'、', u'‘':u'’',
                                     u'？':u'？', u'?':u'?', u'\\':u'\\', u'/':u'/', u'：':u'：',
                                     u':':u':', u"'":u"'", u'（':u'（', u'）':u'）', u'—':u'—',
                                     u'－':u'－', u'～':u'～', '-':'-', ' ':' ', '.':'.', u'°':u'°', u'℃':u'℃', u'【':u'【', u'】':u'】', u'！':u'！'
                                     }
                              }

'''正则表达式特殊字符'''
Const.COMMON_RE_SIGN = '\/*.?+$^[](){}|'

'''各版本订单所对应的article_code'''
Const.COMMON_SUBSCRIBE_MAPPING = {
    "qn":['FW_GOODS-1921400'],
    "kcjl":['ts-25811'],
    "rjjh":['ts-25811-6'],
    "software":['ts-25811', 'FW_GOODS-1921400'],
    "tp":['tp-001', 'tp-002'],
    "saler":['tp-001', 'tp-002', 'tp-003', 'tp-004', 'ts-25811', 'FW_GOODS-1921400', "ts-25811-6"],
    "consult":['ts-25811', 'FW_GOODS-1921400', 'ts-25811-6', 'tp-001'],
    "all":['tp-001', 'tp-002', 'tp-003', 'tp-004', 'ts-25811', 'FW_GOODS-1921400', "ts-25811-6"],
}


# check

'''健康检查类型'''
Const.CHECK_ITEM_TYPE = ('account', 'item', 'adgroup')
Const.CHECK_ITEM_ORDER = [('item_base', '宝贝基础'), ('show', '展现'), ('click', '点击'), ('inversion', '转化'), ('cost', '花费')]
Const.CHECK_ACCOUNT_ORDER = [('show', '展现'), ('click', '点击'), ('inversion', '转化'), ('cost', '花费')]

'''健康检查常量模块'''
Const.CHECK_AREA_NAME_MAPPING = {'华北地区':{'19':'北京', '461':'天津', '125':'河北', '393':'山西', '333':'内蒙古'},
                                 '东北地区':{'294':'辽宁', '234':'吉林', '165':'黑龙江'},
                                 '华东地区':{'368':'山东', '1':'安徽', '39':'福建', '255':'江苏', '417':'上海', '508':'浙江'},
                                 '华中地区':{'145':'河南', '184':'湖北', '212':'湖南', '279':'江西'},
                                 '华南地区':{'68':'广东', '92':'广西', '120':'海南'},
                                 '西南地区':{'532':'重庆', '438':'四川', '488':'云南', '393':'贵州', '109':'西藏自治区'},
                                 '西北地区':{'52':'甘肃', '357':'青海', '406':'陕西', '471':'新疆维吾尔自治区', '351':'宁夏回族自治区'},
                                 '其他地区':{'574':'国外', '576':'澳门', '578':'台湾', '599':'香港'},
                                 }


# crm

'''CRM过滤限制条件 list'''
Const.CRM_LIMIT_FIELDS = ['$gte', '$lte']

'''CRM 报表字段'''
Const.CRM_FILTER_REPORT_FIELDS = {0:[('展现量', 'impressions'), ('点击量', 'click'), ('点击率', 'ctr'), ('平均点击花费', 'cpc'), ('总花费', 'cost'), ('成交额', 'pay'), ('成交笔数', 'paycount'), ('收藏次数', 'favcount'), ('点击转化率', 'conv'), ('投资回报率', 'roi')],
                                  1:[('展现量', 'impressions'), ('点击量', 'click'), ('点击率', 'ctr'), ('平均点击花费', 'cpc'), ('总花费', 'cost'), ('成交额', 'pay'), ('成交笔数', 'paycount'), ('收藏次数', 'favcount'), ('点击转化率', 'conv'), ('投资回报率', 'roi'), ('花费百分比', 'cons_ratio')],
                                  2:[('展现量', 'impressions'), ('点击量', 'click'), ('点击率', 'ctr'), ('平均点击花费', 'cpc'), ('总花费', 'cost'), ('成交额', 'pay'), ('成交笔数', 'paycount'), ('收藏次数', 'favcount'), ('点击转化率', 'conv'), ('投资回报率', 'roi')],
                                  3:[('展现量', 'impressions'), ('点击量', 'click'), ('点击率', 'ctr'), ('平均点击花费', 'cpc'), ('总花费', 'cost'), ('成交额', 'pay'), ('成交笔数', 'paycount'), ('收藏次数', 'favcount'), ('点击转化率', 'conv'), ('投资回报率', 'roi')],
                                  }

'''CRM支持的最大查询结果数量'''
Const.CRM_MAX_RESULT_COUNT = 120000


# engine


# kwlib

'''添加关键词时计算选中的词运算基数'''
Const.KWLIB_KEYWORD_ADD_RADIX = 250

'''类目属性缓存时间'''
Const.KWLIB_ATTRIBUT_CACHE_TIME = 2 * 60 * 60

'''类目缓存时间'''
Const.KWLIB_CAT_CACHE_TIME = 7 * 24 * 60 * 60


# mnt
'''定义各种托管计划下的宝贝个数限制'''
Const.MNT_GSW_MAX_ITEMS_NUM = 500
Const.MNT_IMPT_MAX_ITEMS_NUM = 10


# ncrm
Const.DEFAULT_LOGIN_PASS = 'ps123456'
Const.NCRM_DEPARTMENT_LEADER_EMAIL = {
    'DEV': 'zy@paithink.com',
    'MTK': 'liyan@paithink.com',
    'QC': 'zhangwei@paithink.com',
    'TRAIN': 'liucaiyan@paithink.com',
    'HR': 'hushujuan@paithink.com',
    'DESIGN': 'ht@paithink.com',
    'OPTAGENT': 'lvmeng@paithink.com',
    'GROUP1': 'wuyang@paithink.com',
    'GROUP2': 'qiumengxue@paithink.com',
    'GROUP3': 'zhupeng@paithink.com',
    # 'GROUP1': 'wangjin@paithink.com',
    # 'GROUP4': 'liucaiyan@paithink.com',
    # 'GROUP5': 'wujie@paithink.com',
}

# router

'''淘宝API超限公告描述内容'''
Const.ROUTER_API_LIMIT_DESCRIPTION = {
    '12612063':{
        'taobao.simba.keywordsvon.add':'关键词加词接口超限: 导致“选词”提交到直通车时会提示失败',
        'taobao.simba.keywords.pricevon.set':'关键词改价接口超限: 导致智能优化、批量优化和全自动改价提交到直通车时无法成功',
        'taobao.simba.rpt.adgroupkeywordbase.get':'关键词报表接口超限: 导致“同步当前宝贝”时系统会提示错误，同时关键词报表可能显示错误',
        'taobao.simba.adgroup.add':'宝贝添加接口超限: 导致在精灵里无法添加宝贝'
    },
    '21729299':{
        'taobao.simba.keywordsvon.add':'关键词加词接口超限: 导致“选词”提交到直通车时会提示失败',
        'taobao.simba.keywords.pricevon.set':'关键词改价接口超限: 导致智能优化、批量优化和全自动改价提交到直通车时无法成功',
        'taobao.simba.rpt.adgroupkeywordbase.get':'关键词报表接口超限: 导致“同步当前宝贝”时系统会提示错误，同时关键词报表可能显示错误',
    }
}


# subway

Const.SUBWAY_ITEM_UPDATE_TITLE_XML_DATA = """<?xml version="1.0" encoding="utf-8"?><itemRule><field id="title" name="商品标题" type="input"><value>%s</value></field><field id="update_fields" name="更新字段列表" type="multiCheck"><values><value>title</value></values></field></itemRule>"""

'''宝贝词源缓存'''
Const.SUBWAY_ITEM_PROPERTY_LIST = ('pure_title_word_list', 'title_word_list', 'product_word_list', 'sale_word_list', 'property_list',
                                   'property_dict', 'include_brand_list', 'include_word_list', 'label_dict')

'''可以取多天数据的字段,在999999的参数时，并且该部分数据属于多天数据汇总,需要逐天下载'''
Const.SUBWAY_ALL_REGION_MORE_DAYS_PARAMETERS = ('50017', '50018', '50019', '50020', '50027', '50028', '50030', '50031', '50034', '50035', '50036', '50037', '50038', '50040', '50041', '50048', '50049', '50050',
                                                '60001', '60002', '60003', '60004', '60005', '60009', '60010', '60011', '60013', '60014', '60015', '60016', '60017', '60018', '60019', '60020', '60021', '60022', '60023', '60024',
                                                '70001', '70002', '70003', '70004', '70005', '70006', '70007', '70008', '70009', '70010', '70013', '70014', '70015', '70016')

'''以下数据返回时会细分到地区细节,此部分需要汇总'''
Const.SUBWAY_ALL_REGION_MORE_AREAS_PARAMETERS = ('50001', '50003', '50005', '50007', '50009', '50013', '50015', '50021', '50022', '50023', '50024', '50025', '50026', '50029', '50045', '50046', '50047',
                                                 '60006', '60007', '60008',
                                                 '70011', '70012')

'''可以用0的参数.SUBWAY_NATIONWIDE_PARAMETERS = SUBWAY_NATIONWIDE_DAYS_PARAMETERS + SUBWAY_NATIONWIDE_DAY_PART_PARAMETERS'''
Const.SUBWAY_NATIONWIDE_PARAMETERS = ('50001', '50002', '50004', '50005', '50006', '50008', '50009', '50010', '50012', '50013', '50014', '50016', '50019', '50020', '50021', '50024', '50031', '50034', '50035', '50049', '50050', '50051', '50052',
                                      '60001', '60004', '60006', '60007', '60008', '60013', '60019', '60025', '60026',
                                      '70001', '70003', '70004', '70013', '70015')

'''可以用0的参数. 注：全国的都可以进行多天查询'''
Const.SUBWAY_NATIONWIDE_DAYS_PARAMETERS = ('50001', '50005', '50009', '50013', '50019', '50020', '50021', '50024', '50031', '50034', '50035', '50049', '50050', '50051', '50052',
                                           '60001', '60004', '60006', '60007', '60008', '60013', '60019', '60025', '60026',
                                           '70001', '70003', '70004', '70013', '70015')

'''以下数据不能超过24小时，需要聚合'''
Const.SUBWAY_NATIONWIDE_DAY_PART_PARAMETERS = ('50002', '50004', '50006', '50008', '50010', '50012', '50014', '50016')

'''宝贝UDP字段分类元祖'''
Const.SUBWAY_SHOP_FIELD_TYPE = ('nationwide_more_days', 'nationwide_one_day', 'allrange_more_days', 'allrange_more_areas')

'''对应字典'''
Const.SUBWAY_UDP_SHOP_MAPPING = {'50051':('shop_pv', 'int'),
                                 '50052':('shop_uv', 'int'),
                                 '70001':('shop_conv', 'float'),
                                 '70008':('inquiry_rate', 'float'),
                                 '70011':('respose_time', 'int'),
                                 '50048':('avg_session', 'int'),
                                 '50017':('stay_sec', 'int'),
                                 '50021':('fav_shop_count', 'int'),
                                 '50022':('fav_item_count', 'int'),
                                 '50034':('bounce_rate', 'float'),
                                 '60006':('pay_num', 'int'),
                                 '60007':('pay_count', 'int'),
                                 '60008':('pay', 'int'),
                                 '60014':('each_order_count', 'float'),
                                 '60018':('drains_pay', 'int'),
                                 '60021':('refund_pay', 'int'),
                                 '60018':('drains_pay', 'int'),
                                 '60019':('refund_pay', 'int'),
                                 '60022':('avg_pay_period', 'int'),
                                 '60023':('avg_send_period', 'int'),
                                 '60024':('avg_deal_period', 'int'),
                                 '60016':('bad_comment_count', 'int'),
                                 '60015':('good_comment_count', 'int'),
                                 '60001':('avg_pct', 'float'),
                                 '60002':('avg_price', 'int'),
                                 '70016':('item_total', 'int'),
                                 '60013':('relate_order_rate', 'float')
                                 }

'''支持source（数据来源）字段的参数列表，需要扩展时，仅仅需要在此原表中进行扩展,如: source = 999'''
Const.SUBWAY_SUPPORT_SOURCE_FIELDS = ('80000', '80001', '80002', '80003', '80004', '80005', '80006', '80007', '80008', '80011', '80012', '80013', '80014', '80015', '80016', '80017', '80018', '80019', '80020', '80026')

'''不支持source（数据来源）字段的参数列表，不可进行扩展，同时不支持多地区'''
Const.SUBWAY_NONSUPPORT_SOURCE_FIELDS = ('80009', '80010', '80021', '80022', '80023', '80024', '80025')

'''宝贝UDP字段分类元祖'''
Const.SUBWAY_ITEM_FIELD_TYPE = ('support_source_fields', 'nonsupport_source_fields')

'''宝贝Udp对象与参数映射字段'''
Const.SUBWAY_UDP_ITEM_MAPPING = {'80000':('item_pv', 'dict', 'int'),
                                 '80001':('item_uv', 'dict', 'int'),
                                 '80004':('stay_sec', 'dict', 'int'),
                                 '80005':('login_user_count', 'dict', 'int'),
                                 '80006':('bounce_rate', 'dict', 'float'),
                                 '80008':('related_visit', 'dict', 'int'),
                                 '80011':('item_conv', 'dict', 'float'),
                                 '80014':('pay_count', 'dict', 'int'),
                                 '80015':('payment', 'dict', 'int'),
                                 '80016':('predetermine_num', 'dict', 'int'),
                                 '80017':('pay_num', 'dict', 'int'),
                                 '80018':('related_order', 'dict', 'int'),
                                 '80019':('related_pay', 'dict', 'int'),
                                 '80009':('fav_uv', 'int'),
                                 '80021':('related_items', 'string'),
                                 }

'''无意义的属性词'''
Const.SUBWAY_NONSENSE_PROPERTY_WORDS = ['常规', '图案']


# web
'''促销词'''
Const.WEB_PROMOTION_WORDS = ['包邮', '特价', '新款', '新品', '正品', '促销', '清仓', '限量', '爆款', '热卖', '惊爆', '秒杀', '疯抢', '抢购', '亏本',
                             '新款上市', '新品推荐', '限时折扣', '满就送', '直销', '专柜正品', '厂家正品', '品牌', '全国联保', '一流产品',
                             '热销推荐', '掌柜推荐', '镇店之宝', '销售冠军', '惊爆低价', '震撼低价', '亏本疯抢', '限时抢购', '好评如潮', '最爱', '冲钻', '冲冠',
                             ]

'''品牌旗舰店和授权代理商专用促销词'''
Const.WEB_FLAGSHIP_PROMOTION_WORDS = ['正品', '直销', '专柜正品', '厂家正品', '品牌', '全国联保']


# 待删除 20150620

# '''店铺UDP数据字段参照常量'''
# '''可用999999的参数, SUBWAY_ALL_REGION_PARAMETERS = SUBWAY_ALL_REGION_MORE_DAYS_PARAMETERS + SUBWAY_ALL_REGION_MORE_AREAS_PARAMETERS'''
# Const.SUBWAY_ALL_REGION_PARAMETERS = ('50001', '50003', '50005', '50007', '50009', '50013', '50015', '50017', '50018', '50019', '50020', '50021', '50022', '50023', '50024', '50025', '50026', '50027', '50028', '50029', '50030', '50031', '50034', '50035', '50036', '50037', '50038', '50040', '50041', '50045', '50046', '50047', '50048', '50049', '50050',
#                                       '60001', '60002', '60003', '60004', '60005', '60006', '60007', '60008', '60009', '60010', '60011', '60013', '60014', '60015', '60016', '60017', '60018', '60019', '60020', '60021', '60022', '60023', '60024',
#                                       '70001', '70002', '70003', '70004', '70005', '70006', '70007', '70008', '70009', '70010', '70011', '70012', '70013', '70014', '70015', '70016')


# '''宝贝Udp数据字段参照常量'''
# '''以下字段是为了扩展以后item数据参数用'''
# Const.SUBWAY_SOURCE_TYPE = {'999':"全来源 ", '255':'其他', '1':'直通车', '2':'淘宝客', '3':'钻石展位', '4':'硬广', '5':'主搜索', '6':'类目浏览', '7':'收藏夹', '8':'直接访问'}

# '''全部的UDP商品api参数字段'''
# Const.SUBWAY_ALL_UDP_ITEM_PARAMETERS = ('80000', '80001', '80002', '80003', '80004', '80005', '80006', '80007', '80008', '80009', '80010', '80011', '80012', '80013', '80014', '80015', '80016', '80017', '80018', '80019', '80020', '80021', '80022', '80023', '80024', '80025', '80026')

# '''以下字段暂在程序中不做处理'''
# '''支持全国参数字段，暂仅仅标示出来,标示位：area = 0'''
# Const.SUBWAY_SUPPORT_NATIONWIDE_FIELDS = ('80000', '80001', '80002', '80003', '80004', '80005', '80006', '80007', '80008', '80009', '80010', '80011', '80012', '80013', '80014', '80015', '80016', '80017', '80018', '80019', '80020', '80021', '80022', '80023', '80024', '80025', '80026')

# '''支持多地区参数字段，暂仅仅标示出来,标示位：area = 999999'''
# Const.SUBWAY_SUPPORT_AREAS_FIELDS = ('80000', '80001', '80002', '80003', '80004', '80005', '80006', '80007')

# '''大类目词 泛词'''
# Const.FATHERCAT_WORDS = ['女装']

# '''定义获取相关词的长度'''
# Const.KEYWORD_RELATED_NUMBER = 10

# '''人机结合指定类目'''
# Const.RJJH_CATEGARE_LIST = [(16, 60),
#                             (50006843, 35),
#                             (50006842, 1213),
#                             (1625, 1171),
#                             (50008165, 48)
#                             ]

# '''CRM大任务缓存key'''
# Const.CRM_BIGTASK_KEY = 'CRM_BIGTASK_KEY_%s'

# '''CRM过滤对象类型'''
# Const.CRM_FILTER_TYPE = ['account', 'campaign', 'adgroup', 'keyword']

# '''CRM过滤对象类型'''
# Const.CRM_LARGEST_CACHE_FIELDS = ['last_filter_data']

# '''CRM缓存存储数据大小'''
# Const.CRM_CAHCHE_BLOCK_SIZE = 1000

# '''CRM缓存时间'''
# Const.CRM_CAHCHE_TIME_OUT = 8 * 60 * 60

# '''CRM过滤数据保存方式'''
# Const.CRM_STORE_MODLE = "CRMMemcacheAdpter"

# '''CRM操作模式'''
# Const.OPER_MODEL_TYPE = {'quary':{'login_url':'user_list', 'flag':'quary', 'is_dl':False},
#                          'operater':{'login_url':'crm_account', 'flag':'operater', 'is_dl':True}
#                          }

# '''CRM默认模板列表'''
# Const.DEFAULT_SELECT_CONF_LIST = ['default_max_quick_select_conf',
#                                   'default_middle_quick_select_conf',
#                                   'default_mini_quick_select_conf',
#                                   'default_max_precise_select_conf',
#                                   'default_middle_precise_select_conf',
#                                   'default_mini_precise_select_conf',
#                                   'default_max_important_select_conf',
#                                   'default_middle_important_select_conf',
#                                   'default_mini_important_select_conf',
#                                   'default_max_important_change_conf',
#                                   'default_middle_important_change_conf',
#                                   'default_mini_important_change_conf',
#                                   'default_max_longtail_select_conf ',
#                                   'default_middle_longtail_select_conf',
#                                   'default_mini_longtail_select_conf',
#                                   'default_max_longtail_change_conf',
#                                   'default_middle_longtail_change_conf',
#                                   'default_mini_longtail_change_conf',
#                                   'default_tongzhuang_quick_select_conf',
#                                   'default_tongzhuang_precise_select_conf',
#                                   'default_tongzhuang_important_select_conf',
#                                   'default_tongzhuang_important_change_conf',
#                                   'default_tongzhuang_longtail_select_conf',
#                                   'default_tongzhuang_longtail_change_conf'
#                                   ]

"""
订单业务归类，格式为 :
    {item_code:[
        (start_date, end_date, category),
        ...],
    ...}
    条件：subscribe.item_code == item_code and subscribe.create_time >= start_date and subscribe.create_time < end_date
"""
Const.SUBSCRIBE_CATEGORY = {
    "ts-25811-1":[(None, None, 'kcjl'), ],
    "ts-25811-3":[(None, None, 'kcjl'), ],
    "ts-25811-5":[(None, None, 'kcjl'), ],
    "ts-25811-6":[(None, '2014-08-07', 'kcjl'), ('2014-08-07', None, 'rjjh'), ],
    "ts-25811-8":[(None, None, 'kcjl'), ],
    "ts-25811-v9":[(None, '2014-09-16', 'kcjl'), ('2014-09-16', None, 'vip'), ],
    "FW_GOODS-1921400-1":[(None, None, 'qn'), ],
    "FW_GOODS-1921400-v2":[(None, None, 'qn'), ],
    "FW_GOODS-1921400-v3":[(None, None, 'qn'), ],
    "tp-001":[(None, None, 'ztc'), ],
    "tp-002":[(None, None, 'zz'), ],
    "tp-003":[(None, None, 'zx'), ],
    "tp-004":[(None, None, 'dyy'), ],
    "tp-005":[(None, None, 'other'), ],
    "tp-006":[(None, None, 'seo'), ],
    "tp-007":[(None, None, 'kfwb'), ],
    }

Const.SUBSCRIBE_CATEGORY_SET = {
    'consult':['kcjl', 'qn'],
    'tp':['ztc', 'zz', 'vip'],
    'software':['kcjl', 'rjjh', 'vip', 'qn', 'ztc'],
    'all':['ztc', 'zz', 'zx', 'dyy', 'kcjl', 'rjjh', 'vip', 'qn'], # 仅仅排除了 other，不建议用 in 来确定范围
    }
#===============================定义常量 End==================================================

Const.CAMP_AREA = {'19', '461', '125', '393', '333', '294', '234', '165', '417', '255',
                   '508', '39', '1', '368', '145', '184', '212', '279', '68', '120', '92',
                   '532', '438', '488', '109', '463', '406', '52', '357', '351', '471',
                   '578', '599', '576', '574'}