/**
 * Created by Administrator on 2015/9/17.
 */
define(['jl6/site_media/widget/ajax/ajax'],function(ajax){

    //广告预览次数加1
    var addViewTimes = function(ad_id){
        ajax.ajax('add_show_times',{'ad_id':ad_id},ajax_call_back);
    };

    //广告点击次数加1
    var addClickTimes = function(ad_id){
        ajax.ajax('add_click_times',{'ad_id':ad_id},ajax_call_back);
    };

    var ajax_call_back = function(data){
    }

    return {
        addViewTimes:addViewTimes,
        addClickTimes:addClickTimes
    }
});