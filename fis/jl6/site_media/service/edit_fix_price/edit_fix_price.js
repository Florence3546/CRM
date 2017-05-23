/**
 * Created by Administrator on 2015/9/22.
 */
define(["template",'jl6/site_media/widget/alert/alert'], function(template,alert) {
    "use strict";

    var tpl;

    tpl = __inline('edit_fix_price.html');

    var show=function(options){
        var html,
            obj;

        html = template.compile(tpl)({value:options.value,title:options.title,type:options.type});

        obj=$(html);

        $('body').append(obj);

        obj.modal();

        obj.find('.btn-primary').on('click',function(){
            var fix_price=obj.find('input').val();

            if(isNaN(fix_price) || fix_price>20 || fix_price <0.62){
                $('.alert-danger').fadeIn();
                return false;
            }

            obj.modal('hide');

            if(fix_price==options.value){
                return false;
            }

            options.onChange(fix_price);
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

    }

    return {
        show: show
    }
});
