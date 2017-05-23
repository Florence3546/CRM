/**
 * Created by tianjh on 2015.10.6
 */

define(['require','template','../page_tool/page_tool','jl6/site_media/widget/ajax/ajax'],
    function(require,template,page_tool,ajax) {
    "use strict"

    var condition;
    var init_dom = function(obj){
        condition = obj;
        getHistoryList(obj);
    }

    //获取操作记录列表数据
    var getHistoryList = function(obj){
        ajax.ajax('get_history_list', obj, get_history_list_callback);
    }

    //查询分页数据
    var getPageData = function(pageIdx){
        condition.pageIdx = pageIdx;
        getHistoryList(condition);
    };

    //修正弹出详细窗口的位置
    var fixWindowPostion = function(obj){
        var obj_height = 288;  //控件高
        var obj_width = 180;  //控件宽

        $(obj).find('.sub_div div').each(function(index, element){
            var _html = $.trim($(element).text().replace(/\s*/g,''))
            .replace(',', '')
            .replace('.', '')
            .replace(':', '')
            .replace(';', '')
            .replace('，', '')
            .replace('。', '')
            .replace('：', '')
            .replace(';', '')
            .replace('"', '')
            .replace("'", '');
            var max_len = _html.length * 14 + 20;  //根据字数计算宽度
            if(max_len > obj_width)
                obj_width = max_len;
        });
        if(obj_width > 800)
            obj_width = 800;
        $(obj).find('.sub_div').css('width', obj_width);

        var window_width = $(window).width();  //窗口宽
        var window_height = $(window).height();  //窗口高
        var scroll_top = $(document).scrollTop();  //滚动条上
        var scroll_left = $(document).scrollLeft();  //滚动条左
        var position = obj.position();
        var position_left = position.left - scroll_left; //控件左
        var position_top = position.top - scroll_top; //控件上
        var position_right = position_left + obj_width;  //控件右
        var position_bottom = position_top + obj_height;  //控件下
        var margin_right = window_width - position_right;  //控件距离右边
        var margin_bottom = window_height - position_bottom;  //控件距离下方
        var margin_top = window_height - position_top;  //控件距离上方
        
        //console.log('控件左:' + position_left +  ' 控件上:' + position_top + ' 控件右:' + position_right 
        //+ ' 控件下:' + position_bottom + ' 窗口宽:' + window_width + ' 窗口高:' + window_height 
        //+ ' 控件距离右边:' + margin_right + ' 控件距离下方:' + margin_bottom + ' 控件距离上方:' + margin_top 
        //+ ' 滚动条上:' + scroll_top + ' 滚动条左:' + scroll_left);
        
        var offset = new Object();
        offset.top = position_top + scroll_top;
        offset.left = position_left + scroll_left;
        if(margin_right < 0){ //如果距离右边没有空间
            offset.left = position_left - obj_width + scroll_left;
            //console.log('右边没有空间啦' + margin_right);
        }
        if(margin_bottom < 0){ //如果距离底部没有空间
            offset.top = position_top - obj_height + scroll_top;
            //console.log('底部没有空间啦' + margin_bottom);
        }
        if(margin_top < 0){ //如果距离顶部没有空间
            offset.top = position_top + obj_height + scroll_top;
            //console.log('顶部没有空间啦' + margin_top);
        }
        $(obj).find('.dropdown-menu').offset(offset);
    }

    //获取操作记录列表的回调
    var get_history_list_callback = function (data){
        var html="",
            tpl=__inline("op_row.html");
        for(var i = 0, i_end = data.history_list.length; i<i_end; i++){
            html += template.compile(tpl)({list:data.history_list[i]});
        }
        //html = template.compile(tpl)({list:data.history_list});
        if($.trim(html) == "")
            html = "<tr><td colspan='5' class='tc'>对不起，查询不到相关数据！</td></tr>"
        $('#op_table tbody').html($.trim(html));
        var page_info = {
            page_row: data.page_info.page,
            page_list: data.page_info.page_xrange,
            page_count: data.page_info.page_count,
            page_size: 100
        }
        page_tool.init(page_info, getPageData);
        
        $('.his_item').on('shown.bs.dropdown',function(){
            fixWindowPostion($(this));
        });
    }

    return {
        init: init_dom,
        getPageData: getPageData
    }
});
