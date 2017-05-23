define(["template", 'widget/ajax/ajax', 'moment','highcharts'], function(template, ajax, moment) {
    "use strict";

    var tpl = __inline('real_time.html');
    var char;

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

        if(options.method == 'auto'){
            obj.find('#rob_tips').removeClass('hide');
        }

        //绑定事件
        obj.on('shown.bs.modal', function() {
            var self = this;
            startWebSocket(options);

            getAndSetChat();

            $(this).find('.reset').on('click', function() {
                reset = true;
                $(self).modal('hide');
            });
        });

        //绑定后续事件
        obj.on('hidden.bs.modal', function() {
            if (reset) {
                $('#' + options.keywordId).trigger('get.rob_set', [options]);
            }
            $(this).remove();
            destroyChar();
            // ws.close();
            // ws = undefined;
        });

        obj.find('.show_model a').on('click',function(){
            var id=$(this).data().type;
            obj.find('.show_model a').removeClass('active');
            $(this).addClass('active');
            $('#rob_chat,#rob_sub_info').addClass('hide');
            $('#'+id).removeClass('hide');
        });
    }

    var startWebSocket = function(options) {
        var url,
            ws;

        url = 'ws://' + window.location.host + '/websocket/?keyword_id=' + options.keywordId

        ws = new WebSocket(url);

        ws.onmessage = function(msg) {
            if (msg != '' && msg != undefined) {
                if (msg.data == 'ready') {
                    startRobRank(options);
                    return false;
                }
                var content = $.evalJSON(msg.data);
                showRobMsg(options, content, ws);
            } else {
                console.log("error");
            }
        };
    }

    var startRobRank=function(options){
        //发送手动抢排名请求
        ajax.ajax('manual_rob_rank', {
            keyword_id: options.keywordId,
            adgroup_id: options.adgroupId,
            exp_rank_start: options.rank_start,
            exp_rank_end: options.rank_end,
            limit_price: parseInt(options.limit*100+0.5),
            platform: options.platform,
            nearly_success: options.nearly_success
        },function(data){
            if (data.limitError != '') {
                var title,
                    body;

                if (data.limitError == 'version_limit') {
                    title = 'Sorry!当前版本不支持';
                    body = '亲，您订购的版本不支持手动抢排名哦，请升级到双引擎版！&emsp;&emsp;<a href="/web/upgrade_suggest/" target="_blank">立即升级</a></div></div>';
                }

                if (data.limitError == 'others') {
                    title = 'Sorry，自动抢排名失败';
                    body = '亲，请刷新页面重试';
                }
                $.alert({title:title,closeBtn: false, body: body, okBtn:'知道了', height:"60px", backdrop:"static", keyboard:false});
            }
        });

    }

    var showRobMsg = function(options, msg, ws) {
        var obj = $('#real_time'),
            trObj = $('#' + options.keywordId),
            flag = 'doing';

        if (msg.result_flag == 'ok' || msg.result_flag == 'nearly_ok') {
            obj.find('.main_info').addClass('success');
            obj.find('.finished_status').text('抢排名成功');
            obj.find('#rob_tips').text('设置抢排名成功：系统将在您 指定的时间段内每隔15~30分钟自动为关键词抢排名');

            //修改表格的排名
            trObj.trigger('update.rank', [msg.cur_rank_dict.pc, msg.cur_rank_dict.yd, msg.cur_rank_dict.pc_desc, msg.cur_rank_dict.yd_desc]);

            if (options.target != "rank") {
                trObj.trigger('update.rob_rank', ['success', Number(msg.price).toFixed(2), msg.platform]);
            }

            flag = 'finish';
            ws.close();
        }

        if (msg.result_flag == 'done' || msg.result_flag == 'failed') {
            obj.find('.main_info').addClass('fail');
            obj.find('.finished_status').text('抢排名失败');
            obj.find('#rob_tips').text('测试抢排名失败：建议你重新设置提高限价');

            //修改表格的排名
            trObj.trigger('update.rank', [msg.cur_rank_dict.pc, msg.cur_rank_dict.yd, msg.cur_rank_dict.pc_desc, msg.cur_rank_dict.yd_desc]);

            if (options.target != "rank") {
                trObj.trigger('update.rob_rank', ['fail']);
            }
            flag = 'finish';
            ws.close();
        }

        getAndSetChat(msg);

        obj.find('ol').append("<li class='" + flag + "''><span>" + moment(msg.rob_time).format('H:mm:ss') + "<span class='r'>" + Number(msg.price).toFixed(2) + "元</span></span><span>" + msg.msg + "</span></li>");

        obj.find('.main_info .price').text(Number(msg.price).toFixed(2));
        obj.find('.main_info .msg').text(msg.msg);
    }


    //注销图表
    var destroyChar=function(){
        char = undefined;
    }

    var getAndSetChat = function(msg) {
        if (!char) {
            char = $('#rob_chat').highcharts({
                chart: {
                    type: 'spline'
                },
                title: {
                    text: ''
                },
                subtitle: {
                    text: ''
                },
                legend: {
                    enabled: true,
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
                yAxis: [{
                    title: {
                        text: ''
                    },
                    min: 0,
                    gridLineColor: '#ddd',
                    gridLineDashStyle: 'Dash',
                    gridLineWidth: 1
                },{
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
                    lineColor: '#76a0c6',
                    marker: {
                        lineWidth: 0,
                        width: 8,
                        height: 8,
                        symbol: 'circle',
                        fillColor: '#1a8bf1'
                    }

                },{
                    name: '排名',
                    yAxis: 1,
                    lineColor: '#ccc',
                    // dashStyle: 'shortdot',
                    marker: {
                        lineWidth: 0,
                        width: 8,
                        height: 8,
                        symbol: 'circle',
                        fillColor: '#aaa'
                    }

                }],
                tooltip: {
                    crosshairs: true,
                    shared: true,
                    formatter: function() {
                        return '当前出价:' + this.y.toFixed(2) + '<br/>' + this.points[0].point.data;
                    }
                }
            });
        } else {
            var options={
                y: Number(msg.price),
                data: msg.msg
            };

            if(msg.result_flag == 'ok' || msg.result_flag == 'nearly_ok'){
                options.marker={
                    // symbol: "url("+__uri('../../static/images/success.png')+")",
                    // width:20,
                    // height:20
                    fillColor:'#1ede20',
                    states:{
                        hover:{
                            fillColor:'#1ede20',
                            lineColor:'#1ede20'
                        }
                    }
                }
            }

            if(msg.result_flag == 'done' || msg.result_flag == 'failed'){
                options.marker={
                    // symbol: "url("+__uri('../../static/images/fail.png')+")",
                    // width:20,
                    // height:20
                    fillColor:'#fd5726',
                    states:{
                        hover:{
                            fillColor:'#fd5726',
                            lineColor:'#fd5726'
                        }
                    }
                }
            }

            $('#rob_chat').highcharts().series[0].addPoint(options);
            $('#rob_chat').highcharts().series[1].addPoint({
                y:msg.cur_rank_dict.pc,
                data: msg.msg
            });
        }
    }

    return {
        show: show
    }
});
