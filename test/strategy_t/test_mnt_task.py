# coding=UTF-8

import init_environ

from django.test import TestCase
from apps.mnt.models_task import MntTaskMng, MntTask, mnt_task_coll
from apps.common.utils.utils_misc import trans_dict_2document # (src_dict, dest_obj, exclude = []):



class test_mnt_task(TestCase):
    def setUp(self):
        pass


    def test_task_workflow1(self):
        shop_id = 63518068
        # create routine task
        MntTaskMng.check_routine_task(shop_id = shop_id)
        # query task
        task_cur = mnt_task_coll.find({'shop_id':shop_id})
        # self.assertEqual(task_cur.count(), 2, 'error task count, create routine task failed.')
        print task_cur.count()
        # run task
        for task in task_cur:
            task_obj = MntTask()
            trans_dict_2document(src_dict = task, dest_obj = task_obj)
            print task_obj.is_runnable()
            task_obj.run()

#     def test_task_workflow2(self):
#         shop_id = 0
#         campaign_id = 0
#         pass


    # def upsert_task(cls, shop_id, campaign_id, mnt_type, task_type = 1, **kwargs):







