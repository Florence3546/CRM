# coding=UTF-8

'''
Created on 2016-1-7

@author: YRK
'''
import json
import base
from apps.ncrm.models import StaffPerformance
from apps.common.biz_utils.utils_dictwrapper import DictWrapper

class DBStore(base.BaseStore):

    def __init__(self):
        self.adapter = StaffPerformance
        self.fields = [ f.name for f in self.adapter._meta.fields if f.name != "id"]

    def filter(self, psusers, start_date, end_date, indicators):
        psusers_mapping = {pu.id :pu for pu in psusers}
        indicator_mapping = {it.name :it for it in indicators}
        result = {}
        for sp in self.adapter.query_staff_performance(psusers_mapping.keys(), \
                                                       indicator_mapping.keys(), start_date, end_date):
            entity = DictWrapper({ f:getattr(sp, f) for f in self.fields})
            result.setdefault(psusers_mapping[sp.psuser_id], {})\
                    .setdefault(indicator_mapping[entity.identify], [])\
                        .append(entity)
        return result

    def get(self, psuer, some_date, indicator):
        try:
            sp = self.adapter.objects.get(psuser_id = psuer.id, result_date = some_date, \
                                    identify = indicator.name)
            entity = DictWrapper({ f:getattr(sp, f) for f in self.fields})
            return entity
        except:
            return None

    def save(self, psuer, some_date, indicator, value_list):
        entity, _ = self.adapter.objects.get_or_create(psuser_id = psuer.id, result_date = some_date, \
                                           identify = indicator.name)
        entity.data_json = json.dumps(value_list)
        entity.save()
        return DictWrapper({ f:getattr(entity, f) for f in self.fields})