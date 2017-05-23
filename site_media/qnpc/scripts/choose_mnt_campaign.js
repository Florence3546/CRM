PT.namespace('ChooseMntcampaign');
PT.ChooseMntcampaign = function () {
    var mnt_type = 0;
    var mnt_name = '普通';
    var campaign_id = 0;
    var campaign_title = '';
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
    var mnt_max_num = 500;

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

        $.confirm({
          title:'确认选择'+campaign_title+'为托管计划吗',
          width:'large',
          body:$('#'+set_mnt_dialog).html(),
          shown:function(e){
            var obj=$(e.target);
            obj.find('.btn-primary').addClass('disabled');
            $('.check_value',obj).bind('keyup mouseout', function(){
              var check_str = $(this).closest('div').find('.check_str').html();
              if($.trim(this.value)===check_str){
                obj.find('.btn-primary').removeClass('disabled');
              }
            });
          },
          okHide:function(e){
              $('#campaign_dscr span').html(campaign_title);
              $('#mnt_type_dscr span').html(mnt_name);
              if (mnt_type=='2') {
                  $('#max_price_dscr').hide();
              } else {
                  $('#max_price_dscr span').html(max_price);
                  $('#max_price_dscr').show();
              }
              $('#budget_dscr span').html(budget);
              into_next_step();
          }
        });
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
                                     'PT.MntAdgBox.submit_mnt_adg',
                                     'PT.AddItemBox2.submit_new_item',
                                     'PT.ChooseMntcampaign.mnt_campaign_setter_callback'
                                     ])
                                 });
    };

    var into_next_step = function () {
        var mnt_adg_count = Number($('.mnt_adg_count').html());
        var new_item_count = Number($('.new_item_count').html());
        var mnt_count0 = mnt_adg_count + new_item_count;
        var mnt_count = mnt_max_num - mnt_count0;
        $(".mnt_count0").html(mnt_count0);
        $(".mnt_count").html(mnt_count);
        $("#step"+step_index).fadeOut("fast", function () {

            $("#mnt_wizard .wrap>div").removeAttr('class');
            $("#mnt_wizard .wrap>div:lt("+step_index+")").addClass('finished');
            $("#mnt_wizard .wrap>div:eq("+step_index+")").addClass('current');
            $("#mnt_wizard .wrap>div:gt("+step_index+")").addClass('todo');
            step_index++;
            $("#step"+step_index).fadeIn("fast");
            if (step_index==3) {
                $('#submit_all').unbind('click').click(submit_mnt_campaign);
                if (mnt_type=='1') {
	                var total_adg_count = Number($('.total_adg_count').html());
	                if (total_adg_count>0) {
		                $('#step3 .total_adg_count').closest('div').addClass('r_color');
	                } else {
		                $('#step3 .total_adg_count').closest('div').removeClass('r_color');
	                }
                }
                var danger_item_count = Number($('.danger_item_count').html());
                if (danger_item_count>0) {
                    $('#step3 .danger_item_count').closest('div').show();
                } else {
                    $('#step3 .danger_item_count').closest('div').hide();
                }
            }
        });
    };

    var init_steps_behind = function () {
        $('.btn_submit').unbind().addClass('disabled');
        $('#submit_all').unbind('click');
        if (mnt_type) {
            $(".mnt_max_num").html(mnt_max_num);
            $('.mnt_adg_count').html(0);
            $('.new_item_count').html(0);
            $('.mnt_count0').html(0);
            $('.total_adg_count').html('---');
            $('.total_item_count').html('---');
            PT.MntAdgBox.init_tables();
            PT.AddItemBox2.init_tables();
            $('.btn_OK2').attr('confirmed', '0');
            $('.adg_2del_info, .danger_cats_info').hide();
        }
    };

    var init_dom = function () {
        // 计划列表顺序调整
        $.map($('#campaign_list label.s_color'), function (obj) {
            var pad_div = $(obj).next('div.clearfix');
            $('#campaign_error').before($(obj)).before(pad_div);
        });

        $('#step1').on('keyup', '.keyup_restore', function(){
            $(this).closest('.input_error').removeClass('input_error');
        });

        $(":radio[name='campaign']").change(function(){
            $('#campaign_error').hide();
            campaign_id = this.value;
            $('#campaign_id').val(campaign_id);
            campaign_title = $(this).closest("label").text();
            init_steps_behind();
        });

        $(":radio[name='mnt_type']").change(function(){
            $('#mnt_type_error').hide();
			$('#div_max_price, #div_budget').removeClass('input_error');
            mnt_type = this.value;
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
                    $('#max_price, #budget').attr('disabled', false);
                    $('#chk_rt').attr('checked', false);
                    $('#div_max_price,#div_budget').slideDown();
                    $('#div_chk_rt').slideUp();
                    break;
                case '2':
                    mnt_name = '重点托管 ';
                    budget_recm = 100;
                    budget_min = 100;
                    budget_max = 5000;
                    max_price_min = 0.8;
                    max_price_max = 20;
                    mnt_max_num = 10;
                    $('#chk_rt').attr('checked', true);
                    $('#budget').attr('disabled', false);
                    $('#max_price').attr('disabled', true);
                    $('#chk_rt').attr('disabled', false);
                    $('#div_budget,#div_chk_rt').slideDown();
                    $('#div_max_price').slideUp();
                    break;
            }
            $('#max_price').val(max_price_recm);
            $('#budget_tip').text('['+budget_min+'-'+budget_max+']元');
            $('#budget').attr({min:30,max:budget_max})
            $('[name="mnt_name"]').html(mnt_name);
            $('#mnt_max_num').val(mnt_max_num);
            $('#budget').val(budget_recm);
            $('#budget_range').html('(' + budget_min + '~' + budget_max + '元)');
            $('div.mnt_description span[mnt_type]').hide().filter('[mnt_type="'+mnt_type+'"]').show();
            init_steps_behind();
        });

        $(".btn_prev").click(function(){
            $("#step"+step_index).fadeOut("fast", function () {
                step_index--;
                $("#step"+step_index).fadeIn("fast");
                $("#mnt_wizard .wrap>div").removeAttr('class');
                $("#mnt_wizard .wrap>div:lt("+(step_index-1)+")").addClass('finished');
                $("#mnt_wizard .wrap>div:eq("+(step_index-1)+")").addClass('current');
                $("#mnt_wizard .wrap>div:gt("+(step_index-1)+")").addClass('todo');
            });
        });

        $(".btn_next").click(function(){
          if(step_index==2){
            var mnt_count0 = Number($(".mnt_count0").html());
            if (mnt_count0==0) {
                PT.alert('亲，请先选择宝贝加入托管!');
                return;
            }
            if (mnt_type=='1') {
                if (isNaN($('.total_adg_count').html())) {
                    PT.show_loading('正在检查将被删除的宝贝');
                    PT.sendDajax({
                        'function':'mnt_get_adg_list',
                        'campaign_id':campaign_id,
                        'page_no':1,
                        'page_size':50,
                        'sSearch':'',
                        'rpt_days':7,
                        'into_next_step':1
                    });
                } else if (Number($('.total_adg_count').html())>0 && $('#modal_del_unmnt_adg .btn_OK2').attr('confirmed')=='0') {
                    $('#modal_del_unmnt_adg .into_next_step').show();
                    $('#modal_del_unmnt_adg .btn_OK2').hide();
                    PT.MntAdgBox.confirm_2del_unmnt_adg();
                } else {
                    $.fancybox.close();
                    $('#modal_del_unmnt_adg .btn_OK2').attr('confirmed', '0');
                    into_next_step();
                }
            } else {
                $.fancybox.close();
                into_next_step();
            }
          }


        });

         $("#check_setup_one").validate({
            rules: {
              campaign: {
                required: true,
              },
              mnt_type: {
                required: true,
              },
              max_price: {
                required: true,
                number:true,
                custom:true
              },
              budget: {
                required: true,
                number:true,
                custom:true
              }
            },
            success: function() {
              max_price = $("#max_price").val();
              budget = $("#budget").val();
              confirm_mnt_campaign();
              //$.alert("恭喜，没有问题了。");
              return false;
            }
          })

        $(".into_next_step").click(function () {
            $(this).closest('.modal').modal('hide');
            into_next_step();
        });

        $(".trigger_more_setting").click(function() {
            var trigger_div = $('.div_more_setting');
            trigger_div.slideToggle();
            $(this).find('i').toggleClass('icon-pc-chevron-bottom').toggleClass('icon-pc-chevron-top');
        });

        //$('.check_value').bind('keyup mouseout', check_is_agree);
    };

	return {
		init: function () {
			PT.Base.set_nav_activ(1, mnt_index-1);
			init_dom();
			App.initUniform();
		},
		into_next_step: into_next_step,
		mnt_campaign_setter_callback: function (callback_list, context) {
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
	                        break;
                        case 0:
                            result_str = '失败';
	                        result_cls = 'fail';
                            break;
                        case 1:
                            result_str = '成功';
	                        result_cls = 'success';
                            break;
                        case 2:
                            result_str = '存在错误';
	                        result_cls = 'error';
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
	            PT.alert(msg, undefined, function () {
                    PT.show_loading("正在刷新页面");
                    window.location.href='/qnpc/mnt_campaign/'+campaign_id;
//	                if (report[0]['result']==1) {
//	                    PT.show_loading("正在刷新页面");
//		                window.location.reload(true);
//	                } else {
//	                    $('#submit_all').unbind('click').click(function () {
//	                        PT.alert(msg);
//	                    });
//	                }
	            });
	        }
		}
	}
}();
