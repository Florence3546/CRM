# coding=UTF-8

from apps.alg.strategy import StrategyFactory

class AdgroupCheck():
    def __init__(self):
        self.click_score = 0
        self.ctr_score = 0
        self.cvr_score = 0
        self.ppc_score = 0

    def check(self, adg_wrapper, last_opt_rec):
        click_new = adg_wrapper.analyze_result.get('kw_click3', 0)
        click_old = last_opt_rec.analyze_result.get('kw_click3', 0)
        self.click_score = 1.0 * (click_new - click_old) / click_old if click_old else 0

        ctr_new = adg_wrapper.analyze_result.get('kw_click3', 0)
        ctr_old = last_opt_rec.analyze_result.get('kw_click3', 0)
        self.ctr_score = 1.0 * (ctr_new - ctr_old) / ctr_old if ctr_old else 0

        cvr_new = adg_wrapper.analyze_result.get('kw_cvr3', 0)
        cvr_old = last_opt_rec.analyze_result.get('kw_cvr3', 0)
        self.cvr_score = 1.0 * (cvr_new - cvr_old) / cvr_old if cvr_old else 0

        ppc_new = adg_wrapper.analyze_result.get('kw_ppc3', 0)
        ppc_old = last_opt_rec.analyze_result.get('kw_ppc', 0)
        self.ppc_score = 1.0 * (ppc_old - ppc_new) / ppc_new if ppc_old else 0

        impact_factor_dict = StrategyFactory().get(name = last_opt_rec.strategy).get_impact_factor()
        k1 = impact_factor_dict.get('click', 1.0)
        k2 = impact_factor_dict.get('ctr', 1.0)
        k3 = impact_factor_dict.get('cvr', 1.0)
        k4 = impact_factor_dict.get('cpc', 1.0)
        score = (self.click_score * k1 + self.ctr_score * k2 + self.cvr_score * k3 + self.ppc_score * k4) / (k1 + k2 + k3 + k4)
        return score

    def check_adgroup(self, opt_rec_list):
        return 0
