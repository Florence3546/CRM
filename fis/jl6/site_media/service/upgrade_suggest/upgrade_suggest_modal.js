/**
 * Created by Administrator on 2015/12/2.
 */
define(["template"],function(template){

    var tpl = __inline('upgrade_suggest_modal.html');
    var show = function(msg){
        var html, obj;
        html = template.compile(tpl)({msg:msg});
        obj=$(html);

        $('body').append(obj);

        obj.modal();

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });
    };

    return{
        show:show
    }
});