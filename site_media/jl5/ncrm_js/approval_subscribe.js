PT.namespace('ApprovalSubscribe');
PT.ApprovalSubscribe = function() {

    var init_table=function (){
        $('#approval_subscribe_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": true,
            "bFilter": false,
            "bInfo": true,
            "bSort": true,
            "iDisplayLength": 100,
            "aaSorting": [[5,'asc']],
            "bAutoWidth": true,//禁止自动计算宽度
            'sDom': "<'row-fluid't>",
            "aoColumnDefs": [{sDefaultContent: '', aTargets: ['_all']}],
            "aoColumns": [{"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true},
                          {"bSortable": true, "sType":'custom', "sSortDataType":"custom-text"},
                          {"bSortable": true},
                          ],
            "language": {
                          "emptyTable": "没有记录，请修改过滤条件再次搜索"
                      },
        });

    };

    var submit_form = function(page_no) {
        $('#page_no').val(page_no);
        $('#is_export').val(0);
        $('#search_form').submit();
        PT.show_loading('正在加载数据');
    };

    var init_dom = function() {

        // 日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#order_create_starttime',
                timepicker: false,
                yearStart : 2010,
                yearEnd : 2026,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_create_endtime',
                timepicker: false,
                yearStart : 2010,
                yearEnd : 2026,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#approval_endtime',
                timepicker: false,
                yearStart : 2010,
                yearEnd : 2026,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#approval_starttime',
                timepicker: false,
                yearStart : 2010,
                yearEnd : 2026,
                closeOnDateSelect : true
            });
        });

        $('#export_csv').click(function(){
            var data_str = '';
            $('#approval_subscribe_table tr').each(function(){
                var temp_str = '';
                $(this).find('th').each(function(){
                    if ($(this).index() < 10){
                        temp_str += $.trim($(this).find('div').text()) + ',';
                    }
                });
                $(this).find('td').each(function(){
                    if ($(this).hasClass('approval_status')){
                        temp_str += $.trim($(this).find('.approval_status_display').text()) + ',';
                    }else if ($(this).index() < 10){
                        temp_str += $.trim($(this).text()) + ',';
                    }
                });
                data_str += temp_str.slice(0, -1) + '\n';
            });
            var download_link = document.createElement('a');
            download_link.href = 'data:text/csv;charset=utf-8,\ufeff' + encodeURIComponent(data_str);
            download_link.download = '进账审计.csv';
            document.body.appendChild(download_link);
            download_link.click();
            document.body.removeChild(download_link);
        });


        $('select.approval_status').change(function() {
            var obj_id = $(this).parents('tr:first').attr('id'),
                approval_status = $(this).val();
            $(this).removeClass('approval_status_0 approval_status_1 approval_status_2').addClass('approval_status_'+approval_status);
            $(this).prev().text(approval_status);
            PT.sendDajax({'function': 'ncrm_update_approval_status',
                          'obj_id': obj_id,
                          'approval_status': approval_status});
        });

        $('.modify_approval_status').click(function () {
            var obj_id = $(this).closest('tr[id]').attr('id'),
                approval_status = $(this).attr('approval_status'),
                td_obj = $(this).closest('td'),
                approval_status_cn = '';
            switch (approval_status) {
                case '1':
                    approval_status_cn = '已通过';
                    break;
                case '2':
                    approval_status_cn = '未通过';
                    break;
            }
            if (approval_status_cn) {
                td_obj.find('a.dropdown-toggle>span').text(approval_status_cn);
            }
            td_obj.find('span.hide').text(approval_status);
            td_obj.removeClass('approval_status_0 approval_status_1 approval_status_2').addClass('approval_status_'+approval_status);
            PT.sendDajax({'function': 'ncrm_update_approval_status',
                          'obj_id': obj_id,
                          'approval_status': approval_status});
        });

        $('.upload_contract').change(function() {
            var subscribe_id = $(this).parents('tr:first').attr('id');
            var form_data = new FormData(), that = this, file = $(this)[0].files[0];
            if (file.size > 1024 * 1024 * 2) {
                PT.alert('文件大小不能超过2M');
                $(that).val('');
                return false;
            }
            // if (['application/pdf', 'application/msword', 'image/png', 'image/jpeg', 'image/gif', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].indexOf(file.type) == -1) {
            //     PT.alert('只能上传PDF、WORD文档、图片');
            //     $(that).val('');
            //     return false;
            // }
            form_data.append('subscribe_id', subscribe_id);
            form_data.append('contract', file);
            PT.show_loading('正在上件文件');
            $.ajax({
                url: '/ncrm/upload_contract_file/',
                type: 'POST',
                cache: false,
                data: form_data,
                processData: false,
                contentType: false,
                success: function(data) {
                    data = $.evalJSON(data);
                    PT.hide_loading();
                    if (data.err_msg) {
                        PT.alert(data.err_msg);
                    } else {
                        $(that).next().hide();
                        PT.light_msg('', '上传合同成功');
                        $(that).siblings('.download_contract').show();
                    }
                    $(that).val('');
                    return false;
                },
                error: function() {
                    PT.hide_loading();
                    PT.alert('上传合同失败');
                    $(that).val('');
                    return false;
                }
            });
        });

        $('.pagination>ul>li>a').click(function(){
            submit_form($(this).attr('page_no'));
        });

        $('#submit_form').click(function(){
            submit_form(1);
        });

        $('#search_form input[type=text]').keypress(function(e){
            if (e.which == 13) {
                $('#submit_form').click();
            }
        });

        $('.checkbox_all').click(function(){
            $(this).parent('label').nextAll(':visible').find('input').attr('checked', $(this)[0].checked);
        });

        $('#search_form input[type=checkbox]').change(function(){
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

        $('#search_form input[type=checkbox]').change();

        $('#soft_biz_type').click(function() {
            $(this).parent('label').prevAll().find('input').attr('checked', false);
            $(this).parent('label').prevAll().find('input[value=kcjl],input[value=rjjh],input[value=qn],input[value=other]').attr('checked', true);
        });

        $('#person_biz_type').click(function() {
            $(this).parent('label').prevAll().find('input').attr('checked', false);
            $(this).parent('label').prevAll().find('input[value=vip],input[value=ztc],input[value=zz],input[value=zx],input[value=dyy],input[value=seo],input[value=kfwb],input[value=other]').attr('checked', true);
        });

        $('.tooltips').tooltip({'html': true});

    };

    return {
        init: function() {
            init_dom();
            init_table();
        },

    };
}();
