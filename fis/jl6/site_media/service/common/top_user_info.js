/**
 * Created by tianjh.
 */
define(['jl6/site_media/widget/ajax/ajax'],function(ajax){

    var init = function(){
        var page_name = $('body').attr('id');
        if(page_name == 'web_home'){
            ajax.ajax('check_user_phone',null,function(data){
            if(!data.fill_user_info)
                    $('#top_user_info').removeClass('hide').fadeIn(1000);
            },null,{url:'/web/ajax/'});
        }
    };

    return {
        init:init
    }
});