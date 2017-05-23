"use strict";
PT.namespace('Adgroup_optimize');
PT.Adgroup_optimize = function () {
	
	var adgroup_id=$('#adgroup_id').val();
	var campaign_id=$('#campaign_id').val();
	var item_id=$('#item_id').val();
	var default_price=$('#default_price_hide').val();
	var help=new Tour({backdrop:true});
	
	var get_last_day=function (){
		return $('#dashboard-report-range').find('input[name="last_day"]').val();
	}
	
	var init_dom=function (){
		
		$('.help').click(function(){
			help.restart();
		});
		
		$('#smart_optimize input').change(function(){
			$('#id_rate').val(0).addClass('red_border');
		});
		
		$('#id_rate').change(function(){
			if ($(this).val()!=0){
				PT.show_loading('正在改变优化策略');
				$(this).removeClass('red_border');
				PT.instance_table.get_keyword_data();
			}
		});
        
        $(document).off('click.PT.submit_bword','#id_submit_bword').on('click.PT.submit_bword','#id_submit_bword', function(){
            var word_list = new Array();
            var manual_blackword = $.trim($('#manual_blackword').val());
            $('#id_ban_word_part input:checked').each(function () {
                word_list.push($.trim(this.value));
            });
            if (manual_blackword && $.inArray(manual_blackword, word_list)==-1) {
                word_list.push(manual_blackword);
            }
            if(word_list.length>0){
                PT.sendDajax({'function':'web_submit_bwords', 
                                         'item_id':$('#item_id').val(),
                                         'blackwords':word_list.join(), 
                                         'save_or_update':1,
                                         'common_table_flag':$('#common_table').length
                                         });
                $.fancybox.close();
            } else {
                PT.alert("亲，未选中或输入任何词！");
            }
        });
        
	}
 
	
	var init_table=function(){
		//PT.show_loading('正在获取关键词数据');
		PT.instance_table=new PT.Adgroup_optimize.table_obj('common_table','template_common_table_tr');
	}

//	var get_uploadrecord_count=function(){
//		PT.sendDajax({'function':'web_get_uploadrecord_by_id',
//		                         'adgroup_id':adgroup_id,
//		                         'data':'count_only',
//		                         'call_back':'PT.Adgroup_optimize.creative_count',
//		                         'auto_hide':0
//		                         });	
//	}

	
	var init_help=function(){

		var help_list=[
			{
				element:'#adgroup_nav',
				content:'1/5 这里可以查看推广宝贝详细信息',
				placement:'bottom'	
			},
			{
				element:'.serach_box>div:eq(0)',
				content:'2/5 选择智能优化的条件',
				placement:'bottom'	
			},
			{
				element:'.serach_box>div:eq(1)',
				content:'3/5 显示关键词更改状态后的个数',
				placement:'bottom'	
			},
			{
				element:'#select_column_show_btn',
				content:'4/5 查看更多维度的数据',
				placement:'left'	
			},
			{
				element:'#common_table th:first',
				content:'5/5 下面的选择框可以按shift或者鼠标右键选择其中的一部分进行预估排名等操作',
				placement:'right'		
			}		
		];
		PT.help(help_list);
	}	
	
    return {
        //main function to initiate the module
        init: function () {
			$('ul.main.nav li').eq(0).addClass('active');
		   init_dom();
		   init_table();
//		   get_uploadrecord_count();
        },
		select_call_back: function(value){
			//改变天数的回调函数
			PT.instance_table.loading_table();
			PT.instance_table.data_table.fnDestroy();
			PT.instance_table.get_keyword_data();
		},
		table_callback: function(data){
			PT.instance_table.call_back(data);
		},
		creative_count:function(data){
			$('#history_kw_count').text(data.count);
		},
		get_last_day:function(){
			return get_last_day;	
		},
		adgroup_id:adgroup_id
		,
		item_id:item_id
		,
		campaign_id:campaign_id
		,
		default_price:default_price
		,
		help:init_help
		,
    };

}();











//继承PT.Table.BaseTableObj的属性
PT.Adgroup_optimize.table_obj=function(table_id,temp_id){
	PT.Table.BaseTableObj.call(this,table_id,temp_id);	
}
//继承PT.Table.BaseTableObj的属性方法
PT.Adgroup_optimize.table_obj.prototype=PT.Table.BaseTableObj.prototype;

//填充表格数据
PT.Adgroup_optimize.table_obj.prototype.layout_keyword=function(json){
	PT.console('begin layout keyword');
	var tr_str='',kw_count=json.keyword.length,d;
	tr_str=template.render('template_nosearch',json.nosraech);
	
	for (var i=0;i<kw_count;i++){
		tr_str+=template.render(this.temp_id,json.keyword[i]);
	}


//	this.table_obj.find('tbody tr').remove();
//	this.table_obj.find('tbody').append(tr_str);

	$('tbody',this.table_obj).html(tr_str);
}

//重写后台回调函数
PT.Adgroup_optimize.table_obj.prototype.call_back=function(json){
	
	var that=this;
 
	if(!$.fn.dataTable.fnIsDataTable(this.table_obj[0])){
		if(json.keyword.length){
			this.recount_table_width(json.custom_column);
			this.layout_keyword(json);
			this.sort_table(json.custom_column);
		}else{
			$('#loading_keyword').hide();
			$('#no_keyword').show();
			PT.Adgroup_optimize.help();
			return;
		}
	}
	this.change_price_status_4data(json);

	this.calc_action_count();
	this.update_all_style();
	PT.Adgroup_optimize.help();

	$('#loading_keyword').hide();
}

//获取关键词列表
PT.Adgroup_optimize.table_obj.prototype.get_keyword_data=function(){		
	PT.sendDajax({'function':'web_adgroup_optimize','adgroup_id':PT.Adgroup_optimize.adgroup_id,'last_day':PT.Adgroup_optimize.get_last_day(),'stgy_list':this.get_smart_optimize_argv(),'auto_hide':0});
}

PT.Adgroup_optimize.table_obj.prototype.change_price_status_4data=function(data){
	var result=data.keyword;
	for (var i in result){
		var kw_id=result[i]['keyword_id'],obj=this.row_cache[kw_id];
		obj.new_price_input.val(result[i]['new_price']);
		obj.nRow.attr('label_code',result[i]['label_code'])
		obj.nRow.find('.optm_type').text(result[i]['optm_type']);
		if(result[i]['optm_type']=='1'){
			obj.kw_del=1;	
		}
		if(result[i]['optm_reason']){
			obj.nRow.find('.icon-info-sign').attr('data-original-title',result[i]['optm_reason']).removeClass('hide');
		}else{
			obj.nRow.find('.icon-info-sign').addClass('hide');
		}
		
		//obj.is_del();
	}
	this.calc_action_count();
	PT.hide_loading();
}