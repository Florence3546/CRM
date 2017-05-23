# coding=UTF-8

from apps.common.utils.utils_log import log
from apps.alg.models import StrategyConfig, CommandConfig
from apps.alg.dryrun import KeywordDryRun, AdgroupDryRun
from apps.alg.submit import KeywordSubmit

class Strategy:
    """docstring for Strategy"""
    def __init__(self):
        pass

    def get_name(self):
        return 'default'

    def dry_run(self, data):
        pass

    def execute(self, data):
        pass

    def get_impact_factor(self):
        if not self.impact_factor_dict:
            self.impact_factor_dict = StrategyConfig.DEFAULT_IMPACT_FACTOR_DICT
        return self.impact_factor_dict


class StrategyFactory():

    @property
    def strategy_dict(self):
        if not hasattr(self, '_strategy_dict'):
            self._strategy_dict = self._get_strategy_dict()
        return self._strategy_dict

    def _get_strategy_dict(self):
        strategy_dict = {}
        stg_cfg_dict = StrategyConfig.get_all_configs()
        for name in stg_cfg_dict.iterkeys():
            strategy_dict.update({name: (CommandStrategy, {'cmd_cfg_name': name})})
        return strategy_dict

    def get(self, name):
        klass, args_dict = self.strategy_dict.get(name, (None, {}))
        if klass:
            return klass(**args_dict)
        else:
            raise Exception('can not find the strategy, strategy_name=%s' % name)


class CommandStrategy(Strategy):
    """docstring for CommandStrategy"""
    def __init__(self, cmd_cfg_name, opter = 3, opter_name = ''):
        self.cmd_cfg_name = cmd_cfg_name
        self.opter = opter
        self.opter_name = opter_name

    def __unicode__(self):
        return 'CommandStrategy:%s' % (self.cmd_cfg_name)

    def get_name(self):
        return self.cmd_cfg_name

    @property
    def stg_cfg(self):
        if not hasattr(self, '_stg_cfg'):
            self._stg_cfg = StrategyConfig.get_config(name = self.cmd_cfg_name)
        return self._stg_cfg

    @property
    def kw_cmd_list(self):
        if not hasattr(self, '_kw_cmd_list'):
            if self.stg_cfg:
                self._kw_cmd_list = CommandConfig.get_config_list(name_list = self.stg_cfg.kw_cmd_list)
            else:
                self._kw_cmd_list = []
        return self._kw_cmd_list

    def bind_temp_strategy(self, kw_cmd_list, adg_cmd_list):
        '''crm 后台发送指令时，需要生成临时策略'''
        self._kw_cmd_list = [CommandConfig(cond = kw_cfg['cond'], operate = kw_cfg['operate'], desc = kw_cfg['desc']) for kw_cfg in kw_cmd_list]
        self._stg_cfg = StrategyConfig(adg_cmd_list = adg_cmd_list)
        return

    def get_impact_factor(self):
        return self.stg_cfg.impact_factor_dict

    def dry_run(self, data):
        log.info('Strategy 1, start: stg_name=%s, shop_id=%s, adg_id=%s' %
                 (self.get_name(), data.adgroup.shop_id, data.adgroup.adgroup_id))

        # 策略中新增的属性，统一在这里赋初始值。
        data.cmd_count_dict = {'unchange': 0}
        data.modify_kw_count_dict = {'plan': {'add': 0, 'del': 0, 'upd_price': 0, 'upd_match': 0},
                                     'result': {'add': 0, 'del': 0, 'update': 0, 'most_del_count': 200}
                                     }

        for kw in data.kw_list:
            kw.is_delete = False
            kw.new_price = None
            kw.new_match_scope = None
            kw.optm_reason = ''
            kw.cmd = ''

        adg_right_dict = {'add_word': data.can_add_kw, 'optm_qscore': data.can_del_kw}
        adg_dryrun = AdgroupDryRun(data)
        for adg_func in self.stg_cfg.adg_cmd_list:
            try:
                adg_right_dict.get(adg_func, True) and getattr(adg_dryrun, adg_func)()
            except Exception, e:
                log.error('adg dryrun error, e=%s, adg_func=%s, shop_id=%s, adg_id=%s' % (e, adg_func, data.adgroup.shop_id, data.adgroup.adgroup_id))
        if len(data.kw_list) < 150 and adg_right_dict.get('add_word', True) and 'add_word' not in self.stg_cfg.adg_cmd_list:
            getattr(adg_dryrun, 'add_word')()

        for kw in data.kw_list:
            kw_dryrun = KeywordDryRun(kw)
            kw_dryrun.run_cmd(self.kw_cmd_list, data)

        self.summary(data)
        return

    def summary(self, data):
        cmd_count_dict = {'unchange': 0}
        need_modify_count_dict = {'add': len(data.adgroup.add_kw_list),
                                  'del': 0,
                                  'upd_price': 0,
                                  'upd_match': 0,
                                  'click': 0, 'click_inc': 0, 'click_dec': 0,
                                  }
        for kw in data.kw_list:
            if hasattr(kw, 'cmd') and kw.cmd:
                cmd_count_dict[kw.cmd] = cmd_count_dict.get(kw.cmd, 0) + 1
            else:
                cmd_count_dict['unchange'] += 1
            need_modify_count_dict['click'] += kw.rpt7.click
            if kw.is_delete:
                need_modify_count_dict['del'] += 1
            if kw.new_price:
                need_modify_count_dict['upd_price'] += 1
                need_modify_count_dict['click_inc'] += kw.rpt7.click if kw.new_price > kw.max_price else 0
                need_modify_count_dict['click_dec'] += kw.rpt7.click if kw.new_price < kw.max_price else 0
            if kw.new_match_scope:
                need_modify_count_dict['upd_match'] += 1
        data.cmd_count_dict = cmd_count_dict
        data.modify_kw_count_dict['plan'] = need_modify_count_dict
        log.info('Strategy 2, summary: %s, %s, shop_id=%s, adg_id=%s' %
                 (need_modify_count_dict, cmd_count_dict, data.adgroup.shop_id, data.adgroup.adgroup_id))

        return

    def _submit(self, data):
        '''为全自动任务服务，增加了很多限制'''
        del_kw_list, upd_kw_list, add_kw_list = [], [], []
        kw_list, adg = data.kw_list, data.adgroup

        try:
            if data.can_add_kw and adg.add_kw_list:
                add_kw_list = [[kw.word, kw.new_price, None, None, None] for kw in adg.add_kw_list]

            for kw in kw_list:
                if kw.mnt_opt_type == 2:
                    continue
                if data.can_del_kw and kw.mnt_opt_type == 0 and kw.is_delete:
                    del_kw_list.append([kw.adgroup_id, kw.keyword_id, kw.word, 0, 0, ''])
                    # continue # 如果删除的词超过限价，而又删除失败，那么一定要把价格降下来
                if (data.can_upd_match and kw.new_match_scope) or (data.can_upd_price and kw.new_price):
                    upd_kw_list.append([kw.campaign_id, kw.adgroup_id, kw.keyword_id, kw.word,
                                        {'max_price': data.can_upd_price and kw.new_price or kw.max_price,
                                         'match_scope': data.can_upd_match and kw.new_match_scope or None,
                                         'old_price': kw.max_price}])

            if self.opter in [0, 3]: # 如果是系统或者全自动的话， 防止一次性删除太多的词
                most_del_count = min(int(len(kw_list) * 0.2), 25)
            else: # 人工发送指令时，可以多删除一些
                most_del_count = 200
            del_kw_list = del_kw_list[: most_del_count]
            most_add_count = 200 - len(kw_list) + len(del_kw_list)
            add_kw_list = add_kw_list[: most_add_count > 0 and int(most_add_count * 1.2) or 0]

            log.info('Strategy 3, need_to: update %s kws, delete %s kws, add %s kws, shop_id=%s, adg_id=%s' %
                     (len(upd_kw_list), len(del_kw_list), len(add_kw_list), adg.shop_id, adg.adgroup_id))
            kw_submit = KeywordSubmit(adg.adgroup.shop_id, adg.campaign_id, adg.adgroup_id, self.opter, self.opter_name)
            updated_num = kw_submit.sumbit_updated_keywords(upd_kw_list) # 先保证所有词在限价内
            deled_num = kw_submit.submit_deleted_keywords(del_kw_list)
            added_num, _ = kw_submit.submit_added_keywords(add_kw_list)

            data.modify_kw_count_dict['result'] = {'add': added_num, 'del': deled_num, 'upd': updated_num, 'most_del_count': most_del_count}
            log.info('Strategy 4, finished: updated %s kws, deleted %s kws, added %s kws, shop_id=%s, adg_id=%s' %
                     (updated_num, deled_num, added_num, adg.shop_id, adg.adgroup_id))
        except Exception, e:
            log.error('Strategy 4, submit error, shop_id=%s, adg_id=%s, e=%s' % (adg.shop_id, adg.adgroup_id, e))
            raise e

        return

    def execute(self, data):
        log.info('strategy %s executing.' % self.get_name())
        self.dry_run(data)
        # self.summary(data)
        self._submit(data)
