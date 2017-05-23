# coding=UTF-8

import datetime

from mongoengine.document import Document
from mongoengine.fields import IntField, DateTimeField, StringField, FloatField
from pymongo.errors import BulkWriteError

from apps.common.utils.utils_log import log
from apps.common.utils.utils_collection import genr_sublist
from apps.mnt.models_mnt import mnt_camp_coll
from apps.subway.models_report import camprpt_coll
from apps.ncrm.models import Customer, XiaoFuGroup


class ReportSnap(Document):
    '''全网数据报表快照'''

    OBJECT_TYPE_CHOICES = (('shop', '帐户'), ('camp', '计划'))
    MNT_TYPE_CHOICES = (('all', '所有'), ('mnt', '托管'), ('unmnt', '未托管'))
    SUM_DAYS_CHOICES = (1, 7, 15, 30)
    CONV_DAYS_CHOICES = (1, 3)

    object_type = StringField(verbose_name = '报表对象类型', choices = OBJECT_TYPE_CHOICES)
    mnt_type = StringField(verbose_name = '托管类型', choices = MNT_TYPE_CHOICES)
    count = IntField(verbose_name = '统计数量')
    date = DateTimeField(verbose_name = '快照日期')
    create_time = DateTimeField(verbose_name = '创建日期', default = datetime.datetime.now)
    sum_days = IntField(verbose_name = '报表天数', choices = SUM_DAYS_CHOICES)
    conv_days = IntField(verbose_name = '报表转化天数', choices = CONV_DAYS_CHOICES, default = 3)

    # search_type = IntField(verbose_name = "报表类型", default = 3)
    # source = IntField(verbose_name = "数据来源", default = 3)
    # 基础数据
    impressions = IntField(verbose_name = "展现量", default = 0)
    click = IntField(verbose_name = "点击量", default = 0)
    cost = IntField(verbose_name = "总花费", default = 0)
    # 效果数据
    pay = IntField(verbose_name = "成交金额", default = 0)
    paycount = IntField(verbose_name = "成交笔数", default = 0)
    ctr = FloatField(verbose_name = '', default = 0)
    cpc = FloatField(verbose_name = '', default = 0)
    roi = FloatField(verbose_name = '', default = 0)

    meta = {'db_alias': 'crm-db', 'collection': 'timer_reportsnap', 'indexes': ['date', 'object_type']}

rs_coll = ReportSnap._get_collection()


class TimerLog(Document):
    tj_time = StringField(verbose_name = '统计时段')
    type = StringField(verbose_name = '类型')
    log_type = StringField(verbose_name = '日志内容类型')
    sub_type = StringField(verbose_name = '子类型')
    source = StringField(verbose_name = '来源')
    count = IntField(verbose_name = '个数')
    create_time = DateTimeField(verbose_name = '创建时间')

    meta = {'collection':'timer_log', 'indexes':['type'], "shard_key":('tj_time',)}

tlog_coll = TimerLog._get_collection()


class MntCostSnap(Document):
    '''托管计划快照'''

    rpt_date = DateTimeField(verbose_name = '报表快照日期', required = True)
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "推广计划ID", primary_key = True)
    cost = IntField(verbose_name = "总花费", default = 0)
    category = StringField(verbose_name = "业务类型") # 对应 customer表中的 current_highest_version 字段
    consult_id = IntField(verbose_name = '当前顾问ID')
    xfgroup_id = IntField(verbose_name = '当前销服组ID')

    meta = {'collection': 'timer_mntcostsnap', 'indexes': ['rpt_date', 'xfgroup_id'], "shard_key":('shop_id',)}

    @classmethod
    def bulk_update_db(cls, update_list):
        total_updated_num = 0
        for temp_list in genr_sublist(update_list, 1000): # bulk一次最多1000个
            bulk = cls._get_collection().initialize_unordered_bulk_op()
            for update_tuple in temp_list:
                bulk.find(update_tuple[0]).update(update_tuple[1])
            try:
                result = bulk.execute()
                total_updated_num += result['nModified']
            except BulkWriteError, e:
                log.error('bulk_update_kw2db, detail=%s' % e.details)
                total_updated_num += e.details['nModified']
        return total_updated_num

    @classmethod
    def insert_camp_status(cls, rpt_date):
        mnt_camps = mnt_camp_coll.find()
        insert_list = []
        customer_list = Customer.objects.all().select_related('consult').values_list('shop_id', 'current_highest_version', 'consult')
        cust_dict = {cl[0]: {'version': cl[1], 'consult_id': cl[2]} for cl in customer_list}
        xfgroups = XiaoFuGroup.objects.all().select_related('consult').order_by('is_active')
        xfgroup_dict = {obj.consult.id: obj.id for obj in xfgroups}

        for mnt_camp in mnt_camps:
            cust = cust_dict[mnt_camp['shop_id']]
            insert_list.append({
                'rpt_date': rpt_date,
                'shop_id': mnt_camp['shop_id'],
                'campaign_id': mnt_camp['_id'],
                'category': cust['version'],
                'consult_id': cust['consult_id'],
                'xfgroup_id': xfgroup_dict.get(cust['consult_id'], 0),
                'cost': 0,
                })
        remove_result = cls._get_collection().remove({'rpt_date': rpt_date})
        insert_result = cls._get_collection().insert(insert_list)
        log.info('insert_camp_status ok, rpt_date=%s, insert_count=%s, remove_count=%s' % (rpt_date, len(insert_result), remove_result['n']))

    @classmethod
    def refresh_camp_cost(cls, rpt_date):
        camp_rpts = camprpt_coll.find({'date': rpt_date, 'search_type':-1, 'source':-1}, {'cost': 1, 'campaign_id': 1, 'shop_id': 1})
        update_list = []
        for cr in camp_rpts:
            update_list.append(({'rpt_date': rpt_date, 'shop_id': cr['shop_id'], 'campaign_id': cr['campaign_id']}, {'$set': {'cost': cr['cost']}}))
        update_count = cls.bulk_update_db(update_list)
        log.info('refresh_camp_status ok, rpt_date=%s, update_count=%s' % (rpt_date, update_count))

    @classmethod
    def save_rptsnap(cls):
        today = datetime.datetime.now()
        rpt_date_today = datetime.datetime(today.year, today.month, today.day)
        cls.insert_camp_status(rpt_date_today)

        rpt_date_yesterday = rpt_date_today - datetime.timedelta(days = 1)
        cls.refresh_camp_cost(rpt_date_yesterday)


mcs_coll = MntCostSnap._get_collection()
