define(["template",'jl6/site_media/widget/alert/alert'], function(template,alert) {
    "use strict";

    var tpl;

    tpl = __inline('edit_camp_title.html');

    var show=function(options){
        var html,
            obj;

        html = template.compile(tpl)(options);

        obj=$(html);

        $('body').append(obj);

        obj.modal();

        obj.find('.btn-primary').on('click',function(){
            var newTitle=obj.find('input').val();

            if(newTitle==options.title){
                alert.show('标题还没有修改哦！');
                return false;
            }
            obj.modal('hide');
            options.onChange(newTitle);
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

    }

    return {
        show: show
    }
});
