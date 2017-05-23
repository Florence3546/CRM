# coding=UTF-8
from django import forms

class UserListForm(forms.Form):
    shop_id = forms.CharField(label = "店铺ID", required = False)
    user_name = forms.CharField(label = "用户名称", required = False)
    page_no = forms.IntegerField(label = "转到第几页", required = False, widget = forms.HiddenInput())
    def __init__(self, *args, **kwargs):
        super(UserListForm, self).__init__(*args, **kwargs)