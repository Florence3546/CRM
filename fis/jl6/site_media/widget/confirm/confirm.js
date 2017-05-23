define(["template"], function(template) {
    "use strict";

    var tpl, config;

    tpl = __inline('tpl.html');

    config = {
        id: "alert_modal",
        title: "精灵提醒",
        body: "请开发人员填写内容",
        cancleStr: "取消",
        okStr: "确定",
        backdrop: "static",
        okHidden: function() {},
        okHide: function() {},
        cancleHidden: function() {},
        cancleHide: function() {}
    }

    var show = function(options) {
        var has_modal=false, html, obj, isOk = true;
        options = $.extend({}, config, options);
        template.config('escape', false);

        html = template.compile(tpl)(options);

        $('.modal').each(function() {
            if ($(this).attr('class').indexOf('in') !== -1) {
                has_modal = true;
                return;
            }
        });

        $("body").append(html);

        obj = $("#" + options.id);

        obj.modal(options);

        obj.on("hidden.bs.modal", function() {
            isOk ? options.okHidden && options.okHidden() : options.cancleHidden && options.cancleHidden()
        });

        obj.on("hide.bs.modal", function() {
            isOk ? options.okHide && options.okHide() : options.cancleHide && options.cancleHide()
        });

        obj.on("hidden.bs.modal", function() {
            if(has_modal){
                $('body').addClass('modal-open');
            }
            obj.remove()
        });

        $(obj).find(".modal-footer>button").on("click", function(e) {
            e.target.className.indexOf("primary") == -1 && (isOk = false)
            obj.modal("hide")
        });

        $(obj).find('.close').on("click", function(e) {
            isOk = false;
        });
    }

    return {
        show: show
    }
});
