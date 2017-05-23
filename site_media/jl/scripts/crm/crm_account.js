PT.namespace('CrmAccount');
PT.CrmAccount = function () {
    var account_table=null,hide_column_list=[],fixed_header=null;
    var init_table=function (){
        var custom_column= [
            {"bSortable": false},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": true},
            {"bSortable": false}
        ];

        var show_col_dict={'impressions':3,'click':4,'ctr':5,'cost':6,'cpc':7,'paycount':9,'pay':10,'conv':11,'roi':12};

        for (var i in hide_column_list){
            custom_column[hide_column_list[i][0]]['bVisible']=hide_column_list[i][1];
        }

        account_table=$('#account_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": false,
            "bInfo": true,
            "bAutoWidth":false,//禁止自动计算宽度
            "sDom":"<'row-fluid't>",
            "aoColumns":custom_column,
            "oLanguage": {
                    "sEmptyTable":"没有数据"
            }
        });

    };



    var init_dom=function(){

        $("#assign_consult_operation").click(function(){
            var input_list = $(".kid_box:checked");
            var shop_list = new Array();
            for(var i = 0 ; i < input_list.length ; i++){
                shop_list.push($(input_list[i]).val());
            }
            if(shop_list.length > 0){
                var assign_type = $("input[name=assign_type]:checked").val();
                var consult_id = $("#assign_consult_id").val();
                if(parseInt(consult_id)>0){
                    PT.show_loading('正在分配账户');
                    PT.sendDajax({"function":"crm_assign_customer_2consult","shop_id_list":$.toJSON(shop_list),'consult_id':consult_id,'assign_type':assign_type})
                } else {
                    PT.alert('请选中有效用户');
                }
            } else {
                PT.alert('请选中您要分配的账户。');
            }
        });

        $("#assign_consult").click(function(){
            $("#assign_consult_type").change();
        });

        $("#assign_consult_type").change(function(){
            PT.sendDajax({'function':"crm_get_base_user_info",'department':$(this).val(),'name_space':"CrmAccount"});
        });

        //分配客服组、客服的动画效果
        $(document).on('click.PT.dropdown',function(e){
            e.stopPropagation();
            if(!$('.btn-group').find(e.target).length){
                $('.btn-group .dropdown-menu').removeClass('show');
            }
        });

        $("#show_contact").click(function(){
            PT.show_loading("获取联系方式中");
            var obj_list = $("#account_table .kid_box");
            var ids = [];
            for(var i = 0 ; i < obj_list.length; i++){
                ids.push($(obj_list[i]).val());
            }
            PT.sendDajax({'function':'crm_get_contact_info','acc_ids':$.toJSON(ids)});
        });

        $('.dropdown_a').click(function(e){
            e.stopPropagation();
            $('#fixed_box .btn-group').removeClass('open');
            $(this).next().toggleClass('show');
        });

        $('.btn-group .closer').click(function(e){
            e.stopPropagation();
            $(this).parents('.dropdown-menu').removeClass('show');
        });

//      $('#repair_data').click(function(){
//          $('#assign_group').next().removeClass('show');
//          $('#assign_consult').next().removeClass('show');
//      });
//
//      $('.repair_data').click(function(){
//          var data_type=$(this).attr('data_type'),objs=$('#account_table tbody input:checked'),repair_list=[];
//          if (data_type==0) {
//              objs.each(function(){
//                  var shop_id=parseInt($(this).val());
//                  repair_list.push(shop_id);
//              });
//          } else {
//              objs.each(function(){
//                  var shop_id=parseInt($(this).val());
//                  repair_list.push([shop_id,[shop_id]]);
//              });
//          }
//          if (repair_list.length>0) {
//              PT.confirm('您确定要修复'+repair_list.length+'个店铺的'+(data_type==1?'报表':'结构')+'数据',repair_data,[repair_list,data_type]);
//          }
//      });

        $('#assign_consult').click(function(){
//          $('#repair_data').removeClass('open');
            $('#assign_group').next().removeClass('show');
            var group_id=$('#base_consult_group_id').val();
            // PT.sendDajax({'function':'crm_get_consult_8groupid','group_id':group_id,'name_space':'CrmAccount'});
        });

        $('#assign_consult_submit').click(function(){
            var consult_id=$('input[name="consult_id"]:checked').val(),shop_list=get_checked_data();
            if(shop_list.length>0) {
                PT.sendDajax({'function':'crm_assign_account_2stuff','consult_id':consult_id,'shop_list':$.toJSON(shop_list)});
            }
        });

        $(document).on('keyup','#sms_content',function(){
            var count=$(this).val().length;
            $('#left_count').text(60-count);
        });

        $(document).on('click','#submit_sms',function(){
            var content=$('#sms_content').val();
            if(content){
                var objs=$('#account_table tbody input:checked'),phone_list=[];
                objs.each(function(){
                    var phone=parseInt($(this).attr('phone'));
                    if (phone) {
                        phone_list.push(phone);
                    }
                });
                if (phone_list.length) {
                    PT.show_loading('正在发送短信');
                    PT.sendDajax({'function':'crm_submit_sms','content':content,'phone_list':$.toJSON(phone_list)});
                }else{
                    PT.light_msg('请至少选择一条记录');
                }
            }else{
                PT.light_msg('','请填写短信内容');
            }
        });
    };

    //获取所有选中项的shop_id
    var get_checked_data=function(){
        var objs=$('#account_table tbody input:checked'),shop_list=[];
        objs.each(function(){
            var shop_id=parseInt($(this).val());
            shop_list.push(shop_id);
        });
        return shop_list;
    };

    //显示或隐藏列 参数 [[1,true],[2,false]]
    var hide_custom_column=function(iCol){
        for (var i in iCol){
            var bVis = account_table.fnSettings().aoColumns[iCol[i][0]].bVisible;
            if(iCol[i][1]!=bVis){
                account_table.fnSetColumnVis(iCol[i][0], iCol[i][1]);
            }
        }
    };

    var ajax_init_dom=function(){
        // 添加全选事件
        PT.CrmCondition.add_all_selected_envent();

        $('.group-checkable.father_box').attr('checked',null);

        $('.open_charts').click(function(){
            var shop_id=$(this).parent().parent().find('.kid_box').val();
            PT.sendDajax({'function':'crm_show_trend','shop_id':shop_id,'obj_id':shop_id,'get_type':1,'rpt_days':15});
        });

        App.initTooltips();

        $(window).on('scroll.PT.Table',function(){
            if(account_table==undefined){
                return;
            }
            var body_ofset = document.body.scrollTop | document.documentElement.scrollTop,
                body_ofset_left = document.body.scrollLeft | document.documentElement.scrollLeft,
                base_top=account_table.offset().top-40;
            if (body_ofset>base_top&&base_top>0){
                $('#fixed_div').addClass('active').css({'marginLeft':-body_ofset_left+43,'width':$('#fixed_div').parent().width()});
                if(fixed_header==undefined){
                    fixed_header=new FixedHeader(account_table,{"offsetTop":40});
                }
            }else{
                $('#fixed_div').removeClass('active').css({'marginLeft':0,'width':'auto'});
                if(fixed_header!=undefined){
                    $(fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
                }
                fixed_header=null;
            }
        });

        //定制列选一行
        $('#select_column li[class*="title"] input').change(function(){
            $(this).parents('ul').find('input').not('[value='+this.value+']').attr('checked',this.checked);
        });

        //定制列
        $('.select_column_btn').click(function(){
            var column_list=[],mode=$(this).attr('mode');
            $('#select_column li:not([class*="title"]) input').each(function(){
                column_list.push([Number($(this).val()),(this.checked?true:false)]);
            });
            $('#select_column').parent().removeClass('open');
            hide_custom_column(column_list);
            hide_column_list=column_list;
        });

        //定制列计算
        $('#select_column_show_btn').click(function(){
            var obj=account_table.fnSettings().aoColumns,inputs=$('#select_column');
            for (var i in obj){
                inputs.find('input[value="'+i+'"]').attr('checked',obj[i].bVisible)
            }
        });

        $('.jump').click(function(){
            var shop_id_arr=[],obj=null;
            if ($(this).hasClass('single')) {
                obj=$(this).parents('tr').find('input.kid_box');
            } else {
                obj=$('#account_table tbody input:checked');
            }
            obj.each(function(){
                    shop_id_arr.push(parseInt($(this).val()));
                });
            if (shop_id_arr.length<1) {
                PT.alert('请至少选择一条记录');
                return;
            }
            var action_str='/crm/'+$(this).attr('target_url')+'/',
                id_dict={'account':shop_id_arr};
            $('input[name="id_dict"]').val($.toJSON(id_dict));
            $('#jump_form').attr({action:action_str});
            $('#jump_form').submit();
        });

        $('.jump_ncrm_optimize').click(function(){
            var shop_id_arr=[],obj=null;
            if ($(this).hasClass('single')) {
                obj=$(this).parents('tr').find('input.kid_box');
            } else {
                obj=$('#account_table tbody input:checked');
            }
            obj.each(function(){
                    shop_id_arr.push(parseInt($(this).val()));
                });
            if (shop_id_arr.length<1) {
                PT.alert('请至少选择一条记录');
                return;
            }
            $('input[name="shop_id_list"]').val($.toJSON(shop_id_arr));
            $('#jump_ncrm_optimize_form').submit();
        });

        // 复选框事件
        $('.father_box').click(function(){
            var area_id=$(this).attr('link'),
                kid_box=$('#'+area_id).find('input[class*="kid_box"]'),
                now_check=this.checked;
            kid_box.each(function(){
                if (this.checked!=now_check) {
                    this.checked=now_check;
                    $(this).parent().toggleClass('check_box_color');
                }
            });
            get_checked_count();
        });

        $('input[class*="kid_box"]').click(function(){
            $(this).parent().toggleClass('check_box_color');
            get_checked_count();
        });

        $select({name: 'result_item','callBack': update_checked_status});
        account_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
            'fn':function(){selectRefresh();},
            'sName':'refresh_select'
        });
    };

    var update_checked_status=function(){
        var kid_box=$('input[class*="kid_box"]');
        kid_box.each(function(){
            if ($(this).attr("checked")=="checked") {
                $(this).parent().addClass('check_box_color');
            } else {
                $(this).parent().removeClass('check_box_color');
            }
        });
        get_checked_count();
    };

    var get_checked_count=function(){
        var checked_num = $('#account_table tbody input:checked').length;
        $('#current_count').text(checked_num);
        return checked_num;
    };

//  var repair_data=function(repair_list,data_type){
//      PT.show_loading('正在修复'+(data_type==1?'报表':'结构')+'数据');
//      PT.sendDajax({'function':'crm_repair_data','data_type':data_type,'obj_type':0,'repair_list':$.toJSON(repair_list)});
//  }

    var handle_page=function(page_count,page_no){
        $('#dynamic_pager').bootpag({
                total: page_count,
                page: page_no,
                leaps: false,
                prev:'上一页',
                next:'下一页',
                maxVisible: 10
        }).on('page', function(event, num){
                PT.CrmCondition.get_filter_result(num);
        });
    };

    var change_page_info=function(del_count){
        var old_count=parseInt($('.total_count').eq(0).text());
        $('.total_count').text(old_count - del_count);
    };

    return {
        init:function(){
            PT.Base.set_nav_activ('crm_account');
            init_dom();
        },

        call_back:function(data,page_info){
            var temp_str='';
            for (var i=0;i<data.length;i++){
                data[i].index=i+1;
                temp_str += template.render('account_table_tr', data[i]);
            }
            if(account_table){
                account_table.fnDestroy();
                $('#account_table tbody tr').remove();
            }
            $('#account_table tbody').html(temp_str);
            init_table();

            get_checked_count();
            $('.page_size').text(page_info['page_size']);
            $('.page_count').text(page_info['page_count']);
            $('.total_count').text(page_info['total_count']);
            if (!$('#dynamic_pager ul').length){
                handle_page(page_info['page_count'],page_info['page_no']);
            }
            ajax_init_dom();
            PT.hide_loading();
        },

        get_group_back:function(user_id, user_type, group_list,user_list){
            var obj = $('#assign_consult_type');
            var obj_sub = $("#assign_consult_id");

            var option_str = "";
            if(group_list.length > 0){
                for(var i=0;i<group_list.length;i++) {
                    option_str += "<option value='"+group_list[i][0]+"'>"+group_list[i][1]+"</option>";
                }
                obj.html(option_str);
            }

            option_str = "";
            for(var i=0;i<user_list.length;i++) {
                option_str += "<option value='"+user_list[i][0]+"'>"+user_list[i][1]+"</option>";
            }
            obj_sub.html(option_str);
        },

        get_consult_back:function(consult_list){
            var ul_str='';
            for(var i=0;i<consult_list.length;i++) {
                ul_str+='<li><label class="radio"><input type="radio" value="'+consult_list[i]['id']+'"name="consult_id"><span class="marr_3">'+consult_list[i]["name"]+'</span></label></li>';
            }
            $('#consult_radio').html('').prepend(ul_str);
        },

        assign_account_back:function(type,data){
            msg='已成功分配'+data.length+'个客户到'+(type?'顾问':'顾问组');
            PT.alert(msg);
            for(var i=0; i<data.length; i++) {
                account_table.fnDeleteRow($('#'+data[i])[0]);
            }
            change_page_info(data.length);
        },

        // repair_data_back:function(failed_count){
        //  PT.hide_loading();
        //  msg=(failed_count==0?'已修复完数据':'修复数据失败');
        //  PT.alert(msg);
        //  $('#button_search').click();
        // },

        show_trend:function(account_id, category_list, series_cfg_list) {
            var account_nick =  $('#account_table_wrapper #'+account_id+' .account_nick').text()
            $('#account_trend_title').text(account_nick);
            PT.draw_trend_chart( 'account_trend_chart' , category_list, series_cfg_list);
            $('#modal_account_trend').modal();
        },

        set_contact_info:function(data){
            for(var key in data){
                var temp_html = "" ;
                for(var sub_key in data[key]){
                    temp_html += template.render('contact_record',{'title':sub_key,'content':data[key][sub_key]});
                }
                var opar = $("#account_table tr[id="+key+"] .contact_info");
                if (opar.length>0){
                    opar.html(temp_html);
                    opar.parent().show();
                }
            }
        },

        assign_result_report:function(shop_id_list,faild_len){
            for(var i = 0 ; i < shop_id_list.length ; i++){
                $('#account_table tr[id='+shop_id_list[i]+']').remove();
            }
            if(parseInt(faild_len) === 0 ){
                PT.alert("已成功分配 "+ shop_id_list.length +" 个用户");
            } else {
                PT.alert("已成功分配 "+ shop_id_list.length +" 个用户，失败 "+faild_len+"个用户 ！(存在失败的原因是有选中免费一个月的用户。)");
            }

        },

        submit_sms_back:function(result){
            if (result.is_success){
                $('#modal_sms').modal('hide');
                var msg='成功给'+result.count+'家店铺发送短信';
                PT.alert(msg);
            }else{
                PT.alert('发送短信失败：'+result.error_msg);
            }
        }
    };
}();
