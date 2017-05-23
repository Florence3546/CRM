PT.namespace('OrderManage');
PT.OrderManage = function() {


	var change_model = function(order_id, pos){
		var type_list = ['operater', 'psuser'];
		var temp_obj;
		if(pos==1){
    		$('#'+order_id).find('.save').removeClass('hide');
    		$('#'+order_id).find('.edit').addClass('hide');
    		for(var i=0;i<type_list.length;i++){
    			temp_obj = $('#id_'+order_id+'_'+type_list[i]+'_id');
    			$(temp_obj).val($(temp_obj).attr('org_value'));
    			$(temp_obj).siblings('span').addClass('hide');
    			$(temp_obj).siblings('input').val($(temp_obj).siblings('span').text());
    			$(temp_obj).siblings('input').removeClass('hide');
    		}
		}
		else{
			$('#'+order_id).find('.save').addClass('hide');
			$('#'+order_id).find('.edit').removeClass('hide');
    		// var type_list = ['operater', 'psuser'];
    		for(var i=0;i<type_list.length;i++){
    			temp_obj = $('#id_'+order_id+'_'+type_list[i]+'_id');
    			$(temp_obj).attr('org_value', $(temp_obj).val());
    			$(temp_obj).siblings('span').removeClass('hide');
    			$(temp_obj).siblings('span').text($(temp_obj).siblings('input').val());
    			$(temp_obj).siblings('input').addClass('hide');
    		}
		}
	}


    var init_dom = function() {


    	require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#id_start_date',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '#id_end_date',
                timepicker: false,
                closeOnDateSelect : true
            });

        });

    	$("#search_order").click(function(){
    	   PT.show_loading("正在查询订单");
    	   $('#form_search_order').submit();
    	});

    	$('.edit').click(function(){
    		var order_id = $(this).parent().parent().attr('id');
    		change_model(order_id, 1);
    	});

    	/*
    	$('.allocate').click(function(){
    		$('#id_hide_order_id').val($(this).parent().parent().attr('id'));
    		var psuser_type = $(this).attr('type');
    		user_type = psuser_type=='saler'?'销售':'操作';
    		$('#id_type_display').text(user_type);
    		$('#id_hide_psuser_type').val(psuser_type);
    		var psuser_id = $(this).find('span').attr('psuser_id');
    		$('#id_hide_psuser_id').val(psuser_id);
    		PT.sendDajax({'function':'ncrm_get_psuser_list', 'namespace':'OrderManage.display_allocator'});
    	});*/

    	$('#id_submit_allocate').click(function(){
    		var order_id = $('#id_hide_order_id').val();
    		var psuser_id = $('#id_select_psuser').val();
    		var psuser_type = $('#id_hide_psuser_type').val();
    		if(psuser_id!=null && psuser_id!=undefined && psuser_id!=''){
    			PT.sendDajax({'function':'ncrm_submit_order_allocate', 'order_id':order_id, 'psuser_id':psuser_id, 'psuser_type':psuser_type, 'namespace':'OrderManage.submit_order_allocate_callback'})
    		}else{
    			return false;
    		}
    	});


    	$('.delete_subscribe').click(function(){
	    	var subscribe_id = parseInt($(this).attr('subscribe_id'));
    		PT.confirm(
	    		"确定要删除吗？只有负责人和签单人才能删除哦！",
	    		function () {
			    	PT.show_loading('正在删除订单');
		    		PT.sendDajax({
			    		'function':'ncrm_delete_subscribe',
			    		'subscribe_id':subscribe_id,
		                'call_back':"OrderManage.delete_subscribe_callback"
	                });
	            },
	            []
    		);
    	})

    	$('#table_subscribe .end_subscribe').click(function () {
            $('#modal_end_subscribe .frozen_kcjl, #modal_end_subscribe .unmnt_all').attr('checked', false);
            $('#modal_end_subscribe').attr('sub_id', $(this).attr('subscribe_id')).modal('show');
		})

    	$('#modal_end_subscribe .end_subscribe').click(function () {
	    	PT.show_loading('正在终止订单');
    		PT.sendDajax({
	    		'function':'ncrm_end_subscribe',
	    		'subscribe_id':parseInt($('#modal_end_subscribe').attr('sub_id')),
                'frozen_kcjl': $('#modal_end_subscribe .frozen_kcjl').prop('checked')?1:0,
                'unmnt_all': $('#modal_end_subscribe .unmnt_all').prop('checked')?1:0,
	    		'namespace':"OrderManage.end_subscribe_callback"
    		});
    	})

		// 下载文件
		$("#download_subscribe").click(function () {
			if(!PT.DBCLICK_ENABLED) {
                //禁止重复点击
                return false;
            }
            $.ajax({
                url: '/ncrm/get/',
                type: 'POST',
                cache: false,
                data: {

				},
                success: function(data) {
                     PT.hide_loading();
                     if(data.status==1){
                         $("#id_chat_file_path").val(data.file_path);
                         PT.alert(data.msg);
                     }else{
                          PT.alert(data.msg);
                     }
                },
                error: function() {
                    PT.hide_loading();
                    PT.alert('上传聊天文件失败');
                    $("#up_chat_file").val('');
                    $("#id_chat_file_path").val('');
                    return false;
                }
            });
        });

    }

    return {
        init: function() {
            init_dom();
        },

        display_allocator:function(user_list){
        	var html_str = template.render('id_user_selector_template', {'user_list':user_list});
        	$('#id_select_psuser').html(html_str);
        	$('#id_select_psuser').val($('#id_hide_psuser_id').val());
        	$('#id_allocate_order_layout').modal();
        },
        submit_order_allocate_callback:function(order_id, psuser_id, psuser_type){
        	var tr_obj = $('#'+ order_id);
        	var name_cn = $('#id_select_psuser>option[value='+psuser_id+']').text();
        	var real_name = name_cn.split('：')[1];
			$(tr_obj).find('.'+psuser_type).attr('psuser_id', psuser_id);
			$(tr_obj).find('.'+psuser_type).text(real_name);
			$('#id_allocate_order_layout').modal('hide');
        },
        end_subscribe_callback:function(subscribe_id, end_date, msg){
        	console.log(subscribe_id, end_date, msg);
        	var tr_obj = $('#'+subscribe_id);
        	$(tr_obj).find('td:eq(5)').text(end_date);
        	$(tr_obj).find('td:eq(-2)').text(msg);
			$('#modal_end_subscribe').modal('hide');
        },
        delete_subscribe_callback:function(subscribe_id){
        	$('#'+subscribe_id).remove();
        	PT.light_msg('', '删除成功');
        },
        change_psuser_callback:function(order_id){
        	change_model(order_id, -1);
        }
    }
}();
