# coding=UTF-8
from django.template import Library
from django.db import models
from django.core.urlresolvers import reverse
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

from apps.router.models import User


def renderField(value, f, colsnum = 1):
    if f.choices:
        field_value = getattr(value, 'get_%s_display' % f.name)()
    else:
        org_value = getattr(value, f.name)
        if isinstance(org_value, User):
            field_value = """<div style="height:100%%;"><a href="%(url)s">%(username)s</a>
         <a target="_blank" href="http://wpa.qq.com/msgrd?v=1&uin=%(qq)s&site=qq&menu=yes">
         <img border="0" src="http://wpa.qq.com/pa?p=2:%(qq)s:41" alt="QQ:%(qq)s" title="QQ:%(qq)s"></a>
             </div>""" % {'url':reverse("up_consumer_home", args = [org_value.id]), 'username':org_value.username, 'qq':org_value.first_name}
        elif isinstance(f, models.ImageField):
            field_value = """<img src="%s%s" width="60%%"  align="middle"/> """ % (settings.MEDIA_URL, org_value)
        elif isinstance(f, models.URLField):
            field_value = """<a href="%s" style='text-decoration:underline;'/>%s</a>""" % (org_value, org_value)
        elif isinstance(f, models.FileField) and f.name.find('flash') != -1: #TODO:hack,假定flash字段名包含‘flash’这几个字母
            field_value = """
            <object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" id="flash" width="60%%"  align="middle">
                <param name="movie" value="%s%s">
                <embed src="%s%s"  type="application/x-shockwave-flash"  width="60%%"  align="middle"></embed>
            </object> """ % (settings.MEDIA_URL, org_value , settings.MEDIA_URL, org_value)
        elif isinstance(f, models.BooleanField) or isinstance(f, models.NullBooleanField):
            if org_value == None:
                field_value == '---'
            else:
                field_value = org_value and '是' or '否'
        else:
            field_value = org_value

    if field_value == None or field_value == '':
        field_value = "无"

    return """<th>%s:</th><td>%s</td>""" % (f.name and f.verbose_name, field_value)


register = Library()
def model_as_table(value, arg = ''):#arg标示不要显示的字段的name，以逗号分开。默认时，id列不显示

    if not isinstance(value, models.Model):
        return value
    arg = arg.strip()
    names = arg and arg.split(',') or ['id']

    tr_list = []
    for f in value._meta.fields:
        if f.name in names:
            continue
        tr = '<tr>%s</tr>' % renderField(value, f)
        tr_list.append(tr)
    return mark_safe('\n'.join(tr_list))

register.filter(model_as_table)

def model_as_table_with(value, arg = ''):#arg标示要显示的字段的name，以逗号分开。并且按arg中的顺序来显示
    if not isinstance(value, models.Model):
        return value
    arg = arg.strip()
    names = arg and arg.split(',')
    colsnum = 1
    if len(names) > 0:#传入了arg
        if names[0].isdigit():#第一个是数字
            colsnum = int(names[0])
            if len(names) == 1:#只有一个参数
                names = [f.name for f in value._meta.fields if f.name != 'id']
            else:
                names = names[1:]
    else:
        names = [f.name for f in value._meta.fields if f.name != 'id']

    row_list = []
    col_list = []
    for name in names:
        if name == '-':#换行
            if len(col_list) > 0:
                #col_list+=['<th></th><td></td>']*(colsnum-len(col_list))#补齐当前行
                row_list.append('<tr>%s</tr>' % ''.join(col_list))
                col_list = []

            row = '<tr class="blank"><td colspan="%s"></td></tr>' % (colsnum * 2)#插入空行
            row_list.append(row)
        else:
            for f in value._meta.fields:
                if f.name == name:
                    col = renderField(value, f, colsnum)
                    col_list.append(col)
                    if len(col_list) == colsnum:
                        row_list.append('<tr>%s</tr>' % ''.join(col_list))
                        col_list = []

    if len(col_list) > 0:
        #col_list+=['<th></th><td></td>']*(colsnum-len(col_list))#补齐当前行
        row_list.append('<tr>%s</tr>' % ''.join(col_list))
        col_list = []

    return mark_safe('\n'.join(row_list))

register.filter(model_as_table_with)



def renderField_div(value, f, colsnum = 1):
    if f.choices:
        field_value = getattr(value, 'get_%s_display' % f.name)()
    else:
        org_value = getattr(value, f.name)
        if isinstance(org_value, User):
            field_value = """<div style="height:100%%;"><a href="%(url)s">%(username)s</a>
         <a target="_blank" href="http://wpa.qq.com/msgrd?v=1&uin=%(qq)s&site=qq&menu=yes">
         <img border="0" src="http://wpa.qq.com/pa?p=2:%(qq)s:41" alt="QQ:%(qq)s" title="QQ:%(qq)s"></a>
          </div>""" % {'url':reverse("up_consumer_home", args = [org_value.id]), 'username':org_value.username, 'qq':org_value.first_name}

        elif isinstance(f, models.ImageField):
            field_value = """<img src="%s%s" width="60%%"  align="middle"/> """ % (settings.MEDIA_URL, org_value)
        elif isinstance(f, models.URLField):
            field_value = """<a href="%s" style='text-decoration:underline;'/>%s</a>""" % (org_value, org_value)
        elif isinstance(f, models.FileField) and f.name.find('flash') != -1: #TODO:hack,假定flash字段名包含‘flash’这几个字母
            field_value = """
            <object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" id="flash" width="60%%"  align="middle">
                <param name="movie" value="%s%s">
                <embed src="%s%s"  type="application/x-shockwave-flash"  width="60%%"  align="middle"></embed>
            </object> """ % (settings.MEDIA_URL, org_value , settings.MEDIA_URL, org_value)
        elif isinstance(f, models.BooleanField) or isinstance(f, models.NullBooleanField):
            if org_value == None:
                field_value == '---'
            else:
                field_value = org_value and '是' or '否'
        else:
            field_value = org_value

    if field_value == None or field_value == '':
        field_value = "无"

    return """<div class="col_name">%s:</div><div class="col_value">%s</div>""" % (f.name and f.verbose_name, field_value)

def model_as_divtable_with(value, arg = ''):#arg标示要显示的字段的name，以逗号分开。并且按arg中的顺序来显示
    if not isinstance(value, models.Model):
        return value
    arg = arg.strip()
    names = arg and arg.split(',')
    colsnum = 1
    if len(names) > 0:#传入了arg
        if names[0].isdigit():#第一个是数字
            colsnum = int(names[0])
            if len(names) == 1:#只有一个参数
                names = [f.name for f in value._meta.fields if f.name != 'id']
            else:
                names = names[1:]
    else:
        names = [f.name for f in value._meta.fields if f.name != 'id']

    row_list = []
    col_list = []
    row_format = '<div class="row">%s<div style="clear:both"></div></div>'
    for name in names:
        if name == '-':#换行
            if len(col_list) > 0:
                row_list.append(row_format % ''.join(col_list))
                col_list = []
        else:
            for f in value._meta.fields:
                if f.name == name:
                    col = renderField_div(value, f, colsnum)
                    col_list.append(col)
                    if len(col_list) == colsnum:
                        row_list.append(row_format % ''.join(col_list))
                        col_list = []

    if len(col_list) > 0:
        row_list.append(row_format % ''.join(col_list))
        col_list = []

    return mark_safe('\n'.join(row_list))

register.filter(model_as_divtable_with)

def form_as_table_with(value, arg = ''):#arg标示要显示的字段的name，以逗号分开。并且按arg中的顺序来显示
    if not isinstance(value, forms.BaseForm):
        return value
    arg = arg.strip()
    names = arg and arg.split(',')
    colsnum = 1
    if len(names) > 0:#传入了arg
        if names[0].isdigit():#第一个是数字
            colsnum = int(names[0])
            if len(names) == 1:#只有一个参数
                names = [f.name for f in value.fields]
            else:
                names = names[1:]
    else:
        names = [f.name for f in value.fields]

    tr_list = value.as_table().split('</tr>')
    tr_list = [tr.replace('<tr>', '') for tr in tr_list]

    row_list = []
    col_list = []
    for name in names:
        if name == '-':#换行
            if len(col_list) > 0:
                #col_list+=['<th></th><td></td>']*(colsnum-len(col_list))#补齐当前行
                row_list.append('<tr>%s</tr>' % ''.join(col_list))
                col_list = []
            row = '<tr class="blank"><td colspan="%s"></td></tr>' % (colsnum * 2)#插入空行
            row_list.append(row)
        else:
            for tr in tr_list:
                if tr.find('name="%s"' % value.add_prefix(name)) > -1:
                    col_list.append(tr)
                    if len(col_list) == colsnum:
                        row_list.append('<tr>%s</tr>' % ''.join(col_list))
                        col_list = []
    if len(col_list) > 0:
        #col_list+=['<th></th><td></td>']*(colsnum-len(col_list))#补齐当前行
        row_list.append('<tr>%s</tr>' % ''.join(col_list))
        col_list = []

    return mark_safe('\n'.join(row_list))

register.filter(form_as_table_with)


def table_colsnum(value, arg):
    if not arg.isdigit():
        return value
    num = int(arg)
    tr_list = value.split('</tr>')
    tr_list = [tr.replace('<tr>', '') for tr in tr_list]
    row_list = []
    col_list = []
    for tr in tr_list:
        col_list.append(tr)
        if len(col_list) == num:
            row_list.append('<tr>%s</tr>' % ''.join(col_list))
            col_list = []
    if len(col_list) > 0:
        #col_list+=['<th></th><td></td>']*(num-len(col_list))#补齐当前行
        row_list.append('<tr>%s</tr>' % ''.join(col_list))
        col_list = []
    return mark_safe('\n'.join(row_list))
register.filter(table_colsnum)
