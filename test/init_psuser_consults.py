# coding=UTF-8
'''重新分配所有顾问的客户'''
import init_environ
from apps.common.utils.utils_mysql import execute_query_sql_return_tuple, execute_manage_sql
from apps.subway.models import Account
from apps.ncrm.models import PSUser, ClientGroup

def get_dpt_psu(psuser_reserved_dict):
    temp_dpt_list = [(dpt, sum(pdict.values())) for dpt, pdict in psuser_reserved_dict.items()]
    temp_dpt_list.sort(lambda x,y:cmp(x[1],y[1]))
    dpt = temp_dpt_list[0][0]
    temp_psu_list = psuser_reserved_dict[dpt].items()
    temp_psu_list.sort(lambda x,y:cmp(x[1],y[1]))
    return dpt, temp_psu_list[0][0]

def distribute_customer(shop_id, psu_id):
    # sql = """
    # update ncrm_subscribe c join ncrm_customer e on c.shop_id=e.shop_id
    # set c.consult_id=%s, e.consult_id=%s
    # where c.shop_id=%s and c.end_date>current_date and c.category in ('kcjl', 'qn');
    # """ % (psu_id, psu_id, shop_id)
    sql = """
    update ncrm_subscribe c join (
    select b.shop_id as shop_id, b.id as id from ncrm_subscribe a join (
    select max(id) as id, shop_id from ncrm_subscribe where shop_id=%s and article_code in ('ts-25811','FW_GOODS-1921400') and start_date<=current_date group by shop_id
    ) b on a.id=b.id where a.category in ('kcjl', 'qn')
    ) d on c.shop_id=d.shop_id join ncrm_customer e on c.shop_id=e.shop_id
    set c.consult_id=%s, e.consult_id=%s
    where (c.id>=d.id or c.end_date>current_date) and c.category in ('kcjl', 'qn');
    """ % (shop_id, psu_id, psu_id)
    execute_manage_sql(sql)

def main():
    # 统计服务中客户
    sql = """
    select a.shop_id from ncrm_subscribe a join (
    select max(id) as id from ncrm_subscribe where article_code in ('ts-25811', 'FW_GOODS-1921400') and end_date>current_date group by shop_id
    ) b on a.id=b.id where a.category in ('kcjl', 'qn');
    """
    inservice_list = [row[0] for row in execute_query_sql_return_tuple(sql)]

    # # 先统一分配给指定人员
    # temp_id = 3
    # sql = """
    # update ncrm_subscribe c join (
    # select max(id) as id, shop_id from ncrm_subscribe where category in ('kcjl', 'qn') and end_date>current_date group by shop_id
    # ) d on c.shop_id=d.shop_id join ncrm_customer e on c.shop_id=e.shop_id
    # set c.consult_id=%s, e.consult_id=%s
    # where (c.id>=d.id or c.end_date>current_date) and c.category in ('kcjl', 'qn');
    # """ % (temp_id, temp_id)
    # execute_manage_sql(sql)

    psuser_dict = {
        "GROUP1":["金佩","汪锋","欧阳华宇","胡梦","姚远"],
        "GROUP2":["张志威","蒋雨娜","胡佳丽","桂维维","李雪琴"],
        "GROUP3":["王玥","丁雪琴","万明","杨勇","尚文蔚"],
        "GROUP4":["向宇","瞿小凡","熊钰馨","邓雨晴"],
        "GROUP5":["王昆","薛尧","王洋","冯磊"],
    }
    # 收集售后的保留用户信息
    psuser_list = []
    psuser_reserved_dict = {}
    for dpt, lst in psuser_dict.items():
        psuser_list += lst
        # psuser_reserved_dict[dpt] = {}
    all_reserved_list = []
    psuser_list = PSUser.objects.filter(name_cn__in=psuser_list)
    for psuser in psuser_list:
        dpt_dict = psuser_reserved_dict.setdefault(psuser.department, {})
        dpt_dict[psuser.id] = 0
        cgs = ClientGroup.objects.filter(create_user=psuser, group_type=1)
        if cgs:
            try:
                id_list = eval(cgs[0].id_list)
                if type(id_list)==list and id_list:
                    dpt_dict[psuser.id] = len(id_list)
                    all_reserved_list.extend(id_list)
            except:
                pass

    # 根据最近7天总花费排序所有非保留用户
    for shop_id in all_reserved_list:
        if shop_id in inservice_list:
            inservice_list.remove(shop_id)
    inservice_rpt_list = []
    for shop_id in inservice_list:
        temp_rpt = Account.Report.get_summed_rpt({'shop_id':shop_id}, rpt_days=7)
        if temp_rpt:
            inservice_rpt_list.append((shop_id, temp_rpt[shop_id]['cost']))
        else:
            inservice_rpt_list.append((shop_id, 0))
    inservice_rpt_list.sort(lambda x,y:cmp(y[1], x[1]))
    i = 0
    j = len(inservice_rpt_list)
    for shop_id, _ in inservice_rpt_list:
        dpt, psu_id = get_dpt_psu(psuser_reserved_dict)
        distribute_customer(shop_id, psu_id)
        psuser_reserved_dict[dpt][psu_id] += 1
        i += 1
        print '分配进度：', i, j

if __name__ == "__main__":
    print 'init psuser consults begin'
    main()
    print 'end'
