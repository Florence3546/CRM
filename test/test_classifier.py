# coding=utf-8

import init_environ
from apps.subway.classifier import IllegalClassifier

from apps.subway.models_keyword import illegal_kw_coll, kw_coll
from apps.subway.models_account import account_coll
from apps.subway.models_adgroup import adg_coll
from apps.router.models import User



def get_illegal_word_list():
    illegal_kw_list = []
    illegal_cusor = illegal_kw_coll.find({})
    for i in illegal_cusor:
        illegal_kw_list.append({'category': i['cat_id'], 'keyword': i['word'], 'shop_type': i['last_name'],  'is_illegal': True})

    return illegal_kw_list

def get_all_word_list():
    total_kw_list = []
    cursor = account_coll.find({}, {'_id': 1})
    shop_id_list = [i['_id'] for i in cursor]
    for shop_id in shop_id_list:
        shop_kw_list = get_shop_keyword_list(shop_id)
        total_kw_list.extend(shop_kw_list)
    return total_kw_list

def get_shop_keyword_list(shop_id):
    try:
        user = User.objects.get(shop_id = shop_id)
        shop_type = user.shop_type
    except User.DoesNotExist:
        shop_type = "unknow"

    shop_kw_list = []
    adg_cursor = adg_coll.find({'shop_id': shop_id}, {'_id': 1, 'category_ids': 1})
    adg_dict = {adg['_id']: adg['category_ids'].split(' ')[0] for adg in adg_cursor }
    kw_cursor = kw_coll.find({'shop_id': shop_id}, {'word': 1, 'adgroup_id': 1, 'audit_status': 1})
    for kw in kw_cursor:
        cat_id = adg_dict.get(kw['adgroup_id'], '0') # 类目未知的case
        is_illegal = kw['audit_status'] == 'audit_reject' and True or False
        shop_kw_list.append({'category': cat_id, 'keyword': kw['word'], 'shop_type': shop_type,  'is_illegal': is_illegal})
    return shop_kw_list


if __name__ == "__main__":
    # illegal_kw_list = get_illegal_word_list()
    # shop_kw_list = get_all_word_list()
    #
    # source_list = shop_kw_list + illegal_kw_list
    #
    # IllegalClassifier.train(source_list)

    print IllegalClassifier.classify('C', '16', u'连衣裙')
    print IllegalClassifier.classify('B', '50008612', u'减肥大麦茶韩国原装')
    print IllegalClassifier.classify('B', '3035', u'外单 外贸 男短裤')

    print IllegalClassifier.classify('B', '50010850', u'减肥 显瘦 连衣裙')
