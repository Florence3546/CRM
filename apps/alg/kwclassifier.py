# coding=UTF-8

import copy
import datetime # 下面 eval 语句中引用到了

from apps.subway.models_keyword import Keyword
from apps.subway.realtime_report import RealtimeReport

def round2(i):
    return round(i, 2)

def div100(i):
    return round(i * 1.0 / 100, 2)

'''
批量优化树配置，配置有先后顺序，不能随意调整，影响页面显示顺序。
'''

'''批量优化搜索维度配置'''

BULK_TREE_LIST = [
    {'id': 'ROI', 'count': 0, 'text': '有转化', 'factor': compile('kw.rpt.roi > 0', '', 'eval')},
    {'id': 'FAV', 'count': 0, 'text': '有收藏,无转化', 'factor': compile('kw.rpt.favcount > 0', '', 'eval')},
    {'id': 'CLICK', 'count': 0, 'text': '有点击,无收藏,无转化', 'factor': compile('kw.rpt.click > 0', '', 'eval')},
    {'id': 'PV', 'count': 0, 'text': '有展现,无点击', 'factor': compile('kw.rpt.impressions > 0', '', 'eval')},
    {'id': 'NOPV', 'count': 0, 'text': '无展现', 'factor': compile('kw.create_time.date() < datetime.date.today()', '', 'eval')},
    {'id': 'FRESH', 'count': 0, 'text': '今日新加词', 'factor': compile('kw.create_time.date() >= datetime.date.today()', '', 'eval')},
    ]

BULK_SEARCH_LIST = [
    # {'id': 'suggest', 'name': '系统建议', 'auditions': compile('True', '', 'eval'), 'value': compile('kw.optm_type', '', 'eval'),
    #  'ref_value': '1', 'ref_range': [1, 2, 3], 'format_func': None, 'value_list': [], 'minimum_scale': 1, 'dispaly_unit': None, 'custom': False,
    #  'cond': [{'cls': 'SK', 'count': 0, 'text': '保留', 'range': ['', '']},
    #           {'cls': 'SL', 'count': 0, 'text': '删除', 'range': ['', '']},
    #           {'cls': 'SM', 'count': 0, 'text': '降价', 'range': ['', '']},
    #           {'cls': 'SH', 'count': 0, 'text': '加价', 'range': ['', '']},
    #           ]
    #  },
    # {'id': 'max_price', 'name': '当前出价', 'auditions': compile('True', '', 'eval'), 'value': compile('kw.max_price', '', 'eval'),
    #  'ref_value': 'max(self.adg.rpt.cpc, kw.g_cpc, 100)', 'ref_range': [0.7, 1.5], 'format_func': div100, 'value_list': [], 'minimum_scale': 0.01, 'dispaly_unit': None, 'custom': True,
    #  'cond': [{'cls': 'ML', 'count': 0, 'text': '较低', 'range': ['', '']},
    #           {'cls': 'MM', 'count': 0, 'text': '一般', 'range': ['', '']},
    #           {'cls': 'MH', 'count': 0, 'text': '较高', 'range': ['', '']},
    #           ]
    #  },
    {'id': 'match_scope', 'name': '匹配方式', 'auditions': compile('True', '', 'eval'), 'value': compile('kw.match_scope', '', 'eval'),
     'ref_value': '1', 'ref_range': [2, ], 'format_func': None, 'value_list': [], 'minimum_scale': 1, 'dispaly_unit': None, 'custom': False,
     'cond': [{'cls': 'SL', 'count': 0, 'text': '精准匹配', 'range': ['', '']},
              {'cls': 'SM', 'count': 0, 'text': '广泛匹配', 'range': ['', '']},
              ]
     },
    {'id': 'mnt_opt_type', 'name': '托管类型', 'auditions': compile('True', '', 'eval'), 'value': compile('kw.mnt_opt_type', '', 'eval'),
     'ref_value': '1', 'ref_range': [1, 2], 'format_func': None, 'value_list': [], 'minimum_scale': 0.01, 'dispaly_unit': None, 'custom': False,
     'cond': [{'cls': 'OL', 'count': 0, 'text': '自动优化', 'range': ['', '']},
              {'cls': 'OM', 'count': 0, 'text': '只改价', 'range': ['', '']},
              {'cls': 'OH', 'count': 0, 'text': '不托管', 'range': ['', '']},
              ]
     },
    {'id': 'max_price', 'name': 'PC出价', 'auditions': compile('True', '', 'eval'), 'value': compile('kw.max_price', '', 'eval'),
     'ref_value': 'max(self.adg.rpt1.cpc, 50)', 'ref_range': [0.7, 1.2], 'format_func': div100, 'value_list': [], 'minimum_scale': 0.01, 'dispaly_unit': '元', 'custom': True,
     'cond': [{'cls': 'ML', 'count': 0, 'text': '较低', 'range': ['', '']},
              {'cls': 'MM', 'count': 0, 'text': '一般', 'range': ['', '']},
              {'cls': 'MH', 'count': 0, 'text': '较高', 'range': ['', '']},
              ]
     },
    {'id': 'max_mobile_price', 'name': '移动出价', 'auditions': compile('True', '', 'eval'), 'value': compile('kw.max_price_mobile', '', 'eval'),
     'ref_value': 'max(self.adg.rpt1.cpc, 50)', 'ref_range': [0.7, 1.2], 'format_func': div100, 'value_list': [], 'minimum_scale': 0.01, 'dispaly_unit': '元', 'custom': True,
     'cond': [{'cls': 'YL', 'count': 0, 'text': '较低', 'range': ['', '']},
              {'cls': 'YM', 'count': 0, 'text': '一般', 'range': ['', '']},
              {'cls': 'YH', 'count': 0, 'text': '较高', 'range': ['', '']},
              ]
     },
    {'id': 'qscore', 'name': 'PC质量分', 'auditions': compile('kw.qscore_dict["qscore"]>0', '', 'eval'), 'value': compile('kw.qscore_dict["qscore"]', '', 'eval'),
     'ref_value': '1', 'ref_range': [5, 8], 'format_func': int, 'value_list': [], 'minimum_scale': 1, 'dispaly_unit': None, 'custom': True,
     'cond': [{'cls': 'QL', 'count': 0, 'text': '低', 'range': ['', '']},
              {'cls': 'QM', 'count': 0, 'text': '中', 'range': ['', '']},
              {'cls': 'QH', 'count': 0, 'text': '高', 'range': ['', '']},
              ]
     },
    {'id': 'wireless_qscore', 'name': '移动质量分', 'auditions': compile('kw.qscore_dict["wireless_qscore"]>0', '', 'eval'), 'value': compile('kw.qscore_dict["wireless_qscore"]', '', 'eval'),
     'ref_value': '1', 'ref_range': [5, 8], 'format_func': int, 'value_list': [], 'minimum_scale': 1, 'dispaly_unit': None, 'custom': True,
     'cond': [{'cls': 'WL', 'count': 0, 'text': '低', 'range': ['', '']},
              {'cls': 'WM', 'count': 0, 'text': '中', 'range': ['', '']},
              {'cls': 'WH', 'count': 0, 'text': '高', 'range': ['', '']},
              ]
     },
    {'id': 'click', 'name': '点击量', 'auditions': compile('kw.rpt.click', '', 'eval'), 'value': compile('kw.rpt.click', '', 'eval'),
     'ref_value': 'max(self.kw_avg_click, 5)', 'ref_range': [0.7, 1.5], 'format_func': int, 'value_list': [], 'minimum_scale': 1, 'dispaly_unit': None, 'custom': True,
     'cond': [{'cls': 'KL', 'count': 0, 'text': '低', 'range': ['', '']},
              {'cls': 'KM', 'count': 0, 'text': '中', 'range': ['', '']},
              {'cls': 'KH', 'count': 0, 'text': '高', 'range': ['', '']},
              ]
     },
    {'id': 'ctr', 'name': '点击率', 'auditions': compile('kw.rpt.click', '', 'eval'), 'value': compile('kw.rpt.ctr', '', 'eval'),
     'ref_value': 'self.adg.rpt1.ctr', 'ref_range': [0.7, 1.2], 'format_func': round2, 'value_list': [], 'minimum_scale': 0.01, 'dispaly_unit': '%', 'custom': True,
     'cond': [{'cls': 'TL', 'count': 0, 'text': '低', 'range': ['', '']},
              {'cls': 'TM', 'count': 0, 'text': '一般', 'range': ['', '']},
              {'cls': 'TH', 'count': 0, 'text': '高', 'range': ['', '']},
              ]
     },
    {'id': 'cpc', 'name': '平均花费', 'auditions': compile('kw.rpt.cpc', '', 'eval'), 'value': compile('kw.rpt.cpc', '', 'eval'),
     'ref_value': 'self.adg.rpt1.cpc', 'ref_range': [0.7, 1.3], 'format_func': div100, 'value_list': [], 'minimum_scale': 0.01, 'dispaly_unit': None, 'custom': True,
     'cond': [{'cls': 'CL', 'count': 0, 'text': '较低', 'range': ['', '']},
              {'cls': 'CM', 'count': 0, 'text': '适中', 'range': ['', '']},
              {'cls': 'CH', 'count': 0, 'text': '偏高', 'range': ['', '']},
              ]
     },
    {'id': 'roi', 'name': '投资回报', 'auditions': compile('kw.rpt.cost', '', 'eval'), 'value': compile('kw.rpt.roi', '', 'eval'),
     'ref_value': '1', 'ref_range': [1.0, 1.5], 'format_func': round2, 'value_list': [], 'minimum_scale': 0.01, 'dispaly_unit': None, 'custom': True,
     'cond': [{'cls': 'RL', 'count': 0, 'text': '亏本', 'range': ['', '']},
              {'cls': 'RM', 'count': 0, 'text': '持平', 'range': ['', '']},
              {'cls': 'RH', 'count': 0, 'text': '盈利', 'range': ['', '']},
              ]
     },
]


class KeywordClassifier(object):
    """docstring for KeywordClassifier"""
    def __init__(self, adg, kw_list, start_date, end_date, platform):
        super(KeywordClassifier, self).__init__()
        self.adg = adg
        self.kw_list = kw_list
        self.start_date = start_date
        self.end_date = end_date
        self.platform = platform
        self.bulk_search_list = BULK_SEARCH_LIST
        self.bulk_tree_list = BULK_TREE_LIST
        self.adg.bulk_search_list = []

    def init_report(self):
        # self.adg.rpt = self.adg.get_summed_rpt(start_date = self.start_date, end_date = self.end_date)
        if self.start_date == self.end_date == datetime.date.today().strftime('%Y-%m-%d'):
            kw_rpt_dict = RealtimeReport.get_platformsum_rtrpt('keyword', args_list = [self.adg.shop_id, self.adg.campaign_id, self.adg.adgroup_id], platform = self.platform)
        else:
            query_dict = {'shop_id': self.adg.shop_id, 'campaign_id': self.adg.campaign_id, 'adgroup_id': self.adg.adgroup_id}
            kw_rpt_dict = Keyword.Report.get_platform_summed_rpt(query_dict, start_date = self.start_date, end_date = self.end_date, platform = self.platform)
        for kw in self.kw_list:
            kw.rpt = kw_rpt_dict.get(kw.keyword_id, Keyword.Report())

    @property
    def kw_avg_click(self):
        '''只计算点击量之和大于5的关键词的平均点击量'''
        if not hasattr(self, '_kw_avg_click'):
            self._kw_avg_click = 0.0
            click_sum, kw_count = 0, 0
            for kw in self.kw_list:
                if kw.rpt.click < 5:
                    continue
                kw_count += 1
                click_sum += kw.rpt.click
            if kw_count:
                self._kw_avg_click = float(click_sum) / kw_count
        return self._kw_avg_click

    def classify_keyword(self):
        '''关键词分类'''
        self.init_report()
        for kw in self.kw_list:
            if kw.new_price_pc and kw.new_price_pc < kw.max_price_pc:
                kw.optm_type_pc = 2
            elif kw.new_price_pc and kw.new_price_pc > kw.max_price_pc:
                kw.optm_type_pc = 3
            else:
                kw.optm_type_pc = 0

            if kw.new_price_mobile and kw.new_price_mobile < kw.max_price_mobile:
                kw.optm_type_mobile = 2
            elif kw.new_price_mobile and kw.new_price_mobile > kw.max_price_mobile:
                kw.optm_type_mobile = 3
            else:
                kw.optm_type_mobile = 0

            if kw.is_delete is True:
                kw.optm_type = 1
            elif kw.optm_type_pc or kw.optm_type_mobile:
                kw.optm_type = 2
            else:
                kw.optm_type = 0

            if not kw.new_price:
                kw.new_price = kw.max_price

            kw.tree_code = ''
            kw.word_type = ''

            for cfg in self.bulk_tree_list:
                if eval(cfg['factor']):
                    kw.tree_code += cfg['id']
                    break

    def create_search_list(self):
        '''生成批量优化页面中用到的快速搜索条件'''

        self.adg.bind_qscore(self.kw_list) # 算法中用的是旧算法，批量优化中用的是新算法。
        self.classify_keyword()

        # 克隆全局对象，因为会修改对象的属性
        search_list_copy = copy.deepcopy(self.bulk_search_list)
        for kw in self.kw_list:
            kw.label_code = ""
            # 将关键词归属到对应的过滤维度(计算每个维度上满足条件的关键词个数，并给关键词打标记)
            for cfg in search_list_copy:
                if not eval(cfg['auditions']):
                    continue
                cur_value = eval(cfg['value'])
                ref_value = eval(cfg['ref_value'])
                cur_index = len(cfg['ref_range'])
                for index, ref_range in enumerate(cfg['ref_range']):
                    if cur_value < ref_value * ref_range:
                        cur_index = index
                        break
                kw.label_code += cfg['cond'][cur_index]['cls'] + ' '
                cfg['cond'][cur_index]['count'] += 1
                new_cur_value = cfg['format_func'] and cfg['format_func'](cur_value) or cur_value
                cfg['value_list'].append(new_cur_value)

            kw.label_code = kw.label_code.rstrip()

        # 计算过滤维度的range属性值，如果某维度上的count为0，则删除该维度的配置，使得页面上不显示
        del_key_list = ['auditions', 'value', 'value_list', 'ref_value', 'ref_range', 'format_func']
        for cfg in search_list_copy:
            if cfg['value_list']:
                ref_value = eval(cfg['ref_value'])
                if cfg['format_func']:
                    range_list = [cfg['format_func'](ref_value * rr) for rr in cfg['ref_range']]
                    range_list.insert(0, min(cfg['value_list']))
                    range_list.append(max(cfg['value_list']) + cfg['minimum_scale']) # 因为下面会将 上限值 减去 最小刻度，所以这里要加上。
                for i in range(len(cfg['cond']))[::-1]:
                    if cfg['cond'][i]['count'] == 0:
                        del cfg['cond'][i]
                        continue
                    if cfg['format_func']:
                        temp_range = range_list[i: i + 2]
                        temp_range[1] -= cfg['minimum_scale']
                        if cfg['format_func'] in [round2, div100]:
                            temp_range = [format(j, '.2f') for j in temp_range]
                        if cfg['dispaly_unit']:
                            temp_range = [str(j) + cfg['dispaly_unit'] for j in temp_range]
                        cfg['cond'][i]['range'] = temp_range
                cfg['cond'].reverse() # 页面显示时，倒置顺序，将好的数据显示在前面
                count_list = [i['count'] for i in cfg['cond']]
                if sum(count_list) in count_list:
                    cfg['cond'] = []
            else:
                cfg['cond'] = []
            for k in del_key_list:
                del cfg[k]

        self.adg.bulk_search_list = search_list_copy
        return True
