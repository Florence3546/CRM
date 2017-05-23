# coding=UTF-8
"""根据淘宝新的关键词查排名结果刷新现有数据库的对应值"""
import init_environ
from apps.engine.models_kwlocker import kw_locker_coll
from apps.common.utils.utils_log import log


pc_left = 1                                                     # pc端首页左侧位置直通车位个数

# {platform: [[new_rank_range, old_rank_range], ...], ...}
KW_RT_RANK_MAP_RANGE = {
    'pc': [
        [(0, 0), (1 if pc_left else 0, pc_left)],              # 首页左侧位置
        [(1, 1), (1 + pc_left, 1 + pc_left)],                   # 首页右侧第1
        [(2, 2), (2 + pc_left, 2 + pc_left)],                   # 首页右侧第2
        [(3, 3), (3 + pc_left, 3 + pc_left)],                   # 首页右侧第3
        [(4, 4), (4 + pc_left, 17 + pc_left)],                  # 首页(非前三)
        [(5, 5), (18 + pc_left, 34 + pc_left)],                 # 第2页
        [(6, 6), (35 + pc_left, 51 + pc_left)],                 # 第3页
        [(7, 7), (52 + pc_left, 68 + pc_left)],                 # 第4页
        [(8, 8), (69 + pc_left, 85 + pc_left)],                 # 第5页
        [(9, 9), (86 + pc_left, None)],                         # 5页以后
    ],
    'yd': [
        [(0, 0), (1, 1)],                                       # 首页左侧位置
        [(1, 2), (2, 3)],                                       # 移动前三
        [(3, 5), (4, 6)],                                       # 移动4~6条
        [(6, 9), (7, 10)],                                      # 移动7~10条
        [(10, 10), (11, 15)],                                   # 移动11~15条
        [(11, 11), (16, 20)],                                   # 移动16~20条
        [(12, 12), (21, None)],                                 # 20条以后
    ]
}


def get_new_rank(old_rank, platform, value_index):
    new_rank = None
    for new_rank_range, old_rank_range in KW_RT_RANK_MAP_RANGE[platform]:
        if old_rank_range[0] and old_rank < old_rank_range[0]:
            continue
        if old_rank_range[1] and old_rank > old_rank_range[1]:
            continue
        new_rank = new_rank_range[value_index]
        break
    return new_rank


def refresh_kw_locker_coll():
    try:
        all_count = kw_locker_coll.find().count()
        i = 0
        for doc in kw_locker_coll.find().sort('_id', 1):
            old_rank_start, old_rank_end = doc['exp_rank_range']
            new_rank_start = get_new_rank(old_rank_start, doc['platform'], 0)
            new_rank_end = get_new_rank(old_rank_end, doc['platform'], -1)
            if new_rank_start is None:
                raise Exception('_id = %s, platform = %s, old_rank_start = %s' % (doc['_id'], doc['platform'], old_rank_start))
            if new_rank_end is None:
                raise Exception('_id = %s, platform = %s, old_rank_end = %s' % (doc['_id'], doc['platform'], old_rank_end))
            # kw_locker_coll.update({'_id': doc['_id']}, {'$set': {'exp_rank_range_new': [new_rank_start, new_rank_end]}})
            kw_locker_coll.update({'_id': doc['_id']}, {'$set': {'exp_rank_range': [new_rank_start, new_rank_end]}})
            i += 1
            print '%s / %s, _id: %s' % (i, all_count, doc['_id'])
    except Exception, e:
        log.error('error: %s' % e)

if __name__ == '__main__':
    refresh_kw_locker_coll()
