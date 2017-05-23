# coding=UTF-8
import math
import copy
import datetime
from operator import attrgetter

from django.conf import settings
from apilib import TopObject
from apps.common.utils.utils_log import log
from apps.common.utils.utils_string import get_ordered_str
from apps.common.constant import Const
from apps.common.biz_utils.utils_tapitools import get_gdata_by_redis
from apps.kwslt.select_words import SelectConfManage, Combiner, \
    ItemScorer, WordFactory, KeywordCrawler
from apps.kwslt.select_words import select_words
from apps.kwlib.base import get_tb_recommend_keywords, get_relatewords_new, \
    get_word_subdata
# from apps.kwlib.models_mongodb import RequestAPIMonitor
from apps.kwslt.base import rm_not_relate_keyword, is_include_word, \
    sort_by_label_coverage, sort_by_label_click, sort_by_label_favtotal, \
    sort_by_label_roi
from apps.kwlib.api import get_timescope, check_kw_2save_inDB

class SelectKeywordPackage():

    def __init__(self, kw_list):
        self.score_1000_list = []
        self.score_800_1000_list = []
        self.score_700_800_list = []
        self.score_600_700_list = []
        self.score_500_600_list = []
        self.result_list = [self.score_1000_list, self.score_800_1000_list, self.score_700_800_list, self.score_600_700_list, self.score_500_600_list]
        self.all_result_list = kw_list
        self.init_result_list(kw_list)
        self.r_traffic_package = self.traffic_package()
        self.r_coverage_package = self.coverage_package()
        self.r_high_cost_performance = self.higher_cost_performance_package()

    def init_result_list(self, kw_list):
        for  kw in kw_list:
            if kw.keyword_score == 1000:
                self.score_1000_list.append(kw)
            elif 800 <= kw.keyword_score <= 1000:
                self.score_800_1000_list.append(kw)
            elif 700 <= kw.keyword_score <= 800:
                self.score_700_800_list.append(kw)
            elif 600 <= kw.keyword_score <= 700:
                self.score_600_700_list.append(kw)
            elif 500 <= kw.keyword_score <= 600 :
                self.score_500_600_list.append(kw)
            else:
                continue

    def sort_by_field(self, kw_list, sort_field, resut_sort_field):
        kw_list = sorted(kw_list, key = lambda x:getattr(x, sort_field), reverse = True)
#         return kw_list[:len(kw_list) / 4 * 3 - 1], kw_list[len(kw_list) / 4 * 3 + 1:]
        kw_3_4_list, kw_1_4_list = kw_list[:len(kw_list) / 4 * 3 - 1], kw_list[len(kw_list) / 4 * 3 + 1:]
        return [kw.word for kw in sorted(kw_3_4_list, key = lambda x:getattr(x, resut_sort_field), reverse = True) + sorted(kw_1_4_list, key = lambda x:x.cat_click, reverse = True)]

    """
    .转化包实现
    .根据匹配度的梯度1000分，800分，700分...500分，每个梯度根据点击量进行排序，如果梯度内关键词少于8个，那么直接根据点击量排序
    .否则将关键词列表
    """
    def coverage_package(self):
        rr = []
        for tmp_list in self.result_list:
            if len(rr) >= 200:
                return list(reversed(rr[:200]))
            kw_list = [kw for kw in tmp_list if kw.coverage]
            if len(kw_list) <= 8:
                rr.extend([kw.word for kw in sorted(kw_list, key = lambda x:x.cat_click, reverse = True)])
                continue
            rr.extend(self.sort_by_field(kw_list, 'favtotal', 'coverage'))
        return list(reversed(rr[:200]))

    """
    .流量包实现
    """
    def traffic_package(self):
        rr = []
        for tmp_list in self.result_list:
            if len(rr) >= 200:
                return list(reversed(rr[:200]))
            kw_list = [kw for kw in tmp_list if kw.favtotal]
            rr.extend([kw.word for kw in sorted(kw_list, key = lambda x : x.cat_click, reverse = True)])
        return list(reversed(rr[:200]))

    """
    .高性价比包实现
    """
    def higher_cost_performance_package(self):
        rr = []
        for tmp_list  in self.result_list:
            if len(rr) >= 200:
                return list(reversed(rr[:200]))
            kw_list = [kw for kw in tmp_list if kw.favtotal and kw.coverage]
            if len(kw_list) <= 8:
                rr.extend([kw.word for kw in sorted(kw_list, key = lambda x:x.cat_click, reverse = True)])
                continue
            rr.extend(self.sort_by_field(kw_list, 'cat_click', 'roi'))
        return list(reversed(rr[:200]))

    """
    .移动包实现
    """
    @classmethod
    def mobile_package(cls, kw_list):
        word_dict = {unicode(kw[0]):kw[1:] for kw in kw_list if kw[0]}
        timescope = get_timescope()
        word_list = word_dict.keys()
        tmp_dict = get_word_subdata(word_list, timescope[0], timescope[1])
#         RequestAPIMonitor.insertDocument(len(word_list), len(tmp_dict), 2, u'细分数据移动包')
        keyword_list = []
        for word in word_list:
            if not word in tmp_dict:
                continue

            for ll in tmp_dict[word]:
                if ll['network'] == 4:
                    cpc = float('cpc' in ll and ll['cpc'] or 0.0) or 30
                    new_obj = TopObject()
                    new_obj.word = word
                    new_obj.cat_pv = ll['impression']
                    new_obj.cat_click = ll['click']
                    new_obj.cat_cpc = cpc
                    new_obj.cat_competition = 'competition' in ll and ll['competition'] or 0
                    new_obj.cat_ctr = float('ctr' in ll and ll['ctr'] or 0.0)
                    new_obj.keyword_score = word_dict[word][0]
                    new_obj.is_delete = word_dict[word][1]
                    new_obj.new_price = cpc
                    new_obj.coverage = float('coverage' in ll and ll['coverage']) * 100.0
                    keyword_list.append(new_obj)
        return keyword_list

    """
    .系统推荐实现
    """
    @classmethod
    def recommand_by_system(cls, max_add_num, word_list):
        okay_count, temp_keyword_list, filter_field_list = 0, [], []
        if word_list:
            filter_cond_dict = {'keyword_score':{'weight':5, 'svl':[250, 500, 750, 1000], "from":0, 'limit':1000, 'series_name_cn':'匹配度', 'color':"blue"},
                                       'coverage':{'weight':4, 'svl':5, 'exclude':[0, None], 'series_name_cn':'转化率', 'color':"blue"},
                                       'cat_competition':{'weight':3, 'svl':5, 'series_name_cn':'竞争度', 'color':"blue"},
                                       'cat_click':{'weight':2, 'svl':5, 'exclude':[0, None], 'series_name_cn':'点击指数', 'color':"blue"},
                                       'cat_cpc':{'weight':1, 'svl':5, 'exclude':[0, None], 'series_name_cn':'市场均价', 'color':"blue"},
                                       }
            for field, cfg in filter_cond_dict.items():
                cfg['series_name'] = field

            okay_count, temp_keyword_list, filter_field_list = KeywordSelector.do_filter_keywords(word_list, max(max_add_num, 10), filter_cond_dict)
        filter_field_list = [fl[1] for fl in filter_field_list]
        return okay_count, temp_keyword_list, filter_field_list


class KeywordSelector():
    '''
    该类改成一个选词用的工具类，比如构造淘词的条件，组合关键词，爬词等
    '''
    @classmethod
    def get_quick_select_words(cls, item, adgroup, mode = 'precise'):
        item.select_conf = SelectConfManage.get_selectconf(item, mode)
        result_list = select_words(adgroup, item, item.select_conf)
        result_list = cls.get_recommend_word(result_list, adgroup)
#         result_list = cls.claw_words(result_list, item, adgroup)
        result_list = cls.get_delete_info(result_list, adgroup)
#         item.clear_all_label() # 上线之后删除
        return result_list

    @classmethod
    def get_precise_select_words(cls, item, adgroup, select_arg):
        item.select_conf = SelectConfManage.get_selectconf(item, 'taoci') # 淘词时，一般条件中包含产品词
        # 海选条件自动生成
        select_arg = select_arg.replace('，', ',')
        filter_conf = cls.get_filter_conf(select_arg, item.cat_id)
        item.select_conf.candi_filter = filter_conf
        result_list = select_words(adgroup, item, item.select_conf)
#         result_list = cls.claw_words(result_list, item, adgroup, select_arg)
        result_list = cls.get_delete_info(result_list, adgroup)
        return result_list

    @classmethod
    def get_combiner_words(cls, adgroup, prdtword_list, dcrtword_list, prmtword_list):
        result_list = Combiner.combine_words2(prdtword_list, dcrtword_list, prmtword_list)
        result_list = cls.process_word(result_list, adgroup)
        # 手工组词，默认用户输入的都是跟宝贝相关的词
        for kw in result_list:
            kw.keyword_score = 1000
        result_list.sort(key = attrgetter('keyword_score', 'cat_click', 'cat_ctr', 'cat_pv'), reverse = True)
        return result_list

    @classmethod
    def get_manual_word(cls, manual_list, adgroup):
        result_list = cls.process_word(manual_list, adgroup)
        return result_list

    @classmethod
    def get_mnt_select_words(cls, item, adgroup, select_conf, max_num):
        result_list = select_words(adgroup, item, select_conf, max_num, True)
        if max_num > 150 and len(result_list) < max_num * 0.1:
            result_list = cls.get_recommend_word(result_list, adgroup)
            result_list = result_list[:int(max_num * 0.3)]
        return result_list

    @classmethod
    def get_gdata_2obj(cls, word_list, adgroup):
        kw_list = []
        gdata_dict = get_gdata_by_redis(word_list)
        for key in gdata_dict:
            value = gdata_dict[key]
            # 手工组词、手工加词时 不过滤没有全网数据的词
            # if not value['pv']:
            #     continue
            word = key.decode('utf8')
            keyword_score, label = ItemScorer(adgroup.item.get_label_conf_list()).score_participles_by_item(word)
            cpc = value['cpc'] or 30
            new_obj = TopObject()
            new_obj.word = word
            new_obj.cat_pv = value['pv']
            new_obj.cat_click = value['click']
            new_obj.cat_cpc = cpc
            new_obj.cat_competition = value['cmpt']
            new_obj.cat_ctr = value['ctr']
            new_obj.keyword_score = keyword_score
            new_obj.new_price = cpc
            new_obj.label = label
            new_obj.roi = value['roi']
            new_obj.coverage = value['coverage'] * 100.0
            new_obj.favtotal = value['favtotal']
            kw_list.append(new_obj)
        return kw_list

    @classmethod
    def get_recommend_word(cls, result_list, adgroup):

        if len(result_list) > 0 or not adgroup:
            return result_list
        today = datetime.datetime.today()
        if adgroup.no_recmd_word_time and adgroup.no_recmd_word_time + datetime.timedelta(days = 5) > today:
            return result_list
        try:
            recmd_dict, word_list, kw_list = {}, [], []
            recmd_list = get_tb_recommend_keywords(adgroup.shop_id, adgroup.adgroup_id)
            for kw in recmd_list :
                word = kw['word']
                recmd_dict[word] = kw
                word_list.append(word)
            kw_list = cls.get_gdata_2obj(word_list, adgroup)

            # 结合淘宝数据更新匹配度
            tmp_list, word_list = [], []
            for kw in kw_list:
                if kw.keyword_score >= 666:
                    tmp_list.append(kw)
                    word_list.append(kw.word)
            if len(kw_list):
                kw_list.sort(key = attrgetter('keyword_score', 'cat_click', 'cat_ctr', 'cat_pv'), reverse = True)
                bad_kw_list = [kw for kw in result_list if kw.keyword_score < 1000]
                result_list = kw_list + bad_kw_list
            else:
                adgroup.no_recmd_word_time = today
                adgroup.save()
            word_list = cls.rm_include_word(word_list, adgroup.item.garbage_word_list)
            result_list = [kw for kw in result_list if kw.word in word_list]
            log.info('extend recommend word: count = %s' % len(kw_list))
        except Exception, e:
            log.error('get_ recommend word error: shop_id=%s, adg_id=%s, e=%s' % (adgroup.shop_id, adgroup.adgroup_id, e))
        finally:
            return result_list

    @classmethod
    def claw_words(cls, result_list, item, adgroup, select_arg = ''):
        if len(result_list) > 50:
            return result_list

        relate_list = item.product_word_list
        if select_arg:
            try:
                relate_list = [wd for wd in select_arg.split(',') if wd]
            except Exception, e:
                log.info("can not get word_filter and the error is = %s" % e)
                relate_list = []
        word_list = KeywordCrawler.crawl_words_by_word_list(item.product_word_list, 200)
        if len(word_list) < 50:
            word_list.extend(get_relatewords_new(word_list))
        word_list = check_kw_2save_inDB(word_list)
        word_list = rm_not_relate_keyword(word_list, relate_list)
        kw_list = cls.process_word(word_list, adgroup, item)
        for kw in kw_list:
            if kw.keyword_score > 500:
                kw.keyword_score -= 1
                result_list.append(kw)
        log.info('extend claw word: count = %s' % len(kw_list))
        return result_list

    @classmethod
    def process_word(cls, word_list, adgroup, item = None):
        # 参数中有 adgroup, 为什么还要 item：选词预览页面只有 item, 没有 adgroup
        if not item:
            item = adgroup.item
        word_list = cls.rm_include_word(word_list, item.garbage_word_list)
        word_list = cls.rm_same_word_byword(word_list)
        word_list = cls.rm_cur_word(word_list, adgroup)
#         gdata_dict = get_kw_gdata_4select_word(word_list)
#         score_dict = cls.get_word_score(item, word_list)
#         result_list = cls.change_dict_2obj(word_list, gdata_dict, score_dict)
        result_list = cls.get_gdata_2obj(word_list, adgroup)
        result_list = cls.get_delete_info(result_list, adgroup)
        result_list.sort(key = attrgetter('keyword_score', 'cat_click', 'cat_ctr', 'cat_pv'), reverse = True)
        return result_list

    @staticmethod
    def rm_cur_word(kw_list, adgroup):
        result_list = []
        if not adgroup:
            return kw_list
        cur_dict = {kw:1 for kw in adgroup.select_word_list}
        if not cur_dict:
            return kw_list
        for kw in kw_list:
            if len(kw) > 20:
                continue
            if cur_dict.has_key(get_ordered_str(kw)):
                continue
            result_list.append(kw)
        return result_list

    @staticmethod
    def rm_include_word(kw_list, rm_word_list):
        result_list = []
        if not rm_word_list:
            return kw_list
        for kw in kw_list:
            if is_include_word(kw, rm_word_list):
                continue
            result_list.append(kw)
        return result_list

    @staticmethod
    def rm_same_word_byword(word_list):
        word_dict = {}
        result_list = []
        for kw in word_list:
            word = get_ordered_str(kw)
            if word_dict.has_key(word):
                continue
            word_dict[word] = 1
            result_list.append(kw)
        return result_list

    @staticmethod
    def get_word_score(item, word_list):
        label_conf_list = item.get_label_conf_list(custome_word_dict = {})
        item_scorer = ItemScorer(label_conf_list)
        score_dict = {}
        for word in word_list:
            score_dict[word], _ = item_scorer.score_participles_by_item(word)
        return score_dict

    @staticmethod
    def change_dict_2obj(word_list, gdata_dict, score_dict):
        result_list = []
        for key in word_list:
            tmp = gdata_dict.get(str(key), TopObject())
            new_obj = TopObject()
            new_obj.word = key
            new_obj.cat_pv = getattr(tmp, 'pv', 0)
            new_obj.cat_click = getattr(tmp, 'click', 0)
            new_obj.cat_cpc = getattr(tmp, 'avg_price', 0)
            new_obj.cat_ctr = getattr(tmp, 'ctr', 0)
            new_obj.cat_competition = getattr(tmp, 'competition', 0)
            new_obj.keyword_score = score_dict.get(key, 600)
            result_list.append(new_obj)
        return result_list

    @staticmethod
    def get_delete_info(keyword_list, adgroup):
        result_list = []
        if not adgroup:
            return keyword_list
        word_dict = {get_ordered_str(kw):1 for kw in adgroup.deleted_word_list}
        for keyword in keyword_list:
            if not word_dict.has_key(get_ordered_str(keyword.word)):
                    keyword.is_deleted = False # 不在删除词之列
            else:
                keyword.is_deleted = True # 是曾被删除过的词
            if keyword.cat_cpc is None or keyword.cat_cpc < 5: # 如果cat_cpc小于5分钱。就用30分
                keyword.cat_cpc = 30
            result_list.append(keyword)
        return result_list

    @staticmethod
    def build_field_algorithm_info(obj_list, filter_field_list, chose_num):
        '''(1).从obj_list中找出filter_field_list中的各个条件的值分布==>value_list->vl
                如：obj_list中的各个obj的cat_pv分别为：100,200,150,300,200,500,400,800,1000,1100；
             chose_num为300，即过滤时想获取的关键词数，则生成的filter_field_dict['cat_pv']['svl'] ==> [150,300,800]
        (2)最后确保obj_list以filter_field_list中的第一个field排序'''
        def field_cmp(x, y):
            if x.data[pos] > y.data[pos]:
                return 1
            elif x.data[pos] < y.data[pos]:
                return -1
            else:
                return 0

        def add_fv_to_svl(fv, cfg):
            if fv is None:
                fv = 0
            elif fv > cfg['limit']:
                fv = cfg['limit']
            if not cfg['svl']:
                if fv:
                    cfg['svl'].append(fv)
            elif fv != cfg['svl'][-1]:
                cfg['svl'].append(fv)

        if not obj_list:
            log.info('(2.2.2)KeywordSelector.build_field_algorithm_info obj_list is empty!')
            return filter_field_list

        total_len = len(obj_list)
        if total_len > chose_num * 10:
            step_len = chose_num
        elif total_len > chose_num * 5:
            step_len = chose_num / 2 + 1
        else:
            step_len = chose_num / 5 + 1

        filter_field_list.reverse() # 确保最后以key field 排序
        temp_obj_list = obj_list[:]

        for field, cfg in filter_field_list:
            if cfg.has_key('svl'):
                if isinstance(cfg['svl'], list):
                    continue
                else:
                    field_step_len = total_len / cfg['svl'] + 1
            else:
                field_step_len = step_len

            pos = cfg['pos']
            temp_obj_list.sort(cmp = field_cmp) # 根据属性升序排序
            if not cfg.has_key('from'):
                cfg['from'] = temp_obj_list[0].data[pos]
                if not cfg['from']:
                    cfg['from'] = 0
            if not cfg.has_key('limit'):
                cfg['limit'] = temp_obj_list[-1].data[pos]
            if cfg['limit'] == cfg['from']:
                cfg['limit'] = cfg['from'] + 1
            cfg['svl'] = []
            if cfg['series_name'] in ['cat_cpc', 'coverage']:
                cfg['limit'] = float(cfg['limit']) / 100
                cfg['from'] = float(cfg['from']) / 100
                for i in range(field_step_len, total_len, field_step_len):
                    fv = float(temp_obj_list[i].data[pos]) / 100
                    add_fv_to_svl(fv, cfg)
                fv = float(temp_obj_list[-1].data[pos]) / 100
                add_fv_to_svl(fv, cfg)
            else:
                for i in range(field_step_len, total_len, field_step_len):
                    fv = int(temp_obj_list[i].data[pos])
                    add_fv_to_svl(fv, cfg)
                fv = int(temp_obj_list[-1].data[pos])
                add_fv_to_svl(fv, cfg)

        filter_field_list.reverse() # 顺序还原
        log.info('(2.2.2)KeywordSelector.build_field_algorithm_info finish, len(temp_obj_list)=%s, chose_num=%s' % (len(temp_obj_list), chose_num))
        return filter_field_list

    # 按权重排序过滤条件(如果weight小于0，也参与权重排序)
    @staticmethod
    def sort_by_weight(filter_field_list, reverse = False):
        def weight_cmp(x, y):
            if x[1]['weight'] > y[1]['weight']:
                return 1
            elif x[1]['weight'] < y[1]['weight']:
                return -1
            else:
                return 0
        filter_field_list.sort(cmp = weight_cmp, reverse = reverse)
        return filter_field_list

    # 关键词过滤条件
    @staticmethod
    def get_filter_conf(filter, cat_id):
        # 根据filter解析出条件
        or_temp_list = filter.split(',')
        filter_list = []
        for and_word in or_temp_list:
            syn_list = []
            word_list = and_word.split(' ')
            for word in word_list:
                word_syn_list = WordFactory.get_extend_words(cat_id, [word])
                syn_list.append(word_syn_list)
            o_list = KeywordSelector.union_SynonymWord_list(syn_list)
            # 去掉多余的词
            set_list = [set(ol.replace(' ', '')) for ol in o_list]
            need_set_list = []
            for sl in set_list:
                is_need = True
                for sl1 in set_list:
                    if sl1 != sl and (not (sl1 - sl)):
                        is_need = False
                        break
                if is_need:
                    need_set_list.append(sl)
            for nsl in need_set_list:
                str_and_eval = '(not (%s - set(word)))' % nsl
                filter_list.append(str_and_eval)
        str_filter = ' or '.join(filter_list)
        return str_filter

    @staticmethod
    def union_SynonymWord_list(words_list):
        # 合并同义词数组
        if len(words_list) == 1:
            return words_list[0]
        ii = 0
        f_list = words_list[ii]
        range_list = range(len(words_list))
        range_list.remove(0)
        for ii in range_list:
            s_list = words_list[ii]
            temp_list = []
            for f_word in f_list:
                for s_word in s_list:
                    new_word = f_word + ' ' + s_word
                    temp_list.append(new_word)
            f_list = temp_list
        return f_list

    @staticmethod
    def do_filter_keywords(all_candi_keyword_list, max_add_num, filter_cond_dict = None):
        log.info('(2.1)KeywordSelector.do_filter_keywords,len(all_candi_keyword_list)=%s' % len(all_candi_keyword_list))
        filter_field_dict = copy.deepcopy(filter_cond_dict)

        # 按权重对filter_field_list降序排序
        filter_field_list = KeywordSelector.sort_by_weight(filter_field_dict.items(), reverse = True)

        # 往每个cfg中放入序号pos
        for i in range(len(filter_field_list)):
            filter_field_list[i][1]['pos'] = i

        # 按顺序生成keyword.data  结构为[keyword_score, cat_competition, cat_click, cat_pv, cat_cpc]
        for keyword in all_candi_keyword_list:
            keyword.data = []
            for ff in filter_field_list:
                keyword.data.append(KeywordSelector.getattr(keyword, ff[0]))

        temp_keyword_list = all_candi_keyword_list
        if not temp_keyword_list:
            log.info('(2.3)KeywordSelector.do_filter_keywords end! temp_keyword_list is NULL\n')
            return 0, [], []

        # 计算页面需要选中的候选词个数
        max_add_num = (max_add_num <= 0 and 5 or max_add_num)
        chose_num = int(max_add_num * math.sqrt(math.sqrt(float(Const.KWLIB_KEYWORD_ADD_RADIX) / max_add_num)))
        chose_num = min(len(temp_keyword_list), chose_num)

        # 根据候选词列表，划分刻度值
        KeywordSelector.build_field_algorithm_info(temp_keyword_list, filter_field_list, chose_num)

        # 设置关键词is_ok标记，并设置滑竿属性
        okay_count = KeywordSelector.set_chose_keyword_4filter(temp_keyword_list, filter_field_list, chose_num)
        log.info('(2.3)KeywordSelector.do_filter_keywords end! len(temp_keyword_list)=%s\n' % len(temp_keyword_list))
        return okay_count, temp_keyword_list, filter_field_list

    @staticmethod
    def do_tao_keywords(all_candi_keyword_list, max_add_num, filter_cond_dict = None):
        log.info('(2.1)KeywordSelector.do_tao_keywords, len(all_candi_keyword_list)=%s' % len(all_candi_keyword_list))
        filter_field_dict = copy.deepcopy(filter_cond_dict)

        # 按权重对filter_field_list降序排序
        filter_field_list = KeywordSelector.sort_by_weight(filter_field_dict.items(), reverse = True)

        # 往每个cfg中放入序号pos
        for i in range(len(filter_field_list)):
            filter_field_list[i][1]['pos'] = i

        # 按顺序生成keyword.data  结构为[keyword_score, cat_competition, cat_click, cat_pv, cat_cpc]
        for keyword in all_candi_keyword_list:
            keyword.data = []
            for ff in filter_field_list:
                keyword.data.append(KeywordSelector.getattr(keyword, ff[0]))

        temp_keyword_list = all_candi_keyword_list
        if not temp_keyword_list:
            log.info('(2.3)KeywordSelector.do_filter_keywords end! temp_keyword_list is NULL\n')
            return 0, [], []

        # 计算页面需要选中的候选词个数
        max_add_num = (max_add_num <= 0 and 5 or max_add_num)
        chose_num = int(max_add_num * math.sqrt(math.sqrt(float(Const.KWLIB_KEYWORD_ADD_RADIX) / max_add_num)))
        chose_num = min(len(all_candi_keyword_list), chose_num)

        # 根据候选词列表，划分刻度值
        KeywordSelector.build_field_algorithm_info(temp_keyword_list, filter_field_list, chose_num)

        # 设置关键词is_ok标记
        okay_count = KeywordSelector.set_chose_keyword_4filter(temp_keyword_list, filter_field_list, chose_num)

        log.info('(2.3)KeywordSelector.do_tao_keywords end! len(temp_keyword_list)=%s\n' % len(temp_keyword_list))
        return okay_count, temp_keyword_list, filter_field_list

    # 设置关键词is_ok标记，被删除过的词不设置为选中标记；并设置滑竿属性。只有权重大于0的，才计算被选中的词的最大最小值
    @staticmethod
    def set_chose_keyword_4filter(temp_keyword_list, filter_field_list, chose_num):
        is_ok_num = 0
        # 设置关键词is_ok标记
        for keyword in temp_keyword_list:
            # if keyword.is_deleted:
            #     continue
            if is_ok_num >= chose_num:
                break
            elif is_ok_num == 0:
                # 给最大最小值赋初值
                for field, cfg in filter_field_list:
                    if cfg['weight'] > 0:
                        pos, min_value, max_value = cfg['pos'], "min_" + field, "max_" + field
                        if cfg['series_name'] in ['cat_cpc', 'coverage']:
                            cfg[min_value] = float(keyword.data[pos]) / 100
                            cfg[max_value] = float(keyword.data[pos]) / 100
                        else:
                            cfg[min_value] = int(keyword.data[pos])
                            cfg[max_value] = int(keyword.data[pos])
            else:
                # 比较得到最大最小值
                for field, cfg in filter_field_list:
                    if cfg['weight'] > 0:
                        pos, min_value, max_value = cfg['pos'], "min_" + field, "max_" + field
                        if cfg['series_name'] in ['cat_cpc', 'coverage']:
                            if float(keyword.data[pos]) / 100 < cfg[min_value]:
                                cfg[min_value] = float(keyword.data[pos]) / 100
                            elif float(keyword.data[pos]) / 100 > cfg[max_value]:
                                cfg[max_value] = float(keyword.data[pos]) / 100
                        else:
                            if keyword.data[pos] < cfg[min_value]:
                                cfg[min_value] = int(keyword.data[pos])
                            elif keyword.data[pos] > cfg[max_value]:
                                cfg[max_value] = int(keyword.data[pos])
            keyword.is_ok = 1
            is_ok_num += 1

        # 设置滑竿属性
        for field, cfg in filter_field_list:
            if cfg["weight"] > 0:
                min_value, max_value = "min_" + field, "max_" + field
                if cfg.has_key(min_value) and cfg[min_value]:
                    cfg['current_from'] = cfg[min_value] # cfg[min_value]里面出现了None的情况，因此在上方加上判断
                    if cfg['current_from'] == cfg['limit']:
                        cfg['current_from'] = cfg['from']
                else:
                    cfg['current_from'] = cfg['from']
                if cfg.has_key(max_value):
                    cfg['current_to'] = cfg[max_value]
                    if cfg['current_to'] == cfg['from']:
                        cfg['current_to'] = cfg['limit']
                else:
                    cfg['current_to'] = cfg['limit']
            else:
                cfg['current_from'] = cfg['from']
                cfg['current_to'] = cfg['limit']

            if len(cfg['svl']) >= 3:
                i = 1
                cfg['heterogeneity'] = []
                for v in cfg['svl'][:-1]:
                    cfg['heterogeneity'].append('%s/%s' % (100 / len(cfg['svl']) * i, v))
                    i = i + 1

        log.info('(2.2.3)KeywordSelector.set_chose_keyword_4filter end! len(temp_keyword_list)=%s, is_ok_num=%s' % (len(temp_keyword_list), is_ok_num))
        return is_ok_num

    @staticmethod
    def getattr(obj, fields):
        fl = fields.split('.')
        for f in fl:
            try:
                if hasattr(obj, f):
                    obj = getattr(obj, f)
                else:
                    return None
            except AttributeError, e:
                if settings.DEBUG:
                    print e
                return None
        return obj

    @classmethod
    def get_all_package_keyword(cls, candidate_keyword_list, temp_keyword_list):
        skp = SelectKeywordPackage(candidate_keyword_list)
        keyword_list = []
        for kw in temp_keyword_list:
            """
            .keyword_list[关键词，市场均价，展现指数，点击指数，市场点击率，竞争指数，匹配度，初始出价，转化率，已删词，系统推荐，[关键词分类]]
            .关键词分类:大于0则表示该分类的排名，否则就是该关键词不计入分类，分类：[转化模式，流量模式，高性价比模式]
            """
            tmp_kw = [kw.word, kw.cat_cpc, kw.cat_pv, kw.cat_click, kw.cat_ctr, kw.cat_competition, kw.keyword_score, kw.new_price, kw.coverage, 0, 0, [0, 0, 0]]
            tmp_kw[9] = getattr(kw, 'is_deleted', 0)
            tmp_kw[10] = getattr(kw, 'is_ok', -1)
            compare_list = [skp.r_coverage_package, skp.r_traffic_package, skp.r_high_cost_performance]
            for i in range(3):
                if kw.word in compare_list[i]:
                    tmp_kw[-1][i] = compare_list[i].index(kw.word)
                else:
                    tmp_kw[-1][i] = -1
            keyword_list.append(tmp_kw)
        return keyword_list
