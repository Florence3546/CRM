# coding=UTF-8
from django.contrib import admin
from django import forms

from apps.ncrm.models import PSUser, Customer, XFGroup


class PSUserEditForm(forms.ModelForm):
    password = forms.CharField(label = "密码", widget = forms.PasswordInput(), help_text = "如果用户设置过密码，输入0避免密码被重新修改。新建用户时，不允许设置为0！")

    class Meta:
        model = PSUser
        exclude = []

class PSUserAdmin(admin.ModelAdmin):
    list_filter = ('position',)
    list_display = ('name', 'name_cn', 'position', 'phone', 'qq', 'ww', 'now_load', 'weight')
    search_fields = ('name', 'name_cn', 'position', 'ww')
    form = PSUserEditForm

    def save_model(self, request, obj, form, change):
        form_psd = form.cleaned_data['password']
        if form_psd in ['0', 0]:
            psuser = PSUser.objects.get(pk = obj.pk)
            obj.password = psuser.password
            obj.save()
        else:
            import hashlib
            psd = hashlib.md5(form_psd).hexdigest()
            obj.password = psd
            obj.save()
admin.site.register(PSUser, PSUserAdmin)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('nick', 'is_b2c', "category", 'address', 'qq', 'ww')
    search_fields = ('nick',)

admin.site.register(Customer, CustomerAdmin)


# class XFGroupaEditForm(forms.ModelForm):
#     consult = forms.ModelChoiceField(label='顾问', required = True, queryset = PSUser.objects.filter(position = 'CONSULT').order_by('name_cn'))
#     seller = forms.ModelChoiceField(label='销售', required = True, queryset = PSUser.objects.filter(position__in = ['CONSULT', 'SELLER']).order_by('-position', 'name_cn'))

#     class Meta:
#         model = XFGroup
#         exclude = []

# class XFGroupAdmin(admin.ModelAdmin):
#     list_display = ('consult', 'seller')
#     form = XFGroupaEditForm

# admin.site.register(XFGroup, XFGroupAdmin)
