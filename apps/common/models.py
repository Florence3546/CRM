# coding=UTF-8

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models

from apps.common.utils.utils_log import log
from apps.common.utils.utils_cacheadpter import CacheAdpter


class Config(models.Model):
    key = models.CharField(verbose_name = 'key', max_length = 50, default = '', help_text = '必须按app_name.module_name组织')
    sub_key = models.CharField(verbose_name = '子key', max_length = 50, default = '', blank = True, help_text = '可以为空，用于一个大配置项下的子配置项')
    value = models.CharField(verbose_name = 'value', max_length = 5000, default = '', help_text = """是一个expression字符串，任何可以被eval函数调用的字符串，如：1；1.1；int('x')；x>123 and y<=33；[1,2,3,4]；{'x':1,'y':3,'z':2} """)
    extra = models.CharField(verbose_name = '额外数据', max_length = 300, default = '', blank = True, help_text = '用于为配置项添加其他辅助数据，如：因为cpc小于%s元并大于%s元，所以加价%s%%到%s元')
    shop_id = models.CharField(verbose_name = '店铺ID', max_length = 15, default = '', blank = True)
    help = models.CharField(verbose_name = '帮助信息', max_length = 100, blank = True, default = '配置项说明信息')

    def save(self, force_insert = False, force_update = False, *args, **kwargs):
        the_key = '%s+%s+%s' % (self.key, self.sub_key, self.shop_id)
        CacheAdpter.delete(the_key, 'default')
        return super(Config, self).save(force_insert, force_update, *args, **kwargs)

    @staticmethod
    def get(key, sub_key = '', shop_id = '', fuzzy_key = False):
        the_key = '%s+%s+%s' % (key, sub_key, shop_id)
        if CacheAdpter.get(the_key, 'default'):
            return CacheAdpter.get(the_key, 'default')
        items = None
        if sub_key:
            if shop_id:
                if fuzzy_key:
                    items = Config.objects.filter(key__contains = key, sub_key__contains = sub_key, shop_id = shop_id)
                else:
                    items = Config.objects.filter(key = key, sub_key = sub_key, shop_id = shop_id)
            if not items: # 没有传入shop_id 或者 传入了shop_id但是没有对应shop_id的配置项
                if fuzzy_key:
                    items = Config.objects.filter(key__contains = key, sub_key__contains = sub_key)
                else:
                    items = Config.objects.filter(key = key, sub_key = sub_key)
        else:
            if shop_id:
                if fuzzy_key:
                    items = Config.objects.filter(key__contains = key, shop_id = shop_id)
                else:
                    items = Config.objects.filter(key = key, shop_id = shop_id)
            if not items: # 没有传入shop_id 或者 传入了shop_id但是没有对应shop_id的配置项
                if fuzzy_key:
                    items = Config.objects.filter(key__contains = key)
                else:
                    items = Config.objects.filter(key = key)
        item_list = []
        for i in items:
            try:
                i.value = i.value.strip()
                if i.value == '':
                    i.value = "''"
                i.value = eval(i.value)
            except Exception, e:
                i.value = '%s' % (i.value)
            item_list.append(i)
        if len(item_list) == 0:
            return None
        elif len(item_list) == 1:
            CacheAdpter.set(the_key, item_list[0], 'default', 60 * 60 * 12)
        else:
            CacheAdpter.set(the_key, item_list, 'default', 60 * 60 * 12)
        return CacheAdpter.get(the_key, 'default')

    @staticmethod
    def get_value(key, sub_key = '', shop_id = '', fuzzy_key = False, default = None):
        item_list = Config.get(key, sub_key, shop_id, fuzzy_key)
        if item_list == None:
            return default
        if not isinstance(item_list, list):
            return item_list.value
        elif len(item_list) == 1:
            return item_list[0].value
        else:
            return [item.value for item in item_list]

    @staticmethod
    def get_help(key, sub_key = '', shop_id = '', default = ""):
        item_list = Config.get(key, sub_key, shop_id)
        if item_list == None:
            return default
        if not isinstance(item_list, list):
            return item_list.help
        elif len(item_list) == 1:
            return item_list[0].help
        else:
            return [item.help for item in item_list]

@receiver(post_save, sender = Config)
def set_log_level(sender, **kwargs):
    '''不重启web服务，动态修改日志打印级别，以方便系统调试'''
    config = kwargs['instance']
    if config.key == 'common.SYS_LOG_LEVEL' and (config.value.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']):
        log.setLevel(config.value.upper())
        log.error('SYS_LOG_LEVEL set success, SYS_LOG_LEVEL=========%s(%s)' % (config.value.upper(), log.getEffectiveLevel()))
