# coding=UTF-8

import datetime

from mongoengine.document import Document
from mongoengine.fields import IntField, DateTimeField, StringField

from apps.common.utils.utils_log import log
from apps.common.utils.utils_datetime import date_2datetime
from apps.common.utils.utils_string import get_char_num
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.models import Config
from apps.router.models import User
from apps.subway.models_keyword import Keyword, IllegalKeyword
from apps.subway.models_adgroup import Adgroup
from apps.engine.utils import refresh_shop_cat
from apps.kwslt.analyzer import ChSegement
from apps.ncrm.models import PrivateMessage

class ShopMngTask(Document):
    STATUS_CHOICES = ((-1, '已分配'), (0, '尚未准备'), (1, '等待执行'), (2, '执行中'), (3, '执行成功'), (4, '执行失败'))

    shop_id = IntField(verbose_name = "店铺ID", primary_key = True)
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    status = IntField(verbose_name = "任务状态", default = 0, choices = STATUS_CHOICES)
    run_times = IntField(verbose_name = "当天运行次数", default = 0, help_text = "用于失败重试计数")
    last_start_time = DateTimeField(verbose_name = "上次运行开始时间")
    last_end_time = DateTimeField(verbose_name = "上次运行结束时间")
    sync_mode = IntField(verbose_name = "数据同步方式", default = 0) # 数据同步方式(默认0 同步下载；1 异步下载)
    duplicate_time = DateTimeField(verbose_name = "重复词排查时间")
    stop_func = StringField(verbose_name = "任务执行失败点", default = None)
    keyword_audit_time = DateTimeField(verbose_name = "关键词审核状态排查时间")
    adgroup_audit_time = DateTimeField(verbose_name = "宝贝审核状态排查时间")
    manual_priority = IntField(verbose_name = "人为优先级", default = 0)
    priority = IntField(verbose_name = "优先级", default = 0)

    meta = {'db_alias': "mnt-db", 'collection':'engine_shopmngtask'}

    @property
    def user(self):
        if not hasattr(self, '_user'):
            self._user = User.objects.get(shop_id = self.shop_id)
        return self._user

    def is_today(self):
        """shopmngtask的“今天”定义，应该是凌晨6点至次日凌晨6点"""
        if not (self.last_start_time and isinstance(self.last_start_time, datetime.datetime)):
            return False
        else:
            nw = datetime.datetime.now()
            delta_days = nw.hour < 6 and -1 or 0
            start_date = nw.date() + datetime.timedelta(days = delta_days)
            end_date = nw.date() + datetime.timedelta(days = delta_days + 1)
            time_scope = (datetime.datetime(start_date.year, start_date.month, start_date.day, 6), datetime.datetime(end_date.year, end_date.month, end_date.day, 6))
            if self.last_start_time > time_scope[0] and self.last_start_time < time_scope[1]:
                return True
            else:
                return False

    def display_status(self):
        status_descr = '今天尚未执行'
        if self.is_today():
            status_descr = '今天%s' % self.get_status_display()
            if self.status == 4:
                status_descr += '，失败点为：%s' % self.stop_func
        return status_descr

    def has_permisson(self, is_login = False):
        """判断是否有权限"""
        if is_login:
            return True
        else:
            perms_code = self.user.sync_perms_code()
            if perms_code:
                return True
            else:
                return False

    def is_runnable(self, is_login = False):
        """根据任务状态判断当前是否可以执行"""
        if not self.is_today():
            return True
        else:
            if self.status in [-1, 0, 1]:
                return True
            elif self.status == 2: # TODO: wangqi 2014-1-10 考虑到有缓存作为判断任务是否在运行，这里允许重复执行。注释的代码有判断运行超时的逻辑
                return True
                # if time_is_recent(self.last_start_time, minutes = 45):
                #     log.info('shopmngtask is running, alread ran %s minutes' % ((datetime.datetime.now() - self.last_start_time).seconds / 60))
                #     return False
                # else:
                #     return True
            elif self.status == 3:
                log.info('shopmngtask ran today already, shop_id=%s' % self.shop_id)
                return False
            elif self.status == 4:
                if self.run_times > 3 and not is_login:
                    log.info('shopmngtask %s ran %s times today, and not from login' % (self.shop_id, self.run_times))
                    return False
                else:
                    return True

    def _sync_data(self):
        from apps.subway.download import Downloader
        if not Downloader.download_all_struct(shop_id = self.shop_id):
            log.error('shopmng task download struct failed, shop_id=%s' % self.shop_id)
            return False
        log.info('shopmng task download struct ok, shop_id=%s' % self.shop_id)
#         if self._check_keyword_audit_status():
#             self.keyword_audit_time = datetime.datetime.now()
        if self._check_adgroup_audit_status():
            self.adgroup_audit_time = datetime.datetime.now()
        self.save()
        refresh_shop_cat(self.shop_id)
        log.info('shopmng task refresh shop cat ok, shop_id=%s' % self.shop_id)
        if not Downloader.download_all_rpt(shop_id = self.shop_id, detail_flag = False):
            log.error('shopmng task download rpt failed, shop_id=%s' % self.shop_id)
            return False
        log.info('shopmng task download rpt ok, shop_id=%s' % self.shop_id)
        return True

    def _check_mnt(self):
        from apps.subway.download import Downloader
        from apps.mnt.models import MntMnger, MntTaskMng
        try:
            priority, adg_tuple_list = MntMnger.check_mnt_camps(shop_id = self.shop_id)
            MntTaskMng.check_routine_task(shop_id = self.shop_id)
            if self.priority != priority:
                self.update_task_status(priority = priority)
            log.info('shopmng task checked mnt status, shop_id=%s' % self.shop_id)

            if adg_tuple_list:
                try:
                    dler = Downloader.objects.get(shop_id = self.shop_id)
                    Keyword.download_kwrpt_byadgs(shop_id = self.shop_id, tapi = dler.tapi, token = dler.token, adg_tuple_list = adg_tuple_list)
                except Exception, e:
                    log.error('download kwrpt error, shop_id=%s, e=%s' % (self.shop_id, e))
            log.info('shopmng task downloaded keyword rpt, shop_id=%s' % self.shop_id)
            return True
        except Exception, e:
            log.info('shopmnt task check mnt status error, shop_id=%s, e=%s' % (self.shop_id, e))
            return False

    def _check_keyword_audit_status(self):
        from apps.subway.upload import delete_keywords
        result = True
        if self.keyword_audit_time:
            today = datetime.date.today()
            year, month, day = today.year, today.month, today.day
            today_0 = datetime.datetime(year, month, day)
            if self.keyword_audit_time >= today_0:
                return False
        illegal_keyword_qset = list(Keyword.objects.filter(shop_id = self.shop_id, audit_status = 'audit_reject').only('campaign_id', 'adgroup_id', 'keyword_id', 'word'))
        if not illegal_keyword_qset:
            return True
        adg_cids_dict = dict(Adgroup.objects.filter(shop_id = self.shop_id).values_list('adgroup_id', 'category_ids'))
        camp_kw_arg_dict = {}
        cids_kw_list = []
        cat_id_root_dict = {}
        for keyword in illegal_keyword_qset:
            kw_arg_list = camp_kw_arg_dict.get(keyword.campaign_id, [])
            kw_arg_list.append([keyword.adgroup_id, keyword.keyword_id, keyword.word, 1, 0, '删除违规词'])
            camp_kw_arg_dict[keyword.campaign_id] = kw_arg_list

            category_ids = adg_cids_dict.get(keyword.adgroup_id, '')
            if not category_ids:
                continue
            cat_id = category_ids.split(' ')[-1]
            cids_kw_list.append('&'.join([cat_id, keyword.word]))
            root_cat_id = category_ids.split(' ')[0]
            cat_id_root_dict[cat_id] = root_cat_id
        # 在本地收录违规词
        illegal_keyword_list = []
        try:
            cids_kw_list_indb = IllegalKeyword.objects.filter(shop_id = self.shop_id).values_list('cat_id', 'word')
            cids_kw_list_indb = ['&'.join([str(cat_id), word]) for cat_id, word in cids_kw_list_indb]
            cids_kw_list_delta = list(set(cids_kw_list) - set(cids_kw_list_indb))
            for cids_kw in cids_kw_list_delta:
                temp_list = cids_kw.split('&')
                cat_id, word = temp_list[0], '&'.join(temp_list[1:])
                try:
                    root_parent_id = cat_id_root_dict.get(cat_id, cat_id)
                    cat_path = Cat.get_cat_path(cat_id_list = [cat_id], last_name = ' ').get(str(cat_id), ['未获取到值', ''])[0]
                    illegal_keyword_list.append(IllegalKeyword(shop_id = self.shop_id, root_parent_id = root_parent_id, cat_id = int(cat_id), cat_path = cat_path, word = word, is_handled = 0, last_name = self.user.shop_type))
                except Exception, e:
                    log.error('can not get cat_ids by keyword and the error is =%s' % e)
                    pass
            if illegal_keyword_list:
                IllegalKeyword.objects.insert(illegal_keyword_list)
            log.info('shopmng task check_keyword_audit_status insert IllegalKeyword ok, shop_id=%s' % self.shop_id)
        except Exception, e:
            result = False
            log.error('shopmng task check_keyword_audit_status insert IllegalKeyword error, shop_id=%s, e=%s' % (self.shop_id, e))
        # 在淘宝上删除违规词
        for campaign_id, kw_arg_list in camp_kw_arg_dict.items():
            try:
                delete_keywords(shop_id = self.shop_id, campaign_id = campaign_id, kw_arg_list = kw_arg_list, record_flag = True, data_type = 403, opter = 3, opter_name = '')
                log.info('shopmng task check_keyword_audit_status delete_keywords ok, shop_id=%s, campaign_id=%s' % (self.shop_id, campaign_id))
            except Exception, e:
                result = False
                log.error('shopmng task check_keyword_audit_status delete_keywords error, shop_id=%s, campaign_id=%s, e=%s' % (self.shop_id, campaign_id, e))
        if result:
            log.info('shopmng task check_keyword_audit_status ok, shop_id=%s' % self.shop_id)
        return result

    def _sms_switch(self):
        """读取短信发送的全局配置和用户配置以及上次改动的列表 返回是否发送的标识"""
        from apps.ncrm.models import Customer
        from apps.common.models import Config
        sys_cfg = False
        customer_cfg = False
        try:
            cfg = Config.objects.get(key = 'sms.is_enabled')
            if int(cfg.value):
                sys_cfg = True
            cust = Customer.objects.get(shop_id = self.shop_id)
            if int(cust.remind):
                customer_cfg = True
        except Exception, e:
            return False
        if sys_cfg and customer_cfg:
            return True
        else:
            return False

    def _check_adgroup_audit_status(self):
        today = datetime.date.today()
        year, month, day = today.year, today.month, today.day
        today_0 = datetime.datetime(year, month, day)
        if self.adgroup_audit_time:
            if self.adgroup_audit_time >= today_0:
                return False
        offline_adgroup_list = Adgroup.objects.filter(shop_id = self.shop_id, offline_type = 'audit_offline').values_list('adgroup_id')
        if not offline_adgroup_list:
            return True

        # 用系统默认账号发站内信通知
        from apps.ncrm.models import Customer
        from apps.subway.models_account import Account

        acc_check = False
        acc = Account.objects.get(shop_id = self.shop_id)
        if acc and acc.illegal_adgroup_list:
            # 检查是否有新的违规宝贝
            temp_list = set(offline_adgroup_list) - set(acc.illegal_adgroup_list) # 新list减去旧的list 找出变动的
            if temp_list and len(temp_list) > 0:
                # 当有新的违规宝贝时，需要发送私信
                acc_check = True
                try:
                    content = '''亲，您的直通车有%s个宝贝违规，已被淘宝下架，请立即处理，以免被加大处罚甚至停车。请在宝贝列表中根据“推广状态”下拉框查找违规宝贝''' % len(offline_adgroup_list)
                    start_time = datetime.datetime.now()
                    end_time = start_time + datetime.timedelta(15)
                    PrivateMessage.send_message(shop_id = self.shop_id,
                             title = "宝贝违规下架提醒",
                             content = content,
                             app_id = 12612063,
                             level = 'alert',
                             start_time = start_time,
                             end_time = end_time)
                    log.info('shopmng task check_adgroup_audit_status step 2 ok, shop_id=%s' % self.shop_id)
                except Exception, e:
                    log.error('shopmng task check_adgroup_audit_status step 2 error, shop_id=%s, e=%s' % (self.shop_id, e))

        # 发送手机短信提醒
        from apps.common.utils.utils_sms import send_sms

        last_sms_send_time = acc.sms_send_time or datetime.datetime.now() - datetime.timedelta(days = 30)
        interval_time = datetime.datetime.now() - last_sms_send_time # 获取上次短信发送时间和当前时间差
        sms_switch = self._sms_switch()
        is_need = PrivateMessage.need_2handle(shop_id = self.shop_id)
        if sms_switch and interval_time.days > 7 and acc_check and is_need:
            # 如果需要发送短信，并且上次发送短信超过7天，并且有新的违规宝贝，并且最新的一条违规下架私信没有阅读，则需要发送短信
            try:
                phone = Customer.objects.get(shop_id = self.shop_id).phone
                if phone:
                    username = self.user.nick
                    content = '开车精灵紧急提示：%s您好，贵店%s个直通车宝贝被判定违规下架，请立即处理，以免被加大处罚甚至停车。' % (username, len(offline_adgroup_list))
                    result = send_sms([phone], content)
                    if 'code' in result and result['code'] == 0:
                        account = Account.objects.get(shop_id = self.shop_id)
                        account.sms_send_time = datetime.datetime.now()
                        account.illegal_adgroup_list = offline_adgroup_list
                        account.save()
                        log.info('shopmng task check_adgroup_audit_status send_sms ok, shop_id=%s' % self.shop_id)
                    else:
                        log.info('shopmng task check_adgroup_audit_status send_sms error, shop_id=%s, e=网络或者短信平台出问题' % self.shop_id)
                else:
                    log.info('shopmng task check_adgroup_audit_status send_sms error, shop_id=%s, e=该用户还没录入手机号' % self.shop_id)
            except Exception, e:
                log.error('shopmng task check_adgroup_audit_status send_sms error, shop_id=%s, e=%s' % (self.shop_id, e))
        return True

    def _run(self):
        TASK_OPERATION_LIST = ['_sync_data', '_check_mnt']
        try:
            index = TASK_OPERATION_LIST.index(self.stop_func)
        except ValueError:
            index = -1

        try:
            for i, operation in enumerate(TASK_OPERATION_LIST):
                if i < index:
                    continue
                else:
                    if not getattr(self, operation)():
                        raise Exception(operation)
                    log.info('shopmng task %s OK, shop_id=%s' % (operation, self.shop_id))

            log.info('[timer][shop_task_result][ok]: shop_id=%s' % self.shop_id)
            return True, None
        except Exception, e:
            log.error('[timer][shop_task_result][failed]: shop_id=%s, while doing %s' % (self.shop_id, e))
            return False, str(e)

    def update_task_status(self, **update_info):
        """更新任务状态"""
        for attr, value in update_info.items():
            setattr(self, attr, value)

        shopmng_task_coll.update({'_id':self.shop_id}, {'$set':update_info})
        return True

    def run_task(self, is_login = False):
        """执行任务流程"""
        if not is_login: # 登录前会有权限判断，而且会更新
            if not self.has_permisson(is_login):
                self.update_task_status(status = 0)
                return False

            if not self.is_runnable(is_login):
                return False

        self.update_task_status(status = 2, last_start_time = datetime.datetime.now(), run_times = self.run_times + 1, last_end_time = None)
        result, stop_func = self._run()
        self.update_task_status(status = result and 3 or 4, last_end_time = datetime.datetime.now(), stop_func = stop_func)
        return result

    @staticmethod
    def get_valid_task(need_count):
        """获取符合条件的任务队列"""
        valid_id_list = []
        is_mutual = CacheAdpter.get(CacheKey.ENGINE_SHOPMNG_TASK_MUTUAL_LOCK, 'web')
        if is_mutual: # 如果能够取到缓存，说明门关了
            return valid_id_list
        else: # 否则，马上设置缓存，将门关了
            try:
                CacheAdpter.set(CacheKey.ENGINE_SHOPMNG_TASK_MUTUAL_LOCK, True, 'web', 60 * 2)

                test_shop_id_list = Config.get_value('mnt.TEST_SHOP_IDLIST', default = [])

                today_0time = date_2datetime(datetime.date.today())
                recyle_time = datetime.datetime.today() - datetime.timedelta(hours = 6) # 回收时间
                cursor = shopmng_task_coll.find({'_id': {'$nin': test_shop_id_list},
                                                 '$or':[{'status':1},
                                                        {'status':{'$in':[-1, 2, 4]}, 'last_start_time':{'$lte':recyle_time, '$gte':today_0time}}]
                                                 }, {'_id':1}).sort([('manual_priority', -1), ('priority', -1)])
                cursor = cursor.limit(need_count)

                valid_id_list = [i['_id'] for i in cursor]
                if valid_id_list:
                    shopmng_task_coll.update({'_id':{'$in':valid_id_list}}, {'$set':{'status':-1, 'last_start_time':datetime.datetime.now()}}, multi = True)
                return valid_id_list
            except Exception, e:
                log.error("shopmng_task get_valid_task error, e=%s" % e)
                return valid_id_list
            finally:
                CacheAdpter.delete(CacheKey.ENGINE_SHOPMNG_TASK_MUTUAL_LOCK, 'web') # 清除缓存，把门打开

    @staticmethod
    def reset_task(shop_id = None):
        """重置任务状态"""
        update_info = {'last_start_time':None, 'last_end_time': None, 'run_times':0, 'status':1}
        if shop_id:
            query_cond = {'_id':shop_id}
        else:
            query_cond = {'status':{'$ne':0}} # 非激活的任务不处理，必须要由用户登录才会重新激活
        shopmng_task_coll.update(query_cond, {'$set':update_info}, multi = True)


shopmng_task_coll = ShopMngTask._get_collection()


# 标题转化器.将宝贝标题转化为创意标题
class TitleTransfer:

    garbage_words_string = ""
    can_del_words_list = []
    del_words_list = []

    @staticmethod
    def load_in_mem_if_not():
        if TitleTransfer.garbage_words_string or TitleTransfer.can_del_words_list:
            return

        garbage_words = Config.get_value('title.garbage_words')
        can_del_words = Config.get_value('title.can_del_words')
        if garbage_words:
            TitleTransfer.garbage_words_string += garbage_words
        if can_del_words:
            TitleTransfer.del_words_list.extend(can_del_words["del_words"].split(','))
            TitleTransfer.can_del_words_list.extend(can_del_words["check_len_words"].split(','))

    @staticmethod
    def remove_noneed_words(title):
        TitleTransfer.load_in_mem_if_not()
        # END_WORDS处理，对结束符处理

        def end_title(title):
            end_words = title[-2:]
            end_char = ''
            for ss in end_words:
                if ord(ss) <= 127:
                    end_char += '.'
                else:
                    end_char += '..'
            title = title[:-2] + end_char
            return title

        # 依次检查违禁词，直接去掉
        temp_title = title
        for del_words in TitleTransfer.del_words_list:
            temp_title = temp_title.replace(del_words, "")

        # 检查是否含特殊符号,逐个去掉
        for char in TitleTransfer.garbage_words_string:
            temp_title = temp_title.replace(char, '')
            if get_char_num(temp_title) <= 20:
                end_title(temp_title)
                break

        # 依次检查是否存在泛词，逐个去掉
        if get_char_num(temp_title) > 20:
            for can_del_words in TitleTransfer.can_del_words_list:
                temp_title = temp_title.replace(can_del_words, "") # 去掉
                if get_char_num(temp_title) <= 20:
                    end_title(temp_title)
                    break

        if len(temp_title) <= 2: # 防止标题被去掉成空
            temp_title = title

        return temp_title

    @staticmethod
    def deal_title_tail(title):
        # 如果还是够，就保留前面的17个字符，后面三个加...
        part_list = title.split(' ')
        result_char = ''
        if len(part_list) == 1:
            count = 0
            for cc in title:
                if ord(cc) <= 127:
                    count += 0.5
                else:
                    count += 1
                result_char += cc
                if count == 18.5:
                    result_char += '...'
                    break
                elif count == 19:
                    result_char += '..'
                    break
            return result_char

        for part in part_list:
            if not part:
                continue
            all_num = get_char_num(result_char)
            part_num = get_char_num(part)

            if all_num + part_num > 19.5: # 词不能上，就直接返回 ,包括空格
                continue
            if result_char:
                result_char = result_char + ' ' + part
            else:
                result_char = part
        if not result_char:
            result_char = title
        # 校验,去掉小尾巴
        remove_tail = True
        while remove_tail:
            result_list = result_char.split(' ')
            if len(result_list) > 1 and get_char_num(result_list[-1]) <= 1:
                result_char = result_char.replace(' ' + result_list[-1], '').rstrip()
            else:
                remove_tail = False
        return result_char

    # 根据宝贝标题来生成两个创意标题
    @staticmethod
    def generate_adg_title_list(shop_id, item_id, title):
        item_title = TitleTransfer.remove_noneed_words(title)
        adg_title_list = []
        try:
            adg_title_list = ChSegement.generate_adg_title_list(title = item_title)
            for i, adg_title in enumerate(adg_title_list):
                if adg_title.count(' ') > item_title.count(' ') or get_char_num(adg_title) < 5:
                    adg_title_list[i] = TitleTransfer.deal_title_tail(adg_title)
                else:
                    adg_title_list[i] = TitleTransfer.deal_title_tail(item_title)
        except Exception, e:
            log.error('generate_adg_title_list error, shop_id=%s, item_id=%s, e=%s' % (shop_id, item_id, e))
            adg_title = TitleTransfer.deal_title_tail(item_title)
            adg_title_list = [adg_title, adg_title]
        return adg_title_list

    # 根据宝贝词根和宝贝标题来生成创意标题
    @staticmethod
    def generate_adg_title(shop_id, item_id, creative_no = 1):
        title_word_list = []
        title_sub_list = [] # 标题段落组合公式为 标题修饰词+属性词+卖点词+产品词
        title_len = 0 # 创意标题汉字个数不超过20
        adg_title = ''
        try:
            from apps.subway.models import Item
            item = Item.objects.get(shop_id = shop_id, item_id = item_id)
#             item.delete_item_cache() # 测试用，上线注释掉
            prdtword_list = [word for word, hot in item.get_prdtword_hot_list()][:3]
            if not prdtword_list:
                return TitleTransfer.generate_adg_title_list(shop_id, item_id, item.title)[1]

            # 产品词
            for prdtword in prdtword_list:
                word_len = get_char_num(prdtword)
                if prdtword in title_word_list or title_len + word_len > 20:
                    continue
                title_sub_list.append([prdtword])
                title_word_list.append(prdtword)
                title_len += word_len
            title_sub_len = len(title_sub_list) # 标题分段数
            title_sub_index = 0 # 当前需要加词的分段索引
            end_flag = False # 组合结束标志

            # 卖点词
            for saleword in item.sale_word_list:
                word_len = get_char_num(saleword)
                if saleword in title_word_list:
                    continue
                if title_len + word_len > 20:
                    end_flag = True
                    break
                title_sub_list[title_sub_index].insert(0, saleword)
                title_sub_index = title_sub_index + 1 if title_sub_index < title_sub_len - 1 else 0
                title_word_list.append(saleword)
                title_len += word_len

            # 属性词
            if not end_flag:
                propword_hot_list = item.get_propword_hot_list()[:6]
                if creative_no == 0:
                    propword_hot_list = propword_hot_list[:4] # 第一个创意标题中的宝贝标题分量稍多
                for propword, hot in propword_hot_list:
                    word_len = get_char_num(propword)
                    if propword in title_word_list:
                        continue
                    if title_len + word_len > 20:
                        end_flag = True
                        break
                    title_sub_list[title_sub_index].insert(0, propword)
                    title_sub_index = title_sub_index + 1 if title_sub_index < title_sub_len - 1 else 0
                    title_word_list.append(propword)
                    title_len += word_len

            # 标题修饰词
            if not end_flag:
                title_sub_index = 0 # 一般第一个标题词元会是品牌或者年份
                for dcrtword in item.pure_title_word_list:
                    word_len = get_char_num(dcrtword)
                    if dcrtword in title_word_list:
                        continue
                    if title_len + word_len > 20:
                        end_flag = True
                        break
                    title_sub_list[title_sub_index].insert(0, dcrtword)
                    title_sub_index = title_sub_index + 1 if title_sub_index < title_sub_len - 1 else 0
                    title_word_list.append(dcrtword)
                    title_len += word_len

            if title_len <= 19:
                adg_title = ' '.join([''.join(title_sub) for title_sub in title_sub_list])
            else:
                adg_title = ''.join([''.join(title_sub) for title_sub in title_sub_list])
            return adg_title
        except Exception, e:
            log.error('generate_adg_title error, shop_id=%s, item_id=%s, e=%s' % (shop_id, item_id, e))
            return ''

    # 根据宝贝词根来生成推荐标题
    @staticmethod
    def generate_rec_title(shop_id, item_id):
        title_word_list = []
        title_sub_list = [] # 标题段落组合公式为 修饰词+属性词+卖点词+产品词
        title_len = 0 # 宝贝标题汉字个数不超过30
        rec_title = ''
        try:
            from apps.subway.models import Item
            item = Item.objects.get(shop_id = shop_id, item_id = item_id)
#             item.delete_item_cache() # 测试用，上线注释掉
            prdtword_list = [word for word, hot in item.get_prdtword_hot_list()][:3]
            if not prdtword_list:
                return '', []

            # 产品词
            for prdtword in prdtword_list:
                word_len = get_char_num(prdtword)
                if prdtword in title_word_list or title_len + word_len > 30:
                    continue
                title_sub_list.append([prdtword])
                title_word_list.append(prdtword)
                title_len += word_len
            title_sub_len = len(title_sub_list) # 标题分段数
            title_sub_index = 0 # 当前需要加词的分段索引
            end_flag = False # 组合结束标志

            # 卖点词
            for saleword in item.sale_word_list:
                word_len = get_char_num(saleword)
                if saleword in title_word_list or word_len > 8:
                    continue
                if title_len + word_len > 30:
                    end_flag = True
                    break
                title_sub_list[title_sub_index].insert(0, saleword)
                title_sub_index = title_sub_index + 1 if title_sub_index < title_sub_len - 1 else 0
                title_word_list.append(saleword)
                title_len += word_len

            # 属性词
            if not end_flag:
                propword_hot_list = item.get_propword_hot_list()[:6]
                for propword, hot in propword_hot_list:
                    word_len = get_char_num(propword)
                    if propword in title_word_list:
                        continue
                    if title_len + word_len > 30:
                        end_flag = True
                        break
                    title_sub_list[title_sub_index].insert(0, propword)
                    title_sub_index = title_sub_index + 1 if title_sub_index < title_sub_len - 1 else 0
                    title_word_list.append(propword)
                    title_len += word_len

            # 修饰词
            if not end_flag:
                for dcrtword, hot in item.get_dcrtword_hot_list():
                    word_len = get_char_num(dcrtword)
                    if dcrtword in title_word_list or word_len > 8:
                        continue
                    if title_len + word_len > 30:
                        end_flag = True
                        break
                    title_sub_list[title_sub_index].insert(0, dcrtword)
                    title_sub_index = title_sub_index + 1 if title_sub_index < title_sub_len - 1 else 0
                    title_word_list.append(dcrtword)
                    title_len += word_len

            if title_len <= 29:
                rec_title = ' '.join([''.join(title_sub) for title_sub in title_sub_list])
            else:
                rec_title = ''.join([''.join(title_sub) for title_sub in title_sub_list])
            title_word_list = []
            for word_list in title_sub_list:
                title_word_list += word_list
            return rec_title, ChSegement.split_title_new_to_list(''.join(title_word_list))
#             return rec_title, title_word_list
        except Exception, e:
            log.error('generate_rec_title error, shop_id=%s, item_id=%s, e=%s' % (shop_id, item_id, e))
            return '', []

    @staticmethod
    def transfer_itemtitle_2_adgptitle(title, cat_item_dic = None):
        result_title = title
        if title:
            temp_title = TitleTransfer.remove_noneed_words(title)
            result_title = TitleTransfer.deal_title_tail(temp_title)
            return result_title

        # 将title到词库那边进行分词分割，分割后，按照流量大小排序回来
        if cat_item_dic:
            tmp_dic = {}
            for cat_id, item_list in cat_item_dic.items():
                tmp_list = []
                for item in item_list:
                    item.title = TitleTransfer.remove_noneed_words(item.title)
                    tmp_list.append((item.num_id, item.title))
                tmp_dic[cat_id] = tmp_list
            try:
                split_result = ChSegement.split_title_from_cat(cat_item_dic = tmp_dic)
            except Exception, e:
                log.error('split title from cat error:%s' % (e))
                split_result = None
            new_title_dic = {}
            if split_result:
                for tl in split_result.result:
                    new_title_dic[tl[0]] = tl[1]

            for cat_id, item_list in cat_item_dic.items():
                for item in item_list:
                    temp_title = item.title
                    if new_title_dic.has_key(item.num_id):
                        temp_title = new_title_dic[item.num_id]
                    if temp_title.count(' ') > item.title.count(' '):
                        item.adg_title = TitleTransfer.deal_title_tail(temp_title)
                    else:
                        item.adg_title = TitleTransfer.deal_title_tail(item.title)
        return result_title
