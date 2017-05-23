
# coding=UTF-8

# 下面的说明待调整更新

'''
settings:
    包含三个部分：
    settings.py 主设置   大家都一样
    settings_local_real.py 用于定制自己本地差异化settings，这个文件不要上传，svn服务器上的版本，该文件必须是空的
    settings_dajax.py ajax配置，大家都一样，用于注册整个系统用到的ajax函数（对应/site_media/js/dajax.js）

init_environ.py：
    在根目录下的任何脚本，只要在文件开始加上    import init_environ  语句。(根目录下的init_environ.py与test.init_environ.py有细微区别)
    就把整个工程添加到了python的系统环境中。 就可以在本py文件中以如下方式import我们工程中的任何包。
    对于apilib、scripts、test 等 工程根目录下的包，可以:
    import apilib
    from apilib.japi import JAPI
    from apilib import *

    对于apps 、 thirdapps 下的所有包，做了更简化的处理，可以：
    import download
    from download.models import *

api的声明、实现、使用方法:
    apilib中包含 api库的实现。针对taobao 和  我们自己的各个子系统的apache services 的api调用，分别在apilib下的tapi.py 和 japi.py 文件中声明。

    api声明：
        tapi.py 声明taobao的api
        japi.py 声明我们自己的各个子系统的api，如：
        run_init_download_manual = bind_api(
                app_name = 'download', #子系统app名称，一定要指定哦
                method_name = 'run_init_download_manual',
            )

    api实现：
                各个子系统app的api，在各个app的api.py中实现，如：
        #下载店铺初始化数据
        def run_init_download_manual(shop_id, request = None):
            result = True
            return request and {'result':result} or TopObjectParser.json_to_object({'result':result})
                    注意事项：
            1.api函数的参数中，一定要以request=None作为结尾参数，实际调用时不需要指定该参数
            2.当以http通信方式调用时，api函数的参数，都是以字符串传入的。请注意处理。
            3.进行api函数调用时，参数名必须显式调用，即：必须在参数中指定参数名
            3.返回值必须是return request and {'result':result} or TopObjectParser.json_to_object({'result':result})
            4.不管是http通信方式调用，还是以内部函数方式调用，返回结果都是TopObject类型，使用方法如下：
                  jobj = api.run_init_download_manual(shop_id=shop_id)
                  print jobj.result

    api调用：方式一：http通信调用
                客户端调用api时必须指定服务host及其port，在apilib中的japi.py中已经对各个子系统的apache_services的host及port做了分配。
                大家只要调用相应函数生成api对象即可，如：
        from apilib import *
        jobj = web_api().run_init_download_manual()
        print jobj.result
        jobj = kwlib_api().get_keyword_list(cat_id=cat_id)
        print jobj.result
                    上面的调用方式默认为同步调用，若希望异步执行，则：
        jobj = web_api().run_init_download_manual(is_sync=False)
        jobj = kwlib_api().get_keyword_list(cat_id=cat_id,is_sync=False)
        print jobj.result == True

    api调用：方式二：内部函数调用
        from apilib import *
        jobj = web_api(True).run_init_download_manual()
        print jobj.result
'''