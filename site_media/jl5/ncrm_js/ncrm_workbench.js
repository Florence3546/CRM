PT.namespace('NcrmWorkbench');
PT.NcrmWorkbench = function() {
    var load_staffs = function(){
        var psuser_id_obj = $("#workbanch_search_form input[name='psuser_id']");
        var psuser_id = parseInt(psuser_id_obj.val());
        if(psuser_id > 0){
            PT.sendDajax({
                'function': 'ncrm_get_staffs_bydepartment',
                'psuser_id':psuser_id,
                'call_back': 'PT.NcrmWorkbench.get_staffs_bydepartment_back'
             });
        } else {
            PT.alert("加载员工列表失败，请联系开发人员。");
        }
    }

    var refresh_my_reminder = function () {
        PT.sendDajax({
            'function':'ncrm_get_my_reminder',
            'callback':'PT.NcrmWorkbench.get_my_reminder_callback'
        })
    }

    var init_dom = function() {
        //load_staffs() // 加载 当前用户所在的部门所有员工

        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#id_start_date',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '#id_end_date',
                timepicker: false,
                closeOnDateSelect : true
            });

        });

        $(".department_staffs").change(function(){
            var obj = $(this);
            $("#workbanch_search_form input[name='psuser_id']").val(obj.val());
        });

        $(".ajax_edit").focus(function(){
            var obj = $(this);
            obj.attr('old_val',obj.val());
        });

        $(".ajax_edit").blur(function(){
            var mapping = {
                       'qq':/^[0-9]+$/,
                       'phone':/^[0-9][0-9\-]+[0-9]$/,
            }
            var obj = $(this);
            var attr_name = obj.attr('attr');
            var val = obj.val().replace(/\s/g, "");
            var old_val = obj.attr('old_val').replace(/\s/g, "");
            var shop_id = obj.parent().parent().attr('shop_id');
            if ( val != old_val && parseInt(shop_id) > 0) {
                if(mapping.hasOwnProperty(attr_name)){
                    if(! mapping[attr_name].test(val)){
                        PT.alert("请输入正确参数");
                        return false;
                    }
                }
                var cust_dict = {};
                cust_dict['shop_id'] = shop_id;
                cust_dict[attr_name] = val;

                PT.sendDajax({
                    'function': 'ncrm_update_customer',
                    'cust_dict':$.toJSON(cust_dict),
                    'call_back': 'PT.NcrmWorkbench.update_customer_back'
                 });
            }
        });

        $('.tips').tooltip();

        $('.open_perms_model').click(function(){
            $("#current_perms").html($(this).attr('perms_code'));
            $("#ad_perms").val($(this).attr('ad_perms'));
            $("#user_id").val($(this).attr("cust_id"));
            $("#id_update_perms_layout").modal();
        });

        $('.allocation_record').click(function () {
            PT.show_loading('正在加载');
            PT.sendDajax({
                'function': 'ncrm_get_allocation_record',
                'shop_id': $(this).attr('shop_id'),
                'callback': 'PT.NcrmWorkbench.get_allocation_record_callback'
            });
        });
        //修改店铺的黄金会员
        $(".modify-memberorder").click(function(){
            PT.sendDajax({
                'function':'ncrm_get_modify_cus_memberorder',
                'shop_id':$(this).attr('shop_id'),
                'callback':'PT.NcrmWorkbench.modify_memberorder_callback'
            })
        });

        $('#forbidden_all_perms').click(function () {
            $('#ad_perms').val($('#current_perms').text().toLowerCase());
        });

        $('a.version_perms_code').click(function () {
            var current_perms = $.trim($('#current_perms').text()),
                  version_perms_code = $(this).attr('perms_code'),
                  ad_perms = '', temp = '';
            for (var i in version_perms_code) {
                temp = version_perms_code[i];
                if (current_perms.indexOf(temp)==-1) {
                    ad_perms += temp;
                }
            }
            for (var i in current_perms) {
                temp = current_perms[i];
                if (version_perms_code.indexOf(temp)==-1) {
                    ad_perms += temp.toLowerCase();
                }
            }
            $('#ad_perms').val(ad_perms);
        });

        $('#id_submit_perms').on('click', function(){
            PT.sendDajax({'function':'ncrm_update_perms_code', 'uid':$("#user_id").val(), 'perms_code':$('#ad_perms').val()});
            $("#id_update_perms_layout").modal('hide');
        });

        $('.event_detail').click(function(){
            PT.show_loading("正在加载");
            var shop_id = $(this).parents('tr').attr('shop_id');
            PT.sendDajax({'function':'ncrm_get_event_detail_byshopid','shop_id':shop_id});
        });

        $('.reset_shopmngtask').click(function(){
           PT.show_loading("重置中");
           var shop_id = $(this).parents('tr').attr('shop_id');
           PT.sendDajax({'function':'ncrm_reset_shopmngtask', 'shop_id':shop_id});
        });

        $('.exec_shopmngtask').click(function(){
           PT.show_loading("正在执行");
           var shop_id = $(this).parents('tr').attr('shop_id');
           PT.sendDajax({'function':'ncrm_exec_shopmngtask', 'shop_id':shop_id});
        });

        $('.get_mnt_info').click(function(){
           var shop_id = $(this).parents('tr').attr('shop_id');
           PT.sendDajax({'function':'ncrm_get_mnt_info','shop_id':shop_id});
        });

        $('.repair_lastrpt').click(function(){
           var shop_id = $(this).parents('tr').attr('shop_id');
           PT.show_loading("正在修复");
           PT.sendDajax({"function":"ncrm_repair_lastrpt", "shop_id":shop_id});
        });

        $('.modify_server').click(function(){
           var nick = $(this).closest('tr').attr('nick');
           PT.sendDajax({'function':'ncrm_get_server', 'nick':nick});
        });

        $('#id_submit_port').click(function(){
           var nick = $('#id_nick').text();
           var port_id = parseInt($('#id_port_select').val());
           var port_id_bak = parseInt($('#id_port_id_bak').val());
           if(port_id==port_id_bak){
               $('#id_edit_port_layer').modal('hide');
           } else{
               if(port_id==0){
                   PT.alert("不能将已分配的用户修改为空！");
               }else{
                   PT.sendDajax({'function':'ncrm_update_server', 'nick':nick, 'port_id':port_id});
               }
           }
        });

        $('.clear_token').click(function(){
           PT.show_loading("清除缓存中");
           var shop_id = $(this).parents('tr').attr('shop_id'),
                nick = $(this).closest('tr').attr('nick');
           PT.sendDajax({'function':'ncrm_clear_token', 'shop_id':shop_id, 'nick':nick});
        });

        $('#order_view').click(function () {
            if (!$(this).hasClass('active')) {
                $(this).siblings().removeClass('active');
                $(this).addClass('active');
                $('table.user_table tbody tr div.account_report, table.user_table thead tr ul.account_report').hide();
                $('table.user_table tbody tr div.order_info, table.user_table thead tr ul.order_info').show();
            }
            $('a.report_view').show();
            $('a.order_view').hide();
        });

        $('#report_view').click(function () {
	        if (!$(this).hasClass('active')) {
		        $(this).siblings().removeClass('active');
		        $(this).addClass('active');
		        $('table.user_table tbody tr div.order_info, table.user_table thead tr ul.order_info').hide();
		        $('table.user_table tbody tr div.account_report, table.user_table thead tr ul.account_report').show();
	            if ($(this).attr('loaded')!='1') {
		            PT.show_loading('正在加载店铺报表');
		            PT.sendDajax({
		                'function':'ncrm_get_account_report_dict',
		                'shop_id_list':$.toJSON($.map($('table.user_table tbody tr'),function (tr_obj) {return Number($(tr_obj).attr('shop_id')) || null})),
		                'callback':'PT.NcrmWorkbench.get_account_report_dict_callback'
		            });
	            }
	        }
            $('a.order_view').show();
            $('a.report_view').hide();
        });

        $('a.order_view').click(function () {
            $('#order_view').click();
        });

        $('a.report_view').click(function () {
            $('#report_view').click();
        });

        //事件过滤
        $('#id_event_detail_layer').on('change', '.filter_event', function () {
            if ($(this).attr('name')=='all_event') {
                if ($(this).prop('checked')) {
	                $('#id_event_detail_layer .filter_event').attr('checked', true);
			        $('#event_detail_table>tbody>tr').show();
                } else {
	                $('#id_event_detail_layer .filter_event').attr('checked', false);
			        $('#event_detail_table>tbody>tr').hide();
                }
            } else {
                if ($(this).prop('checked')) {
                    $('#event_detail_table>tbody>tr[event_type='+this.name+']').show();
                } else {
	                $('#id_event_detail_layer .filter_event[name=all_event]').attr('checked', false);
                    $('#event_detail_table>tbody>tr[event_type='+this.name+']').hide();
                }
            }
        });

        //注册删除事件
        $('#id_event_detail_layer').on('click', '.delete_event_detail', function () {
            PT.sendDajax({
                'function': 'ncrm_delete_event',
                'event_id':$(this).attr("event_id"),
                'model_type':$(this).attr("model_type"),
                'call_back': 'PT.NcrmWorkbench.delete_event_back'
            });
        });

        //查看意见反馈
        $('#crm_feedback a.show_feedback').click(function () {
            PT.sendDajax({
                'function': 'ncrm_show_feedback',
                'feedback_id':$(this).attr("feedback_id"),
                'callback': 'PT.NcrmWorkbench.show_feedback_callback'
            });
        });

        //查看公告
        $('#crm_ad a.show_ad').click(function () {
            PT.sendDajax({
                'function': 'ncrm_show_ad',
                'ad_id':$(this).attr("ad_id"),
                'callback': 'PT.NcrmWorkbench.show_ad_callback'
            });
        });

        //查看提醒
        $('#crm_reminder').on('click', 'a.show_reminder', function () {
            PT.sendDajax({
                'function': 'ncrm_show_reminder',
                'reminder_id':$(this).attr("reminder_id"),
                'callback': 'PT.NcrmWorkbench.show_reminder_callback'
            });
        });

        //查看好评及积分兑换
        $('#crm_pa').on('click', 'a.show_pa', function () {
            PT.sendDajax({
                'function': 'ncrm_show_pa',
                'pa_id':$(this).attr("pa_id"),
                'callback': 'PT.NcrmWorkbench.show_pa_callback'
            });
        });

        //标记意见反馈为已处理
        $('#id_show_info').on('click', '.mark_feedback_handled', function () {
            var feedback_note = $.trim($('#id_show_info textarea[name=feedback_note]').val());
            if (!feedback_note) {
                PT.alert('标记前必须填写备注');
            } else {
                $('#id_show_info').modal('hide');
                PT.sendDajax({
                    'function': 'ncrm_mark_feedback_handled',
                    'feedback_id': $('#id_show_info [name=feedback_id]').val(),
                    'feedback_note':feedback_note,
                    'callback': 'PT.NcrmWorkbench.mark_feedback_handled_callback'
                });
            }
        });

        //标记提醒为已处理
        $('#id_show_info').on('click', '.mark_reminder_handled', function () {
            $('#id_show_info').modal('hide');
            PT.sendDajax({
                'function': 'ncrm_mark_reminder_handled',
                'reminder_id': $('#id_show_info [name=reminder_id]').val(),
                'callback': 'PT.NcrmWorkbench.mark_reminder_handled_callback'
            });
        });

        //隐藏好评和积分兑换提醒
        $('#id_show_info').on('click', '.mark_pa_handled', function () {
            $('#id_show_info').modal('hide');
            PT.sendDajax({
                'function': 'ncrm_mark_pa_handled',
                'pa_id': $('#id_show_info [name=pa_id]').val(),
                'callback': 'PT.NcrmWorkbench.mark_pa_handled_callback'
            });
        });

        //点击查看QQ和TEL
        $('body').on('click', '.qq_tip, .phone_tip', function () {
            if ($(this).attr('status')=='0') {
                $(this).popover({content: $.base64('decode', $(this).attr('tip'))}).popover('show');
                $(this).attr('status', '1');
            } else {
                $(this).popover('destroy');
                $(this).attr('status', '0');
            }
        });
    }

    return {
        init: function() {
            init_dom();
            setInterval(refresh_my_reminder, 5*60*1000);
        },delete_event_back:function(json){
            PT.hide_loading();
            if(json.error){
                PT.alert(json.error);
            }else{
                $('#event_detail_table tr[event_id='+json.event_id+']').remove();
                PT.light_msg('提示', '删除成功！');
            }
        },get_event_detail_callback:function(data, data_info){
            $('#id_event_detail_layer').html(template.render('event_detail_template', {'data':data, 'data_info':data_info}));
            $.fancybox.open([{href:'#id_event_detail_layer'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});
            //默认展示事件
            $('#id_event_detail_layer .filter_event[name=unsubscribe]').click();
            $('#id_event_detail_layer .filter_event[name=comment]').click();
            $('#id_event_detail_layer .filter_event[name=tp_subscribe]').click();
            $('#id_event_detail_layer .filter_event[name=pause]').click();
            $('#id_event_detail_layer .filter_event[name=reintro]').click();
            $('#id_event_detail_layer .filter_event[name=visible_contact]').click();
            $('#id_event_detail_layer .filter_event[name=visible_operate]').click();
        },display_mnt_info:function(data){
            var temp_str = '';
            for(i=0;i<data.length;i++){
                temp_str += template.render('mnt_info_template', {'data':data[i]});
            }
            $('#id_mnt_task_layer').html(temp_str);
            $.fancybox.open([{href:'#id_mnt_task_layer'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});
        },update_perms_callback: function(status, perms_code, user_id){
            if(status=='true'){
                var obj = $('#open_perms_model_'+user_id);
                obj.attr('ad_perms', perms_code);
                if (perms_code) {
                    obj.html(obj.attr('perms_code')+'~'+perms_code);
                } else {
                    obj.html(obj.attr('perms_code'));
                }
                PT.alert("修改成功！");
            }else{
                PT.alert("修改失败！请联系系统管理员！");
            }
        },
        update_customer_back:function(json){
             if ( json.error != ""){
                PT.alert(json.error);
             }
        },
        get_staffs_bydepartment_back:function(json){
            if ( json.error != ""){
                PT.alert(json.error);
             }  else {
                // console.log(json.psuser_list);
                var psuser_list = json.psuser_list;
                var psuser_id_obj = $("#workbanch_search_form input[name='psuser_id']");
                var select_obj = $("#workbanch_search_form .department_staffs");

                var html = "";
                if(psuser_list.length >0){
                    html = template.render("id_staffs_selector_template",{"user_list":psuser_list});
                }
                select_obj.append(html);
                $.each(psuser_list, function (i, obj) {
                    if (obj.psuser_id==psuser_id_obj.val()) {
                        select_obj.val(psuser_id_obj.val());
                        return false;
                    }
                });
             }
        },
        get_account_report_dict_callback:function (account_report_dict) {
            for (var shop_id in account_report_dict) {
                $('table.user_table tbody tr[shop_id="'+shop_id+'"] div.account_report>ul').replaceWith(
                    '<ul class="ul_line">'+
                    '<li class="w70 tr pl5">'+account_report_dict[shop_id][0]['cost']+'</li>'+
                    '<li class="w80 tr pl3">'+account_report_dict[shop_id][0]['click']+'</li>'+
                    '<li class="w60 tr pl3">'+account_report_dict[shop_id][0]['cpc']+'</li>'+
                    '<li class="w60 tr pl5">'+account_report_dict[shop_id][0]['ctr']+'</li>'+
                    '<li class="w80 tr pl3">'+account_report_dict[shop_id][0]['pay']+'</li>'+
                    '<li class="w60 tr pl5">'+account_report_dict[shop_id][0]['conv']+'</li>'+
                    '<li class="w40 tr pl3">'+account_report_dict[shop_id][0]['roi']+'</li>'+
                    '</ul>'
                );
                PT.draw_trend_chart( 'account_graph_'+shop_id, account_report_dict[shop_id][1], account_report_dict[shop_id][2]);
            }
            $('#report_view').attr('loaded', '1');
        },
        display_port_info:function(nick, port_id, port_info){
            $('#id_nick').text(nick);
            $('#id_port_id_bak').val(port_id);

            $('#id_port_select').html('');//先清空
            for(key in port_info){
                $('#id_port_select').append('<option value="'+key+'">'+port_info[key]+'</option>');
            }
            $('#id_port_select').prepend('<option value="0">尚未分配</option>');

            $('#id_port_select').val(port_id);
            $('#id_edit_port_layer').modal();
        },
        get_my_reminder_callback: function (crm_reminder) {
            crm_reminder = $.map(crm_reminder, function (reminder) {
                return '<div class="m5">'+
                               '<a href="javascript:;" class="show_reminder" reminder_id="'+reminder._id+'">【提醒】'+reminder.content+'</a>'+
                           '</div>'
            });
            $('#crm_reminder').html(crm_reminder.join(''));
        },
        show_feedback_callback: function (data) {
            $('#id_show_info').html(template.render('feedback_template', {'data':data}));
            $('#id_show_info').modal();
        },
        show_ad_callback: function (data) {
            $('#id_show_info').html(template.render('ad_template', {'data':data}));
            $('#id_show_info').modal();
        },
        show_reminder_callback: function (data) {
            $('#id_show_info').html(template.render('reminder_template', {'data':data}));
            $('#id_show_info').modal();
        },
        show_pa_callback: function (data) {
            if (data.type=='appraise' && data.is_freeze==0) {
                PT.alert('好评积分已加');
                $('#crm_pa a[pa_id='+data._id+']').parent().remove();
            } else if (data.type=='virtual' && data.exchange_status==1) {
                PT.alert('积分已兑换');
                $('#crm_pa a[pa_id='+data._id+']').parent().remove();
            } else if (data.type=='gift' && data.logistics_state==1) {
                PT.alert('积分已兑换');
                $('#crm_pa a[pa_id='+data._id+']').parent().remove();
            } else {
                $('#id_show_info').html(template.render('pa_template', {'data':data}));
                $('#id_show_info').modal();
            }
        },
        mark_feedback_handled_callback: function (result) {
            if (result.err_msg) {
                PT.alert(result.err_msg);
            } else {
                $('#crm_feedback a[feedback_id='+result.feedback_id+']').parent().remove();
            }
        },
        mark_reminder_handled_callback: function (result) {
            if (result.err_msg) {
                PT.alert(result.err_msg);
            } else {
                $('#crm_reminder a[reminder_id='+result.reminder_id+']').parent().remove();
            }
        },
        mark_pa_handled_callback: function (result) {
            if (result.err_msg) {
                PT.alert(result.err_msg);
            } else {
                $('#crm_pa a[pa_id='+result.pa_id+']').parent().remove();
            }
        },
        get_allocation_record_callback: function (error, record_list) {
            if (error) {
                PT.alert('发生异常，联系研发');
            } else {
                $('#modal_allocation_record_list').modal('show');
                if (record_list.length > 0) {
                    $('#modal_allocation_record_list div.modal_body').html(template.render('template_allocation_record_list', {'record_list':record_list}));
                } else {
                    $('#modal_allocation_record_list div.modal_body').html('没有记录');
                }
            }
        },
        modify_memberorder_callback:function(error, result){
            var is_goldmember_msg = result.is_goldmember?'已确认为黄金会员':'已取消黄金会员';
            var this_div = $('tr[shop_id="'+result.shop_id+'"]').find('.modify-memberorder');
            this_div.attr("value",result.is_goldmember);
            if(error){
                PT.alert('发生异常，联系研发');
            } else {
                if(result.msg){
                    PT.light_msg('提醒','修改成功:'+is_goldmember_msg);
                }else{
                    PT.light_msg('提醒','修改失败');
                }
            }
            (function modifyMemberClass(){
                if(this_div.attr('value')){
                   this_div.removeClass('gold-member-n').addClass('gold-member-y');
                }else{
                    this_div.removeClass('gold-member-y').addClass('gold-member-n');
                }
            })();
        }
    }
}();
