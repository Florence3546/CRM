PT.namespace('MntAdg');
PT.MntAdg = function () {
	var camp_id = $('#campaign_id').val(),
		camp_mnt_type=parseInt($('#mnt_type').val()),
		max_num= parseInt($('#mnt_max_num').val()),
		mnt_adg_table=null;
	
	var init_table=function(){
		mnt_adg_table=$('#adgroup_table').dataTable({
			"bRetrieve": true, //允许重新初始化表格
			"bPaginate": true,
			"bFilter": true,
			"bInfo": false,
			"aaSorting": [[6,'desc'],[5,'desc'],[2, 'desc']],
			"bAutoWidth":false,//禁止自动计算宽度
			"iDisplayLength": 50,
			"sDom":"<'row-fluid't<'row-fluid marb_24'<'span6'i><'span6'p>>",
			"aoColumns": [
				{"bSortable": false},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": true},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"}
			],
			"oLanguage": {
				"sSearch": "搜索:",
				"sLengthMenu": "每页显示 _MENU_ 条记录",
				"sZeroRecords": "没有记录",
				"sInfo": "显示第_START_条到第_END_条记录, 共_TOTAL_条记录",
				"sInfoEmpty": "显示0条记录",
				"oPaginate": {
					"sPrevious": " 上一页 ",
					"sNext":     " 下一页 "
					}
			}		
		});
	}
	
	var init_ajax_dom=function(){
		App.initTooltips();
//		$('.show_price_popover').popover({
//			'trigger':'click',
//			'html':true,
//			'placement':'bottom',
//			'content':$('#limit_price_popover').html(),
//			'fnAfterShow':price_popover_after,
//			'multi':true   //同屏只显示一个
//		});
        $('#adgroup_table').off('click', '.show_price_popover');
        $('#adgroup_table').on('click', '.show_price_popover', function () {
	        set_limit_price(this);
        });
		
		$('.update_adg').unbind('click');
		$('.update_adg').live('click',function(){
			var mode=$(this).attr('name'), adg_id=parseInt($(this).parents('tr').attr('adg_id'));
			if (mode=='del') {
				PT.confirm('确认删除该宝贝吗？【删除后将在直通车后台消失且无法恢复，不要误删哦】',update_adg_status,[mode,adg_id]);
			} else {
				update_adg_status(mode,adg_id);
			}
		});
		
		$('body').off('click', '.mnt_oper.single');
		$('body').on('click', '.mnt_oper.single', function(){
			var adg_mnt_type=Number($(this).attr('mnt_type')),
				mnt_oper=(adg_mnt_type==0?1:0),
				new_num = parseInt($('.new_num').html()),
				adg_id=parseInt($(this).parents('tr').attr('adg_id'));
			if (mnt_oper==0) {
				confirm_mnt_oper(mnt_oper,adg_id);
				return;
			}
			if(new_num<=0){
				var mnt_num= parseInt($('.mnt_num').html());
				PT.alert('已托管'+mnt_num+'个宝贝，达到了托管最大数，若要继续托管，请先删除一些已托管宝贝！');
			}else if(camp_mnt_type==2){
				set_limit_price(this);
			}else{
				confirm_mnt_oper(mnt_oper,adg_id);
			}
		});
		
		$('#submit_mnt_oper').unbind('click');
		$('#submit_mnt_oper').click(function(){
			var limit_price = $.trim($('#adg_limit_price').val()),
				check_error=PT.MntAdg.check_limit_price(limit_price);
			if (check_error=='') {
                $('#adg_limit_price').closest('div').removeClass('input_error');
				$('#modal_limit_price').modal('hide');
				var adg_id=parseInt($('#modal_limit_price').attr('adg_id'));
				$('#tr_'+adg_id).find('.limit_price').text(Number(limit_price).toFixed(2)).parent().show();
				if ($('#modal_limit_price').attr('mnt_type')=='0') {
					confirm_mnt_oper(1, adg_id);
				} else {
					PT.sendDajax({'function':'web_set_adg_limit_price', 'adgroup_id':adg_id, 'limit_price':Number(limit_price).toFixed(2), 'mnt_type':camp_mnt_type});
				}
			} else {
				$('#adg_limit_price').closest('div').addClass('input_error');
				$('#adg_limit_price').next().find('.icon-exclamation-sign').attr('data-original-title', check_error);
			}
		});
		
	}
	
	//改变宝贝的推广状态
	var update_adg_status=function (mode,adg_id){
		if (mode=='del') {
			$('.total_item_count').html('---');
		}
		PT.show_loading("正在提交数据到后台");
		PT.sendDajax({'function':'web_update_adg_status','adg_id_list':[adg_id],'mode':mode,'campaign_id':camp_id,'mnt_type':camp_mnt_type,'namespace':'MntAdg'});
	}
	
	var confirm_mnt_oper=function(mnt_oper,adg_id) {
		PT.show_loading("正在提交数据到后台");
		PT.sendDajax({'function':'mnt_update_adg_mnt',
		    'adg_id_list':$.toJSON([adg_id]),
		    'flag':mnt_oper,
		    'mnt_type':camp_mnt_type,
		    'camp_id':camp_id,
		    'limit_price':Number($.trim($('#adg_limit_price').val())) || 0
		    });
	}
	
	var update_mnt_num=function(add_num){
		var mnt_num=parseInt($('.mnt_num').html()),
			new_num=parseInt($('.new_num').html());
		if (mnt_num+add_num>=0) {
			$('.mnt_num').html(mnt_num+add_num);
			$('.new_num').html(new_num-add_num);
		}
	}
	
	var update_adg_count=function(add_count){
		var jq_adg_count=$('#adg_count'), adg_count=parseInt(jq_adg_count.html());
		jq_adg_count.html(adg_count+add_count);
	}

	var price_popover_after=function (e){
		var jq_a=($(e.target).hasClass('show_price_popover')? $(e.target):$(e.target).parents('.show_price_popover:first')),
			jq_price=jq_a.find('.limit_price'),
			old_price=(Number(jq_price.text())==0?'':jq_price.text());
		jq_a.next().find('input').val(old_price);
		//确定按钮
		jq_a.next().find('.limit_price_submit').click(function(){
			if(modify_limit_price(jq_a)){
				jq_price.text(Number(jq_a.next().find('input').val()).toFixed(2));
				jq_price.parent().show();
				jq_a.popover('hide');
			}
		});
		
		//取消按钮
		jq_a.next().find('.limit_price_close').click(function(){
			jq_a.popover('hide');
		});	
	}
	
	var set_limit_price = function (obj) {
	    var adg_id = parseInt($(obj).parents('tr').attr('adg_id'));
	    var mnt_type = $(obj).parents('tr').find('.is_mnt').text();
	    var limit_price=Number($(obj).parents('tr').find('.limit_price').text()).toFixed(2);
	    limit_price=(limit_price==0?'':limit_price);
	    $('#modal_limit_price').modal('show').attr({'adg_id':adg_id, 'mnt_type':mnt_type}).find('input').val(limit_price);
	    $('#modal_limit_price .input_error').removeClass('input_error');
	    $('#modal_limit_price [name="cat_path"]').empty();
        $('#modal_limit_price .cat_path').removeClass('danger_cat');
	    $('#modal_limit_price [name="cat_avg_cpc"]').empty();
	    $('#modal_limit_price .loading_tag').show();
	    PT.sendDajax({'function':'mnt_get_cat_avg_cpc', 'adg_id':adg_id, 'namespace':'AddItemBox2'});
	}
	
	var modify_limit_price=function (object){
		var old_price=object.find('.limit_price').text(),
			new_price=object.next().find('input').val(),
			adg_id=object.parents('tr').attr('adg_id');
		if(old_price==new_price || $.trim(new_price)==''){
			object.popover('hide');
			return false;
		}
		var check_error=PT.MntAdg.check_limit_price(new_price);
		if(check_error==''){
			PT.sendDajax({
				'function':'web_set_adg_limit_price',
				'adgroup_id':adg_id,
				'limit_price':Number(new_price)
				});
			return true;
		}else{
			PT.alert(check_error);
			return false;	
		}
	}
	
	return {
		init:function(){
			PT.initDashboardDaterange();
			PT.MntAdg.select_call_back(1);
		},
		select_call_back: function(value){
			PT.show_loading('正在加载宝贝数据');
			PT.sendDajax({'function':'mnt_get_mnt_adg','rpt_days':value,'campaign_id':camp_id});
		},
		get_adg_back:function(adg_list, mnt_num){
			PT.hide_loading();
			
			template.helper('$parseData', function(content, rate){
                return parseInt(Number(content)/rate);
            });
			
			var tr_str='',table=$('#adgroup_table');
			for (var d in adg_list){
				if(!isNaN(d)){
					tr_str+=template.render('adgroup_tr',adg_list[d]);
				}
			}
			$('#adg_count').text(adg_list.length);
			$('.mnt_num').html(mnt_num);
			$('.new_num').html(max_num-mnt_num);
			if(mnt_adg_table){
				mnt_adg_table.fnDestroy();
			}
			table.find('tbody tr').remove();
			table.find('tbody').append(tr_str);
			init_table();
			init_ajax_dom();
		},
		check_limit_price:function (limit_price){
			var error='';
			var limit_price_min = parseFloat($('.limit_price_min').html()).toFixed(2) || 0.02 ,
				limit_price_max=parseFloat($('.limit_price_max').html()).toFixed(2);
			if($.trim(limit_price)==''){
				error='值不能为空！';
			}else if(isNaN(limit_price)){
				error='值必须是数字！';
			}else if (Number(limit_price)<limit_price_min || Number(limit_price)>limit_price_max){
				error='值必须介于'+limit_price_min+'~'+limit_price_max+'元之间！';
			}
			return error;
		},
		update_adg_back:function(mode,result){
			PT.hide_loading();
			var adg_id=result.success_id_list[0], jq_adg_status=$('#status_'+adg_id), jq_tr=$('#tr_'+adg_id);
			switch(mode){
				case 'start':
					jq_tr.removeClass('mnt_tr');
					jq_adg_status.text('推广中').removeClass('r_color');
					jq_adg_status.next().attr('name','stop').removeClass('icon-play-circle g_color').addClass('icon-pause r_color');
					break;
				case 'stop':
					jq_tr.addClass('mnt_tr');
					jq_adg_status.text('已暂停').addClass('r_color');
					jq_adg_status.next().attr('name','start').removeClass('icon-pause r_color').addClass('icon-play-circle g_color');
					break;
				case 'del':
					if(result.error_msg){
						PT.alert(result.error_msg);
					}else{
						if(adg_id){
							mnt_adg_table.fnDeleteRow(jq_tr[0]);
							update_mnt_num(-1);
							update_adg_count(-1);
						} else if(result.cant_del_list) {
							PT.alert("该宝贝无法删除");
						}
						break;
					}
			}
			if (result.ztc_del_list && result.ztc_del_list.length){
				PT.alert("您已经在直通车后台删除了该宝贝");
				var del_tr=$('#tr_'+result.ztc_del_list[0]);
				mnt_adg_table.fnDeleteRow(del_tr[0]);
				update_mnt_num(-1);
				update_adg_count(-1);
			}
		},
        update_mnt_back: function(adg_id_list,status){
            var adg_id= $.evalJSON(adg_id_list)[0],
				jq_tr=$('#tr_'+adg_id),
				adg_mnt_type=(status?camp_mnt_type:0);
				jq_adg_status=$('#status_'+adg_id);
			jq_tr.find('.no_mnt').toggleClass('hide');
			jq_tr.find('.is_mnt').text(adg_mnt_type);
			if(camp_mnt_type==1) {
				jq_tr.find('.mnt_oper').remove();
			} else {
				jq_tr.find('.mnt_oper').text(status>0?'取消托管':'加入托管').attr('mnt_type',adg_mnt_type);
			}
			update_mnt_num(parseInt(status)?1:-1);   
			if (status) {
                jq_tr.removeClass('mnt_tr');
                jq_adg_status.text('推广中').removeClass('r_color');
                jq_adg_status.next().attr('name','stop').removeClass('icon-play-circle g_color').addClass('icon-pause r_color');
			}
        }
	}	
}();