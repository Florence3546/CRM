/**
 * Created by tianxiaohe on 2015/9/16.
 */
define(function() {
    "use strict"

    var init=function(){
        var main_ad_event;
        var ad_id = $('#chart_link_ad').attr('ad_id');//文字链广告id
        var bottom_ad_id = $('#show_bottom_banner').attr('ad_id');//底部横条广告id
        //如果有文字链广告或底部横条，则需将广告浏览次数加1
        if(ad_id||bottom_ad_id){
            main_ad_event = require('main_poster_event');
            if(ad_id){
                main_ad_event.addViewTimes(ad_id);
            }
            if(bottom_ad_id){
                main_ad_event.addViewTimes(bottom_ad_id);
            }
        }
        //点击文字链广告
        $('#chart_link_ad').click(function(){

            //如果广告没有链接，则显示窗口内容
            if($(this).attr('href')=='javascript:;'){
                $('.bg_layer').fadeIn(200);
                $('#show_chart_link_view').fadeIn(500);
                var height = $('#chart_link_content').height();
                var width = $('#chart_link_content').width();
                $("#show_chart_link_view").css('margin-left',-width/2+"px").css("margin-top",-height/2+"px");
            }

            //点击后添加点击次数
            main_ad_event.addClickTimes(ad_id);

            $('#hide_chart_link_view').on('click',function(){
                $('.bg_layer').fadeOut(500);
                $('#show_chart_link_view').fadeOut(200);
            });
        });

        //点击底部横条广告，则要将该广告的点击事件加1
        $('#bottom_banner_content').click(function(){
            main_ad_event.addClickTimes(bottom_ad_id);
        });
    }

    return {
        init:function(){
            init();
        }
    }
});
