# coding=utf-8

import os
import requests
import datetime
import collections

from django.conf import settings
from mongoengine.document import Document
from mongoengine.fields import IntField, StringField, DateTimeField, BooleanField
from apps.common.utils.utils_enum import BaseEnum, EnumType
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apps.common.utils.utils_datetime import string_2datetime, time_is_ndays_interval
from apps.common.utils.utils_log import log
from apps.subway.models_report import KeywordRpt


class TaskStatusEnum(BaseEnum):

    new = EnumType('ready', '刚创建')
    # waiting = EnumType('waiting', '排队等待中')
    doing = EnumType('doing', '执行中')
    failed = EnumType('failed', '执行失败')
    done = EnumType('done', '完成')


class TaskAPIEnum(BaseEnum):

    base = EnumType("taobao.topats.simba.campkeywordbase.get", "基础数据")
    effect = EnumType("taobao.topats.simba.campkeywordeffect.get", "效果数据")


"""
# 关于时效性

首先，任务是成对出现的，即一个完整的任务应该有两个异步任务，报表的基本数据和效果数据。

那么，对于这两个任务的管理，也是需要有一个管理者的。

理论上，一个计划，可以有多个管理者（即一个计划，可以通过异步下载多次报表），但是由于时效性，通常只有一个任务是可以的。

Here cames the problem

如何保证在新生成任务之前，之前的任务是完成的？

一个场景就是这样的：

昨天有一个管理者来负责任务，任务都创建了，并且在执行中。

到今天了，需要检查这个任务状态的时候，发现时间是昨天的，这个时候，是重置任务吗？还是必须等到结束后才行？

应该有一个超时的限制。

前一个任务，只能以失败或者完成才能进行下一个任务。

如果失败了，是当天则马上重试。

如果是在执行中，则可以继续等到任务超时为止（按淘宝给的说法，超过48小时可以判定失败了）


"""


class KeywordRptATManager(Document):
    """关键词报表的异步任务管理者"""

    TASK_SEARCH_TYPE = "SEARCH"

    SUMMARY_SOURCE = "SUMMARY"
    # DETAIL_SOURCE = "1,2,4,5"
    DETAIL_SOURCE = "1,2"

    campaign_id = IntField(verbose_name="计划ID")
    # search_type = StringField(verbose_name="报表类型", default='SEARCH')  # 只能是SEARCH
    # source = StringField(verbose_name="来源")  # 只能是SUMMARY或者[1, 2, 4, 5]中的
    time_slot = StringField(verbose_name="时间参数")  # 时间参数（昨天：DAY、 前一周：7DAY、 前15天：15DAY、 前30天：30DAY 、前90天：90DAY）单选

    detail_base_task_id = IntField(verbose_name="基础报表任务ID", default=0)
    detail_effect_task_id = IntField(verbose_name="效果报表任务ID", default=0)

    summary_base_task_id = IntField(verbose_name="基础汇总报表任务ID", default=0)
    summary_effect_task_id = IntField(verbose_name="效果报表任务ID", default=0)

    task_start_time = DateTimeField(verbose_name="任务开始时间")
    # task_rpt_type = StringField(verbose_name = "任务的报表类型"， choices = TaskRptTypeEnum.enum_choices, default = TaskRptTypeEnum.detail)
    # 还是应该将summary与detail的任务管理者放一起，这样时间只需要一个，并且对mnger本身的管理也更方便

    meta = {'collection': 'subway_asynctask_manager'}

    def get_status(self, tapi):
        self.binder_tasks()

        detail_base_status = self.detail_base_task.check_task_status(tapi)
        detail_effect_status = self.detail_effect_task.check_task_status(tapi)

        summary_base_status = self.summary_base_task.check_task_status(tapi)
        summary_effect_status = self.summary_effect_task.check_task_status(tapi)

        transform_mapping = {
            TaskStatusEnum.new: 1,
            TaskStatusEnum.doing: 2,
            TaskStatusEnum.done: 4,
            TaskStatusEnum.failed: 0
        }
        """
        四项相乘，只有256时表示完成
        如果是0，表示失败了
        如果是1，则表示还没有执行
        如果是其它的，表示正在执行中
        """

        product = transform_mapping[detail_base_status] * transform_mapping[detail_effect_status] * \
            transform_mapping[summary_base_status] * transform_mapping[summary_effect_status]

        if product == 0:
            return TaskStatusEnum.failed
        elif product == 256:
            return TaskStatusEnum.done
        elif product == 1:
            return TaskStatusEnum.new
        else:
            return TaskStatusEnum.doing

    @classmethod
    def get_manager(cls, campaign_id, last_sync_time, tapi):
        try:
            mnger = cls.objects.get(campaign_id=campaign_id)
        except cls.DoesNotExist:
            time_slot = cls.get_time_slot(last_sync_time)
            mnger = cls.objects.create(campaign_id=campaign_id, time_slot=time_slot)
            mnger.register_task(tapi)  # 开始异步任务
        return mnger

    @classmethod
    def get_time_slot(cls, last_sync_time):
        # return "DAY"
        if last_sync_time and isinstance(last_sync_time, datetime.datetime):
            days = (datetime.datetime.now() - last_sync_time).days
            if days <= 1:
                return "DAY"
            elif days <=7:
                return "7DAY"
            elif days <=15:
                return "15DAY"
            elif days <=30:
                return "30DAY"
            else:
                return "30DAY" # 最多只保存30天的吧
        else:
            return "30DAY"

    @classmethod
    def ensure_task(cls, shop_id, campaign_id, last_sync_time, tapi): # 保证任务生成，不管结果
        mnger = cls.get_manager(campaign_id, last_sync_time, tapi)
        if time_is_ndays_interval(mnger.task_start_time, 2): # 超过两天，就放弃之前的任务，重新生成任务
            mnger.time_slot = cls.get_time_slot(last_sync_time)  # 重新生成time_slot
            mnger.register_task(tapi)
            return True
        else:
            if mnger.get_status(tapi) == TaskStatusEnum.failed:
                if time_is_ndays_interval(mnger.task_start_time, 0): 
                    mnger.regenerate_task(tapi)
                else:
                    mnger.time_slot = cls.get_time_slot(last_sync_time)
                    mnger.register_task(tapi)
                return True
            else:
                return True

    def has_task(self):
        if all([self.detail_base_task_id, self.detail_effect_task_id, self.summary_base_task_id, self.summary_effect_task_id]):
            return True
        else:
            return False

    @classmethod
    def get_task_report(cls, shop_id, campaign_id, last_sync_time, tapi):
        mnger = cls.get_manager(campaign_id, last_sync_time, tapi)
        if not mnger.has_task():
            mnger.time_slot = cls.get_time_slot(last_sync_time)
            mnger.register_task(tapi)

        if time_is_ndays_interval(mnger.task_start_time, 2): # 超过两天，就放弃之前的任务，重新生成任务
            mnger.time_slot = cls.get_time_slot(last_sync_time)  # 重新生成timeslot
            mnger.register_task(tapi)
            return False, []
        else:
            status = mnger.get_status(tapi)
            if status == TaskStatusEnum.done:
                rpt_list = mnger.get_task_result(shop_id)
                return True, rpt_list
            elif status == TaskStatusEnum.failed:
                # 如果是今天的任务，还可以抢救一下，否则只能重新生成任务了，因为报表的特殊性，只要过一天，结果就不一样了。
                if time_is_ndays_interval(mnger.task_start_time, 0): 
                    mnger.regenerate_task(tapi)
                else:
                    mnger.time_slot = cls.get_time_slot(last_sync_time)
                    mnger.register_task(tapi)
                return False, []
            else:
                return False, []

    def register_task(self, tapi):
        detail_base_task, detail_effect_task = KeywordRptAT.create_task_pair(
            self.campaign_id, self.time_slot, self.TASK_SEARCH_TYPE, self.DETAIL_SOURCE, tapi)
        summary_base_task, summary_effect_task = KeywordRptAT.create_task_pair(
            self.campaign_id, self.time_slot, self.TASK_SEARCH_TYPE, self.SUMMARY_SOURCE, tapi)

        self.detail_base_task_id = detail_base_task.task_id
        self.detail_effect_task_id = detail_effect_task.task_id
        self.summary_base_task_id = summary_base_task.task_id
        self.summary_effect_task_id = summary_effect_task.task_id

        self.task_start_time = datetime.datetime.now()
        self.save()
        return True

    def regenerate_task(self, tapi):
        """在任务出现失败时，重新生成任务"""
        self.binder_tasks()
        # 讨厌写这样的代码！
        if self.detail_base_task.status == TaskStatusEnum.failed:
            new_detail_base_task = KeywordRptAT.create_task(self.campaign_id, self.time_slot, self.TASK_SEARCH_TYPE, self.DETAIL_SOURCE, tapi, 'base')
            self.detail_base_task = new_detail_base_task
            self.detail_base_task_id = new_detail_base_task.task_id

        if self.detail_effect_task.status == TaskStatusEnum.failed:
            new_detail_effect_task = KeywordRptAT.create_task(self.campaign_id, self.time_slot, self.TASK_SEARCH_TYPE, self.DETAIL_SOURCE, tapi, 'effect')
            self.detail_effect_task = new_detail_effect_task
            self.detail_effect_task_id = new_detail_effect_task.task_id

        if self.summary_base_task.status == TaskStatusEnum.failed:
            new_summary_base_task = KeywordRptAT.create_task(self.campaign_id, self.time_slot, self.TASK_SEARCH_TYPE, self.SUMMARY_SOURCE, tapi, 'base')
            self.summary_base_task = new_summary_base_task
            self.summary_base_task_id = new_summary_base_task.task_id

        if self.summary_effect_task.status == TaskStatusEnum.failed:
            new_summary_effect_task = KeywordRptAT.create_task(self.campaign_id, self.time_slot, self.TASK_SEARCH_TYPE, self.SUMMARY_SOURCE, tapi, 'effect')
            self.summary_effect_task = new_summary_effect_task
            self.summary_effect_task_id = new_summary_effect_task.task_id

        return True
        

    def binder_tasks(self):
        if not hasattr(self, "_bindered"):
            if self.has_task():
                task_list = KeywordRptAT.objects.filter(
                    task_id__in=[self.detail_base_task_id, self.detail_effect_task_id, self.summary_base_task_id, self.summary_effect_task_id])
                
                task_dict = {task.task_id: task for task in task_list}
                self.detail_base_task = task_dict[self.detail_base_task_id]
                self.detail_effect_task = task_dict[self.detail_effect_task_id]
                self.summary_base_task = task_dict[self.summary_base_task_id]
                self.summary_effect_task = task_dict[self.summary_effect_task_id]
                self._bindered = True
                return True
            else:
                raise Exception("task not registed!")
        return True

    def get_task_result(self, shop_id):
        self.binder_tasks()

        detail_base_result = self.detail_base_task.get_task_result(shop_id)
        detail_effect_result = self.detail_effect_task.get_task_result(shop_id)
        detail_rpt_list = self.merge_rpt_result(shop_id, detail_base_result, detail_effect_result)
        # simply_rpt_list = KeywordRpt.simply_rpt(detail_rpt_list) # 这里还需要合并报表，不保存5种详情，只保存三种
        simply_rpt_list = detail_rpt_list

        summary_base_result = self.summary_base_task.get_task_result(shop_id)
        summary_effect_result = self.summary_effect_task.get_task_result(shop_id)
        summary_rpt_list = self.merge_rpt_result(shop_id, summary_base_result, summary_effect_result)

        simply_rpt_list.extend(summary_rpt_list)

        return simply_rpt_list
            

    def merge_rpt_result(self, shop_id, base_dict, effect_dict):
        rpt_list = []
        for adgroup_id, kw_base_dict in base_dict.items():
            kw_effect_dict = effect_dict.get(adgroup_id, {})
            for kw_id, kw_base_rpt_dict in kw_base_dict.items():
                temp_effect_rpt_dict = kw_effect_dict.get(kw_id, {})
                rpt_list.extend(KeywordRpt.merge_rpt_dict(kw_base_rpt_dict, temp_effect_rpt_dict, {
                                'shop_id': shop_id, 'campaign_id': self.campaign_id, 'adgroup_id': adgroup_id, 'keyword_id': kw_id}))

        return rpt_list


# 在campaign那边需要记录这些报表同步数据，即那里需要记录下，上次同步关键词报表的时间

class KeywordRptAT(Document):

    """关键词报表的异步任务"""

    # 生成前的参数，为了保证这个任务能够失败也自恢复

    task_id = IntField(verbose_name="任务ID", primary_key=True)
    status = StringField(verbose_name="状态", choices=TaskStatusEnum.enum_choices, default=TaskStatusEnum.new)
    create_time = DateTimeField(verbose_name="创建时间", default=datetime.datetime.now)
    download_url = StringField(verbose_name="下载链接", default='')
    method = StringField(verbose_name="调用方法", default='')  # from taobao
    has_downloaded = BooleanField(verbose_name = "是否已下载", default = False)

    meta = {'collection': 'subway_asynctask'}

    # windows是 d: ztcjingling/kwrpt/, linux是/data/ztcjl/kwrpt/
    FILE_FOLDER = os.path.join(os.path.dirname(settings.PROJECT_ROOT), "kwrpt")

    FIELD_MAPPING = {
        'searchtype': 'search_type',
        'keywordid': 'keyword_id',
        'adgroupid': 'adgroup_id'
    }

    @staticmethod
    def ensure_dirs(paths):
        if not os.path.exists(paths):
            os.makedirs(paths)

    @classmethod
    def create_task(cls, campaign_id, time_slot, search_type, source, tapi, rpt_type="base"):
        if rpt_type == "base":
            api_name = "topats_simba_campkeywordbase_get"
        else:
            api_name = "topats_simba_campkeywordeffect_get"

        try:
            result = getattr(tapi, api_name)(campaign_id=campaign_id,
                                             time_slot=time_slot, search_type=search_type, source=source)
        except Exception as e:
            log.error("can`t create task, reason=%s, campaign_id=%s, time_slot=%s, search_type=%s, source=%s" %
                      (e, campaign_id, time_slot, search_type, source))
            raise e

        task_id = result.task.task_id
        create_time = string_2datetime(result.task.created)
        task = cls.objects.create(task_id=task_id, create_time=create_time)
        return task

    @classmethod
    def create_task_pair(cls, campaign_id, time_slot, search_type, source, tapi):
        base_task = cls.create_task(campaign_id, time_slot, search_type, source, tapi, 'base')
        effect_task = cls.create_task(campaign_id, time_slot, search_type, source, tapi, 'effect')
        return base_task, effect_task

    @classmethod
    def get_task_status(cls, task_id, tapi):
        try:
            result = tapi.topats_result_get(task_id=task_id)
        except Exception as e:
            log.error("can`t get task status, e=%s" % e)
        return result.task

    def check_task_status(self, tapi):
        if self.status == TaskStatusEnum.done:  # 如果已经是downloaded过了，就不需要再更新了
            return self.status

        task_result = self.get_task_status(self.task_id, tapi)
        if task_result.status == TaskStatusEnum.done:
            self.download_url = task_result.download_url
            self.status = task_result.status
            self.method = task_result.method
        elif task_result.status in [TaskStatusEnum.doing, TaskStatusEnum.failed]:
            self.status = task_result.status
            self.method = task_result.method
        self.save()
        return self.status

    def get_task_result(self, shop_id):
        """对外接口，状态为完成后，下载报表文件，保存文件，解析文件"""
        if self.status == TaskStatusEnum.done:
            if (not self.has_downloaded) and self.download_url:
                self.download_file(shop_id)
            return self.parse_file(shop_id)
        else:
            raise Exception("task not done yet, task_id=%s" % self.task_id)

    def get_file_path(self, shop_id):
        """获取文件保存路径，默认是/data/ztcjl/kwrpt/<shop_id>/<task_id>"""
        file_folder = os.path.join(self.FILE_FOLDER, str(shop_id))
        self.ensure_dirs(file_folder)
        return os.path.join(file_folder, str(self.task_id))

    def download_file(self, shop_id):
        """下载报表文件"""
        try:
            response = requests.get(url=self.download_url, stream=True)
        except Exception as e:
            log.error("download task file failed, e=%s, task_id=%s" % (e, self.task_id))
            raise e

        try:
            with open(self.get_file_path(shop_id), 'wb') as fd:
                for chunk in response.iter_content(1024):
                    fd.write(chunk)
        except IOError as e:
            log.error("download file failed, IOError, e=%s" % e)
            raise e
        self.has_downloaded = True
        self.save()
        return True

    def _map_column(self, columns):
        """数据项列映射"""
        converted_columns = []
        for column in columns:
            if column in self.FIELD_MAPPING:
                converted_columns.append(self.FIELD_MAPPING[column])
            else:
                converted_columns.append(column)
        return converted_columns

    def load_file(self, shop_id):
        """读取下载的报表文件"""
        try:
            with open(self.get_file_path(shop_id), 'r') as fd:
                content = fd.read()
            return content
        except IOError as e:
            log.error("load file failed, e=%s, shop_id=%s, task_id=%s" % (e, shop_id, self.task_id))
            raise e

    def parse_file(self, shop_id):
        """解析下载文件"""
        if self.method == TaskAPIEnum.base:
            rpt_type = "base"
        elif self.method == TaskAPIEnum.effect:
            rpt_type = "effect"
        else:
            raise Exception("Seems this is a new api not used before?")

        content = self.load_file(shop_id)
        lines = content.split('\n')
        converted_columns = self._map_column(lines[0].split(','))
        result_dict = collections.defaultdict(lambda: collections.defaultdict(dict))
        for line in lines[1:]:
            if line:
                # print line
                temp_dict = DictWrapper(dict(zip(converted_columns, line.split(','))))
                for key in getattr(KeywordRpt, '%s_keys' % rpt_type):
                    value = getattr(temp_dict, key, 0) == '' or 0
                    temp_dict[key] = value
                result_dict[temp_dict.adgroup_id][temp_dict.keyword_id].update(KeywordRpt.parse_rpt(temp_dict, rpt_type))

        return result_dict