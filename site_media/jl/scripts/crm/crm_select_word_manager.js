PT.namespace('CRMSelectWordManager');
PT.CRMSelectWordManager = function () {
	var init_system_event = function(){
		// 搜索模块 INPUT 事件
		$("#search_model .search_cond input[type=text]").click(function(){
			var title = $(this).attr("default_title");
			var input_list = $("#search_model .search_cond input[type=text]");
			PT.SysCssType.Input.input_group_only_one(title,input_list);
		});
		$("#search_model .search_cond input[type=text]").blur(function(){
			PT.CheckLib.all_digit($(this).val());
		});
		PT.SysCssType.system_input_default_bind($("#search_model .search_cond input[type=text]"))
	};
	
	var init_dom = function(){
		// 加载数据
		PT.CRMSelectWordManager.init_loading(); 
		
		$("#config_oper_type").change(function(){
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var cat_id = $("#cur_cat_id").val();
			var model_type = $("#config_oper_type").val() ;
			PT.show_loading("正在切换配置模式");
			PT.sendDajax({"function":"crm_get_selectword_conf_info","cat_id":cat_id,'shop_id':shop_id,'item_id':item_id,'model_type':model_type});
		});
		
		$('.jump_kwlib').click(function(){
			var obj = $(this);
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var url = "/crm/kw_manage?shop_id="+shop_id+"&item_id="+item_id+"&jump_type="+$(this).attr("jump_type");
			obj.attr("href",url);
			obj.click();
		});
		
		// 类目属性词配置
		$('.save_cat_product').click(function(){
			var cat_id = $("#cur_cat_id").val();
			var product_conf_match = $("#product_conf_match").val().replace(' ','');
			var product_conf_absolute = $("#product_conf_absolute").val().replace(' ','');
			PT.sendDajax({
				"function":"crm_save_cat_conf",
				"cat_id":cat_id,
				"product_conf":product_conf_match+";"+product_conf_absolute
			});
		});
		
		$('.save_cat_sale').click(function(){
			var cat_id = $("#cur_cat_id").val();
			var sale_conf_match = $("#sale_conf_match").val().replace(' ','');
			var sale_conf_absolute = $("#sale_conf_absolute").val().replace(' ','');
			PT.sendDajax({
				"function":"crm_save_cat_conf",
				"cat_id":cat_id,
				"sale_conf":sale_conf_match+";"+sale_conf_absolute
			});
		});
		
		// 宝贝属性保存事件	
		$(".save_sale").click(function(){
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var saleword_list = $("#sale_words").val();
			PT.sendDajax({	
										'function':'crm_save_item_attr',
										'shop_id':shop_id,
										'item_id':item_id,
										'saleword_list':saleword_list
									});		
		});
		
		$(".save_black").click(function(){
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var blackword_list = $("#black_words").val();
			PT.sendDajax({	
										'function':'crm_save_item_attr',
										'shop_id':shop_id,
										'item_id':item_id,
										'blackword_list':blackword_list
									});		
		});
		
		$('.cat_save_model').click(function(){
			if (!PT.CRMSelectWordManager.verify_syntax($("#cat_select_conf"))){
				return
			}
			var result = PT.CRMSelectWordManager.pack_select_word_conf($("#cat_select_conf"));
			PT.sendDajax({	
										'function':'crm_update_cat_conf',
										'conf_name':result.conf_name,
										'conf_desc':result.conf_desc,
										'candi_filter':result.candi_filter,
										'label_define_list':$.toJSON(result.label_define_list),
										'select_conf_list':$.toJSON(result.select_conf_list),
										'price_conf_list':$.toJSON(result.price_conf_list),
										'delete_conf':$.toJSON(result.delete_conf),
									});		
		});
		
		$('.save_item_conf').click(function(){
			if (!PT.CRMSelectWordManager.verify_syntax($("#item_select_conf"))){
				return
			}
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var model_type = $("#config_oper_type").val();
			var result = PT.CRMSelectWordManager.pack_select_word_conf($("#item_select_conf"));
			PT.sendDajax({	
										'function':'crm_save_item_conf',
										'shop_id':shop_id,
										'item_id':item_id,
										'model_type':model_type,
										'conf_name':result.conf_name,
										'conf_desc':result.conf_desc,
										'candi_filter':result.candi_filter,
										'label_define_list':$.toJSON(result.label_define_list),
										'select_conf_list':$.toJSON(result.select_conf_list),
										'price_conf_list':$.toJSON(result.price_conf_list),
										'delete_conf':$.toJSON(result.delete_conf),
									});		
		});
		
		$('.cat_select_conf_test').click(function(){
			if (!PT.CRMSelectWordManager.verify_syntax($("#cat_select_conf"))){
				return
			}
			var result = PT.CRMSelectWordManager.pack_select_word_conf($("#cat_select_conf"));
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var adg_id = $("#cur_adg_id").val();
			PT.CRMSelectWordManager.send_test_data(shop_id,item_id,adg_id,result);
		});
		
		$(".test_item_word").click(function(){
			if (!PT.CRMSelectWordManager.verify_syntax($("#item_select_conf"))){
				return
			}
			var result = PT.CRMSelectWordManager.pack_select_word_conf($("#item_select_conf"));
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var adg_id = $("#cur_adg_id").val();
			PT.CRMSelectWordManager.send_test_data(shop_id,item_id,adg_id,result);
		});
		
		$('.cancel_fancybox').click(function(){
			$.fancybox.close();
		});
		
		$('.reset_source').click(function(){
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var flag = $("#word_modifier").text().replace(/\s/g,'');
			if( flag == "AE"){
				PT.show_loading("正在提交重置信息给后台");
				PT.sendDajax({"function":"crm_reset_source_status",'shop_id':shop_id,'item_id':item_id});
			} else {
				PT.alert("当前词元来源状态非 AE 状态，禁止使用此功能。");			
			}
		});

		$('.reanalyze_item').click(function(){
			PT.show_loading("正在重新解析");
			PT.CRMSelectWordManager.get_item_info(1);
		});
		
		$(".system_analyze").click(function(){
			PT.show_loading("正在系统解析");
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			PT.sendDajax({"function":"crm_system_item_analysis","shop_id":shop_id,"item_id":item_id})
		});
		
		$('.add_new_model_dev').click(function(){
			$("#new_conf_name").val();
			$.fancybox.open(
							     		[
							     			{
							     				href:'#add_generate_model',
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
		
		$('.add_new_model').click(function(){
			var new_conf_name = $("#new_conf_name").val();
			if(new_conf_name == ""  || new_conf_name == undefined){
				PT.alert("新通用模板 名称不能为空");
				return
			} else {
				for(var index in new_conf_name){
					var char_num = new_conf_name[index].charCodeAt()
					if (char_num != 95 &&  (char_num > 122 || char_num <97) ){
						PT.alert("通用模板 名称仅可用 \"_\" 或 小写英文字母。");
						return
					}
				}
			}
			PT.show_loading("正在添加新的通用模板");
			if (!PT.CRMSelectWordManager.verify_syntax($("#cat_select_conf"))){
				return
			}
			var result = PT.CRMSelectWordManager.pack_select_word_conf($("#cat_select_conf"));
			PT.sendDajax({	
										'function':'crm_add_new_model',
										'conf_name':"default_" + new_conf_name,
										'conf_desc':result.conf_desc,
										'candi_filter':result.candi_filter,
										'label_define_list':$.toJSON(result.label_define_list),
										'select_conf_list':$.toJSON(result.select_conf_list),
										'price_conf_list':$.toJSON(result.price_conf_list),
										'delete_conf':$.toJSON(result.delete_conf),
									});		
		});
		
		$('.save_cat').click(function(){
			var html = "";
			var cat_id_list = $("#cat_ids").html().split(' ');
			var cat_name_list = $("#cat_path_name").html().split('&gt;');
			var cur_cat_name = $("#cur_cat_name").html();
			var temp_param = "";
			for(var i=0 ; i < cat_name_list.length;i++){
				if( i != cat_name_list.length-1 ){
					var cat_name = '';
					if(i !=0){
						cat_name = temp_param+cat_name_list[i]; 
					} else{
						cat_name = cat_name_list[i];
					}
					temp_param += cat_name_list[i] + "&gt;" ;
				} else {
					cat_name = "当前类目";
				}
				html += template.render('cat_element',{'cat_id':cat_id_list[i],'cat_name':cat_name});
			}
			$("#cat_list").html(html);
			
			$.fancybox.open(
							     		[
							     			{
							     				href:'#cat_model_list',
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
		
		$(".add_item_conf").click(function(){
			PT.CRMSelectWordManager.clear_select_word_conf($("#item_select_conf"));
			PT.CRMSelectWordManager.item_conf_display(1);
			$("#item_conf_name").val(PT.CRMSelectWordManager.get_item_conf_name());
		});
		
		$('.transfer_right_data').click(function(){
			var obj_src = $("#cat_select_conf");
			var obj_des = $("#item_select_conf");
			PT.CRMSelectWordManager.transfer_data(obj_src,obj_des);
			$("#item_conf_name").val(PT.CRMSelectWordManager.get_item_conf_name());
		});
		
		$('.bind_cat_conf').click(function(){
			var check_obj = $("#cat_list input[type=radio]:checked");
			if (check_obj.length >0){
				if (!PT.CRMSelectWordManager.verify_syntax($("#cat_select_conf"))){
					return
				}
				var cat_id = check_obj.attr("cat_id");
				var model_type= $("#config_oper_type").val();
				var is_force = 0;
				if ( $("#is_force:checked").length > 0){
					is_force = 1;
				}
				var cat_name= "c"+cat_id+"_"+model_type;
				var result = PT.CRMSelectWordManager.pack_select_word_conf($("#cat_select_conf"));
				result.conf_name = cat_name;
				PT.sendDajax({	
										'function':'crm_save_cat_select_conf',
										'cat_id':cat_id,
										'model_type':model_type,
										'conf_name':result.conf_name,
										'conf_desc':result.conf_desc,
										'candi_filter':result.candi_filter,
										'label_define_list':$.toJSON(result.label_define_list),
										'select_conf_list':$.toJSON(result.select_conf_list),
										'price_conf_list':$.toJSON(result.price_conf_list),
										'delete_conf':$.toJSON(result.delete_conf),
										'is_force':is_force
									});
			} else {
				PT.alert("请选择要另存为的类目");
			}
		});
		
		$(".plus_items").click(function(){
			var obj = $("#item_index");
			var index = parseInt(obj.val());
			PT.CRMSelectWordManager.assign_changeable_items(index+1);
		});
		
		$(".sub_items").click(function(){
			var obj = $("#item_index");
			var index = parseInt(obj.val());
			PT.CRMSelectWordManager.assign_changeable_items(index-1);
		});
		
		$(".bind_default_model").click(function(){
			var conf_name = $("#cat_conf_name").val();
			var model_type = $("#config_oper_type").val();
			var cur_cat_id = $("#cur_cat_id").val();
			PT.confirm("您确定当下类目要绑定模板 "+conf_name+" 吗？",function(){
				PT.sendDajax({"function":"crm_bind_cat_conf","conf_name":conf_name,"model_type":model_type,"cat_id":cur_cat_id});
			})
		});
		
		$("#system_default_conf option").click(function(){
			var conf_name = $(this).text();
			PT.confirm("您确定要将通用模板 "+conf_name+" 导入到您当前类目选词配置中吗？",function(conf_name){
				PT.show_loading("正在加载模板");
				PT.sendDajax({"function":"crm_get_default_select_conf","conf_name":conf_name});
			},[conf_name])
		});
		
		$(".search_btn_click").click(function(){
			var obj_list = $("#search_model .search_cond input[type=text]")
			var search_type = "";
			var arg = 0;
			for (var i = 0 ; i < obj_list.length ; i++){
				var temp = $(obj_list[i]);
				if( !isNaN(temp.val()) ){
					search_type = temp.attr("search_type") ;
					arg = temp.val();
					break
				}	
			}
			if(search_type != ""){
				PT.show_loading("请求获取数据");
				PT.sendDajax({"function":"crm_get_loading_info","search_type":search_type,"obj_id":arg});
			} else {
				PT.alert("请输入正确搜索参数！");
			}
			
		});
		
		$("#search_model .cat_level").change(function(){
			var obj = $(this);
			var index = parseInt(obj.attr("index"))+1;
			$("#cat_level_index").val(index);
		});
		
		$("#search_model .cat_level").change(function(){
			PT.CRMSelectWordManager.load_sub_cat($(this).find("option:checked").val());
		});
		
		$("#item_source_title").dblclick(function(){
			var obj = $("#item_editer");
			PT.CRMSelectWordManager.extend_scope_event(obj);
		});
		
		$("#category_title").dblclick(function(){
			var obj = $("#category_editer");
			PT.CRMSelectWordManager.extend_scope_event(obj);
		});
		
		$("#category_select_conf_title").dblclick(function(){
			var obj = $("#category_select_conf_div");
			PT.CRMSelectWordManager.extend_scope_event(obj);
		});
		
		$("#item_select_conf_title").dblclick(function(){
			var obj = $("#item_select_conf_div");
			PT.CRMSelectWordManager.extend_scope_event(obj);
		});
		
		$("#category_editer textarea").blur(function(){
			var obj = $(this);
			PT.CRMSelectWordManager.convert_charset_event(obj);
		});
		
		$("#item_editer textarea,#item_editer input").blur(function(){
			var obj = $(this);
			PT.CRMSelectWordManager.convert_charset_event(obj);
		});
	};
	
	return {
		init:function(){
			init_dom();
			init_system_event();
		},
		
		convert_charset_event:function(obj){
			var text = obj.val();
			var replace_old_list = ['，','”','“','‘','’']
			var replace_new_list = [',','"','"',"'","'"]
			for(var i=0; i < replace_old_list.length; i++){
				var regS = new RegExp(replace_old_list[i],"g");
				text = text.replace(regS,replace_new_list[i])
			}
			obj.val(text);
		},
		
		extend_scope_event:function(obj){
			var class_attrs = obj.attr("class");
			var mark_1 = "span6";
			var mark_2 = "span8"
			var mark_3 = "span4"
			var index = class_attrs.indexOf(mark_1);
			if( index > -1){
				obj.removeClass(mark_1)
				obj.removeClass(mark_3)
				obj.addClass(mark_2)
			} else {
				obj.removeClass(mark_2)
				obj.removeClass(mark_3)
				obj.addClass(mark_1)
			}
			var another_obj = obj.next().length>0 ? obj.next() : obj.prev();
			if(index > -1){
				another_obj.removeClass(mark_1)
				another_obj.addClass(mark_3)
				another_obj.removeClass(mark_2)
			} else {
				another_obj.addClass(mark_1)
				another_obj.removeClass(mark_2)
				another_obj.removeClass(mark_3)
			}
		},
		
		select_event:function(){
			var cur_obj = $(this).parent().parent();
			var cur_obj_class = cur_obj.attr('class');
			var parent_obj = cur_obj.parent();
			var old_obj = parent_obj.find('.action');
			
			if( cur_obj_class != undefined && cur_obj_class !='' && cur_obj.attr('class').indexOf("action") > - 1){
				return 
			}
			if(old_obj.length>0){
				old_obj.removeClass('action');
				old_obj.find('.flag').html('');
			}
			var temp_obj = cur_obj.find('.flag');
			if(temp_obj.length>0){
				cur_obj.addClass('action');
				temp_obj.html('*&nbsp;');
			}
		},
		
		del_event:function(){
			$(this).parent().parent().remove();
		},
		
		up_event:function(){
			var table_obj = $(this).parent().parent().parent();
			if ($(table_obj).find('tr').length < 2){
				return 
			}
			var obj = $(table_obj).find('.action');
			if(obj.length < 1){
				return 
			}
			var before_element = obj.prev();
			if (before_element.length > 0){
				var class_value = before_element.attr('class');
				if (class_value != undefined && class_value.indexOf('title') > -1){
					return 
				}
				before_element.insertAfter(obj); 
			}
		},
		
		down_event:function(){
			var table_obj = $(this).parent().parent().parent();
			if (table_obj.find('tr').length < 2){
				return 
			}
			var obj = table_obj.find('.action');
			if(obj.length < 1){
				return 
			}
			var before_element = obj.next();
			if (before_element.length > 0){
				var class_value = before_element.attr('class');
				if (class_value != undefined && class_value.indexOf('title') > -1){
					return 
				}
				before_element.insertBefore(obj); 
			}
		},
		
		verify_event:function(){
			PT.show_loading("正在验证结果");
			var expr = $(this).parent().parent().find('.verify_content').val()
			PT.sendDajax({"function":"crm_check_base_grammar",'expr':expr})
		},
		
		add_element:function(event){
			var html = template.render(event.data.template_name,event.data.init_data);
			var obj = null;
			if(!event.data.is_next){
				obj = $(this).parent().parent().parent();
				obj.append(html);
				PT.CRMSelectWordManager.event_factory(obj.find('tr').last());
			} else {
				obj = $(this).parent().parent().after(html);
				PT.CRMSelectWordManager.event_factory(obj.next());
			}
		},
		
		event_factory:function(obj){
			var del_obj = obj.find('.del_elements');
			if(del_obj.length > 0){
				del_obj.click(PT.CRMSelectWordManager.del_event); // 删除事件
			}
			var select_obj = obj.find('input[type=text]');
			if(select_obj.length > 0){
				select_obj.click(PT.CRMSelectWordManager.select_event); // 选择事件
			}
			
			var up_obj = obj.find('.up_btn');
			if(up_obj.length > 0){
				up_obj.unbind("click");
				up_obj.click(PT.CRMSelectWordManager.up_event); // 上移事件
			}
			
			var down_obj = obj.find('.down_btn');
			if(down_obj.length > 0){
				down_obj.unbind("click");
				down_obj.click(PT.CRMSelectWordManager.down_event); // 下移事件
			}

			var check_obj = obj.find('.verify_statement');
			if(check_obj.length > 0){
				check_obj.unbind("click");
				check_obj.click(PT.CRMSelectWordManager.verify_event); // 语法校验事件事件
			}
			
			// 类目选词事件
			var add_last_obj = obj.find('#custom_label_table_1 .add_last_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'custom_label_tr',
						"init_data":{'label_tag':''},
						"is_next":false
					},
					PT.CRMSelectWordManager.add_element); // 添加最后一个元素事件
			}
			
			var add_last_obj = obj.find('#init_price_table_1 .add_last_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'init_price_tr',
						"init_data": {'cond':'','price':''},
						"is_next":false
					},
					PT.CRMSelectWordManager.add_element); // 添加最后一个元素事件
			}
			
			var add_last_obj = obj.find('#select_word_table_1 .add_last_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'select_word_cond_tr',
						"init_data":{'cond':'','sort':'','num':''},
						"is_next":false
					},
					PT.CRMSelectWordManager.add_element); // 添加最后一个元素事件
			}
			
			// 宝贝选词事件
			var add_last_obj = obj.find('#custom_label_table_2 .add_last_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'custom_label_tr',
						"init_data":{'label_tag':''},
						"is_next":false
					},
					PT.CRMSelectWordManager.add_element); // 添加最后一个元素事件
			}
			
			var add_last_obj = obj.find('#select_word_table_2 .add_last_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'select_word_cond_tr',
						"init_data":{'cond':'','sort':'','num':''},
						"is_next":false
					},
					PT.CRMSelectWordManager.add_element); // 添加最后一个元素事件
			}
			
			var add_last_obj = obj.find('#init_price_table_2 .add_last_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'init_price_tr',
						"init_data": {'cond':'','price':''},
						"is_next":false
					},
					PT.CRMSelectWordManager.add_element); // 添加最后一个元素事件
			}
			
			// 插入记录事件
			var add_last_obj = obj.find('.add_init_next_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'init_price_tr',
						"init_data": {'cond':'','price':''},
						"is_next":true
					},
					PT.CRMSelectWordManager.add_element); // 添加下一个元素事件
			}
			
			var add_last_obj = obj.find('.add_lable_next_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'custom_label_tr',
						"init_data":{'label_tag':''},
						"is_next":true
					},
					PT.CRMSelectWordManager.add_element); // 添加下一个元素事件
			}
			
			var add_last_obj = obj.find('.add_select_next_btn');
			if(add_last_obj.length > 0){
				add_last_obj.unbind("click");
				add_last_obj.click(
					{
						"template_name":'select_word_cond_tr',
						"init_data":{'cond':'','sort':'','num':''},
						"is_next":true
					},
					PT.CRMSelectWordManager.add_element); // 添加下一个元素事件
			}
			
			var input_list = obj.find('input');
			if(input_list.length > 0){
				input_list.unbind("blur");
				input_list.blur(function(){
					var obj=$(this);
					PT.CRMSelectWordManager.convert_charset_event(obj);
				});
			}
		},
		
		clear_item_info:function(){
			// 插入宝贝属性信息
			$('#item_title').html("");
			var prefix_list = ['','system'];
			for(var i = 0 ; i < prefix_list.length ; i ++){
				$("#"+prefix_list[i]+"word_modifier").html("");
				$("#"+prefix_list[i]+"element_words").val("");
				$("#"+prefix_list[i]+"product_words").val("");
				$("#"+prefix_list[i]+"sale_words").val("");
				$("#"+prefix_list[i]+"decorate_words").val("");
			}
			
			// 特有数据
			$("#include_words").val("");
			$("#black_words").val("");
			
			// 更新基本信息
			$("#cur_shop_id").val(-1);
			$("#cur_item_id").val(-1);
			
			$("#item_title").parent().attr("href","#");
			
			// 隐藏系统解析
			$(".system_parse").hide();
		},
		
		insert_item_info:function(item_attrs,is_system,is_clear){
			if (is_clear == 1 ){
				PT.CRMSelectWordManager.clear_item_info();
			}
			
			var prefix = "";
			if( is_system == 1){
				prefix = 'system_';
			} 
			$("#"+prefix+"word_modifier").html(item_attrs.operator);
			$("#"+prefix+"element_words").val(item_attrs.ele_info);
			$("#"+prefix+"product_words").val(item_attrs.pro_info);
			$("#"+prefix+"sale_words").val(item_attrs.sale_info);
			$("#"+prefix+"hot_words").val(item_attrs.hot_info);
			$("#"+prefix+"decorate_words").val(item_attrs.deco_info);
			$("#"+prefix+"custom_words").val(item_attrs.custom_words);
			
			if (prefix == ''){
				// 特有数据
				$("#include_words").val(item_attrs.include_list);
				$("#black_words").val(item_attrs.black_info);
				
				// 插入宝贝属性信息
				$('#item_title').html(item_attrs.title);
				// 更新基本信息
				$("#cur_shop_id").val(item_attrs.shop_id);
				$("#cur_item_id").val(item_attrs.item_id);
				
				$("#item_title").parent().attr("href","http://item.taobao.com/item.htm?id="+item_attrs.item_id);
			} else {
				$(".system_parse").show();
			}
		},
		
		get_item_conf_name:function(){
			var cur_item_id=$("#cur_item_id").val();
			var model_type= $("#config_oper_type").val();
			return 'i'+cur_item_id+"_"+model_type
		},
		
		insert_category_info:function(cat_info){
			// 插入类目属性信息
			$("#cat_ids").html(cat_info.cat_path);
			$("#cat_path_name").html(cat_info.cat_full_name);
			$("#product_conf_match").val(cat_info.product_conf_match);
			$("#product_conf_absolute").val(cat_info.product_conf_absolute);
			$("#sale_conf_match").val(cat_info.sale_conf_match);
			$("#sale_conf_absolute").val(cat_info.sale_conf_absolute);
			// 更新基本信息
			$("#cur_cat_id").val(cat_info.cat_id);
		},
		
		verify_syntax:function(obj){
			// 校验配置名称
			var conf_name_obj = obj.find('.conf_name');
			if(conf_name_obj.length > 0){
				var config_name = conf_name_obj.val();
				if(config_name == "" ){
					PT.alert('配置名称不能为空。');
					return false
				}
				for(index in config_name){
					var char_code = config_name[index].charCodeAt();
					if(!(char_code == 95 || (char_code < 123 && char_code > 96) || (char_code < 91 && char_code > 64) || char_code < 58 && char_code > 47 )){
						PT.alert('\"默认配置名称\" 仅能为 英文字符 ,数字 或 \"_\" 。');
						return false
					}
				}
			}else{
				return false
			}
			
			// 校验海选条件
			var candi_filter_obj = obj.find('.candi_filter');
			if(candi_filter_obj.length > 0){
				var candi_filter = candi_filter_obj.val();
				if(candi_filter == ""){
					PT.alert('海选条件不能为空。');
					return false
				}
			}else{
				return false
			}
			
			// 校验自定义标签
			var label_define_obj_list = obj.find('.label_define_list tr');
			var attr_list = ['type','name','rule','from'] ;
			if(label_define_obj_list.length > 1){
				for(var i = 1 ; i < label_define_obj_list.length ; i++){
					var row_label = $(label_define_obj_list[i]).find('.label_tag').val() ;
					if(row_label == ""){
						PT.alert('自定义标签中不能为空。( 行：'+(i+1)+")");
						return false
					}
					for (var j = 0 ; j < attr_list.length ; j ++){
						if(row_label.indexOf(attr_list[i]) == -1){
							PT.alert('自定义标签中不存在 \"'+attr_list[i]+'\" 字段。( 行：'+(i+1)+")");
							return false
						}
					}
				}
			}
			
			// 校验选词标签
			var select_conf_obj = obj.find('.select_conf_list tr');
			if(select_conf_obj.length > 1){
				for(var i = 1 ; i < select_conf_obj.length ; i++){
					var cond = $(select_conf_obj[i]).find('.cond').val();
					var sort = $(select_conf_obj[i]).find('.sort').val();
					var num = $(select_conf_obj[i]).find('.num').val();
					if(cond == ""){
						PT.alert('选词模块 过滤条件 不能为空。( 行：'+(i+1)+")");
						return false
					}
					if(sort == ""){
						PT.alert('选词模块  排序 不能为空。( 行：'+(i+1)+")");
						return false
					}
					if(num == ""){
						PT.alert('选词模块 数目 不能为空。( 行：'+(i+1)+")");
						return false
					}
				}
			}
			
			// 校验选词标签
			var price_conf_obj = obj.find('.price_conf_list tr');
			if(price_conf_obj.length > 1){
				for(var i = 1 ; i < price_conf_obj.length ; i++){
					var cond = $(price_conf_obj[i]).find('.cond').val();
					var price = $(price_conf_obj[i]).find('.price').val();
					if(cond == ""){
						PT.alert('出价模块 初始出价过滤条件 不能为空。( 行：'+(i+1)+")");
						return false
					}
					if(price == ""){
						PT.alert('出价模块 出价  不能为空。( 行：'+(i+1)+")");
						return false
					}
				}
			}
			
			return true
		},
		
		transfer_data:function(obj_src,obj_des){
			var select_conf = PT.CRMSelectWordManager.pack_select_word_conf(obj_src);
			PT.CRMSelectWordManager.insert_select_word_conf(obj_des,select_conf,1,0);
			PT.CRMSelectWordManager.event_factory(obj_des);
		},
		
		item_conf_display:function(is_existed){
			if(is_existed == "1"){
				$("#item_select_conf").removeClass("hide");
				$(".transfer_right_data").removeClass("hide");
				$(".test_item_word").removeClass("hide");
				$(".save_item_conf").removeClass("hide");

				$("#no_item_show").addClass("hide");
			} else {
				$("#item_select_conf").addClass("hide");
				$(".transfer_right_data").addClass("hide");
				$(".test_item_word").addClass("hide");
				$(".save_item_conf").addClass("hide");
				
				$("#no_item_show").removeClass("hide");
			}
		},
		
		pack_select_word_conf:function(obj){
			// 打包选词信息
			var send_data = {};
			var conf_name_obj = obj.find('.conf_name');
			send_data.conf_name = '';
			if(conf_name_obj.length > 0){
				send_data.conf_name = conf_name_obj.val();
			}
			
			var conf_desc_obj = obj.find('.conf_desc');
			send_data.conf_desc = '';
			if(conf_name_obj.length > 0){
				send_data.conf_desc = conf_desc_obj.val();
			}
			
			var candi_filter_obj = obj.find('.candi_filter');
			send_data.candi_filter = '';
			if(candi_filter_obj.length > 0){
				send_data.candi_filter = candi_filter_obj.val();
			}
			
			var label_define_obj_list = obj.find('.label_define_list tr');
			send_data.label_define_list = [];
			if(label_define_obj_list.length > 1){
				for(var i = 1 ; i < label_define_obj_list.length ; i++){
					send_data.label_define_list[i-1] = "{"+$(label_define_obj_list[i]).find('.label_tag').val()+"}";
				}
			}
			
			var select_conf_obj = obj.find('.select_conf_list tr');
			send_data.select_conf_list = [];
			if(select_conf_obj.length > 1){
				for(var i = 1 ; i < select_conf_obj.length ; i++){
					var val_obj = {} ;
					val_obj.cond = $(select_conf_obj[i]).find('.cond').val();
					val_obj.sort = $(select_conf_obj[i]).find('.sort').val();
					val_obj.num = $(select_conf_obj[i]).find('.num').val();
					send_data.select_conf_list[i-1] = val_obj;
				}
			}
			
			var price_conf_obj = obj.find('.price_conf_list tr');
			send_data.price_conf_list = [];
			if(price_conf_obj.length > 1){
				for(var i = 1 ; i < price_conf_obj.length ; i++){
					var val_obj = {} ;
					val_obj.cond = $(price_conf_obj[i]).find('.cond').val();
					val_obj.price = $(price_conf_obj[i]).find('.price').val();
					send_data.price_conf_list[i-1] = val_obj;
				}
			}
			
			send_data.delete_conf = {}
			
			var remove_dupli_obj = obj.find('.remove_dupli');
			send_data.delete_conf.remove_dupli = 0;
			if(remove_dupli_obj[0].checked){
				send_data.delete_conf.remove_dupli = 1;
			}
			
			var remove_del_obj = obj.find('.remove_del');
			send_data.delete_conf.remove_del = 0;
			if(remove_del_obj[0].checked){
				send_data.delete_conf.remove_del = 1;
			}
			
			var remove_cur_obj = obj.find('.remove_cur');
			send_data.delete_conf.remove_cur = 0;
			if(remove_cur_obj[0].checked){
				send_data.delete_conf.remove_cur = 1;
			}
			
			return send_data
		},
		
		insert_select_word_conf:function(obj,select_conf,is_clear,is_send){
			if(is_clear == "1"){
				PT.CRMSelectWordManager.clear_select_word_conf(obj);
			}
			
			// 初始化选词部分
			var conf_name_obj = obj.find('.conf_name');
			if(conf_name_obj.length > 0){
				if(is_send){
					conf_name_obj.val(select_conf.conf_name);
				}
			}
			
			var conf_desc_obj = obj.find('.conf_desc');
			if(conf_desc_obj.length > 0){
				conf_desc_obj.val(select_conf.conf_desc);
			}
			
			var candi_filter_obj = obj.find('.candi_filter');
			if(candi_filter_obj.length > 0 && select_conf.candi_filter != undefined && select_conf.candi_filter !=""){
				var len = select_conf.candi_filter.length;
				if(is_send == 1){
					candi_filter_obj.val(select_conf.candi_filter.substr(1,len-2));
				} else {
					candi_filter_obj.val(select_conf.candi_filter);
				}
			}
			
			var label_define_obj = obj.find('.label_define_list');
			if(label_define_obj.length > 0 && select_conf.label_define_list != undefined && select_conf.label_define_list !=[]){
				var temp_conf_html = '';
				for (var i = 0 ; i < select_conf.label_define_list.length ; i ++){
					var len = select_conf.label_define_list[i].length;
					temp_conf_html += template.render('custom_label_tr',{'label_tag':select_conf.label_define_list[i].substr(1,len-2)});
				}
				label_define_obj.append(temp_conf_html);
			}
			
			var select_conf_obj = obj.find('.select_conf_list');
			if(select_conf_obj.length > 0 && select_conf.select_conf_list != undefined && select_conf.select_conf_list !=[]){
				var temp_conf_html = '';
				for (var i = 0 ; i < select_conf.select_conf_list.length ; i ++){
					var temp = select_conf.select_conf_list[i];
					if(is_send == 1){
						temp_conf_html += template.render('select_word_cond_tr',{'cond':temp.candi_filter,'sort':temp.sort_mode,'num':temp.select_num});
					} else {
						temp_conf_html += template.render('select_word_cond_tr',{'cond':temp.cond,'sort':temp.sort,'num':temp.num});
					}
				}
				select_conf_obj.append(temp_conf_html);
			}
			
			var price_conf_obj = obj.find('.price_conf_list');
			if(price_conf_obj.length > 0 && select_conf.price_conf_list != undefined && select_conf.price_conf_list !=[]){
				var temp_conf_html = '';
				for (var i = 0 ; i < select_conf.price_conf_list.length ; i ++){
					var temp = select_conf.price_conf_list[i];
					if(is_send==1){
						temp_conf_html += template.render('init_price_tr',{'price':temp.init_price,'cond':temp.candi_filter});
					} else {
						temp_conf_html += template.render('init_price_tr',{'price':temp.price,'cond':temp.cond});
					}
				}
				price_conf_obj.append(temp_conf_html);
			}
			
			var remove_dupli_obj = obj.find('.remove_dupli');
			if(remove_dupli_obj.length > 0 && select_conf.delete_conf != undefined && select_conf.delete_conf !=[]){
				remove_dupli_obj.attr({checked : (select_conf.delete_conf.remove_dupli == 1)? true:false});
			}
			
			var remove_del_obj = obj.find('.remove_del');
			if(remove_del_obj.length > 0 && select_conf.delete_conf != undefined && select_conf.delete_conf !=[]){
				remove_del_obj.attr({checked : (select_conf.delete_conf.remove_del == 1)? true:false});
			}
			
			var remove_cur_obj = obj.find('.remove_cur');
			if(remove_cur_obj.length > 0 && select_conf.delete_conf != undefined && select_conf.delete_conf !=[]){
				remove_cur_obj.attr({checked : (select_conf.delete_conf.remove_cur == 1)? true:false});
			}
		},
		
		clear_select_word_conf:function(obj){
			// 清理选词配置
			var conf_name_obj = obj.find('.conf_name');
			if(conf_name_obj.length > 0){
				conf_name_obj.val("");
			}
			
			var conf_desc_obj = obj.find('.conf_desc');
			if(conf_desc_obj.length > 0){
				conf_desc_obj.val("");
			}
			
			var candi_filter_obj = obj.find('.candi_filter');
			if(candi_filter_obj.length > 0){
				candi_filter_obj.val("");
			}
			
			var label_define_obj = obj.find('.label_define_list tr');
			if(label_define_obj.length > 1){
				for(var i = 1; i <label_define_obj.length ; i ++){
					label_define_obj[i].remove();
				}
			}
			
			var select_conf_obj = obj.find('.select_conf_list tr');
			if(select_conf_obj.length > 1){
				for(var i = 1; i < select_conf_obj.length ; i ++){
					select_conf_obj[i].remove();
				}
			}
			
			var price_conf_obj = obj.find('.price_conf_list tr');
			if(price_conf_obj.length > 1){
				for(var i = 1; i < price_conf_obj.length ; i ++){
					price_conf_obj[i].remove();
				}
			}
			
			var remove_dupli_obj = obj.find('.remove_dupli');
			if(remove_dupli_obj.length > 0){
				remove_dupli_obj.checked = false;
			}
			
			var remove_del_obj = obj.find('.remove_del');
			if(remove_del_obj.length > 0){
				remove_del_obj.checked = false;
			}
			
			var remove_cur_obj = obj.find('.remove_cur');
			if(remove_cur_obj.length > 0){
				remove_cur_obj.checked = false;
			}
		},
		
		set_progress_size:function(){
			var progress_size = parseInt($("#progress_size").val());
			if (progress_size >= 2){
				PT.hide_loading();
			}
			$("#progress_size").val(progress_size+1);
		},
		
		set_item_attr:function(item_attrs){
			PT.CRMSelectWordManager.insert_item_info(item_attrs,0,1);
			PT.CRMSelectWordManager.set_progress_size();
		},
		
		bind_btn_control:function(){
			var default_conf = "default_"+$("#config_oper_type").val()+"_conf";
			var conf_name = $("#select_word_conf #cat_conf_name").val();
			var obj = $("#select_word_conf .bind_default_model");
			if ( conf_name == default_conf	 ||conf_name.indexOf("default_") ==  -1){
				obj.addClass("hide");
			} else {
				obj.removeClass("hide");
			}
		},
		
		set_category_info:function(cat_info){
			PT.CRMSelectWordManager.insert_category_info(cat_info);
			
			PT.CRMSelectWordManager.set_progress_size();
		},
		
		set_select_word_conf:function( cat_id, cat_name, cat_conf, item_conf,is_existed){
			$("#cur_cat_name").html(cat_name);
			$("#model_cat_id").val(cat_id);

			PT.CRMSelectWordManager.insert_select_word_conf($("#cat_select_conf"),cat_conf,1,1);
			PT.CRMSelectWordManager.bind_btn_control();
			
			PT.CRMSelectWordManager.insert_select_word_conf($("#item_select_conf"),item_conf,1,1);
			
			PT.CRMSelectWordManager.item_conf_display(is_existed);
			
			PT.CRMSelectWordManager.event_factory($('#select_word_conf'));
			PT.CRMSelectWordManager.set_progress_size();
		},
		
		set_bind_end_status:function(cat_id,cat_name,conf_name){
			var model_cat_id = $("#model_cat_id").val();
			var cat_list = $("#cat_ids").html().split(" ");
			var temp_index = 0;
			if ( model_cat_id != 0){
				for (var i = 0 ; i < cat_list.length ; i++){
					if (cat_list[i] == model_cat_id){
						temp_index = model_cat_id;
						break;
					}
					if (cat_list[i] == cat_id){
						temp_index = cat_id;
						break;
					}
				}
			}
			if(model_cat_id == 0  || temp_index == model_cat_id){
				 $("#model_cat_id").val(cat_id);
				 $("#cur_cat_name").html(cat_name);
				 $("#cat_select_conf #cat_conf_name").val(conf_name);
			}
			
			PT.alert("保存成功");
			$.fancybox.close();
		},
		
		get_item_info:function(is_clear){
			// 加载宝贝数据
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var cat_id = $("#cur_cat_id").val();
			if(item_id == "0" || shop_id=="0"){
				PT.sendDajax({"function":"crm_get_selectword_item_info","is_manual":true,"cat_id":cat_id,'is_clear':is_clear});
			}else{
				PT.sendDajax({"function":"crm_get_selectword_item_info","item_id":item_id,"is_manual":true,"shop_id":shop_id,'is_clear':is_clear});
			}
		},
		
		send_test_data:function(shop_id,item_id,adg_id,result){
			$("body").append(
				template.render(
					"from_post_submit_model",
					{
						'shop_id':shop_id,
						'item_id':item_id,
						'adg_id':adg_id,
						'conf_name':result.conf_name,
						'conf_desc':result.conf_desc,
						'candi_filter':result.candi_filter,
						'label_define_list':$.toJSON(result.label_define_list),
						'select_conf_list':$.toJSON(result.select_conf_list),
						'price_conf_list':$.toJSON(result.price_conf_list),
						'delete_conf':$.toJSON(result.delete_conf)
					}
				)
			);
			setTimeout(function(){PT.CRMSelectWordManager.prepare_submit_form("temp_form_"+shop_id)},0)
		},
		
		prepare_submit_form:function(id_name){
			var obj = $('#'+id_name);
			if (obj.length < 1){
				PT.CRMSelectWordManager.prepare_submit_form(id_name);
				return
			}
			obj.submit(); 
			obj.remove();
		},	
		
		assign_changeable_items:function(index){
			var size = 10;
			var cat_item_list = $("#cat_item_list").val().split(',');
			/*
			// 该处暂不容错
			if(cat_item_str == ""){
				var cat_id = $("#cur_cat_id").val();
				PT.sendDajax({"function":"crm_get_test_cat_items","cat_id":cat_id});	
				return 
			}
			*/
			
			var item_list = new Array();
			if(item_list.length % 4 != 0 ){
				PT.alert("获取宝贝信息失败。");
				return
			}
			
			for(var i = 0 ; i < cat_item_list.length ; i += 4){
				var temp = new Array();
				for(var j = 0 ; j < 4 ; j++){
					temp.push(cat_item_list[i+j]);
				}
				item_list.push(temp);
			}
			
			// 确定索引
			if(index < 0){
				index = item_list.length % size == 0 ? parseInt(item_list.length / size)-1 : parseInt(item_list.length / size) ;  
			}

			var rest_index = item_list.length - size*index;
			if(rest_index < 0 ){
				index = 0 ;
				rest_index = item_list.length - size*index;
			} 
			
			$("#item_index").val(index);
			
			var max_index = (rest_index > size) ? size :rest_index;
			var is_single = max_index % 2 == 0 ? false : true;
			var row_num = max_index % 2 == 0 ? parseInt(max_index / 2) : parseInt(max_index / 2);  
			var temp_html = "";
			for ( var i = 0; i < row_num ; i++){
				temp_html += "<tr>"
				var td_html =""; 
				for ( var j = 0; j < 2 ; j++){
					var attr_list = item_list[j+i*2+size*index];
					td_html += template.render('change_item_td',{"shop_id":attr_list[0],'item_id':attr_list[1],'pic_url':attr_list[3]})
				}
				temp_html +=  td_html + "</tr>"
			} 
			if (is_single){
				var attr_list = item_list[max_index-1+size*index];
				temp_html +=  "<tr>" +  template.render('change_item_td',{"shop_id":attr_list[0],'item_id':attr_list[1],'pic_url':attr_list[3]}) + "</tr>"
			}
			
			$("#item_list table tbody").html(temp_html);
			
			// 添加事件
			$("#item_list .change_item").click(function(){
				var shop_id = $(this).attr('shop_id');
				var item_id = $(this).attr('item_id');
				var model_type = $("#config_oper_type").val() ;
				PT.show_loading("正在加载宝贝数据");
				PT.sendDajax({"function":'crm_change_item','shop_id':shop_id,'item_id':item_id,'model_type':model_type});
				return false
			});
			
			return true
		},
		
		set_cat_items:function(item_list){
			$("#cat_item_list").val(item_list);
			var index = parseInt($("#item_index").val());
			$("#item_list table tbody").html("");
			PT.CRMSelectWordManager.assign_changeable_items(index);
		},
		
		set_change_item_info:function(item_attrs,item_conf,is_existed){
			// 重置全局变量
			$("#cur_shop_id").val(item_attrs.shop_id);
			$("#cur_item_id").val(item_attrs.item_id);
			$("#cur_adg_id").val(item_attrs.adg_id);
			
			// 变更宝贝搜索信息
			var temp =$("#search_model .search_cond input[search_type=item]");
			temp.val(item_attrs.item_id);
			
			// 修改显示数据
			PT.CRMSelectWordManager.insert_item_info(item_attrs,0,1);
			PT.CRMSelectWordManager.insert_select_word_conf($("#item_select_conf"),item_conf,1,1);
			PT.CRMSelectWordManager.event_factory($('#item_select_conf'));
			
			PT.CRMSelectWordManager.item_conf_display(is_existed);
		},
		
		set_default_conf:function(select_conf){
			PT.CRMSelectWordManager.insert_select_word_conf($("#cat_select_conf"),select_conf,1,1);
			PT.CRMSelectWordManager.event_factory($('#cat_select_conf'));
			PT.CRMSelectWordManager.bind_btn_control();
			
			$("#cur_cat_name").html("通用模板");
		},
		
		set_bind_result:function(){
			$("#cur_cat_name").html("系统绑定");
			PT.alert("绑定成功！");
		},
		
		set_loading_info:function(cat_id, shop_id, item_id, adg_id){
			$("#cur_cat_id").val(cat_id);
			$("#cur_shop_id").val(shop_id);
			$("#cur_item_id").val(item_id);
			$("#cur_adg_id").val(adg_id);
			PT.CRMSelectWordManager.init_loading();
		},
		
		init_loading:function(){
			// 此部分可迁移
			var cat_id = $("#cur_cat_id").val();
			var shop_id = $("#cur_shop_id").val();
			var item_id = $("#cur_item_id").val();
			var model_type = $("#config_oper_type").val() ;
		
			// 初始进度条
			$("#progress_size").val(0);
			
			PT.show_loading("正在加载数据");
			// 加载类目数据
			PT.sendDajax({"function":"crm_get_selectword_category_info","is_manual":true,"cat_id":cat_id});
			
			// 加载宝贝数据
			PT.CRMSelectWordManager.get_item_info(0);
			
			// 加载配置数据
			PT.sendDajax({"function":"crm_get_selectword_conf_info","cat_id":cat_id,'shop_id':shop_id,'item_id':item_id,'model_type':model_type,"is_manual":true});
			
			// 加载宝贝类目宝贝数据
			PT.sendDajax({"function":"crm_get_test_cat_items","cat_id":cat_id ,"is_manual":true});	    
			
			// 加载一级类目信息
			PT.CRMSelectWordManager.load_category_path()
		},
		
		load_category_path:function(){
			var progess = parseInt($("#progress_size").val());
			if(progess > 2){
				var obj_list = $("#cat_select .cat_level");
				for(var i=0 ; i < obj_list.length; i++){
					$(obj_list[i]).html("");
				}
				$("#load_count").val(0);
				$("#cat_level_index").val(0);
				PT.sendDajax({"function":"crm_get_sub_cat","cat_id":0,"pt_obj":"CRMSelectWordManager"});
				setTimeout(function(){
					PT.CRMSelectWordManager.simulate_manual();
				},100);
			} else {
				setTimeout(function(){
					PT.CRMSelectWordManager.load_category_path();
				},500);
			}
		},
		
		hide_category_dictionary:function(index){
			if(index+1 < 4){
				for(var i = index+1 ; i < 4 ;i ++){
					$("#search_model .cat_level[index="+i+"]").parent().hide();
				}
			}
			if(index < 4){
				$("#search_model .cat_level[index="+index+"]").parent().show();
			}
		},
		
		set_sub_cat:function(cat_id_list){
			if(cat_id_list.length < 1){
				return
			}
			
			var index = parseInt($("#cat_level_index").val());
			PT.CRMSelectWordManager.hide_category_dictionary(index);
			
			var obj = $("#search_model .cat_level[index="+index+"]");
			if(obj.length > 0){
				var temp_html = ""
				if(index > 0){
					temp_html =  template.render("cat_level_element",{"cat_id":"all","cat_name":"请选择"});
				}
				for( index in cat_id_list){
					var temp = cat_id_list[index] ;
					temp_html +=  template.render("cat_level_element",{"cat_id":temp.cat_id,"cat_name":temp.cat_name});
				}
				obj.html(temp_html);
			} else {
				PT.alert("异常，请来联系管理员处理。");
			}
		},
		
		set_item_attr_result:function(src){
			$("#word_modifier").text(src);
			PT.alert('保存成功');
		},
		
		set_system_item_info:function(item_attrs){
			PT.CRMSelectWordManager.insert_item_info(item_attrs,1,0);	
			$('.system_parse').show();
			PT.hide_loading();
		},
		
		reset_scource_status:function(){
			$("#word_modifier").text("系统");
			PT.alert("重置成功");
		},
		
		set_add_model_end:function(conf_name){
			var obj = $("#system_default_conf select");
			obj.append("<option>"+conf_name+"</option>");
			obj.find("option").last().click(function(){
				var conf_name = $(this).text();
				PT.confirm("您确定要将通用模板 "+conf_name+" 导入到您当前类目选词配置中吗？",function(conf_name){
					PT.show_loading("正在加载模板");
					PT.sendDajax({"function":"crm_get_default_select_conf","conf_name":conf_name});
				},[conf_name]);
			});
			PT.alert("保存成功");
		},
		
		load_sub_cat:function(cat_id){
			var opar_obj = $("#search_model input[search_type=category]");
			
			if(cat_id == "all"){
				var index = parseInt($("#cat_level_index").val())-2;
				cat_id = $("#search_model .cat_level[index="+index+"]").val();
				PT.CRMSelectWordManager.hide_category_dictionary(index);
			} else{
				PT.sendDajax({"function":"crm_get_sub_cat","cat_id":cat_id,"pt_obj":"CRMSelectWordManager"});
			}

			opar_obj.val(cat_id);
		},
		
		simulate_manual:function(){
			var load_obj = $("#load_count");
			var load_index = parseInt(load_obj.val());
			var cat_ids = $("#cat_ids").text().split(' ');
			if ($("select.cat_level[index="+load_index+"] option").length > 0){
				if(load_index <= cat_ids.length -1){
					$("#cat_level_index").val(load_index+1);
				
					var cat_id = cat_ids[load_index];
					 $(".cat_level[index="+load_index+"]").val(cat_id);
					 
					PT.CRMSelectWordManager.load_sub_cat(cat_id);
					load_obj.val(load_index+1);
					
					setTimeout(function(){
						PT.CRMSelectWordManager.simulate_manual();
					},500);
				} 	
			}else{
				if($("select.cat_level[index="+(load_index-1)+"]").val() == cat_ids[cat_ids.length-1]){
					return
				}
				setTimeout(function(){
					PT.CRMSelectWordManager.simulate_manual();
				},1000);
			}
		}
	}
}()