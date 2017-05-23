# coding=UTF-8
import sys
import os, json, csv
import init_environ

from apps.common.utils.utils_datetime import date_2datetime, datetime
from apps.ncrm.models import PrivateMessage

def main():
    test_single()

def test_single():
    shop_id = 110
    title = '测试标题111'
    content = '测试内容1111'
    app_id = 12612063
    level = 'info'
    start_time = datetime.datetime.now()
    end_time = datetime.datetime.now()
    result = PrivateMessage.send_message(shop_id = shop_id,
             title = title,
             content = content,
             app_id = app_id,
             level = level,
             start_time = start_time,
             end_time = end_time)
    print result

def test_batch():
    shop_id_list = [111, 112, 113, 114, 115]
    title = '测试标题2'
    content = '测试内容2'
    app_id = 111111111
    level = 'info'
    start_time = datetime.datetime.now()
    end_time = datetime.datetime.now()
    result = PrivateMessage.batch_send_message(shop_id_list = shop_id_list,
             title = title,
             content = content,
             app_id = app_id,
             level = level,
             start_time = start_time,
             end_time = end_time)
    print result

def test_read():
    msg_id = "566a3035b94dd11c38e68ad2"
    message = PrivateMessage.read_message(115, msg_id)
    print message

def test_unread_count():
    shop_id = 63518068
    count = PrivateMessage.get_unread_count(shop_id)
    print count

def test_msg_list():
    shop_id = 63518068
    list = PrivateMessage.get_message_list(shop_id)
    print list

if __name__ == '__main__':
    main()
