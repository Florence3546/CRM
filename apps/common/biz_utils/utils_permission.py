# coding=UTF-8

'''
订购用户功能权限码，以及不同版本对应的权限
'''

BASE_CODE = 'A' # 基础功能
ADG_OPTM_CODE = 'B' # 宝贝优化
ADG_ADD_CODE = 'C' # 宝贝选词
DUPICATE_CODE = 'D' # 重复词排查
ATTENTION_CODE = 'E' # 重点关注词
TITLE_OPTM_CODE = 'F' # 标题优化
RANKING_CODE = 'J' # 抢排名
AUTO_RANKING_CODE = 'K' # 自动抢排名
AUTO_MNT_CODE = 'S' # 全自动权限
FULL_MNT_CODE = 'H' # 无限制的全自动权限
CATEGORY_SERVER_CODE = 'I' # 类目专家版标识

# SINGLE_ENGINE_CODE = 'S'
# TWO_ENGINE_CODE = 'G'
# FOUR_ENGINE_CODE = 'H'

V1_CODE = 'ABCF' # 体验版，不能全自动托管、不能抢排名、不能重点关注
V2_CODE = 'ABCDFJS' # 标准版，全自动只有两个托管计划、不能自动抢排名、不能重点关注
V3_CODE = 'ABCDEFHJKS' # 旗舰版，包含全功能
V4_CODE = 'ABCDEFHIJKS' # 类目专家版，I用于标识版本

# ALL_EDIT_CODE = 'F'
# MONITER_CODE = 'H'
# CREATIVE_CODE = 'J'
# NOSEARCH_CODE = 'K'


# PERMS_CODE_DICT = {
#     BASE_CODE:'基础功能',
#     ADG_OPTM_CODE:'宝贝优化',
#     ADG_ADD_CODE:'宝贝选词',
#     DUPICATE_CODE:'重复词排查',
#     ATTENTION_CODE:'我的关注',
#     TITLE_OPTM_CODE:'标题优化',
#     SINGLE_ENGINE_CODE:'单引擎',
#     TWO_ENGINE_CODE:'双引擎',
#     FOUR_ENGINE_CODE:'四引擎',
#     CATEGORY_SERVER_CODE:'类目专家版'
#     # MONITER_CODE:'流量监控',
#     # ALL_EDIT_CODE:'全店优化',
#     # CREATIVE_CODE:'创意管理',
#     # NOSEARCH_CODE:'定向推广',
# }

# V1_CODE = 'ABCDEF' # 手动版
# V2_CODE = 'ABCDEFG' # 双引擎版
# V3_CODE = 'ABCDEFGH' # 四引擎版
# V4_CODE = 'ABCDEFGHI' # 类目专家版


ORDER_VERSION_DICT = {
    'ts-25811-5':(1, '开车精灵基础版'),
    'ts-25811-8':(2, '开车精灵双引擎版'),
    'ts-25811-3':(2, '开车精灵双引擎版'),
    'ts-25811-1':(3, '开车精灵八引擎版'),
    'ts-25811-6':(4, '开车精灵类目专家版'),
    'ts-25811-v9':(5, '开车精灵专家服务版'),
}

QN_ORDER_VERSION_DICT = {
    'FW_GOODS-1921400-1':(1, '千牛试用版'),
    'FW_GOODS-1921400-v2':(2, '千牛标准版'),
    'FW_GOODS-1921400-v3':(3, '千牛旗舰版'),
}

# 功能权限分配
# -- 通用权限 [0-9]
CRM_BASE_CODE = '0' # CRM基础权限
CRM_MNG_CODE = '1' # CRM管理权限：员工事件详情，全网报表趋势图，同步订单, 修改部门内订单, 回收部门内客户，账户页面搜索所有顾问的客户。。。
CRM_DEV_CODE = '2' # CRM研发权限：自动化任务趋势图，删除软件订单
# -- 特定功能权限 [a-zA-Z] 小写权限代表基础权限，大写代表高级权限
AD_BASE_CODE = 'a' # 推广管理中添加广告、公告，查看短信
AD_PUB_CODE = 'A' # 发布广告、公告，发送短信，分发客户
ORDER_MNG_CODE = 'B' # 强行跨部门(纵队)修改订单，QC，市场售前
ROSTER_MNG_CODE = 'C' # 花名册管理功能，部分HR
REPORT_EXPORT_CODE = 'E' # 工作台列表导出权限
MAIN_AD_CODE = 'F' # 首页广告管理权限
APPROVAL_SUBSCRIBE_CODE = 'G' # 进账审计权限
APPROVAL_INCOME_CODE = 'H'
COMMENT_MODIFY_CODE = 'P' # 评论修改权限
XFGROUP_MANAGE_CODE = 'X' # 销服组管理权限

# 角色权限分配
MKT = '0aF'
PRESELLER = '0'
SELLER = '0'
TPAE = '0'
RJJH = '0'
CONSULT = '0'
DESIGNER = '0'
OPTAGENT = '0'
TRAINER = '0'

QC = '01B'
SALELEADER = '01'
TPLEADER = '01'
CONSULTLEADER = '01'
RJJHLEADER = '01'
COMMANDER = '01'

HR = '0C'
DEV = '012aABCEF'
SMANAGER = '012aABCEF'
SUPER = '012aABCEF'


# OTHER_CODE = '0'
# TP_AE_CODE = '01'
# TP_SALE_CODE = '01'
# TP_QC_CODE = '01'
# TP_AM_CODE = '01'
# TP_MNG_CODE = '01'
# CONSULT_CODE = '02'
# DEV_CODE = '03'
# SUPER_CODE = '0123456'
# TP_RJJH_CODE = '05'
# DESIGNER_CODE = '06'
# DES_CONSULT_CODE = '06'

def normalize_perms_code(perms_code_list): # 格式化权限码
    '''注意规范权限码:小写就是强行去掉权限码。如：ABCDcBb => AD'''
    code_list = list(set(''.join(perms_code_list)))
    remove_list = [i for i in code_list if i.islower()]
    for c in remove_list:
        try:
            while True:
                code_list.remove(c)
                code_list.remove(c.upper())
        except ValueError:
            pass
    code_list.sort()
    return ''.join(code_list)

def test_permission(perms_code, user):
    if user.is_anonymous():
        return False
    user_code = user.calc_perms_code()
    for p in perms_code:
        if p not in user_code:
            return False
    return True

def check_perms(perms_code, request):
    from apps.crm.views import get_psuser
    if request and 'psuser_id' in request.session:
        psuser = get_psuser(request)
        return perms_code in psuser.perms
    else: # 这里发现没有带psuser_id时，让它通过，到页面后会有装饰器再定向
        return True

def compute_permission(valid_item_list):
    '''
    at：由于订单接口流控实在太厉害(全网每分钟800次)，故不能以该接口作为权限判断依据，只能根据收费项目来，故有待调整收费项目、营销链接、系统代码
    ts-25811-1  -all-150
    ts-25811-2  -all-150
    ts-25811-3  -A B-50
    ts-25811-4  -all-150-不可订购
    ts-25811-5  -all-10-不可订购
    ts-25811-6  -all-100-类目专家版
    ts-25811-7  -all-20-不可订购
    ts-25811-8  -A B-150
    ts-25811-v9 -all-1000-不可订购
    '''
    perms_code_list = []
    for aus in valid_item_list:
        if aus.item_code == 'ts-25811-1': # 四引擎版
            perms_code_list.append('ABCDEFGH')

        elif aus.item_code == 'ts-25811-2':
            perms_code_list.append('ABCDEFG')

        elif aus.item_code == 'ts-25811-3': # 单引擎
            perms_code_list.append('AS')

        elif aus.item_code == 'ts-25811-4':
            perms_code_list.append('ABCDEFGH') # 类目专家版

        elif aus.item_code == 'ts-25811-5':
            perms_code_list.append('ABCDEFG')

        elif aus.item_code == 'ts-25811-6': # 纯手工低级版
            perms_code_list.append('ABCDEFGHI')

        elif aus.item_code == 'ts-25811-7':
            perms_code_list.append('ABCDEFG')

        elif aus.item_code == 'ts-25811-8': # 双引擎版
            perms_code_list.append('ABCDEFG')

        elif aus.item_code == 'ts-25811-v9':
            perms_code_list.append('ABCDEFGH')

        elif aus.item_code == 'ts-25811-10':
            perms_code_list.append('ABCDEFG')

        elif aus.item_code == 'FW_GOODS-1921400-1': # 基础班
            perms_code_list.append('AS')

        elif aus.item_code == 'FW_GOODS-1921400-v2': # 双引擎版
            perms_code_list.append('ABCDEFG')

        elif aus.item_code == 'FW_GOODS-1921400-v3': # 四引擎版
            perms_code_list.append('ABCDEFGH')
    return perms_code_list
