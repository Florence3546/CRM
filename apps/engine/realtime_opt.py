# coding=UTF-8

import signal
import datetime, time

from apps.common.utils.utils_log import log
from apps.common.utils.utils_misc import trans_batch_dict_2document
from apps.common.biz_utils.utils_tapitools import get_kw_g_data
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.subway.download import Downloader
from apps.subway.upload import update_keywords
from apps.subway.models import Keyword, Adgroup, adg_coll, kw_coll
from apps.mnt.models import MntCampaign, mnt_camp_coll
from apps.router.models import ArticleUserSubscribe
from apps.subway.models_account import Account, account_coll
from apps.ncrm.models import Customer

from apps.subway.realtime_report import RealtimeReport


class ScreenRealtimeAdgroup(object):
    """docstring for ScreenRealtimeAdgroup"""
    def __init__(self, shop_id):
        super(ScreenRealtimeAdgroup, self).__init__()
        self.shop_id = shop_id
        self.rt_camp_list = []
        self.mnt_camp_list = []
        self.adg_list = []

    @property
    def dler(self):
        if not hasattr(self, '_dler'):
            try:
                self._dler = Downloader.objects.get(shop_id = self.shop_id)
            except Exception:
                self._dler = None
        return self._dler

    @property
    def tapi(self):
        if not hasattr(self, '_tapi'):
            self._tapi = self.dler and self.dler.tapi or None
        return self._tapi

    def check_balance(self):
        try:
            # tobj_balance = self.tapi.simba_account_balance_get()
            # if tobj_balance and hasattr(tobj_balance, 'balance'):
            #     account_coll.update({'_id': self.shop_id}, {'$set':{'balance':tobj_balance.balance}})
            #     if tobj_balance.balance > 10:
            #         return True
            balance = self.tapi.get_account_balance()
            account_coll.update({'_id': self.shop_id}, {'$set': {'balance': balance}})
            if balance > 10:
                return True
            return False
        except Exception, e:
            log.error('get balace error, shop_id=%s, e=%s' % (self.shop_id, e))
            return False

    def check_account(self):
        if not self.dler or not self.tapi:
            return False, 'not dler/tapi'

        if not self.check_balance():
            return False, 'balance is less'

        if not self.dler.check_todayrpt_isok():
            return False, 'rpt isnot downloaded'

        rtrpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'account', args_list = [self.shop_id])
        account_rtrpt = rtrpt_dict.get(self.shop_id, Account.Report())
        if account_rtrpt.cost < 2000:
            return False, 'rtrpt is less'

        return True, ''

    def check_camp(self):
        mnt_camp_list = MntCampaign.objects.filter(shop_id = self.shop_id, mnt_rt = 1, mnt_type__in = [2, 4])
        if mnt_camp_list:
            camp_rpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'campaign', args_list = [self.shop_id])
            for camp in mnt_camp_list:
                camp_rtrpt = camp_rpt_dict.get(camp.campaign_id, None)
                if camp_rtrpt and camp_rtrpt.impressions > 1000 and camp_rtrpt.click > 0:
                    self.rt_camp_list.append(camp)
        return

    def check_adg(self):
        for camp in self.rt_camp_list:
            camp_id = camp.campaign_id
            adg_rpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'adgroup', args_list = [self.shop_id, camp_id])
            adg_list = list(adg_coll.find({'shop_id': self.shop_id, 'campaign_id': camp_id, 'online_status': 'online', 'mnt_type': {'$in': [2, 4]}}))
            adg_list = trans_batch_dict_2document(src_dict_list = adg_list, class_object = Adgroup)
            for adg in adg_list:
                adg_rpt = adg_rpt_dict.get(adg.adgroup_id, None)
                adg.user_limit_price = adg.use_camp_limit and camp.max_price or adg.limit_price
                if adg_rpt and adg_rpt.impressions > 1000 and adg_rpt.click > 0:
                    adg.rtrpt = adg_rpt
                    adg.tapi = self.tapi
                    self.adg_list.append(adg)

    def execute(self):
        is_runnable, reason = self.check_account()
        if is_runnable:
            self.check_camp()
            self.check_adg()
        else:
            log.info('does not realtime optimzie shop, shop_id=%s, reason=%s' % (self.shop_id, reason))
        return self.adg_list


class RealtimeOptAdgroup(object):
    """docstring for RealtimeOptAdgroup"""
    def __init__(self, adgroup):
        super(RealtimeOptAdgroup, self).__init__()
        self.adgroup = adgroup
        self.tapi = adgroup.tapi
        self.shop_id = adgroup.shop_id
        self.campaign_id = adgroup.campaign_id
        self.adgroup_id = adgroup.adgroup_id

    @property
    def kw_rtrpt_dict(self):
        if not hasattr(self, '_kw_rtrpt_dict'):
            self._kw_rtrpt_dict = RealtimeReport.get_summed_rtrpt(rpt_type = 'keyword', args_list = [self.shop_id, self.campaign_id, self.adgroup_id])
        return self._kw_rtrpt_dict

    @property
    def kw_rpt_dict(self):
        if not hasattr(self, '_kw_rpt_dict'):
            kw_id_list = self.kw_rtrpt_dict.keys()
            self._kw_rpt_dict = Keyword.Report.get_summed_rpt({'shop_id': self.shop_id, 'campaign_id': self.campaign_id, 'adgroup_id': self.adgroup_id,
                                                               'keyword_id': {'$in': kw_id_list}}, rpt_days = 7)
        return self._kw_rpt_dict

    @property
    def kw_click_top5(self):
        '''点击前5排序'''
        if not hasattr(self, '_kw_click_top5'):
            kw_list = sorted(self.kw_rtrpt_dict.values(), key = lambda e:e.click, reverse = True)
            self._kw_click_top5 = [kw.keyword_id for kw in kw_list[:5] if kw.click > 0]
        return self._kw_click_top5

    @property
    def kw_list(self):
        if not hasattr(self, '_kw_list'):
            kw_list = list(kw_coll.find({'shop_id':self.shop_id, 'campaign_id': self.campaign_id, 'adgroup_id': self.adgroup_id,
                                         'mnt_opt_type': {'$ne': 2}, '_id': {'$in': self.kw_rtrpt_dict.keys()}}))
            self._kw_list = trans_batch_dict_2document(src_dict_list = kw_list, class_object = Keyword)
        return self._kw_list

    @property
    def kw_g_data(self):
        if not hasattr(self, '_kw_g_data'):
            word_list = [kw.word for kw in self.kw_list]
            self._kw_g_data = get_kw_g_data(word_list)
        return self._kw_g_data

    def calc_new_price(self, kw, current_rank, limit_price):
        # 根据新查排名结果更新价格
        return 0

    def kw_current_rank(self, kw):
        '''获取真实排名'''
        rank_dict = Keyword.get_rt_kw_rank(self.tapi, kw.adgroup_id, kw.max_price, kw.keyword_id)
        if not rank_dict:
            return 0
        try:
            rank_desc = rank_dict['pc_rank']
            if rank_desc in ['>100', '未投放']:
                return 0
            if '-' in rank_desc: # 淘宝返回一个范围区间时，取平均值
                rank_range = rank_desc.split('-')
                rank_desc = round((int(rank_range[0]) + int(rank_range[1])) / 2.0) # 四舍五入
            return int(rank_desc)
        except Exception, e:
            log.error('calc cur rank error, e=%s' % e)
            return 0

    def optimize_keyword(self, kw):
        '''
           # 潜力词加价:
           # ROI>2 >> 有预估排名且有真实排名 >> 对比排名准确性 >> 加价提升排名(包括加价几分或一毛多点就能提升两三位排名的请况) 并且 不高于min(行业平均的1.5倍或近7天的1.5倍)
           # 并且  加价后的价格避免拉低ROI导致不赚钱(保底ROI不能低于1.7)
           # 止损条件:
           # 实时无转化 且 实时无收藏且历史7天无转化，或历史7天无收藏 且历史7天无转化
           # 实时关键词价格 >历史7天平均关键词PPC 并且 时实关键词PPC>实时宝贝PPC 并且 关键词实时PPC>行业平均PPC的80% 并且 只更新该宝贝中点击量前5名的关键词
        '''
        default_result = [False, 0]
        kw_rtrpt = self.kw_rtrpt_dict.get(kw.keyword_id, None)
        kw_rpt7 = self.kw_rpt_dict.get(kw.keyword_id, None)
        if not (kw_rtrpt and kw_rpt7):
            return default_result
        g_data = self.kw_g_data.get(kw.word.encode('utf8'), None) # 关键词的行业平均PPC
        if not g_data:
            return default_result
        kw_g_cpc = g_data.g_cpc # 关键词的行业平均PPC
        kw.limit_price = self.adgroup.user_limit_price
        if not kw_g_cpc:
            return default_result
        if kw_rtrpt.roi > 2:
            current_rank = self.kw_current_rank(kw)
            if not current_rank:
                return default_result
            min_roi = 1.7
            low_roi_price = kw_rtrpt.roi * kw.max_price / min_roi # 利用roi与出价成反比的关系，计算在最小期望roi下，的出价为多少
            limit_price = min(kw_g_cpc * 1.5, kw_rpt7.cpc * 1.5, kw.limit_price, low_roi_price) # 不高于 min(行业平均的1.5倍或近7天的1.5倍)，防止多次循环之后加价太高
            new_price = self.calc_new_price(kw, current_rank, limit_price)
            if new_price:
                log.info('realtime optimize keyword, plus price, word=%s, cur_price=%s, new_price=%s, kw_id=%s' % (kw.word, kw.max_price, new_price, kw.keyword_id))
                return True, new_price
        if kw_rtrpt.roi == 0:
            # if kw_rpt7.roi == 0 and (kw_rpt7.favcount == 0 or kw_rtrpt.favcount == 0):
            if kw_rpt7.roi == 0:
                # 实时无收藏且历史7天无转化，或历史7天无收藏 且历史7天无转化
                if kw_rtrpt.cpc > max(self.adgroup.rtrpt.cpc, kw_g_cpc * 0.8) and \
                        kw.max_price > kw_rpt7.cpc and kw.keyword_id in self.kw_click_top5:
                    new_price = kw.max_price * 0.9
                    log.info('realtime optimize keyword, reduce price, word=%s, cur_price=%s, new_price=%s, kw_id=%s' % (kw.word, kw.max_price, new_price, kw.keyword_id))
                    return True, new_price
        return default_result

    def execute(self):
        upd_list = []
        if not self.adgroup.ensure_kw_rpt():
            return len(upd_list)
        for kw in self.kw_list:
            try:
                is_modify, new_price = self.optimize_keyword(kw)
                if is_modify:
                    upd_list.append([self.campaign_id, self.adgroup_id, kw.keyword_id, kw.word, {'max_price': new_price, 'old_price': kw.max_price}])
            except Exception, e:
                log.info('realtime opt kw error, e=%s' % e)
                continue
        if upd_list:
            update_keywords(shop_id = self.shop_id, kw_arg_list = upd_list, tapi = self.tapi, opter = 4, opter_name = '')
            pass
        return len(upd_list)


class RealtimeOptimizeMng():
    """docstring for RealtimeOptimize"""

    work_time = [('08:00', '22:00')]

    @classmethod
    def is_time_todo(cls):
        """当前是否是工作时间"""
        nowtime = datetime.datetime.now().strftime('%H:%m')
        for i in cls.work_time:
            if i[0] <= nowtime <= i[1]:
                return True
        return False

    @classmethod
    def get_valid_shops(cls):
        '''获取未过期的、有余额、需要实时优化的店铺'''
        objs = ArticleUserSubscribe.objects.filter(deadline__gt = datetime.datetime.now()).only('nick')
        article_dict = {obj.nick: 1 for obj in objs}

        objs = Customer.objects.all().only('shop_id', 'nick')
        customer_dict = {obj.shop_id: obj.nick for obj in objs}

        mnt_camp_list = mnt_camp_coll.find({'mnt_rt':1, 'mnt_type': {'$in': [2, 4]}}, {'shop_id':1})
        mnt_shop_dict = {mnt_camp['shop_id']: 1 for mnt_camp in mnt_camp_list}

        shop_id_list = []
        acc_cur = account_coll.find({'$or': [{'balance': {'$gt': 0}}, {'balance': {'$gt': '0'}}]}, {'_id': 1, 'balance': 1})
        for acc in acc_cur:
            shop_id = acc['_id']
            if float(acc['balance']) < 0:
                continue
            if customer_dict.get(shop_id, '') in article_dict and shop_id in mnt_shop_dict:
                shop_id_list.append(shop_id)
        return shop_id_list

    @classmethod
    def execute(cls, poison):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        cachekey = CacheKey.ENGINE_REALTIME_OPTIMIZE_TASK
        default_last_start_time = datetime.datetime.now() - datetime.timedelta(hours = 3)
        last_start_time, stop_shop_id = CacheAdpter.get(cachekey, 'default', [default_last_start_time, 0])
        log.info('start engine for realtime_optimize, last_start_time=%s, stop_shop_id=%s' % (last_start_time, stop_shop_id))
        while True:
            if poison.is_set():
                break
            if not cls.is_time_todo():
                time.sleep(2)
                continue
            if (datetime.datetime.now() - last_start_time).seconds < 60 * 60 * 2 and (not stop_shop_id):
                time.sleep(2)
                continue
            adg_opt_count, kw_opt_count = 0, 0
            log.info('================================= realtime optimize start =================================')
            shop_id_list = cls.get_valid_shops()
            last_start_time = datetime.datetime.now()
            for shop_id in shop_id_list:
                log.info('is optimizing shop, shop_id=%s, total_shop_count=%s' % (shop_id, len(shop_id_list)))
                if poison.is_set():
                    stop_shop_id = shop_id
                    log.info('stop shop_id=%s' % shop_id)
                    break
                if shop_id < stop_shop_id:
                    continue
                adg_list = ScreenRealtimeAdgroup(shop_id).execute()
                for adg in adg_list:
                    if poison.is_set():
                        break
                    cur_kw_count = RealtimeOptAdgroup(adg).execute()
                    kw_opt_count += cur_kw_count
                    adg_opt_count += 1
            else: # 正常执行完后
                stop_shop_id = 0
            log.info('======== realtime optimize end: shop_count=%s, adg_opt_count=%s, kw_opt_count=%s ========' % (len(shop_id_list), adg_opt_count, kw_opt_count))

        log.info('end engine for realtime_optimize, last_start_time=%s, stop_shop_id=%s' % (last_start_time, stop_shop_id))
        CacheAdpter.set(cachekey, [last_start_time, stop_shop_id], 'default', 60 * 60 * 2)
