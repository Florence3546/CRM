//PT是paithink的缩写，以此缩写开创一个命名空间
var PT = function() {
    return {
        namespace: function(ns) {
            var parts = ns.split("."),
                object = this,
                i, len;
            for (i = 0, len = parts.length; i < len; i++) {
                if (!object[parts[i]]) {
                    object[parts[i]] = {};
                }
                object = object[parts[i]];
            }
            return object;
        },
        alert: function(msg, color, call_back, argv, that, timeout) {
            //自定义Alert()信息
            var has_modal = false,
                alert_conf = {
                    backdrop: 'static',
                    bgColor: '#000',
                    keyboard: true,
                    title: '精灵提醒',
                    body: '<span>' + msg + '</span>'
                };

            $('.modal').each(function() {
                if ($(this).attr('class').indexOf('in') !== -1) {
                    has_modal = true;
                    return;
                }
            });

            //如果有遮罩则不显示遮罩
            if ($('.modal-backdrop:visible').length && has_modal) {
                alert_conf.backdrop = false;
                $('.modal:visible').modal('shadeIn');
            }

            if (call_back !== undefined && call_back instanceof Function) {
                alert_conf.okHidden = function() {
                    return function() {
                        call_back.apply(that, argv||[]);
                    }();
                };
            } else {
                alert_conf.okHidden = function() {
                    $('.modal:visible').modal('shadeOut');
                };
            }
            $.alert(alert_conf);
        },
        confirm: function(msg, call_back, argv, that, cancel_call_back, cancel_argv, cancel_that, btn_text_list) {
            //自定义confirm()信息
            var confirm_conf = {
                backdrop: 'static',
                bgColor: '#000',
                keyboard: true,
                title: '精灵提醒',
                body: '<span>' + msg + '</span>'
            };

            if (btn_text_list !== undefined) {
                confirm_conf.okBtn = btn_text_list[0];
                confirm_conf.cancelBtn = btn_text_list[1];
            }

            if (call_back !== undefined && call_back instanceof Function) {
                confirm_conf.okHidden = function() {
                    return function() {
                        call_back.apply(that, argv||[]);
                    }();
                };
            }
            if (cancel_call_back !== undefined && cancel_call_back instanceof Function) {
                confirm_conf.cancelHidden = function() {
                    return function() {
                        cancel_call_back.apply(cancel_that, cancel_argv||[]);
                    }();
                };
            }
            $.confirm(confirm_conf);
        },
        sendDajax: function(jdata) {
            //统一ajax请求接口,发起ajax请求jdata中至少要有一个参数且名字为function,例:sendDajax({'function':'test'})
            //如果有别的参数直接传jsaon 例子:sendDajax({'function':'test','day':1})
            if (!jdata.hasOwnProperty('function')) {
                $('#center_tip_popup').hide();
                PT.alert('sendDajax:缺少必要参数[function]', 'red');
                return false;
            }
            var q, data = {},
                mArray = jdata['function'].split('_');
            for (q in jdata) {
                data[q] = jdata[q];
            }
            data['function'] = mArray.slice(1).join('_');
            Dajax.dajax_call(mArray[0], data['router_path']||'route_dajax', data);
        },
        show_loading: function(msg, lock,transparent) {
            //显示全屏tip消息，并锁定屏幕，禁止滚屏
            var obj = $('#full_screen_tips');
            obj.find('.msg').text(msg + '，请稍候...');
            if (lock) {
                $('body').addClass('modal-open'); //锁定屏幕，禁止滚屏
            }
            if(transparent){
                obj.find('.modal-backdrop').hide();
            }
            obj.show();
        },
        hide_loading: function() {
            //隐藏全屏tip消息
            if ($('.modal-backdrop').length == 1) {
                $('body').removeClass('modal-open');
            }
            $('#full_screen_tips').hide();
            $('#full_screen_tips').find('.modal-backdrop').show();
        },
        true_length: function(str) {
            //获取中英混合真实长度
            var l = 0;
            for (var i = 0; i < str.length; i++) {
                if (str[i].charCodeAt(0) < 299) {
                    l++;
                } else {
                    l += 2;
                }
            }
            return l;
        },
        truncate_str_8true_length: function(str, l) {
            //根据指定的中英混合真实长度截断字符串
            if (PT.true_length(str) <= l) {
                return str;
            } else {
                var ll = 0;
                for (var i = 0; i < str.length; i++) {
                    if (str.charCodeAt(i) < 299) {
                        ll++;
                    } else {
                        ll += 2;
                    }
                    if (ll > l - 2) {
                        return str.slice(0, i) + '...';
                    }
                }
            }
        },
        get_yaxis_4list: function(data) {
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
                    'min':0
                });
            }
            return yaxis_list;
        },
        get_series_4list: function(data) {
            var series_list = [];
            for (var i = 0; i < data.length; i++) {
                series_list.push({
                    'name': data[i].name,
                    'color': data[i].color,
                    'type': 'line',
                    'yAxis': data[i].yaxis,
                    'data': data[i].value_list,
                    'visible': data[i].visible,
                    'marker':{'enabled': true}
                });
            }
            return series_list;
        },
        draw_trend_chart: function(id_container, category_list, series_cfg_list) {
            var chart = new Highcharts.Chart({
                chart: {
                    renderTo: id_container,
                    zoomType: 'xy',
                    animation: true
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
                    offset:20
                }],
                yAxis: PT.get_yaxis_4list(series_cfg_list),
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
                    symbolWidth: 3
                },
                series: PT.get_series_4list(series_cfg_list),
                plotOptions: {
                    line: {
                        marker: {
                            enabled: false
                        }
                    }
                }
            });
        },
        light_msg: function(title, text, time, direction, class_name) {
            /**
             * class_name: gritter-light 白色
             * direction: 控制方向
             */
            !time ? time = 8000 : '';
            !class_name ? class_name = 'my-sticky-class' : '';
            !direction ? direction = 'bottom-right' : '';
            $.extend($.gritter.options, {
                position: direction
            });
            var comm_gritter = $.gritter.add({
                title: title,
                text: text,
                sticky: true,
                class_name: class_name
            });
            setTimeout(function() {
                $.gritter.remove(comm_gritter, {
                    fade: true,
                    speed: 'slow'
                });
            }, time);
        },
        DBCLICK_ENABLED: true, //防止重复点击的全局变量，需自己实现
        set_habit: function(json) {
            var habit=window.localStorage.getItem('habit');
            if(habit===null){
                habit=json;
                 window.localStorage.setItem('habit',$.toJSON(habit));
                return json;
            }

            try{
                habit=$.parseJSON(habit);
            }catch(e){
                habit={};
            }finally{
                for (i in json){
                    habit[i]=json[i]
                }
                 window.localStorage.setItem('habit',$.toJSON(habit));
                return habit;
            }
        },
        get_habit: function() {
            if(window.localStorage.getItem('habit')!==null){
                return $.parseJSON(window.localStorage.getItem('habit'));
            }
            return undefined;
        },
        show_top_info: function(msg){			
            $('#top_info').html(msg).addClass('active');
            $('#top_info').on('click','a[data-dismiss="top_info"]',function(){
                $('#top_info').removeClass('active');
            });
        },
        hide_top_info: function(){
            $('#top_info').removeClass('active');
        },
        init_editors: function (selector, value) {
            editorBox = $(selector).xheditor({
                tools: 'Blocktag,Fontface,FontSize,Bold,Italic,Underline,Strikethrough,FontColor,BackColor,|,Align,List,Outdent,Indent,|,Link,Emot,Fullscreen,Source',
                height: 200
            });
            editorBox.setSource(value);
        }
    };
}();


//shift多选用法 1:带回调函数:$select(checkBoxName) 2:带回调 $select({name:checkBoxName,[callBack:fn]})
(function() {
    var arrList = {};
    var $select = window.$select = function(obj) {
        var checkboxName;
        if (typeof(obj) == 'string') {
            checkboxName = obj;
        }
        if (typeof(obj) == 'object') {
            checkboxName = obj.name;
        }

        // Meet the condition of 'checkbox' save into array
        arrList[checkboxName] = getCheckboxArray(checkboxName);

        // Add event for meet the condition of 'checkbox'
        for (var i = 0, i_end = arrList[checkboxName].length; i < i_end; i++) {
            // Left mouse and shift button event
            ! function() {
                var current = arrList[checkboxName][i];
                current.onclick = function() {
                    var afterClickStatus = current.checked ? true : false;
                    mainFunc(current, arrList[current.name], afterClickStatus, obj);
                };

                // Right mouse event
                current.onmouseup = function(e) {
                    var e = window.event || e;
                    if (e.button == 2) {
                        var afterClickStatus = current.checked ? false : true;
                        pressShift = true;
                        mainFunc(current, arrList[current.name], afterClickStatus, obj);
                        pressShift = false;
                    }
                };

                // (For IE) Right mouse event
                current.oncontextmenu = function(event) {
                    if (document.all) {
                        window.event.returnValue = false;
                    } else {
                        event.preventDefault();
                    }
                };
            }();
        }

        // 当checkbox顺序变了之后调用此函数更新
        selectRefresh = function() {
            setTimeout(function() {
                for (var a in arrList)
                    arrList[a] = getCheckboxArray(a);
            }, 1);
            initSelect();
        };
        //表头变化后重置起止位置
        initSelect = function() {
            startEnd = [null, null];
        };
    };

    function getCheckboxArray(checkboxName) {
        var arr = [];
        var inputs = document.getElementsByTagName("input");
        for (var i = 0; i < inputs.length; i++) {
            if (inputs[i].name == checkboxName && inputs[i].type == "checkbox") {
                arr.push(inputs[i]);
            }
        }
        return arr;
    }

    function getIndex(arr, obj) {
        for (var i = 0, index = 0; i < arr.length; i++, index++) {
            if (arr[i] == obj) {
                return index;
            }
        }
    }

    var pressShift = false;
    var startEnd = [null, null];

    function mainFunc(current, arr, afterClickStatus, obj) {
        // Get the index which click element in the 'checkbox' array
        var index = getIndex(arr, current);

        if (startEnd[0] == null)
            startEnd[0] = index;
        // 'shift button' whether is press
        if (pressShift) {
            startEnd[1] = index;
            // If select the 'checkbox' from the down top, reverse the array
            if (startEnd[0] > startEnd[1]) {
                startEnd.reverse();
            }

            // Select the 'checkbox'
            for (var j = startEnd[0]; j <= startEnd[1]; j++) {
                if (!arr[j].disabled) {
                    arr[j].checked = afterClickStatus;
                }
            }
            startEnd[0] = startEnd[1];
        }
        startEnd[0] = index;
        if (obj.hasOwnProperty('callBack')) {
            obj.callBack.call(obj.that);
        }
    }
    /*<For left mouse and shift button event>*/
    document.onkeydown = function(e) {
        var e = window.event || e;
        if (e.keyCode == 16) {
            pressShift = true;
        } else {
            pressShift = false;
        }
    };
    document.onkeyup = function() {
        pressShift = false;
    };
})();

/*
//使用方法
var now = new Date();
var nowStr = now.format("yyyy-MM-dd hh:mm:ss");
//使用方法2:
var testDate = new Date();
var testStr = testDate.format("YYYY年MM月dd日hh小时mm分ss秒");
alert(testStr);
//示例：
alert(new Date().Format("yyyy年MM月dd日"));
alert(new Date().Format("MM/dd/yyyy"));
alert(new Date().Format("yyyyMMdd"));
alert(new Date().Format("yyyy-MM-dd hh:mm:ss"));
*/

Date.prototype.format = function(format) {
    var o = {
        "M+": this.getMonth() + 1, //month
        "d+": this.getDate(), //day
        "h+": this.getHours(), //hour
        "m+": this.getMinutes(), //minute
        "s+": this.getSeconds(), //second
        "q+": Math.floor((this.getMonth() + 3) / 3), //quarter
        "S": this.getMilliseconds() //millisecond
    };

    if (/(y+)/.test(format)) {
        format = format.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    }

    for (var k in o) {
        if (new RegExp("(" + k + ")").test(format)) {
            format = format.replace(RegExp.$1, RegExp.$1.length == 1 ? o[k] : ("00" + o[k]).substr(("" + o[k]).length));
        }
    }
    return format;
};
