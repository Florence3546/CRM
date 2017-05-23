"use strict";
PT.namespace('Adgroup_optimize');
PT.Adgroup_optimize = function () {
	
	var adgroup_id=$('#adgroup_id').val();
	var campaign_id=$('#campaign_id').val();
	var item_id=$('#item_id').val();
	var default_price=$('#default_price_hide').val();
	var help=new Tour({backdrop:true});
	
	var get_last_day=function (){
		return $('#dashboard-report-range').find('input[name="last_day"]').val();
	}
	
	var init_dom=function (){
		
		//点击获取历史删词列表
		$('a[href="#history_keyword_box"]').click(function(){
			if($(this).attr('switch')==undefined){
				PT.show_loading('正在获取已删除的词');
				$.fn.dataTable.fnIsDataTable($('#history_kw_table')[0])?PT.instance_history_table.data_table.fnDestroy():'';
				PT.instance_history_table=new PT.Adgroup_optimize.history_table('history_kw_table','teplate_history_table_tr',adgroup_id);
				PT.instance_history_table.init_history_table();
			}
			$(this).attr('switch',1);
			
			PT.instance_table.unbind_scroll_event();  //禁止删词里面的浮动影响
			PT.instance_history_table.init_history_scroll_event();
		});
		
		//点击获取删词列表
		$('a[href="#keyword_box"]').click(function(){
			if($(this).attr('switch')==undefined){
				//PT.show_loading('正在获取已删除的词');
				PT.instance_table.loading_table();
				$.fn.dataTable.fnIsDataTable($('#common_table')[0])?PT.instance_table.data_table.fnDestroy():'';
				PT.instance_table.get_keyword_data();
			}
			$(this).attr('switch',1);
			PT.instance_table.init_scroll_event();  //启用删词里面的浮动影
			PT.instance_history_table.unbind_history_scroll_event();
		});
		
		$('.help').click(function(){
			help.restart();
		});
        
        $(document).off('click.PT.submit_bword','#id_submit_bword').on('click.PT.submit_bword','#id_submit_bword', function () {
            var word_list = new Array();
            var manual_blackword = $.trim($('#manual_blackword').val());
            $('#id_ban_word_part input:checked').each(function () {
                word_list.push($.trim(this.value));
            });
            if (manual_blackword && $.inArray(manual_blackword, word_list)==-1) {
                word_list.push(manual_blackword);
            }
            if(word_list.length>0){
                PT.sendDajax({'function':'web_submit_bwords', 
                                         'item_id':$('#item_id').val(),
                                         'blackwords':word_list.join(), 
                                         'save_or_update':1,
                                         'common_table_flag':$('#common_table').length
                                         });
                $.fancybox.close();
            } else {
                PT.alert("亲，未选中或输入任何词！");
            }
        });
	}
	
	
//	var get_keyword_data=function(){		
//		PT.sendDajax({'function':'web_adgroup_optimize','adgroup_id':adgroup_id,'last_day':get_last_day(),'strategy_list':get_smart_optimize_argv(),'auto_hide':0});
//	}
	
	var init_table=function(){
		//PT.show_loading('正在获取关键词数据');
		PT.instance_table=new PT.Adgroup_optimize.table_obj('common_table','template_common_table_tr');
	}
	
	var init_help=function(){
		var help_list=[
			{
				element: "#fixed_box .btn-group:first",
				title:'智能优化',
				content: "系统会根据您选择的优化策略等参数自动分析优化建议",
				placement:'top',
				onShow:function(){
					$('.tour-tour').hide();
					setTimeout(function(){$('#smart_optimize_btn').parent().addClass('open');},0)
					
				},
				onShown:function(){
					$('.tour-tour').show();
					$('.tour-tour').css({'left':250,'top':45});
				},
				onHide:function(){
					$('#smart_optimize_btn').parent().removeClass('open');
				}
			},
			{
				element: "#batch_optimiz",
				title:'手工批量优化',
				content: "您可以快速选中一批词，进行批量加价,降价等操作。还能批量选中一批符合条件的词。",
				placement:'top',
				onShow:function(){
					$('.tour-tour').hide();
					setTimeout(function(){$('#batch_optimize_box').addClass('show');},0)
					
				},
				onShown:function(){
					$('.tour-tour').show();
					$('.tour-tour').css({'left':370,'top':45});
				},
				onHide:function(){
					$('#batch_optimize_box').removeClass('show');
				}
			},
			{
				element:'#id_curwords_submit',
				content:'点击这里可以提交您已经优化好的关键词到直通车'
					
			},
			{
				element:'#dashboard-report-range',
				content:'点这里可以改变报表的统计天数'
			}
		];
		PT.help(help_list);		
	}	
	
    return {
        //main function to initiate the module
        init: function () {
			$('ul.main.nav li').eq(1).addClass('active');
           PT.initDashboardDaterange();
		   init_dom();
		   init_table();
        },
		select_call_back: function(value){
			//改变天数的回调函数
			PT.instance_table.loading_table();
			PT.instance_table.data_table.fnDestroy();
			PT.instance_table.get_keyword_data();
		},
		table_callback: function(data){
			PT.instance_table.call_back(data);
		},
		get_last_day:function(){
			return get_last_day;	
		},
		adgroup_id:adgroup_id
		,
		item_id:item_id
		,
		campaign_id:campaign_id
		,
		default_price:default_price
		,
		help:init_help
//		,
//		sync_data_call_back:function(msg){
//			if(msg.indexOf('成功')!=-1){
//				PT.confirm(msg+'，是否刷新页面？',PT.Adgroup_optimize.select_call_back,[],this,'','','',['刷新页面','不用刷新']);
//				return false;
//			}
//			PT.alert(msg)	
//		}
    };

}();











//继承PT.Table.BaseTableObj的属性
PT.Adgroup_optimize.table_obj=function(table_id,temp_id){
	PT.Table.BaseTableObj.call(this,table_id,temp_id);	
}
//继承PT.Table.BaseTableObj的属性方法
PT.Adgroup_optimize.table_obj.prototype=PT.Table.BaseTableObj.prototype;

//填充表格数据
PT.Adgroup_optimize.table_obj.prototype.layout_keyword=function(json){
	PT.console('begin layout keyword');
	var tr_str='',kw_count=json.keyword.length,d;
	tr_str=template.render('template_nosearch',json.nosraech);
	
	for (var i=0;i<kw_count;i++){
		tr_str+=template.render(this.temp_id,json.keyword[i]);
	}


//	this.table_obj.find('tbody tr').remove();
//	this.table_obj.find('tbody').append(tr_str);

	$('tbody',this.table_obj).html(tr_str);
}

//重写后台回调函数
PT.Adgroup_optimize.table_obj.prototype.call_back=function(json){
	
	var that=this;
	if(!$.fn.dataTable.fnIsDataTable(this.table_obj[0])){
		if(json.keyword.length){
			this.recount_table_width(json.custom_column);
			this.layout_keyword(json);
			this.sort_table(json.custom_column);
		}else{
			$('#loading_keyword').hide();
			$('#no_keyword').show();
			PT.Adgroup_optimize.help();
			return;
		}
	}else{//表格已经存在，只改变价格和删词状态
		this.change_price_status_4data(json);
	}
	
	$('#batch_optimize_count').text(0);
	this.layout_bulk_tree(eval(json.bulk_tree_list));
	this.layout_bulk_search(eval(json.bulk_search_list));
	this.calc_action_count();
	this.update_all_style();
	PT.Adgroup_optimize.help();
	
	$('#loading_keyword').hide();
}

//获取关键词列表
PT.Adgroup_optimize.table_obj.prototype.get_keyword_data=function(){		
	PT.sendDajax({'function':'web_adgroup_optimize','adgroup_id':PT.Adgroup_optimize.adgroup_id,'last_day':PT.Adgroup_optimize.get_last_day(),'stgy_list':this.get_smart_optimize_argv(),'auto_hide':0});
}

PT.Adgroup_optimize.table_obj.prototype.change_price_status_4data=function(data){
	var result=data.keyword;
	for (var i in result){
		//var kw_id=result[i]['keyword_id'],obj=$('#'+kw_id).data('obj');
		var kw_id=result[i]['keyword_id'],obj=this.row_cache[kw_id];
		obj.new_price_input.val(result[i]['new_price']);
		obj.nRow.attr('label_code',result[i]['label_code'])
		obj.nRow.find('.optm_type').text(result[i]['optm_type']);
		if(result[i]['optm_type']=='1'){
			obj.kw_del=1;	
		}
		if(result[i]['optm_reason']){
			obj.nRow.find('.icon-info-sign').attr('data-original-title',result[i]['optm_reason']).removeClass('hide');
		}else{
			obj.nRow.find('.icon-info-sign').addClass('hide');
		}
		
		//obj.is_del();
	}
	this.calc_action_count();
	PT.hide_loading();
}






//下面是删除词的 

//继承PT.Table.BaseTableObj的属性
PT.Adgroup_optimize.history_table=function(table_id,temp_id,adgroup_id){
	this.table_id=table_id;
	this.temp_id=temp_id;
	this.table_obj=$('#'+this.table_id);
		
	this.adgroup_id=adgroup_id;
	this.adgroup_default_price=$('#default_price').text();
	//PT.Table.BaseTableObj.call(this,table_id,temp_id);
}

//继承PT.Table.BaseTableObj的属性方法
PT.Adgroup_optimize.history_table.prototype=PT.Table.BaseTableObj.prototype;

//PT.Adgroup_optimize.history_table.prototype.init_history_table=function(){
//	var request_data=['word',
//					'word_type',
//					'word_from',
//					'op_type',
//					'opt_time',
//					'g_ctr',
//					'g_click',
//					'g_cpc',
//					'g_competition',
//					'g_sync_time'				
//					]
//	request_data=$.toJSON(request_data)
//	PT.sendDajax({'function':'web_get_uploadrecord_by_id',
//	                         'adgroup_id':this.adgroup_id,
//	                         'data':request_data,
//	                         'call_back':'PT.instance_history_table.call_history_back'
//	                         });	
//}

//重写回调
PT.Adgroup_optimize.history_table.prototype.call_history_back=function(json){
	var dom='',i;
	for (i in json){
		json[i]['init_price']=this.adgroup_default_price;
		json[i]['loop']=i;
		dom+=template.render('template_uploadrecord',json[i])
	}
	this.table_obj.find('tbody').html(dom);
	this.table_obj.show();
	this.sort_history_table();
	this.init_history_event();
	//this.recount_table_width();
}

PT.Adgroup_optimize.history_table.prototype.init_history_event=function(){
	var that=this;
	
	//改变匹配模式
	this.table_obj.find('.match').click(function(){
		$(this).parent().parent().parent().data('obj').change_match_scorp();
	});
	
	//改变出价时调用
	this.table_obj.find('.new_price').change(function(){
		$(this).parent().parent().data('obj').history_change_new_price();
	});

	//关键词搜索
	$('#history_search_btn').click(function(){
		var search_word=$('#history_search_val').val();
		if(search_word!=''){
			that.search_word_and_sort(search_word);
		}else{
			PT.light_msg('搜索提示：','请填写要搜索的关键词');
		}
	});
	
	//改变选中关键词的匹配模式
	$('#history_bulk_match_btn').change(function(e){
		var ev = e || window.event;
		ev.stopPropagation();		
		that.history_bulk_match($(this).val());
	});
	
	//设置关键词出价
	$('#history_set_new_price').change(function(){
		that.history_set_new_price($(this).val());
	});
	
	//恢复关键词
	$('#history_recover_kw').click(function(){
		if(that.has_checked_row()){
			PT.confirm('您确定将选中的关键词恢复到现有的宝贝中吗?',that.history_recover_kw,[],that);
		}
	});
	
	//改变关键词类型
	this.table_obj.find('.kw_type').change(function(){
		$(this).parent().parent().data('obj').history_change_type($(this));
	});
	
	// 复选框事件
	this.table_obj.find('.father_box').click(function(e){
		var ev = e || window.event, area_id=$(this).attr('link'),there=this;
		ev.stopPropagation();
		if(area_id!=undefined){
			var kid_box=$('#'+area_id).find('input[class*="kid_box"]');
			kid_box.each(function(){
				!(this.disabled)?this.checked=there.checked:'';
			});
		}
		that.set_checked_count();
	});

	this.init_history_scroll_event();
	
	$select({name: 'hidx'})	
}

PT.Adgroup_optimize.history_table.prototype.sort_history_table=function(){
	var that=this;
	this.data_table=this.table_obj.dataTable({
		"bRetrieve": true, //允许重新初始化表格
		"bPaginate": true,
		"bFilter": false,
		"bInfo": true,
		"bAutoWidth":true,//禁止自动计算宽度
		"iDisplayLength": 50,
		"aoColumns":[
			{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric","sClass": "no_back_img tac"},
			{"bSortable": false},
			{"bSortable": false},
			{"bSortable": false},
			{"bSortable": true},
			{"bSortable": true},
			{"bSortable": true},
			{"bSortable": true},
			{"bSortable": true},
			{"bSortable": true}
		],
		"fnCreatedRow":this.history_fnRowcallback,
		"oLanguage": {
			"sZeroRecords": "没有关键词记录"
			,"sLengthMenu": "每页显示 _MENU_ 条记录"
			,"sInfo": "显示第_START_条到第_END_条记录, 共_TOTAL_条记录"
			,"sInfoEmpty": "显示0条记录"
			,"oPaginate": {
				"sPrevious": " 上一页 "
				,"sNext":     " 下一页 "
			}			
		}		
	});
}

PT.Adgroup_optimize.history_table.prototype.history_fnRowcallback=function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
	var row_data=new PT.Adgroup_optimize.history_row(nRow);
	$(nRow).data('obj',row_data);
}

PT.Adgroup_optimize.history_table.prototype.history_set_new_price=function(multiple){
	var that=this;
	this.row_list().each(function(){
		var obj=$(this).data('obj'),temp;
		if(obj.g_cpc>0&&multiple>0){
			temp=(obj.g_cpc*multiple).toFixed(2);
		}else{
			temp=that.adgroup_default_price;	
		}
		obj.new_price_input.val(temp);
		obj.history_update_style();
	});
}

PT.Adgroup_optimize.history_table.prototype.history_recover_kw=function(){
	var row_obj=this.get_checked_row(),keywords=[];
	row_obj.each(function(){
		var obj=$(this).parent().parent().data('obj');
		keywords.push([obj.word,Number((obj.v_new_price()*100).toFixed(0)),Number(obj.v_match_scope()),null,null]);
	});
	PT.sendDajax({'function':'web_history_add_keywords', 'adgroup_id':this.adgroup_id, 'kw_arg_list':$.toJSON(keywords)});	
}

PT.Adgroup_optimize.history_table.prototype.add_call_back=function(json){
	var added_count=json.added_keyword_list.length,
		repeat_count=json.repeat_word_list.length,
		msg='';
	for (var i=0;i<repeat_count;i++){
		json.added_keyword_list.push(json.repeat_word_list[i]);
	}
	
	this.row_list().each(function(){
		var obj=$(this).data('obj');
		if(json.added_keyword_list.indexOf(obj.word)!=-1){	
			obj.history_delete_row();
		}
	});
	
	if (added_count>0){
		msg='成功恢复关键词:'+added_count+'个';
	}
	if (repeat_count>0){
		msg+='已存在的关键词:'+repeat_count+'个';	
	}
	
	PT.alert(msg);
	this.history_set_kw_count();
	$('a[href="#keyword_box"]').removeAttr('switch'); //删除词后将已删词的开关打开
	$('#keyword_count').text(Number($('#keyword_count').text())+added_count);  //改写现有关键词个数
}

//设置关键词个数
PT.Adgroup_optimize.history_table.prototype.history_set_kw_count=function(){
	var kw_count=this.data_table.fnSettings()['aiDisplay'].length;
	$('#history_kw_count').text(kw_count);
}

PT.Adgroup_optimize.history_table.prototype.history_bulk_match=function(match_scorp){
	if(this.has_checked_row()){
		var row_obj=this.get_checked_row();
		
		row_obj.each(function(){
			var obj=$(this).parent().parent().data('obj');
			obj.history_set_match_scorp(match_scorp);
		});
	}
}

PT.Adgroup_optimize.history_table.prototype.unbind_history_scroll_event=function(){
	$(window).off('scroll.PT.history_table');
}

PT.Adgroup_optimize.history_table.prototype.init_history_scroll_event=function(){
	if($.browser.msie&&Number($.browser.version)<9){
		return;
	}
	var that=this;
	//关键词信息浮动
	$(window).on('scroll.PT.history_table',function(){
		if(that.data_table==undefined){
			return;
		}
		var body_ofset = document.body.scrollTop | document.documentElement.scrollTop;
		var base_top=that.data_table.offset().top-40;
		if (body_ofset>base_top&&base_top>0){
			$('#history_fixed_box').addClass('active');
			if(this.fixed_header==undefined){
				this.fixed_header=new FixedHeader(that.data_table,{"offsetTop":40});
			}
		}else{
			setTimeout(function(){
				$('#history_fixed_box').removeClass('active');
				if(this.fixed_header!=undefined){
					$(this.fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
				}
				this.fixed_header=null;		
			},0);
		}
	});
}




//继承PT.Table.BaseRowObj的属性
PT.Adgroup_optimize.history_row=function(obj){
	PT.Table.BaseRowObj.call(this,obj);
	this.blacklist=this.nRow.find('select').val();
	this.row_input=this.nRow.find('.kid_box');
}

//继承PT.Table.BaseRowObj的方法
PT.Adgroup_optimize.history_row.prototype=PT.Table.BaseRowObj.prototype;

PT.Adgroup_optimize.history_row.prototype.history_update_style=function(){
	this.new_price_input.removeClass('impo_color').attr('disabled',false);
	this.nRow.removeClass('kw_del');
	
	this.is_limit()?this.new_price_input.addClass('impo_color'):'';
	if(this.kw_del){
		this.nRow.addClass('kw_del');
		this.new_price_input.attr('disabled',true);
	}
}

PT.Adgroup_optimize.history_row.prototype.history_change_new_price=function(){
	if(this.kw_del){
		return false;
	}
	var new_price=this.v_new_price();
	if(PT.instance_table.check_digit(new_price)){
		this.new_price_input.val(new_price.toFixed(2));
	}else{
		this.new_price_input.val(PT.instance_history_table.adgroup_default_price);
	}
	this.history_update_style();
}

//删除关键词
PT.Adgroup_optimize.history_row.prototype.history_delete_row=function(){
	var index=PT.instance_history_table.data_table.fnGetPosition(this.nRow[0]);
	PT.instance_history_table.data_table.fnDeleteRow(index);
}

//改变词类型
PT.Adgroup_optimize.history_row.prototype.history_change_type=function(obj){
	var data={
		word:this.word,
		word_type:obj.val(),
		kw_id:this.kw_id
	};
	PT.sendDajax({'function':'web_history_change_type', 'adgroup_id':PT.Adgroup_optimize.adgroup_id, 'data':$.toJSON(data)});
}

PT.Adgroup_optimize.history_row.prototype.unlock_row=function(type){
	if(type=='1'){
		this.row_input.attr({'disabled':true,'checked':false});
	}else{
		this.row_input.attr('disabled',false);	
	}
	PT.light_msg('修改词类型','成功!');
}

PT.Adgroup_optimize.history_row.prototype.history_set_match_scorp=function(match_scorp){
	var scorp_list={1:'精',2:'中',4:'广'};
	this.match_span.attr('scope',match_scorp);

	this.match_span.text(scorp_list[match_scorp]);	
	this.match_changed=match_scorp==this.match_scope?0:1;
}