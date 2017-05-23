PT.namespace('Adgroup_list');
PT.Adgroup_list = function () {

	var search_type='all', //快速查找的类型
		PAGE_NO=1,
		PAGE_SIZE=100,//表格每页显示的记录数
		adgroup_table=null,
		is_quick_entry=parseInt($('#is_quick_entry').val()),
		campaign_id=$('#campaign_id').val(),
		search_val=$('#search_val').val();

	var get_last_day=function (){
		return $('#dashboard-report-range').find('input[name="last_day"]').val();
	}

	var init_table= function (){
		adgroup_table=$('#adgroup_table').dataTable({
			"bRetrieve": true, //允许重新初始化表格
			"bPaginate": false,
			"bFilter": true,
			"bInfo": false,
			"aaSorting": [[7,'desc'],[6,'desc'],[3, 'desc']],
			"bAutoWidth":false,//禁止自动计算宽度
            "sPaginationType": "bootstrap",
            'sDom': "T<'row-fluid't<'row-fluid mt10'<'span12 pl10'i><'span12 pr10 tr'p>>",
			"aoColumns": [
				{"bSortable": false},
				{"bSortable": false},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "string"},
				{"bSortable": true},
				{"bSortable": false}
			],
			"oLanguage": {
				"sZeroRecords": "没有符合要求的宝贝",
				"sInfoEmpty": "显示0条记录"
			}
		});
	}


	var init_dom=function (){

		$('.page_size').text(PAGE_SIZE);

		//当计划切换时,重新获取数据
		$('#id_campaign_id').change(function (){
			PT.show_loading('正在切换计划');
			campaign_id = $(this).val();
			if ($('#campaign_id').val()!='0') {
				window.location.href = '/web/adgroup_list/' + campaign_id;
			}
			get_adgs(1);
		});

		$('#search_btn').click(function (){
			search_adg();
		});

		$('#search_val').keyup(function(e){
			if (e.keyCode==13) {
				search_adg();
			}
		});

		//快速查找事件
		$('#id_quick_search').change(function(){
			search_type=$(this).attr('value');
			get_adgs(1);
		});

//		setTimeout(function(){
//			PT.aks.start();
//		},PT.aks.delay);

		$('#select_campaign').click(function(){
		    $('#modal_select_campaign').modal('show');
		});

		$('#redirect_campaign').click(function(){
		    var campaign_id = $('#campaign_2add_item').val();
		    window.location.href = '/web/adgroup_list/' + campaign_id + '?add_item_flag=1';
		});

		$('#show_keyword_count').unbind('click');
		$('#show_keyword_count').click(function () {
			$('#adgroup_table .keyword_count_str').show();
			var adgroup_id_list = $.map($('#adgroup_table [name="adg_checkbox"]'), function (obj) {
				return Number(obj.value);
			});
			PT.sendDajax({
				'function':'web_get_keyword_count',
				'adgroup_id_list':$.toJSON(adgroup_id_list),
				'namespace':'Adgroup_list'
			});
		});
	}

	var init_help=function(){
		var help_list=[
			{
				element:'#adg_control',
				content:'1/3 批量操作在这里！',
				placement:'right'
			},
			{
				element: "#id_campaign_id",
				content: "2/3 这里可以切换不同的计划",
				placement:'bottom'
			},
			{
				element:'#adgroup_table td:eq(2)',
				content:'3/3 点击标题后面的小扳手可以直接进入标题优化',
				placement:'bottom'
			}
		];
		PT.help(help_list);
	}

	var search_adg=function() {
		search_val=$('#search_val').val();
		get_adgs();
	}

	var ajax_init_dom=function (){

		$('.update_adg').click(function(){
			var adg_id_arr=[], mode=$(this).attr('name'),
				mode_str = (mode=='start' ? '启动推广' : (mode=='stop' ? '暂停推广' : '删除【将在直通车后台消失且无法恢复，不要误删哦】'));
			if($(this).hasClass('single')){
				var adg_id_arr=[parseInt($(this).parents('tr').find('.checkboxes.kid_box').val())];
				if (mode=='del') {
					PT.confirm('确认'+mode_str+'该宝贝？',update_adg_status,[mode,adg_id_arr]);
				} else {
					update_adg_status(mode,adg_id_arr);
				}
				return;
			}else{
				var obj=$('#adgroup_table tbody input:checked');
			}
			obj.each(function(){
				adg_id_arr.push(parseInt($(this).val()));
			});
			if (adg_id_arr.length){
				if(mode=='del' && $(".father_box").is(':checked')){
					PT.confirm('即将删除本页所有推广宝贝，删除后将在直通车后台消失且无法恢复，确认要删除吗？',confirm_update_adgs,[mode_str,mode,adg_id_arr]);
				} else {
					confirm_update_adgs(mode_str,mode,adg_id_arr);
				}
			}else{
				PT.alert('请选择要操作的推广宝贝');
			}
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
            get_checked_num();
        });

        $('input[class*="kid_box"]').click(function(){
            get_checked_num();
            $(this).parent().toggleClass('check_box_color');
        });

		$select({name: 'adg_checkbox','callBack': update_checked_status});
		adgroup_table.fnSettings()['aoDrawCallback'].push({ //当表格排序时重新初始化checkBox右键多选
			'fn':function(){selectRefresh()},
			'sName':'refresh_select'
		});
	}

	//发送请求获取数据
	var get_adgs=function (is_reset){
		PT.show_loading('正在获取数据');
		if(is_reset){
			PAGE_NO=1;
			$('#dynamic_pager').html('').off('page');
		}
		PT.sendDajax({
			'function':'web_get_adgroup_list',
			'campaign_id':campaign_id,
			'page_size':PAGE_SIZE,
			'page_no':PAGE_NO,
			'last_day':get_last_day(),
			'sSearch':search_val,
			'search_type':search_type,
			'is_quick_entry':is_quick_entry,
			'auto_hide':0,
			'page_type':$('#adgroup_table').attr('page') || '',
			'offline_type':$('#offline_type').val()
		});
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
		get_checked_num();
	}

	var get_checked_num=function() {
		var checked_num = $('input[class*="kid_box"]:checked').length;
		$('#current_count').text(checked_num);
		return checked_num;
	}

	var set_mnt_info=function (is_mnt,mnt_num) {
		if (is_mnt==0) {
			$('#is_mnt').hide();
		} else {
			$('#mnt_adg_count').text(mnt_num);
			$('#is_mnt').show();
		}
	}

	var confirm_update_adgs=function (mode_str,mode,adg_id_arr){
		var opt_num=adg_id_arr.length;
		PT.confirm('确认'+mode_str+'所选的'+opt_num+'个宝贝吗？',update_adg_status,[mode,adg_id_arr]);
	}

	//改变宝贝的推广状态
	var update_adg_status=function (mode,adg_id_arr){
		PT.show_loading("正在提交数据到后台");
		PT.sendDajax({'function':'web_update_adg_status','adg_id_list':adg_id_arr,'mode':mode,'campaign_id':campaign_id,'mnt_type':$('#mnt_type').val(),'namespace':'Adgroup_list'});
	}

	var change_tr_color=function(){
		var obj=$('#adgroup_table tbody input[type="checkbox"]');
		obj.each(function(){
            if($(this).attr('online_status')=='offline'){
				$(this).parents('tr').addClass('mnt_tr');
			}
        });
	}

	var handle_page=function(page_count,page_no){
		$('#dynamic_pager').bootpag({
				total: page_count,
				page: page_no,
				leaps: false,
				prev:'上一页',
				next:'下一页',
				maxVisible: 10
		}).on('page', function(event, num){
				PAGE_NO=num;
				get_adgs(0);
		});
	}

    return {
        //main function to initiate the module
        init: function () {
			PT.initDashboardDaterange();
			init_dom();
			get_adgs(1);
			if(is_quick_entry){
				var page=$('#adgroup_table').attr('page');
				var index=$('#quick_entry a').index($('#quick_entry a[page='+page+']'));
				PT.Base.set_nav_activ(3,index);
			}else{
				PT.Base.set_nav_activ(2,1);
				init_help();
			}
		   //PT.aks.start();
        },
		append_table_data:function (page_info,data,mnt_info){
			//后台回调函数
			if (!Number($('#add_item_flag').val())) {
				PT.hide_loading();
			} else {
                $('#add_item').click();
            }
			var table=$('#adgroup_table'),temp_str='';
			if(adgroup_table){
				adgroup_table.fnDestroy();
				table.find('tbody tr').remove();
			}

			template.helper('$parseData', function(content, rate){
			    return parseInt(Number(content)/rate);
			});

			for (var i=0;i<data.length;i++){
				temp_str += template.render('adgroup_tr', data[i]);
			}
			table.find('tbody').html(temp_str);
			init_table();
			set_mnt_info(mnt_info.is_mnt,mnt_info.mnt_num);

			//初始化分页器及页数信息
			$('#current_count').text(0);
			$('.page_count').text(page_info.page_count);
			$('#adgroup_count').text(page_info.total_count);
			if (!$('#dynamic_pager ul').length){
				handle_page(page_info['page_count'],page_info['page_no']);
			}

			ajax_init_dom();
			App.initTooltips();
			new FixedHeader(adgroup_table,{'offsetTop':40});
			$('#mnt_type').val(mnt_info.mnt_type);
			change_tr_color();
		},
		select_call_back:function(value){
			//改变天数的回调函数
			get_adgs(0);
		},
		get_adgroup_fail:function(){
			//获取数据失败
			PT.hide_loading();
			PT.alert('获取数据失败,请稍后重试','red');
		},
		update_adg_back:function(mode,result){
			PT.hide_loading();
			switch(mode){
				case 'start':
					for(var i=0; i<result.success_id_list.length; i++) {
						var adg_id = result.success_id_list[i],
							jq_status=$('#status_'+adg_id),
							jq_tr=$('input[value='+adg_id+']').parents('tr');
						jq_tr.removeClass('mnt_tr');
						jq_status.text('推广中').removeClass('r_color');
						jq_status.next().attr('name','stop').removeClass('icon-play-circle').removeClass('g_color').addClass('icon-pause').addClass('r_color').attr('data-original-title', '暂停推广');
					}
					break;
				case 'stop':
					for(var i=0; i<result.success_id_list.length; i++) {
						var adg_id = result.success_id_list[i],
							jq_status=$('#status_'+adg_id),
							jq_tr=$('input[value='+adg_id+']').parents('tr');
						jq_tr.addClass('mnt_tr');
						jq_status.text('已暂停').addClass('r_color');
						jq_status.next().attr('name','start').removeClass('icon-pause').removeClass('r_color').addClass('icon-play-circle').addClass('g_color').attr('data-original-title', '参与推广');
					}
					break;
				case 'del':
					for(var i=0; i<result.success_id_list.length; i++) {
						var jq_tr=$('#status_'+result.success_id_list[i]).parents('tr');
						adgroup_table.fnDeleteRow(jq_tr[0]);
					}
					var msg = '';
					if(result.error_msg){
						msg=result.error_msg;
					}else{
						if(result.ztc_del_count>0){
							msg += "您已经在直通车后台删除了"+result.ztc_del_count+"个推广宝贝";
						}
						msg += result.cant_del_list.length? ("有"+result.cant_del_list.length+"个推广宝贝无法删除"):'';
					}
					if(msg){
						PT.alert(msg);
					}
					var num=$('#adgroup_count').text()-result.success_id_list.length;
					$('#mnt_adg_count').text(result.mnt_num);
					$('#adgroup_count').text(num);
					get_checked_num();
					break;
			}
		},
		'get_keyword_count_callback':function (keyword_dict) {
			$.map($('#adgroup_table .keyword_count_str'), function (obj) {
				var adgroup_id = Number($(obj).closest('tr').find('[name="adg_checkbox"]').val());
				var keyword_count = Number(keyword_dict[adgroup_id]);
				if (isNaN(keyword_count)) {
					$(obj).siblings('.keyword_count').html(0);
					$(obj).html('<span class="s_color">没有关键词</span>');
				} else {
					$(obj).siblings('.keyword_count').html(keyword_count);
					$(obj).html(keyword_count+'个关键词');
				}
			});
		}
    };

}();
