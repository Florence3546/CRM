/**
 * Created by tianjh on 2015.10.6
 */
define(['op_row','template','dataTable','jl6/site_media/widget/ajax/ajax'],
    function(op_row,template,dataTable,ajax) {
    "use strict"

    var init_dom=function(list_type){
        var html,tpl=__inline("op_table.html");
        html = template.compile(tpl)({list_type:list_type});
        $('.op-table').html(html);
        ajax.ajax('get_camp_list',{},get_camp_list_callback);
        
        op_row.init(list_type);
        setTimeout(delaySign,2000);
    }

    //加载页面后默认显示上次优化时间，3秒后隐藏，隐藏后需启动hover动画样式
    var delaySign = function(){
        $('.width100').animate({width:24},1000,function(){
            $('.width100').removeAttr('style');
            $('.width100').removeClass('width100');
            $('.sign-left>a').addClass('sign-content');
        });
    }

    //获取计划列表回调函数
    var get_camp_list_callback = function (data){
        var html = ''
        $.each(data.camp_list, function(idx, item){
            html += '<li data-value="' + item.camp_id + '"><span>' + item.camp_title + '</span></li>'
        });
        $('#select_camp').find('ul').html(html)
    }

    return {
        init:init_dom
    }
});
