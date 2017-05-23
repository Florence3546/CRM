# coding=UTF-8

'''
Created on 2015-12-30

@author: YRK
'''

import itertools

from .indicators import RATE, NUMBER, AVG_NUMBER

class Report(object):

    def __init__(self, psuser_list, time_scope):
        self.time_scopes = time_scope
        self.psuser_list = psuser_list if isinstance(psuser_list, list) else [psuser_list]
        self.child_list = []

    def __iter__(self):
        return iter(self.child_list)

    @property
    def is_combination(self):
        return len(self.child_list) > 0

    def calc_report(self, indicators, loader, is_force = False):
        if not hasattr(self, '_calc_report') or is_force:
            result = {}
            customers = list(itertools.chain(*[loader.load_customers_bystaff(psuser.id) for psuser in self.psuser_list]))
            for indicator in indicators:
                if callable(indicator.calc_func):
                    selected_customers , value = indicator.calc_func(customers, *self.time_scopes)
                    result.update({indicator.name:value})
            self._calc_report = result
        return self._calc_report

    def hung_on_report(self, indicators, loader, is_force = False):
        if self.is_combination:
            result = {}
            for rpt in self:
                rpt.hung_on_report(indicators, loader, is_force)

                for indicator in indicators:
                    if indicator.name in rpt.report:
                        if indicator.name not in result:
                            result[indicator.name] = rpt.report[indicator.name]
                        else:
                            result[indicator.name] += rpt.report[indicator.name]

            size = len(self.child_list)
            for indicator in indicators:
                if indicator.name in result and indicator.val_type in (RATE, AVG_NUMBER) :
                    result[indicator.name] = round(result[indicator.name] / size, 2)

            self.report = result
        else:
            self.report = self.calc_report(indicators, loader, is_force)

    def add(self, first, *args):
        self.child_list.append(first)
        self.child_list.extend(args)
        return True

    def to_dict(self):
        result = {
#                     'psuser_id':self.psuser.id if self.psuser else 0,
                    'psuser_name_cn':self.psuser_list[0].name_cn if len(self.psuser_list) == 1 else "所有",
                    'time_scope':[self.time_scopes[0].strftime("%m-%d"), self.time_scopes[1].strftime("%m-%d")],
                    'report':self.report
                  }

        if self.is_combination:
            report_list = [ rpt.to_dict() for rpt in self]
            result.update({"report_list":report_list})

        return result