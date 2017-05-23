# coding=UTF-8
import init_environ
import datetime
import time
from django.core.mail import send_mail
from apps.kwlib.tasks import TaskTools
from apps.kwlib.models_redis import KeywordInfo, WordCat
from apps.common.utils.utils_log import log

email_list = ['liushengchuan@paithink.com', 'zy@paithink.com']

# task_list中的所有的任务都是按照顺序来执行的，所以没有特殊情况，不允许调换task的位置
task_list = [
             {'task_name':u"刷新所有关键词数据",
              'task_describe':u"将上次更新的有流量的关键词全部清空，重新刷新有流量的数据，返回结果有流量数据的group个数，基于这个group个数*10000可以大致估算出任务执行结果总量",
              'method':'update_words',
              'rst_method':'get_update_words_result'
              },
             {'task_name':u"刷新所有关键词类目预测结果",
              'task_describe':u"每个关键词对应多个类目，这个匹配规则根据淘宝的类目预测接口来判定，返回结果有执行任务的总量，基于这个任务总量的类目预测之后的结果，根据结果来告知导入到memcache中的数据总量",
              'method':'update_forcecast',
              'rst_method':'get_update_forcecast_result'
              },
             {'task_name':u"导入数据到memcache中",
              'task_describe':u"每次执行完类目预测之后必须要做的一个操作，将最新数据刷新到memcache当中供选词使用，该操作无返回结果，无返回总量",
              'method':'load_data_2memcache',
              'rst_method':''
              },
             {'task_name':u"添加用户关键词",
              'task_describe':u"添加用户关键词到新词队列中，将用户中有展现的关键词全部添加如到redis当中，返回结果返回执行添加用户关键词多少个用户",
              'method':'add_user_keyword',
              'rst_method':''
              },
             {'task_name':u"刷新新词到memcache中",
              'task_describe':u"所有的新的关键词入口都是在db4当中，这些新词需要通过刷新流量类目预测才能够进入到memcache中，下次刷词才会调用生效，所以需要做及时刷新操作，保证新词最新写入到memcache中",
              'method':'update_new_words',
              'rst_method':''
              },

             ]

class KwlibTask():
    def __init__(self, task_name, task_describe, method, rst_method = ''):
        self.task_name = task_name
        self.task_describe = task_describe
        self.method = method
        self.rst_method = rst_method

    @property
    def update_words(self):
        return TaskTools.update_words()

    @property
    def get_update_words_result(self):
        return KeywordInfo.r_gkeyword.dbsize()

    @property
    def update_forcecast(self):
        return TaskTools.update_forcecats()


    @property
    def get_update_forcecast_result(self):
        cat_set = WordCat.r_wckeyword.smembers('cat_set')
        count = 0
        for cat_id in cat_set :
            manager_key = '%s_keyword_list:manager' % cat_id
            for key in WordCat.r_wckeyword.lrange(manager_key, 0, -1):
                count += WordCat.r_wckeyword.llen(key)
        return count

    @property
    def load_data_2memcache(self):
        return  WordCat.load_data_2memcache()

    @property
    def add_user_keyword(self):
        return  TaskTools.add_user_keyword()

    @property
    def update_new_words(self):
        return TaskTools.update_new_words()

    def send_email(self, rst_len, rst_num):
        content = '''
                                           执行任务名称：%s<br>
                                           执行任务总量：%s<br>
                                            执行任务结果：%s<br>
                                            任务描述描述：%s<br>
                 ''' % (self.task_name, rst_len, rst_num, self.task_describe)
        send_mail('词库开始自动执行%s任务' % self.task_name, '', '''%s<%s>''' % ('派生科技', "pskj@paithink.com"), email_list , html_message = content)

    def run(self):
        rst_num = 0
        rst_len = getattr(self, self.method)
        if self.rst_method:
            rst_num = getattr(self, self.rst_method)
        self.send_email(rst_len, rst_num)

if __name__ == '__main__':

    start_time = datetime.date.today()
    is_run_task = True
    while True:
        next_time = start_time + datetime.timedelta(days = KeywordInfo.DATE_LIMIT)
        today = datetime.date.today()
        if (today == next_time):
            is_run_task = True
            start_time = today
        if is_run_task:
            log.info('now start run kwlib task =================================================================')
            for task in task_list:
                tt = KwlibTask(task['task_name'], task['task_describe'], task['method'], task['rst_method'])
                tt.run()
            log.info('now end run kwlib task =================================================================')
            is_run_task = False
        else:
            log.info('now sleep 23 hours wait next check for run kwlib task')
            time.sleep(60 * 60 * 22)

