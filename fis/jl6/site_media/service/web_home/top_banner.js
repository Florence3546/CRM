define(['../common/poster_store'],function(ad_store) {
    "use strict"
    var init=function(){

        var main_ad_event;
        var ad_id = $('#show_top_banner').attr('ad_id');
        var ad_frequency = $('#show_top_banner').attr('ad_frequency');

        var shop_id = $('#shop_id').val();
        var store_id = ad_id+'_'+shop_id;

        //判断该广告是否需要显示
        if(ad_store.getStoreAd(store_id,ad_frequency)){
            return false;
        }

        main_ad_event = require('../common/main_poster_event');
        if($('#show_top_banner').attr('ad_close_btn')){
            $("#hide_top_banner").show();
        }else{
            $("#hide_top_banner").hide();
        }

        $('#show_top_banner').on('click','#hide_top_banner',function(){
            $("#show_top_banner").animate({height:0},1000,function(){
                $("#show_top_banner").remove();
            });
        });

        //广告点击后，修改广告点击次数
        $('#top_banner_content').click(function(){
            main_ad_event.addClickTimes(ad_id);
        });

        //显示首页横条广告
        function showTopBanner(){
            var height = $('#top_banner_content').height();
            $('html, body').animate({scrollTop:0}, 50,function(){
                $("#show_top_banner").animate({height:height},1500,function(){
                    var ad_show_secs = $('#show_top_banner').attr('ad_show_secs');
                    setTimeout('javascript:$("#show_top_banner").animate({height:0},1500,function(){' +
                        '$("#show_top_banner").remove();});',parseInt(ad_show_secs)*1000);
                });
            });

            //广告显示后，修改浏览次数
            main_ad_event.addViewTimes(ad_id);

            //广告显示后，存在前端，下次刷新页面是调用
            var top_banner_ad = {'ad_frequency':$('#show_top_banner').attr('ad_frequency'),'last_show_time':new Date()};
            ad_store.setStoreAd(store_id,top_banner_ad);
        }

        if($("#show_top_banner")){
            setTimeout(showTopBanner,parseInt($('#show_top_banner').attr('ad_delay_secs'))*1000);
        }
    }

    return {
        init:function(){
            init();
        }
    }
});
