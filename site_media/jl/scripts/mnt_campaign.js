PT.namespace('MntCampaign');
PT.MntCampaign = function () {
    var camp_id = $('#campaign_id').val(),
        mnt_index=parseInt($('#mnt_index').val()),
        mnt_type=parseInt($('#mnt_type').val());

    if(mnt_type==1){
        var camp_budget_min=50, camp_budget_max=200;
    }else{
        var camp_budget_min=100, camp_budget_max=5000;
    }

    var init_record_table=function(){
        var record_table=$('#record_table').dataTable({
            "bRetrieve": true, //允许重新初始化表格
            "bPaginate": true,
            "bFilter": true,
            "bInfo": true,
            "aaSorting": [[1,'desc']],
            "bAutoWidth":false,//禁止自动计算宽度
            "iDisplayLength": 100,
            "sDom":"<'row-fluid't<'row-fluid marb_24'<'span6'i><'span6'p>>",
            "aoColumns": [
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true},
                {"bSortable": true}
            ],
            "oLanguage": {
                    "sProcessing" : "正在获取数据，请稍候...",
                    "sInfo":"正在显示第_START_-_END_条信息，共_TOTAL_条信息 ",
                    "sZeroRecords" : "没有您要搜索的内容",
                    "sEmptyTable":"没有数据",
                    "sInfoEmpty": "显示0条记录",
                    "sInfoFiltered" : "(全部记录数 _MAX_ 条)",
                    "oPaginate": {
                            "sFirst" : "第一页",
                            "sPrevious": "上一页",
                            "sNext": "下一页",
                            "sLast" : "最后一页"
                    }
            }
        });
    }

    var init_dom=function(){

        $('#id_budget').attr('data-original-title','建议将日限额设在'+camp_budget_min+'~'+camp_budget_max+'元之间');

        $('#id_close_mnt').click(function(){
            $.fancybox.open([{href:'#id_close_confirm'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});
        });

        $('#id_close_btn').click(function(){
            PT.sendDajax({'function':'mnt_mnt_campaign_setter','campaign_id':camp_id,'set_flag':0,'mnt_type':mnt_type});
        });

        $('.edit_price').click(function(){
            $(this).prev().attr('disabled',false).removeClass('text_input');
            $(this).fadeOut('fast',function(){
                $(this).next().fadeIn('fast');
            });
        });
        $('.cancel_price').click(function(){
            var jq_span=$(this).parent(),
                type_id=$(this).next().attr('id'),
                old_price=Number(jq_span.parent().find('input[type=hidden]').val());
            if (type_id=='submit_max_price') {
                old_price=old_price.toFixed(2);
            }
            jq_span.prev().prev().blur();
            jq_span.prev().prev().val(old_price).addClass('text_input').attr('disabled',true);
            jq_span.fadeOut('fast',function(){
                jq_span.prev().fadeIn('fast');
            });
        });
        $('#submit_max_price').click(function(){
            var max_price= $.trim($('#id_max_price').val()), submit_dict = {};
            if(max_price==$('#max_price_bak').val()){
                $('#max_price_bak').nextAll().find('.cancel_price').click();
                return;
            }
            if(max_price==''||isNaN(max_price)){
                $("#id_max_price").focus();
                PT.alert('关键词最高限价必须是数字！');
            }else if (Number(max_price)<0.2||Number(max_price)>5.00){
                PT.alert('关键词最高限价必须介于0.20~5.00元之间！');
            }else{
                submit_dict['max_price'] = max_price;
                update_cfg(submit_dict);
            }

        });
        $('#submit_budget').click(function(){
            var budget= $.trim($('#id_budget').val());
            if(budget == $('#budget_bak').val()){
                $('#budget_bak').nextAll().find('.cancel_price').click();
                return;
            }
            var submit_dict={'budget':budget};
            if(budget == ''){
                PT.alert('请输入日限额！');
            }else if (isNaN(budget) || /^[1-9]\d*$/.test(budget)==false){
                PT.alert('日限额必须是有效整数！');
            }else if (parseInt(budget,10) < camp_budget_min){
                PT.alert('日限额最少'+camp_budget_min+'元！');
            }else if (parseInt(budget,10) > camp_budget_max){
                var tip="日限额超过<span class='r_color'>"+camp_budget_max+"</span>元！可能导致<span class='r_color'>花费较高</span>！您确认将日限额设为<span class='r_color'>"+Number(budget)+"</span>元吗？";
                PT.confirm(tip,update_cfg,[submit_dict]);
            }else{
                update_cfg(submit_dict);
            }
        });

        $('.quick_oper').click(function(){
            if($(this).hasClass('disabled')){
                return;
            }
            var stgy=parseInt($(this).attr('stgy'));
            msg="系统会定期自动改价换词，您确定现在就要人工干预吗？";
            PT.confirm(msg,quick_oper,[stgy]);
        });

        $('#camp_mnt_oper').click(function(){
            var mnt_oper=parseInt($(this).attr('mnt_oper')),
                msg=(mnt_oper?'即将启动自动优化，同时将计划设置为参与推广，确认启动吗？':'即将暂停自动优化，同时将计划设置为暂停推广，确认暂停吗？');
            PT.confirm(msg,update_camp_status,[mnt_oper]);
        });

        $('#li_opt_record').click(function(){
            if($(this).attr('switch')==0){
                PT.show_loading('正在获取操作记录');
                PT.sendDajax({'function':'mnt_get_opt_record','campaign_id':camp_id,'mnt_type':mnt_type});
                $(this).attr('switch',1);
            }
        });

        $('#li_msg_record').click(function(){
            if($(this).attr('switch')==0){
                PT.show_loading('正在获取顾问留言');
                PT.sendDajax({'function':'web_get_sigle_comment','obj_id':camp_id,'obj_type':1,'name_space':'MntCampaign'});
                $(this).attr('switch',1);
            }
        });
    }

    var update_cfg=function(submit_dict){
        if (submit_dict['budget']) {
            $('#submit_budget').parent().fadeOut('fast');
        }
        if (submit_dict['max_price']) {
            $('#submit_max_price').parent().fadeOut('fast');
        }
        PT.sendDajax({'function':'mnt_update_cfg','campaign_id':camp_id,'submit_data':$.toJSON(submit_dict),'mnt_type':mnt_type});
    }

    var quick_oper = function(stgy){
        switch (stgy) {
            case 1:
                $('.quick_oper:eq(0) img').show();
                break;
            case -1:
                $('.quick_oper:eq(1) img').show();
                break;
        }
        $('#quick_oper_tip').attr('is_recent','True');
        update_quick_oper_tip();
        PT.sendDajax({'function':'mnt_quick_oper', 'campaign_id':camp_id, 'mnt_type':mnt_type, 'stgy':stgy});
    }

    var update_camp_status = function(mnt_oper){
        PT.sendDajax({'function':'mnt_update_prop_status','campaign_id':camp_id,'status':mnt_oper,'mnt_type':mnt_type});
    }

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
    }

    return {
        init:function(){
            PT.show_loading('正在获取数据');
            PT.Base.set_nav_activ(1,mnt_index-1);
            init_dom();
            update_quick_oper_tip();
            PT.sendDajax({'function':'mnt_get_mnt_campaign','rpt_days':1,'campaign_id':camp_id,'auto_hide':0});
        },
        select_call_back: function(value){
            PT.show_loading('正在获取数据');
            PT.sendDajax({'function':'mnt_get_mnt_campaign','rpt_days':value,'campaign_id':camp_id,'auto_hide':0});
            PT.MntAdg.select_call_back(value);
        },
        get_campaign_back:function(data){
            $('#camp_sum_rpt_table').find('tbody').html(template.render('camp_sum_rpt_tr', data));
            App.initTooltips();
        },
        opt_record_back:function(data){
            PT.hide_loading();
            $('#record_table').find('tbody').html(template.render('opt_record_tbody', {data:data}));
            init_record_table();
        },
        get_sigle_comment_back:function(result){
            PT.hide_loading();
            var dom=template.render('template_single_comment',{'msg_list':result.msg_list});
            $('#msg_record').html(dom);
        },
        quick_oper_back:function(result, stgy){
            var oper_name = '';
            switch (stgy) {
                case 1:
                    oper_name = $.trim($('.quick_oper:eq(0)').text());
                    break;
                case -1:
                    oper_name = $.trim($('.quick_oper:eq(1)').text());
                    break;
            }
            $('.quick_oper img').hide();
            if(result){
//              $('#quick_oper_tip').attr('is_recent','True');
//              update_quick_oper_tip();
                PT.light_msg(oper_name + '成功','正在执行智能改价,24小时后您可以再次对计划进行调整！');
            }
            else{
                $('#quick_oper_tip').attr('is_recent','False');
                update_quick_oper_tip();
                PT.alert(oper_name + "失败，请刷新页面重新操作！");
            }
        },
        submit_cfg_back:function(budget, max_price){
            if(budget){
                $('#budget_bak').val(budget).nextAll().find('.cancel_price').click();
            }
            if(max_price){
                $('#max_price_bak').val(max_price).nextAll().find('.cancel_price').click();
            }
            PT.light_msg('修改成功','设置会在系统下次优化时生效！');
        },
        update_camp_back:function(status){
            var optimize_time=$('#optimize_time').val();
            if(status){
                var mnt_oper_str="暂停", is_active='True',
                    camp_online_status="系统自动优化中，上次优化时间："+optimize_time;
            }else{
                var mnt_oper_str="启动", is_active='False',
                    camp_online_status="推广计划已暂停，同时您已暂停托管";
            }
            $('#quick_oper_tip').attr('is_active',is_active);
            update_quick_oper_tip();
            $('#camp_mnt_oper').attr('mnt_oper',1-status).text(mnt_oper_str).toggleClass('green').toggleClass('red');
            $('#camp_online_status').text(camp_online_status);
        },
        close_redicet:function(campaign_id){
            window.location.href='/web/adgroup_list/'+campaign_id;
        }
    };

}();
