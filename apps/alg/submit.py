# coding=UTF-8

from apps.common.utils.utils_log import log
from apps.subway.upload import add_keywords, delete_keywords, update_keywords

class KeywordSubmit(object):
    """docstring for KeywordSubmit"""
    def __init__(self, shop_id, camp_id, adg_id, opter = 3, opter_name = ''):
        super(KeywordSubmit, self).__init__()
        self.shop_id = shop_id
        self.camp_id = camp_id
        self.adg_id = adg_id
        self.opter = opter
        self.opter_name = opter_name

    def submit_deleted_keywords(self, del_kw_list):
        deleted_num = 0
        if del_kw_list:
            try:
                deleted_id_list = delete_keywords(shop_id = self.shop_id, campaign_id = self.camp_id, kw_arg_list = del_kw_list, opter = self.opter, opter_name = self.opter_name)
                deleted_num = len(deleted_id_list)
            except Exception, e:
                log.error('del keywords error, shop_id=%s, adg_id=%s, e=%s' % (self.shop_id, self.adg_id, e))
        return deleted_num

    def sumbit_updated_keywords(self, upd_kw_list):
        updated_num = 0
        if upd_kw_list:
            try:
                updated_id_list, _ = update_keywords(shop_id = self.shop_id, kw_arg_list = upd_kw_list, opter = self.opter, opter_name = self.opter_name)
                updated_num = len(updated_id_list)
            except Exception, e:
                log.error('update keywords error, shop_id=%s, adg_id=%s, e=%s' % (self.shop_id, self.adg_id, e))
        return updated_num

    def submit_added_keywords(self, add_kw_list):
        added_num, repeat_num = 0, 0
        if add_kw_list:
            try:
                _, added_keyword_list, repeat_word_list = add_keywords(shop_id = self.shop_id, adgroup_id = self.adg_id, kw_arg_list = add_kw_list, opter = self.opter, opter_name = self.opter_name)
                added_num = len(added_keyword_list)
                repeat_num = len(repeat_word_list)
            except Exception, e:
                log.error('add keywords error, shop_id=%s, adg_id=%s, e=%s' % (self.shop_id, self.adg_id, e))
        return added_num, repeat_num

    @classmethod
    def alg_dry_run(cls, adg_wrapper):
        add_kw_list = []
        upd_kw_list = []
        del_kw_list = []
        for kw in adg_wrapper.adgroup.add_kw_list:
            add_kw_list.append([kw.word, kw.new_price, None, None, None])
        for kw in adg_wrapper.kw_list:
            if kw.mnt_opt_type == 2:
                    continue
            if kw.is_delete_pc and kw.is_delete_mobile and kw.mnt_opt_type == 0 and adg_wrapper.can_del_kw:
                del_kw_list.append([kw.adgroup_id, kw.keyword_id, kw.word, 0, 0, ''])
                continue
            temp = {}
            if adg_wrapper.can_upd_price and kw.new_price_pc:
                temp.update({'max_price':kw.new_price_pc,
                             'old_price':kw.max_price_pc,
                             'is_default_price':0})
            if adg_wrapper.can_upd_price and kw.new_price_mobile:
                temp.update({'max_mobile_price':kw.new_price_mobile,
                             'mobile_old_price':kw.max_price_mobile,
                             'mobile_is_default_price':0})
            match_scope = kw.match_scope
            if kw.new_match_scope_pc and kw.new_match_scope_pc < match_scope:
                match_scope = kw.new_match_scope_pc
            if kw.new_match_scope_mobile and kw.new_match_scope_mobile < match_scope:
                match_scope = kw.new_match_scope_mobile
            if adg_wrapper.can_upd_match and match_scope != kw.match_scope:
                temp.update({'match_scope': match_scope})
            if temp:
                upd_kw_list.append([kw.campaign_id, kw.adgroup_id, kw.keyword_id, kw.word, temp])
        most_add_count = 200 - len(adg_wrapper.kw_list) + len(del_kw_list)
        add_kw_list = add_kw_list[: most_add_count > 0 and int(most_add_count * 1.2) or 0]
        return upd_kw_list, del_kw_list, add_kw_list

    @classmethod
    def execute(cls, shop_id, campaign_id, adgroup_id, opter, opter_name, upd_kw_list, del_kw_list, add_kw_list):
        kw_submit = cls(shop_id, campaign_id, adgroup_id, opter, opter_name)
        updated_num = kw_submit.sumbit_updated_keywords(upd_kw_list) # 先保证所有词在限价内
        deled_num = kw_submit.submit_deleted_keywords(del_kw_list)
        added_num, _ = kw_submit.submit_added_keywords(add_kw_list)
        log.info('submit keyword finished: updated %s kws, deleted %s kws, added %s kws, shop_id=%s, adg_id=%s' %
                 (updated_num, deled_num, added_num, shop_id, adgroup_id))
        return updated_num, deled_num, added_num
