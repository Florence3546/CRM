PT.namespace('UnsubscribeManage');
PT.UnsubscribeManage = function() {

    var modify_unsubscribe_status = function (unsub_id, status, img_list) {
        PT.sendDajax({
            'function': 'ncrm_modify_unsubscribe_status',
            'id': unsub_id,
            'status': status,
            'img_list': $.toJSON(img_list),
            'call_back': 'PT.UnsubscribeManage.modify_unsubscribe_status_call_back'
        });
    }

	var init_dom = function () {

        //日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#create_time_start',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#create_time_end',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#refund_date_start',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#refund_date_end',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#id_edit_create_time',
                timepicker: true,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#id_edit_refund_date',
                timepicker: true,
                closeOnDateSelect : true
            });
        });

        //初始化表格
        $('#id_unsubscribe_table').dataTable({
            sDom: 't<"#pagination_bar" ip>',
            bLengthChange: false,
            bDestroy: true,
            iDisplayLength: 20,
            aaSorting: [[3, 'desc']],
            aoColumnDefs: [{bSortable: false, aTargets: [10, 13]}],
            oLanguage: {
                sZeroRecords: "没有退款记录",
                sInfo: "第 _START_ 至 _END_ 条（共_TOTAL_条）",
                sInfoEmpty: "0 条记录",
                oPaginate: {
                    sFirst: "首页",
                    sLast: "末页",
                    sNext: "下一页",
                    sPrevious: "上一页"
                }
            }
        });

        var editors = {};

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

        $('#export_csv').click(function(){
            var data_str = '';
            $('#id_unsubscribe_table tr').each(function(){
                var temp_str = '';
                $(this).find('th').each(function(){
                    if ($(this).index()<14){
                        temp_str += $.trim($(this).find('div').text()) + ',';
                    }
                });
                $(this).find('td').each(function(){
                    if ($(this).index() == 7) {
                        temp_str += $.trim($(this).find('.unsubscribe_status_cn').text()) + ',';
                    } else if ($(this).index() < 14) {
                        temp_str += $.trim($(this).text()) + ',';
                    }
                });
                data_str += temp_str.slice(0, -1) + '\n';
            });
            var download_link = document.createElement('a');
            download_link.href = 'data:text/csv;charset=utf-8,\ufeff' + encodeURIComponent(data_str);
            download_link.download = '退款审计.csv';
            document.body.appendChild(download_link);
            download_link.click();
            document.body.removeChild(download_link);
        });

        $('#id_edit_unsubscribe_layout').on('shown',function(){
            editors['id_unsubscribe_note'].render();
            editors['id_unsubscribe_note'].value($('#id_edit_unsubscribe_layout [name=note]').val());
        });

        //修改退款信息
        $('#id_unsubscribe_table').on('click', 'a.modify_unsubscribe', function () {
            var tr_obj = $(this).closest('tr');
            $('#id_edit_unsubscribe_layout').attr('unsub_id', tr_obj.attr('unsub_id'));
            $('#id_edit_unsubscribe_layout').attr('sub_id', tr_obj.attr('sub_id'));
            $('#id_edit_unsubscribe_layout').attr('nick', tr_obj.children().eq(0).text());
            $('#sub_descr').html(tr_obj.children().eq(0).text()+'　'+tr_obj.children().eq(2).text().slice(0,10)+'　'+tr_obj.attr('sub_category')+'　'+tr_obj.children().eq(8).text()+'元');
            $('#id_edit_unsubscribe_layout input[name=create_time]').val(tr_obj.attr('create_time').slice(0,16));
            $('#id_edit_unsubscribe_layout input[name=refund_date]').val(tr_obj.attr('refund_date').slice(0,16));
            $('#id_edit_unsubscribe_layout input[name=refund]').val(Number(tr_obj.attr('refund'))/100);
            // 退款原因 多选 判断是否是列表
            // 清除多选值
            $('#id_edit_unsubscribe_layout [name=refund_reason]').attr('checked', false);
            // $('#id_edit_unsubscribe_layout [name=refund_reason][value='+tr_obj.attr('refund_reason')+']').attr('checked', true);

            tr_obj.attr('refund_reason').split(',').forEach(function (e) {
                $('#id_edit_unsubscribe_layout [name=refund_reason][value='+e+']').attr('checked', true);
            });

            // $('#id_edit_unsubscribe_layout [name=refund_reason][value='+tr_obj.attr('refund_reason')+']').attr('checked', true);

            //$('#id_edit_unsubscribe_layout [name=refund_type][value='+tr_obj.attr('refund_type')+']').attr('checked', true);
            $('#id_edit_unsubscribe_layout [name=refund_style][value='+tr_obj.attr('refund_style')+']').attr('checked', true);
            $('#id_edit_unsubscribe_layout [name=refund_info]').val(tr_obj.attr('refund_info'));
            $('#id_edit_unsubscribe_layout [name=saler_apportion]').val(Number(tr_obj.attr('saler_apportion'))/100);
            $('#id_edit_unsubscribe_layout [name=server_apportion]').val(Number(tr_obj.attr('server_apportion'))/100);
            $('#id_edit_unsubscribe_layout [name=saler_dpt_apportion]').val(Number(tr_obj.attr('saler_dpt_apportion'))/100);
            $('#id_edit_unsubscribe_layout [name=server_dpt_apportion]').val(Number(tr_obj.attr('server_dpt_apportion'))/100);
            $('#id_edit_unsubscribe_layout [name=other_apportion]').val(Number(tr_obj.attr('other_apportion'))/100);
            $('#id_edit_unsubscribe_layout [name=pm_apportion]').val(Number(tr_obj.attr('pm_apportion'))/100);
            $('#id_edit_unsubscribe_layout [name=note]').val(tr_obj.attr('note'));
            $('#id_edit_unsubscribe_layout [name=receiver_cn]').val(tr_obj.attr('receiver_cn'));
            $('#id_edit_unsubscribe_layout').attr('cashier_id', tr_obj.attr('cashier_id'));
            if (tr_obj.attr('refund_style')=='2') {
                $('#unsubscribe_cashier_id').val(tr_obj.attr('cashier_id'));
                $('#unsubscribe_cashier_id').closest('tr').show();
            } else {
                $('#unsubscribe_cashier_id').val('');
                $('#unsubscribe_cashier_id').closest('tr').hide();
            }
            $('#id_edit_unsubscribe_layout').attr('sub_pay', tr_obj.attr('sub_pay')).modal('show');
        });

        $('#id_edit_unsubscribe_layout input[name=refund_style]').change(function () {
            if ($('#id_edit_unsubscribe_layout input[name=refund_style]:checked').val()=='2') {
                $('#unsubscribe_cashier_id').val($('#id_edit_unsubscribe_layout').attr('cashier_id'));
                $('#unsubscribe_cashier_id').closest('tr').show();
            } else {
                $('#unsubscribe_cashier_id').val('');
                $('#unsubscribe_cashier_id').closest('tr').hide();
            }
        });

        $('#submit_unsubscribe').click(function () {
            var submit_obj = {},
                sub_pay = Number($('#id_edit_unsubscribe_layout').attr('sub_pay'));
            submit_obj.id = $('#id_edit_unsubscribe_layout').attr('unsub_id');
            submit_obj.sub_id = parseInt($('#id_edit_unsubscribe_layout').attr('sub_id'));
            submit_obj.create_time = $.trim($('#id_edit_unsubscribe_layout input[name=create_time]').val());
            submit_obj.refund_date = $.trim($('#id_edit_unsubscribe_layout input[name=refund_date]').val());
            submit_obj.refund = parseInt($('#id_edit_unsubscribe_layout input[name=refund]').val()*100);

            // 退款原因 多选
            var refund_reason_list = [];
            $('#id_edit_unsubscribe_layout :checked[name=refund_reason]').each(function () {
                refund_reason_list.push(parseInt($(this).val()));
            });
            // submit_obj.refund_reason = parseInt($('#id_edit_unsubscribe_layout :checked[name=refund_reason]').val());
            submit_obj.refund_reason = refund_reason_list;

            //submit_obj.refund_type = parseInt($('#id_edit_unsubscribe_layout :checked[name=refund_type]').val());
            submit_obj.refund_style = parseInt($('#id_edit_unsubscribe_layout :checked[name=refund_style]').val());
            submit_obj.refund_info = $('#id_edit_unsubscribe_layout [name=refund_info]').val();
            submit_obj.note = $.trim(editors['id_unsubscribe_note'].value());
            submit_obj.saler_apportion = parseInt($('#id_edit_unsubscribe_layout [name=saler_apportion]').val()*100);
            submit_obj.server_apportion = parseInt($('#id_edit_unsubscribe_layout [name=server_apportion]').val()*100);
            submit_obj.saler_dpt_apportion = parseInt($('#id_edit_unsubscribe_layout [name=saler_dpt_apportion]').val()*100);
            submit_obj.server_dpt_apportion = parseInt($('#id_edit_unsubscribe_layout [name=server_dpt_apportion]').val()*100);
            submit_obj.other_apportion = parseInt($('#id_edit_unsubscribe_layout [name=other_apportion]').val()*100);
            submit_obj.pm_apportion = parseInt($('#id_edit_unsubscribe_layout [name=pm_apportion]').val()*100);
            var receiver_cn = $.trim($('#id_edit_unsubscribe_layout [name=receiver_cn]').val());
            submit_obj.cashier_id = Number($('#unsubscribe_cashier_id').val());
            submit_obj.reimburse_dpt = $.trim($('#unsubscribe_cashier_id>option:checked').attr('dept'));
            if (isNaN(submit_obj.refund)) {
                PT.alert('退款金额未填写或格式不正确');
                return false;
            }
            //if (submit_obj.refund_type!=5 && submit_obj.refund>sub_pay) {
            if (submit_obj.refund_reason!=6 && submit_obj.refund>sub_pay) {
                PT.alert('退款金额不能大于订单实付金额');
                return false;
            }
            //if (isNaN(submit_obj.refund_type)) {
            //    PT.alert('退款类型不能为空');
            //    return false;
            //}
            // if (isNaN(submit_obj.refund_reason)) {
            //     PT.alert('退款原因不能为空');
            //     return false;
            // }
            if (submit_obj.refund_reason.length == 0) {
                PT.alert('退款原因不能为空,可多选!');
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
            submit_obj.refund_info += '__'+receiver_cn;
            if (isNaN(submit_obj.saler_apportion) || isNaN(submit_obj.server_apportion) || isNaN(submit_obj.other_apportion) || isNaN(submit_obj.pm_apportion) || isNaN(submit_obj.saler_dpt_apportion) || isNaN(submit_obj.server_dpt_apportion)) {
                PT.alert('退款分摊金额格式不正确');
                return false;
            }
            if (submit_obj.saler_apportion + submit_obj.server_apportion + submit_obj.other_apportion + submit_obj.pm_apportion + submit_obj.saler_dpt_apportion + submit_obj.server_dpt_apportion != submit_obj.refund) {
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
            PT.sendDajax({
                'function': 'ncrm_modify_unsubscribe',
                'obj': $.toJSON(submit_obj),
                'nick': $('#id_edit_unsubscribe_layout').attr('nick'),
                'org_cashier_id':$('#id_edit_unsubscribe_layout').attr('cashier_id'),
                'call_back': 'PT.UnsubscribeManage.modify_unsubscribe_call_back'
            });
        });

        //删除退款事件
        $('#id_unsubscribe_table').on('click', 'a.del_unsubscribe', function () {
            var tr_obj = $(this).closest('tr');
            PT.confirm('确定要删除这笔退款事件吗？', function () {
                PT.sendDajax({
                    'function': 'ncrm_delete_event',
                    'event_id': tr_obj.attr('unsub_id'),
                    'model_type': 'unsubscribe',
                    'call_back': 'PT.UnsubscribeManage.delete_unsubscribe_back'
                });
            }, []);
        });

        //修改退款状态
        //$('#id_unsubscribe_table a.modify_unsubscribe_status').click(function () {  // 分页后非首页绑定失败，原因未查明
        //    var unsub_id = $(this).closest('tr[unsub_id]').attr('unsub_id'),
        //        status = $(this).attr('status');
        //    if (status=='1') {
        //        modify_unsubscribe_status(unsub_id, status, []);
        //    } else {
        //        $('#image_clip_board').empty();
        //        $('#modal_modify_unsubscribe_status').attr({unsub_id:unsub_id, status:status}).modal('show');
        //    }
        //});
        $('#modal_modify_unsubscribe_status a.modify_unsubscribe_status').click(function () {
            if ($('#image_clip_board').children('img').length) {
                var unsub_id = $('#modal_modify_unsubscribe_status').attr('unsub_id'),
                    status = $('#modal_modify_unsubscribe_status').attr('status'),
                    img_list = $('#image_clip_board img').map(function(){return this.src;}).get();
                modify_unsubscribe_status(unsub_id, status, img_list);
            } else {
                $('#image_clip_board').empty();
                PT.alert('截图交易凭证并粘贴在空白区域中！');
            }
        });

        //查看截图
        $('#id_unsubscribe_table').on('click', 'a.show_img_modal', function () {
            PT.sendDajax({
                'function':'ncrm_get_unsubscribe_img_list',
                'unsub_id':$(this).closest('tr').attr('unsub_id'),
                'call_back':'PT.UnsubscribeManage.show_img_modal'
            });
        });


        $('#submit_form').click(function(){
            PT.show_loading('正在加载数据');
            $('#is_export').val(0);
            $('#form_unsubscribe_manage').submit();
        });

        $('#form_unsubscribe_manage input[type=text]').keypress(function(e){
            if (e.which == 13) {
                $('#submit_form').click();
            }
        });


        $('.checkbox_all').click(function(){
            $(this).parent('label').nextAll(':visible').find('input').attr('checked', $(this)[0].checked);
        });

        $('#form_unsubscribe_manage input[type=checkbox]').change(function(){
            if ($(this).hasClass('checkbox_all')){
                return;
            }
            var jq_div = $(this).parents('div:first'),
                jq_first_input = jq_div.find('.checkbox_all');
            if (jq_first_input.length === 0){
                return;
            }
            // if ($(this)[0].checked == jq_first_input[0].checked){
            //     return;
            // }
            var all_sibings_labels = jq_first_input.parent('label').nextAll(':visible'),
                all_input_count = all_sibings_labels.find('input[type=checkbox]').length,
                all_checked_count = all_sibings_labels.find('input[type=checkbox]:checked').length,
                checked_status = false;
            if (all_checked_count === all_input_count){
                checked_status = true;
            }
            jq_first_input.attr('checked', checked_status);
        });
        $('#form_unsubscribe_manage input[type=checkbox]').change();
    };

    return {
        init: function() {
            init_dom();
        },
        modify_unsubscribe_call_back: function (json) {
            if(json.error){
                PT.alert(json.error);
            }else{
                // 退款原因 多选
                var refund_reason_cn_char = '';
                console.log(json.data.refund_reason);
                    // 返回退款原因中文拼接
                    // json.data.refund_reason.forEach(function(a){
                    //     refund_reason_cn_char += $.trim($('#form_unsubscribe_manage input[name=refund_reason][value='+a+']').parent().text());
                    //     refund_reason_cn_char += '';
                    // });
                // 返回退款原因数字
                refund_reason_cn_char = json.data.refund_reason.join(', ');

                var tr_obj = $('#id_unsubscribe_table tr[unsub_id='+json.data.id+']'),
                    refund = json.data.refund/100,
                    saler_apportion = json.data.saler_apportion/100,
                    server_apportion = json.data.server_apportion/100,
                    saler_dpt_apportion = json.data.saler_dpt_apportion/100,
                    server_dpt_apportion = json.data.server_dpt_apportion/100,
                    other_apportion = json.data.other_apportion/100,
                    pm_apportion = json.data.pm_apportion/100,
                    td_apportion = tr_obj.children().eq(10),
                    refund_style_cn = $.trim($('#id_edit_unsubscribe_layout [name=refund_style][value='+json.data.refund_style+']').parent().text()),

                    // refund_reason_cn = $.trim($('#form_unsubscribe_manage input[name=refund_reason][value='+json.data.refund_reason+']').parent().text()),
                    refund_reason_cn = refund_reason_cn_char;
                    //refund_type_cn = $.trim($('#form_unsubscribe_manage input[name=refund_type][value='+json.data.refund_type+']').parent().text()),
                    cashier_cn = $.trim($('#unsubscribe_cashier_id>[value='+json.data.cashier_id+']').text());

                tr_obj.children().eq(3).html(json.data.create_time);
                tr_obj.children().eq(4).html(refund_reason_cn);
                //tr_obj.children().eq(4).html(refund_type_cn);
                tr_obj.children().eq(6).html(cashier_cn);
                tr_obj.children().eq(9).html(refund.toFixed(2));
                td_apportion.find('.saler_apportion').html(saler_apportion.toFixed(2));
                td_apportion.find('.server_apportion').html(server_apportion.toFixed(2));
                td_apportion.find('.saler_dpt_apportion').html(saler_dpt_apportion.toFixed(2));
                td_apportion.find('.server_dpt_apportion').html(server_dpt_apportion.toFixed(2));
                td_apportion.find('.other_apportion').html(other_apportion.toFixed(2));
                td_apportion.find('.pm_apportion').html(pm_apportion.toFixed(2));
                if (saler_dpt_apportion==0) {
                    td_apportion.find('.saler_dpt_apportion').parent().hide();
                } else {
                    td_apportion.find('.saler_dpt_apportion').parent().show();
                }
                if (server_dpt_apportion==0) {
                    td_apportion.find('.server_dpt_apportion').parent().hide();
                } else {
                    td_apportion.find('.server_dpt_apportion').parent().show();
                }
                if (other_apportion==0) {
                    td_apportion.find('.other_apportion').parent().hide();
                } else {
                    td_apportion.find('.other_apportion').parent().show();
                }
                if (pm_apportion==0) {
                    td_apportion.find('.pm_apportion').parent().hide();
                } else {
                    td_apportion.find('.pm_apportion').parent().show();
                }
                //tr_obj.children().eq(10).find('span').html(saler_apportion.toFixed(2));
                //tr_obj.children().eq(11).find('span').html(server_apportion.toFixed(2));
                //tr_obj.children().eq(12).html(other_apportion.toFixed(2));
                tr_obj.children().eq(11).html(refund_style_cn);
                tr_obj.children().eq(12).html(json.data.refund_info+'__'+json.data.receiver_cn);
                tr_obj.attr({
                    'refund':json.data.refund,
                    'create_time':json.data.create_time || '',
                    'refund_date':json.data.refund_date || '',
                    'refund_reason':json.data.refund_reason,
                    //'refund_type':json.data.refund_type,
                    'refund_style':json.data.refund_style,
                    'refund_info':json.data.refund_info,
                    'saler_apportion':json.data.saler_apportion,
                    'server_apportion':json.data.server_apportion,
                    'saler_dpt_apportion':json.data.saler_dpt_apportion,
                    'server_dpt_apportion':json.data.server_dpt_apportion,
                    'other_apportion':json.data.other_apportion,
                    'pm_apportion':json.data.pm_apportion,
                    'note':json.data.note,
                    'cashier_id':json.data.cashier_id,
                    'receiver_cn':json.data.receiver_cn
                });
                $('#id_edit_unsubscribe_layout').modal('hide');
                PT.light_msg('提示', '保存成功！');
            }
        },
        delete_unsubscribe_back: function (json) {
            if(json.error){
                PT.alert(json.error);
            }else{
                $('#id_unsubscribe_table tr[unsub_id='+json.event_id+']').remove();
                PT.light_msg('提示', '删除成功！');
            }
        },
        modify_unsubscribe_status_call_back: function (json) {
            if(json.error){
                PT.alert(json.error);
            }else{
                $('#modal_modify_unsubscribe_status').modal('hide');
                var tr_obj = $('#id_unsubscribe_table tr[unsub_id='+json.data._id+']'),
                    cashier_cn = $.trim($('#unsubscribe_cashier_id>[value='+json.data.cashier_id+']').text());
                tr_obj.children().eq(6).html(cashier_cn);
                tr_obj.children().eq(7).removeClass().addClass('unsubscribe_status_'+json.data.status);
                tr_obj.find('.unsubscribe_status_cn').html(json.data.status_cn);
                PT.light_msg('提示', '操作成功！');
            }
        },
        show_img_modal: function (json) {
            if (json.error) {
                PT.alert(json.error);
            } else {
                $('#modal_unsubscribe_img_list .modal-body').empty();
                $.each(json.img_list, function (i, data_uri) {
                    $('#modal_unsubscribe_img_list .modal-body').append('<div class="tc mb10"><a href="'+data_uri+'" target="_blank"><img src="'+data_uri+'" style="max-width: 780px;"></a></div>');
                });
                $('#modal_unsubscribe_img_list').modal('show');
            }
        },
        modify_unsubscribe_status_wrapper: function (unsub_id, status) {
            // 标记为已退款时须上传支付宝交易截图
            //if (status==1) {
            //    modify_unsubscribe_status(unsub_id, status, []);
            //} else {
            //    $('#image_clip_board').empty();
            //    $('#modal_modify_unsubscribe_status').attr({unsub_id:unsub_id, status:status}).modal('show');
            //}
            modify_unsubscribe_status(unsub_id, status, []);
        }
    }
}();
