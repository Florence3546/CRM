# coding=UTF-8
import datetime
from apilib import get_tapi
from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.subway.models_report import ReportDictWrapper, BaseReport
from apps.subway.models_parser import RealtimeReportParser

# PureReport
class RealtimeReport():
    """实时报表"""

    Parser = RealtimeReportParser

    @classmethod
    def _summary_report(cls, rpt_list, source, search_type):
        source_list = [source]
        search_type_list = [search_type]
        if source == -1:
            source_list = [i for i, _ in BaseReport.SOURCE_TYPE_CHOICES]
        if search_type == -1:
            search_type_list = [i for i, _ in BaseReport.SEARCH_TYPE_CHOICES]
        new_rpt_list = [rpt for rpt in rpt_list if rpt.source in source_list and rpt.search_type in search_type_list]
        rpt = ReportDictWrapper.sum_rpt_list(new_rpt_list)
        rpt.source = source
        rpt.search_type = search_type
        return rpt

    @classmethod
    def _download_account_rtrpt(cls, shop_id, date):
        '''下载帐户实时实数'''
        rtrpt_dict = {}
        try:
            tapi = get_tapi(shop_id = shop_id)
            if tapi:
                top_result = tapi.simba_rtrpt_cust_get(the_date = date)
                if top_result and hasattr(top_result, 'results') and top_result.results \
                        and hasattr(top_result.results, 'rt_rpt_result_entity_d_t_o') \
                        and top_result.results.rt_rpt_result_entity_d_t_o:
                    top_rtrpt_obj = top_result.results.rt_rpt_result_entity_d_t_o[0]
                    top_rtrpt_obj.thedate = date.strftime(format = '%Y-%m-%d %H:%M:%S')
                    if top_rtrpt_obj:
                        rtrpt_dict[shop_id] = [cls.Parser.parse(top_rtrpt_obj)]
        except Exception, e:
            log.error('download shop realtime rpt FAILED, shop_id=%s, e=%s' % (shop_id, e))
        return rtrpt_dict

    @classmethod
    def _download_campaign_rtrpt(cls, shop_id, date):
        '''下载推广计划实时报表数据'''
        rtrpt_dict = {}
        try:
            tapi = get_tapi(shop_id = shop_id)
            if tapi:
                top_result = tapi.simba_rtrpt_campaign_get(the_date = date)
                if top_result and hasattr(top_result, 'resultss') and top_result.resultss \
                        and hasattr(top_result.resultss, 'rt_rpt_result_entity_d_t_o') \
                        and top_result.resultss.rt_rpt_result_entity_d_t_o:
                    for top_rtrpt_obj in top_result.resultss.rt_rpt_result_entity_d_t_o:
                        rtrpt_dict.setdefault(int(top_rtrpt_obj.campaignid), []).append(cls.Parser.parse(top_rtrpt_obj))
        except Exception, e:
            log.error('download camp realtime rpt FAILED, shop_id=%s, e=%s' % (shop_id, e))
        return rtrpt_dict

    @classmethod
    def _download_adgroup_rtrpt(cls, shop_id, campaign_id, date):
        '''下载推广宝贝实时报表数据'''
        rtrpt_dict = {}
        try:
            tapi = get_tapi(shop_id = shop_id)
            if tapi:
                top_result = tapi.simba_rtrpt_adgroup_get(the_date = date, campaign_id = campaign_id)
                if top_result and hasattr(top_result, 'results') and top_result.results \
                        and hasattr(top_result.results, 'rt_rpt_result_entity_d_t_o') \
                        and top_result.results.rt_rpt_result_entity_d_t_o:
                    for top_rtrpt_obj in top_result.results.rt_rpt_result_entity_d_t_o:
                        rtrpt_dict.setdefault(int(top_rtrpt_obj.adgroupid), []).append(cls.Parser.parse(top_rtrpt_obj))
        except Exception, e:
            log.error('download adg realtime rpt FAILED, shop_id=%s, camp_id=%s, e=%s' % (shop_id, campaign_id, e))
        return rtrpt_dict

    @classmethod
    def _download_keyword_rtrpt(cls, shop_id, campaign_id, adgroup_id, date):
        '''下载推广关键词实时报表数据'''
        rtrpt_dict = {}
        try:
            tapi = get_tapi(shop_id = shop_id)
            if tapi:
                top_result = tapi.simba_rtrpt_bidword_get(the_date = date, campaign_id = campaign_id, adgroup_id = adgroup_id)
                if top_result and hasattr(top_result, 'results') and top_result.results \
                        and hasattr(top_result.results, 'rt_rpt_result_entity_d_t_o') \
                        and top_result.results.rt_rpt_result_entity_d_t_o:
                    for top_rtrpt_obj in top_result.results.rt_rpt_result_entity_d_t_o:
                        rtrpt_dict.setdefault(int(top_rtrpt_obj.bidwordid), []).append(cls.Parser.parse(top_rtrpt_obj))
        except Exception, e:
            log.error('download kw realtime rpt FAILED, shop_id=%s, adg_id=%s, e=%s' % (shop_id, adgroup_id, e))
        return rtrpt_dict

    @classmethod
    def get_detail_rtrpt(cls, rpt_type, args_list, update_now = False, date = None):
        '''获取详细报表，包含每个平台的报表
        rpt_type 可选值：'account', 'campaign', 'adgroup', 'keyword'
        args_list 与 rpt_type 对应关系, rpt_type = 'account', args_list = [shop_id]
                                       rpt_type = 'campaign', args_list = [shop_id]
                                       rpt_type = 'adgroup', args_list = [shop_id, campaign_id]
                                       rpt_type = 'keyword', args_list = [shop_id, campaign_id, adgroup_id]
        '''

        config_dict = {'account': {'cachekey': CacheKey.SUBWAY_ACCOUNT_RTRPT, 'download_fun': '_download_account_rtrpt'},
                       'campaign': {'cachekey': CacheKey.SUBWAY_CAMPAIGN_RTRPT, 'download_fun': '_download_campaign_rtrpt'},
                       'adgroup': {'cachekey': CacheKey.SUBWAY_ADGROUP_RTRPT, 'download_fun': '_download_adgroup_rtrpt'},
                       'keyword': {'cachekey': CacheKey.SUBWAY_KEYWORD_RTRPT, 'download_fun': '_download_keyword_rtrpt'},
                       }

        # 从缓存或者淘宝api获取实时报表
        rtrpt_dict = {}
        config = config_dict.get(rpt_type, {})
        if not date:
            date = datetime.datetime.now()
        if config:
            cachekey = config['cachekey'] % (args_list[-1], date.date())
            rtrpt_dict = CacheAdpter.get(cachekey, 'default', 'nocache')
            if update_now or rtrpt_dict == 'nocache':
                rtrpt_dict = getattr(cls, config['download_fun'])(*args_list, date = date)
                CacheAdpter.set(cachekey, rtrpt_dict, 'default', 60 * 5)
        else:
            log.warn('has no this rpt_type, rpt_type=%s' % rpt_type)

        # 将从字典转换成 ReportDictWrapper 对象，方便页面调用
        result_rpt_dict = {}
        for k, rpt_list in rtrpt_dict.iteritems():
            result_rpt_dict[k] = [ReportDictWrapper(rpt) for rpt in rpt_list]
        return result_rpt_dict

    @classmethod
    def get_summed_rtrpt(cls, rpt_type, args_list, update_now = False, date = None, source = -1, search_type = -1):
        '''获取某个维度汇总的报表
        rpt_type 可选值：'account', 'campaign', 'adgroup', 'keyword'
        source, search_type 的可选值，参考BaseReport中该字段的chioces
        args_list 与 rpt_type 对应关系, rpt_type = 'account', args_list = [shop_id]
                                       rpt_type = 'campaign', args_list = [shop_id]
                                       rpt_type = 'adgroup', args_list = [shop_id, campaign_id]
                                       rpt_type = 'keyword', args_list = [shop_id, campaign_id, adgroup_id]
        '''
        result_dict = {}
        all_rtrpt_dict = cls.get_detail_rtrpt(rpt_type, args_list, update_now = update_now, date = date)
        for key_id, rpt_list in all_rtrpt_dict.iteritems():
            result_dict.update({key_id: cls._summary_report(rpt_list, source, search_type)})
        return result_dict

    @classmethod
    def get_split_rtrpt(cls, rpt_type, args_list, update_now = False, date = None):
        '''获取细分报表，一般计划列表、宝贝列表中用到
        rpt_type 可选值：'account', 'campaign', 'adgroup', 'keyword'
        args_list 与 rpt_type 对应关系, rpt_type = 'account', args_list = [shop_id]
                                       rpt_type = 'campaign', args_list = [shop_id]
                                       rpt_type = 'adgroup', args_list = [shop_id, campaign_id]
                                       rpt_type = 'keyword', args_list = [shop_id, campaign_id, adgroup_id]
        '''
        result_dict = {}
        source_list = [1, 2, 4, 5]
        all_rtrpt_dict = cls.get_detail_rtrpt(rpt_type, args_list, update_now = update_now, date = date)
        for key_id, rpt_list in all_rtrpt_dict.iteritems():
            temp_list = []
            for source in source_list:
                temp_list.append(cls._summary_report(rpt_list, source, search_type = -1))
            result_dict.update({key_id: temp_list})
        return result_dict

    @classmethod
    def _summary_platform_report(cls, rpt_list, platform):
        if platform == -1:
            source_list = [i for i, _ in BaseReport.SOURCE_TYPE_CHOICES]
        elif platform == 1:
            source_list = [1, 2]
        else:
            source_list = [4, 5]
        search_type_list = [i for i, _ in BaseReport.SEARCH_TYPE_CHOICES]
        new_rpt_list = [rpt for rpt in rpt_list if rpt.source in source_list and rpt.search_type in search_type_list]
        rpt = ReportDictWrapper.sum_rpt_list(new_rpt_list)
        rpt.avgpos = 0
        rpt.search_type = -1
        return rpt

    @classmethod
    def get_platformsum_rtrpt(cls, rpt_type, args_list, platform = -1):
        '''获取PC/YD或者全平台的 汇总的报表 platform 可选值：-1 全部， 0 移动， 1 PC.
        rpt_type 可选值：'account', 'campaign', 'adgroup', 'keyword'
        source, search_type 的可选值，参考BaseReport中该字段的chioces
        args_list 与 rpt_type 对应关系, rpt_type = 'account', args_list = [shop_id]
                                       rpt_type = 'campaign', args_list = [shop_id]
                                       rpt_type = 'adgroup', args_list = [shop_id, campaign_id]
                                       rpt_type = 'keyword', args_list = [shop_id, campaign_id, adgroup_id]
        '''
        result_dict = {}
        all_rtrpt_dict = cls.get_detail_rtrpt(rpt_type, args_list)
        for key_id, rpt_list in all_rtrpt_dict.iteritems():
            result_dict.update({key_id: cls._summary_platform_report(rpt_list, platform)})
        return result_dict
