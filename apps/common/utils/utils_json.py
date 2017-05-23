# coding=UTF-8

import thirdapps.simplejson as json

# TODO wangqi 20150627 虽然json.dumps比simlejson.dumps速度快，但以下封装存在问题，
# 如 json.dumps([{'a': 1, 'b': [1, 2, 3]}, ]) 出错

# import datetime
# from bson import ObjectId
# from django.db.models import Model
# import json

# ===============================================================================
# action  json    simplejson
# dumps   fastter slower
# loads   slower  fastter
# ===============================================================================

# class MyEncoder(json.JSONEncoder):

#     def default(self, obj):
#         if isinstance(obj, datetime.time):
#             return obj.__str__()
#         elif isinstance(obj, datetime.datetime):
#             return obj.__str__()
#         elif isinstance(obj, datetime.date):
#             return obj.__str__()
#         elif isinstance(obj, ObjectId):
#             return obj.__str__()
#         elif isinstance(obj, Model):
#             value_dict = vars(obj)
#             value_dict.pop('_state', None)
#             return value_dict
#         else:
#             return json.JSONEncoder.default(self, obj)

# def json_wrapper(fn):

#     def _inner(obj, cls = None, *args, **kwargs):
#         return fn(obj, cls = MyEncoder, *args, **kwargs)

#     return _inner

# json.dumps = json_wrapper(json.dumps)
# json.dump = json_wrapper(json.dump)
