# coding=UTF-8
import init_environ

from apps.common.utils.utils_mysql import bulk_update_for_sql, execute_manage_sql
from apps.common.utils.utils_datetime import date_2datetime
from apps.ncrm.models import XFGroup, XiaoFuGroup, Customer, event_coll
from apps.mnt.models_monitor import mcs_coll

def export_oldxfg_2new():
    print 'start export_oldxfg_2new'
    if XiaoFuGroup.objects.count() > 0:
        print 'XiaoFuGroup has data, exit'
        return
    xfs = XFGroup.objects.all()
    for xf in xfs:
        XiaoFuGroup.objects.create(
            consult = xf.consult,
            seller = xf.seller,
            is_active = True,
            name = '%s+%s' % (xf.consult.name_cn, xf.seller.name_cn),
            department = xf.consult.department,
            create_time = date_2datetime(xf.consult.entry_date)
            )
    print 'finish export_oldxfg_2new'

def add_xfgid_4mntcostsnap():
    print 'start add_xfgid_4mntcostsnap'
    cust_list = Customer.objects.all().select_related('consult').values_list('shop_id', 'consult')
    consult_shop_dict = {}
    for shop_id, consult_id in cust_list:
        if consult_id not in consult_shop_dict:
            consult_shop_dict[consult_id] = []
        consult_shop_dict[consult_id].append(shop_id)

    xfgroups = XiaoFuGroup.objects.all().select_related('consult').order_by('is_active')
    xfgroup_dict = {obj.consult.id: obj.id for obj in xfgroups}
    for consult_id, shop_id_list in consult_shop_dict.iteritems():
        mcs_coll.update(
            {'shop_id': {'$in': shop_id_list}},
            {'$set': {'consult_id': consult_id, 'xfgroup_id': xfgroup_dict.get(consult_id, None)}},
            multi = True
            )
    print 'finish add_xfgid_4mntcostsnap'

def get_psuser_group_dict():
    xfgroups = XiaoFuGroup.objects.all()
    psuser_group_dict = {}
    for obj in xfgroups:
        if int(obj.consult_id) not in psuser_group_dict:
            psuser_group_dict[int(obj.consult_id)] = int(obj.id)
        if int(obj.seller_id) not in psuser_group_dict:
            psuser_group_dict[int(obj.seller_id)] = int(obj.id)
    return psuser_group_dict

def add_xfgid_4subscibe():
    print 'start add_xfgid_4subscibe'
    psuser_group_dict = get_psuser_group_dict()
    update_list = [[(xfgroup_id, psuser_id)] for psuser_id, xfgroup_id in psuser_group_dict.iteritems()]
    update_xfgroup_sql = "update ncrm_subscribe set xfgroup_id=%s where psuser_id=%s"
    update_consult_xfgroup_sql = "update ncrm_subscribe set consult_xfgroup_id=%s where consult_id=%s"
    count = bulk_update_for_sql(update_xfgroup_sql, update_list)
    consult_count = bulk_update_for_sql(update_consult_xfgroup_sql, update_list)
    print 'finish add xfgid 4subscibe: psuser_count=%s, consult_count=%s' % (count, consult_count)

def add_xfgid_4comment():
    print 'start add_xfgid_4comment'
    psuser_group_dict = get_psuser_group_dict()
    for psuser_id, xfgroup_id in psuser_group_dict.iteritems():
        event_coll.update({'type': 'comment', 'psuser_id': psuser_id}, {'$set': {'xfgroup_id': xfgroup_id}}, multi = True)
        event_coll.update({'type': 'comment', 'duty_person_id': psuser_id}, {'$set': {'duty_xfgroup_id': xfgroup_id}}, multi = True)
    print 'finish add_xfgid_4comment'

def add_xfgid_4unsubscribe():
    print 'start add_xfgid_4unsubscribe'
    psuser_group_dict = get_psuser_group_dict()
    for psuser_id, xfgroup_id in psuser_group_dict.iteritems():
        event_coll.update({'type': 'unsubscribe', 'psuser_id': psuser_id}, {'$set': {'xfgroup_id': xfgroup_id}}, multi = True)
        event_coll.update({'type': 'unsubscribe', 'saler_id': psuser_id}, {'$set': {'saler_xfgroup_id': xfgroup_id}}, multi = True)
        event_coll.update({'type': 'unsubscribe', 'server_id': psuser_id}, {'$set': {'server_xfgroup_id': xfgroup_id}}, multi = True)
    print 'finish add_xfgid_4unsubscribe'

def remove_field():
    print 'start remove field'
    event_coll.update({'type': 'comment'}, {'$unset': {'xfgroup_id': '', 'duty_xfgroup_id': ''}}, multi = True)
    event_coll.update({'type': 'unsubscribe'}, {'$unset': {'xfgroup_id': '', 'saler_xfgroup_id': '', 'server_xfgroup_id': ''}}, multi = True)
    mcs_coll.update({}, {'$unset': {'consult_id': '', 'xfgroup_id': ''}}, multi = True)
    update_subscribe_sql = '''
        alter table ncrm_subscribe
        drop foreign key subscribe_xfgid_fk_xfgid,
        drop foreign key subscribe_consult_xfgid_fk_xfgid,
        drop column xfgroup_id,
        drop column consult_xfgroup_id;
    '''
    delete_table_sql = '''
        drop table if exists ncrm_xiaofugroup;
        drop table if exists ncrm_xfgroupperformance;
    '''
    execute_manage_sql(update_subscribe_sql)
    execute_manage_sql(delete_table_sql)

    print 'finish remove field'
    # drop foreign key subscribe_xfgid_fk_xfgid,
    # drop foreign key subscribe_consult_xfgid_fk_xfgid;

def add_field():
    export_oldxfg_2new()
    add_xfgid_4mntcostsnap()
    add_xfgid_4subscibe()
    add_xfgid_4comment()
    add_xfgid_4unsubscribe()


if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'add_field':
        add_field()
    elif sys.argv[1] == 'rm_field':
        remove_field()
    else:
        print 'args must in: [add_field, rm_field]'
