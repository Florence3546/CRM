define(['template'], function(template) {

    var default_config = {binfo: true};
    var show = function(options) {
        var config = $.extend({}, default_config, options.data);
        var tpl, html;
        tpl = __inline('pageBar.html');
        html = template.compile(tpl)(config);

        var obj = $(html);

        obj.find('a').on('click', function() {
            var page;
            page = $(this).attr('data-page');

            if (page == config.page) {
                return false;
            }

            $(obj).find('li').removeClass('active');
            $(obj).find('li').eq(page).addClass('active');
            $(obj).find('.page').text(page);

            options.onChange(page);
        });

        if (!config.page) {
            $(obj).find('li').eq(1).addClass('active');
            $(obj).find('.page').text(1);
        }

        return obj;
    }

    /**
     * 扩展 by tianxiaohe 根据记录总数、每页数据量及页面相识分页工具条
     * @param recordCount
     * @param page_size
     * @param page_no
     */
    var draw_config = {
            inObj:$(document),
            recordCount:0,
            page_size:50,
            page_no:1,
            onChange:function(){}
        };
    var draw = function(options){
        var config = $.extend({}, draw_config, options);
        var startPage = 1,endPage = 1;
        var pageXrange = [],
            pageCount = Math.ceil(config.recordCount / config.page_size);

        var HALF_SHOW_PAGE = 2; // 分页显示数量的一半
        var SHOW_PAGE = HALF_SHOW_PAGE * 2 + 1;

        if(pageCount <= SHOW_PAGE || config.page_no <= HALF_SHOW_PAGE + 1){
            if(pageCount <= SHOW_PAGE){
                endPage = pageCount+1;
            }else{
                endPage = SHOW_PAGE + 1;
            }
        }else{
            startPage = config.page_no - HALF_SHOW_PAGE;
            if(HALF_SHOW_PAGE > pageCount){
                endPage = pageCount;
            }else{
               endPage = config.page_no + HALF_SHOW_PAGE + 1
            }
        }

        if((config.page_no + 2) > pageCount && pageCount > SHOW_PAGE){
            startPage = pageCount - SHOW_PAGE + 1;
            endPage = pageCount+1;
        }

        for (var i = startPage; i < endPage; i++) {
            pageXrange.push(i);
        }

        //取消页码的点击事件，避免多次绑定
        config.inObj.find('.pagination a').unbind('click');

        var dom = show({
            data: {
                record_count: config.recordCount,
                page_xrange: pageXrange,
                page_count: pageCount,
                page: config.page_no
            },
            onChange: config.onChange
        });
        config.inObj.html(dom);
        config.inObj.show();
    };
    return {
        show: show,
        draw:draw
    }
});
