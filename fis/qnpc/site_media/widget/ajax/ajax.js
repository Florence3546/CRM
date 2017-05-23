define(["widget/loading/loading"], function(loading) {
    "use strict";
    var success = function(result, callBack) {
        if (result.errMsg != "") {
            $.alert({title:'错误',closeBtn: false, body: result.errMsg, okBtn:"确定", height:"60px"});
            loading.hide();
        } else {
            callBack && callBack(result);
        }
    };
    var ajax = function(func, data, callBack, error, options) {
        var config = {
            'url': '/qnyd/ajax/',
            'type': 'post',
            'dataType': 'json',
            'data': $.extend({}, {
                'function': func || 'undefined'
            }, data),
            'timeout': 60000,
            'cache': false,
            'success': function(result) {
                success(result, callBack)
            },
            'error': error || function(XMLHttpRequest, textStatus, errorThrown) {
                loading.hide();
            }
        }
        config = $.extend({}, config, options);
        $.ajax(config);
    };
    return {
        ajax: ajax
    }
});
