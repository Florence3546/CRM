"use strict";
PT.namespace('Delete_keyword');
PT.Delete_keyword = function () {
	var adgroup_id=$('#adgroup_id').val();
	var campaign_id=$('#campaign_id').val();
	var item_id=$('#item_id').val();
	var default_price=$('#default_price').val();
	var help=new Tour({backdrop:true});

	var init_dom=function (){
		$('.help').click(function(){
			help.restart();
		});     
	}

	var init_table=function(){
		PT.instance_table=new PT.Delete_keyword.history_table('common_table','teplate_history_table_tr',adgroup_id);
		PT.instance_table.init_history_table();
	}
	
	var get_uploadrecord_count=function(){
		PT.sendDajax({'function':'web_get_uploadrecord_by_id',
		                         'adgroup_id':adgroup_id,
		                         'data':'count_only',
		                         'call_back':'PT.Delete_keyword.deleted_count',
		                         'auto_hide':0
		                         });	
	}
	
	var init_help=function(){
		if(!$.browser.webkit&&$.browser.msie&&Number($.browser.version)<7){
			return;
		}
		help.addSteps([]);
	}	
	
    return {
        init: function () {
		   $('ul.main.nav>li').eq(5).addClass('active');
		   init_dom();
		   init_table();
//		   get_uploadrecord_count();
		   //init_help();
        },
		table_callback: function(data){PT.instance_table.call_back(data);},
		deleted_count:function(data){$('#keyword_count').text(data.count);},
		adgroup_id:adgroup_id,
		item_id:item_id,
		campaign_id:campaign_id,
		default_price:default_price,
		help:help
    };
}();

//继承PT.Table.BaseTableObj的属性
PT.Delete_keyword.history_table=function(table_id,temp_id,adgroup_id){
	this.table_id=table_id;
	this.temp_id=temp_id;
	this.table_obj=$('#'+this.table_id);
		
	this.adgroup_id=adgroup_id;
	this.default_price=$('#default_price').val();
	this.row_cache={};
	this.KW_LIMIT_PRICE=5; //设置超过该价格就提示
}

//继承PT.Table.BaseTableObj的属性方法
PT.Delete_keyword.history_table.prototype=PT.Table.BaseTableObj.prototype;

PT.Delete_keyword.history_table.prototype.init_history_table=function(){
	PT.show_loading('亲，正在查询');
	var request_data=['word','word_type','word_from','op_type','opt_time','g_ctr','g_click','g_cpc','g_competition','g_sync_time','keyword_id'];
	request_data=$.toJSON(request_data);
	PT.sendDajax({'function':'web_get_uploadrecord_by_id', 
	                         'adgroup_id':this.adgroup_id, 
	                         'data':request_data, 
	                         'call_back':'PT.instance_table.call_history_back'
	                         });	
}

//重写回调
PT.Delete_keyword.history_table.prototype.call_history_back=function(json){
	var dom='', i, count=0, limit_price = Number($('#init_limit_price').val());
	for (i in json){
		var temp_price = json[i]['g_cpc']>0.05 ? json[i]['g_cpc'] : this.default_price;
		if(limit_price>0){
			temp_price = temp_price>limit_price ? limit_price : temp_price;
		}
		json[i]['init_price']=temp_price;
		json[i]['loop']=i;
		dom+=template.render('template_uploadrecord',json[i]);
		count++;
	}
	this.table_obj.find('tbody').html(dom);
	this.table_obj.show();
	this.sort_history_table();
	this.init_history_event();
	$('#keyword_count').text(count);
}

PT.Delete_keyword.history_table.prototype.init_history_event=function(){
	var that=this;
	
	//改变匹配模式
	this.table_obj.on('click','.match',function(){
		that.row_cache[$(this).parent().parent().parent().attr('id')].change_match_scorp();
	});
	
	//改变出价时调用
	this.table_obj.on('change', '.new_price', function(){
		that.row_cache[$(this).parent().parent().attr('id')].history_change_new_price();
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
		var limit_price = $.trim($('#init_limit_price').val());
		if(limit_price =='' || isNaN(limit_price)){
			PT.alert('请输入新词限价');
			return false;
		}
		var row_objs=that.get_checked_row(),checked_count=0;
		row_objs.each(function(){
			var obj=that.row_cache[$(this).parent().parent().attr('id')];
			if(!obj.check_box().is(':disabled')){
				checked_count++;
			}
		});
		if(checked_count>0){
			PT.confirm('确定将选中的'+checked_count+'个词添加到当前宝贝吗？',that.history_recover_kw,[],that);
		}else{
			PT.alert('请选择要恢复的关键词');
			return false;
		}
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
	
	//新词出价超过限价提醒
    $('#init_limit_price').unbind('blur');
	$('#init_limit_price').blur(function(){
		var limit_price = Number($(this).val());
        var limit_price_max = Number($('#limit_price_max').val());
        if (isNaN(limit_price) || limit_price==0) {
            $(this).val(Number($(this).attr('value_bak')).toFixed(2));
        } else if (limit_price<0.05) {
            $(this).val(0.05);
        } else if (limit_price>limit_price_max) {
            $(this).val(limit_price_max.toFixed(2));
        } else {
            $(this).val(limit_price.toFixed(2));
        }
//		if(!PT.instance_table.check_digit(limit_price)){
//			$(this).val('');
//			return false;
//		}
//		limit_price = limit_price.toFixed(2);
//		$(this).val(limit_price);
		
		that.KW_LIMIT_PRICE = limit_price;
		that.row_list().each(function(){
			var obj=that.row_cache[this.id];
			var new_price=obj.v_new_price();
			if(new_price>limit_price){
				obj.new_price_input.val(limit_price);
			}
		});

		that.update_all_style();
	});

	this.init_history_scroll_event();
	
	$select({name: 'hidx'});
	this.data_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
		'fn':function(){selectRefresh()},
		'sName':'refresh_select'	
	});
}

PT.Delete_keyword.history_table.prototype.sort_history_table=function(){
	var that=this;
	this.data_table=this.table_obj.dataTable({
		"bRetrieve": true, //允许重新初始化表格
		"bPaginate": true,
		"bFilter": false,
		"bInfo": true,
		"aaSorting": [[3,'asc'],[6,'desc']],
		"bAutoWidth":true,//禁止自动计算宽度
		"iDisplayLength": 50,
		"aoColumns":[
			{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric","sClass": "no_back_img tac"},
			{"bSortable": false},
			{"bSortable": true},
			{"bSortable": true},
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

PT.Delete_keyword.history_table.prototype.history_fnRowcallback=function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
	var row_data=new PT.Delete_keyword.history_row(nRow);
	if(nRow.id){
		PT.instance_table.row_cache[nRow.id]=row_data;
	}
}

PT.Delete_keyword.history_table.prototype.history_set_new_price=function(multiple){
	var that=this;
    var limit_price = $('#init_limit_price').val();
	this.row_list().each(function(){
		var obj=that.row_cache[this.id],temp;
		if(obj.g_cpc>0 && multiple>0){
			temp=(obj.g_cpc*multiple).toFixed(2);
		}else{
			temp=that.default_price;
		}
		obj.new_price_input.val(Math.min(temp, limit_price).toFixed(2));
	});
}

PT.Delete_keyword.history_table.prototype.history_recover_kw=function(){
	var row_obj=this.get_checked_row(),keywords=[],that=this;
	row_obj.each(function(){
		var obj=that.row_cache[$(this).parent().parent().attr('id')];
		if(!obj.check_box().is(':disabled')){
			keywords.push([obj.word,Number((obj.v_new_price()*100).toFixed(0)),Number(obj.v_match_scope()),null,null]);
		}
	});
	if(keywords.length>0){
		PT.show_loading('正在恢复选中的'+keywords.length+'个已删词');
		PT.sendDajax({'function':'web_history_add_keywords', 'adgroup_id':this.adgroup_id, 'kw_arg_list':$.toJSON(keywords)});	
	}
}

PT.Delete_keyword.history_table.prototype.add_call_back=function(json){
	var added_count=json.added_keyword_list.length,
		repeat_count=json.repeat_word_list.length,
		msg='',
		that=this;
	for (var i=0;i<repeat_count;i++){
		json.added_keyword_list.push(json.repeat_word_list[i]);
	}
	
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		if(json.added_keyword_list.indexOf(obj.word)!=-1){
			obj.history_delete_row();
		}
	});
	
	if (added_count>0){
		msg='成功恢复'+added_count+'个关键词';
	}
	if (repeat_count>0){
		msg+=','+repeat_count+'个已存在的重复词无法恢复';
	}
	
	PT.alert(msg);
	this.history_set_kw_count();
}

//设置关键词个数
PT.Delete_keyword.history_table.prototype.history_set_kw_count=function(){
	var kw_count=this.data_table.fnSettings()['aiDisplay'].length;
	$('#keyword_count').text(kw_count);
}

PT.Delete_keyword.history_table.prototype.history_bulk_match=function(match_scorp){
	var that=this;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		obj.history_set_match_scorp(match_scorp);
	});
}

PT.Delete_keyword.history_table.prototype.unbind_history_scroll_event=function(){
	$(window).off('scroll.PT.history_table');
}

PT.Delete_keyword.history_table.prototype.init_history_scroll_event=function(){
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
PT.Delete_keyword.history_row=function(obj){
	PT.Table.BaseRowObj.call(this,obj);
	this.blacklist=this.nRow.find('select').val();
	this.row_input=this.nRow.find('.kid_box');
}

//继承PT.Table.BaseRowObj的方法
PT.Delete_keyword.history_row.prototype=PT.Table.BaseRowObj.prototype;

PT.Delete_keyword.history_row.prototype.history_change_new_price=function(){
	var new_price=this.v_new_price();
	var limit_price = $('#init_limit_price').val();
	if(PT.instance_table.check_digit(new_price)){
		if(limit_price && new_price > limit_price){
			this.new_price_input.val(limit_price);
		}else{
			this.new_price_input.val(new_price.toFixed(2));
		}
	}else{
		this.new_price_input.val(PT.instance_table.default_price);
	}
	this.update_style();
}

//删除关键词
PT.Delete_keyword.history_row.prototype.history_delete_row=function(){
	var index=PT.instance_table.data_table.fnGetPosition(this.nRow[0]);
	PT.instance_table.data_table.fnDeleteRow(index);
}

//改变词类型
PT.Delete_keyword.history_row.prototype.history_change_type=function(obj){
	var data={
		word:this.word,
		word_type:obj.prev().text()==0?1:0,
		kw_id:this.kw_id
	};
	PT.sendDajax({'function':'web_history_change_type', 'adgroup_id':PT.Delete_keyword.adgroup_id, 'data':$.toJSON(data)});
}

PT.Delete_keyword.history_row.prototype.history_set_match_scorp=function(match_scorp){
	var scorp_list={1:'精',2:'中',4:'广'};
	this.match_span.attr('scope',match_scorp);

	this.match_span.text(scorp_list[match_scorp]);	
	this.match_changed=match_scorp==this.match_scope?0:1;
}

//搜索并排序
PT.Table.BaseTableObj.prototype.search_word_and_sort=function(search_word){
	var that=this;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		if(obj.word.indexOf(search_word)!=-1){
			obj.set_row_up(true);
		}else{
			obj.set_row_down(false);
		}
	});

	this.data_table.fnSort([ [0,'desc']]);
	this.set_checked_count();
	$('#current_check_count').parent().show();
}