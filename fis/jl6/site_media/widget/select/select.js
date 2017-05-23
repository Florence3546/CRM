define(['jquery'],function($) {
    "use strict";

    $(document).on('click.data-select.api','.select_warp>ul>li',function(){
        var value,
            opt,
            parent=$(this).parent().parent();

        value=$(this).data('value');
        opt=$(this).text();

        parent.find('.tip').text(opt);
        parent.trigger('change',[value]);
        $(this).parent().find('li>span').removeClass('active');
        $(this).find('span').addClass('active');
    });

    $(document).on('choose.data-select','.select_warp',function(e,value){
        var options;

        $(this).find('ul>li>span').removeClass('active');
        $(this).find('ul>li').each(function(){
            if($(this).data('value')==value){
                $(this).find('span').addClass('active');
                options=$(this).find('span').text();
                return false;
            }
        });
        $(this).find('.tip').text(options);
    });
});
