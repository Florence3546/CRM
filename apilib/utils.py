# coding=UTF-8
# Copyright 2010 Joshua Roesslein
# See LICENSE for details.

from datetime import datetime
import time
import htmlentitydefs
import re

def parse_datetime(str):
    '''We must parse datetime this way to work in python 2.4'''
    return datetime(*(time.strptime(str, '%a %b %d %H:%M:%S +0800 %Y')[0:6]))

def parse_html_value(html):
    return html[html.find('>') + 1:html.rfind('<')]

def parse_a_href(atag):
    start = atag.find('"') + 1
    end = atag.find('"', start)
    return atag[start:end]

def parse_search_datetime(str):
    '''We must parse datetime this way to work in python 2.4'''
    return datetime(*(time.strptime(str, '%a, %d %b %Y %H:%M:%S +0000')[0:6]))

def unescape_html(text):
    """Created by Fredrik Lundh (http://effbot.org/zone/re-sub.htm#unescape-html)"""
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

def convert_2utf8_str(arg):
    if isinstance(arg, unicode):
        arg = arg.encode('utf-8')
    elif not isinstance(arg, str):
        arg = str(arg)
    return arg

def convert_arg_2utf8_str(arg):
    if isinstance(arg, unicode):
        return True, arg.encode('utf-8')
    elif isinstance(arg, str):
        return True, arg
    else:
        return False, str(arg)

def import_simplejson():
    try:
        from apps.common.utils.utils_json import json
    except ImportError:
        try:
            import json
        except ImportError:
            raise ImportError, "Can't load a json library"
    return json

def humanize_exception(e):
    error_msg = e.message.encode('utf-8')
    if 'need to wait' in error_msg:
        error_msg = 'API接口超限'
    else:
        error_msg = '操作失败，请联系顾问'
    return error_msg
