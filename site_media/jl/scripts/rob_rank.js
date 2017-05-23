"use strict";
PT.namespace('Table');
PT.namespace('instance_table');
PT.namespace('Rob_rank');

PT.Rob_rank=function(){
	var adgroup_id=$('#adgroup_id').val();

	var get_last_day=function (){
		return $('#dashboard-report-range').find('input[name="last_day"]').val();
	};

	var init_table=function(){
		PT.instance_table=new PT.Table.robTable('rob_table');
	};

	var init_help=function(){
		var help_list=[
			{
				element:'.link_inner_checkbox:eq(1)',
				content:'1/3 按住shift单击复选框或者右键可以选出一批要执行抢排名的关键词',
				placement:'right'
			},
			{
				element:'.rob_set:eq(0)',
				content:'2/3 设置每个词语的期望排名和最高限价,也可以点击后面的限价，系统会给出建议的最高限价',
				placement:'bottom'
			},
			{
				element:'#rob_btn',
				content:'3/3 提交到后台执行操作，最后会显示没个词的执行情况',
				placement:'left'
			}
		];

		PT.help(help_list);
	};

	return {
        init: function () {
			$('ul.main.nav>li').eq(4).addClass('active');
			PT.initDashboardDaterange();
			init_table();
			PT.instance_table.get_keyword_data();
        },
		select_call_back: function(value){
			//改变天数的回调函数
			//PT.instance_table.data_table.fnDestroy();
			PT.instance_table.get_keyword_data();
		},
		table_callback:function(data){
			PT.hide_loading();
			$('#total_count').text(data.length);
			PT.instance_table.call_back(data);
		},
		get_last_day:get_last_day,
		adgroup_id:adgroup_id,
		help:init_help
	};

}();



PT.Table.KW_LIMIT_PRICE=15.00; //关键词预估排名限价最高值

//抢排名的行对象
PT.Table.robRow=function(obj){
	this.nRow=$(obj);
	this.kw_id=obj.id;
	this.word=$('#word_'+this.kw_id).text();
	this.o_max_price=this.nRow.find('.max_price');
	this.check_ranking_btn=this.nRow.find('.check_ranking');
	this.o_rank=this.nRow.find('.rank');
	this.o_min=this.nRow.find('.rob_min');
	this.o_max=this.nRow.find('.rob_max');
	this.o_limit=this.nRow.find('.rob_limit');
	this.prompt_price=this.nRow.find('.prompt_price');
};


//显示抢排名信息
PT.Table.robRow.prototype.show_rob_info=function(mode,new_price,rank){
	var msg;
	if(mode==1){
		msg='已经抢到排名，不能再抢';
		this.nRow.find('.rob_set').addClass('success');
		this.nRow.find('.rob_set input').val('');
		this.nRow.find('.max_price').text(new_price);
		this.nRow.find('.rank').text(rank);
 		this.nRow.find('.kid_box').attr({'disabled':true,'checked':false}).addClass('disabled');
		this.nRow.find('td:first').removeClass('pointer');
	}
	if(mode==2){
		msg='未抢到排名，已恢复原出价';
		this.nRow.find('.rob_set').addClass('fail');
	}

	this.nRow.find('.rob_set_info').text(msg);
};

//查排名
PT.Table.robRow.prototype.check_ranking=function(){
	this.check_ranking_btn.html("<img src='/site_media/jl/img/forecast_orde_ajax.gif'>");
	PT.sendDajax({'function':'web_get_word_order','adgroup_id':PT.Rob_rank.adgroup_id,'item_id':$('#item_id').val(),'keyword_id':this.kw_id,'ip':PT.instance_table.v_zone_ip()});
};

//设置排名
PT.Table.robRow.prototype.set_ranking=function(rank){
	this.check_ranking_btn.html(rank);
	this.check_ranking_btn.attr('switch',"0");
	//判断是否是批量预测
	if (PT.instance_table.bulk_ranking){
		PT.instance_table.bulk_ranking_order();
	}
	//判断是否需要同步强排名的表
	if (PT.instance_table.sync_rob_table){
		$('#rob_'+this.kw_id).data('rob').set_ranking(rank);
	}
};

PT.Table.robRow.prototype.goto_ztc_kw=function(){
	PT.Base.goto_ztc(5, 0, 0, this.word);

};

//检查页面是有存在预估排名，若没有就从后台获取。
PT.Table.robRow.prototype.check_forecast_data=function(tip){
	var forecast_data=this.nRow.data('forecast_data');
	if(forecast_data===undefined){
		var rob_min=this.o_min.val(), rob_max=this.o_max.val();
		if(rob_min && rob_max){
			this.prompt_price.html("<img src='/site_media/jl/img/forecast_orde_ajax.gif'>");
			PT.sendDajax({'function':'web_get_forecast_data','kw_id':this.kw_id});
		}else{
			PT.alert("请先填写期望排名");
		}
	}else{
		this.set_prompt_price();
	}
};

PT.Table.robRow.prototype.forecast_data_back=function(result,data){
	if(result){
		this.nRow.data('forecast_data',data);
		this.set_prompt_price();
	}else{
		PT.alert("即使出价99.99元也排名在100名以外，建议该词不要抢排名");
	}
	this.prompt_price.html("建议限价");
};

//设置建议限价
PT.Table.robRow.prototype.set_prompt_price=function(){
	var prompt_price=this.get_prompt_price(),
		limit_price= prompt_price<PT.Table.KW_LIMIT_PRICE?prompt_price:PT.Table.KW_LIMIT_PRICE ;
	this.o_limit.val(Number(limit_price).toFixed(2));
};

PT.Table.robRow.prototype.get_prompt_price=function(){
	var rob_min=parseInt(this.o_min.val()), rob_max=parseInt(this.o_max.val()),
		rob_rank=parseInt(rob_min+(rob_max-rob_min)/3);
	return this.get_price_by_rank(rob_rank);
};

//提交强排名前，检验当前预估排名是否准确，准确则返回预估值，否则返回0；
PT.Table.robRow.prototype.get_forecast_price=function(){

	if (Number(this.check_ranking_btn.attr('switch'))) {
		return [0, 0];
	}else{
		var result_list = this.forecast_is_right();
		if (result_list[0]) {
			return [this.get_prompt_price(), result_list[1]];
		}else{
			return [0, 0];
		}
	}
};

PT.Table.robRow.prototype.forecast_is_right=function(){
	var rank_text=this.check_ranking_btn.text(),
		cur_rank= rank_text=='100+'?101:Number(rank_text),
		forecast_data=this.nRow.data('forecast_data'),
		interval_rank=4,
		head_rank=cur_rank+interval_rank<101?cur_rank+interval_rank:101,
		tail_rank=cur_rank-interval_rank>1?cur_rank-interval_rank:1,
		head_price=this.get_price_by_rank(head_rank),
		tail_price=this.get_price_by_rank(tail_rank),
		cur_price=parseFloat(this.o_max_price.text());
	if (cur_rank==101){
		return [cur_price<=head_price? true: false, cur_rank];
	}else if (cur_price>=head_price && cur_price<=tail_price){
		return [true, cur_rank];
	}else{
		return [false, cur_rank];
	}
};

PT.Table.robRow.prototype.get_price_by_rank=function(rank){
	var forecast_data=this.nRow.data('forecast_data'), forecast_price=0;
	if (!forecast_data) {
		return 0;
	}
	for(var i=0;i<30;i++){
		if(forecast_data.hasOwnProperty(rank-i)){
			forecast_price=parseFloat(forecast_data[rank-i].price);
			break;
		}else if(forecast_data.hasOwnProperty(rank+i)){
			forecast_price=parseFloat(forecast_data[rank+i].price)+0.1*i;
			break;
		}
	}
	return forecast_price;
};

//将显示行显示到前面
PT.Table.robRow.prototype.set_row_up=function(checked,num){
	var jq_input=this.nRow.find('.kid_box');
	if (jq_input){
		num!==undefined?jq_input.prev().text(num):jq_input.prev().text(1);
		if(!jq_input.attr('disabled')){
			jq_input.attr('checked',checked);
		}
	}
};

//将显示行显示到后面
PT.Table.robRow.prototype.set_row_down=function(checked){
	var jq_input=this.nRow.find('.kid_box');
	if (jq_input){
		jq_input.prev().text(0);
		jq_input.attr('checked',checked);
	}
};


//强排名的表对象
PT.Table.robTable=function(id){
	this.id=id;
	this.table_obj=$('#'+id);
	this.row_cache={};
};

//获取关键词列表
PT.Table.robTable.prototype.get_keyword_data=function(){
	PT.show_loading('正在加载关键词数据');
	PT.sendDajax({'function':'web_rob_rank_kws','adgroup_id':PT.Rob_rank.adgroup_id,'last_day':PT.Rob_rank.get_last_day()});
};

PT.Table.robTable.prototype.call_back=function(data){
	var that=this;
	if(!$.fn.dataTable.fnIsDataTable(this.table_obj[0])){
		if(data.length){
			this.layout_keyword(data);
			this.sort_table();
		}else{
			$('#rob_table').hide();
			$('#no_keyword').show();
			PT.Rob_rank.help();
			return;
		}
	}else{//改变统计天数时，只刷新报表数据
		this.update_kw_rpt(data);
	}
	PT.Rob_rank.help();
};

//填充表格数据
PT.Table.robTable.prototype.layout_keyword=function(data){
	PT.console('begin layout keyword');
	var tr_str='',kw_count=data.length,d;
	for (var i=0;i<kw_count;i++){
		tr_str+=template.render('template_rob_table_tr',data[i]);
	}
	this.table_obj.find('tbody tr:not([class*="unsort"])').remove();
	this.table_obj.find('tbody tr.unsort').after(tr_str);
};


PT.Table.robTable.prototype.sort_table=function(){
	var that=this;
	this.data_table=this.table_obj.dataTable({
			"bRetrieve":true,
			"bPaginate": false,
			"bFilter": false,
			"bInfo": false,
			"bAutoWidth":false,//禁止自动计算宽度
			"aaSorting":[[4,'desc']],
			"fnCreatedRow":that.fnRobRowCallback,
			"aoColumns": [
				{"bSortable": false},
				{"bSortable": false},
				{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
				{"bSortable": true, "sType": "custom"},
				{"bSortable": true, "sType": "custom"},
				{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
				{"bSortable": true, "sType": "custom"},
				{"bSortable": true, "sType": "custom"},
				{"bSortable": true, "sType": "custom"},
				{"bSortable": true, "sType": "custom","sSortDataType": "custom-text"},
				{"bSortable": true, "sType": "custom"},
				{"bSortable": true, "sType": "custom"},
				{"bSortable": true, "sType": "custom"},
				{"bSortable": false, "sType": "custom"}
			],
			"oLanguage": {
				"sEmptyTable":'没有质量得分5分以上的词,请重新选择！'
		}});
		this.init_event();
};

PT.Table.robTable.prototype.fnRobRowCallback=function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
	var row_data=new PT.Table.robRow(nRow);
	if(nRow.id){
		PT.instance_table.row_cache[nRow.id]=row_data;
	}
};

PT.Table.robTable.prototype.row_list=function(){
	return this.table_obj.find('tbody tr:not([class*="unsort"])');
};

PT.Table.robTable.prototype.bulk_rob_set=function(){
	var rob_min,rob_max,rob_limit,that=this;
	rob_min=$('#rob_worder_select').val().split('-')[0];
	rob_max=$('#rob_worder_select').val().split('-')[1];
	rob_limit=Number($('#rob_worder_input').val());
	if(isNaN(rob_limit)||rob_limit<0.05||rob_limit>PT.Table.KW_LIMIT_PRICE){
		PT.alert('最高限价必须是0.05到'+PT.Table.KW_LIMIT_PRICE+'的数字，请重新填写');
		return;
	}
	this.checked_row().each(function(){
		var obj=that.row_cache[$(this).closest('tr').attr('id')];
		//obj.recover_rob_input();
		obj.o_min.val(rob_min);
		obj.o_max.val(rob_max);
		obj.o_limit.val(rob_limit);
	});
};

PT.Table.robTable.prototype.get_checked_count=function(){
	var that=this;
	this.row_list().each(function(){
		var obj=that.row_cache[this.id];
		if(obj.nRow.find('.kid_box').attr('checked')=='checked'){
			$(this).addClass('selected');
		}else{
			$(this).removeClass('selected');
		}
	});
	var checked_num = this.checked_row().length;
	$('#current_count').text( checked_num );
	return checked_num;
};

PT.Table.robTable.prototype.init_event=function(){
	var that=this;

	new FixedHeader(this.data_table);
	$select({name: 'idx','callBack': this.get_checked_count,'that':this}); //shift多选
	this.data_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
		'fn':function(){selectRefresh()},
		'sName':'refresh_select'
	});

	$('input.father_box').change(function(){
		$('.kid_box:not([disabled])').attr('checked',!!$(this).attr('checked'));
		that.get_checked_count();
	});

	$('input.kid_box').change(function(){
		that.get_checked_count();
	});

	$('#rob_btn').click(function(){
		that.bulk_rob_ranking();
	});

	//关键词搜索
	$('.search_btn').click(function(){
		var search_word=$(this).prev().val();
		if(search_word!==''){
			that.search_word_and_sort(search_word);
		}else{
			PT.light_msg('搜索提示：','请填写要搜索的关键词');
		}
	});

	this.table_obj.find('.prompt_price').click(function(){
		var tr_id=$(this).closest('tr').attr('id');
		that.row_cache[tr_id].check_forecast_data();
	});

	//
	this.table_obj.find('.rob_min,.rob_max,.rob_limit').blur(function(){
		if($(this).hasClass('rob_limit')){
			that.check_input($(this),[0.05,PT.Table.KW_LIMIT_PRICE],false);
		}else{
			that.check_input($(this),[1,100],true);
			var js_span=$(this).closest('.rob_set_box'),
				rob_min=js_span.find('.rob_min').val(),
				rob_max=js_span.find('.rob_max').val();
			if(rob_min && rob_max && Number(rob_min)>Number(rob_max) ){
				var temp_val= (parseInt(rob_min)<100?parseInt(rob_min)+1:100);
				js_span.find('.rob_max').val(temp_val);
			}else if(rob_min && rob_max && Number(rob_min)==Number(rob_max) ){
				PT.light_msg('','建议将期望排名的范围设置大些，更容易抢到排名');
			}
		}
	});


	//查看当前排名
	this.table_obj.find('.check_ranking').click(function(){
		var tr_id=$(this).closest('tr').attr('id');
		that.row_cache[tr_id].check_ranking();
	});

	//关键词点击事件
	this.table_obj.find('.keyword').click(function(){
		var tr_id=$(this).closest('tr').attr('id');
		that.row_cache[tr_id].goto_ztc_kw();
	});

	//批量查当前排名
	$('#ip_zone').change(function(){
		if(that.has_checked_row()){
			if($(this).val()==''){
				return;
			}
			if(that.has_checked_row()){
				that.start_bulk_ranking_order();
			}
		}else{
			$(this).val('');
		}
	});

	$('#bulk_rob_set').click(function(){
		if(that.has_checked_row()){
			that.bulk_rob_set();
		}
	});

	$('#rob_reset').click(function(){
		that.bulk_rob_reset();
	});

};

//搜索并排序
PT.Table.robTable.prototype.search_word_and_sort=function(search_word){
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
	this.get_checked_count();
};

PT.Table.robTable.prototype.bulk_rob_reset=function(){
	var that=this;
	if(this.has_checked_row()){
		this.checked_row().each(function(){
			var jq_tr=$(this).parents('tr'),
				obj=that.row_cache[jq_tr.attr('id')];
			jq_tr.find('.rob_set').removeClass('fail');
			jq_tr.find('.rob_set_info').text('');
			obj.o_min.val('');
			obj.o_max.val('');
			obj.o_limit.val('');
		});
	}
};

//开始批量查排名
PT.Table.robTable.prototype.start_bulk_ranking_order=function(){
	PT.confirm('查询当前排名可能执行时间较长，您确定要执行吗？',function(){
		this.bulk_ranking=1;
		$('#ip_zone').attr('disabled',true); //禁止下拉菜单改变再次触发查询
		this.bulk_ranking_order();
	},[],this);
};

PT.Table.robTable.prototype.bulk_ranking_order=function(){
		var current_btn=$(this.table_obj.find('input[type="checkbox"]:checked').parent().parent().find('.check_ranking[switch="1"]')[0]);
		if(current_btn.length){
			this.row_cache[current_btn.closest('tr').attr('id')].check_ranking();
			return;
		}
		this.bulk_ranking=0;
		$('#ip_zone').attr('disabled',false);
		$('.check_ranking').attr('switch','1');

};


PT.Table.robTable.prototype.checked_row=function(){
	return this.table_obj.find('tbody input:checked');
};

PT.Table.robTable.prototype.has_checked_row=function(){
	if(this.checked_row().length===0){
		PT.light_msg('提示','没有选中任何关键词');
		return false;
	}
	return true;
};

PT.Table.robTable.prototype.bulk_rob_ranking=function(){
	var that=this;
	if(this.has_checked_row()){
		var that=this,error_count=0,unfull_count=0,total_count=0,keyword_list={},msg,min_obj,max_obj,limit_obj,rob_min,rob_max,rob_limit;

		this.checked_row().each(function(){
			if($(this).find('.rob_set').hasClass('fail')||$(this).find('.rob_set').hasClass('success')){
				return;
			}
			//var obj=$(this).parent().parent().data('rob');
			var obj=that.row_cache[$(this).closest('tr').attr('id')];
			min_obj=obj.o_min;
			max_obj=obj.o_max;
			limit_obj=obj.o_limit;

			rob_min=Number(min_obj.val());
			rob_max=Number(max_obj.val());
			rob_limit=Number(limit_obj.val());
			total_count++;

			if(rob_min!=''||rob_max!==''||rob_limit!==''){
				if(that.check_rob_input(min_obj,[1,100],true)&&that.check_rob_input(max_obj,[1,100],true)&&that.check_rob_input(limit_obj,[0.05,PT.Table.KW_LIMIT_PRICE],false)){
					if(rob_min>rob_max){ //确保最小值小于最大值
						min_obj.addClass('red_border');
						max_obj.addClass('red_border');
						error_count++;
					}else{
						min_obj.removeClass('red_border');
						max_obj.removeClass('red_border');
						var forecast_list=obj.get_forecast_price();
						keyword_list[obj.kw_id]=[Number(rob_min),Number(rob_max),Number(rob_limit),forecast_list[0],forecast_list[1]];
					}
				}else{
					error_count++;
				}
			}else{
				min_obj.removeClass('red_border');
				max_obj.removeClass('red_border');
				limit_obj.removeClass('red_border');
				unfull_count++;
			}

		});
		if(total_count>(error_count+unfull_count)){
			msg='当前选中:'+total_count+'个,输入有误'+error_count+'个,未填写'+unfull_count+'个。您确定要批量抢排名吗？';
			PT.confirm(msg,that.start_rob_ranking,[keyword_list]);
		}else{
			PT.alert('没有正确设置的关键词，请重新设置！');
		}
	}
};

//失去焦点时，自动验证抢抢排名输入合法性
PT.Table.robTable.prototype.check_input=function(obj,limit_arr,is_int){
	var num=parseFloat(obj.val()), input_val=num;
	if(!obj.val()){
		return;
	}else if(isNaN(num)){
		obj.addClass('red_border').val('');
		PT.light_msg('','请输入数字');
		return false;
	}
	if (num<limit_arr[0]) {
		input_val=limit_arr[0];
	}else if(num>limit_arr[1]) {
		input_val=limit_arr[1];
	}
	if(is_int){
		input_val=parseInt(input_val);
	}else{
		input_val=input_val.toFixed(2);
	}
	obj.removeClass('red_border').val(input_val);
	return true;
};

//验证抢抢排名输入合法性
PT.Table.robTable.prototype.check_rob_input=function(obj,limit_arr,is_int){
	var num=parseFloat(obj.val());
	if(isNaN(num)||num<limit_arr[0]||num>limit_arr[1]||(is_int&&parseInt(num)!=num)){
		obj.addClass('red_border');
		return false;
	}else{
		obj.removeClass('red_border');
		return true;
	}
};

//开始抢排名
PT.Table.robTable.prototype.start_rob_ranking=function(keyword_list){
	PT.show_loading('正在执行抢排名');
	$('#rob_info').slideUp(300);
	$('.new_price').removeClass('yello_border');
	PT.sendDajax({'function':'web_rob_ranking','adgroup_id':PT.Rob_rank.adgroup_id,'keyword_list':$.toJSON(keyword_list),'lock_status':1,'ip':$('#ip_zone').val()});
};

//抢排名回调函数
PT.Table.robTable.prototype.rob_ranking_call_back=function(data){
	var i,obj,kw_list=[],rob_info_change=0,rob_info_unchange=0,rob_error=0,msg='';
	for (i in data){
		obj=this.row_cache[data[i].kw_id];
		if(data[i].state==0){ //抢成功并在期望排名区间
			//obj.new_price_input.addClass('yello_border');
			var new_price=(data[i].new_price/100).toFixed(2);

			obj.nRow.find('.max_price').text(new_price);

			obj.check_ranking_btn.text(data[i].rank);
			rob_info_change++;

			obj.show_rob_info(1,new_price,data[i].rank);
		}
		if(data[i].state==1){ //表示执行成功
			//obj.check_ranking_btn.text(data[i].rank);

			rob_info_unchange++;
			obj.show_rob_info(2);
		}
		if(data[i].state==2){ //表示执行失败

			obj.show_rob_info(2);
			rob_error++;
		}
	}
	this.get_checked_count();


	setTimeout(function(){
		msg="执行结果：达到期望排名"+rob_info_change+"个 未达期望排名"+rob_info_unchange+"个 失败"+rob_error+"个";
		PT.alert(msg);
	},16);

};

PT.Table.robTable.prototype.v_zone_ip=function(){
	return $('#ip_zone').val();
};

PT.Table.robTable.prototype.update_kw_rpt=function(data){
	var rpt_col=['click','ctr','cpc','avgpos','impressions','conv','roi','g_cpc','g_pv'];//添加报表列时，要更新该值
	for (var i in data){
		var kw_id=data[i]['keyword_id'],obj=this.row_cache[kw_id];
		for (var j in rpt_col) {
			var temp=rpt_col[j];
			obj.nRow.find('.'+temp).text(data[i][temp]);
		}
	}
};
