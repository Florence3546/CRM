# coding=UTF-8

'''
Created on 2015-12-16

@author: YRK
'''
import json

class TreePasser(object):

    def __init__(self, tree_template, node_container, fields_mapping):
        self.node_container = node_container
        self.fields_mapping = fields_mapping
        self.tree_template = tree_template
        self.root_node = self._parser_to_objtree(self.tree_template.tree_json)

    @property
    def related_fields(self):
        if not hasattr(self, '_related_field'):
            field_set = set()
            self.node_container.loading_condition_fields(self.root_node, field_set)
            self._related_field = list(self.fields_mapping[field_name] for field_name in field_set if field_name in self.fields_mapping)
        return self._related_field

    def parser_to_json(self):
        return self.root_node.to_dict()

    def hungon_people_counter(self, cust_mapping):
        cache_result = {}
        self.root_node.init_root_data(self.tree_template.id, cust_mapping.keys())
        related_fields_mapping = {field.name : field  for field in self.related_fields}
        self.root_node.hungon_people_counter(cust_mapping, related_fields_mapping, cache_result)
        return cache_result

    def _parser_to_objtree(self, tree_json_str):
        tree_info = json.loads(tree_json_str)
        if isinstance(tree_info, list):
            self.root_node = self.node_container(name = "我的客户", cond_list = [], child_list = tree_info)
        else:
            self.root_node = self.node_container(**tree_info)
        return self.root_node