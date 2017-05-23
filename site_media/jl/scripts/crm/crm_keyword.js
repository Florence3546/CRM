PT.namespace('CrmKeyword');
PT.CrmKeyword = function () {
	
	var hide_column_list=[];
	
	var init_table=function(){
		PT.instance_table=new PT.CrmKeyword.table_obj('common_table','template_common_table_tr');
	}
	
	var init_dom=function(){

//		$('#batch_optimize_btn').click(function(){
//			$('#repair_data').removeClass('open');
//		});
		
		$("#kw_rpt_repair").click(function(){
			var adg_count = parseInt($(".portlet-title .adg_count").text()) ;
			var kw_total_count = parseInt($(".portlet-title .total_count").text()) ;
			var minutes = new Number(adg_count * 2.0 / 60).toFixed(2);
			var msg = "该操作将会修复 "+kw_total_count+" 个关键词数据, 大约需要 "+minutes+" 分钟，您确定要进行该操作吗？"; 
			var confirm_func = function(){
				var is_jumped = $("#base_is_jumped option:selected").val(); 
				var tr_list = $("#common_table tr");
				var temp_dict = {};
				for( var i = 2 ; i < tr_list.length ; i++){
					var obj = $(tr_list[i]);
					var adgroup_id = obj.attr("adgroup_id");
					var camp_id = obj.attr("campaign_id");
					var shop_id =obj.attr("shop_id");
					
					if( shop_id == undefined){
					    continue
					}
					
					if( !temp_dict.hasOwnProperty(shop_id)){
						temp_dict[shop_id] = new Set() 
					}
					temp_dict[shop_id].add(camp_id+" "+adgroup_id);
				} 
				
				var send_dict = {}
				for(var k in temp_dict){
					var temp_list = []
					var count = 0;
					temp_dict[k].forEach(function(adg_info){
						temp_list[count] = adg_info;
						count ++;
					});
					send_dict[k] = temp_list;
				}
				
				PT.show_loading("正在修复关键词数据");
				PT.sendDajax({'function':'crm_repair_yestoday_kwrpt','is_jumped':is_jumped,'send_dict':$.toJSON(send_dict)});
			};
			PT.confirm(msg,confirm_func);
		});
		
//		$('#repair_data').click(function(){
//			$('#batch_optimize_box').removeClass('show');
//		});
		
		
//		$('#id_sys_suggest').click(function(){
//		   var kw_id_list = $.map($('#common_table tbody tr:not(.noSearch)'),function(obj){return parseInt($(obj).attr('id'));});
//		   PT.show_loading('正在获取系统建议');
//		   PT.sendDajax({'function':'crm_get_kw_suggest', 'rpt_days':parseInt($('#base_rpt_day').val()), 'stgy':$('input[name=strategy]').val(), 'keyword_id_list':$.toJSON(kw_id_list)});
//		   $('#id_suggest_box').removeClass('open');
//		});
		
		$('#submit_all_kw').click(function(){
			var is_rpt = parseInt($('#base_is_rpt option:selected').val());
			var obj = $('.tal.tab-content .active');
			var opar_id = obj.attr('id');
			var kw_count = parseInt($('#page_info .total_count').text());
			var is_jumped = parseInt($('#base_is_jumped option:selected').val());
			$('#common_table').find('.kid_box').attr('checked','checked');
			if (kw_count > 0){
				var  all_opar_dict = {} ;
				all_opar_dict.opar_model = opar_id;
				if (opar_id == 'bulk_price'){
					var opar_type = $('#'+opar_id+' [name=\"bulk_radio\"]:checked').val();
					all_opar_dict.opar_type = opar_type;
					if( opar_type == 'plus'  ){
						var update_range = parseFloat($('#bulk_up_price_delta').val());
						var limit_price = parseFloat($('#bulk_up_price_limit').val());
						if (limit_price >= 0.05 && limit_price <=99.99 ){
							if (update_range > 0 ){
								all_opar_dict.limit_price = limit_price;
								all_opar_dict.update_range = update_range;
								var comp_type = $('#bulk_up_price_base option:selected').val();
								all_opar_dict.comp_type = comp_type;
								var ratio_type = $('#bulk_up_price_mode option:selected').val();
								all_opar_dict.ratio_type = ratio_type;
							} else {
								PT.alert('亲，请设置或输入正确的加价幅度。');
								return 
							}
						} else {
							PT.alert('亲，请设置或输入正确的最高限价。');
							return 
						}
					} else if(opar_type == 'fall' ){
						var update_range = parseFloat($('#bulk_fall_price_delta').val());
						var limit_price = parseFloat($('#bulk_fall_price_limit').val());
						if (limit_price >= 0.05 && limit_price <=99.99 ){
							if (update_range > 0 ){
								all_opar_dict.limit_price = limit_price;
								all_opar_dict.update_range = update_range;
								var comp_type = $('#bulk_fall_price_base option:selected').val();
								all_opar_dict.comp_type = comp_type;
								var ratio_type = $('#bulk_fall_price_mode option:selected').val();
								all_opar_dict.ratio_type = ratio_type;
							} else {
								PT.alert('亲，请设置或输入正确的降价幅度。');
								return 
							}
						} else {
							PT.alert('亲，请设置或输入正确的最低限价。');
							return 
						}
					} else if(opar_type == 'custom' ){
						var cus_price = parseFloat($('#custom_price').val());
						if (cus_price > 0.05 && cus_price < 99.99) {
							all_opar_dict.cus_price = cus_price ;
						}else{
							PT.alert('亲，请输入正确的参数。');
							return 
						}
					} else {
						PT.alert('亲，请选择您要执行的操作。');
						return
					}
					PT.instance_table.bulk_price_router();
				}else if (opar_id == 'keyword_del'){
					PT.instance_table.bulk_del()
				}else if (opar_id == 'keyword_match'){
					var match_scope = $('#'+opar_id+' [name=\"bulk_match_radio\"]:checked').val();
					all_opar_dict.match_scope = match_scope;
					PT.instance_table.bulk_match(match_scope);
				}else{
					PT.alert('亲，请选择操作方式。');
					return 
				}
				PT.confirm('此操作是不可逆的，为了慎重起见，您确定要全部提交吗？（如果超出限价，默认限价值。）',submit_all_kw,[all_opar_dict,is_jumped]);
			}else{
				PT.alert('亲，很抱歉，没有关键词可以进行一键提交。');
			}
		});
		
//		$('.repair_data').click(function(){
//			var data_type=$(this).attr('data_type'),objs=$('#common_table tbody input:checked'),repair_list=[];
//			if (data_type==0) {
//				objs.each(function(){
//					var shop_id=parseInt($(this).parents('tr').attr('shop_id'));
//					if(repair_list.indexOf(shop_id)==-1) {
//						repair_list.push(shop_id);
//					}
//				});
//			} else {
//				data_dict={};
//				objs.each(function(){
//					var jq_tr=$(this).parents('tr'),adg_id=parseInt(jq_tr.attr('adgroup_id')),
//						camp_id=parseInt(jq_tr.attr('campaign_id')),shop_id=jq_tr.attr('shop_id');
//					if (data_dict.hasOwnProperty(shop_id)) {
//						data_dict[shop_id].push([adg_id,camp_id]);
//					} else {
//						data_dict[shop_id]=[[adg_id,camp_id]];
//					}
//				});
//				for (var key in data_dict) {
//					repair_list.push([parseInt(key),data_dict[key]]);
//				}
//			}
//
//			if (repair_list.length>0) {
//				PT.confirm('您确定要修复'+objs.length+'个关键词的'+(data_type==1?'报表':'结构')+'数据',repair_data,[repair_list,data_type]);
//			}
//		});
		
	}
	
	var submit_all_kw = function(all_opar_dict,is_jumped){
		PT.sendDajax({'function':'crm_curwords_submit','all_opar_dict':$.toJSON(all_opar_dict),'is_jumped':is_jumped});
		PT.show_loading('正在提交');
	}
	
//	var repair_data=function(repair_list,data_type){
//		PT.show_loading('正在修复'+(data_type==1?'报表':'结构')+'数据');
//		PT.sendDajax({'function':'crm_repair_data','data_type':data_type,'obj_type':4,'repair_list':$.toJSON(repair_list)});
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
			PT.Base.set_nav_activ('crm_keyword');
			init_table();
			init_dom();
		},
		call_back:function(kw_list,page_info){
			if($.fn.DataTable.fnIsDataTable($('#common_table')[0])){
				$(window).off('scroll');
				PT.instance_table.data_table.fnDestroy();
			}

			$('.page_size').text(page_info['page_size']);
			$('.page_count').text(page_info['page_count']);
			$('.total_count').text(page_info['total_count']);
			$('.account_count').text(page_info['statistics_list'][0]);
			$('.camp_count').text(page_info['statistics_list'][1]);
			$('.adg_count').text(page_info['statistics_list'][2]);

			$('#id_curwords_submit').prev().find('span>span').text(0);
			$('#batch_optimize_count').text(0);
			$('.father_box').attr('checked',null);
			var data={'custom_column':PT.CrmKeyword.hide_column_list,'keyword':kw_list};
			PT.instance_table.call_back(data,page_info);
			PT.hide_loading();
		},
		
		handle_page:handle_page,
		hide_column_list:hide_column_list,
		
//		repair_data_back:function(failed_count){
//			PT.hide_loading();
//			msg=(failed_count==0?'已修复完数据':'修复数据失败');
//			PT.alert(msg);
//			$('#button_search').click();
//		},
//		display_suggest_opt:function(result){
//		    PT.hide_loading();
//            var result_obj = $.evalJSON(result);
//            var kw_list = result_obj['keyword_list'];
//            //要根据返回的操作类型修改new_price的样式与值,并将操作理由显示在页面上
//            for(i=0;i<kw_list.length;i++){
//                var temp_kw = kw_list[i];
//                switch(temp_kw['optm_type']){
//                    case 2:{
//                        $('#'+temp_kw['kw_id']).addClass('kw_del');
//                    };
//                    case -1:{
//                        $('#'+temp_kw['kw_id']+' .new_price').val(temp_kw['new_price']);
//                        $('#'+temp_kw['kw_id']+' .new_price').addClass('safe_color');
//                    }
//                    case 1:{
//                        $('#'+temp_kw['kw_id']+' .new_price').val(temp_kw['new_price']);
//                        $('#'+temp_kw['kw_id']+' .new_price').addClass('m_color');
//                    }
//                }
//                //添加理由
//                $('#'+temp_kw['kw_id']+ ' td:eq(2) span').append('<i class="icon-info-sign yellow tooltips" data-placement="top" data-original-title="'+temp_kw['optm_reason']+'"></i>');
//            }
//            PT.instance_table.calc_action_count();
//            App.initTooltips();
//		},
		show_trend:function(kw_id, category_list, series_cfg_list) {
			var kw_word=  $('#word_'+kw_id).text();
			$('#kw_trend_title').text('\"'+kw_word+'\"');
			PT.draw_trend_chart( 'kw_trend_chart' , category_list, series_cfg_list);
			$('#modal_kw_trend').modal();
		},
		set_freeze_status:function(kw_id,flag){
			var obj = $('#common_table tr[id='+kw_id+'] .lock_keyword');
			var mark_lock = 'icon-lock';
			var mark_unlock = 'icon-unlock';
			if (flag == 1){
				obj.removeClass(mark_lock);
				obj.addClass(mark_unlock);
			} else {
				obj.removeClass(mark_unlock);
				obj.addClass(mark_lock);
			}
		},
		
		repair_yestoday_kwrpt_back:function(kw_id,flag){
			PT.show_loading('正在查询数据');
			PT.CrmCondition.get_filter_result(1);
		}
	}
}();


//继承PT.Table.BaseTableObj的属性
PT.CrmKeyword.table_obj=function(table_id,temp_id){
	PT.Table.BaseTableObj.call(this,table_id,temp_id);	
}

//继承PT.Table.BaseTableObj的属性方法
PT.CrmKeyword.table_obj.prototype=PT.Table.BaseTableObj.prototype;

PT.CrmKeyword.table_obj.prototype.get_keyword_data=function(){		
	return false; //默认改页面不需要主动获取数据
}


PT.CrmKeyword.table_obj.prototype.sort_table=function(custom_column){
	PT.console('begin dataTable:'+this.table_id);
	var that=this,custom_aoColumns;
	custom_aoColumns=[
			{"bSortable": true,"sSortDataType": "custom-text", "sType": "custom","sClass": "no_back_img tac"},
			{"bSortable": false},
			{"bSortable":  true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": false,"sClass": 'tac'},
			{"bSortable": true,"sClass": 'tac', "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"}
		];
	
	if(custom_column==''||custom_column==undefined){
		custom_column=this.DEFAULT_HIDE_COLUMN;
	}
	
	if(String(custom_column).indexOf('all')!=-1){ //区分于默认显示项目
		custom_column=[];
	}
	
	for (var i in custom_column){
		custom_aoColumns[this.COLUM_DICT[custom_column[i]]]['bVisible']=false;
	}
	
	
	this.data_table=this.table_obj.dataTable({
		"bRetrieve": true, //允许重新初始化表格
		"bPaginate": false,
		"bFilter": false,
		"bInfo": false,
		"bAutoWidth":false,//禁止自动计算宽度
		"sDom": 'Tlfrtip',
		"oTableTools": {
			"sSwfPath": "/site_media/assets/swf/copy_csv_xls.swf",
			"aButtons": [{
                    "sExtends": "xls",
					'sTitle':that.get_adgroup_title(),
                    "fnClick": function ( nButton, oConfig, flash ) {
                        this.fnSetText( flash, that.creat_scv_data() );
                    }
			}],
			"custom_btn_id":"save_as_csv"
		},
		"aoColumns":custom_aoColumns,
		"fnCreatedRow":this.fnRowCallback,
		"oLanguage": {
			"sZeroRecords": "没有关键词记录"
		}
	});
	this.init_ajax_event();
	this.set_kw_count();
	PT.hide_loading();
	PT.console('end dataTable:'+this.table_id);
}

PT.Table.BaseTableObj.prototype.sort_table=function(custom_column){
	PT.console('begin dataTable:'+this.table_id);
	var that=this,custom_aoColumns;
	custom_aoColumns=[
			{"bSortable": true,"sSortDataType": "custom-text", "sType": "custom","sClass": "no_back_img tac"},
			{"bSortable": false},
			{"bSortable":  true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": false,"sClass": 'tac'},
			{"bSortable": true,"sClass": 'tac', "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
			{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"}
		];
	
	if(custom_column==''||custom_column==undefined){
		custom_column=this.DEFAULT_HIDE_COLUMN;
	}
	
	if(String(custom_column).indexOf('all')!=-1){ //区分于默认显示项目
		custom_column=[];
	}
	
	for (var i in custom_column){
		custom_aoColumns[this.COLUM_DICT[custom_column[i]]]['bVisible']=false;
	}
	
	
	this.data_table=this.table_obj.dataTable({
		"bRetrieve": true, //允许重新初始化表格
		"bPaginate": false,
		"bFilter": false,
		"bInfo": false,
		"bAutoWidth":false,//禁止自动计算宽度
		"sDom": 'Tlfrtip',
		"oTableTools": {
			"sSwfPath": "/site_media/assets/swf/copy_csv_xls.swf",
			"aButtons": [{
                    "sExtends": "xls",
					'sTitle':that.get_adgroup_title(),
                    "fnClick": function ( nButton, oConfig, flash ) {
                        this.fnSetText( flash, that.creat_scv_data() );
                    }
			}],
			"custom_btn_id":"save_as_csv"
		},
		"aaSorting": [[ 8, "desc" ],[ 7, "desc" ],[ 20, "desc" ]],
		"aoColumns":custom_aoColumns,
		"fnCreatedRow":this.fnRowCallback,
		"oLanguage": {
			"sZeroRecords": "没有关键词记录"
		}
	});
	this.init_ajax_event();
	this.set_kw_count();
	PT.hide_loading();
	PT.console('end dataTable:'+this.table_id);
}

//重写后台回调函数
PT.CrmKeyword.table_obj.prototype.call_back=function(json,page_info){
	PT.hide_loading();
	this.layout_keyword(json.keyword,page_info);
	this.sort_table(json.custom_column);
	this.recount_table_width();
}

//填充表格数据
PT.CrmKeyword.table_obj.prototype.layout_keyword=function(json,page_info){
		var temp_str='';
		for (var i=0;i<json.length;i++){
			temp_str += template.render('template_common_table_tr', json[i]);
		}
		this.table_obj.find('tbody tr:not(#nosearch_table)').remove();
		this.table_obj.find('tbody').append(temp_str);

		if (!$('#dynamic_pager ul').length){
				PT.CrmKeyword.handle_page(page_info['page_count'],page_info['page_no']);		
		}
		//ajax_init_dom();
		$('.open_charts').click(function(){
			var obj=$(this).parent().parent().parent().parent().parent();
			var shop_id = obj.attr('shop_id');
			var kw_id = obj.attr('id');
			PT.sendDajax({'function':'crm_show_trend','shop_id':shop_id,'obj_id':kw_id,'get_type':4});	
		});
		$('.lock_keyword').click(function(){
			var obj = $(this);
			var class_fileds = obj.attr('class');
			var val_obj = obj.parent().parent().parent().parent().parent();
			var kw_id = val_obj.attr('id');
			var shop_id = val_obj.attr('shop_id');
			var adgroup_id = val_obj.attr('adgroup_id');
			var mark_lock = 'icon-lock';
			var freeze_flag = 1;
			if (class_fileds.indexOf(mark_lock) != -1){
				freeze_flag = 0;	
			} 
			PT.sendDajax({'function':'crm_update_keyword_freeze_status','shop_id':shop_id,'adg_id':adgroup_id,'kw_id':kw_id,'freeze_flag':freeze_flag});	
		})
		
		PT.hide_loading();
}

//保存用户自定义列
PT.CrmKeyword.table_obj.prototype.save_custom_column=function(){
	var column_list=[],that=this;
	
	$('#select_column li:not([class*="title"]) input').each(function(){
		if(!this.checked){
			for (var i in that.COLUM_DICT){
				if (parseInt(this.value)==that.COLUM_DICT[i]){
					column_list.push(i);
					break;
				}
			}
		}	
	});
	PT.CrmKeyword.hide_column_list=column_list;
}
