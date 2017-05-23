PT.namespace('CRMCategoryList');
PT.CRMCategoryList = function () {
	var init_system_event = function(){
		// 搜索模块 INPUT 事件
		$("#search_model .category_group").click(function(){
			var title = $(this).attr("default_title");
			var input_list = $("#search_model .category_group");
			PT.SysCssType.Input.input_group_only_one(title,input_list);
		});
		PT.SysCssType.system_input_default_bind("#search_model .category_group")

		PT.SysCssType.system_checkbox_msg_bind("#contain_sub","包含子类目")
	};
	
	var init_dom = function(){
        PT.Base.set_nav_activ('category_list');
        $(".search_btn_click").click(function(){
        	PT.show_loading('正在获取数据');
        	var cat_id_obj = $(".category_group[search_type=cat_id]")
        	var cat_id = cat_id_obj.val();
        	var cat_name_obj = $(".category_group[search_type=cat_name]"); 
        	var cat_name = cat_name_obj.val();
        	
        	var same_cat_id = cat_id == cat_id_obj.attr('default_title') ? true : false; 
        	var same_cat_name= cat_name== cat_name_obj.attr('default_title') ? true : false; 
        	
        	if ( same_cat_id && same_cat_name){
        		PT.hide_loading();
        		return PT.alert("请输入您要查询的内容");
        	} else if (same_cat_id){
        		cat_id = '0';
        	} else if (same_cat_name){
        		cat_name = '';
        	}
        	
        	var is_contain = 0;
        	if( $('#contain_sub').attr('checked') != undefined ){
        		is_contain = 1 ;
        	}
        	PT.sendDajax({"function":"crm_search_category_list",'cat_id':cat_id,'cat_name':cat_name,'is_contain':is_contain});
        });
        
        $('.assign_account').click(function(){
        	PT.show_loading("正在分配账户")
        	var cat_id = $("#assign_cat_id").text().replace(/\s/g,'');
        	var group_id = $("#group_select option:selected").val();
        	var user_id = $("#user_select option:selected").val();
        	var count = $("#assign_count").val();

        	var is_clear = PT.CommonUtils.checkbox_val($("#clear_account"));
			var is_contain = PT.CommonUtils.checkbox_val($("#contain_sub_cat"));
        	PT.sendDajax({"function":"crm_assign_account_bycategory","cat_id":cat_id,"group_id":group_id,"user_id":user_id,"count":count,"is_clear":is_clear,"is_contain":is_contain})
        });
		

		$("#contain_sub").click();
	}
	
	return {
		
		init:function(){
			init_system_event();
			init_dom();
		},
		set_category_data:function(cat_data,user_name){
			if(cat_data.length > 0){
				var html = "";
				for (var i = 0 ; i < cat_data.length ; i++){
					html += template.render('cat_element_tr',{'cat':cat_data[i],'user':user_name});
				}
				$("#category_content").html(html);
				
				/*
				$('#category_table').dataTable({
		    		'bLengthChange':false,
		    		'iDisplayLength':100,
			   		'bFilter': false,
			   		"aoColumns": [
						{"bSortable": false},
						{"bSortable": true,"sSortDataType": "dom-text", "sType": "string"},
						{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
						{"bSortable": false},
					],
		    		'aaSorting':[[2,'desc'],[1,'asc']]
		    	});
		    	*/
		    	
				$('.jump_select_conf').click(function(){
					var cat_id = $(this).attr('category_id');
				});
				
				$('.load_assign_account').click(function(){
					PT.CRMCategoryList.clear_assign_account_div();
					
					var obj = $(this);
					$("#assign_cat_id").text(obj.attr('cat_id'));
					$("#assign_cat_name").text(obj.attr('cat_name'));
					$("#assign_cat_level").text(obj.attr('cat_level'));
					
					PT.show_loading('正在加载相关数据')
					PT.sendDajax({'function':"crm_load_assign_account_bycategory","cat_id":obj.attr('cat_id')})
				});
				
				$("#no_cat_data").hide();
				$("#show_cat_data").show();
			} else {
				$("#no_cat_data").show();
				$("#show_cat_data").hide();
			}
		},
		set_assign_info:function(acc_total,all_total,group_info,user_info){
			var group_html = '';
			for(var i = 0 ; i < group_info.length ; i ++){
				group_html += template.render('option_element',group_info[i]);
			}
			$("#group_select").html(group_html)
			
			var user_html = template.render('option_element',{"id":"0","name":"------"});
			for(var i = 0 ; i < user_info.length ; i ++){
				user_html += template.render('option_element',user_info[i]);
			}
			$("#user_select").html(user_html)
			
			$("#account_count").text(acc_total+' / '+all_total);
			
			$('#group_select').change(function(){
				PT.sendDajax({"function":"crm_get_assignable_user_bygroup","group_id":$(this).val()})
			});
			
			$.fancybox.open(
		     		[
		     			{
		     				href:'#assign_account_div',
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
		},
		set_assign_user:function(user_info){
			var user_html = template.render('option_element',{"id":"0","name":"------"});
			for(var i = 0 ; i < user_info.length ; i ++){
				user_html += template.render('option_element',user_info[i]);
			}
			$("#user_select").html(user_html)
		},
		clear_assign_account_div:function(){
			$("#assign_cat_name").text('');
			$("#assign_cat_id").text('');
			$("#assign_cat_level").text('');
			$("#group_select").html("");
			$("#user_select").html("");
			$("#assign_count").val('0');
			$("#account_count").text("");
			$("#clear_account").removeAttr('checked');
			$("#contain_sub_cat").removeAttr('checked');
		}
	}
}()