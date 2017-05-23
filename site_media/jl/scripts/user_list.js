PT.namespace('UserList');

PT.UserList = function(){
    var init = function(){
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
	}
	
	return {
		init:function(){
			init();
		}
	}
	
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
