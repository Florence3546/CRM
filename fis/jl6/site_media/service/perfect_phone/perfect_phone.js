define(["require","template",'widget/alert/alert','widget/lightMsg/lightMsg','widget/ajax/ajax','widget/vaildata/vaildata'], function(require,template,alert,lightMsg,ajax) {
    "use strict";

    var tpl,
        obj;

    tpl = __inline('perfect_phone.html');

    var show=function(options){
        var html;

        html = template.compile(tpl)(options);

        obj=$(html);

        $('body').append(obj);

        obj.find('form').vaildata({
            placement: 'right',
            callBack: function(formObj) {
                var phone,
                    qq;

                phone=$(formObj).find('[name=phone]').val();
                qq=$(formObj).find('[name=qq]').val();

                 ajax.ajax('submit_userinfo',{phone:phone,qq:qq},function(){
                    lightMsg.show('激活成功');
                 });

                 obj.modal('hide');
            }
        });

        obj.on('show.bs.modal',function(){
            ajax.ajax('customer_info',{},function(data){
                console.log(data)
                obj.find('[name=phone]').val(data.data[0].phone);
                obj.find('[name=qq]').val(data.data[0].qq);
            });
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

        obj.modal();
    }

    return {
        show: show
    }
});
