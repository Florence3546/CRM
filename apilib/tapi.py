# coding=UTF-8
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

import mimetypes
import os

from apilib.binder import bind_api
from apilib.error import TopError
from apilib.parsers import TopObjectParser
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey


class TAPI(object):
    def __init__(self, auth_handler = None,
            host = 'gw.api.taobao.com', api_root = '/router/rest', # API_URL = 'http://gw.api.tbsandbox.com/router/rest',API_URL = 'http://gw.api.taobao.com/router/rest '
            cache = None, secure = False,
            retry_count = 0, retry_delay = 0, retry_errors = None,
            parser = None, log = None, timeout = None, is_quick_send = False):
        self.auth = auth_handler
        self.host = host
        self.api_root = api_root
        self.cache = cache
        self.secure = secure
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.retry_errors = retry_errors
        self.parser = parser or TopObjectParser()
        self.log = log
        self.timeout = timeout
        self.is_quick_send = is_quick_send
    # 用户相关接口
    user_get = bind_api(
        method_name = 'taobao.user.get',
    )
    # 查询用户卖家信息
    user_seller_get = bind_api(
        method_name = 'taobao.user.seller.get'
    )
    sellercenter_subusers_get = bind_api(
        method_name = 'taobao.sellercenter.subusers.get',
    )
    traderates_get = bind_api(
        method_name = 'taobao.traderates.get',
    )

    # 订购关系相关接口
    vas_order_search = bind_api(
        method_name = 'taobao.vas.order.search',
    )
    vas_subscribe_get = bind_api(
        method_name = 'taobao.vas.subscribe.get',
    )
    vas_subsc_search = bind_api(
        method_name = 'taobao.vas.subsc.search',
    )

    # 服务平台相关接口
    fuwu_sale_link_gen = bind_api(
        method_name = 'taobao.fuwu.sale.link.gen',
    )
    fuwu_sale_scores_get = bind_api(
        method_name = 'taobao.fuwu.scores.get',
    )

    # 店铺结构相关接口
    shop_get = bind_api(
        method_name = 'taobao.shop.get',
    )
    taobaoke_shops_get = bind_api(
        method_name = 'taobao.taobaoke.shops.get',
    )

    # 淘宝商品函数
    item_get = bind_api(
        method_name = 'taobao.item.get',
    )
    item_seller_get = bind_api(
        method_name = 'taobao.item.seller.get',
    )
    item_update = bind_api(
        method_name = 'taobao.item.update',
    )
    itemcats_get = bind_api(
        method_name = 'taobao.itemcats.get',
    )
    itemprops_get = bind_api(
        method_name = 'taobao.itemprops.get',
    )
    itempropvalues_get = bind_api(
        method_name = 'taobao.itempropvalues.get',
    )
    items_list_get = bind_api(
        method_name = 'taobao.items.list.get',
    )
    items_seller_list_get = bind_api(
        method_name = 'taobao.items.seller.list.get',
    )
    items_onsale_get = bind_api(
       method_name = 'taobao.items.onsale.get'
    )
    sellercats_list_get = bind_api(
        method_name = 'taobao.sellercats.list.get',
    )
    sellercats_list_add = bind_api(
        method_name = 'taobao.sellercats.list.add',
        method = 'POST',
        require_auth = True
    )
    sellercats_list_update = bind_api(
        method_name = 'taobao.sellercats.list.update',
        method = 'POST',
        require_auth = True
    )
    trades_sold_get = bind_api(
        method_name = 'taobao.trades.sold.get',
    )
    trades_sold_increment_get = bind_api(
        method_name = 'taobao.trades.sold.increment.get',
    )
    topats_result_get = bind_api(
        method_name = 'taobao.topats.result.get',
    )


    '''
    taobao.simba.campaigns.get #取得一组推广计划
    taobao.simba.campaign.add #创建一个推广计划
    taobao.simba.campaign.update #更新一个推广计划
    taobao.simba.campaign.area.get #取得一个推广计划的投放地域设置
    taobao.simba.campaign.area.update #更新一个推广计划的投放地域
    taobao.simba.campaign.areaoptions.get #取得推广计划的可设置投放地域列表
    taobao.simba.campaign.budget.get #取得一个推广计划的日限额
    taobao.simba.campaign.budget.update #更新一个推广计划的日限额
    taobao.simba.campaign.platform.get #取得一个推广计划的投放平台设置
    taobao.simba.campaign.platform.update #更新一个推广计划的平台设置
    taobao.simba.campaign.schedule.get #取得一个推广计划的分时折扣设置
    taobao.simba.campaign.schedule.update #更新一个推广计划的分时折扣设置
    taobao.simba.campaign.channeloptions.get #取得推广计划的可设置投放频道列表
    '''
    # 直通车推广计划相关接口
    simba_campaigns_get = bind_api(# 取得一组推广计划
        method_name = 'taobao.simba.campaigns.get',
    )
    simba_campaign_add = bind_api(# 创建一个推广计划
        method_name = 'taobao.simba.campaign.add',
    )
    simba_campaign_update = bind_api(# 更新一个推广计划
        method_name = 'taobao.simba.campaign.update',
    )
    simba_campaign_area_get = bind_api(# 取得一个推广计划的投放地域设置
        method_name = 'taobao.simba.campaign.area.get',
    )
    simba_campaign_area_update = bind_api(# 更新一个推广计划的投放地域
        method_name = 'taobao.simba.campaign.area.update',
    )
    simba_campaign_areaoptions_get = bind_api(# 取得推广计划的可设置投放地域列表
        method_name = 'taobao.simba.campaign.areaoptions.get',
    )
    simba_campaign_budget_get = bind_api(# 取得一个推广计划的日限额
        method_name = 'taobao.simba.campaign.budget.get',
    )
    simba_campaign_budget_update = bind_api(# 更新一个推广计划的日限额
        method_name = 'taobao.simba.campaign.budget.update',
    )
    simba_campaign_platform_get = bind_api(# 取得一个推广计划的投放平台设置
        method_name = 'taobao.simba.campaign.platform.get',
    )
    simba_campaign_platform_update = bind_api(# 更新一个推广计划的平台设置
        # search_channels = '1,2,4,8,16',  依次代表：站内搜索、站外搜索、【4未知】、移动站内搜索、移动站外搜索；其中1必须开(无线推广账户除外)；8与16之间互无依赖；参数必须且不可为空；
        # nonsearch_channels='1,2,8,16', 依次代表：站内定向、站外定向、移动站内定向、移动站外定向；其中2对1有依赖，开2必须开1，但也可以都不开；8与16之间互无依赖；参数非必须可不写，写则不能空；
        method_name = 'taobao.simba.campaign.platform.update',
    )
    simba_campaign_schedule_get = bind_api(# 取得一个推广计划的分时折扣设置
        method_name = 'taobao.simba.campaign.schedule.get',
    )
    simba_campaign_schedule_update = bind_api(# 更新一个推广计划的分时折扣设置
        method_name = 'taobao.simba.campaign.schedule.update',
    )
    simba_campaign_channeloptions_get = bind_api(# 取得推广计划的可设置投放频道列表
        method_name = 'taobao.simba.campaign.channeloptions.get',
    )


    '''
    taobao.simba.adgroup.add #创建一个推广组
    taobao.simba.adgroup.delete #删除一个推广宝贝
    taobao.simba.adgroup.update #更新一个推广宝贝
    taobao.simba.adgroupsbyadgroupids.get #批量得到推广宝贝
    taobao.simba.adgroupsbycampaignid.get #批量得到推广计划下的推广宝贝
    taobao.simba.adgroups.item.exist #商品是否推广
    taobao.simba.adgroupids.deleted.get #获取删除的推广宝贝ID
    taobao.simba.adgroups.changed.get #分页获取修改的推广宝贝ID和修改时间
    taobao.simba.adgroup.onlineitemsvon.get #获取用户上架在线销售的全部宝贝
    '''
    # 直通车宝贝相关接口
    simba_adgroup_add = bind_api(# 创建一个推广组
        method_name = 'taobao.simba.adgroup.add',
        method = 'POST'
    )
    simba_adgroup_delete = bind_api(# 删除一个推广组
        method_name = 'taobao.simba.adgroup.delete',
    )
    simba_adgroup_update = bind_api(# 更新一个推广宝贝
        method_name = 'taobao.simba.adgroup.update',
        method = 'POST'
    )
    simba_adgroupsbyadgroupids_get = bind_api(# 批量得到推广宝贝
        method_name = 'taobao.simba.adgroupsbyadgroupids.get',
    )
    simba_adgroupsbycampaignid_get = bind_api(# 批量得到推广计划下的推广宝贝
        method_name = 'taobao.simba.adgroupsbycampaignid.get',
    )
    simba_adgroups_item_exist = bind_api(# 商品是否推广
        method_name = 'taobao.simba.adgroups.item.exist',
    )
    simba_adgroupids_deleted_get = bind_api(# 获取删除的推广宝贝ID
        method_name = 'taobao.simba.adgroupids.deleted.get',
    )
    simba_adgroups_changed_get = bind_api(# 分页获取修改的推广宝贝ID和修改时间
        method_name = 'taobao.simba.adgroups.changed.get',
    )
    simba_adgroup_onlineitemsvon_get = bind_api(# 获取用户上架在线销售的全部宝贝
        method_name = 'taobao.simba.adgroup.onlineitemsvon.get',
    )


    '''
    taobao.simba.creatives.get #批量获得创意
    taobao.simba.creative.add #增加创意
    taobao.simba.creative.delete #删除创意
    taobao.simba.creative.update #修改创意
    taobao.simba.creativeids.deleted.get #获取删除的创意ID
    taobao.simba.creatives.changed.get #分页获取修改过的广告创意ID和修改时间
    taobao.simba.creatives.record.get #批量得到创意修改记录
    '''
    # 直通车创意相关接口
    simba_creatives_get = bind_api(# 批量获得创意
        method_name = 'taobao.simba.creatives.get',
    )
    simba_creative_add = bind_api(# 增加创意
        method_name = 'taobao.simba.creative.add',
    )
    simba_creative_delete = bind_api(# 删除创意
        method_name = 'taobao.simba.creative.delete',
    )
    simba_creative_update = bind_api(# 修改创意
        method_name = 'taobao.simba.creative.update',
    )
    simba_creativeids_deleted_get = bind_api(# 获取删除的创意ID
        method_name = 'taobao.simba.creativeids.deleted.get',
    )
    simba_creatives_changed_get = bind_api(# 分页获取修改过的广告创意ID和修改时间
        method_name = 'taobao.simba.creatives.changed.get',
    )
    simba_creatives_record_get = bind_api(# 批量得到创意修改记录
        method_name = 'taobao.simba.creatives.record.get',
    )


    '''
    taobao.simba.keywordsvon.add #创建一批关键词
    taobao.simba.keywords.delete #删除一批关键词
    taobao.simba.keywordsbykeywordids.get #取得一组关键词的信息
    taobao.simba.keywordsbyadgroupid.get #取得一个推广组的所有关键词
    taobao.simba.keywords.pricevon.set #设置一批关键词的出价
    taobao.simba.keywordscat.qscore.get #取得一个推广组的所有关键词的质量得分
    taobao.simba.keywords.recommend.get #取得一个推广组的推荐关键词列表
    taobao.simba.keywords.changed.get #分页获取修改过的关键词ID和修改时间
    taobao.simba.keywordids.deleted.get #获取删除的词ID
    taobao.simba.keyword.keywordforecast.get #获取词预估信息
    '''
    # 直通车关键词相关接口
    simba_keywordsvon_add = bind_api(# 创建一批关键词
        method_name = 'taobao.simba.keywordsvon.add',
        method = 'POST',
    )
    simba_keywords_delete = bind_api(# 删除一批关键词
        method_name = 'taobao.simba.keywords.delete',
    )
    simba_keywordsbykeywordids_get = bind_api(# 取得一组关键词的信息
        method_name = 'taobao.simba.keywordsbykeywordids.get',
    )
    simba_keywordsbyadgroupid_get = bind_api(# 取得一个推广组的所有关键词
        method_name = 'taobao.simba.keywordsbyadgroupid.get',
    )
    simba_keywords_pricevon_set = bind_api(# 设置一批关键词的出价
        method_name = 'taobao.simba.keywords.pricevon.set',
        method = 'POST',
    )
    simba_keywords_qscore_get = bind_api(# 取得一个推广组的所有关键词的质量得分,包括(rele_score,cvr_score,cust_score,creative_score)
        method_name = 'taobao.simba.keywords.qscore.get',
    )
    simba_keywordscat_qscore_get = bind_api(# 取得一个推广组的所有关键词的质量得分
        method_name = 'taobao.simba.keywordscat.qscore.get',
    )
    simba_keywords_recommend_get = bind_api(# 取得一个推广宝贝的推荐关键词列表
        method_name = 'taobao.simba.keywords.recommend.get',
    )
    simba_keywords_changed_get = bind_api(# 分页获取修改过的关键词ID和修改时间
        method_name = 'taobao.simba.keywords.changed.get',
    )
    simba_keywordids_deleted_get = bind_api(# 获取删除的词ID
        method_name = 'taobao.simba.keywordids.deleted.get',
    )
    simba_keyword_keywordforecast_get = bind_api(# 获取关键词预估信息
        method_name = 'taobao.simba.keyword.keywordforecast.get',
    )
    simba_keyword_rankingforecast_get = bind_api(# 获取关键词排名预估  测试阶段
        method_name = 'taobao.simba.keyword.rankingforecast.get',
    )


    '''
    taobao.simba.login.authsign.get #取得报表api调用签名，即登陆权限签名
    taobao.simba.rpt.custbase.get #取得账户报表基础数据对象
    taobao.simba.rpt.custeffect.get #取得账户报表效果数据查询(只有汇总数据，无分类数据)
    taobao.simba.rpt.campaignbase.get #推广计划报表基础数据对象
    taobao.simba.rpt.campaigneffect.get #推广计划效果报表数据对象
    taobao.simba.rpt.campadgroupbase.get #推广计划下的推广组报表基础数据查询(只有汇总数据，无分类类型)
    taobao.simba.rpt.campadgroupeffect.get #推广计划下的推广组报表效果数据查询(只有汇总数据，无分类类型)
    taobao.simba.rpt.adgroupbase.get #推广组基础报表数据对象
    taobao.simba.rpt.adgroupeffect.get #推广组效果报表数据对象
    taobao.simba.rpt.adgroupcreativebase.get #推广组下创意报表基础数据查询(汇总数据，不分类型)
    taobao.simba.rpt.adgroupcreativeeffect.get #推广组下的创意报表效果数据查询(汇总数据，不分类型)
    taobao.simba.rpt.adgroupkeywordbase.get #推广组下的词基础报表数据查询(明细数据不分类型查询)
    taobao.simba.rpt.adgroupkeywordeffect.get #推广组下的词效果报表数据查询(明细数据不分类型查询)
    taobao.topats.simba.campkeywordbase.get #直通车推广计划下的词报表基础数据查询
    taobao.topats.simba.campkeywordeffect.get #推广计划下的词报表效果数据查询
    '''
    # 直通车报表数据接口
    simba_login_authsign_get = bind_api(# 取得报表api调用签名，即登陆权限签名
        method_name = 'taobao.simba.login.authsign.get',
    )
    simba_rpt_custbase_get = bind_api(# 取得账户报表基础数据
        method_name = 'taobao.simba.rpt.custbase.get',
    )
    simba_rpt_custeffect_get = bind_api(# 取得账户报表效果数据（只有汇总数据，无分类数据）
        method_name = 'taobao.simba.rpt.custeffect.get',
    )
    simba_rpt_campaignbase_get = bind_api(# 取得推广计划报表基础数据
        method_name = 'taobao.simba.rpt.campaignbase.get',
        field_mapping = {'searchtype':'search_type', 'campaignid':'campaign_id'}
    )
    simba_rpt_campaigneffect_get = bind_api(# 取得推广计划报表效果数据
        method_name = 'taobao.simba.rpt.campaigneffect.get',
        field_mapping = {'searchtype':'search_type', 'favitemcount':'favitemcount', 'favshopcount':'favshopcount'}
    )
    simba_rpt_campadgroupbase_get = bind_api(# 取得推广计划下的推广组报表基础数据(只有汇总数据，无分类类型)
        method_name = 'taobao.simba.rpt.campadgroupbase.get',
        field_mapping = {'searchtype':'search_type', 'campaignid':'campaign_id', 'adgroupid':'adgroup_id', 'avgpos':'avgpos'}
    )
    simba_rpt_campadgroupeffect_get = bind_api(# 取得推广计划下的推广组报表效果数据(只有汇总数据，无分类类型)
        method_name = 'taobao.simba.rpt.campadgroupeffect.get',
        field_mapping = {'searchtype':'search_type', 'adgroupid':'adgroup_id', 'favitemcount':'favitemcount', 'favshopcount':'favshopcount'}
    )
    simba_rpt_adgroupbase_get = bind_api(# 取得推广组报表基础数据
        method_name = 'taobao.simba.rpt.adgroupbase.get',
        field_mapping = {'searchtype':'search_type', 'campaignid':'campaign_id', 'adgroupid':'adgroup_id'}
    )
    simba_rpt_adgroupeffect_get = bind_api(# 取得推广组报表效果数据
        method_name = 'taobao.simba.rpt.adgroupeffect.get',
        field_mapping = {'searchtype':'search_type', 'adgroupid':'adgroup_id', 'favitemcount':'favitemcount', 'favshopcount':'favshopcount'}
    )
    simba_rpt_adgroupcreativebase_get = bind_api(# 推广组下的创意报表基础数据(汇总数据，不分类型)
        method_name = 'taobao.simba.rpt.adgroupcreativebase.get',
        field_mapping = {'searchtype':'search_type', 'campaignid':'campaign_id', 'adgroupid':'adgroup_id', 'creativeid':'creative_id', 'avgpos':'avgpos'}
    )
    simba_rpt_adgroupcreativeeffect_get = bind_api(# 推广组下的创意报表效果数据(汇总数据，不分类型)
        method_name = 'taobao.simba.rpt.adgroupcreativeeffect.get',
        field_mapping = {'searchtype':'search_type', 'creativeid':'creative_id', 'favitemcount':'favitemcount', 'favshopcount':'favshopcount'}
    )
    simba_rpt_adgroupkeywordbase_get = bind_api(# 推广组下的关键词报表基础数据(明细数据不分类型查询)
        method_name = 'taobao.simba.rpt.adgroupkeywordbase.get',
        field_mapping = {'searchtype':'search_type', 'campaignid':'campaign_id', 'adgroupid':'adgroup_id', 'keywordid':'keyword_id'}
    )
    simba_rpt_adgroupkeywordeffect_get = bind_api(# 推广组下的关键词报表效果数据(明细数据不分类型查询)
        method_name = 'taobao.simba.rpt.adgroupkeywordeffect.get',
        field_mapping = {'searchtype':'search_type', 'keywordid':'keyword_id'}
    )
    topats_simba_campkeywordbase_get = bind_api(# 推广计划下的词报表基础数据查询
        method_name = 'taobao.topats.simba.campkeywordbase.get',
    )
    topats_simba_campkeywordeffect_get = bind_api(# 推广计划下的词报表效果数据查询
        method_name = 'taobao.topats.simba.campkeywordeffect.get',
    )


    '''
    taobao.simba.nonsearch.adgroupplaces.add #批量推广组添加定向推广投放位置
    taobao.simba.nonsearch.adgroupplaces.delete #批量删除推广组定向推广投放位置
    taobao.simba.nonsearch.adgroupplaces.get #根据指定推广计划下推广组列表获取相应推广组投放位置包括通投位置和单独出价位置
    taobao.simba.nonsearch.adgroupplaces.update #批量修改推广组定向推广投放位置价格
    taobao.simba.nonsearch.alldemographics.get #获取定向投放人群维度列表
    taobao.simba.nonsearch.allplaces.get #获取单独出价投放位置列表
    taobao.simba.nonsearch.demographics.get #获取给定campaign设置的投放人群维度列表
    taobao.simba.nonsearch.demographics.update #设置投放人群维度加价
    taobao.simba.adgroup.nonsearchprices.update #修改通投出价
    taobao.simba.adgroup.nonsearchstates.update #更改通投状态(暂停或启动)
    '''
    # 直通车定向推广接口
    simba_nonsearch_adgroupplaces_add = bind_api(# 批量推广组添加定向推广投放位置
        method_name = 'taobao.simba.nonsearch.adgroupplaces.add',
        method = 'POST'
    )
    simba_nonsearch_adgroupplaces_delete = bind_api(# 批量删除推广组定向推广投放位置
        method_name = 'taobao.simba.nonsearch.adgroupplaces.delete',
    )
    simba_nonsearch_adgroupplaces_get = bind_api(# 根据指定推广计划下推广组列表获取相应推广组投放位置包括通投位置和单独出价位置
        method_name = 'taobao.simba.nonsearch.adgroupplaces.get',
    )
    simba_nonsearch_adgroupplaces_update = bind_api(# 批量修改推广组定向推广投放位置价格
        method_name = 'taobao.simba.nonsearch.adgroupplaces.update',
        method = 'POST'
    )
    simba_nonsearch_alldemographics_get = bind_api(# 获取定向投放人群维度列表
        method_name = 'taobao.simba.nonsearch.alldemographics.get',
    )
    simba_nonsearch_allplaces_get = bind_api(# 获取单独出价投放位置列表
        method_name = 'taobao.simba.nonsearch.allplaces.get',
    )
    simba_nonsearch_demographics_get = bind_api(# 获取给定campaign设置的投放人群维度列表
        method_name = 'taobao.simba.nonsearch.demographics.get',
    )
    simba_nonsearch_demographics_update = bind_api(# 设置投放人群维度加价
        method_name = 'taobao.simba.nonsearch.demographics.update',
        method = 'POST'
    )
    simba_adgroup_nonsearchprices_update = bind_api(# 修改通投出价
        method_name = 'taobao.simba.adgroup.nonsearchprices.update',
        method = 'POST'
    )
    simba_adgroup_nonsearchstates_update = bind_api(# 更改通投状态(暂停或启动)
        method_name = 'taobao.simba.adgroup.nonsearchstates.update',
        method = 'POST'
    )


    '''
    taobao.simba.insight.cats.get #获取类目信息
    taobao.simba.insight.catsanalysis.get #类目分析数据查询
    taobao.simba.insight.catsbase.get #类目基础数据查询
    taobao.simba.insight.catsforecast.get #类目属性预测
    taobao.simba.insight.catsrelatedword.get #类目相关词查询
    taobao.simba.insight.catstopword.get #类目TOP词查询
    taobao.simba.insight.toplevelcats.get #获取全部类目
    taobao.simba.insight.wordsanalysis.get #词分析数据查询
    taobao.simba.insight.wordsbase.get #词基础数据查询
    taobao.simba.insight.wordscats.get #词和类目查询
    '''
    # 直通车insight接口
    simba_insight_cats_get = bind_api(# 获取类目信息
        method_name = 'taobao.simba.insight.cats.get',
        method = 'POST',
    )
    simba_insight_catsanalysis_get = bind_api(# 类目分析数据查询
        method_name = 'taobao.simba.insight.catsanalysis.get',
    )
    simba_insight_catsbase_get = bind_api(# 类目基础数据查询
        method_name = 'taobao.simba.insight.catsbase.get',
        method = 'POST',
    )
    simba_insight_catsforecast_get = bind_api(# 类目属性预测
        method_name = 'taobao.simba.insight.catsforecast.get',
        method = 'POST',
    )
    simba_insight_catsrelatedword_get = bind_api(# 类目相关词查询
        method_name = 'taobao.simba.insight.catsrelatedword.get',
    )
    simba_insight_catstopword_get = bind_api(# 类目TOP词查询
        method_name = 'taobao.simba.insight.catstopword.get',
    )
    simba_insight_toplevelcats_get = bind_api(# 获取全部类目
        method_name = 'taobao.simba.insight.toplevelcats.get',
        method = 'POST',
    )
    simba_insight_wordsanalysis_get = bind_api(# 词分析数据查询
        method_name = 'taobao.simba.insight.wordsanalysis.get',
    )
    simba_insight_wordsbase_get = bind_api(# 词基础数据查询
        method_name = 'taobao.simba.insight.wordsbase.get',
        method = 'POST',
    )
    simba_insight_wordscats_get = bind_api(# 词和类目查询
        method_name = 'taobao.simba.insight.wordscats.get',
        method = 'POST',
    )


    '''
    taobao.simba.account.balance.get #获取实时余额，单位为元
    taobao.simba.tools.items.top.get #取得一个关键词的推广宝贝排名列表
    taobao.simba.customers.authorized.get #取得当前登录用户的授权账户列表
    '''
    # 直通车账户、工具相关接口
    simba_account_balance_get = bind_api(# 获取实时余额，单位为元
        method_name = 'taobao.simba.account.balance.get',
    )
    simba_tools_items_top_get = bind_api(# 取得一个关键词的推广宝贝排名列表
        method_name = 'taobao.simba.tools.items.top.get',
    )
    simba_customers_authorized_get = bind_api(# 取得当前登录用户的授权账户列表
        method_name = 'taobao.simba.customers.authorized.get',
    )


    '''
    taobao.udp.target.search 查询指标数据
    taobao.udp.shop.get 店铺指标查询
    taobao.udp.item.get 商品指标查询
    '''
    # 淘宝UDP接口
    udp_target_search = bind_api(
        method_name = 'taobao.udp.target.search',
    )
    udp_shop_get = bind_api(
        method_name = 'taobao.udp.shop.get',
    )
    udp_item_get = bind_api(
        method_name = 'taobao.udp.item.get',
    )

    """聚石塔相关"""
    clouddata_mbp_data_get = bind_api(
        method_name = 'taobao.clouddata.mbp.data.get'
    )

    """20140901新增接口
    taobao.simba.insight.catsdata.get         获取类目的大盘数据
    taobao.simba.insight.catsforecastnew.get  获取词的相关类目预测数据
    taobao.simba.insight.catsinfo.get         类目信息获取
    taobao.simba.insight.catstopwordnew.get   获取类目下最热门的词
    taobao.simba.insight.catsworddata.get     获取类目下关键词的数据
    taobao.simba.insight.relatedwords.get     获取词的相关词
    taobao.simba.insight.wordsareadata.get    获取关键词按地域进行细分的数据
    taobao.simba.insight.wordsdata.get        获取关键词的大盘数据
    taobao.simba.insight.wordspricedata.get   关键词按竞价区间的分布数据
    taobao.simba.insight.wordssubdata.get     获取关键词按流量细分的数据
    """
    simba_insight_catsdata_get = bind_api(
        method_name = 'taobao.simba.insight.catsdata.get',
        method = 'POST'
    )
    simba_insight_catsforecastnew_get = bind_api(
        method_name = 'taobao.simba.insight.catsforecastnew.get',
        method = 'POST'
    )
    simba_insight_catsinfo_get = bind_api(
        method_name = 'taobao.simba.insight.catsinfo.get',
        method = 'POST'
    )
    simba_insight_catstopwordnew_get = bind_api(
        method_name = 'taobao.simba.insight.catstopwordnew.get',
        method = 'POST'
    )
    simba_insight_catsworddata_get = bind_api(
        method_name = 'taobao.simba.insight.catsworddata.get',
        method = 'POST'
    )
    simba_insight_relatedwords_get = bind_api(
        method_name = 'taobao.simba.insight.relatedwords.get',
        method = 'POST'
    )
    simba_insight_wordsareadata_get = bind_api(
        method_name = 'taobao.simba.insight.wordsareadata.get',
        method = 'POST'
    )
    simba_insight_wordsdata_get = bind_api(
        method_name = 'taobao.simba.insight.wordsdata.get',
        method = 'POST'
    )
    simba_insight_wordspricedata_get = bind_api(
        method_name = 'taobao.simba.insight.wordspricedata.get',
        method = 'POST'
    )
    simba_insight_wordssubdata_get = bind_api(
        method_name = 'taobao.simba.insight.wordssubdata.get',
        method = 'POST'
    )


    """20150623新增免费实时接口
    taobao.simba.rpt.targetingtageffect.get  免费获取定向效果报表数据
    taobao.simba.rpt.targetingtagbase.get    免费定向基础报表
    taobao.simba.rtrpt.creative.get          免费获取创意实时报表数据
    taobao.simba.rtrpt.campaign.get          免费获取推广计划实时报表数据
    taobao.simba.rtrpt.bidword.get           免费获取推广词实时报表数据
    taobao.simba.rtrpt.adgroup.get           免费获取推广组实时报表数据
    taobao.simba.rtrpt.cust.get              免费获取账户实时报表数据
    """
    simba_rpt_targetingtageffect_get = bind_api(
        method_name = 'taobao.simba.rpt.targetingtageffect.get',
        method = 'POST'
    )
    simba_rpt_targetingtagbase_get = bind_api(
        method_name = 'taobao.simba.rpt.targetingtagbase.get',
        method = 'POST'
    )
    simba_rtrpt_creative_get = bind_api(
        method_name = 'taobao.simba.rtrpt.creative.get',
        method = 'POST'
    )
    simba_rtrpt_campaign_get = bind_api(
        method_name = 'taobao.simba.rtrpt.campaign.get',
        method = 'POST'
    )
    simba_rtrpt_bidword_get = bind_api(
        method_name = 'taobao.simba.rtrpt.bidword.get',
        method = 'POST'
    )
    simba_rtrpt_adgroup_get = bind_api(
        method_name = 'taobao.simba.rtrpt.adgroup.get',
        method = 'POST'
    )
    simba_rtrpt_cust_get = bind_api(
        method_name = 'taobao.simba.rtrpt.cust.get',
        method = 'POST'
    )
    """
    .消息服务的api接口
    taobao.jushita.jms.user.add 添加ONS消息同步用户
    taobao.jushita.jms.user.get 删除ONS消息同步用户
    taobao.jushita.jms.user.delete 查询某个用户是否同步消息
    """
    simba_jshita_jms_user_add = bind_api(
        method_name = 'taobao.jushita.jms.user.add',
        method = 'POST'
    )
    simba_jshita_jms_user_delete = bind_api(
        method_name = 'taobao.jushita.jms.user.delete',
    )
    simba_jshita_jms_user_get = bind_api(
        method_name = 'taobao.jushita.jms.user.get',
    )

    """
    .天猫item维护新API,旧版的item接口将慢慢过度掉
    tmall.item.schema.add 天猫根据规则发布商品
    tmall.item.add.schema.get 天猫发布商品规则获取
    tmall.product.add.schema.get 产品发布规则获取接口
    tmall.product.match.schema.get 获取匹配产品规则
    tmall.product.schema.match product 匹配接口
    tmall.product.schema.add 使用Schema文件发布一个产品
    taobao.item.update.schema.get 商品编辑规则信息获取接口
    taobao.item.add.schema.get 商品发布规则信息获取接口
    taobao.item.schema.add 基于xml格式的商品发布api
    taobao.item.schema.update 新模式下的商品编辑接口
    tmall.product.update.schema.get 产品更新规则获取接口
    tmall.product.schema.update 产品更新接口
    tmall.item.schema.update 天猫根据规则编辑商品
    tmall.item.update.schema.get 天猫编辑商品规则获取
    tmall.product.schema.get 产品信息获取schema获取
    tmall.item.increment.update.schema.get 天猫增量更新商品规则获取
    tmall.item.schema.increment.update 天猫根据规则增量更新商品
    taobao.item.schema.increment.update 集市schema增量编辑
    taobao.item.increment.update.schema.get 获取增量更新规则
    tmall.item.outerid.update 天猫商品/SKU商家编码更新接口
    """
    simba_tmall_product_match_schema_get = bind_api(
        method_name = 'tmall.product.match.schema.get',
    )
    simba_tmall_item_schema_add = bind_api(
        method_name = 'tmall.item.schema.add',
    )
    simba_tmall_item_add_schema_get = bind_api(
        method_name = 'tmall.item.add.schema.get',
    )
    simba_tmall_product_schema_match = bind_api(
        method_name = 'tmall.product.schema.match product',
    )
    simba_tmall_product_schema_add = bind_api(
        method_name = 'tmall.product.schema.add',
    )
    simba_taobao_item_update_schema_get = bind_api(
        method_name = 'taobao.item.update.schema.get',
    )
    simba_taobao_item_schema_add = bind_api(
        method_name = 'taobao.item.schema.add',
    )
    simba_taobao_item_schema_update = bind_api(
        method_name = 'taobao.item.schema.update',
    )
    simba_tmall_product_update_schema_get = bind_api(
        method_name = 'tmall.product.update.schema.get',
    )
    simba_tmall_product_schema_update = bind_api(
        method_name = 'tmall.product.schema.update',
    )
    simba_tmall_item_schema_update = bind_api(
        method_name = 'tmall.item.schema.update',
    )
    simba_tmall_item_update_schema_get = bind_api(
        method_name = 'tmall.item.update.schema.get',
    )
    simba_tmall_product_schema_update = bind_api(
        method_name = 'tmall.product.schema.update',
    )
    simba_tmall_item_increment_update_schema_get = bind_api(
        method_name = 'tmall.item.increment.update.schema.get',
    )
    simba_tmall_item_schema_increment_update = bind_api(
        method_name = 'tmall.item.schema.increment.update',
    )
    simba_taobao_item_schema_increment_update = bind_api(
        method_name = 'taobao.item.schema.increment.update'
    )
    simba_taobao_item_increment_update_schema_get = bind_api(
        method_name = 'taobao.item.increment.update.schema.get',
    )
    simba_tmall_item_outerid_update = bind_api(
        method_name = 'tmall.item.outerid.update',
    )


    """
    taobao.item.img.upload         添加商品图片
    taobao.item.img.delete         删除商品图片
    taobao.item.propimg.upload
    """

    taobao_item_img_upload = bind_api(
        method_name = 'taobao.item.img.upload',
        method = 'POST',
        multi_para = 'image'
    )

    taobao_item_propimg_upload = bind_api(
        method_name = 'taobao.item.propimg.upload',
        method = 'POST',
        multi_para = 'image'
    )

    taobao_item_img_delete = bind_api(
        method_name = 'taobao.item.img.delete'
    )

    """
    taobao.picture.category.get    获取图片分类信息
    taobao.picture.category.add    新增图片分类信息
    taobao.picture.upload          上传单张图片
    """

    taobao_picture_category_get = bind_api(
        method_name = 'taobao.picture.category.get'
    )

    taobao_picture_category_add = bind_api(
        method_name = 'taobao.picture.category.add'
    )

    taobao_picture_upload = bind_api(
        method_name = 'taobao.picture.upload',
        method = 'POST',
        multi_para = 'img'
    )

    simba_keywords_qscore_split_get = bind_api(
        method_name = "taobao.simba.keywords.qscore.split.get"
    )

    simba_adgroup_mobilediscount_update = bind_api(
        method_name = 'taobao.simba.adgroup.mobilediscount.update'
    )

    simba_adgroup_mobilediscount_delete = bind_api(
        method_name = 'taobao.simba.adgroup.mobilediscount.delete'
    )

    """
    taobao.simba.keywords.realtime.ranking.get   获取词的实时排名
    """

    simba_keywords_realtime_ranking_get = bind_api(
        method_name = 'taobao.simba.keywords.realtime.ranking.get'
    )

    simba_keywords_realtime_ranking_batch_get = bind_api(
        method_name = 'taobao.simba.keywords.realtime.ranking.batch.get'
    )

    """
    .提供给军哥的接口
    """
    ump_promotion_get = bind_api(
        method_name = 'taobao.ump.promotion.get',
        method = 'POST'
    )

    """ statuses/upload """
    def upload_img(self, filename, status, lat = None, long = None, source = None):
        if source is None:
            source = self.source
        headers, post_data = TAPI._pack_image(filename, 1024, source = source, status = status, lat = lat, long = long, contentname = "pic")
        args = [status]
        allowed_param = ['status']

        if lat is not None:
            args.append(lat)
            allowed_param.append('lat')

        if long is not None:
            args.append(long)
            allowed_param.append('long')

        if source is not None:
            args.append(source)
            allowed_param.append('source')

        return bind_api(
            path = '/statuses/upload.json',
            method = 'POST',
            payload_type = 'status',
            require_auth = True,
            allowed_param = allowed_param
        )(self, post_data = post_data, headers = headers, *args)

    """ help/test """
    def test(self):
        try:
            bind_api(path = '/help/test.json',)(self)
        except TopError:
            return False
        return True

    """ Internal use only """
    @staticmethod
    def _pack_image(filename, max_size, source = None, status = None, lat = None, long = None, contentname = "image"):
        """Pack image from file into multipart-formdata post body"""
        # image must be less than 700kb in size
        try:
            if os.path.getsize(filename) > (max_size * 1024):
                raise TopError('File is too big, must be less than 700kb.')
        # except os.error, e:
        except os.error:
            raise TopError('Unable to access file')

        # image must be gif, jpeg, or png
        file_type = mimetypes.guess_type(filename)
        if file_type is None:
            raise TopError('Could not determine file type')
        file_type = file_type[0]
        if file_type not in ['image/gif', 'image/jpeg', 'image/png']:
            raise TopError('Invalid file type for image: %s' % file_type)

        # build the mulitpart-formdata body
        fp = open(filename, 'rb')
        BOUNDARY = 'Tw3ePy'
        body = []
        if status is not None:
            body.append('--' + BOUNDARY)
            body.append('Content-Disposition: form-data; name="status"')
            body.append('Content-Type: text/plain; charset=US-ASCII')
            body.append('Content-Transfer-Encoding: 8bit')
            body.append('')
            body.append(status)
        if source is not None:
            body.append('--' + BOUNDARY)
            body.append('Content-Disposition: form-data; name="source"')
            body.append('Content-Type: text/plain; charset=US-ASCII')
            body.append('Content-Transfer-Encoding: 8bit')
            body.append('')
            body.append(source)
        if lat is not None:
            body.append('--' + BOUNDARY)
            body.append('Content-Disposition: form-data; name="lat"')
            body.append('Content-Type: text/plain; charset=US-ASCII')
            body.append('Content-Transfer-Encoding: 8bit')
            body.append('')
            body.append(lat)
        if long is not None:
            body.append('--' + BOUNDARY)
            body.append('Content-Disposition: form-data; name="long"')
            body.append('Content-Type: text/plain; charset=US-ASCII')
            body.append('Content-Transfer-Encoding: 8bit')
            body.append('')
            body.append(long)
        body.append('--' + BOUNDARY)
        body.append('Content-Disposition: form-data; name="' + contentname + '"; filename="%s"' % filename)
        body.append('Content-Type: %s' % file_type)
        body.append('Content-Transfer-Encoding: binary')
        body.append('')
        body.append(fp.read())
        body.append('--' + BOUNDARY + '--')
        body.append('')
        fp.close()
        body.append('--' + BOUNDARY + '--')
        body.append('')
        body = '\r\n'.join(body)
        # build headers
        headers = {
            'Content-Type': 'multipart/form-data; boundary=Tw3ePy',
            'Content-Length': len(body)
        }
        return headers, body

    """ upload_tex """
    def upload_tex(self, result = '1', failed_reason = 0, shop_id = "", filename = "", fieldname = "data_file"):
        other_args = {'method':"upload_tex", 'result':result, 'shop_id':shop_id, 'failed_reason':failed_reason}
        headers, post_data = TAPI._pack_file(fieldname = fieldname, filename = filename, other_args = other_args)
        return bind_api(
            method_name = 'upload_tex',
            method = 'POST',
            is_ours = True,
        )(self, post_data = post_data, headers = headers)

    @staticmethod
    def _pack_file(fieldname = None, filename = None, other_args = {}, max_size = 1024 * 10):
        # build the mulitpart-formdata body
        BOUNDARY = 'Tw3ePy'
        body = []
        for k, v in other_args.items():
            body.append('--' + BOUNDARY)
            body.append('Content-Disposition: form-data; name="%s"' % (k))
            body.append('Content-Type: text/plain; charset=US-ASCII')
            body.append('Content-Transfer-Encoding: 8bit')
            body.append('')
            body.append(str(v))
        if filename:
            try:
                if max_size == -1:
                    pass
                elif os.path.getsize(filename) > (max_size * 1024):
                    raise TopError('File is too big, must be less than 10MB.')
            except os.error, e:
                raise TopError('Unable to access file, e=%s' % (e))

            file_type = mimetypes.guess_type(filename)
            file_type = file_type[0]
            if file_type is None:
                raise TopError('Could not determine file type')

            body.append('--' + BOUNDARY)
            body.append('Content-Disposition: form-data; name="' + fieldname + '"; filename="%s"' % filename)
            body.append('Content-Type: %s' % file_type)
            body.append('Content-Transfer-Encoding: binary')
            body.append('')
            fp = open(filename, 'rb')
            body.append(fp.read())
            fp.close()
            body.append('--' + BOUNDARY + '--')
            body.append('')
        body.append('--' + BOUNDARY + '--')
        body.append('')
        body = '\r\n'.join(body)
        # build headers
        headers = {
            'Content-Type': 'multipart/form-data; boundary=Tw3ePy',
            'Content-Length': len(body)
        }

        return headers, body

    def get_account_balance(self):
        """优先从memcache中读取"""
        session = self.auth.session_key
        if session:
            balance = CacheAdpter.get(CacheKey.NCRM_ACCOUNT_BALANCE % session, 'web', None)
            if balance is None:
                tobj_balance = self.simba_account_balance_get()
                CacheAdpter.set(CacheKey.NCRM_ACCOUNT_BALANCE % session, tobj_balance.balance, 'web', 60 * 5)
                return tobj_balance.balance
            else:
                return balance
        else:
            raise(Exception('缺少session'))