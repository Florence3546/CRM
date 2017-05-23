# coding=utf-8

"""
虽然没有办法使用gevent来加速，但是这里还是想自己写一个

主要是为了更好的优化下载时候遇到流控必须要等待的逻辑。


### 更新想法

这里可以先不自己实现，先用原来的逻辑处理。


### 更新关于拆分的问题

db.adgroup_report.aggregate([
    {$match: {'shop_id': 63499260, 'adgroup_id': 467616872, 'search_type': {'$in': [0, -1]}}},
    {$group: {'_id': {'date':'$date', 'source': '$source'},
              'click': {'$sum': '$click'}
                }
    },
    {$project: {
      'date': '$_id.date',
      'source': '$_id.source',
      'click': '$click'
    }}
])
↑ 上面的aggregate可以尝试一下对于下载报表这一块的加速，通过一次查数据库，来确定接下来keyword应该下载哪些报表

1. 汇总的数据没有，则细分的数据肯定也没有  --任务依赖(任务分解前，看adgroup的报表及天数状态，看是否有对应的天数，是否有对应的细分数据)
2. base的数据没有，则effect的数据也肯定没有 --任务依赖时，如何处理？ <base, effect参数相同，放在一个任务里，如果有数据，则继续调用，否则不调用>
3. 计划未投放对应的细分时，则:站内&站外，PC&移动时，则相应的细分数据也肯定没有   -->生成任务的时候，就应该计算出任务参数，source_type没有想像中那么多（有问题，如果这些参数是2天前修改的，则2天前的数据实际上还是有的）


### 想法update 2016年6月27日

需要完成哪些工作量：

1. 完成下载负责人的逻辑，包括这些功能：
1.1 对推广组批量处理的逻辑，即最好是从多个adgroup生成任务
1.2 批量


### 一些缓存的key描述

任务队列： download:queue
任务结果的key列表  <adgroup_id>_<date>_<source>_<search_type>， 例如： 467616872_2016-06-27_SUMMARY_SUMMARY


"""
import time
import datetime
import collections

from apilib import get_tapi, TopError
from apps.common.utils.utils_log import log
from apps.common.utils.utils_collection import genr_sublist
from apps.subway.models_adgroup import Adgroup
from apps.subway.models_report import KeywordRpt
from apps.common.utils.utils_cacheadpter import CacheAdpter

from task_queue import DownloadRedisQueue, SlowerDownloadRedisQueue
from errors import DownloadFailed, WorkerFailed, WorkerTimeout


class DownloadContracter(object):

    TASK_QUEUE = DownloadRedisQueue

    def __init__(self, shop_id, campaign_id, adg_date_dict, token, end_date):
        """
        adg_date_list 形如： [{adgroup_id: datetime.datetime(2016, 6, 30)}, ...] 即每个Adgroup的关键词上次同步时间可能不一样
        """
        self.shop_id = shop_id
        self.campaign_id = campaign_id
        self.adg_date_dict = adg_date_dict
        self.token = token
        self.end_date = end_date
        self.cache_db = "download"
        self.parse_adg_date_dict()
        self.key_list = []
        self.task_list = []

    def __str__(self):
        return "DownloadContractor(shop_id=%s, camp_id=%s, adg_count=%s)" % (self.shop_id, self.campaign_id, len(self.adgroup_id_list))

    def parse_adg_date_dict(self):
        self.earliest_date = None # 这批广告组的关键词报表，上次同步时间最早的一个
        self.adgroup_id_list = []

        for adg_id, last_sync_time in self.adg_date_dict.items():
            if self.earliest_date:
                if last_sync_time < self.earliest_date:
                    self.earliest_date = last_sync_time
            else:
                self.earliest_date = last_sync_time
            self.adgroup_id_list.append(adg_id)

        # self.get_delta_days()
        # self.source_search_type_pair_list = [('SUMMARY', 'SUMMARY')] + [('SEARCH', source) for source in ['1', '2', '4', '5']]

    # def get_delta_days(self):
    #     self.date_list = []
    #     days = (self.end_date - self.start_date).days
    #     for i in range(days):
    #         self.date_list.append(self.start_date + datetime.timedelta(days = i))

    def conver_args(self, source_or_search_type): # 不建议这样写参数，这里只为了简单，但并不明确
        if source_or_search_type == -1:
            return 'SUMMARY'
        else:
            return source_or_search_type

    def generate_task(self):
        """有两种方式来拆分任务：
        1. 起止时间拆分、细分类型拆分
        2. 通过获取推广组的报表数据来拆分任务
        """
        query_dict = {'shop_id': self.shop_id, 'adgroup_id': {'$in': self.adgroup_id_list}}

        # 这里想要批量的话，实际上有一点不现实，因为需要从每个adgroup的关键词下载状态是不一样的，有一些推广组只需要下载最近两三天的关键词
        # 而有一些推广组则需要初始化，即需要下载最多15天的细分报表，这个就又麻烦了，当然呢，后者也可以根据(adgroup_id, campaign_id, last_date)来过滤掉对应的天数，实际上又浪费了这些数据库查询的参数了。
        # 这里需要批量下载时，会不会造成数据库较大压力呢，比如需要下载一个campaign下面所有的关键词报表，岂不是for循环然后每个都去数据库取了一次？

        # 1. 批量是必要的，要不然仍然是一个大循环，没有本质的改善
        # 2. 根据推广组的计划，分成几个计划来批量下载，这里用线性的循环，因为实际场景中，通常情况下都是下载单个计划的（下载全店关键词报表除外）、当然，这里也可以加速。
        # 3. 一个计划内，会找到一个最远的start_time（即这个start_time是数据库查询的基准，后面会根据每个推广组的上次同步时间再调校任务的生成）

        # 这里再妥协一下，只能基于单个计划来下载关键词报表，即只能一个计划，一个计划的下载，这样也比较符合业务和逻辑。
        # 即一个计划下，取一次数据库来分发任务。
        result = Adgroup.Report.aggregate_rpt(query_dict= query_dict, group_keys = "adgroup_id,date,source,search_type",
                                              start_date = str(self.earliest_date), end_date = str(self.end_date),
                                              source = {'$in': [-1, 1, 2, 4, 5] }, search_type = {"$in": [-1, 0]}) # 由于source, search_type有默认值，这里写清楚
        for adg_rpt in result:

            temp_adg_id = adg_rpt['_id']['adgroup_id']
            temp_datetime = adg_rpt['_id']['date'] # mongodb包含时分秒，去掉，转为date
            temp_date = datetime.date(temp_datetime.year, temp_datetime.month, temp_datetime.day)

            if temp_date >= self.adg_date_dict[temp_adg_id]: # 判断这个广告组的关键词时间是否是在上次同步之外的

                temp_source = self.conver_args(adg_rpt['_id']['source'])
                temp_search_type = self.conver_args(adg_rpt['_id']['search_type'])

                cache_key = "%s_%s_%s_%s" % (temp_adg_id, temp_date, temp_source, temp_search_type)

                self.task_list.append({
                    'shop_id': self.shop_id,
                    'campaign_id': self.campaign_id,
                    'token': self.token,
                    'adgroup_id': temp_adg_id,
                    'source': temp_source,
                    'search_type': temp_search_type,
                    'date': str(temp_date),
                    'cache_db': self.cache_db,
                    'cache_key': cache_key
                })

                self.key_list.append(cache_key)

    # def decompose_task(self):
    #     # 自己按时间、类似全部分割
    #     task_list = []
    #     for source_search_pair in self.source_search_type_pair_list:
    #         for xdate in self.date_list:
    #             task_list.append({
    #                 'shop_id': self.shop_id,
    #                 'campaign_id': self.campaign_id,
    #                 'adgroup_id': self.adgroup_id,
    #                 'token': self.token,
    #                 'start_time': xdate,
    #                 'end_time': xdate,
    #                 'source': source_search_pair[1],
    #                 'search_type': source_search_pair[0]
    #             })
    #
    #     return task_list

    def publish_task(self):
        try:
            self.TASK_QUEUE.publish_tasks(self.task_list)
            return True
        except Exception as e:
            log.error("publish task error, e=%s" % e)
            return False

    def check_status(self): # 这里会不会有问题，造成api访问太过频繁超限？

        def is_done(status_dict, task_count):
            if status_dict:
                all_successed = all(status_dict.values())
                if not all_successed:
                    raise WorkerFailed("download-failed")
                else:
                    if len(status_dict) == task_count:
                        return True
                    return False
            else:
                return False

        key_list = [("%s_status" % key) for key in self.key_list]
        status_dict = CacheAdpter.get_many(key_list, self.cache_db)
        has_done = is_done(status_dict, len(self.key_list))

        time_interval = 0.1
        # 还是给一个超时吧，超时就下载失败。（还要考虑全局的流控，比如今天关键词的报表下载完毕）
        timeout = len(self.adgroup_id_list) * 60 # 超时时间依据下载的adgroup个数来计算（最好还有一个最大超时时间）
        st_time = time.time()
        while (not has_done):
            time.sleep(time_interval)
            if time.time() - st_time >= timeout:
                # 记录状态
                log.error("timeout: total %s, finished %s, undone task=%s" % (len(self.key_list), len(status_dict), list(set(self.key_list) - set(status_dict.keys()))))
                raise WorkerTimeout("download-timeout")
            status_dict = CacheAdpter.get_many(key_list, self.cache_db)
            has_done = is_done(status_dict, len(self.key_list))

        CacheAdpter.delete_many(key_list, self.cache_db) # 确认了本次任务的状态之后，清掉这些标准位，以免影响下次的判断
        return True

    def sum_result(self):
        result_dict = CacheAdpter.get_many(self.key_list, self.cache_db)
        if result_dict:
            rpt_list = reduce(list.__add__, result_dict.values())
            new_rpt_list = KeywordRpt.simply_rpt(rpt_list)
        else:
            new_rpt_list = []
        return new_rpt_list

    def __call__(self):
        rpt_list = []
        st_time = time.time()
        self.generate_task()
        if len(self.task_list): # 没有任务
            if not self.publish_task(): # 发布任务失败，很有可能是Redis挂掉了 TODO： 加上redis连接超时的参数，错误早知道
                raise Exception("can`t publish task")
            try:
                self.check_status()
            except Exception as e:
                log.error("download FAILED, %s, e=%s" % (self, e))
                raise DownloadFailed()
            rpt_list = self.sum_result()
            log.info("download OK, %s, total task=%s, total result=%s, cost %.2f seconds" %
                     (self, len(self.key_list), len(rpt_list), (time.time() - st_time)))
        return rpt_list


class SlowerDownloadContracter(DownloadContracter):

    TASK_QUEUE = SlowerDownloadRedisQueue

    def split_time_scope(self, start_date, end_date, split_day = 5):
        # 8.25~9.7 --> [(8.25, 8.30), (8.31, 9.4), (9.4, 9.7)]
        delta_days = (end_date - start_date).days
        quotient, remainder = divmod(delta_days, split_day)

        date_pair_list = []
        if quotient:
            for i in range(quotient):
                date_pair_list.append((start_date + datetime.timedelta(days = split_day * i), start_date + datetime.timedelta(days = split_day * (i + 1) - 1)))

        if remainder: # 有余数的情况下，还是需要添加最后的一组
            date_pair_list.append((start_date + datetime.timedelta(days = split_day * quotient), end_date))

        if delta_days == 0: # 起始时间和结束时间一致时
            date_pair_list.append((start_date, end_date))

        return date_pair_list


    # alternative方法，可以从数据库取出具体的天数来调整，比如一推广组可能只有【21, 22, 23, 25, 29, 31, 1, 2】这样的几天报表，可以根据有报表的天数将时间区间分的更合理一点

    def generate_task(self):
        # 将任务的粒度调整的低一点
        """
        困惑点：
        1，直接使用单Adgroup然后多天多维度的，只管下载就好
        2，单adgroup，多天，但是维度是经过调整的，比如只有1,2这样子的【这个压根没有意义，如果没有数据，返回的数据量是一样的，也不会造成API的调用量增加或者减少】

        那么应该就是直接单adgroup然后多维度就行。

        但是仍然有其它问题：
        1. 天数是否需要再作分解，比如15天的报表分成5份或者分成3份，效果是不一样的。
        2. 维度是否需要再分？【肯定要分开，因为没法在同一种参数的api调用完】

        那么，现在可以确定了，参数是这样的：

        1. adgroup_id -->单个
        2. start_date, end_date -->区间需要再根据实际情况调整分成多少份
        3. summary/detail两种数据肯定要区分开来。但是summary的时间区间是否跟详情的一致呢？
        """

        for adg_id, last_sync_time in self.adg_date_dict.items():
            split_date_list = self.split_time_scope(last_sync_time, self.end_date, 5)
            for search_type, source in KeywordRpt.REPORT_CFG:
                desc = source == "SUMMARY" and "summary" or "detail" # 明细数据与汇总数据分成两个任务
                for date_pair in split_date_list:
                    start_time = str(date_pair[0])[:10]
                    end_time = str(date_pair[1])[:10]

                    cache_key = "%s_%s_%s_%s" % (adg_id, start_time, end_time, desc)

                    self.task_list.append({
                        'shop_id': self.shop_id,
                        'campaign_id': self.campaign_id,
                        'token': self.token,
                        'adgroup_id': adg_id,
                        'source': source,
                        'search_type': search_type,
                        'start_time': start_time,
                        'end_time': end_time,
                        'cache_db': self.cache_db,
                        'cache_key': cache_key
                    })

                    self.key_list.append(cache_key)


class EnhancedDownloadContracter(DownloadContracter):

    TASK_QUEUE = SlowerDownloadRedisQueue

    def generate_task(self):
        adg_date_list = collections.defaultdict(list)
        query_dict = {'shop_id': self.shop_id, 'adgroup_id': {'$in': self.adgroup_id_list}}
        result = Adgroup.Report.aggregate_rpt(query_dict= query_dict, group_keys = "adgroup_id,date",
                                              start_date = str(self.earliest_date), end_date = str(self.end_date))
        for adg_rpt in result:
            temp_adg_id = adg_rpt['_id']['adgroup_id']
            temp_datetime = adg_rpt['_id']['date'] # mongodb包含时分秒，去掉，转为date
            temp_date = datetime.date(temp_datetime.year, temp_datetime.month, temp_datetime.day)

            if temp_date >= self.adg_date_dict[temp_adg_id]: # 判断这个广告组的关键词时间是否是在上次同步之外的
                adg_date_list[temp_adg_id].append(temp_date)

        for adg_id, adg_date_list in adg_date_list.items():
            adg_date_list.sort()
            for temp_time_scope in genr_sublist(adg_date_list, 5):
                for search_type, source in KeywordRpt.REPORT_CFG:
                    desc = source == "SUMMARY" and "summary" or "detail" # 明细数据与汇总数据分成两个任务
                    start_time = str(temp_time_scope[0])[:10]
                    end_time = str(temp_time_scope[-1])[:10]

                    cache_key = "%s_%s_%s_%s" % (adg_id, start_time, end_time, desc)

                    self.task_list.append({
                        'shop_id': self.shop_id,
                        'campaign_id': self.campaign_id,
                        'token': self.token,
                        'adgroup_id': adg_id,
                        'source': source,
                        'search_type': search_type,
                        'start_time': start_time,
                        'end_time': end_time,
                        'cache_db': self.cache_db,
                        'cache_key': cache_key
                    })

                    self.key_list.append(cache_key)


def download_task(task):
    """理想：这个function只做发送请求，并且将结果保存到缓存里去。

    1. 只传递session，由api这边动态构建请求；
    现实是要发送一个请求，必须要知道app_key, app_secrect, session来构建auth等信息

    2. 发送请求及接受的逻辑，重新写一份，因为原来的逻辑有必须等待1秒之类的设定，造成整体速度较慢。
    并且返回的数据结构为TopObject，实际上这个封装没有必要，原生的json更直接，能够免去memcached的进出的转换开销

    现实是要完成tapi对应的授权校验，就很难绕过上面的问题，在自动下载的时候，很难知道session是来自千牛还是WEB端的

    最后的妥协:
    使用原来的逻辑来构建请求，不作任何改动。

    扩展:
    这个任务，应该是可以接到动态的参数的；即也可以加速其它的数据，比如adgroup的报表加速
    """

    st = time.time()

    shop_id = task['shop_id']
    campaign_id = task['campaign_id']
    adgroup_id = task['adgroup_id']
    token = task['token']

    start_time = end_time = task['date']
    source = task['source']
    search_type = task['search_type']

    cache_key = task['cache_key']
    cache_db = task['cache_db']

    successed = True
    cached_result = CacheAdpter.get(cache_key, cache_db, None)
    if not cached_result: # 有缓存，不用再下载（除非有重下的标志位）
        tapi = get_tapi(shop_id= shop_id)
        base_list, effect_list = [], []
        try:
            # page_no, page_size 这里可以写死，因为单个推广组、单天、单来源、单类型的关键词报表，不会超过200条
            top_base_objs = tapi.simba_rpt_adgroupkeywordbase_get(campaign_id = campaign_id, adgroup_id = adgroup_id,
                                                                  start_time = start_time, end_time = end_time,
                                                                  search_type = search_type, source = source, subway_token = token,
                                                                  page_no = 1, page_size = 200)

            if top_base_objs and hasattr(top_base_objs, 'rpt_adgroupkeyword_base_list') and top_base_objs.rpt_adgroupkeyword_base_list:
                base_list = top_base_objs.rpt_adgroupkeyword_base_list
        except Exception as e:
            log.error("base fucked, e=%s" % e)
            successed = False

        if base_list:
            try:
                top_effect_objs = tapi.simba_rpt_adgroupkeywordeffect_get(campaign_id = campaign_id, adgroup_id = adgroup_id,
                                                                          start_time = start_time, end_time = end_time,
                                                                          search_type = search_type, source = source, subway_token = token,
                                                                          page_no = 1, page_size = 200)

                if top_effect_objs and hasattr(top_effect_objs, 'rpt_adgroupkeyword_effect_list') and top_effect_objs.rpt_adgroupkeyword_effect_list:
                    effect_list = top_effect_objs.rpt_adgroupkeyword_effect_list
            except Exception as e:
                log.error("effect fucked, e=%s" % e)
                successed = False

        if base_list:
            rpt_list = []
            base_dict, effect_dict = collections.defaultdict(dict), collections.defaultdict(dict)

            for base in base_list:
                base_dict[base.keyword_id].update(KeywordRpt.parse_rpt(base, 'base'))

            for effect in effect_list:
                effect_dict[effect.keyword_id].update(KeywordRpt.parse_rpt(effect, 'effect'))

            for kw_id, base_rpt_dict in base_dict.items():
                rpt_list.extend(KeywordRpt.merge_rpt_dict(base_rpt_dict, effect_dict.get(kw_id, {}), {'shop_id': shop_id, 'campaign_id': campaign_id, 'adgroup_id':adgroup_id, 'keyword_id':kw_id}))

            CacheAdpter.set(cache_key, rpt_list, cache_db,  12 * 60 * 60) # 考虑到缓存的数据

    log.info("total cost %.5f seconds, cache_key=%s" % ((time.time() - st), cache_key))
    CacheAdpter.set("%s_status" % (cache_key), successed, cache_db, 60 * 10) # 确认了某一次的任务状态之后，由contractor删除掉状态


def download_task_new(task):
    st = time.time()

    shop_id = task['shop_id']
    campaign_id = task['campaign_id']
    adgroup_id = task['adgroup_id']
    token = task['token']

    start_time = task['start_time']
    end_time = task['end_time']
    source = task['source']
    search_type = task['search_type']

    cache_key = task['cache_key']
    cache_db = task['cache_db']

    successed = True
    cached_result = CacheAdpter.get(cache_key, cache_db, None)
    if not cached_result: # 有缓存，不用再下载（除非有重下的标志位）
        base_list, effect_list = [], []
        tapi = get_tapi(shop_id = shop_id)
        try:
            base_list = KeywordRpt.download_kwrpt_base(shop_id, campaign_id, adgroup_id, token, start_time, end_time, search_type, source, tapi)
            if base_list:
                effect_list = KeywordRpt.download_kwrpt_effect(shop_id, campaign_id, adgroup_id, token, start_time, end_time, search_type, source, tapi)
        except TopError as e:
            log.error("download keyword report failed, e=%s, shop_id=%s, adgroup_id=%s" % (e, shop_id, adgroup_id))
            successed = False

        rpt_list = KeywordRpt.merge_kwrpt(shop_id, campaign_id, adgroup_id, base_list, effect_list)

        if rpt_list:
            CacheAdpter.set(cache_key, rpt_list, cache_db,  12 * 60 * 60) # 考虑到缓存的数据

    log.info("total cost %.5f seconds, cache_key=%s" % ((time.time() - st), cache_key))
    CacheAdpter.set("%s_status" % (cache_key), successed, cache_db, 60 * 10) # 确认了某一次的任务状态之后，由contractor删除掉状态


