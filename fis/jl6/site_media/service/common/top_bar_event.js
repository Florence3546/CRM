define(['require','common','char_link','main_poster_event', 'poster_store'],function(require,common,char_link,main_poster_event,store){

    //文字链广告
    char_link.init();

    var inited=false,
        initedAdg=false;

    var initEvent=function(){
        //如果今天没有获取过未读消息，则获取一次,否则则从缓存中取
        if(!store.hasGetUnRead()){
            startAnimation();
        }else{
            drawUnreadCount(parseInt(store.getUnreadCount()));
        }
    }
    
    function startAnimation(){
        var page_name = $('body').attr('id');
        if(page_name != 'top_logout'){
            common.sendAjax.ajax('get_unread_message_count',null,function(data){
                store.setUnreadCount(data.count);
                drawUnreadCount(parseInt(data.count));
            });
        }
    }

    var drawUnreadCount = function(count){
        $("#msg_count").text(count);
        if(parseInt(count) > 0){
            $("#msg_count").removeClass('hide');
        }
    }

    var baseMain=function(){

        //避免重复执行
        if(inited){
            return false;
        }

        inited=true;

        //意见反馈
        $('#suggest button').on('click',function(){

            //意见反馈提交到后台
            if($(this).data('is_lock')){
                return;
            }
            var that = this,
                suggest=$.trim($('#suggest').find('textarea').val()),
                phone=$.trim($('#suggest').find('input').val());

            if(suggest!=""){
                $(that).addClass('disabled').text('提交中...').data('is_lock', true);
                common.sendAjax.ajax('add_suggest',{suggest:suggest},function(data){
                    if (data.error_msg) {
                        common.lightMsg.show(data.error_msg);
                    }else{
                        common.lightMsg.show('感谢您的建议');
                        $('#suggest').parent().removeClass('active');
                        $('#suggest').find('textarea').val('');
                    }
                    $(that).data('is_lock', '');
                    $(that).removeClass('disabled').text('提交反馈');
                });

                if(/^1[3|4|5|7|8]\d{9}$/.test(phone)){
                    common.sendAjax.ajax('submit_userinfo',{phone:phone},function(){
                        $('#suggest').find('textarea').val('');
                    });
                }
            }else{
                common.lightMsg.show('请先填写您的宝贵建议');
            }
        });

        //切换风格
        var switchThemes = function(oldthemes,newthemes){
            var targetelement='link';
            var targetattr="href";
            var allsuspects=document.getElementsByTagName(targetelement)
            for (var i=allsuspects.length; i>=0; i--){
            if (allsuspects[i] && allsuspects[i].getAttribute(targetattr)!=null && allsuspects[i].getAttribute(targetattr).indexOf(oldthemes)!=-1)
               allsuspects[i].parentNode.removeChild(allsuspects[i])
            }

            var fileref=document.createElement("link")
                fileref.setAttribute("rel", "stylesheet")
                fileref.setAttribute("type", "text/css")
                fileref.setAttribute("href", "/site_media/jl6_temp/themes/"+newthemes+"/theme.css")
            if (typeof fileref!="undefined")
                document.getElementsByTagName("head")[0].appendChild(fileref);
            $('#top_logout').attr('href', '/router/logout/'+newthemes);
        }

        //同步数据
        $('#id_sync_data').on('click', function(){
            common.loading.show("正在同步数据，可能耗时较长");

            common.sendAjax.ajax(
                'sync_data', {}, function(data){
	                common.loading.hide();
	                if(data.msg!=undefined){
	                    common.alert.show(data.msg);
	                }
	            }, function(XMLHttpRequest, textStatus, errorThrown) {
	                common.loading.hide();
	                common.alert.show('获取服务器数据较慢，请耐心等待，或联系顾问');
	            }, {'timeout': 10*60*1000}
            )
        });

        //切换风格
        $('#account_setting .themes a').on('click', function() {

            var obj,
                theme;

            // day = 30 * 12 * 5;
            // exp = new Date();
            obj = $('link[href*="theme"]');
            theme = $(this).attr('class');

            // exp.setTime(exp.getTime() + day * 24 * 60 * 60 * 1000);
            // document.cookie = "theme=" + theme + ";path=/;expires="+exp.toGMTString();

            common.sendAjax.ajax('save_theme',{theme:theme},function(){
                var curthemes = $('#systhemes').val();
                //switchThemes(curthemes,theme);
                window.location.reload();
            });
        });

        //保存手机号和昵称
        $('#account_setting .btn-primary').on('click',function(){
            var remind,
                phone,
                nick;

            remind=$('#account_setting .switch').hasClass('on')?1:0;
            phone=$.trim($('#account_setting input[name=phone]').val());
            nick=$.trim($('#account_setting input[name=nick]').val());

            if(remind && (isNaN(phone) || !(/^1[3|4|5|7|8]\d{9}$/.test(phone)))){
                common.lightMsg.show("手机号码填写不正确！");
                return false;
            }

            common.sendAjax.ajax('submit_userinfo',{remind:remind,phone:phone,nick:nick},function(data){
                if(data.remind=="1"){
                    common.lightMsg.show('设置成功');
                }else{
                    common.lightMsg.show('已关闭短信提醒');
                }
            });

        });

        //我的消息
        $('#top_msg').on('click',function(){
            require(['../my_message/msg_dialog'],function(modal){
                modal.show()
            });
        });

        //完善会员信息
        $('#btn_save_info').on('click', function(){
            var phone = $.trim($('#txt_tel').val());
            var qq = $.trim($('#txt_qq').val());

            if(phone == ''){
                common.lightMsg.show("请输入手机号码。");
                return false;
            }else if(isNaN(phone) || !(/^1[3|4|5|7|8]\d{9}$/.test(phone))){
                common.lightMsg.show("手机号码填写不正确！");
                return false;
            }else if(isNaN(qq)){
                common.lightMsg.show("QQ号码填写不正确！");
                return false;
            }

            common.sendAjax.ajax('submit_userinfo',{phone:phone,qq:qq},function(data){
                if(data.errMsg == ''){
                    $('#top_user_info').slideUp(500);
                    common.lightMsg.show('恭喜，您的信息已经完善啦，感谢您的配合。');
                }else{
                    common.lightMsg.show(data.errMsg);
                }
            });
        });
        
        //完善会员信息(关闭)
        $('#close_user_info').on('click', function(){
            $('#top_user_info').fadeOut(500);
        });

        //显示用户信息
        $('#account_setting .switch').on('change',function(e,checked){
            if(checked){
                $('#user_info').removeClass('hidden');
            }else{
                $('#user_info').addClass('hidden');
            }
        });

        //服务中心 点击事件
        $("#site_nav").on('click','.server_menu',function(){
            main_poster_event.addViewTimes($(this).attr('value'));
        });

        //全店删词
        $('#duplicate_check_id').on('click',function(){

            common.sendAjax.ajax('to_duplicate_check',{},function(data){
                if(data.no_limit){
                    require(['jl6/site_media/service/upgrade_suggest/upgrade_suggest_modal'],function(upgradeModal){
                        upgradeModal.show('亲，很抱歉！您当前订购的版本没有使用该功能的权限，如果您想使用全店删词功能，就请升级吧！');
                    });
                    return false;
                }
                if(data.rpt_flag){
                    common.confirm.show({
                        body:'关键词报表尚未下载完，会影响系统推荐的删词级别，现在就下载报表并排重吗？',
                        okHidden:function(){
//                            common.loading.show('正在下载关键词报表，请稍候...');
                            window.location.href = "/web/duplicate_check";
                        }
                    });
                }else{
                    window.location.href = "/web/duplicate_check";
                }
            });
        });

        // 店铺预约诊断点击a_WW，发送邮件，添加提醒
        $('#order_shop_check').click(function(){
             common.sendAjax.ajax('order_shop_check',{},function(data){});
        });
    }

    var adgMain=function(){

        //避免重复执行
        if(initedAdg){
            return false;
        }

        initedAdg=true;

        $(document).on('scroll',function(){
            var body_offset = document.body.scrollTop | document.documentElement.scrollTop;
            if(body_offset<98){
                $('#main_content>header').css('marginTop',-body_offset)
            }else{
                $('#main_content>header').css('marginTop',-9999);
            }
        });

        $(document).trigger('scroll');
    }

    return {
        init:initEvent,
        baseMain:baseMain,
        adgMain:adgMain
    }
});
