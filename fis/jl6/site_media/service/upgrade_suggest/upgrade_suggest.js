define(["jquery", 'jl6/site_media/widget/alert/alert', 'jl6/site_media/widget/ajax/ajax', 'jl6/site_media/widget/confirm/confirm'],function($, alert, ajax, confirm){

    var init=function(){
        $('.dg_box .next').on('click',function(){
            $(this).parent().find('.ul_line').css('marginLeft','-100%');
            $(this).removeClass('active');
            $(this).prev().addClass('active');
        });

        $('.dg_box .prev').on('click',function(){
            $(this).parent().find('.ul_line').css('marginLeft','0');
            $(this).removeClass('active');
            $(this).next().addClass('active');
        })
        
        $(".spend_mark").on("click",function(){
            var obj = $(this);
            var temp_id = parseInt(obj.attr('temp_id'));
            if( !isNaN(temp_id) ) {
	            confirm.show({
	                body:'您确定要进行兑换操作吗？',
	                okHidden:function(){
	                    ajax.ajax("generate_link",{
                            'temp_id':temp_id                
	                    }, function(result){
	                       window.location.href = result.url;
	                    });
	                }
	            });
            } else {
                console.log("server version config error.");
            }
        });
    }

    return {
        init:init
    }
});
