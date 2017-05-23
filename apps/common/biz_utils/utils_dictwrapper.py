# coding=UTF-8
import re

RPT_PATTERN = re.compile(r'^([a-z]+)([1-9]{1}|1[0-5]{1})$')


class DictWrapper(dict):

    def __getattr__(self, name):
        try:
            return super(DictWrapper, self).__getitem__(name)
        except KeyError:
            raise AttributeError("key %s not found" % name)

    def __setattr__(self, name, value):
        super(DictWrapper, self).__setitem__(name, value)

    def __delattr__(self, name):
        super(DictWrapper, self).__delitem__(name)

    def hasattr(self, name):
        return name in self

    @classmethod
    def load_dict(cls, org_data):
        """支持将嵌套的dict转成wrapper, e.g.:
        test_dict = {'a':{'b':1,'c':[2,{'e':3}],'f':{'g':4}}}
        ss = DictWrapper.load_dict(test_dict)
        print ss.a.c[0].e
        print ss.a.b
        """
        if isinstance(org_data, dict):
            dr = {}
            for k,v in org_data.items():
                dr.update({k:cls.load_dict(v)})
            return cls(dr)
        elif isinstance(org_data, (list, tuple)):
            return [cls.load_dict(i) for i in org_data]
        else:
            return org_data


class KeywordGlobal(DictWrapper):

    def __init__(self, g_pv = 0, g_click = 0, g_competition = 0, g_cpc = 0, g_coverage = 0, g_roi = 0, g_paycount = 0):
        self.g_pv = g_pv
        self.g_click = g_click
        self.g_competition = g_competition
        self.g_cpc = g_cpc
        self.g_coverage = g_coverage
        self.g_roi = g_roi
        self.g_paycount = g_paycount

    @property
    def g_ctr(self):
        '''返回全网点击率'''
        if self.g_click and self.g_pv:
            return self.g_click * 100.0 / self.g_pv
        return 0.00
