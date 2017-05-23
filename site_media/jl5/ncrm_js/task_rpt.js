PT.namespace('TaskRpt');
PT.TaskRpt = function() {
    var data_dict = {};
    var tj_type_dict = {'hour': '每小时报表', 'day': '天报表', 'month': '月报表', 'by_hour': '按小时汇总'};
    var index_dict = {'hour': [0, 13], 'day': [0, 10], 'month': [0, 7], 'by_hour': [11, 13]}; // '2015-05-12 16'
    var cfg_dict = {'info': [
                             {'name':'待执行大任务数', 'color':'#426ab3', 'func':null, 'unit':'', 'field_name':'get_task_list_shop_task', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':1, 'yaxis':0},
                             {'name':'大任务成功数', 'color':'#005687', 'func':null, 'unit':'', 'field_name':'shop_task_result_ok', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':0, 'yaxis':0},
                             {'name':'大任务失败数', 'color':'#1E90FF', 'func':null, 'unit':'', 'field_name':'shop_task_result_failed', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':0, 'yaxis':0},
                             {'name':'待执行快速任务数', 'color':'#87CEFA', 'func':null, 'unit':'', 'field_name':'get_task_list_mnt_quick_task', 'value_list':[], 'visible':false, 'opposite':true, 'is_axis':1, 'yaxis':1},
                             {'name':'待执行例行任务数', 'color':'#06B9D1', 'func':null, 'unit':'', 'field_name':'get_task_list_mnt_routine_task', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':0, 'yaxis':1},
                             {'name':'全自动任务成功数', 'color':'#FD5B78', 'func':null, 'unit':'', 'field_name':'mnt_task_result_ok', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':1, 'yaxis':2},
                             {'name':'全自动任务失败数', 'color':'#FD5777', 'func':null, 'unit':'', 'field_name':'mnt_task_result_failed', 'value_list':[], 'visible':false, 'opposite':true, 'is_axis':1, 'yaxis':3},
                             {'name':'全自动任务不能执行数', 'color':'#FF84BA', 'func':null, 'unit':'', 'field_name':'mnt_task_result_unable', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':0, 'yaxis':3},
                             ],
                    'error': [{'name':'淘宝内部错误', 'color':'#426ab3', 'func':null, 'unit':'', 'field_name':'isp', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':1, 'yaxis':0},
                              {'name':'session过期', 'color':'#87CEFA', 'func':null, 'unit':'', 'field_name':'session', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':0, 'yaxis':0},
                              {'name':'流控', 'color':'#06B9D1', 'func':null, 'unit':'', 'field_name':'limited', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':0, 'yaxis':0},
                              {'name':'其他已知错误', 'color':'#FF84BA', 'func':null, 'unit':'', 'field_name':'mnt_task_result_unable', 'value_list':[], 'visible':true, 'opposite':true, 'is_axis':1, 'yaxis':1},
                              {'name':'其他未知错误', 'color':'#005687', 'func':null, 'unit':'', 'field_name':'others', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':1, 'yaxis':2},
                              {'name':'日志格式不规范', 'color':'#1E90FF', 'func':null, 'unit':'', 'field_name':'unformart', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':0, 'yaxis':1},
                              {'name':'解析日志出错', 'color':'#FD5B78', 'func':null, 'unit':'', 'field_name':'unknow_e', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':0, 'yaxis':1},
                              ]
                    };

    var init_data = function(data) {
        data_dict = data;
    };

    var get_deep_copy = function(obj) {
        return JSON.parse(JSON.stringify(obj));
    };

    var sort_by_date = function(a, b) {
        if (a.date > b.date) {
            return 1;
        }
        if (a.date < b.date) {
            return -1;
        }
        return 0;
    };

    var init_html = function(){
        var html_dict = {'info': {'jq_id': 'tab1', 'html_str': ''}, 'error': {'jq_id': 'tab2', 'html_str': ''}},
            str_1 = "<div class='h400 w1287 mb40' id='trend_",
            str_2 = "'></div>";
        for (var i in html_dict) {
            for (var key in tj_type_dict) {
                html_dict[i].html_str += str_1 + i + '_' + key + str_2;
            }
            $('#'+html_dict[i].jq_id).html(html_dict[i].html_str);
        }
    };

    var get_trend_data = function(log_type, tj_type) {
        var rpt_list = [],
            rpt_dict = {},
            s_index = index_dict[tj_type][0],
            e_index = index_dict[tj_type][1];
        for (var i in data_dict[log_type]) {
            var key = i.slice(s_index, e_index);
            if (! rpt_dict.hasOwnProperty(key)) {
                rpt_dict[key] = {'date': key};
            }
            for (var j in data_dict[log_type][i]) {
                if(! rpt_dict[key].hasOwnProperty(j)) {
                    rpt_dict[key][j] = 0;
                }
                rpt_dict[key][j] += data_dict[log_type][i][j];
            }
        }
        for (var k in rpt_dict) {
            rpt_list.push(rpt_dict[k]);
        }
        rpt_list.sort(sort_by_date);
        return rpt_list.slice(-52);
    };

    var show_trend = function(log_type, tj_type) {
        var cfg_list = get_deep_copy(cfg_dict[log_type]);
        rpt_list = get_trend_data(log_type, tj_type);
        var contain_id = 'trend_' + log_type + '_' + tj_type;
        PT.TrendChart.draw_trend_chart(contain_id, rpt_list, cfg_list, tj_type_dict[tj_type]);
    };


    var init_dom = function() {

        // $('.nav.nav-tabs li').on('click', function(){
        //     var type=$(this).data('type');
        //     show_all_trend(tj_type);
        // });
    };

    var show_all_trend = function() {
        for (var log_type in cfg_dict) {
            for (var tj_type in tj_type_dict) {
                show_trend(log_type, tj_type);
            }
        }
    };

    return {
        init: function(data) {
            init_html();
            init_dom();
            PT.show_loading('正在加载数据');
            PT.sendDajax({'function': 'ncrm_get_timer_log'});
        },

        get_data_back: function(data) {
            init_data(data);
            show_all_trend();
        }

    };
}();
