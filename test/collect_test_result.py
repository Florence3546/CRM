# coding=UTF-8
'''
'''


import init_environ
from apps.subway.models_campaign import camp_coll
# from apps.alg.interface import auto_optimize_campaign
from apps.alg.models import optrec_coll
from pprint import pprint


# def get_all_camps():
#    camp_cur = camp_coll.find({'online_status': 'online'}, {'_id': 1, 'shop_id': 1})
#    return [(camp['shop_id'], camp['_id']) for camp in camp_cur]
#     for camp in camp_cur:
#         yield camp['shop_id'], camp['_id']

# def main():
    # shop_camps = get_all_camps()
    # for shop_id, camp_id in shop_camps:
    #    auto_optimize_campaign(shop_id, camp_id)

if __name__ == '__main__':
    # main()
    strategy_dict = {}
    command_dict = {}
    modify_dict = {}
    rec_cur = optrec_coll.find({})
    for rec in rec_cur:
        #
        strategy_dict.setdefault(rec.strategy, 0)
        strategy_dict[rec.strategy] += 1
        #
        for k, v in rec.cmd_count.items():
            command_dict.setdefault(k, 0)
            command_dict[k] += int(v)
        #
        for k, v in rec.modify_kw_count['plan'].items():
            modify_dict.setdefault(k, 0)
            modify_dict[k] += int(v)

    pprint(strategy_dict)
    pprint(command_dict)
    pprint(modify_dict)
