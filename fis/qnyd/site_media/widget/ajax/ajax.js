define(["zepto",'sm'], function() {
    "use strict";
    var success = function(result, callBack) {
        if (result.errMsg != "") {
            $.hidePreloader();
            $.alert(result.errMsg);
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
                $.hidePreloader();
                $.alert('获取服务器数据失败，请刷新页面重试，或联系顾问');
            }
        }
        config = $.extend({}, config, options);
        $.ajax(config)
    };
    return {
        ajax: ajax
    }
});
