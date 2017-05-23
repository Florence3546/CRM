PT.namespace('Home');
PT.Home = function () {

    //第一次进入时，发送请求当天时实的数据
    var send_date=function(){
        PT.show_loading('正在获取数据');        
        last_day = $('.cust_last_day').attr('value');
		PT.sendDajax({'function':'web_get_account','last_day':last_day});
    };

    var init_detailed_table=function(){
        var detailed_table=$('#detailed_table').dataTable({
            "bPaginate": false,
            "bFilter": false,
            "bInfo": false,
            "aaSorting":[[0,'desc']],
            "sDom":"",
            "oLanguage": {
                "sZeroRecords": "亲，没有最近15天的店铺数据！",
                "sInfoEmpty": "亲，没有最近15天的店铺数据！"
                },
            "aoColumns":[null, null, null, null, null, null,
                                    {"sSortDataType":"td-text", "sType":"numeric"},
                                    {"sSortDataType":"td-text", "sType":"numeric"},
                                    {"sSortDataType":"td-text", "sType":"numeric"},
                                    null, null]
        });
    };

    var init_dom=function() {

        $('#btn_recharge').click(function(){
            PT.Base.goto_ztc(6,'','','');
        });

        $('#account_select_days').on('change',function(e,value){
        	PT.show_loading('正在获取数据');
            PT.sendDajax({'function':'web_get_account','last_day':value});
        });

        $('.commom_msg_link').on('click',function(){
            var msgid=$(this).data().msgid;
            PT.sendDajax({'function':'web_get_common_msg','msgid':msgid});
        });
        
        $("#common_message li").on('click',function(){
        	split_str = $('a',this).attr('href').split('_');
        	msg_num = split_str[split_str.length-1];
        	msg_id = '#title_common_' + msg_num;
        	$(msg_id + " i").attr('class','mr5 iconfont normally  silver');
        	PT.sendDajax({'function':'web_close_msg','msg_id':msg_num,"is_common":1});
        });


        //填写精灵币推荐人
        // $(document).on('click', '#modal_referer .close_modal_referer', function() {
        //     var jq_modal = $('#modal_referer'),
        //         jq_target = $('#point_info');
        //     move_effect(jq_modal, jq_target);

        // });

        // $(document).on('click','#receive_recount_home',function(){
        //     var user_name = $('#input_referrer').val().replace(/^\s+|\s+$/g,"");
        //     if (user_name){
        //         $('#error_msg').hide();
        //         $('#loading_tips').fadeIn();
        //         PT.sendDajax({'function':'web_receive_recount','nick':user_name,'namespace':'Home'});
        //     }else{
        //         // $('#error_msg').text('请先输入推荐人的店铺主旺旺').fadeIn();
        //         // $('#input_referrer').focus();
        //         PT.alert('请先输入推荐人的店铺主旺旺');
        //     }
        // });
        //填写精灵币推荐人

        //初始化tooltip
        $('.tips').tooltip({
          html: true
        });

        //修正公告信息高度
        !function(){
            var obj_h=$('#main_info>li:eq(1)').height();
            if(obj_h>80){
                $('#common_message_window').css('height',337-obj_h);
            }
        }();

        $('#common_message_window').OverflowScroll();

        $(document).on('click', '.click_lottery_url', function() {
            var source = $(this).data('source');
            PT.sendDajax({'function': 'web_record_lottery_click', 'source': source, 'auto_hide':0 });
        });

        //签到送积分
        $('#sign_point').on('click',function(){
            if ($('#sign_point').hasClass('disabled')) {
                PT.light_msg('精灵提示','今天已经签过了，明天再来吧！');
                return false;
            }

            $('#sign_point').addClass('disabled');

            PT.sendDajax({
                'function': 'web_sign_point',
                'callback': 'PT.Home.sign_point_callback'
            });
        });

        //提示软件即将到期
        // !function(){
        //     var left_days=Number($('#left_days').val()),point_count=Number($('#point_count').val()),freeze_point_deadline=$('#freeze_point_deadline').val();
        //     if (left_days<=15 && point_count>0){
        //         setTimeout(function(){
        //             if(freeze_point_deadline==''){
        //                 tips='软件即将过期，您还有积分没有使用&emsp;<a href="/web/point_mall/" target="_blank">立即使用</a>&emsp;<a class="freeze_point" href="javascript:;">[保留积分，过期后再订]</a>'
        //             }else{
        //                 tips='软件即将过期，您还有积分没有使用&emsp;<a href="/web/point_mall/" target="_blank">立即使用</a>'
        //             }
        //             PT.show_top_info(tips);
        //         },1000);
        //     }
        // }();

        //软件弹窗
        ! function() {
            var popup_config=$.parseJSON($('#popup_config').val());

           if(!popup_config){
            return false;
           }

            var ls_data={},
                ls_data1={},
                key = 'popup' + popup_config.id,
                key1='popup_show_again_' + popup_config.id;

            var show_modal=function(){

                if (PT.get_habit() && PT.get_habit()[key1] != undefined) { //用户手动开启不再显示
                    return;
                }

                if (popup_config.level == 'everyday') { //如果是每天显示一次
                    if (PT.get_habit() && PT.get_habit()[key] != undefined && new Date().format('yyyy-MM-dd') <= PT.get_habit()[key]) {
                        return;
                    } else {
                        ls_data[key] = new Date().format('yyyy-MM-dd');
                        PT.set_habit(ls_data);
                    }
                } else {
                    ls_data[key] = undefined;
                    PT.set_habit(ls_data);
                }

                $('#popup .modal').modal();
            }

            //简单模式
            if(popup_config.content_model=='simple'){
                if ($('#popup').length) {
                    var src, obj;
                    obj = new Image();
                    obj.src = $('#popup_img_url>img').attr('data-src');

                    if (typeof(obj.onreadystatechange) == "undefined") {
                        obj.onload = function() {
                            if (obj.complete == true) {
                                $('#popup_img_url>img').attr('src', obj.src);
                                show_modal();
                            }
                        }
                    } else {
                        if (obj.complete) { //解决IE8直接在地址栏按确定，导致的不加载图片的问题
                            window.location.reload();
                        }
                        obj.onreadystatechange = function() {
                            $('#popup_img_url>img').attr('src', obj.src);
                            show_modal();
                        }
                    }
                }
            }

            //高级模式
            if(popup_config.content_model=='senior'){
                show_modal();
            }

            if($('#popup .show_again').length){
                $('#popup .show_again input').on('change',function(){
                    if(this.checked){
                        ls_data1[key1]=1;
                    }else{
                        ls_data1[key1]=undefined;
                    }
                    PT.set_habit(ls_data1);
                });
            }
        }();

        //顶部通栏消息
        !function(){
           var top_bar_config=$.parseJSON($('#top_bar_config').val());

           if(!top_bar_config){
            return false;
           }

            var html='<div>' + $('#top_bar').html().replace("<p>", "").replace("</p>", ""),
                ls_data={},
                ls_data1={},
                key = 'top_bar' + top_bar_config.id,
                key1='top_bar_show_again_' + top_bar_config.id;

            var show_top_bar=function(){
            
                if (PT.get_habit() && PT.get_habit()[key1] != undefined) { //用户手动开启不再显示
                    return;
                }

                if (top_bar_config.level == 'everyday') { //如果是每天显示一次
                    if (PT.get_habit() && PT.get_habit()[key] != undefined && new Date().format('yyyy-MM-dd') <= PT.get_habit()[key]) {
                        return;
                    } else {
                        ls_data[key] = new Date().format('yyyy-MM-dd');
                        PT.set_habit(ls_data);
                    }
                } else {
                    ls_data[key] = undefined;
                    PT.set_habit(ls_data);
                }

				html = html.replace(new RegExp('<p>','gm'),'').replace(new RegExp('</p>','gm'),'').replace(new RegExp('%3A;','gm'),':;')
				
                html+='<div class="r mr10">';
                
                if(top_bar_config.show_again=="1"){
                    html+='<input class="vn" type="checkbox"><span>不再提示</span>';
                }
                
                html+='<a class="ml10" data-dismiss="top_info" href="javascript:;">[关闭]</a></div></div>';

                setTimeout(function(){
                    PT.show_top_info(html);
                },1000);
            }

            //只在高级模式显示
            if(top_bar_config.content_model=='senior'){
                show_top_bar();
            }

            if($('#top_info .again').length){
                $('#top_info .again input').on('change',function(){
                    if(this.checked){
                        ls_data1[key1]=1;
                    }else{
                        ls_data1[key1]=undefined;
                    }
                    PT.set_habit(ls_data1);
                });
            }

        }();

        //主区通告
        !function(){
           var main_tip_config=$.parseJSON($('#main_tip_config').val());

           if(!main_tip_config){
            return false;
           }

            var html=$('#main_info').html(),
                ls_data={},
                ls_data1={},
                key = 'main_info' + main_tip_config.id,
                key1='main_info_show_again_' + main_tip_config.id;

            var show_main_info=function(){

                if (PT.get_habit() && PT.get_habit()[key1] != undefined) { //用户手动开启不再显示
                    return;
                }

                if (main_tip_config.level == 'everyday') { //如果是每天显示一次
                    if (PT.get_habit() && PT.get_habit()[key] != undefined && new Date().format('yyyy-MM-dd') <= PT.get_habit()[key]) {
                        return;
                    } else {
                        ls_data[key] = new Date().format('yyyy-MM-dd');
                        PT.set_habit(ls_data);
                    }
                } else {
                    ls_data[key] = undefined;
                    PT.set_habit(ls_data);
                }

                html+='<div class="r mr10 gray">';

                if(main_tip_config.show_again=="1"){
                    html+='<span class="again"><input class="vn" type="checkbox"></span><span>不再提示</span>';
                }

                html+='<a class="ml10" data-dismiss="top_info" href="javascript:;">关闭</a></div>';

                $('#main_tip').removeClass('hide');
            }

            //只在高级模式显示
            if(main_tip_config.content_model=='senior'){
                show_main_info();
            }

            if($('#top_info .again').length){
                $('#top_info .again input').on('change',function(){
                    if(this.checked){
                        ls_data1[key1]=1;
                    }else{
                        ls_data1[key1]=undefined;
                    }
                    PT.set_habit(ls_data1);
                });
            }

        }();
    };

    // var move_effect = function (jq_modal, jq_target) {
    //     var now_left = jq_modal.offset()['left'],
    //         now_top = jq_modal.offset()['top']-4,
    //         offset_left = jq_target.offset()['left']+$('#modal_referer').width()/2,
    //         offset_top = jq_target.offset()['top']+$('#modal_referer').height()/2,
    //         width = jq_target.width(),
    //         height = jq_target.height();

    //     //jq_modal.css({'marginTop':0,'marginLeft':0,'top':now_top,'left':now_left,'overflow':'hidden'});
    //     jq_modal.animate({'height':height, 'width':width, 'top':offset_top, 'left':offset_left, 'opacity':0},300,function(){

    //     jq_modal.modal('hide');
    //     });
    //     //jq_target.find('a').pulsate({color: "#FF0000",repeat: 3});
    // };

    var init_right_down_ad = function(){
        // if(PT.get_habit()&&PT.get_habit()['right_down_ad']!='undefined'&&new Date().format('yyyy-MM-dd')<=PT.get_habit()['right_down_ad']){
        //     return;
        // }
        PT.sendDajax({'function': 'web_right_down_ad','call_back':'PT.Home.right_down_ad_call_back'});
    }
      
    return {

        init: function () {
            send_date();
            init_dom();
            init_detailed_table();
            init_right_down_ad();
            // init_help();
        },
        select_call_back: function(value){
            PT.sendDajax({'function':'web_get_account','last_day':value});
        },
        append_account_data: function(data){
        	PT.hide_loading();
            var table_dom = template.compile(pt_tpm['sum_report.tpm.html'])(data[0]);
            $('#sum_rpt').html(table_dom);
            $('.tips').tooltip({html: true});
        },
        receive_recount_back:function(result){
            if (result.error_msg) {
                $('#loading_tips').hide();
                //$('#error_msg').text(result.error_msg).fadeIn();
                PT.alert(result.error_msg);
            }else{
                $('#modal_referer').modal('hide');
                var msg="恭喜您获得精灵赠送的<span class='r_color'>"+result.point_1+"</span>个精灵币";
                PT.alert(msg);
            }
        },
        right_down_ad_call_back:function(result){
            var config;
            config={
                'body':result.html,
                'dealy': parseInt(result.config.dealy),
                'during': parseInt(result.config.during),
                'size': result.config.size,
                'autoclose':result.config.autoclose
            }

            if(result.times=='everyday'){ //如果是每天显示一次
                if(PT.get_habit()&&PT.get_habit()['right_down_ad']!='undefined'&&new Date().format('yyyy-MM-dd')<=PT.get_habit()['right_down_ad']){
                    return;
                }else{
                    PT.set_habit({'right_down_ad':new Date().format('yyyy-MM-dd')});
                }
            }else{
                 PT.set_habit({'right_down_ad':undefined});
            }

            new RightDownAd(config);
        },
        sign_point_callback:function(data){
            if(data.msg!=''){
                 alert(data.msg);
            }else{
                $('.point_count').each(function(){
                    var point=Number($(this).text());
                    $(this).text(point+data.data.point);
                });
                $('#sign_point>span').text('已签到');
                $('#get_attendance_day').text(data.data.attendance_day);
                PT.light_msg('签到成功','赠送积分'+data.data.point+',连续签到'+data.data.attendance_day+'天');
            }
        }

    };

}();

PT.namespace('vipHome');
PT.vipHome.submit_userinfo_back=function(){
    $('#info_modal_dialog').modal('hide');
    PT.alert('提交成功，感谢您的信任和支持！');
};
