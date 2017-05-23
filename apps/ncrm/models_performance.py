# coding=utf-8

import datetime
import calendar
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import EmbeddedDocumentField, IntField, StringField, ListField, DictField, FloatField

from apps.common.cachekey import CacheKey
from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_misc import trans_batch_dict_2document
from apps.ncrm.models import XiaoFuGroup, PSUser
from apps.ncrm.guidance3 import get_performance_statistics


class PerfScoreCalcConf(EmbeddedDocument):
    """积分计算配置"""
    indicator_name_cn = StringField(verbose_name = '指标中文说明')
    indicator_name = StringField(verbose_name = '指标key')
    multiplier = FloatField(verbose_name = '系数', default = 1)


class PerfScoreConf(EmbeddedDocument):
    """积分档位配置"""
    desc = StringField(verbose_name = '积分档位')
    count = IntField(verbose_name = '名额个数')
    consult_royalty_equation = DictField(verbose_name = '公式系数', default = {'x0': 0.7349, 'x1':-0.1078, 'x2': 0.0058})
    consult_pay_limit = IntField(verbose_name = '顾问提成上限')

    def get_consult_royalty(self, order_pay):
        x = order_pay / 10000.0
        return round(self.consult_royalty_equation['x2'] * x ** 2 + self.consult_royalty_equation['x1'] * x + self.consult_royalty_equation['x0'], 4)


class PerfPayConf(EmbeddedDocument):
    """业绩配置"""
    desc = StringField(verbose_name = '说明')
    pay_min = IntField(verbose_name = '金额档位标准线')
    team_royalty = DictField(verbose_name = '团队绩效配置')


class PerformanceConfig(Document):
    """绩效配置快照表"""

    date = StringField(verbose_name = '时间', required = True) # 格式为 2015-06
    score_calc_cfg_list = ListField(verbose_name = '积分计算配置', field = EmbeddedDocumentField(PerfScoreCalcConf), required = True)
    score_cfg_list = ListField(verbose_name = '积分档位配置', field = EmbeddedDocumentField(PerfScoreConf), required = True)
    pay_cfg_list = ListField(verbose_name = '业绩配置', field = EmbeddedDocumentField(PerfPayConf), required = True)

    meta = {'db_alias': 'crm-db', 'collection': 'ncrm_performanceconf'}

    @property
    def team_royalty_list(self):
        return [[pc.team_royalty[sc.desc] for sc in self.score_cfg_list] for pc in self.pay_cfg_list]

    def get_score_cfg(self, score_rank):
        # TODO, 当人数增加、减少时
        score_cfg_list = self.score_cfg_list[:]
        if score_rank == 0:
            score_cfg = score_cfg_list[0]
        else:
            total_count = 0
            score_cfg_list.reverse()
            for sc_obj in score_cfg_list:
                total_count += sc_obj.count
                if score_rank <= total_count:
                    score_cfg = sc_obj
                    break
            else:
                score_cfg = score_cfg_list[-1]
        return score_cfg

    def get_pay_cfg(self, order_pay):
        pay_cfg_list = self.pay_cfg_list[:]
        pay_cfg_list.reverse()
        for pc_obj in pay_cfg_list:
            if order_pay >= pc_obj.pay_min:
                pay_cfg = pc_obj
                break
        else:
            pay_cfg = pay_cfg_list[-1]
        return pay_cfg

    def get_score_cfg_8desc(self, desc):
        result = self.score_cfg_list[-1]
        for score_cfg in self.score_cfg_list:
            if desc == score_cfg.desc:
                result = score_cfg
                break
        return result

    @classmethod
    def get_init_data(cls, is_save = False):
        score_cfg_list = [
            PerfScoreConf(desc = 'A', count = 2, consult_pay_limit = 2300, consult_royalty_equation = {'x0': 0.7349, 'x1':-0.1078, 'x2': 0.0058}),
            PerfScoreConf(desc = 'B', count = 8, consult_pay_limit = 3200, consult_royalty_equation = {'x0': 0.7583, 'x1':-0.1078, 'x2': 0.0058}),
            PerfScoreConf(desc = 'C', count = 5, consult_pay_limit = 3600, consult_royalty_equation = {'x0': 0.7893, 'x1':-0.1078, 'x2': 0.0058}),
            PerfScoreConf(desc = 'D', count = 3, consult_pay_limit = 4100, consult_royalty_equation = {'x0': 0.8002, 'x1':-0.1078, 'x2': 0.0058}),
            PerfScoreConf(desc = 'E', count = 2, consult_pay_limit = 4700, consult_royalty_equation = {'x0': 0.8044, 'x1':-0.1078, 'x2': 0.0058}),
            ]
        pay_cfg_list = [
            PerfPayConf(desc = '<1.5W ', pay_min = 0, team_royalty = {'A': 0.00, 'B': 0.01, 'C': 0.02, 'D': 0.03, 'E': 0.05}),
            PerfPayConf(desc = '>=1.5W', pay_min = 15000, team_royalty = {'A': 0.03, 'B': 0.04, 'C': 0.06, 'D': 0.07, 'E': 0.09}),
            PerfPayConf(desc = '>=2.5W', pay_min = 25000, team_royalty = {'A': 0.05, 'B': 0.06, 'C': 0.07, 'D': 0.08, 'E': 0.10}),
            PerfPayConf(desc = '>=3.5W', pay_min = 35000, team_royalty = {'A': 0.07, 'B': 0.08, 'C': 0.09, 'D': 0.10, 'E': 0.12}),
            PerfPayConf(desc = '>=5W', pay_min = 50000, team_royalty = {'A': 0.09, 'B': 0.10, 'C': 0.11, 'D': 0.12, 'E': 0.13}),
            PerfPayConf(desc = '>=7W', pay_min = 70000, team_royalty = {'A': 0.10, 'B': 0.11, 'C': 0.12, 'D': 0.13, 'E': 0.15}),
            PerfPayConf(desc = '>=10W', pay_min = 100000, team_royalty = {'A': 0.12, 'B': 0.13, 'C': 0.14, 'D': 0.15, 'E': 0.16}),
        ]
        score_calc_cfg_list = [
            PerfScoreCalcConf(indicator_name = "active_customer_count", indicator_name_cn = "活跃用户人天", multiplier = 0.25),
            PerfScoreCalcConf(indicator_name = "new_good_comment_count", indicator_name_cn = "好评数", multiplier = 2),
            PerfScoreCalcConf(indicator_name = "top_good_comment_count", indicator_name_cn = "踩好评数", multiplier = 15),
            PerfScoreCalcConf(indicator_name = "unsubscribe_apportion", indicator_name_cn = "退款责任分摊", multiplier = 1),
            PerfScoreCalcConf(indicator_name = "pay_subscribe_month1_count", indicator_name_cn = "付费订购一个月", multiplier = 1),
            PerfScoreCalcConf(indicator_name = "pay_subscribe_month3_count", indicator_name_cn = "付费订购一季度", multiplier = 2),
            PerfScoreCalcConf(indicator_name = "pay_subscribe_month6_count", indicator_name_cn = "付费订购半年", multiplier = 4),
            PerfScoreCalcConf(indicator_name = "pay_subscribe_month12_count", indicator_name_cn = "付费订购一年", multiplier = 8),
            PerfScoreCalcConf(indicator_name = "free_pay_subscribe_month3_count", indicator_name_cn = "非付费订购一季度", multiplier = 0.25),
            PerfScoreCalcConf(indicator_name = "free_pay_subscribe_month6_count", indicator_name_cn = "非付费订购半年", multiplier = 2),
            PerfScoreCalcConf(indicator_name = "free_pay_subscribe_month12_count", indicator_name_cn = "非付费订购一年", multiplier = 3),
        ]
        obj = cls(date = datetime.datetime.now().strftime('%Y-%m'), score_cfg_list = score_cfg_list, pay_cfg_list = pay_cfg_list, score_calc_cfg_list = score_calc_cfg_list)
        if is_save:
            obj.save()
        return obj

    @classmethod
    def tran_dict2obj(cls, cfg_dict):
        score_cfg_list = trans_batch_dict_2document(cfg_dict['score_cfg_list'], PerfScoreConf)
        pay_cfg_list = trans_batch_dict_2document(cfg_dict['pay_cfg_list'], PerfPayConf)
        score_calc_cfg_list = trans_batch_dict_2document(cfg_dict['score_calc_cfg_list'], PerfScoreCalcConf)
        return cls(date = cfg_dict['date'], score_calc_cfg_list = score_calc_cfg_list, score_cfg_list = score_cfg_list, pay_cfg_list = pay_cfg_list)

    @classmethod
    def save_perf_cfg(cls, cfg_dict):
        try:
            perf_cfg = cls.tran_dict2obj(cfg_dict)
            Performance.execute(date_month = perf_cfg.date, perf_cfg = perf_cfg)
            cls.objects.filter(date = perf_cfg.date).delete()
            perf_cfg.save()
            return True
        except Exception, e:
            log.error('save perf cfg error, cfg_dict=%s, e=%s' % (cfg_dict, e))
            return False

    @classmethod
    def get_cfg_8month(cls, date_month):
        try:
            obj = cls.objects.get(date = date_month)
        except Exception:
            objs = cls.objects.all().order_by('-date').limit(1)
            if objs:
                obj = objs[0]
            else:
                obj = cls.get_init_data(is_save = False)
        return obj

    @classmethod
    def get_metric_indicator_8date(cls, start_date, end_date):
        month_indicator_dict = {}
        temp_date = start_date
        while temp_date <= end_date:
            temp_month_str = temp_date.strftime('%Y-%m')
            if temp_month_str not in month_indicator_dict:
                try:
                    # perf_cfg = cls.objects.get(date = temp_month_str)
                    perf_cfg = cls.get_cfg_8month(temp_month_str)
                    month_indicator_dict[temp_month_str] = [scc.indicator_name for scc in perf_cfg.score_calc_cfg_list]
                except Exception:
                    month_indicator_dict[temp_month_str] = []
            temp_date += datetime.timedelta(days = 1)
        return list(set(reduce(lambda x, y: x + y, month_indicator_dict.itervalues())))

perf_cfg_coll = PerformanceConfig._get_collection()


class Performance(Document):
    """绩效表"""

    date = StringField(verbose_name = '统计时间', required = True) # 格式为 2015-06
    xfgroup_id = IntField(verbose_name = '销服组ID', required = True)
    department = StringField(verbose_name = "部门")
    order_pay = IntField(verbose_name = '团队金额', required = True, default = 0)
    score = IntField(verbose_name = '团队积分', required = True, default = 0)
    refund_pay = IntField(verbose_name = '退款金额', default = 0)
    market_unsubscribe_pay = IntField(verbose_name = '市场签单退款', default = 0)

    order_pay_rank = IntField(verbose_name = '金额排名', required = True, default = 0)
    score_rank = IntField(verbose_name = '积分排名', required = True, default = 0)
    order_pay_level = StringField(verbose_name = '金额等级', required = True)
    score_level = StringField(verbose_name = '积分等级', required = True)

    team_royalty = FloatField(verbose_name = '团队提成', required = True, default = 0)
    team_pay = IntField(verbose_name = '团队收入', required = True, default = 0)
    consult_royalty = FloatField(verbose_name = '顾问提成', required = True, default = 0)
    consult_pay = IntField(verbose_name = '顾问业绩', required = True, default = 0)
    seller_pay = IntField(verbose_name = '销售业绩', required = True, default = 0)
    consult_id = IntField(verbose_name = '顾问ID', required = True, default = 0)
    seller_id = IntField(verbose_name = '销售ID', required = True, default = 0)

    score_detail_list = ListField(verbose_name = '积分计算详情', default = [])

    meta = {'db_alias': 'crm-db', 'collection': 'ncrm_performance'}

    @classmethod
    def calc_score(cls, user_data_dict, score_calc_cfg_list):
        score = 0
        score_detail_list = []
        for scc in score_calc_cfg_list:
            value = sum(user_data_dict.get(scc.indicator_name, [0]))
            cur_score = int(value * scc.multiplier)
            score += cur_score
            score_detail_list.append({
                'old_value': value,
                'multiplier': scc.multiplier,
                'score': cur_score,
                'indicator_name': scc.indicator_name,
                'indicator_name_cn': scc.indicator_name_cn,
                })
        return score, score_detail_list

    @classmethod
    def step_1(cls, date_month, perf_cfg):
        metric_list = [scc.indicator_name for scc in perf_cfg.score_calc_cfg_list]
        metric_list += ['real_renew_order_pay', 'unsubscribe_pay', 'market_unsubscribe_pay']
        metric_list = list(set(metric_list))

        _, days = calendar.monthrange(year = int(date_month[:4]), month = int(date_month[5:]))
        start_time = datetime.datetime.strptime('%s-01' % date_month, '%Y-%m-%d')
        end_time = datetime.datetime.strptime('%s-%02d' % (date_month, days), '%Y-%m-%d')
        xfgroups = XiaoFuGroup.get_involved_xfgroup(start_time, end_time)
        xfgroup_dict = {obj.id: obj for obj in xfgroups}

        _, statistic_data = get_performance_statistics(time_scope = [start_time, end_time], cycle = 'month', indicators = metric_list, xfgroups = xfgroups)

        perf_list = []
        for data in statistic_data:
            user_data_dict = {temp['name']: temp['data'] for temp in data['metric_list']}
            order_pay = sum(user_data_dict.get('real_renew_order_pay', [0]))
            refund_pay = sum(user_data_dict.get('unsubscribe_pay', [0]))
            market_unsubscribe_pay = sum(user_data_dict.get('market_unsubscribe_pay', [0]))
            score, score_detail_list = cls.calc_score(user_data_dict, perf_cfg.score_calc_cfg_list)
            xfgroup = xfgroup_dict[data['xfgroup_id']]
            department = xfgroup.get_department_display() or ''
            perf_list.append(
                cls(
                    xfgroup_id = data['xfgroup_id'],
                    date = date_month,
                    department = department,
                    order_pay = order_pay,
                    refund_pay = refund_pay,
                    market_unsubscribe_pay = market_unsubscribe_pay,
                    score = score,
                    score_detail_list = score_detail_list,
                    consult_id = xfgroup.consult_id,
                    seller_id = xfgroup.seller_id,
                )
            )
        perf_list.sort(key = lambda p: (p.order_pay, p.score), reverse = True)
        for i, obj in enumerate(perf_list):
            obj.order_pay_rank = i + 1
        perf_list.sort(key = lambda p: (p.score, p.order_pay), reverse = True)
        for i, obj in enumerate(perf_list):
            obj.score_rank = i + 1
        return perf_list

    @classmethod
    def step_1_old(cls, date_month, perf_cfg):
        psusers = PSUser.objects.filter(position = 'CONSULT').exclude(status = '离职')
        psuser_dict = {obj.id: obj for obj in psusers}
        xf_groups = XiaoFuGroup.objects.all()
        consult_list = [obj.consult for obj in xf_groups]
        consult_seller_dict = {obj.consult_id: obj.seller_id for obj in xf_groups}
        metric_list = [scc.indicator_name for scc in perf_cfg.score_calc_cfg_list]
        metric_list += ['real_renew_order_pay', 'unsubscribe_pay']
        metric_list = list(set(metric_list))
        _, days = calendar.monthrange(year = int(date_month[:4]), month = int(date_month[5:]))
        time_scope = [datetime.datetime.strptime('%s-01' % date_month, '%Y-%m-%d'), datetime.datetime.strptime('%s-%02d' % (date_month, days), '%Y-%m-%d')]
        _, statistic_data = get_performance_statistics(time_scope, cycle = 'month', indicators = metric_list, psusers = consult_list)

        # statistic_data = []
        perf_list = []
        for data in statistic_data:
            user_data_dict = {temp['name']: temp['data'] for temp in data['metric_list']}
            order_pay = sum(user_data_dict.get('real_renew_order_pay', [0]))
            refund_pay = sum(user_data_dict.get('unsubscribe_pay', [0]))
            score, score_detail_list = cls.calc_score(user_data_dict, perf_cfg.score_calc_cfg_list)
            department = data['psuser_id'] in psuser_dict and psuser_dict[data['psuser_id']].get_department_display() or ''
            perf_list.append(
                cls(
                    xfgroup_id = data['psuser_id'], date = date_month, department = department,
                    order_pay = order_pay, refund_pay = refund_pay, score = score, score_detail_list = score_detail_list,
                    consult_id = data['psuser_id'], seller_id = consult_seller_dict[data['psuser_id']],
                )
            )
        perf_list.sort(key = lambda p: (p.order_pay, p.score), reverse = True)
        for i, obj in enumerate(perf_list):
            obj.order_pay_rank = i + 1
        perf_list.sort(key = lambda p: (p.score, p.order_pay), reverse = True)
        for i, obj in enumerate(perf_list):
            obj.score_rank = i + 1
        return perf_list

    @classmethod
    def step_2(cls, perf_list, perf_cfg):
        for obj in perf_list:
            if obj.score_level: # 支持前台强制设置某个员工的积分档位
                score_cfg = perf_cfg.get_score_cfg_8desc(obj.score_level)
            else:
                score_cfg = perf_cfg.get_score_cfg(obj.score_rank)
                obj.score_level = score_cfg.desc
            pay_cfg = perf_cfg.get_pay_cfg(obj.order_pay)
            obj.order_pay_level = pay_cfg.desc
            obj.team_royalty = pay_cfg.team_royalty[obj.score_level]
            overflow_refund = max(obj.market_unsubscribe_pay - 3000, 0)
            obj.team_pay = max(int((obj.order_pay - obj.refund_pay - overflow_refund) * obj.team_royalty), 0)
            obj.consult_royalty = score_cfg.get_consult_royalty(order_pay = obj.order_pay)
            obj.consult_pay = min(int(obj.team_pay * obj.consult_royalty), score_cfg.consult_pay_limit)
            obj.seller_pay = obj.team_pay - obj.consult_pay
        return perf_list

    @classmethod
    def save_xfgroup_perf(cls, perf_cfg_dict, score_level_dict):
        try:
            perf_list = cls.execute(date_month = perf_cfg_dict['date'], perf_cfg = perf_cfg_dict, is_force = True)
            cls.objects.filter(date = perf_cfg_dict['date']).delete()
            for obj in perf_list:
                obj.save()
            return True
        except Exception, e:
            log.error('save_xfgroup_perf error, cfg_dict=%s, e=%s' % (perf_cfg_dict, e))
            return False

    @classmethod
    def execute(cls, date_month, perf_cfg = None, is_force = False): # 例如：date_month = '2016-01'
        # is_force = True
        perf_list = [] if is_force else cls.objects.filter(date = date_month)
        if not perf_list:
            cache_key = CacheKey.NCRM_RANKING_LIST % date_month
            perf_list = CacheAdpter.get(cache_key, 'web', [])
            if not perf_cfg:
                perf_cfg = PerformanceConfig.get_cfg_8month(date_month = date_month)
            if isinstance(perf_cfg, dict):
                perf_cfg = PerformanceConfig.tran_dict2obj(perf_cfg)
            if (not perf_list) or is_force:
                perf_list = cls.step_1(date_month = date_month, perf_cfg = perf_cfg)
                CacheAdpter.set(cache_key, perf_list, 'web', 60 * 60)
            perf_list = cls.step_2(perf_list = perf_list, perf_cfg = perf_cfg)
        return perf_list

    @classmethod
    def save_manual_setting(cls, date_month, perf_cfg_dict, score_level_dict):
        try:
            score_level_dict = {int(k): v for k, v in score_level_dict.items()}
            perf_cfg = PerformanceConfig.tran_dict2obj(perf_cfg_dict)
            perf_list = cls.step_1(date_month = date_month, perf_cfg = perf_cfg)
            for p in perf_list:
                p.score_level = score_level_dict[p.xfgroup_id]
            perf_list = cls.step_2(perf_list = perf_list, perf_cfg = perf_cfg)
            cls.objects.filter(date = perf_cfg_dict['date']).delete()
            for obj in perf_list:
                obj.save()
            return True
        except Exception, e:
            log.error('save_xfgroup_perf error, cfg_dict=%s, e=%s' % (perf_cfg_dict, e))
            return False

performance_coll = Performance._get_collection()
