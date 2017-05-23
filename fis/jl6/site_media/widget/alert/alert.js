define(["template"], function(template) {
    "use strict";

    var tpl = __inline('tpl.html');

    var show = function(options, forced) {
        var html,
            obj,
            config;

        config = {
            id: "alert_modal",
            title: "精灵提醒",
            body: "",
            okStr: "确定",
            backdrop: "static",
            hidden: function() {},
            type: '',
            footer: true,
            hide: function() {}
        };

        if ("string" == typeof options) {
            options = $.extend({}, config, {
                body: options
            }, forced);
        } else {
            options = $.extend({}, config, options, forced);
        }

        html = template.compile(tpl)(options);

        $("body").append(html);

        obj = $("#" + options.id);
        obj.modal({
            backdrop: options.backdrop
        });

        obj.on("hidden.bs.modal", options.hidden);
        obj.on("hide.bs.modal", options.hide);
        obj.on("hidden.bs.modal", function() {
            obj.remove()
        });

        if (options.id == 'alert_modal_fixed') {
            obj.on("hidden.bs.modal", function() {
                $('body').addClass('modal-open');
            });
        }
    };

    //当已经有一个弹出层时的时候使用，可以修复不对齐和底部抖动的问题
    var fixedShow = function(options) {
        show(options, {
            id: 'alert_modal_fixed',
            backdrop: false
        })
    }

    var success_show = function(options) {
        show(options, {
            type: 'success'
        });
    }

    var error_show = function(options) {
        show(options, {
            type: 'error'
        });
    }

    return {
        show: show,
        fixedShow: fixedShow,
        success_show: success_show,
        error_show: error_show
    }
});
