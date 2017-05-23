PT.namespace('All_history');
PT.All_history = function () {
	var history_table=null,
		adg_id=$('#adg_history_table').attr('value');

	var init_table=function(){
		history_table=$('#all_history_table').dataTable({
			// "bRetrieve": true, //允许重新初始化表格
			"iDisplayLength": 100,
            "bPaginate" : true,
            "bDeferRender": true,
            "bAutoWidth":false,
            "bFilter": true,
            "bSort":false,
            "bServerSide": true,//开启服务器获取资源
            "fnServerData": send_data,//获取数据的处理函数
            "sPaginationType": "bootstrap",
            'sDom': "T<'row-fluid't<'row-fluid mt10'<'span12 pl10'i><'span12 pr10 tr'p>>",
            "oLanguage": {
                "sProcessing" : "正在获取数据，请稍候...",
                "sInfo":"正在显示第_START_-_END_条信息，共_TOTAL_条信息 ",
                "sZeroRecords" : "30天内没有您要搜索的内容",
                "sEmptyTable":"没有数据",
                "sInfoEmpty": "显示0条记录",
                "sInfoFiltered" : "(全部记录数 _MAX_ 条)",
                "oPaginate": {
                    "sFirst" : "第一页",
                    "sPrevious": "上一页",
                    "sNext": "下一页",
                    "sLast" : "最后一页"
                }
            }
		});
	}

	var init_dom = function () {
	
		$('#drp_opter>a').dropdown();
		$('#drp_opter_text').html('全部操作人');
     	$('#drp_camp>a').dropdown();
		$('#drp_camp_text').html('全部计划');
		$('#drp_op_type>a').dropdown();
		$('#drp_op_type_text').html('全部数据类型');
		$('#drp_days>a').dropdown();
		$('#drp_days_text').html('过去1天');

        $('#drp_camp').change(function (e,v){
            camp_id = v;
            alert(v);
        });
		
		$('#btn_item_search').click(function(){
			search_history();
		});

		$('#txt_item').keyup(function(e){
			if (e.keyCode==13) {
				search_history();
			}
		});
	}

	var search_history = function() {
		var search_word=$('#txt_item').val();
		history_table.fnFilter(search_word);
	}

	//发送请求获取数据
	var send_data=function (sSource, aoData, fnCallback, oSettings){
		//发送请求获取数据
		//PT.show_loading('正在获取数据');
		page_info=get_userful_json(aoData);
		//第一次进入后会执行本函数，这里将必要的参数存入全局变量
		PT.All_history.page_info=page_info;
		PT.All_history.callBack=fnCallback;
		PT.sendDajax({
			'function':'web_get_all_history',
			'page_info':page_info
		});
	}

	var get_dom_4template=function (json){
		//将模板转化为dom对象
		var tr_arr=[];
		var index=1;
		for (d in json){
			json[d]['loop']=index;
			if(!isNaN(d)){
				tr_arr.push($(template.render('history_table_tr', json[d])));
			}
			index++;
		}
		return tr_arr;
	}

	var get_array=function(data){
		//将模板返回的html按td将其分割,以便datatable填充数据
		var array_data=[];
		for (var i=0;i<data.length;i++){
			var temp_tds=$(data[i]).find('td'),td_arr=[];
			for (var j=0;j<temp_tds.length;j++){
				td_arr.push(temp_tds[j].innerHTML);
			}
			array_data.push(td_arr);
		}
		return array_data;
	}

	//将datatable产生的分页数据格式化为字符串,以便后台接收
	var get_userful_json=function (aoData){
		var json={};
		for (var i=0; i<aoData.length; i++){
			json[aoData[i].name]=aoData[i].value;
		}
		return $.toJSON(json);
	}

    return {

        init: function (){
			init_table();
			init_dom();
        },
		append_table_data:function(page_info_server,data){
			PT.hide_loading();
			var table=$('#camp_history_table'),template_data,datatable_arr;
			template_data=get_dom_4template(data);
			datatable_arr=get_array(template_data);
			table.find('tbody tr').remove();
			page_info_server['aaData']=datatable_arr;//构造dataTable能够识别的数据格式
			PT.All_history.callBack(page_info_server);//填充数据
			table.show();
		}
    };
}();
