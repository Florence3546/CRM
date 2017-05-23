# coding=UTF-8
'''
!!! 警告：执行此脚本前，注释掉相关的提交代码，以及选词入口（耽误时间）
'''


import init_environ
from apps.subway.models_campaign import camp_coll
from apps.alg.interface import auto_optimize_campaign


def get_all_camps():
    camp_cur = camp_coll.find({'online_status': 'online'}, {'_id': 1, 'shop_id': 1})
    return [(camp['shop_id'], camp['_id']) for camp in camp_cur]
#     for camp in camp_cur:
#         yield camp['shop_id'], camp['_id']

def main():
    shop_camps = get_all_camps()
    for shop_id, camp_id in shop_camps:
        auto_optimize_campaign(shop_id, camp_id)

if __name__ == '__main__':
    main()
