PT.namespace('CommentManage');
PT.CommentManage = function() {

    var init_table = function() {
        // $('#id_comment_table').dataTable();
        $('#id_comment_table').dataTable({
            sDom: "<t<'mt10'<'dib' i><'dib r' p>>",
            bLengthChange: false,
            bDestroy: true,
            iDisplayLength: 20,
            bAutoWidth: true,
            // aaSorting: [[3, 'desc']],
            // aoColumnDefs: [{bSortable: True, aTargets: [1, 2]}],
            oLanguage: {
                sZeroRecords: "没有符合条件的评论",
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
    };

    var init_dom = function() {

        // var comment_note = undefined;
        // require('pt/pt-editor-mini,node', function(editor, $) {
        //     comment_note = new editor({
        //         render: '#id_comment_note',
        //         textareaAttrs: {
        //             name: 'comment_note'
        //         },
        //         height:'200px'
        //     });
        // });

        // 日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#create_time_start',
                timepicker: false,
                yearStart : 2010,
                yearEnd : 2026,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#create_time_end',
                timepicker: false,
                yearStart : 2010,
                yearEnd : 2026,
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

        $('#comment_form input[type=text]').keypress(function(e){
            if (e.which == 13) {
                $('#comment_form').click();
            }
        });

        $('.checkbox_all').click(function(){
            $(this).parent('label').nextAll(':visible').find('input').attr('checked', $(this)[0].checked);
        });

        $('#comment_form input[type=checkbox]').change(function(){
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

        $('#comment_form input[type=checkbox]').change();

        $('.jq_delete_comment').click(function(){
            var comment_id = $(this).parents('tr:first').attr('comment_id');
            PT.confirm('确认［删除］该评论？', function(){
                PT.show_loading('正在删除评论');
                PT.sendDajax({
                    'function': 'ncrm_delete_comment',
                    'comment_id': comment_id,
                    'call_back': 'PT.CommentManage.save_comment_callback()'
                });
            });
        });

        $('.jq_demotion_comment').click(function(){
            var comment_id = $(this).parents('tr:first').attr('comment_id');
            PT.confirm('确认将该评论降为［日常好评］？', function(){
                PT.show_loading('正在保存评论');
                PT.sendDajax({
                    'function': 'ncrm_demotion_comment',
                    'comment_id': comment_id,
                    'call_back': 'PT.CommentManage.save_comment_callback()'
                });
            });
        });

        $('.jq_upgrade_comment').click(function(){
            var comment_id = $(this).parents('tr:first').attr('comment_id');
            $('#modal_upgrade_comment').attr('comment_id', comment_id);
            $('#modal_upgrade_comment').modal();
        });

        $('.submit_upgrade_comment').click(function(){
            var comment_id = $('#modal_upgrade_comment').attr('comment_id'),
                top_comment_times = $('#modal_upgrade_comment input[name=top_comment_times]').val();
            if (Number(top_comment_times) > 0) {
                PT.show_loading('正在保存评论');
                PT.sendDajax({
                    'function': 'ncrm_upgrade_comment',
                    'comment_id': comment_id,
                    'top_comment_times': top_comment_times,
                    'call_back': 'PT.CommentManage.save_comment_callback()'});
            }else{
                PT.alert('踩好评名次必须是正整数');
                return;
            }
        });

    };

    return {
        init: function() {
            init_table();
            init_dom();
        },
        save_comment_callback: function(error_msg) {
            if (error_msg) {
                PT.alert(error_msg);
            }
            location.reload();
        }
    };
}();
