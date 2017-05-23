# coding=UTF-8

'''
Created on 2016-1-7

@author: YRK
'''
import json
import base
from apps.ncrm.models import XFGroupPerformance
from apps.common.biz_utils.utils_dictwrapper import DictWrapper

class DBStore(base.BaseStore):

    def __init__(self):
        self.adapter = XFGroupPerformance
        self.fields = [f.name for f in self.adapter._meta.fields if f.name != "id"]

    def filter(self, xfgroups, start_date, end_date, indicators):
        xfgroups_mapping = {xfg.id: xfg for xfg in xfgroups}
        indicator_mapping = {it.name: it for it in indicators}
        result = {}
        for sp in self.adapter.query_staff_performance(xfgroups_mapping.keys(), indicator_mapping.keys(), start_date, end_date):
            entity = DictWrapper({f:getattr(sp, f) for f in self.fields})
            result.setdefault(xfgroups_mapping[sp.xfgroup_id], {}).setdefault(indicator_mapping[entity.identify], []).append(entity)
        return result

    def get(self, xfgroup, some_date, indicator):
        try:
            sp = self.adapter.objects.get(xfgroup_id = xfgroup.id, result_date = some_date, identify = indicator.name)
            entity = DictWrapper({f:getattr(sp, f) for f in self.fields})
            return entity
        except:
            return None

    def save(self, xfgroup, some_date, indicator, value_list):
        entity, _ = self.adapter.objects.get_or_create(xfgroup_id = xfgroup.id, result_date = some_date, identify = indicator.name)
        entity.data_json = json.dumps(value_list)
        entity.save()
        return DictWrapper({f:getattr(entity, f) for f in self.fields})
