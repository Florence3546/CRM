PT.namespace('CrmCondition');
PT.CrmCondition = function () {
	var cond_type_list=['account', 'campaign', 'adgroup', 'keyword'],
		current_type=parseInt($('input[name="source_type"]').val()); //当前页面的索引
	
	var get_dangerous_info = function(){
		PT.sendDajax({'function':"crm_get_dangerous_info"});
	};

	var rjjh_remind_show_func = function(){
		var flag_obj = $("#rjjh_remind_flag");
		var flag = flag_obj.val();
		var speed = 5000;
		var obj = $("#rjjh_remind_show");
		if(flag == 0 || flag == '0'){
			obj.css({'color':'white','font-weight':300});
		}  else if (flag == 1|| flag == '1'){
			obj.css({'color':'red','font-weight':600});
			speed = 400;
			flag_obj.val(2);
		} else if (flag == 2 || flag == '2'){
			obj.css({'color':'black','font-weight':300});
			speed = 400;
			flag_obj.val(1);
		}
		setTimeout(function(){rjjh_remind_show_func();},speed);
	};
	
	var init_dom=function(){
		
		var rjjh_dev = $("#rjjh_remind_dev");
		if(rjjh_dev.length > 0){
			$("#pull_but").click();
			get_dangerous_info();
			setInterval(get_dangerous_info,1000*60*5);
			rjjh_remind_show_func();
		}

		$("#base_consult_group_id").change(function(){
				PT.sendDajax({'function':"crm_get_base_user_info",'department':$(this).val(),'name_space':"CrmCondition"});
		});

		$('#campaign_mnt_type').change(function(){
			var type = $('#campaign_mnt_type').val();
			if(type=='2'){
				$("#campaign_stat_type").removeAttr('disabled');
			}else{
				$("#campaign_stat_type").attr({'disabled':'disabled'});
			}
		});

		$('#base_is_rpt').change( function(){
			var is_rpt=$(this).val();
			if (is_rpt==1) {
				$('#base_rpt_day').parent().show();
				$('.c_content .rpt ').slideDown('fast');
				$('.is_on_rpt').fadeIn('fast');
			} else {
				$('#base_rpt_day').parent().hide();
				$('.c_content .rpt ').slideUp('fast');
				$('.is_on_rpt').fadeOut('fast');
			}
		});

		$('#button_search').live('click',function(){
			//初始化分页器
			$('#dynamic_pager').html('');
			$('#dynamic_pager').off('page');
			PT.CrmCondition.get_filter_result(1);

			var show_btn=$('#show_summary_rpt');
			if($('#base_is_rpt').val()==1){
				show_btn.fadeIn();
			}else{
				show_btn.fadeOut();
			}
			$('#summary_rpt_table').hide();
		});

		$('#show_summary_rpt').live('click',function(){
			var obj = $('#summary_info_tip');
			if(obj.css('display') == 'none'){
				var is_jumped=parseInt($('#base_is_jumped').val());
				PT.sendDajax({'function':'crm_statistical_summary','filter_type_index':current_type,'is_jumped':is_jumped});
			}
			obj.slideDown('fast');
			$('#summary_rpt_table').slideUp('fast');
		});

		$(".submit_msg").live('click',function(){
			var content=$('#msg_content').val();
			if (content) {
				var obj_list=get_objs_list(current_type), title=$('#msg_title').val();
				if (obj_list.length) {
					PT.show_loading('正在提交消息');
					PT.sendDajax({'function':'crm_submit_msg','msg_type':$(this).attr('msg_type'),'title':title,'content':content,'obj_type':current_type,'obj_list':$.toJSON(obj_list)});
				}else{
					PT.alert('请至少选择一条记录');
				}
			}
		});

		$('.open_msg').live('click',function(){
			var now_tr = $(this).parents('tr')[0],
				table_list=['account_table','camp_table','adg_table'],
				data_table=$('#'+table_list[current_type]).dataTable();

            if (data_table.fnIsOpen(now_tr) ){
                data_table.fnClose(now_tr);
				$(this).text('展开');
            } else {
				$(this).text('收缩');
				var detail_str=$(now_tr).data('detail_str');
				if (detail_str && $(now_tr).attr('is_refresh')==0 ) {
					data_table.fnOpen( now_tr, $(detail_str) , 'info_row' );
				} else {
					data_table.fnOpen( now_tr, "<span class='tac'><img src='/site_media/jl/img/forecast_orde_ajax.gif'>正在加载中。。。</span>", 'info_row tac' );
					var jq_check_box=$(now_tr).find('.kid_box');
					PT.sendDajax({'function':'crm_get_msg','obj_type':current_type,'obj_id':jq_check_box.val(),'shop_id':jq_check_box.attr('shop_id')});
				}
            }
		});
	}

	var init_common_dom=function(){
		// 初始化全选按钮
		var all_select_html = "<a href='javascript:;' class='use_cache single ' ><i class='icon-lightbulb' style='color:red;font-size:20px;' ></i></a>&nbsp;&nbsp;多页全选(<span id='selected_status' style='color:gray'>已关闭</span>)";
		var obj = $('#all_selected');
		obj.html(all_select_html);

		PT.CrmCondition.init_all_selected_envent();
	}

	var get_objs_list=function(obj_type){
		var objs=$('table tbody input:checked'), obj_list=[];
		objs.each(function(){
			obj_list.push({'shop_id':parseInt($(this).attr('shop_id')),'obj_id':parseInt($(this).val())});
		});
		return obj_list;
	}

	var init_data=function(type_id,data){
		var format_dict={'pay':[100,1,2],'cost':[100,1,2],'cpc':[100,1,2],'ctr':[1,100,2],'conv':[1,100,2],'budget':[100,1,2],'max_price':[100,1,2],'limit_price':[100,1,2],'cons_ratio':[1,100,0]};
		var format_id_list=[],str_list=['nick','contain','cat_id'];
		for (var k in format_dict) {
			format_id_list.push(k);
		}
		//如果需要返回字符串
		if(data==-1){
		  	return '';
		}
		if(format_dict.hasOwnProperty(type_id)) {
			var denominator=format_dict[type_id][0], multiple=format_dict[type_id][1], point=format_dict[type_id][2];
			return parseFloat((data * multiple / denominator).toFixed(point));
		} else {
		  	return data;
		}
	}

	var format_data=function(type_id,data){
		//格式化数据 {key:[ multiple, denominator, point]}
		var format_dict={'pay':[100,1,2],'cost':[100,1,2],'cpc':[100,1,2],'ctr':[1,100,4],'conv':[1,100,4],'budget':[100,1,2],'max_price':[100,1,2],'limit_price':[100,1,2],'cons_ratio':[1,100,2]};
		var format_id_list=[],str_list=['nick','contain','cat_id'];
		for (var k in format_dict) {
			format_id_list.push(k);
		}

		//如果需要返回字符串
		if(str_list.indexOf(type_id)!=-1) {
			data=data.replace(/^\s+|\s+$/g,'');
			return (data?data:-1)
		}
		data=parseFloat(data);
		if(isNaN(data)){
			return -1;
		}
		if(format_dict.hasOwnProperty(type_id)) {
			var multiple=format_dict[type_id][0], denominator=format_dict[type_id][1], point=format_dict[type_id][2];
			return parseFloat((data * multiple / denominator).toFixed(point));
		} else {
			return data;
		}
	}

	//获取所有过滤条件
	var get_conditions=function(){
		var account_rpt_dict={}, campaign_rpt_dict={}, adgroup_rpt_dict={}, keyword_rpt_dict={},cond_dict={},
			base_special_dict={},account_special_dict={}, campaign_special_dict={}, adgroup_special_dict={}, keyword_special_dict={};
		var rpt_inputs=$('.condtion_select .rpt>span'),
			special_single_inputs=$('.condtion_select .special .single'),
			special_double_inputs=$('.condtion_select .special .double');

		//获取报表过滤条件
		rpt_inputs.each(function() {
			var cond_type=$(this).attr('id').replace('_','0').split('0'),
				min_data=$(this).find('.min').val(), max_data=$(this).find('.max').val();
			eval(cond_type[0]+'_rpt_dict')[cond_type[1]]=[format_data(cond_type[1],min_data),format_data(cond_type[1],max_data)];
		});
		//获取单个输入框和下拉列表的值
		special_single_inputs.each(function() {
			var cond_type=$(this).attr('id').replace('_','0').split('0'), cond_data=$(this).val();
			eval(cond_type[0]+'_special_dict')[cond_type[1]]=(format_data(cond_type[1],cond_data));
		});
		//获取报表以外的一对输入框的值
		special_double_inputs.each(function() {
			var cond_type=$(this).attr('id').replace('_','0').split('0'),
				min_data=$(this).find('.min').val(), max_data=$(this).find('.max').val();
			eval(cond_type[0]+'_special_dict')[cond_type[1]]=[format_data(cond_type[1],min_data),format_data(cond_type[1],max_data)];
		});

		for (var i in cond_type_list) {
			var cond_type=cond_type_list[i];
			cond_dict[cond_type]={'special':eval(cond_type+'_special_dict'),'rpt':eval(cond_type+'_rpt_dict')};
		}

		return [base_special_dict,cond_dict];
	}

	return {
		init:function(){
			init_dom();
			init_common_dom();
		},

		//初始化过滤条件
		init_condition:function(base_dict,cond_dict){
			PT.show_loading('正在初始化过滤条件');
			for (var k in base_dict) {
				$('#base_'+k).val(base_dict[k]==-1?'':base_dict[k]);
			}
			if ( $('#base_is_jumped').val()==1) {
				var source_type=parseInt($('#source_type').val()),
					jq_conditions=$('#condition_div .condtion_select'),base_div=jq_conditions.eq(0);
				for(var i=0; i<=source_type; i++){
					jq_conditions.eq(i+1).hide();
				}
				base_div.find('#base_is_jumped').parent().show();
				base_div.find('select').slice(0,3).attr('disabled','disabled');
			}

			for (var key in cond_dict) {
				var key_array = key.replace(/\s/g,'').split('_');
				if(key_array.length > 2){
					var temp_dict = cond_dict[key];
					cond_type = key_array[1];
					if (temp_dict == null){
						continue
					}
					var key_list = new Array();
					if (temp_dict.hasOwnProperty('rpt')){
						key_list.push('rpt');
					}
					if (temp_dict.hasOwnProperty('special')){
						key_list.push('special');
					}
					for(sub_key in key_list){
						render_dict = temp_dict[ key_list[sub_key] ];
						for (cond_id in render_dict){
							var data = render_dict[cond_id];
							if (data instanceof Array) {
								var min=init_data(cond_id,data[0]),max=init_data(cond_id,data[1]);
								$('#'+cond_type+'_'+cond_id).find('.min').val(min);
								$('#'+cond_type+'_'+cond_id).find('.max').val(max);
							} else {
								data=init_data(cond_id,data);
								$('#'+cond_type+'_'+cond_id).val(data);
							}
						}
					}
				}
			}

			$('#base_is_rpt').change();
			$("#base_consult_group_id").change();
			PT.hide_loading();


			if (['1131', '1159', '1223'].indexOf($('#consult_id').val()) >= 0) {
				$('.is_usable').attr('disabled', false);
			}
		},

		get_filter_result:function (page_no){
			var cond_arr=get_conditions();
			var tree_path = $("#tree_path").val();
			if (!cond_arr) {
				return false;
			}
			PT.show_loading('正在查询数据');
			PT.sendDajax({'function':'crm_get_filter_result','filter_type_index':current_type,'tree_path':tree_path,'base_dict':$.toJSON(cond_arr[0]),'cond_dict':$.toJSON(cond_arr[1]),'page_no':page_no,'is_manual':true});
		},

		statistics_summary_back:function(data,error_msg){
			$('#summary_info_tip').slideUp('fast');
			var result_dict=eval(data),td_str=template.render('summary_rpt_table_td', result_dict),sum_table=$('#summary_rpt_table');
			sum_table.find('tbody tr').html(td_str);
			sum_table.slideDown('fast');
			if(error_msg != ''){
				PT.alert(error_msg);
			}
		},

		get_group_back:function (psuser_id, psuser_type,group_list, user_list) {

			var obj = $('#base_consult_group_id');
			var obj_sub = $("#base_consult_id");

			if(group_list.length > 0){
				var option_str="";
				for(var i=0;i<group_list.length;i++) {
					option_str += "<option value='"+group_list[i][0]+"'>"+group_list[i][1]+"</option>";
				}
				obj.html(option_str);
			}

			option_str="<option value='-1'>---------</option>";
			for(var i=0;i<user_list.length;i++) {
				option_str += "<option value='"+user_list[i][0]+"'>"+user_list[i][1]+"</option>";
			}
			obj_sub.html(option_str);

			if($("#base_consult_id option[value="+psuser_id+"]").length > 0){
				obj.val(psuser_type);
				obj_sub.val(psuser_id);
			}

			var is_jumped=parseInt($('#base_is_jumped').val());
			if(is_jumped==1){
				$('#button_search').click();
			} else if ($('#request_condition input').length>0) {
                // 从ncrm过来时自动搜索账户
                $('#condition_div input, #condition_div select:not(#base_consult_group_id, #base_rpt_day)').val(null);
                if (!$('#base_rpt_day').val()) {$('#base_rpt_day').val('7')};
                $('#request_condition input').each(function () {
                    $('#'+$(this).attr('name')).val(this.value);
                });
                $('#request_condition').empty();
                $('#button_search').click();
            }
		},

		submit_msg_back:function(error_flag,obj_id_list){
			if(error_flag){
				PT.alert("提交消息失败，请刷新页面后重试");
			}else{
				PT.light_msg("","提交消息成功");
				$("#modal_msg").modal('hide');
				for(var i=0;i<obj_id_list.length;i++) {
					var jq_tr=$(".kid_box[value='"+obj_id_list[i]+"']").parents('tr'),
						jq_msg_td=jq_tr.find('.msg_td');
					if (jq_msg_td.find('.open_msg').length){
						jq_tr.attr('is_refresh',1);
					}else{
						jq_msg_td.html('<a herf="javascript:;" class="open_msg cur">展开</a>');
					}
				}
			}
		},

		get_msg_back:function(error_flag, obj_id, msg_list){
			var jq_tr=$(".kid_box[value='"+obj_id+"']").parents('tr'),
				table_list=['account_table','camp_table','adg_table'],
				data_table=$('#'+table_list[current_type]).dataTable();
			if(error_flag){
				var detail_str = "<span class='tac'>获取消息失败</span>";
			}else if (msg_list){
				template.isEscape=false;
				var detail_str = template.render("msg_template", {'msg_list':msg_list});
				jq_tr.data('detail_str',detail_str);
				jq_tr.attr('is_refresh',0);
				template.isEscape=true;
			}else{
				var detail_str ="<span class='tac'>没有消息</span>";
			}
			jq_tr.next().find('.info_row').html(detail_str);
		},

		init_all_selected_envent:function(){
			var color_red = 'rgb(245, 46, 19)';
			var init_obj = $('#all_selected a.use_cache');
			init_obj.find('i').css('color',color_red);
			init_obj.unbind('click');
			init_obj.click(function(){
				PT.alert("很抱歉，您还未搜索出任何结果，该操作无效！");
			});
		},
		
		get_dangerous_info_back:function(result){
			var data = eval(result);
			if(data.length > 0){
				var content = '';
				for(var i=0; i < data.length ; i ++){
					var temp = data[i];
					temp['num'] = i+1;
					temp['title'] = temp['title'] ; 
					temp['shop_ids'] = eval(temp['val']) ; 
					content += template.render('rjjh_remind_tr',temp);
				}
				
				$("#rjjh_remind_table tbody").html(content);
				$("#rjjh_remind_table").removeClass('hide');
				$("#rjjh_noremide_div").addClass('hide');
				$("#rjjh_remind_flag").val(1);
				
			} else {
				$("#rjjh_remind_table").addClass('hide');
				$("#rjjh_noremide_div").removeClass('hide');
				$("#rjjh_remind_flag").val(0);
			}
			
		},
		
		add_all_selected_envent:function(){
			var parent_obj = $("#all_selected");
			var obj_table = parent_obj.attr('table');
			var color_green = 'rgb(33, 243, 5)';
			var color_red = 'rgb(245, 46, 19)';

			var add_obj = $('#all_selected a.use_cache');
			add_obj.find('i').css('color',color_red);
			var opar_objs = $('#'+obj_table+' input[type=checkbox]');
			opar_objs.attr({'checked':false});
			opar_objs.removeAttr('disabled');
			var select_status = $('#selected_status');
			select_status.text("已关闭");


			add_obj.unbind("click");
			add_obj.click(function(){
				var obj =  $(this).find('.icon-lightbulb');
				if ( obj.css('color') == color_red) {
					obj.css('color',color_green);
					opar_objs.attr({'checked':true,'disabled':'disabled'});
					parent_obj.attr('is_all',1);
					select_status.css('color','red');
					select_status.text("已开启");
				} else {
					obj.css('color',color_red);
					opar_objs.attr({'checked':false});
					opar_objs.removeAttr('disabled');
					parent_obj.attr('is_all',0);
					select_status.css('color','gray');
					select_status.text("已关闭");
				}
			});
		}
	}

}()
