PT.namespace('MntCampaign');
PT.MntCampaign = function () {
    var camp_id = $('#campaign_id').val(),
        mnt_index=parseInt($('#mnt_index').val()),
        mnt_type=parseInt($('#mnt_type').val()),
        camp_budget_min = 30, camp_budget_max = 99999,
        mnt_opter = parseInt($('#mnt_opter').val())? parseInt($('#mnt_opter').val()): 0;

    if (mnt_type == 1) {
        camp_budget_min = 100;
        camp_budget_max = 300;
    } else if(mnt_type == 2){
        camp_budget_min = 100;
        camp_budget_max = 5000;
    }

    var init_record_table=function(){
        var record_table=$('#record_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": false,
            "bFilter": true,
            "bInfo": true,
            "aaSorting": [[1,'desc']],
            "bAutoWidth":false,//禁止自动计算宽度
            "iDisplayLength": 100,
            "sDom":"",
            "aoColumns": [
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true}
            ],
            "oLanguage": {
                    "sProcessing" : "正在获取数据，请稍候...",
                    "sEmptyTable":"没有数据",
            }
        });
    };

    var init_dom=function(){

        // $('#id_budget').attr('data-original-title','建议将日限额设在'+camp_budget_min+'~'+camp_budget_max+'元之间');

        $('#id_close_mnt').click(function(){
            var body_str="1、系统会停止托管您的宝贝，但不会改变当前计划的推广状态<br/>2、您可以重新开启，但需要重新选择计划和宝贝等等";
            $.confirm({
                backdrop:'static',
                title:'确认【解除托管】该计划吗？',
                body:body_str,
                okBtn:'解除',
                cancelBtn:'不解除',
                okHide:function(){
                    PT.sendDajax({'function':'mnt_mnt_campaign_setter','campaign_id':camp_id,'set_flag':0,'mnt_type':mnt_type});
                }
            });
        });

        $('.edit_camp_price').on('click', function(){
            var type = $(this).parents('div:first').attr('type'),
                title = '', price_desc = '';
            switch (type) {
                case 'budget':
                    title = '推广计划日限额';
                    price_desc = '建议设在'+camp_budget_min+'~'+camp_budget_max+'元之间';
                    break;
                case 'max_price':
                    title = '关键词最高限价';
                    price_desc = '建议设在0.80~5.00元之间';
                    break;
                case 'min_cost':
                    title = '每日最低花费';
                    price_desc = '尚未实现此功能';
                    break;
            }
            //获取当前默认的价格
            var default_price = $(this).parent().find(".jq_price").html();
            if("不限"==default_price){
                default_price = 0.00;
            }
            var body_str='<div class="input-append mb0"><input class="w50" type="text" value="'+default_price+'" id="price"><span class="add-on">元</span></div><span class="gray ml10">('
                            + price_desc+')</span>';
            $.confirm({
                backdrop:'static',
                title:title,
                okBtn:'提交',
                width:'small',
                body:body_str,
                okHide:function(){
                    var price = $('#price').val(),
                        error_msg = eval('submit_'+type+'(price)');
                    if (error_msg) {
                        $.alert({
                            title:'填写错误',
                            body:error_msg,
                            width:'small',
                        });
                        return false;
                    }
                    return true;
                }
            });
        });

        $('.edit_rt_engine').on('click', function(){
            var type = $(this).parents('div:first').attr('type');
            var title = '系统提示';
            var msg = ''
            if (type == 1){
            	type = 0
                msg = '确定要关闭实时优化功能吗？'
            }else{
                msg = '确定要开启实时优化功能吗？'
                type = 1
            }
            var body_str='<div class="input-append mb0"></div><span class="gray ml10">' + msg+ '</span>';
            $.confirm({
                backdrop:'static',
                title:title,
                okBtn:'确定',
                width:'small',
                body:body_str,
                okHide:function(){
                    PT.sendDajax({'function':'mnt_update_rt_engine_status', 'campaign_id':camp_id, 'mnt_type':mnt_type, 'status':type});
                    return true;
                }
            });
        });

        // $('.edit_price').click(function(){
        //     $(this).prev().attr('disabled',false).removeClass('text_input');
        //     $(this).fadeOut('fast',function(){
        //         $(this).next().fadeIn('fast');
        //     });
        // });
        // $('.cancel_price').click(function(){
        //     var jq_span=$(this).parent(),
        //         type_id=$(this).next().attr('id'),
        //         old_price=Number(jq_span.parent().find('input[type=hidden]').val());
        //     if (type_id=='submit_max_price') {
        //         old_price=old_price.toFixed(2);
        //     }
        //     jq_span.prev().prev().blur();
        //     jq_span.prev().prev().val(old_price).addClass('text_input').attr('disabled',true);
        //     jq_span.fadeOut('fast',function(){
        //         jq_span.prev().fadeIn('fast');
        //     });
        // });

        // $('#submit_max_price').click(function(){
        //     var max_price= $.trim($('#id_max_price').val()), submit_dict = {};
        //     if(max_price==$('#max_price_bak').val()){
        //         $('#max_price_bak').nextAll().find('.cancel_price').click();
        //         return;
        //     }
        //     if(max_price==''||isNaN(max_price)){
        //         $("#id_max_price").focus();
        //         PT.alert('关键词最高限价必须是数字！');
        //     }else if (Number(max_price)<0.2||Number(max_price)>5.00){
        //         PT.alert('关键词最高限价必须介于0.20~5.00元之间！');
        //     }else{
        //         submit_dict['max_price'] = max_price;
        //         update_cfg(submit_dict);
        //     }
        // });

        // $('#submit_budget').click(function(){
        //     var budget= $.trim($('#id_budget').val());
        //     if(budget == $('#budget_bak').val()){
        //         $('#budget_bak').nextAll().find('.cancel_price').click();
        //         return;
        //     }
        //     var submit_dict={'budget':budget};
        //     if(budget == ''){
        //         PT.alert('请输入日限额！');
        //     }else if (isNaN(budget) || /^[1-9]\d*$/.test(budget)==false){
        //         PT.alert('日限额必须是有效整数！');
        //     }else if (parseInt(budget,10) < camp_budget_min){
        //         PT.alert('日限额最少'+camp_budget_min+'元！');
        //     }else if (parseInt(budget,10) > camp_budget_max){
        //         var tip="日限额超过<span class='red'>"+camp_budget_max+"</span>元！可能导致<span class='red'>花费较高</span>！您确认将日限额设为<span class='red'>"+Number(budget)+"</span>元吗？";
        //         PT.confirm(tip,update_cfg,[submit_dict]);
        //     }else{
        //         update_cfg(submit_dict);
        //     }
        // });

        $('.quick_oper').click(function(){
            if($(this).hasClass('disabled')){
                return;
            }
            var that=this,
                stgy=parseInt($(this).attr('stgy')),
	            msg="系统会定期自动改价换词，您确定现在就要人工干预吗？";
            $.confirm({
                backdrop:'static',
                body:msg,
                okBtn : '干预',
                cancelBtn : '不干预',
                okHide:function(){
                    $(that).find('img').show();
                    $('#quick_oper_tip').attr('is_recent','True');
                    update_quick_oper_tip();
                    PT.sendDajax({'function':'mnt_quick_oper', 'campaign_id':camp_id, 'mnt_type':mnt_type, 'stgy':stgy});
                }
            });
        });

        $('.quick_oper_adg').on('click', function(){
            var stgy=parseInt($(this).attr('stgy')),
                jq_inputs = $('#adgroup_table').find('tbody tr .kid_box:checked'),
                checked_num = jq_inputs.length,
                adg_id_list = [];
            if (!checked_num) {
                PT.alert('请选择要操作的推广宝贝');
                return;
            }
            jq_inputs.each(function(){
                if ($(this).parents('tr:first').attr('is_quick_opered') == '0') {
                    adg_id_list.push(parseInt($(this).val()));
                }
            });
            if (!adg_id_list.length){
                PT.alert('今天已经优化过该宝贝，不能再优化了（每天只能优化一次）');
                return;
            }
            PT.sendDajax({'function':'mnt_quick_oper', 'campaign_id':camp_id, 'adg_id_list':adg_id_list, 'mnt_type':mnt_type, 'stgy':stgy});
        });

        $('#camp_mnt_oper').click(function(){
            var mnt_oper=parseInt($(this).attr('mnt_oper')),
                msg=(mnt_oper?'即将启动自动优化，同时将计划设置为参与推广，确认启动吗？':'即将暂停自动优化，同时将计划设置为暂停推广，确认暂停吗？');
            PT.confirm(msg,update_camp_status,[mnt_oper]);
        });

        $('#li_opt_record').click(function(){
            if(Number($(this).attr('switch'))===0){
                PT.show_loading('正在获取操作记录');
                PT.sendDajax({'function':'mnt_get_opt_record','campaign_id':camp_id,'mnt_type':mnt_type});
                $(this).attr('switch',1);
            }
        });

        $('#li_msg_record').click(function(){
            if($(this).attr('switch')===0){
                PT.show_loading('正在获取顾问留言');
                PT.sendDajax({'function':'web_get_sigle_comment','obj_id':camp_id,'obj_type':1,'name_space':'MntCampaign'});
                $(this).attr('switch',1);
            }
        });

        // 初始化 inputtags
        $('#camp_blackword').tagsInput({
            width: 515,
            height: 100,
            defaultText:'输入屏蔽词，回车确定'
        });

        $(document).on('change', 'input[name="opt_type"]', function () {
            PT.sendDajax({'function': 'mnt_change_mntcfg_type', 'camp_id':camp_id, 'cfg_type': $(this).data('cfg'), 'mnt_type': mnt_type});
            PT.light_msg('算法设置', '已经切换到【'+ $(this).next().text() + '】');
        });
		
		$('#div_camp_blackword').on('show',function(){
			var campaign_id = $("#campaign_id").val();
			$('#camp_blackword').importTags('');
			PT.sendDajax({'function':'web_get_longtail_blackword','campaign_id':campaign_id})
        });
		
        $('#div_camp_blackword').on('click', '.submit', function () {
            var blackword = $('#camp_blackword').val();
//            if (blackword) {
            $('#div_camp_blackword').modal('shadeIn');
            $.confirm({
                title:'',
                width:'small',
                body:'注意：如果宝贝在其他计划下推广，包含屏蔽词的关键词也会被删除，确认删除吗？',
                okBtn:'确定删除',
                okHide:function(){
                    PT.show_loading('正在保存屏蔽词并删除相关关键词');
                    PT.sendDajax({'function':'web_submit_camp_bwords', 'camp_id':camp_id, 'blackwords':blackword, });
                },
                cancelHidden:function(){
                    $('#div_camp_blackword').modal('shadeOut');
                }
            });
//            }
        });

        $('.adgroup_select_days').on('change',function(e,v){
           PT.sendDajax({'function':'mnt_get_mnt_campaign','rpt_days':v,'campaign_id':camp_id,'auto_hide':0});
        });

    };

/*
*	   	$('#div_camp_blackword').on('show',function(){
        	alert('fuck')
        });

        $('#div_camp_blackword').on('shown',function(){
        	alert('fuck afert')
        });
        
        $('#div_camp_blackword').on('hide',function(){
        	alert('fuck afert')
        });    
*/

    var submit_budget = function(price){
        var submit_dict={'budget':parseInt(price)},
            error_msg = '';
        if(price === ''){
            error_msg = '请输入日限额！';
        }else if (isNaN(price) || /^[1-9]\d*$/.test(price)==false){
            error_msg = '日限额必须是有效整数！';
        }else if (parseInt(price,10) < 30){
            error_msg = '日限额最少30元！';
        }else if (parseInt(price,10) > camp_budget_max){
            var tip="日限额超过<span class='red'>"+camp_budget_max+"</span>元！可能导致<span class='red'>花费较高</span>！您确认将日限额设为<span class='red'>"+Number(price)+"</span>元吗？";
            $.confirm({
                backdrop:'static',
                title:'',
                body:tip,
                okHide:function(){
                    update_cfg(submit_dict);
                }
            });
        }else{
            update_cfg(submit_dict);
        }
        return error_msg;
    };

    var submit_max_price = function(price){
        var submit_dict = {}, error_msg = '';
        if(price===''||isNaN(price)){
            error_msg = '关键词最高限价必须是数字！';
        }else if (mnt_opter<2 && Number(price)<0.2||Number(price)>5.00){ // 方便客服设置更低限价
            error_msg = '关键词最高限价必须介于0.20~5.00元之间！';
        }else{
            submit_dict['max_price'] = Number(price);
            update_cfg(submit_dict);
        }
        return error_msg;
    };

    var submit_min_cost = function(price){
        $.alert({
            body:'尚未实现此功能',
            width:'small',
        });
        return '';
    };

    var update_cfg=function(submit_dict){
        PT.sendDajax({'function':'mnt_update_cfg','campaign_id':camp_id,'submit_data':$.toJSON(submit_dict),'mnt_type':mnt_type});
    };

    var update_camp_status = function(mnt_oper){
        PT.sendDajax({'function':'mnt_update_prop_status','campaign_id':camp_id,'status':mnt_oper,'mnt_type':mnt_type});
    };

    var update_quick_oper_tip = function(){
        var jq_tip=$('#quick_oper_tip'), is_active=jq_tip.attr('is_active'), is_recent=jq_tip.attr('is_recent'), tips='';
        if(is_active=='False' || is_recent=='True'){
            jq_tip.find('.quick_oper').addClass('disabled');
        } else {
            jq_tip.find('.quick_oper').removeClass('disabled');
        }
        if(is_active=='False'){
            tips='计划暂停托管，不能调整投入';
        }else if (is_recent=='True'){
            tips='今天已调整过，每天仅能调整一次';
        }else{
            tips='即时调整投入，每天仅能调整一次';
        }
        jq_tip.attr('data-original-title',tips);
    };

    return {
        init:function(){
            PT.show_loading('正在获取数据');
            init_dom();
            update_quick_oper_tip();
            PT.sendDajax({'function':'mnt_get_mnt_campaign','rpt_days':1,'campaign_id':camp_id,'auto_hide':0});
        },
        get_longtail_blackword_callback:function(json){
        	if (json!=""){
        		var ll = json.split(',');
        		for (var i in ll){
        			$('#camp_blackword').addTag(ll[i]);
        		}
        	}
        	
        }
        ,
        mnt_opter: mnt_opter,
        select_call_back: function(value){
            PT.show_loading('正在获取数据');
            PT.sendDajax({'function':'mnt_get_mnt_campaign','rpt_days':value,'campaign_id':camp_id,'auto_hide':0});
            PT.MntAdg.select_call_back(value);
        },
        get_campaign_back:function(data){
            var table_dom = template.compile(pt_tpm['sum_report.tpm.html'])(data);
            $('#sum_rpt').html(table_dom);
            $('.tips').tooltip({html: true});
            //PT.hide_loading();
        },
        opt_record_back:function(data){
            PT.hide_loading();
            var tr_dom = '';
            for (var i in data) {
                tr_dom += '<tr><td class="tc">'+data[i].opter+'</td><td class="tc">'+data[i].opt_time+'</td><td class="tc">'+data[i].opt_type+'</td><td class="tc">'+data[i].opt_desc+'</td></tr>';
            }
            $('#record_table').find('tbody').html(tr_dom);
            init_record_table();
        },
        get_sigle_comment_back:function(result){
            PT.hide_loading();
            var dom=template.render('template_single_comment',{'msg_list':result.msg_list});
            $('#msg_record').html(dom);
        },
        quick_oper_back:function(result, stgy){
            var index = stgy==1? 0:-1,
                oper_name = $.trim($('.quick_oper:eq(1) span').text());
            $('.quick_oper img').hide();
            if(!result){
                $('#quick_oper_tip').attr('is_recent','False');
                update_quick_oper_tip();
                PT.alert(oper_name + "失败，请刷新页面重新操作！");
            }
        },
        rt_engine_status_back:function(status){
	        if(status == 0){
	            $("#lbl_rt_engine_status").html('已关闭');
	            $("#div_rt_engine").attr('type', 0)
	        }else{
	            $("#lbl_rt_engine_status").html('已开启');
	            $("#div_rt_engine").attr('type', 1)
	        }
        },
        quick_oper_adg_back:function(result, stgy, adg_list){
            var oper_name = stgy==1? '加大投入': '减少投入';
            adg_list = $.evalJSON(adg_list);
            if (result) {
                PT.light_msg('操作成功', '宝贝'+oper_name+'成功');
                for (var i in adg_list) {
                    $('#'+adg_list[i]).attr('is_quick_opered', 1);
                }
            }else{
                PT.alert(oper_name + "失败，请刷新页面重新操作！");
            }
        },
        submit_cfg_back:function(budget, max_price){
            if(budget){
                $('div[type="budget"] .jq_price').text(budget).next('.unit').show();
            }
            if(max_price){
                $('div[type="max_price"] .jq_price').text(parseFloat(max_price).toFixed(2));
            }
        },
        update_camp_back:function(status){
            var optimize_time=$('#optimize_time').val();
            var mnt_oper_str = '',
                is_active = '',
                camp_online_status = '';
            if(status){
                mnt_oper_str="暂停";
                is_active='True';
                camp_online_status="系统自动优化中，上次优化时间："+optimize_time;
            }else{
                mnt_oper_str="启动";
                is_active='False';
                camp_online_status="推广计划已暂停，同时您已暂停托管";
            }
            $('#quick_oper_tip').attr('is_active',is_active);
            update_quick_oper_tip();
            $('#camp_mnt_oper').attr('mnt_oper',1-status).text(mnt_oper_str).toggleClass('green').toggleClass('red');
            $('#camp_online_status').text(camp_online_status);
        },
        close_redicet:function(campaign_id){
            window.location.href='/web/campaign/'+campaign_id;
        },
        set_bwords_back: function (result) {
            if (result==1) {
                $('#div_camp_blackword').modal('hide');
                $('#div_camp_blackword').modal('shadeOut');
                PT.light_msg('设置屏蔽词', '保存成功！');
            } else {
                PT.alert('保存失败，请联系顾问！');
            }
        }
    };

}();