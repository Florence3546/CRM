define(['jquery', '../common/common'], function($, common) {

    // 后台调用来设置前台进度条的进度
    function callBack(data) {
        if (typeof(data.redicrect) != 'undefined') {
            window.location.href = data.redicrect;
        };

        if (typeof(data.finished) != 'undefined') {
            if(data.finished){
                $('#progress').animate({
                    width: '100%'
                }, 100, function() {
                    window.location.href = '/web/web_home';
                });
            }else{
                $('#progress').animate({ width: data.progress + '%' }, 100);
            }
        };
    }

    var init = function() {
        //兼容检查
        if (typeof IeTester === true) {
            return;
        }

        //心跳

        setInterval(function() {
            common.sendAjax.ajax('is_data_ready', {}, callBack);
        }, 5000);


        //立即执行一次
        common.sendAjax.ajax('is_data_ready', {}, callBack);

        $('#carousel_box').removeClass('hide');
        $('#myCarousel').carousel();
    }


    return {
        init: init
    }
});
