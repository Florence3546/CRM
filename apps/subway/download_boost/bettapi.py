# coding=utf-8

"""

现阶段，由于下载的速度较慢，是由单线程线性执行的，实际上可以用gevent来加速，但是使用gevent同样会对原来的代码造成一些破坏性的修改，比如pymongo的兼容性等问题。

因此可以使用传统的消费者&生产者的模式来加速。

为了保证修改的量较小，可以提供一些经常用到的下载的逻辑作调整，比如专门有一组（多进程组成）的，并且使用协程加速的api请求。

为了保证灵活及性能，可以将解析的方法也定义好（即callback)，并且每个方法都只提供最原始的api请求封装，不绑定具体的参数。

中间件可以继续使用redis，可以将所有的参数都封装到一个消息队列里，由消费者端负责将消息解析，将找到对应的方法执行。 最后将结果解析汇总，然后再塞回到Redis中去？

入库的逻辑由生产者这边来负责。


### 通道

最好有两个通道，一个优先的通道就是生产者这边需要即时给用户以反馈，表示数据已经下载完毕。另一个是任务性质的，可以下载的稍慢一点。


需要考虑到淘宝API的请求速度，如果都这样使用的话，可能会造成淘宝的流控较高，反而无法加速。

代码的部署：代码是如何部署，是否需要单独的一台机器来部署这些应用，或者在原来的web服务器上添加一个进程来执行，由各自的生产者与消费者绑定成一组？


由于考虑到代码的依赖性，因此这里只作请求，并且将基本的数据结构给返回。不作其它解析、合并的处理。



### 另外，任务的如何分解呢？

来看我们的基本场景呢，主要是应用于批量下载多个adgroup的关键词报表。

然后是针对单个广告组下载下面所有的关键词的报表数据。


因此发布任务的基本单位是adgroup_id为key的。

任务分解到这个级别后，由消费者这边获取到具体的adgroup及对应的参数，这里可以再继续作分解：

1，对天数分解，天数分解到单天。

2，对数据来源作分解，分解到5种数据类型（当然数据类型有依赖，如果没有汇总数据，另外的数据类似就不用再发了）。

### 扩展

如果想对其它的报表加速，自然也是可以的，不过就看值得不值得了，或者想不想做了，比如camp下载adgroup的报表。


### 困难

这里可能还是没有办法将gevent这部分剥离出来，因为考虑了再三，还是没有办法直接构建api，必须要依赖原来的业务逻辑来处理API。

看来下载加速只能靠多线程或者多进程来boost了咯？使用多进程的话及依赖现有的框架的话，还是有觉得有一点麻烦。


### 为什么想自己再写一个HTTP请求的机制

因为以前的机制限定的较死，比较必须等待一秒之类的，是拖慢下载的主要原因之一。还有就是解析的函数可以再改进一下（实际上改进不大）

这样看来，后者的改进较小，无所谓，主要还是前者的改进，在下载慢的地方不能采用统一的机制。

"""

# from gevent import monkey
# monkey.patch_socket()
#
# from gevent import pool

import requests

# class Consumer(object): # 继承自进程？
#
#     def got_task(self):
#         pass
#
#     def run_task(self):
#         pass
#
#
#
# class VirtualRequester(object):
#
#
#     def do_request(self):
#         pass
#
#
# class VirtualDownloader(object):
#
#
#     def __init__(self, init_args):
#         pass
#
#     def parse_args(self):
#         # days-->拆解
#         # source_type 拆解
#         pass
#
#     def split_task(self):
#         self.tasks = []
#
#     def do_request(self):
#         for task in self.tasks:
#             pass
#         self.save_back()
#
#     def save_back(self):
#         # 将数据写回到缓存中
#         # 由原来的生产者负责将数据解析、拼装、入库（这里会不会造成数据量大，实际上仍然没有什么加速？）
#         pass
#
#
# class BaseReportDownloader(VirtualDownloader, VirtualRequester):
#     pass
#
# class EffectReportDownloader(VirtualDownloader, VirtualRequester):
#     pass

if __name__ == "__main__":
    from task_queue import RedisQueue

    task_list = [{

    }]

    RedisQueue.publish_tasks()
