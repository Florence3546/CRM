# coding=UTF-8
import itertools, datetime
from bson.objectid import ObjectId

from apps.ncrm.models import TreeTemplate, PlanTree, pt_coll, ptr_coll, Customer
from apps.common.biz_utils.utils_cacheadapter import CrmCacheAdapter
from apps.common.utils.utils_log import log

from .field import FieldManager
from .node import TreeNode
from .parser import TreePasser

__all__ = ["build_tree", "read_tree_branch"]

class CustomerLoader(object):

    def __init__(self):
        pass

    def loading(self, load_fields, customer_mapping):
        load_funcs = set(itertools.chain(*[ field.load_func for field in load_fields ]))

        for load_func in load_funcs:
            if callable(load_func):
                load_func(customer_mapping)

        for customer in customer_mapping.values():
            for field in load_fields:
                if callable(field.custom_func):
                    field_result = field.custom_func(customer)
                    setattr(customer, field.name, field_result)

#                 if getattr(customer, field.name) :
#                     print "{} : {} - {}".format(customer.shop_id, field.name, getattr(customer, field.name))

        return customer_mapping

class Classifier(object):

    def __init__(self, parser_cls, loader_cls, node_container):
        self.parser = parser_cls
        self.node_container = node_container
        self.loader = loader_cls
        self.cache_backend = CrmCacheAdapter()
        self.timeout = 60 * 60 * 30

    def load_customers_bypath(self, path, psuser):
        tree_id = path.split("_", 1)[0]
        if tree_id.isdigit():
            cache_key = "{}_{}".format(psuser.id, path)
            shop_id_list = self.cache_backend.get(cache_key)
            if shop_id_list is None:
                tree_template = TreeTemplate.get_tree_byid(int(tree_id))
                self(tree_template, psuser)
                shop_id_list = self.cache_backend.get(path) or []
        else:
            shop_id_list = self.get_plan_tree_shops(path)
        return shop_id_list

    def get_plan_tree_shops(self, path):
        def get_child_data_list(node_data, key, result_list):
            if node_data['child_list']:
                for child in node_data['child_list']:
                    get_child_data_list(child, key, result_list)
            else:
                value = node_data[key]
                if type(value) is list:
                    result_list.extend(node_data[key])
                else:
                    result_list.append(value)
            return result_list

        node_path_list = path.split("_")
        node_data = PlanTree.get_tree_byid(node_path_list[0])
        for i in node_path_list[1:]:
            node_data = node_data['child_list'][int(i)]
        shop_id_list = list(set(get_child_data_list(node_data, 'shop_id_list', [])))
        return shop_id_list

    # def get_path_by_shop_id(self, shop_id, tree_template):
    #     path = None
    #     customer_mapping = {customer.shop_id:customer for customer in Customer.objects.filter(shop_id=shop_id)}
    #     if customer_mapping:
    #         # 加载及解析树
    #         fields_mapping = FieldManager.read_allfields_mapping()
    #         parser = self.parser(tree_template, self.node_container, fields_mapping)
    #
    #         # 挂载用于计算的数据
    #         self.loader().loading(parser.related_fields, customer_mapping)
    #
    #         tree_data = parser.hungon_people_counter(customer_mapping)
    #         path_list = [_path for _path, shop_id_list in tree_data.items() if shop_id in shop_id_list]
    #         path_list.append(str(tree_template.id))
    #         path_list.sort()
    #         path = path_list[-1]
    #
    #     return path

    def get_path_by_shop_id(self, shop_id, tree_data):
        path = None
        if shop_id in tree_data.get('shop_id_list', []):
            path = tree_data.get('path')
        else:
            for child_data in tree_data.get('child_list', []):
                path = self.get_path_by_shop_id(shop_id, child_data)
                if path:
                    break
        return path

    def get_or_create_path_by_shop_id(self, shop_id, tree_id, tree_data):
        path = self.get_path_by_shop_id(shop_id, tree_data)
        if not path:
            if tree_data['child_list']:
                rest_node_list = filter(lambda x: not x['cond_list'], tree_data['child_list'])
                if rest_node_list:
                    path = rest_node_list[0]['path']
                    rest_node_list[0]['shop_id_list'].append(shop_id)
                    rest_node_list[0]['shop_count'] = len(rest_node_list[0]['shop_id_list'])
                else:
                    path = '%s_%s'% (tree_data['path'], len(tree_data['child_list']))
                    tree_data['child_list'].append({
                        'name': '其他',
                        'desc': '',
                        'goal': {},
                        'child_list': [],
                        'cond_list': [],
                        'path': path,
                        'shop_count': 1,
                        'shop_id_list': [shop_id]
                    })
            else:
                path = tree_data['path']
                tree_data['shop_id_list'].append(shop_id)
            tree_data['shop_count'] += 1
            PlanTree.update_tree(tree_id, tree_data)
        return path

    def load_plan_tree_record(self, tree_id, start_time, tree_data):
        rec_dict = {}
        def load_data(tree_data):
            tree_data.update({'record':{k: 0 for k, _ in PlanTree.GOAL_KEY_CHOICES}})
            if tree_data['child_list']:
                for child_data in tree_data['child_list']:
                    load_data(child_data)
                    for k in tree_data['record']:
                        tree_data['record'][k] += child_data['record'][k]
            else:
                for k in tree_data['record']:
                    if tree_data['path'] in rec_dict:
                        tree_data['record'][k] = rec_dict[tree_data['path']].get(k, 0)

        pipeline = [
            {
                '$match':{
                    'tree_id': ObjectId(tree_id),
                    'create_time': {
                        '$gte': start_time,
                    }
                }
            },
            {
                '$group':{
                    '_id': {
                        'path': '$path',
                        'rec_type': '$rec_type'
                    },
                    'rec_value': {'$sum': '$rec_value'}
                }
            },
            {
                '$project':{
                    '_id': 0,
                    'path': '$_id.path',
                    'rec_type': '$_id.rec_type',
                    'rec_value': 1
                }
            }
        ]
        rec_list = ptr_coll.aggregate(pipeline)['result']
        for rec in rec_list:
            rec_dict.setdefault(rec['path'], {})[rec['rec_type']] = rec['rec_value']

        load_data(tree_data)

    def auto_insert_record(self, psuser, shop_id, nick, rec_type, rec_value, create_time):
        try:
            plan_tree = list(pt_coll.find({
                'psuser_id': psuser.id,
                'status': 1,
                'start_time':{'$lte':create_time},
                'end_time':{'$gt':create_time - datetime.timedelta(days=1)}
            }))
            if plan_tree:
                plan_tree = plan_tree[0]
                # tree_obj = PlanTree.get_tree_template(plan_tree)
                # path = self.get_path_by_shop_id(shop_id, tree_obj)
                path = self.get_or_create_path_by_shop_id(shop_id, plan_tree['_id'], plan_tree)
                if path:
                    ptr_coll.insert({
                        'tree_id': plan_tree['_id'],
                        'path': path,
                        'shop_id': shop_id,
                        'nick': nick,
                        'rec_type': rec_type,
                        'rec_value': rec_value,
                        'psuser_id': 0,
                        'psuser_cn': '系统',
                        'create_time': create_time
                    })
        except Exception, e:
            log.error('build_tree.auto_insert_record error, e=%s' % e)


    def __call__(self, tree_template, psuser, is_stat = True, cat_id_list = None, plan_stat = False):

        # 初始化用户客户数据
        if cat_id_list:
            customer_mapping = {customer.shop_id:customer for customer in psuser.mycustomers_withcat if customer.cat_id in cat_id_list}
        else:
            customer_mapping = {customer.shop_id:customer for customer in psuser.mycustomers}

        # 加载及解析树
        fields_mapping = FieldManager.read_allfields_mapping()
        parser = self.parser(tree_template, self.node_container, fields_mapping)

        if is_stat:
            # 挂在用于计算的数据
            self.loader().loading(parser.related_fields, customer_mapping)

            # 计算机缓存数据
            cache_result = parser.hungon_people_counter(customer_mapping)
            cache_result = {'{}_{}'.format(psuser.id, key):val for key, val in cache_result.items()}
            self.cache_backend.set_many(cache_result, self.timeout) # 记录缓存

        # 逆向解析数据
        tree_data = parser.parser_to_json()

        if plan_stat:
            # 统计计划树目标跟踪数据
            self.load_plan_tree_record(tree_template.id, tree_template.start_time, tree_data)

        return tree_data

    def refresh_plan_tree(self, tree_id, tree_data, psuser):
        try:
            tree_doc = PlanTree.get_tree_byid(tree_id)
            tree_doc.update(tree_data)
            tree_obj = PlanTree.get_tree_template(tree_doc)
            tree_doc = self(tree_obj, psuser)
            tree_doc.update(tree_data)
            PlanTree.update_tree(tree_id, tree_doc)
        except Exception, e:
            print 'build_tree.refresh_plan_tree error, tree_id=%s, e=%s' % (tree_id, e)


build_tree = Classifier(TreePasser, CustomerLoader, TreeNode)
read_tree_branch = build_tree.load_customers_bypath
load_all_fields = FieldManager.read_all_fields