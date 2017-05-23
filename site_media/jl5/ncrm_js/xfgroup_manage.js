PT.namespace('XFGroupManage');
PT.XFGroupManage = function() {

    var jq_add_xfgroup = $('#add_xfgroup_modal');

    var init_dom = function() {

        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            $('.end_time').each(function(){
                var this_id = $(this).attr('id');
                new Datetimepicker({
                    start : '#' + this_id,
                    yearStart : 2016,
                    format : 'YYYY-MM-DD HH:mm:ss',
                    formatTime : 'HH:mm:ss',
                });

            });

            new Datetimepicker({
                start : '#new_xfgroup_starttime',
                yearStart : 2016,
                format : 'YYYY-MM-DD HH:mm:ss',
                formatTime : 'HH:mm:ss',
            });
        });

        $('.jq_freeze').click(function(){
            var xfgroup_id = $(this).parents('tr:first').attr('xfgroup_id');
            PT.confirm('确定要「冻结」销服组?' , function(){
                PT.sendDajax({'function': 'ncrm_freeze_xfgroup', 'xfgroup_id': xfgroup_id});
            });
        });

        $('.modify_end_time').click(function(){
            $(this).prev().attr('disabled', false);
            $(this).hide().next().show();
        });

        $('.save_end_time').click(function(){
            PT.sendDajax({
                'function': 'ncrm_save_xfgroup_endtime',
                'xfgroup_id': $(this).parents('tr:first').attr('xfgroup_id'),
                'end_time': $(this).prevAll('.end_time').val(),
            });
        });

        jq_add_xfgroup.find('select').change(function(){
            var consult = jq_add_xfgroup.find('select[name=consult_id]').find('option:checked').text(),
                seller = jq_add_xfgroup.find('select[name=seller_id]').find('option:checked').text(),
                new_xfgroup_name = consult.split('_')[2] + '+' + seller.split('_')[2];
            jq_add_xfgroup.find('input[name=xfgroup_name]').val(new_xfgroup_name);
        });

        jq_add_xfgroup.find('select:last').change();

        $('.tooltips').tooltip({'html': true});

        $('#submit_xfgroup').click(function() {
            if (!jq_add_xfgroup.find('input[name=xfgroup_name]').val()) {
                PT.light_msg('', '销服名不能为空');
                return;
            }else if(!jq_add_xfgroup.find('select[name=consult_id]').val()) {
                PT.light_msg('', '顾问不能为空');
                return;
            }else if(!jq_add_xfgroup.find('select[name=seller_id]').val()) {
                PT.light_msg('', '销售不能为空');
                return;
            }else if(!jq_add_xfgroup.find('input[name=start_time]').val()) {
                PT.light_msg('', '生效时间不能为空');
                return;
            }
            $('#form_xfgroup').submit();
        });

    };


    return {
        init: function() {
            init_dom();
        },

        save_xfgroup_endtime_back: function(xfgroup_id){
            location.reload();
            // var jq_td = $('tr[xfgroup_id=' + xfgroup_id + ']');
            // jq_td.find('td:last').html('<span class="red">已冻结</span>');
        }
    };
}();
