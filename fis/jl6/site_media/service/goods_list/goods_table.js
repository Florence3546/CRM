/**
 * Created by Administrator on 2015/9/21.
 */
define(['goods_list','template','select_tool','dataTable','jl6/site_media/widget/ajax/ajax'],
    function(goods_list,template,select_tool,dataTable,ajax) {
    "use strict"

    var init_dom=function(list_type,start_date,end_date,camp_id){
        var html, tpl=__inline("goods_table.html");
        html = template.compile(tpl)();
        $('.ad-group-table').html(html);
        goods_list.init(list_type,start_date,end_date,camp_id);

        var del_callback = function(){
             goods_list.getPageData()
        };
        select_tool.init(list_type,camp_id,del_callback);

        //全选事件
        $(document).on('click','.select-all',function(){
            if($(this).prop('checked')){
                $('body').find('.select-all').prop('checked',true);
                $('.kid_check').prop('checked',true);
                $('.kid_check').parents('td').addClass('tr-checked');
                select_tool.setSelected($('.kid_check').length);
            }else{
                $('body').find('.select-all').prop('checked',false);
                $('.kid_check').prop('checked',false);
                $('.kid_check').parents('td').removeClass('tr-checked');
                select_tool.setSelected(0);
            }
        });

        $('#goods_table').on('change','.kid_check',function(){
            var select_count = $('input:checkbox[class=kid_check]:checked').length;
            select_tool.setSelected(select_count);
            if(select_count==$('.kid_check').length){
                $('body').find('.select-all').prop('checked',true);
            }else{
                $('body').find('.select-all').prop('checked',false);
            }
            if($(this).prop('checked')){
                $(this).parents('td').addClass('tr-checked');
            }else{
                $(this).parents('td').removeClass('tr-checked');
            }
        });

        setTimeout(delaySign,2000);

        //显示或隐藏关键词及创意
        $("#show_kw").on('click',function(){
            $(this).attr('flag','true');
            $(this).text('刷新关键词数');
            var adg_ids = [];
            $('#goods_table').find('.kid_check').each(function(){
                var adgroup_id = $(this).parents("tr").attr('adgroup_id')
                adg_ids.push(adgroup_id);
            });
            ajax.ajax('get_adg_status', {
                'type':'keyword',
                'adg_id_list':'[' + adg_ids.toString() + ']'
            }, get_adg_status_callback);
        });

        $("#show_cr").on('click',function(){
            $(this).attr('flag','true');
            $(this).text('刷新创意数');
            var adg_ids = [];
            $('#goods_table').find('.kid_check').each(function(){
                var adgroup_id = $(this).parents("tr").attr('adgroup_id')
                adg_ids.push(adgroup_id);
            });
            ajax.ajax('get_adg_status', {
                'type':'creative',
                'adg_id_list':'[' + adg_ids.toString() + ']'
            }, get_adg_status_callback);
        });
    }
    
    function get_adg_status_callback(data){
        if(data.errMsg == ""){
            var opt_objs;
            if(data.type == "keyword"){
                opt_objs = $('#goods_table').find('.count-kw');
            }else if(data.type == "creative"){
                opt_objs = $('#goods_table').find('.count-cr');
            }

            $(opt_objs).each(function(){
                var adgroup_id = $(this).parents("tr").attr('adgroup_id');
                var counts = 0;
                if(data.result_dict.hasOwnProperty(adgroup_id)){
                    counts = data.result_dict[adgroup_id];
                }
                $(this).html(counts);
                if($(this).hasClass('hide')){
                    $(this).removeClass('hide');
                }else{
                    $(this).fadeOut(500).fadeIn(500);
                }
            });
        }
    }

    //加载页面后默认显示上次优化时间，3秒后隐藏，隐藏后需启动hover动画样式
    var delaySign = function(){
        $('.width100').animate({width:24},1000,function(){
            $('.width100').removeAttr('style');
            $('.width100').removeClass('width100');
            $('.sign-left>a').addClass('sign-content');
        });
    }

    //查询数据的方法
    var filterData = function(start_date, end_date,campaign_id,search_word,opt_type,status_type,is_follow){
        goods_list.filterData(start_date, end_date,campaign_id,search_word,opt_type,status_type, is_follow);
    }

    return {
        init:init_dom,
        filterData:filterData
    }
});
