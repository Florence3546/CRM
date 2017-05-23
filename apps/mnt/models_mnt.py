# coding=UTF-8
import time
import datetime
import itertools

from django.core.urlresolvers import reverse
from mongoengine.document import Document
from mongoengine.errors import DoesNotExist
from mongoengine.fields import IntField, DateTimeField, StringField, ListField, DictField

from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_datetime import date_2datetime
from apps.common.constant import Const
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey

from apps.common.biz_utils.utils_permission import test_permission, AUTO_MNT_CODE, FULL_MNT_CODE
from apps.router.models import User
from apps.subway.models_campaign import Campaign
from apps.subway.models_keyword import Adgroup, adg_coll, Keyword
from apps.kwslt.models_cat import CatStatic


class MntMnger(object):
    """引擎管理器"""

    @staticmethod
    def get_mnt_num(user):
        """根据权限码判断的托管数量"""
        mnt_num = 0
        if test_permission(AUTO_MNT_CODE, user):
            mnt_num = 2
        if test_permission(FULL_MNT_CODE, user):
            mnt_num = 8
        return mnt_num

    @staticmethod
    def check_mnt_campaigns(shop_id):
        """检查全自动计划数量与权限是否对应，有对降级的特殊处理"""
        mnt_num = MntMnger.get_mnt_num(User.objects.get(shop_id = shop_id))
        mnt_camp_list = MntCampaign.objects.filter(shop_id = shop_id).order_by('start_time')
        invalid_mnt_camp_list = mnt_camp_list[mnt_num:]
        for mnt_camp in invalid_mnt_camp_list:
            log.info('check permissons going to unmnt tasks, shop_id=%s, campaign_id=%s' % (shop_id, mnt_camp.campaign_id))
            MntMnger.unmnt_campaign(shop_id = shop_id, campaign_id = mnt_camp.campaign_id)
        return mnt_camp_list[:mnt_num]

    @staticmethod
    def check_create_mnt(shop_id):
        """检查是否能创建新的全自动计划"""
        mnt_num = MntMnger.get_mnt_num(User.objects.get(shop_id = shop_id))
        if MntCampaign.objects.filter(shop_id = shop_id).count() >= mnt_num:
            return False
        else:
            return True

    @staticmethod
    def check_mnt_camps(shop_id):
        mnt_camp_list = MntMnger.check_mnt_campaigns(shop_id)
        prority = 0
        adg_tuple_list = []
        impt_camp_id_list = []
        for mnt_camp in mnt_camp_list:
            if mnt_camp.mnt_type in [2, 4]:
                impt_camp_id_list.append(mnt_camp.campaign_id)
                prority += 1

        if impt_camp_id_list:
            init_start_time = datetime.datetime.now() - datetime.timedelta(days = Keyword.Report.INIT_DAYS)
            adg_cursor = adg_coll.find({'shop_id':shop_id, 'campaign_id':{'$in':impt_camp_id_list}, 'mnt_type':{'$in':[2, 4]}, 'offline_type':'online', 'online_status':'online'}, {'_id':1, 'campaign_id':1, 'kwrpt_sync_time':1})
            adg_tuple_list = [(adg['_id'], adg['campaign_id'], adg.get('kwrpt_sync_time', init_start_time)) for adg in adg_cursor]

        return prority, adg_tuple_list

    @staticmethod
    def get_limited_url():
        return reverse('upgrade_suggest')

    @staticmethod
    def get_longtail_camp_ids(shop_id):
        """获取长尾计划的计划ID列表"""
        return list(MntCampaign.objects.filter(shop_id = shop_id, mnt_type__in = [1, 3]).values_list('campaign_id'))

    @staticmethod
    def unmnt_campaign(shop_id, campaign_id):
        """终止掉托管计划"""
        from apps.mnt.models_task import MntTaskMng
        Adgroup.objects.filter(shop_id = shop_id, campaign_id = campaign_id).update(set__mnt_type = 0, set__mnt_time = None)
        MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id).delete()
        MntTaskMng.remove_task(shop_id = shop_id, campaign_id = campaign_id)

    @staticmethod
    def set_mnt_camp(campaign_id, flag, mnt_type, opter = 3, opter_name = '', **kwargs):
        """托管计划设置器，flag标识开启或者关闭"""
        from apps.subway.upload import update_campaign, set_cmp_mnt_status_log
        try:
            campaign = Campaign.objects.get(campaign_id = campaign_id)
        except DoesNotExist:
            log.info('can not find campaign, campaign_id = %s' % campaign_id)
            return None

        set_dict = {'mnt_status':flag}
        max_num_dict = {1: 500, 2: 10 , 3: 50, 4: 10}
        max_num = max_num_dict.get(mnt_type, 10)
        if flag:
            # TODO: wangqi 20151019 这里检查是否有权限创建
            if not MntMnger.check_create_mnt(campaign.shop_id):
                raise Exception("no_permission")

            set_dict.update({'online_status':'online',
                             'budget':kwargs['budget'],
                             'use_smooth':'true',
                             })

            if kwargs.get('area', 0) != 0:
                if campaign.area == 'all':
                    area_list = Const.CAMP_AREA
                else:
                    area_list = campaign.area.split(',')
                new_area_list = list(set(area_list) - {'599', '576', '578', '574'}) # 后面的数字，分别是港澳台国外，{1,2,3}是set初始化方法
                new_areas = ','.join(new_area_list)
                set_dict.update({'area': new_areas})
            if kwargs.get('platform', 0) != 0:
                set_dict.update({'search_channels':'1,2,4,8,16',
                                 'nonsearch_channels':'1,2,8,16',
                                 'outside_discount':60,
                                 'mobile_discount':110
                                 })
            if kwargs.get('schedule', 0) != 0:
                set_dict.update({'schedule':'00:00-01:00:45,01:00-08:00:35,08:00-09:00:70,09:00-14:00:75,14:00-17:00:100,17:00-19:00:80,19:00-20:30:100,20:30-23:00:105,23:00-24:00:100;\
00:00-01:00:45,01:00-08:00:35,08:00-09:00:70,09:00-14:00:75,14:00-17:00:100,17:00-19:00:80,19:00-20:30:100,20:30-23:00:105,23:00-24:00:100;\
00:00-01:00:45,01:00-08:00:35,08:00-09:00:70,09:00-14:00:75,14:00-17:00:100,17:00-19:00:80,19:00-20:30:100,20:30-23:00:105,23:00-24:00:100;\
00:00-01:00:45,01:00-08:00:35,08:00-09:00:70,09:00-14:00:75,14:00-17:00:100,17:00-19:00:80,19:00-20:30:100,20:30-23:00:105,23:00-24:00:100;\
00:00-01:00:45,01:00-08:00:35,08:00-09:00:70,09:00-14:00:75,14:00-17:00:100,17:00-19:00:80,19:00-20:30:100,20:30-23:00:105,23:00-24:00:100;\
00:00-01:00:50,01:00-08:00:35,08:00-10:00:65,10:00-14:00:75,14:00-17:00:100,17:00-19:00:80,19:00-20:30:100,20:30-23:00:105,23:00-24:00:100;\
00:00-01:00:50,01:00-08:00:35,08:00-10:00:65,10:00-14:00:75,14:00-17:00:100,17:00-19:00:80,19:00-20:30:100,20:30-23:00:105,23:00-24:00:100'})

#             mnt_desc = mnt_type == 1 and '长尾托管' or '重点托管'
#             set_dict.update({'title':'开车精灵-%s%s' % (mnt_desc, kwargs['mnt_index'])})

            if kwargs.has_key('max_price') and kwargs['max_price'] > 0:
                set_dict.update({'max_price':kwargs['max_price']})

            if kwargs.has_key('mobile_max_price') and kwargs['mobile_max_price'] > 0:
                set_dict.update({'mobile_max_price':kwargs['mobile_max_price']})
            result_list, msg_list = update_campaign(shop_id = campaign.shop_id, campaign_id = campaign.campaign_id, opter = opter, opter_name = opter_name, **set_dict)

            create_args = {'shop_id':campaign.shop_id, 'campaign_id': campaign.campaign_id, 'mnt_index': kwargs['mnt_index'], 'mnt_type': mnt_type,
                           'max_num': max_num, 'mnt_cfg_list': []}
            if mnt_type in [2, 4]:
                create_args.update({
                    'max_price': kwargs.get('max_price', 200),
                    'mobile_max_price': kwargs.get('mobile_max_price', 200),
                    'mnt_rt': kwargs.get('mnt_rt', 0),
                    'mnt_bid_factor': kwargs.get('mnt_bid_factor', 50),
                    'opt_wireless': kwargs.get('opt_wireless', 0),
                })
            elif mnt_type in [1, 3]:
                create_args.update({
                    'max_price': kwargs.get('max_price', 200),
                    'mobile_max_price': kwargs.get('mobile_max_price', 200),
                    'mnt_bid_factor': kwargs.get('mnt_bid_factor', 50),
                    'opt_wireless': kwargs.get('opt_wireless', 0)
                })
            MntCampaign.objects.create(**create_args)
        else:
            msg_list = []
#             campaign.rpt_days = 7
#             if campaign.rpt_sum.roi < 1.5 and '开车精灵' in campaign.title or '开車精灵' in campaign.title:
#                 set_dict['title'] = '推广计划%s' % time.strftime('%m%d%H%M')
            campaign.rpt_sum = campaign.get_summed_rpt(rpt_days = 15)
            if campaign.rpt_sum.roi < 1 and ('开车精灵-' in campaign.title or '开車精灵-' in campaign.title or '无线精灵-' in campaign.title or not flag):
                set_dict['title'] = campaign.title.replace('开车精灵-', '').replace('开車精灵-', '').replace('无线精灵-', '')
                result_list, msg_list = update_campaign(shop_id = campaign.shop_id, campaign_id = campaign.campaign_id, opter = opter, opter_name = opter_name, **set_dict)
            MntMnger.unmnt_campaign(shop_id = campaign.shop_id, campaign_id = campaign.campaign_id)

        CacheAdpter.delete(CacheKey.WEB_MNT_MENU % campaign.shop_id, 'web')
        warn_msg_dict = {}
        if msg_list:
            warn_dict = {'名称或状态': 'title_status', '日限额': 'budget', '投放地域': 'area', '分时折扣': 'schedule', '平台设置': 'platform'}
            for msg in msg_list:
                for warn_str, warn_key in warn_dict.items():
                    if warn_str in msg:
                        warn_msg_dict[warn_key] = msg
                        break

        return warn_msg_dict


    @staticmethod
    def set_mnt_adgroup(shop_id, campaign_id, adg_cfg_dict, opter = 3, opter_name = ''):
        """将推广组添加托管，并设置个性化参数"""

        def take_adg_online(adg_id_list):
            from apps.subway.upload import update_adgroups
            adg_id_list_offline = list(Adgroup.objects.filter(shop_id = shop_id, adgroup_id__in = adg_id_list, online_status = 'offline').values_list('adgroup_id'))
            if adg_id_list_offline:
                adg_arg_dict = {}
                for id in adg_id_list_offline:
                    adg_arg_dict[id] = {'online_status':'online'}
                try:
                    update_adgroups(shop_id = shop_id, adg_arg_dict = adg_arg_dict, opter = opter, opter_name = opter_name)
                except Exception, e:
                    log.error('mnt update_adg_mnt error,shop_id=%s, campaign_id = %s, e = %s' % (shop_id, campaign_id, e))
            return True

        try:
            mnt_camp = MntCampaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
        except DoesNotExist:
            return True

        exist_mnt_count = adg_coll.find({'shop_id': shop_id, 'campaign_id': campaign_id, 'mnt_type': mnt_camp.mnt_type}).count()
        remain_mnt_count = mnt_camp.max_num - exist_mnt_count
        remain_mnt_count = remain_mnt_count > 0 and remain_mnt_count or 0

        added_adg_id_list = []
        if remain_mnt_count > 0:
            from apps.mnt.models_task import MntTaskMng
            from apps.subway.upload import modify_cmp_adg_log

            update_list = []
            update_dict = {'mnt_type': mnt_camp.mnt_type, 'mnt_time': datetime.datetime.now()}
            for adg_id, cfg_dict in adg_cfg_dict.items()[:remain_mnt_count]:
                temp_dict = {
                    'mnt_opt_type': int(cfg_dict.get('mnt_opt_type') or 1),
                    'limit_price': int(cfg_dict.get('limit_price') or 200),
                    'mobile_limit_price': int(cfg_dict.get('mobile_limit_price') or 200),
                    'use_camp_limit': int(cfg_dict.get('use_camp_limit', 1))
                }
                temp_dict.update(update_dict)
                update_list.append(({'shop_id': shop_id, 'campaign_id': campaign_id, '_id': int(adg_id)}, {'$set': temp_dict}))
                added_adg_id_list.append(adg_id)
            Adgroup.bulk_update_adg2db(update_list)

            take_adg_online(added_adg_id_list)

            descr = '加入托管'
            modify_cmp_adg_log(shop_id = shop_id, campaign_id = campaign_id, adg_id_list = added_adg_id_list, opt_desc = descr, opter = opter, opter_name = opter_name)
            MntTaskMng.upsert_task(shop_id = shop_id, campaign_id = campaign_id, mnt_type = mnt_camp.mnt_type, task_type = 1, adgroup_id_container = {'changed':[], 'added':added_adg_id_list})

        return True

    @staticmethod
    def unmnt_adgroup(shop_id, campaign_id, adg_id_list, opter = 3, opter_name = ''):
        """将推广组解除托管"""
        from apps.subway.upload import modify_cmp_adg_log

        adg_coll.update({'shop_id': shop_id, 'campaign_id':campaign_id, '_id':{'$in': adg_id_list}}, {'$set': {'mnt_type': 0, 'mnt_time': None}})
        descr = '取消托管'
        modify_cmp_adg_log(shop_id = shop_id, campaign_id = campaign_id, adg_id_list = adg_id_list, opt_desc = descr, opter = opter, opter_name = opter_name)
        return True


MNT_TYPE_CHOICES = ((0, "未托管"), (1, "长尾托管"), (2, "重点托管"), (3, "ROI托管"), (4, "无线托管"))
class MntCampaign(Document):
    # STRATEGY_CHOICES = ((0, '系统智能优化'), (1, '加大投入'), (2, '减小投入'))
    MNT_STATUS_CHOICES = ((0, "暂停自动优化"), (1, "开启自动优化"))
    OPAR_STATUS_CHOICES = ((0, '系统自动优化'), (1, 'AE手工操作'))

    """还是采用传统的方法来操作，因为继承有个映射的问题"""
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "推广计划ID", primary_key = True)

    mnt_status = IntField(verbose_name = "监控状态", choices = MNT_STATUS_CHOICES, default = 1)
    mnt_type = IntField(verbose_name = "监控类型", choices = MNT_TYPE_CHOICES, default = 1)
    mnt_index = IntField(verbose_name = "引擎号", default = 1)
    max_num = IntField(verbose_name = "最多托管宝贝个数", default = 100)

    # 优化配置
    mnt_rt = IntField(verbose_name = "是否开启实时优化", default = 0)
    max_price = IntField(verbose_name = "关键词最高限价", default = 50)
    mobile_max_price = IntField(verbose_name = "移动关键词最高限价", default = 0)
    mnt_bid_factor = IntField(verbose_name = "算法导向", default = 50) # 50表示均衡,越小越偏ROI,越大越偏流量
    opt_wireless = IntField(verbose_name = "是否优化无线折扣", default = 1)

    start_time = DateTimeField(verbose_name = '启动时间', default = datetime.datetime.now)
    quick_optime = DateTimeField(verbose_name = "加大投入/减少投入操作时间") # TODO: wangqi 2013-12-19 这里只能控制一天一次的情况，更复杂的控制，可能需要在timer里定时重置次数控制

    opar_status = IntField(verbose_name = "CRM操作状态", choices = OPAR_STATUS_CHOICES, default = 0)

    task_time = DateTimeField(verbose_name = "例行任务生成时间")
    task_time_dict = DictField(verbose_name = "例行任务生成时间", default = {})
    optimize_time = DateTimeField(verbose_name = "系统优化时间") # 任务执行后写回，用于标识该计划最新的优化时间
    modify_camp_title_time = DateTimeField(verbose_name = "软件自动改计划名的时间") # 用于定期根据报表修改计划名
    mnt_cfg_list = ListField(verbose_name = "全自动配置", default = ['cw_mnt_cfg'])
    cycle_cfg = StringField(verbose_name = "周期配置", default = 'cw_cycle_cfg')
    stgy_cfg = StringField(verbose_name = "策略配置", default = 'cw_stgy_cfg')
    opt_cfg = StringField(verbose_name = "操作配置", default = 'cw_opt_cfg')

    meta = {"db_alias": "mnt-db", 'collection':'mnt_campaign', 'indexes':['shop_id']}

    @property
    def real_mobile_max_price(self):
        return self.mobile_max_price or self.max_price

    @property
    def campaign(self):
        """获取当前推广组的所属计划"""
        if not hasattr(self, '_campaign'):
            self._campaign = Campaign.objects.get(shop_id = self.shop_id, campaign_id = self.campaign_id)
        return self._campaign

    @campaign.setter
    def campaign(self, campaign):
        """获取当前推广组的所属计划"""
        self._campaign = campaign

    def get_adgroup_sum_cost(self, rpt_days):
        result_list = Adgroup.Report.aggregate_rpt(query_dict = {'shop_id': self.shop_id, 'campaign_id': self.campaign_id},
                                                   group_keys = 'campaign_id', rpt_days = rpt_days)
        if result_list:
            return result_list['cost']
        else:
            return 0

    @staticmethod
    def get_mnt_max_num(shop_id, campaign_id):
        """获取计划最大托管宝贝数"""
        campaigns = MntCampaign.objects.filter(shop_id = shop_id, campaign_id = campaign_id)
        if campaigns:
            return campaigns[0].max_num
        else:
            return 0

    @staticmethod
    def get_gsw_recm_price(shop_id):
        """通过该店推广宝贝最多的类目来取PPC"""
        from apps.subway.models_account import account_coll
        from apps.engine.utils import refresh_shop_cat

        recm_price = ''
        try:
            shop_id = int(shop_id)
            acct_obj = account_coll.find_one({'_id':shop_id}, {'cat_id':1})
            if acct_obj:
                if acct_obj.has_key('cat_id') and acct_obj['cat_id']:
                    cat_id = acct_obj['cat_id']
                else:
                    cat_id = refresh_shop_cat(shop_id)

            if cat_id:
                cat_info = CatStatic.get_market_data_8id(cat_id)
                recm_price = round(cat_info.get('cpc', 0) * 0.01, 2)
                if recm_price < 0.2 or recm_price > 5:
                    recm_price = recm_price > 5 and 5 or 0.2
                recm_price = '%.2f' % float(recm_price)
        except Exception, e:
            log.error('get_mnt_recommended_price error, shop_id=%s, e=%s' % (shop_id, e))
        return recm_price

    @property
    def adgroup_id_list(self):
        """获取托管中的adgroup_id_list"""
        if not hasattr(self, '_adgroup_id_list'):
            self._adgroup_id_list = [adg['_id'] for adg in adg_coll.find({'shop_id':self.shop_id, 'campaign_id':self.campaign_id, 'mnt_type':self.mnt_type, 'offline_type':'online', 'online_status':'online'}, {'_id':1})]
        return self._adgroup_id_list

    @property
    def is_active(self):
        """根据计划是否暂停判断托管是否激活"""
        if not hasattr(self, '_is_active'):
            self._is_active = (self.campaign.online_status == 'online' and True or False) and bool(self.mnt_status)
        return self._is_active

    @classmethod
    def get_mnt_campaigns(cls, shop_id):
        """获取托管的计划"""
        types = filter(lambda obj : obj , [flag for flag, _ in MNT_TYPE_CHOICES])
        return cls.objects.filter(shop_id = shop_id, mnt_type__in = types)

    @classmethod
    def get_unmnt_campaigns(cls, shop_id):
        """获取未被托管的计划"""
        mnt_id_list = [mnt.campaign_id for mnt in cls.get_mnt_campaigns(shop_id)]
#         return Campaign.objects.filter(shop_id = shop_id).exclude(campaign_id__in = mnt_ids)
        camp_list = Campaign.objects.filter(shop_id = shop_id)
        return itertools.ifilter(lambda obj : obj.campaign_id not in mnt_id_list , camp_list)

mnt_camp_coll = MntCampaign._get_collection()
