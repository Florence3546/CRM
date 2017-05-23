# coding=UTF-8

import datetime
from mongoengine.document import Document
from mongoengine.errors import DoesNotExist
from mongoengine.fields import (IntField, FloatField, DateTimeField, StringField,
                                ListField, EmbeddedDocumentField, DictField)

from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey

from apps.common.utils.utils_misc import trans_batch_dict_2document


class CommandConfig(Document):
    name = StringField(verbose_name = "指令名")
    date = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    cond = StringField(verbose_name = "指令条件")
    desc = StringField(verbose_name = "指令说明")
    operate = StringField(verbose_name = "指令操作")

    meta = {'db_alias': "mnt-db", 'collection':'alg_cmdcfg', 'indexes': ['name']}

    def __unicode__(self):
        return '%s: %s' % (self.name, self.desc)

    @property
    def compiled_cond(self):
        if not hasattr(self, '_compiled_cond'):
            self._compiled_cond = compile(self.cond, '', 'eval')
        return self._compiled_cond

    @property
    def compiled_operate(self):
        if not hasattr(self, '_compiled_operate'):
            self._compiled_operate = compile('self.%s' % self.operate, '', 'eval')
        return self._compiled_operate

    @classmethod
    def get_config(cls, name):
        cachekey = CacheKey.MNT_CMDCFG % name
        cmd_cfg = CacheAdpter.get(cachekey, 'web', None)
        if not cmd_cfg:
            try:
                cmd_cfg = cls.objects.get(name = name)
                CacheAdpter.set(cachekey, cmd_cfg, 'web', 60 * 60 * 24)
            except DoesNotExist: # 取不到，使用默认值
                cmd_cfg = None
                log.error('task config doesnot exsit, name = %s' % name)
        return cmd_cfg

    @classmethod
    def get_config_list(cls, name_list):
        result_list = []
        for name in name_list:
            cmd_cfg = cls.get_config(name)
            if cmd_cfg:
                result_list.append(cmd_cfg)
        return result_list

    @classmethod
    def refresh_all_configs(cls):
        strat_cfgs = cls._get_collection().find({}, {'name': 1})
        for sc in strat_cfgs:
            CacheAdpter.delete(CacheKey.MNT_CMDCFG % sc['name'], 'web')
        return

cmd_cfg_coll = CommandConfig._get_collection()


class StrategyConfig(Document):
    """..."""
    DEFAULT_IMPACT_FACTOR_DICT = {'click': 1.0, 'ctr': 1.0, 'cvr': 1.0, 'cpc': 1.0}
    CACHEKEY = CacheKey.MNT_STGCFG

    name = StringField(verbose_name = "配置名")
    kw_cmd_list = ListField(verbose_name = "关键词指令名list", default = [])
    adg_cmd_list = ListField(verbose_name = "宝贝指令名list", default = []) # add_word, modify_yd_discount, optm_qscore
    impact_factor_dict = DictField(verbose_name = "影响系数", default = DEFAULT_IMPACT_FACTOR_DICT)
    desc = StringField(verbose_name = '备注说明', default = '')

    meta = {'db_alias': "mnt-db", 'collection':'alg_stratcfg', 'indexes': ['name']}

    def __unicode__(self):
        return self.name

    @classmethod
    def get_all_configs(cls):
        sc_dict = CacheAdpter.get(cls.CACHEKEY, 'web', None)
        if not sc_dict:
            objs = cls.objects.all()
            sc_dict = {obj.name: obj for obj in objs}
            if sc_dict:
                CacheAdpter.set(cls.CACHEKEY, sc_dict, 'web', 60 * 60 * 24)
        return sc_dict

    @classmethod
    def get_config(cls, name):
        """读取配置"""
        sc_dict = cls.get_all_configs()
        strat_cfg = sc_dict.get(name, None)
        return strat_cfg

    @classmethod
    def refresh_all_configs(cls):
        CacheAdpter.delete(cls.CACHEKEY, 'web')
        return True

strat_cfg_coll = StrategyConfig._get_collection()


class OptimizeRecord(Document):
    shop_id = IntField(verbose_name = "店铺ID")
    campaign_id = IntField(verbose_name = "推广计划ID")
    adgroup_id = IntField(verbose_name = "推广组ID")
    opt_type = IntField(verbose_name = "优化类型")
    analyze_result = DictField(verbose_name = "宝贝数据分析结果")
    cmd_count = DictField(verbose_name = "执行指令次数")
    modify_kw_count = DictField(verbose_name = "修改关键词个数")
    diagnose = DictField(verbose_name = "诊断结果")
    strategy = StringField(verbose_name = "优化策略")
    score = FloatField(verbose_name = "优化结果积分")
    next_optdate = DateTimeField(verbose_name = '预计下次优化时间')
    create_time = DateTimeField(verbose_name = "诊断时间", default = datetime.datetime.now)

    meta = {'collection': 'alg_optrecord', 'indexes':['shop_id', 'adgroup_id'], 'shard_key':('campaign_id',)}

    RESERVED_DAYS = 15 # 报表的保留天数

    @classmethod
    def create(cls, **args):
        args_dict = {}
        attr_list = ['shop_id', 'campaign_id', 'adgroup_id', 'opt_type', 'analyze_result', 'cmd_count', 'modify_kw_count', 'diagnose', 'strategy']
        for attrname in attr_list:
            args_dict[attrname] = args.get(attrname)
        time_now = datetime.datetime.now()
        args_dict['next_optdate'] = (time_now + datetime.timedelta(days = args.get('next_optdate', 2))).date()
        cls.objects.create(**args_dict)

    @classmethod
    def get_last_rec(cls, shop_id, campaign_id, adgroup_id):
        query_dict = {'shop_id':shop_id,
                      'campaign_id':campaign_id,
                      'adgroup_id':adgroup_id,
                      'create_time':{'$gt':datetime.datetime.now() - datetime.timedelta(days = 7)},
                      }
        data_list = optrec_coll.find(query_dict)
        rec_list = trans_batch_dict_2document(src_dict_list = data_list, class_object = OptimizeRecord) or []
        rec_list.sort(key = lambda x:x.create_time)
        return rec_list[-1] if rec_list else None

    @classmethod
    def get_last_rec_4adgroups(cls, shop_id, campaign_id, adgroup_id_list):
        query_dict = {'shop_id':shop_id,
                      'campaign_id':campaign_id,
                      'adgroup_id':{'$in':adgroup_id_list},
                      'create_time':{'$gt':datetime.datetime.now() - datetime.timedelta(days = 7)},
                      }
        data_list = optrec_coll.find(query_dict)
        rec_list = trans_batch_dict_2document(src_dict_list = data_list, class_object = OptimizeRecord) or []
        rec_dict = {adgroup_id:[] for adgroup_id in adgroup_id_list}
        for rec in rec_list:
            rec_dict[rec.adgroup_id].append(rec)
        result_dict = {}
        for k, v in rec_dict.items():
            if len(v):
                v.sort(key = lambda x:x.create_time)
                result_dict[k] = v[-1]
            else:
                result_dict[k] = None
        return result_dict

    @classmethod
    def clean_outdated(cls):
        """清除过期数据"""
        cls._get_collection().remove({'create_time': {'$lte': datetime.datetime.now() - datetime.timedelta(days = cls.RESERVED_DAYS)}})
        return True

optrec_coll = OptimizeRecord._get_collection()
