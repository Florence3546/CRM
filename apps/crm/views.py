# coding=UTF-8

from django.contrib.auth import logout as auth_logout
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

from dajax.core import Dajax
from apps.common.utils.utils_log import log
from apps.common.utils.utils_json import json
from apps.common.utils.utils_render import render_to_limited, render_to_error
from apps.common.biz_utils.utils_misc import get_credit_gif
from apps.subway.models import Adgroup, Item
from apps.router.models import User, ArticleUserSubscribe
from apps.ncrm.models import PSUser
from apps.engine.models import ShopMngTask

from apps.crm.forms import UserListForm
from apps.crm.utils import get_init_conditon
from apps.crm.service import CrmCacheServer
from apps.kwslt.models_cat import Cat


# 保留
def ps_auth(func):
    """装饰器，将没带指定参数的请求定向给login"""

    def _is_auth(request):
        if request.is_ajax():
            if request and request.session.get('psuser_id', '') :
                return True
            else:
                return False
        else:
            if request and request.session.get('psuser_id', '') :
                return True
            else:
                return False

    def _inner_check(request, *args, **kwargs):
        if _is_auth(request):
            return func(request, *args, **kwargs)
        else:
            redirect_url = reverse('login')
            if request.is_ajax():
                dajax = Dajax()
                dajax.script("alert('您尚未登录，即将跳转到登录页面！');")
                dajax.script("location.href='%s'" % redirect_url)
                return dajax
            else:
                return HttpResponseRedirect(redirect_url)

    return _inner_check

# 保留
def get_psuser(request):
    """根据请求获取对应的用户"""
    if not hasattr(request, '_psuser'):
        psuser_id = request.session.get('psuser_id', 0)
        try:
            if psuser_id == 0:
                raise ObjectDoesNotExist
            psuser = PSUser.objects.get(id = psuser_id)
        except ObjectDoesNotExist:
            psuser = None
        request._psuser = psuser
    return request._psuser

# 保留
@ps_auth
def test_select_words(request, template = 'test_select_words.html'):
    """CRM 新测试选词配置接口"""
    try:
        shop_id = int(request.POST['shop_id'])
        item_id = int(request.POST['item_id'])
        adg_id = int(request.POST['adg_id'])
        conf_name = str(request.POST['conf_name'])
        conf_desc = str(request.POST['conf_desc'])
        candidate_words = str(request.POST['candi_filter'])
        label_define = json.loads(request.POST['label_define_list'])
        select_conf_list = json.loads(request.POST['select_conf_list'])
        price_conf_list = json.loads(request.POST['price_conf_list'])
        delete_conf = json.loads(request.POST['delete_conf'])
    except Exception, e:
        log.error('get parameters error, e=%s' % (e))
        return render_to_error(request, msg = "系统获取参数失败，请重试！")
    result = {"shop_id":shop_id,
              "item_id":item_id,
              'adg_id':adg_id,
              "conf_name":conf_name,
              "conf_desc":conf_desc,
              "candidate_words":candidate_words,
              "label_define":label_define,
              "select_conf_list":select_conf_list,
              "price_conf_list":price_conf_list,
              "delete_conf":delete_conf
              }
    return render_to_response(template, result, context_instance = RequestContext(request))

# 保留
@ps_auth
def user_list(request, flag = ''):
    '''管理员界面，显示用户列表，先取当页数据，再循环当页数据'''

    refresh_user = False
    shop_id, user_name = "", ""
    page_no, page_size = 1, 400
    if flag:
        if 'ref' in flag: # /tpm/user_list/ref会触发重新获取权限码
            refresh_user = True
        elif flag.isdigit(): # /tpm/user_list/1234只查询一个店铺
            shop_id = flag
    if request.method == 'POST':
        user_list_form = UserListForm(data = request.POST)
        if user_list_form.is_valid():
            shop_id = user_list_form.cleaned_data['shop_id']
            user_name = user_list_form.cleaned_data['user_name']
            page_no = user_list_form.cleaned_data['page_no']
    else:
        user_list_form = UserListForm(initial = {'shop_id':shop_id, 'user_name':user_name, 'page_no':page_no, 'page_size':page_size})

    # 没有输入查询条件则默认为不查询
    if not shop_id and not user_name:
        return render_to_response('user_list.html', {'page_obj':None, 'search_list_form':user_list_form}, context_instance = RequestContext(request))

    # 开始查询并分页
    user_list = User.objects.filter(is_staff = False, shop_type__in = ['B', 'C']).order_by('-date_joined')
    if shop_id:
        user_list = user_list.filter(shop_id = shop_id)
    if user_name:
        user_name = user_name.replace(' ', '')
        if '*' in user_name: # 支持中间带*号的模糊查询
            index = user_name.find('*')
            start_name = user_name[:index]
            end_name = user_name[index + 1:].replace('*', '')
            user_list = user_list.filter(nick__istartswith = start_name, nick__iendswith = end_name)
        else:
            user_list = user_list.filter(nick__icontains = user_name)

    # 执行翻页
    try:
        paginator = Paginator(user_list, page_size)
        this_page = paginator.page(page_no)
    except (EmptyPage, InvalidPage):
        this_page = paginator.page(paginator.num_pages)

    # 根据shop_id以获取大任务信息
    result_shop_id_list = [int(user.shop_id) for user in this_page.object_list if user.shop_id]
    smt_list = ShopMngTask.objects.filter(shop_id__in = result_shop_id_list)
    task_dict = {smt.shop_id:smt.display_status() for smt in smt_list}

    # 为user_list添加其它显示属性
#     psuser_name = request.session['name']
    psuser_name = request.session['psuser_name']
    for user in this_page.object_list:
        if user.is_staff:
            continue

        # 设置页面显示属性
        user.backend_url_dict = user.get_backend_url(user_type = "staff", psuser_name = psuser_name)
        user.domain = user.get_subport()
        user.shop_status = task_dict.get(user.shop_id, 'Unknow')
        user.credit_gif = get_credit_gif(user.credit)
        user.subs_item_list = ArticleUserSubscribe.get_valid_item_list(user)
    return render_to_response('user_list.html', {'page_obj':this_page, 'search_list_form':user_list_form}, context_instance = RequestContext(request))

# 待定
@ps_auth
def category_list(request, template = "crm_category_list.html"):
    """类目管理列表"""
    return render_to_response(template, {}, context_instance = RequestContext(request))

# 保留
@ps_auth
def selection_word_manager(request, template = "crm_selectword_manager.html"):
    psuser = get_psuser(request)
    cat_id = request.GET.get('cat_id', 0)
    item_id = request.GET.get('item_id', 0)
    adgroup_id = request.GET.get('adgroup_id', 0)
    shop_id = request.GET.get('shop_id', 0)
    if not shop_id and not item_id and cat_id and not adgroup_id:
        try:
            cat_id = int(cat_id)
            item = Item.objects.filter(cat_id = cat_id)[0]
            adg_id = Adgroup.objects.only('adgroup_id').filter(item_id = item.item_id)[0].adgroup_id
        except IndexError, e:
            return render_to_error(request = request, msg = "该类目下没有任何宝贝")
        except Exception, e:
            log.exception("get item or convert type error, e=%s" % (e))
            return render_to_error(request = request, msg = "异常，请联系管理员")
    elif shop_id and not cat_id:
        if adgroup_id:
            try:
                item_id = int(item_id)
                shop_id = int(shop_id)
                adgroup = Adgroup.objects.get(shop_id = shop_id, adgroup_id = adgroup_id)
                item = Item.objects.get(shop_id = shop_id, item_id = adgroup.item_id)
                adg_id = adgroup_id
            except Exception, e:
                log.error("get item error! shop_id=%s, item_id=%s, e=%s" % (shop_id, item_id, e))
                return render_to_error(request = request, msg = "系统中无该宝贝，请联系管理员")
        elif item_id:
            try:
                item_id = int(item_id)
                shop_id = int(shop_id)
                item = Item.objects.get(shop_id = shop_id, item_id = item_id)
                adg_id = Adgroup.objects.only('adgroup_id').filter(item_id = item.item_id)[0].adgroup_id
            except Exception, e:
                log.error("get item error! shop_id=%s, item_id=%s, e=%s" % (shop_id, item_id, e))
                return render_to_error(request = request, msg = "系统中无该宝贝，请联系管理员")
        else:
            return render_to_error(request = request, msg = "异常，请联系管理员")
    else:
        return render_to_error(request = request, msg = "输入连接有误，请联系管理员")

    try:
        from apps.kwslt.models_selectconf import SelectConf
        conf_list = [select_conf.conf_name for select_conf in SelectConf.objects.only("conf_name").filter(conf_type__lte = 1)]
    except Exception, e:
        log.error("get select conf error, e=%s" % (e))
        return render_to_error(request = request, msg = "获取通用选词模板异常，请联系管理员")
    result = {"adg_id":adg_id, "item_id":item.item_id, "cat_id":item.cat_id, "username":psuser.name, "shop_id":item.shop_id, 'conf_list':conf_list}
    return render_to_response(template, result, context_instance = RequestContext(request))

# 保留
def crm_logout(request, template = 'crm_logout.html'):
    try:
        psuser = get_psuser(request)
        CrmCacheServer(psuser.id).clear_user_cache()
        auth_logout(request)
    except Exception, e:
        log.error('system exit is error , e=%s' % e)
    return render_to_response(template)

# 保留
@ps_auth
def crm_account(request, template = "crm_account.html"):
    psuser = get_psuser(request)
    server = CrmCacheServer(user_id = psuser.id)
    tree_path = request.GET.get('tree_path', "")

    curr_type = 0
    if request.method == 'POST':
        curr_page = 'account'
    else:
        _, curr_page = server.get_page_type(curr_type, 0, curr_type)

    base_info = server('base').get('base', {})
    base_info.update({'is_jumped':0, 'is_rpt':1})
    filter_condition = server.get_condition_cache(curr_page).pop(curr_page)

    top_cats_list, cond_type_list = get_init_conditon(cond_type = curr_type)
    result_dict = {
                           'top_cats_list':top_cats_list,
                           'cond_type_list':cond_type_list,
                           'base_condition':json.dumps(base_info),
                           'filter_condition':json.dumps(filter_condition),
                           'consult_id':base_info.get('consult_id', -1),
                           'perms':psuser.perms,
                           'ps_type':psuser.position,
                           'request_condition':dict(request.GET.items()),
                           "tree_path":tree_path
                        }
    return render_to_response(template, result_dict, \
                    context_instance = RequestContext(request))

# 保留
@ps_auth
def crm_campaign(request, template = "crm_campaign.html"):
    psuser = get_psuser(request)
    server = CrmCacheServer(user_id = psuser.id)

    curr_type = 1
    source_type = 1

    if request.method == 'POST':
        source_type = int(request.POST.get('source_type'))
        source_is_jump = int(request.POST.get('is_jump'))
        id_dict = json.loads(request.POST.get('id_dict'))
        source_page, curr_page = server.get_page_type(source_type, source_is_jump, curr_type)
        server.transfer_cache(source_page, curr_page, id_dict)
        is_jumped = 1
    else:
        source_page, curr_page = server.get_page_type(source_type, 0, curr_type)
        is_jumped = 0

    base_info = server('base').get('base', {})
    base_info.update({'is_jumped':is_jumped, 'is_rpt':1})
    filter_condition = server.get_condition_cache(curr_page).pop(curr_page)

    top_cats_list, cond_type_list = get_init_conditon(cond_type = curr_type)
    result_dict = {
                           'top_cats_list':top_cats_list,
                           'cond_type_list':cond_type_list,
                           'base_condition':json.dumps(base_info),
                           'filter_condition':json.dumps(filter_condition),
                           'consult_id':base_info.get('consult_id', -1),
                           'perms':psuser.perms,
                           'ps_type':psuser.position,
                           'source_type':source_type
                        }
    return render_to_response(template, result_dict, context_instance = RequestContext(request))

# 保留
@ps_auth
def crm_adgroup(request, template = "crm_adgroup.html"):
    psuser = get_psuser(request)
    server = CrmCacheServer(user_id = psuser.id)

    curr_type = 2
    source_type = 2

    if request.method == 'POST':
        source_type = int(request.POST.get('source_type'))
        source_is_jump = int(request.POST.get('is_jump'))
        id_dict = json.loads(request.POST.get('id_dict'))
        source_page, curr_page = server.get_page_type(source_type, source_is_jump, curr_type)
        server.transfer_cache(source_page, curr_page, id_dict)
        is_jumped = 1
    else:
        source_page, curr_page = server.get_page_type(source_type, 0, curr_type)
        is_jumped = 0

    base_info = server('base').get('base', {})
    base_info.update({'is_jumped':is_jumped, 'is_rpt':1})
    filter_condition = server.get_condition_cache(curr_page).pop(curr_page)

    top_cats_list, cond_type_list = get_init_conditon(cond_type = curr_type)
    result_dict = {
                           'top_cats_list':top_cats_list,
                           'cond_type_list':cond_type_list,
                           'base_condition':json.dumps(base_info),
                           'filter_condition':json.dumps(filter_condition),
                           'consult_id':base_info.get('consult_id', -1),
                           'perms':psuser.perms,
                           'ps_type':psuser.position,
                           'source_type':source_type
                        }
    return render_to_response(template, result_dict, context_instance = RequestContext(request))

# 保留
@ps_auth
def crm_keyword(request, template = "crm_keyword.html"):
    psuser = get_psuser(request)
    server = CrmCacheServer(user_id = psuser.id)

    curr_type = 3
    source_type = 3

    json_nosraech_data = {}
    if request.method == 'POST':
        source_type = int(request.POST.get('source_type'))
        source_is_jump = int(request.POST.get('is_jump'))
        id_dict = json.loads(request.POST.get('id_dict'))
        source_page, curr_page = server.get_page_type(source_type, source_is_jump, curr_type)
        server.transfer_cache(source_page, curr_page, id_dict)
        is_jumped = 1

        adgroup_list = id_dict.get('adgroup', [])
        if len(adgroup_list) == 1:
            adg_id = adgroup_list[0]
            try:
                adgroup = Adgroup.objects.get(adgroup_id = adg_id)
                # 封装定向推广数据
                json_nosraech_data = {
                                                        "impressions":adgroup.rpt_nosch.impressions,
                                                        "click":adgroup.rpt_nosch.click,
                                                        "ctr":format(adgroup.rpt_nosch.ctr, '.2f'),
                                                        "cost":format(adgroup.rpt_nosch.cost / 100.0, '.2f'),
                                                        "cpc":format(adgroup.rpt_nosch.cpc / 100.0, '.2f'),
                                                        "avgpos":adgroup.rpt_nosch.avgpos,
                                                        "favcount":adgroup.rpt_nosch.favcount,
                                                        "paycount":adgroup.rpt_nosch.paycount,
                                                        "pay":format(adgroup.rpt_nosch.pay / 100.0, '.2f'),
                                                        "conv":format(adgroup.rpt_nosch.conv, '.2f'),
                                                        "roi":format(adgroup.rpt_nosch.roi, '.2f'),
                                                        "favctr":adgroup.rpt_nosch.click and format(adgroup.rpt_nosch.favcount * 100.0 / adgroup.rpt_nosch.click, '.2f') or '0.00',
                                                        "favpay":adgroup.rpt_nosch.favcount and format(adgroup.rpt_nosch.cost / (adgroup.rpt_nosch.favcount * 100.0), '.2f') or '0.00',
                                                    }
            except Exception, e:
                log.error('get nosearch data error, adgroup_id=%s' % (adg_id))
    else:
        source_page, curr_page = server.get_page_type(source_type, 0, curr_type)
        is_jumped = 0

    base_info = server('base').get('base', {})
    base_info.update({'is_jumped':is_jumped, 'is_rpt':1})
    filter_condition = server.get_condition_cache(curr_page).pop(curr_page)

    top_cats_list, cond_type_list = get_init_conditon(cond_type = curr_type)
    result_dict = {
                           'top_cats_list':top_cats_list,
                           'cond_type_list':cond_type_list,
                           'base_condition':json.dumps(base_info),
                           'filter_condition':json.dumps(filter_condition),
                           'consult_id':base_info.get('consult_id', -1),
                           'perms':psuser.perms,
                           'ps_type':psuser.position,
                           'source_type':source_type
                        }

    if json_nosraech_data:
        result_dict.update({'json_nosraech_data':json_nosraech_data})
    return render_to_response(template, result_dict, context_instance = RequestContext(request))

# 保留
@ps_auth
def crm_url_redirect(request):
    """获取跳转开车精灵的url"""
    try:
        shop_id = int(request.GET.get('shop_id', ''))
        login_type = str(request.GET.get('login_type'))
        next_url = request.GET.get('next_url', '')
        psuser_name = request.session['psuser_name']
    except Exception, e:
        return render_to_limited(request, '异常，服务器接收参数失败，请联系管理员！')

    if shop_id:
        try:
            user = User.objects.get(shop_id = shop_id)
        except Exception, e:
            log.exception('the user has been lost, shop_id=%s, e=%s' % (shop_id, e))
            return render_to_limited(request, '抱歉, 该用户不存在我们系统中！')
        backend_url = user.get_backend_url(user_type = "staff", psuser_name = psuser_name, next_url = next_url, visitor_from = login_type).get('web_url')
        if backend_url:
            return HttpResponseRedirect(backend_url)
        else:
            return render_to_limited(request, "跳转失败，请检查用户的软件版本，如版本无误请联系管理员！")

# 保留
def kw_manage(request):
    if not request.GET:
        result_dict = {}
    else:
        try:
            shop_id = int(request.GET['shop_id'])
            item_id = int(request.GET['item_id'])
            jump_type = str(request.GET['jump_type'])
        except Exception, e:
            log.error('get parameters error, e=%s')
            return render_to_error(request, msg = '出错，跳转失败，请联系管理员！')
        else:
            from apps.subway.models_item import Item
            try:
                cat_id = Item.objects.get(shop_id = shop_id, item_id = item_id).cat_id
            except Exception, e:
                log.error('get item error, item_id=%s, shop_id=%s, e=%s' % (item_id, shop_id, e))
                return render_to_error(request, msg = '宝贝在我们系统中不存在！')
            else:
                try:
                    cat_path = Cat.get_cat_attr_func(cat_id = cat_id, attr_alias = "cat_path_id")
#                     cat_path = cat_list_str and '%s %s' % (cat_list_str, cat_id) or str(cat_id)
                except Exception, e:
                    log.error('get cat parent ids error,cat_id=%s, e=%s' % (cat_id, e))
                result_dict = {'item_id':item_id, 'jump_type':jump_type, 'init_cat_path':cat_path}
    return render_to_response('crm_kw_manage.html', result_dict, context_instance = RequestContext(request))


# 保留
@ps_auth
def manager_mntcfg(request):
    return render_to_response('manager_mntcfg.html', {}, context_instance = RequestContext(request))
