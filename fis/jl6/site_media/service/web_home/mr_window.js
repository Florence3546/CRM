define(['../common/poster_store'],function(ad_store) {
    "use strict"
    var init=function(){
        var main_ad_event;
        var ad_id = $('#mr_window_content').attr('ad_id');
        var ad_frequency = $('#show_mr_window').attr('ad_frequency');
        var shop_id = $('#shop_id').val();
        var store_id = ad_id+'_'+shop_id;

        //判断该广告是否需要显示
        if(ad_store.getStoreAd(store_id,ad_frequency)){
            return false;
        }

        if(ad_id){
            main_ad_event = require('../common/main_poster_event');
            if($('#show_mr_window').attr('ad_close_btn')){
                $("#hide_mr_window").show();
            }else{
                $("#hide_mr_window").hide();
            }

            var height = $('#show_mr_window').height();
            $('#show_mr_window').css('bottom',(0-height)+'px');
            $("#show_mr_window").show();

            //延迟N秒后显示广告
            setTimeout(showMrWindow,parseInt($('#show_mr_window').attr('ad_delay_secs'))*1000);

            //点击广告后需要将广告的浏览次数加1
            $("#mr_window_content").click(function(){
                main_ad_event.addClickTimes(ad_id);
            });
        }

        //显示右下广告
        function showMrWindow(){
            $("#show_mr_window").animate({bottom:0},1000,function(){
                var ad_show_secs = $('#show_mr_window').attr('ad_show_secs');
                setTimeout('javascript:$("#show_mr_window").animate({height:0},1000,function(){' +
                    '$("#show_mr_window").remove();});',parseInt(ad_show_secs)*1000);
            });

            //广告显示后需要将广告的浏览次数加1
            main_ad_event.addViewTimes(ad_id);

            //广告显示后，存在前端，下次刷新页面是调用
            var mr_window_ad = {'ad_frequency':$('#show_mr_window').attr('ad_frequency'),'last_show_time':new Date()};
            ad_store.setStoreAd(store_id,mr_window_ad);
        }

        //点击关闭按钮后关闭广告
        $('#show_mr_window').on('click','#hide_mr_window',function(){
            $("#show_mr_window").animate({bottom:0-height},1000,function(){
                $("#show_mr_window").remove();
            });
        });
    }

    return {
        init:function(){
            init();
        }
    }
});
