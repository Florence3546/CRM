# coding=UTF-8
'''
Created on 2015年7月9日

@author: tianxiaohe
'''
from apps.common.utils.utils_datetime import datetime_2string
from apps.common.utils.util_expert_excel import export_excel
from apps.ncrm.models import PSUser

def export_workbench_data(customer_list,export_type):
    """个人工作台数据导出"""
    title = "客户列表"
    export_list = []
    for data in customer_list:
        temp_data = {'shop_id':data.shop_id,
                     'nick':data.nick,
                     'phone':data.phone,
                     'qq':data.qq,
                     'category':data.category,
                     'department':'',
                     'name_cn':''}
        if hasattr(data,'consult'):
            if hasattr(data.consult,'department'):
                temp_data.update({'department':dict(PSUser.DEPARTMENT_CHOICES)[data.consult.department]})
            if hasattr(data.consult,'name_cn'):
                temp_data.update({'name_cn':data.consult.name_cn})
        elif hasattr(data,'operater'):
            if hasattr(data.operater,'department'):
                temp_data.update({'department':dict(PSUser.DEPARTMENT_CHOICES)[data.operater.department]})
            if hasattr(data.operater,'name_cn'):
                temp_data.update({'name_cn':data.operater.name_cn})

        if hasattr(data,'order_info'):
            order_info = data.order_info
            if order_info:
                temp_data.update({'create_time':datetime_2string(order_info.create_time, '%Y-%m-%d'),
                                  'end_date':datetime_2string(order_info.end_date, '%Y-%m-%d'),
                                  'biz_type':order_info.display_biz_type(),
                                  'cycle':order_info.cycle,
                                  'pay':'%.2f' %(order_info.pay/100.0),
                                  'item_code':order_info.item_code
                                  })
        if hasattr(data,'rpt'):
            rpt = data.rpt if data.rpt else {'click':0,'cost':'0.00','paycount':0,'pay':'0.00','cpc':'0.00','ctr':'0.00','roi':'0.00'}
            temp_data.update(rpt)
        export_list.append(temp_data)

    column_dict = [ {'key':'shop_id', 'name':'店铺ID'},
                    {'key':'nick', 'name':'店铺名称', 'width':2},
                    {'key':'phone', 'name':'电话', 'width':2},
                    {'key':'qq', 'name':'QQ'},
                    {'key':'category', 'name':'店铺类别', 'width':2},
                    {'key':'name_cn', 'name':'所属顾问'},
                    {'key':'department', 'name':'所属部门'}]

    if export_type == '1':
        column_dict += [{'key':'create_time', 'name':'订购时间'},
                        {'key':'end_date', 'name':'到期时间'},
                        {'key':'biz_type', 'name':'订单类型'},
                        {'key':'cycle', 'name':'订购周期'},
                        {'key':'pay', 'name':'实付金额'},
                        {'key':'item_code', 'name':'版本Code', 'width':2}]
    elif export_type == '2':
        column_dict += [{'key':'click', 'name':'7天点击量'},
                        {'key':'cost', 'name':'7天总花费'},
                        {'key':'paycount', 'name':'7天成交量'},
                        {'key':'pay', 'name':'7天成交金额'},
                        {'key':'cpc', 'name':'PPC'},
                        {'key':'ctr', 'name':'CTR'},
                        {'key':'roi', 'name':'ROI'}]
    elif export_type == '3':
        column_dict += [{'key':'create_time', 'name':'订购时间'},
                        {'key':'end_date', 'name':'到期时间'},
                        {'key':'biz_type', 'name':'订单类型'},
                        {'key':'cycle', 'name':'订购周期'},
                        {'key':'pay', 'name':'实付金额'},
                        {'key':'item_code', 'name':'版本Code', 'width':2},
                        {'key':'click', 'name':'7天点击量'},
                        {'key':'cost', 'name':'7天总花费'},
                        {'key':'paycount', 'name':'7天成交量'},
                        {'key':'pay', 'name':'7天成交金额'},
                        {'key':'cpc', 'name':'PPC'},
                        {'key':'ctr', 'name':'CTR'},
                        {'key':'roi', 'name':'ROI'}]
    response = export_excel(title,column_dict,export_list)
    return response