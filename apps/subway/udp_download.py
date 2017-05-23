# coding=UTF-8
from utils import *
from apilib import *
from apps.common.utils.utils_datetime import *
from models_account import account_coll
from models_item import item_coll

def check_parameters(func):
    """
        该函数是为了提取所有的公共接口而参数正确性的装饰器
    """
    def _check_parameters(self, flag = False, date_scope = (), * args, **kwargs):
        if flag:
            if not tapi or not date_scope:
                log.info('the tapi or date_scope is necessary.')
                return False
        else:
            if not tapi :
                log.info('the tapi is necessary.')
                return False
        return func(self = self, flag = flag, date_scope = date_scope, *args, **kwargs)
    return _check_parameters

class UdpSyncer(object):
    """
      用于下载UDP店铺数据及宝贝数据的接口
      对外提供接口：
        1.通过店铺ID同步店铺UDP数据
            sync_shop_udp(self, shop_id, udp_fields, flag = False)
        2.通过宝贝ID列表同步多个宝贝UDP数据
            sync_items_udp(self, item_id_list, udp_fields, flag = False)
        3.通过宝贝ID列表同步多个宝贝UDP数据
            sync_item_udp(self, item_id, udp_fields, flag = False)
        4.通过店铺ID同步多个宝贝UDP数据
            sync_items_udp_byshop(self, shop_id, udp_fields, flag = False)

      参数说明:
            shop_id:         店铺ID
            udp_fields:      udp下载字段
            flag：                是否强制下载
            date_scope：       下载时间区间
            tapi：                淘宝API

      接口返回结果:
            True/False(boolean)
    """
    # TODO: 淘宝没准备好数据的情况下，需要考虑
    # TODO: 下载时间是否统一补全，而不是逐一补全
    def __init__(self, shop_id, tapi = None):
        self.shop_id = int(shop_id)
        self.tapi = tapi


    @check_parameters
    def sync_shop_udp(self, date_scope, udp_fields, flag = False):
        """
            通过店铺ID同步店铺UDP数据
        """
        date_scope = self.__get_valid_date_scope(coll = account_coll, date_scope = date_scope, shop_id = self.shop_id, item_id = None, flag = flag, tapi = self.tapi)
        if not date_scope:
            return True
        if self.__sync_shop_udp(shop_id = self.shop_id, udp_fields = udp_fields, date_scope = date_scope, tapi = self.tapi):
            log.info('download shop UDP OK, shop_id=%s!' % (self.shop_id))
        else:
            log.info('download shop UDP error, shop_id=%s!' % (self.shop_id))

    @check_parameters
    def sync_items_udp(self, item_id_list, date_scope, udp_fields, flag = False):
        """
            通过宝贝ID列表同步多个宝贝UDP数据
            注: item_id_list一定要为int数组
        """
        # 验证宝贝UDP数据是否需要下载
        result_dict = self.__get_item_id_dict(coll = item_coll, item_id_list = item_id_list, date_scope = date_scope, flag = flag, tapi = self.tapi)
        if result_dict:
            return self.__sync_items_udp(udp_fields = udp_fields, shop_id = self.shop_id, item_id_dict = result_dict, date_scope = date_scope, tapi = self.tapi)
        return True

    @check_parameters
    def sync_item_udp(self, item_id, date_scope, udp_fields, flag = False):
        """
            通过宝贝ID同步单个宝贝UDP数据
        """
        date_scope = self.__get_valid_date_scope(coll = item_coll, date_scope = date_scope, shop_id = self.shop_id, item_id = item_id, flag = flag, tapi = self.tapi)
        if not date_scope:
            return True
        return self.__sync_item_udp(udp_fields = udp_fields, shop_id = self.shop_id, item_id = item_id, date_scope = date_scope , tapi = self.tapi)

    @check_parameters
    def sync_items_udp_byshop(self, date_scope, udp_fields, flag = False):
        """
            通过店铺ID同步多个宝贝UDP数据
        """
        try:
            cursor = item_coll.find({'shop_id':int(self.shop_id)}, {'_id':1})
            item_id_list = []
            for item in cursor:
                item_id_list.append(int(item.get('_id')))
            return self.sync_items_udp(item_id_list = item_id_list, date_scope = date_scope, udp_fields = udp_fields, flag = flag)
        except Exception, e:
            log.exception('access db error, e=%s' % e)
            return False

    def  __get_item_id_dict(self, coll, item_id_list, date_scope, flag = False, tapi = None):
        """
            排除掉无需下载的item字段
        """
        try:
            datas = coll.find({'shop_id':int(self.shop_id), '_id':{'$in':[int(item_id) for item_id in item_id_list]}}, {'udp_list':{'$slice':-1}, 'udp_list.date':1})
            result = {} # 格式: {'宝贝ID','下载有效时间'}
            if datas:
                ytime = datetime.datetime.now() - datetime.timedelta(days = 1)
                ydate = datetime.datetime(ytime.year, ytime.month, ytime.day)
                for data in datas:
                    item_id = int(data.get('_id'))
                    if flag:
                        result[str(item_id)] = self.__get_valid_timescope_bytapi(date_scope, item_id , tapi)
                        continue

                    if data and data.get('udp_list', None):
                        db_time = data['udp_list'][0]['date']
                        if db_time.date() >= ydate.date():
                            # 数据库数据已经是最新，因而不需要下载
                            continue
                        else:
                            # 获取自动补全的数据段
                            temp_date_scope = (db_time + datetime.timedelta(days = 1), ydate)
                    else:
                        # 获取数据库没有记录时，应下载数据的天数
                        start_date = ydate - datetime.timedelta(days = 14)
                        temp_date_scope = (start_date, ydate)

                    result[str(item_id)] = self.__get_valid_timescope_bytapi(temp_date_scope, item_id , tapi)
            return result
        except Exception, e:
            log.exception('access db error, e=%s' % e)
            return {}

    def __get_valid_date_scope(self, coll, date_scope, shop_id, item_id = None, flag = False, tapi = None):
        """
            获取到UDP数据的正确下载时间段
            接口要求：
                coll：pymongo模式的collection
                item_id:宝贝ID
                flag:是否强制下载标识
                tapi:访问淘宝的Tapi
            返回参数：
                        时间元祖（tuple/()）：绝对有效的时间范围
        """
        if flag:
            # 强制更新需要进行下载
            return self.__get_valid_timescope_bytapi(date_scope, item_id = item_id, tapi = tapi)

        try:
            # 获取UDP在对象中的数据
            if 'subway_account' == coll.name:
                data = coll.find_one({'_id':int(shop_id)}, {'udp_list':{'$slice':-1}, 'udp_list.date':1})
            elif 'subway_item' == coll.name:
                data = coll.find_one({'shop_id':int(shop_id), '_id':int(item_id)}, {'udp_list':{'$slice':-1}, 'udp_list.date':1})
            else:
                # TODO:此处暂未处理
                return ()
        except Exception, e:
            if item_id:
                log.exception('access DB is error. shop_id=%s, item_id=%s, e=%s' % (shop_id, item_id, e))
            else:
                log.exception('access DB is error. shop_id=%s, e=%s' % (shop_id, e))
            return ()

        # 确定下载UDP数据的有效时间
        # 得到最初的时间段
        ytime = datetime.datetime.now() - datetime.timedelta(days = 1)
        ydate = datetime.datetime(ytime.year, ytime.month, ytime.day)
        if data and data.get('udp_list', None):
            # 获取数据库有记录，并且没有进行强制下载时，应进行自动补全天数
            db_time = data['udp_list'][0]['date']
            if db_time.date() >= ydate.date():
                # 数据库数据已经是最新，因而不需要下载
                return ()
            else:
                # 获取自动补全的数据段
                date_scope = (db_time + datetime.timedelta(days = 1), ydate)
        else:
            # 获取数据库没有记录时，应下载数据的天数
            start_date = ydate - datetime.timedelta(days = 14)
            date_scope = (start_date, ydate)

        # 通过淘宝API还确定有效的时间
        return self.__get_valid_timescope_bytapi(date_scope, item_id = item_id, tapi = tapi)

    def __get_valid_timescope_bytapi(self, time_scope, item_id = None, tapi = None):
        """
            获取淘宝UDP数据可以下载的时间范围
        """
        if not time_scope:
            return ()

        days = (time_scope[1] - time_scope[0]).days
        temp_time = time_scope[1]
        for day in range(days + 1):
            try:
                if not item_id:
                    # 店铺UDP全地区检测字段
                    shop_test_field1 = Const.SUBWAY_ALL_REGION_MORE_DAYS_PARAMETERS[:5] + Const.SUBWAY_ALL_REGION_MORE_AREAS_PARAMETERS[:5]
                    # 店铺UDP全国检测字段
                    shop_test_field2 = Const.SUBWAY_NATIONWIDE_PARAMETERS[:5] + Const.SUBWAY_NATIONWIDE_DAYS_PARAMETERS[:5]
                    tapi.udp_shop_get(begin_time = temp_time, end_time = temp_time, fields = ','.join(shop_test_field1), area = 999999)
                    tapi.udp_shop_get(begin_time = temp_time, end_time = temp_time, fields = ','.join(shop_test_field2), area = 0)
                else:
                    # 宝贝UDP检测字段
                    item_test_field = Const.SUBWAY_SUPPORT_SOURCE_FIELDS[:5] + Const.SUBWAY_NONSUPPORT_SOURCE_FIELDS[:5]
                    tapi.udp_item_get(begin_time = temp_time, end_time = temp_time, fields = ','.join(item_test_field), itemid = item_id)
                break
            except Exception, e:
                log.info('%s' % e)
                temp_time = time_scope[1] - datetime.timedelta(day + 1)
                if temp_time < time_scope[0]:
                    return ()
                continue
        return (time_scope[0], temp_time)

    def __get_fields_list(self, field_list):
        size = 10
        list_len = len(field_list)
        no_remainder = list_len % size == 0
        result_list = []
        max_index = list_len / size
        for index in range(max_index):
            fields = field_list[index * size:(index + 1) * size]
            result_list.append(','.join(fields))
        if not no_remainder:
            result_list.append(','.join(field_list[max_index * size:]))
        return result_list

    def __get_shop_udp_fields(self, udp_fields):
        """
            获取需要下载的udp字段字典
            字典里将所有进行下载的UDP数据字段进行分类
            并以字典的形式返回
        """
        if not udp_fields:
            return {}

        # 该列表存储可以查询多天数据报表,此部分需要逐天下载，属于全地区范围，标示位999999
        allrange_days_list = []
        # 该列表存储可以查询地区细节的字段,此部分需要在下载部分汇总，属于全地区范围，表示位999999
        allrange_areas_list = []
        # 该列表存储可以查询当天详细数据，此部分在下载时需要汇总，属于全国范围标示位0
        nationwide_day_list = []
        # 该报表存储可以查询多天报表数据，此部分在下载时需要逐天下载，属于全国范围标示位0
        nationwide_days_list = []

        # 初始化字段分类字典，并进行分类操作
        for field in udp_fields:
            # 过滤所有的需要输入全国参数的字段
            if field in Const.SUBWAY_NATIONWIDE_DAYS_PARAMETERS:
                nationwide_days_list.append(field)
            elif field in Const.SUBWAY_NATIONWIDE_DAY_PART_PARAMETERS:
                nationwide_day_list.append(field)
            # 过滤所有的需要输入全地区参数的字段，如果存在全国全地区都存在的字段，以全国优先
            elif field in Const.SUBWAY_ALL_REGION_MORE_AREAS_PARAMETERS:
                allrange_areas_list.append(field)
            elif field in Const.SUBWAY_ALL_REGION_MORE_DAYS_PARAMETERS:
                allrange_days_list.append(field)

        shop_udp_field_dict = {
                                   Const.SUBWAY_SHOP_FIELD_TYPE[0]:self.__get_fields_list(nationwide_days_list),
                                   Const.SUBWAY_SHOP_FIELD_TYPE[1]:self.__get_fields_list(nationwide_day_list),
                                   Const.SUBWAY_SHOP_FIELD_TYPE[2]:self.__get_fields_list(allrange_days_list),
                                   Const.SUBWAY_SHOP_FIELD_TYPE[3]:self.__get_fields_list(allrange_areas_list)
                               }
        return shop_udp_field_dict

    def __get_item_udp_fields(self, udp_fields):
        """
            获取需要下载的udp字段字典
            字典里将所有进行下载的UDP数据字段进行分类
            并以字典的形式返回
        """
        if not udp_fields:
            return []

        # 允许支持添加数据来源字段的列表
        support_field_list = []
        # 不允许允许支持添加数据来源字段的列表
        unsupport_field_list = []

        for field in udp_fields:
            if field in Const.SUBWAY_SUPPORT_SOURCE_FIELDS:
                support_field_list.append(field)
            elif field in Const.SUBWAY_NONSUPPORT_SOURCE_FIELDS:
                unsupport_field_list.append(field)

        item_udp_field_dict = {
                               Const.SUBWAY_ITEM_FIELD_TYPE[0]:self.__get_fields_list(support_field_list),
                               Const.SUBWAY_ITEM_FIELD_TYPE[1]:self.__get_fields_list(unsupport_field_list)
                              }
        return item_udp_field_dict

    def __get_shop_udp(self, udp_fields, date_scope = (), tapi = None):
        """
            下载店铺UDP数据接口
            接口要求：
            date_scope 要求 date_scope[1] >= date_scope[0]
                                                要求time_scope[1]不能大于等于当天时间
            udp_fields 要求符合正确的JAPI UDP接口字段，保证字段的正确性
                                                要求字段是经过去重操作的
            返回参数：
                            数据字典(dict)
        """
        # 获取UDP分类字段字典
        udp_field_dict = self.__get_shop_udp_fields(udp_fields = udp_fields)
        # 下载UDP数据
        data_dict = self.__download_shop_udp(shop_udp_field_dict = udp_field_dict, date_scope = date_scope, tapi = tapi)
        # 转换存储列表,此列表经过排序
        udp_save_list = self.__transfer_save_list(data_dict, Const.SUBWAY_UDP_SHOP_MAPPING)
        return udp_save_list

    def __download_support_source(self, field_list, udp_item_dict, item_id, tapi = None):
        """
            基于单个商品下载支持数据来源的UDP商品数据
            该接口对于udp下载需要进行逐天下载
        """
        try:
            # 执行每个宝贝的udp数据下载
            for fields in field_list:
                for date in udp_item_dict:
                    obj = tapi.udp_item_get(begin_time = date, end_time = date, fields = fields, source = 999, itemid = item_id)
                    udp_item_dict[date].update(eval(obj.content.result_data))
        except TopError, e:
            log.error('download item udp error, item_id=%s, e=%s' % (item_id, e))
            return False
        return True

    def __download_unsupport_source(self, field_list, time_tuple, udp_item_dict, item_id, tapi = None):
        """
            基于单个商品下载不支持数据来源的UDP商品数据
            该接口可以对商品udp数据进行多天下载
        """
        try:
            # 执行每个宝贝的udp数据下载
            for fields in field_list:
                obj = tapi.udp_item_get(begin_time = time_tuple[0], end_time = time_tuple[1], fields = fields, itemid = item_id)
                result_dict = eval(obj.content.result_data)
                for field in result_dict:
                    for date in result_dict[field]:
                        if udp_item_dict.get(date, {}):
                            udp_item_dict[date][field] = result_dict[field][date]
        except TopError, e:
            log.error('download item udp error, item_id=%s, e=%s' % (item_id, e))
            return False
        return True

    def __download_nationwide_days(self, field_list, udp_data_dict, date_scope = (), tapi = None):
        """
            下载全国多天数据，通过可以多天查询数据字段进行下载
            其中的下载字段要属于集合：Const.NATIONWIDE_DAYS_PARAMETERS
        """
        try:
            for fields in field_list:
                obj = tapi.udp_shop_get(begin_time = date_scope[0], end_time = date_scope[1], fields = fields, area = 0)
                result_dict = eval(obj.content.result_data)
                for key in result_dict.keys():
                    date_list = result_dict[key].keys()
                    for date in date_list:
                        if udp_data_dict.has_key(date):
                            udp_data_dict[date][key] = result_dict[key][date]
        except TopError, e:
            log.error("download shop udp error, e=%s" % e)
            return False
        return True

    def __download_nationwide_day(self, field_list, udp_data_dict, date_list, tapi = None):
        """
            逐一下载全国每天数据，通过全国单天数据查询字段进行下载
            其中的下载字段要属于集合：NATIONWIDE_DAY_PART_PARAMETERS
        """
        interval_date_list = get_interval_date_list(date_list)
        if not interval_date_list:
            return False

        try:
            for fields in field_list:
                for date_scope in interval_date_list:
                    obj = tapi.udp_shop_get(begin_time = date_scope[0], end_time = date_scope[1], fields = fields, area = 0)
                    result_dict = eval(obj.content.result_data)
                    for key in result_dict.keys():
                        date = str(date_scope[0])[:10]
                        if udp_data_dict.has_key(date):
                            udp_data_dict[date][key] = accumulation_values(result_dict[key])
        except TopError, e:
            log.error("download shop udp error, e=%s" % e)
            return False
        return True

    def __download_allrange_days(self, field_list, udp_data_dict, date_list, tapi = None):
        """
            下载全地区多天数据，通过全地区多天数据查询字段进行下载
            其中的下载字段要属于集合：Const.ALL_REGION_MORE_DAYS_PARAMETERS
        """
        interval_date_list = get_interval_date_list(date_list)
        if not interval_date_list:
            return False

        try:
            for fields in field_list:
                for time in interval_date_list:
                    obj = tapi.udp_shop_get(begin_time = time[0], end_time = time[1], fields = fields, area = 999999)
                    result_dict = eval(obj.content.result_data)
                    for key in result_dict.keys():
                        date_value = result_dict[key]
                        for date_key in date_value.keys():
                            if udp_data_dict.has_key(date_key[0:10]):
                                udp_data_dict[date_key[0:10]][key] = date_value[date_key]
                                break
        except TopError, e:
            log.error("download shop udp error, e=%s" % e)
            return False
        return True

    def __download_allrange_areas(self, field_list, udp_data_dict, tapi = None):
        """
            逐一下载全地区多地方数据，通过全地区多地区数据查询字段进行下载
            其中的下载字段要属于集合：Const.ALL_REGION_MORE_AREAS_PARAMETERS
        """
        try:
            for fields in field_list:
                for date in udp_data_dict:
                    obj = tapi.udp_shop_get(begin_time = date, end_time = date, fields = fields, area = 999999)
                    result_dict = eval(obj.content.result_data)
                    for key in result_dict.keys():
                        if udp_data_dict.has_key(date):
                            udp_data_dict[date][key] = accumulation_values(result_dict[key])
        except TopError, e:
            log.error("download shop udp error， e=%s" % e)
            return False
        return True

    def __download_shop_udp(self, shop_udp_field_dict, date_scope = (), tapi = None):
        """
            同步下载店铺UDP数据
        """
        # 检查字典中是否存在我们所需要的数据
        if not(shop_udp_field_dict.has_key(Const.SUBWAY_SHOP_FIELD_TYPE[0])
               or shop_udp_field_dict.has_key(Const.SUBWAY_SHOP_FIELD_TYPE[1])
               or shop_udp_field_dict.has_key(Const.SUBWAY_SHOP_FIELD_TYPE[2])
               or shop_udp_field_dict.has_key(Const.SUBWAY_SHOP_FIELD_TYPE[3])):
            log.info('the shop_udp_field_dict is not fields, check date error!')
            return {}

        # 得到要下载的时间部分
        date_list = get_date_list(date_scope)

        # 初始化字典,该数据字典以时间为KEY
        udp_data_dict = {}
        for date in date_list:
            udp_data_dict[str(date)[:10]] = {}

        # 下载店铺UDP数据
        if self.__download_nationwide_days(field_list = shop_udp_field_dict.get(Const.SUBWAY_SHOP_FIELD_TYPE[0], []), udp_data_dict = udp_data_dict, date_scope = date_scope, tapi = tapi) and \
           self.__download_nationwide_day(field_list = shop_udp_field_dict.get(Const.SUBWAY_SHOP_FIELD_TYPE[1], []), udp_data_dict = udp_data_dict, date_list = date_list, tapi = tapi) and \
           self.__download_allrange_days(field_list = shop_udp_field_dict.get(Const.SUBWAY_SHOP_FIELD_TYPE[2], []), udp_data_dict = udp_data_dict , date_list = date_list, tapi = tapi) and \
           self.__download_allrange_areas(field_list = shop_udp_field_dict.get(Const.SUBWAY_SHOP_FIELD_TYPE[3], []), udp_data_dict = udp_data_dict, tapi = tapi):
            return udp_data_dict
        return {}

    def __download_udp_by_itemids(self, udp_field_type_dict, shop_id, item_id_dict, date_scope = (), tapi = None):
        """
            通过商品id列表逐一下载多个商品UDP数据
            该接口需要的是宝贝id列表
        """
        for item_id, date_scope in item_id_dict.items():
            try :
                # 获取到单个宝贝得到的下载数据
                self.__download_udp_by_itemid(udp_field_type_dict = udp_field_type_dict, shop_id = shop_id, item_id = item_id, date_scope = date_scope, tapi = tapi)
            except Exception:
                continue

    def __download_udp_by_itemid(self, udp_field_type_dict, shop_id, item_id, date_scope = (), tapi = None):
        """
            通过商品id下载单个商品UDP数据
            该接口要求：调用时应指定宝贝id
            参数要求：
            udp_field_type_dict：
                                UDP下载字段分类字典，可以通过ShopUdp.__get_item_udp_fields()方法获取
            date_scope:
                                1.date_scope[1] >= date_scope[0]
                                2.time_scope[1]不能大于等于当天时间
            item_id:
                                                必须是该店铺的宝贝
            tapi:
                                                必须有效，程序中没有判定

            返回结果:
                                                成功或失败(boolean)

        """
        # 得到宝贝的下载结果
        udp_item_dict = self.__download_item_udp(udp_field_type_dict = udp_field_type_dict, item_id = item_id, date_scope = date_scope , tapi = tapi)
        # 转换成用于存储的数据结构
        item_udp_list = self.__transfer_save_list(udp_item_dict, Const.SUBWAY_UDP_ITEM_MAPPING)
        # 存储单个宝贝的UDP数据
        if self.__save_item_udp(shop_id, item_id, item_udp_list):
            log.info('download UDP item is OK, shop_id=%s, item_id=%s' % (shop_id, item_id))
        else :
            log.info('download UDP item is error, shop_id=%s, item_id=%s' % (shop_id, item_id))

    def __download_item_udp(self, udp_field_type_dict, item_id, date_scope = () , tapi = None):
        # 得到要下载的时间部分
        date_list = get_date_list(date_scope)
        # 初始化单个宝贝UDP数据字典，以时间为KEY
        udp_item_dict = {}
        for date in date_list:
            udp_item_dict[str(date)[:10]] = {}

        # 下载支持source参数字段的数据，支持的数据来源参数字段数据需要逐天下载
        if self.__download_support_source(field_list = udp_field_type_dict.get(Const.SUBWAY_ITEM_FIELD_TYPE[0], []), udp_item_dict = udp_item_dict, item_id = item_id, tapi = tapi) and \
           self.__download_unsupport_source(field_list = udp_field_type_dict.get(Const.SUBWAY_ITEM_FIELD_TYPE[1], []), time_tuple = date_scope, udp_item_dict = udp_item_dict, item_id = item_id, tapi = tapi):
            return udp_item_dict
        return {}

    def __save_shop_udp(self, udp_save_list, shop_id):
        """
            保存店铺UDP数据到数据库中
        """
        if not udp_save_list:
            return False

        shop_id = int(shop_id)
        try:
            account = account_coll.find_one({'_id':shop_id}, {'udp_list':1})
            if not account:
                return False
            udp_list = account.get('udp_list', [])
            if udp_list:
                # 如果数据存在，则判定是属于更新数据了，则先进行删除操作，而后插入数据
                time = udp_save_list[0]['date']
                # 删除已存在的数据
                account_coll.update({'_id':shop_id}, {'$pull':{'udp_list':{'date':{'$gte':time}}}})
                # 更新所有新数据
                account_coll.update({'_id':shop_id}, {'$pushAll':{'udp_list':udp_save_list}})
            else:
                # 如果数据不存在，则判定是第一次创建数据，直接进行更新操作
                account_coll.update({'_id':shop_id}, {'$set':{'udp_list':udp_save_list}})
            return True
        except Exception, e:
            log.exception('save shop udp error! shop_id=%s, e=%s' % (shop_id, e))
        return False

    def __save_item_udp(self, shop_id, item_id, udp_save_list):
        """
            保存宝贝UDP数据到数据库中
        """
        if not udp_save_list:
            return False

        item_id = int(item_id)
        try:
            udp_list = item_coll.find_one({'shop_id':shop_id, '_id':item_id}, {'udp_list':1}).get('udp_list', None)
            if udp_list:
                # 如果数据存在，则判定是属于更新数据了，则先进行删除操作，而后插入数据
                time = udp_save_list[0]['date']
                # 删除已存在的数据
                item_coll.update({'shop_id':shop_id, '_id':item_id}, {'$pull':{'udp_list':{'date':{'$gte':time}}}})
                # 更新所有新数据
                item_coll.update({'shop_id':shop_id, '_id':item_id}, {'$pushAll':{'udp_list':udp_save_list}})
            else:
                # 如果数据不存在，则判定是第一次创建数据，直接进行更新操作
                item_coll.update({'shop_id':shop_id, '_id':item_id}, {'$set':{'udp_list':udp_save_list}})
        except Exception, e:
            log.exception('save items udp error! shop_id=%s, item_id=%s, e=%s' % (shop_id, item_id, e))
            return False
        return True

    def __sync_shop_udp(self, shop_id, udp_fields, date_scope, tapi = None):
        """
            同步udp数据到数据库接口
            接口要求：
            date_scope 要求 date_scope[1] >= date_scope[0]
                                                要求time_scope[1]不能大于等于当天时间
            udp_fields 要求符合正确的JAPI UDP接口字段，保证字段的正确性
                                                要求字段是经过去重操作的
            返回参数：
                            成功/失败(booealn)
        """
        # 获取下载后的数据库数据
        udp_save_list = self.__get_shop_udp(udp_fields = udp_fields, date_scope = date_scope, tapi = tapi)
        # 存储下载后数据到数据库中
        result = self.__save_shop_udp(udp_save_list = udp_save_list, shop_id = shop_id)
        return result

    def __sync_items_udp(self, udp_fields, shop_id, item_id_dict, date_scope = (), tapi = None):
        """
            同步多个宝贝udp数据到数据库接口
            接口要求：
            date_scope 要求 date_scope[1] >= date_scope[0]
                                                要求time_scope[1]不能大于等于当天时间
            udp_fields 要求符合正确的JAPI UDP接口字段，保证字段的正确性
                                                要求字段是经过去重操作的
            item_id_list:
                                                该店铺的宝贝id列表
            返回参数：
                            成功/失败(boolean)
        """
        # 获取UDP分类字段字典
        udp_field_type_dict = self.__get_item_udp_fields(udp_fields)

        # 检查字典中是否存在我们所需要的数据
        if not(udp_field_type_dict.has_key(Const.SUBWAY_ITEM_FIELD_TYPE[0]) or udp_field_type_dict.has_key(Const.SUBWAY_ITEM_FIELD_TYPE[1])):
            log.info('the item_udp_dic is not exists fields, check date error!')
            return False

        # 下载宝贝的UDP数据
        self.__download_udp_by_itemids(udp_field_type_dict = udp_field_type_dict, shop_id = shop_id, item_id_dict = item_id_dict, date_scope = date_scope, tapi = tapi)

    def __sync_item_udp(self, udp_fields, shop_id, item_id, date_scope = () , tapi = None):
        """
            同步单个宝贝udp数据到数据库接口
            接口要求：
            date_scope 要求 date_scope[1] >= date_scope[0]
                                                要求time_scope[1]不能大于等于当天时间
            udp_fields 要求符合正确的JAPI UDP接口字段，保证字段的正确性
                                                要求字段是经过去重操作的
            item_id_list:
                                                该店铺的宝贝id列表
            返回参数：
                            成功/失败(boolean)
        """
        # 获取UDP分类字段字典
        udp_field_type_dict = self.__get_item_udp_fields(udp_fields)

        # 检查字典中是否存在我们所需要的数据
        if not(udp_field_type_dict.has_key(Const.SUBWAY_ITEM_FIELD_TYPE[0]) or udp_field_type_dict.has_key(Const.SUBWAY_ITEM_FIELD_TYPE[1])):
            log.info('the item_udp_dic is not exists fields, check date error!')
            return False

        # 下载宝贝的UDP数据
        return self.__download_udp_by_itemid(udp_field_type_dict = udp_field_type_dict, shop_id = shop_id, item_id = item_id, date_scope = date_scope, tapi = tapi)

    def __transfer_save_list(self, data_dict, mapping_dict):
        """
            转换成用于存储的列表格式
        """
        if not data_dict:
            return []

        # 改变存储列表格式
        udp_list = []
        for date in data_dict:
            temp_dict = {}
            for attr in data_dict[date]:
                if attr in mapping_dict:
                    temp_dict[mapping_dict[attr][0]] = transfer_type(data_dict[date][attr], mapping_dict[attr])
            temp_dict['date'] = datetime.datetime.strptime(date, '%Y-%m-%d')
            udp_list.append(temp_dict)
        # 对udp数据按日期进行排序
        udp_list.sort(cmp = lambda x, y:cmp(x['date'], y['date']))
        return udp_list
