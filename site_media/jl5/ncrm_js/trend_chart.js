PT.namespace('TrendChart');
PT.TrendChart = function() {
    var get_yaxis_4list= function(data) {
        var yaxis_list = [];
        for (var i = 0; i < data.length; i++) {
            if (data[i].is_axis === 0) {
                continue;
            }
            yaxis_list.push({
                'gridLineColor': '#ddd',
                'gridLineDashStyle': 'Dash',
                'gridLineWidth': 1,
                'title': {
                    'text': '',
                    'style': {
                        'color': data[i].color
                    }
                },
                'labels': {
                    'formatter': function() {
                        var temp_unit = data[i].unit;
                        return function() {
                            return this.value + temp_unit;
                        };
                    }(),
                    'style': {
                        'color': data[i].color
                    }
                },
                'opposite': data[i].opposite,
                'min':0
            });
        }
        return yaxis_list;
    };

    var get_series_4list = function(data) {
        var series_list = [];
        for (var i = 0; i < data.length; i++) {
            series_list.push({
                'name': data[i].name,
                'color': data[i].color,
                'yAxis': data[i].yaxis,
                'data': data[i].value_list,
                'visible': data[i].visible
            });
        }
        return series_list;
    };

    var get_chart_data = function(rpt_list, cfg_list) {
        var cat_list = [];
        for (var i in rpt_list) {
            cat_list.push(rpt_list[i].date);
            for (var j in cfg_list) {
                value = rpt_list[i][cfg_list[j].field_name];
                if (value === undefined) {
                    value = 0;
                }
                if (value && cfg_list[j].func) {
                    value = cfg_list[j].func(value);
                }
                cfg_list[j].value_list.push(value);
            }
        }
        for (var index in cfg_list) {
            delete cfg_list[index].func;
        }

        return [cat_list, cfg_list];
    };

    return {

        draw_trend_chart: function(id_container, rpt_list, cfg_list, title_str) {
            var chart_data = get_chart_data(rpt_list, cfg_list);
            var category_list = chart_data[0],
                series_cfg_list = chart_data[1];
            var chart = new Highcharts.Chart({
                chart: {
                    renderTo: id_container,
                    zoomType: 'xy',
                    animation: true,
                    defaultSeriesType: 'spline',
                    type: 'spline'
                },
                title: {
                    text: title_str && title_str || ''
                },
                subtitle: {
                    text: ''
                },
                xAxis: [{
                    gridLineColor: '#ddd',
                    gridLineDashStyle: 'Dash',
                    gridLineWidth: 1,
                    tickPosition: 'inside',
                    tickmarkPlacement: 'on',
                    categories: category_list,
                    labels: {
                        rotation: 30 //45度倾斜
                    },
                    offset:20
                }],
                yAxis: get_yaxis_4list(series_cfg_list),
                tooltip: {
                    formatter: function() {
                        var obj_list = chart.series;
                        var result = this.x  + "<br/>";
                        for (var i = 0; i < obj_list.length; i++) {
                            if (obj_list[i].visible) {
                                result = result + (obj_list[i].name) + " " + obj_list[i].data[this.point.x].y + (series_cfg_list[i].unit) + "<br/>"
                            }
                        }
                        return result;
                    }
                },
                legend: {
                    backgroundColor: '#FFFFFF'
                },
                series: get_series_4list(series_cfg_list),
                plotOptions: {
                    line: {
                        marker: {
                            enabled: false
                        }
                    }
                }
            });
        },
    };
}();
