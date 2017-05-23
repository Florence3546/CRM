PTQN.namespace('base');
PTQN.Base = function () {
    var init_dom_execute = false;

    var init_dom = function () {

        $('#animate_layer').on('click', '#auto_set', function () {
            auto_set_attention_kw();
            return false;
        });

        $('#animate_layer .tab-item').click(function (e) {
            e.stopPropagation();
            $('#animate_layer').fadeOut(300).css('z-index', 0);
            $('body').removeClass('hidden');
        });

        $('.alert_box').on('touchmove', function (e) {
            e.preventDefault();
        });

        $('.call_wangwang').on('click', function () {
            TOP.mobile.ww.chat({
                chatNick: '派生科技',
                text: '来自千牛移动：',
                domain_code: "taobao"
            });
        });

        $(document).on('click', '#id_submit_info', function(){
            var qq = $('#id_qq').val(),
                phone = $('#id_phone').val();
            if(isNaN(phone) || !(/^1[3|4|5|7|8]\d{9}$/.test(phone))){
                PTQN.light_msg("手机号码填写不正确！");
                return false;
            }
            PTQN.sendDajax({'function':'qnyd_submit_phone', 'phone':phone, 'qq':qq});
            PTQN.show_loading();
        });
    };

    var auto_set_attention_kw = function () {
        PTQN.show_loading('获取报表中，请稍后');
        PTQN.sendDajax({
            'function': 'qnyd_auto_set_attention_kw'
        });
    };

    return {
        'init': function () {
            if (!init_dom_execute) {
                init_dom();
                init_dom_execute = true;
            }
        },
        'attention_call_back': function (result) {
            if (result) {
                $('.PT_page').addClass('hide');
                $('#keyword_manage').removeClass('hide');

                $('nav .tab-item').removeClass('active');
                $('#keyword_manage_link').parent().addClass('active');

                //改变浏览器URL,以便于刷新操作
                history.pushState('keyword_manage', "", 'keyword_manage');

                //调用对应的函数
                PTQN.router('keyword_manage');
            } else {
                PTQN.show_animate_layer($('#set_attention_page').html());
            }
        },
        'sync_result': function (msg) {
            PTQN.light_msg(msg);
            var index = 4;
            if (msg.indexOf('直通车') != -1) {
                index = 0;
            }
            if (msg.indexOf('报表') != -1) {
                index = 1;
            }
            if (msg.indexOf('结构') != -1) {
                index = 2;
            }
            $('#sync_ul button:eq(' + index + ')').removeClass('disabled');

            if (msg.indexOf('错误') != -1 || index == 4) {
                $('#sync_ul button').removeClass('disabled');
                return false;
            }
        },
        'submit_feedback_back': function (result_flag) {
            PT.hide_loading();
            if (result_flag === 0) {
                PT.alert('亲，提交失败，非常抱歉，麻烦将意见发给您的顾问');
            } else {
                PT.alert('提交成功，感谢您的参与！我们会及时处理您的意见');
            }
        },
        'submit_phone_back': function (is_success) {
            if (is_success) {
                PTQN.light_msg('提交成功，感谢您的信任和支持');
            }
            $('#account').data('isneed-phone', 0);
            $('#animate_layer').fadeOut(300).css('z-index', 0);
            $('body').removeClass('hidden');
        }
    };
}();

PTQN.namespace('account');
PTQN.account = function () {
    var init_dom_execute = false;
    var ACCOUNT_TABLE = $('#account_detail');
    var DATE_VALUE = $('#account .last_day .date_value');
    var page_control = 0;

    var init_data = function () {
        if (page_control) {
            return;
        }
        var last_day = DATE_VALUE.text();
        PTQN.show_loading();
        PTQN.sendDajax({
            'function': 'qnyd_account_data',
            'last_day': last_day
        });
    };

    var init_chart = function () {
        if (page_control) {
            return;
        }
        PTQN.sendDajax({
            'function': 'qnyd_get_account_chart',
        });
    };

    var layout_table = function (json) {
        for (var i in json) {
            ACCOUNT_TABLE.find('.' + i).text(json[i]);
        }
    };

    var layout_chart = function (id, x, series) {
        PTQN.draw_chart(id, x, series);
        $('#chart').css('width', $('#chart').width());
    };

    var init_dom = function () {
        $('#account .select select').change(function () {
            //切换统计天数事件
            DATE_VALUE.text($(this).val());
            page_control = 0;
            init_data();
        });
    };

    var init_message_box=function(){
        $('#PT_message .message_btn').on('touchend',function(){
            var obj=$(this).find('.message_detail');

            $('#PT_message .message_btn.active').removeClass('active').css('height',35);
            $(this).addClass('active').css('height',obj.height()+35);
        });

        $('#PT_message .message_close').on('touchend',function(){
            var msf_ids=[];
             $('#PT_message').hide();
            $('#PT_message .message_btn').each(function(){
                msf_ids.push($(this).attr('msg_id'));
            });
            PTQN.sendDajax({'function':'qnyd_close_msgs','msg_ids':msf_ids.toString()});
        });

        setTimeout(function(){
             var obj=$($('#PT_message .message_btn')[0]).find('.message_detail');
             $($('#PT_message .message_btn')[0]).addClass('active').css('height',obj.height()+35);
        },00);
    };

    var layout_message=function(message){

        var html='',i=0;
        template.isEscape=false;
        for(i;i<message.length;i++){
            html+=template.render('common_message_layer',message[i]);
        }
        $('#PT_message .message_box_ul').html(html);

        $('#PT_message').css('display','table');
        init_message_box();
    };

    var show_phone_dialog = function(){
        PTQN.show_animate_layer($('#phone_layer').html());
        // $('#animate_layer').find('.tab-item').remove(); # 提供返回，让用户可跳过填写手机号
    };

    return {
        'init': function () {
            PTQN.that = this;
            init_chart();
            init_data();
            if (!init_dom_execute) {
                init_dom();
                init_dom_execute = true;
                if (Number($('#account').data('isneed-phone')) === 1 ){
                    show_phone_dialog();
                }
            }
        },
        'call_back': function (result) {
            if (result.common_message.length){
                layout_message(result.common_message);
            }
            layout_table(result.account_table);
            page_control = 1;
        },
        'chart_call_back': function (account_chart) {
            layout_chart('chart', account_chart.x, account_chart.series);
        }
    };
}();



PTQN.namespace('keyword_manage');
PTQN.keyword_manage = function () {
    var init_dom_execute = false;
    var page_control = 0;
    var record_count, page = 1,
        page_count = 20,
        lock;


    var init_data = function () {
        if (page_control) {
            return;
        }
        PTQN.sendDajax({
            'function': 'qnyd_keyword_manage_data',
            'page': page,
            'page_count': page_count
        });
    };

    var init_more_data = function () {
        if (!record_count || lock) {
            return;
        }

        if ((page * page_count) > record_count) {
            $('#keyword_manage_table tfoot').remove();
            return;
        }
        page++;
        lock = 1; //锁住
        PTQN.sendDajax({
            'function': 'qnyd_keyword_manage_data',
            'page': page,
            'page_count': page_count
        });
    };

    var layout_table = function (json) {
        var html = '';
        for (var i in json['record']) {
            html += template.render('nomal_tr_template', json['record'][i]);
        }
        $('#keyword_manage_table tbody').append(html);

        record_count = json.record_count;
        if (page_count >= record_count) {
            $('#keyword_manage_table tfoot').remove();
        }
        lock = 0;
        init_ajax();
    };

    var init_ajax = function () {
        $('#keyword_manage_table .word').slice((page - 1) * page_count, page * page_count).click(function () {

            //点击关键词显示详细信息
            var keyword_id = $(this).parent().attr('id').replace('km_', ''),
                obj = $('#detail_' + keyword_id);

            if (obj.css('display') == 'table-row') {
                $(this).find('span').removeClass('roate');
                obj.hide();
            } else {
                $('#keyword_manage_table .word').find('span').removeClass('roate');
                $('#keyword_manage_table .detail').parent().hide();
                $(this).find('span').addClass('roate');
                $(this).parents('tr').find('.count').click();
                if (!($(this).parents('tr').next().find('.forecast').text() == '预估排名')) {
                    PTQN.sendDajax({
                        // 'function': 'qnyd_forecast_order_list',
                        // 'keyword_id': keyword_id
                        'function': 'qnyd_get_keywords_rankingforecast',
                        'kw_id_list':[keyword_id]
                    });
                }

                obj.show();
            }
        });

        $('#keyword_manage_table .count').slice((page - 1) * page_count, page * page_count).click(function () {
            if ($(this).text() != '查') {
                return;
            }
            $(this).html('<img src="/site_media/qnyd/img/loader-small.gif" width="11" height="11">');
            var keyword_id = $(this).parents('tr').attr('id').replace('km_', '');
            var item_id = $(this).attr('item_id');
            var adgroup_id = $(this).attr('adgroup_id');
            PTQN.sendDajax({
                'function': 'qnyd_word_order',
                'adgroup_id': adgroup_id,
                'keyword_id': keyword_id,
                'ip': '',
                'item_id': item_id
            });
        });

        $('#keyword_manage_table input').slice((page - 1) * page_count, page * page_count).change(function () {
            var new_price = Number($(this).val());
            var max_price = Number($(this).attr('max_price'));

            //输入校验
            if (isNaN(new_price) || new_price < 0.05 || new_price > 99.99) {
                PTQN.alert('出价必须是介于0.05到99.99之间的数字');
                $(this).val(max_price);
                return;
            }

            change_input_class($(this), max_price, new_price); //改变输入框颜色
        });

        $('#keyword_manage_table .cancel_attention').slice((page - 1) * page_count, page * page_count).click(function () {
            var keyword_id = $(this).attr('id').replace('cancel_', '');
            var adgroup_id = $(this).attr('adgroup_id').replace('cancel_', '');
            PTQN.show_loading('请稍后...');
            PTQN.sendDajax({
                'function': 'qnyd_cancel_attention',
                'keyword_id': keyword_id,
                'adgroup_id': adgroup_id
            });
        });
    };

    var change_input_class = function (obj, max_price, new_price) {
        obj.removeClass('plus fall limit');

        if (new_price > 5) {
            obj.addClass('limit');
            return;
        }
        if (max_price < new_price) {
            obj.addClass('plus');
            return;
        } else if (max_price > new_price) {
            obj.addClass('fall');
            return;
        }
    };

    var layout_order = function (json) {
        $('#km_' + json.keyword_id + ' .count').html(json.order);
    };

    var remove_row = function (result) {
        if (result.length) {
            var keyword_id = result[0];
            $('#detail_' + keyword_id).fadeOut(170);
            $('#km_' + keyword_id).fadeOut(170);
            setTimeout(function () {
                $('#detail_' + keyword_id).remove();
                $('#km_' + keyword_id).remove();
                if (!$('#keyword_manage_table tbody tr').length) {
                    PTQN.show_animate_layer($('#set_attention_page').html());
                }
            }, 17);
        } else {
            PTQN.alert('取消关注失败,请稍后重试');
        }
    };

    var init_dom = function () {
        //能进来说明有关注的词，将状态设置一下
        //$('#is_attention').val(1);

        $('#keyword_manage select.plus').change(function () {
            //批量加价
            bulk_price($(this).val());
        });

        $('#keyword_manage select.fall').change(function () {
            //批量降价
            fall_price($(this).val());
        });

        $('#keyword_manage_submit').click(function () {
            var plus_num = 0,
                fall_num = 0,
                result = [];
            $('#keyword_manage_table input').each(function () {
                var data = eval('[' + $(this).attr('data') + ']')[0];
                var max_price = Number($(this).attr('max_price'));
                var new_price = Number($(this).val());

                if (new_price == max_price) {
                    return;
                }

                if (new_price > max_price) {
                    plus_num++;
                }
                if (new_price < max_price) {
                    fall_num++;
                }

                result.push({
                    'keyword_id': data.keyword_id,
                    'adgroup_id': data.adgroup_id,
                    'campaign_id': data.campaign_id,
                    'word': data.word,
                    'is_del': 0,
                    'new_price': new_price,
                    'max_price': max_price,
                    'match_scope': data.match_scope
                });
            });

            if (!(plus_num + fall_num)) {
                PTQN.alert('请先修改出价！');
                return;
            }

            //            if (confirm('加价：' + plus_num + '个，降价：' + fall_num + '个\n 您确认提交到直通车吗？')) {
            //                PTQN.sendDajax({'function': 'qnyd_curwords_submit','data': JSON.stringify(result)});
            //            }
            var msg = '加价：' + plus_num + '个，降价：' + fall_num + '个\n 您确认提交到直通车吗？';
            PTQN.confirm(msg, function () {
                PTQN.show_loading();
                PTQN.sendDajax({
                    'function': 'qnyd_curwords_submit',
                    'data': JSON.stringify(result)
                });
            });

        });
    };

    var bulk_price = function (val) {
        $('#keyword_manage_table input').each(function () {
            var max_price = Number($(this).attr('max_price'));
            var new_price = (max_price * (1 + val / 100)).toFixed(2);

            if (new_price > 99.99 || new_price < 0.05) {
                new_price = max_price;
            }

            $(this).val(new_price);
            change_input_class($(this), max_price, new_price); //改变输入框颜色
        });

    };

    var fall_price = function (val) {
        $('#keyword_manage_table input').each(function () {
            var max_price = Number($(this).attr('max_price'));
            var new_price = (max_price * (1 - val / 100)).toFixed(2);

            if (new_price > 99.99 || new_price < 0.05) {
                new_price = max_price;
            }

            $(this).val(new_price);
            change_input_class($(this), max_price, new_price); //改变输入框颜色
        });
    };

    var call_back_submit = function (result) {
        var msg = '';
        if (result.success.length) {
            msg = '修改成功:' + result.success.length + '个';
        }
        if (result.fall.length) {
            msg = '修改失败:' + result.success.length + '个';
        }
        PTQN.alert(msg);

        $(result.success).each(function () {
            var obj = $('#km_' + this).find('input');
            obj.removeClass('plus fall limit').attr('max_price', obj.val());
        });
    };

//    var layout_forecast = function (result) {
//        var obj = $('#detail_' + result.kw_id + ' .forecast'),
//            html;
//        var forecast_dict = {
//            '1-5': '第1-5名',
//            '6-8': '第6-8名',
//            '9-13': '第一页底部',
//            '14-21': '第二页右侧',
//            '22-26': '第二页底部',
//            '27-39': '第三页',
//            '40-52': '第四页',
//            '53-65': '第五页',
//            '66-78': '第六页',
//            '79-91': '第七页',
//            '92-100': '第八页',
//            '101': '100名后',
//        };
//
//        result['forecast_dict'] = forecast_dict;
//
//        if (result.result.length) {
//            html = template.render('forecast_template', result);
//        } else {
//            html = '<select><option>99.99元排名101后</option></select>';
//        }
//        obj.after(html);
//
//        $(obj).next().change(function () {
//            var obj_input = $('#km_' + result.kw_id).find('input');
//            var new_price = this.value;
//            var max_price = Number(obj_input.attr('max_price'));
//            if (new_price == 'default') {
//                new_price = max_price;
//            }
//            obj_input.val(new_price);
//            PTQN.that.change_input_class(obj_input, max_price, new_price);
//        });
//        obj.text('预估排名').addClass('orange btn_l ');
//    };

    var layout_forecast = function (kw_id, prices) {
	    // 出价排名解析函数
	    var handle_rank_data = function (rank_data) {
	        var result = [], page_data = [], page_data_rt = [], page_data_rb = [], page_data_b = [], page_pos = 17, position = 0, page_no, price, max_price, min_price, page_str;
	        //分页处理
	        for (var i=0;i<Math.ceil(rank_data.length/page_pos);i++) {
	            page_no = i+1;
	            page_data = rank_data.slice(i*page_pos, (i+1)*page_pos);
	            page_str = page_no>1?'第'+page_no+'页':'';
	            //页面区域划分
	            if (page_no<3) {
	                page_data_rt = page_data.slice(0, 4);
	                page_data_rb = page_data.slice(4, 12);
	                page_data_b = page_data.slice(12, 17);
	            } else {
	                page_data_rt = [];
	                page_data_rb = page_data.slice(0, 12);
	                page_data_b = page_data.slice(12, 17);
	            }
	            //右侧前四位(第3页以后为0)
	            for (var j in page_data_rt) {
	                price = (page_data_rt[j]/100).toFixed(2);
	                result.push([page_str+'第'+(Number(j)+1)+'名：'+price+'元', price]);
	            }
	            //右侧后八位(第3页以后为12)
	            if (page_data_rb.length>0) {
	                var rank_h = page_data_rt.length + 1, rank_l = page_data_rt.length + page_data_rb.length;
	                if (page_data_rb.length==1) {
	                    price = (page_data_rb[0]/100).toFixed(2);
	                    result.push([page_str+'第'+rank_h+'名：'+price+'元', price]);
	                } else {
	                    max_price = (page_data_rb[0]/100).toFixed(2);
	                    min_price = (page_data_rb[page_data_rb.length-1]/100).toFixed(2);
	                    result.push([page_str+'第'+rank_h+'~'+rank_l+'名：'+max_price+'~'+min_price+'元', max_price+'-'+min_price]);
	                }
	            }
	            //底部五位
	            if (page_data_b.length>0) {
	                if (page_data_b.length==1) {
	                    price = (page_data_b[0]/100).toFixed(2);
	                    result.push(['第'+page_no+'页底部：'+price+'元', price]);
	                } else {
	                    max_price = (page_data_b[0]/100).toFixed(2);
	                    min_price = (page_data_b[page_data_b.length-1]/100).toFixed(2);
	                    result.push(['第'+page_no+'页底部：'+max_price+'~'+min_price+'元', max_price+'-'+min_price]);
	                }
	            }
	        }
	        result.push([rank_data.length+'名以后：'+(min_price-0.01).toFixed(2)+'元', (min_price-0.01).toFixed(2)]);
	        return result;
	    };

        var obj = $('#detail_' + kw_id + ' .forecast'), html;

        if (prices.length) {
            html = template.render('forecast_template', {'rank_data':handle_rank_data(prices)});
        } else {
            html = '<select><option>99.99元排名101后</option></select>';
        }
        obj.after(html);

        $(obj).next().change(function () {
            var obj_input = $('#km_' + kw_id).find('input');
            var new_price = this.value.split('-')[0];
            var max_price = Number(obj_input.attr('max_price'));
            if (new_price == 'default') {
                new_price = max_price;
            }
            obj_input.val(new_price);
            PTQN.that.change_input_class(obj_input, max_price, new_price);
        });
        obj.text('预估排名').addClass('orange btn_l ');
    };

    return {
        'init': function () {
            PTQN.that = this;
            init_data();
            if (!init_dom_execute) {
                init_dom();
                init_dom_execute = true;
            }
        },
        'call_back': function (result) {
            layout_table(result);
            page_control = 1;
        },
        'call_back_order': function (result) {
            layout_order(result);
        },
        'call_back_cancel_attention': function (result) {
            remove_row(result);
        },
        'call_back_submit': function (result) {
            call_back_submit(result);
        },
//        'call_back_forecast': function (result) {
//            layout_forecast(result);
//        },
        'call_back_forecast': function (kw_id, prices) {
            layout_forecast(kw_id, prices);
        },
        'loader_Sign': $('#keyword_manage_loader_Sign'),
        'init_more_data': init_more_data,
        'change_input_class': change_input_class
    };
}();



PTQN.namespace('adgroup_cost');
PTQN.adgroup_cost = function () {
    var init_dom_execute = false;
    var page_control = 0;
    var record_count, page = 1,
        page_count = 20,
        lock, change_day_lock;

    var ADGROUP_TABLE = $('#adgroup_table');
    var DATE_VALUE = $('#adgroup_cost .last_day .date_value');

    var init_data = function () {
        if (page_control) {
            return;
        }
        var last_day = DATE_VALUE.text();
        localStorage.removeItem('adgroup'); //清除缓存
        PTQN.show_loading();
        PTQN.sendDajax({
            'function': 'qnyd_adgroup_cost_data',
            'last_day': last_day,
            'page': page,
            'page_count': page_count
        });
    }

    var init_more_data = function () {
        if (!record_count || lock) {
            return;
        }

        if ((page * page_count) > record_count) {
            $('#adgroup_cost tfoot').remove();
            return;
        }
        var last_day = DATE_VALUE.text();
        page++;
        lock = 1; //锁住
        PTQN.sendDajax({
            'function': 'qnyd_adgroup_cost_data',
            'last_day': last_day,
            'page': page,
            'page_count': page_count
        });
    }

    var layout_table = function (json) {
        var html = '';
        if (json['record'].length) {
            for (var i in json['record']) {
                html += template.render('adgroup_tr_template', json['record'][i]);
            }

            localStorage['adgroup'] = JSON.stringify(json['record']);

            if (change_day_lock) {
                change_day_lock = 0; //解开切换天数的所
                ADGROUP_TABLE.find('tbody').html(html);
            } else {
                ADGROUP_TABLE.find('tbody').append(html);
            }
            record_count = json.record_count;
            if (page_count >= record_count) {
                $('#adgroup_cost tfoot').remove();
            }
            lock = 0;
            init_ajax();
        } else {
            $('#adgroup_cost tfoot td').html('暂时没有有花费的宝贝');
        }
    }

    var init_ajax = function () {
        ADGROUP_TABLE.find('tr').slice((page - 1) * page_count, page * page_count).tap(function () {
            var adgroup_id = $(this).attr('id');
            var record = JSON.parse(localStorage.adgroup);
            for (var i in record) {
                if (record[i]['adgroup_id'] == adgroup_id) {
                    var result = record[i];
                    break;
                }
            }
            PTQN.show_animate_layer(template.render('creative_info_template', result));
        });
    }

    var layout_table_creative = function (json) {
        var html = '';
        html = template.render('creative_info_template', json);
        PTQN.show_animate_layer(html);
    }

    var init_dom = function () {
        $('#adgroup_cost .select select').change(function () {
            //切换统计天数事件
            DATE_VALUE.text($(this).val());
            change_day_lock = 1;
            page_control = 0;
            init_data();
        });
    }

    return {
        'init': function () {
            PTQN.that = this;
            init_data();
            if (!init_dom_execute) {
                init_dom();
                init_dom_execute = true;
            }
        },
        'call_back': function (result) {
            layout_table(result);
            page_control = 1;
        },
        'loader_Sign': $('#adgroup_table_loader_Sign'),
        'init_more_data': init_more_data
    }
}();

PTQN.namespace('kw_monitor');
PTQN.kw_monitor = function () {
    var match_models = [1,2,4];
    var match_desces = ['精','中','广'];

    var is_android = function(){
        var u = navigator.userAgent, app = navigator.appVersion;
        var isAndroid = u.indexOf('Android') > -1 || u.indexOf('Linux') > -1; //android终端或者uc浏览器
        return isAndroid;
    };

    var is_ios = function(){
        var u = navigator.userAgent, app = navigator.appVersion;
        var isiOS = !!u.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/); //ios终端
        return isiOS;
    };

    var kw_rt_rpt_cache = {};

    var reset_rtrpt_cache = function(){
        kw_rt_rpt_cache = {};
    };

    var fill_chr = function( chr , len ){
        var st = "";
        for ( var i = 0 , l = len ; i < l ; i++){
            st += chr ;
        }
        return st ;
    };

    var format_price = function(price){
        var new_price = price.toString();
        var len = new_price.length;
        var index = new_price.indexOf('.') + 1;

        var float_size = 2;
        var chr = '0';
        if ( index == 0 ){
            new_price = new_price + '.'+fill_chr(chr, float_size);
        } else {
            var rest_num = float_size + index  -  len ;

            if ( rest_num <= 0 ){
                new_price = new_price.substring(0, index+float_size);
            } else {
                new_price += fill_chr(chr, rest_num);
            }
        }

        return new_price;
    };

    var get_count = function(obj_list, obj ){
       var count = 0;
       for(var i = 0 , l = obj_list.length ; i < l ; i ++){
            if( obj_list[i] == obj ){
                count += 1;
            }
       }
       return count ;
    };

    var get_rtrpt_cache = function(kw_id){
        if( kw_rt_rpt_cache.hasOwnProperty(kw_id) ){
	        return kw_rt_rpt_cache[kw_id]
        } else {
            return {}
        }
    };

    var update_rtrpt_cache = function(kw_id,data){
        kw_rt_rpt_cache[kw_id] = data;
    };

    var get_submit_obj = function(kw_id,is_del,scope,new_price){
        var kw_rtrpt = get_rtrpt_cache(kw_id);
        return {'adgroup_id': kw_rtrpt.adg_id,
                 'campaign_id': kw_rtrpt.camp_id,
                 'keyword_id': kw_rtrpt.kw_id,
                 'word': kw_rtrpt.kw_name,
                 "max_price": kw_rtrpt.kw_price,
                 'is_del': 0,
                 'match_scope': scope,
                 'new_price': new_price} ;
    };

    var monitor_price = function(cur_obj){
        var cur_price_str = cur_obj.val();
        var li_obj = cur_obj.parents("li[kw_id]");
        var kw_id = parseInt(li_obj.attr("kw_id"));
        var kw_rtrpt = get_rtrpt_cache(kw_id);
        var cur_price = parseFloat(cur_price_str);
        var old_price = format_price(kw_rtrpt.kw_price);

        var is_valid  = true ;
        if ( get_count(cur_price_str, '.' ) > 1 || isNaN(cur_price) || ! /^(\d{1,2})((\.)(\d{1,2})?)?$/.test(cur_price) ){
            PTQN.alert("输入格式有误，出价自动还原默认值。");
            cur_obj.val(old_price);
            is_valid = false ;
        } else {
            if ( cur_price  < 0.05 || cur_price > 99.99 ){
                PTQN.alert("关键词出价应该在 0.05~99.99 范围内。");
                cur_obj.val(old_price);
                is_valid = false ;
            } else {
                update_modify_infos();
            }
        }
        return is_valid ;
    };

    var change_price_style = function(obj){
        var cur_price = parseFloat(obj.val());
        var kw_rtrpt_obj = obj.parents("li[kw_id]");
        var kw_id = parseInt(kw_rtrpt_obj.attr('kw_id'));
        var kw_rtrpt = get_rtrpt_cache(kw_id);

        var new_price = cur_price;
        if( isNaN(cur_price) ){
            new_price = kw_rtrpt.kw_price ;
        } else {
            // 颜色变更，暂为了维护放在该方法
            obj.css("color","");
            if (kw_rtrpt.kw_price < cur_price){
                obj.css("color",'red');
            } else if(kw_rtrpt.kw_price > cur_price) {
                obj.css("color",'green');
            }
        }
        return new_price;
    };

    var bluk_format_price = function(obj_list){
        for(var i = 0 , l = obj_list.length ; i < l ; i ++ ){
	        var cur_obj = $(obj_list[i]);
	        var new_price = format_price(cur_obj.val());
	        cur_obj.val(new_price);
        }
    };

    var assert_modify_keyword = function(obj,kw_rtrpt){
        var kw_price_obj = obj.find(".kw_price");
        var cur_price = parseFloat(kw_price_obj.val());

        var is_modify = false ;
        if( isNaN(cur_price) ){
            obj.val(format_price(kw_rtrpt.kw_price));
        } else {
            if (kw_rtrpt.kw_price < cur_price){
                is_modify = true ;
            } else if(kw_rtrpt.kw_price > cur_price) {
                is_modify = true ;
            }
        }
        return is_modify;
    };

    var package_modify_keyword = function( obj, kw_rtrpt ){
        var kw_price_obj = obj.find(".kw_price");
        var cur_price = parseFloat(kw_price_obj.val());

        var kw_id = kw_rtrpt.kw_id;
        var is_del = 0;
        var scope = kw_rtrpt.kw_scope;

        return get_submit_obj(kw_id,is_del,scope,cur_price);
    };

    var keyword_filter = function( assert_func, package_func ){
        var kw_list = [];
        $("li[kw_id]").each(function(){
            var obj = $(this);
            var kw_id = parseInt(obj.attr("kw_id"));
            var kw_rtrpt = get_rtrpt_cache(kw_id);
            if( assert_func(obj,kw_rtrpt) ){ // 此处为了扩展，考虑到可能不止改价一种情形
                var package_obj = package_func(obj,kw_rtrpt);
                kw_list.push(package_obj);
            }
        });
        return kw_list ;
    };

    var update_modify_infos = function(){
        var modify_kw_list = keyword_filter(assert_modify_keyword, package_modify_keyword);
        $("#modify_keyword_num").text(modify_kw_list.length);
    };

    var valid_kw_price = function(cur_obj){
        // 校验数据
        var is_valid = monitor_price(cur_obj);
        // 颜色变动
        if ( is_valid ) {
	        cur_obj.parents("li[kw_id]").attr('kw_id')
	        var new_price = change_price_style(cur_obj);
	        cur_obj.val(format_price(new_price));
        }
        return is_valid;
    };

    var init_event = function(){

        $("#kw_submit").click(function(){
            setTimeout(function(){
	            var submit_data = keyword_filter(assert_modify_keyword, package_modify_keyword);
	            bluk_format_price($(".kw_price"));
	            if( submit_data.length > 0 ){
	                PTQN.show_loading('正在提交数据');
	                PTQN.sendDajax({
	                    'function': 'qnyd_curwords_submit_4monitor',
	                    'data' : JSON.stringify(submit_data)
	                });
	            } else {
	                PTQN.alert("亲，暂无任何关键词出价修改，不能执行该操作。")
	            }
            }, 300);
        });
        
        $("#lbl_close").click(function(){
            $("#popup_div").hide();
        });

    };

    var kw_submit_callback = function(result){
        PTQN.hide_loading();
        var submit_data = keyword_filter(assert_modify_keyword, package_modify_keyword);
        var submit_dict = {}
        for (var i = 0 , l = submit_data.length ; i < l ; i++){
            var temp_data = submit_data[i];
            submit_dict[temp_data.keyword_id] = temp_data ;
        }

        // 刷新成功的缓存
        if( result.success.length > 0  ){
	        for(var i = 0 , l = result.success.length ; i < l ; i++){
	           var s_kw_id = result.success[i] ;
	           var cache_temp = get_rtrpt_cache(s_kw_id);
	           var submit_temp = submit_dict[s_kw_id]
	           var new_price = submit_temp.new_price ;
	           var new_scope = submit_temp.match_scope ;

	           cache_temp['kw_price'] = new_price;
	           cache_temp['kw_scope'] = new_scope;

	           var cur_obj = $("li[kw_id='"+s_kw_id+"'] .kw_price");
	           var new_price = change_price_style(cur_obj);
               cur_obj.val(format_price(new_price));
	        }
        }

        // 提示失败
        var count = 0 ;
        if( result.fall.length > 0 ){
            count = result.fall.length;
            PTQN.alert("亲，还存在 "+count+" 未提交成功，请检查您的出价，默认出价范围 0.05~99.99 元。");
        }

        // 刷新页面显示
        $("#modify_keyword_num").text(count);
    };

    var loader_keyword_rtrpt_callback = function(result,adg_info){
        PTQN.hide_loading();
        if( result.length > 0 ){
            var ul_obj = $("#kw_panel");
            ul_obj.html("");

            $("#camp_name").text(adg_info.camp_title);
            $("#item_name").text(adg_info.item_title);

            for( var i = 0 , l = result.length ; i < l ; i ++){
                var data = result[i] ;
                var render = {
                    'kw_id':data.kw_id,
                    'kw_name':data.kw_name,
                    'kw_price':format_price(data.kw_price),
                    'kw_rt_click':data.kw_rt_click,
                    'kw_rt_impr':data.kw_rt_impr,
                    'kw_rt_pay_count':data.kw_rt_pay_count,
                    'kw_rt_cost':format_price(data.kw_rt_cost),
                };
                var html = template.render('kw_moniter_li',render);
                ul_obj.append(html);

                // 更新缓存
                var kw_id = data.kw_id ;
                update_rtrpt_cache(kw_id,data);
            }

            // 绑定事件
            ul_obj.find(".kw_price").focus(function(e){
                var cur_target = this;
                var cur_obj = $(cur_target);
                ul_obj.find(".kw_price").removeClass("kw_active");
                cur_obj.addClass("kw_active");

                var docTouchend = function(event){
	                if(event.target !=  cur_target){
	                    setTimeout(function(){
                            var is_valid = valid_kw_price(cur_obj);
	                        document.removeEventListener('touchend', docTouchend,false);
	                        if( ! is_valid ){
	                           cur_obj.focus();
	                        } else {
	                           cur_obj.blur();
	                        }
	                    }, 100 );
	                }
	            };

                document.addEventListener('touchend', docTouchend, false);
            });

            ul_obj.find(".kw_price").keydown(function(e){
                var code = e.keyCode;
                var back_space = 8;
                var l_dot_chr = 110;
                var a_dot_chr = 190;

                var last_price = $(this).val();
                var dot_index = last_price.indexOf(".");
                if ( code == back_space ){
                    return true;
                } else if ( 48 <= code  && code <= 57 || 96 <= code && code <= 105 ){
                    /*
                    if ( !(dot_index > -1 && last_price.length - 1 - dot_index >= 2) ){
                        return true;
                    }
                    */
                    return true;
                } else if ( code == l_dot_chr || code == a_dot_chr ) {
                    if ( dot_index ==  -1 ){
                        return true;
                    }
                }

                return false;
            });

            ul_obj.find(".kw_price").keyup(function(e){
                var code = e.keyCode;
                var back_space = 8;

                var opar_obj = $(this);
                var new_price = opar_obj.val();
                var dot_index = new_price.indexOf(".");

                change_price_style(opar_obj);
                if ( code != back_space  && dot_index == -1 &&  /^\d{2}$/.test(new_price) ){
                    opar_obj.val(new_price+".");
                }

                return true;
            });

        } else {
            console.log("this is a impossible things.");
        }
    };

    var loader_adgroup_rtrpt_callback = function(result){
        PTQN.hide_loading();
        if( result.length > 0 ){
            var adg_panel_obj = $("#adg_panel") ;
            var adg_header_html = "";
            for(var i = 0 , l = result.length ; i < l ; i ++){
                var data = result[i];
                adg_header_html += template.render("adgroup_moniter_li",data);
            }
            adg_panel_obj.html(adg_header_html);

            // 初始化事件
            adg_panel_obj.find('>li').click(function(){
                var cur_obj = $(this);

                $("#modify_keyword_num").text('0');
                adg_panel_obj.find(".select_img").removeClass("select_img");
                cur_obj.find("img").addClass("select_img");

                var adg_id = parseInt(cur_obj.attr('adg_id'));
                PTQN.show_loading('正在获取关键词实时数据');
	            PTQN.sendDajax({
	                'function': 'qnyd_query_keywords_rtclick',
	                'adg_id' : adg_id
	            });
            });

            // 初始化数据
            adg_panel_obj.find('li').first().click();

	        $("#float_title").show();
	        $("#kw_opar_panel").show();
            $("#no_rtrpt").hide();
        } else {
            $("#float_title").hide();
            $("#kw_opar_panel").hide();
            $("#no_rtrpt").show();
        }
    };

    var init_loader = function(){
        $("#no_rtrpt").hide();
        reset_rtrpt_cache();
        PTQN.show_loading("正在加载宝贝实时数据");
        PTQN.sendDajax({
            'function': 'qnyd_query_adgroups_rtclick',
        });

    };

    var init_section = function(){
        // 初始化数据
        init_loader();

        // 初始化事件
        init_event();
    };

    return {
        init : init_section,
        adgroup_rtrpt_callback : loader_adgroup_rtrpt_callback,
        keyword_rtrpt_callback : loader_keyword_rtrpt_callback,
        kw_submit_callback:kw_submit_callback,
    }
}();

PTQN.namespace('mnt');
PTQN.mnt = function () {
    var is_active,
        init_dom_execute = false,
        page_control = 0,
        append_control = 1, //判断宝贝列表是否追加
        record_count, page = 1,
        page_count = 20,
        lock, change_day_lock,
        MNT_LIMIT_PRICE_DEFAULT = 0.8, //默认推广宝贝限价
        MNT_TABLE = $('#mnt_adgroup'),
        DATE_VALUE = $('#mnt .last_day .date_value');

    var init_data = function () {
        if (page_control) {
            return;
        }
        var last_day = DATE_VALUE.text();
        var campaign_id = $('#mnt_title_list>a:hasClass("active")').attr('campaign_id');
        PTQN.show_loading('获取报表中，请稍后');
        PTQN.sendDajax({
            'function': 'qnyd_mnt_campaign',
            'rpt_days': last_day,
            'campaign_id': campaign_id,
            'auto_hide': 0,
            'page': page,
            'page_count': page_count
        });
    }

    var init_more_data = function () {
        if (!record_count || lock) {
            return;
        }

        if ((page * page_count) > record_count) {
            $('#mnt_adgroup tfoot').hide();
            return;
        }
        var last_day = DATE_VALUE.text();
        var campaign_id = $('#mnt_title_list>a:hasClass("active")').attr('campaign_id');
        page++;
        lock = 1; //锁住
        PTQN.sendDajax({
            'function': 'qnyd_mnt_campaign',
            'rpt_days': last_day,
            'campaign_id': campaign_id,
            'page': page,
            'page_count': page_count
        });
    }

    var init_mnt_adg = function () {
        //取一页的数据
        var last_day = DATE_VALUE.text();
        var campaign_id = $('#mnt_title_list>a:hasClass("active")').attr('campaign_id');
        PTQN.sendDajax({
            'function': 'qnyd_mnt_adg',
            'rpt_days': last_day,
            'campaign_id': campaign_id,
            'page': page,
            'page_count': page_count
        });
    }

    var layout_rpt = function (json) {
        for (var i in json) {
            $('#mnt_rpt').find('.' + i).text(json[i]);
        }
    }

    var layout_adg = function (adg_list) {
        var html = '';
        for (var i in adg_list.record) {
            adg_list.record[i]['namespace'] = 'mnt';
            html += template.render('adgroup_tr_template', adg_list.record[i]);
        }
        if (append_control) {
            MNT_TABLE.find('tbody').append(html);
        } else {
            MNT_TABLE.find('tbody').html(html);
            append_control = 1;
        }
        $('#mnt_adg_num').text(adg_list.record_count);
        record_count = adg_list.record_count;
        lock = 0;
        //init_ajax();
    }

    var layout_setting = function (json) {
        is_active = json.is_active;

        $('#mnt_budget').val(json.budget).attr('old_value', json.budget);
        $('#mnt_title_list>a:hasClass("active")').attr('mnt_type', json.mnt_type);
        if (json.mnt_type == 2 || json.mnt_type == 4) {
            $('#mnt_max_price').parents('tr').fadeOut(500);
        } else {
            $('#mnt_max_price').val(json.max_price).attr('old_value', json.max_price).parents('tr').fadeIn(500);
        }
        $('#mnt .page_header .title').text(json.title);
        $('#mnt_planned_time').text(json.optimize_time);

        if (json.is_active && json.mnt_status) {
            $('.quick_oper').removeClass('disabled');
        } else {
            $('.quick_oper').addClass('disabled');
        }

        if (json.mnt_status) {
            $('#camp_mnt_oper').text('暂停').addClass('red').remove();
            $('#camp_mnt_oper').attr('mnt_oper', 0);
            $('#camp_oper_parent').attr('class', 'online');
        } else {
            $('#camp_mnt_oper').text('开启').removeClass('red');
            $('#camp_mnt_oper').attr('mnt_oper', 1);
            $('#camp_oper_parent').attr('class', 'offline');
        }
    }

    var init_dom = function () {
        $('#mnt_title_list>a:eq(0)').addClass('active');

        $('#mnt_budget').change(function () {
            var campaign_id = $('#mnt_title_list>a:hasClass("active")').attr('campaign_id');
            var mnt_type = $('#mnt_title_list>a:hasClass("active")').attr('mnt_type'),
                submit_data = {},
                budget = $(this).val(),
                old_value = $(this).attr('old_value');

            if (parseInt(budget) != parseFloat(budget)) {
                $(this).val(old_value);
                PTQN.light_msg('请使用整数', 'red');
                return false;
            }

            if (parseInt(budget) < 30) {
                $(this).val(old_value);
                PTQN.light_msg('日限额不能低于30元', 'red');
                return false;
            }

            submit_data['budget'] = budget;
            PTQN.sendDajax({
                'function': 'qnyd_update_cfg',
                'campaign_id': campaign_id,
                'mnt_type': mnt_type,
                submit_data: JSON.stringify(submit_data)
            });

        });

        $('#mnt_max_price').change(function () {
            var campaign_id = $('#mnt_title_list>a:hasClass("active")').attr('campaign_id');
            var mnt_type = $('#mnt_title_list>a:hasClass("active")').attr('mnt_type'),
                submit_data = {},
                max_price = Number($(this).val()).toFixed(2),
                old_value = $(this).attr('old_value');

            if (max_price < 0.2 || max_price > 5) {
                $(this).val(old_value);
                PTQN.light_msg('限价必须在0.2到5之间', 'red');
                return false;
            }

            submit_data['max_price'] = max_price;
            PTQN.sendDajax({
                'function': 'qnyd_update_cfg',
                'campaign_id': campaign_id,
                'mnt_type': mnt_type,
                submit_data: JSON.stringify(submit_data)
            });
        });

        $('#mnt_title_list>a').click(function () {
            $('#mnt_title_list>a').removeClass('active');
            $(this).addClass('active');
            page_control = 0;
            page = 1;
            MNT_TABLE.find('tbody').html('');
            $('#mnt_adgroup tfoot').show();
            init_data();
        });

        $('.quick_oper').tap(function () {
            if ($(this).hasClass('disabled')) {
                PTQN.light_msg('计划暂停或已执行过该操作');
                return;
            }
            var stgy = $(this).attr('stgy'),
                temp = {
                    '1': '加大',
                    '-1': '减小'
                },
                campaign_id = $('#mnt_title_list>a:hasClass("active")').attr('campaign_id');
            PTQN.confirm('确定要执行' + temp[stgy] + '投入的操作吗？', function () {
                PTQN.show_loading("正在执行中");
                PTQN.sendDajax({
                    'function': 'qnyd_quick_oper',
                    'campaign_id': campaign_id,
                    'stgy': stgy
                });
            }, [stgy]);
        });

        $('#camp_mnt_oper').tap(function () {
            var mnt_oper = parseInt($(this).attr('mnt_oper')),
                campaign_id = $('#mnt_title_list>a:hasClass("active")').attr('campaign_id'),
                mnt_type = $('#mnt_title_list>a:hasClass("active")').attr('mnt_type'),
                msg = (mnt_oper ? '即将启动自动优化，同时将计划设置为参与推广，确认启动吗？' : '即将暂停自动优化，同时将计划设置为暂停推广，确认暂停吗？');
            PTQN.confirm(msg, function () {
                PTQN.show_loading("正在执行中");
                PTQN.sendDajax({
                    'function': 'qnyd_update_prop_status',
                    'campaign_id': campaign_id,
                    'status': mnt_oper,
                    'mnt_type': mnt_type
                });
            }, [mnt_oper]);
        });

        $('#reload_mnt_campaign').tap(function () {
            window.location.reload();
        });

        $('#close_mnt').tap(function () {
            var campaign_id = $('#mnt_title_list>a:hasClass("active")').attr('campaign_id'),
                mnt_type = $('#mnt_title_list>a:hasClass("active")').attr('mnt_type');
            PTQN.confirm('确认"解除托管"该计划吗？', function () {
                PTQN.show_loading("正在执行中");
                PTQN.sendDajax({
                    'function': 'qnyd_close_mnt',
                    'campaign_id': campaign_id,
                    'mnt_type': mnt_type
                });
            });
            //
        });

        $('#mnt .select select').change(function () {
            //切换统计天数事件
            DATE_VALUE.text($(this).val());
            page_control = 0;
            append_control = 0;
            page = 1;
            if (has_mnt_capmaign()) {
                init_data();
            }
        });

        $('#mnt_adgroup').on('tap.mnt', 'tr', function () {
            var html, obj = JSON.parse($(this).attr('data'));
            if (!Number(obj.limit_price)) {
                obj.limit_price = $("#mnt_max_price").attr("old_value");
            }

            var acitve_campaign=$('nav a[class*="active"]').attr('mnt_type');
            obj.campaign_mnt_type = acitve_campaign;
            html = template.render('mnt_adg_layer', obj);
            PTQN.show_animate_layer(html);

        });

        $('#animate_layer').on('tap.mnt', '.mnt_type', function () {
            var flag = $(this).attr('flag'),
                mnt_type = $('#mnt_title_list>a:hasClass("active")').attr('mnt_type');
            data = JSON.parse($(this).parents('ul').attr('data'));
            PTQN.light_msg('执行中');
            PTQN.sendDajax({
                'function': 'mnt_update_adg_mnt',
                'flag': flag,
                'adg_id_list': '[' + data.adgroup_id + ']',
                'mnt_type': mnt_type,
                'camp_id': data.campaign_id,
                'limit_price':Number($.trim($('#animate_layer .layer_set input').val())) || 0
            });

            if (flag == '1' && parseFloat($('#animate_layer').find('input').val()) == MNT_LIMIT_PRICE_DEFAULT) { //使用默认限价，可能是数据库没有限价数据，提交个默认的上去
                $('#animate_layer').find('input').change();
            }
        });

        $('#animate_layer').on('tap.mnt', '.adg_status_btn', function () {
            var mode = $(this).attr('mode'),
                mnt_type = $('#mnt_title_list>a:hasClass("active")').attr('mnt_type');
            data = JSON.parse($(this).parents('ul').attr('data'));
            PTQN.light_msg('执行中');
            PTQN.sendDajax({
                'function': 'web_update_adg_status',
                'mode': mode,
                'adg_id_list': [data.adgroup_id],
                'mnt_type': mnt_type,
                'campaign_id': data.campaign_id,
                'namespace': 'mnt'
            });
        });

        $('#animate_layer').on('change.mnt', 'input', function () {
            var limit_price = $(this).val(),
                old_price = new_price = $(this).attr('old_price'),
                mnt_type = $('#mnt_title_list>a:hasClass("active")').attr('mnt_type'),
                data = JSON.parse($(this).parents('ul').attr('data'));

            if (isNaN(limit_price) || limit_price < 0.05 || limit_price > 99.99) {
                PTQN.alert('出价必须是介于0.05到99.99之间的数字');
                $(this).val(old_price);
                return;
            }

            PTQN.sendDajax({
                'function': 'web_set_adg_limit_price',
                'adgroup_id': data.adgroup_id,
                'mnt_type': mnt_type,
                'limit_price': limit_price
            });
        });
    }

    var has_mnt_capmaign = function () {
        if ($('#mnt_title_list>a').length) {
            $('#none_mnt_campagin').hide();
            $('#has_mnt_campaign').show();
            return true;
        } else {
            $('#has_mnt_campaign').hide();
            $('#none_mnt_campagin').show();
            return false;
        }
    }

    return {
        'init': function () {
            PTQN.that = this;
            if (!init_dom_execute) {
                init_dom();
                init_dom_execute = true;
            }
            if (has_mnt_capmaign()) {
                init_data();
            }
        },
        'mnt_campaign_back': function (json) {
            layout_rpt(json.rpt);
            layout_setting(json.set);
            init_mnt_adg();
            page_control = 1;
        },
        'mnt_adg_back': function (adg_list) {
            layout_adg(adg_list);
            PTQN.hide_loading();
        },
        'submit_cfg_back': function (budget, max_price) {
            if (budget != '') {
                $('#mnt_budget').attr('old_value', budget);
                PTQN.light_msg('修改计划日限额成功');
            }
            if (max_price != '') {
                $('#mnt_max_price').attr('old_value', max_price);
                PTQN.light_msg('修改关键词日限额成功');
            }
        },
        'quick_oper_back': function (stgy) {
            if(stgy=='0'){
                PTQN.light_msg('今天已改价过!');
            }else{
                 var temp = {
                    '1': '加大',
                    '-1': '减小'
                };
                PTQN.light_msg(temp[stgy] + '投入执行完成');
            }
            $('.quick_oper').addClass('disabled');
        },
        'update_camp_back': function (status) {
            if (status) {
                if (is_active) {
                    $('.quick_oper').removeClass('disabled');
                }
                $('#camp_mnt_oper').text('暂停').addClass('red').attr('mnt_oper', 0).remove();
                $('#camp_oper_parent').attr('class', 'online');
            } else {
                $('.quick_oper').addClass('disabled');
                $('#camp_mnt_oper').text('开启').removeClass('red').attr('mnt_oper', 1);
                $('#camp_oper_parent').attr('class', 'offline');
            }
        },
        'update_mnt_back': function (adg_id_list, flag) {
            var adgroup_id = JSON.parse(adg_id_list)[0];
            var data = JSON.parse($('#mnt' + adgroup_id).attr('data'));
            if (flag) {
                PTQN.light_msg('加入托管成功');
                data['mnt_type'] = $('#mnt_title_list>a:hasClass("active")').attr('mnt_type');
                $('#mut_status_btn_' + adgroup_id).html('<span class="marr_12 b_color normal_size">托管中</span><span class="btn_l red mnt_type" flag="0">取消托管</span>');
            } else {
                PTQN.light_msg('取消托管成功');
                data['mnt_type'] = '0';
                $('#mut_status_btn_' + adgroup_id).html('<span class="marr_12 r_color normal_size">未托管</span><span class="btn_l mnt_type" flag="1">加入托管</span>');
            }
            $('#mnt' + adgroup_id).attr('data', JSON.stringify(data));
        },
        'update_adg_back': function (mode, result) {
            var adg_id = result.success_id_list[0],
                jq_adg_status = $('#adg_status_btn_' + adg_id),
                jq_tr = $('#mnt' + adg_id)
            var data = JSON.parse(jq_tr.attr('data'));
            switch (mode) {
            case 'start':
                PTQN.light_msg('开启推广成功');
                jq_adg_status.html('<span class="marr_12 b_color normal_size">推广中</span><span class="btn_l red adg_status_btn" mode="stop">暂停推广</span>');
                data['online_status'] = 'online';
                jq_tr.removeClass('offline');
                break;
            case 'stop':
                PTQN.light_msg('暂停推广成功');
                jq_adg_status.html('<span class="marr_12 r_color normal_size">未推广</span><span class="btn_l adg_status_btn" mode="start">开启推广</span>');
                data['online_status'] = 'offline';
                jq_tr.addClass('offline');
                break;
            }

            jq_tr.attr('data', JSON.stringify(data));


            if (result.ztc_del_list && result.ztc_del_list.length) {
                PTQN.alert("您已经在直通车后台删除了该宝贝");
            }
        },
        'loader_Sign': $('#mnt_table_loader_Sign'),
        'init_more_data': init_more_data
    }
}();
//兼容现网
PTQN.MntAdg = PTQN.mnt;
PT.Adgroup_list=PTQN.mnt;

PTQN.namespace('set');
PTQN.set = function () {
    var init_dom_execute = false;

    var init_dom = function () {
        $('#sync_button').on('tap', function () {
            PTQN.show_animate_layer($('#sync_layer').html());

            $('#sync_ul button:eq(0)').on('tap', function () {
                if (!$(this).hasClass('disabled')) {
                    $(this).addClass('disabled');
                    PTQN.sendDajax({
                        'function': 'web_sync_increase_data'
                    });
                    PTQN.light_msg('后台正在执行，请耐心等待');
                }
            });
            $('#sync_ul button:eq(1)').on('tap', function () {
                if (!$(this).hasClass('disabled')) {
                    $(this).addClass('disabled');
                    PTQN.sendDajax({
                        'function': 'web_sync_all_data',
                        'data_type': 1,
                        'rpt_days': 15
                    });
                    PTQN.light_msg('后台正在执行，请耐心等待');
                }
            });
            $('#sync_ul button:eq(2)').on('tap', function () {
                if (!$(this).hasClass('disabled')) {
                    $(this).addClass('disabled');
                    PT.sendDajax({
                        'function': 'web_sync_all_data',
                        'data_type': 2
                    });
                    PTQN.light_msg('后台正在执行，请耐心等待');
                }
            });
        });

        $('#suggestion_button').on('click', function () {
            PTQN.show_animate_layer($('#suggestion_layer').html());
            $('#suggestion_submit').on('click', function () {
                var content = $('#suggestion').val();

                if (content == '') {
                    PTQN.alert('麻烦您不吝赐教，输入您的建议');
                    return false;
                }
                PTQN.show_loading('感谢您的反馈');
                PTQN.sendDajax({
                    'function': 'web_submit_feedback',
                    'score_str': '[["health_check","qnpc"]]',
                    'content': content
                });
            });
        });
    }

    return {
        'init': function () {
            PTQN.that = this;
            if (!init_dom_execute) {
                init_dom();
                init_dom_execute = true;
            }
        }
    }
}();
