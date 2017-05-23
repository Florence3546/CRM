PT.namespace('CrmSelectWords');
PT.CrmSelectWords = function () {
    var init_table = function(){
    	$('#select_words_list').dataTable({
    		'bLengthChange':true,
    		'bFilter': true,
    		'bSort':true,
    		'iDisplayLength':200,
    		"aLengthMenu": [
                [15, 30,50,100, 200,-1],
                [15, 30,50,100,200,"All"] 
            ],
            "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>",
            "sPaginationType": "bootstrap",
            "oLanguage": {
                "sZeroRecords": "没有关键词记录"
				,"sLengthMenu": "每页显示 _MENU_ 条记录"
				,"sInfo": "显示第_START_条到第_END_条记录, 共_TOTAL_条记录"
				,"sInfoFiltered" : "(全部记录数 _MAX_ 条)"
				,"sInfoEmpty": "显示0条记录"
				,"oPaginate": {
					"sPrevious": " 上一页 "
					,"sNext":     " 下一页 "
				}		
            },
    		'aaSorting':[]
    	});
    }
    
    var init_dom = function(){
		PT.show_loading('正在选词');
		var shop_id = $("#shop_id").val();
		var item_id = $("#item_id").val();
		var adg_id = $("#adg_id").val();
		var conf_name = $("#conf_name").val();
		var conf_desc = $("#conf_desc").val();
		var candidate_words = $("#candidate_words").val();
		var label_define = $("#label_define").val();
		var select_conf_list = $("#select_conf_list").val();
		var price_conf_list = $("#price_conf_list").val();
		var delete_conf = $("#delete_conf").val();
		
		PT.sendDajax({
				'function':'crm_test_select_words',
				'shop_id':shop_id,
				'item_id':item_id,
				'adg_id':adg_id,
				'conf_name':conf_name,
				'conf_desc':conf_desc,
				'candidate_words':candidate_words,
				'label_define':label_define,
				'select_conf_list':select_conf_list,
				'price_conf_list':price_conf_list,
				'delete_conf':delete_conf,
		});    	
    };

    return {
        init: init_dom,
        set_kw_list:function(kw_list){
        	var tbody_html = '';
        	var num = 1;
        	for (var i = 0 ; i < kw_list.length ; i ++){
        		tbody_html += template.render("kw_record_tr",{'record':kw_list[i],'num':num++});
        	}
        	$('#kw_list').html(tbody_html);
        	init_table();
        	PT.hide_loading();
        	$("#select_words_list").show();
        }
    };
}();
