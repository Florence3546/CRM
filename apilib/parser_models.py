
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

from apilib.utils import parse_datetime, parse_html_value, parse_search_datetime, unescape_html

class ResultSet(list):
    """A list like object that holds results from a Twitter API query."""


class Model(object):

    def __init__(self, api = None):
        self._api = api

    def __getstate__(self):
        pickle = dict(self.__dict__)
        del pickle['_api'] # do not pickle the API reference
        return pickle

    @classmethod
    def parse(cls, api, json):
        """Parse a JSON object into a model instance."""
        raise NotImplementedError

    @classmethod
    def parse_list(cls, api, json_list):
        """Parse a list of JSON objects into a result set of model instances."""
        results = ResultSet()
        for obj in json_list:
            results.append(cls.parse(api, obj))
        return results


class User(Model):

    @classmethod
    def parse(cls, api, json):
        user = cls(api)
        for k, v in json.items():
            print k, v
            if k in ['last_visit', 'created']:
                setattr(user, k, parse_datetime(v))
            elif k == 'location':
                setattr(user, k, Location.parse(api, v))
            elif k in ['buyer_credit', 'seller_credit']:
                setattr(user, k, Credit.parse(api, v))
            elif k == 'boolfield':
                # sets this to null if it is false
                if v is True:
                    setattr(user, k, True)
                else:
                    setattr(user, k, False)
            else:
                setattr(user, k, v)
        return user

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['users']

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

    def timeline(self, **kargs):
        return self._api.user_timeline(user_id = self.id, **kargs)

    def friends(self, **kargs):
        return self._api.friends(user_id = self.id, **kargs)

    def followers(self, **kargs):
        return self._api.followers(user_id = self.id, **kargs)

    def follow(self):
        self._api.create_friendship(user_id = self.id)
        self.following = True

    def unfollow(self):
        self._api.destroy_friendship(user_id = self.id)
        self.following = False

    def lists_memberships(self, *args, **kargs):
        return self._api.lists_memberships(user = self.screen_name, *args, **kargs)

    def lists_subscriptions(self, *args, **kargs):
        return self._api.lists_subscriptions(user = self.screen_name, *args, **kargs)

    def lists(self, *args, **kargs):
        return self._api.lists(user = self.screen_name, *args, **kargs)

    def followers_ids(self, *args, **kargs):
        return self._api.followers_ids(user_id = self.id, *args, **kargs)



class SearchResult(Model):

    @classmethod
    def parse(cls, api, json):
        result = cls()
        for k, v in json.items():
            if k == 'created_at':
                setattr(result, k, parse_search_datetime(v))
            elif k == 'source':
                setattr(result, k, parse_html_value(unescape_html(v)))
            else:
                setattr(result, k, v)
        return result

    @classmethod
    def parse_list(cls, api, json_list, result_set = None):
        results = ResultSet()
        results.max_id = json_list.get('max_id')
        results.since_id = json_list.get('since_id')
        results.refresh_url = json_list.get('refresh_url')
        results.next_page = json_list.get('next_page')
        results.results_per_page = json_list.get('results_per_page')
        results.page = json_list.get('page')
        results.completed_in = json_list.get('completed_in')
        results.query = json_list.get('query')

        for obj in json_list['results']:
            results.append(cls.parse(api, obj))
        return results


class JSONModel(Model):

    @classmethod
    def parse(cls, api, json):
        lst = JSONModel(api)
        for k, v in json.items():
            setattr(lst, k, v)
        return lst


class ModelFactory(object):
    """
    Used by parsers for creating instances
    of models. You may subclass this factory
    to add your own extended models.
    """
    user = User
    search_result = SearchResult
    json = JSONModel
