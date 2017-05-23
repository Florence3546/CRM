# coding=UTF-8
import json
import datetime

from apps.common.utils.utils_log import log


def get_statistics_table(table_name, where_sql, days = 7):
    now_time = datetime.datetime.now()
    start_time = now_time - datetime.timedelta(days = days)
    sql = """
        (
         select ncr.shop_id,count(*) as num
         from ncrm_customer as ncr left join %s as et
                 on ncr.shop_id = et.shop_id
         where 1=1 and create_time >= '%s' %s
         group by ncr.shop_id
        )
    """ % (table_name, start_time, where_sql)
    return sql

NSE_CTR_TABLE = """
    (
     select shop_id, count(*) as num , max(end_date) as deadline
     from ncrm_subscribe
     group by shop_id
    )
"""

TABLE_MAPPING = {
               "ncr":"ncrm_customer",
               "nse":"ncrm_subscribe",
               "nct":"ncrm_contact",
               "nse_ctr":NSE_CTR_TABLE,
               }

def default_deal(val):
    if type(val) == str:
        return val.strip()
    else:
        return str(val)

def str_deal(val):
    if type(val) == str:
        val = val.strip()
    return "'%s'" % (str(val))

# def date_deal(val):
#     return "'%s'" % (str(val))
#
# def datetime_deal(val):
#     return "'%s'" % (str(val))

FIELD_MAPPING = {
                 "nick":default_deal,
                 "shop_id":default_deal,
                 "qq":default_deal,
                 "phone":default_deal,
                 "address":default_deal,
                 "note":default_deal,
                 "article_code":str_deal,
                 "start_date":str_deal,
                 "end_date":str_deal,
                 'biz_type':default_deal,
                 "create_time":str_deal,
                 "consult_id":default_deal,
                 "operater_id":default_deal,
                 "deadline":str_deal,
                 "num":default_deal,
                 "category":str_deal,
                 }

OPERATION_MAPPING = {
                "lt":"< %s",
                "lte":"<= %s",
                "gt":"> %s",
                "gte":">= %s",
                "constants":"like '%%%%%s%%%%'",
                "equal":" = %s",
                "nequal":" <> %s",
                "in":(" in (%s)", list),
                "nin":(" not in (%s)", list),
                "isnull":(" is null", None,),
                "nonull":(" is not null", None),
                }

def check_statement(short_name, field_name, operation):
    reason = ""
    if short_name not in TABLE_MAPPING:
        reason = " table short name : %s is not existed | " % (short_name)
    elif field_name not in FIELD_MAPPING:
        reason = " field name : %s is not existed | " % (field_name)
    elif operation not in OPERATION_MAPPING:
        reason = " operation flag name : %s is not existed | " % (operation)
    return reason

# def parse_table_mapping(short_name):
#     table, kwargs = TABLE_MAPPING[short_name]
#     if type(table) is str:
#         table_name = table
#     else:
#         table_name = table(**kwargs)
#     return {short_name:table_name}

def parse_field_mapping(short_table, field_name, operation, val):
    operation_descr = OPERATION_MAPPING[operation]
    deal_func = FIELD_MAPPING[field_name]

    where_sql = ""
    if type(operation_descr) is tuple:
        where_template, model = operation_descr
        if model: # type deault is llist
            if type(val) is str:
                val = json.loads(val)
            new_val_list = map(deal_func, val)
            where_sql = where_template % (','.join(new_val_list))
        else:
            where_sql = where_template
    else:
        where_template = operation_descr
        where_sql = where_template % (deal_func(val))

    return ("%s.%s" % (short_table, field_name), where_sql)

def parse_base_info(key, val):
    reason = ""
    table_dict = {}
    field_tuple = ()
    try:
        short_name, field_name, operation = key.split("__", 2)
        reason = check_statement(short_name, field_name, operation)
        if not reason:
            # table_dict = parse_table_mapping(short_name)
            table_dict = {short_name: TABLE_MAPPING[short_name]}
            field_tuple = parse_field_mapping(short_name, field_name, operation, val)
    except Exception, e:
        log.error("parse_base_info error, e=%s" % (e))
        reason = "key %s is not in my system" % (key)
    return reason, table_dict, field_tuple

def parse_statement(arg_dict):
    reason = ''
    field_tuple_list = []
    table_name_mapping = {}

    for key, val in arg_dict.items():
        if type(val) is str:
            val = val.strip()
        if val:
            reason, table_dict, field_tuple = parse_base_info(key, val)
            if reason:
                return reason, table_name_mapping, field_tuple_list
            field_tuple_list.append(field_tuple)
            table_name_mapping.update(table_dict)
    return reason, table_name_mapping, field_tuple_list

def generator_select_statement():
    return "SELECT DISTINCT ncr.shop_id \n"

def generator_from_statement(table_name_mapping):
    from_sql = "FROM ncrm_customer as ncr"
    join_template = " join %s as %s on ncr.shop_id=%s.shop_id"
    for short_name, table_name in table_name_mapping.items():
        if short_name != "ncr":
            from_sql += join_template % (table_name, short_name, short_name)
    return "%s \n" % from_sql

def generator_where_statement(field_tuple_list):
    where_sql = "WHERE 1=1"
    where_template = " and %s %s"
    for field_name, val_sql in field_tuple_list:
        where_sql += where_template % (field_name, val_sql)
    return "%s \n" % where_sql

def generator_order_by_statement(table_mapping):
    order_by_list = []
    mark = "nse"
    if mark in table_mapping:
        order_by_list.append("%s.end_date" % (mark))

    if order_by_list:
        return " order by %s asc" % (','.join(order_by_list))
    return ""

def get_valid_args_dict(arg_dict):
    result_dict = {}
    for key, val in arg_dict.items():
        attr_list = key.strip().split("__")
        if len(attr_list) >= 3 and val:
            result_dict.update({key:val})
    return result_dict

def is_continue(field_mapping):
    if "ncr__shop_id__in" in field_mapping:
        if not field_mapping["ncr__shop_id__in"]:
            return False
    return True

def sql_generator(arg_dict):
    sql = ""
    reason, table_name_mapping, field_tuple_list = parse_statement(arg_dict)
    if reason:
        return reason, sql

    sql += generator_select_statement()
    sql += generator_from_statement(table_name_mapping)
    sql += generator_where_statement(field_tuple_list)
    sql += generator_order_by_statement(table_name_mapping)
    return reason, sql

if __name__ == "__main__":
    teset_dict = {"nse_ctr__num__gt":"2"}
    reason, sql = sql_generator(teset_dict)
    print sql
