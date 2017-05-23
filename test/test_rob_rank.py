# coding=UTF-8

import init_environ

'''
生成抢排名任务
'''

def test_create_kwlockers():
    from apps.subway.models_keyword import Keyword
    from apps.engine.models_kwlocker import KeywordLocker
    import random
    shop_id = 63518068

    kws = Keyword.objects.filter(shop_id = shop_id).limit(50)
    for kw in kws:
        i = random.randint(1, 20)
        j = random.randint(1, 10)
        limit_price = random.randint(50, 500)
        platform = KeywordLocker.PLATFORM_CHOICES[j % 2][0]
        KeywordLocker.objects.create(shop_id = kw.shop_id, campaign_id = kw.campaign_id, adgroup_id = kw.adgroup_id, keyword_id = kw.keyword_id,
                                     word = kw.word, exp_rank_range = [i, i + j], limit_price = limit_price, platform = platform)

def test_customer_rob():
    from apps.subway.models_keyword import Keyword
    import random
    from apps.engine.rob_rank import CustomRobRank
    from apps.subway.upload import update_keywords
    from apps.router.models import User
    shop_id = 63518068
    adgroup_id = 665427501
    keyword_id = 263613645346
    user = User.objects.get(shop_id = shop_id)
    kws = Keyword.objects.filter(shop_id = shop_id, adgroup_id = adgroup_id).limit(100)
    kws = Keyword.objects.filter(keyword_id = keyword_id)
    # shop_id = 71146177
    # kws = Keyword.objects.filter(shop_id = shop_id, keyword_id = 262853781642)
    platform_dict = {0: 'yd', 1: 'pc'}
    kw_cfg_list = []
    upd_kw_list = []
    for kw in kws:
        # platform = platform_dict[random.randint(0, 1)]
        platform = platform_dict[1]
        kw_cfg_list.append({'word': kw.word, 'keyword_id': kw.keyword_id, 'exp_rank_range': [40, 50], 'limit_price': 300, 'platform': platform, 'nearly_success': 0})
        upd_kw_list.append([kw.campaign_id, kw.adgroup_id, kw.keyword_id, kw.word, {'max_price': kw.max_price, 'old_price': kw.max_price}])
    CustomRobRank.test_execute(user = user, adgroup_id = adgroup_id, kw_cfg_list = kw_cfg_list)
    # update_keywords(shop_id = shop_id, kw_arg_list = upd_kw_list, opter = 2, opter_name = 'whq')


def main():
    # test_create_kwlockers()
    test_customer_rob()

if __name__ == '__main__':
    main()
