# coding=UTF-8
'''刷新所有客户的 latest_end '''
import init_environ
from apps.common.utils.utils_mysql import execute_manage_sql

def main():
    sql = """
    update ncrm_customer c join (
    select a.shop_id as shop_id, a.nick as nick, a.latest_end as latest_end, max(b.end_date) as max_end_date from
    (select shop_id, nick, latest_end from ncrm_customer where latest_end<=CURRENT_DATE) a join
    ncrm_subscribe b on a.shop_id=b.shop_id group by a.shop_id HAVING a.latest_end!=max_end_date
    ) d on c.shop_id=d.shop_id
    set c.latest_end=d.max_end_date
    """
    sql2 = """
    update ncrm_customer c join (
    select shop_id, max(end_date) as max_end_date from ncrm_subscribe WHERE category not in ('zz', 'zx', 'other', 'seo', 'kfwb') group by shop_id
    ) s on c.shop_id=s.shop_id
    set c.latest_end=s.max_end_date
    WHERE c.latest_end!=s.max_end_date
    """
    execute_manage_sql(sql2)

if __name__ == "__main__":
    print 'begin'
    main()
    print 'end'
