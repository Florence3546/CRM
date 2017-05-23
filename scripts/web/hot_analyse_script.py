# coding=UTF-8

import pymongo
import os
import math

#=================================================================================
# 用户行为分析采集脚本，并保存文件：hot_analyse_result.csv
#=================================================================================
web_online_conn = pymongo.Connection(host = 'mongodb://PS_superAdmin:PS_managerAdmin@223.4.49.56:30001/')
# web_online_conn = pymongo.Connection(host = '192.168.1.210', port = 12345)
online_db = web_online_conn.ztcjl4
hot_coll = online_db.web_hotzone

def exist_number(content):
    for x in content:
        if 47 < ord(x) < 58:
            return True
    return False

def all_number(content):
    for x in content:
        if ord(x) > 47 or ord(x) > 58:
            return False
    return True

def statictics_behavior(size = 200000):
    result_dict = {}
    total = hot_coll.find().count()
    times = int(math.ceil(total * 1.0 / size))
    print u"统计数据开始 "
    for index in xrange(times) :
        try:
            aggregate_pipeline = [
                                                    {
                                                        '$match':{
                                                                's1':{'$regex':"^[a-zA-Z]"}
                                                        }
                                                     },
                                                      {
                                                        '$group':{
                                                                    '_id':{
                                                                                "s1":"$s1",
                                                                                "page":"$page"
                                                                           },
                                                                    'total_count':{"$sum":1}
                                                                  }
                                                       },
                                                    {
                                                        "$project":{
                                                                        "_id":0,
                                                                        "s1":"$_id.s1",
                                                                        "page":"$_id.page",
                                                                        "count":"$total_count",
                                                                    }
                                                     },
                                                    {
                                                        "$sort":{"page":-1}
                                                    },
                                                    {
                                                        "$skip":index * size
                                                   },
                                                   {
                                                        "$limit":size
                                                    }
                                                ]

            result_list = hot_coll.aggregate(aggregate_pipeline)['result']
            for result in result_list:
                if result.has_key('s1'):
                    field_list = str(result['s1']).split('_')
                    try:
                        if len(field_list) > 1 and  exist_number(field_list[-1]):
                            key = "%s+%s" % (result['page'], '_'.join(field_list[:-1]) + '_')
                        else:
                            key = "%s+%s" % (result['page'], result['s1'])
                        if not result_dict.has_key(key):
                            result_dict[key] = 0
                        result_dict[key] = result_dict[key] + result['count']
                    except Exception, e:
                        print "出现异常，e=%s" % (e)
            print u"已统计完成 %s%%" % ((index + 1) * 100 / times)
        except Exception, e:
            print "aggregate consulter behavior error! e=%s" % (e)
    print u"统计数据完成 "
    return result_dict

def create_file(file_name , field_name_list, charset = 'GBK'):
    is_exist = os.path.exists(file_name)
    if is_exist:
        os.remove(file_name)

    f = open(file_name , 'w')
    try:
        content = "%s\n" % (','.join(field_name_list))
        f.write(content.encode(charset))
    except Exception, e:
        print "create file error,e=%s" % (e)
        return False
    else:
        print "已生成 %s 文件" % (file_name)
    finally:
        f.close()
    return  True

def append_content(file_name, content_list, charset = 'GBK'):
    with open(file_name , 'a') as f:
        content = ''
        for temp in content_list:
            content += "%s\n" % (temp)
        f.write(content.encode(charset))

file_name = "hot_analyse_special_result_2.csv"
try:
    result_dict = statictics_behavior()
except Exception, e:
    print 'aggragete error, e=%s' % (e)
else:
    field_name_list = ['操作页面', '执行ID', '操作次数']
    if create_file(file_name, field_name_list):
        store_data = sorted(result_dict.items(), key = lambda x:x[0])
        content_list = []
        for data in store_data:
            page, s1 = data[0].split('+')
            count = data[1]
            content_list.append('%s,%s,%s' % (page, s1, count))
        append_content(file_name, content_list)
        print u"生成行为分析详细文档完成 "
