# coding=UTF-8

import datetime

from mongoengine.document import Document
from mongoengine.fields import IntField, DateTimeField, ListField, StringField

class UploadRecord(Document):
    """保存用户的操作明细"""
    OPERATOR_CHOICES = ((0, '系统'), (1, '用户'), (2, '技术专家'), (3, '自动托管'), (4, '实时优化'), (5, '一键优化'), (6, '手动抢位'), (7, '自动抢位'), (8, '全店删词'), (9, '创意测试'))

    OP_TYPE_CHOICES = ((1, '计划'), (2, '宝贝'), (3, '创意'), (4, '关键词'))

    DATA_TYPE_CHOICES = ((101, '修改推广状态'), (102, '修改计划名称'), (103, '设置日限额'),
                         (104, '设置投放平台'), (105, '修改分时投放'), (106, '修改投放区域'),
                         (107, '开启自动托管'), (108, '取消自动托管'), (109, '调整计划投入'),
                         (110, '设置关键词限价'), (111, '设置屏蔽词'), (112, '设置托管算法'),
                         (113, '系统优化检查'), (114, '修改实时优化状态'),(115, '关注'),
                         (116, '取消关注'),

                         (201, '添加宝贝'), (202, '删除宝贝'), (203, '修改推广状态'),
                         (204, '修改默认出价'), (205, '修改移动折扣'), (206, '修改托管状态'),
                         (207, '调整宝贝投入'), (208, '设置关键词限价'), (209, '配置产品词'),
                         (210, '设置托管算法'), (211, '设置屏蔽词'), (212, '一键优化'),
                         (213, '修改宝贝标题'),

                         (301, '添加创意'), (302, '删除创意'), (303, '修改创意'),

                         (401, '添加关键词'), (402, '删除关键词'), (403, '删除违规词'),
                         (404, '删除屏蔽词'), (405, '修改关键词')
                         )
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    campaign_id = IntField(verbose_name = "计划ID")
    adgroup_id = IntField(verbose_name = "广告组ID")
    item_name = StringField(verbose_name = "宝贝名称")
    op_type = IntField(verbose_name = "操作父类别", choices = OP_TYPE_CHOICES, required = True) # 操作类型父编号
    data_type = IntField(verbose_name = "操作子类别", choices = DATA_TYPE_CHOICES, required = True) # 操作类型子编号
    detail_list = ListField(verbose_name = "操作明细", default = [])
    opter = IntField(verbose_name = "操作者类型", choices = OPERATOR_CHOICES, default = 3)
    opter_name = StringField(verbose_name = "操作者名字", default = '')
    opt_time = DateTimeField(verbose_name = "操作时间", default = datetime.datetime.now)

    meta = {'collection':'subway_opt_history', 'indexes':['campaign_id', 'adgroup_id', 'op_type', 'opt_time'], "shard_key":('shop_id',)}

    RESERVED_DAYS = 90

    # 根据id从CHOICES中获取text
    @staticmethod
    def get_choices_text(choices, cid):
        text = ''
        for cho in choices:
            if cid in cho:
                text = cho[1]
                break
        return text

    @staticmethod
    def full_del_kw(shop_id, adgroup_id):
        """获取带有行业数据的已删除的词"""
        from apps.common.biz_utils.utils_tapitools import get_kw_g_data
        kw_list = []
        upload_records = UploadRecord.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id, data_type__in = [402, 403, 404]).order_by('-opt_time')
        for upload_record in upload_records:
            kw_list.append(upload_record.word.lower())
        gdata_dict = get_kw_g_data(kw_list)

        for upload_record in upload_records:
            temp_word = str(upload_record.word.lower())
            if gdata_dict.has_key(temp_word):
                upload_record.g_ctr = gdata_dict[temp_word].g_ctr
                upload_record.g_click = gdata_dict[temp_word].g_click
                upload_record.g_cpc = format(gdata_dict[temp_word].g_cpc / 100.0, '.2f')
                upload_record.g_competition = gdata_dict[temp_word].g_competition

        return upload_records

    @classmethod
    def clean_outdated(cls):
        """清除过期数据"""
        cls._get_collection().remove({'opt_time': {'$lte': datetime.datetime.now() - datetime.timedelta(days = cls.RESERVED_DAYS)}})
        return True

uprcd_coll = UploadRecord._get_collection()
