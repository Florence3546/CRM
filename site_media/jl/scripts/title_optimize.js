PT.namespace('TitleOptimize');
PT.TitleOptimize = function(){
    var title_elemword_list = $('#title_word_str').val().split(',');
	var adgroup_id = $('#adgroup_id').val();
	var item_id = $('#item_id').val();
	var update_convwrod_flag = $('#update_convwrod_flag').val();
    var init = function() {
    	//PT.aks.start();

		$('ul.main.nav>li').eq(3).addClass('active');
        //词根区布局调整
        $('#div_prmtword, #div_dcrtword, #div_propword, #div_prdtword').each(function(){
            if($(this).find('li').length>14){
                //$(this).find('ul').append('<button type="button" class="btn mini yellow btn_more">更多</button>');
                $(this).find('li:last').after('<button type="button" class="btn mini yellow btn_more">更多</button>');
                $(this).find('li:gt(13)').hide();
            }
        });
        $('html').on('click', '.btn_more', function(){
            $(this).siblings('li').animate({opacity:'show'}, 'normal');
            $(this).html('收起');
            $(this).removeClass('btn_more');
            $(this).addClass('btn_collapse');
        });
        $('html').on('click', '.btn_collapse', function(){
            $(this).siblings('li:gt(13)').animate({opacity:'hide'}, 'fast');
            $(this).html('更多');
            $(this).removeClass('btn_collapse');
            $(this).addClass('btn_more');
        });

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
//	    $("#div_elemword :checkbox").click(function(){click_elemword($(this));});
//	    $("#table_titles").on('click','span.title',function(){modify_title($(this));});

        // 选词区词根悬停事件，为避免样式BUG分开写
        $('#div_elemword').on('mouseenter','li',function(){
            $('#div_elemword li').removeClass('selected_elemword');
            $('#div_preview_title li').removeClass('selected_elemword');
            $('#div_preview_title .icon-remove-sign').remove();
            var word = $(this).find('input').val();
            var preview_obj = $('#div_preview_title li[text="'+word+'"]');
            $(this).addClass('selected_elemword');
            //$(this).find('i').triggerHandler('mouseenter');
            preview_obj.addClass('selected_elemword');
            var remove_sign = preview_obj.find('.icon-remove-sign');
            if(!remove_sign.length){
                preview_obj.append('<i class="icon-remove-sign"></i>');
            }
        });

        $('#div_elemword').on('mouseleave','li',function(){
            var word = $(this).find('input').val();
            var preview_obj = $('#div_preview_title li[text="'+word+'"]');
            $(this).removeClass('selected_elemword');
            //$(this).find('i').triggerHandler('mouseleave');
            preview_obj.removeClass('selected_elemword');
            var remove_sign = preview_obj.find('.icon-remove-sign');
            if(remove_sign.length){
                remove_sign.remove();
            }
        });

        $('#div_preview_title').on('mouseenter mouseleave','li:not(#preview_title_prompt)',function(){
            var word = $(this).text();
            $('#div_elemword li:has(input[value="'+word+'"])').show();
            $('#div_elemword li:has(input[value="'+word+'"])').toggleClass('selected_elemword');
            $(this).toggleClass('selected_elemword');
	        var remove_sign = $(this).find('.icon-remove-sign');
	        if(remove_sign.length){
	            remove_sign.remove();
	        }else{
	            $(this).append('<i class="icon-remove-sign"></i>');
	        }
        });

        $('#div_preview_title').on('click','.icon-remove-sign',function(){
            var word = $(this).closest('li').text();
            var obj = $('#div_elemword li:has(input[value="'+word+'"])');
            obj.removeClass('selected_elemword');
            $(this).closest('li').remove();
            obj.find('input').click();
        });

	    $("#table_titles").on('click', 'span.title', function(){
	        $("#table_titles span.title").removeClass("r_color");
	        $(this).addClass("r_color");
	        //显示词根信息和关键词信息
	        show_title_elemword($(this).data('title_elemword_list')||[]);
	        show_title_kw($(this).data('kw_list'), false);
	        $('#sum_traffic_score td').html($(this).data('title_traffic_score'));
	    });
	    $("#table_titles").on('click', '.edit_title', function(){
	       var obj = $(this).prev();
	       modify_title(obj);
	    });
	    $("#table_titles").on('click','a.get_title_traffic_score',function(){
	        var title_tr = $(this).closest("tr");
	        var title_input = title_tr.find("input");
	        var title = title_input.val()||title_tr.find('span.title').text();
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
	        title_input.closest('td').replaceWith('<td data-title="参考标题"><span class="title">'+title+'</span><i class="icon-pencil pointer marl_3 edit_title"></i></td>');
	        var title_num = title_tr.attr("title_num");
	        get_title_traffic_score(title,title_num,[]);
	        $(this).replaceWith('<a href="javascript:void(0);" class="submit_title btn red mini">提交</a>');
	        title_tr.removeClass("modifying");
            $("#table_titles span.title").removeClass("r_color");
	        title_tr.find("span.title").addClass("r_color");
//	        title_tr.prev().find("span.title").removeClass("r_color");
	        var first_num = title_num.split('-')[0];
	        $("#table_titles tr[title_num^='"+first_num+"-']:last").after(title_tr); // 修改过的标题按编号排序
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

        check_title_length();
//        App.initUniform();
		init_help();
    }

    //按照模板【品牌 + 年份 + 促销词 + (修饰词 + 属性词 + 产品词) * n + 转化词】对标题词根进行排序
    var sort_title = function(){
        var objs = $("#div_preview_title li");
        for(var i=0;i<objs.length;i++){
            var word_type = objs.eq(i).attr("type");
            if(!word_type){
                word_type = $("#div_elemword :checkbox[value='"+objs.eq(i).html()+"']").attr("name");
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
        if(remain_char_count>=0){
            $("#remain_char_prompt").html("你还可勾选");
            $("#remain_char_count").html(remain_char_count);
        }else{
            $("#remain_char_prompt").html("你已超过");
            $("#remain_char_count").html(Math.abs(remain_char_count));
        }
        if(title.length==0){
            $("#div_preview_title ul").html('<li id="preview_title_prompt">勾选词根后此组合框会自动组合标题</li>');
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
        if($("#div_prdtword :checked").length>3){
            $("#prdtword_warning").css("display","inline-block");
	        if(!App.isIE8() && $().pulsate){
                $("#prdtword_warning").pulsate("destroy");
	            $("#prdtword_warning").pulsate({color:"#ff8a3b"});
	        }
        }else{
            if(!App.isIE8() && $().pulsate){
                $("#prdtword_warning").pulsate("destroy");
            }
            $("#prdtword_warning").hide();
        }
    }

    var click_elemword = function(obj){
        if($("#preview_title_prompt").length!=0){
            $("#preview_title_prompt").remove();
        }
        check_prdtword_count();
        var value = obj.val();
        if(obj[0].checked){
            obj.parents("label").addClass("active");
            $("#div_preview_title ul").append("<li text='"+value+"' type='"+obj.attr('name')+"' class='selected_elemword'>"+value+"<i class='icon-remove-sign'></i></li>");
        }else{
            obj.parents("label").removeClass("active");
            $("#div_preview_title li[text='"+value+"']").remove();
        }
        sort_title();
        check_title_length();
    }

    var create_title = function(){
        if($("#preview_title_prompt").length!=0){
            PT.alert("请先勾选词根");
        }else{
            var new_title = $("#div_preview_title li").text();
            var title_elemword_list = $.map($("#div_preview_title li"), function(obj){return $(obj).text();});
            if(is_duplicate_title(new_title)){
                PT.alert("列表中已存在相同的标题");
                return;
            }else if(bytes_len(new_title)>60){
                PT.alert("标题长度不能超过30个汉字");
                return;
            }
            var last_title_num = $("#table_titles tr:last").attr("title_num").split('-')[0];
            var title_num = String(Number(last_title_num)+1);
            var title_tr = template.render('html_title_tr', {title_num:title_num,title:new_title});
            $("#table_titles").append(title_tr);
            $("#table_titles tr.modifying").remove();
            $("#table_titles span.title").removeClass("r_color");
            var title_obj = $("#table_titles tr[title_num='"+title_num+"'] span.title");
            title_obj.data("title_elemword_list",title_elemword_list);
            title_obj.addClass("r_color");
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
            var new_tr = template.render('html_modify_title_tr',{title_num:new_num, title:obj.text(), title_traffic_score:obj.data('title_traffic_score')});
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
        PT.sendDajax({'function':'web_get_title_traffic_score','title':title,'title_num':title_num,'title_elemword_list':title_elemword_list,'item_id':item_id});
    }

    var submit_title = function (title, title_num) {
	    PT.sendDajax({'function':'web_update_item', 'title':title, 'item_id':item_id, 'title_num':title_num});
	}

	var set_current_title = function (new_title, title_num) {
	    $("#item_title").val(new_title);
	    $(".current_title").click(function(){
	        var title = $(this).parentsUntil('tr').parent().find('span.title').text();
	        submit_title(title);
	    });
	    $(".current_title").html('提交');
	    $(".current_title").addClass('red');
	    $(".current_title").removeClass('current_title green');
	    var btn_current_title = $("#table_titles [title_num='" + title_num + "'] .submit_title");
	    btn_current_title.html('当前标题');
	    btn_current_title.unbind('click');
	    btn_current_title.addClass('current_title green');
	    btn_current_title.removeClass('red');
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
	        if(title==title_list[i]){
	            return true;
	        }
	    }
	    return false;
	}

	var show_title_elemword = function (title_elemword_list){
	    $("#div_elemword :checkbox").val(title_elemword_list);
	    $("#div_elemword :checkbox").parent().removeClass("checked");
	    $("#div_elemword :checkbox").parents("label").removeClass("active");
	    $("#div_elemword :checked").parent().addClass("checked");
	    $("#div_elemword :checked").parents("label").addClass("active");
	    check_prdtword_count();
	    var obj = $("#div_preview_title ul");
	    obj.empty();
	    for(var i=0;i<title_elemword_list.length;i++){
	        obj.append("<li text='"+title_elemword_list[i]+"'>"+title_elemword_list[i]+"</li>");
	    }
	    obj.sortable({axis:'x', containment:'parent'});
	    obj.disableSelection();
	}

	var show_title_kw = function (kw_list,sum_flag){
	    $("#table_keywords").dataTable({
	        'aaData':kw_list,
	        'aoColumns':[
	            {"sTitle":"关键词"},
	            {"sTitle":"搜索指数"},
	            {"sTitle":"竞争度"},
	            {"sTitle":"引流能力"}
	        ],
	        'aaSorting':[[3,'desc']],
	        'bDestroy':true,
	        'bFilter':false,
	        'bLengthChange':false,
//	        'bScrollCollapse':true,
//	        'sScrollY':'200px',
	        'bPaginate':false,
	        'oLanguage':{
	            'sInfo':'总共_TOTAL_条记录',
	            'sInfoEmpty':'',
                'sEmptyTable':'亲，没有找到匹配的关键词'}
	    });
//	    $("#table_keywords").parents('.dataTables_scroll').next().children(":eq(1)").remove();
	    var title_traffic_score = 0;
	    if(sum_flag){
	        for(var i=0;i<kw_list.length;i++){
	            title_traffic_score += kw_list[i][3];
	        }
	    }
	    PT.hide_loading();
	    return title_traffic_score.toFixed(2);
	}

	var show_title_traffic_score = function (title, title_num, kw_list, title_elemword_list){
	    var title_traffic_score=show_title_kw(kw_list, true);
	    $('#table_titles tr[title_num="'+title_num+'"] td.title_traffic_score').html(title_traffic_score); // 标题列表显示引流指数
        $('#table_titles').dataTable({'bDestroy':true,'bPaginate':false,'bFilter':false,'oLanguage':{'sInfo':''}});
        $('#table_titles').next().remove();
	    var title_span=$('#table_titles tr[title_num="'+title_num+'"] span.title');
	    title_span.data('kw_list',kw_list);
	    title_span.data('title_traffic_score',title_traffic_score);
	    if(title_elemword_list.length>0){
	        title_span.data('title_elemword_list',title_elemword_list);
	    }
	    var title_list = $("#table_titles").data("title_list")||[];
	    title_list.push(title);
	    $("#table_titles").data("title_list",title_list);
	}

	var clear_title = function (){
	    $(":checkbox").val([]);
	    $("#div_elemword span.checked").removeClass("checked");
	    $("#div_elemword label.active").removeClass("active");
	    $("#div_preview_title ul").empty();
	    check_title_length();
	}

	var init_help=function(){
		if(!$.browser.webkit&&$.browser.msie&&Number($.browser.version)<7){
			return;
		}
		var content1 = "<ul style='list-style-type:lower-alpha;'><li>您可以在选词区里的每类词中勾选中一批关键词在标题组合框中组合标题，促销词选一个就行，产品词不得超过3个</li>";
		content1 += "<li>带感叹号标记的促销词和品牌词在勾选前请务必留意标记上的提示信息</li>";
		content1 += "<li>修饰词、属性词、产品词和直通车转化词这四类词都已按热度排序，位置越靠前的越好，但也须您自行判断是否合适该宝贝</li>";
		content1 += "<li>当前标题所包含的关键词会被默认选中</li></ul>";

        var content2 = "<ul style='list-style-type:lower-alpha;'><li>鼠标点中标题组合框中的关键词左右拖动可以调整它在标题中的位置</li>";
        content2 += "<li>鼠标移动到关键词上后，右上角会出现删除图标，点击可以删除该关键词</li>";
        content2 += "<li>调整完毕后，点击【生成测试标题】按钮，会在测试标题列表中显示出该标题的引流能力</li></ul>";

        var content3 = "<ul style='list-style-type:lower-alpha;'><li>列表中会列举出当前已经生成的多个测试标题及其引流能力，一般情况下引流能力越高越好</li>";
        content3 += "<li>点击表中的标题会同时更新上方的选词区、标题组合框和下方的关键词分析列表</li>";
        content3 += "<li>点击标题后面的编辑图标，可以在输入框中手动编辑该标题，点击【分析流量】按钮获取编辑后的引流能力</li>";
        content3 += "<li>选好标题后，点【提交】按钮就可以在淘宝上同步修改</li></ul>";

        var content4 = "<ul style='list-style-type:lower-alpha;'><li>列表中会列举出与被点中标题相匹配的有效的关键词组合，并按关键词的引流能力排序</li>";
        content4 += "<li>表中所有关键词组合的引流能力之和即为标题的引流能力</li>";
        content4 += "<li>分析不同标题间的关键词组合数据可以帮您筛选出较好的关键词</li></ul>";

		var help_list=[
			{
				element: "#div_elemword",
				content: "1/5 勾选每类关键词中位置靠前并且适合宝贝的关键词，请留意带感叹号标记的词，当前标题中的词已经被选中",
				placement:'top'
//				,onShown:function(tour){
//				    var temp_top = $('#div_elemword').offset().top - $('#step-0').outerHeight();
//				    $(window).scrollTop(temp_top);
//				}
			},
            {
                element: "#update_elemword",
                content: "2/5 点击后会立即更新选词区中的关键词，系统默认3天自动更新一次",
                placement:'top'
            },
//            {
//                element: "#manage_elemword",
//                content: "点击进入词根管理页面，可以手动配置选词区中的产品词和修饰词",
//                placement:'top'
//            },
			{
				element: "#div_preview_title",
				content: "3/5 鼠标拖动关键词调整它在标题中的位置，或者点击删除图标删掉关键词，调完后点击【生成测试标题】获取引流能力",
				placement:'top'
			},
			{
				element: "#div_titles",
				content: "4/5 点击标题后的编辑图标可以手动修改标题，引流能力越高越好，选好后点【提交】就可以在淘宝上同步修改",
				placement:'top'
			},
			{
				element: "#div_keywords",
				content: "5/5 引流能力是基于这些关键词分析数据计算出来的，比较不同标题的关键词数据可以帮您筛选出较好的关键词",
				placement:'top'
			}
		];
		PT.help(help_list);
	}

	return {
	    init: init,
	    show_title_traffic_score: show_title_traffic_score,
	    get_item_convword_callback: function(convword_list){
	        if (convword_list.length > 0) {
	            var html_convword = template.render('html_convword', {convword_list:convword_list});
	        } else {
	            var html_convword = '<div class="pad5">暂无数据</div>';
	        }
	        $("#div_convword").html(html_convword);
	        $("#div_elemword :checkbox").click(function(){click_elemword($(this));});
	        App.initUniform();
	    },
	    set_current_title: set_current_title
	}
}();
