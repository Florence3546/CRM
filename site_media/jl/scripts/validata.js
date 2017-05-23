/* ===========================================================
 * @version			0.0.1
 * @since			2014.05.22
 * @author			zhongJinFeng
 * @function        自定义表单验证 $('##').vaildata({submit:bool,call_back:function});
 * @package			jQuery.js,jQuery-tooltip.js
 */


(function ($) {
    $.fn.vaildata = function (options) {
        var tip_msg;

        var tooltip = function (obj, msg) {
            if (typeof (obj.tooltip) === "undefined") {
                obj.tooltip = new $.fn.tooltip.Constructor(obj, {
                    title: msg
                })
            }
            if (!$(obj).parent().find(obj.tooltip.tip()).length) {
                obj.tooltip.show();
            }
            if (obj.tooltip.tip().length && obj.tooltip.options.title !== msg) {
                tooltip_hide(obj);
                obj.tooltip = new $.fn.tooltip.Constructor(obj, {
                    title: msg
                })
                obj.tooltip.show();
            }
        }

        var tooltip_hide = function (obj) {
            if (typeof (obj.tooltip) !== "undefined") {
                obj.tooltip.hide();
            }
        }

        var require = function (obj) {
            if ($.trim(obj.value) === '') {
                tip_msg += '该项不能为空<br/>';
                return false;
            }
            return true;
        }

        var digital = function (obj) {
            if (isNaN(Number(obj.value))) {
                tip_msg += '该项必须为数字<br/>';
                return false;
            }
            return true;
        }

        var router_judge_rules = function (obj, rules) {
            var rule_fuc_list = [],
                rules_pass = true,
                rule_list = rules.split(' ');
            tip_msg = ''
            //验证其中的一个规则
            for (var i = 0; i < rule_list.length; i++) {
                var rule_fuc, rule;
                if (rule_list[i].indexOf('[') != -1) {
                    rule_fuc = rule_list[i].match('.*\\[')[0].replace('[', ''),
                    rule = rule_list[i].match('.*\\[')[0].match('\\[.*\\]');
                } else {
                    rule_fuc = rule_list[i];
                }

                if (typeof (eval(rule_fuc)) == 'function') {
                    rules_pass = rules_pass & eval(rule_fuc)(obj, rule);
                }
            }
            if (!tip_msg == '') {
                tooltip(obj, tip_msg)
            } else {
                tooltip_hide(obj);
            }

            return rules_pass
        };

        $('input[vail-rule]', this).on('keyup.PT.e', function () { //添加个键盘监听事件
            router_judge_rules(this, this.getAttribute('vail-rule'));
            this.focus();
        });

        this.submit(function () {
            var inputs, pass=1;
            inputs = $('input[vail-rule]', this);
            for (var i = 0; i < inputs.length; i++) {
                pass &= router_judge_rules(inputs[i], inputs[i].getAttribute('vail-rule'))
            }
            if (typeof options.call_back !== 'undefined' && pass) {
                options.call_back(this);
            }
            return options.submit
        });

        return this;
    };
})(jQuery);