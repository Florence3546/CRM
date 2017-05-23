# coding=UTF-8
from django.contrib import admin

from apps.web.models import Feedback, OrderTemplate, LotteryOrder, MemberStore


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('shop', 'score_str', 'create_time', 'content')
    search_fields = ('shop__nick',)
    raw_id_fields = ('shop',)
    fields = ('shop', 'score_str', 'create_time', 'content')

admin.site.register(Feedback, FeedbackAdmin)

class OrderTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'desc', "version", 'order_type', 'ori_price', 'discount', 'cycle', "param_str")
    search_fields = ('version', 'name', 'cycle', 'discount', 'order_type')
admin.site.register(OrderTemplate, OrderTemplateAdmin)

class LotteryOrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'desc', "version", 'order_type', 'ori_price', 'discount', 'cycle', "param_str")
    search_fields = ('version', 'name', 'cycle', 'discount', 'order_type')
admin.site.register(LotteryOrder, LotteryOrderAdmin)

class MemberStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'desc', "shop_type", 'worth', 'point', 'limit_point')
    search_fields = ('name', 'shop_type')
admin.site.register(MemberStore, MemberStoreAdmin)
