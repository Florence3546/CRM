# coding=UTF-8

import re

from apps.ncrm.querier_conf import CUSTOMER_FIELDS, CONFIG_MAPPING, \
     SPECIAL_CHARACTER_CONVERT_MAPPING, customers_initialize_data
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apps.common.utils.utils_log import log

__all__ = ['query_enter', 'query_statement_info']


def check_statement(fields):
    """检查语法"""
    all_fields_set = set(CUSTOMER_FIELDS.keys() + CONFIG_MAPPING.keys())
    for field in fields:
        if field not in all_fields_set:
            try:
                int(field)
            except :
                return False, '字段 %s 查询器不支持 ' % (field)
    return True, ''

def special_character_convert(query_statement):
    for old_str, new_str in SPECIAL_CHARACTER_CONVERT_MAPPING.items():
        query_statement = query_statement.replace(old_str, new_str)
    return query_statement

def split_qurey_statement(query_statement):
    """"拆分查询器"""
    statement = query_statement.strip()
    cond_list = []
    split_flags = ('and', 'or')
    for cond in re.split('(\s%s\s)|(\s%s\s)' % (split_flags), statement):
        if cond and cond.strip() not in split_flags:
            cond_list.append(cond)
    return cond_list

def extract_fields(cond_list):
    """抽取有效字段"""
    def get_valid_filed(split_list):
        field = ""
        key_words = ['not', 'in', 'is']
        for split_str in split_list:
            if split_str \
                 and split_str not in key_words \
                 and "'" not in split_str  \
                 and '"' not in split_str  \
                 and '[' not in split_str  \
                 and ']' not in split_str  \
                 and not split_str.isdigit():
                try:
                    int(split_str)
                except:
                    field = split_str
                    break
        return field

    fields = []
    for cond in cond_list:
        field = get_valid_filed(re.split(r'[\s<>=]', cond))
        if field :
            fields.append(field)
    return fields

def filter_fields(fields):
    init_fields = []
    reset_fields = []
    for field in fields:
        if field in CUSTOMER_FIELDS.keys():
            init_fields.append(field)
        else:
            reset_fields.append(field)
    return init_fields, reset_fields

def get_all_db_fields(handler_list):
    db_fields = []
    for handler in handler_list:
        cur_db_fiedls = handler.db_field
        db_fields.extend(cur_db_fiedls)
    return list(set(db_fields))

def prepare_data_foruser(fields):
    """为过滤操作，准备数据"""
    # 1. 初始化所有字段
    # 2. 构建所有字段，并更新

    init_fields, reset_fields = filter_fields(fields)

    reset_fiedls_default = {}
    handler_list = []
    for field in reset_fields:
        handler = CONFIG_MAPPING[field]
        handler_list.append(handler)
        reset_fiedls_default.update({field:handler.default})

    user_list = customers_initialize_data(init_fields)
    user_mapping = {}
    shop_nick_mapping = {}
    for user in user_list:
        shop_id = user['shop_id']
        user = DictWrapper(user)
        user.update(reset_fiedls_default)
        user_mapping.update({shop_id:user})
        shop_nick_mapping[user.nick] = shop_id

    exec_mapping = {}
    for handler in handler_list:
        func_name = handler.collector_handler
        if func_name not in exec_mapping:
            exec_mapping[func_name] = []
        exec_mapping[func_name].append(handler)

    for deal_func, h_list in exec_mapping.items():
        # 1. 获取数据源
        db_fields = get_all_db_fields(h_list)
        data_list = deal_func(db_fields, shop_nick_mapping)
        # 2. 处理数据源
        for data in data_list:
            shop_id = data.pop('shop_id')
            if shop_id in user_mapping:
                temp_result = {}
                for hler in h_list:
                    result = hler.data_handler(data)
                    temp_result.update(result)
                user_mapping[shop_id].update(temp_result)
            else:
                # 没有数据暂不处理
                pass

    return user_mapping.values()

def filter_user(fields, user_list, query_statement):
    """对所得到的内部参数进行过滤，赛选"""

    def get_filter_statement(fields, query_statement, mark):
        filter_statement = query_statement
        for field in fields:
            filter_statement = filter_statement.replace(field, "%s.%s" % (mark, field))
        return filter_statement

    mark = 'user'
    filter_statement = get_filter_statement(fields, query_statement, mark)
    log.info('step 3 : express statement : %s' % (filter_statement))

    result_list = []
    for user in user_list:
        try:
            if eval(filter_statement):
                result_list.append(user.shop_id)
        except :
            pass # customer表中字段可能会为None，该部分直接过滤

    return result_list

def get_users_byquery(fields, query_statement):
    """查询器核心，用户准备数据，并执行过滤"""
    user_list = prepare_data_foruser(fields)
    result_list = filter_user(fields, user_list, query_statement)
    return result_list

def query_enter(query_statement):
    """查询器入口"""
    query_statement = query_statement.strip()
    query_statement = special_character_convert(query_statement)
    cond_list = split_qurey_statement(query_statement)

    log.info('step 1 : split condition list is :  %s' % (' | '.join(cond_list)))

    fields = extract_fields(cond_list)
    log.info('step2 :  fields list is :  %s' % (' | '.join(fields)))

    is_valid , reason = check_statement(fields)
    id_list = []
    if is_valid:
        try:
            id_list = get_users_byquery(fields, query_statement)
        except Exception, e:
            log.error('querier execute error, query_statement = %s, e=%s' % (query_statement, e))
            reason = "查询器执行失败，请检查您的语法"
    return id_list, reason

def query_statement_info():
    """获取查询器的语法简介"""
    result_dict = {}
    result_dict.update(CUSTOMER_FIELDS)
    for keyword , event in CONFIG_MAPPING.items():
        result_dict.update({keyword:event.description})
    return result_dict

if __name__ == "__main__":
    query_statement = """
       '如果' in nick and is_kcjl and is_qn and surplus > 5 and subscribe > 30 and last_order_status == 2 and last_pay > 100 and total_pay>800 and order_count > 4 and roi_7 > 0
    """
#     query_statement = """
#        is_kcjl and is_qn and subscribe > 0
#     """
    import time
    start = time.clock()
#     query_enter = performance_test.profile(file_name = "query_enter.status", size = 500)(query_enter)
    x = query_enter(query_statement)
    print 'exec time  :  ', time.clock() - start
    print 'data : ', x
    help_dict = query_statement_info()
