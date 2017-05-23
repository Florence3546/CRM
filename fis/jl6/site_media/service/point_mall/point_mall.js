define(['require', 'widget/confirm/confirm', 'widget/alert/alert', 'widget/ajax/ajax', 'widget/loading/loading'], function(require, confirm, alert, ajax,loading) {

    var init = function() {
    
        var ticket_callback = function( obj ){
            var gift_id = obj.attr('data-type');
            var url = $("#exurl").val();
            window.location.href =  url+"?present_id="+gift_id;
        };
        
        //虚拟物品兑换
        var virtual_callback = function( obj ){
            var gift_id = obj.attr('data-type');
            confirm.show({
                body: '您确定要兑换吗？',
                okHidden: function() {
                    ajax.ajax('convert_virtual', {
                        gift_id: gift_id
                    }, function(data) {
                        loading.hide();
                        if( data.remind.length > 0 ){
                            alert.show(data.remind);                        
                        } else {
                            alert.show({
                               body:"亲！您的兑换申请我们已经收到，会尽快安排顾问与您联系，感谢您的支持！",
                               hidden:function(){
                                   location.reload();
                               }
                            });
                        }
                    });
                }
            });
        };
        
        //实物兑换
        var gift_callback = function( obj ){
            var is_perfect_info=$('#is_perfect_info').val();
            var gift_id=obj.attr('data-type');

            require(['../complete_user_info/complete_user_info'],function(modal){
                modal.show({
                    type:'exchange',
                    callBack:function(){
                        convert_gift(gift_id);
                    }
                })
            });
        };
        
        $(".exchange").click(function(){
            var obj = $(this);
            var et = obj.attr("et");
            var present_id=obj.attr('data-type');
            try{
                var func = eval(et+"_callback")
                if(typeof func == 'function'){
                    ajax.ajax('check_exchange_condition', {
                        present_id: present_id
                    }, function(data) {
                        if(data.result){
                            func(obj);
                        } else {
                            alert.show("亲，您的积分不够，无法兑换哦，请联系您的精灵顾问吧！   "+'<a href="aliim:sendmsg?uid=cntaobao&amp;siteid=cntaobao&amp;touid=cntaobao派生科技"><img class="marl_6" src="/site_media/jl/img/online.ww.gif"></a>');                        
                        }
                    });
                } else {
                    console.log("func is not exists.")
                }
            } catch (e){
                console.log("et error!")
            }
        });
        
    };

    var convert_gift=function(gift_id){
        loading.show('正在申请');
        ajax.ajax('convert_gift', {
            gift_id: gift_id
        }, function(data) {
            loading.hide();
            if( data.remind.length > 0 ){
                alert.show(data.remind);                        
            } else {
                alert.show({
                               body:"亲！您的兑换申请我们已经收到，会尽快安排为您发货。请在积分明细中查看，物流单号",
                               hidden:function(){
                                   location.reload();
                               }
                            });
            }
        });
    };

    return {
        init: init
    }
});
