/**
 * Created by Administrator on 2016/1/20.
 */
define(['template'], function(template){

    var tpl= __inline('loading.html');
    var obj;

    var show = function(tip){
        var html = template.compile(tpl)({tip: tip});
        obj = $(html);
        $("body").append(obj);
    }

    var hide = function(){
        obj&&obj.remove();
    }

    return {
        show: show,
        hide: hide
    }
});