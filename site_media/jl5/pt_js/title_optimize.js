PT.namespace('TitleOptimize');
PT.TitleOptimize = function(){
    var title_elemword_list = $('#title_word_str').length&&$('#title_word_str').val().split(',');
    var adgroup_id = $('#adgroup_id').val();
    var item_id = $('#item_id').val();
    var update_convwrod_flag = $('#update_convwrod_flag').val();
    var init = function() {

        //词根区布局调整
        $('#div_prmtword, #div_dcrtword, #div_propword, #div_prdtword').each(function(){
            if($(this).find('li').length>14){
                //$(this).find('ul').append('<button type="button" class="btn mini yellow btn_more">更多</button>');
                $(this).find('li:last').after('<i class="iconfont poi gray btn_more">&#xe61a;</i>');
                //$(this).find('li:gt(13)').hide();
            }
        });
        $(document).on('click', '.btn_more', function(){
            $(this).siblings('li').animate({opacity:'show'}, 'normal');
            $(this).html('&#xe658');
            $(this).removeClass('btn_more');
            $(this).addClass('btn_collapse');
        });
        $(document).on('click', '.btn_collapse', function(){
            $(this).siblings('li:gt(13)').animate({opacity:'hide'}, 'fast');
            $(this).html('&#xe61a');
            $(this).removeClass('btn_collapse');
            $(this).addClass('btn_more');
        });
        
        // 由于流控问题，临时提醒用户会很慢
//        if (!confirm('亲，由于最近淘宝接口流控问题，加载数据会比较慢，确定要继续吗？')) {
//	        window.close();
//        }

        // 获取直通车转化词
        PT.sendDajax({'function':'web_get_item_convword',
            'item_id':item_id,
            'update_convwrod_flag':update_convwrod_flag,
            'auto_hide':0
            });

        //当前标题绑定数据
        $("span.title:eq(0)").data('title_elemword_list',title_elemword_list);
        show_title_elemword(title_elemword_list);
        get_title_traffic_score($("#item_title").val(), 0, title_elemword_list);

        //页面元素绑定事件
        $("#btn_create_title").click(create_title);
        $("#btn_clear_title").click(clear_title);
        $('#update_elemword').click(function () {
            PT.show_loading('正在更新词根');
            window.location.href = '?adgroup_id=' + adgroup_id + '&update_flag=True';
        });
        $('#update_elemword_hot').click(function () {
            PT.show_loading('正在更新词根引流能力');
            window.location.href = '?adgroup_id=' + adgroup_id + '&update_hot_flag=True';
        });
//      $("#div_elemword :checkbox").click(function(){click_elemword($(this));});
//      $("#table_titles").on('click','span.title',function(){modify_title($(this));});

        // 选词区词根悬停事件，为避免样式BUG分开写
        $('#div_elemword').on('mouseenter','li.select',function(){
            $('#div_elemword li').removeClass('selected_elemword');
            $('#div_preview_title li').removeClass('selected_elemword');
            $('#div_preview_title .icon-remove').remove();
            var word = $(this).find('a').attr('value');
            var preview_obj = $('#div_preview_title li[text="'+word+'"]');
            $(this).addClass('selected_elemword');
            //$(this).find('i').triggerHandler('mouseenter');
            preview_obj.addClass('selected_elemword');
            var remove_sign = preview_obj.find('.icon-remove');
            if(!remove_sign.length){
                preview_obj.append('<i class="icon-remove"></i>');
            }
        });

        $('#div_elemword').on('mouseleave','li.select',function(){
            var word = $(this).find('a').attr('value');
            var preview_obj = $('#div_preview_title li[text="'+word+'"]');
            $(this).removeClass('selected_elemword');
            //$(this).find('i').triggerHandler('mouseleave');
            preview_obj.removeClass('selected_elemword');
            var remove_sign = preview_obj.find('.icon-remove');
            if(remove_sign.length){
                remove_sign.remove();
            }
        });

        $('#div_preview_title').on('mouseenter mouseleave','li:not(#preview_title_prompt)',function(){
            var word = $(this).text();
            $('#div_elemword li:has(input[value="'+word+'"])').show();
            $('#div_elemword li:has(input[value="'+word+'"])').toggleClass('selected_elemword');
            $(this).toggleClass('selected_elemword');
            var remove_sign = $(this).find('.icon-remove');
            if(remove_sign.length){
                remove_sign.remove();
            }else{
                $(this).append('<i class="icon-remove"></i>');
            }
        });

        $('#div_preview_title').on('click','.icon-remove',function(){
            var word = $(this).closest('li').text();
            var obj = $('#div_elemword li.select a[value="'+word+'"]').parent();
            obj.removeClass('select');
            $(this).closest('li').remove();
            check_title_length();
            // obj.find('input').click();
        });

        $("#table_titles").on('click', 'span.title', function(){
            $("#table_titles span.title").removeClass("red");
            $(this).addClass("red");
            //显示词根信息和关键词信息
            show_title_elemword($(this).data('title_elemword_list')||[]);
            show_title_kw($(this).data('kw_list'), false);
            // $('#sum_traffic_score td').html($(this).data('title_traffic_score'));
        });

        $("#table_titles").on('click', '.edit_title', function(){
           var obj = $(this).prev();
           modify_title(obj);
        });

        $("#table_titles").on('click','a.get_title_traffic_score',function(){
            var title_tr = $(this).closest("tr");
                title_input = title_tr.find("input"),
                title = title_input.val()||title_tr.find('span.title').text(),
                title_num = title_tr.attr("title_num"),
                first_num = title_num.split('-')[0];

            if(is_duplicate_title(title)){
                PT.alert("列表中已存在相同的标题");
                return;
            }else if(bytes_len(title)>60){
                PT.alert("标题超过30个汉字，请做出修改");
                return;
            }else if(!title){
                PT.alert("标题不能为空，请做出修改");
                return;
            }

            title_input.closest('td').replaceWith('<td data-title="参考标题"><span class="title poi">'+title+'</span><i class="icon-pencil poi ml5 edit_title"></i></td>');
            get_title_traffic_score(title,title_num,[]);
            $(this).replaceWith('<a href="javascript:void(0);" class="submit_title btn btn-mini">提交</a>');
            title_tr.removeClass("modifying");
            $("#table_titles span.title").removeClass("red");
            title_tr.find("span.title").addClass("red");
            title_tr.find('.icon-add').removeClass('hide');
            $("#table_titles tr[title_num^='"+first_num+"-']:last").after(title_tr); // 修改过的标题按编号排序
            
	        //隐藏上一级标题，讲折叠符号变为“+”
            $(this).parent().parent().prev().find("i.icon-low").removeClass('icon-low').addClass('icon-add');
        });

        $("#table_titles").on("click","a.submit_title:not(.current_title)",function(){
            var title_tr = $(this).closest('tr');
            var title = title_tr.find('span.title').text();
            if(title==$("#item_title").val()){
                PT.alert("与宝贝当前标题相同");
            }else{
                var title_num = title_tr.attr('title_num');
                submit_title(title, title_num);
            }
        });

        $("#table_titles").on('click','.icon-add',function(){
            var title_num,kw_list,title_tr = $(this).closest('tr');
            title_num = title_tr.attr('title_num');
            kw_list=title_tr.find('span.title').data('kw_list');
            show_title_kw(title_num,kw_list);
            $(this).removeClass('icon-add').addClass('icon-low')
        });

        $("#table_titles").on('click','.icon-low',function(){
            var title_tr = $(this).closest('tr');
            title_tr.next().remove();
            $(this).removeClass('icon-low').addClass('icon-add')
        });

        //宝贝属性显示隐藏切换
        $('#adgroup_property').on('click',function(){
            $('#adgroup_property_box').toggleClass('hide');
        });

        check_title_length();

        $('.popovers').popover({html:true});
    }

    //按照模板【品牌 + 年份 + 促销词 + (修饰词 + 属性词 + 产品词) * n + 转化词】对标题词根进行排序
    var sort_title = function(){
        var objs = $("#div_preview_title li");
        for(var i=0;i<objs.length;i++){
            var word_type = objs.eq(i).attr("type");
            if(!word_type){
                word_type = $("#div_elemword li.select a[value='"+objs.eq(i).html()+"']").attr("name");
                objs.eq(i).attr("type", word_type||"dcrtword");
            }
        }
        var title = $("#div_preview_title ul");
        //品牌词
        var brand = $("#div_preview_title li[type='brand']");
        title.append(brand);
        //年份
        var year = new Date().getFullYear();
        year = $("#div_preview_title li[text='"+year+"']");
        year.attr("type", "year");
        title.append(year);
        //促销词
        var prmtword = $("#div_preview_title li[type='prmtword']");
        title.append(prmtword);
        //(修饰词 + 属性词 + 产品词)*n
        var dcrtword_propword = $("#div_preview_title li[type='dcrtword'], #div_preview_title li[type='propword']");
        title.append(dcrtword_propword);
        var prdtword = $("#div_preview_title li[type='prdtword']");
        title.append(prdtword);
        if(dcrtword_propword.length > 0){
            var incr = Math.floor((dcrtword_propword.length-1)/prdtword.length); //增量
            var mod = (dcrtword_propword.length-1)%prdtword.length; //余数
            var begin = 0, end = 0;
            for(var i=0, j=prdtword.length;i<j;i++){
                var _mod = i<mod?1:0
                end = begin + incr + _mod;
                prdtword.eq(i).before(dcrtword_propword.slice(begin, end));
                begin = end;
                if(i==mod) prdtword.eq(i).before(dcrtword_propword.last());
            }
        }
        //转化词
        var convword = $("#div_preview_title li[type='convword']");
        title.append(convword);
    }

    var check_title_length = function(){
        var title = $("#div_preview_title li").text();
        var remain_char_count = Math.floor(30-bytes_len(title)/2);
        if(title.length==0){
            $("#div_preview_title ul").html('<li id="preview_title_prompt">勾选词根后此组合框会自动组合标题</li>');
        }

        if(remain_char_count>=0){
            $("#remain_char_prompt").parent().removeClass('red');
            $("#remain_char_prompt").html("你还可选");
            $("#remain_char_count").html(remain_char_count);
        }else{
            $("#remain_char_prompt").parent().addClass('red');
            $("#remain_char_prompt").html("你已超过");
            $("#remain_char_count").html(Math.abs(remain_char_count));
        }

        if(remain_char_count>0){
            return true;
        }else{
            return false;
        }
    }

    var check_title_length2 = function(title){
        var remain_char_count = Math.floor(30-bytes_len(title)/2);
        if(remain_char_count>=0){
            $("#check_title_prompt").html("还可加");
            $("#check_result").html(remain_char_count);
        }else{
            $("#check_title_prompt").html("已超过");
            $("#check_result").html(Math.abs(remain_char_count));
        }
    }

    var check_prdtword_count = function(){
        if($("#div_prdtword li.select").length>3){
            $("#prdtword_warning").css("display","inline-block");
            // if(!App.isIE8() && $().pulsate){
            //     $("#prdtword_warning").pulsate("destroy");
            //     $("#prdtword_warning").pulsate({color:"#ff8a3b"});
            // }
        }else{
            // if(!App.isIE8() && $().pulsate){
            //     $("#prdtword_warning").pulsate("destroy");
            // }
            $("#prdtword_warning").hide();
        }
    }

    var click_elemword = function(obj) {
        var value = obj.find('a').attr('value');

        if (check_title_length()) {
            //如果可以插入数据
            if ($("#preview_title_prompt").length != 0) {
                //删除提示
                $("#preview_title_prompt").remove();
            }

            obj.toggleClass('select');

            //检查产品词
            check_prdtword_count();

            if (obj.hasClass('select')) {
                $("#div_preview_title ul").append("<li text='" + value + "' type='" + obj.find('a').attr('name') + "' class='selected_elemword'>" + value + "<i class='icon-remove'></i></li>");
            } else {
                $("#div_preview_title li[text='" + value + "']").remove();
            }

            sort_title();
        } else {
            obj.removeClass('select');
            $("#div_preview_title li[text='" + value + "']").remove();
        }

        check_title_length();
    }

    var create_title = function(){
        if($("#preview_title_prompt").length!=0){
            PT.alert("请先选词根");
        }else{
            var new_title = $("#div_preview_title li").text();
//            var title_elemword_list = $.map($("#div_preview_title li"), function(obj){return $(obj).text();});
            var title_elemword_list = [];
            if(is_duplicate_title(new_title)){
                PT.alert("列表中已存在相同的标题");
                return;
            }else if(bytes_len(new_title)>60){
                PT.alert("标题长度不能超过30个汉字");
                return;
            }
            var last_title_num = $("#table_titles tr[title_num]:last").attr("title_num").split('-')[0];
            var title_num = String(Number(last_title_num)+1);
            var title_tr = template.compile(pt_tpm['title_opt_title.tpm.html'])({title_num:title_num,title:new_title});
            $("#table_titles>tbody>tr:not([title_num])").remove();// 删除点开的引流能力列表
            $("#table_titles>tbody>tr i.icon-low").removeClass('icon-low').addClass('icon-add');

            $("#table_titles").append(title_tr);
            $("#table_titles tr.modifying").remove();
            $("#table_titles span.title").removeClass("red");
            var title_obj = $("#table_titles tr[title_num='"+title_num+"'] span.title");
            title_obj.data("title_elemword_list",title_elemword_list);
            title_obj.addClass("red");
            get_title_traffic_score(new_title,title_num,title_elemword_list);
        }
    }

    var modify_title = function(obj){
        var title_tr = obj.parentsUntil('tr').parent();
        //生成或者去掉编辑行
        if(title_tr.next(".modifying").length){
            title_tr.next(".modifying").remove();
        }else{
            $("#table_titles tr.modifying").remove();
            var title_num = title_tr.attr('title_num');
            var first_num = title_num.split('-')[0];
            var siblings_count = $("#table_titles tr[title_num^='"+first_num+"-']").length;
            var new_num = first_num+'-'+String(siblings_count+1); //编辑行的title_num
            var new_tr = template.compile(pt_tpm['title_opt_modify_title.tpm.html'])({title_num:new_num, title:obj.text(), title_traffic_score:obj.data('title_traffic_score')});
            title_tr.after(new_tr);
            check_title_length2(obj.text());
            $("#table_titles tr.modifying input").unbind('keyup');
            $("#table_titles tr.modifying input").keyup(function(){
                check_title_length2($(this).val());
            });
        }
    }

    var get_title_traffic_score = function (title,title_num,title_elemword_list) {
        PT.show_loading('亲，正在加载统计数据');
        $("#table_titles>tbody>tr:not([title_num])").remove();// 删除点开的引流能力列表
        PT.sendDajax({'function':'web_get_title_traffic_score','title':title,'title_num':title_num,'title_elemword_list':title_elemword_list,'item_id':item_id});
    }

    var submit_title = function (title, title_num) {
        PT.sendDajax({'function':'web_update_item', 'title':title, 'item_id':item_id, 'title_num':title_num});
    }

    var set_current_title = function (new_title, title_num) {
        $("#item_title").val(new_title);
        // $(".current_title").click(function(){
        //     var title = $(this).parentsUntil('tr').parent().find('span.title').text(),title_num=$(this).parents('tr').attr('title_num');
        //     submit_title(title,title_num);
        // });
        $(".current_title").html('提交').addClass('btn btn-mini submit_title').removeClass('current_title');
        var btn_current_title = $("#table_titles [title_num='" + title_num + "'] .submit_title");
        btn_current_title.html('当前标题');
        btn_current_title.unbind('click');
        btn_current_title.addClass('current_title').removeClass('btn btn-mini');
        PT.alert("提交成功");
    }

    //计算字符串的字节长度
    var bytes_len = function(str){
        var bytes_length = 0;
        for(var i=0;i<str.length;i++){
            if(str.charCodeAt(i)>255){
                bytes_length+=2;
            }else{
                bytes_length+=1;
            }
        }
        return bytes_length;
    }

    //检查标题是否重复
    var is_duplicate_title = function (title){
        var title_list = $("#table_titles").data("title_list")||[];
        for(var i in title_list){
            if(title.toLocaleLowerCase()==title_list[i].toLocaleLowerCase()){
                return true;
            }
        }
        return false;
    }

    var show_title_elemword = function (title_elemword_list){
        // $("#div_elemword :checkbox").val(title_elemword_list);
        // $("#div_elemword :checkbox").parent().removeClass("checked");
        // $("#div_elemword :checkbox").parents("label").removeClass("active");
        // $("#div_elemword :checked").parent().addClass("checked");
        // $("#div_elemword :checked").parents("label").addClass("active");
        $('#div_elemword li').removeClass('select');
        for (var i = title_elemword_list.length - 1; i >= 0; i--) {
            $('#div_elemword li a[value="'+title_elemword_list[i]+'"]').parent().addClass('select')
        };

        check_prdtword_count();
        var obj = $("#div_preview_title ul");
        obj.empty();
        for(var i=0;i<title_elemword_list.length;i++){
            obj.append("<li text='"+title_elemword_list[i]+"'>"+title_elemword_list[i]+"</li>");
        }
        obj.sortable({axis:'x', containment:'parent'});
        obj.disableSelection();
    }

    var show_title_kw = function (title_num,kw_list){
        var table=$('#table_titles tr[title_num="'+title_num+'"]').after(pt_tpm['title_traffic_detil_tr.tpm.html']);

        table.next().find('table').dataTable({
            'aaData':kw_list,
            'aoColumns':[
                {"sTitle":"<div>关键词</div>"},
                {"sTitle":"<div>搜索指数</div>"},
                {"sTitle":"<div>竞争度</div>"},
                {"sTitle":"<div>引流能力</div>"}
            ],
            'aaSorting':[[3,'desc']],
            'bDestroy':true,
            'bFilter':false,
            'bLengthChange':false,
//          'bScrollCollapse':true,
//          'sScrollY':'200px',
            'bInfo':false,
            'bPaginate':false,
            'sDom':'',
            'oLanguage':{
                'sInfo':'总共_TOTAL_条记录',
                'sInfoEmpty':'',
                'sEmptyTable':'亲，没有找到匹配的关键词'}
        });
//      $("#table_keywords").parents('.dataTables_scroll').next().children(":eq(1)").remove();
        // var title_traffic_score = 0;
        // if(sum_flag){
        //     for(var i=0;i<kw_list.length;i++){
        //         title_traffic_score += kw_list[i][3];
        //     }
        // }
        // PT.hide_loading();
        // return title_traffic_score.toFixed(2);
    }

    var get_traffic_score = function(kw_list){
        var title_traffic_score = 0;
        for(var i=0;i<kw_list.length;i++){
            title_traffic_score += kw_list[i][3];
        }
        return title_traffic_score.toFixed(2);
    }

    var show_title_traffic_score = function (title, title_num, kw_list, title_elemword_list){
        var title_traffic_score=get_traffic_score(kw_list);
        $('#table_titles').dataTable({
            'bDestroy': true,
            'bPaginate': false,
            'bFilter': false,
            "aoColumns": [{
                "bSortable": false
            },{
                "bSortable": false
            },{
                "bSortable": true,
                "sSortDataType": "dom-text",
                "sType": "numeric"
            },{
                "bSortable": false
            }],
            'oLanguage': {
                'sInfo': ''
            }
        });

        $('#table_titles tr[title_num="'+title_num+'"] .title_traffic_score').html(title_traffic_score); // 标题列表显示引流指数
        var title_span=$('#table_titles tr[title_num="'+title_num+'"] span.title');

        //show_title_kw(title_num,kw_list);
        title_span.data('kw_list',kw_list);
        title_span.data('title_traffic_score',title_traffic_score);
        if(title_elemword_list.length>0){
            title_span.data('title_elemword_list',title_elemword_list);
        }
        var title_list = $("#table_titles").data("title_list")||[];
        title_list.push(title);
        $("#table_titles").data("title_list",title_list);

        //首次打开页面时生成系统推荐标题
        if (title_num=='0') {
	        PT.show_loading('正在生成系统推荐标题');
	        PT.sendDajax({'function':'web_generate_rec_title','item_id':item_id});
        }
    }

    var clear_title = function (){
        //$(":checkbox").val([]);
        $("#div_elemword li.select").removeClass("select");
        // $("#div_elemword label.active").removeClass("active");
        $("#div_preview_title ul").empty();
        check_title_length();
    }

    return {
        init: init,
        show_title_traffic_score: show_title_traffic_score,
        get_item_convword_callback: function(convword_list){
            if (convword_list.length > 0) {
                var html_convword = template.render('html_convword', {convword_list:convword_list});
            }
            $("#div_convword").html(html_convword);
            $("#div_elemword li").click(function(){
                    click_elemword($(this));
            });
            //App.initUniform();
        },
        set_current_title: set_current_title,
        generate_rec_title_callback: function (rec_title, title_elemword_list) {
            var title_tr = template.compile(pt_tpm['title_opt_title.tpm.html'])({title_num:1, title:rec_title});
            $("#table_titles>tbody").append(title_tr);
            $("#table_titles tr[title_num='1'] span.title").data("title_elemword_list",title_elemword_list);
            $("#table_titles tr[title_num='1'] i.popovers:eq(0)").popover();
            get_title_traffic_score(rec_title, 1, title_elemword_list);
        }
    }
}();
