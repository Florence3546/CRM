PT.namespace('CrmMaintenance');
PT.CrmMaintenance = function () {

	$('.fancybox_close').click(function(e){
		$.fancybox.close();
	});
	
	$('.opar_type').change(function(e){
		$('#opar_type_list .active').removeClass('active');
		var obj = $(this);
		obj.addClass('active');
		if (obj.val() == "all"){
			$('#opar_args').attr({disabled:"disabled"});
		} else {
			$('#opar_args').removeAttr("disabled");
		}
	});
	
	$('.build_type').change(function(e){
		$('#rebuild_type_list .active').removeClass('active');
		$(this).addClass('active');
	});
	
	$('.clean_trash').click(function(e){
		PT.confirm('您确定要去清理离职员工所分配的账户吗？',
						function(){
							PT.sendDajax({'function':'crm_clear_trash'});
						})
	});
	
	$('.exec_reset_shop').click(function(e){
		var opar_type = $('.active').val();
		var update_parms = $('#opar_args').val();
		var group_id = $('#group_id').val();
		var consult_id = $('#consult_id').val();
		
		alert(update_parms+' '+ group_id+' '+consult_id +' ');
		PT.sendDajax({'function':'crm_reset_assign_shop',"update_parms":update_parms,"opar_type":opar_type,"group_id":group_id,"consult_id":consult_id});
	});
	
	$('.exec_rebuild_keywords').click(function(e){
		var rebuild_args = $('#rebuild_args').val();
		if (rebuild_args == '' ){
			PT.alert('未输入任何操作参数。');
			return 
		}
		
		var obj = $('#rebuild_type_list .active');
		var desc = obj.attr('desc');
		var rebuild_type = obj.val();
		var rebuild_adg_type =$('#rebuild_adg_type').find('option:checked').val();
		
		PT.confirm('您确定遵照 '+desc+' 重建以下条件关键词吗？ 条件：'+rebuild_args,
							function(rebuild_type,rebuild_adg_type,rebuild_args){
								PT.show_loading("任务执行中");
								PT.sendDajax({'function':'crm_rebuild_keywords','rebuild_type':rebuild_type,'rebuild_adg_type':rebuild_adg_type,'rebuild_args':rebuild_args});
							},
							[rebuild_type,rebuild_adg_type,rebuild_args])
	});
	
	$('.refresh_cats').click(function(){
		PT.sendDajax({'function':'crm_refresh_cats_4group'});
	});
	
	$('.reassign').click(function(e){
		$.fancybox.open(
	     		[
	     			{
	     				href:'#reset_assign_shop',
	     				afterClose:function(){
	     				},
	     				padding:10
	     			}
	     		],
	     		{
			     	helpers:{
						 title : {type : 'outside'},
					     overlay : {closeClick: false}
		     		},
		     	}
	     );
	});

	$('.rebuild').click(function(e){
		$.fancybox.open(
	     		[
	     			{
	     				href:'#rebuild_keywords',
	     				afterClose:function(){
	     				},
	     				padding:10
	     			}
	     		],
	     		{
			     	helpers:{
						 title : {type : 'outside'},
					     overlay : {closeClick: false}
		     		},
		     	}
	     );
	});	
	
	$(".select_conf_manage").click(function(){
		var make_x = "icon-remove-sign";
		var make_ok = "icon-ok-sign";
		$("#change_conf_name").val("");
		$("#select_conf_flag i").removeClass(make_x);
		$("#select_conf_flag i").removeClass(make_ok);
		$.fancybox.open(
	     		[
	     			{
	     				href:'#select_conf_manage',
	     				afterClose:function(){
	     				},
	     				padding:10
	     			}
	     		],
	     		{
			     	helpers:{
						 title : {type : 'outside'},
					     overlay : {closeClick: false}
		     		},
		     	}
	     );
	});
	
	$("#change_conf_name").blur(function(){
		var conf_name = $("#change_conf_name").val();
		PT.sendDajax({"function":"crm_is_exist_conf","conf_name":conf_name});
	});
	
	$(".change_conf_type").click(function(){
		var conf_name = $("#change_conf_name").val();
		var conf_type = $("#conf_type option:checked").val();
		if(conf_name != undefined && conf_name != "" ){
			PT.sendDajax({"function":"crm_change_select_conf_type","conf_name":conf_name,"conf_type":conf_type})
		}  else {
			PT.alert("配置名称不能为空！");
		}
	});
	
	return {
		set_select_conf_flag:function(is_success){
			var make_x = "icon-remove-sign";
			var make_ok = "icon-ok-sign";
			var obj = $("#select_conf_flag i");
			if(is_success == 1){
				obj.addClass(make_ok);
				obj.removeClass(make_x);
			} else {
				obj.addClass(make_x);
				obj.removeClass(make_ok);
			}
		}	
	}
}()