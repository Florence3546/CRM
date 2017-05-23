PT.namespace('ChooseMntcampaign');
PT.ChooseMntcampaign = function () {
    var mnt_type = 0;
    var mnt_name = '普通';
    var campaign_id = parseInt($('#campaign_id').val());
    var campaign_title = $.trim($('input[name=campaign]:checked').parent().text());
    var budget = 0;
    var budget_recm = 100;
    var budget_min = 100;
    var budget_max = 300;
    var max_price = 0;
    var max_price_recm = $('#max_price_recm').val();
    var max_price_min = 0.2;
    var max_price_max = 5;
    var step_index = 1;
    var mnt_index = Number($('#mnt_index').val());
    var mnt_max_num = 150;
	
    var check_step1 = function () {
        var result = true;
        if (!campaign_id) {
            $('#campaign_error').show();
            result = false;
        }

        if (!mnt_type) {
            $('#mnt_type_error').show();
            result = false;
        } else {
            if (mnt_type=='1') {
                max_price = $("#max_price").val();
                var check_error = '';
                $('#tr_max_price').addClass('input_error');
                if ($.trim(max_price)=='') {
                    check_error = '值不能为空！';
                    result = false;
                } else if (isNaN(max_price)) {
                    check_error = '值必须是数字！';
                    result = false;
                } else if (Number(max_price) < max_price_min || Number(max_price) > max_price_max) {
                    check_error = '值必须介于' + max_price_min + '~' + max_price_max + '元之间！';
                    result = false;
                } else {
                    $('#tr_max_price').removeClass('input_error');
                }
                if (check_error) {
                    $('#tr_max_price .iconfont').attr('data-original-title', check_error);
                }
            }

            budget = $("#budget").val();
            var check_error = '';
            $('#tr_budget').addClass('input_error');
            if ($.trim(budget)=='') {
                check_error = '值不能为空！';
                result = false;
            } else if (isNaN(budget) || /^[1-9]\d*$/.test(budget)==false) {
                check_error = '值必须是整数！';
                result = false;
            } else if (parseInt(budget,10) < 30 || parseInt(budget,10) > budget_max) {
                check_error = '值必须介于30~' + budget_max + '元之间！';
                result = false;
            } else {
                $('#tr_budget').removeClass('input_error');
            }
            if (check_error) {
                $('#tr_budget .iconfont').attr('data-original-title', check_error);
            }
        }
        return result;
    };

    var confirm_mnt_campaign = function () {
        $('.check_value').val('');
        $('.confirm_camp').html(campaign_title);
        var set_mnt_dialog = '';
        switch (mnt_type) {
            case '1': set_mnt_dialog = 'set_gsw_dialog';
                          break;
            case '2': set_mnt_dialog = 'set_impt_dialog';
                          break;
        }

        $('#campaign_dscr').html(campaign_title);
        $('#campaign_mnt_dscr').html(campaign_title);
        $('#mnt_type_dscr').html(mnt_name);
        if (mnt_type=='2') {
            $('#max_price_dscr').parent().hide();
        } else {
            $('#max_price_dscr').html(max_price);
            $('#max_price_dscr').parent().show();
        }
        $('#budget_dscr').html(budget);
        into_next_step();

      //   $.confirm({
         //    title:'确认选择'+campaign_title+'为'+mnt_name+'吗?',
         //    width:'large',
         //    body:$('#'+set_mnt_dialog).html(),
            // shown:function(e){
               //  var obj=$(e.target);
               //  obj.find('.btn-primary').addClass('disabled');
               //  $('.check_value', obj).bind('keyup mouseout', function () {
                  //   var check_str = $(this).closest('div').find('.check_str').html();
                  //   if ($.trim(this.value)===check_str) {
                     //    obj.find('.btn-primary').removeClass('disabled');
                  //   } else {
                     //    obj.find('.btn-primary').addClass('disabled');
                  //   }
               //  })
         //    },
         //    okHide:function(e){
         //        $('#campaign_dscr').html(campaign_title);
         //        $('#mnt_type_dscr').html(mnt_name);
         //        if (mnt_type=='2') {
         //            $('#max_price_dscr').parent().hide();
         //        } else {
         //            $('#max_price_dscr').html(max_price);
         //            $('#max_price_dscr').parent().show();
         //        }
         //        $('#budget_dscr').html(budget);
         //        into_next_step();
         //    }
      //   });
    };

    var get_more_setting_list = function () {
        var val_list = [],
            jq_input = $('input[name="more_setting"]:checked');
        jq_input.each(function(){
            val_list.push($(this).val());
        });
        return val_list;
    };

	var get_mnt_rt = function() {
		var mnt_rt = $('input[name=chk_rt]').is(':checked');
		if (mnt_rt)
			return 1
		else 
			return 0
	}

    var submit_mnt_campaign = function () {
        $('#submit_all').unbind('click');
        PT.show_loading("正在开启"+mnt_name);
        PT.sendDajax({'function':'mnt_mnt_campaign_setter',
                                 'campaign_id':campaign_id,
                                 'set_flag':1,
                                 'mnt_type':mnt_type,
                                 'max_price':max_price,
                                 'budget':budget,
                                 'mnt_index':mnt_index,
                                 'mnt_rt':get_mnt_rt,
                                 'more_setting_list': get_more_setting_list(),
                                 'namespace':'ChooseMntcampaign',
                                 'callback_list':$.toJSON([
                                     'PT.AddItemBox3.submit_mnt_adg',
                                     'PT.AddItemBox3.submit_new_item',
                                     'PT.ChooseMntcampaign.mnt_campaign_setter_callback'
                                     ])
                                 });
    };

    var into_next_step = function () {
//        var mnt_adg_count = Number($('.mnt_adg_count').html());
//        var new_item_count = Number($('.new_item_count').html());
//        var mnt_count0 = mnt_adg_count + new_item_count;
//        var mnt_count = mnt_max_num - mnt_count0;
//        $(".mnt_count0").html(mnt_count0);
//        $(".mnt_count").html(mnt_count);
        $("#mnt_step"+step_index).fadeOut("fast", function () {
            $("#mnt_wizard .wrap>div").removeClass();
            $("#mnt_wizard .wrap>div:lt("+step_index+")").addClass('finished');
            $("#mnt_wizard .wrap>div:eq("+step_index+")").addClass('current');
            $("#mnt_wizard .wrap>div:gt("+step_index+")").addClass('todo');
            step_index++;
            $("#mnt_step"+step_index).fadeIn("fast");
            if (step_index==2) {
                $('#choose_mnt_item').html($('#add_item_box3'));
                PT.AddItemBox3.init(1);
                $('#add_item_box3').show();
                $('#candidate [href="#item_pane"]').tab('show');
                PT.AddItemBox3.open();
            } else if (step_index==3) {
                $('#submit_all').unbind('click').click(submit_mnt_campaign);
                if (mnt_type=='1') {
                    var total_adg_count = Number($('.total_adg_count').html());
                    if (total_adg_count>0) {
                        $('#mnt_step3 .total_adg_count').closest('div').addClass('r_color');
                    } else {
                        $('#mnt_step3 .total_adg_count').closest('div').removeClass('r_color');
                    }
                }
                var danger_item_count = Number($('.danger_item_count').html());
                if (danger_item_count>0) {
                    $('#mnt_step3 .danger_item_count').closest('div').show();
                } else {
                    $('#mnt_step3 .danger_item_count').closest('div').hide();
                }
            }
        });
    };

//    var check_is_agree = function () {
//        var obj = $(this).closest('.set_mnt_dialog').find('.btn_submit');
//        var check_str = $(this).closest('div').find('.check_str').html();
//        if($(this).val() == check_str){
//            obj.removeClass('disabled');
//            obj.unbind(); // 解绑之前的事件
//            mnt_name = $.trim($('[name="mnt_type"]:checked').closest('label').text());
//            obj.click(function(){
//                $.fancybox.close();
//                into_next_step();
//            });
//        }else{
//            obj.unbind().addClass('disabled');
//        }
//    }

    var init_steps_behind = function () {
        $('.btn_submit').unbind().addClass('disabled');
        $('#submit_all').unbind('click');
        if (mnt_type) {
//            $(".mnt_max_num").html(mnt_max_num);
//            $('.mnt_adg_count').html(0);
//            $('.new_item_count').html(0);
//            $('.mnt_count0').html(0);
//            $('.total_adg_count').html('---');
//            $('.total_item_count').html('---');
//            PT.MntAdgBox.init_tables();
            $('.doing_count').html(0);
            $(".doable_count").html(mnt_max_num);
            $('.adgroup_doing_count').html(0);
            $('.item_doing_count').html(0);
            $('.total_count').html('---');
            PT.AddItemBox3.init_tables();
            $('.btn_OK2').attr('confirmed', '0');
            $('.adg_2del_info, .danger_cats_info').hide();
        }
    };

    var init_dom = function () {
        // 计划列表顺序调整
        $('#campaign_error').before($('#campaign_list label.silver').parent());

        $('.tooltips').tooltip({html: true});

        $('#mnt_step1').off('keyup', '.keyup_restore');
        $('#mnt_step1').on('keyup', '.keyup_restore', function(){
            $(this).closest('.input_error').removeClass('input_error');
        });

        $(":radio[name='campaign']").change(function(){
            $('#campaign_error').hide();
            campaign_id = this.value;
            $('#campaign_id').val(campaign_id);
            campaign_title = $(this).closest("label").text();
            init_steps_behind();
        });

        $("#mnt_step1 .div_mnt_type").click(function () {
            $(this).removeClass('disabled').addClass('active').siblings('.div_mnt_type').removeClass('active').addClass('disabled');
            $('#mnt_type_error').hide();
            $('#max_price, #budget').attr('disabled', false);
            $('#tr_max_price, #tr_budget').removeClass('input_error');
            mnt_type = $(this).attr('mnt_type');
            $('#mnt_type').val(mnt_type);
            switch (mnt_type) {
                case '1':
                    mnt_name = '长尾托管';
                    budget_recm = 100;
                    budget_min = 100;
                    budget_max = 300;
                    max_price_min = 0.2;
                    max_price_max = 5;
                    mnt_max_num = 500;
                    var prompt_rpice = 0.80;
//                    $('#tr_max_price').slideDown();
                    $('#tr_max_price').fadeIn();
                    $('#tr_rt').fadeOut();
                    $('#chk_rt').attr('checked', false);
                    $('#max_price').val(max_price_recm);
                    $('#max_price_range').html('(' + prompt_rpice.toFixed(2) + '~' + max_price_max.toFixed(2) + '元)');
//                  $('#add_item_box3 .batch_add_item').show().next().hide();
//                    $('#consult_note').hide();
                    $('#nagao_dialog_body').show();
                    $('#import_dialog_body').hide();
                    $('#mnt_info').removeClass('hide');
                    break;
                case '2':
                    mnt_name = '重点托管 ';
                    budget_recm = 100;
                    budget_min = 100;
                    budget_max = 5000;
                    max_price_min = 0.8;
                    max_price_max = 20;
                    mnt_max_num = 10;
//                    $('#tr_max_price').slideUp();
                    $('#tr_max_price').fadeOut();
                    $('#chk_rt').attr('checked', true);
                    $('#tr_rt').fadeIn();
                    $('.limit_price_max').html(max_price_max.toFixed(2));
//                    $('#add_item_box3 .batch_add_item').hide().next().show();
//                    $('#consult_note').show();
                    $('#nagao_dialog_body').hide();
                    $('#import_dialog_body').show();
                    $('#mnt_info').addClass('hide');
                    break;
            }
            $('#candidate [href="#adgroup_pane"]').parent().removeClass('active');
            $('[name="mnt_name"]').html(mnt_name);
            $('#mnt_max_num').val(mnt_max_num);
            $('#budget').val(budget_recm);
            $('#budget_range').html('(' + budget_min + '~' + budget_max + '元)');
            $('div.mnt_description span[mnt_type]').hide().filter('[mnt_type="'+mnt_type+'"]').show();
            init_steps_behind();
        });

        $(".btn_prev").click(function(){
            if(!PT.DBCLICK_ENABLED){
                //禁止重复点击
                return false;
            }
            PT.DBCLICK_ENABLED=false;

            setTimeout(function(){
                PT.DBCLICK_ENABLED=true;
            },300);

            $("#mnt_step"+step_index).fadeOut("fast", function () {
                step_index--;
                $("#mnt_wizard .wrap>div").removeClass();
                $("#mnt_wizard .wrap>div:lt("+step_index+")").addClass('current');
                $("#mnt_wizard .wrap>div:eq("+step_index+")").addClass('todo');
                $("#mnt_wizard .wrap>div:gt("+step_index+")").addClass('todo');

                $("#mnt_step"+step_index).fadeIn("fast");
                $("#mnt_wizard li").removeClass("active");
                $("#mnt_wizard li:eq("+step_index+")").addClass("active");
            });
        });

        $(".btn_next").click(function(){
            if(!PT.DBCLICK_ENABLED){
                //禁止重复点击
                return false;
            }
            PT.DBCLICK_ENABLED=false;

            setTimeout(function(){
                PT.DBCLICK_ENABLED=true;
            },300);

            switch (step_index) {
                case 1:
                    if (check_step1()) {
                        confirm_mnt_campaign();
                    } else {
                        return false;
                        //PT.alert('设置有误！');
                    }
                    break;
                case 2:
                    if($(this).hasClass('disabled')){
                        return false;
                    }

                    if (PT.AddItemBox3.check_creative_isvalid()) {
                        $('#modal_new_item_info .btn_OK2').hide();
                        $('#modal_new_item_info .into_next_step').show();
                        $('#add_item_box3').modal('hide');
                        if($('.danger_cats_info:visible').length){
                            $('#modal_new_item_info').modal('show');
                        }else{
                            into_next_step();
                        }
                    }
                    break;
            }
        });

        $(".into_next_step").click(function () {
            $(this).closest('.modal').modal('hide');
            into_next_step();
        });

        $('#precautions_check_box').on('click',function(){
            if(this.checked){
                $('.btn_next:eq(1)').removeClass('disabled');
            }else{
                $('.btn_next:eq(1)').addClass('disabled');
            }
        });

        $(".trigger_more_setting").click(function() {
            var text_1 = '&#xe614',
                text_2 = '&#xe613',
                trigger_div = $('.div_more_setting'),
                trigger_i = $(this).find('i');
            trigger_div.slideToggle();
            trigger_i.toggleClass('is_down');
            if (trigger_i.hasClass('is_down')) {
                trigger_i.html(text_1);
            }else{
                trigger_i.html(text_2);
            }
        });
    };

    return {
        init: function () {
            init_dom();
            // $("#mnt_step1 .div_mnt_type:eq(0)").click();
            // $('#mnt_step1 [value="'+$('#default_campaign').val()+'"]').click();
        },
        into_next_step: into_next_step,
        mnt_campaign_setter_callback: function (callback_list, context) {
            var errot_switch=0;
            PT.hide_loading();
            if (!$.isArray(callback_list)) {
                callback_list = [];
            }
            if (!$.isPlainObject(context)) {
                context = {};
            }
            if (callback_list.length) {
                var callback = eval(callback_list.shift());
                context['mnt_campaign_setter_callback'] = {};
                callback(callback_list, context);
            } else {
                // 开启托管计划的反馈信息处理
                if (context['mnt_mnt_campaign_setter']['result']==1) {
                    context['mnt_mnt_campaign_setter']['msg'] = mnt_name + '：' + campaign_title;
                }
                // 生成反馈报告列表
                var report = [context['mnt_mnt_campaign_setter'], context['mnt_update_mnt_adg'], context['web_add_items2']];
                var result_str = '';
                var result_cls = '';
                for (var i in report) {
                    switch (report[i]['result']) {
                        case -1:
                            result_str = '未执行';
                            result_cls = 'no_run';
                            errot_switch=1;
                            break;
                        case 0:
                            result_str = '失败';
                            result_cls = 'fail';
                            errot_switch=1;
                            break;
                        case 1:
                            result_str = '成功';
                            result_cls = 'success';
                            break;
                        case 2:
                            result_str = '存在错误';
                            result_cls = 'error';
                            errot_switch=1;
                            break;
                    }
                    report[i]['result_str'] = result_str;
                    report[i]['result_cls'] = result_cls;
                }
                // 生成最后的报告
                var msg = template.render('create_mnt_campaign_msg', {'report':report});
                // 添加失败的宝贝信息
                var failed_item_dict = context['web_add_items2']['failed_item_dict'];
                if ($.isPlainObject(failed_item_dict) && !$.isEmptyObject(failed_item_dict)) {
                    msg += template.render('add_item_fail_msg', {'fail_msg':failed_item_dict});
                }
                if(errot_switch){
                    $.alert({'title':'开启托管完成',
                        'body':msg,
                        'okHide':function () {
                            PT.show_loading("正在刷新页面");
                            window.location.reload(true);
                        }
                    });
                }else{
                    PT.show_loading("正在刷新页面");
                    window.location.reload(true);
                }
//              PT.alert(msg, undefined, function () {
//                    PT.show_loading("正在刷新页面");
//                    window.location.reload(true);
//                  if (report[0]['result']==1) {
//                      PT.show_loading("正在刷新页面");
//                      window.location.reload(true);
//                  } else {
//                      $('#submit_all').unbind('click').click(function () {
//                          PT.alert(msg);
//                      });
//                  }
//              });
            }
        }
    };
}();

