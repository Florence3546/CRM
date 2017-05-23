# coding=UTF-8
import requests, re
from pyquery import PyQuery as pq
from urlparse import urlparse, parse_qsl

from django.http import HttpResponse
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.kwslt.keyword_selector import KeywordSelector, SelectKeywordPackage
from apps.subway.models_item import Item
from apps.common.cachekey import CacheKey
from apps.common.utils.utils_cacheadpter import CacheAdpter
from apps.kwslt.models_cat import Cat
from apps.web.models import  TrialUser

def route_ajax(request):
    '''ajax路由函数，返回数据务必返回字典的格式'''
    function_name = request.POST.get('function', '')
    call_back = request.GET.get('callback')
    try:
        if function_name and globals().get(function_name, ''):
            data = globals()[function_name](request = request)
        else:
            log.exception("route_ajax: function_name Does not exist")
            data = {'error': 'function_name Does not exist'}
    except Exception, e:
        log.exception("route_ajax error, e=%s ,request_data=%s" %
                      (e, request.POST))
    return HttpResponse('%s(%s)' % (call_back, json.dumps(data)))

def select_keyword_order(request):
    def get_title(html, shop_type):
        tt = html.find('title')[-1].text.lower()
        split_index = tt.rfind('-')
        title = tt[:split_index]
        if u'天猫' in tt or 'tmall' in tt:
            st = shop_type[u'tmall.com天猫']
        elif u'淘宝网' in tt:
            st = shop_type[u'淘宝网']
        else:
            st = shop_type[tt[split_index + 1:]]
        return title, st

    def get_price_cat_id(html):
        if st:
            select_content = 'ul#J_AttrUL li'
            cat_content = 'script'
            cat_id, price = 0, 0
            for rr in html.find(cat_content):
                content = rr.text or ''
                if 'categoryId' in content and not cat_id:
                    start_index = content.find('categoryId') + len('categoryId')
                    try:
                        cat_id = int(content[start_index + 1 :content.find(',', start_index)])
                    except :
                        pass
                for price_str in ['price', 'defaultItemPrice']:
                    if (price_str in content) and not price:
                        start_index = content.find(price_str) + len(price_str)
                        try:
                            price = float(content[start_index + 3 :content.find(',', start_index) - 1])
                        except :
                            continue
                if cat_id and price:
                    break

        else:
            select_content = 'ul.attributes-list li'
            cat_content = 'div#detail-recommend-viewed'
            cat_id = int(html.find(cat_content)[-1].attrib.get('data-catid'))
            price = html.find('em.tb-rmb-num')[-1].text
            if '-' in price:
                try:
                    price = float(price.split('-')[0])
                except Exception, e:
                    log.error("float price error and the error is = %s and url is = %s" % (e, item_url))
                    price = 0
        return cat_id, price, select_content

    def get_shop_args(result_select, st, html):
        attr_list, element_list, property_dict = [], [], {}
        if not result_select:
            if not st:
                rr = html.find("script")
                for r in rr:
                    content = r.text or ''
                    if 'g_config.spuStandardInfo' in content:
#                                 start_index = content.find('g_config.spuStandardInfo')
                        json_list, r_dict = [], {}
                        for kw in content[content.find('{', content.find('g_config.spuStandardInfo')):content.rfind('}') + 1].split(';'):
                            if 'spuStandardInfoUnits' in kw :
                                json_list.append(kw)
                        if json_list:
                            r_dict = json_list[0]
                        for key in r_dict:
                            value = r_dict[key]
                            if value:
                                for vv in value:
                                    for v in vv['spuStandardInfoUnits']:
                                        key = v['propertyName']
                                        value = v['valueName']
                                        attr_list.append(key + ':' + value)
                                        element_list.append(value)
                                        property_dict[key] = value
                            break
                        break
        for li in result_select:
            value = li.text
            value = value.lower()
            attr_list.append(value)
            em_list = []
            for split_sign in split_sign_list:
                if split_sign in value:
                    em_list = value.split(split_sign)
            has_split = False
            if em_list:
                em = em_list[-1]
            property_dict[em_list[0]] = em
            for sl in elem_split_list:
                if sl in em:
                    element_list.extend(em.split(sl)[1:])
                    has_split = True
            if not has_split:
                element_list.append(em)
        return attr_list, element_list, property_dict

    def get_parent_id(cat_id):
        parent_cat_ids = Cat.get_parent_cids(cat_id)
        if not parent_cat_ids:
            parent_cat_id = 0
        else:
            parent_cat_id = parent_cat_ids[-1]
        return parent_cat_id

    def get_pic_url(html):
        pic_url = html.find('img#J_ImgBooth')[-1].attrib.get('data-src')
        if not pic_url:
            pic_url = html.find('img#J_ImgBooth')[-1].attrib.get('src')
        return pic_url

    def get_tmall_role_args(html, attr_list, element_list, property_dict):
        for tr in html.find('div#J_Attrs table tbody tr'):
            td = tr.find('td')
            if td is not None:
                key = tr.find('th').text
                value = td.text
                attr_list.append(key + ':' + value)
                element_list.append(value)
                property_dict[key] = value

        return attr_list, element_list, property_dict

    def get_user_nick(html, st):
        if st:
            return html.find('div#shopExtra div.slogo a strong').text()
        else:
            nick_text = html.find('script').text()
            nick_start_index = nick_text.find('shopName')
            nick_start_index = nick_text.find(':', nick_text.find('sellerNick')) + 1
            nick_end_index = nick_text.find(',', nick_start_index)
            nick = nick_text[nick_start_index:nick_end_index]
            nick = nick.replace("'", '').strip()
            return nick

    shop_type = {u'淘宝网':0, u'tmall.com天猫':1}
    elem_split_list = [u' ', u'\xa0', u'/']

    errorMsg, data = '', {}
    try:
        item_url = request.POST.get('item_url')
        item_id = int(dict(parse_qsl(urlparse(item_url).query)).get('id', 0))
        select_type = request.POST.get('select_type') or ''
        if not item_id:
            errorMsg = "请确认该宝贝是否已经下架！"
        else:
            psuser_id = request.session.get('psuser_id')
            cachekey = CacheKey.SUBWAY_ITEM_DETAIL % item_id
            item_dict = CacheAdpter.get(cachekey, 'web', {})
            if not item_dict:
                try:
                    r = requests.get(item_url)
                except Exception, e:
                    log.error('crawl item page failed and the error =%s' % e)
                    return {'errMsg':'获取用户数据失败，请重新发送请求！', 'data':data}
                result = pq(r.text)
                title , st = get_title(result, shop_type)
                split_sign_list = [u': ', u':', u'\uff1a']
                cat_id, price, select_content = get_price_cat_id(result)
                result_select = result.find(select_content)
                attr_list, element_list, property_dict = get_shop_args(result_select, st, result)
                if st:
                    attr_list, element_list, property_dict = get_tmall_role_args(result, attr_list, element_list, property_dict)
                cat_path, _ = Cat.get_cat_path(cat_id_list = [cat_id], last_name = ' ').get(str(cat_id), ['未获取到值', ''])
                parent_cat_id = get_parent_id(cat_id)
                pic_url = get_pic_url(result)
                nick = get_user_nick(result, st)
                item_dict = {
                           'item_id':item_id,
                           'nick':nick,
                           'pic_url' :'https:' + pic_url,
                           'title':title,
                           'cat_id':cat_id,
                           'parent_cat_id':parent_cat_id,
                           'item_price':price,
                           'property_dict':property_dict,
                           'cat_path':cat_path,
                           'property_list':attr_list
                           }
                CacheAdpter.set(cachekey, item_dict, 'web')
            if not psuser_id: # 公司内部员工不受访问次数限制
                user = request.user
                if user.is_authenticated():
                    if user.select_count < 100:
                        user.select_count += 1
                        user.save()
                    else:
                        return {'errMsg':"为防止恶意调用，每天最多使用100次，请明天再用！", 'data':data}
                else:
                    nick = item_dict.get('nick', '')
                    if not nick:
                        return {'errMsg':'请确认宝贝链接是否正确！', 'data':{}}
                    tu, _ = TrialUser.objects.get_or_create(trial_nick = nick, defaults = {'login_count':0})
                    if tu.login_count < 20:
                        tu.login_count += 1
                        tu.save()
                    else:
                        return {'errMsg':"您已使用20次，购买开车精灵可继续使用！", 'data':data}
            item = Item.get_item_dict_2_order(item_dict)
            item._property_dict = {key:[value.replace(u'\xa0', '')] for key, value in item_dict.get('property_dict', {}).items()}
            candidate_keyword_list, keyword_list = [], []
            mode = request.POST.get('mode') or 'precise'
            item.mode = mode
            item_dict['elem_dict'] = {'prdtword_list':item.get_label_dict.get('P', []), 'dcrtword_list':[kw for kw in (item.get_label_dict.get('S', []) + item.get_label_dict.get('H', []) + item.get_label_dict.get('D', [])) if len(kw) > 1]}
            if select_type == 'quick':
                candidate_keyword_list = KeywordSelector.get_quick_select_words(item, None, mode)
                okay_count, temp_keyword_list, filter_field_list = SelectKeywordPackage.recommand_by_system(221, candidate_keyword_list)
                keyword_list = KeywordSelector.get_all_package_keyword(candidate_keyword_list, temp_keyword_list)
            else:
                item_dict['elem_dict'] = {'prdtword_list':item.get_label_dict.get('P', []), 'dcrtword_list':[kw for kw in (item.get_label_dict.get('S', []) + item.get_label_dict.get('H', []) + item.get_label_dict.get('D', [])) if len(kw) > 1]}
                word_filter = request.POST.get('word_filter', '') or ''
                if word_filter:
                    select_arg = word_filter.strip().lower()
                    word_match = re.match(ur'^[\u4e00-\u9fa5\s,，a-zA-Z0-9]+$', select_arg)
                    if not word_match:
                        return {'errMsg':'核心词不能为空，且只能包含中文、字母、数字、空格、中英文逗号!', 'data':{}}
                    candidate_keyword_list = KeywordSelector.get_precise_select_words(item, None, select_arg)
                    okay_count, temp_keyword_list, filter_field_list = SelectKeywordPackage.recommand_by_system(221, candidate_keyword_list)
                    keyword_list = KeywordSelector.get_all_package_keyword(candidate_keyword_list, temp_keyword_list)
                    return {'errMsg':errorMsg, 'data':{
                                                       'okay_count':okay_count,
                                                       'filter_field_list':filter_field_list,
                                                       'keyword_list':keyword_list
                                 }}
                else:
                    return {'errMsg':errorMsg, 'data':{
                                                       'item_info':{
                                                                    'nick':item_dict['nick'],
                                                                    'item_id':item_id,
                                                                    'title':item.title,
                                                                    'pic_url':item_dict['pic_url'],
                                                                    'cat_id':item_dict['cat_id'],
                                                                    'parent_cat_id':item_dict['parent_cat_id'],
                                                                    'cat_path':item_dict['cat_path'],
                                                                    'item_price':item_dict['item_price'],
                                                                    'elemword_dict':item_dict['elem_dict'],
                                                                    'property_list':item_dict['property_list'],
                                                                    'item_url':item_url
                                                                    }
                                 }}

        return {'errMsg':errorMsg, 'data':{
                                           'item_info':{
                                                        'nick':item_dict['nick'],
                                                        'item_id':item_id,
                                                        'title':item.title,
                                                        'pic_url':item_dict['pic_url'],
                                                        'cat_id':item_dict['cat_id'],
                                                        'parent_cat_id':item_dict['parent_cat_id'],
                                                        'cat_path':item_dict['cat_path'],
                                                        'item_price':item_dict['item_price'],
                                                        'elemword_dict':item_dict['elem_dict'],
                                                        'property_list':item_dict['property_list'],
                                                        'item_url':item_url
                                                        },
                                           'okay_count':okay_count,
                                           'filter_field_list':filter_field_list,
                                           'keyword_list':keyword_list
                                 }}
    except Exception, e:
        log.error(e)
        return {'errMsg':'请确认宝贝链接是否正确！', 'data':{}}

def mobile_package(request):
    """
    .获取关键词的移动数据
    """
    keyword_list , errorMsg = [], ''
    word_list = json.loads(request.POST.get('word_list', '[]'))
    tmp_list = SelectKeywordPackage.mobile_package(word_list)
    okay_count, temp_keyword_list, filter_field_list = SelectKeywordPackage.recommand_by_system(200, tmp_list)
    for kw in temp_keyword_list:
        tmp_kw = [kw.word, kw.cat_cpc or 30, kw.cat_pv, kw.cat_click, kw.cat_ctr, kw.cat_competition, kw.keyword_score, kw.new_price or 30, kw.coverage, kw.is_delete, 0, []]
        tmp_kw[10] = getattr(kw, 'is_ok', 0)
        keyword_list.append(tmp_kw)
    data = {
      'keyword_list':sorted(keyword_list, key = lambda x:x[3], reverse = True)[:200],
      'okay_count':okay_count,
      'filter_field_list':filter_field_list,
      'select_type':'',
      }
    return {'errMsg':errorMsg, 'data':data}



