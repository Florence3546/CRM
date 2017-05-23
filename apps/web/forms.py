# coding=UTF-8
from django import forms

from apps.common.utils.utils_log import log
from apps.subway.models import Campaign
from apps.kwslt.models_cat import Cat

class AdgroupSearchForm(forms.Form):
    def __init__(self, shop_id = None, *args, **kwargs):
        super(AdgroupSearchForm, self).__init__(*args, **kwargs)
        if shop_id:
            campaign_list = list(Campaign.objects.only('campaign_id', 'title').filter(shop_id = shop_id))
            campaign_list.insert(0, {'campaign_id':0, 'title':'全部...'})
            self.fields['campaign_id'] = forms.ChoiceField(label = "推广计划ID", required = False, widget = forms.Select(attrs = {'class':''}))
            self.fields['campaign_id'].choices = [(camp['campaign_id'], camp['title']) for camp in campaign_list]

class RptDaysForm(forms.Form):
    rpt_days = forms.ChoiceField(label = "统计周期", required = True, widget = forms.Select(), choices = ((1, '昨天'), (2, '过去2天'), (3, '过去3天'), (5, '过去5天'), (7, '过去7天'), (10, '过去10天'), (14, '过去14天'), (15, '过去15天')))
    def clean_rpt_days(self):
        return int(self.cleaned_data.get('rpt_days', 1))

class KeywordFilterForm(forms.Form):
    '''精准淘词的表单信息'''
    cat_name = forms.ChoiceField(label = "类目名称", required = False, widget = forms.Select())
    is_get_count = forms.BooleanField(label = "是否是获取词数", required = False, initial = False, widget = forms.HiddenInput())
    include_words = forms.CharField(label = "包含的关键词", required = False, initial = '')

    def __init__(self, adgroup = None, cat_id = None, *args, **kwargs):
        '''根据adgroup初始化form表单'''
        super(KeywordFilterForm, self).__init__(*args, **kwargs)
        if adgroup and cat_id:
            # 获取宝贝的多级类目信息
            try:
                result = Cat.get_ancestral_cats(cat_ids = adgroup.category_ids)
            except Exception, e:
                log.exception('__init__:get_ancestral_cats, e=%s' % (e))
                return

            cat_choice = ()
            for cat in result:
                cat_choice = cat_choice + ((cat[0], cat[-1]),) # tuple中有tuple，千万不要删除逗号
                temp_cat_list = cat[0].split(' ')
                if str(cat_id) == temp_cat_list[-1]:
                    self.fields['cat_name'].initial = cat[0]
            self.fields['cat_name'].choices = cat_choice

class ZoneForm(forms.Form):
    zone = forms.ChoiceField(label = "地域", required = True, widget = forms.Select(), choices = (('', '选地区'), ('localhost', '当地'), ('202.96.0.133', '北京'), ('202.96.199.132', '上海'), ('110.76.46.215', '杭州'), ('202.96.128.143', '广州'), ('202.99.96.68', '天津'), ('218.2.135.1', '南京'), ('61.128.128.68', '重庆'), ('202.103.24.68', '武汉'), ('202.98.96.68', '成都'),
           ('202.96.134.133', '深圳'), ('222.172.200.68', '云南'), ('222.74.242.189', '内蒙'), ('219.149.194.56', '吉林'), ('218.6.145.111', '四川'), ('202.100.96.68', '宁夏'), ('202.102.192.68', '安徽'), ('202.102.134.68', '山东'), ('219.149.190.60', '山西'), ('220.192.32.103', '广东'), ('202.103.224.68', '广西'), ('61.128.99.133', '新疆'), ('202.102.29.3', '江苏'),
           ('202.101.224.68', '江西'), ('202.99.160.68', '河北'), ('202.102.227.68', '河南'), ('202.96.102.3', '浙江'), ('202.100.209.123', '海南'), ('202.103.24.68', '湖北'), ('202.103.100.206', '湖南'), ('61.178.152.40', '甘肃'), ('202.101.115.55', '福建'), ('202.98.224.68', '西藏'), ('119.1.42.35', '贵州'), ('221.202.189.57', '辽宁'), ('124.115.214.58', '陕西'),
           ('202.100.138.68', '青海'), ('202.45.84.58', '香港'), ('202.175.3.8', '澳门'), ('168.95.1.1', '台湾'), ('202.97.224.69', '黑龙江')))

class StrategyForm(forms.Form):
    stgy = forms.ChoiceField(label = "策略类型", required = True, initial = 'routine', widget = forms.RadioSelect(), choices = (('routine', '例行优化'), ('plus', '加价引流'), ('fall', '降价省油')))
    rate = forms.ChoiceField(label = "调价幅度", required = True, initial = 5, widget = forms.Select(), choices = ((0, '--'), (3, '3%'), (5, '5%'), (7, '7%'), (10, '10%'), (15, '15%'), (20, '20%'), (25, '25%'), (30, '30%'), (35, '35%'), (40, '40%')))
    limit = forms.ChoiceField(label = "最高幅度", required = True, initial = 10, widget = forms.Select(), choices = ((3, '0.3元'), (5, '0.5元'), (7, '0.7元'), (10, '1元'), (15, '1.5元'), (20, '2.0元'), (25, '2.5元'), (30, '3.0元'), (35, '3.5元'), (40, '4.0元')))
    rpt_days = forms.ChoiceField(label = "统计天数", required = True, initial = 3, widget = forms.Select(), choices = ((1, '昨天'), (2, '过去2天'), (3, '过去3天'), (5, '过去5天'), (7, '过去7天'), (10, '过去10天'), (11, '过去11天'), (15, '过去15天')))
    def clean_rpt_days(self):
        return int(self.cleaned_data.get('rpt_days', 3))
