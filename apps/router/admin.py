# coding=UTF-8
from django.contrib import admin
from django import forms

from apps.router.models import (User, Port, Shop, ArticleUserSubscribe, ArticleItem,
                                AdditionalPermission)

class UserForm(forms.ModelForm):
    password = forms.CharField(label = "密码", widget = forms.PasswordInput(), help_text = "如果用户设置过密码，输入0避免密码被重新修改。新建用户时，不允许设置为0！")

    class Meta:
        model = User
        exclude = []

class UserAdmin(admin.ModelAdmin):
    list_display = ('nick', 'shop_id', 'session', 'perms_code', 'shop_type', 'date_joined', 'reg_date', 'select_count')
    search_fields = ('nick', 'shop_id')
    form = UserForm

    def save_model(self, request, obj, form, change):
        form_psd = form.cleaned_data['password']
        if form_psd in ['0', 0]:
            user = User.objects.get(pk = obj.pk)
            obj.set_password(user.password)
            obj.save()
        else:
            obj.set_password(form_psd)
            obj.save()
admin.site.register(User, UserAdmin)

class PortAdmin(admin.ModelAdmin):
    list_display = ('domain', 'back_domain', 'now_load', 'max_load', 'all_load', 'type', 'note')
    search_fields = ('domain', 'back_domain', 'type')
    list_filter = ('type',)
admin.site.register(Port, PortAdmin)

class ShopAdmin(admin.ModelAdmin):
    list_display = ('sid', 'nick', 'cid', 'item_score', 'service_score', 'delivery_score', 'created')
    search_fields = ('sid', 'nick')
admin.site.register(Shop, ShopAdmin)

class ArticleUserSubscribeAdmin(admin.ModelAdmin):
    list_display = ('nick', 'article_code', 'item_code', 'deadline')
    search_fields = ('nick', 'article_code', 'item_code')
    ordering = ('deadline',)
admin.site.register(ArticleUserSubscribe, ArticleUserSubscribeAdmin)

class ArticleItemAdmin(admin.ModelAdmin):
    list_display = ('article_code', 'article_name', 'item_code', 'item_name', 'perms_code', 'note')
    search_fields = ('item_code',)
    ordering = ('article_code',)

    def save_model(self, request, obj, form, change):
        obj.save()
        ArticleItem.refresh_item_dict() # admin保存的时候，清除缓存

admin.site.register(ArticleItem, ArticleItemAdmin)

class AdditionalPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'perms_code', 'effectline', 'deadline')
    search_fields = ('user__username', 'perms_code')
admin.site.register(AdditionalPermission, AdditionalPermissionAdmin)

# class PointAdmin(admin.ModelAdmin):
#     list_display = ('nick_1', 'nick_2', 'order_version', 'order_cycle', 'point_1', 'point_2', 'create_time')
#     search_fields = ('nick_1', 'nick_2')
# admin.site.register(Point, PointAdmin)

# class LotteryAdmin(admin.ModelAdmin):
#     list_display = ('reminder_flag', 'exec_model', 'extraction_flag', 'award_type', 'create_time', 'last_show_time', 'user')
#     search_fields = ('user__username', 'exec_model', 'reminder_flag', 'extraction_flag', 'award_type')
#     ordering = ('-create_time',)
#     raw_id_fields = ('user',)
# admin.site.register(LotteryInfo, LotteryAdmin)
