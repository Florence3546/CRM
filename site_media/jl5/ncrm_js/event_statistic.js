PT.namespace('EventStatistic');
PT.EventStatistic = function() {

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
            
            //初始化表格列的显示
            if ($('#check_all_events').prop('checked')) {
                $('#table_event_statistic th, #table_event_statistic td').show();
            } else {
                $('[name=event_type]:checked').each(function () {
	                var i = $(':checkbox[name=event_type]').index(this);
		            $('#table_event_statistic th:eq('+(i+2)+')').show();
			        $('#table_event_statistic>tbody>tr>td:nth-child('+(i+3)+')').show();
                });
                $('#table_event_statistic>tbody>tr:eq(0)>td[colspan]').attr('colspan', 3+$('[name=event_type]:checked').length);
            }
            
            //过滤事件列
            $(':checkbox[name=event_type]').click(function () {
                var i = $(':checkbox[name=event_type]').index(this);
                if (this.id=='check_all_events') {
	                $(':checkbox[name=event_type]').attr('checked', this.checked);
	                if (this.checked) {
		                $('#table_event_statistic th, #table_event_statistic td').show();
		                $('#table_event_statistic>tbody>tr:eq(0)>td[colspan]').attr('colspan', 8);
	                } else {
		                $('#table_event_statistic th:gt(2)').hide();
	                    $('#table_event_statistic>tbody>tr>td:nth-child(n+4)').hide();
		                $('#table_event_statistic>tbody>tr:eq(0)>td[colspan]').attr('colspan', 3);
	                }
                } else if (this.checked) {
                    $('#table_event_statistic>tbody>tr:eq(0)>td[colspan]').attr('colspan', 3+$('[name=event_type]:checked').length);
                    if ($(':checkbox[name=event_type]:gt(0):not(:checked)').length==0) {
                        $('#check_all_events').attr('checked', true);
                    }
                    $('#table_event_statistic th:eq('+(i+2)+')').show();
                    $('#table_event_statistic>tbody>tr>td:nth-child('+(i+3)+')').show();
                } else {
                    $('#check_all_events').attr('checked', false);
                    $('#table_event_statistic>tbody>tr:eq(0)>td[colspan]').attr('colspan', 3+$('[name=event_type]:checked').length);
                    $('#table_event_statistic th:eq('+(i+2)+')').hide();
                    $('#table_event_statistic>tbody>tr>td:nth-child('+(i+3)+')').hide();
                }
            });
            
            //搜索
            $('#search').click(function () {
                var start_time = $.trim($('#start_time').val()),
                      end_time = $.trim($('#end_time').val());
                if (!start_time || !end_time) {
                    PT.alert('起止时间不能为空！');
                    return;
                } else {
                    var start_time_list = start_time.split(' ', 1)[0].split('-', 3),
                          end_time_list = end_time.split(' ', 1)[0].split('-', 3);
                    start_time = new Date(start_time_list[0], Number(start_time_list[1])-1, start_time_list[2]).getTime();
                    end_time = new Date(end_time_list[0], Number(end_time_list[1])-1, end_time_list[2]).getTime();
                    if (isNaN(start_time) || isNaN(end_time)) {
                        PT.alert('起止时间格式不对！');
                        return;
                    }
                    if ((end_time-start_time)>31*24*60*60*1000) {
                        PT.alert('起止时间范围不能超过1个月！');
                        return;
                    }
                    $('#search_form').submit();
                }
            });
            
            //展开收起
            $('a.cascade_switch').click(function () {
                var tr_obj = $(this).closest('tr');
                var level_flag = Number(tr_obj.attr('level_flag'));
                if (isNaN(level_flag)) {
                    return;
                }
                if ($(this).attr('flag')=='0') {
                    $(this).attr('flag', '1').html('收起');
                    tr_obj.nextUntil('[level_flag='+level_flag+']').filter('[level_flag='+(level_flag-1)+']').show();
                } else {
                    $(this).attr('flag', '0').html('展开');
                    tr_obj.nextUntil('[level_flag='+level_flag+']').filter('[level_flag!=2]').hide().find('a.cascade_switch').attr('flag', '0').html('展开');
                }
            });
        }

    return {
        init: function() {
            init_dom();
        }
    }
}();
