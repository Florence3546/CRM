# coding=UTF-8
import random
from apilib.parsers import TopObject
from apps.common.utils.utils_string import get_ordered_str
from apps.common.utils.utils_log import log
from apps.common.utils.utils_collection import genr_sublist
from apilib import tsapi
from apilib.error import TopError


def is_string_char_digit(str_source):
    '''
    判定字符串是否是数字以及字母
    '''
    for uchar in str_source:
        if ord(uchar) <= 127:
            continue
        else:
            return False
    return True

def rm_not_relate_keyword(word_list, prdt_list):
    '''
    /清除爬词带来不相关的词
    '''
    result_list = []
    if not prdt_list:
        return word_list
    for word in word_list:
        for prdt in prdt_list:
            if prdt in word:
                result_list.append(word)
                break
    return result_list

def is_include_word(word, word_list):
    word = word.replace(' ', '')
    for wd in word_list:
        if not wd:
            continue
        # if Const.ALL_SIGN_DICT['all'].has_key(wd):
        #     continue
        if wd in word:
            return True
    return False

def remove_same_words_byword(keyword_list):
    dic = {}
    result_list = []
    # 修改关键词的排序，按照指定的排序方式，这样保证能够去掉所有的重复词
    for kw in keyword_list:
        key = get_ordered_str(kw[0])
        if not dic.has_key(key):
            dic[key] = 1
            result_list.append(kw)

    return result_list

def sort_by_pvclick(x, y):
    if x[1] > y[1]:
        return -1
    elif x[1] < y[1]:
        return 1
    elif x[2] > y[2]:
        return -1
    elif x[2] < y[2]:
        return 1
    else:
        return 0

def campair_x_y_by_attr(x, y, attr):
    if hasattr(x, 'label') and hasattr(y, 'label'):
        if 'P' in x.label and not 'P' in y.label:
            return 1
        elif not 'P' in x.label and 'P' in y.label:
            return -1
        else:
            return getattr(x, attr) > getattr(y, attr)
    elif hasattr(x, 'label'):
        return 1
    elif hasattr(y, 'label'):
        return -1
    else:
        return getattr(x, attr) > getattr(y, attr)

def sort_by_label_click(x, y):
    return campair_x_y_by_attr(x, y, 'cat_click')

def sort_by_label_roi(x, y):
    return campair_x_y_by_attr(x, y, 'roi')

def sort_by_label_favtotal(x, y):
    return campair_x_y_by_attr(x, y, 'favtotal')


def sort_by_label_coverage(x, y):
    return campair_x_y_by_attr(x, y, 'coverage')

def sort_kwlist_by_click(x, y):
    return sort_by_pvclick(x, y)

def sort_kwlist_by_pv(x, y):
    return sort_by_pvclick(x, y)

def sort_by_pvclick_reverse(x, y):
    return -sort_by_pvclick(x, y)

def sort_by_scorepv(x, y):
    '''
    根据内部配置的权重排序，最后一个元素是匹配度
    '''
    x_score = int(x[-1] / 100)
    y_score = int(y[-1] / 100)
    if x_score < y_score:
        return 1
    elif x_score > y_score:
        return -1
    elif x[1] > y[1]:
        return -1
    return 0

def sort_kwlist_by_score(x, y):
    '''
    根据内部配置的权重排序，最后一个元素是匹配度
    '''
    x_score = int(x[7] / 100)
    y_score = int(y[7] / 100)
    if x_score < y_score:
        return 1
    elif x_score > y_score:
        return -1
    elif x[7] > y[7]:
        return -1
    return 0

def sort_kwlist_by_random(x, y):
    '''
    随机排序
    '''
    random_i = random.randint(-1, 1)
    return random_i

def sort_by_random(kw_list):
    '''
    对关键词进行随机排序
    '''
    random.shuffle(kw_list)
    return kw_list


def remove_same_words(keyword_list):
    # 先对关键词进行排序
    keyword_list.sort(sort_by_pvclick)

    # 将相同的cat_pv、cat_cpc的词删除掉
    result_list = []

    ii = 0
    jj = 0
    lenth = len(keyword_list)
    if lenth == 0:
        return result_list
    # 选择关键词的时候，优先选择空格多的，空格多的，已经被淘宝做了分词处理，这样选词做分词
    # 的时候，可以更准确的切割分词，计算相关度会更准确
    max_part_kw = keyword_list[0]
    for ii in range(lenth):
        jj = ii + 1
        cur_kw = keyword_list[ii]
        if jj < lenth:
            nxt_kw = keyword_list[jj]
            # 如果后一个词和当前的词相同
            if (cur_kw[1] == None or cur_kw[1] == 0) or (cur_kw[1] == nxt_kw[1] \
                                                 and cur_kw[2] == nxt_kw[2]\
                                                 and cur_kw[4] == nxt_kw[4]):
                # 保留分词个数多的关键词
                if nxt_kw[0].count(' ') > max_part_kw[0].count(' '): # 要大于等于，因为繁体的一般排在简写的前面，以简体为准
                    max_part_kw = nxt_kw

                ii += 1
                continue
            else:
                result_list.append(max_part_kw)
                max_part_kw = nxt_kw
        else:
            result_list.append(max_part_kw)

        ii += 1

    return result_list

def group_kwlist(kw_list, item_scorer, cat_id, cat_cpc, cats, remove_word_list, filter_conf, filter_list, price_list):
    group_dict = {}
    # 类目变量标准化
    c1, c2, c3, c4, c5, index = 0, 0, 0, 0, 0, 0
    for c_id in cats:
        if index == 0:
            c1 = int(c_id)
            index += 1
            continue
        elif index == 1:
            c2 = int(c_id)
            index += 1
            continue
        elif index == 2:
            c3 = int(c_id)
            index += 1
            continue
        elif index == 3:
            c4 = int(c_id)
            index += 1
            continue
        else:
            c5 = int(c_id)
    # 把条件表达式以及运算表达式编译好
    code_filter_conf = compile(filter_conf, '', 'eval')
    code_flter_list = []
    for filter in filter_list: # 初始化
        try:
            group_dict[filter] = []
            # 做类目预处理cat_id in (c1) and score=1000 and "P" in label，这种，如果类目对不上
            # 这条就不应该加入比较，只支持全and方式
            is_right = True
            if ('not' not in filter) and (' or ' not in filter) and ('cat_id' in filter): #
                test_list = filter.split('and')
                for tl in test_list:
                    if 'cat_id' in tl:
                        if not eval(tl):
                            is_right = False
                            break
            if is_right:
                code_flter_list.append(((compile(filter, '', 'eval')), filter))
        except Exception, e:
            log.error('select word filter error: filter=%s, e=%s' % (filter, e))
    if not code_flter_list:
        return group_dict
    code_price_list = []
    for p_conf in price_list:
        code_price_list.append({'candi_filter':compile(p_conf['candi_filter'], '', 'eval'), 'init_price':compile(p_conf['init_price'], '', 'eval')})

    # log.info('start group now ....')
    for kw in kw_list:
        word = kw[0]
        is_need_remove = False
        for wd in remove_word_list:
            if wd in word:
                is_need_remove = True
                break
        if is_need_remove:
            continue
        score, label = item_scorer.score_participles_by_item(word) # 132000 2s
        pv, click, cpc, competition, ctr = kw[1], kw[2], kw[3], kw[4], kw[5]
        # 根据配置判断是否满足海选条件
        if not eval(code_filter_conf):
            continue
        # 精选关键词
        default_kw_price = max(cpc * 0.8, 10) + random.randint(-5, 15)
        for filter in code_flter_list:
            if eval(filter[0]):
                new_price = default_kw_price
                for price_conf in code_price_list:
                    if eval(price_conf['candi_filter']):
                        new_price = eval(price_conf['init_price'])
                        break
                new_price = new_price or default_kw_price
                group_dict[filter[1]].append([word, pv, click, cpc, competition, ctr, cat_id, score, new_price, label])
                break
    # 去掉没有符合条件的k，v
    for k, v in group_dict.items():
        if not v:
            group_dict.pop(k)
    # log.info('group finish,len=%s' % len(kw_list))

    return group_dict

def get_word_num(is_mnt, good_count, cur_count = 0):
    # 通过分析已有词、
    default_count = 200
    if is_mnt:
        need_bad_count = default_count - cur_count - good_count

        if need_bad_count < 5:
            return good_count

        result_count = good_count + int(need_bad_count * need_bad_count / default_count * 0.10)
        return result_count
    else:
        default_count = 600
        need_bad_count = default_count - good_count
        if need_bad_count < 0:
            return good_count + 60
        return good_count + int(need_bad_count * 1.2)

def transform_tuple_2tobj(kw_list):
    temp_list = []
    # word, pv, click, cpc, competition, ctr, cat_id, score, new_price, label, filter_index
    for kw in kw_list:
        new_obj = TopObject()
        new_obj.word = kw[0]
        new_obj.cat_pv = kw[1]
        new_obj.cat_click = kw[2]
        new_obj.cat_cpc = kw[3]
        new_obj.cat_competition = kw[4]
        new_obj.cat_ctr = kw[5]
        new_obj.cat_id = kw[6]
        new_obj.keyword_score = kw[7]
        new_obj.new_price = kw[8] or 0.3
        new_obj.label = kw[9]
        new_obj.roi = kw[10]
        new_obj.coverage = kw[11] * 100.0
        new_obj.favtotal = kw[12]
        new_obj.filter_index = kw[13]
        temp_list.append(new_obj)
    return temp_list

def del_include_product_word(cat_name_list, word_set):
    # 「地板>地板附件」类目下，默认不要将父类目的固定产品词「地板」作为子类目产品词
    include_list = [u'零/配件', u'零配件', u'零配件', u'配件', u'附件', u'零件']
    remove_set = set()
    for cat_name in cat_name_list:
        for word in include_list:
            if word in cat_name:
                temp_str = cat_name
                temp_list = temp_str.replace(word, '').split('/')
                remove_set.update([i for i in temp_list if i])
    result_set = set(word_set) - remove_set
    return result_set

def get_match_word(rule_list, words_list):
    result_list = []
    for conf in rule_list:
        conf = conf.replace(' ', '')
        if '*' not in conf:
            if conf in words_list:
                result_list.append(conf)
        elif conf.find('*') == 0: # 如：*裙
            sub_string = conf.replace('*', '')
            sub_len = len(sub_string)
            temp_list = [wd for wd in words_list if len(wd) >= sub_len and str(wd[0 - sub_len:]) == str(sub_string)]
            result_list.extend(temp_list)
        else: # 如:牛仔*
            sub_string = conf.replace('*', '')
            sub_len = len(sub_string)
            temp_list = [wd for wd in words_list if len(wd) > sub_len and str(wd[:0 + sub_len]) == str(sub_string)]
            result_list.extend(temp_list)
    return list(set(result_list))

def get_match_attribut(rule_list, words_list):
    result_list = []
    for conf in rule_list:
        if '*' not in conf:
            if conf in words_list:
                result_list.append(conf)
        if conf.find('*') == 0: # 如：*裙
            sub_string = conf.replace('*', '')
            sub_len = len(sub_string)
            for wd in words_list:
                if len(wd) > len(sub_string) and str(wd[0 - sub_len:]) == str(sub_string): # 匹配上
                    if len(wd) - sub_len > 1: # 「短袖」-> 短/袖， 「长裙」-> 长/裙, 修饰词长度为1时不添加
                        result_list.append(wd[0:len(wd) - sub_len])
                    result_list.append(sub_string)
    return list(set(result_list))

def get_rule_list(rule):
    rule_list, word_list = [], []
    if not rule:
        return rule_list, word_list
    try:
        spit_rule_list = rule.split(';')
        if not spit_rule_list:
            return rule_list, word_list
        elif len(spit_rule_list) == 1:
            word_list.extend(spit_rule_list[0].split(','))
        else:
            rule_list = spit_rule_list[0].split(',')
            if spit_rule_list[1]:
                word_list.extend(spit_rule_list[1].split(','))
    except Exception, e:
        log.info('can not get word by rule and the error is = %s ' % e)
    rule_list = [word for word in rule_list if word]
    word_list = [word for word in word_list if word]
    return rule_list, word_list

# 几个特殊类目的标签解析函数#
# <1岁    <80    新生儿    婴儿    宝宝    婴童
# 1-4岁    80-110    小童    宝宝    小宝    幼儿
# 4-8岁    110-130    中童    儿童    宝宝
# >8岁    >130    大童    儿童
# [u'120cm', u'110cm', u'140cm', u'100cm', u'130cm', u'90cm']
def get_age_from_height(source_list):
    # 从source中获取身高
    result_list = []
    title = ''
    for sl in source_list:
        sl = sl.replace('cm', '')
        if not is_string_char_digit(sl): # 标题\
            title += sl
            temp_list = get_age_from_title(title)
            result_list.extend(temp_list)
            continue
        try:
            height = int(sl)
        except:
            continue
        if height == 100: # 为什么要去掉100呢?这里涉及到一个体系的问题，因为100%这种词，被解析成了100，万一真的是100，怎么办，一般有95。
            continue
        if height <= 80:
            result_list.append(u'婴儿')
        elif height < 110:
            result_list.append(u'小童')
        elif height < 130:
            result_list.append(u'中童')
        elif height > 130: # 不要随便动
            result_list.append(u'大童')
    result_list = list(set(result_list))
    # 对词进行核对检查，对所有小孩子的词：,
    # u'宝宝', u'小宝', u'幼儿',新生儿', u'婴儿', u'婴童', u'婴幼儿',u'女婴',u'男婴,男宝，女宝
    # '小童', u'小宝', u'幼儿', u'小中童', u'中小童', u'小男童',u'小女童',u'小中大童', u'小儿', u'小儿童'
    # u'中童', u'中大童', u'大中童', u'小中童', u'中小童', u'中儿童', u'中女童', u'中男童' u'女中童', u'男中童'
    # '大童', u'大儿童', u'大孩子', u'大女童', u'大男童' u'女大童', u'男大童'
    # 儿童,男童，女童,男孩，女孩，男娃，女娃
    desc_list = []
    desc_list.extend(result_list)
    # 解析出来的标准说法是：婴儿、小童、中童、大童，结合标题，依次检查上述说法是否准确
    if u'婴儿' in result_list or u'小童' in result_list:
        desc_list.extend([u'宝宝', u'小宝'])
    if u'婴儿' in result_list:
        desc_list.extend([u'幼儿', u'新生儿', u'婴童', u'婴幼儿'])
    if u'婴儿' in result_list and u'男' in title:
        desc_list.extend([u'男婴'])
    if u'婴儿' in result_list and u'女' in title:
        desc_list.extend([u'女婴'])
    if u'婴儿' in result_list or u'小童' in result_list or u'中童' in result_list:
        desc_list.extend([u'宝宝'])
    if u'宝宝' in desc_list and u'男' in title:
        desc_list.extend([u'男宝', u'男宝宝', u'男娃'])
    if u'宝宝' in desc_list and u'女' in title:
        desc_list.extend([u'女宝', u'女宝宝', u'女娃'])
    if u'小童' in result_list:
        desc_list.extend([u'小宝', u'幼儿', u'小儿', u'小儿童'])
    if u'小童' in result_list and u'中童' in result_list:
        desc_list.extend([u'小中童', u'中小童', u'幼儿'])
    if u'小童' in result_list and u'男' in title:
        desc_list.extend([u'小男童', u'男小童'])
    if u'小童' in result_list and u'女' in title:
        desc_list.extend([u'小女童', u'女小童'])
    if u'中童' in result_list and u'大童' in result_list:
        desc_list.extend([u'中大童', u'大中童', u'儿童'])
    if u'中童' in result_list and u'小童' in result_list:
        desc_list.extend([u'中小童', u'小中童', u'儿童'])
    if u'中童' in result_list:
        desc_list.extend([u'中儿童'])
    if u'中童' in result_list and u'男' in title:
        desc_list.extend([u'中男童', u'男中童'])
    if u'中童' in result_list and u'女' in title:
        desc_list.extend([u'中女童', u'女中童'])
    if u'大童' in result_list :
        desc_list.extend([u'大儿童', u'大孩子'])
    if u'大童' in result_list and u'男' in title:
        desc_list.extend([u'大男童', u'男大童'])
    if u'大童' in result_list and u'女' in title:
        desc_list.extend([u'大女童', u'女大童'])
    if u'中童' in result_list or u'大童' in result_list:
        desc_list.extend([u'儿童'])
    if u'儿童' in desc_list and u'男' in title:
        desc_list.extend([u'男童', u'男孩', u'男娃'])
    if u'儿童' in desc_list and u'女' in title:
        desc_list.extend([u'女童', u'女孩', u'女娃'])
    return desc_list

# 传入的是标题描述，这样判断更准确
def get_age_from_title(source_list):
    result_list = []
    word_list = [u'新生儿', u'婴儿', u'婴童', u'婴幼儿', u'女婴', u'男婴']
    for wd in word_list:
        if wd in source_list:
            result_list.extend([u'婴儿'])

    word_list = [u'小童', u'小宝', u'幼儿', u'小中童', u'中小童', u'小小童', u'小中大童', u'小儿', u'小儿童', u'小男童', u'小女童']
    for wd in word_list:
        if wd in source_list:
            result_list.extend([u'小童'])

    word_list = [u'中童', u'中大童', u'大中童', u'小中童', u'中小童', u'中儿童', u'中女童', u'中男童']
    for wd in word_list:
        if wd in source_list:
            result_list.extend([u'中童'])

    word_list = [u'大童', u'中大童', u'大中童', u'大儿童', u'大孩子', u'大女童', u'大男童']
    for wd in word_list:
        if wd in source_list:
            result_list.extend([u'大童'])

    return result_list

def get_catinfo_new(select_type, category_id_list = []): # TODO 该返回值信息量很大，所以是否要保留类目树需要待定，或者修改类目树的基本结构，所以该操作暂时待定
    """
    新的获取类目信息接口，获取类目信息，此接口既提供所有顶级类目的查询，
    又提供给定类目id自身信息和子类目信息的查询，所以可以根据此接口逐层获取所有的类目信息
    传入参数：
    type: 0 表示请求所有顶级类目的信息，这时可以忽略第二个参数
          1 表示获取给定的类目id的详细信息
          2 表示获取给定类目id的所有子类目的详细信息
    category_id_list:以逗号隔开的类目id "16,30"
    返回值：
    parent_cat_id：父类目id
    cat_name:类目名称
    cat_path_name：类目路径名称
    cat_id：类目id
    cat_level:类目层级
    last_sync_time：最后一次同步时间
    cat_path_id：类目路径id
    """
    def get_cat_data_info(tobj, cat_dict):
        if tobj and hasattr(tobj, "category_info_list"):
            category_info_list = tobj.category_info_list
            if hasattr(category_info_list, "insight_category_info_d_t_o"):
                insight_category_info_d_t_o = category_info_list.insight_category_info_d_t_o
                for cat in insight_category_info_d_t_o:
                    cat_id = cat.cat_id
                    cat_dict[cat_id] = {'cat_id':cat_id, 'cat_path_name':cat.cat_path_name, 'parent_cat_id':cat.parent_cat_id, 'cat_name':cat.cat_name, 'cat_level':cat.cat_level, 'last_sync_time':cat.last_sync_time, 'cat_path_id':cat.cat_path_id}
        return cat_dict

    tobj = None
    cat_dict = {}
    try:
        if category_id_list:
            for tmp_list in genr_sublist(category_id_list, 10):
                tobj = tsapi.simba_insight_catsinfo_get(type = select_type, category_id_list = ','.join(tmp_list))
                cat_dict = get_cat_data_info(tobj, cat_dict)
        else:
            tobj = tsapi.simba_insight_catsinfo_get(type = select_type)
        cat_dict = get_cat_data_info(tobj, cat_dict)
    except TopError, e:
        log.error('get simba_insight_catsinfo_get error, e=%s' % (e))
        return {}
    return cat_dict

def cat_data_list(cat_id_list, start_date, end_date): # TODO 需要测试起始时间和终止时间的最长时间和最短时间
    """
    根据类目id获取类目的大盘数据，其中cpc, ctr, cvr, roi这几个指标数据是真实数据，其它的数据都是通过指数化后的数据，
    其中competition这个字段的目前无法做到精确统计，只是一个参考值，本次提供的insight相关的其它接口的都是这种情况。
    cat_id_list格式为:"16,30"以逗号分割
    start_data格式为：yyyy-MM-dd 起始时间
    end_data格式为：yyyy-MM-dd 终止时间
    返回值：
    impression：展现量
    click：点击量
    cost：花费，单位（分）
    directtransaction：直接成交额
    indirecttransaction：间接成交额
    directtransactionshipping：直接成交笔数
    indirecttransactionshipping：间接成交笔数
    favitemtotal：宝贝收藏数
    favshoptotal：店铺收藏数
    transactionshippingtotal：总的成交笔数
    transactiontotal：成交总金额
    favtotal：总的收藏数，包括宝贝收藏和店铺收藏
    competition：竞争度
    ctr：点击率
    cpc：平均点击花费
    roi：投入产出比
    coverage：点击转化率
    cat_id：类目id
    cat_name：类目名称
    """

    cat_id_list = [str(cat_id) for cat_id in cat_id_list]
    top_cat_data_dict = {}
    for cat_list in genr_sublist(cat_id_list, 5):
        try:
            tobj = tsapi.simba_insight_catsdata_get(category_id_list = ','.join(cat_list), start_date = start_date, end_date = end_date)
            if hasattr(tobj, "cat_data_list"):
                cat_data_list = tobj.cat_data_list
                if hasattr(cat_data_list, "insight_category_data_d_t_o"):
                    insight_category_data_d_t_o = cat_data_list.insight_category_data_d_t_o
                    for cat_data in insight_category_data_d_t_o:
                        top_cat_data_dict[cat_data.cat_id] = cat_data
        except TopError, e:
            log.error('get simba_insight_catsdata_get error, e=%s' % (e))
            continue
    return top_cat_data_dict

def get_cat_property(cat_id, shop_type):
    result = tsapi.itemprops_get(cid = cat_id, type = shop_type)
    return result
