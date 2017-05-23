from django.http import HttpResponse
from django.conf import settings

import json


# Dajax Request
class Dajax:
    """Dajax Core Class.

    Response methods to construct the ajax response."""

    def __init__(self):
        self.calls = []

    """
     Tested Methods
    """
    def render(self):
        if settings.DEBUG:
            return HttpResponse(json.dumps(self.calls), content_type = "text/plain")
        return HttpResponse(json.dumps(self.calls), content_type = "application/x-json")

    def alert(self, message):
        self.calls.append({'cmd':'alert', 'val':self._clean(message)})

    def assign(self, id, attribute, value):
        self.calls.append({'cmd':'as', 'id':id, 'prop':attribute, 'val':self._clean(value)})

    def addCSSClass(self, id, value):
        self.calls.append({'cmd':'addcc', 'id':id, 'val':self._clean(value)})

    def removeCSSClass(self, id, value):
        self.calls.append({'cmd':'remcc', 'id':id, 'val':self._clean(value)})

    def append(self, id, attribute, value):
        self.calls.append({'cmd':'ap', 'id':id, 'prop':attribute, 'val':self._clean(value)})

    def prepend(self, id, attribute, value):
        self.calls.append({'cmd':'pp', 'id':id, 'prop':attribute, 'val':self._clean(value)})

    def clear(self, id, attribute):
        self.calls.append({'cmd':'clr', 'id':id, 'prop':attribute})

    def redirect(self, url, delay = 0):
        self.calls.append({'cmd':'red', 'url':url, 'delay':delay})

    def script(self, code): # OK
        self.calls.append({'cmd':'js', 'val':code})

    def remove(self, id):
        self.calls.append({'cmd':'rm', 'id':id})

    def addData(self, data, function):
        self.calls.append({'cmd':'data', 'val':data, 'fun':function})

    def _clean(self, data):
        if hasattr(data, '__iter__'):
            return map(self._clean, data)
        else:
            return str(data).replace('\n', '').replace('\r', '')
            # return str(data.encode('utf-8')).replace('\n','').replace('\r','')#modify by hehao->needn't to modify here. add "import sys,os reload(sys) sys.setdefaultencoding('utf8')" in django.core.handlers.modpython

    """
     Untested Methods
    """

    def replace(self, id, attribute, search, replace):
        raise Exception("Not yet Implemented")
        self.calls.append({'cmd':'pp', 'id':id, 'prop':attribute, 'search':search, 'replace':replace})

    def debug(self, message):
        raise Exception("Not yet Implemented")
        self.calls.append({'cmd':'debug', 'val':message})

    def create(self, parent, tag, id, stype):
        raise Exception("Not yet Implemented")
        self.calls.append({'cmd':'ce', 'parent':parent, 'tag':tag, 'id':id, 'type':stype})

    def insert(self, id, before, tag):
        raise Exception("Not yet Implemented")
        self.calls.append({'cmd':'ie', 'id':id, 'before':before, 'tag':tag})

    def insertAfter(self, id, after, tag):
        raise Exception("Not yet Implemented")
        pass

    def setEvent(self, target, event, script):
        raise Exception("Not yet Implemented")
        pass

    def addEvent(self, target, event, script):
        raise Exception("Not yet Implemented")
        pass
