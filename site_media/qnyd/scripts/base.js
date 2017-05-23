LOADING_BOX = $('#loading');
LOADING_BOX_INFO = $('#loading .loading_info');

! function () {
    if ($('#main_nav').length) {
        $('#main_nav').css({
            'top': 0,
            'marginTop': $('#main_nav')[0].offsetTop + 2
        });
    }
    $(window).scroll(function () {
        if (typeof PTQN.that == 'undefined' || PTQN.that.loader_Sign == undefined) {
            return;
        }
        var base = PTQN.that.loader_Sign.offset()['top'];
        var body_ofset = document.body.scrollTop;
        var clientH = document.documentElement.clientHeight
        if (base <= (body_ofset + clientH + 200)) { //如果该元素的距离页面顶部的距离 = 浏览器可视高度+滚动高度
            PTQN.that.init_more_data();
        }
    });

}();


PTQN = function () {
    return {
        namespace: function (ns) {
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
        alert: function (msg, call_back, argv, that) {
            //自定义Alert()信息
            var handle = $('#PT_alert');
            handle.find('.alert_box_content').html(msg);

            handle.find('.alert_btn').off('touchend').on('touchend', function (e) {
                return function (e) {
                    e.preventDefault();
                    handle.fadeOut(83);
                    setTimeout(function () {
                        if (call_back != undefined && call_back instanceof Function) {
                            if (that == undefined) {
                                that = null;
                            }
                            call_back.apply(that, argv);
                        }
                    }, 100);
                }
            }());
            handle.fadeIn(83);
        },
        confirm: function (msg, call_back, argv, that, cancel_call_back, cancel_argv, cancel_that) {
            //自定义confirm()信息
            var handle = $('#PT_confirm');
            handle.find('.alert_box_content').html(msg);

            handle.find('.ok').off('touchend').on('touchend', function (e) {
                return function (e) {
                    e.preventDefault();
                    setTimeout(function () {
                        handle.fadeOut(83);
                        if (call_back != undefined && call_back instanceof Function) {
                            if (that == undefined) {
                                that = null;
                            }
                            call_back.apply(that, argv);
                        }
                    }, 100)
                }
            }());
            handle.find('.no').off('touchend').on('touchend', function (e) {
                return function (e) {
                    e.preventDefault();
                    setTimeout(function () {
                        handle.fadeOut(83);
                        if (cancel_call_back != undefined && cancel_call_back instanceof Function) {
                            if (cancel_that == undefined) {
                                cancel_that = that;
                            }
                            cancel_call_back.apply(cancel_that, cancel_argv);
                        }
                    }, 100)
                }
            }());
            handle.fadeIn(300);
        },
        'show_loading': function (msg) {
            //显示提示
            if (msg == undefined) {
                msg = '正在加载数据';
            }
            LOADING_BOX_INFO.text(msg);
            LOADING_BOX.show();
        },
        'hide_loading': function () {
            //隐藏提示
            LOADING_BOX.hide();
        },
        sendDajax: function (jdata) {
            //统一ajax请求接口,发起ajax请求jdata中至少要有一个参数且名字为function,例:sendDajax({'function':'test'})
            //如果有别的参数直接传jsaon 例子:sendDajax({'function':'test','day':1})
            if (!jdata.hasOwnProperty('function')) {
                $('#center_tip_popup').hide();
                PTQN.alert('sendDajax:缺少必要参数[function]', 'red');
                return false;
            }
            var q, data = {},
                mArray = jdata['function'].split('_');
            for (q in jdata) {
                data[q] = jdata[q];
            }
            data['function'] = mArray.slice(1).join('_');
            Dajax.dajax_call(mArray[0], 'route_dajax', data);
        },
        cookie: function (name, value, options) {
            if (typeof value != 'undefined') { // name and value given, set cookie
                options = options || {};
                if (value === null) {
                    value = '';
                    options.expires = -1;
                }
                var expires = '';
                if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) {
                    var date;
                    if (typeof options.expires == 'number') {
                        date = new Date();
                        date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
                    } else {
                        date = options.expires;
                    }
                    expires = '; expires=' + date.toUTCString(); // use expires attribute, max-age is not supported by IE
                }
                var path = options.path ? '; path=' + options.path : '';
                var domain = options.domain ? '; domain=' + options.domain : '';
                var secure = options.secure ? '; secure' : '';
                document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join('');
            } else { // only name given, get cookie
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = cookies[i];
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
        },
        draw_chart: function (id, x, series) {
            if (!$('#' + id).length) {
                return;
            }

            lalal = new Highcharts.Chart({
                chart: {
                    renderTo: id,
                    type: 'line'
                },
                title: null,
                credits: {
                    text: null,
                },
                xAxis: {
                    categories: x //['12-18', '12-18', '12-18','12-18', '12-18', '12-18','12-18']
                },
                yAxis: {
                    title: null
                },
                series: series
                //[{
                //	name: '成交额',
                //	data: [1, 800, 400,100,20,30,88]
                //}, {
                //	name: '总花费',
                //	data: [88, 7, 3,60,984,1651,4861]
                //}]
            })

        },
        router: function (page_name) {
            setTimeout(function () {
                try {
                    eval('PTQN.' + page_name + '.init()')
                } catch (e) {
                    console.error(e)
                }
            }, 0);
        },
        show_animate_layer: function (html) {
            $('body').addClass('hidden');
            $('#animate_layer .main').html(html);
            $('#animate_layer').css('z-index', 11).fadeIn(300);
        },
        light_msg: function (msg, type, time) {
            if (type == undefined) {
                type = "blue";
            }
            if (time == undefined) {
                time = 3000;
            }
            if ($('.light_msg_box').length) {
                $('.light_msg_box').animate({
                    top: -35
                }, 300, 'ease-out', function () {
                    this.remove();
                });
            }
            var hander = $('<div class="light_msg_box ' + type + '"><div class="light_msg_box_inner">' + msg + '</div></div>');
            $('body').append(hander);
            hander.animate({
                top: 0
            }, 300, 'ease-out', function () {
                setTimeout(function () {
                    hander.animate({
                        top: -hander.height()
                    }, 300, 'ease-out', function () {
                        hander.remove();
                    });
                }, time);
            });
        }
    }
}();

//兼容现网版的js
PT = PTQN;