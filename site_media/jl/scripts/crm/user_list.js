PT.namespace('UserList');

PT.UserList = function(){
    var init = function(){
        PT.Base.set_nav_activ('user_list');
        var oTable = $('#user_table').dataTable({
            "aoColumnDefs":[{"bSortable": false, "aTargets": [7,8]}],
			"bPaginate": false,
			"bLengthChange": false,
			"bFilter": false,
			"bSort": true,
			"bInfo": false
    	});

		$("#id_shop_name").keyup(function(){
			search_shop_names();
		});

		//点击搜索查询，每次点击搜索自动去第一页
		$('#id_do_search').click(function(){
			search_shop_list();
		});

		//点击回车，执行查询
		$('#id_shop_id').keydown(function(event){
			enter(event);
		});
		$('#id_user_name').keydown(function(event){
			enter(event);
		});

		$('.edit_perms_code').click(function(){
		   var user_id = $(this).parents('tr').attr('id');
		   PT.sendDajax({'function':'crm_get_perms_code', 'user_id':user_id});
		});

		$('#id_submit_perms').on('click', function(){

		    function submit_perms(user_id, perms_code){
		        PT.sendDajax({'function':'crm_update_perms_code', 'uid':user_id, 'perms_code':perms_code});
		    }

		    var user_id = $(this).attr('user_id');
		    var perms_code = $('#id_perms_code').val();
		    var perms_code_bak = $('#id_perms_code_bak').val();
		    if(perms_code == perms_code_bak){
                $.fancybox.close();
                return false;
		    }else{
		        if(perms_code == '' || perms_code ==undefined || perms_code ==null){
		            PT.confirm("亲，输入的是空的额外权限码，确定要删除掉它吗？", submit_perms, [user_id, perms_code]);
		            $.fancybox.close();
		        }
		        else{
		            submit_perms(user_id, perms_code);
		            $.fancybox.close();
		        }
		    }
		});

		$('.exec_shopmngtask').click(function(){
            var shop_id = $(this).parents('tr').attr('shop_id');
            PT.show_loading('正在执行中');
            PT.sendDajax({'function':'crm_exec_shopmngtask', 'shop_id':shop_id});
		});

		$('.reset_shopmngtask').click(function(){
		   var shop_id = $(this).parents('tr').attr('shop_id');
		   PT.sendDajax({'function':'crm_reset_shopmngtask', 'shop_id':shop_id});
		});

		$('.modify_server').click(function(){
		   var nick = $(this).parents('tr').attr('nick');
		   PT.sendDajax({'function':'crm_get_server', 'nick':nick});
		});

		$('#id_submit_port').on('click', function(){
		   var nick = $('#id_nick').text();
		   var port_id = parseInt($('#id_port_select').val());
		   var port_id_bak = parseInt($('#id_port_id_bak').val());
		   if(port_id==port_id_bak){
		       $.fancybox.close();
		       return false;
		   } else{
		       if(port_id==0){
		           PT.alert("不能将已分配的用户修改为空！");
		           return false;
		       }else{
		           PT.sendDajax({'function':'crm_update_server', 'nick':nick, 'port_id':port_id});
		       }
		   }
		});

	}
	//托管计划状态
    var get_mnt_info = function (shop_id){
        PT.sendDajax({'function':'crm_get_mnt_info','shop_id':shop_id});
    };

    //执行托管任务
    var run_task = function (obj_id){
        PT.sendDajax({'function':'crm_run_mnt_task',"object_id":obj_id});
        $.fancybox.close();
        PT.show_loading('正在执行');
    };

    var update_max_num = function (camp_id){
        var max_num = $('#id_max_num_'+camp_id).val();
        if(max_num==''||isNaN(max_num)){
            alert('所填的不是数字！');
            return false;
        }else if(parseInt(max_num)<0||parseInt(max_num)>1000){
            alert("托管宝贝数量范围为0~1000！");
            return false;
        }else{
            if(max_num!=parseInt($('#max_num_bak_'+camp_id).val())){
                PT.sendDajax({'function':'crm_update_mnt_max_num',"camp_id":camp_id, "max_num":max_num});
                $.fancybox.close();
            }
        }
    };

    var stop_mnt_campaign = function (camp_id){
        PT.confirm("确认终止当前全自动计划吗？", submit_stop_camp, [camp_id]);
    };

    var submit_stop_camp =function(camp_id){
        $.fancybox.close();
        PT.sendDajax({'function':'crm_stop_mnt_campaign', 'campaign_id':camp_id});
    };

	return {
		init: init,
		get_mnt_info:get_mnt_info,
		run_task:run_task,
		update_max_num:update_max_num,
		stop_mnt_campaign:stop_mnt_campaign,
		display_mnt_info:function(data){
		    var temp_str = '';
            for(i=0;i<data.length;i++){
                temp_str += template.render('mnt_info_template', {'data':data[i]});
            }
            $('#id_mnt_task_layer').html(temp_str);
            $.fancybox.open([{href:'#id_mnt_task_layer'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});
		},
		display_perms_info: function(perms_code, user_id){
		    $('#id_perms_code').val(perms_code);
		    $('#id_perms_code_bak').val(perms_code);
		    $('#id_submit_perms').attr('user_id', user_id);
		    $.fancybox.open([{href:'#id_edit_perms_layer'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});
		},
	    update_perms_callback: function(status, perms_code, user_id){
	        if(status=='true'){
    	        $('#id_perms_code_'+user_id).text(perms_code);
	        }else{
	            PT.alert("修改失败！请联系系统管理员！");
	        }
	    },
	    display_port_info:function(nick, port_id, port_info){
	        var port_obj = $.evalJSON(port_info);
	        $('#id_nick').text(nick);
	        $('#id_port_id_bak').val(port_id);

	        $('#id_port_select').html('');//先清空
	        for(key in port_obj){
	            $('#id_port_select').append('<option value="'+key+'">'+port_obj[key]+'</option>');
	        }
	        $('#id_port_select').prepend('<option value="0">尚未分配</option>');

	        $('#id_port_select').val(port_id);
	        $.fancybox.open([{href:'#id_edit_port_layer'}], {helpers:{
                title : {type : 'outside'},
                overlay : {closeClick: false}
            }});
	    },
	    download_lastrpt:function(shop_id){
	    	PT.show_loading("正在修复");
	    	PT.sendDajax({"function":"crm_repair_lastrpt", "shop_id":shop_id});
	    },
	};

	//敲回车查询
	function enter(event){
		var e = event||window.event;
		var curr_key = e.keyCode||e.which||e.charCode;
		if(curr_key == 13){
			search_shop_list();
		}
	}
	//执行后台请求
	function search_shop_list(){
		var shop_id = $("#id_shop_id").val();
		if(shop_id != "" && isNaN(shop_id)){
			PT.alert("店铺ID只能为空或者是整数","red");
			$("#id_shop_id").focus();
			return false;
		}
		if($("#id_user_name").val()==$("#id_user_name").attr('placeholder')){//修复ie的bug
			$("#id_user_name").val('');
		}
		$("#id_page_no").val(1);
		var v_per_page = $("#id_per_page").val();
		PT.show_loading('正在查询');
		$("#id_page_size").val(v_per_page);
		$("#id_search_list_form").submit();
	}
	//根据店铺名搜索本页
	function search_shop_names(){
		var keyword = $('#id_shop_name').val();
		$(".shop_name").each(function(){
			if($(this).text().indexOf(keyword) != -1){
				$(this).parent().show();
			}else{
				$(this).parent().hide();
			}
		});
	}
}();
