PT.namespace('EventDetial');
PT.EventDetial = function() {

    var plan_id = $('#lower_detail_plan_id').val(),

        init_dom = function() {

            $(document).on('shown','#event_nav', function() {
                var index = get_active_tab_name(),
                    obj = $('a[href=#' + index + ']');

                if (obj.attr('switch') == '0') {
                    get_event_detail();
                    obj.attr('switch', 1);
                }
            });

            //日期时间选择器
            require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
                var b, c;
                b = new Datetimepicker({
                    start: '#start_time',
                    timepicker: false,
                    closeOnDateSelect: true
                });
                c = new Datetimepicker({
                    start: '#end_time',
                    timepicker: false,
                    closeOnDateSelect: true
                });

            });

            $('#search').on('click', function() {
                if(!vaild()){
                    return false;
                }

                generate_event_detial_box();

                $('#event_nav a').attr('switch', 0);

                get_event_num();

                if($('#conifg_switch:checked').length){
                    save_statistics_config();
                }
            });

            $('#event_list li').on('click', function() {
                $(this).toggleClass('select');
            });

            //还原统计配置的显示
            !function(){
                var statistics_config,i=0,obj;

                statistics_config=PT.get_habit()?$.parseJSON(PT.get_habit()['ncrm_statistics_config']):undefined;

                if(statistics_config){
                    obj=$('#event_list')
                    for (var i; i < statistics_config.length; i++) {
                        obj.find('li[data-event-name='+statistics_config[i]+']').addClass('select');
                    };
                }
            }();
        },

        //验证输入
        vaild=function(){
            var date_reg=RegExp(/\d{4}(\-|\/|\.)\d{1,2}\1\d{1,2}$/),start_time,end_time,ps_id;

            ps_id=$('#ps_id').val()
            start_time= $('#start_time').val();
            end_time= $('#end_time').val();

            if(ps_id==''){
                PT.alert('请填写所属人')
                return false;
            }

            if(!date_reg.test(start_time)||!date_reg.test(end_time)){
                PT.alert('开始时间或结束时间填写有误')
                return false;
            }

            if(!get_select_event().length){
                PT.alert('请选择统计维度');
                return false;
            };

            return true;
        },

        //生成事件详情的box
        generate_event_detial_box = function() {
            var event_list = get_select_event(),
                html = '',
                i = 0,
                data = [];

            html = template.render('event_detial_box_content', {
                'event_list': event_list
            });

            $('#event_detial_box').html(html);

        },

        //获取选中事件列表
        get_select_event = function() {
            var event_list = [];

            $('#event_list li.select').each(function() {
                event_list.push({
                    'name': $(this).attr('data-event-name'),
                    'describe': $(this).text()
                });
            });
            return event_list;
        },

        //获取提交的事件列表
        get_select_event_str = function() {
            var data = get_select_event(),event_list=[],i=0;

            for(i;i<data.length;i++){
                event_list.push(data[i].name);
            }

            return $.toJSON(event_list)
        },

        //获取事件的统计数量
        get_event_num = function() {
            var event_list = get_select_event_str();
            PT.sendDajax({
                'function': 'ncrm_get_event_num',
                'start_time': $('#start_time').val(),
                'end_time': $('#end_time').val(),
                'event_list':event_list,
                'psuser_list':'[' + $('#ps_id').val() + ']',
                'call_back': 'PT.EventDetial.get_event_num_call_back'
            });
        },

        //获取当前事件详情
        get_event_detail = function() {
            var event_name;

            event_name = get_active_tab_name();

            PT.sendDajax({
                'function': 'ncrm_get_event_detail',
                'start_time': $('#start_time').val(),
                'end_time': $('#end_time').val(),
                'psuser_list': '[' + $('#ps_id').val() + ']',
                'event_name': event_name,
                'call_back': 'PT.EventDetial.get_event_detail_call_back'
            });
        },

        //保存统计维度到本地
        save_statistics_config = function() {
            var event_list=get_select_event_str();

            PT.set_habit({'ncrm_statistics_config':event_list});
        }

        //获取当前活动的tab
        get_active_tab_name = function() {
            return $('#event_nav li.active a').attr('href').replace('#', '');
        };



    return {
        init: function() {
            init_dom();
        },
        get_event_num_call_back: function(json) {
            var data = json.data,
                i = 0;

            for (i; i < data.length; i++) {
                if (data[i][1]) {
                    $('.' + data[i][0] + '_count').text(data[i][1]).show();
                } else {
                    $('.' + data[i][0] + '_count').text(0).hide();
                }
            }

            get_event_detail();
        },
        get_event_detail_call_back: function(json) {
            if (json.error == "") {
                var mark = json.mark,
                    table_id = "id_" + mark + "_layout",
                    tr_id = "id_" + mark + "_layout_tr",
                    html = "",
                    i = 0;

                if (json.data.length > 0) {

                    template.isEscape = false;

                    for (i = 0; i < json.data.length; i++) {
                        var data = json.data[i];
                        html += template.render(tr_id, data);

                    }

                    $('#' + json.event_name+'_shop_counter').text(json.shop_counter);

                    $('#' + json.event_name+'_content').html(template.render(table_id, {
                        'data': html
                    }));
                } else {
                    $('#' + json.event_name+'_content').html('<div class="tc p10">无任何详情数据</div>');
                }


            } else {
                PT.alert(json.error);
            }
        }
    }
}();
