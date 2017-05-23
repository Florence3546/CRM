/**
 * Created by Administrator on 2015/10/10.
 */
define(['../common/common','jl6/site_media/widget/alert/alert','jl6/site_media/widget/ajax/ajax',
        '../add_item_box/add_item_box','dataTable','jslider'],function(common,alert,ajax,addItemBox){

    var sliderValue = 38;//存储滑杆的value

    var init = function(){

        var carousel_next = true;
        var to_step;
        var mnt_type = 0;
        var max_price_pc = 0;
        var max_price_yd = 0;
        var adg_counts = 500;
        var budget= 0;
        var mnt_index = Number($('#mnt_index').val());
        var strategy = {};
        var old_mnt_type = 0;
        var old_camp_id = 0;
        var campaign_id = parseInt($('#campaign_id').val());
        var loadAdg = false;

        //进入下一步
        $('.next_step').on('click',function(){
            carousel_next = true;
            to_step = $(this).attr('to_step');
            //进入下一步前需要先验证当前步骤的结果
            switch(parseInt(to_step)){
                case 2:
                    var select_radio = $('input[name="campaign"]:checked');
                    campaign_id = select_radio.val();
                    $('#campaign_id').val(campaign_id);
                    if (!campaign_id) {
                        alert.show('请选择托管计划！');
                        return false;
                    }
                    $('.select_compaign_name').text(select_radio.attr('title'));
                    if(old_camp_id!=campaign_id){
                        $('.mnt_type_desc').removeClass('checked');
                        $('.mnt_type_title').find('.unselect').removeClass('hide');
                        $('.mnt_type_title').find('.select').addClass('hide');
                        mnt_type = 0;
                    }
                    break;
                case 3:
                    if (!mnt_type) {
                        alert.show('还未选择托管类型！');
                        return false;
                    }
                    //长尾及ROI托管时无需设置自动优化状态
                    if(mnt_type == 1 || mnt_type ==3){
                        $('.jslider-box input').slider("value",38);
                        sliderValue = 38;
                    }else{
                        $('.jslider-box input').slider("value",62);
                        sliderValue = 62;
                    }

                    setBigFactor(sliderValue);

                    $('#campaign_budget').tooltip('hide');
                    $('.campaign_max_price').tooltip('hide');
                    ajax.ajax('get_recommend_price',{campaign_id:campaign_id,mnt_type:mnt_type},function(data){
                        $('#campaign_budget').val(data.budget);
                        if(mnt_type==1||mnt_type==3){
                            $('.campaign_max_price').val(Math.max(2*parseFloat(data.cat_cpc),1).toFixed(2));
                        }else{
                            $('.campaign_max_price').val(Math.max(2*parseFloat(data.cat_cpc),2).toFixed(2));
                        }

                        $('#suggest_budge').text(data.budget);
                        $('#avg_price').text(parseFloat(data.cat_cpc).toFixed(2));

                        //根据托管类型设置第三步托管策略中的相关参数
                        $('#min_price').text(parseFloat(0.20).toFixed(2));
                        if(mnt_type==1||mnt_type==3){
                            $('#min_budget').text(30);
                            $('#max_budget').text(3000);
                            $('#suggest_price').text(parseFloat(1.5*data.cat_cpc).toFixed(2)+"~"+parseFloat(2.5*data.cat_cpc).toFixed(2))
                            $('#price_multiple').text('1.5~2.5');
                            $('.set_chk_rt').addClass('hide');

                        }else{
                            $('#min_budget').text(30);
                            $('#max_budget').text(10000);
                            $('#suggest_price').text(parseFloat(2.0*data.cat_cpc).toFixed(2)+"~"+parseFloat(3.0*data.cat_cpc).toFixed(2));
                            $('#price_multiple').text('2.0~3.0');
                            $('.set_chk_rt').removeClass('hide');
                        }
                    });
                    break;
                case 4:
                    budget=Number($('#campaign_budget').val());
                    var min_budget = $('#min_budget').text();
                    var max_budget = $('#max_budget').text();
                    if(isNaN(budget)||(parseInt(budget)!=budget)){
                        $('#campaign_budget').tooltip({title:'日限额只能为整数',placement:'top',trigger:'manual'});
                        $('#campaign_budget').tooltip('show');
                        return false;
                    }
                    if(budget<parseInt(min_budget)||budget>parseInt(max_budget)){
                        $('#campaign_budget').tooltip({title:'日限额最低'+$('#min_budget').text()+'元，最高'+$('#max_budget').text()+'元',placement:'top',trigger:'manual'});
                        $('#campaign_budget').tooltip('show');
                        return false;
                    }
                    max_price_pc=Number($('#campaign_max_price_pc').val());
                    max_price_yd=Number($('#campaign_max_price_yd').val());

                    if(isNaN(max_price_pc)){
                        $('#campaign_max_price_pc').tooltip({title:'请输入数字',placement:'top',trigger:'manual'});
                        $('#campaign_max_price_pc').tooltip('show');
                        return false;
                    }

                    if(max_price_pc<Number($('#min_price').text())||max_price_pc>99.99){
                        $('#campaign_max_price_pc').tooltip({title:'关键词限价最低'+Number($('#min_price').text())+'元，最高99.99元',placement:'top',trigger:'manual'});
                        $('#campaign_max_price_pc').tooltip('show');
                        return false;
                    }

                    if(isNaN(max_price_yd)){
                        $('#campaign_max_price_yd').tooltip({title:'请输入数字',placement:'top',trigger:'manual'});
                        $('#campaign_max_price_yd').tooltip('show');
                        return false;
                    }

                    if(max_price_yd<Number($('#min_price').text())||max_price_yd>99.99){
                        $('#campaign_max_price_yd').tooltip({title:'关键词限价最低'+Number($('#min_price').text())+'元，最高99.99元',placement:'top',trigger:'manual'});
                        $('#campaign_max_price_yd').tooltip('show');
                        return false;
                    }

                    //已阅读，跳转到下一步
                    strategy['budget'] = budget;
                    strategy['max_price_pc'] = max_price_pc.toFixed(2);
                    strategy['max_price_yd'] = max_price_yd.toFixed(2);
                    strategy['bid_factor'] = get_bid_factor();
                    strategy['platform'] = get_platform();
                    strategy['schedule'] = get_schedule();
                    strategy['opt_wireless'] = get_opt_wireless();
                    strategy['area'] = get_area();
                    strategy['mnt_opt_type'] = get_chk_mnt_type();
                    strategy['chk_rt'] = 0;
//                    if(mnt_type==1||mnt_type==3){
//                        strategy['chk_rt'] = 1;
//                    }else{
//                        strategy['chk_rt'] = get_mnt_rt();
//                    }
                    addItemBox.setStrategy(strategy);

                    $('.mnt_max_price_pc').text(max_price_pc.toFixed(2));
                    $('.mnt_max_price_yd').text(max_price_yd.toFixed(2));
                    $('.mnt_budget').text(budget);

                    if(strategy['chk_rt']=="1"){
                        $('.mnt_chk_rt').text('开启实时优化');
                    }else{
                        $('.mnt_chk_rt').text('关闭实时优化');
                    }

                    if(mnt_type==1||mnt_type==3){
                        $('.mnt_service_1').removeClass('hide');
                        $('.mnt_service_2').addClass('hide');
                    }else{
                        $('.mnt_service_2').removeClass('hide');
                        $('.mnt_service_1').addClass('hide');
                    }
                    $('#term_service').modal({backdrop: 'static', keyboard: false});
                    return false;
                    break;
                case 5:
                    if(!addItemBox.getSelectCounts()){
                        alert.show('请选择托管宝贝！');
                        return false;
                    }

                    var has_error = false;
                    $('input[name="adg_title"]').each(function(){
                        if($.trim($(this).val()).length==0||$(this).val()=='正在获取...'){
                            alert.show('创意标题不能为空!');
                            has_error = true;
                            return;
                        }
                        if(parseInt($(this).attr('char_delta'))<0){
                            alert.show('创意标题的长度不能超过20个汉字!');
                            has_error = true;
                            return;
                        }
                    });

                    if(has_error){
                        return false;
                    }
                    var adg_count = $('#item_cart tbody tr[tb="1"]').length,
                        item_count = $('#item_cart tbody tr[tb="0"]').length;
                    if (adg_count) {
                        $('#adg_success_count').text(adg_count + '个宝贝即将加入托管');
                        $('.adg_show_div').show();
                    }else{
                        $('.adg_show_div').hide();
                    }
                    if (item_count) {
                        $('#item_success_count').text(item_count + '个宝贝即将加入托管');
                        $('.item_show_div').show();
                    }else{
                        $('.item_show_div').hide();
                    }
                    break;
                default:
                    break;
            }

            $('.progress-bar[to_step='+to_step+']').css('width','267px');
            $("#progress_step_box").carousel(parseInt(to_step)-1);
        });

        $('.last_step').on('click',function(){
            carousel_next = false;
            to_step = $(this).attr('to_step');
            $('.progress-bar[to_step='+(parseInt(to_step)+1)+']').css('width','0');
            $('.progress_step[step='+(parseInt(to_step)+1)+']').removeClass('current');
            $("#progress_step_box").carousel(parseInt(to_step)-1);
        });

        //聚焦后，关掉tips提示
        $('#campaign_budget,.campaign_max_price').focus(function(){
            $('#campaign_budget,.campaign_max_price').tooltip('destroy')
        });

        $('#progress_step_box').on('slid.bs.carousel', function () {
            if(carousel_next){
                $('.progress_step[step='+to_step+']').addClass('current');
                $('.progress_step[step='+to_step+']').addClass('current');
            }
        });

        //选择计划
        $(":radio[name='campaign']").change(function(){
            $('#campaign_id').val(this.value);
        });

        //选择托管类型
        $('.mnt_type_box').click(function(){
            var obj = $(this).find('.mnt_type_title>i');
            mnt_type = parseInt(obj.attr('mnt_type'));
            adg_counts = parseInt(obj.attr('adg_counts'));
            $('.mnt_type_desc').removeClass('checked');
            $('.mnt_type_title .unselect').removeClass('hide');
            $('.mnt_type_title .select').addClass('hide');
            $(this).find('.unselect').addClass('hide');;
            $(this).find('.select').removeClass('hide');;
            $('.mnt_type_desc[mnt_type='+mnt_type+']').addClass('checked');
            $('#mnt_type_error').addClass('hide');
            $('.select_mnt_type').text(obj.attr('mnt_name'));
        });

        //新建计划
        $('.js_create_camp').click(function(){
            common.goto_ztc(1,'','','');
        });

        //阅读条款
        $('#read_service').on('change',function(){
            if($(this).prop('checked')){
                $('#check_read_service').removeClass('disabled');
            }else{
                $('#check_read_service').addClass('disabled');
            }
        });

        //阅读淘宝规则 确定
        $('#check_read_service').click(function(){
            if($('#read_service').prop('checked')){
                $('#term_service').modal('hide');
                var options = {
                    mnt_type:mnt_type,
                    adg_counts:adg_counts,
                    cur_count:0,
                    strategy:strategy
                }
                var params = {
                    campaign_id:campaign_id,
                    page_no:1,
                    page_size:50,
                    sSearch:'',
                    exclude_existed:1,
                    auto_hide:0
                }

                //初始化add_item_box，加载不在当前计划下的宝贝列表,如果初始化过，则无需再初始化
                if(!loadAdg){
                    addItemBox.init(options);
                    loadAdg = true;
                }

                //如果选择的托管类型或计划有变化，则需重新加载add_item_box
                if(old_mnt_type!=mnt_type || old_camp_id != campaign_id){
                    old_mnt_type=mnt_type;
                    old_camp_id = campaign_id
                    addItemBox.reDraw(options);
                    addItemBox.loadItemList(params);
                    addItemBox.loadAdgList({campaign_id:campaign_id,page_no:1,page_size:50,sSearch:'',rpt_days:7,auto_hide:0});
                }

                $('#item_cart .limit_price_pc').attr('value',strategy.max_price_pc).text(strategy.max_price_pc);
                $('#item_cart .limit_price_yd').attr('value',strategy.max_price_yd).text(strategy.max_price_yd);
                $('#item_cart .adg_cfg').attr('camp_limit',1);

                $('.progress-bar[to_step='+to_step+']').css('width','267px');
                $("#progress_step_box").carousel(parseInt(to_step)-1);
            }
        });

        //不升级时进入计划主页
        $('#no_upgrade_suggest').click(function(){
            window.location.href = '/mnt/mnt_campaign/'+campaign_id;
        });

        //提交数据
        var step_num = 0;
        var interval;//定时器，滚动效果需要
        var steps =  $('.step-index');
        //记录当前提交的请求位置1：提交托管策略，2：提交计划内的宝贝，3：提交记录外的宝贝
        var ajax_step = 1;
        $('#submit_data').click(function(){
            $('#submit_data').unbind('click');
            $('#to_mnt_page').children('a').remove();
            interval = setInterval(submitData,500);
            ajax.ajax('mnt_campaign_setter',
                      {'campaign_id':campaign_id,
                       'set_flag':1,
                       'mnt_type':mnt_type,
                       'max_price':strategy.max_price_pc,
                       'mobile_max_price':strategy.max_price_yd,
                       'budget':strategy.budget,
                       'mnt_index':mnt_index,
                       'mnt_rt':strategy.chk_rt,
                       'mnt_bid_factor':strategy.bid_factor,
                       'area':strategy.area,
                       'platform':strategy.platform,
                       'schedule':strategy.schedule,
                       'opt_wireless':strategy.opt_wireless},
                        function(data){
                            if(data.result=='0'){
                                if(data.error_msg=='no_permission'){
                                    clearInterval(interval);
                                    $('#upgrade_suggest_modal').modal({backdrop: 'static', keyboard: false});
                                }else{
                                    alert.show(data.error_msg);
                                }
                                $(steps[step_num-1]).find('.node').html('<a><i class="iconfont red" style="color:red">&#xe61e;</i></a>');
                                return false;
                            }

                            if(data.warn_msg_dict){
                                var error_dict = eval('('+data.warn_msg_dict+')');
                                for (var error in error_dict){
                                    $('#'+error+'_error').text(error_dict[error]);
                                }
                            }
                            ajax_step = 2;
                            //设置完托管策略后，提交计划内宝贝
                            //如果此时滚动进度停在当前步骤，则需手动开始执行下一步
                            if($(steps[step_num]).hasClass('stop')){
                                step_num++;
                                to_next();
                                update_mnt_adg();
                            }
                        },null,{'url':'/mnt/ajax/'});
        });

        //提交数据
        var submitData = function(){
            //到提交托管策略时，需清除interval，后面的滚动有ajax回调函数驱动，停止位置用stop标记
            to_next();
            if($(steps[step_num]).hasClass('stop')){
                //检查第一步（提交托管策略）是否完成，如果完成则进行第二部提交
                if(ajax_step==2){
                    step_num++;
                    to_next();
                    update_mnt_adg();
                }
                clearInterval(interval);
            }else{
                step_num++;
            }
        };

        var load_img = $('#load_img').attr('src');
        //提交滚动到下一步
        var to_next = function(){
            if(step_num>0){
                $(steps[step_num-1]).find('.node').html('<a><i class="iconfont base">&#xe63f;</i></a>');
                $(steps[step_num-1]).next().addClass('base');
                $(steps[step_num-1]).next().find('.step_error').fadeIn(500);
                if(step_num>=steps.length){
                    return false;
                }
            }

            $(steps[step_num]).parents('ul').prev('.step_name').addClass('base');
            $(steps[step_num]).find('.line').addClass('bg_base');
            $(steps[step_num]).find('.node').html("<img src='"+load_img+"' alt=''>");

            if($(steps[step_num]).offset().top+120>$(window).height()){
                $("html,body").animate({scrollTop: $(steps[step_num]).offset().top+120-$(window).height()}, 200);
            }

        }

        //提交计划内的宝贝
        var update_mnt_adg = function(){
            var mnt_adg_info = addItemBox.getMntAdgInfo();
            ajax.ajax('update_mnt_adg',
                        {'mnt_adg_dict':JSON.stringify(mnt_adg_info.mnt_adg_dict),
                         'update_creative_dict': JSON.stringify(mnt_adg_info.update_creative_dict),
                         'new_creative_list': JSON.stringify(mnt_adg_info.new_creative_list),
                         'camp_id':campaign_id,
                         'mnt_type':mnt_type,
                         'flag':2
                        },function(data){
                            //如果有提交异常的宝贝，需提示错误信息
                            if(data.failed_count){
                                $('#adg_failed_count').parent().removeClass('hide');
                                require(['../add_item_box/error_adg_list'],function(error){
                                    error.setError($('#error_msg_adg'),{error_list:data.failed_item_dict});
                                });
                            }
                            $('#adg_success_count').text(data.success_count + '个宝贝加入托管成功');
                            $('#adg_failed_count').text(data.failed_count);
                            submit_new_item();
                            step_num++;
                            to_next();
                        },null,{'url':'/mnt/ajax/'})
        };

        //提交计划外的宝贝
        var submit_new_item = function(){
            var new_item_dict = addItemBox.getNewItemDict();
            ajax.ajax('add_new_item',{ 'new_item_dict':JSON.stringify(new_item_dict),
                                 'camp_id':campaign_id,
                                 'mnt_type':mnt_type},
                function(data){
                    //如果有提交异常的宝贝，需提示错误信息
                    if(data.failed_count){
                        $('#item_failed_count').parent().removeClass('hide');
                        $('#error_msg_item').removeClass('hide');
                        require(['../add_item_box/error_adg_list'],function(error){
                            error.setError($('#error_msg_item'),{error_list:data.failed_item_dict});
                        });
                    }
                    $('#item_success_count').text(data.success_count + '个宝贝加入托管成功');
                    $('#item_failed_count').text(data.failed_count);
                    step_num++;
                    to_next();
                    $('#to_mnt_page').html('<a class="btn btn-primary btn-sm" href="/mnt/mnt_campaign/'+campaign_id+'">进入计划主页</a>');
                    $('.commit_result').fadeIn(200);
                    $('#to_mnt_main').click(function(){
                        window.location.href = '/mnt/mnt_campaign/'+campaign_id;
                    });
                },null,{'url':'/mnt/ajax/'});
        };

        //点击li，选中计划
        $('#select_campaign>ul>li span').click(function(){
            var radio = $(this).parent().find('[type=radio]');
            if(!radio.prop('disabled')){
                radio.prop("checked","checked");
            }
        });

        //滑杆 调价力度
        $('.jslider-box input').slider({
            from: 0,
            to: 100,
            skin: 'power',
            onstatechange: function(value){
                setBigFactor(value);
            },
            callback: function(value) {
                sliderValue = value;
            }
        });

        $("[data-toggle='tooltip']").tooltip({html:true});

        /**
         * 点击区域，选中checkbox 和 radio
         */
        $('.select_div').on('click', ':radio,:checkbox', function (e) {
            //停止事件冒泡,当点击的是checkbox时,就不执行父div的click
            e.stopPropagation();
        });
        $('.select_div').click(function(){
            $(this).find(':radio,:checkbox').click();
        });
    };

    //获取计划优化方式（是否自动优化）
    var get_mnt_rt = function() {
		var mnt_rt = $('input[name=chk_rt]:checked').val();
        return mnt_rt;
	}

    //获取宝贝优化方式（自动/只改价）
    var get_chk_mnt_type = function() {
		var chk_mnt_type = $('input[name=chk_mnt_type]:checked').val();
        return parseInt(chk_mnt_type);
	}

    //获取计划优化方式（是否自动优化）
    var get_bid_factor = function() {
        if(sliderValue>50){
            $('.mnt_bid_factor').text('偏流量导向');
        }else if(sliderValue==50){
            $('.mnt_bid_factor').text('均衡导向');
        }else{
            $('.mnt_bid_factor').text('偏ROI导向');
        }
		return sliderValue;
	};

    var get_schedule = function(){
        var schedule = $('input[name=schedule]').is(':checked');
		if (schedule){
            $('.mnt_schedule').text('开启优化');
            return 1;
        }else{
            $('.mnt_schedule').text('未开启优化');
            return 0;
        }
    }

    var get_platform = function(){
        var platform = $('input[name=platform]').is(':checked');
		if (platform){
            $('.mnt_platform').text('开启自动优化');
            return 1;
        }else{
            $('.mnt_platform').text('关闭自动优化');
            return 0;
        }
    }

    var get_opt_wireless = function(){
        var opt_wireless = $('input[name=opt_wireless]').is(':checked');
		if (opt_wireless){
            $('.mnt_opt_wireless').text('开启无线投放');
			return 1;
        }else{
            $('.mnt_opt_wireless').text('关闭无线投放');
            return 0;
        }
    }

    var get_area = function(){
        var area = $('input[name=area]').is(':checked');
		if (area){
            $('.mnt_area').text('关闭港澳台、国外投放');
            return 1;
        }else{
            $('.mnt_area').text('开启港澳台、国外投放');
            return 0;
        }
    }

    //设置宝贝推广意向
    var setBigFactor = function(value){
        var big_factor_value = Math.abs(value-50)
        if(value<50){
            $('#big_factor_name').text('偏向ROI');
            $('#big_factor_value').removeClass('hide');
        }else if(value==50){
            $('#big_factor_name').text('均衡模式');
            $('#big_factor_value').addClass('hide');
            $('#big_factor_value').text('0%')
        }else{
            $('#big_factor_name').text('偏向流量');
            $('#big_factor_value').removeClass('hide');
        }
        $('#big_factor_value').text((big_factor_value/50*100).toFixed(0)+'%');
    }
    return {
        init:function(){
            init();
        }
    }
});
