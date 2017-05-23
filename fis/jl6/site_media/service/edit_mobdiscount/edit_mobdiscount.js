/**
 * Created by Administrator on 2015/9/22.
 */
define(["template", 'jl6/site_media/widget/ajax/ajax','jl6/site_media/widget/lightMsg/lightMsg'], function(template,ajax,lightMsg) {
    "use strict";

    var tpl;

    tpl = __inline('edit_mobdiscount.html');

    var show=function(options){

        var html,
            obj;

        html = template.compile(tpl)({value:options.value});

        obj=$(html);

        $('body').append(obj);

        obj.modal();

        obj.find('.btn-primary').on('click',function(){
            var discount=obj.find('input').val();
            if(discount==options.value){
                obj.modal('hide');
                return false;
            }
            if(Number(discount)){
                discount = parseInt(discount);
                if(discount>400 || discount <1){
                    obj.find('.form-control').tooltip({title:'移动折扣介于1%~400%之间！',placement:'top',trigger:'manual'});
                    obj.find('.form-control').tooltip('show');
                    return false;
                }
            }else{
                obj.find('.form-control').tooltip({title:'移动折扣格式不正确，请输入正整数！',placement:'top',trigger:'manual'});
                obj.find('.form-control').tooltip('show');
                return false;
            }

            obj.modal('hide');
            ajax.ajax('set_adg_mobdiscount', {'campaign_id': options.campaign_id, 'adgroup_id': options.adgroup_id, 'discount':discount},
                function(data){
                    lightMsg.show({'body':'修改移动折扣成功！'});
                    options.obj.text(data.discount);
                }
            );
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });

        obj.find('#use_camp_mobdiscount').on('click', function(){
            obj.modal('hide');
            ajax.ajax('delete_adg_mobdiscount', {'campaign_id': options.campaign_id, 'adgroup_id':options.adgroup_id},
                function(data){
                    lightMsg.show({'body':'修改移动折扣成功！'});
                    options.obj.text(data.discount);
                }
            );
        })

        obj.find('input').focus(function(){
            obj.find('.form-control').tooltip('hide');
        });
    }


    return {
        show: show
    }
});
