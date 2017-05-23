# coding=UTF-8
from django.contrib import admin

from apps.common.models import Config


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'key', 'sub_key', 'value', 'extra', 'shop_id', 'help')
    search_fields = ('key', 'sub_key', 'value', 'extra', 'shop_id', 'help')
    ordering = ('key', 'sub_key',)
admin.site.register(Config, ConfigAdmin)
