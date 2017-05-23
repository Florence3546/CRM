# coding=utf-8

import csv
import MySQLdb
import init_environ

"""
从s3上将日志导入到crm中。

s3中的diary数据，主要有两个关联：author、commenter
从auth_user中取出id与name的映射，然后
再根据crm_psuser中取出name与id映射。
最后一把迁移过来。

需要解决的问题是：
1，先导出tp_diary，auth_user
2，根据auth_user旧表中的id换成nick
3，根据psuser表生成nick_to_id的字典
4，将旧表中的id绑定成新的id
5，将tp_diary的数据格式转成ncrm_diary并导入
"""

# s3conn = MySQLdb.Connect(host = '10.200.175.246', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl3_tp')
# w3conn = MySQLdb.Connect(host = '10.200.175.246', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl4')

s3conn = MySQLdb.Connect(host = '127.0.0.1', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl3_tp')
w3conn = MySQLdb.Connect(host = '127.0.0.1', user = 'root', passwd = 'zxcvbnhy6', charset = 'utf8', db = 'ztcjl4')

writer_dict = {}

def get_writer(failed_type):
    global writer_dict
    writer = writer_dict.get(failed_type , None)
    if not writer:
        FILE_PATH = 'd:/ztcdata/failed_%s.csv' % failed_type
        try:
            writer = csv.writer(open(FILE_PATH, 'w'), lineterminator = '\n')
        except Exception, e:
            print e
            return None
        writer_dict.update({failed_type:writer})
    return writer

def get_data(cursor, sql):
    cursor.execute(sql)
    result_list = []
    for i in cursor.fetchall():
        result_list.append(i)
    return result_list


def get_tpdiary():
    cursor = s3conn.cursor()
    sql = """select author_id,content,create_time,todolist,comment,commenter_id,comment_time from tp_diary"""
    return get_data(cursor, sql)


def get_newid_byoldid():
    cursor = s3conn.cursor()
    sql = "select id, username from auth_user" # TODO: wangqi 20141208 修改表名
    id_2nick_dict = dict(get_data(cursor, sql))

    w3cursor = w3conn.cursor()
    sql = "select name, id from ncrm_psuser"
    nick_2id_dict = dict(get_data(w3cursor, sql))

    oldid_2newid_dict = {}
    for old_id, nick in id_2nick_dict.items():
        new_id = int(nick_2id_dict.get(nick, 0))
        oldid_2newid_dict.update({int(old_id): new_id})
        if new_id == 0:
            writer = get_writer('user')
            if writer:
                writer.writerow([nick])
    # TODO: wangqi 20141208 这里可以选择一个公共账户，将找不到客户的数据处理掉
    return oldid_2newid_dict

def insert_diary(diary_list):
    insert_count, failed_list = 0, []
    insert_field_list = ['author_id', 'content', 'create_time', 'todolist', 'comment', 'commenter_id', 'comment_time']
    if diary_list:
        insert_sql = """insert into ncrm_diary(author_id, content, create_time, todolist, comment, commenter_id, comment_time)
                        values(%s,%s,%s,%s,%s,%s,%s)"""
        cursor = w3conn.cursor()
        for insert_obj in diary_list:
            try:
                insert_tuple = [insert_obj[field] for field in insert_field_list]
                cursor.execute(insert_sql, insert_tuple)
                insert_count += 1
            except Exception, e:
                writer = get_writer('diary')
                if writer:
                    writer.writerow(insert_tuple)

        w3conn.commit()
    return insert_count, failed_list

def export_diary():
    print u'1st, 获取新旧ID映射列表'
    id_dict = get_newid_byoldid()

    print u'2nd, 获取日志'
    tpdiary_list = get_tpdiary()

    invalid_diary_list = []
    diary_list = []

    for td in tpdiary_list:
        try:
            diary_list.append({'author_id': id_dict[int(td[0])], 'content':td[1], 'create_time':td[2], 'todolist':td[3], 'comment':td[4], 'commenter_id':id_dict.get(td[5], None), 'comment_time':td[6]})
        except Exception, e:
            print e
            invalid_diary_list.append(td)

    print u'3rd, 总日志数：%s, 需导入数：%s, 失败数：%s' % (len(tpdiary_list), len(diary_list), len(invalid_diary_list))

    insert_count, diary_failed_list = insert_diary(diary_list)
    print u'4th, 导入完成，总条数：%s, 日志导入%s个，失败%s个' % (len(tpdiary_list), insert_count, len(diary_failed_list))


if __name__ == '__main__':
    export_diary()
