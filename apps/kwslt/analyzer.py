# coding=UTF-8
from mongoengine.document import Document
from mongoengine.fields import StringField, BooleanField, ListField, IntField
import math
import re
from apps.common.constant import Const
from itertools import combinations, permutations
from apps.common.cachekey import CacheKey
import datetime
from apps.kwslt.base import is_string_char_digit
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import get_time_delta
from apps.common.biz_utils.utils_sorter import sort_list_bystring
from apps.common.utils.utils_string import get_char_num


class ChSegement(Document):
    word = StringField(verbose_name = "原子词", max_length = 10, required = True, unique = True)
    count = IntField(verbose_name = "词频")

    meta = {"collection":"kwlib_analyzer", "db_alias": "kwlib-db"}

    word_dict = {}
    WORD_MAX_LENGTH = 6
    VERIFY_CANDIT_LENGTH = 3

    mem_modifi_time = None

    @classmethod
    def update_memcache(cls):
        CacheAdpter.set(CacheKey.KWLIB_ELEMWORD_MODIFI_TIME, datetime.datetime.now(), 'web', 60 * 60 * 24 * 7)
        log.info('update elemword modifi time')

    @classmethod
    def load_to_mem(cls, is_need_refresh = False):
        now_time = datetime.datetime.now()
        if not is_need_refresh: # 不是强制刷新时，判断是否需要刷新数据，每隔5分钟从缓存获取原子词更新时间
            if not cls.mem_modifi_time:
                is_need_refresh = True
            elif get_time_delta(cls.mem_modifi_time, now_time, 'SECONDS') > 60:
                cache_modifi_time = CacheAdpter.get(CacheKey.KWLIB_ELEMWORD_MODIFI_TIME, 'web', cls.mem_modifi_time)
                if cache_modifi_time > cls.mem_modifi_time:
                    is_need_refresh = True
                else:
                    cls.mem_modifi_time = datetime.datetime.now()

        if is_need_refresh:
            for word in word_coll.find():
                cls.word_dict[word['word']] = word['count']
            cls.mem_modifi_time = datetime.datetime.now()
            log.info('init all elemword into mem')

    # 根据原子词分解标题
    @classmethod
    def split_title_new_to_list(cls, title):
        title = title.lower()
        finished_list = cls.chsgm_words(title)
        finished_list = sort_list_bystring(finished_list, title)
        return finished_list

    # 根据传入的描述信息，获取修饰词。从原子词中和word_list对比，完全匹配上，就属于修饰词。word_list中不包含产品词
    @classmethod
    def get_decorate_word_list(cls, word_list):
        cls.load_to_dict()

        result_list = []
        ele_list = cls.word_dict.keys()
        for wd in word_list:
            if '/' in wd:
                word_list.extend(wd.split('/'))
                continue
            if is_string_char_digit(wd):
                for ele in ele_list:
                    if ele == wd:
                        result_list.append(ele)
                        break
            else:
                for ele in ele_list:
                    if ele in wd:
                        result_list.append(ele)
                        break

        if result_list:
            return list(set(result_list))
        else:
            return list(set(word_list))

    # 根据传入的描述信息，获取修饰词。从原子词中和word_list对比，完全匹配上，就属于修饰词。word_list中不包含产品词
    @classmethod
    def get_element_word_dict(cls, cat_id, word_dict):
        result_dict = {}
        for key, wds in word_dict.items():
            if wds == '' or not wds:
                continue
            v_list = []
            for s_str in [u' ', u',', u'，', u'^']:
                wds = wds.replace(s_str, '/')
            word_list = wds.split('/')
            if u'品牌' in key:
                result_dict[key] = [word for word in word_list if word]
                continue
            for wd in word_list:
                if is_string_char_digit(wd):
                    temp_list = [wd]
                else:
                    temp_list = cls.chsgm_words(wd)
                v_list.extend(temp_list)
            # 重复调用缓存，影响速度，且后续会获取贬义词
            # v_list = WordFactory.get_extend_words(cat_id, v_list)
            result_dict[key] = v_list
        return result_dict

    @classmethod
    def generate_title(cls, title):
        '''
         产生新标题
        '''
        part_list = cls.split_title_new_to_list(title)
        return cls.make_newtitle_bywordlist(part_list)

    @classmethod
    def make_newtitle_bywordlist(cls, part_list):
        '''
        根据切割好的标题，组合成标题
        '''
        # 分三段，第一段大约2个关键词组成，中间一段一般3、5个关键词，最后一段按照关键词尽量往上补，长词特殊处理
        p1, p2, p3 = '', '', ''
        long_list = []
        p_ok = 1
        for part in part_list:
            if not part:
                continue
            if get_char_num(part) > 4:
                long_list.append(part)
                continue
            if p_ok == 1:
                if get_char_num(p2 + part) > 7:
                    p3 = p3 + ' ' + part
                    continue
                p1 += part
                if get_char_num(p1) > 4:
                    p_ok = 2
                    continue
            if p_ok == 2:
                if get_char_num(p2 + part) > 13:
                    p_ok = 3
                    p3 = p3 + ' ' + part
                    continue
                p2 += part
                if get_char_num(p2) > 7:
                    p_ok = 3
                    continue
            if p_ok == 3:
                p3 = p3 + ' ' + part

        result_str = ''
        result_str = result_str + p1 + ' '
        for part in long_list:
            result_str += part
        if p2:
            result_str = result_str + ' ' + p2
        if p3:
            result_str = result_str + p3

        return result_str

    @classmethod
    def generate_adg_title_list(cls, title):
        '''
        生成双标题
        '''
        part_list = cls.split_title_new_to_list(title)
        result_list = []
        if len(part_list) > 1:
            part_list2 = [part_list[1 - i] for i in range(len(part_list))]
        else:
            part_list2 = part_list[:]
        for temp_list in [part_list, part_list2]:
            adg_title = cls.make_newtitle_bywordlist(temp_list)
            result_list.append(adg_title)
        return result_list

    @classmethod
    def split_title_from_cat(cls, cat_item_dic):
        title_list = []
        try:
            for _, items in cat_item_dic.items():
                for item in items:
                    new_title = cls.generate_title(item[1])
                    title_list.append((item[0], new_title))
        except Exception, e:
            log.exception('error:%s' % (e))
        return title_list

    @classmethod
    def get_word_dict(cls):
        """
        .加载数据到内存
        """
        if not cls.word_dict:
            for word in word_coll.find():
                cls.word_dict[word['word']] = word['count']
        return cls.word_dict

    @classmethod
    def get_avg_len(cls, chunk):
        """
        .计算单个chunk的平均词长
        """
        avg_word_len = 0
        chunk_len = len(chunk)
        for ck in chunk:
            avg_word_len += float(len(ck)) / chunk_len
        return avg_word_len

    @classmethod
    def get_result_dict(cls, key, value, result_dict):
        if key in result_dict:
            result_dict[key].append(value)
        else:
            result_dict[key] = [value]
        return result_dict

    @classmethod
    def max_match_word(cls, chunk_list):
        """
        .最大词长匹配
        """
        result_dict = {}
        max_word_size = 0
        for chunk in chunk_list:
            chunk_len = len(''.join(chunk))
            result_dict = cls.get_result_dict(chunk_len, chunk, result_dict)
            max_word_size = max_word_size < chunk_len and chunk_len or max_word_size
        return result_dict[max_word_size]

    @classmethod
    def max_avg_word(cls, chunk_list):
        """
        .最大平均词长匹配
        """
        max_avg_word_size = 0
        result_dict = {}
        for chunk in chunk_list:
            avg_word_len = cls.get_avg_len(chunk)
            max_avg_word_size = avg_word_len > max_avg_word_size and avg_word_len or max_avg_word_size
            chunk_len_str = str(avg_word_len)
            result_dict = cls.get_result_dict(chunk_len_str, chunk, result_dict)
        return result_dict[str(max_avg_word_size)]

    @classmethod
    def min_variance_word(cls, chunk_list):
        """
        .最小方差匹配
        """
        min_variance = None
        result_dict = {}
        for chunk in chunk_list :
            avg_word_len = cls.get_avg_len(chunk)
            variance = 0
            for ck in chunk:
                tmp = len(ck) - avg_word_len
                variance += tmp * tmp
            if not min_variance and not (str(min_variance) == '0.0'):
                min_variance = variance
            else:
                if variance < min_variance:
                    min_variance = variance
            variance_str = str(variance)
            result_dict = cls.get_result_dict(variance_str, chunk, result_dict)
        return result_dict[str(min_variance)]

    @classmethod
    def max_word_count(cls, chunk_list):
        """
        .最大词频匹配
        """
        max_word_count = 0
        word_dict = cls.get_word_dict()
        result_dict = {}
        for chunk in chunk_list:
            word_count = 0
            for ck in chunk:
                word_count += int(float(word_dict.get(ck, 0)))
            max_word_count = word_count > max_word_count and word_count or max_word_count
            result_dict = cls.get_result_dict(word_count, chunk, result_dict)
        return result_dict[max_word_count]

    @classmethod
    def filter_chunks(cls, chunk_list):
        """
        .过滤,经过4种规则
        """
        result_chunk = cls.max_match_word(chunk_list)
        if len(result_chunk) >= 2:
            result_chunk = cls.max_avg_word(result_chunk)
            if len(result_chunk) >= 2:
                result_chunk = cls.min_variance_word(result_chunk)
                if len(result_chunk) >= 2:
                    result_chunk = cls.max_word_count(result_chunk)

        return result_chunk[0]

    @classmethod
    def get_next_match(cls, word_list, index):
        """
        .获取下一个节点的chunk
        """
        match_list = []
        next_index = 1
        word = word_list[index]
        word_dict = cls.get_word_dict()
        if word in word_dict:
            match_list.append(word)
        word_str = word
        while (next_index < cls.WORD_MAX_LENGTH and (next_index + index) < len(word_list)):
            word_str += word_list[index + next_index]
            if word_str in word_dict:
                match_list.append(word_str)
            next_index += 1
        return match_list

    @classmethod
    def get_best_chunk(cls, word_list, index):
        """
        .得到最优的chunk_list
        """
        match_list = cls.get_next_match(word_list, index)
        match_n_list, match_nn_list, chunk_list = [], [], []
        word_list_len = len(word_list)
        for x in range(len(match_list)):
            idx_n = index + len(match_list[x])
            if idx_n < word_list_len:
                match_n_list = cls.get_next_match(word_list, idx_n)
                if not match_n_list:
                    chunk_list.append([match_list[x]])
                for y in range(len(match_n_list)):
                    idx_nn = idx_n + len(match_n_list[y])
                    if idx_nn < word_list_len:
                        match_nn_list = cls.get_next_match(word_list, idx_nn)
                        if not match_nn_list:
                            chunk_list.append([match_list[x], match_n_list[y]])
                        for z in range(len(match_nn_list)):
                            chunk_list.append([match_list[x], match_n_list[y], match_nn_list[z]])
                    else:
                        chunk_list.append([match_list[x], match_n_list[y]])
            else:
                chunk_list.append([match_list[x]])
        if chunk_list:
            return cls.filter_chunks(chunk_list)
        else:
            return []

    @classmethod
    def type_of_words(cls, words):
        '''
        .判断字符串类型,如果包含中文则做拆分,否则不做拆分
        '''
        for i in words:
            if ord(i) > 127:
                return False
        return True

    @classmethod
    def split_by_cn_eng(cls, word):
        count = 0
        splt_wd, result = ' ~~~ ', ''
        for wd in word:
            if wd == ' ' and count not in [0, len(word) - 1]:
                if (ord(word[count - 1]) <= 127 and ord(word[count + 1]) > 127) or (ord(word[count - 1]) > 127 and ord(word[count + 1]) <= 127):
                    result += splt_wd
                else:
                    result += wd
            else:
                result += wd
            count += 1
        return [wd.strip() for wd in result.split(splt_wd)]

    @classmethod
    def replace_all_sign_from_eng(cls, word):
        temp_word = ''
        for wd in word:
            if 'a' <= wd <= 'z' or '0' <= wd <= '9':
                temp_word += wd
            else:
                temp_word += ' '


    @classmethod
    def replace_unavailable_wd(cls, words, sign_dict = 'unavailable_wd_dict'):
        tmp_words = ''
        for wd in words:
            if wd in Const.COMMON_ALL_SIGN_DICT[sign_dict]:
                tmp_words += ' '
                continue
            tmp_words += wd
        return tmp_words

    @classmethod
    def get_eng_verify(cls, verify_words, words):
        """
        .将 包含在一起没有意义的verify字符串或者有歧义的verify字符串拆开   如  1 wled , 128gu盘等
        """
        def cmp_verify_word(x, y):
            x = x[1]
            y = y[1]
            x_len = cls.get_word_len(x)
            y_len = cls.get_word_len(y)
            if x_len != y_len:
                return cmp(x_len, y_len)
            else:
                return cmp(cls.word_dict[x], cls.word_dict[y])

        def cmp_eng_num_word(x, y):
            x = x[1]
            y = y[1]
            x_len = len(x)
            y_len = len(y)
            if x_len != y_len:
                return cmp(x_len, y_len)
            else:
                return cmp(cls.word_dict[x], cls.word_dict[y])

        def get_key(result_dict, tmp_list, verify_words, is_eng_num = False):
            if len(result_dict) == 1:
                key = result_dict.keys()[0]
            else:
                if is_eng_num:
                    key = sorted(result_dict.items(), cmp = cmp_eng_num_word, reverse = True)[0][0]
                else:
                    key = sorted(result_dict.items(), cmp = cmp_verify_word, reverse = True)[0][0]
            other_key = [i for i in verify_words.split(key) if i]
            if other_key:
                for i in range(verify_words.count(key)): # @UnusedVariable
                    if key:
                        other_key.append(key)
                tmp_list.extend(other_key)
            else:
                tmp_list.append(key)
            return tmp_list

        result_dict, tmp_list = {}, []
        i = 0
        match = False
        index = words.index(verify_words)
        varify_len = len(verify_words)
        word = words[index + varify_len:index + varify_len + 4]
        word_len = len(word)
        tmp_word = ''
        word_type = cls.type_of_words(words)
        while i <= varify_len - 1 and word_len:
            j = 0
            while j <= word_len and word_len:
                if word_type:
                    tmp_word = verify_words[i:] + word[:j + 1]
                else:
                    tmp_word = verify_words[i:] + (word[:j + 1]).strip()
                if tmp_word in cls.word_dict:
                    result_dict[verify_words[i:]] = tmp_word
                j += 1
            i += 1
        if result_dict :
            match = True
            tmp_list = get_key(result_dict, tmp_list, verify_words)
        else:
            for i in range(1, varify_len + 1):
                tmp_word = verify_words[:i]
                if tmp_word in cls.word_dict:
                    result_dict[tmp_word] = tmp_word
            i = 0
            while i <= varify_len - 1:
                tmp_word = verify_words[i:]
                if tmp_word in cls.word_dict:
                    result_dict[tmp_word] = tmp_word
                i += 1
            if result_dict:
                tmp_list = get_key(result_dict, tmp_list, verify_words, True)
            else:
                tmp_list.append(verify_words)
        return tmp_list, match

    @classmethod
    def get_verify_words(cls, verify_words, is_num , is_eng, is_sign, words):
        """
        .找出英文  数字  英数  段
        """
        tmp_list = []
        if verify_words:
            # 如果是纯数字或者包含特殊符号,直接返回   如果是纯英文的话,解析是否要拆开
            if (is_num and not is_eng) or (is_eng and not is_num) or is_sign:
                if is_eng and not (is_num or is_sign or verify_words in cls.word_dict):
                    t_list , _ = cls.get_eng_verify(verify_words, words)
                    tmp_list.extend(t_list)
                else:
                    tmp_list.append(verify_words)
            else:
                # 说明verify当中包含了英文数字 则对英文数字进行处理   如  1v,1v2a,1v100,a1v100等数据进行拆分操作,如果条件不满足,则全部返回
                vrf_len = len(verify_words)
                tmp1, tmp2 = '', ''
                for i in range(vrf_len):
                    wd = verify_words[i]
                    if '0' <= wd <= '9' or wd == '.':
                        tmp1 += wd
                    else:
                        tmp2 += wd
                if verify_words in cls.word_dict or len(verify_words) == 1: # 如果长度为1或者在词典中,则直接返回
                    tmp_list.append(verify_words)
                else:
                    if verify_words.replace(tmp1, '') == tmp2: # 如果包含字母数字,replace以后相等的话,则区别以下情况
                        if tmp1 in verify_words and not tmp2 in verify_words: # 如果数字在verify中,字母不在verify中,则对split(数字)得到2组英文
                            is_unit = True
                            u_list = verify_words.split(tmp1)
                            for u in u_list:
                                if u in UnitTools.unit_list:
                                    continue
                                else:
                                    is_unit = False
                            if is_unit:
                                tmp_list.extend(u_list) # 如 ah100v  第一个数字乱序 12电池ah100v
                                tmp_list.append(tmp1)
                            else:
                                tmp_list.append(verify_words)
                        elif tmp2 in verify_words and not tmp1 in verify_words and tmp2 in UnitTools.unit_list: # 如果字母在verify中,数字不在,并且字母是单位
                            tmp_list.extend(verify_words.split(tmp2))
                            tmp_list.append(tmp2)
                        else:
                            # 否则,先对英文做拆分,看是否英文合法
                            tmp2_list, match = cls.get_eng_verify(tmp2, words)
                            if len(tmp2_list) == 1:
                                if tmp2_list[0] in UnitTools.unit_list and not match:
                                    tmp_list.append(verify_words)
                                else:
                                    tmp_list.extend([tmp1, tmp2])
                            elif tmp2_list and not '0' <= verify_words[-1] <= '9': # 如  00mg 0805led  避免出现 r13,a03,g17 某种特定型号的代称 拆分的问题
                                tmp_list.append(tmp1)
                                tmp_list.extend(tmp2_list)
                            elif tmp1 in cls.word_dict or (tmp2 in UnitTools.unit_list) or tmp2 in cls.word_dict:
                                tmp_list.extend([tmp1, tmp2])
                            else:
                                tmp_list.append(verify_words)
                    else:
                        # 对于英文数字互插的情况,如  5a12v这样的情况,可以去用数字匹配单位,都匹配上,则匹配返回,否则直接返回
                        num_list = cls.find_num_list(verify_words)
                        num_list_len = len(num_list)
                        unit_dict = UnitTools.get_verify_unit_dict(verify_words, num_list)
                        value_list = []
                        for value in unit_dict.values():value_list.extend(value)
                        if unit_dict and (len(unit_dict) == num_list_len or (len(set(num_list)) != num_list_len and len(value_list) == num_list_len)):
                            for key in unit_dict:
                                unit_list = unit_dict[key]
                                for unit in unit_list:
                                    tmp_list.append(key + unit)
                        else:
                            if verify_words.replace(tmp2, '') == tmp1:
                                tmp_list.extend([tmp2] + verify_words.split(tmp2))
                            else:
                                tmp_list.append(verify_words)
        return tmp_list

    @classmethod
    def get_verify(cls, words):
        verify_words, tmp_list = '', []
        is_num , is_eng, is_sign = False, False, False
        for wd in words:
            if ord(wd) <= 127 and not (wd == ' '):
                verify_words += wd
                if u'0' <= wd <= u'9' or '.' == wd:
                    is_num = True
                elif u'a' <= wd <= u'z':
                    is_eng = True
                else:
                    is_sign = True
            else:
                if verify_words:
                    tmp_list.extend(cls.get_verify_words(verify_words, is_num , is_eng, is_sign, words))
                verify_words = ''
                is_num , is_eng, is_sign = False, False, False
        tmp_list.extend(cls.get_verify_words(verify_words, is_num , is_eng, is_sign, words))
        return tmp_list

    @classmethod
    def get_verify_list(cls, words):
        """
        .得到英文  数字  英数 组合列表
        """
        verify_list = []
        tmp_list = cls.get_verify(words)
        for word in list(set(tmp_list)):
#             if cls.get_word_len(word) == 1:
#                 verify_list.append(word)
            if len(word) == 1:
                verify_list.append(word)
                continue
            result = cls.get_verify_chunk(word, words)
            words = words.replace(word, '', 1)
            if result :
                verify_list.append(result)
        return verify_list

    @classmethod
    def get_verify_chunk(cls, word, words):
        """
        .找出相关的中英   中英数   英中   中数等相关的关键词   比如  胖mm  SIM卡
        """
        result, tmp = [word], word
        index = words.find(word)
        next_index = index + len(word)
        words_len = len(words)
        tmp_index = index
        while index > tmp_index - cls.VERIFY_CANDIT_LENGTH and index > 0:
            index -= 1
            tmp = words[index] + tmp
            result.append(tmp)
        index = next_index
        tmp = word
        while next_index <= index + cls.VERIFY_CANDIT_LENGTH - 1 and not(next_index == words_len):
            tmp = tmp + words[next_index]
            result.append(tmp)
            next_index += 1
        return result

    @classmethod
    def find_verify_words(cls, words):
        """
        .得到所有的需要确认的关键词
        """
        result_list = []
        word_dict = cls.get_word_dict()
        verify_list = cls.get_verify_list(words)
        for verify in verify_list:
            result = []
            for chk in verify:
                if chk in word_dict:
                    result.append([chk])
            if len(result) >= 2 :
                result_list.append(cls.filter_chunks(result)[0])
            elif len(result) == 1:
                result_list.append(result[0][0])
            else:
                if len(verify[0]) > 0:
                    result_list.append(verify[0])
        return list(set(result_list))

    @classmethod
    def chsgm_word_list(cls, word_list):
        """
        .分词
        """
        index = 0
        result_list = []
        while index < len(word_list):
            chunk = cls.get_best_chunk(word_list, index)
            if chunk:
                word = chunk[0]
            else:
                word = word_list[index]
            result_list.append(word)
            index += len(word)
        return result_list

    @classmethod
    def chsgm_words(cls, words):
        """
        .结果汇总
        """
        cls.get_word_dict()
        result_list, tmp_list = [], []
        words = cls.replace_unavailable_wd(words)
        words = unicode(words.lower())
        verify_list = cls.find_verify_words(words)
        if verify_list:
            tmp_list.extend(verify_list)
            for verify in verify_list:
                words = words.replace(verify, ' ')
        word_list = words.split()
        for word in  word_list:
            if not word:
                continue
            elif len(word) <= 2:
                tmp_list.append(word)
            else:tmp_list.extend(cls.chsgm_word_list(list(word)))
        for tmp in tmp_list:
            if len(tmp) > 1:
                words = words.replace(tmp, ' ', 1)
                result_list.append(tmp)
            elif tmp in verify_list:
                result_list.append(tmp)
            else:
                continue
        for tmp in words.split():
            if tmp:
                result_list.append(tmp)

        return result_list

    @classmethod
    def find_num_list(cls, words):
        """
        .从关键词当中匹配出数字
        """
        tmp_list, tmp_word = [], ''
        for wd in words:
            if u'0' <= wd <= '9' or wd == u'.':
                tmp_word += wd
            else:
                if tmp_word:
                    if not tmp_word == '.':
                        tmp_list.append(tmp_word)
                    tmp_word = ''
        if tmp_word:
            tmp_list.append(tmp_word)
        return tmp_list

    @classmethod
    def get_list_dup_word(cls, word_list):
        """
        .从list当中选出重复的元素
        """
        tmp_list = word_list[:]
        for rs in set(word_list):
            tmp_list.remove(rs)
        return tmp_list

    @classmethod
    def word_stat_in_list(cls, word, word_list):
        """
        .查看列表当中的元素是否都是属于该字符串word
        """
        for wd in word_list:
            if wd in word:
                return True
        return False

    @classmethod
    def get_word_len(cls, word):
        """
        .获取关键词长度  默认连续的英文和连续的数字长度为1
        """
        count , tmp_word = 0, ''
        for wd in word:
            if ord(wd) < 127:
                tmp_word += wd
            else:
                if tmp_word:
                    count += 1
                count += 1
                tmp_word = ''
        if tmp_word:
            count += 1
        return count

    @classmethod
    def is_num(cls, num_str):
        if num_str == '.' or num_str.count('.') > 1:
            return False
        num_f = float(num_str)
        if str(int(num_f)) == num_str or str(num_f) == num_str:
            return True
        return False

    @classmethod
    def get_clash_combine(cls, combinations_dict, result_list, s_tmp, values_list):
        """
        .将有冲突的组合词列表当中  选择出最合适的一组  如  ['u盘','盘子']  返回 u盘
        """
        def sort_by_combine_word(x, y):
            x_len = cls.get_word_len(x)
            y_len = cls.get_word_len(y)
            len_x = len(x)
            len_y = len(y)
            if len(x) == 1:return - 1
            elif len_x == len_y:return cmp(cls.word_dict[x], cls.word_dict[y])
            elif x_len != y_len:return cmp(x_len, y_len)
            elif cls.word_dict[x] != cls.word_dict[y]:return cmp(cls.word_dict[x], cls.word_dict[y])
            elif len(x) != len(y): return cmp(len(x), len(y))
            else:return - 1
        dup_list = cls.get_list_dup_word(values_list)
        clash_word_list = [key for key in combinations_dict.keys() if cls.word_stat_in_list(key, dup_list)]
        word_list = []
        if clash_word_list:
            clash_word_list.sort(sort_by_combine_word, reverse = True)
            word = clash_word_list[0]
            word_list.append(word)
        else:
            word_list = combinations_dict.keys()
        result_list.extend(word_list)
        finish_list = []
        for word in word_list:
            finish_list.extend(combinations_dict[word])
        tmp_list = list(s_tmp - set(finish_list))
        if tmp_list:
            result_list.extend(cls.combine_word(tmp_list))
        return result_list, tmp_list

    @classmethod
    def combine_word(cls, word_list):
        """
        .将乱序关键词组合   如  床  婴儿  组合成  婴儿床
        """
        result_list, combinations_dict = [], {}
        result_list.extend(cls.get_list_dup_word(word_list)) # 先去除重复的词
        tmp_list = list(set(word_list))
        for i in range(4, 1, -1):
            for tmp in combinations(tmp_list, i): # 先组长的,3个3个一组,如果长度小于3 则会返回空
                result = permutations(tmp) # 将返回的值进行排列组合
                for kw in result:
                    word = ''.join(kw)
                    if word in cls.word_dict:
                        combinations_dict[word] = list(tmp)
        values_list = []
        for value in combinations_dict.values():values_list.extend(value) # 获取结果
        values_len, tmp_len = len(values_list), len(tmp_list)
        s_values, s_tmp = set(values_list), set(tmp_list)
        if values_list == tmp_list or (s_values == s_tmp and values_len == tmp_len): result_list.extend(combinations_dict.keys()) # 没有冲突,直接返回
        elif len(combinations_dict) == 1: # 结果长度为1也没有冲突返回结果,并进行下一波组词
            word = combinations_dict.keys()[0]
            result_list.extend(combinations_dict.keys())
            tmp_list = list(s_tmp - set(combinations_dict[word]))
            if tmp_list:
                result_list.extend(cls.combine_word(tmp_list))
        elif len(s_values) and values_list: # 有返回结果,并且长度不为1 则是否要做解决冲突操作
            result_list, tmp_list = cls.get_clash_combine(combinations_dict, result_list, s_tmp, values_list)
        else:
            result_list.extend(tmp_list) # 组不出任何结果,直接返回
        return result_list

    @classmethod
    def sort_sign_word(cls, vrf_list, key):
        """
        .将模板两边的数字排序
        """
        if not TemplateSign.get_match_unit_stat(key):
            vrf_list.sort(lambda x, y:float(x) > float(y) and 1 or -1)
        key_num = key.join(vrf_list)
        return key_num

    @classmethod
    def get_num_unit(cls, tmp_list, num_list, key):
        """
        .最后一道程序  将没有匹配到的数字和单位  匹配在一起
        """
        result, unit_list, has_unit = [], [], False
        if num_list:
            num_list = [num for num in num_list if num in tmp_list]
            for tmp in tmp_list:
                if tmp:
                    if tmp in UnitTools.unit_list:
                        has_unit = True
                        unit_list.append(tmp)
                        continue
#                     result.append(SynonymyWord.get_use_word(tmp))
                    result.append(tmp)
            if num_list and list(set(tmp_list) & set(num_list)) == num_list and len(num_list) == 1 and has_unit and len(unit_list) == 1 :
                num = num_list[0]
                if not num == '.' and ((key and key in num) or not (num.count('.') <= 1 and 1990 <= int(float(num)) <= 2050)):
                    result.append(num + unit_list[0])
                    result.remove(num)
                    has_unit = False
            if has_unit and unit_list :
                result.extend(unit_list)
        else:
            result = tmp_list
        return result

    @classmethod
    def replace_white_space(cls, word):
        if ' ' in word and not word == ' ':
            wd_list = word.split()
            wd_list_len = len(wd_list)
            tmp_word = ''
            for i in range(wd_list_len - 1):
                j = i + 1
                if ord(wd_list[i][-1]) < 127 and ord(wd_list[j][0]) < 127:
                    tmp_word += (wd_list[i] + ' ')
                else:
                    tmp_word += wd_list[i]
            if wd_list:
                tmp_word += wd_list[-1]
            return tmp_word
        else:
            return word

    @classmethod
    def chsgm_keyword(cls, keyword):
        """
        .关键词拆分
        """
        cls.get_word_dict()
        keyword = cls.replace_white_space(keyword)
        result_list, tmp_list, replace_list = [], [], []
        verify_list = cls.get_verify(keyword)
        num_list = cls.find_num_list(keyword)
        sign_dict = TemplateSign.check_temp_sign_keyword(keyword)
        key = ''
        if verify_list and TemplateSign.check_sign_dict(sign_dict, num_list, keyword):
            key = sign_dict.keys()[0]
            num_len = len(num_list)
            key_num = ''
            verify_words = ','.join(verify_list)
            key_stat = key in verify_words
            if not key_stat:
                verify_words = keyword
            match_stat, value = TemplateSign.is_model(key, verify_words, num_list)
            if match_stat or num_len >= 3 or num_len <= 1:
                if not key_stat and value:
                    result_list.append(value)
                    replace_list.append(value)
                else:
                    tmp_list.extend(verify_list)
                    replace_list.extend(verify_list)
            else:
                key_num = cls.sort_sign_word(num_list, key)
                replace_list.extend(num_list + [key])
            if TemplateSign.get_match_unit_stat(key) and key_num:
                num_list = [key_num]
            result_list.append(key_num)
            for replace in replace_list:
                keyword = keyword.replace(replace, ' ', 1)
        else:
            for replace in verify_list:
                if not replace:
                    continue
                if len(replace) > 1 or ord(replace) < 127:
                    keyword = keyword.replace(replace, ' ', 1)
                    tmp_list.append(replace)
        kw_list = keyword.split()
        for kw in kw_list:
            if not kw:continue
            else:tmp_list.extend(cls.chsgm_word_list(list(kw)))
        if len(tmp_list) > 1 and keyword.replace(' ', ''):
            tmp_list = cls.combine_word(tmp_list)

        return cls.get_num_unit(result_list + tmp_list, num_list, key)

word_coll = ChSegement._get_collection()

class UnitTools(Document):
    unit_name = StringField(verbose_name = "单位类别名称",)
    unit_dscrb = StringField(verbose_name = "单位类别描述", max_length = 100, required = True)
    unit_list = ListField(verbose_name = "单位列表")
    split_with_num = BooleanField(verbose_name = "是否和数字拆分,比如时间单位 2014年 拆分成2014,年")
    meta = {"collection":"kwlib_unit_tools", "db_alias": "kwlib-db"}
    unit_dict = {}
    unit_list = []

    @classmethod
    def get_unit_dict(cls):
        '''
        .加载到内存
        '''
        if not cls.unit_dict:
            for wd in unit_coll.find():
                cls.unit_dict[wd['_id']] = wd
                cls.unit_list.extend(wd['unit_list'])
        return cls.unit_dict

    @classmethod
    def get_verify_unit_dict(cls, verify_word, num_list):
        '''
        .匹配 1v15a 这样组合关键词的单位
        '''
        cls.get_unit_dict()
        unit_dict , unit_list = {}, []
        for num in num_list:
            verify_word = verify_word.replace(num, ' ', 1)
        tmp_list = verify_word.split()
        for tmp in tmp_list:
            if not tmp:
                continue
            if tmp in cls.unit_list:
                unit_list.append(tmp)
                continue
            else :
                return unit_dict
        if len(unit_list) == len(num_list):
            count = 0
            for num in num_list:
                unit = unit_list[count]
                if num in unit_dict:
                    unit_dict[num].append(unit)
                else:
                    unit_dict[num] = [unit]
                count += 1
        return unit_dict

    @classmethod
    def get_unit(cls, keyword):
        '''
        .获取关键词的单位
        '''
        cls.get_unit_dict()
        unit , count = '', 0
        kw_len = len(keyword)
        has_find = False
        for kw in keyword:
            count += 1
            if '0' <= kw <= '9' or kw == '.':
                continue
            else:
                index = count - 1
                unit_tmp = ''
                while index <= count + 4 and index <= kw_len - 1:
                    next_wd = keyword[index]
                    index += 1
                    if next_wd == ' ' and next_wd:
                        unit_tmp = ''
                        continue
                    if unit_tmp and not (ord(next_wd) > 127 and ord(unit_tmp[-1]) > 127 or ord(next_wd) <= 127 and ord(unit_tmp[-1]) <= 127):
                        unit_tmp = ''
                    unit_tmp += next_wd
                    if unit_tmp in cls.unit_list:
                        unit = unit_tmp
                        has_find = True
            if has_find:
                break
        return unit

unit_coll = UnitTools._get_collection()

class TemplateSign(Document):
    temp_sign = StringField(verbose_name = "模板符号或者字符")
    temp_schm = StringField(verbose_name = "模板样式,比如,1-3岁为匹配模式 正则表达式为 ,'\d+%s\d+'", max_length = 100, required = True)
    synonym_list = ListField(verbose_name = "同义列表,比如1岁-3")
    is_range = BooleanField(verbose_name = "是否遍历范围")
    max_range_index = IntField(verbose_name = "最大遍历范围")
    split_by_sign = BooleanField(verbose_name = "是否根据符号拆分")
    synonym_word = StringField(verbose_name = "符号同义词,比如   1-2==1到2==1至2")
    is_match_unit = BooleanField(verbose_name = "是否匹配单位")
    meta = {"collection":"kwlib_template_sign", "db_alias": "kwlib-db"}
    temp_sign_dict = {}

#   demo  re.compile(r'\d+比\d+').findall('123比456,123456比,456比123')
    @classmethod
    def get_temp_sign_dict(cls):
        '''
        .加载到内存
        '''
        if not cls.temp_sign_dict:
            for wd in temp_sign_coll.find():
                cls.temp_sign_dict[wd['_id']] = wd
        return cls.temp_sign_dict

    @classmethod
    def get_match_unit_stat(cls, key):
        '''
        .获取是否匹配单位
        '''
        return cls.temp_sign_dict[key]['is_match_unit']

    @classmethod
    def get_match_scheme(cls, key, words):
        '''
        .获取基本模板匹配到的关键词
        '''
        temp_schm = cls.temp_sign_dict[key]['temp_schm']
        return re.compile(temp_schm).findall(words)

    @classmethod
    def get_reverse_stat(cls, key):
        '''
        .获取是否对模板两边进行排序
        '''
        return cls.temp_sign_dict[key]['is_reverse']

    @classmethod
    def is_model(cls, key, words, num_list):
        '''
        .正则表达式匹配模型数据,包括一些模板特殊情况匹配  如  4对6  12v转220v av线转vga线
        '''
        cls.get_temp_sign_dict()
        for num in num_list:
            if num == '.' or not (ChSegement.is_num(num)):
                return True, ''
        match_model_list = [
                        '\w*[a-z]+\d+%s\d+[a-z]+\w*' % key,
                        '\w*\d+%s\d+[a-z]{3,10}\w*' % key,
                        '\w*\d+[a-z]{3,10}%s\d+\w*' % key,
                        '\w*\d+%s[a-z]+\w*' % key,
                        '\w*[a-z]+\d+%s[a-z]+\w*' % key,
                        '\w*[a-z]+%s\d+[a-z]+\w*' % key,
                        '\w*[a-z]+%s[a-z]+\w*' % key,
                        '\w*[a-z]+\d+%s\d+\w*' % key,
                        '\w*[a-z]+\d+[a-z]+%s\d+\w*' % key,
                        '\d+[a-z]+%s\d+[a-z]+' % key,
                        '[a-z]+\W*%s[a-z]+\W*' % key,
                        '\w*\d+\.\d+\W+%s\d+\.\d+\W+\w*' % key,
                          ]
        for schm in match_model_list:
            word = re.compile(schm).findall(words)
            if word:
                return True, word[0]
        return False, ''

    @classmethod
    def check_temp_sign_keyword(cls, keyword):
        '''
        .检查关键词中是否包含模板 key
        '''
        cls.get_temp_sign_dict()
        sign_dict = {}
        for wd in keyword:
            if wd in TemplateSign.temp_sign_dict:
                if wd in sign_dict:
                    sign_dict[wd] += 1
                else:
                    sign_dict[wd] = 1
        return sign_dict

    @classmethod
    def check_sign_dict(cls, sign_dict, num_list, keyword):
        num_list_len = len(num_list)
        keyword = keyword.replace(' ', '')
        if len(sign_dict) == 1 and num_list_len == 2:
            key = sign_dict.keys()[0]
            if sign_dict[key] == 1:
                if ord(key) > 127:
                    num1_index = keyword.index(num_list[0]) + len(num_list[1])
                    num2_index = keyword.rindex(num_list[1])
                    key_index = keyword.index(key)
                    if not(math.fabs(num1_index - key_index) > 2 or math.fabs(num2_index - key_index) > 2):
                        return True
                else:
                    return True
        return False

temp_sign_coll = TemplateSign._get_collection()

class SynonymyWord(Document):
    use_word = StringField(verbose_name = "使用的关键词")
    synonymy_words = StringField(verbose_name = "同义词,多个词之间  使用  ,号隔开   如:  女式,女士")
    synonymy_dict = {}
    meta = {"collection":"kwlib_synonymy_word", "db_alias": "kwlib-db"}

    @classmethod
    def get_synonymy_dict(cls): # TODO  以后全部改成使用sort(原子词) 这里如果拆分结果只有一个的话,排序,如果结果大于1个的话,那么则进行排序  来消除2个顺序不同的词一样的意思  比如  壳套  套壳   这个类将会被干掉  2015.03.01 刘声传
        if not cls.synonymy_dict: # TODO 同上示例     "木杉"   "杉木"
            for synm in synonymy_coll.find():
                use_word = synm['_id']
                cls.synonymy_dict[use_word] = {'use_word':use_word, 'synm':synm['synonymy_words']}
                word_list = synm['synonymy_words'].split(',')
                word_list.remove(use_word)
                for word in word_list:
                    cls.synonymy_dict[word] = {'use_word':use_word, 'synm':synm['synonymy_words']}
        return cls.synonymy_dict

    @classmethod
    def get_use_word(cls, word):
        cls.get_synonymy_dict()
        if word in cls.synonymy_dict:
            return cls.synonymy_dict[word]['use_word']
        return word

synonymy_coll = SynonymyWord._get_collection()