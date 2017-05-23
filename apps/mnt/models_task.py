# coding=UTF-8
import datetime
import random
import time

from mongoengine.document import Document
from mongoengine.errors import DoesNotExist
from mongoengine.fields import IntField, DateTimeField, ObjectIdField, StringField, ListField

from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.subway.models_account import Account
from apps.subway.models_campaign import Campaign
from apps.subway.models_adgroup import adg_coll
from apps.subway.models_upload import UploadRecord
from apps.subway.upload import update_campaign
from apps.subway.download import Downloader
from apps.mnt.models_mnt import MntCampaign, mnt_camp_coll, MNT_TYPE_CHOICES
from apps.ncrm.models import Subscribe
from apps.alg.interface import optimize_adgroups, auto_optimize_campaign, check_price_4adgroups, temp_strategy_optimize_adgroups


def check_mnt_camp_title(shop_id, mnt_camp_list):
    camp_id_list = []
    today = datetime.datetime.now()
    try:
        for mnt_camp in mnt_camp_list:
            is_first = not mnt_camp.modify_camp_title_time and today >= mnt_camp.start_time + datetime.timedelta(days = 7)
            # is_long_time = mnt_camp.modify_camp_title_time and today >= mnt_camp.modify_camp_title_time + datetime.timedelta(days = 15) or False
            if is_first:
                camp_id_list.append(mnt_camp.campaign_id)

        if not camp_id_list:
            return True

        camps = Campaign.objects.filter(shop_id = shop_id, campaign_id__in = camp_id_list)
        camp_rpt_dict = Campaign.Report.get_summed_rpt({'shop_id': shop_id, 'campaign_id':{'$in': camp_id_list}}, rpt_days = 15)
        result_id_list = []
        for camp in camps:
            if '开车精灵-' in camp.title:
                continue
            camp_rpt = camp_rpt_dict.get(camp.campaign_id, None)
            if camp_rpt and camp_rpt.roi >= 1:
                new_title = '开车精灵-' + camp.title.replace('无线精灵-', '').replace('开車精灵-', '')
                result, _ = update_campaign(shop_id = camp.shop_id, campaign_id = camp.campaign_id, title = new_title, opter = 3, opter_name = '')
                if result:
                    result_id_list.append(camp.campaign_id)
        if result_id_list:
            mnt_camp_coll.update({'_id': {'$in': result_id_list}},
                                 {'$set': {'modify_camp_title_time': datetime.datetime.now()}},
                                 multi = True
                                 )
        return True
    except Exception, e:
        log.error('e = %s' % e)
        return False


class UserOptimizeRecord(Document):
    shop_id = IntField(verbose_name = "店铺ID")
    psuser_id = IntField(verbose_name = '用户ID', required = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)

    meta = {'db_alias': "mnt-db", 'collection': 'mnt_useroptrecord', 'indexes':['psuser_id', 'shop_id']}

    @classmethod
    def get_opted_shop_list(cls, shop_id_list):
        today = datetime.datetime.now()
        user_record_cur = cls._get_collection().find({'shop_id': {'$in': shop_id_list}, 'create_time': {'$gte': datetime.datetime(today.year, today.month, today.day)}},
                                                     {'shop_id': 1})
        opted_shopid_list = [ur['shop_id'] for ur in user_record_cur]
        return list(set(opted_shopid_list))

    @classmethod
    def bulk_add_records(cls, shop_id_list, psuser_id):
        insert_list = []
        for shop_id in set(shop_id_list):
            insert_list.append({'shop_id': shop_id, 'psuser_id': psuser_id, 'create_time': datetime.datetime.now()})
        if insert_list:
            user_optrecord_coll.insert(insert_list)
        return

user_optrecord_coll = UserOptimizeRecord._get_collection()


class MntTaskMng(object):
    """用于管理Task的创建，更改，获取要执行的队列，执行任务"""

    @classmethod
    def check_routine_task(cls, shop_id):
        """检查店铺的例行任务"""

        mnt_camps = MntCampaign.objects.filter(shop_id = shop_id, mnt_status = 1)
        mnt_camp_list = [obj for obj in mnt_camps]
        check_mnt_camp_title(shop_id, mnt_camp_list)

        opt_list = [{'func': 'routine_optimmize', 'args': {}}]
        for mnt_camp in mnt_camp_list:
            if not mnt_camp.is_active: # 如果计划暂停，则不生成任务
                continue
            # 如果是启动中的，则将暂停中的任务激活
            cls.trigger_task_status(shop_id = mnt_camp.shop_id, campaign_id = mnt_camp.campaign_id, trigger_flag = True)
            cls.build_task(shop_id = mnt_camp.shop_id, campaign_id = mnt_camp.campaign_id, create_time = datetime.datetime.now(),
                           status = 'ready', mnt_type = mnt_camp.mnt_type, task_type = 0, opt_list = opt_list)
        return

    @classmethod
    def upsert_task(cls, shop_id, campaign_id, mnt_type, task_type = 1, **kwargs):
        opt_list = []
        if task_type == 1:
            adgroup_id_container = kwargs['adgroup_id_container']
            if isinstance(adgroup_id_container, list):
                return True
            elif isinstance(adgroup_id_container, dict):
                changed_adg_id_list = adgroup_id_container['changed']
                added_adg_id_list = adgroup_id_container.get('added', [])
                added_adg_id_list.extend(changed_adg_id_list)
                if added_adg_id_list:
                    opt_list = [{'func': 'optimize_adgroups', 'args': {'adgroup_id_list': added_adg_id_list, 'strategy_name':''}}]
        elif task_type == 2:
            opt_list = [{'func': 'check_price', 'args': {'adgroup_id_list': kwargs['adgroup_id_list']}}]

        if opt_list:
            cls.build_task(shop_id = shop_id, campaign_id = campaign_id, create_time = datetime.datetime.now(),
                           status = 'ready', mnt_type = mnt_type, task_type = task_type, opt_list = opt_list)

        return

    @classmethod
    def generate_quickop_task(cls, shop_id, campaign_id, mnt_type, stgy, adgroup_id_list = []):
        strategy_name = stgy == 1 and 'IncreaseCost' or 'ReduceCost'
        opt_list = [{'func': 'optimize_adgroups', 'args': {'adgroup_id_list': adgroup_id_list, 'strategy_name': strategy_name}}]
        cls.build_task(shop_id = shop_id, campaign_id = campaign_id, create_time = datetime.datetime.now(),
                       status = 'ready', mnt_type = mnt_type, task_type = 4, opt_list = opt_list)
        return

    @classmethod
    def bulk_generate_task_bycmd(cls, shop_id_list, psuser_id, opter_name, strategy_name = '', kw_cmd_list = [], adg_cmd_list = []):
        """将广告组先分组，再生成任务"""

        opted_shopid_list = UserOptimizeRecord.get_opted_shop_list(shop_id_list)
        unopt_shopid_list = list(set(shop_id_list) - set(opted_shopid_list))
        mnt_camp_list = list(mnt_camp_coll.find({'shop_id': {'$in': unopt_shopid_list}}, {'shop_id': 1, '_id': 1, 'mnt_type': 1}))

        args_dict = {'adgroup_id_list': 'ALL', 'opter_name': opter_name}
        if strategy_name:
            args_dict.update({'strategy_name': strategy_name})
        else:
            args_dict.update({'kw_cmd_list': kw_cmd_list, 'adg_cmd_list': adg_cmd_list})

        insert_list = []
        new_shop_id_list = []
        for mnt_camp in mnt_camp_list:
            task_dict = {'shop_id': mnt_camp['shop_id'], 'campaign_id': mnt_camp['_id'],
                         'mnt_type': mnt_camp['mnt_type'], 'create_time': datetime.datetime.now(),
                         'failed_count': 0, 'status': 'ready', 'task_type': 3,
                         'opt_list': [{'func': 'sync_all_rpt', 'args': {}},
                                      {'func': 'custom_optimize_adgroup', 'args': args_dict}
                                      ]
                         }
            insert_list.append(task_dict)
            new_shop_id_list.append(mnt_camp['shop_id'])
        new_shop_id_list = list(set(new_shop_id_list))

        result_id_list = []
        if insert_list:
            result_id_list = mnt_task_coll.insert(insert_list)

        UserOptimizeRecord.bulk_add_records(new_shop_id_list, psuser_id)
        return len(new_shop_id_list), len(result_id_list)

    @classmethod
    def build_task(cls, **kwargs):
        return MntTask.objects.create(**kwargs)

    @classmethod
    def remove_task(cls, **kwargs):
        """移除符合条件的任务，用于两种场景：1，托管任务被取消时删除全部任务；2，单个任务检测到托管计划不存在"""
        MntTask.objects.filter(**kwargs).delete()

    @classmethod
    def run_task(cls, task, is_force = False):
        """任务的执行流程
        1.检查任务是否可执行，不能则状态设置为未激活
        2.执行任务，执行成功与失败均会记录状态，失败时会记录失败状态
        """
        is_runnable, reason = task.is_runnable(is_force)
        if not is_runnable:
            if reason in ['not_callable', 'failed_too_much']:
                task.save_log(check_desc = "授权过期，无法优化")
                task.update_task_status(status = 'deactive')
            elif reason == 'mnt_camp_not_active':
                task.save_log(check_desc = "计划暂停，暂停优化")
                task.update_task_status(status = 'paused')
            elif reason == 'mnt_camp_not_found':
                task.save_log(check_desc = "托管计划已取消，不再优化")
                cls.remove_task(id = task.id)
            elif reason == 'shop_banlance_is_less':
                task.save_log(check_desc = "店铺余额不足，放弃优化")
                cls.remove_task(id = task.id)
            log.info('[timer][mnt_task_result][unable]: shop_id=%s, campaign_id=%s, task_id=%s, reason=%s' % (task.shop_id, task.campaign_id, task.id, reason))
            return False
        else:
            task.update_task_status(status = 'doing', start_time = datetime.datetime.now()) # 尽管在取任务处有马上改时间，但这里最好也改一下，因为可能是用户触发的
            result = task.run()
            update_args = {'end_time':datetime.datetime.now()}
            if result:
                log.info('[timer][mnt_task_result][ok]: shop_id=%s, campaign_id=%s, opt_list=%s' % (task.shop_id, task.campaign_id, task.opt_list))
                task.save_log(check_desc = "系统已优化")
                task.report_progress() # 报告
                cls.remove_task(id = task.id)
            else:
                log.info('[timer][mnt_task_result][failed]: shop_id=%s, campaign_id=%s, opt_list=%s' % (task.shop_id, task.campaign_id, task.opt_list))
                update_args.update({'status':'failed', 'failed_count':task.failed_count + 1})
                task.update_task_status(**update_args)
            return result

    @classmethod
    def get_valid_task(cls, task_type, need_count):
        """获取对应的任务类型的队列"""

        def is_accessible():
            is_mutual = CacheAdpter.get(CacheKey.MNT_MUTUAL_LOCK % task_type, 'web')
            loop_count = 0
            while (loop_count < 10):
                loop_count += 1
                if not is_mutual:
                    return True
                else:
                    time.sleep(random.randint(1, 5))
                    is_mutual = CacheAdpter.get(CacheKey.MNT_MUTUAL_LOCK % task_type, 'web')
            return False

        valid_id_list = []
        if not is_accessible():
            return valid_id_list
        else:
            try:
                CacheAdpter.set(CacheKey.MNT_MUTUAL_LOCK % task_type, True, 'web', 60 * 2)
                # test_shop_id_list = Config.get_value('mnt.TEST_SHOP_IDLIST', default = [])
                query_value = task_type != 0 and {'$gt':0} or 0 # 例行任务都是0，快速均大于1
                recycle_time = datetime.datetime.now() - datetime.timedelta(hours = 6) # 回收6个小时以前，状态仍然是已分配、执行中、执行失败的任务。
                cursor = mnt_task_coll.find({'task_type':query_value,
                                             # 'shop_id': {'$nin': test_shop_id_list},
                                             '$or':[{'status':'ready'},
                                                    {'status':{'$in':['allocated', 'doing', 'failed']}, 'start_time':{'$lte':recycle_time}}
                                                    ]},
                                            {'_id':1}).sort([('create_time', 1)])

                cursor = cursor.limit(need_count)
                valid_id_list = [i['_id'] for i in cursor]
                if valid_id_list:
                    mnt_task_coll.update({'_id':{'$in':valid_id_list}}, {'$set':{'status':'allocated', 'start_time':datetime.datetime.now()}}, multi = True)
                return valid_id_list
            except Exception, e:
                log.error("task_type=%s, get_task error, e=%s" % (task_type, e))
                return valid_id_list
            finally:
                CacheAdpter.delete(CacheKey.MNT_MUTUAL_LOCK % task_type, 'web') # 清除缓存，把门打开

    @classmethod
    def trigger_task_status(cls, shop_id, campaign_id, trigger_flag = True):
        if trigger_flag: # 将暂停的任务改成准备中
            mnt_task_coll.update({'shop_id':shop_id, 'campaign_id':campaign_id, 'status':'paused'}, {'$set':{'status':'ready'}}, multi = True)
        else: # 将任务状态改成暂停
            mnt_task_coll.update({'shop_id':shop_id, 'campaign_id':campaign_id, 'status':{'$ne':'deactive'}}, {'$set':{'status':'paused'}}, multi = True)


class MntTask(Document):
    """全自动计划任务"""

    TASK_TYPE_CHOICES = ((0, '例行任务'), (1, '快速任务-添加宝贝'), (2, '快速任务-修改限价'), (3, '命令生成任务'), (4, '快速任务-加大/减小投入'))
    STATUS_CHOICES = (('deactive', '未激活'), ('ready', '准备中'), ('allocated', '已分配'), ('doing', '执行中'), ('successed', '执行成功'), ('failed', '执行失败'), ('paused', '优化暂停'))

    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "推广计划ID", required = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    task_type = IntField(verbose_name = '任务类型', default = 0, choices = TASK_TYPE_CHOICES)
    mnt_type = IntField(verbose_name = "监控类型", choices = MNT_TYPE_CHOICES, default = 1)
    start_time = DateTimeField(verbose_name = "执行时间", default = None)
    end_time = DateTimeField(verbose_name = "结束时间", default = None)
    status = StringField(verbose_name = "任务执行时间", default = 'ready', choices = STATUS_CHOICES)
    failed_count = IntField(verbose_name = "任务失败次数", default = 0)
    opt_list = ListField(verbose_name = "任务执行操作列表", default = []) # 形如:[{'func':'add_keywords', 'args':'{}'},{'func':'optimize_keywords', 'args':'{}'}], 由json序列化
    reporter = ObjectIdField(verbose_name = "任务报告者", default = None)

    meta = {'db_alias': "mnt-db", 'collection':'mnt_task', 'indexes':['shop_id', 'campaign_id', 'task_type']}

    @property
    def mnt_campaign(self):
        """获取当前任务对应的计划"""
        if not hasattr(self, '_mnt_campaign'):
            try:
                mnt_camp = MntCampaign.objects.get(shop_id = self.shop_id, campaign_id = self.campaign_id)
            except DoesNotExist:
                mnt_camp = None
            self._mnt_campaign = mnt_camp
        return self._mnt_campaign

    def is_runnable(self, is_force = False): #
        """检查是否可以执行：
        1.是否有api权限
        2.对应的全自动计划，且全计划未暂停，自动计划是托管中
        3.失败次数超过3次，且非强制执行
        """
        dler = Downloader.objects.get(shop_id = self.shop_id)
        if not dler.tapi: # api不可用
            return False, 'not_callable'
        if not self.mnt_campaign: # 托管计划不存在
            return False, 'mnt_camp_not_found'

        # return True, 'OK'

        if self.task_type == 0: # 只检查例行任务，因为快速任务是用户手动触发的，需要立即执行
            if not self.mnt_campaign.is_active: # 托管计划被暂停
                return False, 'mnt_camp_not_active'
            account = Account.objects.get(shop_id = self.shop_id)
            if account.is_keep_stop:
                return False, 'shop_banlance_is_less'

        if self.failed_count >= 3 and (not is_force): # 后台执行失败超过3次
            return False, 'failed_too_much'

        return True, 'OK'

    def save_log(self, check_desc):
        try:
            UploadRecord.objects.create(shop_id = self.shop_id, campaign_id = self.campaign_id, op_type = 1, data_type = 113, detail_list = [check_desc], opter = 3)
        except Exception, e:
            log.error('save mnt log error, shop_id=%s, camp_id=%s, desc=%s, e=%s' % (self.shop_id, self.campaign_id, check_desc, e))
        return

    def update_task_status(self, **update_dict):
        for attr, value in update_dict.items():
            setattr(self, attr, value)
        mnt_task_coll.update({'_id':self.id}, {'$set':update_dict})

    def report_progress(self):
        mnt_camp_coll.update({'_id':self.campaign_id}, {'$set':{'optimize_time':datetime.datetime.now()}})
        return

    def get_all_adgroup_idlist(self):
        adg_cur = adg_coll.find({'shop_id': self.shop_id, 'campaign_id': self.campaign_id, 'mnt_type': self.mnt_type})
        adgroup_id_list = [adg['_id'] for adg in adg_cur]
        return adgroup_id_list

    def run(self):
        """运行任务"""
        try:
            if not Downloader.download_all_struct(shop_id = self.shop_id):
                return False
            for opt in self.opt_list:
                try:
                    getattr(self, opt['func'])(**opt['args'])
                except Exception, e: # 现在 opt_list 只有一个任务，错误直接上抛
                    log.error('mnt run task step %s(%s) error, shop_id=%s, camp_id=%s, e=%s'
                              % (opt['func'], opt['args'], self.shop_id, self.campaign_id, e))
                    raise Exception
            log.info('mnt task ran OK, shop_id=%s' % self.shop_id)
            return True
        except Exception, e:
            log.error('mnt task ran FAILED, shop_id=%s, e=%s' % (self.shop_id, e))
            return False

    def sync_all_rpt(self):
        if not Downloader.download_all_rpt(shop_id = self.shop_id, detail_flag = False):
            raise Exception('sync_all_rpt failed')
        return True

    def optimize_adgroups(self, adgroup_id_list, strategy_name = ''):
        if adgroup_id_list == 'ALL': # 先简单处理
            adgroup_id_list = self.get_all_adgroup_idlist()
        adgroup_id_list_i = [int(adgroup_id) for adgroup_id in adgroup_id_list]
        optimize_adgroups(self.shop_id, self.campaign_id, adgroup_id_list_i, strategy_name)
        return

    def routine_optimmize(self):
        auto_optimize_campaign(self.shop_id, self.campaign_id)
        return

    def check_price(self, adgroup_id_list):
        if adgroup_id_list == 'ALL': # 先简单处理
            adgroup_id_list = self.get_all_adgroup_idlist()
        adgroup_id_list_i = [int(adgroup_id) for adgroup_id in adgroup_id_list]
        check_price_4adgroups(self.shop_id, self.campaign_id, adgroup_id_list_i)
        return

    def custom_optimize_adgroup(self, adgroup_id_list, opter_name, strategy_name = '', kw_cmd_list = [], adg_cmd_list = []):
        if adgroup_id_list == 'ALL': # 先简单处理
            adgroup_id_list = self.get_all_adgroup_idlist()
        adgroup_id_list_i = [int(adgroup_id) for adgroup_id in adgroup_id_list]
        temp_strategy_optimize_adgroups(self.shop_id, self.campaign_id, adgroup_id_list_i, strategy_name, kw_cmd_list, adg_cmd_list, opter_name)
        return

mnt_task_coll = MntTask._get_collection()
