define(['require', 'zepto', 'sm'], function(require, $) {

    var initDom = function() {


        $('.select_days').each(function() {
            var self=this;

            $(this).find('select').on('change',function(){
                $(self).find('.text').text($(this).find(':checked').text());
                $(self).trigger('change',[this.value]);
            });


        });
    }

    return {
        init: initDom
    }

});
