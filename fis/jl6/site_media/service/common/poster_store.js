/**
 * Created by Administrator on 2015/9/17.
 */
define(['store'],function(store){

    var getStoreAd = function(id,ad_frequency){
        var local_ad = store.get(id);
        //如果广告已浏览过，根据显示频率及上次显示时间，判断广告在此次是否需要加载
        if(local_ad&&ad_frequency=='2'){
            var last_show_time = new Date(local_ad.last_show_time);
            var now_time = new Date();
            //如果广告频率为每天一次，并且上次显示日期与当前日期相同时，则不显示
            if(last_show_time.getYear()==now_time.getYear()&&
               last_show_time.getMonth()==now_time.getMonth()&&
               last_show_time.getDay()==now_time.getDay()){
               return true;
            }
        }
        return false;
    }

    var setStoreAd = function(id,data){
        store.set(id,data);
    };

    var hasGetUnRead = function(){
        var unReadTime = store.get('unReadTime');
        var now_time = new Date();
        if(unReadTime){
            unReadTime = new Date(unReadTime);
            if(unReadTime.getYear()==now_time.getYear()
                &&unReadTime.getMonth()==now_time.getMonth()
                &&unReadTime.getDay()==now_time.getDay()){
                return true;
            }
        }
        store.set('unReadTime', new Date());
        return false;
    };

    var setUnreadCount = function(count){
        store.set('unReadCount', count);
    };

    var getUnreadCount = function(){
        return store.get('unReadCount');
    };

    return {
        getStoreAd:getStoreAd,
        setStoreAd:setStoreAd,
        hasGetUnRead:hasGetUnRead,
        setUnreadCount:setUnreadCount,
        getUnreadCount:getUnreadCount
    }
});