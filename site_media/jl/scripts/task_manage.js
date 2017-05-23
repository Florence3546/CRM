PT.namespace('TaskManage');
PT.TaskManage = function () {

	var now_table = null, old_table = null;
	
	var init_dom=function(){
	
		$("#now_task_li").click( function() {
			now_table.fnDestroy();
			PT.sendDajax({'function':"kwlib_get_task_obj"});
		});
		
		$(document).on('click',".delete_task", function() {
            PT.confirm('您确认删除该任务？',delete_task,[this]);
		});
	
		$("#now_task_table").on('click','a.switch_task_status', function() {
            PT.show_loading('正在切换任务');
            var n_row = $(this).parents('tr').eq(0),
            	task_id = $('.task_id',n_row).text(),
            	oper_type = ($(this).text()=='暂停'?0:1);
			PT.sendDajax({'function':'kwlib_switch_oper_status','task_id':task_id,'oper_type':oper_type});
		});
		
		$("#new_task_table").on('click','a.creat_task', function() {
			var task_type_id = $(this).parents("tr").attr("id");
			PT.sendDajax({'function':'kwlib_creat_task','task_type_id':task_type_id});
		});
		
	}

	var delete_task=function(obj) {
		var n_row = $(obj).parents('tr').eq(0),
			task_id = $('.task_id',n_row).text();
		PT.sendDajax({'function':'kwlib_delete_task','task_id':task_id});
	}

	var init_now_table=function() {
		now_table = $('#now_task_table').dataTable({
			"iDisplayLength": 30,
			"bPaginate" : false,
			"bLengthChange": false,
			"bDeferRender": true,
			"bAutoWidth":false,
			"aaSorting": [[0, 'desc']],
			"aoColumns": [
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": false}
			],
			"sPaginationType": "bootstrap",
			"sDom": "<'row-fluid'r>t",
			"oLanguage": {
					"sZeroRecords" : "没有您要搜索的内容", 
					"sEmptyTable":"没有数据",
					"sInfoEmpty": "显示0条记录"
			}
    });
	}
	
	var init_old_table=function() {
		old_table = $('#old_task_table').dataTable({
			"aLengthMenu": [[20, 30, 50],[20, 30, 50]],
			"iDisplayLength": 20,
            "bPaginate" : true,
            "bLengthChange": true,
            "bDeferRender": true,
            "bAutoWidth":false,
            "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>",
            "sPaginationType": "bootstrap",
            "oLanguage": {
                "sInfo":"正在显示第_START_-_END_条信息，共_TOTAL_条信息 ",
                "sZeroRecords" : "没有您要搜索的内容", 
                "sEmptyTable":"没有数据",
                "sInfoEmpty": "显示0条记录",
                "sInfoFiltered" : "(全部记录数 _MAX_ 条)",
                "sSearch":"搜索",
                "sLengthMenu": "_MENU_ 条记录/页",
                "oPaginate": {
                    "sFirst" : "第一页",
                    "sPrevious": "上一页",
                    "sNext": "下一页",
                    "sLast" : "最后一页"
                }
            }
        });
	}
	
    return {
        init:function(){
            var upload_flag=$('#upload_flag').val();
            switch(upload_flag){
                case 'type_error':
                    PT.alert('上传失败：上传文件只能为TXT文件','red');
                    break;
                case 'size_error':
                    PT.alert('上传失败：上传文件不能超过5M','red');
                    break;
                case 'success':
                    PT.alert('上传成功，创建任务成功','red');
                    break;
                case 'task_error':
                    PT.alert('上传成功，创建任务失败','red');
                    break;
            }
    		PT.sendDajax({'function':"kwlib_get_task_obj"});
    		init_old_table();
    		init_dom();
    		App.initTooltips();
    	},
    	
    	renow_task_table:function(data) {
			var temp_str='';
			for (var i=0;i<data.length;i++){
				temp_str += template.render('now_table_tr', data[i]);
			}
			$('#now_table_body').html(temp_str);
			init_now_table();
		},
		
		switch_status_back:function(result,oper_type,task_id){
			PT.hide_loading();
			switch(result) {
				case -1:
					PT.alert('该任务已经结束了');
					break;
				case 0:
					PT.alert((oper_type?'启动':'暂停')+'任务失败!,请刷新页面重试');
					break;
				case 1:
					$('#'+task_id).find('.switch_task_status').text((oper_type?'暂停':'启动'));
					$('#'+task_id).find('.delete_task').toggleClass('hide');
					$('#'+task_id).find('.task_status').text(oper_type?'running':'stop');
			}
		},
		
    	creat_task_back:function(result,task_type_id){
    		if (result) {
    			PT.alert('新建任务成功');
    			$('#'+task_type_id).find('a').addClass('disabled').removeClass('red creat_task');
    		} else {
    			PT.alert('新建任务失败','red');
    		}
    	},
    	
    	delete_task_back:function(result,task_id){
    		if (result) {
    			PT.alert('删除任务成功');
    			var temp_table=$('.tabbable>ul>li.active').attr('id').replace(/li/,'table');
    			$('#'+temp_table).dataTable().fnDeleteRow($('#'+task_id)[0]);
    		} else {
    			PT.alert('删除任务失败','red');
    		}
    	}
    }

}();