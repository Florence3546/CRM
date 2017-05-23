# coding=UTF-8
import datetime
from apps.common.utils.utils_collection import genr_sublist
from apilib import tsapi
from apilib.error import TopError
from apps.common.utils.utils_log import log
from apps.common.biz_utils.utils_dictwrapper import DictWrapper
from apilib.app import QNApp



"""
.词库所有的taobao api方法
"""

def get_catsworddata(cat_id, word_list, start_date, end_date): # TODO 需要测试传入word_str的最大长度  起始时间和终止时间的时间间距，isp错误 连接超时
    """
    获取关键词在类目下的数据
    传入参数：
    cat_id：类目id str
    bidword_list：以^^分割的字符串，默认最长为200
    start_date:起始时间
    end_date:终止时间
    taobao返回值：
    impression:展现量
    click:点击量
    cost：花费，单位 分
    directtransaction：直接成交金额
    indirecttransaction：间接成交金额
    directtransactionshipping：直接成交笔数
    indirecttransactionshipping：间接成交笔数
    favitemtotal：宝贝收藏数
    favshoptotal：店铺收藏数
    transactionshippingtotal：总的成交笔数
    transactiontotal：总的成交金额
    favtotal：总的收藏总数，包括宝贝收藏和店铺收藏
    competition：竞争度
    ctr：点击率
    roi：投入产出比
    cpc：点击花费
    coverage：点击转化率
    cat_id：类目id
    cat_name:类目名称
    bidword：关键词

    函数返回值：
    {
        ‘连衣裙’：{‘pv’:1,‘click’:1,‘cpc’:1,‘ctr’:1,‘competition’:1,}
        ...
        ..
        .
    }
    """
    cat_word_data_dict = {}
    last_update_time = datetime.datetime.now()
    for temp_list in genr_sublist(word_list, 100):
        try:
            tobj = tsapi.simba_insight_catsworddata_get(cat_id = cat_id, bidword_list = ','.join(temp_list), start_date = start_date, end_date = end_date)
            if hasattr(tobj, "catword_data_list"):
                catword_data_list = tobj.catword_data_list
                if hasattr(catword_data_list, "insight_word_data_under_cat_d_t_o"):
                    insight_word_data_under_cat_d_t_o = catword_data_list.insight_word_data_under_cat_d_t_o
                    for cat_data in insight_word_data_under_cat_d_t_o:
                        cpc = getattr(cat_data, "cpc", cat_data.click > 0 and (cat_data.cost / cat_data.click) or 0)
                        try:
                            cat_word_data_dict[cat_data.bidword] = {'pv':cat_data.impression, 'click':cat_data.click, 'cpc':cpc, 'ctr':cat_data.ctr, 'competition':cat_data.competition, 'last_update_time':last_update_time, 'word':cat_data.bidword}
                        except Exception, e:
                            log.error("get the top error = %s" % e)
                            continue
        except TopError, e:
            log.error('get simba_insight_catstopwordnew_get error, e=%s' % (e))
    return cat_word_data_dict

def get_relatewords_new(word_list, number = 10): # TODO 调用长度是一个非常严重的问题
    """
    获取给定词的若干相关词，返回结果中越相关的权重越大，排在越前面，根据number参数对返回结果进行截断。
    以词滚词，扩充词库
    传入参数:
    bidword_list:以逗号分割的关键词字符串
    number：返回个数
    返回值：
    related_word：相关关键词
    weight:相关度
    函数返回值：
    [
        连衣裙，
        连衣裙夏，
        ...
        ..
        .
    ]
    """
    relate_list = []
    for temp_list in genr_sublist(word_list, 100):
        try:
            tobj = tsapi.simba_insight_relatedwords_get(bidword_list = ','.join(temp_list), number = number)
            if hasattr(tobj, "related_words_result_list"):
                related_words_result_list = tobj.related_words_result_list
                if hasattr(related_words_result_list, "insight_related_words"):
                    insight_related_words = related_words_result_list.insight_related_words
                    for relate_word in insight_related_words:
                        if hasattr(relate_word, "related_word_items_list"):
                            related_word_items_list = relate_word.related_word_items_list
                            if hasattr(related_word_items_list, "insight_related_word"):
                                insight_related_word = related_word_items_list.insight_related_word
                                for word in insight_related_word:
                                    relate_list.append(word.related_word.replace('\t', '').decode('utf8'))
        except TopError, e:
            log.error('get simba_insight_relatedwords_get error, e=%s' % (e))
    return relate_list

def get_words_gdata(word_list, time_scope = None):
    """
    获取关键词的详细数据，全网数据接口
    传入参数:
    bidword_list:以逗号分割的字符串列表，如“连衣裙,红色连衣裙...”
    start_date：起始时间
    end_date：终止时间
    返回值：
    impression：展现量
    click：点击量
    cost：花费，单位 分
    directtransaction：直接成交金额
    indirecttransaction：间接成交金额
    directtransactionshipping：直接成交笔数
    indirecttransactionshipping：间接成交笔数
    favitemtotal：宝贝收藏数
    favshoptotal：店铺收藏数
    transactionshippingtotal：总的成交笔数 1
    transactiontotal：成交总金额
    favtotal：总的收藏数，包括宝贝收藏数以及店铺收藏数 1
    competition：竞争度
    ctr：点击率
    cpc：平均点击花费
    roi：投资回报率 1 string
    coverage：点击转化率 1 string
    bidword：关键词
    函数返回值：
    {
    '连衣裙'：{'pv':1, 'click':1, 'cpc':1, 'ctr':1, 'competition':1, 'last_update_time':1}
    ...
    ..
    .
    }
    """
    if not time_scope: # 不给时间区间，就默认采用昨天的数据
        yst_date = '%s' % (datetime.date.today() - datetime.timedelta(days = 1))
        time_scope = (yst_date, yst_date)

    word_dict = {}
    for temp_list in genr_sublist(word_list, 100):
        try:
            tobj = tsapi.simba_insight_wordsdata_get(bidword_list = ','.join(temp_list), start_date = time_scope[0], end_date = time_scope[1])
            if hasattr(tobj, "word_data_list"):
                word_data_list = tobj.word_data_list
                if hasattr(word_data_list, "insight_word_data_d_t_o"):
                    insight_word_data_d_t_o = word_data_list.insight_word_data_d_t_o
                    for word_data in insight_word_data_d_t_o:
                        cpc = int(float(getattr(word_data, "cpc", word_data.click > 0 and word_data.cost / word_data.click or 0)))
                        ctr = float(getattr(word_data, "ctr", 0))
                        competition = int(float(getattr(word_data, "competition", 0)))
                        roi = float(getattr(word_data, "roi", 0))
                        coverage = float(getattr(word_data, "coverage", 0))
                        favtotal = int(float(getattr(word_data, "favtotal", 0)))
                        transactionshippingtotal = int(float(getattr(word_data, "transactionshippingtotal", 0)))
                        word_dict[word_data.bidword] = DictWrapper({'pv':int(word_data.impression), 'click':int(word_data.click), 'avg_price':cpc, 'ctr':ctr, 'competition':competition, 'word':word_data.bidword, 'roi':roi, 'coverage':coverage, 'favtotal':favtotal, 'transactionshippingtotal':transactionshippingtotal })
        except TopError, e:
            if "API error response" in str(e):
                log.info("test error for :" + str(datetime.datetime.now()) + ',\t' + ','.join(temp_list))
            log.error('simba_insight_wordsdata_get TopError, e=%s' % (e))
    return word_dict

def get_cats_forecast_new(word_list):
    """
    根据传入的关键词获取该关键词适合的类目
    新的类目预测接口,传入参数为纯word以逗号隔开，淘宝没有提供传入字符串长度，所以默认长度为原有的200以内。
    淘宝返回值：
    cat_path_name：类目路径及名称
    bidword:关键词
    score：类目相关度
    cat_path_id：类目路径id
    当前返回值：
    {
    '连衣裙':[1,2,3,4],
    ...
    ..
    }
    """
    cat_forecast_dict = {}
    for temp_list in genr_sublist(word_list, 100):
        try:
            tobj = tsapi.simba_insight_catsforecastnew_get(bidword_list = ",".join(temp_list))
            if hasattr(tobj, "category_forecast_list"):
                category_forecast_list = tobj.category_forecast_list
                if hasattr(category_forecast_list, "insight_category_forcast_d_t_o"):
                    insight_category_forcast_d_t_o = category_forecast_list.insight_category_forcast_d_t_o
                    for catforecast in insight_category_forcast_d_t_o:
                        cat_path_id = catforecast.cat_path_id
                        if cat_path_id == "":
                            continue
                        cat_id = int(catforecast.cat_path_id.split(' ')[-1])
                        word = catforecast.bidword
                        if catforecast.bidword in cat_forecast_dict:
                            cat_forecast_dict[word].append(cat_id)
                        else:
                            cat_forecast_dict[word] = [cat_id]
        except TopError, e:
            log.error('get simba_insight_catsforecastnew_get error, e=%s' % (e))
            continue
    return cat_forecast_dict


def get_cat_top_word(cat_id, start_date, end_date, dimension = 'click', page_size = 20): # TODO 远程链接超时isp错误
    """
    按照某个维度，查询某个类目下最热门的词，维度有点击，展现，花费，点击率等，具体可以按哪些字段进行排序，参考参数说明，比如选择了impression，则返回该类目下展现量最高那几个词。
    传入参数：
    cat_id:类目id   str
    start_date:起始时间  str yyyy-MM-dd
    end_time:终止时间    str  yyy-MM-dd
    dimension:查询维度   str
        {
            'impression':展现
            ‘click’：点击
            ‘cost’：花费
            ‘ctr’:点击率
            'cpc':点击花费
            ‘coverage’：点击转化率
            ‘transactiontotal’：成交总额
            'transactionshippingtotal':总的成交笔数
            ‘favtotal’：收藏总数
            'roi'：投入产出比
        }
    page_size：返回前多少条数据，最大为20，最小为1
    返回值：

    """
    result_list = []
    try:
        tobj = tsapi.simba_insight_catstopwordnew_get(cat_id = cat_id, start_date = start_date, end_date = end_date, dimension = dimension, page_size = page_size)
        if hasattr(tobj, 'topword_data_list'):
            topword_data_list = tobj.topword_data_list
            if hasattr(topword_data_list, 'insight_word_data_under_cat_d_t_o'):
                insight_word_data_under_cat_d_t_o = topword_data_list.insight_word_data_under_cat_d_t_o
                for word_data in insight_word_data_under_cat_d_t_o:
                    result_list.append(word_data.bidword)
    except TopError, e:
        log.error('get simba_insight_catstopwordnew_get error, e=%s' % (e))
    return result_list

def get_wordsarea_data(word, start_date, end_date): # TODO最后一个参数不知道有什么作用
    """
    获取关键词按地域细分的详细数据，目前地域只能细化到省级别，返回的结果中包括市，是为了方便以后扩展，目前结果中市的值等于省。
    出入参数：
    bidword：关键词
    start_date：起始时间
    end_date：终止时间
    返回值：
    impression：展现量
    click：点击量
    cost：花费，单位 分
    directtransaction：直接成交金额
    indirecttransaction：间接成交金额
    directtransactionshipping：直接成交笔数
    indirecttransactionshipping：间接成交笔数
    favitemtotal：宝贝收藏数
    favshoptotal：店铺收藏数
    transactionshippingtotal：总的成交笔数
    transactiontotal：成交总金额
    favtotal：总的收藏树，包括宝贝收藏数以及店铺收藏数
    competition：竞争度
    ctr：点击率
    cpc：平均点击花费
    roi：投资回报率
    coverage：点击转化率
    bidword：关键词
    provincename：省名称
    cityname：市名称，暂时不支持市，这个接口为保留接口
    """
    province_word_dict = {}
    try:
        tobj = tsapi.simba_insight_wordsareadata_get(bidword = word, start_date = start_date, end_date = end_date)
        if hasattr(tobj, "word_areadata_list"):
            word_areadata_list = tobj.word_areadata_list
            if hasattr(word_areadata_list, "insight_words_area_distribute_data_d_t_o"):
                insight_words_area_distribute_data_d_t_o = word_areadata_list.insight_words_area_distribute_data_d_t_o
                for words_area in insight_words_area_distribute_data_d_t_o:
                    if hasattr(words_area, "provincename"): # TODO 需要确定不包含省的是什么数据 去掉不包含省的数据
                        province_word_dict[words_area.provincename] = words_area
    except TopError, e:
        log.error('get simba_insight_wordsareadata_get error, e=%s' % (e))
        return {}
    return province_word_dict

def get_word_price_data(bidword, start_date, end_date):
    """
    获取关键词按竞价区间进行细分的数据
    传入参数：
    bidword:关键词
    start_date：起始时间
    end_date：终止时间
    返回值：
    'bidword': 关键词
    'click': 点击量
    'competition':竞争度
    'cost': 花费 单位为分
    'coverage': 转化率
    'cpc': 点击花费
    'ctr': 点击率
    'directtransaction': 直接成交金额,
    'directtransactionshipping': 直接成交笔数
    'favitemtotal': 宝贝收藏数
    'favshoptotal': 店铺收藏数
    'favtotal': 总的收藏数
    'impression': 展现
    'indirecttransaction': 间接成交金额
    'indirecttransactionshipping': 间接成交笔数
    'price': 竞价区间
    'roi': 投资回报率
    'transactionshippingtotal': 总的成交笔数
    'transactiontotal': 总的成交金额
    函数返回值：
    {
        price1:{
        'bidword':1,
        'click': 1,
        'competition': 1,
        'cost': 1,
        'coverage': 1,
        'cpc': 1,
        'ctr': 2,
        'directtransaction': 1,
        'directtransactionshipping': 1,
        'favitemtotal': 1,
        'favshoptotal': 1,
        'favtotal': 1,
        'pv': 1,
        'indirecttransaction': 1,
        'indirecttransactionshipping':1,
        'price': 1,
        'roi': 1,
        'transactionshippingtotal': 1,
        'transactiontotal': 1
        }
        price2:{
            ...
            ..
            .
        }
        ...
        ..
        .

    }
    """
    word_price_date = {}
    try:
        tobj = tsapi.simba_insight_wordspricedata_get(bidword = bidword, start_date = start_date, end_date = end_date)
        if hasattr(tobj, "word_pricedata_list"):
            word_pricedata_list = tobj.word_pricedata_list
            if hasattr(word_pricedata_list, "insight_word_price_distribute_data_d_t_o"):
                insight_word_price_distribute_data_d_t_o = word_pricedata_list.insight_word_price_distribute_data_d_t_o
                for price_data in insight_word_price_distribute_data_d_t_o:
                    price = price_data.price
                    temp_dict = {
                                    'bidword':price_data.bidword,
                                    'click': price_data.click,
                                    'competition': price_data.competition,
                                    'cost': price_data.cost,
                                    'coverage': price_data.coverage,
                                    'cpc': price_data.cpc,
                                    'ctr': price_data.ctr,
                                    'directtransaction': price_data.directtransaction,
                                    'directtransactionshipping': price_data.directtransactionshipping,
                                    'favitemtotal': price_data.favitemtotal,
                                    'favshoptotal': price_data.favshoptotal,
                                    'favtotal': price_data.favtotal,
                                    'pv': price_data.impression,
                                    'indirecttransaction': price_data.indirecttransaction,
                                    'indirecttransactionshipping':price_data.indirecttransactionshipping,
                                    'price': price_data.price,
                                    'roi': price_data.roi,
                                    'transactionshippingtotal': price_data.transactionshippingtotal,
                                    'transactiontotal': price_data.transactiontotal
                                    }
                    if price in word_price_date:
                        word_price_date.append(temp_dict)
                    else:
                        word_price_date[price] = [temp_dict]
    except TopError, e:
        log.error('get simba_insight_wordspricedata_get error, e=%s' % (e))
        return {}
    return word_price_date

def get_word_subdata(word_list, start_date, end_date):
    """
    获取关键词按流量进行细分的数据，返回结果中network表示流量的来源，意义如下：1->PC站内，2->PC站外,4->无线站内 5->无线站外
    出入参数：
    bidword_list：以逗号分割的关键词列表
    start_date：起始时间
    end_date：终止时间
    返回值：
    impression: 展现量
    click：点击量
    cost： 花费，单位（分）
    directtransaction： 直接成交金额
    indirecttransaction：间接成交金额
    directtransactionshipping：直接成交笔数
    indirecttransactionshipping：间接成交笔数
    favitemtotal：宝贝搜藏数
    favshoptotal：店铺搜藏数
    transactionshippingtotal：总的成交笔数
    transactiontotal：成交总金额
    favtotal：总的收藏数，包括宝贝收藏和店铺收藏
    competition：竞争度
    ctr：点击率
    cpc：平均点击花费
    roi：投入产出比
    coverage：点击转化率
    bidword：关键词
    network：流量来源：1:PC站内，2：PC站外,4:无线站内 5：无线站外
    mechanism：投放机制:0:关键词推广 2：定向推广 3：通用定向
    函数返回值：
    {
        '连衣裙'：{
            "pv":1,
            "click":1,
            "cost":1,
            "directtransaction":1,
            "indirecttransaction":1,
            "directtransactionshipping":1,
            "indirecttransactionshipping":1,
            "favitemtotal":1,
            "favshoptotal":1,
            "transactionshippingtotal":1,
            "transactiontotal":1,
            "favtotal":1,
            "competition":1,
            "ctr":1,
            "cpc":1,
            "roi":1,
            "coverage":1,
            "network":1,
            "mechanism":1,
        },
        ‘红色连衣裙’:{
            ...
            },
        ...
        ..
        .
    }
    """
    word_sub_data_dict = {}
    for temp_list in genr_sublist(word_list, 100):
        try:
            tobj = tsapi.simba_insight_wordssubdata_get(bidword_list = ','.join(temp_list), start_date = start_date, end_date = end_date)
            if hasattr(tobj, "word_subdata_list"):
                word_subdata_list = tobj.word_subdata_list
                if hasattr(word_subdata_list, "insight_word_sub_data_d_t_o"):
                    insight_word_sub_data_d_t_o = word_subdata_list.insight_word_sub_data_d_t_o
                    for sub_data in insight_word_sub_data_d_t_o:
                        word = sub_data.bidword
                        temp_dict = sub_data.__dict__
                        if word in word_sub_data_dict:
                            word_sub_data_dict[word].append(temp_dict)
                        else:
                            word_sub_data_dict[word] = [temp_dict]
        except TopError , e :
            log.error('get simba_insight_wordssubdata_get error, e=%s' % (e))
            return {}
    return word_sub_data_dict

def get_tb_recommend_keywords(shop_id, adgroup_id):
    tapi = QNApp.get_tapi(shop_id = shop_id)
    # 取得淘宝推荐词
    try:
        top_obj = tapi.simba_keywords_recommend_get(adgroup_id = adgroup_id, page_no = 1, page_size = 200, order_by = 'relevance')
    except Exception, e:
        log.error("get_tb_recommand_keywords error=%s" % (e))
        return []

    word_list = []
    if top_obj and top_obj.recommend_words and top_obj.recommend_words.recommend_word_list:
        for rw in top_obj.recommend_words.recommend_word_list.recommend_word:
            word_list.append({'word': rw.word, 'pertinence': int(float(rw.pertinence))})

    return word_list