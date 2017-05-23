define(['jquery'], function($) {
    var init = function () {
        $('[data-toggle="tooltip"]').tooltip();
    }
    return {
        init:init
    }
});