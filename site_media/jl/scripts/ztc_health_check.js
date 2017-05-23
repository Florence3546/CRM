PT.namespace('HealthCheck');
PT.HealthCheck = function () {
	
	var init_loading_layout = function(){
		PT.sendDajax({'function':'web_get_health_layout','obj_id':$("#shop_id").val(),'check_type':'account','flag':0});
	}
	
	var init_recheck = function(){
		
		$("#re_health_check").on("click.PT.HealthCheck",function(){
			send_data();
			$(this).off("click.PT.HealthCheck");	
		})	
	}
	
	var send_data=function(){
		PT.sendDajax({'function':'web_get_health_layout','obj_id':$("#shop_id").val(),'check_type':'account','flag':1});
	}
	
    return {

        //main function to initiate the module
		sent_time_interval:250,
		show_flag:['icon-globe','icon-hand-up','icon-truck','icon-gbp'],
        init:function () {
			// initializ page for adgroup health check
            PT.Base.set_nav_activ(4,1);
			init_loading_layout();
			// init_recheck();
        },
		// initialize page layout
		init_layout:function(account_id,data_list){
			// template.isEscape = false;  // 对于特殊字符不解析，用途：在后台编写html标签文本
			$('#health_check_content').html('');
			check_content = '';
			for ( var i = 0 ; i < data_list.length ; i ++){
				check_content += template.render('time_part',{
															'check_title':data_list[i]['title'],
															'icon':PT.HealthCheck.show_flag[i],
															'index':i
															}
												);
			}
			$('#health_check_content').html(check_content);			
			setTimeout(function(){PT.sendDajax({'function':'web_get_health_items','cache_key':'account_'+account_id,'client_position':-1});},PT.HealthCheck.sent_time_interval);
		},
		// show health check result from server
		set_show_result:function(base_dict,result_dict){
			var cache_key = base_dict['cache_key'];
			var client_position = parseInt(base_dict['client_position']);
			var server_position = parseInt(base_dict['server_position']);
			var ratio_of_hundred = parseInt(result_dict['ratio_of_hundred']);
			
			if(client_position >= server_position ){
				if(ratio_of_hundred != 100){
					$("#process_show_"+(server_position+1)).html(ratio_of_hundred+"%");					
				}					
				setTimeout(function(){PT.sendDajax({'function':'web_get_health_items','cache_key':cache_key,'client_position':server_position});},PT.HealthCheck.sent_time_interval);	
				return
			}
			
			// define args to page show						
			client_position += 1;
			length = result_dict['data'].length;
			
			// set health check items, the data include title, check_type, no_check_items and check_items.
			template.isEscape = false;
			for( var i = 0; i < result_dict['data'].length ; i++){
				var data = result_dict['data'][i];
				var content_obj = $("#item_content_"+(client_position+i));
				var check_type = data['check_type'];
				var title = data['name'];				
				
				// modify ceil size for show check content.
				// set flag size of self-inspection.
				if (data['no_remind_items'].length == 0 ){
					var check_item_html = template.render('check_no_problem',{'title':title});																  
					content_obj.html(check_item_html);
				} else {
					var check_item_html = template.render('check_item_content',{
																				'no_check_items':data['is_remind_items'],
																				'check_items':data['no_remind_items'],
																				'check_type':check_type
																				}
															);																  
					content_obj.html(check_item_html);
					
					for( var k = 0 ; k < data['no_remind_items'].length ; k++ ){
						var content_height = parseInt($("#check_content_"+check_type+"_"+k).height());
						$("#check_flag_"+check_type+"_"+k).css('height',content_height);	
					}
					
					//set flag size of system check.
					for( var k = 0 ; k < data['is_remind_items'].length ; k++ ){
						var content_height = $("#nocheck_content_"+check_type+"_"+k).height();
						$("#nocheck_flag_"+check_type+"_"+k).height(content_height);		
					}
				}
				
				$("#process_show_"+(client_position+i)).html('检查完成');						
				$("html,body").animate({scrollTop:$("#show_"+(client_position+i)).offset().top},1000);//1000是ms,也可以用slow代替
			}
			
			// the following code was tested.
			// alert(client_position+"      " +server_position+"                "+result_dict['data'].length);
			if ( server_position < 3) {	
				if(ratio_of_hundred != 100){
					$("#process_show_"+(server_position+1)).html(ratio_of_hundred+"%");					
				}	
				setTimeout(function(){PT.sendDajax({'function':'web_get_health_items','cache_key':cache_key,'client_position':server_position});},PT.HealthCheck.sent_time_interval);
				return 
			}else{
				init_recheck();
			}
		}
    };

}();

