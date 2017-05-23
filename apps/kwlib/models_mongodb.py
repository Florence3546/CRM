# coding=UTF-8
import socket
import datetime
from mongoengine.document import Document
from mongoengine.fields import StringField, IntField

HOST_IP = socket.gethostbyname(socket.gethostname())

class RequestAPIMonitor(Document):
    host_ip = StringField(verbose_name = "服务器IP地址")
    words_count = IntField(verbose_name = "调用api关键词的个数")
    return_count = IntField(verbose_name = "api返回有流量关键词的个数")
    request_type = IntField(verbose_name = "请求类型，1为全网数据，2为细分数据")
    function_type = StringField(verbose_name = "方法调用类型")

    meta = {'collection':'kwlib_api_monitor', 'indexes':['host_ip', 'request_type'], "db_alias": "kwlib-db"}

    @classmethod
    def insertDocument(cls, words_count, return_count, request_type, function_type):

        cls._get_collection().insert({
                         'host_ip':HOST_IP,
                         'words_count':words_count,
                         'return_count':return_count,
                         'request_type':request_type,
                         'datetime':datetime.datetime.now(),
                         'function_type':function_type
                         })



rqm_coll = RequestAPIMonitor._get_collection()