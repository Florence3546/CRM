/**
 * Created by Administrator on 2015/9/19.
 */
define(['template'],function(template){
    "use strict";
    var init = function(options,func){
        var tpl = __inline('page_tool.html');
        var html,obj;
        html = template.compile(tpl)(options);
        obj = $(html);
        $('.page-tool').empty();
        $('.page-tool').append(obj);
        $(".page_row").on('click',function(){
            if($(this).attr('page_row')==obj.find('.current_page').val()){
                return false;
            }
            $(".page_row").removeClass('active');
            $(this).addClass('active');
            return func($(this).attr('page_row'));
        });
    }

    var show = function(){
        $('.page-tool').removeClass('hide');
    };

    var hide = function(){
        $('.page-tool').addClass('hide');
    };

    return {
        init:init,
        show:show,
        hide:hide
    }
});