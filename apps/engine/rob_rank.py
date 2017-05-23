# coding=UTF-8

import datetime, time
from threading import Thread
import signal
import random
import traceback
from django.core.mail import send_mail
from mongoengine.queryset.visitor import Q

import settings
from apilib import get_tapi

from apps.common.utils.utils_log import log

from apps.router.models import User
from apps.common.biz_utils.utils_permission import RANKING_CODE, AUTO_RANKING_CODE, test_permission
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.subway.models_adgroup import Adgroup
from apps.subway.models_keyword import Keyword, kw_coll
from apps.subway.upload import update_keywords
from apps.subway.download import Downloader
from apps.engine.models_kwlocker import KeywordLocker, kw_locker_coll


CHANCK_RANK_WATING_TIME = 1  # 改价后等待多少时间后，再去查排名。时间太短，排名没未更新；时间太长，影响任务运行速度。此处根据测试情况来定值


class RobRankTask(object):
    def __init__(self, shop_id, adgroup_id, kw_locker_list, opt_type = 'auto'):
        self.shop_id = shop_id
        self.adgroup_id = adgroup_id
        self.check_time = 0
        self.kw_locker_list = kw_locker_list
        self.unable_reason = ''
        self.opt_type = opt_type
        self.opter = opt_type == 'auto' and 7 or 6
        self.is_moblile = False

    @property
    def tapi(self):
        if not hasattr(self, '_tapi'):
            self._tapi = get_tapi(shop_id = self.shop_id)
        return self._tapi

    @property
    def nick(self):
        if not hasattr(self, '_nick'):
            try:
                user = User.objects.get(shop_id = self.shop_id)
                self._nick = user.nick
            except Exception, e:
                log.error('can not get user, shop_id=%s, e=%s' % (self.shop_id, e))
                self._nick = ''
        return self._nick

    @property
    def adgroup(self):
        if not hasattr(self, '_adgroup'):
            try:
                self._adgroup = Adgroup.objects.get(shop_id = self.shop_id, adgroup_id = self.adgroup_id)
            except Exception, e:
                log.warn('rob_rank, can not find adg, shop_id=%s, adg_id=%s, e=%s' % (self.shop_id, self.adgroup_id, e))
                self._adgroup = None
        return self._adgroup

    @property
    def campaign(self):
        if not hasattr(self, '_campaign'):
            if self.adgroup is None:
                self._campaign = None
            else:
                self._campaign = self.adgroup.campaign # 因为 Adgroup 模型中经常用 adg.campaign, 这里就不再从数据库中取了。
        return self._campaign

    @property
    def campaign_id(self):
        if not hasattr(self, '_campaign_id'):
            self._campaign_id = self.adgroup.campaign_id
        return self._campaign_id

    def is_runnable(self):
        if self.opt_type == 'auto':
            # 自动抢排名时才校验，手动抢排名时在前面已校验
            try:
                user = User.objects.get(shop_id = self.shop_id)
                if not test_permission(AUTO_RANKING_CODE, user):
                    self.unable_reason = '当前版本不支持自动抢排名'
                    return False
            except Exception, e:
                log.error('can not get user, shop_id=%s' % self.shop_id)
                self.unable_reason = '其他原因'
                return False
            if not Downloader.often_sync_struct(shop_id = self.shop_id):
                self.unable_reason = '同步数据失败'
                return False

        if not self.nick:
            self.unable_reason = '找不到用户'
            return False

        if not self.kw_locker_list:
            self.unable_reason = '没有词'
            return False
        if not self.adgroup:
            self.unable_reason = '找不到词所在的宝贝'
            return False

        # 检查店铺余额
        if not self.tapi:
            self.unable_reason = '调用淘宝api失败'
            return False
        try:
            # tobj_balance = self.tapi.simba_account_balance_get()
            # if tobj_balance.balance <= 0:
            balance = self.tapi.get_account_balance()
            if balance <= 0:
                self.unable_reason = '账户余额不足'
                return False
        except Exception, e:
            log.error('get balance error, shop_id=%s, e=%s' % (self.shop_id, e))
            self.unable_reason = '获取账户余额失败'
            return False
        adg_error = self.adgroup.error_descr(self.campaign)
        if adg_error:
            self.unable_reason = adg_error
            return False
        if self.adgroup.online_status == 'offline':
            self.unable_reson = '宝贝已暂停推广'
            return False
        return True

    def init_data(self):
        kw_id_list = [obj.keyword_id for obj in self.kw_locker_list]
        kw_cur = kw_coll.find({'_id': {'$in': kw_id_list}}, {'max_price': 1, 'max_mobile_price': 1})
        kw_dict = {kw['_id']: {'max_price': kw['max_price'], 'max_mobile_price': kw.get('max_mobile_price', 0)} for kw in kw_cur}
        del_kw_list = []
        if self.adgroup:
            self.is_moblile = self.adgroup.get_mobile_status()
            for kl in self.kw_locker_list:
                temp_kwprice_dict = kw_dict.get(kl.keyword_id, 0)
                if temp_kwprice_dict:
                    if kl.platform == 'pc':
                        kw_cur_price = temp_kwprice_dict['max_price']
                    else:
                        if temp_kwprice_dict['max_mobile_price']:
                            kw_cur_price = temp_kwprice_dict['max_mobile_price']
                        else:
                            mobile_discount = self.adgroup.mobile_discount / 100.0
                            if not mobile_discount:
                                mobile_discount = self.campaign.platform['mobile_discount'] / 100.0
                            kw_cur_price = int(temp_kwprice_dict['max_price'] * mobile_discount)
                    kl.add_alg_property(kw_cur_price)
                else:
                    del_kw_list.append(kl.keyword_id)
        else:
            del_kw_list = [kl.keyword_id for kl in self.kw_locker_list]
        self.kw_locker_list = [kl for kl in self.kw_locker_list if kl.keyword_id not in del_kw_list]
        if del_kw_list:
            kw_locker_coll.remove({'_id': {'$in': del_kw_list}}, multi = True)

    def is_finishing(self):
        for kl in self.kw_locker_list:
            if kl.result_flag == 'doing':
                return False
        return True

    def update_kw_locker_error(self):
        if self.unable_reason:
            for kl in self.kw_locker_list:
                kl.result_flag = 'failed'
                kl.save_process(desc = '%s, 抢排名结束' % self.unable_reason)
        return

    def colse(self):
        self.check_keyword_status()
        if self.opt_type == 'auto':
            next_run_time = datetime.datetime.now() + datetime.timedelta(minutes = random.randint(20, 30))
            locker_id_list = [kl.keyword_id for kl in self.kw_locker_list]
            if locker_id_list:
                kw_locker_coll.update({'shop_id': self.shop_id, 'adgroup_id': self.adgroup_id, '_id': {'$in': locker_id_list}},
                                      {'$set': {'next_run_time': next_run_time, 'is_running': 0}}, multi = True)
                # log.info('update next_run_time, shop_id=%s, next_run_time=%s' % (self.shop_id, next_run_time))
        return

    def get_real_rank(self):
        kw_id_list = []
        for kl in self.kw_locker_list:
            if kl.result_flag != 'doing':
                continue
            if kl.platform == 'yd' and (not self.is_moblile):
                kl.result_flag = 'failed'
                kl.save_process(desc = '没有投放移动平台, 抢排名结束')
            else:
                kw_id_list.append(kl.keyword_id)
        rank_dict = Keyword.batch_get_rt_kw_rank(self.tapi, self.nick, self.adgroup_id, kw_id_list)
        for kl in self.kw_locker_list:
            if kl.result_flag != 'doing':
                continue
            try:
                temp_rank_dict = rank_dict.get(str(kl.keyword_id), {})
                if not temp_rank_dict or ('stat' not in temp_rank_dict):
                    kl.result_flag = 'waiting'
                    kl.fail_reason = '查不到当前排名'
                elif temp_rank_dict['stat'] != '0':
                    kl.result_flag = 'waiting'
                    kl.fail_reason = '查当前排名异常'
                    log.warning('auto_rob_rank: shop_id=%s, kw_id=%s, rank_dict=%s' % (self.shop_id, kl.keyword_id, temp_rank_dict))
                else:
                        kl.cur_rank_dict.update({
                            'pc': int(temp_rank_dict['pc_rank']),
                            'pc_desc': temp_rank_dict['pc_rank_desc'],
                            'yd': int(temp_rank_dict['mobile_rank']),
                            'yd_desc': temp_rank_dict['mobile_rank_desc']
                            })
                        kl.cur_rank = kl.cur_rank_dict[kl.platform]
                        kl.cur_rank_desc = kl.cur_rank_dict['%s_desc' % kl.platform]
                        if kl.cur_rank < 0:
                            kl.result_flag = 'failed'
                            kl.save_process(desc = '%s, 抢排名结束' % kl.cur_rank_desc)
                        elif kl.exp_rank_range[0] > 0 and kl.check_is_ok(kl.cur_rank) and kl.test_price <= kl.limit_price: # 因为如果抢排名成功，但期望排名是第一名，则应该降价
                            kl.result_flag = 'ok'
                            kl.save_process(desc = '%s, 抢排名成功' % kl.cur_rank_desc)
                        else:
                            kl.save_process(desc = '%s, 继续出价' % kl.cur_rank_desc)
            except Exception, e:
                kl.result_flag = 'waiting'
                kl.fail_reason = '查当前排名出错'
                log.error('auto_rob_rank error shop_id=%s, kw_id=%s, rank_dict=%s, e=%s' % (self.shop_id, kl.keyword_id, temp_rank_dict, e))
        return

    def check_keyword_status(self):
        '''在特殊情况下淘宝改价接口异常时，再次尝试改价。正常情况下，到这里时所有关键词都已经抢排名结束了'''
        upd_arg_list = []
        for kl in self.kw_locker_list:
            if kl.result_flag not in kl.fininshed_status_list:
                new_price = min(kl.limit_price, max(kl.old_price, 5))
                if new_price == kl.cur_price:
                    kl.result_flag = 'done'
                    kl.save_process(desc = '抢排名结束')
                else:
                    upd_arg_list.append([self.campaign_id, self.adgroup_id, kl.keyword_id, kl.word, {'max_price': new_price, 'old_price': kl.cur_price}])
                    kl.result_flag = 'failed'
                    kl.save_process(desc = '尝试恢复初始出价%s元, 抢排名结束' % round(kl.old_price / 100.0, 2))
        if upd_arg_list:
            try:
                update_keywords(shop_id = self.shop_id, kw_arg_list = upd_arg_list, opter = self.opter, opter_name = '')
            except Exception, e:
                log.error('submit_keywords error, shop_id=%s, upd_arg_list=%s, e=%s' % (self.shop_id, upd_arg_list, e))
        return

    def submit_keywords(self):
        upd_arg_list = []
        for kl in self.kw_locker_list:
            kl.do_failed_word()
            if kl.result_flag not in kl.fininshed_status_list:
                update_dict = {'old_price':kl.cur_price}
                if kl.platform == 'pc':
                    update_dict.update({'max_price': kl.test_price, 'old_price':kl.cur_price})
                else:
                    update_dict.update({'max_mobile_price': kl.test_price, 'mobile_old_price':kl.cur_price})
                upd_arg_list.append([self.campaign_id, self.adgroup_id, kl.keyword_id, kl.word, update_dict])
        if upd_arg_list:
            updated_kw_list = []
            try:
                updated_kw_list, _ = update_keywords(shop_id = self.shop_id, kw_arg_list = upd_arg_list, opter = self.opter, opter_name = '')
            except Exception, e:
                log.error('submit_keywords error, shop_id=%s, upd_arg_list=%s, e=%s' % (self.shop_id, upd_arg_list, e))
            for kl in self.kw_locker_list:
                kl.check_upded_price(updated_kw_list)
        return

    def rob_rank(self):
        self.get_real_rank()
        for kl in self.kw_locker_list:
            kl.clac_next_bid()
        self.submit_keywords()
        if self.is_finishing():
            self.submit_keywords()
            self.colse()
            return True
        else:
            self.check_time = datetime.datetime.now() + datetime.timedelta(seconds = CHANCK_RANK_WATING_TIME)
            return False

class RobRankMng(object):

    @classmethod
    def create_auto_robrank(cls, user, keyword_id, exp_rank_range, limit_price, platform, start_time, end_time, nearly_success):
        error_msg = ''
        shop_id = user.shop_id
        next_run_time = datetime.datetime.now() + datetime.timedelta(minutes = 5) # 不立即优化的原因：1、防止用户短时间内多次修改，重复执行；2、避免立即改价后，页面未更新价格的问题
        try:
            if not test_permission(AUTO_RANKING_CODE, user):
                error_msg = "version_limit"
            else:
                # 删除抢排名表中已经删除的关键词
                kw_locker_id_list = [keyword['_id'] for keyword in kw_locker_coll.find({'shop_id':shop_id})]
                kw_id_list = [keyword['_id'] for keyword in kw_coll.find({'_id': {'$in': kw_locker_id_list}})]
                kw_locker_coll.remove({'_id': {'$in': list(set(kw_locker_id_list) - set(kw_id_list))}}, multi = True)

                # 当是添加抢排名记录并且超过50个锁定排名的关键词时
                if kw_locker_coll.find({'_id':keyword_id}).count() == 0 and len(kw_id_list) >= 50:
                    error_msg = "nums_limit"
                else:
                    kw = Keyword.objects.get(shop_id = shop_id, keyword_id = keyword_id)
                    result = kw_locker_coll.update({'shop_id': shop_id, 'campaign_id': kw.campaign_id, 'adgroup_id': kw.adgroup_id, '_id': kw.keyword_id},
                                                   {'$set': {'exp_rank_range': exp_rank_range, 'word': kw.word, 'limit_price': limit_price,
                                                             'platform': platform, 'start_time': start_time, 'end_time': end_time, 'nearly_success':nearly_success,
                                                             'is_running': 0, 'is_stop': 0, 'next_run_time': next_run_time, 'is_auto_robrank': True}},
                                                   upsert = True)
                    if not result['updatedExisting']:
                        kw.is_locked = True
                        kw.save()
        except Exception, e:
            log.error('auto_rob_rank error shop_id=%s, e=%s' % (shop_id, e))
            error_msg = 'others'
        return error_msg

    @classmethod
    def consel_auto_robrank(cls, shop_id, keyword_id):
        from apps.engine.models_channel import MessageChannel
        kw_locker_coll.remove({'shop_id': shop_id, '_id': keyword_id})
        kw_coll.update({'shop_id': shop_id, '_id': keyword_id}, {'$set': {'is_locked': False}})
        MessageChannel.delete_msg_history([keyword_id])

    @classmethod
    def get_rob_rank_task(cls):
        new_task_list = []
        is_mutual = CacheAdpter.get(CacheKey.ENGINE_ROBRANK_TASK_MUTUAL_LOCK, 'web')
        if not is_mutual: # 否则，马上设置缓存，将门关了
            kw_lockers = []
            try:
                CacheAdpter.set(CacheKey.ENGINE_ROBRANK_TASK_MUTUAL_LOCK, True, 'web', 60 * 2)
                now = datetime.datetime.now()
                time_str = now.strftime('%H:%M')
                # 关键词自动抢排名的开始时间、结束时间，只在取任务时做检验。每个关键词抢排名时，不再校验，因为可能抢排名时，时间刚好超过该执行的时间
                kw_lockers = KeywordLocker.objects.filter(
                    Q(is_stop__in = [0, None], start_time__lte = time_str, end_time__gte = time_str, next_run_time__lte = now)
                    & (Q(is_running__in = [0, None]) | Q(is_running = 1, last_run_time__lte = now - datetime.timedelta(hours = 1)))) \
                    .order_by('-is_running', 'next_run_time', 'adgroup_id').limit(100)
                kw_id_list = [kl.keyword_id for kl in kw_lockers]
                kw_locker_coll.update({'_id': {'$in': kw_id_list}}, {'$set': {'is_running': 1, 'last_run_time': now}}, multi = True)
            except Exception, e:
                log.error("robrank_task get_valid_task error, e=%s" % e)
            finally:
                CacheAdpter.delete(CacheKey.ENGINE_ROBRANK_TASK_MUTUAL_LOCK, 'web') # 清除缓存，把门打开

            adg_dict = {}
            for kl in kw_lockers:
                adg_dict.setdefault(kl.adgroup_id, []).append(kl)
            for adgroup_id, kl_list in adg_dict.items(): # 最后一个宝贝可能没有包含这个宝贝下所有的关键词，所以过滤掉，等下次执行
                shop_id = kl_list[0].shop_id
                task = RobRankTask(shop_id = shop_id, adgroup_id = adgroup_id, kw_locker_list = kl_list, opt_type = 'auto')
                task.init_data()
                if task.is_runnable():
                    new_task_list.append(task)
                else:
                    task.update_kw_locker_error()
                    task.colse()
        log.info('get rob rank task, count=%s' % len(new_task_list))
        return new_task_list

    @classmethod
    def execute(cls, poison):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        rob_rank_list = []
        new_rob_rank_list = []
        try:
            while True:
                if rob_rank_list and rob_rank_list[0].check_time <= datetime.datetime.now():
                    task = rob_rank_list.pop(0)
                    if not task.rob_rank():
                        rob_rank_list.append(task)
                    continue
                if new_rob_rank_list:
                    task = new_rob_rank_list.pop(0)
                    if not task.rob_rank():
                        rob_rank_list.append(task)
                    continue
                if not poison.is_set():
                    new_task_list = cls.get_rob_rank_task()
                    if len(new_task_list):
                        new_rob_rank_list.extend(new_task_list)
                    else:
                        time.sleep(10)
                    continue
                if not rob_rank_list:
                    break
        except Exception, e:
            subject = '【紧急问题】自动抢排名任务出错'
            exstr = traceback.format_exc()
            content = str(exstr)
            cc_list = [settings.AUTO_TASK_EMAIL]
            send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, cc_list)
            log.error('auto_rob_rank error, e=%s' % exstr)

class CustomRobRank(object):
    '''手动抢排名 接口'''

    @classmethod
    def create_rob_rank_task(cls, user, adgroup_id, kw_cfg_list):
        error_msg = ''
        task = None
        shop_id = int(user.shop_id)
        try:
            if RANKING_CODE not in user.perms_code:
                error_msg = "version_limit"
            else:
                kw_locker_list = []
                for kw in kw_cfg_list:
                    kw_locker = KeywordLocker(shop_id = shop_id, adgroup_id = adgroup_id, keyword_id = kw['keyword_id'],
                                              word = kw['word'], exp_rank_range = kw['exp_rank_range'], limit_price = kw['limit_price'],
                                              platform = kw['platform'], nearly_success = kw['nearly_success'], is_auto_robrank = False)
                    kw_locker_list.append(kw_locker)
                task = RobRankTask(shop_id = shop_id, adgroup_id = adgroup_id, kw_locker_list = kw_locker_list, opt_type = 'manual')
        except Exception, e:
            log.error('shop_id=%s, adg_id=%s, e=%s' % (shop_id, adgroup_id, e))
            error_msg = 'others'
        return error_msg, task

    @classmethod
    def rob_rank(cls, task):
        task.init_data()
        if not task.is_runnable():
            task.update_kw_locker_error()
            return

        while not task.rob_rank():
            time.sleep(CHANCK_RANK_WATING_TIME)

    @classmethod
    def execute(cls, **kargs): # 参数 user, adgroup_id, kw_cfg_list
        error_msg, task = cls.create_rob_rank_task(**kargs)
        if not error_msg:
            # 抢排名的过程是通过 web_socket 传到前台的，所以新起线程运行，当前直接返回
            bg_thread = Thread(target = cls.rob_rank, kwargs = {'task': task})
            bg_thread.start()
        return error_msg

    @classmethod
    def test_execute(cls, **kargs): # 参数 user, adgroup_id, kw_cfg_list
        '''测试时用到该函数，因为需要执行完后，即时改回原价、所以不能新起线程'''
        error_msg, task = cls.create_rob_rank_task(**kargs)
        if not error_msg:
            cls.rob_rank(task)
        return error_msg
