define(["highcharts"], function(highcharts) {
    "use strict";

    var get_series_4list=function(data) {
        var series_list = [];
        for (var i = 0; i < data.length; i++) {
            series_list.push({
                'name': data[i].name,
                'color': data[i].color,
                'type': 'spline',
                'yAxis': data[i].yaxis,
                'data': data[i].value_list,
                'visible': data[i].visible,
                'marker': {
                    // 'enabled': false,
                    'radius': 3
                }
            });
        }
        return series_list;
    }

    var get_yaxis_4list=function(data) {
        var yaxis_list = [];
        for (var i = 0; i < data.length; i++) {
            if (data[i].is_axis == 0) {
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
                'min': 0
            });
        }
        return yaxis_list;
    }

    var draw_trend_chart=function(id_container, category_list, series_cfg_list) {
        var chart = new Highcharts.Chart({
            chart: {
                renderTo: id_container,
                zoomType: 'xy',
                animation: true
            },
            credits:{
                text:'',
            },
            title: {
                text: ''
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
                offset: 20
            }],
            yAxis: get_yaxis_4list(series_cfg_list),
            tooltip: {
                formatter: function() {
                    var obj_list = chart.series;
                    var result = this.x + '日 ' + "<br/>";
                    for (var i = 0; i < obj_list.length; i++) {
                        if (obj_list[i].visible) {
                            result = result + (obj_list[i].name) + " " + obj_list[i].data[this.point.x].y + (series_cfg_list[i].unit) + "<br/>"
                        }
                    }
                    return result;
                }
            },
            legend: {
                backgroundColor: '#FFFFFF',
                symbolWidth: 3,
                itemStyle: {
                    fontWeight: 'normal'
                }
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
    }

    return {
        draw: draw_trend_chart
    }
});
