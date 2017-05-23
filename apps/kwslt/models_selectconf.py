# coding=UTF-8
import json, datetime

from mongoengine.document import EmbeddedDocument, Document
from mongoengine.fields import StringField, EmbeddedDocumentField, ListField, \
    DictField, DateTimeField, IntField
from apps.kwslt.base import get_match_word, get_rule_list
from apps.common.utils.utils_log import log
from apps.kwslt.base import get_age_from_height
from apps.kwslt.analyzer import ChSegement

class GetWordConf(EmbeddedDocument):
    candi_filter = StringField(verbose_name = "候选词过滤条件", default = 'False') # score=1000 and "P" in label and "S" in label
    sort_mode = StringField(verbose_name = "排序方式", default = 'click')
    select_num = StringField(verbose_name = "选择数目", default = '0-1')

class InitPriceConf(EmbeddedDocument):
    candi_filter = StringField(verbose_name = "选择 条件", default = 'True')
    init_price = StringField(verbose_name = "初始出价", default = '0.8*cpc')

class SelectConf(Document):
    conf_name = StringField(verbose_name = "配置名称", primary_key = True)
    conf_desc = StringField(verbose_name = "配置描述")
    label_define_list = ListField(verbose_name = "标签定义", default = []) # "name":"B", "type":"match", "from":u"品牌", "rule":"*"
    candi_filter = StringField(verbose_name = "海选过滤条件", default = 'False')
    select_conf_list = ListField(verbose_name = "精选过滤条件", field = EmbeddedDocumentField(GetWordConf), default = [])
    price_conf_list = ListField(verbose_name = "初始出价", field = EmbeddedDocumentField(InitPriceConf), default = [])
    delete_conf = DictField(verbose_name = "关键词删除条件", default = {"remove_del":1, "remove_dupli":0, "remove_cur":1})
    conf_type = IntField(verbose_name = "", choices = ((0, "系统默认"), (1, "通用模板"), (2, "类目"), (3, "宝贝"))) # 此处可以设计仅供参考
    create = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.today())

    meta = {'collection':"kwlib_SelectConf", "db_alias": "kwlib-db"}

    @staticmethod
    def analyse_single_label(label, item):
        """解析当个标签，接口需要保证label参数为字典""" # 因其为底层接口，在此不考虑校验问题
        match_type = label['type']
        word_list, source_word_list = [], []
        label_from = label['from'].decode().split(',')
        label_rule = label['rule'].decode()
        for frm in label_from:
            if frm in item.get_chseg_prop and item.get_chseg_prop[frm]:
                source_word_list.extend(item.get_chseg_prop[frm])
        if match_type == 'match':
            rule_list, word_list = get_rule_list(label_rule)
            if (not word_list) and (not rule_list):
                word_list = source_word_list
            else:
                word_list.extend(get_match_word(rule_list, source_word_list))
        else:
            func_name = label_rule
            word_list = eval(func_name + '( source_word_list  )')
        return word_list

    def analyse_label(self, item):
        '''
        解析自定义标签。
        '''
        word_dict = {}
        for label_str in self.label_define_list:
            if ('{' not in label_str) and ('}' not in label_str):
                label = eval('{' + label_str + '}')
            else:
                label = eval(label_str)
            temp_list = list(set(SelectConf.analyse_single_label(label, item)))
            if temp_list:
                if word_dict.has_key(label['name']):
                    word_dict[label['name']].extend(temp_list)
                    word_dict[label['name']] = list(set(word_dict[label['name']]))
                else:
                    word_dict[label['name']] = list(set(temp_list))
        return word_dict

    @staticmethod
    def check_exist(conf_name):
        try:
            SelectConf.objects.get(conf_name = conf_name)
        except Exception:
            return False
        return True

    @staticmethod
    def pack_select_conf_object(select_conf, conf_desc, candidate_words, label_define, select_conf_list, price_conf_list, delete_conf):
        select_conf.conf_desc = str(conf_desc)
        select_conf.label_define_list = label_define
        select_conf.candi_filter = str(candidate_words)

        get_word_conf_list = []
        for conf in select_conf_list:
            get_word_conf = GetWordConf()
            if conf.has_key('cond'):
                get_word_conf.candi_filter = str(conf['cond'])
            if conf.has_key('sort'):
                get_word_conf.sort_mode = str(conf['sort'])
            if conf.has_key('num'):
                get_word_conf.select_num = str(conf['num'])
            get_word_conf_list.append(get_word_conf)
        select_conf.select_conf_list = get_word_conf_list

        init_price_conf_list = []
        for conf in price_conf_list:
            init_price_conf = InitPriceConf()
            if conf.has_key('cond'):
                init_price_conf.candi_filter = str(conf['cond'])
            if conf.has_key('price'):
                init_price_conf.init_price = str(conf['price'])
            init_price_conf_list.append(init_price_conf)
        select_conf.price_conf_list = init_price_conf_list
        select_conf.delete_conf = delete_conf
        return select_conf

    @staticmethod
    def save_select_conf(conf_name, conf_desc, candidate_words, label_define, select_conf_list, price_conf_list, delete_conf, conf_type, new_create = False):
        """保存选词配置"""
        try:
            select_conf, is_create = SelectConf.objects.get_or_create(auto_save = False, conf_name = str(conf_name))
            if is_create and not new_create:
                return False
            select_conf = SelectConf.pack_select_conf_object(select_conf, conf_desc, candidate_words, label_define, select_conf_list, price_conf_list, delete_conf)
            select_conf.conf_type = conf_type
            return select_conf.save()
        except Exception, e:
            log.exception('save SelectConf error, conf_name=%s,  e=%s' % (conf_name, e))
            return False

    @staticmethod
    def pack_select_word_conf(select_conf_name):
        if not select_conf_name:
            return {}

        try:
            select_conf = SelectConf.objects.get(conf_name = select_conf_name)
            return {
                        'conf_name':select_conf.conf_name,
                        'conf_desc':select_conf.conf_desc,
                        'candi_filter':json.dumps(select_conf.candi_filter),
                        'label_define_list':select_conf.label_define_list,
                        'select_conf_list':[conf._data for conf in select_conf.select_conf_list],
                        'price_conf_list':[conf._data for conf in select_conf.price_conf_list],
                        'delete_conf':select_conf.delete_conf
                       }
        except Exception, e:
            log.error("get select conf error, name=%s, e=%s" % (select_conf_name, e))
            return {}