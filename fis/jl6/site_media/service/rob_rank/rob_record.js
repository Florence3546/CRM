define(["template", 'widget/ajax/ajax', 'moment'], function(template, ajax, moment) {
    "use strict";

    var tpl,
        tpl = __inline('rob_record.html');

    var show = function(options) {
        var html,
            obj,
            reset = false;

        html = template.compile(tpl)(options);

        obj = $(html);

        $('body').append(obj);
        obj.modal({
            backdrop: "static"
        });

        //绑定事件
        obj.on('shown.bs.modal', function() {
            var self = this;

            ajax.ajax('rob_record', {
                keyword_id: options.keywordId
            }, function(data) {
                layoutChar(data, options);
            });
        });

        //绑定后续事件
        obj.on('hidden.bs.modal', function() {
            $(this).remove();
        });

        obj.find('.show_model .btn').on('click', function() {
            var id = $(this).data().type;
            obj.find('.show_model .btn').removeClass('active');
            $(this).addClass('active');
            $('#char_info,#table_info').addClass('hide');
            $('#' + id).removeClass('hide');
        });
   

        obj.find('.close_drawer').on('click', function() {
            obj.find('.drawer_body').removeClass('active');
        });
    }

    var layoutChar = function(data, options) {
        var dataList = [],
            tempList = [],
            htmlList = [];

        if (data.data[options.keywordId].length) {
            for (var i in data.data[options.keywordId].reverse()) {
                var obj = $.evalJSON(data.data[options.keywordId][i]);

                tempList.push(obj);

                if (obj.result_flag == 'ok' || obj.result_flag == 'nearly_ok') {
                    dataList.push({
                        flag: 'ok',
                        time: obj.rob_time,
                        price: obj.price,
                        data: tempList,
                        msg: obj.msg,
                        platform:obj.platform,
                        limit_price:obj.limit_price,
                        exp_rank_range:obj.exp_rank_range,
                        nearly_success:obj.nearly_success
                    });
                    tempList = [];
                    htmlList.push('<tr><td>' + obj.rob_time + '</td><td>' + Number(obj.price).toFixed(2) + '</td><td><img src="'+__uri("../../static/images/success.png")+'"/>' + obj.msg + '</td></tr>');
                    continue;
                }

                if (obj.result_flag == 'done' || obj.result_flag == 'failed') {
                    dataList.push({
                        flag: 'fail',
                        time: obj.rob_time,
                        price: obj.price,
                        data: tempList,
                        platform:obj.platform,
                        limit_price:obj.limit_price,
                        exp_rank_range:obj.exp_rank_range,
                        nearly_success:obj.nearly_success,
                        msg: tempList.length > 1 ? tempList[1].msg : tempList[0].msg //失败取上一次结果
                    });
                    tempList = [];
                    htmlList.push('<tr><td>' + obj.rob_time + '</td><td>' + Number(obj.price).toFixed(2) + '</td><td><img src="'+__uri("../../static/images/fail.png")+'"/>' + obj.msg + '</td></tr>');
                    continue;
                }
                
                htmlList.push('<tr><td>' + obj.rob_time + '</td><td>' + Number(obj.price).toFixed(2) + '</td><td>' + obj.msg + '</td></tr>');
            }
        }


        $('#char_info').highcharts({
            chart: {
                type: 'spline'
            },
            title: {
                text: ''
            },
            subtitle: {
                text: ''
            },
            credits: {
                text: '',
            },
            legend: {
                enabled: false,
            },
            xAxis: {
                categories: dataList.slice(-18).map(function(item) {
                    return moment(item.time).format('MM-D H:mm')
                })
            },
            yAxis: [{
                title: {
                    text: '出价(元)'
                },
                min: 0,
                gridLineColor: '#ddd',
                gridLineDashStyle: 'Dash',
                gridLineWidth: 1
            }],
            plotOptions: {
                spline: {
                    marker: {
                        radius: 4,
                        lineColor: '#666666',
                        lineWidth: 1
                    }
                }
            },
            series: [{
                cursor: 'pointer',
                name: '出价',
                lineColor: '#76a0c6',
                data: dataList.slice(-18).map(function(item) {
                    var img;
                    if (item.flag == 'ok') {
                        img = __uri('../../static/images/success.png');
                    } else {
                        img = __uri('../../static/images/fail.png');
                    }
                    return {
                        // cursor: 'pointer',
                        y: item.price,
                        events: {
                            click: function() {
                                return false;
                                layoutSignChar.call(this);
                                layoutSignTable.call(this);
                            }
                        },
                        marker: {
                            symbol: "url(" + img + ")",
                            width: 20,
                            height: 20
                        },
                        data: item
                    }
                })
            }],
            tooltip: {
                formatter: function() {
                    var data=this.point.data;
                    return '当前出价:' + this.y.toFixed(2) + '元<br/>' +
                           '平台:' + (data.platform=='yd'?'移动':'PC') + '   ' +
                           '限价:' + data.limit_price + '元<br/>' +
                           '期望排名:' + data.exp_rank_range[0]+'~'+ data.exp_rank_range[1] + '<br/>' +
                           // '抢位失败设置:' + (data.nearly_success=='0'?'恢复原价':'保留当前出价') + '<br/>' +
                            data.msg;
                }
            }
        });

        

        // for (var i in tempList) {
        //     var obj = this.data.data[i];
        //     html += '<tr><td>' + obj.rob_time + '</td><td>' + Number(obj.price).toFixed(2) + '</td><td>' + obj.msg + '</td></tr>'
        // }

        $('#table_info').find('tbody').html(htmlList.reverse().join());        
    }

    var layoutSignTable = function() {
        var html = '';

        for (var i in this.data.data) {
            var obj = this.data.data[i];
            html += '<tr><td>' + obj.rob_time + '</td><td>' + Number(obj.price).toFixed(2) + '</td><td>' + obj.msg + '</td></tr>'
        }

        $('#sign_table').find('tbody').html(html);
    }

    var layoutSignChar = function() {
        var self = this,
            platform = this.data.platform;
        $('#rob_record .drawer_body').addClass('active');

        $('#rob_record .setting').text((this.data.platform=='yd'?'移动':'PC')+'，'+this.data.exp_rank_range[0]+'~'+this.data.exp_rank_range[1]+'，限价：'+this.data.limit_price+'元')//'，抢位失败设置：'+(this.data.nearly_success=='0'?'恢复原价':'保留当前出价'))

        $('#sign_char').highcharts({
            chart: {
                type: 'spline'
            },
            title: {
                text: ''
            },
            subtitle: {
                text: ''
            },
            credits: {
                text: '',
            },
            xAxis: {
                type: 'linear',
                minTickInterval: 1,
                formatter: function() {
                    return this.value + 1;
                }
            },
            legend: {
                enabled: true,
            },
            yAxis: [{
                title: {
                    text: ''
                },
                min: 0,
                gridLineColor: '#ddd',
                gridLineDashStyle: 'Dash',
                gridLineWidth: 1
            }, {
                title: {
                    text: ''
                },
                opposite: true,
                min: 0,
                gridLineColor: '#ddd',
                gridLineDashStyle: 'Dash',
                gridLineWidth: 1,
                labels: {
                    formatter: function() {
                        return '';
                    }
                }
            }],
            plotOptions: {
                spline: {
                    marker: {
                        radius: 4,
                        lineColor: '#666666',
                        lineWidth: 1
                    }
                }
            },
            series: [{
                name: '出价',
                yAxis: 0,
                lineColor: '#76a0c6',
                marker: {
                    lineWidth: 0,
                    width: 8,
                    height: 8,
                    symbol: 'circle',
                    fillColor: '#1a8bf1'
                },
                data: self.data.data.map(function(item) {
                    var options={
                        y: Number(item.price)
                    };

                    if(item.result_flag == 'ok' || item.result_flag == 'nearly_ok'){
                        options.marker={
                            fillColor:'#1ede20',
                            states:{
                                hover:{
                                    fillColor:'#1ede20',
                                    lineColor:'#1ede20'
                                }
                            }
                        }
                    }

                    if(item.result_flag == 'done' || item.result_flag == 'failed'){
                        options.marker={
                            fillColor:'#fd5726',
                            states:{
                                hover:{
                                    fillColor:'#fd5726',
                                    lineColor:'#fd5726'
                                }
                            }
                        }
                    }
                    return options;
                })
            },
            {
                name: '排名',
                yAxis: 1,
                lineColor: '#ccc',
                marker: {
                    lineWidth: 0,
                    width: 8,
                    height: 8,
                    symbol: 'circle',
                    fillColor: '#aaa'
                },
                data: self.data.data.map(function(item) {
                    return {
                        y: item.cur_rank_dict[platform],
                        data: {
                            desc:item.cur_rank_dict[platform+'_desc'],
                            msg:item.msg,
                            pc_desc:item.cur_rank_dict.pc_desc,
                            yd_desc:item.cur_rank_dict.yd_desc,
                        }
                    };
                })
            },
            // {
            //     name: '移动排名',
            //     yAxis: 1,
            //     marker: {
            //         lineWidth: 0,
            //         width: 8,
            //         height: 8,
            //         symbol: 'circle'
            //     },
            //     data: self.data.data.map(function(item) {
            //         return {
            //             y: item.cur_rank_dict.yd,
            //             data: item.cur_rank_dict.yd_desc
            //         };
            //     })
            // }
            ],
            tooltip: {
                // crosshairs: true,
                shared: true,
                formatter: function() {
                    return '当前出价:' + this.y.toFixed(2) + '元' +
                            '<br/>pc排名:' + this.points[1].point.data.pc_desc +
                            '<br/>移动排名:' + this.points[1].point.data.yd_desc +
                            '<br/>'+this.points[1].point.data.msg;
                }
            }
        });
    }


    return {
        show: show
    }
});
