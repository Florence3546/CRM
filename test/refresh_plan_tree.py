# coding=UTF-8
'''刷新客户的服务人员分配'''
import init_environ
from bson.objectid import ObjectId
from apps.ncrm.models import PSUser, pt_coll
from apps.ncrm.classify_tree import build_tree

if __name__ == "__main__":
    tree_id = '5774f00e2d16893d7c54e0b0'
    psuser_id = 688
    psuser = PSUser.objects.get(id=psuser_id)
    tree_data = list(pt_coll.find({'_id': ObjectId(tree_id)}))[0]
    build_tree.refresh_plan_tree(tree_id, tree_data, psuser)
