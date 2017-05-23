define(["template"], function(template) {
    "use strict";

    var show = function(options){
        var tpl = __inline('confirm_win.html');
        var html = template.compile(tpl)(options);
        var obj = $(html);
        $('body').append(obj);
        obj.find('.modal-title').text('宝贝现有关键词' + options.result.kw_count + '个，系统分析结果如下，请选择项目后提交：');
        if(options.result.update_count > 0){
            obj.find('#lbl_update').text('改价关键词' + options.result.update_count + '个 ');
            obj.find('#lbl_update').removeClass('hide');
            obj.find('#div_update').removeClass('hide');
            obj.find('#chk_update').attr('checked', 'checked');
        }
        if(options.result.del_count > 0){
            obj.find('#lbl_del').text('删除关键词' + options.result.del_count + '个 ');
            obj.find('#lbl_del').removeClass('hide');
            obj.find('#div_del').removeClass('hide');
            obj.find('#chk_del').attr('checked', 'checked');
        }
        if(options.result.add_count > 0){
            obj.find('#lbl_add').text('添加关键词' + options.result.add_count + '个 ');
            obj.find('#lbl_add').removeClass('hide');
            obj.find('#div_add').removeClass('hide');
            obj.find('#chk_add').attr('checked', 'checked');
        }
        obj.find('#submit_onekey').attr('adgroup_id', options.result.adg_id);
        obj.find('#finish_onekey').attr('adgroup_id', options.result.adg_id);
        obj.find('#cancel_onekey').attr('adgroup_id', options.result.adg_id);
        obj.modal();
    };

    return {
        show: show
    };
});
