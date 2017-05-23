PT.namespace('MetricStatisticRJJH');
PT.MetricStatisticRJJH = function() {
        var data_dict = {};

        var init_dom = function() {

            // 日期时间选择器
            require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
                new Datetimepicker({
                    start: '#start_date',
                    timepicker: false,
                    closeOnDateSelect: true
                });
                new Datetimepicker({
                    start: '#end_date',
                    timepicker: false,
                    closeOnDateSelect: true
                });
            });

            $('#div_search').on('click', '.checkbox_all', function () {
                $(this).parent('label').nextAll(':visible').find('input').attr('checked', $(this)[0].checked);
            });

            $('#div_search').on('change', 'input[type=checkbox]', function () {
                if ($(this).hasClass('checkbox_all')){
                    return;
                }
                var jq_div = $(this).parents('div:first'),
                    jq_first_input = jq_div.find('.checkbox_all');
                if (jq_first_input.length === 0){
                    return;
                }
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
                var start_date = $('#start_date').val(),
                    end_date = $('#end_date').val();
                if (!(start_date && end_date)) {
                    PT.alert('必须选择起止日期');
                    return;
                }
                if (start_date > end_date) {
                    PT.alert('起始日期不能大于终止日期');
                    return;
                }
                if (start_date < '2016-07-01') {
                    PT.alert('起始日期不能小于2016-07-01');
                    return;
                }

                var period_type = $('#period_type').val(),
                    period_millisec = new Date(end_date).getTime() - new Date(start_date).getTime(),
                    max_collumns = 9,
                    is_overload = false;
                switch (period_type) {
                    case 'month':
                        is_overload = period_millisec > max_collumns*30*24*60*60*1000;
                        break;
                    case 'week':
                    case 'ps_week':
                        is_overload = period_millisec > max_collumns*7*24*60*60*1000;
                        break;
                    default:
                        is_overload = period_millisec > max_collumns*24*60*60*1000;
                        break;
                }
                if (is_overload) {
                    PT.alert('日期分段太多，请缩小日期范围，或调大周期类型');
                    return;
                }

                var psuser_id_list = $('#div_search [name=psuser_id]:checked').map(function () {return parseInt(this.value);}).get();
                if (psuser_id_list.length == 0) {
                    PT.alert('必须选择人机人员或者TP人员');
                    return;
                }

                var metric_list = $('#div_search [name=metric]:checked').map(function () {return this.value;}).get();
                if (metric_list.length == 0) {
                    PT.alert('必须选择度量维度');
                    return;
                }

                PT.show_loading('正在加载数据');
                PT.sendDajax({
                    'function': 'ncrm_get_metric_statistic_rjjh',
                    'start_date': start_date,
                    'end_date': end_date,
                    'psuser_id_list': $.toJSON(psuser_id_list),
                    'metric_list': $.toJSON(metric_list),
                    'period_type': period_type,
                    'callback': 'PT.MetricStatisticRJJH.get_metric_statistic_rjjh_callback'
                });
            });

            // 跳转工作台搜索店铺
            $(document).on('click','a.search_shops', function () {
                var tr_obj = $(this).closest('tr'),
                    psuser_id = tr_obj.attr('psuser_id'),
                    metric_name = tr_obj.attr('metric_name'),
                    data_no = $(this).closest('td').attr('data_no'),
                    details,
                    shop_id_list = [];
                if (data_dict[psuser_id] && data_dict[psuser_id][metric_name]) {
                    var temp_obj = data_dict[psuser_id][metric_name];
                    if (data_no) {
                        details = temp_obj['data_list'][data_no]['details'];
                    } else {
                        details = temp_obj['details'];
                    }
                    if (metric_name == 'net_income') {
                        $.each(details, function (i, obj_list) {
                            $.each(obj_list, function (j, obj) {
                                if (obj.shop_id && $.inArray(obj.shop_id, shop_id_list) == -1) {
                                    shop_id_list.push(obj.shop_id);
                                }
                            });
                        });
                    } else {
                        $.each(details, function (i, obj) {
                            if (obj.shop_id && $.inArray(obj.shop_id, shop_id_list) == -1) {
                                shop_id_list.push(obj.shop_id);
                            }
                        });
                    }
                    if (shop_id_list.length > 0) {
                        window.open('/ncrm/myworkbench/?nick=' + shop_id_list.join('&nick='));
                    } else {
                        PT.alert('没有相关的店铺');
                    }
                } else {
                    PT.alert('发生异常，联系研发');
                }
            });

            // 导出单个度量维度数据
            $(document).on('click','a.export_data', function () {
                var tr_obj = $(this).closest('tr'),
                    psuser_id = tr_obj.attr('psuser_id'),
                    metric_name = tr_obj.attr('metric_name'),
                    data_no = $(this).closest('td').attr('data_no'),
                    details;
                if (data_dict[psuser_id] && data_dict[psuser_id][metric_name]) {
                    var temp_obj = data_dict[psuser_id][metric_name];
                    if (data_no) {
                        details = temp_obj['data_list'][data_no]['details'];
                    } else {
                        details = temp_obj['details'];
                    }
                    PT.show_loading('正在导出');
                    PT.sendDajax({
                        'function': 'ncrm_get_metric_details',
                        'metric_name': metric_name,
                        'details': $.toJSON(details),
                        'file_name': tr_obj.attr('psuser_name_cn') + '_' + tr_obj.attr('metric_name_cn') + '_' + $(this).attr('period_str') + '.csv',
                        'callback': 'PT.MetricStatisticRJJH.export_metric_data'
                    })
                } else {
                    PT.alert('发生异常，联系研发');
                }
            });

            // 度量趋势图
            $(document).on('click','a.metric_chart', function () {
                var this_tr = $(this).closest('tr'),
                    my_name = this_tr.attr('psuser_name_cn'),
                    metric_name = this_tr.attr('metric_name'),
                    metric_unit = this_tr.attr('metric_unit'),
                    psuser_name_cn_list = $('#metric_statistic_table td.psuser_name').map(function () {return $(this).text();}).get(),
                    category_list = $('#metric_statistic_table thead th:gt(2)').map(function () {return $(this).text();}).get(),
                    series_cfg_list = [],
                    color_list = ['#426ab3', '#87CEFA', '#06B9D1', '#005687', '#1E90FF', '#FD5B78'];

                $.each(psuser_name_cn_list, function (i, psuser_name_cn) {
                    var tr_obj = $('#metric_statistic_table tr[psuser_name_cn='+psuser_name_cn+'][metric_name='+metric_name+']'),
                        td_objs = tr_obj.children('td[data_no]:gt(0)');
                    if (td_objs.length==0) {
                        td_objs = tr_obj.children('td:last-child');
                    }
                    series_cfg_list.push({
                        'name': psuser_name_cn,
                        'value_list': $.map(td_objs, function (td) {return Number($(td).find('a.search_shops').text()) || 0}),
                        'color': color_list[i%6],
                        'visible': psuser_name_cn==my_name?true:false,
                        'unit': metric_unit,
                        'opposite': false,
                        'is_axis': i===0?1:0,
                        'yAxis': 0
                    });
                });
                $('#title_metric_chart').html($(this).text());
                $('#modal_metric_chart').modal();
                PT.draw_trend_chart('div_metric_chart', category_list, series_cfg_list);
            });
        };

    return {
        init: function () {
            init_dom();
            var args = $.evalJSON(window.localStorage['metric_statistic_rjjh'] || 0);
            if (args && args['start_date'] && args['end_date'] && args['metric_list'] && args['psuser_id_list']) {
                $('#start_date').val(args['start_date']);
                $('#end_date').val(args['end_date']);
                $('#period_type').val(args['period_type'] || '');

                $.each(args['metric_list'], function (i, metric) {
                    $('#div_search [name=metric][value='+metric+']').attr('checked', true);
                });
                $('#div_search [name=metric]:eq(0)').trigger('change');

                $.each(args['psuser_id_list'], function (i, psuser_id) {
                    $('#div_search [name=psuser_id][value='+psuser_id+']').attr('checked', true);
                });
                $('#div_search [name=psuser_id]:eq(0)').trigger('change');

                $('#search').click();
            }
        },
        export_metric_data: function (error, file_name, metric_data) {
            if (error) {
                PT.alert(error);
            } else {
                var data_str = '';
                for (var i in metric_data) {
                    data_str += metric_data[i].join(',') + '\n';
                }
                var download_link = document.createElement('a');
                download_link.href = 'data:text/csv;charset=utf-8,\ufeff' + encodeURIComponent(data_str);
                download_link.download = file_name;
                document.body.appendChild(download_link);
                download_link.click();
                document.body.removeChild(download_link);
            }
        },
        get_metric_statistic_rjjh_callback: function (error, html, metric_dict, args) {
            if (error) {
                PT.alert(error);
            } else {
                $('#metric_statistic_table').replaceWith(html);
                data_dict = metric_dict;
                window.localStorage['metric_statistic_rjjh'] = $.toJSON(args);
            }
        }
    };
}();
