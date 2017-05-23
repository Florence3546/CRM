# coding=UTF-8

import datetime

from mongoengine.document import Document
from mongoengine.errors import DoesNotExist
from mongoengine.fields import IntField, DateTimeField, StringField, ListField, BooleanField

from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.common.cachekey import CacheKey
from apps.subway.models_campaign import Campaign
from apps.subway.models_adgroup import Adgroup

KLASS_DICT = {'0':['Account', 'shop_id'], '1':['Campaign', 'campaign_id'], '2':['Adgroup', 'adgroup_id']}
class PsMessage(Document):
    MESSAGE_TYPE_CHOICES = ((0, '备注'), (1, '留言')) # 备注是给公司内部人员看的， 留言是给客户看的
    OBJECT_TYPE_CHOICES = ((0, '帐户'), (1, '计划'), (2, '宝贝'))
    LEVEL_CHOICES = (('error', '错误(error)：系统出现故障时使用此消息通知用户'), ('success', '成功(success)：系统成功完成了某项任务'),
                     ('info', '信息(info)：需要用户关注的某些信息'), ('alert', '警告(alert)：需要用户避免危险操作的提示'))

    level = StringField(verbose_name = "消息级别", choices = LEVEL_CHOICES, max_length = 10, default = 'info')
    psuser_id = IntField(verbose_name = "消息发送者", required = True)
    shop_id = IntField(verbose_name = "店铺编号", required = True)
    message_type = IntField(verbose_name = "消息类型", choices = MESSAGE_TYPE_CHOICES, default = 0, required = True)
    object_type = IntField(verbose_name = "消息对象类型", choices = OBJECT_TYPE_CHOICES, default = 0, required = True)
    object_id = IntField(verbose_name = "消息对象ID", required = True)
    last_modified = DateTimeField(verbose_name = "修改时间", default = datetime.datetime.now)
    title = StringField(verbose_name = "标题", max_length = 30, default = None)
    content = StringField(verbose_name = '消息内容', default = '')
    is_prompt = BooleanField(verbose_name = "是否提示", default = True)

    meta = {'collection':'crm_message', 'indexes':[], 'shard_key':('shop_id',), }

    @staticmethod
    def need_2handle(shop_id, object_type, object_id):
        '''检查是否已有过目标对象的信息以及是否被处理过'''
        try:
            is_prompt = PsMessage.objects.filter(shop_id = shop_id, object_type = object_type, object_id = object_id, level = 'alert', psuser_id = -1).order_by('-last_modified')[0].is_prompt
            return not is_prompt
        except:
            return False

    @staticmethod
    def bulk_add_msg(msg_type, obj_type, content, obj_list, psuser_id = 9999, title = None, level = 'info'):
        '''批量添加消息,  psuser_id = 9999时表示为系统发送的普通消息，-1表示系统发送的店铺宝贝违规信息'''
        insert_list = []
        klass, klass_id = KLASS_DICT[str(obj_type)]
        now = datetime.datetime.now()
        for i in obj_list:
            if psuser_id == -1 and not PsMessage.need_2handle(shop_id = i['shop_id'], object_type = obj_type, object_id = i['obj_id']):
                continue
            args = {'shop_id':i['shop_id'], klass_id:i['obj_id']}
            try:
                obj = globals()[klass].objects.get(**args)
                obj.set_msg_count(msg_type = msg_type, add_count = 1)
                insert_list.append({'psuser_id':psuser_id, 'shop_id':int(i['shop_id']), 'message_type':msg_type, 'object_type':obj_type,
                                    'object_id':int(i['obj_id']), 'content':content, 'is_prompt':True, 'level':level, 'title':title, 'last_modified':now
                                    })
            except Exception, e:
                log.info('add msg error , object does not exist, obj_type=%s, obj_id=%s, e=%s' % (obj_type, i['obj_id'], e))
                pass
        if insert_list:
            psmsg_coll.insert(insert_list)

    @staticmethod
    def close_msg(shop_id, msg_id):
        try:
            msg = PsMessage.objects.get(id = msg_id)
            if msg.is_prompt:
                msg.is_prompt = False
                msg.save()
                klass, klass_id = KLASS_DICT[str(msg.object_type)]
                args = {'shop_id':shop_id, klass_id:msg.object_id}
                obj = globals()[klass].objects.get(**args)
                obj.set_msg_count(msg_type = msg.message_type, add_count = -1)
                CacheAdpter.delete(CacheKey.WEB_MSG_COUNT % shop_id, 'web')
            return True
        except Exception, e:
            log.error('close msg error, shop_id = %s, e = %s' % (shop_id, e))
            return False

    @staticmethod
    def get_display_msg(msgs):
        from django.core.urlresolvers import reverse
        from apps.ncrm.models import PSUser
        delete_msg_list, user_msg_list, shop_id_list = [], [], []
        psuser_id_list = [msg.psuser_id for msg in msgs]
        psusers = PSUser.objects.filter(id__in = list(set(psuser_id_list)))
        user_dict = {user.id:user.ww for user in psusers}
        for msg in msgs:
            obj_title, jump_url, ww = '', '', ''
            if msg.object_type == 0:
                obj_title = msg.title and msg.title or '直通车账户'
                jump_url = ''
            elif msg.object_type == 1:
                obj = Campaign.objects.get(shop_id = msg.shop_id, campaign_id = msg.object_id)
                obj_title = obj.title
                jump_url = reverse('campaign', kwargs = {'campaign_id':msg.object_id})
            elif msg.object_type == 2:
                try:
                    obj = Adgroup.objects.get(shop_id = msg.shop_id, adgroup_id = msg.object_id)
                    obj_title = obj.item and obj.item.title or ''
                    jump_url = reverse('adgroup_details', kwargs = {'adgroup_id':msg.object_id})
                except DoesNotExist:
                    delete_msg_list.append(msg.id)
                    shop_id_list.append(msg.shop_id)
                    continue

            ww = user_dict.get(msg.psuser_id, '')
            ww = ww or '派生科技' # 有些psuser_id 没有填写旺旺
            user_msg_list.append({'id':'%s' % msg.id, 'is_prompt':msg.is_prompt, 'obj_title':obj_title, 'jump_url':jump_url, 'content':msg.content,
                                  'object_type':msg.get_object_type_display(), 'last_modified':msg.last_modified, 'ww':ww})

        if delete_msg_list:
            PsMessage.objects.filter(id__in = delete_msg_list).delete()
            shop_id_list = list(set(shop_id_list))
            for shop_id in shop_id_list:
                CacheAdpter.delete(CacheKey.WEB_MSG_COUNT % shop_id, 'web')

        return user_msg_list

psmsg_coll = PsMessage._get_collection()


class UserOrder(Document):
    """用户发送的命令"""
    psuser_id = IntField(verbose_name = '用户ID', required = True)
    query_dict = StringField(verbose_name = "操作的宝贝ID列表", required = True)
    command_detail = StringField(verbose_name = "命令详情", required = True)
    task_id_list = ListField(verbose_name = "任务ID列表", default = [])
    from_source = IntField(verbose_name = "生成来源", choices = ((0, '命令行'), (1, '页面')))
    create_time = DateTimeField(verbose_name = "创建时间", default = datetime.datetime.now)
    success_count = IntField(verbose_name = "任务成功个数", default = 0)

    meta = {'db_alias': 'crm-db', 'collection':'crm_userorder', 'indexes':['psuser_id']}

    @classmethod
    def create_order(cls, psuser_id, command_detail, query_dict, from_source):
        last_time = datetime.datetime.now() - datetime.timedelta(minutes = 5) # 5分钟内，如果查询条件、操作、用户都是同一个，则认定重复
        uo_count = cls.objects.filter(psuser_id = psuser_id, command_detail = command_detail, query_dict = query_dict,
                                     from_source = from_source, create_time__gte = last_time).count()
        if uo_count:
            return None
        else:
            return cls.objects.create(psuser_id = psuser_id, command_detail = command_detail, query_dict = query_dict, from_source = from_source)

    @staticmethod
    def task_report(uo_id):
        uo_coll.update({'_id':uo_id}, {'$inc':{'success_count':1}})

uo_coll = UserOrder._get_collection()
