# coding=UTF-8

from django.template import RequestContext
from django.shortcuts import render_to_response

def select_keyword_new(request, template = 'select_keyword_order.html'):
    return render_to_response(template, {}, context_instance = RequestContext(request))
