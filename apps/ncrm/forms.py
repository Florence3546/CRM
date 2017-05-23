# coding=UTF-8
from django import forms

from apps.ncrm.models import Customer, PSUser, Subscribe, ARTICLE_CODE_CHOICES, SUBSCRIBE_SOURCE_TYPE_CHOICES, CATEGORY_CHOICES, APPROVAL_STATUS_CHOICES


class LoginForm(forms.Form):
    username = forms.CharField(label = "用户名", required = True)
    password = forms.CharField(label = "密码", widget = forms.PasswordInput(), required = True)

# ARTICLE_CODE_SELECTOR = list(ARTICLE_CODE_CHOICES)
# ARTICLE_CODE_SELECTOR.insert(0, ('', '请选择订购项'))
SUBSCRIBE_SOURCE_TYPE_CHOICES = list(SUBSCRIBE_SOURCE_TYPE_CHOICES)
SUBSCRIBE_SOURCE_TYPE_CHOICES.insert(0, ('', '-成交方式-'))
CATEGORY_SELECTOR = list(CATEGORY_CHOICES)
CATEGORY_SELECTOR.insert(0, ('', '-业务类型-'))
APPROVAL_STATUS_SELECTOR = list(APPROVAL_STATUS_CHOICES)
APPROVAL_STATUS_SELECTOR.insert(0, ('', '-审批状态-'))

class OrderForm(forms.Form):
    # global ARTICLE_CODE_SELECTOR
    nick = forms.CharField(label = "店铺名", required = False)
    # article_code = forms.ChoiceField(label = "订购版本", required = False, widget = forms.Select(attrs = {'class' : 'w140 mr10'}), choices = ARTICLE_CODE_SELECTOR)
    category = forms.ChoiceField(label = "业务类型", required = False, widget = forms.Select(attrs = {'class' : 'w120 mr10'}), choices = CATEGORY_SELECTOR)
    start_date = forms.DateField(label = "订购时间起", required = False)
    end_date = forms.DateField(label = "订购时间止", required = False)
    owner = forms.CharField(label = "所属人", required = False)
    name_cn = forms.CharField(label = "所属人姓名", required = False)
    source_type = forms.ChoiceField(label = "成交方式", required = False, widget = forms.Select(attrs = {'class' : 'w100 mr10'}), choices = SUBSCRIBE_SOURCE_TYPE_CHOICES)
    biz_type = forms.ChoiceField(label = "订单类型", required = False, widget = forms.Select(attrs = {'class' : 'w120 mr10'}), choices = (('', '-订单类型-'), (1, '新订'), (2, '续订'), (3, '升级'), (4, '后台赠送'), (5, '后台自动续订'), (6, '未知'), (7, '自我新订'), (8, '转介绍'), (9, '软件成交'), (10, '进账划分客户'), (11, '店铺提成')))
    approval_status = forms.ChoiceField(label = "审批状态", required = False, widget = forms.Select(attrs = {'class' : 'w100'}), choices = APPROVAL_STATUS_SELECTOR)
    page_no = forms.ChoiceField(label = "页数", required = False, widget = forms.Select(attrs = {'class' : 'w80 r'}), choices = [(i + 1, '第%s页' % (i + 1)) for i in range(50)])
    saler_id = forms.CharField(label = "签单人", required = False)
    operater_id = forms.CharField(label = "操作人", required = False)
    consult_id = forms.CharField(label = "顾问", required = False)
    saler_name = forms.CharField(label="签单人姓名", required=False)
    operater_name = forms.CharField(label="操作人姓名", required=False)
    consult_name = forms.CharField(label="顾问姓名", required=False)

class RecordDistribute(forms.Form):
    psuser_id = forms.CharField(label="分配人ID", required=False)
    psuser_cn = forms.CharField(label="分配人姓名", required=False)
    shop = forms.CharField(label="店铺ID/店铺名", required=False)
    subscribe_id = forms.CharField(label="订单ID", required=False)
    org_list_id = forms.CharField(label="原人员ID", required=False)
    org_list_cn = forms.CharField(label="原人员姓名列表", required=False)
    new_list_id = forms.CharField(label="新人员ID", required=False)
    new_list_cn = forms.CharField(label="新人员姓名列表", required=False)

    order_start_date = forms.DateField(label="订购时间起", required=False)
    order_end_date = forms.DateField(label="订购时间止", required=False)

    distribute_start_date = forms.DateField(label="分配时间起", required=False)
    distribute_end_date = forms.DateField(label="分配时间止", required=False)

    pay_start = forms.IntegerField(label="金额起", required=False)
    pay_end = forms.IntegerField(label="金额止", required=False)

    category = forms.ChoiceField(label="业务类型", required=False, widget=forms.Select(attrs={'class': 'w120 mr10'}),
                                 choices=CATEGORY_SELECTOR)
    page_no = forms.ChoiceField(label="页数", required=False, widget=forms.Select(attrs={'class': 'w80 r mr20'}),
                                choices=[(i + 1, '第%s页' % (i + 1)) for i in range(50)])

class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        exclude = ('create_time', 'udpate_time')

MANUAL_ARTICLE_SELECTOR = ARTICLE_CODE_CHOICES # 修改的时候，移除软件的单子，只能编辑人工单子
class SubscribeForm(forms.ModelForm):
    global MANUAL_ARTICLE_SELECTOR
    article_code = forms.ChoiceField(label = "订购类型", required = True, widget = forms.Select(), choices = MANUAL_ARTICLE_SELECTOR)
    # biz_type = forms.ChoiceField(label = "订单类型", required = True, widget = forms.Select(), choices = ((1, '新订'), (2, '续订'), (3, '升级'), (4, '后台赠送'), (5, '后台自动续订')))

    class Meta:
        model = Subscribe
        exclude = ('shop', 'order_id')

class DateRangeForm(forms.Form):
    start_date = forms.DateField(label = "开始日期", required = True)
    end_date = forms.DateField(label = "结束日期", required = True)


class PSUserForm(forms.ModelForm):
    class Meta:
        model = PSUser
        fields = ('id', 'name_cn', 'birthday', 'gender', 'department', 'position', 'perms', 'ww', 'qq', 'phone')

class PSUserForm2(forms.ModelForm):
    class Meta:
        model = PSUser
        fields = ('name_cn', 'birthday', 'gender', 'ww', 'qq', 'phone')

class UserInfoForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ('qq', 'phone')
