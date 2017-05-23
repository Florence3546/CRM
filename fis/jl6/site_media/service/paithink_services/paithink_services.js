/**
 * Created by Administrator on 2015/10/31.
 */
define(['jquery','../common/main_poster_event'],function($,main_poster_event){

    var init = function(){
        $('#server_menu').click(function(){
            main_poster_event.addClickTimes($(this).attr('obj_id'));
        });
    }

    return{
        init:init
    }
});