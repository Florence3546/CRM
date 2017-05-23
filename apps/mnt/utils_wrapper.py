# coding=UTF-8
import re

from apps.common.utils.utils_datetime import date_2datetime, datetime

RPT_PATTERN = re.compile(r'^([a-z]+)([1-9]{1}|1[0-5]{1})$')

class Wrapper(object):
    """基础包装器，适合通过的模型，主要是绑定报表，比如adg.cost3, adg.roi7，制定一套标准，用于编辑一些全自动配置及改价指令"""

    from apps.subway.models_report import BaseReport
    empty_rpt = BaseReport()

    def __init__(self, obj, rpt_list):
        self.obj = obj
        self.rpt_dict = {rpt.date:rpt for rpt in rpt_list}

    def __getattr__(self, attr_name):
        if attr_name in type(self.obj).__dict__:
            return getattr(self.obj, attr_name)
        elif attr_name in self.obj.__dict__:
            return getattr(self.obj, attr_name)
        else:
            m = re.match(RPT_PATTERN, attr_name)
            if not m:
                raise AttributeError(attr_name)
            else:
                attr, days = m.groups()
                if attr in ['cost', 'pay', 'roi', 'click', 'avgpos', 'favcount', 'impr', 'paycount', 'conv', 'ctr', 'cpc']:
                    days = int(days)
                    return self.get_rpt_attr(attr, days)
                else:
                    raise AttributeError(attr_name)

    def get_rpt_attr(self, attr, days):
        if not hasattr(self.obj, '%s%s' % (attr, days)):
            self.set_rpt_attr(days)
        return getattr(self.obj, '%s%s' % (attr, days))

    def set_rpt_attr(self, days):

        if not hasattr(self.obj, 'cost1'):
            rpt1 = self.get_rpt(1)
            self.obj.cost1 = rpt1.cost
            self.obj.click1 = rpt1.click
            self.obj.impr1 = rpt1.impressions
            self.obj.avgpos1 = rpt1.avgpos
            self.obj.pay1 = rpt1.pay
            self.obj.roi1 = rpt1.roi
            self.obj.paycount1 = rpt1.paycount
            self.obj.conv1 = rpt1.conv
            self.obj.favcount1 = rpt1.favcount
            self.obj.ctr1 = rpt1.ctr
            self.obj.cpc1 = rpt1.cpc

        for i in xrange(2, days + 1):
            if not hasattr(self.obj, 'cost%s' % i):
                temp_rpt = self.get_rpt(i)
                cost = getattr(self.obj, 'cost%s' % (i - 1)) + temp_rpt.cost
                click = getattr(self.obj, 'click%s' % (i - 1)) + temp_rpt.click
                impr = getattr(self.obj, 'impr%s' % (i - 1)) + temp_rpt.impressions
                pay = getattr(self.obj, 'pay%s' % (i - 1)) + temp_rpt.pay
                paycount = getattr(self.obj, 'paycount%s' % (i - 1)) + temp_rpt.paycount
                favcount = getattr(self.obj, 'favcount%s' % (i - 1)) + temp_rpt.favcount
                avgpos = self.obj.avgpos1

                if cost > 0:
                    roi = float(pay) / cost
                    cpc = float(cost) / click
                    conv = float(paycount) * 100 / click
                else:
                    roi = 0.0
                    cpc = 0.0
                    conv = 0.0

                if impr > 0:
                    ctr = float(click) * 100 / impr
                else:
                    ctr = 0.0

                setattr(self.obj, 'cost%s' % i, cost)
                setattr(self.obj, 'click%s' % i, click)
                setattr(self.obj, 'impr%s' % i, impr)
                setattr(self.obj, 'pay%s' % i, pay)
                setattr(self.obj, 'paycount%s' % i, paycount)
                setattr(self.obj, 'favcount%s' % i, favcount)
                setattr(self.obj, 'avgpos%s' % i, avgpos)
                setattr(self.obj, 'roi%s' % i, roi)
                setattr(self.obj, 'cpc%s' % i, cpc)
                setattr(self.obj, 'conv%s' % i, conv)
                setattr(self.obj, 'ctr%s' % i, ctr)

    def get_rpt(self, days):
        last_date = date_2datetime(datetime.date.today() - datetime.timedelta(days = days))
        return self.rpt_dict.get(last_date, self.empty_rpt)
