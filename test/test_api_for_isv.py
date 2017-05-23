# coding=UTF-8

import init_environ

from apilib.japi import web_api

host = 'localhost:8000'

def test_account_rpt():
    shop_id = '63518068'
    shop_id = '71193535'
    # shop_id = 12334
    result = web_api(inner = False, host = host).isv_get_account_rpt(shop_id = shop_id, rpt_days = '5')
    print result

def test_select_word():
    item_id = '35242607147'
    result = web_api(inner = False, host = host).isv_get_select_word(item_id = item_id)
    print result

def main():
    test_account_rpt()
    test_select_word()

if __name__ == '__main__':
    main()
