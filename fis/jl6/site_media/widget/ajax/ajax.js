define(["../alert/alert.js","widget/loading/loading"], function(_alert,_loading) {
    "use strict";
    var success = function(result, callBack) {
        if (result.errMsg != "") {
            _loading.hide();
            _alert.show(result.errMsg);
        } else {
            callBack && callBack(result);
        }
    };
    var ajax = function(func, data, callBack, error, options) {
        var config = {
            'url': '/web/ajax/',
            'type': 'post',
            'dataType': 'jsonp',
            'data': $.extend({}, {
                'function': func || 'undefined'
            }, data),
            'timeout': 60000,
            'cache': false,
            'success': function(result) {
                success(result, callBack)
            },
            'error': error || function(XMLHttpRequest, textStatus, errorThrown) {
                _loading.hide();
                _alert.show('获取服务器数据失败，请刷新页面重试，或联系顾问');
            }
        }
        config = $.extend({}, config, options);
        $.ajax(config);
    };
    return {
        ajax: ajax
    }
});
