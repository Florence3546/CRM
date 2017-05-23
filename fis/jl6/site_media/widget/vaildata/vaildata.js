/* ===========================================================
 * @version         0.0.1
 * @since           2014.05.22
 * @author          钟进峰
 * @function        自定义表单验证 $('##').vaildata({callBack:function});
 * @package         jQuery.js,jQuery-tooltip.js
 */

define(['jquery'], function($) {
  "use strict";

  $.fn.vaildata = function(options) {
    var tip_msg;

    var tooltip = function(obj, msg) {
      if (typeof(obj.tooltip) === "undefined") {
        obj.tooltip = new $.fn.tooltip.Constructor(obj, {
          title: msg,
          html: true,
          placement: options.placement
        })
      }
      if (!$(obj).parent().find(obj.tooltip.tip()).length) {
        obj.tooltip.show();
      }
      if (obj.tooltip.tip().length && obj.tooltip.options.title !== msg) {
        tooltip_hide(obj);
        obj.tooltip = new $.fn.tooltip.Constructor(obj, {
          title: msg,
          html: true,
          placement: options.placement
        })
        obj.tooltip.show();
      }
    }

    var tooltip_hide = function(obj) {
      if (typeof(obj.tooltip) !== "undefined") {
        obj.tooltip.hide();
      }
    }

    var require = function(obj) {
      if ($.trim(obj.value) === '') {
        tip_msg += '该项不能为空<br/>';
        return false;
      }
      return true;
    }

    var digital = function(obj) {
      if (isNaN(Number(obj.value))) {
        tip_msg += "该项必须为数字<br/>";
        return false;
      }
      return true;
    }

    var range = function(obj, rule) {

      if (!(/^[0-9]*[1-9][0-9]*$/).test($.trim(obj.value))) {
        tip_msg += '请输入正整数<br/>';
        return false;
      } else {
        if (rule) {
          var min = parseInt(rule.split(",")[0]);
          var max = parseInt(rule.split(",")[1]);
          var value = parseInt(obj.value);
          if (value < min || value > max) {
            tip_msg = '请输入' + min + '与' + max + '之间的整数<br/>'
            return false;
          }
        }
      }

      return true;
    }

    var phone = function(obj) {
      if ($.trim(obj.value) && !(/^0?(13[0-9]|15[012356789]|17[78]|18[0-9]|14[57])[0-9]{8}$/).test($.trim(obj.value))) {
        tip_msg += '请输入正确的手机号码<br/>';
        return false;
      }
      return true;
    }

    var match = function(obj, rule) {
      var other = $(obj).parents('form:first').find('input[name=' + rule + ']').val();
      if ($.trim(other) != $.trim(obj.value)) {
        tip_msg += '两次输入不一致<br/>';
        return false;
      }
      return true;
    }

    var email = function(obj) {
      if ($.trim(obj.value) && !(/^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/).test($.trim(obj.value))) {
        tip_msg += '请输入正确的邮箱地址<br/>';
        return false;
      }
      return true;
    }

    var date = function(obj) {
      if (!(/\d{4}-\d{2}-\d{2}/).test($.trim(obj.value))) {
        tip_msg += '请输入正确的日期<br/>';
        return false;
      }
      return true;
    }

    var minlength = function(obj, rule) {
      if ($.trim(obj.value).length < Number(rule)) {
        tip_msg += '长度不能小于' + rule + '<br/>';
        return false;
      }
      return true;
    }

    var maxlength = function(obj, rule) {
      if ($.trim(obj.value).length > Number(rule)) {
        tip_msg += '长度不能大于' + rule + '<br/>';
        return false;
      }
      return true;
    }

    var nomalstr = function(obj) {
      if (obj.value.match("[%--`~!@#$^&*()=|{}':;',\\[\\].<>/?~！@#￥……&*（）——| {}【】‘；：”“'。，、？]") != null) {
        tip_msg += '不能输入特殊字符<br/>';
        return false;
      }
      return true;
    }

    var nochn = function(obj) {
      if (/.*[\u4e00-\u9fa5]+.*$/.test($.trim(obj.value))) {
        tip_msg += '不能输入中文<br/>';
        return false;
      }
      return true;
    }

    var password = function(obj) {
      var value = $.trim(obj.value);
      if (/.*[\u4e00-\u9fa5]+.*$/.test(value) || value.length > 18 || value.length < 6) {
        tip_msg += '密码格式不正确<br/>';
        return false;
      }
      return true;
    }

    var router_judge_rules = function(obj, rules) {
      var rule_fuc_list = [],
        rules_pass = true,
        rule_list = rules.split(' ');
      tip_msg = ''
        //验证其中的一个规则
      for (var i = 0; i < rule_list.length; i++) {
        var rule_fuc, rule;
        if (rule_list[i].indexOf('[') != -1) {
          rule_fuc = rule_list[i].match('.*\\[')[0].replace('[', ''),
            rule = rule_list[i].match('\\[.*\\]$')[0].slice(1, -1);
        } else {
          rule_fuc = rule_list[i];
        }

        if (typeof(eval(rule_fuc)) === 'function') {
          rules_pass = rules_pass & eval(rule_fuc)(obj, rule);
        }
      }
      if (tip_msg !== '') {
        tooltip(obj, tip_msg)
      } else {
        tooltip_hide(obj);
      }

      return rules_pass
    };

    $('input[data-rule]', this).on('keyup.PT.e', function() { //添加个键盘监听事件
      router_judge_rules(this, this.getAttribute('data-rule'));
      this.focus();
    });


    this.submit(function(e) {
      var inputs, selects, pass = 1,
        that = this;
      e.preventDefault();

      options = $.extend({}, {
        placement: 'top'
      }, options)
      inputs = $('[data-rule]', this);
      selects = $('select[data-rule]', this);

      for (var i = 0; i < selects.length; i++) {
        inputs.push(selects[i]);
      }

      for (var i = 0; i < inputs.length; i++) {
        pass &= router_judge_rules(inputs[i], inputs[i].getAttribute('data-rule'))
      }
      if (typeof options.callBack !== 'undefined' && pass) {
        options.callBack(that);
      }
    });

    return this;
  };
});
