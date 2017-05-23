
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

from apilib.parser_models import ModelFactory
from apilib.utils import import_simplejson
from apilib.error import TopError

class Parser(object):
    def parse(self, method, payload):
        """
        Parse the response payload and return the result.
        Returns a tuple that contains the result data and the cursors
        (or None if not present).
        """
        raise NotImplementedError

    def parse_error(self, method, payload):
        """
        Parse the error message from payload.
        If unable to parse the message, throw an exception
        and default error message will be used.
        """
        raise NotImplementedError


class JSONParser(Parser):
    payload_format = 'json'

    def __init__(self):
        self.json_lib = import_simplejson()

    def parse(self, method, payload):
        try:
            json = self.json_lib.loads(payload, strict = False)
        except Exception, e:
            # print "Failed to parse JSON payload:" + str(payload)
            from apps.common.utils.utils_log import log
            log.error('Failed to parse JSON payload: e=%s' % e)
            raise TopError(payload)

        # if isinstance(json, dict) and 'previous_cursor' in json and 'next_cursor' in json:
        #    cursors = json['previous_cursor'], json['next_cursor']
        #    return json, cursors
        # else:
        return json

    def parse_error(self, method, payload):
        return self.json_lib.loads(payload)


class ModelParser(JSONParser):
    def __init__(self, model_factory = None):
        JSONParser.__init__(self)
        self.model_factory = model_factory or ModelFactory

    def parse(self, method, payload):
        try:
            if method.payload_type is None: return
            model = getattr(self.model_factory, method.payload_type)
        except AttributeError:
            raise TopError('No model for this payload type: %s' % method.payload_type)

        json = JSONParser.parse(self, method, payload)
        if isinstance(json, tuple):
            json, cursors = json
        else:
            cursors = None

        if method.payload_list:
            result = model.parse_list(method.api, json)
        else:
            result = model.parse(method.api, json)
        if cursors:
            return result, cursors
        else:
            return result


class TopObject(object):
    @staticmethod
    def clean(obj):
        vars_dict = vars(obj)
        if len(vars_dict) == 1:
            k, v = vars_dict.items()[0]
            if isinstance(v, TopObject):
                return TopObject.clean(v)
            elif isinstance(v, list):
                if v and  isinstance(v[0], TopObject):
                    return [ TopObject.clean(obj) for obj in v]
                else:
                    return obj
            else:
                return obj
        else:
            return obj

    def to_dict(self):
        """transfer to dict"""
        result_dict = {}
        for k, v in vars(self).items():
            if isinstance(v, TopObject):
                dict_value = v.to_dict()
            elif isinstance(v, list):
                if v and isinstance(v[0], TopObject):
                    dict_value = [item.to_dict() for item in v]
                else:
                    dict_value = v
            else:
                dict_value = v
            result_dict.update({k:dict_value})
        return result_dict

    def __len__(self):
        return len(vars(self))

    def __nozero__(self):
        return not vars(self) == False

    def __str__(self):
        return str(vars(self))

    def __repr__(self):
        return str(vars(self))

class TopObjectParser(JSONParser):
    def __init__(self):
        JSONParser.__init__(self)

    def parse(self, method, payload):
        json = JSONParser.parse(self, method, payload)
        if len(json) == 1 and json.has_key('error_response'):
            raise TopError(payload)

        title_key = method.method_name.replace('taobao.', '').replace('.', '_') + '_response'
        if not json.has_key(title_key):
            raise TopError('wrong response data')
        return TopObjectParser.json_to_object(json[title_key], method.field_mapping)

    @staticmethod
    def json_to_object(json, fm = None):
        if isinstance(json, dict):
            if json:
                obj = TopObject()
                for k, v in json.items():
                    if fm: # and fm.has_key(k.lower()):
                        k = fm.get(k.lower(), k)
                    setattr(obj, k, TopObjectParser.json_to_object(v, fm))
                return obj
            else:
                return TopObject()
        elif isinstance(json, (list, tuple)):
            return [TopObjectParser.json_to_object(item, fm) for item in json]
        else:
            return json
