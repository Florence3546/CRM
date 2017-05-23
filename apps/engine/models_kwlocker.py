# coding=UTF-8

import datetime, json

from apilib import get_tapi

from mongoengine.document import Document
from mongoengine.fields import IntField, StringField, ListField, DateTimeField, BooleanField

from apps.common.utils.utils_log import log
from apps.engine.models_channel import MessageChannel


class KeywordLocker(Document):

    PLATFORM_CHOICES = (('yd', '移动平台'), ('pc', 'PC平台'))

    shop_id = IntField(verbose_name = '店铺ID', required = True)
    campaign_id = IntField(verbose_name = '计划ID', required = True)
    adgroup_id = IntField(verbose_name = '推广宝贝ID', required = True)
    keyword_id = IntField(verbose_name = '关键词ID', primary_key = True)
    word = StringField(verbose_name = '关键词', max_length = 100)
    exp_rank_range = ListField(verbose_name = '期望排名区间', default = [1, 20])
    limit_price = IntField(verbose_name = '最高限价', default = 500) # 单位 分
    platform = StringField(verbose_name = '所抢平台', choices = PLATFORM_CHOICES, default = 'pc')
    nearly_success = IntField(verbose_name = '允许接近成功', choices = (0, 1), default = 0) # 值为1时, 表示如果抢不到期望排名，接近期望排名也可以.

    # 锁排名比手工抢排名多用到 的字段
    start_time = StringField(verbose_name = '每天开始抢排名时间', default = '00:00')
    end_time = StringField(verbose_name = '每天结束抢排名时间', default = '23:59')
    next_run_time = DateTimeField(verbose_name = '下次运行时间', default = datetime.datetime.now)
    last_run_time = DateTimeField(verbose_name = '任务开始运行时间')  # 记录任务开始执行的时间，方便回收1小时前的正在运行的任务。
    is_running = IntField(verbose_name = '任务运行状态', default = 0)
    is_stop = IntField(verbose_name = '是否暂停', choices = (0, 1), default = 0)
    is_auto_robrank = BooleanField(verbose_name = '是否是自动抢排名', default = False)

    meta = {'db_alias': "mnt-db", 'collection':'engine_kwlocker', 'indexes':['shop_id', 'campaign_id', 'adgroup_id', 'word']}

    MOST_TRY_TIMES = 6

    @property
    def tapi(self):
        if not hasattr(self, '_tapi'):
            self._tapi = get_tapi(shop_id = self.shop_id)
        return self._tapi

    @property
    def forecast_price(self):
        if not hasattr(self, '_forecast_price'):
            # 由于淘宝下架了预估排名接口，这里就直接返回0，等淘宝再次上线后，再更新此函数
            self._forecast_price = 0
        return self._forecast_price

    @property
    def back_price(self):
        '''抢排名失败时，还原到什么价格'''
        if not hasattr(self, '_back_price'):
            self._back_price = min(self.limit_price, max(5, self.old_price))
        return self._back_price

    def add_alg_property(self, cur_price):
        self.old_price = cur_price # 抢排名前的出价
        self.test_price = cur_price # 测试出价
        self.cur_price = cur_price # 当前关键词排名
        self.cur_rank = -1 # 当前关键词排名
        self.cur_rank_dict = {'pc': 9, 'yd': 12, 'pc_desc': '5页以后', 'yd_desc': '20条以后'}
        self.head_test_price = 0 # 二分法的时候，排在前面的价格
        self.tail_test_price = 0 # 二分法的时候，排在后面的价格
        self.try_times = 0 # 抢排名次数
        self.fail_reason = ''
        self.result_flag = 'doing'
        self.last_result_flag = 'doing'
        self.last_price = 0
        self.last_rank = 101
        self.fininshed_status_list = ['nearly_ok', 'ok', 'failed']
        self.rollback_status_list = ['nearly_ok_ing', 'ok_ing', 'failed_ing']
        # result_flag 测试结果, 'doing'，'waiting' | 'ok', 'nearly_ok' 'failed')
        # 抢排名中，尚未下结论 'doing'，不断地改价，尝试
        # |--> 失败 'waiting'
        #   |--> 当前排名已成功，或接近成功，结束 'ok', 'nearly_ok'
        #   |--> 上次排名已成功，或接近成功，改回上一次出价 'nearly_ok_ing', 'ok_ing'
        #       |--> 改价成功 'nearly_ok', 'ok'
        #       |--> 改价失败，重试改价
        #   |--> 标记为失败，改回原价 'failed_ing'
        #       |--> 改价成功 'failed'
        #       |--> 改价失败，重试改价

    def check_is_ok(self, checking_rank):
        return self.exp_rank_range[0] <= checking_rank <= self.exp_rank_range[1]

    def check_price(self, price):
        return 5 <= price <= self.limit_price

    def check_test_price(self):
        return self.test_price != self.cur_price and self.check_price(self.test_price)

    def check_nearly_success(self, checking_rank):
        return self.nearly_success and checking_rank - self.exp_rank_range[1] <= 3

    def calc_test_price(self):
        if (not self.head_test_price) or (not self.tail_test_price): # 第一次计算出价时
            self.head_test_price = self.limit_price
            self.tail_test_price = min(5, self.limit_price) # 最低出价 0.05元
            if self.forecast_price:
                self.test_price = min(self.forecast_price, self.limit_price)
                return True
        if self.cur_rank <= self.exp_rank_range[1]:
            self.head_test_price = self.cur_price - 1
            self.test_price = int(self.cur_price * 0.95)
            if self.test_price <= self.tail_test_price < self.head_test_price:
                self.test_price = (self.head_test_price + self.tail_test_price) / 2
        else:
            self.tail_test_price = self.cur_price + 1
            self.test_price = (self.head_test_price + self.tail_test_price + 1) / 2 # 向上取整
        self.test_price = max(self.test_price, 5)
        self.test_price = min(self.test_price, self.limit_price)
        return True

    def save_log(self, desc):
        log.info('[rob_rank] word=%s, %s, test_price=%s, try_times=%s, exp_rank=%s, limit_price=%s, old_price=%s, %s' %
                 (self.word, self.platform, self.test_price, self.try_times, self.exp_rank_range, self.limit_price, self.old_price, desc))

    def save_process(self, desc):
        # log.info('%s, %s, %s, %s, %s, %s, %s' % (self.keyword_id, self.word, self.cur_price, self.limit_price, desc, self.cur_rank_dict['%s_desc' % self.platform], self.result_flag))
        msg_dict = ({
            self.keyword_id: json.dumps({
                'msg': str(desc),
                'price': self.cur_price / 100.0,
                'word': self.word,
                'platform': self.platform,
                'exp_rank_range': self.exp_rank_range,
                'limit_price': self.limit_price / 100.0,
                'nearly_success': self.nearly_success,
                'result_flag': self.result_flag,
                'cur_rank_dict': self.cur_rank_dict,
                'rob_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            })
        if self.is_auto_robrank:
            MessageChannel.save_msg(msg_dict)
        else:
            MessageChannel.publish_msg(msg_dict)
        return True

    def clac_next_bid(self):
        if self.result_flag != 'doing':
            return
        try:
            if self.try_times >= KeywordLocker.MOST_TRY_TIMES:
                self.result_flag = 'waiting'
                self.fail_reason = '尝试次数过多'
                return
            # elif self.cur_price == self.limit_price:
            #     self.result_flag = 'waiting'
            #     self.fail_reason = '已经出到限价'
            else:
                self.calc_test_price()
                if self.check_test_price():
                    # 成功时保存快照，方便失败时，直接恢复到该价格
                    if self.check_is_ok(self.cur_rank) or self.check_nearly_success(self.cur_rank):
                        self.last_rank = self.cur_rank
                        self.last_price = self.cur_price
                        self.last_rank_dict = self.cur_rank_dict
                    self.try_times += 1
                else:
                    self.result_flag = 'waiting'
                    self.fail_reason = '没有改价空间'
        except Exception, e:
            self.result_flag = 'waiting'
            self.save_log(desc = '计算出价失败: e=%s' % e)
            self.fail_reason = '其他原因'
            return

    def do_failed_word(self):
        if self.result_flag != 'waiting':
            return
        self.save_process(desc = '由于%s, 停止抢排名' % self.fail_reason)
        if self.cur_rank >= 0:
            if self.check_is_ok(self.cur_rank):
                self.result_flag = 'ok'
                self.save_process(desc = '抢排名成功')
                return
            if self.check_nearly_success(self.cur_rank):
                self.result_flag = 'nearly_ok'
                self.save_process(desc = '接近期望排名，抢排名结束')
                return
            if self.last_price and self.check_price(self.last_price):
                if self.check_is_ok(self.last_rank):
                    self.test_price = self.last_price
                    self.cur_rank = self.last_rank
                    self.result_flag = 'ok_ing'
                    return
                if self.check_nearly_success(self.last_rank):
                    self.test_price = self.last_price
                    self.cur_rank = self.last_rank
                    self.result_flag = 'nearly_ok_ing'
                    return
        if self.cur_price == self.back_price:
            self.result_flag = 'failed'
            self.save_process(desc = '抢排名结束')
            return
        else:
            self.test_price = self.back_price
            self.result_flag = 'failed_ing'
            return

    def check_upded_price(self, upd_list):
        if self.result_flag in self.fininshed_status_list:
            return
        if self.keyword_id in upd_list:
            self.cur_price = self.test_price
            if self.result_flag in self.rollback_status_list:
                self.result_flag = self.result_flag[:-4] # 去掉进行时后缀
                desc = ''
                if self.result_flag == 'ok':
                    desc = '已恢复上一次价格，抢排名成功'
                elif self.result_flag == 'nearly_ok':
                    desc = '已恢复上一次价格，接近期望排名'
                else:
                    desc = '已恢复初始出价%s元, 抢排名结束' % round(self.old_price / 100.0, 2)
                self.save_process(desc = desc)
        else:
            if self.result_flag == 'doing':
                self.result_flag = 'waiting'
                self.save_process(desc = '改价失败')
            else:
                self.save_log(desc = '改价失败')
        return


kw_locker_coll = KeywordLocker._get_collection()
