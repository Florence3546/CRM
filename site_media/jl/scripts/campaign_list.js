PT.namespace('Campaign_list');
PT.Campaign_list = function () {
	var checked_count = 0;
	var init_sort=function(){
		PT.campaign_table=$('#campaign_table').dataTable({
			//"bRetrieve": true, 允许重新初始化表格
			"bPaginate": false,
			"bFilter": false,
			"bInfo": false,
			"aaSorting":[[6,'asc'],[5,'desc'],[3,'desc']],
			"oLanguage": {
				"sZeroRecords": "亲，您还没有开启推广计划"
			},
			"aoColumns": [{"bSortable": false},{"bSortable": false},{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable":  true,"sSortDataType": "dom-text", "sType": "numeric"},{"bSortable":  true,"sSortDataType": "dom-text", "sType": "numeric"}]
		});
	};

	var init_dom=function () {
		//启用、暂停、新建计划
		$('#camp_control .camp').click(function(){
			var camp_id_arr=[],
				oper=parseInt($(this).attr('oper')),
				obj=$('#campaign_table tbody input:checked');
			obj.each(function(){
				camp_id_arr.push(parseInt($(this).val()));
			});
			if (oper==-1) {
				PT.Base.goto_ztc(1,0,0,'');
			} else if (checked_count) {
				if (oper==0){
					PT.confirm('确定要暂停选中的'+checked_count+'个计划吗？',set_update_camps,[oper,camp_id_arr]);
				}else if(oper==1){
					set_update_camps(oper,camp_id_arr);
				}
			}else{
				PT.alert('请至少选择一个计划');
			}
		});

		$("#camp_history").fancybox({
			minWidth	: '66%',
			fitToView	: false,
			width		: '80%',
			height		: '80%',
			autoSize	: false,
			closeClick	: false,
		});

	};

	var init_help=function(){
		var help_list=([
			{
				element:'#campaign_table td:eq(1)',
				content:'1/2 点铅笔可编辑标题,点击图表可以查看趋势',
				placement:'right'
			},
			{
				element: "#campaign_table td:eq(2)",
				content: "2/2 这里点铅笔是修改计划限额",
				placement:'top'
			}
		]);
		PT.help(help_list);
	};


	//发送请求获取数据
	var get_date=function (){
		PT.show_loading('正在获取数据');
		PT.sendDajax({'function':'web_get_campaign_list'});
	};

	var update_checked_count=function() {
		checked_count = $('input[class*="kid_box"]:checked').length;
		$('#checked_count').text(checked_count);
	};

	var set_update_camps=function(oper,camp_id_arr) {
		PT.sendDajax({'function':'web_set_camps_status','camp_id_list':camp_id_arr,'oper':oper,'name_space':'Campaign_list'});
	};

	//给修改计划日限额的弹窗弹中的"确定"和"取消"加上关闭弹窗件
	var budget_popover_after=function (e){
		App.initTooltips();
		budget_popover_set(e);

		$('#budget_submit').click(function(){
			if(modify_camp_budget(e)){
				$(e.target).popover('hide');
			}
		});

		$('#budget_cancel').click(function(){
			$(e.target).popover('hide');
		});

		//控制日限额显示，当选中不限时隐藏下面的框
		$('#edit_budget_box').find('input[name="budget_radio"]').click(function(){
			if($(this).val()=='1'){
				$('#put_setting').show();
				$('#budget_value').attr('disabled',false);
			}else{
				$('#put_setting').hide();
				$('#budget_value').attr('disabled',true);
			}
		});
	};

	//页面显示时设置弹出层显示状态是不限制日限额还是已设置
	var budget_popover_set=function (e){
		var budget=parseInt($(e.target).text());
		if(!isNaN(budget)){
			var smooth=parseInt($(e.target).parent().find('[id^="is_smooth"]').val());
			$('#set_budget').attr('checked',true);
			$('#budget_value').val(budget);
			$('#put_setting').find('[name="smooth_radio"]').eq(smooth).attr('checked',true);
		}else{
			$('#noset_budget').attr('checked',true);
			$('#put_setting').hide();
			$('#budget_value').attr('disabled',true);
		}
	};

	var modify_camp_budget=function (e){
		var budget,
			use_smooth=true,
			camp_id=$(e.target).parents('tr').find('td:first input').val(),
			is_set_budget=parseInt($('input[name="budget_radio"]:checked').val());
		//判断是否设置日限额
		if(is_set_budget){
			budget=$('#budget_value').val();
			use_smooth=$('#put_setting').find('[name="smooth_radio"]').eq(1).attr('checked')=='checked';
			if(!check_budget(budget)){
				return false;
			}
		}else{
			budget=20000000;
		}
		PT.show_loading('正在修改计划日限额');
		PT.sendDajax({
			'function':'web_modify_camp_budget',
			'camp_id':camp_id,
			'budget':parseInt(budget,10),
			'use_smooth':use_smooth
		});
		return true;
	};

	var check_budget=function (budget){
		var re=/^[1-9]+[0-9]*]*$/ ;
		if(budget==''){
			PT.alert('日限额不能为空');
			return false;
		}
		if(parseInt(budget)>=100000){
			PT.alert('<div style="text-indent:2em">日限额不能超过10万元 ! </div></br><div style="text-indent:2em">因为淘宝只允许第三方软件修改日限额最大为10万，如果您确定要修改为'+budget+'元，请到直通车后台修改</div>');
			return false;
		}
		if(parseInt(budget)<30){
			PT.alert('日限额不能低于30元');
			return false;
		}
		if(!re.test(budget)){
			PT.alert('日限额只能为整数');
			return false;
		}
		return true;
	};

/*	//修改标题弹出层显示前调用
	var title_popover_before=function (e){
		$('#campaign_table .edit_title').not($(e.target)).popover('hide');
	}*/

	//修改标题弹出层显示后调用
	var title_popover_after=function (e){

		title_popover_set(e);

		//确定按钮
		$(e.target).next().find('button:first').click(function(){
			if(modify_camp_title(e)){
				$(e.target).popover('hide');
			}
		});

		//取消按钮
		$(e.target).next().find('button:eq(1)').click(function(){
			$(e.target).popover('hide');
		});
	};

	//设置弹出默认计划名称
	var title_popover_set=function (e){
		$(e.target).next().find('input').val($(e.target).prev().text());
	};

	//设置计划标题
	var modify_camp_title=function (e){
		var old_title=$(e.target).prev().text(),
			new_title=$(e.target).next().find('input').val(),
			camp_id=$(e.target).parent().prev().find('input').val();
		if(check_camp_title(old_title,new_title,e)){
			PT.show_loading('正在修改计划名称');
			PT.sendDajax({
				'function':'web_modify_camp_title',
				'camp_id':camp_id,
				'new_title':new_title
				});
			return true;
		}else{
			return false;
		}
	};

	//检测输入标题是否合法
	var check_camp_title=function (old_title,new_title,e){
		if($.trim(new_title)==''){
			PT.alert('标题不能为空');
			return false;
		}
		if(old_title==new_title){
			$(e.target).popover('hide');
			return false;
		}
		return true;
	};

	var platform_popover_after=function (e){

		platform_popover_set(e);

		$('#outside_discount,#mobile_discount').slider({"from":0,
                                "to":200,
                                'step':1,
                                "range":'min',
                                "skin":"plastic",
                                "limits":false,
                                "dimension":"&nbsp;%",
                                'scale': [0, '|', 50, '|', 100, '|', 150, '|', 200]
                            });

		$("input[name='pc_insite_nonsearch']").on('click', function(){
			var jq_inputs = $("input[name='pc_outsite_nonsearch']");
			if (parseInt($(this).val()) == 1) {
				jq_inputs.attr('disabled', false).removeClass('non_cursor');
				jq_inputs.parent().removeClass('non_cursor');
			} else {
				jq_inputs.eq(0).attr('checked', 'checked');
				jq_inputs.attr('disabled', 'disabled').addClass('non_cursor');
				jq_inputs.parent().addClass('non_cursor');
			}
		});

		//确定按钮
		$(e.target).next().find('button:first').click(function(){
			if(modify_platform(e)){
				$(e.target).popover('hide');
			}
		});

		//取消按钮
		$(e.target).next().find('button:eq(1)').click(function(){
			$(e.target).popover('hide');
		});
	};

	var platform_popover_set=function(e){
		var jq_div = $(e.target).next();
			pform = eval('('+$(e.target).attr('platform')+')');
		for (var prop in pform) {
			jq_div.find('[name="'+prop+'"]').eq(pform[prop]).attr('checked', true);
		}
		jq_div.find('#outside_discount').val(pform['outside_discount']);
		jq_div.find('#mobile_discount').val(pform['mobile_discount']);
		var is_set_nonsearch = $(e.target).attr('is_set_nonsearch');
		if (is_set_nonsearch == '0') {
			$(".can_set").remove();
			$('.not_set').show();
		}
		App.initTooltips();
	};

	var modify_platform=function (e){
		var jq_div = $(e.target).next(),
			outside_discount = jq_div.find('#outside_discount').val(),
			mobile_discount = jq_div.find('#mobile_discount').val(),
			jq_inputs = jq_div.find('input[type="radio"]:checked'),
			result_data = {},
			camp_id = $(e.target).parents('tr').find('.kid_box').val();
		jq_inputs.each(function () {
			result_data[$(this).attr('name')] = parseInt($(this).val());
		});
		result_data.outside_discount = parseInt(outside_discount);
		result_data.mobile_discount = parseInt(mobile_discount);
		$(e.target).data('modify_data', result_data);
		PT.show_loading('正在设置计划投放平台');
		PT.sendDajax({
			'function':'web_update_camp_platform',
			'camp_id':camp_id,
			'platform_dict':$.toJSON(result_data)
			});
		return true;
	};

	//用于ajax调用之后初始化dom元素,避免使用live方法
	var ajax_init_dom=function (){

		var edit_budget_temp=$('#edit_budget_temp').html()
			,budget_popover_temp=$('#budget_popover_temp').html()
			,platform_popover_temp=$('#platform_popover_temp').html()
			,title_popover_temp=$('#title_popover_temp').html();

		$('.edit_btn').popover({
			'trigger':'click',
			'title':'修改计划日限额',
			'content':edit_budget_temp,
			'html':true,
			'placement':'bottom',
			'fnAfterShow':budget_popover_after,
			'template':budget_popover_temp,
			'multi':true	//同屏只显示一个
		});

		//App.initUniform(); //重绘Ajax新生成的form元素

		$('.edit_title').popover({
			'trigger':'click',
			'html':true,
			'placement':'bottom',
			'title':'修改计划标题（不超过20个汉字）',
			'content':title_popover_temp,
			'fnAfterShow':title_popover_after,
			'multi':true   //同屏只显示一个
		});

		$('.edit_platform').popover({
			'trigger':'click',
			'html':true,
			'placement':'bottom',
			'title':'修改投放平台',
			'content':platform_popover_temp,
			'fnAfterShow':platform_popover_after,
			'multi':true   //同屏只显示一个
		});

		$('.show_trend_chart').click(function(){
			var camp_id=$(this).parents('td').prev().find('input').val();
			PT.sendDajax({'function':'web_show_camp_trend','camp_id':camp_id});
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
            update_checked_count();
        });

        $('input[class*="kid_box"]').click(function(){
            update_checked_count();
            $(this).parent().toggleClass('check_box_color');
        });

	};

    return {

        //main function to initiate the module
        init: function (){
        	PT.initDashboardDaterange();
			PT.Base.set_nav_activ(2,0);
			get_date();
			init_dom();
        },
		append_table_data:function(data){
			var tr_str='',table=$('#campaign_table'),total_camp_count;
			for (d in data){
				if(!isNaN(d)){
					data[d].platform_str=$.toJSON(data[d].platform);
					tr_str+=template.render('campaign_tr',data[d]);
				}
			}
			total_camp_count=data.length;
			PT.hide_loading();
			if(PT.hasOwnProperty('campaign_table')){
				PT.campaign_table.fnDestroy(); //删除datetable
			}
			table.find('tbody tr').remove();
			table.find('tbody').append(tr_str);
			//table.show();
			init_sort();
			$('#total_camp_count').text(total_camp_count);
			ajax_init_dom();
			App.initTooltips();
			init_help();
		},
		select_call_back:function(value){
			PT.sendDajax({'function':'web_get_campaign_list','last_day':value});
		},
		modify_title_call_back:function(result){
			PT.hide_loading();
			if(result.status){
				PT.alert('修改计划名称成功！');
				$('#title_'+result.camp_id).text(result.new_title);
			}else{
				PT.alert(result.err);
			}
		},
		modify_budget_call_back:function(result){
			PT.hide_loading();
			if(result.status){
				PT.light_msg('修改日限额','修改成功！');
				var budget_hide=$('#budget_value_hide_'+result.camp_id);
				var budget_show=$('#budget_value_show_'+result.camp_id);
				if(result.budget<20000000){
					budget_hide.text(result.budget);
					budget_show.text(result.budget);
				}else{
					budget_hide.text(result.budget);
					budget_show.text('不限');
				}

				$("#is_smooth_"+result.camp_id).val(result.use_smooth=='true'?1:0);

				PT.campaign_table.fnDestroy();//日限额改变后重新加载datatable
				init_sort();
			}else{
				PT.alert(result.err);
			}
		},
		update_camp_back:function(oper, succ_camp_ids, failed_camp_ids) {
			for (var i=0; i<succ_camp_ids.length; i++){
				var camp_id=succ_camp_ids[i],
					jq_status=$('#status_'+camp_id);
				jq_status.prev().text(oper);
				if(oper){
					jq_status.text('推广中');
					jq_status.parents('tr').removeClass('mnt_tr');
				}else{
					jq_status.text('已暂停');
					jq_status.parents('tr').addClass('mnt_tr');
				}
			}
			if(failed_camp_ids.length > 0){
				var status_desc = (oper? '启用' : '暂停');
				PT.alert(status_desc+"失败"+failed_camp_ids.length+"个计划");
			}
		},
		show_camp_trend:function(camp_id, category_list, series_cfg_list) {
			var cmap_title = $('#title_'+camp_id).text();
			$('#camp_trend_title').text(cmap_title);
			PT.draw_trend_chart( 'camp_trend_chart' , category_list, series_cfg_list);
			$('#modal_camp_trend').modal();
		},
		update_platform_back:function(camp_id, is_success, msg_list) {
			if (is_success) {
				var jq_a = $('#platform_'+camp_id),
					modify_data = jq_a.data('modify_data'),
					plat_str = '计算机';
				jq_a.attr('platform', $.toJSON(modify_data));
				if (modify_data.yd_insite + modify_data.yd_outsite > 0) {
					plat_str += '&nbsp移动设备';
				}
				jq_a.html(plat_str);

			}
		}
    };
}();
