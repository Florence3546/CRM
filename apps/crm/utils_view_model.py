# coding=UTF-8
from django.template.context import RequestContext

class CRMViewRequestContext(RequestContext):
    def __init__(self, request, dict = None, processors = None, current_app = None, use_l10n = None):
        # 此处继承沿袭了RequestContext 的深度继承方式
        self.processors = [] if not processors else processors
        self.processors.extend(self.get_processors())
        RequestContext.__init__(self, request, dict , self.processors, current_app, use_l10n)

    def crm_view_processor(self, request):
#         oper_model_type = request.session.get('oper_model_type', '')
#         if oper_model_type:
#             return {'oper_model_type':oper_model_type}
        return {}

    def get_processors(self):
        return [self.crm_view_processor]



