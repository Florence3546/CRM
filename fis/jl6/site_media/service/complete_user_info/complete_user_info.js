define(["require", "template", 'widget/alert/alert', 'widget/lightMsg/lightMsg', 'widget/ajax/ajax', 'widget/vaildata/vaildata'], function(require, template, alert, lightMsg, ajax) {
    "use strict";

    var tpl,
        obj;

    tpl = __inline('complete_user_info.html');

    var show = function(options) {
        var html,
            config={
                callBack:function(){}
            };
            
        options=$.extend({},config,options);
        html = template.compile(tpl)(options);

        obj = $(html);

        $('body').append(obj);

        obj.find('form').vaildata({
            placement: 'right',
            callBack: function() {
                var receiver, receiver_phone, receive_address, zip_code, qq;

                receiver = $('#receiver').val();
                receiver_phone = $('#receiver_phone').val();
                receive_address = $('#receive_address').val();
                zip_code = $('#zip_code').val();
                qq = $('#qq').val();

                ajax.ajax('perfect_info', {
                    phone: receiver_phone,
                    receiver: receiver,
                    receive_address: receive_address,
                    zip_code: zip_code,
                    qq:qq
                }, function(data) {
                    lightMsg.show('更新成功');
                    options.callBack && options.callBack();
                });

                obj.modal('hide');
            }
        });

        obj.on('show.bs.modal', function() {
            ajax.ajax('user_info', {}, function(data) {
                $('#receiver').val(data.info_dict.receiver);
                $('#receiver_phone').val(data.info_dict.phone);
                $('#receive_address').val(data.info_dict.receive_address);
                $('#zip_code').val(data.info_dict.zip_code);
                $('#qq').val(data.info_dict.qq);
            });

            obj.find('[disabled]').removeAttr('disabled');
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
