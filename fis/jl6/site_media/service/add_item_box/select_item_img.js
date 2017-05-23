/**
 * Created by Administrator on 2015/10/16.
 */
define(["template",'jl6/site_media/widget/alert/alert'], function(template,alert) {
    "use strict";

    var show = function(options){

        var html,obj,tpl=__inline("select_item_img.html");
            html = template.compile(tpl)(options);
        obj=$(html);

        $('body').append(obj);

        obj.modal();

        $('#modal_select_creative_img').on('click', '#update_creative', function () {
            var item_img = $('#modal_select_creative_img li.active>img').attr('src');
            var item_id = $('#modal_select_creative_img').attr('item_id');
            var no = $('#modal_select_creative_img').attr('no');

            if(!item_img){
                alert.show('还未选择创意图片!')
                return false;
            }
            options.onChange(item_img);

            $('#modal_select_creative_img').modal('hide');

            obj.modal('hide');

        });

        $('#modal_select_creative_img .ul_line').on('click','li',function(){
            $('#modal_select_creative_img .ul_line').find('li').removeClass('active');
            $(this).addClass('active');
        });

        obj.on('hidden.bs.modal',function(){
            obj.remove();
        });
    }

    return {
        show:show
    }
});