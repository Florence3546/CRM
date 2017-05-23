PT.namespace('Duplicate_check');
PT.Duplicate_check = function () {
	var help=new Tour({backdrop:true});
	var DUPLICATE_CHECK_SIZE=20;//页面显示重复词列表一页的数量
	var DUPLICATE_CHECK_LEAVE_LOCK=3; //锁定删词级别小于设定的数值的词
	var NOW_TR=null;//当前正在点击的行
	var garbage_words_len=0
	var init_dupl_list=function (){
		PT.dupl_list_table=$('#dupl_kw_list').dataTable({
			"bServerSide": true,//开启服务器获取资源
			"bPaginate": true,
			"bFilter": false,
			"bInfo": true,
			"bAutoWidth":false,//禁止自动计算宽度
			"aaSorting": [[1, 'desc']],
			"aoColumns": [
				{"bSortable": false},
				{"bSortable": true}
			],
			"fnServerData": send_date,//指定函数发起请求
			"iDisplayLength": DUPLICATE_CHECK_SIZE,
			"sDom":"<'row-fluid't<'row-fluid marb_24'<'span6'i><'span6'p>>",
			"oLanguage": {
				"sZeroRecords": "没有记录",
				"sEmptyTable":"没有数据",
				"sInfoEmpty": "显示0条记录",
				"sInfo": "正在显示第_START_-_END_条信息，共_TOTAL_条信息",
				"oPaginate": {
					"sPrevious": " 上一页 ",
					"sNext":     " 下一页 "
					}
			}					
		});
		
	}
	
	var init_dupl_detail=function (){

		$(NOW_TR).next().find('.dupl_table').dataTable({
			"bServerSide": false,
			"bPaginate": false,
			"bFilter": false,
			"bInfo": false,
			"bAutoWidth":false,//禁止自动计算宽度
			//"iDisplayLength":20,
			"aoColumns": [
				{"bSortable": false},
				{"bSortable": true,"sSortDataType": "dom-text", "sType": "numeric"},
				{"bSortable": false},
				{"bSortable": false},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true},
				{"bSortable": true}
			],
			"fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
				//设置删词级别小于设定值时，锁定关键词
				if ($(NOW_TR).data('is_lock')===1) {
					var leave=$(nRow).find('td:eq(1) span:first').text();
					if (parseInt(leave)<=DUPLICATE_CHECK_LEAVE_LOCK){
						$(nRow).find('td:first input').attr('disabled','disabled');
						$(nRow).find('td:eq(1) i').removeClass('icon-unlock').addClass('icon-lock');
					}
				}
			},
			"sDom": "t",
			"oLanguage": {
				"sProcessing" : "正在获取数据，请稍候...",
				"sInfo":"正在显示第_START_-_END_条信息，共_TOTAL_条信息 ",
				"sZeroRecords" : "没有数据", 
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

	
	//发送请求获取数据	
	var send_date=function (sSource, aoData, fnCallback, oSettings){
		var page_info=get_userful_json(aoData);
		//第一次进入后会执行本函数，这里将必要的参数存入全局变量
		PT.Duplicate_check.callBack=fnCallback;
		PT.show_loading('正在获取数据');
		PT.sendDajax({
			'function':'web_dupl_kw_list'
			,'page_info':page_info
		}); 
	}
	
	//将datatable产生的分页数据格式化为字符串,以便后台接收	
	var get_userful_json=function (aoData){
		var json={};
		for (var i=0;i<aoData.length;i++){
			json[aoData[i].name]=aoData[i].value;
		}
		return $.toJSON(json);
	}	
	
	//智能删除
	var smart_del=function (){
		PT.show_loading('正在删除重复词');
		PT.sendDajax({
			'function':'web_delete_dupl_word',
			'del_type':'smart'	
		});
	}
	
	var condition_del=function(kw_arr){
		PT.show_loading('正在删除重复词');
		PT.sendDajax({
			'function':'web_delete_dupl_word',
			'condition':get_delete_condition(true),
			'del_type': kw_arr? 'manual':'advanced',
			'word_list':kw_arr? kw_arr:[]
		});
	}
	
	//将模板转化为dom对象	
	var get_dom_4template=function (id,json){
		var tr_arr=[];
		for (d in json){
			if(!isNaN(d)){
				tr_arr.push($(template.render(id,json[d])));
			}
		}		
		return tr_arr;
	}
	
	//将模板返回的html按td将其分割,以便datatable填充数据	
	var get_array=function(data){
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
	
	//获取删除条件
	var get_delete_condition=function (str){
		var condition={};	
		condition.del_level=parseInt($('#del_level').val());
		condition.del_day=parseInt($('#del_day').val());
		condition.del_statistics_type=$('#del_statistics_type').val();
		$('#del_offline')[0].checked?condition.del_offline=1:condition.del_offline=0;
		if(str){
			return $.toJSON(condition);
		}else{
			return condition;
		}
	}
	
	var get_kw_arr=function (){
		var kw_arr=[];
		$('#dupl_kw_list tbody input:checked').each(function(){
			kw_arr.push($(this).parent().next().find('.keyword').text());
		});	
		return kw_arr;
	}
	
	//获取关键词详细列表
	var get_keyword_deatil=function (keyword){
		//PT.show_loading('正在查询:"'+keyword+'"的详细信息');
		PT.sendDajax({
			'function':'web_dupl_kw_detail'
			,'keyword':keyword
		}); 			
	}
	
	var init_dom=function (){
		
		//重新检查按钮事件
		$('#id_recheck').click(function(){
			PT.confirm('排查重复词可能较慢，确认现在就重新排查吗？',function(){PT.dupl_list_table.fnDraw();});
		});
		
		//切换tab页时的动画效果
		$('#smart_btn').click(function(){
			$('#dupl_box').fadeOut(300);
			$('#condition').slideUp('fast',function(){
				$('#condition_detail').hide();
				$('#smart_explain').show();
				$('#condition').slideDown('fast');
			});
		});
		$('#advanced_btn').click(function(){
			$('#dupl_box').fadeOut(300);
			$('#condition').slideUp('fast',function(){
				$('#obj_descr').text('针对全店所有关键词：');
				$('#smart_explain').hide();
				$('#condition_detail').show();
				$('#condition').slideDown('fast');
			});	
		});
		$('#manual_btn').click(function(){		
			$('#dupl_box').fadeIn(300);
			$('#condition').slideUp('fast',function(){
				$('#obj_descr').text('针对以下选中项：');
				$('#smart_explain').hide();
				$('#condition_detail').show();
				$('#condition').slideDown('fast');
			});
		});			
		
		//公共提交按钮
		$('#comm_submit_btn').click(function(){
			var del_type=$('.nav.nav-tabs li.active').index();
			switch(del_type){
				case 0:
					var kw_arr=get_kw_arr();
					if(kw_arr.length){
						PT.confirm('您确认按条件批量删除包含以下'+kw_arr.length+'个关键词的重复词吗？', condition_del, [kw_arr]);	
					}else{
						PT.alert('请选中下方要删除的关键词');	
					}
					break;
				case 1:
					PT.confirm('您确认按条件批量删除店铺中的重复词吗？', condition_del);
					break;
				case 2:
					PT.confirm('您确认批量删除店铺中无展现词吗？',smart_del)	
					break;
			}
		});
		
		//手动删除详细表中的词
		$(document).on('click','#single_submit_btn',function(){
			var kw_id_arr=[];	
			$(this).parents('tr').next().find('tbody input:checked').each(function(){
				kw_id_arr.push(parseInt($(this).val()));
			});
			if (kw_id_arr.length){
				NOW_TR=$(this).parents('tr');
				PT.show_loading('正在删除重复词');
				PT.sendDajax({'function':'web_delete_dupl_word','kw_id_list':kw_id_arr,'del_type':'manual'});	
			}else{
				PT.alert('请选中下方要删除的关键词');	
			}
		});
		
		$('.help').click(function(){
			help.restart();
		});
	}
	
	var init_help=function(){
		if(!$.browser.webkit&&$.browser.msie&&Number($.browser.version)<7){
			return;
		}
		help.addSteps([
			{
				element:'.keyword:eq(0)',
				content:'1/5 这里可以查看每个关键词的详情',
				placement:'top',
				onShow:function(tour){
					$('.keyword:eq(0)').click();
				}					
			},
			{
				element:'#DataTables_Table_0_wrapper tr:eq(-1) td:eq(0)',
				content:'2/5 选择要删除的重复关键词',
				placement:'right'	
			},
			{
				element: "#single_submit_btn",
				content: "3/5  删除当前重复词下被选中的关键词",
				placement:'bottom'
			},
			{
				element: "#advanced_btn",
				content: "4/5 这里可以批量删除指定条件的重复词",
				placement:'top'
			},
			{
				element: "#smart_btn",
				content: "5/5 删除所有淘宝判定的垃圾词（15天无展现）",
				placement:'top'
			}
		]);			
	}
		
	var init_ajax_dom_first=function(){
		
		// 复选框事件
		$('.father_box').click(function(){
			var area_id=$(this).attr('link');
			var that=this;
			if(area_id!=undefined){
				var kid_box=$('#'+area_id).find('input[class*="kid_box"]');
				kid_box.each(function(){
					!(this.disabled)?this.checked=that.checked:'';
				});
			}
		});	
			
		//绑定行点击展开事件
		$('#dupl_kw_list tbody td .pointer').on('click', function () {
            NOW_TR = $(this).parents('tr')[0];
			$(this).find('.row-details').toggleClass("row-details-close").toggleClass("row-details-open");
            $(this).next().toggleClass('hide');
            if ( PT.dupl_list_table.fnIsOpen(NOW_TR) )
            {
				var detail_str=$(NOW_TR).next().find('.dataTables_wrapper').html();
				$(NOW_TR).data('detail_str',detail_str);
                PT.dupl_list_table.fnClose( NOW_TR );
            } else {         
				var detail_str=$(NOW_TR).data('detail_str');
				if (detail_str) {
					PT.dupl_list_table.fnOpen( NOW_TR, detail_str , 'info_row' );
					$(NOW_TR).data('is_lock',0);
					init_dupl_detail();
					init_ajax_dom_second();
					App.initTooltips();
				} else {
					var keyword=$(this).find('.keyword').text();
					PT.show_loading('正在查询:"'+keyword+'"的详细信息');
                	get_keyword_deatil(keyword);
				}
            }
        });	
	}
	
	//切换锁定状态
	var init_ajax_dom_second=function(){
		
		$('.dupl_table').on('click','i[class*="icon-lock"]',function(){
			$(this).removeClass('icon-lock').addClass('icon-unlock').parent().prev().find('input').attr({'disabled':false,'checked':true});
		});	
		
		$('.dupl_table').on('click','i[class*="icon-unlock"]',function(){
			$(this).removeClass('icon-unlock').addClass('icon-lock').parent().prev().find('input').attr({'disabled':true,'checked':false});
		});	
		
		// 复选框事件
		$('.top_box').click(function(){
			var jq_table=$(this).parents('table').eq(0);
			var that=this;
			if(jq_table!=undefined){
				var sub_box=jq_table.find('input[class*="sub_box"]');
				sub_box.each(function(){
					!(this.disabled)?this.checked=that.checked:'';
				});
			}
		});	
			
	}
	
    return {

        //main function to initiate the module
        init: function (){
			PT.Base.set_nav_activ(4,0);
			init_dom();
			init_dupl_list();
			template.isEscape=false;
			//init_help();
        },
		dupl_list: function (page_info_server,data,garbage_words_len){
			var template_data,datatable_arr;
			PT.hide_loading();
			garbage_words_len=garbage_words_len
			$('#garbage_count').text(garbage_words_len);
			template_data=get_dom_4template('dupl_list_tr',data);
			datatable_arr=get_array(template_data);	
			
			PT.dupl_list_table.fnClearTable(false);
			
			$('.dupl_word_count').html(page_info_server['iTotalRecords']);
			
			page_info_server['aaData']=datatable_arr;//构造dataTable能够识别的数据格式
			PT.Duplicate_check.callBack(page_info_server);//填充数据
			//init_detail_table(); //获取第一个关键词的详细列表
			init_ajax_dom_first();
		},
		dupl_detail: function(data){
			PT.hide_loading();
			//填充数据
			var tr_str='';
			for (var i=0;i<data.length;i++){
				tr_str += template.render('dupl_detail_tr', data[i]);
			}
			var dupl_detail_str= template.render('dupl_detail_template', {'tr_str':tr_str});
			PT.dupl_list_table.fnOpen( NOW_TR, dupl_detail_str , 'info_row' );
			$(NOW_TR).data('is_lock',1);
			init_dupl_detail();
			App.initTooltips();
			init_ajax_dom_second();
		},
		delete_result: function (del_type, del_count, failed_count, del_kw_list, is_refresh) {
			PT.hide_loading();
			if (del_type=='manual') {
				var jq_count=$(NOW_TR).find('.dupl_count'),
					now_count=jq_count.text()-del_count;
				if (now_count>1) {
					jq_count.text(now_count);
					for (var i=0; i<del_kw_list.length; i++) {
						var js_input=$('input[value='+del_kw_list[i]+']');
						js_input.parents('table:first').dataTable().fnDeleteRow(js_input.parents('tr:first')[0]);
					}
				} else {
					$(NOW_TR).next().remove();
					$(NOW_TR).remove();
					var dupl_count=Number($('.dupl_word_count:first').text());
					$('.dupl_word_count').html(dupl_count-1);
				}
			}
			if(del_count==0){
				PT.alert('亲，您的店铺中不存在符合条件的重复词');
			} else if(failed_count>0 | is_refresh | del_type!='manual') {
				PT.alert('删除成功'+del_count+'个，删除失败'+failed_count+'个，请点击“重新检查”按钮以刷新数据');
			}
		}
    };
}();