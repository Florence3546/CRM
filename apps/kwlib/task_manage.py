# coding=UTF-8
import types
import threading
import datetime
import time

from mongoengine.queryset.visitor import Q
from mongoengine.document import DynamicDocument, DynamicEmbeddedDocument
from mongoengine.fields import IntField, DateTimeField, StringField, ListField

from apps.common.utils.utils_log import log
from apps.common.utils.utils_thread import ThreadLock


class TaskExecuter(threading.Thread):
    '''
          任务抽象类，提供控制框架
          适用场景：多线程分批执行具体任务，提供启动、停止等控制操作
    '''
    ''''all_task_num:任务总数 finished_count:以完成任务数 sub_task_count:最大并发数'''
    def __init__(self, manager, iterator, sub_task_count, group_size, method, query_condition, filter_condition):
        self.manager = manager
        self.record_count, self.finished_count, self.start_index, self.prev_index, self.query_condition, self.filter_condition = manager.record_count, manager.finished_count, manager.start_index, manager.prev_index, query_condition, filter_condition
        self.iterator, self.sub_task_count, self.group_size, self.method = iterator, sub_task_count, group_size, method
        self.status = self.get_status()
        self.thread_pool = [] # 线程池,用于登记正在运行的线程
        self.pool_lock = ThreadLock() # 为了保护线程池，分配一把递归锁
        self.finished_count_lock = ThreadLock() # 为了保护完成任务总数，分配一把锁
        self.index_count_lock = ThreadLock()
        self.result = True
        threading.Thread.__init__(self)

    def create_next_subtasks(self, task_num):
        task_list = []
        new_task_num = 0
        while new_task_num < task_num:
            sub_task = SubTaskExecuter(self.iterator, self.start_index, self.prev_index, self.group_size, self.method, self.manager, self.query_condition, self.filter_condition)
            self.prev_index = sub_task.start_index
            self.start_index = sub_task.next_index
            self.query_condition = sub_task.query_condition
            self.filter_condition = sub_task.filter_condition
            if self.prev_index == sub_task.next_index:
                break
            new_task_num += 1
            task_list.append(sub_task)
        return task_list


    def sub_execute(self):
        '''
                   子任务执行函数.用于实现正在干活的业务
        '''
        return


    def save_status(self):
        '''
                   保持状态。不同的任务需要保存的信息不一样，用于任务控制者控制任务
        '''
        return

    def add_finished_count(self, num):
        '''
                   增加成功的任务个数
        '''
        self.finished_count_lock.acquire_lock()
        self.finished_count += num
        self.manager.finished_count = self.finished_count
        self.finished_count_lock.release_lock()
        self.manager.write_status()

    def get_finished_count(self):
        self.finished_count_lock.acquire_lock()
        result = self.finished_count
        self.finished_count_lock.release_lock()
        return result

    def get_finished_index(self):
        self.index_count_lock.acquire_lock()
        prev_index = self.prev_index
        next_index = self.start_index
        self.index_count_lock.release_lock()
        if prev_index == next_index and prev_index != None:
            return False
        return True

    def get_idle_thread_num(self):
        '''
                   获取空闲的线程个数
        '''
        self.pool_lock.acquire_lock()
        idle_num = 0
        thread_num = len(self.thread_pool)
        for tl in self.thread_pool:
            if tl.is_idle() == True:
                idle_num += 1
                continue
        self.pool_lock.release_lock()

        return thread_num, idle_num

    '''
           登记开始执行的子任务
    '''
    def register_subtask(self, sub_task):
        self.pool_lock.acquire_lock()
        self.thread_pool.append(sub_task)
        self.pool_lock.release_lock()

    def update_result(self, num):
        '''
                   刷新执行结果，提供给线程使用
        '''
        self.add_finished_count(num)

    def unregister_subtask(self, sub_task):
        '''
                           注销子任务
            '''
        self.pool_lock.acquire_lock()
        try:
            site = self.thread_pool.index(sub_task)
            sub_task = self.thread_pool[site]
        except Exception, e:
            log.error("unregister_subtask error=%s" % (e))
            self.pool_lock.release_lock()
            return
        self.thread_pool.pop(site)
        self.pool_lock.release_lock()

    def run(self):
        # 启动线程
        for i in range(self.sub_task_count):
            new_thread = SubTaskThread(self)
            new_thread.start() # task先是没有的，每十秒判断有没有task，如果有了，就执行task的execute，并调用TaskExecuter中的update_result
        # 循环执行子任务，直到任务完成，判断完成的group数
#         while self.get_finished_count() < self.record_count :
        while self.get_finished_index():
            # 先检查是否有空闲的线程
            thread_num, idle_thread_num = self.get_idle_thread_num()
            if thread_num == 0: # 没有线程，说明线程执行关闭，任务已经执行结束了
                break
            if idle_thread_num == 0: # 没有空闲的线程，就等1S
                time.sleep(1)
                continue
            # 如果用户关闭了，需要等所有的子任务全部关闭了，然后才能关闭
            if self.status == 'stop' or self.status == 'finished': # 如果任务被关闭，就直接返回
                if idle_thread_num == self.sub_task_count: # 一组全部完成，才关闭
                    self.shut_down_all_threads()
                    self.manager.write_log('task closed by user')
                    return
                else:
                    time.sleep(1)
                    continue
            task_list = []
            task_list = self.create_next_subtasks(idle_thread_num) # 其实是按idle_thread_num（不能多生成，否则线程不够用）来生成相应数量的SubTaskUpdateKeyowrdTask，即真正的task
            if thread_num == idle_thread_num and not task_list:
                self.shut_down_all_threads()
                self.manager.write_log('task closed by user')
                return
            # 启动任务执行
            for tl in task_list:
                work_thread = self.find_first_idle_thread()
                work_thread.set_task(tl) # 设置后SubTaskThread便可拿到SubTaskUpdateKeyowrdTask了，执行其execute
        # 任务执行完毕后，通知线程池中的线程退出
        self.shut_down_all_threads()
        self.manager.finished_count = self.manager.record_count
        self.manager.write_log('task finished!') # 保存执行者状态信息
        self.manager.write_status()


    def find_first_idle_thread(self):
        '''
                             找第一个空闲线程
         '''
        self.pool_lock.acquire_lock()
        for tl in self.thread_pool:
            if tl.is_idle():
                self.pool_lock.release_lock()
                return tl
        self.pool_lock.release_lock()
        return None

    def shut_down_all_threads(self):
        '''
                   关闭所有的线程
        '''
        self.pool_lock.acquire_lock()
        for tl in self.thread_pool:
            tl.shut_down()
        self.thread_pool = []
        self.pool_lock.release_lock()

    def close_task(self):
        self.status = 'stop'

    def get_status(self):
        return 'running'



class SubTaskThread(threading.Thread):
    '''
          执行子任务的线程
    '''
    def __init__(self, father_task):
        self.father_task = father_task
        self.sub_task = None
        self.status_on = True
        self.sub_task_lock = ThreadLock()
        threading.Thread.__init__(self)
        self.status_lock = ThreadLock()
        # self.wait_lock = ThreadLock()

    def set_task(self, sub_task):
        '''
                   设置执行的任务
        '''
        self.sub_task_lock.acquire_lock()
        self.sub_task = sub_task
        self.sub_task_lock.release_lock()
#        self.wait_lock.release_lock()

    def get_task(self):
        '''
                   获取任务
        '''
        self.sub_task_lock.acquire_lock()
        result = self.sub_task
        self.sub_task_lock.release_lock()
        return result

    def get_status(self):
        '''
                   得到线程开关
        '''
        self.status_lock.acquire_lock()
        result = self.status_on
        self.status_lock.release_lock()
        return result

    def is_idle(self):
        '''
                    线程是否忙
        '''
        if self.get_task() == None:
            return True
        return False

    def shut_down(self):
        '''
                   关闭线程
        '''
        self.status_lock.acquire_lock()
        self.status_on = False
        # 任务注销
        self.status_lock.release_lock()

    def start(self):
        '''
                   重写线程的启动函数
        '''
        self.status_on = True
        # 启动该线程
        threading.Thread.start(self)
        # 在父类线程池登记
        self.father_task.register_subtask(self)

    def run(self):
        '''
                   重写线程的运行函数
        '''
        while self.get_status():
            sub_task = self.get_task()
            if sub_task == None:
#                self.wait_lock.acquire_lock()
#                self.wait_lock.acquire_lock()
                time.sleep(1)
                continue
            # 子任务执行
            log.info('sub_task = %s begin to work' % (sub_task))
            finished_count = sub_task.execute()
            log.info('sub_task = %s work finished' % (sub_task))
            if finished_count == -1:
                return
            # 如果子任务完成数目为0，说明已经遍历完，取不到任务，该线程自动结束
            if finished_count == 0 or not finished_count:
                self.father_task.unregister_subtask(self)
                self.shut_down()
                return
            # 刷新父任务的进度
            self.father_task.update_result(finished_count)
            # 子任务清除
            self.set_task(None)


    def __cmp__(self, other):
        '''
                   重写比较函数
        '''
        if self.getName() == other.getName():
            return 0
        else:
            return 1


class SubTaskExecuter():
    '''
         子任务执行者
    '''
    def __init__(self, iterator, start_index, prev_index, group_size, method, manager, query_condition, filter_condition):
        self.iterator = iterator
        self.start_index = start_index
        self.prev_index = prev_index
        self.group_size = group_size
        self.method = method
        self.manager = manager
        self.query_condition = query_condition
        self.filter_condition = filter_condition

        log.info('start get data from database where index = %s-%s' % (str(self.start_index), str(self.group_size)))
        start_time = datetime.datetime.now()
        record_list, next_index = eval(self.iterator).get_record_list(self.start_index, self.prev_index, self.group_size, self.manager, self.query_condition, self.filter_condition)
        self.next_index = next_index
        task_manager_coll.update({'task_id':self.manager.task_id}, {'$set':{'prev_index':self.start_index, 'start_index':self.next_index, 'query_condition':self.query_condition, 'filter_condition':self.filter_condition}})
        log.info('end get data from database where $gt index =%s,next_index = %s,cost time is = %s' % (str(self.start_index), str(self.next_index), datetime.datetime.now() - start_time))
        self.record_list = record_list

    def execute(self):
        result = 0
        method_string = self.method + '(self.record_list,self.manager)'
        try:
            result = eval(method_string)
        except Exception, e:
            log.error('e=%s' % e)
        finally:
            return result

#######DEMO################
tt = range(1000)
class test_it:
    @staticmethod
    def get_record_list(start_index, record_count):
        return tt[start_index:start_index + record_count]
    @staticmethod
    def get_all_record_count():
        return len(tt)

def test_method(record_list, manager):
    for rl in record_list:
        print rl

# 应用如下,创建一个任务管理器，然后运行任务即可
# manager = TaskManager.create_manager(1)
# manager.run_task()
########END#################
'''
任务配置信息。凡是遍历某个数据，需要多线程扫描，就可以利用该框架。业务需要实现取记录的函数，以及对这些记录操作的API(不返回值)。
在此框架运行的任务，支持多线程 运行，支持日志记录，任务运行进度查询，任务启动，任务停止，管理员界面自动展现任务。简单Demo
请参考上面的DEMO，多线程遍历打印1000个数.
'''
task_cfg = {
# 1:{'task_type':u'test', 'task_descr':u'test', 'iterator':'test_it', 'sub_task_count':5, 'group_size':10, 'method':'test_method'},
1:{'task_type':u'加词_用户关键词', 'task_descr':u'从当前用户找出所有有展现的关键词，补充到词库中', 'iterator':'Account', 'manager':'TaskManager', 'sub_task_count':10, 'group_size':5, 'method':'add_user_keyword', 'query_condition':"{}", 'filter_condition':"{}"},
2:{'task_type':u'刷新_关键词类目统计信息', 'task_descr':u'获取关键词类目下的统计信息，包括类目下的展现、点击、CPC等', 'iterator':'Cat', 'manager':'TaskManager', 'sub_task_count':1, 'group_size':1, 'method':'update_word_cats_new', 'query_condition':"{}", 'filter_condition':"{}"},
3:{'task_type':u'刷新_关键词全网统计信息', 'task_descr':u'获取关键词全网统计信息，包括展现、点击、CPC等', 'iterator':'KeywordInfo', 'manager':'TaskManager', 'sub_task_count':5, 'group_size':10000, 'method':'update_words_gdata', 'query_condition':"{}", 'filter_condition':"{'word':1,'g_pv':1}"},
4:{'task_type':u'加词_top20万、人工收集关键词', 'task_descr':u'从淘宝下载的top20万或者本地收集的关键词', 'iterator':'FileManager', 'manager':'TaskManager', 'sub_task_count':1, 'group_size':200000, 'method':'add_file_word', 'query_condition':"{}", 'filter_condition':"{}"},
5:{'task_type':u'刷新_关键词的类目信息', 'task_descr':u'从淘宝获取关键所在的所有类目', 'iterator':'KeywordInfo', 'sub_task_count':5, 'group_size':10000, 'manager':'TaskManager', 'method':'update_wordforecast_new', 'query_condition':"{'g_pv':{'$gt':0}}", 'filter_condition':"{'word':1}"},
6:{'task_type':u'加词_获取类目相关词', 'task_descr':u'对已有关键词调取apilib.apilib.tsapi获取和已有关键词相关的词', 'iterator':'KeywordInfo', 'manager':'TaskManager', 'sub_task_count':1, 'group_size':10000, 'method':'save_related_word_new', 'query_condition':"{}", 'filter_condition':"{'word':1}"},
7:{'task_type':u'加词_获取类目Top词', 'task_descr':u'对已有的类目调取apilib.apilib.tsapi获取该类目下的top关键词', 'iterator':'Cat', 'manager':'TaskManager', 'sub_task_count':1, 'group_size':1, 'method':'save_cat_topword_new', 'query_condition':"{}", 'filter_condition':"{}"},
8:{'task_type':u'管理_清理垃圾词', 'task_descr':u'对大词库进行清理垃圾词操作，主要针对含有特殊符号并且没有全网流量的词', 'iterator':'KeywordInfo', 'manager':'TaskManager', 'sub_task_count':5, 'group_size':10000, 'method':'clear_garbage_word', 'query_condition':"{}", 'filter_condition':"{}"},
9:{'task_type':u'管理_清理禁用词', 'task_descr':u'对大词库进行清理禁用词操作，主要根据禁用词表当中的所有禁用词，如果词库中的关键词包含任何一个禁用词则被删除', 'iterator':'KeywordInfo', 'manager':'TaskManager', 'sub_task_count':10, 'group_size':10000, 'method':'clear_forbid_word', 'query_condition':"{}", 'filter_condition':"{}"},
10:{'task_type':u'加词_分配词根到用户爬词', 'task_descr':u'从大词库分配词给前台用户爬取词，每次登陆到宝贝列表，用户将开始启动爬词并反馈结果给词库', 'iterator':'KeywordInfo', 'manager':'ClawManager', 'sub_task_count':1, 'group_size':100, 'method':'get_keyword_2web', 'query_condition':"{}", 'filter_condition':"{}"},
11:{'task_type':u'管理_为每个关键词做分解分解成产品词和修饰词', 'task_descr':u'每个关键词由一个或没有产品词和一个或多个修饰词组词，将它们分解成由类目加产品词和修饰词，并存放到小表当中', 'iterator':'WordCat', 'manager':'TaskManager', 'sub_task_count':10, 'group_size':1000, 'method':'get_prdt_dcrt_words', 'query_condition':"{}", 'filter_condition':"{}"},
12:{'task_type':u'刷新_所有类目信息', 'task_descr':u'获取所有类目信息，包括类目名称、类目ID、父类目名称', 'iterator':'Cat', 'manager':'TaskManager', 'sub_task_count':1, 'group_size':100000, 'method':'update_all_cats_new', 'query_condition':"{}", 'filter_condition':"{}"},
13:{'task_type':u'刷新_新词类目预测信息', 'task_descr':u'获取每天入库的新词，并对其进行类目预测', 'iterator':'NewWorCatInfo', 'manager':'TaskManager', 'sub_task_count':10, 'group_size':10000, 'method':'update_cat_info', 'query_condition':"{}", 'filter_condition':"{}"},
14:{'task_type':u'wordcat表同步到关键词表word当中补全关键词表', 'task_descr':u'导数据时不能保证keywordinfo和wordcat表同步，所以得先把wordcat中没有的词同步到keywordinfo当中', 'iterator':'WordCat', 'manager':'TaskManager', 'sub_task_count':15, 'group_size':5000, 'method':'wc_syn_kw', 'query_condition':"{}", 'filter_condition':"{}"},
15:{'task_type':u'keywordinfo补全wordcat表当中的ref_id', 'task_descr':u'将keyword的引用同步到wordcat的ref_id当中', 'iterator':'KeywordInfo', 'manager':'TaskManager', 'sub_task_count':10, 'group_size':10000, 'method':'kw_syn_wc', 'query_condition':"{}", 'filter_condition':"{}"},
16:{'task_type':u'统计wordcat当中每个类目下的统计信息', 'task_descr':u'统计每个类目下的avg_cpc,avg_click,word_count等等并把统计信息保存到Cat表当中去', 'iterator':'Cat', 'manager':'TaskManager', 'sub_task_count':10, 'group_size':5, 'method':'flowrate_in_singlecat', 'query_condition':"{}", 'filter_condition':"{}"},
17:{'task_type':u'新版本的爬词任务，新版suggest爬词，用于爬取关键词属性，关键词', 'task_descr':u'从淘宝下拉框列表当中爬取关键词，爬取到的关键词存入到爬词表当中，定期同步word到词库', 'iterator':'KeywordClawer', 'manager':'ClawNewManager', 'sub_task_count':1, 'group_size':20, 'method':'get_keyword_2web', 'query_condition':"{}", 'filter_condition':"{}"},
}



class LogInfo(DynamicEmbeddedDocument):
    '''
         任务控制器。负责任务的控制，具体的执行由任务执行者负责。
    '''
    info = StringField(verbose_name = "单条日志", max_length = 1024)

class TaskManager(DynamicDocument):
    '''
         管理所有的任务的总控制器，其中实现功能，启动任务，暂停任务，读取任务进度，创建任务，查找任务，更新日志
    '''
    task_id = StringField(verbose_name = "")
    task_type_id = IntField(verbose_name = "任务类型ID")
    record_count = IntField(verbose_name = "总的任务数")
    finished_count = IntField(verbose_name = "完成数")
    start_time = DateTimeField(verbose_name = "开始时间")
    finished_time = DateTimeField(verbose_name = "结束时间")
    log_list = ListField(verbose_name = "日志记录")
    oper_status = StringField(verbose_name = "任务状态")
    file_path = StringField(verbose_name = "文件路径")
    start_index = StringField(verbose_name = '下一个排序执行的_id')
    prev_index = StringField(verbose_name = '上一个排序执行的_id')
    meta = {'allow_inheritance':True, "db_alias": "kwlib-db"}
    manager_list = []

    @staticmethod
    def create_manager(task_type_id):
        '''
                    创建一个task，前台传入一个task_type_id,如果为文件则需传入file_path。创建task时还需要确认该task是否为爬词任务，如果是，则不需要新建，
                    修改finished
        '''
        TaskManager.check_manager_list()
        now_time = datetime.datetime.now()
        task_id = now_time.strftime('%m%d%H%M%S')
        manager = None
        task_dict = task_cfg[task_type_id]
        if task_dict['iterator'] == 'FileManager':
            record_count = 1 # 为了防止获取总数为0直接返回所以设置为1，在view当中要重新赋值
        else:
            record_count = eval(task_dict['iterator']).get_all_record_count()
        if record_count == 0:
            return None
        if task_type_id == 10 or task_type_id == 17:
            manager = TaskManager.objects.filter(task_type_id = task_type_id)
            if manager:
                manager = manager[0]
                if manager.finished_count >= manager.record_count:
                    manager.finished_count = 0
                    manager.start_time = now_time
                    manager.save()
                return manager
            else:
                manager = eval(task_dict['manager'])(task_id = task_id, task_type_id = task_type_id, record_count = record_count, finished_count = 0, start_index = None, prev_index = None, start_time = now_time)

        else:
            manager = TaskManager(task_id = task_id, task_type_id = task_type_id, record_count = record_count, finished_count = 0, start_index = None, prev_index = None, start_time = now_time)
        if manager:
            TaskManager.manager_list.append(manager) # 加入内存队列
            manager.oper_status = 'running'
            manager.save() # 刷新数据库中
            manager.write_log('create task ok') # 记录日志
        # 对于特殊的任务创建可以在后面根据task_type_id进行补充
        return manager

    @staticmethod
    def find_task(task_id):
        '''
                   查询任务，找到则返回
        '''
        for task in TaskManager.manager_list:
            if task.task_id == task_id:
                return task
        return None

    @staticmethod
    def check_manager_list():
        '''
                    服务器意外重启。断电情况把数据库当中为执行的任务和暂停转化为挂起的任务，并全部加载到TaskManager.manager_list当中
        '''
        if not TaskManager.manager_list:
            result_list = TaskManager.objects.filter(Q(oper_status = 'running') | Q(oper_status = 'stop') | Q(oper_status = 'suspend'))
            if result_list:
                for manager in result_list:
                    TaskManager.manager_list.append(manager)
                    manager.oper_status = 'suspend'
                    manager.save()

    def run_task(self):
        '''
                    运行任务，需要手动调用，并个当前运行的task创建一个excute执行者
        '''
#        if self.finished_count >= self.record_count: # 如果任务已经运行完毕，就直接返回
#            task_manager_coll.update({'task_id':self.task_id}, {'$set':{'oper_status':'finished'}})
#            return []
        task = None
        try:
            task = TaskManager.objects.get(task_id = self.task_id)
        except Exception, e:
            log.info('The error is = %s' % e)
        self.start_index, self.prev_index = task.start_index, task.prev_index
        task_manager_coll.update({'task_id':self.task_id}, {'$set':{'oper_status':'running'}})
        self.oper_status = 'running'
        task_dict = task_cfg[self.task_type_id] # 创建executer
        executer = TaskExecuter(self, task_dict['iterator'], task_dict['sub_task_count'], task_dict['group_size'], task_dict['method'], task_dict['query_condition'], task_dict['filter_condition'])
        self.executer = executer
#        self.executer.run()
        self.executer.setDaemon(True)
        self.executer.start()

    def stop_task(self):
        '''
                      停止任务，修改任务状态
        '''
        task_manager_coll.update({'task_id':self.task_id}, {'$set':{'oper_status':'stop'}})
        self.oper_status = 'stop'
        self.executer.close_task()

    def get_log(self):
        '''
                   查看日志
        '''
        return self.log_list

    def write_log(self, str_log):
        '''
                     增加日志，写到数据库当中
        '''
        t_str = time.strftime('%m-%d %H:%M:%S ') + str_log
        task_manager_coll.update({'task_id':self.task_id}, {'$push':{'log_list':{'info':t_str}}})
#        log_record = Log_Info(info = t_str)
#        self.log_list.append(log_record)
#        self.save()

    def get_percentage(self):
        '''
                     任务执行的百分比
        '''
        if self.record_count:
            return '%.2f' % float(self.finished_count * 100.00 / self.record_count) + '%'
        return '0%'

    def write_status(self):
        '''
        .记录任务进行的进度，如果任务执行完成，则记录任务的完成时间，修改任务的状态为已完成,清掉TaskManager.manager_list当中的manager，否则值记录完成数
        '''
        manager = TaskManager.objects.get(task_id = self.task_id)
        manager.finished_count = self.finished_count
        if(self.finished_count >= self.record_count):
            finished_time = datetime.datetime.now()
            if manager in TaskManager.manager_list:
                TaskManager.manager_list.remove(manager) # 清除缓存在内存当中的manager
                manager.oper_status = 'finished'
                manager.finished_time = finished_time
        manager.save()

task_manager_coll = TaskManager._get_collection()

class FileManager():
    '''
         文件任务管理，主要分配每个线程调取文件内容的个数，文件管理不需要标注文件的长度方法，文件的finished_count和其他任务的task相对独立不需要管理
    '''
    @staticmethod
    def get_record_list(start_index, prev_index, group_size, manager, query_condition, filter_condition):
        '''
        .获取上传文件当中的关键词，并且记录下标存入到数据库当中
        '''
        if start_index == None and prev_index == None:
            start_index = '0'
        start_index = int(start_index)
        result_list = []
        try:
            file_r = open(manager.file_path, 'rb')
            offset = manager.finished_count # 取文件的偏移量
            file_r.seek(offset)
            while True:
                word = file_r.readline()
                if word != None and len(result_list) <= group_size: # 如果文件读取完成或者超过预定的长度则停止读取
                    try:
                        word = word.decode('gbk').strip('\r\n') # 为每个word去除'\r\n'操作
                    except Exception:
                        continue
                    result_list.append(word)
                else:
                    break
            manager.finished_count = int(file_r.tell()) # 保存读取后的文件偏移量以便于下次取文件内容
        except Exception, e:
            log.info('file open failed, e=%s' % e)
        finally:
            file_r.close()
        str_next_index = str(manager.finished_count)
        next_index = str_next_index
        return result_list, str(next_index)


