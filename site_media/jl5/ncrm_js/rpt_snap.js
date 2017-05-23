PT.namespace('RptSnap');
PT.RptSnap = function() {
    var all_rpt = [];

    var get_all_rpt = function() {
        return all_rpt;
    };

    var set_all_rpt = function(data) {
        all_rpt = data;
    };

    var get_cur_type = function() {
        return $('.nav.nav-tabs li.active').data('type');
    };

    var get_sum_days = function(type) {
        var days = 1;
        switch (type) {
            case 'day':
                days = parseInt($('input[name=rpt_sum_days]:checked').val());
                break;
            case 'week':
                days = 7;
                break;
            case 'month':
                days = 30;
                break;
            default:
                days = 1;
        }
        return days;
    };

    var get_next_day = function(date_str) {
        return new Date(new Date(date_str).getTime() + 1000*60*60*24);
    };

    var is_the_day = function(type, date_str, conv_days) {
        if (type == 'day1') {
            return conv_days == 1;
        }

        if (conv_days == 1) {
            return false;
        }

        if (type == 'day') {
            return true;
        }

        var next_day = get_next_day(date_str);
        if (type == 'week') {
            return next_day.getDay() == 1;
        } else {
            return next_day.getDate() == 1;
        }
    };

    var get_single_rpt = function(type) {
        var sum_days = get_sum_days(type),
            rpt_dict = {'shop_all': [], 'camp_mnt': [], 'camp_unmnt': [], 'camp_has_kcjl': [], 'camp_has_no_kcjl': []};

        for (var i in all_rpt) {
            if (all_rpt[i].sum_days == sum_days && is_the_day(type, all_rpt[i].date, all_rpt[i].conv_days)) {
                var rpt_type = all_rpt[i].obj_type + '_' + all_rpt[i].mnt_type;
                rpt_dict[rpt_type].push(all_rpt[i]);
            }
        }
        return rpt_dict;
    };

    var show_single_trend = function(type) {
        var rpt_dict = get_single_rpt(type);
        for (var k in rpt_dict) {
            var cfg_list = [{'name':'展现量', 'color':'#426ab3', 'func':null, 'unit':'次', 'field_name':'impressions', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':0, 'yaxis':0},
                            {'name':'点击量', 'color':'#87CEFA', 'func':null, 'unit':'次', 'field_name':'click', 'value_list':[], 'visible':false, 'opposite':false, 'is_axis':1, 'yaxis':0},
                            {'name':'平均点击花费', 'color':'#06B9D1', 'func':null, 'unit':'元', 'field_name':'cpc', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':1, 'yaxis':1},
                            {'name':'点击率', 'color':'#005687', 'func':null, 'unit':'%', 'field_name':'ctr', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':1, 'yaxis':2},
                            {'name':'花费', 'color':'#1E90FF', 'func':null, 'unit':'元', 'field_name':'cost', 'value_list':[], 'visible':false, 'opposite':true, 'is_axis':1, 'yaxis':3},
                            {'name':'成交额', 'color':'#FD5B78', 'func':null, 'unit':'元', 'field_name':'pay', 'value_list':[], 'visible':false, 'opposite':true, 'is_axis':0, 'yaxis':3},
                            // {'name':'成交笔数', 'color':'#FF84BA', 'func':null, 'unit':'笔', 'field_name':'paycount', 'value_list':[], 'visible':false, 'opposite':true, 'is_axis':0, 'yaxis':4},
                            {'name':'样本量', 'color':'#f3715c', 'func':null, 'unit':'个', 'field_name':'count', 'value_list':[], 'visible':false, 'opposite':true, 'is_axis':1, 'yaxis':4},
                            {'name':'投资回报率', 'color':'#FF0090', 'func':null, 'unit':'', 'field_name':'roi', 'value_list':[], 'visible':true, 'opposite':true, 'is_axis':1, 'yaxis':5},
                           ];
            PT.TrendChart.draw_trend_chart( 'trend_chart_' + k + '_' + type , rpt_dict[k].slice(-52), cfg_list);
        }
    };

    var get_campare_rpt = function(type) {
        var sum_days = get_sum_days(type),
            rpt_dict = {},
            rpt_field = $('input[name=rpt_field]:checked').val();
        for (var i in all_rpt) {
            if (all_rpt[i].sum_days == sum_days && is_the_day(type, all_rpt[i].date, all_rpt[i].conv_days)) {
                var rpt_date = all_rpt[i].date;
                var rpt_type = all_rpt[i].obj_type + '_' + all_rpt[i].mnt_type;
                if (!rpt_dict.hasOwnProperty(rpt_date)) {
                    rpt_dict[rpt_date] = {'shop_all': 0, 'camp_mnt': 0, 'camp_unmnt': 0, 'camp_has_kcjl': 0, 'camp_has_no_kcjl': 0, 'date': rpt_date};
                }
                rpt_dict[rpt_date][rpt_type] = all_rpt[i][rpt_field];
            }
        }
        var rpt_list = [];
        for (var j in rpt_dict) {
            rpt_list.push(rpt_dict[j]);
        }
        return rpt_list.slice(-52);
    };

    var show_campare_trend = function(type) {
        var cfg_list = [{'name':'全网店铺', 'color':'#ff0090', 'func':null, 'unit':'', 'field_name':'shop_all', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':0, 'yaxis':0},
                        {'name':'托管计划', 'color':'#f3715c', 'func':null, 'unit':'', 'field_name':'camp_mnt', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':1, 'yaxis':0},
                        {'name':'未托管计划', 'color':'#06B9D1', 'func':null, 'unit':'', 'field_name':'camp_unmnt', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':1, 'yaxis':0},
                        {'name':'托管中含开车精灵', 'color':'#1E90FF', 'func':null, 'unit':'', 'field_name':'camp_has_kcjl', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':1, 'yaxis':0},
                        {'name':'托管中不含开车精灵', 'color':'#426ab3', 'func':null, 'unit':'', 'field_name':'camp_has_no_kcjl', 'value_list':[], 'visible':true, 'opposite':false, 'is_axis':1, 'yaxis':0},
                       ];
        rpt_list = get_campare_rpt(type);
        PT.TrendChart.draw_trend_chart( 'trend_chart_camp_compare_' + type , rpt_list, cfg_list);
    };

    var init_dom = function() {

        $('input[name = rpt_sum_days]').on('change', function(){
            show_all_trend('day');
        });

        $('input[name = rpt_field]').on('change', function(){
            var type = get_cur_type();
            show_campare_trend(type);
        });

        $('.nav.nav-tabs li').on('click', function(){
            var type=$(this).data('type');
            show_all_trend(type);
        });
    };

    var show_all_trend = function(type) {
        var type_list = ['day', 'week', 'month', 'day1'];
        if (type) {
            type_list = [type];
        }
        for (var i in type_list) {
            show_single_trend(type_list[i]);
            show_campare_trend(type_list[i]);
        }
    };

    return {
        init: function() {
            init_dom();
            PT.show_loading('正在加载数据');
            PT.sendDajax({'function': 'ncrm_get_rpt_snap'});
        },

        get_data_back: function(data) {
            set_all_rpt(data);
            show_all_trend('day');
        }
    };
}();
