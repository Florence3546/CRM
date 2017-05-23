# coding=UTF-8

'''
Created on 2015-12-16

@author: YRK
'''
import itertools

class TreeNode(object):
    _valid_fields = ('name', 'goal', 'child_list', 'cond_list', 'shop_count', 'path', 'mark', 'shop_id_list')

    def __init__(self, name, cond_list, child_list, **kwargs):
        self.name = name
        self.cond_list = cond_list
        self.child_list = []
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.shop_count = 0
        self.path = ""
        self._shop_id_list = []
        self.shop_id_list = []

        self._generate_child_node(child_list)

    def _generate_child_node(self, child_list):
        if child_list and all(isinstance(child, dict) for child in child_list):
            for child in child_list:
                child_instance = self.__class__(**child)
                self.child_list.append(child_instance)

    def set_shop_list(self, shop_id_list):
        self._shop_id_list = shop_id_list
        if not self.child_list:
            self.shop_id_list = shop_id_list
        self.shop_count = len(shop_id_list)

    def get_shop_list(self):
        return self._shop_id_list

    def init_root_data(self, tree_id, shop_id_list):
        self.path = str(tree_id)
        self.set_shop_list(shop_id_list)
        return True

    def condition_valid(self, customer, related_field_mapping):
        or_list = []
        for cond_dict in self.cond_list:
            and_list = []
            for attr_name, args_list in cond_dict.items():
                field = related_field_mapping.get(attr_name, None)
                attr_val = getattr(customer, attr_name)
                result = field.verify_condition(attr_val, *args_list)
                and_list.append(result)
            or_list.append(all(and_list))
        return any(or_list)

    def hungon_people_counter(self, cust_mapping, related_field_mapping, cache_result):
        if self.child_list :
            temp_mapping = {shop_id :cust_mapping.get(shop_id) for shop_id in self._shop_id_list \
                           if cust_mapping.get(shop_id)}
            for child_index, child in enumerate(self.child_list):
                shop_id_list = []
                if temp_mapping:
                    for shop_id, customer in temp_mapping.items():
                        if not child.cond_list or child.condition_valid(customer, related_field_mapping):
                            temp_mapping.pop(shop_id)
                            shop_id_list.append(shop_id)

                child.set_shop_list(shop_id_list)
                child.path = "{}_{}".format(self.path, child_index) if self.path else  "{}".format(child_index)
                child.hungon_people_counter(cust_mapping, related_field_mapping, cache_result)
                cache_result.update({child.path:child.get_shop_list()})

            if temp_mapping:
                rest_node = TreeNode(name = '其他', cond_list = [], child_list = [], goal={})
                rest_node.set_shop_list(temp_mapping.keys())
                rest_node.path = "{}_{}".format(self.path, len(self.child_list)) if self.path else  "{}".format(len(self.child_list))
                self.child_list.append(rest_node)
                cache_result.update({rest_node.path:rest_node.get_shop_list()})

        return None

    def to_dict(self):
        result = {key:self.__dict__[key] for key in self._valid_fields if key in self.__dict__}
        new_chlid_list = []
        for child in self.child_list:
            new_child = child.to_dict()
            new_chlid_list.append(new_child)
        result['child_list'] = new_chlid_list
        return result

    @classmethod
    def loading_condition_fields(cls, node, field_set):
        for cond_dict in node.cond_list:
            for field_name in cond_dict:
                field_set.add(field_name)

        for child in node.child_list:
            cls.loading_condition_fields(child, field_set)