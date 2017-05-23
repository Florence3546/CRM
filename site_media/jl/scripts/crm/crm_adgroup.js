PT.namespace('CrmAdgroup');
PT.CrmAdgroup = function () {
	var adg_table=null, fixed_header=null;
	var init_table=function (){
		adg_table=$('#adg_table').dataTable({
			"bRetrieve": true, //允许重新初始化表格
			"bPaginate": false,
			"bFilter": false,
			"bInfo": true,
			"bAutoWidth":false,//禁止自动计算宽度
			"sDom":'Tlfrt',
			"oTableTools": {
				"sSwfPath": "/site_media/assets/swf/copy_csv_xls.swf",
				"aButtons": [{
						"sExtends": "copy",
						"fnClick": function ( nButton, oConfig, flash ) {
							this.fnSetText( flash, get_copy_data() );
						},
						"fnComplete": function ( nButton, oConfig, oFlash, sFlash ) {
							if(get_checked_count()>0){
								PT.alert( '复制成功，您可以使用Ctrl+V粘贴复制的内容' );
							}else{
								PT.alert('请先至少选择一个宝贝');
							}
						}
				}],
				"custom_btn_id":"save_as_csv"
			},
			"aoColumns": [
									{"bSortable": false},
									{"bSortable": true},
									{"bSortable": false},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
									{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": false}
								],
			"oLanguage": {
					"sEmptyTable":"没有数据"
			}
		});	
	}
	
	var get_copy_data=function(){
		var data_str='',shop_id_list=[];
		for (var i=0,i_end=adg_table.fnSettings()['aiDisplay'].length;i<i_end;i++){
			var nRow=adg_table.fnGetNodes(i),
				jq_input=$(nRow).find("input[type='checkbox']"),
				shop_id=(jq_input.attr('checked')? jq_input.attr('shop_id'):0);
			if(shop_id && shop_id_list.indexOf(shop_id)==-1){
				shop_id_list.push(shop_id);
				data_str+=shop_id+'\n';
			}
		}
		return data_str;
	}
	
//	var init_select_conf_list = function(){
//		if($("#select_words_operater").css('display') != 'none'){
//			PT.sendDajax({'function':'crm_get_all_selectword_conf','is_manual':true});		
//		}
//	};
	
	var init_dom=function(){
	
		$("#show_kw_count").click(function(){
			var obj_list = $("#adg_table").find('tr');
			if(obj_list.length > 1 ){
				var opar_list = new Array();
				for ( var i = 1 ; i < obj_list.length ; i ++){
					var temp = $(obj_list[i]).find('.kid_box');
					if(temp.length > 0){
						var adg_id = $(temp).val();
						var shop_id = $(temp).attr('shop_id');
						opar_list.push({'adg_id':adg_id,'shop_id':shop_id})
					}
				}
				if (obj_list.length > 0){
					PT.show_loading("加载数据");
					PT.sendDajax({"function":"crm_get_keword_count","adg_list":$.toJSON(opar_list),'is_manual':true});
				} else {
					PT.alert("出错，请联系管理员。");
				}
			} else {
				PT.alert('您尚未搜索出数据');
			}
		
		});
		
		$('#search_top_ratio').click(function(){
			var obj = $('#search_top_ratio_panel');
			if(obj.attr('class').indexOf('hide') != -1) {
				obj.removeClass('hide');
				obj.addClass('show');
			}else{
				obj.removeClass('show');
				obj.addClass('hide');
			}
		});
		
		$('#search_camp_ratio').click(function(){
			var tr_list = $('#adg_table tbody tr .kid_box');
			if(tr_list.length == 0 ){
				PT.alert("没有任何记录，不能进行该操作！");
				return
			}
			var adgroup_id_list = []
			for(var i = 0 ; i < tr_list.length ; i ++){
				adgroup_id_list.push($(tr_list[i]).val());
			}
			var search_type = $('#search_top_ratio_panel [name=search_top_ratio_radio]:checked').val();
			var gte_val =  $('#search_top_ratio_panel .min').val();
			var lte_val =  $('#search_top_ratio_panel .max').val();
			try {
				if(gte_val == '') {
					gte_val = 0 ;
				}
				if(lte_val == ''){
					 lte_val = 100;
				}
				if(gte_val == 0 && lte_val == 100 ){
					PT.alert("请输入关键词比对标准范围！");
					return
				}
				if(parseFloat(gte_val) <= parseFloat(lte_val)){
					PT.show_loading("正在获取数据.....");
					PT.sendDajax({'function':'crm_get_keyword_price_ratio',"search_type":search_type,'gte_val':gte_val,'lte_val':lte_val,'obj_list':$.toJSON(adgroup_id_list),'obj_model':'adgroup'});
				} else {
					PT.alert("输入参数有误！");
					return
				}
			}catch (err){
				PT.alert("输入参数有误！");
				return
			}
		});
		
		$('#adg_control .adg').click(function(){
			var mode=$(this).attr('name'),checkbox_data=get_checkbox_data();
			if (checkbox_data){
				if(mode=='del' && $(".father_box").is(':checked')){
					PT.confirm('即将删除本页所有推广宝贝，删除后都无法恢复，确认要删除吗？',confirm_update_adgs,[mode,checkbox_data]);
				} else {
					confirm_update_adgs(mode,checkbox_data);
				}
			}
		});
		
		//TODO: wangqi 20140909 该方法已可移除
//		$('#adg_control .download').click(function(){
//			var mode=$(this).attr('mode'),adg_list=[];
//			if (mode==0) {
//				var objs=$('#adg_table tbody input:checked');
//				objs.each(function(){
//					var adg_id=parseInt($(this).val());
//					adg_list.push(adg_id);
//				});
//				if (adg_list.length>0) {
//					PT.confirm('您确定要下载'+adg_list.length+'个宝贝的关键词数据',download_keyword,[adg_list]);
//				}
//			}
//			//为了避免下载数据量过大，暂时不支持下载全部宝贝的关键词数据
//		});
		
//		$('.conf_search').click(function(){
//			var conf_name = $('#search_selection_word').val();
//			var shop_id = $('#select_word_shop_id').val();
//			var item_id = $('#select_word_item_id').val();
//			PT.confirm(
//								'当前操作将会覆盖工作区间，您确定要继续吗？',
//								function(conf_name,shop_id,item_id){
//									PT.show_loading('正在加载选词配置');
//									PT.sendDajax({'function':'crm_get_search_selec_conf','conf_name':conf_name,'shop_id':shop_id,'item_id':item_id});
//								},
//								[conf_name,shop_id,item_id]
//							);
//		});
		
//		$('.conf_import').click(function(){
//			var conf_name = $('#search_selection_word').val();
//			PT.confirm(
//								'您确定要导入该项选词到当前配置工作平台吗？',
//								function(conf_name){
//									PT.show_loading('正在加载选词配置');
//									PT.sendDajax({'function':'crm_get_import_selec_conf','conf_name':conf_name});
//								},
//								[conf_name]
//							);
//		});
		
		$('#add_select_words_conf').click(function(){
			var html = template.render('select_words_conf_tr',{'select_word_conf':NaN});
			var obj = $(this).parent().parent().parent().next();
			obj.append(html);
			obj.find("tr .select_wards_conf_delete").last().click(function(){
				$(this).parent().parent().parent().remove();
			});
			obj.find("tr .select_wards_conf_up").last().click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.prev();
				if (before_element.length > 0){
					before_element.insertAfter(obj); 
				}
			});
			obj.find("tr .select_wards_conf_down").last().click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.next();
				if (before_element.length > 0){
					before_element.insertBefore(obj); 
				}
			});
			obj.find("tr .select_wards_conf_add").last().click(PT.CrmAdgroup.set_insert_tr_select_wards);
		});
		
		$('#add_words_price_conf').click(function(){
			var html = template.render('words_price_conf_tr',{'word_price_conf':NaN});
			var obj = $(this).parent().parent().parent().next();
			obj.append(html);
			obj.find("tr .words_price_conf_delete").last().click(function(){
				$(this).parent().parent().parent().remove();
			});
			obj.find("tr .words_price_conf_up").last().click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.prev();
				if (before_element.length > 0){
					before_element.insertAfter(obj); 
				}
			});
			obj.find("tr .words_price_conf_down").last().click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.next();
				if (before_element.length > 0){
					before_element.insertBefore(obj); 
				}
			});
			obj.find("tr .words_price_conf_add").last().click(PT.CrmAdgroup.set_insert_tr_words_price);
		});
		
		$('#add_label_conf').click(function(){
			var html = template.render('label_conf_tr',{'label_conf':''});
			var obj = $(this).parent().parent().parent().next();
			obj.append(html);
			obj.find("tr .label_conf_delete").last().click(function(){
				$(this).parent().parent().parent().remove();
			});
			obj.find("tr .label_conf_up").last().click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.prev();
				if (before_element.length > 0){
					before_element.insertAfter(obj); 
				}
			});
			obj.find("tr .label_conf_down").last().click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.next();
				if (before_element.length > 0){
					before_element.insertBefore(obj); 
				}
			});
			obj.find("tr .label_conf_check").last().click(function(){
				var label_str = "{"+$(this).parent().parent().parent().find(".define_label").val()+"}";
				try{
					var express = eval("("+label_str+")");
				} catch (e) {
					PT.alert('当前标签语法有误！');
					return 
				}
				attr_list = ['type','name','rule','from']
				for (var i = 0 ; i < attr_list.length; i++){
					if( ! (express.hasOwnProperty(attr_list[i])) ){
						PT.alert('当前标签缺少 '+attr_list[i]+' 属性');
						return
					} 	
				}
				
				var shop_id = $('#select_word_shop_id').val();
				var item_id = $('#select_word_item_id').val();
				if (label_str != ""){
					PT.show_loading("正在检查");
					PT.sendDajax({'function':"crm_check_label_is_accurate",'shop_id':shop_id,'item_id':item_id,'label_str':label_str});
				} else {
					PT.alert("当前定义标签不能为空！");
				}
			});
			obj.find("tr .label_conf_add").last().click(PT.CrmAdgroup.set_insert_tr_label_conf);
		});
		
		$('#conf_edit').click(function(){
			var obj= $(this).find('#conf_lock');
			var class_list = obj.attr('class');
			var lock_mark = 'icon-lock';
			var unlock_mark = 'icon-unlock';
			if(class_list.indexOf(lock_mark) > -1){
				$(obj).removeClass(lock_mark);
				$(obj).addClass(unlock_mark);
				PT.CrmAdgroup.clear_clock();
			} else {
				$(obj).removeClass(unlock_mark);
				$(obj).addClass(lock_mark);
				PT.CrmAdgroup.init_clock();
			}
		});
		
//		$('.analyse_item').click(function(){
//			var shop_id = $('#select_word_shop_id').val();
//			var item_id = $('#select_word_item_id').val();
//			PT.show_loading('正在解析宝贝');
//			PT.sendDajax({'function':'crm_analyse_item_info','item_id':item_id,'shop_id':shop_id});
//		});
		
//		$('.test_select_words').click(function(){
//			var shop_id = $('#select_word_shop_id').val();
//			var adgroup_id = $('#select_word_adgroup_id').val();
//			var conf_name = $('#config_name').val();
//			var obj = $(this);
//			obj.attr({'href':'/crm/crm_test_select_words/?conf_name='+conf_name+'&shop_id='+shop_id+'&adgroup_id='+adgroup_id});
//		});
		
//		$('.save_conf').click(function(){
//			var oper_type = $('#config_oper_type option:selected').val();
//			var config_name = $('#config_name').val();
//			if (config_name == ''){
//				PT.alert('\"默认配置名称\" 不能为空。');
//				return 
//			} else {
//				for(index in config_name){
//					var char_code = config_name[index].charCodeAt();
//					if(!(char_code == 95 || (char_code < 123 && char_code > 96) || (char_code < 91 && char_code > 64) )){
//						PT.alert('\"默认配置名称\" 仅能为 英文字符 或 \"_\" 。');
//						return
//					}
//				}
//			}
//			var config_discribe = $('#config_discribe').val();
//			if (config_discribe == ''){
//				PT.alert('\"配置描述\" 不能为空。');
//				return 
//			}
//			
//			// 自定义标签配置
//			var label_define_list = $('#config_label_define .label_conf');
//			var label_conf_list = []
//			for (var i = 0 ; i < label_define_list.length ; i ++){
//				var config_record = $(label_define_list[i]).find('td');
//				var define_label = $(config_record[0]).find('.define_label').val();
//				if(define_label == ''){
//					PT.alert('\"定义标签\" 不能为空 (行'+(i+1)+')。');
//					return
//				}
//				label_conf_list.push('{'+define_label+'}');
//			}
//			
//			// 海选配置
//			var candidate_words = $('#config_candidate_words').val();
//			if (candidate_words == ''){
//				PT.alert('\"候选词条件\" 不能为空。');
//				return 
//			}
//			
//			// 选词配置						
//			var select_word_list = $('#config_select_words .select_word');
//			var select_conf_list = [];
//			for( var i = 0; i < select_word_list.length ; i ++){
//				var config_record = $(select_word_list[i]).find('td');
//				var record_json = {}
//				record_json.candi_filter=$(config_record[0]).find('.candi_filter').val();
//				if (record_json.candi_filter == ''){
//					PT.alert('\"选词配置\" 部分存在未编写的 过滤条件 (行 '+(i+1)+')。');
//					return 
//				}
//				
//				record_json.sort_mode=$(config_record[1]).find('.sort_mode').val();
//				if (record_json.sort_mode == ''){
//					PT.alert('\"选词配置\" 部分存在未编写的 搜索条件 (行 '+(i+1)+')。');
//					return 
//				}
//				
//				record_json.select_num=$(config_record[2]).find('.select_num').val();
//				if (record_json.select_num == ''){
//					PT.alert('\"选词配置\" 部分存在未输入 数目 (行 '+(i+1)+')。');
//					return 
//				} 
//				if (!(parseFloat(record_json.select_num) >= 0&& parseFloat(record_json.select_num) < 200)){
//					PT.alert('\"选词配置\" 部分存在输入 数目 不合法 (行 '+(i+1)+')。');
//					return 	
//				}
//				select_conf_list.push(record_json);
//			}
//			
//			// 初始出价配置
//			var word_price_list = $('#config_price_init .word_price');
//			var price_conf_list = [];
//			for( var i = 0; i < word_price_list.length ; i ++){
//				var config_record = $(word_price_list[i]).find('td');
//				var record_json = {}
//				record_json.candi_filter = $(config_record[0]).find('.candi_filter').val();
//				if ( record_json.candi_filter == ''){
//					PT.alert('\"初始出价配置\" 部分存在未编写的 条件 (行 '+(i+1)+')。');
//					return 
//				}
//				record_json.init_price=$(config_record[1]).find('.init_price').val();
//				if (record_json.init_price == ''){
//					PT.alert('\"初始出价配置\" 部分存在未编写的 出价 (行 '+(i+1)+')。');
//					return 
//				}
//				price_conf_list.push(record_json);
//			}
//			
//			// 删除配置
//			var del_conf_list = $('#select_words_conf .del_words');
//			var del_conf = {}
//			del_conf.remove_dupli = (del_conf_list[0].checked == true) ? 1: 0;
//			del_conf.remove_del = (del_conf_list[1].checked == true) ? 1: 0;
//			del_conf.remove_cur = (del_conf_list[2].checked == true) ? 1: 0;
//			
//			var is_same = ($('#web_return_cat_name').val() == config_name) ? 1 : 0;
//			var oper_level = $('#select_words_conf #oper_level').val();
//			if (oper_level == '0' && is_same== 1){
//				if ($('#optr_user').val() != "cj"){
//					PT.alert("您未有权限修改当前配置，如有需要请联系陈军....");
//					return 
//				}
//				PT.confirm("当前配置作用范围并非仅对该宝贝, 该操作需要慎重，您确认要进行提交吗？",
//						function(config_name,config_discribe,candidate_words,label_conf_list,select_conf_list,price_conf_list,del_conf,is_same){
//							PT.show_loading("正在保存数据");
//							PT.sendDajax({
//											'function':'crm_save_select_words_conf',
//											'oper_name':$('.username').html(),
//											'conf_name':config_name,
//											'conf_desc':config_discribe,
//											'candi_filter':candidate_words,
//											'label_define_list':$.toJSON(label_conf_list),
//											'select_conf_list':$.toJSON(select_conf_list),
//											'price_conf_list':$.toJSON(price_conf_list),
//											'delete_conf':$.toJSON(del_conf),
//											'is_same':is_same
//										});		
//						},
//						[config_name,config_discribe,candidate_words,label_conf_list,select_conf_list,price_conf_list,del_conf,is_same]
//				);
//			} else {
//				PT.show_loading("正在保存数据");
//				PT.sendDajax({
//											'function':'crm_save_select_words_conf',
//											'oper_name':$('.username').html(),
//											'conf_name':config_name,
//											'conf_desc':config_discribe,
//											'candi_filter':candidate_words,
//											'label_define_list':$.toJSON(label_conf_list),
//											'select_conf_list':$.toJSON(select_conf_list),
//											'price_conf_list':$.toJSON(price_conf_list),
//											'delete_conf':$.toJSON(del_conf),
//											'is_same':is_same
//										});		
//			}
//		});
		
//		$('#config_oper_type').change(function(){
//			var shop_id = $('#select_word_shop_id').val();
//			var item_id = $('#select_word_item_id').val();
//			var oper_model = $('#config_oper_type option:selected').val();
//			PT.show_loading('正在加载配置');
//			PT.sendDajax({'function':'crm_swith_select_words_conf','item_id':item_id,'shop_id':shop_id,'oper_model':oper_model});
//		});
		
//		$('.unbind_conf').click(function(){
//			var oper_model = $('#config_oper_type option:selected').val();
//			var shop_id = $('#select_word_shop_id').val();
//			var item_id = $('#select_word_item_id').val();
//			var oper_level = $('#select_words_conf #oper_level').val();
//			if (oper_level != '1'){
//				PT.alert('亲，当前宝贝没有绑定任何选词配置。');
//			} else {
//				PT.show_loading('正在解绑宝贝当前选词配置');
//				PT.sendDajax({'function':'crm_unbind_select_words_conf','shop_id':shop_id,'item_id':item_id,'oper_model':oper_model});
//			}
//		});
		
//		$('.bind_conf').click(function(){
//			var oper_model = $('#config_oper_type option:selected').val();
//			var config_name = $('#config_name').val();
//			var shop_id = $('#select_word_shop_id').val();
//			var item_id = $('#select_word_item_id').val();
//			var oper_type= $(this).attr('save_type');
//			PT.show_loading('正在绑定配置');
//			PT.sendDajax({'function':'crm_bind_select_words_conf','oper_type':oper_type,'shop_id':shop_id,'item_id':item_id,'config_name':config_name,'oper_model':oper_model});
//		});
		
//	   $('.save_attr').click(function(){
//	   		var shop_id = $('#select_word_shop_id').val();
//			var item_id = $('#select_word_item_id').val();
//	   		var save_type = $(this).attr('save_type');
//	   		var attr_val = $(this).parent().find('.attr_val').val();
//	   		PT.show_loading('正在保存该属性');
//	   		PT.sendDajax({'function':'crm_save_attr','save_type':save_type,'shop_id':shop_id,'item_id':item_id,'attr_val':attr_val});
//	   });
	   
		$('#id_send_command').click(function(){
            var objs = $('#adg_table tbody input:checked');
            if(objs.length>0){
	            PT.show_loading('正在加载');
                PT.sendDajax({'function':'crm_open_command_dialog'});
            }
            else{
                PT.alert("请勾选宝贝后再发送命令!");
                return false;
            }
        });
        
        $('#id_check_cmd_history').click(function(){
            PT.sendDajax({'function': 'crm_get_cmd_history'});
        });
        
        $(document).on('click.PT.exec_mnt_task', '.exec_mnt_task', function(){
           PT.sendDajax({'function':'crm_run_mnt_task',"object_id":$(this).attr('id')});
           PT.show_loading('正在执行');
        });
		
		$(document).on('click.PT.add_operate', '.add_operate', function(){
            var func =$(this).siblings().attr('func');
            if($('#operate_'+func).length>0){
                return false;
            }
            var name =$(this).text();//已有操作则不允许再添加！！
            var args = $.evalJSON($(this).siblings().val());
            var temp_name = 'id_operate_template';
            if(func=='optimize_keywords'){
                temp_name = 'id_optimize_template';
                var expand_obj = $('#id_instrcn_list_div .expand');
                if(expand_obj.length>0){
                    $('#id_instrcn_list_div .portlet-body').css('display','block');
                    $('#id_instrcn_list_div .tools a').removeClass('expand');
                    $('#id_instrcn_list_div .tools a').addClass('collapse');
                }
            }else if(func=='add_keywords'){
                temp_name = 'id_addkw_template';
            }
            var html =template.render(temp_name, {'operate':{'name':name, 'func':func, 'args':args}});
            $('#id_operate_list tbody').append(html);
       });
       
       var change_order =function(org_index, new_index, all_obj){
            if(new_index >=$(all_obj).length || new_index <=-1){
                return false;
            }
            if(org_index >new_index){//提升顺序
                $(all_obj).filter(':eq('+org_index+')').after($(all_obj).filter(':eq('+new_index+')'));
            }else if(org_index < new_index){//降低顺序
                $(all_obj).filter(':eq('+org_index+')').before($(all_obj).filter(':eq('+new_index+')'));
            }else{//置顶
                $(all_obj).filter(':eq('+org_index+')').after($(all_obj));
            }
        };
        
        $(document).on('click.PT.sort_up', '.sort', function(){
            var all_obj = $(this).parent().parent().parent().parent().find('tr[name=operation]');
            var index = $(all_obj).index($(this).parent().parent().parent());
            var new_index = index - parseInt($(this).attr('move'));
            change_order(index, new_index, all_obj);
        });
        
        $(document).on('focus.PT.edit_cfg', '.before_edit', function(){
            $(this).removeClass('before_edit').addClass('edit_cfg');
        });
        
        $(document).on('blur.PT.lost_focus', '.edit_cfg', function(){
            $(this).removeClass('edit_cfg').addClass('before_edit');
        });
        
        $(document).on('click.PT.check_instrcn2', '#id_check_instrcn', function(){
           var raw_instrcns = $('#id_instrcn_list_input').val();
           if(raw_instrcns!=''&&raw_instrcns!=undefined&&raw_instrcns!=null){
               var instrcn_list = raw_instrcns.replace(/，/g, ',').split(',');           
               var index = instrcn_list.indexOf('');
               while(index!=-1){
                   instrcn_list.splice(index, 1);
                   index = instrcn_list.indexOf('');
               }
               var cleared_list = new Array();
               for(var i=0;i<instrcn_list.length;i++){
                   var temp_instrcn = instrcn_list[i].trim();
                   if(cleared_list.indexOf(temp_instrcn)==-1){
                       cleared_list.push(temp_instrcn);
                   }
               }
               
               var valid_instrcn_list = new Array();
               $('#id_instrcn_table>tbody>tr').each(function(){
                   if(cleared_list.indexOf($(this).attr('tag_name'))!=-1){
                       $(this).show();
                       $(this).find(':checkbox[name=instrcn_checkbox]').attr('checked', true);
                       valid_instrcn_list.push($(this).attr('tag_name'));
                   }else{
                       $(this).find(':checkbox[name=instrcn_checkbox]').attr('checked', false);
                       $(this).hide();
                   }
               });
               
               if(cleared_list.length>valid_instrcn_list.length){
                   var invalid_list = new Array();
                   for(var j=0;j<cleared_list.length;j++){
                       if(valid_instrcn_list.indexOf(cleared_list[j])==-1){
                           invalid_list.push(cleared_list[j]);
                       }
                   }
                   $('#id_invalid_instrcn').text(invalid_list.toString());
                   $('#id_check_hint').removeClass('hide');
               }else{
                   $('#id_check_hint').addClass('hide');
               }
               $('#id_instrcn_list_input').val(cleared_list.toString());
            }
        });
        
        $(document).on('click.PT.send_cmd', '#id_send_operation' , function(){
            var opt_obj = $('tr[name=operation]');
            if(opt_obj.length>0){
                var opt_list = new Array();
                for(var i=0;i<opt_obj.length;i++){
                    var temp_opt = new Object();
                    temp_opt['func'] = $(opt_obj[i]).attr('id').slice(8);
                    temp_opt['args'] = {};
                    var input_obj = $(opt_obj[i]).find('.args_elem');
                    for(var j=0;j<input_obj.length;j++){
                        var temp_keyname = $(input_obj[j]).attr('key_name');
                        if(temp_keyname=='instrcn_list'){
                            var instrcn_list = $(input_obj[j]).val().split(',');
                            temp_opt['args'][temp_keyname] = instrcn_list;
                        }else{
                            temp_opt['args'][temp_keyname] = $(input_obj[j]).val();
                        }
                    }
                    opt_list.push(temp_opt);
                }
                if(opt_list.length>0){
                    var adg_list = new Array();
                    $('#adg_table tbody input:checked').each(function(){
                        adg_list.push({
                            shop_id:parseInt($(this).attr('shop_id')),
                            campaign_id:parseInt($(this).attr('camp_id')),
                            adgroup_id:parseInt($(this).val())
                        });
                    });
                    PT.confirm("确认对选中的"+adg_list.length+"个宝贝发送命令吗？请不要重复发送！", PT.sendDajax, [{'function':'crm_send_cmd', 'opt_list':$.toJSON(opt_list), 'adg_list':$.toJSON(adg_list)}]);
                }
            }
            else{
                PT.alert("尚未选择任何操作！");
                return false;
            }
        });
		
	}
	
	var get_checkbox_data=function(){
		var result=0,adg_dict={},objs=$('#adg_table tbody input:checked');
		objs.each(function(){
			var shop_id=parseInt($(this).attr('shop_id')),adg_id=parseInt($(this).val());
			if(adg_dict.hasOwnProperty(shop_id)) {
				adg_dict[shop_id].push(adg_id);
			} else {
				adg_dict[shop_id]=[adg_id];
			}
			result=1;
		});
		return (result?adg_dict:false)
	}
	
	var confirm_update_adgs=function (mode,adg_dict){
		var mode_str = (mode=='start' ? '启动推广' : (mode=='stop' ? '暂停推广' : '删除【将在直通车后台消失且无法恢复，不要误删哦】')),
			opt_num=get_checked_count();
		PT.confirm('确认'+mode_str+'所选的'+opt_num+'个宝贝吗？',update_adgs_status,[mode,adg_dict]);
	}
	
	var get_checked_count=function(){
		var checked_num = $('#adg_table tbody input:checked').length;
		$('#current_count').text(checked_num);
		return checked_num;
	}
	
	//改变宝贝的推广状态
	var update_adgs_status=function (mode,adg_dict){
		PT.show_loading("正在提交数据到后台");
		PT.sendDajax({'function':'crm_update_adgs_status','adg_dict':$.toJSON(adg_dict),'mode':mode});
	}

//	var download_keyword=function(adg_list){
//		PT.show_loading('正在下载关键词数据');
//		PT.sendDajax({'function':'crm_bulk_download_keyword','adg_list':$.toJSON(adg_list)});
//	}
	
	var ajax_init_dom=function(){
		// 添加全选事件
		PT.CrmCondition.add_all_selected_envent();
		
		$('.group-checkable.father_box').attr('checked',null);
		
		$('.show_creative_box').click(function () {
//			PT.show_loading("正在加载数据");
			var obj=$(this).parent().parent().parent().find('.kid_box');
//			var shop_id = obj.attr('shop_id');
//			var adgroup_id = obj.val();
			PT.CreativeBox.show_creative_box('crm', obj.attr('shop_id'), obj.attr('camp_id'), obj.val(), obj.attr('item_id'));
//			var rpt_days = $("#change_rpt_days").val();
//			var temp = $("#curr_adgroup");
//			temp.val(adg_id);
//			temp.attr('shop_id',shop_id);
//			PT.sendDajax({'function':'crm_show_creative','shop_id':shop_id,'adg_id':adg_id,"rpt_days":rpt_days});
		});
		
//		$('#change_rpt_days').change(function(){
//			PT.show_loading("正在加载数据");
//			var rpt_days = $(this).val();
//			var temp = $("#curr_adgroup");
//			var adg_id = temp.val();
//			var shop_id = temp.attr('shop_id');
//			PT.sendDajax({'function':'crm_show_creative','shop_id':shop_id,'adg_id':adg_id,'rpt_days':rpt_days});
//		});
				
		$('.open_charts').click(function(){
			var obj=$(this).parent().parent().parent().find('.kid_box');
			var shop_id = obj.attr('shop_id');
			var adg_id = obj.val();
			PT.sendDajax({'function':'crm_show_trend','shop_id':shop_id,'obj_id':adg_id,'get_type':3});	
		});
	
		App.initTooltips();
		
		$(window).on('scroll.PT.Table',function(){
			if(adg_table==undefined){
				return;
			}		
			var body_ofset = document.body.scrollTop | document.documentElement.scrollTop,
				body_ofset_left = document.body.scrollLeft | document.documentElement.scrollLeft,
				base_top=adg_table.offset().top-40;
			if (body_ofset>base_top&&base_top>0){
				$('#fixed_div').addClass('active').css({'marginLeft':-body_ofset_left+43,'width':$('#fixed_div').parent().width()});
				if(fixed_header==undefined){
					fixed_header=new FixedHeader(adg_table,{"offsetTop":40});
				}
			}else{
				$('#fixed_div').removeClass('active').css({'marginLeft':0,'width':'auto'});
				if(fixed_header!=undefined){
					$(fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
				}
				fixed_header=null;
			}
		});
		
//		$('.repair_data').click(function(){
//			
//			var data_type=$(this).attr('data_type'),objs=$('#adg_table tbody input:checked'),repair_list=[];
//			if (data_type==0) {
//				objs.each(function(){
//					var shop_id=parseInt($(this).attr('shop_id'));
//					if(repair_list.indexOf(shop_id)==-1) {
//						repair_list.push(shop_id);
//					}
//				});
//			} else {
//				data_dict={};
//				objs.each(function(){
//					var camp_id=parseInt($(this).attr('camp_id')),shop_id=$(this).attr('shop_id');
//					if (!data_dict.hasOwnProperty(shop_id)) {
//						data_dict[shop_id]=[camp_id];
//					} else if (data_dict[shop_id].indexOf(camp_id)==-1) {
//						data_dict[shop_id].push(camp_id);
//					}
//				});
//				for (var key in data_dict) {
//					repair_list.push([parseInt(key),data_dict[key]]);
//				}
//			}
//
//			if (repair_list.length>0) {
//				PT.confirm('您确定要修复'+objs.length+'个宝贝的'+(data_type==1?'报表':'结构')+'数据',repair_data,[repair_list,data_type]);
//			}
//		});
		
		$(".clear_shop_items").click(function(){
			var shop_id = $(this).parent().parent().parent().find('.kid_box').attr('shop_id');
			if(shop_id != undefined && shop_id != ''){
				PT.show_loading('正在提交信息');
				PT.sendDajax({'function':'crm_clear_shop_items_cache','shop_id':shop_id});
			} else {
				PT.alert('出错，请联系管理员。');
			}
		});
		
		$('.jump').click(function(){
			var shop_id_arr=[], camp_id_arr=[], adg_id_arr=[], obj=null;
			if ($(this).hasClass('single')) {
				obj=$(this).parents('tr').find('input.kid_box');
			} else {
				obj=$('#adg_table tbody input:checked');
			}
			obj.each(function(){
				adg_id_arr.push(parseInt($(this).val()));
				var shop_id=parseInt($(this).attr('shop_id')),camp_id=parseInt($(this).attr('camp_id'));
				if(shop_id_arr.indexOf(shop_id)==-1) {
					shop_id_arr.push(shop_id);
				}
				if(camp_id_arr.indexOf(camp_id)==-1) {
					camp_id_arr.push(camp_id);
				}
			});
			if (adg_id_arr.length<1) {
				PT.alert('请至少选择一条记录');
				return
			}
			var action_str='/crm/'+$(this).attr('target_url')+'/',
				id_dict={'account':shop_id_arr,'campaign':camp_id_arr,'adgroup':adg_id_arr};
			$('input[name="id_dict"]').val($.toJSON(id_dict));
			$('input[name="is_jump"]').val($('#base_is_jumped').val());
			$('#jump_form').attr({action:action_str});
			$('#jump_form').submit();
		});
		
		// 复选框事件
		$('.father_box').click(function(){
			var area_id=$(this).attr('link'),
				kid_box=$('#'+area_id).find('input[class*="kid_box"]'),
				now_check=this.checked;
			kid_box.each(function(){
				if (this.checked!=now_check) {
					this.checked=now_check;
					$(this).parent().toggleClass('check_box_color');
				}
			});
			get_checked_count();
		});   
		
		$('input[class*="kid_box"]').click(function(){
			$(this).parent().toggleClass('check_box_color');
			get_checked_count();
		}); 
		
		$select({name: 'result_item','callBack': update_checked_status});
		adg_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
			'fn':function(){selectRefresh();},
			'sName':'refresh_select'	
		});
		
//		$('.get_word_conf').click(function(){
//			var obj = $(this).parent().parent().parent().find('.kid_box');
//			var shop_id = parseInt(obj.attr('shop_id'));
//			var adgroup_id = parseInt(obj.val());
//			$('#config_oper_type option[value=quick_select]').attr({'selected':'selected'});
//			$('#search_selection_word').val('');
//			if (shop_id > 0 && adgroup_id > 0){
//				PT.show_loading('正在加载选词配置');
//				PT.sendDajax({'function':'crm_get_select_words_conf','adgroup_id':adgroup_id,'shop_id':shop_id,'model_type':'quick_select'});
//			} else {
//				PT.alert('页面获取参数失败，请联系管理员。');
//			}
//		});
	}
	
	var update_checked_status=function(){
		var kid_box=$('input[class*="kid_box"]');
		kid_box.each(function(){
			if ($(this).attr("checked")=="checked") {
				$(this).parent().addClass('check_box_color');
			} else {
				$(this).parent().removeClass('check_box_color');
			}
		});
		get_checked_count();
	}
	
//	var repair_data=function(repair_list,data_type){
//		PT.show_loading('正在修复'+(data_type==1?'报表':'结构')+'数据');
//		PT.sendDajax({'function':'crm_repair_data','data_type':data_type,'obj_type':2,'repair_list':$.toJSON(repair_list)});
//	}
	
	var handle_page=function(page_count,page_no){
		
		$('#dynamic_pager').bootpag({
				total: page_count,
				page: page_no,
				leaps: false,
				prev:'上一页',
				next:'下一页',
				maxVisible: 10 
		}).on('page', function(event, num){
				PT.CrmCondition.get_filter_result(num);
		});
	}
	
	return {
		
		init:function(){
			PT.Base.set_nav_activ('crm_adgroup');
			init_dom();
//			init_select_conf_list();
//			setInterval(init_select_conf_list,60000);
		},
		
		call_back:function(data,page_info){
			var temp_str='';
			for (var i=0;i<data.length;i++){
				data[i].index=i+1;
				temp_str += template.render('adg_table_tr', data[i]);
			}
			if(adg_table){
				adg_table.fnDestroy();
				$('#adg_table tbody tr').remove();
			}
			$('#adg_table tbody').html(temp_str);
			init_table();
			
			get_checked_count();
			$('.page_size').text(page_info['page_size']);
			$('.page_count').text(page_info['page_count']);
			$('.total_count').text(page_info['total_count']);
			$('.account_count').text(page_info['statistics_list'][0]);
			$('.camp_count').text(page_info['statistics_list'][1]);
			
			if (!$('#dynamic_pager ul').length){
					handle_page(page_info['page_count'],page_info['page_no']);		
			}
			ajax_init_dom();
			PT.hide_loading();
		},
		
		bind_select_conf_action:function(del_obj,up_obj,down_obj){
			$(del_obj).click(function(){
				$(this).parent().parent().parent().remove();
			});
			$(up_obj).click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.prev();
				if (before_element.length > 0){
					before_element.insertAfter(obj); 
				}
			});
			$(down_obj).click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.next();
				if (before_element.length > 0){
					before_element.insertBefore(obj); 
				}
			});
		},
		
		set_insert_tr_words_price:function(){
			var cur_obj = $(this).parent().parent().parent();
			cur_obj.after(template.render('words_price_conf_tr',{'word_price_conf':NaN}));
			var next_obj = cur_obj.next();
			$(next_obj).find(".words_price_conf_add").click(
				PT.CrmAdgroup.set_insert_tr_words_price
			);
			$(next_obj).find(".words_price_conf_delete").click(function(){
				$(this).parent().parent().parent().remove();
			});
			$(next_obj).find(".words_price_conf_up").click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.prev();
				if (before_element.length > 0){
					before_element.insertAfter(obj); 
				}
			});
			$(next_obj).find(".words_price_conf_down").click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.next();
				if (before_element.length > 0){
					before_element.insertBefore(obj); 
				}
			});
		},
		
		set_insert_tr_label_conf:function(){
			var cur_obj = $(this).parent().parent().parent();
			cur_obj.after(template.render('label_conf_tr',{'label_conf':''}));
			var next_obj = cur_obj.next();
			$(next_obj).find(".label_conf_add").click(
				PT.CrmAdgroup.set_insert_tr_label_conf
			);
			$(next_obj).find(".label_conf_delete").click(function(){
				$(this).parent().parent().parent().remove();
			});
			$(next_obj).find(".label_conf_up").click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.prev();
				if (before_element.length > 0){
					before_element.insertAfter(obj); 
				}
			});
			$(next_obj).find(".label_conf_down").click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.next();
				if (before_element.length > 0){
					before_element.insertBefore(obj); 
				}
			});
			$(next_obj).find(".label_conf_check").click(function(){
				var label_str = "{"+$(this).parent().parent().parent().find(".define_label").val()+"}";
				try{
					var express = eval("("+label_str+")");
				} catch (e) {
					PT.alert('当前标签语法有误！');
					return 
				}
				attr_list = ['type','name','rule','from']
				for (var i = 0 ; i < attr_list.length; i++){
					if( ! (express.hasOwnProperty(attr_list[i])) ){
						PT.alert('当前标签缺少 '+attr_list[i]+' 属性');
						return
					} 	
				}
				
				var shop_id = $('#select_word_shop_id').val();
				var item_id = $('#select_word_item_id').val();
				if (label_str != ""){
					PT.show_loading("正在检查");
					PT.sendDajax({'function':"crm_check_label_is_accurate",'shop_id':shop_id,'item_id':item_id,'label_str':label_str});
				} else {
					PT.alert("当前定义标签不能为空！");
				}
			});
		},
		
		set_insert_tr_select_wards:function(){
			var cur_obj = $(this).parent().parent().parent();
			cur_obj.after(template.render('select_words_conf_tr',{'select_word_conf':NaN}));
			var next_obj = cur_obj.next();
			$(next_obj).find(".select_wards_conf_add").click(
				PT.CrmAdgroup.set_insert_tr_select_wards
			);
			$(next_obj).find(".select_wards_conf_delete").click(function(){
				$(this).parent().parent().parent().remove();
			});
			$(next_obj).find(".select_wards_conf_up").click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.prev();
				if (before_element.length > 0){
					before_element.insertAfter(obj); 
				}
			});
			$(next_obj).find(".select_wards_conf_down").click(function(){
				var obj = $(this).parent().parent().parent();
				var before_element = obj.next();
				if (before_element.length > 0){
					before_element.insertBefore(obj); 
				}
			});
		},
		
		set_empty_select_conf:function(){
			$('#web_return_cat_name').val('');
			$('#oper_level').val(1);
			$('#config_name').val('');
			$('#config_discribe').val('');
			$('#config_candidate_words').val('');
			$('#config_select_words tbody').html('');
			$('#config_price_init tbody').html('');
			$('#config_label_define tbody').html('');
			$('#remove_dupli').attr({checked : 0});
			$('#remove_del').attr({checked : 0});
			$('#remove_cur').attr({checked : 0});
		},
		
		set_select_conf_info:function(select_conf,flag){
			// 初始化选词部分
			if (flag == true){
				$('#web_return_cat_name').val(select_conf.conf_name);
				$('#oper_level').val(select_conf.oper_level);			
				$('#config_name').val(select_conf.conf_name);
			}
			
			// 选词配置
			$('#config_discribe').val(select_conf.conf_desc);
			var candidate_len = select_conf.candi_filter.length;
			$('#config_candidate_words').val(select_conf.candi_filter.substr(1,candidate_len-2));
			var select_words_html = '';
			for (var i = 0 ; i < select_conf.select_conf_list.length ; i ++){
				select_words_html += template.render('select_words_conf_tr',{'select_word_conf':select_conf.select_conf_list[i]});
			}
			$('#config_select_words tbody').html(select_words_html);
			
			var words_price_conf_html = '';
			for (var i = 0 ; i < select_conf.price_conf_list.length ; i ++){
				words_price_conf_html += template.render('words_price_conf_tr',{'word_price_conf':select_conf.price_conf_list[i]});
			}
			$('#config_price_init tbody').html(words_price_conf_html);
			
			var label_conf_html = '';
			for (var i = 0 ; i < select_conf.label_define_list.length ; i ++){
				var len = select_conf.label_define_list[i].length;
				label_conf_html += template.render('label_conf_tr',{'label_conf':select_conf.label_define_list[i].substr(1,len-2)});
			}
			$('#config_label_define tbody').html(label_conf_html);
			
			$('#remove_dupli').attr({checked : (select_conf.delete_conf.remove_dupli == 1)? true:false});
			$('#remove_del').attr({checked : (select_conf.delete_conf.remove_del == 1)? true:false});
			$('#remove_cur').attr({checked : (select_conf.delete_conf.remove_cur == 1)? true:false});
			
			// 绑定事件
			PT.CrmAdgroup.bind_select_conf_action($("#config_price_init tr .words_price_conf_delete"),$("#config_price_init tr .words_price_conf_up"),$("#config_price_init tr .words_price_conf_down"))
			$("#config_price_init tr .words_price_conf_add").click(PT.CrmAdgroup.set_insert_tr_words_price);
			PT.CrmAdgroup.bind_select_conf_action($("#config_label_define tr .label_conf_delete"),$("#config_label_define tr .label_conf_up"),$("#config_label_define tr .label_conf_down"));
			$("#config_label_define tr .label_conf_add").click(PT.CrmAdgroup.set_insert_tr_label_conf);
			PT.CrmAdgroup.bind_select_conf_action($("#config_select_words tr .select_wards_conf_delete"),$("#config_select_words tr .select_wards_conf_up"),$("#config_select_words tr .select_wards_conf_down"));
			$("#config_select_words tr .select_wards_conf_add").click(PT.CrmAdgroup.set_insert_tr_select_wards);
		},
		
		set_select_conf_interface:function(select_conf,msg){
			PT.CrmAdgroup.set_select_conf_info(select_conf,true);
			PT.hide_loading();
			PT.alert(msg);
		},
		
		set_empty_select_conf_interface:function(msg){
			PT.CrmAdgroup.set_empty_select_conf();
			PT.hide_loading();
			PT.alert(msg);
		},

		init_clock:function(){
			$('#conf_lock').attr({'class':'icon-lock'});
			$('#select_words_conf input[type="text"]').attr({'disabled':'disabled'});
			$('#select_words_conf input[type="checkbox"]').attr({'disabled':'disabled'});
			$('#select_words_conf textarea').attr({'disabled':'disabled'});
		},
		
		clear_clock:function(){
			$('#conf_lock').attr({'class':'icon-unlock'});
			$('#select_words_conf input[type="text"]').removeAttr('disabled');
			$('#select_words_conf input[type="checkbox"]').removeAttr('disabled');
			$('#select_words_conf textarea').removeAttr('disabled');
		},
		
//		set_item_attrs_info:function(item_attrs){
//			$('#product_words').val(item_attrs.pro_info);
//			$('#sale_words').val(item_attrs.sale_info);
//			$('#decorate_words').val(item_attrs.deco_info);
//			$('#black_words').val(item_attrs.black_info);
//			$('#word_modifier').text(item_attrs.word_modifier);
//			$('#include_words').val(item_attrs.include_list);
//		},
	
		save_conf_success:function(conf_text){
			PT.CrmAdgroup.init_clock();
			$('#web_return_cat_name').val(conf_text);
			PT.alert("选词配置保存成功！");
		},
		
		set_all_selectword_conf:function(all_conf){
			var value = '[';
			for (var i = 0 ; i < all_conf.length -1 ; i++){
				value += '\"'+all_conf[i]+'\",' ;
			}
			value += '\"' + all_conf[all_conf.length -1]+'\"]';
			if(value != $('#search_selection_word').attr('data-source')){
				$('#search_selection_word').attr('data-source',value);
			}
		},
			
		set_select_word_conf:function(item_attrs,select_conf){
			// 初始化操作类型
			$('#config_oper_type option[value=quick_select]').attr({'selected':'selected'})
			// 属性配置
			$('#item_url').attr({'href':'http://item.taobao.com/item.htm?id='+item_attrs.item_id});
			$('#item_img').attr({'src':item_attrs.pic_url});
			$('#item_desc').text(item_attrs.title);
			$('#select_word_shop_id').val(item_attrs.shop_id);
			$('#select_word_item_id').val(item_attrs.item_id);
			$('#select_word_adgroup_id').val(item_attrs.adgroup_id);
//			PT.CrmAdgroup.set_item_attrs_info(item_attrs);
			// 设置跳转链接
			var attr_list = ['prodword','saleword','metaword','synoword','forbidword','includeword','elemword'] ;
			for (var i = 0 ; i < attr_list.length ; i ++){
				$(".jump_"+attr_list[i]).attr('href','/crm/kw_manage?shop_id='+item_attrs.shop_id+'&item_id='+item_attrs.item_id+'&jump_type='+attr_list[i]);
			}
			
			// 选词配置
			$('#cat_name').text(select_conf.cat_name);
			PT.CrmAdgroup.set_select_conf_info(select_conf,true);
			
			// 初始化编辑锁
			PT.CrmAdgroup.init_clock();
			
			PT.hide_loading();
			$.fancybox.open(
			     		[
			     			{
			     				href:'#select_words_operater',
			     				padding:10,
			     				afterClose:function(){
								}
			     			}
			     		]
			   );
		},
		
		update_adgs_back:function(mode,success_id_list, cant_del_list, ztc_del_count, error_msg){
			PT.hide_loading();
			switch(mode){
				case 'start':
					for(var i=0; i<success_id_list.length; i++) {
						$('#status_'+success_id_list[i]).text('推广中').removeClass('alert-error').addClass('alert-info');
					}
					break;
				case 'stop':
					for(var i=0; i<success_id_list.length; i++) {
						$('#status_'+success_id_list[i]).text('已暂停').addClass('alert-error').removeClass('alert-info');
					}
					break;
				case 'del':
					for(var i=0; i<success_id_list.length; i++) {
						$('#status_'+success_id_list[i]).parents('tr').remove();
					}
					var msg = '';
					if(result.error_msg){
						msg = result.error_msg;
					}else{
						if(ztc_del_count>0){
							msg += "您已经在直通车后台删除了"+ztc_del_count+"个推广宝贝";
						}
						msg += cant_del_list.length? ("有"+cant_del_list.length+"个推广宝贝无法删除"):'';
					}
					if(msg){
						PT.alert(msg);
					}
					break;
			}
		},
		
		deal_bind_result:function(conf_name,type){
			PT.hide_loading();
			if(type == 'item'){
				$('#web_return_cat_name').val(conf_name);
				$('#select_words_conf #oper_level').val(1);
				PT.alert("配置名称："+conf_name+" 已成功绑定到 宝贝 .");
			} else {
				PT.alert("配置名称："+conf_name+" 已成功绑定到 类目 .");
			}
		},
		
//		download_keyword_back:function(succ_adg_list,failed_adg_list){
//			PT.hide_loading();
//			var failed_count=failed_adg_list.length,total_count=get_checked_count(),
//				msg='下载结果：成功:'+(total_count-failed_count)+'个,失败:'+failed_count+'个。';
//			PT.alert(msg);
////			for(var i in succ_adg_list) {
////				var jq_tr=$("input[type='checkbox'][value="+succ_adg_list[i]+"]").parents('tr');
////				jq_tr.attr('data-original-title','').removeClass('unreliable_rpt');
////			}
//		},
		
//		repair_data_back:function(failed_count){
//			PT.hide_loading();
//			msg=(failed_count==0?'已修复完数据':'修复数据失败');
//			PT.alert(msg);
//			$('#button_search').click();
//		},
		
//		show_creative_detail:function(data){
//			var obj = $("#creative_container");
//			obj.html("");
//			for(var index in data){
//				var temp_data =data[index] ;
//				obj.append(template.render('show_creative_div',{'create':temp_data}));
//				PT.draw_trend_chart( 'creative_'+temp_data.id , temp_data.category_list, temp_data.series_cfg_list);
//			}
//			if(data.length <= 1){
//				obj.append(template.render('add_creative_div',{}));
//			}
//			
//			$('.add_creative').click(function(){
//				PT.show_loading('正在加载数据');
//				var temp = $("#curr_adgroup");
//				var adg_id = temp.val();
//				var shop_id = temp.attr('shop_id');
//				PT.sendDajax({"function":"crm_get_creative_info","shop_id":shop_id,"adg_id":adg_id});
//			});
//			
//			$('.cancel').click(function(){
//				$("#edit_creative_model").hide();		
//				$("#add_creative_model").show();
//			});
//			
//			$('.commit_creative').click(function(){
//				var temp = $("#curr_adgroup");
//				var adg_id = temp.val();
//				var shop_id = temp.attr('shop_id');
//				var url = $("#select_image .action img").attr('src');
//				var title = $("#creative_title").val();
//				if(url == undefined || url == ""){
//					PT.alert("请选择推广图片");
//				}else if(title == undefined || title == ""){
//					PT.alert("请输入推广创意");
//				}else{
//					PT.show_loading('正在提交数据');
//					PT.sendDajax({"function":"crm_save_creative_info","shop_id":shop_id,"adg_id":adg_id,"url":url,"title":title});
//				}
//			});
//			
//			$('#creative_box').modal();
//		},
		
		set_create_info:function(system_title,img_urls){
			$("#creative_title").val(system_title);
			var temp_html = "";
			for (var i in img_urls){
				temp_html += template.render("image_div",{'img_url':img_urls[i]});
			}
			$("#select_image").html(temp_html);
			$(".selected_div").click(function(){
				var obj = $(this) ;
				var last_obj = obj.parent().find('.action');
				if(last_obj.length>0){
					last_obj.removeClass('action');
					last_obj.css('border','0px');
				}
				obj.css('border','2px solid red');
				obj.addClass('action');
			});
			
			$("#edit_creative_model").show();		
			$("#add_creative_model").hide();
		},
		
		reset_create_info:function(adg_id,num){
			PT.alert('已成功添加'+num+"个创意到当前宝贝。");
			$("input[value="+adg_id+"]").parent().parent().find(".show_creative_box").click();
		},
		
		show_trend:function(adg_id, category_list, series_cfg_list) {
			var adg_title =  $('#adg_table .kid_box[value='+adg_id+']').parent().parent().find('.tooltips').html();
			$('#adg_trend_title').html(adg_title);
			PT.draw_trend_chart( 'adg_trend_chart' , category_list, series_cfg_list);
			$('#modal_adg_trend').modal();
		},
		
		display_cmd_dialog:function(instrcn_list, opt_list){
		    for(var i=0;i<opt_list.length;i++){
		        opt_list[i].args = $.toJSON(opt_list[i].args);
		    }
		    var html = template.render('send_cmd_template', {'instrcn_list':instrcn_list, 'opt_list':opt_list});
		    $('#id_cmd_layer').html(html);
		    $.fancybox.open([{href:'#id_cmd_layer'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false},
            }});
            PT.InstructionList.init_dom();
		},
		
		display_cmd_history:function(userorder_list){
		    var html = template.render('id_cmd_history_template', {'uo_list':userorder_list});
		    $('#id_cmd_history_layer').html(html);
		    $.fancybox.open([{href:'#id_cmd_history_layer'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false},
            }});
		},
		
		set_kw_price_ratio:function(result_dict){
			var obj = $('#adg_table');
			for (adgroup_id in result_dict){
				var temp = obj.find('[value='+adgroup_id+']').parent().parent().find('.price_ratio');
				temp.text(result_dict[adgroup_id]+'%');
				temp.parent().find("span").first().text(result_dict[adgroup_id]);
			}
			var obj = $('#search_top_ratio_panel');
			if(obj.attr('class').indexOf('hide') == -1) {
				obj.removeClass('show');
				obj.addClass('hide');
			}
		},
		
		set_keyword_count:function(result_dict){
			var obj_list  = $("#adg_table tr");
			for(var i = 1;i < obj_list.length ; i++){
				var temp = $(obj_list[i])
				var adg_id = temp.find('.kid_box').val()
				var kw_count = result_dict.hasOwnProperty(adg_id) ? result_dict[adg_id] : 0;
				temp.find('.kw_count').text(kw_count);
			}
			for (adg_id in result_dict) {
				obj_list.find('.kid_box[value='+adg_id+']').parent().parent().find('.kw_count').text(result_dict[adg_id]);
			}
			PT.hide_loading();
		}
		
	}
}()