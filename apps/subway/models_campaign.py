# coding=UTF-8
import datetime

from django.conf import settings
from mongoengine.document import Document
from mongoengine.errors import DoesNotExist
from mongoengine.fields import (IntField, DateTimeField, StringField,
                                ListField, EmbeddedDocumentField, BooleanField)

from apilib import get_tapi, TopError
from apilib.utils import humanize_exception
from apps.common.utils.utils_log import log
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.utils.utils_datetime import date_2datetime, string_2datetime, time_is_someday, string_2date
from apps.subway.models_parser import CampaignParser
from apps.subway.models_report import CampaignRpt
from apps.subway.utils import (set_rpt_days, get_rpt_days, get_rpt_date,
                               get_rpt_date_list, get_rpt_yt, get_rpt_sum, get_msg_count_list,
                               get_note_count, get_comment_count, save_msg_count, get_snap_list)

class Campaign(Document):
    ONLINE_STATUS_CHOICES = (("offline", "暂停"), ("online", "推广中"))
    SETTLE_STATUS_CHOICES = (("offline", "下线"), ("online", "上线"))
    STATUS_BUDGET_CHOICES = (('0', '未超过日限额'), ('1', '超过日限额'))
    OPAR_STATUS_CHOICES = ((0, '未操作'), (1, '已操作'))

    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "推广计划ID", primary_key = True)
    title = StringField(verbose_name = "推广计划名称", max_length = 40, required = True)
    budget = IntField(verbose_name = "日限额", default = 3000)
    is_smooth = BooleanField(verbose_name = "是否平滑消耗", default = True, choices = ((True, '是'), (False, '否'))) # 是否平滑消耗(0-false-否；1-true-是)
    online_status = StringField(verbose_name = "上下线状态", max_length = 10, choices = ONLINE_STATUS_CHOICES, default = 'online') # 用户设置的上下线状态(offline-暂停；online-推广中)
    settle_status = StringField(verbose_name = "结算状态", max_length = 10, choices = SETTLE_STATUS_CHOICES, default = 'online') # 结算状态(offline-下线；online-上线)
    settle_reason = StringField(verbose_name = "结算下线原因", max_length = 10, default = '') # 结算下线原因(1-余额不足；2-超过日限额)，以分号分隔多个下线原因
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    modify_time = DateTimeField(verbose_name = "最后修改时间", default = datetime.datetime.now)
    budget_status = StringField(verbose_name = '日限额状态', choices = STATUS_BUDGET_CHOICES, default = '0')
    opar_status = IntField(verbose_name = "CRM操作状态", choices = OPAR_STATUS_CHOICES, default = 0)
    # rt_limit_price = IntField(verbose_name = "实时优化限价")
    # rt_date = DateTimeField(verbose_name = "实时优化时间")
    # 报表数据
    # rpt_list = ListField(verbose_name = "计划报表列表", field = EmbeddedDocumentField(Report), default = [])
    msg_status = StringField(verbose_name = "消息状态", default = None) # 格式为 1_2 : 1条备注，2条留言
    # property
    # rpt_days = property(fget = get_rpt_days, fset = set_rpt_days)
    # rpt_date = property(fget = get_rpt_date)
    # rpt_date_list = property(fget = get_rpt_date_list)
    # rpt_yt = property(fget = get_rpt_yt)
    # rpt_sum = property(fget = get_rpt_sum)
    # snap_list = property(fget = get_snap_list)
    msg_count_list = property(fget = get_msg_count_list)
    note_count = property(fget = get_note_count) # 备注条数
    comment_count = property(fget = get_comment_count) # 留言条数
    set_msg_count = property(fget = save_msg_count)

    Parser = CampaignParser
    Report = CampaignRpt

    meta = {'collection':'subway_campaign', 'indexes':[], "shard_key":('shop_id',), }

    @property
    def tapi(self):
        if not hasattr(self, '_tapi'):
            self._tapi = get_tapi(shop_id = self.shop_id)
        return self._tapi

    @property
    def platform(self):
        '''投放平台'''
        if not hasattr(self, '_platform'):
            platform = CacheAdpter.get(CacheKey.WEB_CAMPAIGN_PLATFORM % self.campaign_id, 'web', None)
            if not platform:
                platform = {'pc_insite_search':1, 'pc_insite_nonsearch':0,
                            'pc_outsite_search':0, 'pc_outsite_nonsearch':0,
                            'yd_insite':0, 'yd_outsite':0,
                            'outside_discount':100, 'mobile_discount':100
                            }
                top_platform = None
                if self.tapi:
                    try:
                        top_platform = self.tapi.simba_campaign_platform_get(campaign_id = self.campaign_id)
                    except TopError, e:
                        log.error('get campaign platform error, shop_id=%s, campaign_id=%s, e=%s' % (self.shop_id, self.campaign_id, e))
                if top_platform and hasattr(top_platform, 'campaign_platform'):
                    pf = top_platform.campaign_platform
                    platform['outside_discount'] = pf.outside_discount
                    platform['mobile_discount'] = pf.mobile_discount
                    if hasattr(pf.nonsearch_channels, 'number'):
                        if 1 in pf.nonsearch_channels.number:
                            platform['pc_insite_nonsearch'] = 1
                        if 2 in pf.nonsearch_channels.number:
                            platform['pc_outsite_nonsearch'] = 1
                        if 8 in pf.nonsearch_channels.number:
                            platform['yd_insite'] = 1
                        if 16 in pf.nonsearch_channels.number:
                            platform['yd_outsite'] = 1
                    if hasattr(pf.search_channels, 'number'):
                        if 2 in pf.search_channels.number:
                            platform['pc_outsite_search'] = 1
                        if 8 in pf.search_channels.number:
                            platform['yd_insite'] = 1
                        if 16 in pf.search_channels.number:
                            platform['yd_outsite'] = 1
                CacheAdpter.set(CacheKey.WEB_CAMPAIGN_PLATFORM % self.campaign_id, platform, 'web', 60 * 30)
            self._platform = platform
        return self._platform

    @platform.setter
    def platform(self, value):
        self._platform = value

    @property
    def area(self):
        '''投放地域'''
        if not hasattr(self, '_area'):
            self._area = CacheAdpter.get(CacheKey.WEB_CAMPAIGN_AREA % self.campaign_id, 'web', None)
            if not self._area:
                try:
                    top_area = self.tapi.simba_campaign_area_get(campaign_id = self.campaign_id)
                except TopError, e:
                    log.error('get campaign area error, shop_id=%s, campaign_id=%s, e=%s' % (self.shop_id, self.campaign_id, e))
                    top_area = None
                if top_area and hasattr(top_area, 'campaign_area'):
                    self._area = top_area.campaign_area.area
                    CacheAdpter.set(CacheKey.WEB_CAMPAIGN_AREA % self.campaign_id, self._area, 'web', 60 * 30)
        return self._area

    @area.setter
    def area(self, value):
        self._area = value

    @property
    def schedule(self):
        '''分时折扣'''
        if not hasattr(self, '_schedule'):
            schedule = CacheAdpter.get(CacheKey.WEB_CAMPAIGN_SCHEDULE % self.campaign_id, 'web', None)
            if not schedule:
                try:
                    top_schedule = self.tapi.simba_campaign_schedule_get(campaign_id = self.campaign_id)
                except TopError, e:
                    log.error('get campaign schedule error, shop_id=%s, campaign_id=%s, e=%s' % (self.shop_id, self.campaign_id, e))
                    top_schedule = None
                if top_schedule and hasattr(top_schedule, 'campaign_schedule'):
                    schedule = top_schedule.campaign_schedule.schedule
                    CacheAdpter.set(CacheKey.WEB_CAMPAIGN_SCHEDULE % self.campaign_id, schedule, 'web', 60 * 30)
                else:
                    self._schedule = ''
            self._schedule = schedule
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        self._schedule = value

    @staticmethod
    def update_campaign_inner(shop_id, campaign_id, tapi, opter, opter_name, **para):
        result_list, msg_list, record_list = [], [], []
        try:
            campaign = Campaign.objects.get(shop_id = shop_id, campaign_id = campaign_id)
        except DoesNotExist:
            log.error('campaign not found, campaign_id = %s' % campaign_id)
            return [], ['计划不存在'], []

        if para.has_key('title') or para.has_key('online_status'):
            oper_name = '修改计划名称或状态'
            new_title = para.get('title', campaign.title)
            new_online_status = para.get('online_status', campaign.online_status)
            try:
                tapi.simba_campaign_update(campaign_id = campaign.campaign_id, title = new_title, online_status = new_online_status)
            except TopError, e:
                log.error('simba_campaign_update TopError, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败：%s' % (oper_name, e.humanized_reason))
            except Exception, e:
                log.error('simba_campaign_update Error, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败：%s' % (oper_name, humanize_exception(e)))
            else:
                result_list.extend(['title', 'online_status'])
                if new_title != campaign.title:
                    detail_list = ['将计划标题 %s 修改为 %s ' % (campaign.title, new_title)]
                    record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':102, 'opter':opter, 'opter_name': opter_name})
                    campaign.title = new_title
                if new_online_status != campaign.online_status:
                    detail_list = ['将计划%s推广' % (new_online_status == 'online' and '参与' or '暂停')]
                    record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':101, 'opter':opter, 'opter_name': opter_name})
                    campaign.online_status = new_online_status
                campaign.save()

        if para.has_key('budget'):
            oper_name = '修改计划日限额'
            old_budget = campaign.budget / 100
            old_smooth = campaign.is_smooth
            old_budget_descr = campaign.budget == 2000000000 and '不限' or ('%s元' % old_budget) # 数据库保存的预算单位是分
            try:
                use_smooth = para.get('use_smooth', 'true')
                is_smooth = use_smooth == 'true' and True or False
                if old_budget != para['budget'] or old_smooth != is_smooth:
                    if para['budget'] != 20000000: # 设置日限额
                        tapi.simba_campaign_budget_update(campaign_id = campaign.campaign_id, budget = para['budget'], use_smooth = use_smooth)
                        campaign.budget = int(para['budget']) * 100 # API调用中预算单位是元，数据库保存的是分
                        campaign.is_smooth = is_smooth
                        detail_list = ['将计划限额调由%s调整为%s元' % (old_budget_descr, para['budget'])]
                        record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':103, 'opter':opter, 'opter_name': opter_name})
                    else: # 取消设置日限额
                        use_smooth = 'false'
                        tapi.simba_campaign_budget_update(campaign_id = campaign.campaign_id, use_smooth = use_smooth)
                        campaign.budget = 2000000000
                        campaign.is_smooth = False
                        detail_list = ['计划限额由%s调整为不限' % old_budget_descr]
                        record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list':detail_list, 'op_type':1, 'data_type':103, 'opter':opter, 'opter_name': opter_name})
            except TopError, e:
                log.error('simba_campaign_budget_update TopError, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败:%s' % (oper_name, e.humanized_reason))
            except Exception, e:
                log.error('simba_campaign_budget_update Error, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败:%s' % (oper_name, humanize_exception(e)))
            else:
                result_list.append('budget')
                campaign.save()

        if para.has_key('area'):
            oper_name = '修改计划投放地域'
            try:
                tapi.simba_campaign_area_update(campaign_id = campaign.campaign_id, area = para['area'])
            except TopError, e:
                log.error('simba_campaign_area_update TopError, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败:%s' % (oper_name, e.humanized_reason))
            except Exception, e:
                log.error('simba_campaign_area_update Error, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败:%s' % (oper_name, humanize_exception(e)))
            else:
                result_list.append('area')
                if para.has_key('area_names'):
                    detail_list = ['修改计划投放地域为:%s' % para['area_names'][0:-1]]
                    record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list':detail_list, 'op_type':1, 'data_type':106, 'opter':opter, 'opter_name': opter_name})
                CacheAdpter.delete(CacheKey.WEB_CAMPAIGN_AREA % campaign_id, 'web')
                campaign.save()

        if para.has_key('schedule'):
            oper_name = '修改计划分时折扣'
            try:
                tapi.simba_campaign_schedule_update(campaign_id = campaign.campaign_id, schedule = para['schedule'])
            except TopError, e:
                log.error('simba_campaign_schedule_update TopError, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败:%s' % (oper_name, e.humanized_reason))
            except Exception, e:
                log.error('simba_campaign_schedule_update Error, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败:%s' % (oper_name, humanize_exception(e)))
            else:
                result_list.append('schedule')
                list1 = para['schedule'].split(';')
                descr_all = ''
                week_dict = {0:'星期一', 1:'星期二', 2:'星期三', 3:'星期四', 4:'星期五', 5:'星期六', 6:'星期天'}
                for idx1, item1 in enumerate(list1):
                    descr_all += ' %s:' % week_dict[idx1]
                    list2 = item1.split(',')
                    count = len(list2) - 1
                    for idx2, item2 in enumerate(list2):
                        if idx1 == 6 and idx2 == count:
                            descr_all += item2 + '%'
                        else:
                            descr_all += item2 + '%,'
                detail_list = ['修改计划分时折扣为:%s' % descr_all]
                record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list':detail_list, 'op_type':1, 'data_type':105, 'opter':opter, 'opter_name': opter_name})
                CacheAdpter.delete(CacheKey.WEB_CAMPAIGN_SCHEDULE % campaign_id, 'web')

        if para.has_key('search_channels') or para.has_key('nonsearch_channels') or para.has_key('outside_discount') or para.has_key('mobile_discount'):
            oper_name = '修改计划平台设置'
            search_channels = para.get('search_channels', '1,2,4')
            nonsearch_channels = para.get('nonsearch_channels', '') # 可选参数，有该参数则数值不能为空
            outside_discount = para.get('outside_discount', 100)
            mobile_discount = para.get('mobile_discount', 100)
            try:
                search_descr = search_channels.replace('16', '移动站外搜索开启').replace('8', '移动站内搜索开启').replace(',4', '').replace('2', 'PC站外搜索开启').replace('1', 'PC站内搜索开启')
                if not nonsearch_channels:
                    tapi.simba_campaign_platform_update(campaign_id = campaign.campaign_id, search_channels = search_channels, outside_discount = outside_discount, mobile_discount = mobile_discount)
                    detail_list = ['修改计划平台设置 :%s,站外折扣%s%%,移动端折扣%s%%' % (search_descr, outside_discount, mobile_discount)]
                    record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':104, 'opter':opter, 'opter_name': opter_name})
                else:
                    tapi.simba_campaign_platform_update(campaign_id = campaign.campaign_id, search_channels = search_channels, nonsearch_channels = nonsearch_channels, outside_discount = outside_discount, mobile_discount = mobile_discount)
                    nonsearch_descr = nonsearch_channels.replace('16', '移动站外定向开启').replace('8', '移动站内定向开启').replace('2', 'PC站外定向开启').replace('1', 'PC站内定向开启')
                    detail_list = ['修改计划平台设置 :%s,%s,站外折扣%s%%,移动端折扣%s%%' % (search_descr, nonsearch_descr, outside_discount, mobile_discount)]
                    record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':104, 'opter':opter, 'opter_name': opter_name})
            except TopError, e:
                log.error('simba_campaign_platform_update TopError, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败:%s' % (oper_name, e.humanized_reason))
            except Exception, e:
                log.error('simba_campaign_platform_update Error, shop_id = %s, error = %s' % (shop_id, e))
                msg_list.append('%s失败:%s' % (oper_name, humanize_exception(e)))
            else:
                result_list.extend(['search_channels', 'nonsearch_channels', 'outside_discount', 'mobile_discount'])
                CacheAdpter.delete(CacheKey.WEB_CAMPAIGN_PLATFORM % campaign_id, 'web')

        if para.has_key('mnt_status'):
            if para['mnt_status']:
                detail_list = ['开启自动托管']
                record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':107, 'opter':opter, 'opter_name': opter_name})
            else:
                detail_list = ['取消自动托管']
                record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':108, 'opter':opter, 'opter_name': opter_name})

        # 长尾计划开启时对计划设置限价
        if para.has_key('max_price') and para.has_key('mobile_max_price'):
            detail_list = ['设置PC端限价为:%.2f元，移动端限价为:%.2f元' % (para['max_price'] / 100.0, para['mobile_max_price'] / 100.0)]
            record_list.append({'shop_id':shop_id, 'campaign_id':campaign_id, 'detail_list': detail_list, 'op_type':1, 'data_type':110, 'opter':opter, 'opter_name': opter_name})

        return result_list, msg_list, record_list

    @classmethod
    def struct_download(cls, shop_id, tapi, sync_budget = True):
        """同步campaign"""
        try:
            exist_camp_id_list = [camp['_id'] for camp in camp_coll.find({'shop_id':shop_id}, {'_id':1})]
            new_camp_list, changed_camp_dict = [], {}
            tobj_campaign = tapi.simba_campaigns_get()
            if tobj_campaign and hasattr(tobj_campaign, 'campaigns') and tobj_campaign.campaigns:
                for camp in tobj_campaign.campaigns.campaign:
                    temp_dict = {}
                    if sync_budget:
                        top_budget = tapi.simba_campaign_budget_get(campaign_id = camp.campaign_id)
                        if top_budget and hasattr(top_budget, 'campaign_budget'):
                            temp_dict = {'budget':top_budget.campaign_budget.budget * 100, 'is_smooth':top_budget.campaign_budget.is_smooth}
                    if camp.campaign_id in exist_camp_id_list:
                        temp_dict.update(cls.Parser.parse(camp, trans_type = 'inc'))
                        changed_camp_dict.update({camp.campaign_id:temp_dict})
                    else:
                        temp_result_dict = cls.Parser.parse(camp, trans_type = "init", extra_dict = {'shop_id': shop_id})
                        temp_result_dict.update(temp_dict)
                        new_camp_list.append(temp_result_dict)

            if new_camp_list:
                camp_coll.insert(new_camp_list)
            if changed_camp_dict:
                for camp_id, camp_value in changed_camp_dict.items():
                    camp_coll.update({'_id':camp_id}, {'$set':camp_value})

            log.info('sync campaign OK, shop_id = %s' % shop_id)
            return True
        except Exception, e:
            log.error('sync campaign ERROR, shop_id = %s, e = %s' % (shop_id, e))
            return False

    @classmethod
    def increase_download(cls, shop_id, tapi, last_sync_time):
        # 判断上次更新时间是否是今天，如果不是今天则进行同步预算
        return cls.struct_download(shop_id = shop_id, tapi = tapi, sync_budget = (not time_is_someday(last_sync_time)) and True or False)

    @classmethod
    def download_camp_bycampids(cls, shop_id, camp_id_list, tapi, token, time_scope):
        result_flag = 'FAILED'
        try:
            rpt_list = []
            for search_type, source in cls.Report.REPORT_CFG:
                for camp_id in camp_id_list :
                    top_base_objs = tapi.simba_rpt_campaignbase_get(campaign_id = camp_id, start_time = time_scope[0], end_time = time_scope[1], search_type = search_type, source = source, subway_token = token, retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
                    if top_base_objs and hasattr(top_base_objs, 'rpt_campaign_base_list') and top_base_objs.rpt_campaign_base_list:
                        base_dict, effect_dict = {}, {}
                        for base in top_base_objs.rpt_campaign_base_list:
                            base_dict.update(cls.Report.parse_rpt(base, 'base'))

                        top_effect_objs = tapi.simba_rpt_campaigneffect_get(campaign_id = camp_id, start_time = time_scope[0], end_time = time_scope[1], search_type = search_type, source = source, subway_token = token, retry_count = settings.TAPI_RETRY_COUNT * 4, retry_delay = 1)
                        if top_effect_objs and hasattr(top_effect_objs, 'rpt_campaign_effect_list') and top_effect_objs.rpt_campaign_effect_list:
                            for effect in top_effect_objs.rpt_campaign_effect_list:
                                effect_dict.update(cls.Report.parse_rpt(effect, 'effect'))

                        if base_dict:
                            rpt_list.extend(cls.Report.merge_rpt_dict(base_dict, effect_dict, {'shop_id': shop_id, 'campaign_id': camp_id}))

            if rpt_list:
                remove_query = {'shop_id': shop_id, 'campaign_id': {'$in': camp_id_list}, 'date': {'$lte':date_2datetime(time_scope[1]), '$gte':date_2datetime(time_scope[0])}}
                cls.Report.update_rpt_list(remove_query, rpt_list)
                result_flag = 'OK'
            else:
                result_flag = 'EMPTY'
            log.info('download campaign rpt OK, shop_id = %s, camp_list = %s' % (shop_id, camp_id_list))
        except Exception, e:
            log.error('download campaign rpt FAILED, shop_id = %s, e = %s' % (shop_id, e))
        return result_flag

    @classmethod
    def report_download(cls, shop_id, tapi, token, time_scope):
        camp_id_list = [int(camp['_id']) for camp in camp_coll.find({'shop_id':shop_id}, {'_id':1})]
        return cls.download_camp_bycampids(shop_id, camp_id_list, tapi, token, time_scope)

    def get_snap_list(self, **kwargs):
        rpt_dict = self.Report.get_snap_list({'shop_id': self.shop_id, 'campaign_id': self.campaign_id}, **kwargs)
        return rpt_dict.get(self.campaign_id, [])

    def get_summed_rpt(self, **kwargs):
        rpt_dict = self.Report.get_summed_rpt({'shop_id': self.shop_id, 'campaign_id': self.campaign_id}, **kwargs)
        return rpt_dict.get(self.campaign_id, self.Report())

    def error_descr(self):
        if not hasattr(self, '_error_descr'):
            descr = ""
            if self.settle_status == "offline":
                descr = "计划强制下线"
                if self.settle_reason:
                    if "1" in self.settle_reason:
                        descr = "账户余额不足"
                    elif "2" in self.settle_reason:
                        descr = "达到日限额"
                    elif "3" in self.settle_reason:
                        descr = "不在投放时间"
            self._error_descr = descr
        return self._error_descr
    error_descr = property(fget = error_descr)

    @staticmethod
    def fromat_platform(pt_dict):
        search_list = ['1']
        nonsearch_list = []
        if int(pt_dict.get('pc_insite_nonsearch', 0)):
            nonsearch_list.append('1')
        if int(pt_dict.get('pc_outsite_search', 0)):
            search_list.extend(['2', '4'])
        if int(pt_dict.get('pc_outsite_nonsearch', 0)):
            nonsearch_list.append('2')
        if int(pt_dict.get('yd_insite', 0)):
            search_list.append('8')
            if int(pt_dict.get('pc_insite_nonsearch', 0)):
                nonsearch_list.append('8')
        if int(pt_dict.get('yd_outsite', 0)):
            search_list.append('16')
            if int(pt_dict.get('pc_outsite_nonsearch', 0)):
                nonsearch_list.append('16')

        result_dict = {'mobile_discount': 100}
        result_dict['search_channels'] = ','.join(search_list)
        if nonsearch_list:
            result_dict['nonsearch_channels'] = ','.join(nonsearch_list)
        result_dict['outside_discount'] = pt_dict.get('outside_discount', 100)
        result_dict['mobile_discount'] = pt_dict.get('mobile_discount', 100)
        return result_dict

camp_coll = Campaign._get_collection()
