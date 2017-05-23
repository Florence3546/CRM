# coding=UTF-8

from apps.common.utils.utils_json import json

#===============================================================================
# 与命令行客户端交互的API
#===============================================================================
def get_grammer_dict(request = None):
    """语法字典，通过版本号推送给客户端"""
    VALIDATE_DICT = {'select_adgroup':{'download_kwrpt':{},
                                       'optimize_keywords':{'instrcn_list':('str_list',)},
                                       'add_keywords':{'min_num':('int', 140), 'conf_name':('str', 'auto_change')},
                                       'sync_qscore':{},
                                       'modify_out_limit_price':{},
                                       'init_new_adgroups':{}},
                     'select_account':{},
                     'select_campaign':{},
                     'select_creative':{},
                     'select_keyword':{},
                     }

    return json.dumps(VALIDATE_DICT)

def select_adgroup(query_dict, opt_list, opt_cmd_str, user_id, request = None):
    """基于adgroup生成任务"""
    from apps.crm.models import UserOrder
    from apps.mnt.models import MntTaskMng
    from apps.subway.models_adgroup import adg_coll
    try:
        query_dict = json.loads(query_dict)
        psuser_id = int(user_id)
        adg_list = list(adg_coll.find(query_dict, {'shop_id':1, 'campaign_id':1, '_id':1}))
        if not adg_list:
            return {'result':'查询不到对象，无法操作!'}
        else:
            adg_dict = {}
            for adg in adg_list:
                temp_key = '%s-%s' % (adg['shop_id'], adg['campaign_id'])
                if temp_key not in adg_dict:
                    adg_dict[temp_key] = []
                adg_dict[temp_key].append(adg['_id'])

            uo = UserOrder.create_order(psuser_id = psuser_id, command_detail = opt_cmd_str, query_dict = str(query_dict), from_source = 0)
            if not uo:
                return {'result':'命令已生成！'}
            uo.task_id_list = MntTaskMng.generate_task_bycmd(adg_dict = adg_dict, opt_list = json.loads(opt_list), reporter = uo.id) # 注意：参数中一些int型的，页面上传回来是str，注意在函数中强转
            uo.save()
            return {'result':'命令生成成功！'}
    except Exception, e:
        return {'result':'命令生成失败，原因：%s' % e}
