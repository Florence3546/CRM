define(['jquery','widget/lightMsg/lightMsg','zclip'],function($,lightMsg){

    var init=function(){
        var zclip_params = {
            path:__uri('../../plugins/zclip/ZeroClipboard.swf'),
            copy:function(){
                var temp;
                $.ajax({
                    type:'post',
                    async:false,
                    url:'/web/ajax/',
                    data:{'function':"get_praise"},
                    dataType:'jsonp',
                    success:function(data){
                        if(data.errMsg==""){
                            temp= data.data;
                        }else{
                            lightMsg.show(data.errMsg);
                        }
                    }
                });
                if(temp){
                    $('#div_msg').removeClass('hide');
                    $('#show_history_praise').html('换一条评语');
                    $('#div_content').html('"' + temp + '"');
                }
                return temp;
            },
            afterCopy:function(){
            }
        };
        $('#show_history_praise').zclip(zclip_params);
        $("#go_to_comment").zclip(zclip_params);
        
        $("#go_to_comment").click(function(){
            $("#commont_header").hide();
            $("#commont_panel").show();
        });
    }

    return {
        init:init
    }
});
