PT.namespace('CrmCampaign');
PT.CrmCampaign = function () {
	var camp_table=null,fixed_header=null;

	var init_table=function (){
		camp_table=$('#camp_table').dataTable({
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
								PT.alert('请先至少选择一个计划');
							}
						}
				}],
				"custom_btn_id":"save_as_csv"
			},
			"aoColumns": [{"bSortable": false},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true},
									{"bSortable": true, "sSortDataType":"dom-text", "sType":"numeric"},
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
									{"bSortable": true},
									{"bSortable": false}],
			"oLanguage": {
					"sEmptyTable":"没有数据"
			}
		});
	};

	var get_copy_data=function(){
		var data_str='',shop_id_list=[];
		for (var i=0,i_end=camp_table.fnSettings()['aiDisplay'].length;i<i_end;i++){
			var nRow=camp_table.fnGetNodes(i),
				jq_input=$(nRow).find("input[type='checkbox']"),
				shop_id=(jq_input.attr('checked')? jq_input.attr('shop_id'):0);
			if(shop_id && shop_id_list.indexOf(shop_id)==-1){
				shop_id_list.push(shop_id);
				data_str+=shop_id+'\n';
			}
		}
		return data_str;
	};

	var init_dom=function(){

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
			var tr_list = $('#camp_table tbody tr .kid_box');
			if(tr_list.length === 0 ){
				PT.alert("没有任何记录，不能进行该操作！");
				return;
			}
			var camp_id_list = [];
			for(var i = 0 ; i < tr_list.length ; i ++){
				camp_id_list.push($(tr_list[i]).val());
			}
			var search_type = $('#search_top_ratio_panel [name=search_top_ratio_radio]:checked').val();
			var gte_val =  $('#search_top_ratio_panel .min').val();
			var lte_val =  $('#search_top_ratio_panel .max').val();
			try {
				if(gte_val === '') {
					gte_val = 0 ;
				}
				if(lte_val === ''){
					 lte_val = 100;
				}
				if(gte_val === 0 && lte_val == 100 ){
					PT.alert("请输入关键词比对标准范围！");
					return;
				}
				if(parseFloat(gte_val) <= parseFloat(lte_val)){
					PT.show_loading("正在获取数据.....");
					PT.sendDajax({'function':'crm_get_keyword_price_ratio',"search_type":search_type,'gte_val':gte_val,'lte_val':lte_val,'obj_list':$.toJSON(camp_id_list),'obj_model':'campaign'});
				} else {
					PT.alert("输入参数有误！");
					return;
				}
			}catch (err){
				PT.alert("输入参数有误！");
				return;
			}
		});

		$(document).on('click.PT.save_camp_cfg', '#id_save_camp_cfg', function(){
			var campaign_id = parseInt($('#id_campaign_id').val()),
				shop_id= parseInt($('#id_shop_id').val()),
				jq_inputs = $('#camp_mntcfg').find('input[name="camp_cfg"]:checked'),
				cfg_list = $.map(jq_inputs, function (obj) {
					return obj.value;
				});
			PT.sendDajax({'function':'crm_save_camp_cfg', 'cfg_list':cfg_list, 'shop_id':shop_id, 'campaign_id':campaign_id});
		});

	};

	var ajax_init_dom=function(){
		// 添加全选事件
		PT.CrmCondition.add_all_selected_envent();

		$('.group-checkable.father_box').attr('checked',null);

		$('.open_charts').click(function(){
			var obj=$(this).parent().parent().find('.kid_box');
			var shop_id = obj.attr('shop_id');
			var camp_id = obj.val();
			PT.sendDajax({'function':'crm_show_trend','shop_id':shop_id,'obj_id':camp_id,'get_type':2});
		});

		$('.set_task_cfg').click(function(){
			var obj=$(this).parent().parent().find('.kid_box');
			var shop_id = parseInt(obj.attr('shop_id'));
			var camp_id = parseInt(obj.val());
			PT.sendDajax({'function':'crm_get_camp_mntcfg', 'shop_id':shop_id, 'campaign_id':camp_id});
		});

		App.initTooltips();

		$(window).on('scroll.PT.Table',function(){
			if(camp_table==undefined){
				return;
			}
			var body_ofset = document.body.scrollTop | document.documentElement.scrollTop,
				body_ofset_left = document.body.scrollLeft | document.documentElement.scrollLeft,
				base_top=camp_table.offset().top-40;
			if (body_ofset>base_top&&base_top>0){
				$('#fixed_div').addClass('active').css({'marginLeft':-body_ofset_left+43,'width':$('#fixed_div').parent().width()});
				if(fixed_header==undefined){
					fixed_header=new FixedHeader(camp_table,{"offsetTop":40});
				}
			}else{
				$('#fixed_div').removeClass('active').css({'marginLeft':0,'width':'auto'});
				if(fixed_header!=undefined){
					$(fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
				}
				fixed_header=null;
			}
		});

		//查询日志
		$('.quray_logs').click(function(){
			var camp_id = parseInt($(this).parent().parent().find('.kid_box').val());
			var log_days = parseInt($('#log_days').find('option:checked').val());
			if(camp_id !== undefined && camp_id !== 0 && log_days !==undefined && log_days!==0 ){
				PT.show_loading("正在获取日志记录");
				PT.sendDajax({'function':'crm_get_log_records','camp_id':camp_id,'days':log_days});
			}
		});

//		$('.repair_data').click(function(){
//
//			var data_type=$(this).attr('data_type'),objs=$('#camp_table tbody input:checked'),repair_list=[];
//			if (data_type===0) {
//				objs.each(function(){
//					var shop_id=parseInt($(this).attr('shop_id'));
//					if(repair_list.indexOf(shop_id)==-1) {
//						repair_list.push(shop_id);
//					}
//				});
//			} else {
//				data_dict={};
//				objs.each(function(){
//					var camp_id=parseInt($(this).val()),shop_id=$(this).attr('shop_id');
//					if (data_dict.hasOwnProperty(shop_id)) {
//						data_dict[shop_id].push(camp_id);
//					} else {
//						data_dict[shop_id]=[camp_id];
//					}
//				});
//				for (var key in data_dict) {
//					repair_list.push([parseInt(key),data_dict[key]]);
//				}
//			}
//
//			if (repair_list.length>0) {
//				PT.confirm('您确定要修复'+objs.length+'个计划的'+(data_type==1?'报表':'结构')+'数据',repair_data,[repair_list,data_type]);
//			}
//		});

		$('.jump').click(function(){
			var shop_id_arr=[], camp_id_arr=[], obj=null;
			if ($(this).hasClass('single')) {
				obj=$(this).parents('tr').find('input.kid_box');
			} else {
				obj=$('#camp_table tbody input:checked');
			}
			obj.each(function(){
				camp_id_arr.push(parseInt($(this).val()));
				var shop_id=parseInt($(this).attr('shop_id'));
				if(shop_id_arr.indexOf(shop_id)==-1) {
					shop_id_arr.push(shop_id);
				}
			});
			if (camp_id_arr.length<1) {
				PT.alert('请至少选择一条记录');
				return;
			}
			var action_str='/crm/'+$(this).attr('target_url')+'/',
				id_dict={'account':shop_id_arr,'campaign':camp_id_arr};
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
		camp_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
			'fn':function(){selectRefresh();},
			'sName':'refresh_select'
		});
	};

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
	};

	var get_checked_count=function(){
		var checked_num = $('#camp_table tbody input:checked').length;
		$('#current_count').text(checked_num);
		return checked_num;
	};

//	var repair_data=function(repair_list,data_type){
//		PT.show_loading('正在修复'+(data_type==1?'报表':'结构')+'数据');
//		PT.sendDajax({'function':'crm_repair_data','data_type':data_type,'obj_type':1,'repair_list':$.toJSON(repair_list)});
//	};

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
	};

	return {

		init:function(){
			PT.Base.set_nav_activ('crm_campaign');
			init_dom();
			PT.TaskCfgList.init_dom();
		},

		call_back:function(data,page_info){
			var temp_str='';
			for (var i=0;i<data.length;i++){
				data[i].index=i+1;
				temp_str += template.render('camp_table_tr', data[i]);
			}
			if(camp_table){
				camp_table.fnDestroy();
				$('#camp_table tbody tr').remove();
			}
			$('#camp_table tbody').html(temp_str);
			init_table();

			get_checked_count();
			$('.page_size').text(page_info['page_size']);
			$('.page_count').text(page_info['page_count']);
			$('.total_count').text(page_info['total_count']);
			$('.account_count').text(page_info['statistics_list'][0]);

			if (!$('#dynamic_pager ul').length){
					handle_page(page_info['page_count'], page_info['page_no']);
			}
			ajax_init_dom();
			PT.hide_loading();
		},

		update_camp_back:function(oper, succ_camp_ids, failed_camp_ids) {
			var descr_str=(oper==1?'推广中':'已暂停');
			for (var i=0; i<succ_camp_ids.length; i++){
				var camp_id=succ_camp_ids[i];
				$('#status_'+camp_id).prev().text(oper);
				$('#status_'+camp_id).text(descr_str).toggleClass('alert-error').toggleClass('alert-info');
			}
			if(failed_camp_ids.length > 0){
				var status_descr = (oper == 1? '启用' : '暂停');
				PT.alert(status_descr+"失败"+failed_camp_ids.length+"个计划");
			}
		},

//		repair_data_back:function(failed_count){
//			PT.hide_loading();
//			msg=(failed_count==0?'已修复完数据':'修复数据失败');
//			PT.alert(msg);
//			$('#button_search').click();
//		},

		update_opar_status:function(obj){
			var shop_id = obj.getAttribute('shop_id') ;
			var camp_id = obj.getAttribute('camp_id') ;
			var opar_status = obj.getAttribute('opar_status') ;
			PT.sendDajax({'function':'crm_update_opar_status','shop_id':shop_id,'camp_id':camp_id,'opar_status':opar_status});
		},

		update_opar_status_end:function(camp_id,opar_status){
			var obj = $(".opar[camp_id="+camp_id+"]");
			obj.attr({opar_status:opar_status});
			if (opar_status == '1'){
				obj.text('解除干预') ;
			} else {
				obj.text('人工干预') ;
			}
		},

		update_logshow_status:function(show_list,hide_list,class_name){
			for(var i = 0 ; i < show_list.length; i++){
				for(var k = 0 ; k < show_list[i].length ; k++){
					$(show_list[i][k]).removeClass(class_name);
				}
			}
			for(var i = 0 ; i < hide_list.length; i++){
				for(var k = 0 ; k < hide_list[i].length ; k++){
					$(hide_list[i][k]).addClass(class_name);
				}
			}
		},

		set_log_records:function(shop_id,camp_id,mnt_type,data){
			var html = '';
			for( var i = 0 ; i < data.length ; i++){
				html += template.render("log_record", {'record':data[i]});
			}
			$('#record_content').html(html);

			$('#log_camp_id').val(camp_id);
			$("#log_days").unbind( "change" );
			$("#log_days").change( function(){
				var camp_id = parseInt($('#log_camp_id').val());
				var log_days = parseInt($('#log_days').find("option:selected").val());
				$('#reset_status').attr({'checked':'checked'});
				if(camp_id !== undefined && camp_id !== 0 && log_days !==undefined && log_days!==0 ){
					PT.show_loading("正在获取日志记录");
					PT.sendDajax({'function':'crm_get_log_records','camp_id':camp_id,'days':log_days});
				}
			});

			$("#log_manager .select_filter_type").unbind( "click" );
			$("#log_manager .select_filter_type").click( function(){
				$("#log_manager .select_filter_type").find('.active').removeClass('active');
				var obj = $(this);
				obj.addClass('active');
				var flag = obj.val();
				var class_name = 'hide';
				if (flag == 'all'){
					var log_list = $('#record_content tr[name="crm_log"]');
					PT.CrmCampaign.update_logshow_status([log_list],[],class_name);
				} else {
					var sys_log_list = $('#record_content .sys');
					var user_log_list = $('#record_content .user');
					var aes_log_list = $('#record_content .aes');
					 if(flag == 'sys'){
						PT.CrmCampaign.update_logshow_status([sys_log_list],[user_log_list,aes_log_list],class_name);
					} else if(flag == 'user'){
						PT.CrmCampaign.update_logshow_status([user_log_list],[sys_log_list,aes_log_list],class_name);
					} else if(flag == 'aes'){
						PT.CrmCampaign.update_logshow_status([aes_log_list],[sys_log_list,user_log_list],class_name);
					} else {
					}
				}
			});

			PT.hide_loading();
			$.fancybox.open(
						[
							{
								href:'#log_operater',
								padding:10,
								afterClose:function(){
									$('#reset_status').attr({'checked':'checked'});
								}
							}
						]
			   );
		},

		show_trend:function(camp_id, category_list, series_cfg_list) {
			var camp_title =  $('#camp_table .camp_title[camp_id='+camp_id+']').text();
			$('#camp_trend_title').text(camp_title);
			PT.draw_trend_chart( 'camp_trend_chart' , category_list, series_cfg_list);
			$('#modal_camp_trend').modal();
		},
		display_cfg_dialog:function(result_dict){
			var html = template.render("camp_cfg_template", {'shop_id':result_dict.shop_id, 'campaign_id':result_dict.campaign_id, 'data_list':result_dict.mnt_cfg_list});
			$('#camp_mntcfg').html(html);
			$('#modal_camp_cfg').modal();
		},
		set_kw_price_ratio:function(result_dict){
			var obj = $('#camp_table');
			for (camp_id in result_dict){
				var temp_obj = obj.find('[value='+camp_id+']').parent().parent().find('.price_ratio');
				temp_obj.parent().find('span').first().text(result_dict[camp_id]);
				temp_obj.html('关键词价位占比：'+result_dict[camp_id]+'%');
			}
			var obj = $('#search_top_ratio_panel');
			if(obj.attr('class').indexOf('hide') == -1) {
				obj.removeClass('show');
				obj.addClass('hide');
			}
		}
	};
}();
