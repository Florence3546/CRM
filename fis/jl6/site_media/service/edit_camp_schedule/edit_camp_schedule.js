define(["template","jslider",'jl6/site_media/widget/alert/alert','schedule_templet'], function(template,_,alert,scheduleTemplet) {
    "use strict";

    var tpl,
        tpl_ds;

    tpl = __inline('edit_camp_schedule.html');
    tpl_ds = __inline('duration_setting.html');

    var hide_duration_setting = function () {
        $('.ui-selected').removeClass('ui-selected');
        $('#duration_setting').fadeOut();
    };

    var schedule=function(options){
        this.options=options;
    }

    var curset = '0';
    var last_values = [];
    var batch = 1;
    var batch_value = 0;
    schedule.prototype.day_desc_list = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期天'];
    schedule.prototype.time_desc_list = ['00:00', '00:30', '01:00', '01:30', '02:00', '02:30', '03:00', '03:30', '04:00', '04:30',
                      '05:00', '05:30', '06:00', '06:30', '07:00', '07:30', '08:00', '08:30', '09:00', '09:30',
                      '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
                      '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30',
                      '20:00', '20:30', '21:00', '21:30', '22:00', '22:30', '23:00', '23:30', '24:00'
                      ];

    schedule.prototype.show=function(options){
        this.show_modal(options);
        this.init_data();
    }

    schedule.prototype.show_modal=function(options){
        var liObjList = [];
        for (var i = 0; i < 336; i++) {
            liObjList.push(i);
        }
        var templets = scheduleTemplet.templets;
        var html = template.compile(tpl)({liObjList:liObjList,templets: templets});

        this.obj=$(html);

        $('body').append(this.obj).append(tpl_ds);

        $('#selectable').selectable();

        this.obj.modal();

        this.bind_event(options);
    }

    schedule.prototype.init_data=function(){

        if (this.options.schedules == 'all') {
            this.options.schedules = '00:00-24:00:100;00:00-24:00:100;00:00-24:00:100;00:00-24:00:100;00:00-24:00:100;00:00-24:00:100;00:00-24:00:100';
        }
        curset = this.options.schedules;
        last_values.push(curset);
        this.draw_data(curset);
    }

    schedule.prototype.draw_data = function(schedules, batch_value){
        var data_list = schedules.split(';');
        for (var i = 0;i<data_list.length;i++) {
            if (data_list[i] == '0') {
                for (var k = i*48; k < (i+1)*48; k++) {
                    $('#duration_box_'+k).attr('class', 'box ui-selectee li_bgcolor_0').data('num', 0);
                }
            }else{
                var temp_list = data_list[i].split(',');
                for (var j in temp_list) {
                    var time_list = temp_list[j].slice(0, 11).split('-'),
                        sche_num = temp_list[j].slice(12),
                        start_index = $.inArray(time_list[0], schedule.prototype.time_desc_list),
                        end_index = $.inArray(time_list[1], schedule.prototype.time_desc_list)-1,
                        rgb_class = 1;
                    //需要批量加大或减小折扣
                    if(batch_value>0){
                        sche_num = parseInt(sche_num)+batch_value*batch;
                        sche_num =Math.min(Math.max(30,sche_num),250);//范围在30~250
                        sche_num = parseInt(sche_num);
                    }
                    if (sche_num != 100) {
                        rgb_class = parseInt(sche_num/10);
                    }
                    for (var k = start_index + i*48; k <= end_index + i*48; k++) {
                        $('#duration_box_'+k).attr('class', 'box ui-selectee li_bgcolor_'+rgb_class).data('num', sche_num);
                    }
                }
            }
        }
    }

    schedule.prototype.bind_event=function(options){
        var that=this;
        $('#selectable').selectable();

        $('#duration_discount input')[0].checked=true;

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
            if (day_list.length === 0) {
                return;
            };
            var day_desc = that.day_desc_list[day_list[0]]+' - '+that.day_desc_list[day_list[day_list.length -1]],
                time_desc = that.time_desc_list[time_list[0]]+' - '+that.time_desc_list[time_list[time_list.length-1] + 1];
            if (day_list.length == 1) {
                day_desc = that.day_desc_list[day_list[0]];
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
                time_desc = that.time_desc_list[time_index]+' - '+that.time_desc_list[time_index + 1];
            $('#duration_hover_week').text(that.day_desc_list[day_index]);
            $('#duration_hover_time').text(time_desc);
            $('#duration_hover_discount').text(li_val);
            $('#duration_hover').stop().css({'margin-left': left, 'margin-top': top}).fadeIn();
        });

        $('#selectable').on('mouseleave', function(e){
            $('#duration_hover').hide();
        });

        $('#duration_setting_discount').slider({"from":30,
                                                "to":250,
                                                'step':5,
                                                "range":'min',
                                                "skin":"showvalue",
                                                "dimension":"&nbsp;%",
                                                // 'scale': [30, 250],
                                                "onstatechange": function(value) {
                                                    var parent_div = $('#duration_setting_discount').closest('div');
                                                    $('#duration_discount input')[0].checked=true;
                                                    parent_div.find('.jslider-bg .v').css('width',parseFloat((value-30)*100)/220+"%");
                                                }
                                            });

        $('#modal_camp_schedule').on('hide', function(){
            $('#duration_setting').stop().hide();
        });

        $('#modal_camp_schedule').on('click', '.bluk_set', function() {
            var result_val = parseInt($(this).val());
            if(result_val<0){
                //恢复上一步
                if(last_values.length<=1){
                    alert.show('已经恢复到初始设置！');
                    return false;
                }
                schedule.prototype.draw_data(last_values[last_values.length-1]);
                last_values.pop();//恢复到上一步后需要把最后一步的数据删除掉
            }else{
                last_values.push(getSchedule());
                var class_str = result_val>0? 'li_bgcolor_1': 'li_bgcolor_0';
                $('#selectable>li').attr('class', 'box ui-selectee '+class_str).data('num', result_val);
            }
        });

        $('#duration_setting').on('click', '.submit', function(){
            last_values.push(getSchedule());
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


        this.obj.find('.btn-primary').on('click',function(){
            var result_str = getSchedule();
            if(result_str==";;;;;;"){
                alert.show('计划投放时间不能为空!')
                return false;
            }

            that.obj.modal('hide');
            if(options.schedules==result_str){
                return false;
            }
            that.options.onChange&&that.options.onChange(result_str);
        });

        this.obj.on('hidden.bs.modal',function(){
            that.obj.remove();
            curset = '0';
            last_values = [];
            batch = 1;
            batch_value = 0;
        });

        $('#search_schedule').click(function(){
            $('#select_template').prop('checked',true);
        });

        /**
         * 选择分时折扣模板
         */
        $('#search_schedule').on('change',function(e,value){
            last_values.push(getSchedule());
            batch_value = 0;
            $('#batch_value').val('');
            schedule.prototype.draw_data(scheduleTemplet.getTempletValue(value));
        });

        $('.schedule_type').click(function(e){
            e.stopPropagation();
        });

        $('.schedule_radio').on('change',function(){
            last_values.push(getSchedule());
            var select = $('[name=schedule_radio]:checked').val();
            batch_value = 0;
            $('#batch_value').val('');
            if(select=='current'){
                schedule.prototype.draw_data(curset);
            }else if(select=='100'){
                $('#selectable>li').attr('class', 'box ui-selectee li_bgcolor_1').data('num', 100);
            }
        });

        $('#select_batch').on('change',function(e,value){
            if(batch == value){
                return false;
            }
            batch = value
            last_values.push(getSchedule());
            batch_value = $('#batch_value').val();
            schedule.prototype.draw_data(getSchedule(),batch_value);
        });

        // 输入框输入限制
        $("#batch_value").on("keyup", function() {
            $(this).val($(this).val().replace(/[^\d]/g,''));
        });
        $("#batch_value").focus(function(){
            $(this).tooltip('hide');
        });
        $("#batch_value").blur(function(){
            var value = $(this).val();
            if(value==''|| batch_value == parseInt(value)){
                return false;
            }
            last_values.push(getSchedule());
            batch_value = parseInt(value);
            schedule.prototype.draw_data(getSchedule(),batch_value);
        });
    }

    /**
     * 获取设置的内容
     */
    var getSchedule = function(){
        var jq_lis = $('#selectable li'),
                cur_index = 0,
                cur_val = 0,
                cur_day_index = 0,
                start_time_index = 0,
                cur_time_index = 0,
                temp_val = 0,
                result_str = '',
                temp_list;

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
                        if (temp_val!=0) {
                            result_str += schedule.prototype.time_desc_list[start_time_index] + '-' + schedule.prototype.time_desc_list[cur_time_index] + ':' + temp_val + ',';
                        }
                        start_time_index = cur_time_index;
                        temp_val = cur_val;
                    }
                    if (cur_time_index == 47) {
                        if (temp_val!=0) {
                            result_str += schedule.prototype.time_desc_list[start_time_index] + '-' + schedule.prototype.time_desc_list[48] + ':' + temp_val + ';';
                        }else{
                            result_str +="0;";
                        }
                    }
                }
            });
        result_str = result_str.slice(0, -1);
        return result_str;
    }

    return {
        show: function(options){
            var m=new schedule(options);
            m.show(options);
        }
    }
});
