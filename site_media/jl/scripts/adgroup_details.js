PT.namespace('AdgroupDetails');
PT.AdgroupDetails = function () {
	var adg_id=$('#adgroup_id').val();
	
	//第一次进入时，发送请求第一天的数据
	var send_date=function(){
		PT.show_loading('正在获取数据');
		PT.sendDajax({'function':'web_get_adgroup_sumrpt','last_day':1,'adg_id':adg_id});
	}
	
	var init_detailed_table=function(){
		var detailed_table=$('#detailed_table').dataTable({
			"bPaginate": false,
			"bFilter": false,
			"bInfo": false,
			"aaSorting":[[0,'desc']],
			"oLanguage": {
				"sZeroRecords": "亲，没有最近15天的宝贝数据！",
				"sInfoEmpty": "亲，没有最近15天的宝贝数据！"
				},	
			"aoColumns":[null, null, null, null, null, null, 
			                        {"sSortDataType":"td-text", "sType":"numeric"},
                                    {"sSortDataType":"td-text", "sType":"numeric"},
                                    {"sSortDataType":"td-text", "sType":"numeric"},
			                        null, null]
		});
	}
	
	var init_dom=function() {
		
	}
	
    return {

        init: function () {
			//PT.initDashboardDaterange();
			send_date();
			init_dom();
			init_detailed_table();
        },
		select_call_back: function(value){
			PT.sendDajax({'function':'web_get_adgroup_sumrpt','last_day':value,'adg_id':adg_id});
		},
		append_adg_data: function(data){
			PT.hide_loading();
			$('#adg_p').html(template.render('adg_c',data));
			App.initTooltips();
		},

    };

}();