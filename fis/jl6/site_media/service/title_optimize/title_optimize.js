/**
 * Created by Administrator on 2015/9/24.
 */
define(['require','../common/common',"template",'caret','tag_editor',
        'jl6/site_media/widget/alert/alert',
        'jl6/site_media/widget/ajax/ajax',
        'jl6/site_media/widget/lightMsg/lightMsg',
        'jl6/site_media/widget/loading/loading','dataTable', 'zclip'],
    function(require,common,template,caret,tagEditor,alert,ajax,lightMsg,loading,dataTable) {
    "use strict"

    var title_elemword_list = $('#title_word_str').length && $('#title_word_str').val().split(',');
    var adgroup_id = $('#adgroup_id').val();
    var item_id = $('#item_id').val();
    
    var refresh_residue = function () {
        var _width = 10;
        $('#title_input ul.tag-editor li').each(function () {
            _width += $(this).width();
        });
        $('#residue').css('left', _width);
    };
    
    var get_tags = function (obj) {
        return obj.tagEditor('getTags')[0].tags;
    };
    
    var get_tags_value = function (obj) {
        var value = '';
        var tags = get_tags(obj);
        for (var i in tags) {
            value += tags[i];
        }
        return value;
    };
    
    var remove_all_tags = function (obj) {
        obj.text('');
        var tags = get_tags(obj);
        for (var i in tags) {
            obj.tagEditor('removeTag', tags[i]);
        }
    };
    
    var show_title_box = function () {
        $("#select_title_box").height($(".title_box").height());
    };
    
    var hide_title_box = function () {
        $("#select_title_box").height(0);
    };

    var init = function(){
        getRemainLength($('#title_word_str').val().replace(new RegExp(/(,)/g),""));
        $('[data-toggle=tooltip]').tooltip();
        for (var i in title_elemword_list) {
            $('.title_box li a[value="'+title_elemword_list[i]+'"]').parent().addClass('select');
        }

        var options = {
            placeholder: '',
            initialTags:title_elemword_list,
            removeDuplicates: false,
            onChange:function (field, editor, tags) {
                $('#select_title_box ul.pt-tag>li').removeClass('select');
	            var value = '';
	            for (var i in tags) {
	                value += tags[i];
		            $('#select_title_box a[value="'+tags[i]+'"]').parent('li').addClass('select');
	            }
	            getRemainLength(value);
	            //refresh_residue();
            }
        }
        $('#adg_title').tagEditor(options);
        //refresh_residue();
        
        $('#title_input').on('keydown', '.tag-editor-tag input', function () {
            getRemainLength($('#adg_title').next('ul').find('.tag-editor-tag').text());
            //refresh_residue();
        });
        
        $('#title_input').focusin(function () {
            //refresh_residue();
            show_title_box();
        });
        
        $(document).click(function (e) {
            if ($(e.target).closest('#title_input').length==0 && $(e.target).closest("#table_titles td.title").length == 0) {
                hide_title_box();
                getRemainLength($('#adg_title').next('ul').find('.tag-editor-tag').text());
                //refresh_residue();
            }
        });

        //生成测试标题
        $("#btn_create_title").click(function(){
            //var new_title = titleEditor.getValue();
            var new_title = get_tags_value($('#adg_title'));
            if(new_title.length==0){
                alert.show('亲，标题不能为空');
                return;
            }else{
                if(bytes_len(new_title)>60){
                    alert.show("标题长度不能超过30个汉字");
                    return;
                }
                if(is_duplicate_title(new_title)){
                    alert.show("列表中已存在相同的标题");
                    return;
                }
            }
            var last_title_num = $("#table_titles tr[title_num]:last").attr("title_num");
            var title_num = String(Number(last_title_num)+1);

            var tpl=__inline("title_opt_title.html");
            var title_tr = template.compile(tpl)({title_num:title_num, title:new_title});
            $("#table_titles>tbody").append(title_tr);
            $("#table_titles tr[title_num='"+title_num+"'] span.title").data("title_elemword_list",get_tags($('#adg_title')));
            //$("#table_titles tr[title_num='"+title_num+"'] .popovers").popover();
            get_title_traffic_score(new_title, title_num, get_tags($('#adg_title')));
        });

        //复制标题

        $('#btn_copy_title').zclip({
            path: __uri('../../plugins/zclip/ZeroClipboard.swf'),
            copy: function() {
                var new_title = get_tags_value($('#adg_title'));
                if(new_title.trim().length==0){
                    return '';
                }
                return new_title;
            },
            afterCopy: function() {
                var new_title = get_tags_value($('#adg_title'));
                if(new_title.trim().length==0){
                    alert.show('亲，标题不能为空');
                }else{
                    lightMsg.show('标题已经复制到剪贴板！');
                }
            }
        });

        $("#table_titles").on("click","a.submit_title:not(.current_title)",function(){
            var title_tr = $(this).closest('tr');
            var title = title_tr.find('span.title').text();
            if(title==$("#item_title").html()){
                alert.show("与宝贝当前标题相同");
            }else{
                var title_num = title_tr.attr('title_num');
                submit_title(title, title_num);
            }
        });


        //清除输入框内容
        $('#remove_all_tags').click(function(){
            //titleEditor.removeAll();
            remove_all_tags($('#adg_title'));
            $('.pt-tag>li').removeClass('select');
        });

        //存储当前使用的标题
        $("#table_titles tr[title_num='0'] span.title").data("title_elemword_list",title_elemword_list);

        //获取引流数据
        get_title_traffic_score($("#item_title").html(), 0, title_elemword_list);

        $('.pt-tag>li').click(function(){
            if($(this).hasClass('select')){
                $(this).removeClass('select');
                //titleEditor.removeTag($(this).find('a').attr('value'));
                $('#adg_title').tagEditor('removeTag', $(this).text());
            }else{
                var new_title = get_tags_value($('#adg_title'));
                if (bytes_len(new_title)<=60) {
	                $(this).addClass('select')
	                //titleEditor.addTag($(this).find('a').attr('value'));
	                $('#adg_title').tagEditor('addTag', $(this).text());
                } else {
                    alert.show("标题长度不能超过30个汉字");
                }
            }
        });

        //编辑标题
        $(document).on('click','.edit_title',function(){
            //titleEditor.removeAll();
            remove_all_tags($('#adg_title'));

            //显示词根信息和关键词信息
            var elemword_list = $(this).prev('span.title').data('title_elemword_list');

            $('.title_box li').removeClass('select');
            for (var i in elemword_list) {
                //titleEditor.addTag(title_elemword_list[i]);
                $('.title_box li a[value="'+elemword_list[i]+'"]').parent().addClass('select');
                $('#adg_title').tagEditor('addTag', elemword_list[i]);
            }
            show_title_box();
        });

        //查看属性词
        $('#adgroup_property').on('click',function(){
            $('#adgroup_property_box').toggleClass('hide');
            $('.open-property').toggleClass('hide');
            $('.close-property').toggleClass('hide');
            $("#select_title_box").height($(".title_box").height());
        });

        //词根区布局调整
        $('#div_prmtword, #div_dcrtword, #div_propword, #div_prdtword').each(function(){
            if($(this).find('li').length>14){
                //$(this).find('ul').append('<button type="button" class="btn mini yellow btn_more">更多</button>');
                $(this).find('li:last').after('<a href="javascript:;"><i class="iconfont ml5 open-more b">&#xe605;</i><i class="iconfont ml5 hide close-more b">&#xe604;</i></a>');
                //$(this).find('li:gt(13)').hide();
            }
        });

        //显示所有词
        $(document).on('click','.open-more',function(){
            $(this).toggleClass('hide');
            var obj = $(this).siblings();
            obj.toggleClass('hide');
            $(this).parent().siblings().animate({opacity:'show'}, 'normal');
            $("#select_title_box").height($(".title_box").height());
        });

        //隐藏部分词
        $(document).on('click','.close-more',function(){
            $(this).toggleClass('hide');
            var obj = $(this).siblings();
            obj.toggleClass('hide');
            $(this).parent().siblings('li:gt(13)').animate({opacity:'hide'}, 'fast',function(){
                $("#select_title_box").height($(".title_box").height());
            });
        });

        //展开/隐藏引流数据
       $("#table_titles").on('click','.icon-add',function(){
            var title_num,kw_list,title_tr = $(this).closest('tr');
            title_num = title_tr.attr('title_num');
            kw_list=title_tr.find('span.title').data('kw_list');
            show_title_kw(title_num,eval("("+kw_list+")"));
           $(this).toggleClass('hide');
           $(this).siblings('i').toggleClass('hide');
       });

        //隐藏引流数据
        $("#table_titles").on('click','.icon-del',function(){
            var title_tr = $(this).closest('tr');
            title_tr.next().remove();
            $(this).toggleClass('hide');
            $(this).siblings('i').toggleClass('hide');
        });
    };

    //提交标题
    var submit_title = function (title, title_num) {
        ajax.ajax('update_item',{
            'title':title,
            'item_id':item_id,
            'adgroup_id':$('#adgroup_id').val(),
            'campaign_id':$('#campaign_id').val(),
            'title_num':title_num
        },set_current_title);
    }

    var set_current_title = function (data) {
        $("#item_title").html(data.title);
        $(".current_title").html('提交').addClass('btn submit_title btn-primary btn-sm').removeClass('current_title');
        var btn_current_title = $("#table_titles [title_num='" + data.title_num + "'] .submit_title");
        btn_current_title.html('当前标题');
        btn_current_title.unbind('click');
        btn_current_title.addClass('current_title').removeClass('btn submit_title btn-primary btn-sm');
        alert.show("提交成功");
    }

    //检查标题是否重复
    var is_duplicate_title = function (title){

        var title_list = $("#table_titles").find('.adg_title');

        for(var i=0; i<title_list.length;i++){
            if(title==$(title_list[i]).text()){
                return true;
            }
        }
        return false;
    }

    //计算字符串的字节长度
    var bytes_len = function (str) {
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

    //校验输入的字数
    var getRemainLength = function(title){
        var remain_char_count = Math.floor(30-bytes_len(title)/2);

        if(remain_char_count>=0){
            $("#remain_char_prompt").parent().removeClass('red');
            $("#remain_char_prompt").html("还可输入");
            $("#remain_char_count").html(remain_char_count);
        }else{
            $("#remain_char_prompt").parent().addClass('red');
            $("#remain_char_prompt").html("已超过");
            $("#remain_char_count").html(Math.abs(remain_char_count));
        }

        return remain_char_count;
    }

    //获取引流指数
    var get_title_traffic_score = function (title,title_num,title_elemword_list, is_rec_title) {
        loading.show('正在统计引流指数');
        $("#table_titles>tbody>tr:not([title_num])").remove();// 删除点开的引流能力列表
        ajax.ajax('get_title_traffic_score',{'title':title,'title_num':title_num,'title_elemword_list':title_elemword_list,'item_id':item_id,'is_rec_title':is_rec_title || 0}, show_title_traffic_score);
        hide_title_box();
    }

   //计算引流能力
    var get_traffic_score = function(kw_list){
        kw_list = eval ("(" + kw_list + ")");
        var title_traffic_score = 0;
        for(var i=0;i<kw_list.length;i++){
            title_traffic_score += kw_list[i][3];
        }
        return title_traffic_score.toFixed(2);
    }

    //获取引流指数回调函数
    var show_title_traffic_score = function (data){
        loading.hide();
        var resultData = data.data;
        var title_traffic_score = Number(get_traffic_score(resultData.kw_list));
        var origin_score = Number($('#table_titles tr[title_num=0] .title_traffic_score').html());
        if (resultData.is_rec_title && title_traffic_score<origin_score) {
            $('#table_titles tr[title_num="'+resultData.title_num+'"]').remove();
            return;
        } else {
            $('#table_titles tr[title_num="'+resultData.title_num+'"]').removeClass('hidden');
        }

        $('#table_titles tr[title_num="'+resultData.title_num+'"] .title_traffic_score').html(title_traffic_score); // 标题列表显示引流指数
        var title_span=$('#table_titles tr[title_num="'+resultData.title_num+'"] span.title');

        title_span.data('kw_list',resultData.kw_list);
        title_span.data('title_traffic_score',title_traffic_score);

        var title_list = $("#table_titles").data("title_list")||[];
        title_list.push(resultData.title);
        $("#table_titles").data("title_list",resultData.title_list);

        //首次打开页面时生成系统推荐标题
        if (resultData.title_num=='0') {
            loading.show('正在生成系统推荐标题');
            ajax.ajax('generate_rec_title',{'item_id':item_id},generate_rec_title_back);
        }
    };

    //获取系统推荐标题的回调函数
    var generate_rec_title_back = function(data) {
        loading.hide();
        var tpl=__inline("title_opt_title.html");
        var title_tr = template.compile(tpl)({title_num:1, title:data.rec_title, extra_class:'rec_title'});
        $("#table_titles>tbody").append(title_tr);
        $("#table_titles tr[title_num='1'] span.title").data("title_elemword_list",eval('('+data.title_elemword_list+')'));
        //$("#table_titles tr[title_num='1'] .popovers").popover();
        get_title_traffic_score(data.rec_title, 1, data.title_elemword_list, 1);
        $('[data-toggle=tooltip]').tooltip();
    };

    //展开引流列表
    var show_title_kw = function (title_num,kw_list){
        var tpl=__inline("title_traffic_detil_tr.html");
        var table_html = template.compile(tpl)();
        var table=$('#table_titles tr[title_num="'+title_num+'"]').after(table_html);

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
    }

    return {
        init:function(){
            init();
        }
    }
});
