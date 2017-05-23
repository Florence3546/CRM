/**
 * Created by Administrator on 2015/9/17.
 */
define(['../common/poster_store'],function(ad_store){
    var init = function(){

        var main_ad_event;
        var ad_id = $("#mc_window_content").attr('ad_id');
        var ad_frequency = $('#show_mc_window').attr('ad_frequency');
        var shop_id = $('#shop_id').val();
        var store_id = ad_id+'_'+shop_id;

        //判断该广告是否需要显示
        if(ad_store.getStoreAd(store_id,ad_frequency)){
            return false;
        }

        //当有中间弹窗广告时，才执行一下方法
        if(ad_id){
            main_ad_event = require('../common/main_poster_event');
            var height = $('#show_mc_window').height();
            var width = $('#show_mc_window').width();
            $("#show_mc_window").css('margin-left',-width/2+"px").css("margin-top",-height+"px");
            $('.bg_layer').fadeIn(200);
            $("#show_mc_window").show();
            $("#show_mc_window").animate({'margin-left':-width/2,'margin-top':-height/2,'top':'50%'},500);

            //显示广告后，需要将广告浏览次数加1
            main_ad_event.addViewTimes(ad_id);

            //广告显示后，存在前端，下次刷新页面是调用
            var mc_window_ad = {'ad_frequency':$('#show_mc_window').attr('ad_frequency'),'last_show_time':new Date()};
            ad_store.setStoreAd(store_id,mc_window_ad);

            //点击广告后需要将广告的点击次数加1
            $('#mc_window_content').click(function(){
                main_ad_event.addClickTimes(ad_id);
            });

            $('#show_mc_window').on('click','#hide_mc_window',function(){
                $('.bg_layer').fadeOut(500);
                $("#show_mc_window").fadeOut(200);
            });
        }
    };

    return {
        init :function(){
            init();
        }
    }
})