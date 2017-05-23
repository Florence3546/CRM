PT.namespace('MetricStatistic');
PT.MetricStatistic = function() {

        var check_limit_date = function(){
            var date_str = $("#start_time").val();
            var limit_date = "2016-01-01";
            if ( limit_date > date_str){
                $("#start_time").val(limit_date);
                PT.alert("亲，当下度量工具仅仅支持 <b style='color:red;'> "+limit_date+" </b> 之后的数据统计。");
                return false;
            }
            return true;
        };

        var check_time = function(){
            var start_date_str = $("#start_time").val();
            var end_date_str = $("#end_time").val();
            if ( end_date_str >= start_date_str ){
                return true;
            } else {
                PT.alert("亲，时间选择有误，<b style='color:red;'>起始时间</b> 要小于等于 <b style='color:red;'>截止时间</b>");
                return false;
            }
        };

        var date_format = function(date_obj){
            var month = date_obj.getMonth()+1 > 9 ? date_obj.getMonth()+1 : "0" + (date_obj.getMonth()+1);
            var date = date_obj.getDate() > 9 ? date_obj.getDate() : "0" + date_obj.getDate();
            return date_obj.getFullYear() + "-" + month +"-" + date;
        };

        var limit_refresh_cycle = function(){
            var end_date = new Date();
            var start_date = new Date();

            if ( end_date.getDate() > 5 ){
                start_date.setDate(1);
            } else {
                start_date.setMonth(start_date.getMonth() - 1)
                start_date.setDate(1);
            }

            $("#start_time").val(date_format(start_date));
            $("#end_time").val(date_format(end_date));
            $("#period option[value=ps_week]").attr('selected',true);

            PT.show_loading('正在加载数据');
            $('input[name=refresh_flag]').val('1');
            $('#search_form').submit();
        };

        var init_dom = function() {

            // 日期时间选择器
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

            // 根据职位过滤
            $(':radio[name=position_type]').click(function () {
                $(':checkbox[name=server_id]').attr('checked', false).parent().hide();
                $(':checkbox[name=server_id][position_type='+this.value+']').parent().show();
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

            // 搜索
            $('#search').click(function () {
                if (check_time() && check_limit_date()){
                    PT.show_loading('正在加载数据');
                    $('#search_form').submit();
                }
            });

            // 强制刷新
            $('#refresh_data').click(function () {
                if ( check_time() && check_limit_date() ){
                    PT.confirm("亲，请注意，如果 <b style='color:red;'>校验时间在本月5日之前，则可刷新上月数据，反之，则只能刷新本月数据</b>，您是否要进行 <b style='color:red;'>绩效校准 </b>？", limit_refresh_cycle);
                }
            });

            // 快速查询
            $('a.shortcut').click(function () {
                var years = Number($(this).attr('years')) || 0,
                      months = Number($(this).attr('months')) || 0,
                      days = Number($(this).attr('days')) || 0,
                      period = $(this).attr('period'),
                      start_time = new Date(),
                      timedelta = 0;
                if (years>0) {
                    timedelta += years*365;
                }
                if (months>0) {
                    timedelta += months*30;
                }
                if (days>0) {
                    timedelta += days;
                }
                if (timedelta>0) {
                    start_time.setTime(start_time.getTime()-timedelta*24*60*60*1000);
                    $('#start_time').val(start_time.format('yyyy-MM-dd'));
                    $('#end_time').val('');
                    $('#period').val(period);
                    $('#search').click();
                }
            });

            // 跳转工作台搜索店铺
            $('a.search_shops').click(function () {
                var psuser_id = $(this).parent('td').siblings('td[psuser_id]').attr('psuser_id'),
                      metric_name = $(this).parent('td').siblings('td[metric_name]').attr('metric_name'),
                      start_date = $('#table_event_statistic th[data_no='+$(this).parent().attr('data_no')+']').attr('start_date'),
                      end_date = $('#table_event_statistic th[data_no='+$(this).parent().attr('data_no')+']').attr('end_date');
                window.open('/ncrm/myworkbench/?metric_statistic_args_old='+[psuser_id, metric_name, start_date, end_date].join(','));
            });

            // 导出单个度量维度数据
            $('a.export_data').click(function () {
                var psuser_id = $(this).parent('td').siblings('td[psuser_id]').attr('psuser_id'),
                      metric_name = $(this).parent('td').siblings('td[metric_name]').attr('metric_name'),
                      data_no = $(this).parent().attr('data_no'),
                      start_date = $('#table_event_statistic th[data_no='+data_no+']').attr('start_date'),
                      end_date = $('#table_event_statistic th[data_no='+data_no+']').attr('end_date');
                PT.show_loading('正在加载');
                PT.sendDajax({
                    'function': 'ncrm_get_export_metric_data_old',
                    'psuser_id': psuser_id,
                    'metric_name': metric_name,
                    'data_no': data_no,
                    'start_date': start_date,
                    'end_date': end_date,
                    'callback': 'PT.MetricStatistic.export_metric_data_callback'
                });
            });

            // 刷新单个度量维度数据
            $('a.refresh_data').click(function () {
                var psuser_id = $(this).parent('td').siblings('td[psuser_id]').attr('psuser_id'),
                      metric_name = $(this).parent('td').siblings('td[metric_name]').attr('metric_name'),
                      data_no = $(this).parent().attr('data_no'),
                      start_date = $('#table_event_statistic th[data_no='+data_no+']').attr('start_date'),
                      end_date = $('#table_event_statistic th[data_no='+data_no+']').attr('end_date');
                PT.show_loading('正在加载');
                PT.sendDajax({
                    'function': 'ncrm_refresh_metric_data_old',
                    'psuser_id': psuser_id,
                    'metric_name': metric_name,
                    'data_no': data_no,
                    'start_date': start_date,
                    'end_date': end_date,
                    'callback': 'PT.MetricStatistic.refresh_metric_data_callback'
                });
            });

            // 度量趋势图
            $('a.metric_chart').click(function () {
                var td_obj = $(this).parent('td'),
                      data_objs = [],
                      my_name = td_obj.attr('psuser_name'),
                      metric_name = td_obj.attr('metric_name'),
                      metric_unit = td_obj.attr('unit');
                var psuser_name_list = $.map($('#table_event_statistic>tbody td.psuser_name'), function (elem) {return $(elem).text()});
                var category_list = $.map($('#table_event_statistic>thead th[data_no]:gt(0)'), function (elem) {return $(elem).text()});
                var series_cfg_list = [];
                var color_list = ['#426ab3', '#87CEFA', '#06B9D1', '#005687', '#1E90FF', '#FD5B78'];
                $.each(psuser_name_list, function (i, psuser_name) {
                    td_obj = $('#table_event_statistic>tbody td[metric_name='+metric_name+']').eq(i);
                    data_objs = td_obj.nextAll(':gt(0)');
                    if (data_objs.length==0) {
                        data_objs = td_obj.next();
                    }
                    series_cfg_list.push({
                        'name': psuser_name,
                        'value_list': $.map(data_objs, function (elem) {return Number($(elem).find('a.search_shops').text()) || 0}),
                        'color': color_list[i%6],
                        'visible': psuser_name==my_name?true:false,
                        'unit': metric_unit,
                        'opposite': false,
                        'is_axis': i==0?1:0,
                        'yAxis': 0
                    })
                })
                $('#title_metric_chart').html($(this).text());
                $('#modal_metric_chart').modal();
                PT.draw_trend_chart('div_metric_chart', category_list, series_cfg_list);
            });

            $('#search_form input[type=checkbox]').change();
        }

    return {
        init: function() {
            init_dom();
        },
        refresh_metric_data_callback: function (psuser_id, metric_name, data_no, result) {
            $('#table_event_statistic td[psuser_id='+psuser_id+'][metric_name='+metric_name+']').siblings('[data_no='+data_no+']').children('a.search_shops').html(result);
        },
        export_metric_data_callback: function(psuser_id, metric_name, data_no, event_list){
            var data_str = '',
                psuser_name = $.trim($('input[type=checkbox][name=server_id][value='+psuser_id+']').parent().text()),
                metric_str = $.trim($('input[type=checkbox][name=metric][value='+metric_name+']').parent().text()),
                th_name = $('#table_event_statistic th[data_no='+data_no+']').text(),
                file_name = psuser_name + '_' + metric_str + '_' + th_name + '.csv';
            for (var i=0; i<event_list.length; i++){
                var temp_str = '';
                for (var j=0; j<event_list[i].length; j++){
                    temp_str += event_list[i][j] + ',';
                }
                data_str += temp_str.slice(0, -1) + '\n';
            }
            var download_link = document.createElement('a');
            download_link.href = 'data:text/csv;charset=utf-8,\ufeff' + encodeURIComponent(data_str);
            download_link.download = file_name;
            document.body.appendChild(download_link);
            download_link.click();
            document.body.removeChild(download_link);
        }
    }
}();
