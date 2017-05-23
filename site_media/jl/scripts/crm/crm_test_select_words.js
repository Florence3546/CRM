PT.namespace('CrmSelectWords');
PT.CrmSelectWords = function () {
    var init_table = function(){
    	$('#select_words_list').dataTable({
    		'bLengthChange':false,
    		'iDisplayLength':200,
    		'bFilter': false,
    		'bSort':true,
    		'aaSorting':[]
    	});
    }
    
    var init_dom = function(){
		PT.show_loading('正在选词');
		PT.sendDajax({
				'function':'crm_get_test_select_words',
				'conf_name':$('#conf_name').val(),
				'shop_id':$('#shop_id').val(),
				'adgroup_id':$('#adgroup_id').val()
		});    	
    };

    return {
        init: init_dom,
        set_kw_list:function(kw_list){
        	var tbody_html = '';
        	var num = 0;
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
