# coding=UTF-8

import random

from apps.common.utils.utils_log import log
from apps.kwslt.select_words import SelectConfManage
from apps.kwslt.keyword_selector import KeywordSelector


def validate_price(new_price, old_price, max_limit_price):
    min_limit_price = 20 # 强制托管宝贝的最低出价为0.20元

    # 避免出价都一样
    min_price = min_limit_price + random.randint(0, 10)
    max_price = max_limit_price + random.randint(-10, -1)

    # 关键词出价不能低于 0.05 元
    max_price = max_price >= 5 and max_price or max_limit_price
    min_price = 5 <= min_price <= max_limit_price and min_price or max(5, int((max_price + 5) / 2))

    min_desc = '低于%.2f元' % (min_limit_price / 100.0)
    max_desc = '超出限价'

    if max_limit_price < min_limit_price:
        return max_limit_price, '限价太低'

    if new_price > old_price: # 加价时
        if old_price > max_limit_price:
            return max_price, max_desc
        if new_price > max_limit_price: # 超过限价时
            return max(old_price, max_price), max_desc # 取较大值，防止反而降价
        if new_price < min_limit_price:
            return min_price, min_desc
        return new_price, ''

    if new_price < old_price: # 降价时
        if old_price < min_limit_price:
            return min_price, min_desc
        if new_price > max_limit_price: # 超过限价时
            return max_price, max_desc
        if new_price < min_limit_price:
            return min(old_price, min_price), min_desc # 取较小值，防止反而加价
        return new_price, ''

    if new_price > max_limit_price: # 不改价时，也要校验价格
        return max_price, max_desc

    return new_price, ''


class KeywordDryRun():
    """关键词演习，即每个关键词将怎样优化、改价"""
    def __init__(self, kw):
        self.kw = kw
        self.kw.modify_price_factor = 1

    def check_price(self, new_price):
        new_price = self.kw.max_price + (new_price - self.kw.max_price) * self.kw.modify_price_factor * self.kw.increase_reduce_factor # 加入改价幅度、加大减少投入
        calc_new_price, validate_reason = validate_price(new_price, self.kw.max_price, self.kw.limit_price)
        if calc_new_price != self.kw.max_price:
            self.kw.new_price = calc_new_price
        if validate_reason:
            self.kw.optm_reason += ', 但%s' % validate_reason
        return

    def del_kw(self):
        self.kw.is_delete = True
        return

    def upd_price(self, price):
        self.check_price(int(price))
        return

    def upd_match(self, match_scope = 4):
        if match_scope in [1, 4]:
            self.kw.new_match_scope = match_scope
        return

    def upd_kw(self, price, match_scope = 0): # 即将废弃掉
        match_scope = int(match_scope)
        if match_scope in [1, 4]:
            self.kw.new_match_scope = match_scope
        self.check_price(int(price))
        return

    def run_cmd(self, kw_cmd_list, data):
        kw = self.kw
        if kw.is_locked: # 设置为自动抢排名的，跳过优化
            return
        if kw.is_delete or kw.new_price or kw.new_match_scope: # 可能在宝贝层面已优化
            return
        item = data.item
        adg = data.adgroup
        camp = data.campaign
        mnt_camp = data.mnt_campaign
        cat = data.category
        self.kw.modify_price_factor = getattr(adg, 'modify_price_factor', 1)
        self.kw.increase_reduce_factor = getattr(adg, 'increase_reduce_factor', 1)
        self.check_price(kw.max_price)
        for kw_cmd in kw_cmd_list:
            try:
                if eval(kw_cmd.compiled_cond):
                    kw.optm_reason = kw_cmd.desc
                    kw.cmd = kw_cmd.name
                    eval(kw_cmd.compiled_operate)
                    break
            except Exception, e:
                log.error('run kw cmd error, cmd=%s, kw=%s, e=%s' % (kw_cmd.name, str(kw), e))
        return

    def test_run_cmd(self, kw_cmd_list, data):
        '''单元测试用'''
        kw = self.kw
        item = data.item
        adg = data.adgroup
        camp = data.campaign
        mnt_camp = data.mnt_campaign
        cat = data.category
        self.kw.modify_price_factor = getattr(adg, 'modify_price_factor', 1)
        self.kw.increase_reduce_factor = getattr(adg, 'increase_reduce_factor', 1)
        self.check_price(kw.max_price)
        for kw_cmd in kw_cmd_list:
            try:
                eval(kw_cmd.compiled_cond)
                eval(kw_cmd.compiled_operate)
            except Exception, e:
                log.error('run kw cmd error, cmd=%s, kw=%s, e=%s' % (kw_cmd.name, str(kw), e))
        return



class AdgroupDryRun():
    '''
    该类的方法，统一在方法内加上说明，参照 add_word 格式。
    因为函数名及说明会被页面 strategy_cfg 页面调用
    '''

    def __init__(self, adg_wrapper):
        self.adg = adg_wrapper.adgroup
        self.item = adg_wrapper.item
        self.kw_list = adg_wrapper.kw_list
        self.top_element_word = adg_wrapper.topkw_elementword()
        self.kw_g_ppc7 = adg_wrapper.analyze_result['kw_g_ppc7']
        self.bid_factor = adg_wrapper.bid_factor
        self.sync_qscore_flag = adg_wrapper.analyze_result.get('sync_qscore_flag', False)

    def add_word(self, conf_name = 'auto_change'):
        '''加词'''

        def get_select_conf(mnt_type, conf_name):
            select_type = ''
            add_word_type = ''
            if conf_name in ['auto_change', 'auto_select']:
                select_type = mnt_type in [1, 3] and 'precise' or 'traffic'
                add_word_type = conf_name.split('_')[1]
                conf_name = '' # 将conf_name置空，由选词配置那边获取
            return add_word_type, select_type, conf_name

        if self.adg.has_selected_word:
            return

        add_kw_list = []
        if len(self.kw_list) < 195:
            add_word_type, select_type, conf_name = get_select_conf(self.adg.mnt_type, conf_name)
            cur_word_count = len(self.kw_list)
            need_count = int((200 - cur_word_count) * 1.2)
            select_conf = SelectConfManage.get_selectconf(item = self.item, select_type = select_type, conf_name = conf_name)
            if add_word_type == 'change': # 换词时，要过滤「已删词」
                select_conf.delete_conf['remove_del'] = 1
            self.item.select_conf = select_conf
            self.item.get_label_dict.get('S', []).extend(self.top_element_word)
            mnt_select_word_list = KeywordSelector.get_mnt_select_words(self.item, self.adg, select_conf, need_count)
            add_kw_list.extend(mnt_select_word_list)
        # 加词时,默认移动端价格=pc价格*移动端折扣, 所以这里需要根据移动端限价计算出 为了移动端不超过限价时,默认出价的上限.
        limit_price = min(self.adg.user_limit_price_pc, int(self.adg.user_limit_price_mobile * 100.0 / self.adg.real_mobile_discount))
        for kw in add_kw_list:
            test_price = max(kw.cat_cpc * self.bid_factor, kw.cat_cpc + self.kw_g_ppc7 * (self.bid_factor - 1))
            kw.new_price, _ = validate_price(test_price, 50, limit_price)
        self.adg.add_kw_list = add_kw_list
        self.adg.has_selected_word = True
        return

    def optm_qscore(self):
        '''优化质量得分'''
        if not self.sync_qscore_flag:
            return

        most_del_count = min(int(len(self.kw_list) * 0.2), 15)
        if most_del_count == 0:
            return

        low_qscore_kw_list = [kw for kw in self.kw_list if 0 < kw.qscore < 5 and kw.rpt7.roi == 0 and
                              (kw.rpt7.click < 10 and kw.rpt7.click < self.adg.rpt7.click * 0.1)]
        low_qscore_kw_list.sort(key = lambda kw: kw.qscore)
        for kw in low_qscore_kw_list[:most_del_count]:
            kw.is_delete = True
            kw.optm_reason = '质量得分差'
        # log.info('mnt: optm_qscore, delete kw count = %s' % len(low_qscore_kw_list[:most_del_count]))
        return

    # def modify_yd_discount(self):
    #     '''优化移动折扣'''
    #     pass
