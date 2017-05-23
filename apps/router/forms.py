# -*- coding: utf-8 -*-
from django import forms

class AgentLoginForm(forms.Form):
    username = forms.CharField(label = "代理用户名", required = True)
    password = forms.CharField(label = "代理用户密码", widget = forms.PasswordInput(), required = True)