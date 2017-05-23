# coding=UTF-8
import django, sys, re, os, multiprocessing, glob, datetime, csv, time, traceback
from selenium import webdriver
from mongoengine import Document, StringField, IntField, DictField, DateTimeField, ObjectIdField, ListField

PROJECT_ROOT = "D:\\ztcjingling\\ztcjl"
def init_environ():
    reload(sys)
    sys.setdefaultencoding('utf8')
    sys.path.insert(0, PROJECT_ROOT)
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "thirdapps"))
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))

    try:
        import settings # Assumed to be in the same directory.
    except ImportError:
        sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
        sys.exit(1)

    os.environ.update({"DJANGO_SETTINGS_MODULE": "settings"})
    django.setup()
init_environ()

class PMShopImg(Document):
    '''派美客户每日图片库'''
    create_time = DateTimeField(verbose_name = "创建日期")
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    nick = StringField(verbose_name = "掌柜昵称")
    page_url = StringField(verbose_name = "页面地址")
    img_list = ListField(verbose_name = "链接列表")

    meta = {'db_alias':'pm-db', 'collection':'pm_shop_img', 'indexes':['shop_id', 'nick']}

pm_img_coll = PMShopImg._get_collection()

class PMShopModifiedImg(Document):
    '''派美客户每日图片改动'''
    create_time = DateTimeField(verbose_name = "创建日期")
    shop_id = IntField(verbose_name = "店铺ID", required = True)
    nick = StringField(verbose_name = "掌柜昵称")
    page_url = StringField(verbose_name = "页面地址")
    img_add = ListField(verbose_name = "新增的图片列表")
    img_del = ListField(verbose_name = "删除的图片列表")
    page_status = IntField(verbose_name = "页面状态", choices = [(-1, '删除'), (0, '修改'), (1, '新增')])

    meta = {'db_alias':'pm-db', 'collection':'pm_mod_img', 'indexes':['shop_id', 'nick']}

pm_mod_img_coll = PMShopModifiedImg._get_collection()

class TaoBaoSpider(object):

    def __init__(self, shop_nick_txt):
#         self.driver = webdriver.Chrome()
        self.shop_nick_dict = {}
        self.csv_rows = []
        with open(shop_nick_txt) as f:
            for line in f:
                shop_id, nick = line.strip().split(' ')
                self.shop_nick_dict[int(shop_id)] = nick
        for i, shop_id in enumerate(self.shop_nick_dict):
            print u'%s 进度: %s/%s' % (shop_nick_txt, i + 1, len(self.shop_nick_dict))
            self.crawl(shop_id)
#         self.driver.quit()
        self.result_csv = 'result%s%s' % (os.sep, shop_nick_txt.replace('.txt', '.csv'))
        self.export_to_csv(self.csv_rows)
        print 'finished', shop_nick_txt

    def crawl(self, shop_id):
        '''爬取店铺首页及宝贝详情页'''
        self.driver = webdriver.Chrome()
        try:
            temp_no = 0
            sec = 1
            nick = unicode(self.shop_nick_dict[shop_id])
            print 'crawl home page: shop_id', shop_id, 'nick', nick
            home_url = "https://shop%s.taobao.com/index.htm" % shop_id
            self.driver.get(home_url)
            temp_no += 1
            img_list = list(set(re.findall(r'//\w+\S*?\.jpg', self.driver.page_source)))
            self.save_to_db(shop_id, home_url, img_list)
            time.sleep(sec)

            print 'crawl item page: shop_id', shop_id
            page_no = 1
            while 1:
                search_url = "https://shop%s.taobao.com/search.htm?pageNo=%s" % (shop_id, page_no)
                self.driver.get(search_url)
                temp_no += 1
                time.sleep(sec)
                page_no += 1
                if self.driver.find_elements_by_css_selector('div.no-result-new'):
                    break
                item_id_list = [elem.get_attribute('data-id') for elem in self.driver.find_elements_by_css_selector('dl.item')]
                for item_id in item_id_list:
                    item_url = "https://item.taobao.com/item.htm?id=%s" % item_id
                    self.driver.get(item_url)
                    temp_no += 1
                    time.sleep(sec)
                    img_list = list(set(re.findall(r'//\w+\S*?\.jpg', self.driver.page_source)))
                    self.save_to_db(shop_id, item_url, img_list)
                    if temp_no >= 10:
                        self.driver.quit()
                        self.driver = webdriver.Chrome()
                        temp_no = 0
        except:
            print traceback.print_exc()
        finally:
            self.driver.quit()

    def save_to_db(self, shop_id, page_url, img_list):
        '''数据库存储'''
        create_time = datetime.datetime.now()
        nick = self.shop_nick_dict[shop_id]
        doc = pm_img_coll.find_one({'shop_id':shop_id, 'page_url':page_url})
        if doc:
            img_add = list(set(img_list) - set(doc['img_list']))
            img_del = list(set(doc['img_list']) - set(img_list))
            if img_add and img_del:
                page_status = 1
            elif img_add:
                page_status = 2
            elif img_del:
                page_status = 3
            else:
                page_status = 0
            if page_status:
                pm_mod_img_coll.insert({
                                        'create_time':create_time,
                                        'shop_id':shop_id,
                                        'nick':nick,
                                        'page_url':page_url,
                                        'img_add':img_add,
                                        'img_del':img_del,
                                        'page_status':page_status
                                        })
                pm_img_coll.update({'shop_id':shop_id, 'page_url':page_url}, {'$set':{'create_time':create_time, 'img_list':img_list}})
                td = create_time.date()
                for img in img_add:
                    self.csv_rows.append([td, shop_id, nick, page_url, u'新增', img])
                for img in img_del:
                    self.csv_rows.append([td, shop_id, nick, page_url, u'删除', img])
        else:
            pm_img_coll.insert({
                                'create_time':create_time,
                                'shop_id':shop_id,
                                'nick':nick,
                                'page_url':page_url,
                                'img_list':img_list
                                })

    def export_to_csv(self, rows):
        '''导出至CSV'''
        dirname = os.path.dirname(self.result_csv)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(self.result_csv, 'ab') as f:
            writer = csv.writer(f)
            writer.writerow([u'日期', u'店铺ID', u'掌柜昵称', u'页面网址', u'变化类型', u'图片链接' ])
            writer.writerows(rows)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print u'未指定爬取目录'
        sys.exit()
    txt_list = []
    os.chdir(os.path.join(PROJECT_ROOT, "test", "taobao_spider"))
    for d in sys.argv[1:]:
        txt_list.extend(glob.glob('%s%s*.txt' % (d, os.sep)))
    for shop_nick_txt in txt_list:
        TaoBaoSpider(shop_nick_txt)
#     # 多进程 有问题
#     if txt_list:
#         pool = multiprocessing.Pool(processes = 2)
#         pool.map_async(TaoBaoSpider, txt_list)
#         pool.close()
#         pool.join()
    print 'All finished'
