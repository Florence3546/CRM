PT.namespace('CommonEvent');
PT.CommonEvent = function() {

    var init_dom = function() {

        var editors = {};

        //日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#id_subscribe_create_time',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#id_subscribe_start_time',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#id_subscribe_end_time',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '.time',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '#comment_create_time',
                timepicker: true,
                minuteSelect:true,
                closeOnTimeSelect : true
            });

            new Datetimepicker({
                start: '#modify_comment_time',
                timepicker: true,
                minuteSelect:true,
                closeOnTimeSelect : true
            });
        });

        require('pt/pt-editor-mini,node', function(editor, $) {

            $('.editor').each(function() {
                var id = $(this).attr('id');

                editors[id] = new editor({
                    render: '#' + id,
                    textareaAttrs: {
                        name: id
                    },
                    height:'200px'
                });
            });

        });

        $('#id_add_contact_layout').on('shown',function(e){
            var note_id;
            editors['id_contact_note'].render();

            if($('#editor_submit_contact:hidden').length){
                editors['id_contact_note'].value(' ');
            }else{
                note_id=$('#id_add_contact_layout').attr('contact_id');
                editors['id_contact_note'].value($('#contact_note_'+note_id).html());
            }
            $('#id_add_contact_layout .contact_prompt').hide();
            $('#id_add_contact_layout input[name=contact_visible][value=1]').attr('checked', true);

        });


        $('#id_add_subscribe_layout').on('shown',function(){
            editors['new_subscribe_note'].render();
            editors['new_subscribe_note'].value(' ');
        });

        $('#id_add_operate_layout').on('shown',function(){
            editors['id_operate_note'].render();
            if ($('#editor_submit_operate').is(':hidden')) {
	            editors['id_operate_note'].value('<p>已操作</p>');
            } else {
	            editors['id_operate_note'].value($('#operate_note_'+$('#id_add_operate_layout').attr('operate_id')).html());
            }
            $('#id_add_operate_layout .operate_prompt').hide();
            $('#id_add_operate_layout input[name=oper_visible][value=1]').attr('checked', true);
        });

        $('#id_add_reintro_layout').on('shown',function(){
            editors['id_reintro_note'].render();
            editors['id_reintro_note'].value(' ');
        });

        $('#id_add_comment_layout').on('shown',function(){
            editors['id_comment_note'].render();
            editors['id_comment_note'].value(' ');
        });

        $('#id_add_unsubscribe_layout').on('shown',function(){
            editors['id_unsubscribe_note'].render();
            editors['id_unsubscribe_note'].value(' ');
        });

        $('#id_add_pause_layout').on('shown',function(){
            editors['id_pause_note'].render();
            if ($('#editor_submit_pause').is(':hidden')) {
                editors['id_pause_note'].value(' ');
            } else {
                editors['id_pause_note'].value($('#pause_note_'+$('#id_add_pause_layout').attr('pause_id')).html());
            }
        });

        $('#div_contact_fail a[contact_type]').click(function () {
            if (!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            PT.DBCLICK_ENABLED = false;
            var submit_obj = new Object();
            submit_obj.shop_id = parseInt($(this).closest('tr[shop_id]').attr('shop_id'));
            submit_obj.note = '未回复';
            submit_obj.contact_type = $(this).attr('contact_type');
            submit_obj.visible = 0;
            submit_obj.xf_flag = 1;
            PT.show_loading('正在保存');
            PT.sendDajax({
                'function': 'ncrm_save_contact',
                'contact': $.toJSON(submit_obj),
                'call_back': 'PT.CommonEvent.save_contact_call_back'
            });

            setTimeout(function() {
                PT.DBCLICK_ENABLED = true;
            }, 300);
        });

        $('.contact').on('click', function() {
            var last_shop_id = $('#id_contact_shop_id').val();
            var cur_shop_id = $(this).parent().attr('shop_id');
            if (last_shop_id != cur_shop_id){
                $('#id_contact_shop_id').val(cur_shop_id);
                $('input[name=contact_type]:eq(0)').attr('checked', true);
                $('#id_contact_isinitiative').attr('checked', true);
                $('#id_contact_intention').val('');
            }

            $('#submit_contact').show();
            $('#editor_submit_contact').hide();

            $('#id_add_contact_layout').modal();

        });


        $('#submit_contact').on('click', function() {
            if (!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            PT.DBCLICK_ENABLED = false;

            var submit_obj = new Object();
            submit_obj.shop_id = parseInt($('#id_contact_shop_id').val());
            submit_obj.contact_type = $('input[name=contact_type]:checked').val();
            //submit_obj.create_time = $('#id_contact_time').val();
            //submit_obj.end_time = $('#id_contact_end_time').val();
            submit_obj.is_initiative = $('#id_contact_isinitiative').attr('checked') == "checked" ? 1 : 0;
            submit_obj.note = editors['id_contact_note'].value();
            submit_obj.intention = $('#id_contact_intention').val();
            submit_obj.visible = parseInt($('input[name=contact_visible]:checked').val());
            submit_obj.xf_flag = parseInt($('input[name=contact_xf_flag]:checked').val());

            var note_text = $.trim($(submit_obj.note).text());
            if (note_text==''){
                PT.alert('请输入备注');
                PT.DBCLICK_ENABLED = true;
                return false;
            } else if (note_text.length<3 && submit_obj.visible==1) {
                $('#id_add_contact_layout .contact_prompt').show();
                PT.DBCLICK_ENABLED = true;
                return false;
            }
            PT.show_loading('正在保存');
            PT.sendDajax({
                'function': 'ncrm_save_contact',
                'contact': $.toJSON(submit_obj),
                'call_back': 'PT.CommonEvent.save_contact_call_back'
            });

            setTimeout(function() {
                PT.DBCLICK_ENABLED = true;
            }, 300);
        });


        $('.subscribe').on('click', function() {
            var last_shop_id = $('#id_subscribe_shop_id').val();
            var cur_shop_id = $(this).parent().attr('shop_id');
            if (last_shop_id != cur_shop_id){
                $('#id_subscribe_shop_id').val(cur_shop_id);
                $("input[link='#id_subscribe_sale_user']").val('');
                $('#id_subscribe_sale_user').val();
                $('input[name=biz_type]:eq(0)').attr('checked', 'checked');
                $('#id_subscribe_article_code option:eq(0)').attr('selected', 'selected');
                $('#id_subscribe_source_type option:eq(0)').attr('selected', 'selected');
                $("#id_subscribe_pay").val('');
                $("#id_subscribe_start_time").val('');
                $("#id_subscribe_end_time").val('');

                $("#is_valid_flag").text('');
            }
            $('#id_add_subscribe_layout').modal();
        });


        $('#add_subscribe').on('click', function() {
            var sale_id = parseInt($('#id_subscribe_sale_user').val());
            var subscribe_pay = $("#id_subscribe_pay").val();
            var category_obj = $("#id_subscribe_category option:selected");
            if (!sale_id) {
                PT.alert("请填写签单人！");
                return false;
            }
            if (!category_obj.val()) {
                PT.alert("请选择订单类型！");
                return false;
            }
            if (!subscribe_pay) {
                PT.alert("请输入成交金额！");
                return false;
            }
            if (!/(\d|\.)+/.test(subscribe_pay)){
                PT.alert("金额输入错误！");
                return false;
            }
            if (Number(subscribe_pay)<=0 && category_obj.val()!='other') {
                PT.alert("非【补单】订单的订购金额必须大于0！");
                return false;
            }
            var source_type = $('#id_subscribe_source_type').val();
//            var option_obj = $("#id_subscribe_article_code option:selected");
            var start_date = $("#id_subscribe_start_time").val();
            var end_date = $("#id_subscribe_end_time").val();
            var create_time = $('#id_subscribe_create_time').val();
            if (!create_time) {
                PT.alert('请选择订购时间');
                return false;
            }
            if(parseInt(source_type) > 0 ){
                if (start_date && end_date && start_date < end_date) {
                    var submit_obj = new Object();
                    submit_obj.shop_id = parseInt($('#id_subscribe_shop_id').val());
                    submit_obj.psuser_id = sale_id;
                    submit_obj.biz_type = $('input[type=radio][name=biz_type]:checked').val();
                    submit_obj.source_type = source_type ;
                    submit_obj.category = category_obj.val();
                    submit_obj.article_code = category_obj.attr('article_code');
                    submit_obj.item_code = submit_obj.article_code;
                    //submit_obj.article_name = option_obj.text().replace('/\s/g','');
                    submit_obj.pay = parseInt(parseFloat(subscribe_pay)*100);
                    submit_obj.create_time =  create_time;
                    submit_obj.start_date =  start_date;
                    submit_obj.end_date =  end_date;
                    submit_obj.note = editors['new_subscribe_note'].value();
                    submit_obj.visible = parseInt($('input[name=subscribe_visible]:checked').val());
                    submit_obj.xf_flag = parseInt($('input[name=subscribe_xf_flag]:checked').val());
                    submit_obj.pay_type = parseInt($('#id_subscribe_pay_type').val());
                    submit_obj.pay_type_no = $.trim($('#subscribe_pay_type_no').val());
                    var receiver_cn = $.trim($('#subscribe_receiver_cn').val());
                    if (submit_obj.pay_type>=2 && submit_obj.pay_type<=4) {
                        if (!submit_obj.pay_type_no) {
                            PT.alert('支付宝和银行付款时必须填写付款信息');
                            return false;
                        }
                        if (!receiver_cn) {
                            PT.alert('支付宝和银行付款时必须填写户主姓名');
                            return false;
                        }
                    }
                    submit_obj.pay_type_no += '__'+receiver_cn;
                    // to_add 2017-05-12
                    submit_obj.has_contract = $("input[name=subscribe_has_contract]:checked").val();
                    submit_obj.chat_file_path = $("#chat_file_path").val();
                    PT.show_loading('正在保存');
                    PT.sendDajax({
                        'function': 'ncrm_save_new_subscribe',
                        'subscribe': $.toJSON(submit_obj),
                        'call_back': 'PT.CommonEvent.save_subscribe_call_back'
                    });
                } else {
                    PT.alert("请选择正确的起止时间！");
                    return false;
                }
            } else{
                PT.alert("请选择订单来源！");
                return false;
            }
        });

        // 聊天文件选择事件绑定
        $("#chat_file_path").on('click',function () {
            $("#subscribe_chat_file").click();//触发文件选择
        });
        // 文件选择后，将当前文件路径显示到输入框
        $("#subscribe_chat_file").on("change",function(){
            $("#chat_file_path").val($("#subscribe_chat_file").val());
        });
        // ajax文件上传
        $("#up_chat_btn").on("click",function(){
            if(!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            var form_data = new FormData(), file = $("#subscribe_chat_file")[0].files[0];
            if(file == undefined ){
                PT.alert('请先选择要上传的文件');
                $("#subscribe_chat_file").val('');
                $("#chat_file_path").val('');
                return false;
            }
            // 验证文件相关参数
            if (file.size > 1024 * 1024 * 10) {
                PT.alert('文件大小不能超过10M');
                $("#subscribe_chat_file").val('');
                $("#chat_file_path").val('');
                return false;
            }
            var extStart = file.name.lastIndexOf(".");
            var ext = file.name.substring(extStart, file.name.length).toUpperCase();
            if (ext == ".EXE"){
                PT.alert('请不要上传可执行文件');
                $("#subscribe_chat_file").val('');
                $("#chat_file_path").val('');
                return false;
            }
            // 上传文件
            form_data.append('up_file', file);
            form_data.append('up_path', "chat_file/");
            PT.show_loading('正在上件文件');
            $.ajax({
                url: '/ncrm/upload_file/',
                type: 'POST',
                cache: false,
                data: form_data,
                processData: false,
                contentType: false,
                success: function(data) {
                     PT.hide_loading();
                     if(data.status==1){
                         $("#chat_file_path").val(data.file_path);
                         PT.alert(data.msg);
                     }else{
                          PT.alert(data.msg);
                     }
                },
                error: function() {
                    PT.hide_loading();
                    PT.alert('上传聊天文件失败');
                    $("#subscribe_chat_file").val('');
                    $("#chat_file_path").val('');
                    return false;
                }
            });
        });


        $('.operate').click(function(){
             var last_shop_id = $('#id_operate_shop_id').val();
             var cur_shop_id = $(this).parent().attr('shop_id');
             if (last_shop_id != cur_shop_id){
                 $('#id_operate_shop_id').val(cur_shop_id);
                 if($('#workbench_type').val()=='hmi'){ //人机结合
                    $('input[name=oper_type]:eq(1)').attr('checked', 'checked');
                 }else{
                    $('input[name=oper_type]:eq(0)').attr('checked', 'checked');
                 }
             }

            $('#submit_operate').show();
            $('#editor_submit_operate').hide();
            $('#id_add_operate_layout').modal();
        });

        $('#submit_operate').click(function(){
            if (!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            PT.DBCLICK_ENABLED = false;
            var submit_obj = new Object();
            submit_obj.shop_id = parseInt($('#id_operate_shop_id').val());
            submit_obj.oper_type = $('input[name=oper_type]:checked').val();
            submit_obj.note = editors['id_operate_note'].value();
            submit_obj.visible = parseInt($('input[name=oper_visible]:checked').val());

            var note_text = $.trim($(submit_obj.note).text());
            if (note_text==''){
                PT.alert('请输入备注');
                PT.DBCLICK_ENABLED = true;
                return false;
            } else if (note_text.length<3 && submit_obj.visible==1) {
                $('#id_add_operate_layout .operate_prompt').show();
                PT.DBCLICK_ENABLED = true;
                return false;
            }
            PT.show_loading('正在保存');
            PT.sendDajax({
                'function': 'ncrm_save_operate',
                'operate': $.toJSON(submit_obj),
                'call_back': 'PT.CommonEvent.save_operate_call_back'
            });

            setTimeout(function() {
                PT.DBCLICK_ENABLED = true;
            }, 300);
        });

        $('.reintro').click(function(){
            var last_shop_id = $('#id_reintro_shop_id').val();
            var cur_shop_id = $(this).parent().attr('shop_id');
            if (last_shop_id != cur_shop_id){
                 $('#id_reintro_shop_id').val(cur_shop_id);
                 $('input[name=reintro_type]:eq(0)').attr('checked', 'checked');
            }
            PT.show_loading('正在加载');
            PT.sendDajax({'function':'ncrm_get_psuser_list', 'namespace':'CommonEvent.showreintro_callback'});
        });

        $('#submit_reintro').click(function(){
            var submit_obj = new Object();
            submit_obj.shop_id = parseInt($('#id_reintro_shop_id').val());
            submit_obj.reintro_type = $('input[name=reintro_type]:checked').val();
            submit_obj.note = $.trim(editors['id_reintro_note'].value());
            submit_obj.receiver_id = parseInt($('#id_select_receiver').val());
            submit_obj.visible = parseInt($('input[name=reintro_visible]:checked').val());
            var note_text = $.trim($(submit_obj.note).text());
            if(note_text==''){
                PT.alert('请输入备注');
                return false;
            }
            if(isNaN(submit_obj.receiver_id)){
                PT.alert('请填写接收人');
                return false;
            }

            PT.show_loading('正在保存');
            PT.sendDajax({
                'function': 'ncrm_save_reintro',
                'obj': $.toJSON(submit_obj)
            });
        });

        $('.comment').click(function(){
            // var order_title_list=[],html='<option value="0">请选择</option>',i=0;
            var last_shop_id = $('#id_comment_shop_id').val();
            var cur_shop_id = $(this).parent().attr('shop_id');
            $('#comment_current_version').val($(this).parent().attr('current_version'));
            if (last_shop_id != cur_shop_id){
                 $('#id_comment_shop_id').val(cur_shop_id);
            }

            $('#comment_type').val('0').change();
            var ct  = new Date();
            ct.setTime(ct.getTime()-1000*60*10);
            $('#comment_create_time').val(ct.format('yyyy-MM-dd hh:mm'));

            $('#id_add_comment_layout').modal();
        });

        $('#submit_comment').click(function() {
            var submit_obj = {}, type = $(':radio[name=comment_type]:checked').val(), type0;

            submit_obj.shop_id = parseInt($('#id_comment_shop_id').val());
            submit_obj.article_code = $('[name=comment_article_code]:checked').val();
            submit_obj.note = $.trim(editors['id_comment_note'].value());
            submit_obj.create_time = $('#comment_create_time').val();
            submit_obj.current_version = $('#comment_current_version').val();

            if($('#top_comment_times').val()!=''){
                submit_obj.top_comment_times = $('#top_comment_times').val();
            }

            if($('#modify_comment_time').val()!=''){
                submit_obj.modify_comment_time = $('#modify_comment_time').val();
            }

            if(submit_obj.create_time==''){
                PT.alert('请填写评价时间');
                return false;
            }

            if (type) {
                type0 = type.slice(0, 1);
            } else {
                PT.alert('请选择正确的评价类型');
                return false;
            }

            if (type == '120' && (submit_obj.top_comment_times == ''||isNaN(submit_obj.top_comment_times))) {
                PT.alert('请输入正确的踩评名次');
                return false;
            }

            if (type0 == '3' && submit_obj.modify_comment_time == '') {
                PT.alert('请输入改评时间');
                return false;
            }

            var note_text = $.trim($(submit_obj.note).text());
            if(note_text=='' && type0!='1'){
                PT.alert('请输入备注');
                return false;
            }

            submit_obj.comment_type = parseInt(type);
            //submit_obj.visible = parseInt($('input[name=comment_visible]:checked').val());

            PT.show_loading('正在保存');
            PT.sendDajax({
                'function': 'ncrm_save_comment',
                'obj': $.toJSON(submit_obj),
                'call_back':'PT.CommonEvent.save_comment_callback'
            });
        });

//        $('.unsubscribe').click(function(){
//            $('#id_unsubscribe_shop_id').val($(this).parent().attr('shop_id'));
//            var order_obj=eval('('+$(this).attr('data-order')+')');
//            var html='<option value="">--请选择--</option>';
//            for(i in order_obj){
//                html+='<option value="'+i+'">'+order_obj[i]+'</option>';
//            }
//            if(html!=''){
//                $('#unsubscribe_event_id').html(html);
//                $('#id_add_unsubscribe_layout').modal();
//            }else{
//                PT.alert("没有有效订单");
//            }
//        });

        $('#id_add_unsubscribe_layout [name=refund_style]').click(function () {
            if (this.value=='1') {
                $(':checkbox[name=frozen_kcjl], :checkbox[name=unmnt_all]').attr({'checked':true});
            } else {
                $(':checkbox[name=frozen_kcjl], :checkbox[name=unmnt_all]').attr('checked', false);
            }
        });

        //$('#add_refund_apportion').click(function () {
        //    $('#ul_refund_apportion').append(
        //        '<li class="dib mt10 w250">'+
        //        '<input type="text" class="w80 f12" name="refund_staff" placeholder="员工姓名"> 分摊 '+
        //        '<input type="text" class="w60 f12" name="refund_money" placeholder="金额"> 元 '+
        //        '<a class="remove_refund_apportion" href="javascript:;"><i class="iconfont gray">&#xe67a;</i></a>'+
        //        '</li>'
        //    );
        //})
        //
        //$('#ul_refund_apportion').on('click', '.remove_refund_apportion', function () {
        //    $(this).parent('li').remove();
        //})

        $('#submit_unsubscribe').click(function(){
            var submit_obj = {},
                unsubscribe_event_pay = Number($('#id_add_unsubscribe_layout').attr('unsubscribe_event_pay'))*100;
            submit_obj.shop_id = parseInt($('#id_unsubscribe_shop_id').val());
            submit_obj.event_id = parseInt($('#unsubscribe_event_id').val());
            submit_obj.refund = parseInt($('#unsubscribe_refund').val()*100);

            // 退款原因 多选
            var refund_reason_list = [];
            $('#id_add_unsubscribe_layout :checked[name=refund_reason]').each(function () {
                refund_reason_list.push(parseInt($(this).val()));
            });
            console.log(refund_reason_list);
            // submit_obj.refund_reason = parseInt($('#id_add_unsubscribe_layout :checked[name=refund_reason]').val());
            submit_obj.refund_reason = refund_reason_list;

            //submit_obj.refund_type = parseInt($('#id_add_unsubscribe_layout :checked[name=refund_type]').val());
            submit_obj.refund_style = parseInt($('#id_add_unsubscribe_layout :checked[name=refund_style]').val());
            submit_obj.refund_info = $('#unsubscribe_refund_info').val();
            submit_obj.frozen_kcjl = $('#id_add_unsubscribe_layout :checkbox[name=frozen_kcjl]').prop('checked')?1:0;
            submit_obj.note = $.trim(editors['id_unsubscribe_note'].value());
            submit_obj.status = submit_obj.refund_style==2?1:2;
            var receiver_cn = $.trim($('#unsubscribe_receiver_cn').val());
            submit_obj.cashier_id = Number($('#unsubscribe_cashier_id').val());
            submit_obj.reimburse_dpt = $.trim($('#unsubscribe_cashier_id>option:checked').attr('dept'));
            submit_obj.saler_id = parseInt($('#unsubscribe_saler_id').val());
            if ($('#id_add_unsubscribe_layout').attr('auto_apportion')) {
                submit_obj.saler_apportion = submit_obj.refund;
                submit_obj.server_apportion = 0;
                submit_obj.saler_dpt_apportion = 0;
                submit_obj.server_dpt_apportion = 0;
                submit_obj.other_apportion = 0;
                submit_obj.pm_apportion = 0;
            } else {
                submit_obj.saler_apportion = parseInt($('#unsubscribe_saler_apportion').val()*100);
                submit_obj.server_apportion = parseInt($('#unsubscribe_server_apportion').val()*100);
                submit_obj.saler_dpt_apportion = parseInt($('#unsubscribe_saler_dpt_apportion').val()*100);
                submit_obj.server_dpt_apportion = parseInt($('#unsubscribe_server_dpt_apportion').val()*100);
                submit_obj.other_apportion = parseInt($('#unsubscribe_other_apportion').val()*100);
                submit_obj.pm_apportion = parseInt($('#unsubscribe_pm_apportion').val()*100);
            }
            if (!submit_obj.event_id) {
                PT.alert('必须选中要退款的订单');
                return false;
            }
            if (isNaN(submit_obj.refund) || submit_obj.refund<=0) {
                PT.alert('退款金额未填写或格式不正确');
                return false;
            }
            //if (submit_obj.refund_type!=5 && submit_obj.refund>unsubscribe_event_pay) {
            if (submit_obj.refund_reason!=6 && submit_obj.refund>unsubscribe_event_pay) {
                PT.alert('退款金额不能大于订单实付金额');
                return false;
            }
            //if (isNaN(submit_obj.refund_type)) {
            //    PT.alert('退款类型不能为空');
            //    return false;
            //}
            // liuhuan
            // if (isNaN(submit_obj.refund_reason)) {
            //     PT.alert('退款原因不能为空');
            //     return false;
            // }
            if (submit_obj.refund_reason.length == 0) {
                PT.alert('退款原因不能为空,可多选!');
                return false;
            }

            if (submit_obj.refund_reason==5 && isNaN(submit_obj.saler_id)) {
                PT.alert('标记赠送时必须指定签单人');
                return false;
            }
            if (isNaN(submit_obj.refund_style)) {
                PT.alert('退款方式不能为空');
                return false;
            }
            if (submit_obj.refund_style>=2 && submit_obj.refund_style<=4) {
                if (!submit_obj.refund_info) {
                    PT.alert('支付宝和银行退款时必须填写退款信息');
                    return false;
                }
                if (!receiver_cn) {
                    PT.alert('支付宝和银行退款时必须填写户主姓名');
                    return false;
                }
            }
            if (submit_obj.refund_style==5 && !receiver_cn) {
                PT.alert('现金退款时必须填写户主姓名');
                return false;
            }
            submit_obj.refund_info += '__' + receiver_cn;
            if (isNaN(submit_obj.server_apportion) || isNaN(submit_obj.saler_apportion) || isNaN(submit_obj.other_apportion) || isNaN(submit_obj.pm_apportion) || isNaN(submit_obj.saler_dpt_apportion) || isNaN(submit_obj.server_dpt_apportion)) {
                PT.alert('退款分摊金额格式不正确');
                return false;
            }
            if (submit_obj.server_apportion + submit_obj.saler_apportion + submit_obj.other_apportion + submit_obj.pm_apportion + submit_obj.saler_dpt_apportion + submit_obj.server_dpt_apportion != submit_obj.refund) {
                PT.alert('退款分摊金额之和与总额不一致');
                return false;
            }
            if (submit_obj.refund_style==2 && !submit_obj.cashier_id) {
                PT.alert('支付宝退款时必须指定经办人');
                return false;
            }
            if (submit_obj.note=='') {
                PT.alert('备注不能为空');
                return false;
            }
            PT.show_loading('正在保存');
            PT.sendDajax({
                'function': 'ncrm_save_unsubscribe',
                'obj': $.toJSON(submit_obj),
                'nick': $('#subscribe_menu').attr('nick'),
                'unknown_subscribe_flag': $('#unknown_subscribe_flag').val(),
                'unmnt_all': $('#id_add_unsubscribe_layout :checkbox[name=unmnt_all]').prop('checked')?1:0,
                'call_back': 'PT.CommonEvent.save_unsubscribe_call_back'
            });
        });

//        $('.pause').click(function () {
//            $('#id_pause_shop_id').val($(this).parent().attr('shop_id'));
//            var order_obj=eval('('+$(this).siblings('.unsubscribe').attr('data-order')+')');
//            var html='<option value="">--请选择--</option>';
//            for(i in order_obj){
//                html+='<option value="'+i+'">'+order_obj[i]+'</option>';
//            }
//            if(html!=''){
//                $('#pause_event_id').html(html).attr('disabled', false);
//                var ct = new Date();
//                $('#pause_create_time').val(ct.format('yyyy-MM-dd hh:mm:ss'));
//                $('#proceed_date').val('');
//	            $('#submit_pause').show();
//	            $('#editor_submit_pause').hide();
//	            $('#pause_event_id').show();
//	            $('#pause_event_id0').hide();
//                $('#id_add_pause_layout').modal();
//            }else{
//                PT.alert("没有有效订单");
//            }
//        });

        $('#submit_pause').click(function () {
            var submit_obj = {};
            submit_obj.shop_id = parseInt($('#id_pause_shop_id').val());
            submit_obj.event_id = parseInt($('#pause_event_id').val());
            submit_obj.pause_create_time = $('#pause_create_time').val();
            submit_obj.note = $.trim(editors['id_pause_note'].value());
            if(!submit_obj.event_id){
                PT.alert('必须选中要暂停的订单');
                return false;
            }
            if(submit_obj.note==''){
                PT.alert('备注不能为空');
                return false;
            }
            PT.show_loading('正在保存');
            PT.sendDajax({
                'function': 'ncrm_save_pause',
                'obj': $.toJSON(submit_obj),
                'call_back': 'PT.CommonEvent.save_pause_call_back'
            });
        });

        //创建客户群
        $('#create_client_group_submit').click(function(){
            var client_group_name,psuser_id,client_group_note;
            psuser_id=$('#psuser_id').val();
            client_group_name=$('#client_group_name').val();
            client_group_note=$('#client_group_note').val();
            if(client_group_name){
                PT.sendDajax({
                    'function': 'ncrm_creaete_client_group',
                    'psuser_id': psuser_id,
                    'title': client_group_name,
                    'note':client_group_note,
                    'is_manual':1,
                    'call_back': 'PT.CommonEvent.creaete_client_group_back'
                });
                $('#create_client_group').modal('hide');
                PT.show_loading('正在创建');
            }else{
                PT.alert('请输入客户群名称');
            }
        });

        //客户群重命名
        $('#rename_client_group_submit').click(function(){
            var name,client_id,note;
            name=$('#rename_client_group_value').val();
            note=$('#renote_client_group_value').val();
            client_id=$('#rename_client_group input[name=client_id]').val();

            PT.sendDajax({
                'function': 'ncrm_rename_client_group',
                'client_id': client_id,
                'title':name,
                'note':note,
                'call_back': 'PT.CommonEvent.rename_client_group_back'
            });

            $('#rename_client_group').modal('hide');
        });

        //同步名称
        $('#client-group-list .rename').click(function(){
            var name,client_id;
            name=$(this).attr('data-value');
            client_id=$(this).attr('client_id');
            client_note=$(this).attr('client_note');

            $('#rename_client_group input[name=client_id]').val(client_id);
            $('#rename_client_group_value').val(name);
            $('#renote_client_group_value').val(client_note);
        });

        //删除客户群
        $('#client-group-list .delete').click(function(){
            var client_id=$(this).attr('client_id');
            PT.confirm('你确定要删除这个客户群吗？',function(){
                PT.sendDajax({
                    'function': 'ncrm_delete_client_group',
                    'client_id': client_id,
                    'call_back': 'PT.CommonEvent.delete_client_group_back'
                });
            })
        });

        //添加客户
        $('.add_client').click(function(){

            $('#id_list_textarea').attr('client_group_id',$(this).attr('data-id'));
            $("#id_manual_add_customer_layout").modal();
        });

        //切换客户群
        $('#client-group-list input[type=checkbox]').change(function(){
            if(this.checked){
//                var form_obj = $(this).parents('form:first');
//                form_obj.find("input[name=search_type]").val("query_client_group");
//                form_obj.submit();
                PT.show_loading("正在搜索客户群");
                $("#workbanch_search_form input[name=search_type]").val("query_client_group");
                //$("#client-group-list :checkbox").attr('checked', false);
                $('#reset_form').click();
                $(this).attr('checked', true);
                $("#workbanch_search_form").submit();
            }
        });

        //切换我的所有客户
        $('#client-group-list #search_query').click(function(){
            PT.show_loading("正在查找我的客户");
            var form_obj = $(this).parents('form:first');
            //form_obj[0].reset();
            form_obj.find("input[name=search_type]").val("query_mycustomers");
            form_obj.submit();
        });

        //过滤手机号
        $('#has_phone').change(function () {
	        if (this.value=='2') {
		        $('#phone').val('');
	        }
        });

        //售后搜全局
        $('#search_global').click(function(){
            PT.show_loading("正在进行全局搜索");
            var form_obj = $(this).parents('form:first');
            form_obj.find("input[name=search_type]").val("query_global");
            form_obj.submit();
        });

        //售后搜全局
        $('#search_my_customers').click(function(){
            PT.show_loading("正在进行我的客户搜索");
            var form_obj = $(this).parents('form:first');
            form_obj.find("input[name=search_type]").val("query_mycustomers");
            form_obj.submit();
        });

        //售后搜已选客户群
        $('#search_checked_client').click(function(){
            PT.show_loading("正在进行客户群搜索");
            var form_obj = $(this).parents('form:first');
            form_obj.find("input[name=search_type]").val("query_client_group");
            form_obj.submit();
        });

        $('.client_group_input').change(function(){
            var client_id=$(this).val();
            var shop_id=$(this).parents('tr:first').attr('shop_id');
            PT.sendDajax({
                'function': 'ncrm_add_or_del_client',
                'client_id': client_id,
                'shop_ids':'['+shop_id+']',
                'mode':this.checked?'add':'del',
                'call_back': 'PT.CommonEvent.change_client_group_back'
            });
        });

        //修改联系事件
        $(document).on('click','.editor_contact',function(){
            var info=$(this).attr('data-info'),obj;
            obj=$.parseJSON(info);

            $('#submit_contact').hide();
            $('#editor_submit_contact').show();

            $('#id_add_contact_layout').attr('contact_id',obj.id);
            $('#id_add_contact_layout input[name=contact_type][value='+obj.type+']').attr('checked', true);
            $('#id_add_contact_layout input[name=contact_xf_flag][value='+obj.xf_flag+']').attr('checked', true);

            $('#id_add_contact_layout').modal();
        });

        //修改操作事件
        $(document).on('click','.editor_operate',function(){
            var info=$(this).attr('data-info'),obj;
            obj=$.parseJSON(info);

            $('#submit_operate').hide();
            $('#editor_submit_operate').show();

            $('#id_add_operate_layout').attr('operate_id',obj.id);
            $('#id_add_operate_layout input[name=oper_type][value='+obj.type+']').attr('checked', 'checked');

            $('#id_add_operate_layout').modal();
        });

        //修改暂停事件
        $(document).on('click','.editor_pause',function(){
            var info=$(this).attr('data-info'),obj;
            obj=$.parseJSON(info);

            $('#submit_pause').hide();
            $('#editor_submit_pause').show();

            $('#id_add_pause_layout').attr('pause_id', obj.id);
//            $('#pause_event_id').hide();
//            $('#pause_event_id0').show();
            var order_obj = $(this).closest('tr[shop_id]').find('.order_info .ul_line[sub_id='+obj.event_id+']');
            $('#pause_event_descr').html(order_obj.find('li:eq(3)').text()+' '+order_obj.find('li:eq(1)').text()+' '+order_obj.find('li:eq(2)').text()+' '+order_obj.find('li:eq(0)').text()+' '+order_obj.find('li:eq(5)').text()+'元');
            $('#pause_create_time').val(obj.create_time);
            $('#proceed_date').val(obj.proceed_date);
            $('#id_add_pause_layout').modal();
        });

        //开启暂停事件
        $(document).on('click','.proceed',function(){
            $.fancybox.close();
            $('#proceed_date2').val(new Date().format('yyyy-MM-dd hh:mm:ss'));
            $('#submit_proceed').attr({
                'pause_id': $(this).attr('pause_id'),
                'pause_date': $(this).attr('pause_date'),
                'shop_id': $(this).attr('shop_id'),
                'sub_id': $(this).attr('sub_id'),
            });
            $('#id_proceed_layout').modal();
        });
        $('#submit_proceed').click(function () {
            PT.sendDajax({
                'function': 'ncrm_cancel_pause',
                'pause_id': $(this).attr('pause_id'),
                'pause_date': $(this).attr('pause_date'),
                'shop_id': $(this).attr('shop_id'),
                'sub_id': $(this).attr('sub_id'),
                'proceed_date': $('#proceed_date2').val(),
                'call_back': 'PT.CommonEvent.cancel_pause_back'
            });
        });

        //撤销暂停开启事件
        $(document).on('click', '.del_proceed', function () {
            PT.sendDajax({
                'function': 'ncrm_del_proceed',
                'pause_id': $(this).attr('pause_id'),
                'call_back': 'PT.CommonEvent.del_proceed_back'
            });
        });

        //当事件编辑框隐藏式，同时隐藏富文本编辑器添加超链接时的浮动框
        $('#id_add_contact_layout').on('hidden', function () {
            $(".ks-editor-bubble-url").parent().parent().hide();
        });

        $('#id_add_comment_layout').on('hidden', function () {
            $(".ks-editor-bubble-url").parent().parent().hide();
        });

        $('#id_add_reintro_layout').on('hidden', function () {
            $(".ks-editor-bubble-url").parent().parent().hide();
        });

        $('#id_add_unsubscribe_layout').on('hidden', function () {
            $(".ks-editor-bubble-url").parent().parent().hide();
        });

        $('#id_add_pause_layout').on('hidden', function () {
            $(".ks-editor-bubble-url").parent().parent().hide();
        });

        //修改联系事件提交事件
        $('#editor_submit_contact').click(function(){
            if (!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            PT.DBCLICK_ENABLED = false;
            var submit_obj = new Object();
            submit_obj.contact_id=$('#id_add_contact_layout').attr('contact_id');
            submit_obj.contact_type = $('#id_add_contact_layout  input[name=contact_type]:checked').val();
            //submit_obj.is_initiative = $('#id_contact_isinitiative').attr('checked') == "checked" ? 1 : 0;
            submit_obj.note = editors['id_contact_note'].value();
            //submit_obj.intention = $('#id_contact_intention').val();
            submit_obj.visible = parseInt($('input[name=contact_visible]:checked').val());
            submit_obj.xf_flag = parseInt($('input[name=contact_xf_flag]:checked').val());

            var note_text = $.trim($(submit_obj.note).text());
            if (note_text==''){
                PT.alert('请输入备注');
                PT.DBCLICK_ENABLED = true;
                return false;
            } else if (note_text.length<3 && submit_obj.visible==1) {
                $('#id_add_contact_layout .contact_prompt').show();
                PT.DBCLICK_ENABLED = true;
                return false;
            }
            PT.sendDajax({
                'function': 'ncrm_editor_contact',
                'contact': $.toJSON(submit_obj),
                'call_back': 'PT.CommonEvent.editor_contact_back'
            });

            setTimeout(function() {
                PT.DBCLICK_ENABLED = true;
            }, 300);
        });

        //修改操作事件提交事件
        $('#editor_submit_operate').click(function(){
            if (!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            PT.DBCLICK_ENABLED = false;
            var submit_obj = new Object();
            submit_obj.operate_id=$('#id_add_operate_layout').attr('operate_id');
            submit_obj.oper_type = $('#id_add_operate_layout  input[name=oper_type]:checked').val();
            submit_obj.note = editors['id_operate_note'].value();
            submit_obj.visible = parseInt($('input[name=oper_visible]:checked').val());

            var note_text = $.trim($(submit_obj.note).text());
            if (note_text==''){
                PT.alert('请输入备注');
                PT.DBCLICK_ENABLED = true;
                return false;
            } else if (note_text.length<3 && submit_obj.visible==1) {
                $('#id_add_operate_layout .operate_prompt').show();
                PT.DBCLICK_ENABLED = true;
                return false;
            }

            PT.sendDajax({
                'function': 'ncrm_editor_operate',
                'operate': $.toJSON(submit_obj),
                'call_back': 'PT.CommonEvent.editor_operate_back'
            });

            setTimeout(function() {
                PT.DBCLICK_ENABLED = true;
            }, 300);
        });

        //修改联系事件提交事件
        $('#editor_submit_pause').click(function(){
            if (!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            PT.DBCLICK_ENABLED = false;
            var submit_obj = new Object();
            submit_obj.pause_id=$('#id_add_pause_layout').attr('pause_id');
            submit_obj.note = editors['id_pause_note'].value();

            var note_text = $.trim($(submit_obj.note).text());
            if (note_text==''){
                PT.alert('请输入备注');
                PT.DBCLICK_ENABLED = true;
                return false;
            }
            PT.sendDajax({
                'function': 'ncrm_editor_pause',
                'pause': $.toJSON(submit_obj),
                'call_back': 'PT.CommonEvent.editor_pause_back'
            });

            setTimeout(function() {
                PT.DBCLICK_ENABLED = true;
            }, 300);
        });

        //删除联系事件
        $(document).on('click','.del_contact',function(){
            var info=$(this).attr('data-info'),obj;
            obj=$.parseJSON(info);
            PT.sendDajax({
                'function': 'ncrm_del_contact',
                'contact_id': obj.id,
                'shop_id': $(this).closest('tr[shop_id]').attr('shop_id')
            });
        });

        //删除操作事件
        $(document).on('click','.del_operate',function(){
            var info=$(this).attr('data-info'),obj;
            obj=$.parseJSON(info);
            PT.sendDajax({
                'function': 'ncrm_del_operate',
                'operate_id': obj.id
            });
        });

        //删除暂停事件
        $(document).on('click','.del_pause',function(){
            var info=$(this).attr('data-info'),obj;
            obj=$.parseJSON(info);
            PT.sendDajax({
                'function': 'ncrm_del_pause',
                'pause_id': obj.id
            });
        });

        //评论类型
        $(':radio[name=comment_type]').click(function () {
            if (this.value=='120') {
                $('#top_comment_time_box').show();
            } else {
                $('#top_comment_time_box').hide();
                $('#top_comment_times').val('');
            }
	        if (Number(this.value)/100>3) {
	            $('#modify_comment_time_box').show();
	        } else {
                $('#modify_comment_time_box').hide();
                $('#modify_comment_time').val('');
	        }
        });

        //录入评论一级联动
//        $('#comment_type').change(function(){
//            var value=$(this).val(), obj1=$('#comment_type1'), obj2=$('#comment_type2');
//            switch (value) {
//                case '1':
//                    obj1.show();
//                    obj2.val('0').hide().change();
//                    $('#modify_comment_time_box').hide();
//                    $('#modify_comment_time').val('');
//                    break;
//                case '3':
//                    $('#comment_type2').show();
//                    $('#modify_comment_time_box').show();
//                    obj1.val('0').hide().change();
//                    break;
//                default:
//                    obj1.val('0').hide().change();
//                    obj2.val('0').hide().change();
//                    $('#modify_comment_time_box').hide();
//                    $('#modify_comment_time').val('');
//                    break;
//            }
//        });

        //录入评论二级联动
//        $('#comment_type1').change(function(){
//            var value=$(this).val();
//
//            if(value==2){
//                $('#top_comment_time_box').show();
//            }else{
//                $('#top_comment_time_box').hide();
//                $('#top_comment_times').val('');
//            }
//        });

        // 客户群标记
        $('table.user_table :checkbox.common_group').change(function () {
            var key = this.name,
	            value = this.checked?1:0,
	            tr_obj = $(this).closest('tr');
            if (key=='advertise_effective') {
	            if (value) {
		            tr_obj.find(':checkbox[name=advertise_ineffective]').attr('checked', false);
	            }
	            key = 'advertise_effect';
            } else if (key=='advertise_ineffective') {
                if (value) {
	                tr_obj.find(':checkbox[name=advertise_effective]').attr('checked', false);
	                value = 2;
                }
	            key = 'advertise_effect';
            }
	        PT.sendDajax({
		        'function':'ncrm_change_customer_info',
		        'shop_id':tr_obj.attr('shop_id'),
		        'key':key,
		        'value':value,
		        'call_back':'PT.CommonEvent.change_customer_info_callback'
		        })
        });

        // 更多客户群
        $('.group_switch').click(function () {
	        var td_obj = $(this).closest('td');
	        if ($(this).attr('flag')=='1') {
		        td_obj.children().show();
		        $(this).attr('flag', 0).html('收起');
	        } else {
                td_obj.find('.common_group:disabled:not(:checked)').parent().hide();
                td_obj.find('.client_group_input:not(:checked)').parent(':not(.orange)').hide();
                $(this).attr('flag', 1).html('展开');
	        }
        });

        // 自定义表单重设按钮
        $('#reset_form').click(function () {
	        $('#server_id, #node_path, #saler_id, #operater_id, #consult_id').val('');
	        $('#workbanch_search_form :text:visible').val('');
	        $('#workbanch_search_form select').val('');
	        $('#workbanch_search_form :checkbox').attr('checked', false);
	        $('#workbanch_search_form :radio').attr('checked', false);
        });

        // 订单操作菜单
        $('ul.is_serving, ul.is_ended').click(function () {
            if ($(this).next('#subscribe_menu').length==0 && $(this).attr('category')!='other') {
                var tr_obj = $(this).closest('tr[shop_id]');
	            $('#subscribe_menu').attr({
	                'sub_id':$(this).attr('sub_id'),
	                'shop_id':tr_obj.attr('shop_id'),
	                'nick':tr_obj.attr('nick')
	                });
	            $('#subscribe_menu .edit_subscribe').attr({
	                'subscribe_id':$(this).attr('sub_id'),
	                'nick':tr_obj.attr('nick')
	                });
	            if ($(this).attr('category')=='rjjh' && $('#subscribe_menu').attr('myself_position')!='RJJHLEADER') {
                    $('#subscribe_menu .unsubscribe.forbid_manual').hide();
                } else if ($(this).attr('category')=='vip' || $(this).attr('category')=='ztc') {
                    $('#subscribe_menu .unsubscribe.forbid_manual').hide();
                } else {
                    $('#subscribe_menu .unsubscribe').show();
                }
                if ($("#subscribe_menu .unknown_subscribe").hasClass('forbid_manual')) {
                    var create_date = $(this).children(':eq(3)').text(),
                        days3_after = new Date();
                    days3_after.setTime(Date.parse(create_date)+3*24*60*60*1000);
                    //if ((($(this).attr('psuser_id')=='' && ($("#psuser_id").val() == $(this).attr('cslt_id') || $("#psuser_id").val() == $(this).attr('operater_id')))
                    //    || $(this).attr('psuser_id')==$("#psuser_id").val()) && days3_after>new Date()) {
                    if (($(this).attr('psuser_id')=='' || $(this).attr('psuser_id')==$("#psuser_id").val()) && days3_after>new Date()) {
                        $("#subscribe_menu .unknown_subscribe").removeClass("hide");
                    } else {
                        $("#subscribe_menu .unknown_subscribe").addClass("hide");
                    }
                } else {
                    $("#subscribe_menu .unknown_subscribe").removeClass("hide");
                }
	            $(this).after($('#subscribe_menu'));
            } else {
                $('#subscribe_menu').attr({'sub_id':'', 'shop_id':'', 'nick':''});
                $('body').append($('#subscribe_menu'));
            }
        });

        // 标记刷单
        $('#subscribe_menu .unknown_subscribe').click(function () {
            $('#unknown_subscribe_flag').val('1');
            $('#id_unsubscribe_shop_id').val($('#subscribe_menu').attr('shop_id'));
            $('#unsubscribe_event_id').val($('#subscribe_menu').attr('sub_id'));
            var order_obj = $('#subscribe_menu').prev('ul[sub_id]'),
                refund = Number(order_obj.children('li:eq(5)').find('div:first').html());
            $('#unsubscribe_event_descr').html($('#subscribe_menu').attr('nick') + '　' + order_obj.children('li:eq(3)').find('div:first').html() + '　' + order_obj.children('li:eq(1)').html() + '　' + order_obj.children('li:eq(2)').find('div:first').html() + '　' + order_obj.children('li:eq(0)').html() + '　' + refund + '元');
            $('#unsubscribe_refund').val(refund);
            $(':checkbox[name=refund_reason][value=5]').attr('checked', true);
            //$(':radio[name=refund_type][value=3]').attr('checked', true);
            //$(':radio[name=refund_style][value=2]').attr('checked', true);
            $(':radio[name=refund_style][value=2]').click();
            $(':checkbox[name=frozen_kcjl], :checkbox[name=unmnt_all]').attr('checked', false);
            $("#unsubscribe_refund_info, #unsubscribe_receiver_cn").val("");
            $('#unsubscribe_saler_apportion').val(refund);
            $('#unsubscribe_server_apportion, #unsubscribe_saler_dpt_apportion, #unsubscribe_server_dpt_apportion, #unsubscribe_other_apportion, #unsubscribe_pm_apportion').val('');
            $('#id_add_unsubscribe_layout').attr('unsubscribe_event_pay', refund);
            $('#unsubscribe_cashier_id').val($('#unsubscribe_cashier_id>option[dept='+$('#psuser_dept').val()+']').val());
            $('#unsubscribe_cashier_id').closest('tr').show();
            $('#id_add_unsubscribe_layout tr.only_unsubscribe').hide();
            $('#id_add_unsubscribe_layout tr.only_unknown_subscribe').show();
            $('#unsubscribe_saler_id').val($("#psuser_id").val());
            $('#unsubscribe_saler_cn').val($("#psuser_cn").val());
            $('#id_add_unsubscribe_layout').modal();
        });

        // 录入退款
        $('#subscribe_menu .unsubscribe').click(function () {
            $('#unknown_subscribe_flag').val('');
            $('#id_add_unsubscribe_layout').find('input[type=hidden], input:text, textarea').val('');
            $('#id_add_unsubscribe_layout').find('input:radio, input:checkbox').attr('checked', false);
            $('#id_unsubscribe_shop_id').val($('#subscribe_menu').attr('shop_id'));
            $('#unsubscribe_event_id').val($('#subscribe_menu').attr('sub_id'));
            var order_obj = $('#subscribe_menu').prev('ul[sub_id]');
            //var order_obj = $('#subscribe_menu').prev('ul.is_serving');
            $('#unsubscribe_event_descr').html($('#subscribe_menu').attr('nick') + '　' + order_obj.children('li:eq(3)').find('div:first').html() + '　' + order_obj.children('li:eq(1)').html() + '　' + order_obj.children('li:eq(2)').find('div:first').html() + '　' + order_obj.children('li:eq(0)').html() + '　' + order_obj.children('li:eq(5)').find('div:first').html() + '元');
            $('#id_add_unsubscribe_layout').attr('unsubscribe_event_pay', order_obj.children('li:eq(5)').find('div:first').html());
            $('#unsubscribe_cashier_id').val('');
            $('#unsubscribe_cashier_id').closest('tr').hide();
            $('#id_add_unsubscribe_layout tr.only_unsubscribe').show();
            $('#id_add_unsubscribe_layout tr.only_unknown_subscribe').hide();
            $('#unsubscribe_refund_info, #unsubscribe_receiver_cn').closest('tr').hide();
            $('#unsubscribe_saler_id, #unsubscribe_saler_cn').val('');
            $('#id_add_unsubscribe_layout').modal();
        });

        $('#id_add_unsubscribe_layout input[name=refund_style]').change(function () {
            if (this.value=='2') {
                $('#unsubscribe_cashier_id').val($('#unsubscribe_cashier_id>option[dept='+$('#psuser_dept').val()+']').val());
                $('#unsubscribe_cashier_id').closest('tr').show();
            } else {
                $('#unsubscribe_cashier_id').val('');
                $('#unsubscribe_cashier_id').closest('tr').hide();
            }
            switch (this.value) {
                case '1':
                    $('#unsubscribe_refund_info, #unsubscribe_receiver_cn').closest('tr').hide();
                    break;
                case '2':
                    $('#unsubscribe_refund_info, #unsubscribe_receiver_cn').closest('tr').show();
                    $('#unsubscribe_refund_info').attr('placeholder', '支付宝账号');
                    break;
                case '3':
                    $('#unsubscribe_refund_info, #unsubscribe_receiver_cn').closest('tr').show();
                    $('#unsubscribe_refund_info').attr('placeholder', '银行账号');
                    break;
                case '4':
                    $('#unsubscribe_refund_info, #unsubscribe_receiver_cn').closest('tr').show();
                    $('#unsubscribe_refund_info').attr('placeholder', '银行账号');
                    break;
                case '5':
                    $('#unsubscribe_refund_info').closest('tr').hide();
                    $('#unsubscribe_receiver_cn').closest('tr').show();
                    break;
            }
        });

        // 暂停订单
        $('#subscribe_menu .pause').click(function () {
            $('#id_pause_shop_id').val($('#subscribe_menu').attr('shop_id'));
            $('#pause_event_id').val($('#subscribe_menu').attr('sub_id'));
            var order_obj = $('#subscribe_menu').prev('ul.is_serving');
            $('#pause_event_descr').html($('#subscribe_menu').attr('nick') + '　' + order_obj.children('li:eq(3)').find('div:first').html() + '　' + order_obj.children('li:eq(1)').html() + '　' + order_obj.children('li:eq(2)').find('div:first').html() + '　' + order_obj.children('li:eq(0)').html() + '　' + order_obj.children('li:eq(5)').find('div:first').html() + '元');
            $('#pause_create_time').val(new Date().format('yyyy-MM-dd hh:mm:ss'));
            $('#proceed_date').val('');
            $('#submit_pause').show();
            $('#editor_submit_pause').hide();
            $('#id_add_pause_layout').modal();
        });

        // 终止订单
        $('#subscribe_menu .end_subscribe').click(function () {
            $('#modal_end_subscribe .frozen_kcjl, #modal_end_subscribe .unmnt_all').attr('checked', false);
            $('#modal_end_subscribe').modal('show');
        });
        $('#modal_end_subscribe .end_subscribe').click(function () {
            PT.show_loading('正在终止订单');
            PT.sendDajax({
                'function': 'ncrm_end_subscribe',
                'subscribe_id': parseInt($('#subscribe_menu').attr('sub_id')),
                'frozen_kcjl': $('#modal_end_subscribe .frozen_kcjl').prop('checked')?1:0,
                'unmnt_all': $('#modal_end_subscribe .unmnt_all').prop('checked')?1:0,
                'namespace':"CommonEvent.end_subscribe_callback"
            });
        });
    }

    return {
        init: function() {
            init_dom();
        },
        save_subscribe_call_back:function(data){
            if (data.status==true){
                $("#id_add_subscribe_layout .subscribe_btn").click();
                PT.alert('订单保存成功',null,function(){
                    window.location.reload();
                });

            }  else {
                PT.alert('保存订单出错了');
            }
        },
        showreintro_callback:function(user_list){
            var html_str = template.render('id_user_selector_template', {'user_list':user_list});
            $('#id_select_receiver').html(html_str);
            $('#id_add_reintro_layout').modal();
        },
        creaete_client_group_back:function(json){
            if(json.error){
                PT.alert(json.error);
            }else{
                window.location.reload();
            }
        },
        delete_client_group_back:function(json){
            if(json.error){
                PT.alert(json.error);
            }else{
                window.location.reload();
            }
        },
        change_client_group_back:function(json){
            var str='';
            if(json.err){
                PT.alert(json.err);
                $.each(json.id_list, function (i, shop_id) {
                    var obj = $('table.user_table tr[shop_id='+shop_id+'] .client_group_input[value='+json.client_id+']');
                    obj.attr('checked', obj.prop('checked') && false);
                });
            }else{
                if(json.mode=='add'){
                    str+='添加';
                }else{
                    str+='删除';
                }
                str+='客户群'+'<span class="red">'+json.title+'</span>';
                PT.light_msg(str,'成功');
            }
        },
        rename_client_group_back:function(json){
            if(json.err){
                PT.alert(json.err);
            }else{
                $('#dropdown_client_group_name_'+json.data.id).text(json.data.title);
                $('#dropdown_client_group_name_'+json.data.id).attr('data-original-title',json.data.note);
            }
        },
        editor_contact_back:function(json){
            $('#id_add_contact_layout').modal('hide');
            if(json.err){
                PT.alert(json.err);
            }else{
                var obj=$('#contact_box_'+json.data.id);
                $('#contact_note_'+json.data.id).html(json.data.note);
                obj.find('span:first').text(json.data.contact_type);
                obj.find('.create_time').text(new Date(Date.parse(json.data.create_time)).format('yyyy-MM-dd'));
                if (json.data.xf_flag==1) {
                    obj.find('span.xf_flag').show();
                } else {
                    obj.find('span.xf_flag').hide();
                }
                obj.find('.editor_contact').attr('data-info', $.toJSON({"id":json.data.id, "type":json.data.contact_type, "xf_flag":json.data.xf_flag}));
            }
        },
        editor_operate_back:function(json){
            $('#id_add_operate_layout').modal('hide');
            if(json.err){
                PT.alert(json.err);
            }else{
                var obj=$('#operate_box_'+json.data.id);
                $('#operate_note_'+json.data.id).html(json.data.note);
                obj.find('.create_time').text(new Date(Date.parse(json.data.create_time)).format('yyyy-MM-dd'));
            }
        },
        editor_pause_back:function(json){
            $('#id_add_pause_layout').modal('hide');
            if(json.err){
                PT.alert(json.err);
            }else{
                var obj=$('#pause_box_'+json.data.id);
                $('#pause_note_'+json.data.id).html(json.data.note);
            }
        },
        save_comment_callback:function (result) {
	        $('#id_add_comment_layout').modal('hide');
//	        PT.light_msg('提醒','保存成功！');
//	        if (has_bad_comment) {
//		        var event_labels = $('table.user_table tr[shop_id='+shop_id+'] .event_labels');
//		        if (event_labels.find('.has_bad_comment').length==0) {
//			        event_labels.append('<span class="label label-warning has_bad_comment">'+has_bad_comment+'</span>');
//		        } else {
//			        event_labels.find('.has_bad_comment').html(has_bad_comment);
//		        }
//	        }
            if (result.error) {
	            PT.alert(result.error);
            } else {
                PT.light_msg('提醒','保存成功！');
                if (result.data.comment_type/100>=2) {
	                var _checkbox = $('table.user_table tr[shop_id='+result.data.shop_id+'] :checkbox[name=bad_comment]');
	                if (!_checkbox.prop('checked')) {
	                    _checkbox.attr('checked', true).parent().show();
	                    PT.sendDajax({
	                        'function':'ncrm_change_customer_info',
	                        'shop_id':result.data.shop_id,
	                        'key':'bad_comment',
	                        'value':1,
	                        'call_back':''
	                        })
	                }
                }
            }
        },
        save_contact_call_back:function(json){
            var html;
            $('#id_add_contact_layout').modal('hide');
            if(json.error){
                PT.alert(json.error);
            }else{
                template.isEscape=false;
                html=template.render('contact_note_temp',json.data);
                template.isEscape=true;
                $('#event_note_'+json.data.shop_id).prepend(html);
                PT.light_msg('提醒','保存成功！');
                var _checkbox1 = $('table.user_table tr[shop_id='+json.data.shop_id+'] :checkbox[name=to_1st_contact]'),
                      _checkbox2 = $('table.user_table tr[shop_id='+json.data.shop_id+'] :checkbox[name=to_2nd_contact]');
                if (_checkbox1.prop('checked')) {
	                _checkbox1.attr('checked', false);
	                if (_checkbox2.length>0) {
		                _checkbox2.attr('checked', true).parent().show();
	                }
                } else if (_checkbox2.length>0 && _checkbox2.prop('checked')) {
                    _checkbox2.attr('checked', false);
                }
            }
        },
        save_operate_call_back:function(json){
            var html;
            $('#id_add_operate_layout').modal('hide');
            if(json.error){
                PT.alert(json.error);
            }else{
                template.isEscape=false;
                html=template.render('operate_note_temp',json.data);
                template.isEscape=true;
                $('#event_note_'+json.data.shop_id).prepend(html);
	            PT.light_msg('提醒','保存成功！');
	            var _checkbox = $('table.user_table tr[shop_id='+json.data.shop_id+'] :checkbox[name=unoperated_3days]');
	            if (_checkbox.prop('checked')) {
		            _checkbox.attr('checked', false);
	            }
            }
        },
        save_unsubscribe_call_back:function(json){
            var html;
            $('#id_add_unsubscribe_layout').modal('hide');
            if(json.error){
                PT.alert(json.error)
            }else{
                template.isEscape=false;
                html=template.render('unsubscribe_note_temp',json.data);
                template.isEscape=true;
                if(json.data.unknown_subscribe_flag == 1){
                    $('#subscribe_menu').prev('ul.is_serving').children('li:eq(6)').html(json.data.psuser_name);
                    $('#subscribe_menu').prev('ul.is_serving').children('li:eq(1)').html("未知");
                }
                $('#event_note_'+json.data.shop_id).prepend(html);
	            PT.light_msg('提醒','保存成功！');
            }
        },
        save_pause_call_back:function(json){
            var html;
            $('#id_add_pause_layout').modal('hide');
            if(json.error){
                PT.alert(json.error)
            }else{
                template.isEscape=false;
                html=template.render('pause_note_temp',json.data);
                template.isEscape=true;
                $('#event_note_'+json.data.shop_id).prepend(html);
                PT.light_msg('提醒','保存成功！');
                var _checkbox = $('table.user_table tr[shop_id='+json.data.shop_id+'] :checkbox[name=is_pausing]');
                if (json.data.proceed_date) {
	                _checkbox.attr('checked', false);
                } else {
	                _checkbox.attr('checked', true).parent().show();
                }
            }
        },
        cancel_pause_back:function(json){
            if (json.error) {
                PT.alert(json.error);
            } else {
                $('#id_proceed_layout').modal('hide');
                $('#pause_status_'+json.pause_id).html('【'+json.proceed_date.slice(0, 10)+' 已开启】').addClass('green');
                if (json.is_pausing==0) {
                    $('table.user_table tr[shop_id='+json.shop_id+'] :checkbox[name=is_pausing]').attr('checked', false);
                }
                $('#pause_box_'+json.pause_id+' a.proceed').remove();
                $('#pause_box_'+json.pause_id+' a.del_pause').show();
                var obj = $.parseJSON($('#pause_box_'+json.pause_id+' a.editor_pause').attr('data-info'));
                obj.proceed_date = json.proceed_date;
                $('#pause_box_'+json.pause_id+' a.editor_pause').attr('data-info', $.toJSON(obj));
                PT.light_msg('提醒','保存成功！');
            }
        },
        del_proceed_back:function(json){
            if (json.error) {
                PT.alert(json.error);
            } else {
                $.fancybox.close();
                PT.light_msg('提醒','操作成功！');
            }
        },
        end_subscribe_callback:function (subscribe_id, end_date, msg) {
            $('.order_info>ul[sub_id='+subscribe_id+']').click();
            $('.order_info>ul[sub_id='+subscribe_id+']').removeClass('is_serving').addClass('is_ended').children('li:eq(4)').html(end_date);
            $('#modal_end_subscribe').modal('hide');
            PT.light_msg('提醒','操作成功！');
        },
        change_customer_info_callback:function (key, value, result) {
            if (result>0) {
	            PT.light_msg('提醒', '修改成功！');
	            var mark_obj = $('#client-group-list :checkbox[name='+key+']').siblings('.round_mark');
	            if (mark_obj.length>0) {
		            var mark_value = Number(mark_obj.html());
		            if (!isNaN(mark_value)) {
			            if (value) {
				            mark_obj.html(mark_value+1);
			            } else {
				            mark_obj.html(mark_value-1);
			            }
		            }
	            }
            } else {
	            PT.light_msg('提醒', '修改失败！');
            }
        },
        upload_chat_file:function(){
            var form_data = new FormData(), file = $("#subscribe_chat_file")[0].files[0];
            if(file == undefined ){
                PT.alert('请先选择要上传的文件');
                $("#subscribe_chat_file").val('');
                $("#chat_file_path").val('');
                return true;
            }
            // 验证文件相关参数
            if (file.size > 1024 * 1024 * 10) {
                PT.alert('文件大小不能超过10M');
                $("#subscribe_chat_file").val('');
                $("#chat_file_path").val('');
                return false;
            }
            var extStart = file.name.lastIndexOf(".");
            var ext = file.name.substring(extStart, file.name.length).toUpperCase();
            if (ext == ".EXE"){
                PT.alert('请不要上传可执行文件');
                $("#subscribe_chat_file").val('');
                $("#chat_file_path").val('');
                return false;
            }
            // 上传文件
            form_data.append('up_file', file);
            form_data.append('up_path', "chat_file/");
            var flag = false;
            $.ajax({
                url: '/ncrm/upload_file/',
                type: 'POST',
                cache: false,
                data: form_data,
                processData: false,
                contentType: false,
                async: false,
                success: function(data) {
                     if(data.status==1){
                         $("#chat_file_path").val(data.file_path);
                         flag = true;
                     }else{
                         PT.alert(data.msg);
                         flag = false;
                     }
                },
                error: function() {
                    $("#subscribe_chat_file").val('');
                    $("#chat_file_path").val('');
                     flag = false;
                }
            });
            return flag;
        }
    }
}();
