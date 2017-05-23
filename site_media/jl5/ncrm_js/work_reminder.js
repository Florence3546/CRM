PT.namespace('WorkReminder');
PT.WorkReminder = function() {

        var init_dom = function() {

            //日期时间选择器
            require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
                var b, c;
                b = new Datetimepicker({
                    start: '#start_time',
                    timepicker: false,
                    closeOnDateSelect: true
                });
                c = new Datetimepicker({
                    start: '#end_time',
                    timepicker: false,
                    closeOnDateSelect: true
                });
            });

            //查询
            $('#btn_search').click(function () {
                var is_valid = false;
                var start_time = $.trim($('#start_time').val()),
                      end_time = $.trim($('#end_time').val());
                var start_time_list = start_time.split(' ', 1)[0].split('-', 3),
                      end_time_list = end_time.split(' ', 1)[0].split('-', 3);
                start_time = new Date(start_time_list[0], Number(start_time_list[1])-1, start_time_list[2]).getTime();
                end_time = new Date(end_time_list[0], Number(end_time_list[1])-1, end_time_list[2]).getTime();
                
                if (!isNaN(start_time) || !isNaN(end_time) || $('#psuser_id').val() || $('#department').val() || $('#position_type').val() || $('#handle_status').val()) {
                    is_valid = true;
                }
                if (is_valid) {
	                $('#search_form').submit();
                } else {
                    PT.alert('为确保服务器性能，请输入更多查询条件')
                }
            });
            
            //添加提醒
            $('#btn_create').click(function () {
                $('#modal_add_reminder [name=receiver_name], #modal_add_reminder [name=receiver_id], #modal_add_reminder [name=content]').val('');
                $('#modal_add_reminder').modal();
            });
            $('#submit_reminder').click(function () {
                var receiver_id = Number($('#receiver_id').val());
                if (!receiver_id) {
                    PT.alert('必须填写接收人!');
                    return;
                }
                var content = $.trim($('#modal_add_reminder [name=content]').val());
                if (!content) {
                    PT.alert('必须填写提醒内容!');
                    return;
                }
                PT.show_loading('正在提交');
                PT.sendDajax({
                    'function': 'ncrm_add_reminder',
                    'receiver_id': receiver_id,
                    'content': content,
                    'callback': 'PT.WorkReminder.add_reminder_callback'
                });
            });
            
            //删除提醒
            $('#table_work_reminder a.remove_reminder').click(function () {
                PT.sendDajax({
                    'function': 'ncrm_remove_reminder',
                    'reminder_id': $(this).closest('tr').attr('reminder_id'),
                    'callback': 'PT.WorkReminder.remove_reminder_callback'
                });
            });
            
            //标记为已处理
            $('#table_work_reminder a.mark_reminder_handled').click(function () {
                PT.sendDajax({
                    'function': 'ncrm_mark_reminder_handled',
                    'reminder_id': $(this).closest('tr').attr('reminder_id'),
                    'callback': 'PT.WorkReminder.mark_reminder_handled_callback'
                });
            });
        }

    return {
        init: function() {
            init_dom();
        },
        add_reminder_callback: function (err_msg) {
            $('#modal_add_reminder').modal('hide');
            if (err_msg) {
                PT.alert(err_msg);
            } else {
                PT.alert('操作成功');
            }
        },
        remove_reminder_callback: function (result) {
            if (result.err_msg) {
                PT.alert(result.err_msg);
            } else {
	            $('#table_work_reminder tr[reminder_id='+result.reminder_id+']').remove();
                PT.alert('删除成功');
            }
        },
        mark_reminder_handled_callback: function (result) {
            if (result.err_msg) {
                PT.alert(result.err_msg);
            } else {
                var tr_obj = $('#table_work_reminder tr[reminder_id='+result.reminder_id+']');
                tr_obj.find('td:eq(4)').html('已处理');
                tr_obj.find('td:eq(5)').empty();
                PT.alert('标记成功');
            }
        }
    }
}();
