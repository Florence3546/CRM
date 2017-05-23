
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

import time

from apps.common.biz_utils.utils_misc import jl_sign_with_secret


class AuthHandler(object):
    def apply_auth(self, url, method, headers, parameters):
        """Apply authentication headers to request"""
        raise NotImplementedError
    def get_username(self):
        """Return the username of the authenticated user"""
        raise NotImplementedError


class TopAuthHandler(AuthHandler):
    def __init__(self, app_key, app_secret, session_key = None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.session_key = session_key

    def apply_auth(self, parameters):
        param_dict = {
            'timestamp':time.strftime('%Y-%m-%d %X', time.localtime()),
            'format':'json',
            'app_key':self.app_key,
            'v':'2.0',
            'sign_method':'md5',
        }
        if self.session_key:
            param_dict['session'] = self.session_key
        parameters.update(param_dict)
        jl_sign_with_secret(parameters, self.app_secret)

class JAuthHandler(AuthHandler):
    def __init__(self, app_secret):
        self.app_secret = app_secret

    def apply_auth(self, parameters):
        jl_sign_with_secret(parameters, self.app_secret)
