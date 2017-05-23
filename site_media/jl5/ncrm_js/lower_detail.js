PT.namespace('LowerDetail');
PT.LowerDetail = function() {

    var plan_id = $('#lower_detail_plan_id').val(),

        init_dom = function() {

            $('#event_nav').on('shown',function(){
                var index=get_active_tab_name(),obj=$('a[href=#'+index+']');

                if(obj.attr('switch')=='0'){
                    get_event_detail();
                    obj.attr('switch',1);
                }
            });

            //日期时间选择器
            require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
                var b, c;
                b = new Datetimepicker({
                    start: '#start_time',
                    timepicker: false,
                    closeOnDateSelect : true
                });
                c = new Datetimepicker({
                    start: '#end_time',
                    timepicker: false,
                    closeOnDateSelect : true
                });

            });

            $('#search').on('click',function(){
                $('#event_nav a').attr('switch',0);
                get_event_num()
            });
        },

        //获取事件的统计数量
        get_event_num = function() {
            PT.sendDajax({
                'function': 'ncrm_get_plan_list_info',
                'plan_id_list': '['+plan_id+']',
                'start_time':$('#start_time').val(),
                'end_time':$('#end_time').val(),
                'call_back': 'PT.LowerDetail.get_event_num_call_back'
            });
        },

        //获取当前事件详情
        get_event_detail = function() {
            var event_name;

            event_name = get_active_tab_name();

            PT.sendDajax({
                'function': 'ncrm_get_plan_event_detail',
                'plan_id':plan_id,
                'start_time':$('#start_time').val(),
                'end_time':$('#end_time').val(),
                'psuser_list': '['+$('#ps_id').val()+']',
                'event_name': event_name,
                'call_back': 'PT.LowerDetail.get_event_detail_call_back'
            });
        },

        //获取当前活动的tab
        get_active_tab_name = function() {
            return $('#event_nav li.active a').attr('href').replace('#', '');
        };



    return {
        init: function() {
            init_dom();

            get_event_num();
        },
        get_event_num_call_back: function(json) {
            var data = json.data[plan_id],i=0;

            for(i;i<data.length;i++){
                if(data[i][1]){
                    $('.' + data[i][0] + '_count').text(data[i][1]).show();
                }else{
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
