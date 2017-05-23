PT.namespace('Schedule');
PT.Schedule = function () {

    var camp_id = $('#campaign_id').val();

    var day_desc_list = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期天'],
        time_desc_list = ['00:00', '00:30', '01:00', '01:30', '02:00', '02:30', '03:00', '03:30', '04:00', '04:30',
                      '05:00', '05:30', '06:00', '06:30', '07:00', '07:30', '08:00', '08:30', '09:00', '09:30',
                      '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
                      '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30',
                      '20:00', '20:30', '21:00', '21:30', '22:00', '22:30', '23:00', '23:30', '24:00'
                      ];

    var hide_duration_setting = function () {
        $('.ui-selected').removeClass('ui-selected');
        $('#duration_setting').fadeOut();
    };

    var init_dom = function() {
        var li_str = '';
        for (var i = 0; i < 336; i++) {
            li_str += '<li class="box" id="duration_box_' + i + '" box-index="' + i + '" data-num=0 ></li>';
        }
        $('#selectable').html(li_str);
        $('#selectable').selectable();

        $(document).on('click', '.edit_schedule', function() {
            // var camp_id = $(this).parents('tr').find('.kid_box').val();
            // $('#camp_schedule_title').text($(this).parents('tr').find('.camp_title').text());
            // $('#camp_schedule_title').data('camp_id', camp_id);
            if ($(this).data('is_lock')){
                init_modal($(this).data('schedule'));
            } else {
                PT.show_loading('正在获取分时折扣');
                PT.sendDajax({'function':'web_get_camp_schedule', 'camp_id':camp_id});
            }
        });

        $('#selectable').on('mousedown', function(){
            hide_duration_setting();
        });

        $('#duration_setting').on('click', '.close_duration', function(){
            hide_duration_setting();
        });

        $('#selectable').on('mouseup', function(){
            var jq_li = $(this).find('.ui-selecting'),
                jq_setting = $('#duration_setting'),
                day_list = [],
                time_list = [],
                day_index = 0,
                time_index = 0,
                li_index = 0;
            jq_li.each(function(){
                li_index = parseInt($(this).attr('box-index'));
                day_index = parseInt(li_index / 48);
                // if (day_list.indexOf(day_index) == -1) {
                if ($.inArray(day_index, day_list) == -1) {
                    day_list.push(day_index);
                }
                time_index = li_index % 48;
                // if (time_list.indexOf(time_index) == -1) {
                if ($.inArray(time_index,time_list) == -1) {
                    time_list.push(time_index);
                }
            });
            var day_desc = day_desc_list[day_list[0]]+' - '+day_desc_list[day_list[day_list.length -1]],
                time_desc = time_desc_list[time_list[0]]+' - '+time_desc_list[time_list[time_list.length-1] + 1];
            if (day_list.length == 1) {
                day_desc = day_desc_list[day_list[0]];
            }
            jq_setting.find('#day_desc').text(day_desc);
            jq_setting.find('#time_desc').text(time_desc);
            var s_li = jq_li.eq(0),
                s_index = parseInt(jq_li.eq(0).attr('box-index')),
                e_index = parseInt(jq_li.eq(jq_li.length-1).attr('box-index')),
                left = s_li.offset().left + (e_index - s_index + 1) % 48 / 2 * 15,
                cur_top = s_li.offset().top - window.scrollY + (parseInt(e_index / 48)  - parseInt(s_index / 48) + 1 ) / 2 * 60,
                max_top = $(window).height() - jq_setting.outerHeight(),
                top = cur_top < max_top? cur_top: max_top;
            jq_setting.css({'margin-left': left, 'margin-top': top}).fadeIn();
        });

        $('#selectable li').on('mousemove', function(e){
            var left = e.pageX+10,
                top = e.pageY-window.scrollY+14,
                li_val = parseInt($(this).data('num')),
                li_index = parseInt($(this).attr('box-index')),
                day_index = parseInt(li_index / 48),
                time_index = parseInt(li_index % 48),
                time_desc = time_desc_list[time_index]+' - '+time_desc_list[time_index + 1];
            $('#duration_hover_week').text(day_desc_list[day_index]);
            $('#duration_hover_time').text(time_desc);
            $('#duration_hover_discount').text(li_val);
            $('#duration_hover').css({'margin-left': left, 'margin-top': top}).fadeIn();
        });

        $('#selectable').on('mouseleave', function(e){
            $('#duration_hover').stop().hide();
        });

        $('#duration_setting_discount').slider({"from":30,
                                                "to":250,
                                                'step':5,
                                                "range":'min',
                                                "skin":"plastic",
                                                "dimension":"&nbsp;%",
                                                "onstatechange": function() {
                                                    $('#duration_discount input').attr('checked', true);
                                                }
                                            });

        $('#modal_camp_schedule').on('hide', function(){
            $('#duration_setting').stop().hide();
        });

        $('#modal_camp_schedule').on('click', '.bluk_set', function() {
            var result_val = parseInt($(this).val()),
                class_str = result_val>0? 'li_bgcolor_1': 'li_bgcolor_0';
            $('#selectable>li').attr('class', 'box ui-selectee '+class_str).data('num', result_val);
        });

        $('#modal_camp_schedule').on('click', '.submit', function() {
            var jq_lis = $('#selectable li'),
                cur_index = 0,
                cur_val = 0,
                cur_day_index = 0,
                start_time_index = 0,
                cur_time_index = 0,
                temp_val = 0,
                result_str = '';
            jq_lis.each(function () {
                cur_index = $(this).attr('box-index');
                cur_val = $(this).data('num');
                cur_time_index = cur_index % 48;
                cur_day_index = parseInt(cur_index/48);
                if (cur_time_index === 0) {
                    temp_val = cur_val;
                    start_time_index = 0;
                    temp_list = [];
                } else {
                    if (cur_val != temp_val) {
                        if (temp_val) {
                            result_str += time_desc_list[start_time_index] + '-' + time_desc_list[cur_time_index] + ':' + temp_val + ',';
                        }
                        start_time_index = cur_time_index;
                        temp_val = cur_val;
                    }
                    if (cur_time_index == 47) {
                        if (temp_val) {
                            result_str += time_desc_list[start_time_index] + '-' + time_desc_list[48] + ':' + temp_val + ';';
                        }else{
                            if (start_time_index === 0) {
                                result_str += '0;';
                            }else{
                                result_str = result_str.slice(0,-1)+';';
                            }
                        }
                    }
                }
            });
            result_str = result_str.slice(0, -1);
            // var camp_id = $('#camp_schedule_title').data('camp_id');
            if(result_str==$('.edit_schedule').data().schedule){
                $('#modal_camp_schedule').modal('hide');
                return false;search_btn
            }
            $('#camp_schedule_title').data('schedule', result_str);
            if(result_str=='0;0;0;0;0;0;0'){
	             PT.alert('计划投放时间不能为空');
            }else{
                PT.show_loading('正在修改投放时间');
                PT.sendDajax({'function': 'web_update_camp_schedule', 'camp_id': camp_id, 'schedule_str': result_str});
            }
            
        });

        $('#duration_setting').on('click', '.submit', function(){
            var result_val = parseInt($("input[name='duration_setting']:checked").val());
            if (result_val > 1) {
                result_val = parseInt($('#duration_setting_discount').val());
            } else {
                result_val = result_val * 100;
            }
            var rgb_class = parseInt(result_val/10),
                class_str = "box ui-selectee li_bgcolor_1";
            if (result_val != 100) {
                class_str = "box ui-selectee li_bgcolor_"+rgb_class;
            }
            $('.ui-selected').attr('class', class_str).data('num', result_val);
            $('#duration_setting').fadeOut();
        });

        $(document).on('click', function (e) {
            if($('#selectable')[0]==e.target){
                return;
            }
            hide_duration_setting();
        });

        $('#duration_setting').on('click', function(e){
            e.stopPropagation();
        });
    };

    var init_modal = function(schedule_str){
        var jq_modal = $('#modal_camp_schedule');
        if (schedule_str == 'all') {
            schedule_str = '00:00-24:00:100;00:00-24:00:100;00:00-24:00:100;00:00-24:00:100;00:00-24:00:100;00:00-24:00:100;00:00-24:00:100';
        }
        var data_list = schedule_str.split(';');
        for (var i in data_list) {
            if (data_list[i] == '0') {
                continue;
            }
            var temp_list = data_list[i].split(',');
            for (var j in temp_list) {
                var time_list = temp_list[j].slice(0, 11).split('-'),
                    sche_num = temp_list[j].slice(12),
                    // start_index = time_desc_list.indexOf(time_list[0]),
                    // end_index = time_desc_list.indexOf(time_list[1]) - 1,
                    start_index = $.inArray(time_list[0], time_desc_list),
                    end_index = $.inArray(time_list[1], time_desc_list)-1,
                    rgb_class = 1;
                if (sche_num != 100) {
                    rgb_class = parseInt(sche_num/10);
                }
                for (var k = start_index + i*48; k <= end_index + i*48; k++) {
                    $('#duration_box_'+k).attr('class', 'box ui-selectee li_bgcolor_'+rgb_class).data('num', sche_num);
                }
            }
        }
        jq_modal.modal();
    };

    return {

        init: function (){
            init_dom();
        },

        get_schedule_back:function(camp_id, schedule_str) {
            if (schedule_str) {
                $('.edit_schedule').data({'is_lock': 1, 'schedule': schedule_str});
                init_modal(schedule_str);
            } else {
                PT.alert('淘宝接口不稳定，请稍后再试');
            }

        },

        update_schedule_back:function(is_success, msg_list) {
            PT.hide_loading();
            if (is_success) {
                // var camp_id = $('#camp_schedule_title').data('camp_id'),
                var schedule_str = $('#camp_schedule_title').data('schedule');
                $('.edit_schedule').data('schedule', schedule_str);
                $('#modal_camp_schedule').modal('hide');
                PT.light_msg('修改计划投放时间', '修改成功');
            } else {
                PT.alert('修改计划投放时间失败');
            }
        }
    };
}();
