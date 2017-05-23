define(['jquery', '../../widget/ajax/ajax', 'owlcarousel'], function ($, ajax, owlcarousel) {

    // 后台调用来设置前台进度条的进度
    var progress = 20;
    function callBack(data) {
        if (typeof(data.redicrect) != 'undefined') {
            window.location.href = data.redicrect;
        }

        if (typeof(data.finished) != 'undefined') {
            if (data.finished) {
                $('#download_progress').animate({
                    width: '100%'
                }, 100, function () {
                    $('#download_progress').text('100%');
                    window.location.href = '/qnpc/qnpc_home';
                });

            } else {
                $('#download_progress').animate({ width: data.progress + '%' }, 100);
                $('#download_progress').text(data.progress+'%');
            }
        }
        ;
    }

    var init = function () {
        $('#owl-carousel').owlCarousel({
            items: 1,
            autoPlay: true,
            itemsDesktop:false
        });

        //心跳
        setInterval(function() {
            ajax.ajax('is_data_ready', {}, callBack);
        }, 5000);


        //立即执行一次
        ajax.ajax('is_data_ready', {}, callBack);

    };


    return {
        init: init
    }
});
