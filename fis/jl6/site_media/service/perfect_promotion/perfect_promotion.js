define(["require", "template", 'widget/alert/alert', 'widget/ajax/ajax', 'store', 'widget/vaildata/vaildata'], function(require, template, alert, ajax, store) {
    "use strict";

    var tpl,
        obj;

    tpl = __inline('perfect_promotion.html');

    var show = function(options) {
        var html;

        if(store.get('perfect_promotion')){
            return
        }

        html = template.compile(tpl)(options);

        obj = $(html);

        $('body').append(obj);

        obj.find('form').vaildata({
            placement: 'right',
            callBack: function(formObj) {
                var guide_name;

                guide_name = $(formObj).find('[name=guide_name]').val();

                ajax.ajax('receive_recount',{guide_name:guide_name},function(data){
                    alert.show('恭喜您获得精灵赠送的<span class="red">'+data.point+'</span>个精灵币');
                    obj.modal('hide');
                });
            }
        });

        obj.find('input[type=checkbox]').on('change',function(){
            if(this.checked){
                store.set('perfect_promotion',true);
            }else{
                store.clear('perfect_promotion')
            }
        });

        obj.on('hidden.bs.modal', function() {
            obj.remove();
        });

        obj.modal();
    }

    return {
        show: show
    }
});
