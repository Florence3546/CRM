# coding=UTF-8

import math


class Diagnostic:
    def __init__(self):
        pass

    def name(self):
        return 'default'

    def diagnose(self, adg_wrapper):
        pass


class HighCostDiagnose(Diagnostic):
    def __init__(self):
        pass

    def name(self):
        return 'cost'

    def diagnose(self, adg_wrapper):
        camp_lastrpt = adg_wrapper.campaign.rpt_list[-1] if adg_wrapper.campaign.rpt_list else None
        if camp_lastrpt and camp_lastrpt.cost * 1.0 < 0.95 * adg_wrapper.campaign.budget:
            return 0
        adg_lastrpt = adg_wrapper.adgroup.rpt_list[-1] if adg_wrapper.adgroup.rpt_list else None
        if not adg_lastrpt:
            return 0
        adg_rpt7 = adg_wrapper.adgroup.kwrpt7
        camp_rpt7 = adg_wrapper.campaign.rpt7
        k = adg_rpt7.roi * 1.0 / camp_rpt7.roi if camp_rpt7.roi else 1.0
        return max(100 - k * 50, 0) # 当宝贝roi>=计划roi的2倍时，判定为宝贝花费不高，其他判定为宝贝roi高


class ClickDiagnose(Diagnostic):
    def __init__(self):
        pass

    def name(self):
        return 'click'

    def diagnose(self, adg_wrapper):
        camp_lastrpt = adg_wrapper.campaign.rpt_list[-1] if adg_wrapper.campaign.rpt_list else None
        if not camp_lastrpt:
            return 50 # 未获取到昨日计划报表，直接判定为计划流量严重不够
        cost_boundary = 100 * min(15 + math.pow(adg_wrapper.campaign.budget * 0.01 - 20, 0.65), 50)
        if camp_lastrpt.cost < cost_boundary:
            return 50 # 当计划花费太小时，判定为所有宝贝流量不够
        cost_boundary2 = 100 * min(18 + math.pow(adg_wrapper.campaign.budget * 0.01 - 20, 0.80) * math.sqrt(adg_wrapper.bid_factor), 120)
        if camp_lastrpt.cost < cost_boundary2:
            return 60 # 当计划流量不够时，判定为所有宝贝流量不够
        # 计划流量足够
        adg_rpt3 = adg_wrapper.adgroup.kwrpt3
        camp_rpt3 = adg_wrapper.campaign.rpt3
        if adg_rpt3.cost >= 0.10 * camp_rpt3.cost or \
            adg_rpt3.click >= 0.10 * camp_rpt3.click or \
            adg_wrapper.adgroup.kwrpt7.roi > adg_wrapper.campaign.rpt7.roi:
            return 100 # 计划流量足够，计划内流量多的adgroup判定流量充足
        return 0 # 计划内流量少的adgroup判定为没有流量


class PPCDiagnose(Diagnostic):
    def __init__(self):
        pass

    def name(self):
        return 'ppc'

    def diagnose(self, adg_wrapper):
        '''返回值越高，说明ppc越高'''
        # 当前出价
        # topkw_price = adgroup_index.value('topkw_ppc')
        kw_price = adg_wrapper.analyze_result.get('kw_ppc', 0)
        # 按照行业均价预估的宝贝出价上限
        eva_price = adg_wrapper.deal_price() * adg_wrapper.category.rpt7.cpc / 1.0
        score1 = min(60 * math.pow(eva_price * 1.0 / kw_price, 0.73697), 100) if kw_price else 100
        # 类目均价
        # price2 = adgroup_index.value('topkw_g_ppc7')
        cat_price = adg_wrapper.bid_factor * adg_wrapper.analyze_result.get('kw_g_ppc', 0)
        score2 = min(60 * math.pow(cat_price * 1.0 / kw_price, 0.73697), 100) if kw_price and cat_price else 100
        # 按照日限额预算的出价上限
        budget_price = adg_wrapper.campaign.budget / 50
        score3 = min(60 * budget_price / kw_price, 100) if kw_price else 100
        score = min(score1, score2)
        return score if score3 > score else (score + score3) / 2.0


class CVRDiagnose(Diagnostic):
    def __init__(self):
        pass

    def name(self):
        return 'cvr'

    def diagnose(self, adg_wrapper):
        cvr7 = adg_wrapper.analyze_result.get('kw_cvr7', 0.1)
        cat_cvr7 = adg_wrapper.category.rpt7.coverage
        return min(60 * math.log(1 + cvr7 * 3.0 / cat_cvr7, 10), 100) if cat_cvr7 else 100


class CTRDiagnose(Diagnostic):
    def __init__(self):
        pass

    def name(self):
        return 'ctr'

    def diagnose(self, adg_wrapper):
        ctr7 = adg_wrapper.analyze_result.get('kw_ctr7', 0.1)
        cat_ctr7 = adg_wrapper.category.rpt7.ctr
        return min(100 * math.log(1 + ctr7 * 3.5 / cat_ctr7, 10), 100) if cat_ctr7 else 100


class QScoreDiagnose(Diagnostic):
    def __init__(self):
        pass

    def diagnose(self, adg_wrapper):
        return 0
