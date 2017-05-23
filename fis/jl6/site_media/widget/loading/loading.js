define(['jquery',"template"], function($,template) {
    "use strict";

    var tpl, obj, is_show, obj_list=[];

    tpl = __inline('tpl.html');

    var show = function(tip) {
        var html;

        is_show=true;

        html = template.compile(tpl)({
            tip: tip
        });

        obj=$(html);

        $("body").append(obj).addClass('loading-open');

        obj.focus();
        if (obj_list.length==0) {
            obj.addClass('active');
        }

        obj.on($.support.transition.end,function(){
            if(is_show==false){
                obj&&obj.remove();
            }
        });
        obj_list.push(obj);
    }

    var hide=function(){
        is_show=false;
        obj = obj_list.pop();
        if (obj_list.length==0) {
            $("body").removeClass('loading-open');
            obj&&obj.removeClass('active');
        }
        obj&&obj.remove();
    }

    return {
        show: show,
        hide: hide
    }
});
