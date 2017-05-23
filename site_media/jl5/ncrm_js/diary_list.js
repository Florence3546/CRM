PT.namespace('DiaryList');
PT.DiaryList = function() {

	var editors=new Object();
	
	var init_sort=function(){
		
		$('#id_diary_list').dataTable({
		 	"bPaginate": false,
		 	"bFilter": false,
		 	"bInfo": false,
			"aaSorting": [[ 1, "desc" ]],
			"aoColumns": [
				{ "bSortable": true },
				{ "bSortable": true },
				{ "bSortable": true },
				{ "bSortable": true },
				{ "bSortable": true },
				{ "bSortable": false }
			]
		});
	};
	
	var init_editors = function(selector, value){
		require('pt/pt-editor-mini,node', function(editor, $) {
			var editor = new editor({
	            render: selector,
	            textareaAttrs: {name: $(selector).attr('id')},
	            height:'200px'
	        });
			editor.initData(value)
			editor.render();
			editors[selector] = editor;
		});
	}
	
	var kill_editors = function(diary_id, data_dict){
		$('#'+diary_id).find('.ks-editor').each(function(){
			$(this).remove();
		});
    	var obj_list = ['content', 'todolist'];
    	for(var i=0;i<obj_list.length;i++){
    		var obj_id = '#id_'+diary_id+ '_' + obj_list[i];
    		if(arguments[2]==undefined){
    			$(obj_id + ' .init_data').html(data_dict[obj_list[i]]);
    		}
    		$(obj_id + ' .init_data').removeClass('hide');
    		delete editors[obj_id];
    	}
    	$('#' + diary_id).find('a.save_diary').addClass('hide');
    	$('#' + diary_id).find('a.edit_diary').removeClass('hide');
	}
	
	var kill_comment_editor = function(diary_id, data_dict){
		$('#'+diary_id).find('.ks-editor').each(function(){
			$(this).remove();
		});
		var obj_id = '#id_'+diary_id+ '_comment';
		if(arguments[2]==undefined){
			template.isEscape = false;
			$(obj_id + ' .comment_data').html(template.render('id_comment_template', data_dict));
			template.isEscape = true;
		}
		$(obj_id + ' .comment_data').removeClass('hide');
		delete editors[obj_id];
    	$('#' + diary_id).find('a.save_comment').addClass('hide');
    	$('#' + diary_id).find('a.comment_diary').removeClass('hide');
	}
	
	
    var init_dom = function() {
    	init_sort();
   	
    	$('.show_more').click(function(){
    		var pos = parseInt($(this).attr('position'));
    		if(pos>0){
    			$(this).parent().removeClass('h160');
    			$(this).text('收起');
    			$(this).attr('position', -1);
    		}else{
    			$(this).parent().addClass('h160');
    			$(this).text('展开');
    			$(this).attr('position', 1);
    		}
    	});
    	
    	$('.add_diary').click(function(){
    		PT.sendDajax({'function':'ncrm_check_write_today', 'callback':'DiaryList.check_write_diary_callback'})
         });
    	
    	$(document).on('click.PT.edit_diary', '.edit_diary', function(){
    		var diary_id = $(this).parent().parent().attr('id');
    		var content_id = '#id_'+diary_id+'_content';
    		var todolist_id = '#id_'+diary_id+'_todolist';
    		if(editors.hasOwnProperty(content_id) || editors.hasOwnProperty(todolist_id)){
    			return false;
    		}else{
    			init_editors(content_id, $(content_id+' .init_data').html());
    			init_editors(todolist_id, $(todolist_id+' .init_data').html());
    			$(content_id+ ' .init_data').addClass('hide');
    			$(todolist_id+ ' .init_data').addClass('hide');
    		}
    		$(this).siblings('.save_diary').removeClass('hide');
    		$(this).addClass('hide');
    	});
    	
    	$(document).on('click.PT.save_diary', '.save_diary', function(){
    		var diary_id = $(this).parent().parent().attr('id');
    		var content_id = '#id_'+diary_id+'_content';
    		var todolist_id = '#id_'+diary_id+'_todolist';
    		var content = editors[content_id].value();
    		var todolist = editors[todolist_id].value();
			if(content == $(content_id+' .init_data').html() && todolist == $(todolist_id+' .init_data').html()){
				kill_editors(diary_id, {}, false);
				console.log("无更改哟！");
				return true;
			}else{
				if(content!='' && todolist!=''){
					PT.sendDajax({'function':'ncrm_save_diary', 'content':content, 'todolist':todolist, 'diary_id':diary_id, 'callback':'DiaryList.save_diary_callback'});
				}else{
                    PT.alert("不能为空哟亲");
					return false;
				}
			}
    	});
    	
    	$('.comment_diary').click(function(){
    		var diary_id = $(this).parent().parent().attr('id');
    		var comment_id = '#id_'+diary_id+'_comment';
    		if(editors.hasOwnProperty(comment_id)){
    			return false;
    		}else{
    			init_editors(comment_id, $(comment_id+' .init_data').html());
    			$(comment_id+' .comment_data').addClass('hide');
    		}
    		$(this).siblings('.save_comment').removeClass('hide');
    		$(this).addClass('hide');
    	});
    	
    	$('.save_comment').click(function(){
    		var diary_id = $(this).parent().parent().attr('id');
    		var comment_id = '#id_'+diary_id+'_comment';
    		var comment = editors[comment_id].value();
			if(comment == $(comment_id+' .init_data').html()){
				kill_comment_editor(diary_id, {}, false);
				console.log("无更改哟！");
				return true;
			}else{
				PT.sendDajax({'function':'ncrm_save_diary_comment', 'comment':comment, 'diary_id':diary_id, 'callback':'DiaryList.save_comment_callback'});
			}
    	});

    	require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
    		new Datetimepicker({
                start: '#id_start_date',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#id_end_date',
                timepicker: false,
                closeOnDateSelect : true
            });
        });
    };

    return {
        init: function() {
            init_dom();
        },
        check_write_diary_callback:function(has_written){
        	if(!has_written){
        		if($('#0').length>0){
        			return false;
        		}else{
        			$('#id_diary_list>tbody').prepend(template.render('id_diary_template', {}));
        			init_editors('#id_0_content', '');
        			init_editors('#id_0_todolist', '');
        		}
        	}else{
        		PT.alert("今天已经写过了哟亲！");
        		return false;
        	}
        },
        save_diary_callback: function(diary_id, data_dict, is_new){
        	kill_editors(diary_id, data_dict);
        	if(diary_id==0){//弄那么麻烦干嘛，直接刷新，反正一天也才一篇。
        		window.location.reload();
        	}
        },
        save_comment_callback:function (diary_id, data_dict){
        	kill_comment_editor(diary_id, data_dict);
        },
        editors:editors//方便调试
    }
}();
