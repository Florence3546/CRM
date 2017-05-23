PT.namespace('ConsultManager');
PT.ConsultManager = function(){

	//从下拉框选择顾问、放入候选表中
	var add_diser = function(consult_id, allocate_num){
		if(consult_id!=null){
//			var option_obj = $('#id_candidate_list>option[value='+consult_id+']');
//			var name = $(option_obj).attr('name');
//			var now_load = $(option_obj).attr('now_load');
//			var weight = $(option_obj).attr('weight');
//			$('#id_dirstribute_table>tbody').append(template.render('id_distribute_template', {'consult_id':consult_id, 'name':name, 'now_load':now_load, 'weight':weight, 'allocate_num':allocate_num}));
//			$(option_obj).remove();
			
			var tr_obj = $('#id_consult_table #'+consult_id);
//			var customer_count = 0;
//			switch ($('#customer_type').val()) {
//				case '0':
//					customer_count = tr_obj.find('td:eq(4)').html();
//					break;
//                case '1':
//                    customer_count = tr_obj.find('td:eq(5)').html();
//                    break;
//                case '2':
//                    customer_count = tr_obj.find('td:eq(6)').html();
//                    break;
//			}
			$('#id_dirstribute_table>tbody').append(template.render('id_distribute_template', {
				'consult_id':consult_id,
				'department':tr_obj.find('td:eq(1)').attr('department'),
				'name':tr_obj.find('td:eq(0)').html(),
				'customer_count':tr_obj.find('td:eq('+$('#customer_type option:selected').attr('td_index')+')').html() || '-',
				'weight':tr_obj.find('.consult_weight').val(),
				'allocate_num':allocate_num
			}));
			$('#id_candidate_list>option[value='+consult_id+']').remove();
			refresh_dirstribute_sum();
		}
	};
	
	//根据给出主顾问，重新生成select下拉框
	var rebuild_selector = function(consult_id){
//		$('#id_candidate_list').html('');
//		var consult_list = $('#id_consult_table>tbody>tr');
//		for(var i=0;i<consult_list.length;i++){
//			var temp_consult_id = parseInt($(consult_list[i]).attr('id'));
//			var temp_type = $(consult_list[i]).attr('work_type');
//			var temp_weight = parseInt($(consult_list[i]).find('input').val() || $('#'+temp_consult_id+' td:eq(4)').html());
//			if(temp_consult_id!=consult_id && (temp_type == 'CONSULT' || temp_type == 'CONSULTLEADER')) {
//				$('#id_candidate_list').append(template.render('id_candidate_template', {'name': $(consult_list[i]).find('td:eq(0)').text(),
//					'now_load':$(consult_list[i]).find('td:eq(3)').text(), 'consult_id':temp_consult_id, 'weight':temp_weight}));
//			}
//		}
		var html_candidate_list = '';
		$('#id_consult_table>tbody>tr').each(function () {
			if (this.id!=consult_id && !$(this).hasClass('red')) {
				html_candidate_list += template.render('id_candidate_template', {
					'consult_id':this.id,
					'department':$(this).find('td:eq(1)').attr('department'),
					'name':$(this).find('td:eq(0)').html(),
					'customer_count_str':$('#customer_type option:selected').html(),
					'customer_count':$(this).find('td:eq('+$('#customer_type option:selected').attr('td_index')+')').html() || '-',
					'weight':$(this).find('.consult_weight').val()
				});
			}
		});
		$('#id_candidate_list').html(html_candidate_list);
		//清空候选列表
		$('#id_dirstribute_table>tbody').html('');
	};
	
	//刷新权重统计值
	var refresh_weight = function () {
		var group1_weight = eval($.map($('#id_consult_table tr[department=GROUP1]:not(.red)'), function (tr_obj) {var wt = Number($(tr_obj).find('.consult_weight').val()) || 0;return wt>0?wt:0}).join('+') || '0');
		var group2_weight = eval($.map($('#id_consult_table tr[department=GROUP2]:not(.red)'), function (tr_obj) {var wt = Number($(tr_obj).find('.consult_weight').val()) || 0;return wt>0?wt:0}).join('+') || '0');
		var group3_weight = eval($.map($('#id_consult_table tr[department=GROUP3]:not(.red)'), function (tr_obj) {var wt = Number($(tr_obj).find('.consult_weight').val()) || 0;return wt>0?wt:0}).join('+') || '0');
		var tgroup_weight = eval($.map($('#id_consult_table tr[department=OTHERS]:not(.red)'), function (tr_obj) {var wt = Number($(tr_obj).find('.consult_weight').val()) || 0;return wt>0?wt:0}).join('+') || '0');
		var mkt_weight = eval($.map($('#id_consult_table tr[department=MKT]:not(.red)'), function (tr_obj) {var wt = Number($(tr_obj).find('.consult_weight').val()) || 0;return wt>0?wt:0}).join('+') || '0');
		$('#group1_weight').html(group1_weight);
		$('#group2_weight').html(group2_weight);
		$('#group3_weight').html(group3_weight);
		$('#tgroup_weight').html(tgroup_weight);
		$('#mkt_weight').html(mkt_weight);
		$('#weight_sum').html(group1_weight+group2_weight+group3_weight+tgroup_weight+mkt_weight);
		var modified = false;
		$('#id_consult_table input.consult_weight.editable').each(function () {
			if ((Number(this.value) || 0)!=Number($(this).attr('org_value'))) {
				modified = true;
				return false;
			}
		});
		if (modified) {
			$('#id_modify_weight').attr('disabled', false);
		} else {
			$('#id_modify_weight').attr('disabled', true);
		}
	};
	
	//刷新客户数
	var refresh_customer_count = function () {
	    //总客户数
        var group1_customer = eval($.map($('#id_consult_table tr[department=GROUP1]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(4)').html()) || 0;}).join('+') || '0');
        var group2_customer = eval($.map($('#id_consult_table tr[department=GROUP2]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(4)').html()) || 0;}).join('+') || '0');
        var group3_customer = eval($.map($('#id_consult_table tr[department=GROUP3]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(4)').html()) || 0;}).join('+') || '0');
        var tgroup_customer = eval($.map($('#id_consult_table tr[department=OTHERS]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(4)').html()) || 0;}).join('+') || '0');
        var mkt_customer = eval($.map($('#id_consult_table tr[department=MKT]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(4)').html()) || 0;}).join('+') || '0');
        $('#group1_customer').html(group1_customer);
        $('#group2_customer').html(group2_customer);
        $('#group3_customer').html(group3_customer);
        $('#tgroup_customer').html(tgroup_customer);
        $('#mkt_customer').html(mkt_customer);
        $('#customer_sum').html(group1_customer+group2_customer+group3_customer+tgroup_customer+mkt_customer);
        //服务中
        var group1_inservice = eval($.map($('#id_consult_table tr[department=GROUP1]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(5)').html()) || 0;}).join('+') || '0');
        var group2_inservice = eval($.map($('#id_consult_table tr[department=GROUP2]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(5)').html()) || 0;}).join('+') || '0');
        var group3_inservice = eval($.map($('#id_consult_table tr[department=GROUP3]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(5)').html()) || 0;}).join('+') || '0');
        var tgroup_inservice = eval($.map($('#id_consult_table tr[department=OTHERS]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(5)').html()) || 0;}).join('+') || '0');
        var mkt_inservice = eval($.map($('#id_consult_table tr[department=MKT]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(5)').html()) || 0;}).join('+') || '0');
        $('#group1_inservice').html(group1_inservice);
        $('#group2_inservice').html(group2_inservice);
        $('#group3_inservice').html(group3_inservice);
        $('#tgroup_inservice').html(tgroup_inservice);
        $('#mkt_inservice').html(mkt_inservice);
        $('#inservice_sum').html(group1_inservice+group2_inservice+group3_inservice+tgroup_inservice+mkt_inservice);
        //已过期
        var group1_expired = eval($.map($('#id_consult_table tr[department=GROUP1]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(6)').html()) || 0;}).join('+') || '0');
        var group2_expired = eval($.map($('#id_consult_table tr[department=GROUP2]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(6)').html()) || 0;}).join('+') || '0');
        var group3_expired = eval($.map($('#id_consult_table tr[department=GROUP3]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(6)').html()) || 0;}).join('+') || '0');
        var tgroup_expired = eval($.map($('#id_consult_table tr[department=OTHERS]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(6)').html()) || 0;}).join('+') || '0');
        var mkt_expired = eval($.map($('#id_consult_table tr[department=MKT]:not(.red)'), function (tr_obj) {return Number($(tr_obj).find('td:eq(6)').html()) || 0;}).join('+') || '0');
        $('#group1_expired').html(group1_expired);
        $('#group2_expired').html(group2_expired);
        $('#group3_expired').html(group3_expired);
        $('#tgroup_expired').html(tgroup_expired);
        $('#mkt_expired').html(mkt_expired);
        $('#expired_sum').html(group1_expired+group2_expired+group3_expired+tgroup_expired+mkt_expired);
	};
	
    //刷新分配数
	var refresh_dirstribute_sum = function () {
        var dirstribute_sum = 0;
        $('#id_dirstribute_table>tbody>tr input').each(function () {
	        if (Number(this.value)>0) {
	            dirstribute_sum += Number(this.value);
	        }
        });
        $('#dirstribute_sum').html(dirstribute_sum);
	};
	
	var init_dom = function(){
		$('#id_consult_table').dataTable({
			'aoColumnDefs':[
				{'bSortable':false, 'aTargets':[0, 7]},
				{'sSortDataType':'dom-input', 'aTargets':[1, 2]}
				],
			'aaSorting':[[1, 'asc'], [4, 'desc']],
			'bPaginate':false,
			'oLanguage':{
				'sInfo':''
				}
			});
		refresh_weight();
		refresh_customer_count();
		$('#id_consult_table tbody input.consult_weight.editable').keyup(refresh_weight);
		$('#id_dirstribute_table tbody').on('keyup', 'tr input', refresh_dirstribute_sum);

	    //保存权重
		$('#id_modify_weight').click(function () {
			if ($(this).attr('disabled')) {
                PT.alert('未作出修改！');
                return;
			}
			if (Number($('#weight_sum').html())!=100) {
				PT.alert('在职顾问的权重总和必须为100！');
				return;
			}
			var weight_dict = {};
			$('#id_consult_table tbody>tr:not(.red)').each(function () {
				var wt = Number($(this).find('.consult_weight').val()) || 0;
				weight_dict[this.id] = wt>0?wt:0;
			});
			PT.confirm(
				'确定要保存当前的权重设置吗？',
				function () {
					PT.show_loading('正在保存权重');
					PT.sendDajax({
						'function':'ncrm_update_consult_weight',
						'weight_dict':$.toJSON(weight_dict),
						'callback':'PT.ConsultManager.update_consult_weight_callback'
					});
				},
				[]
			);
		});

		//切换客户类型
		$('#customer_type').change(function () {
			$('#id_dirstribute_table>thead>tr>th:eq(2)').html($(this).find('option:selected').html());
			rebuild_selector($('#id_consult_id').val());
			$('#dirstribute_sum').html(0);
			var klass = 'red b f18';
			$('#id_distribute_statistic span').removeClass(klass);
			switch (this.value) {
				case '0':
					$('#id_consult_now_load').addClass(klass);
					break;
				case '1':
                    $('#id_consult_inservice').addClass(klass);
                    break;
                case '2':
                    $('#id_consult_expired').addClass(klass);
                    break;
				case '3':
					$('#id_consult_reserved').addClass(klass);
					break;
				case '4':
					$('#id_consult_to_distribute').addClass(klass);
					break;
			}
		});

		//刷新总客户数
		$('#id_refresh_consult').click(function(){
			PT.confirm(
				"确定要刷新客户数吗？可能会比较慢！",
				function () {
					PT.show_loading('正在刷新客户数');
					PT.sendDajax({'function':'ncrm_refresh_consult'});
				},
				[]
			)
		});

		$('#id_reallocate').click(function(){
			PT.confirm("确定要重新分配客户吗？", PT.sendDajax, [{'function':'ncrm_reallocate_consult'}]);
		});

//		$('.save').click(function(){
//			var tr_obj = $(this).parent().parent();
//			var consult_id = parseInt($(tr_obj).attr('id'));
//			var weight = parseInt($(tr_obj).find('.consult_weight').val());
//			PT.sendDajax({'function':'ncrm_update_consult_weight', 'consult_id':consult_id, 'weight':weight});
//		});
		
		$('.distribute').click(function(){
//			var tr_obj = $(this).parent().parent();
//			var consult_id = parseInt($(tr_obj).attr('id'));
//			var name = $(tr_obj).find("td:eq(0)").text();
//			var now_load = $(tr_obj).find("td:eq(3)").text();
			
			var tr_obj = $(this).closest('tr');
			$('#id_consult_id').val(tr_obj.attr('id'));
			$('#id_consult_name').html(tr_obj.find('td:eq(0)').html());
			$('#id_consult_now_load').html(tr_obj.find('td:eq(4)').html());
			$('#id_consult_inservice').html(tr_obj.find('td:eq(5)').html());
			$('#id_consult_expired').html(tr_obj.find('td:eq(6)').html());
			$('#id_consult_reserved').html(tr_obj.find('td:eq(7)').html());
			$('#id_consult_to_distribute').html(tr_obj.find('td:eq(8)').html());

			rebuild_selector(tr_obj.attr('id'));
			$('#id_distribute_layout').modal();
//			$.fancybox.open([{href:'#id_distribute_layout'}], {helpers:{
//                title : {type : 'outside'},
//                overlay : {closeClick: false}
//            }});
		});
		
		$('#id_add_distributer').click(function(){
			var consult_id = $('#id_candidate_list').val();
			add_diser(consult_id, 0);
		});
		
//		$('#id_auto_distribute').click(function(){
//			var sort_func = function(a, b){
//				if((a.now_load/a.weight)> (b.now_load/b.weight)) return 1;
//				else if((a.now_load/a.weight)< (b.now_load/b.weight)) return -1;
//				else return 0;
//			}
//			
//			rebuild_selector($('#id_consult_id').val());
//			var total_count = parseInt($('#id_consult_now_load').text());
//			var obj_list = $('#id_candidate_list>option');
//			var diser_list = new Array();
//			for(var i=0;i<obj_list.length;i++){
//				diser_list.push({
//					'now_load': parseInt($(obj_list[i]).attr('now_load')),
//					'weight':parseInt($(obj_list[i]).attr('weight')),
//					'consult_id':parseInt($(obj_list[i]).val()),
//				});
//			}
//			diser_list = diser_list.sort(sort_func);
//			
//			var add_dict = new Object();
//			while (total_count >0){
//				for(var j=0;j<diser_list.length;j++){
//					var temp_consult_id =diser_list[j].consult_id; 
//					if(total_count > diser_list[j].weight){
//						if(add_dict.hasOwnProperty(temp_consult_id)){
//							add_dict[temp_consult_id] += diser_list[j].weight;
//						}else{
//							add_dict[temp_consult_id] = diser_list[j].weight;
//						}
//						total_count -= diser_list[j].weight;
//					}else{
//						if(add_dict.hasOwnProperty(temp_consult_id)){
//							add_dict[temp_consult_id] += total_count;
//						}else{
//							add_dict[temp_consult_id] = total_count;
//						}
//						total_count = 0;
//						break;
//					}
//				}
//			}
//			for(var temp_cid in add_dict){
//				add_diser(temp_cid, add_dict[temp_cid]);
//			}
//		});
        
        //自动分配
        $('#id_auto_distribute').click(function(){
            var sort_func = function(a, b){
                if((a.customer_count/a.weight)> (b.customer_count/b.weight)) return 1;
                else if((a.customer_count/a.weight)< (b.customer_count/b.weight)) return -1;
                else return 0;
            }
            
            rebuild_selector($('#id_consult_id').val());
            var total_count = 0;
            switch ($('#customer_type').val()) {
	            case '0':
		            total_count = parseInt($('#id_consult_now_load').html());
		            break;
                case '1':
                    total_count = parseInt($('#id_consult_inservice').html());
                    break;
                case '2':
                    total_count = parseInt($('#id_consult_expired').html());
                    break;
                case '3':
                    total_count = parseInt($('#id_consult_now_load').html())-parseInt($('#id_consult_reserved').html());
                    break;
                case '4':
                    total_count = parseInt($('#id_consult_to_distribute').html());
                    break;
            }
            var diser_list = $.map($('#id_candidate_list>option'), function (opt_obj) {
	            var wt = parseInt($(opt_obj).attr('weight'));
                return wt>0?{
                    'consult_id':parseInt(opt_obj.value),
                    'customer_count':parseInt($(opt_obj).attr('customer_count')),
                    'weight':wt
                }:null;
            });
            diser_list = diser_list.sort(sort_func);
            
            var add_dict = new Object();
            while (total_count >0) {
                for(var j=0;j<diser_list.length;j++){
                    var temp_consult_id =diser_list[j].consult_id; 
                    if(total_count > diser_list[j].weight){
                        if(add_dict.hasOwnProperty(temp_consult_id)){
                            add_dict[temp_consult_id] += diser_list[j].weight;
                        }else{
                            add_dict[temp_consult_id] = diser_list[j].weight;
                        }
                        total_count -= diser_list[j].weight;
                    }else{
                        if(add_dict.hasOwnProperty(temp_consult_id)){
                            add_dict[temp_consult_id] += total_count;
                        }else{
                            add_dict[temp_consult_id] = total_count;
                        }
                        total_count = 0;
                        break;
                    }
                }
            }
            for(var temp_cid in add_dict){
                add_diser(temp_cid, add_dict[temp_cid]);
            }
        });
		
		$(document).on('click.PT.remove_distributer', '.remove_distributer', function(){
			var tr_obj = $(this).parent().parent();
			$('#id_candidate_list').prepend(template.render('id_candidate_template', {
				'consult_id':$(tr_obj).attr('id'),
				'department':$(tr_obj).find('td:eq(0)').html(),
				'name':$(tr_obj).find('td:eq(1)').html(), 
				'customer_count_str':$('#customer_type option:selected').html(), 
				'customer_count':$(tr_obj).find('td:eq(2)').html(), 
				'weight':$(tr_obj).find('td:eq(3)').html()
			}));
			$(tr_obj).remove();
			refresh_dirstribute_sum();
		});
		
		$('#id_do_distribute').click(function(){
			//var max_count = parseInt($('#id_consult_now_load').text());
			var max_count = 0;
            switch ($('#customer_type').val()) {
                case '0':
                    max_count = parseInt($('#id_consult_now_load').html());
                    break;
                case '1':
                    max_count = parseInt($('#id_consult_inservice').html());
                    break;
                case '2':
                    max_count = parseInt($('#id_consult_expired').html());
                    break;
                case '3':
                    max_count = parseInt($('#id_consult_now_load').html())-parseInt($('#id_consult_reserved').html());
                    break;
                case '4':
                    max_count = parseInt($('#id_consult_to_distribute').html());
                    break;
            }
			var submit_list = new Array();
			var total_count = 0;
			var tr_obj_list = $('#id_dirstribute_table>tbody>tr');
			for(var i=0;i<tr_obj_list.length;i++){
				var temp_count =parseInt($(tr_obj_list[i]).find('input').val()); 
				if(temp_count>0){
					submit_list.push({
						'consult_id':parseInt($(tr_obj_list[i]).attr('id')),
						'dis_count':temp_count
					});
					total_count +=temp_count;
				}
				if(total_count>max_count){
					PT.alert("要分配"+total_count+"个客户，但最多只有"+max_count+"个客户，请重新调整！");
					return false;
				}
			}
			if(total_count<=0){
				PT.alert('没有分配给任何人！');
				return false;
			}else{
				PT.confirm("确定要分配出去"+total_count+"个客户吗？",
					function () {
						PT.show_loading('正在分发客户');
						PT.sendDajax({
							'function':'ncrm_distribute_customer',
							'dis_list':$.toJSON(submit_list),
							'consult_id':$('#id_consult_id').val(),
							'customer_type':$('#customer_type').val()
						})
					},
					[]
				)
			}
		});
	};
	
    return {
        init:init_dom,
        update_consult_weight_callback:function (result) {
	        switch (result) {
		        case 1:
			        PT.alert('修改成功！');
			        $('#id_consult_table input.consult_weight.editable').each(function () {
				        var value = Number(this.value) || 0;
				        $(this).attr('org_value', value);
				        $(this).val(value);
			        });
			        $('#id_modify_weight').attr('disabled', true);
			        break;
                case 2:
                    PT.alert('权限不够，请联系市场部主管帮忙修改！');
                    break;
                default:
                    PT.alert('修改失败，请联系管理员！');
	        }
        }
//        distribute_customer_callback:function(consult_dict){
//        	for(var consult_id in consult_dict){
//        		var temp_obj =$('#'+consult_id+'>td:eq(3)'); 
//        		$(temp_obj).text(parseInt(consult_dict[consult_id]) + parseInt($(temp_obj).text()));
//        	}
//        	$('#id_distribute_layout').modal('hide');
//        	PT.alert("分发成功！");
//        }
    };
}();
