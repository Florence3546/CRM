APP.controller('routeCtl', function($scope, $timeout) {
    $(document).on("pageInit", function(e, pageId, $page) {

        $timeout(function(){
            $scope.$emit("qnydCtl."+pageId+"Data");
        },0);

        $('#main_bar>a').each(function() {
            var href = $(this).attr('data-href') || '';
            if (href.indexOf(pageId) == -1) {
                $(this).attr('href', $(this).attr('data-href'));
                $(this).removeClass('active');
            } else {
                $(this).attr('href', '#');
                $(this).addClass('active');
                document.title = $(this).attr('title');
            }
        });

    });


    $(document).ready(function() {
        $('.select_days').each(function() {
            var self = this;

            $(this).find('select').on('change', function() {
                $(self).find('.text').text($(this).find(':checked').text());
                $(self).trigger('change', [this.value]);
            });
        });

        $('.page').removeAttr('style');
        $.init();
    });

});

__inline('home/home.js');
__inline('rob_rank/rob_rank.js');
__inline('shop_core/shop_core.js');
__inline('my/my.js');
