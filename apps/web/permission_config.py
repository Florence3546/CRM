# coding=UTF-8

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from dajax.core import Dajax
from apps.common.utils.utils_log import log
from apps.common.utils.utils_render import render_to_limited
from apps.common.biz_utils.utils_permission import (BASE_CODE, ADG_OPTM_CODE, ADG_ADD_CODE, DUPICATE_CODE, ATTENTION_CODE, TITLE_OPTM_CODE, AUTO_MNT_CODE,
                                          CRM_BASE_CODE, CRM_DEV_CODE, AD_BASE_CODE, CRM_MNG_CODE, ROSTER_MNG_CODE, MAIN_AD_CODE
                                          )


def ajax_default(request, perms_code):
    dajax = Dajax()
    dajax.script("window.location.href='%s';" % (reverse('upgrade_suggest')))
    return dajax

def end_dajax():
    dajax = Dajax()
    return dajax

def view_default(request, perms_code):
    return HttpResponseRedirect(reverse('upgrade_suggest'))

def view_limited(request, perms_code):
    return render_to_limited(request, '亲，您尚未购买该功能，请购买后再使用！')

def ps_view_limited(request):
    return render_to_limited(request, '亲，您没有权限使用该功能，请联系系统管理员！')

AJAX_PERMS_CONFIG = {
    'get_keyword_count':(None, None, 1, ()), # 所有宝贝->显示关键词个数
    'sync_increase_data':(None, None, 1, ()), # 同步下载->全店快速下载
    'submit_feedback':(None, None, 1, ()), # 意见反馈->提交反馈
    'sync_all_data':(None, None, 1, ('data_type',)), # 同步下载  sync_all_data_1:直通车报表数据 sync_all_data_2:直通车基本数据
    'sync_current_adg':(None, None, 1, ()), # 同步当前宝贝
    'curwords_submit':(None, None, 1, ()), # bulk_optomize_curwords_submit:批量优化提交关键词到直通车,smart_optimize_curwords_submit:智能优化提交关键词到直通车
    'batch_add_keywords':(ADG_ADD_CODE, ajax_default, 1, ('href',)), # quick_add_keyword_batch_add_keywords:快速选词->添加关键词,precise_tao_keyword_batch_add_keywords:精准淘词->添加关键词
    'rob_ranking':(ADG_OPTM_CODE, ajax_default, 1, ()), # 开始抢排名
    # 'mnt_campaign_setter':(AUTO_MNT_CODE, ajax_default, 1, ('mnt_type', 'set_flag')), # mnt_campaign_setter_1_0:长尾计划解除托管,mnt_campaign_setter_2_0:重点计划解除托管,mnt_campaign_setter_1_1:长尾计划加入托管,mnt_campaign_setter_2_1:重点计划加入托管
    'quick_oper':(AUTO_MNT_CODE, ajax_default, 1, ('mnt_type', 'stgy')), # quick_oper_1_-1:长尾计划减小投入,quick_oper_2_-1:重点计划减小投入,quick_oper_1_1:长尾计划加大投入,quick_oper_2_1:重点计划加大投入
    'update_prop_status':(AUTO_MNT_CODE, ajax_default, 1, ('mnt_type', 'status')), # update_prop_status_1_0:暂停长尾计划,update_prop_status_2_0:暂停重点计划,update_prop_status_1_1:开启长尾计划,update_prop_status_2_1:开启重点计划
    'behavior_only':(None, end_dajax, 1, ('href', 'data')), # invite_friend_behavior_only_copy_btn 赢取精灵币->我的精灵币->推荐有礼->复制
    'to_attention_list':(ATTENTION_CODE, ajax_default, 1, ()), # 关注词功能
    'to_duplicate_check':(DUPICATE_CODE, None, 1, ()), # 重复词功能
}

VIEW_PERMS_CONFIG = {
    'web_home':(BASE_CODE, view_limited, 1),
    'adgroup_list':(BASE_CODE, view_default, 1),
    'quick_entry':(BASE_CODE, view_default, 1),
    'adgroup_history':(BASE_CODE, view_default, 0),
    'campaign_list':(BASE_CODE, view_default, 1),
    'campaign_history':(BASE_CODE, view_default, 0),
    'all_history':(BASE_CODE, view_default, 0),
    'ztc_health_check':(BASE_CODE, view_default, 1),
    'set_agent':(BASE_CODE, view_default, 0),

    'mnt_campaign':(BASE_CODE, view_default, 1),
    'adgroup_data':(AUTO_MNT_CODE, view_default, 1),
    # 'choose_mnt_campaign':(AUTO_MNT_CODE, view_default, 1),#页面上有特殊提示，无需跳转
    'check_danger_cats':(BASE_CODE, view_default, 1),

    'bulk_optomize':(ADG_OPTM_CODE, view_default, 0),
    'smart_optimize':(ADG_OPTM_CODE, view_default, 0),
    'rob_rank':(ADG_OPTM_CODE, view_default, 0),
    'deleted_keyword':(BASE_CODE, view_default, 1),
    'adgroup_health_check':(ADG_OPTM_CODE, view_default, 1),

    'select_keyword':(ADG_ADD_CODE, view_default, 0),

    'attention_list':(ATTENTION_CODE, view_default, 1),
    'duplicate_check':(DUPICATE_CODE, view_default, 1),
    'title_optimize':(TITLE_OPTM_CODE, view_default, 1),
}

CRM_PERMS_CONFIG = {
    'user_list':(CRM_BASE_CODE, ps_view_limited, 0),
    'crm_account':(CRM_BASE_CODE, ps_view_limited, 0),
    'crm_campaign':(CRM_BASE_CODE, ps_view_limited, 0),
    'crm_adgroup':(CRM_BASE_CODE, ps_view_limited, 0),
    'crm_keyword':(CRM_BASE_CODE, ps_view_limited, 0),
    # 'cf_designer':(CF_DES_CODE, ps_view_limited, 0),
    # 'cf_consult':(CF_CONSULT_CODE, ps_view_limited, 0),
    'common_message':(AD_BASE_CODE, ps_view_limited, 0),
    'right_down_ad':(AD_BASE_CODE, ps_view_limited, 0),
    'sale_link':(AD_BASE_CODE, ps_view_limited, 0),
    'consult_manager':(CRM_MNG_CODE, ps_view_limited, 0),
    'ncrm_psuser_roster':(CRM_BASE_CODE, ps_view_limited, 0),
    'ncrm_add_psuser':(ROSTER_MNG_CODE, ps_view_limited, 0),
    'event_detail':(CRM_MNG_CODE, ps_view_limited, 0),
    'rpt_snap':(CRM_MNG_CODE, ps_view_limited, 0),
    'task_rpt':(CRM_DEV_CODE, ps_view_limited, 0),
    'short_message_manage':(AD_BASE_CODE, ps_view_limited, 0),
    'order_dunning':(MAIN_AD_CODE, ps_view_limited, 0),
}
