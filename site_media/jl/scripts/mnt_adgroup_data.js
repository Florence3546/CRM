"use strict";
PT.namespace('Mnt_adgroup_data');
PT.Mnt_adgroup_data = function () {
	
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
		PT.instance_table=new PT.Mnt_adgroup_data.table_obj('common_table','template_common_table_tr');
	}
	
	var init_help=function(){
		if(!$.browser.webkit&&$.browser.msie&&Number($.browser.version)<7){
			return;
		}
		help.addSteps([
			{
				element: "#fixed_box .btn-group:first",
				content: "系统会根据您选择的优化策略等参数自动分析优化建议",
			},
			{
				element: "#batch_optimiz",
				content: "您可以快速选中一批词，进行批量加价,降价等操作。还能批量选中一批符合条件的词。",
			},
			{
				element:'#id_curwords_submit',
				content:'点击这里可以提交您已经优化好的关键词到直通车'
			},
			{
				element:'#dashboard-report-range',
				content:'点这里可以改变报表的统计天数'
			}
		]);			
	}	
	
    return {
        //main function to initiate the module
        init: function () {
           $('ul.main.nav>li').eq(0).addClass('active');
		   PT.initDashboardDaterange();
		   init_dom();
		   setTimeout(function(){init_table();},0);
		   //init_help();
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
		help:help
    };

}();


//继承PT.Table.BaseTableObj的属性
PT.Mnt_adgroup_data.table_obj=function(table_id,temp_id){
	PT.Table.BaseTableObj.call(this,table_id,temp_id);	
}
//继承PT.Table.BaseTableObj的属性方法
PT.Mnt_adgroup_data.table_obj.prototype=PT.Table.BaseTableObj.prototype;

//填充表格数据
PT.Mnt_adgroup_data.table_obj.prototype.layout_keyword=function(json){
	PT.console('begin layout keyword');
	var tr_str=[],kw_count=0,d;
	tr_str=template.render('template_nosearch',json.nosraech);
	
	for (d in json.keyword){
		if(!isNaN(d)){
			tr_str+=template.render(this.temp_id,json.keyword[d]);
			kw_count++;
		}
	}
//	this.table_obj.find('tbody tr').remove();
//	this.table_obj.find('tbody').append(tr_str);
	$('tbody',this.table_obj).html(tr_str);
}

//重写后台回调函数
PT.Mnt_adgroup_data.table_obj.prototype.call_back=function(json){
	if(!$.fn.dataTable.fnIsDataTable(this.table_obj[0])){
		this.layout_keyword(json);
		this.sort_table(json.custom_column);
		this.recount_table_width();
	}else{//表格已经存在，只改变价格和删词状态
		this.change_price_status_4data(json);
	}
	$('#loading_keyword').hide();
	//this.calc_action_count();
	this.update_all_style();
	PT.Mnt_adgroup_data.help.start();
}

//获取关键词列表
PT.Mnt_adgroup_data.table_obj.prototype.get_keyword_data=function(){		
	PT.sendDajax({'function':'mnt_get_adgroup_data','adgroup_id':PT.Mnt_adgroup_data.adgroup_id,'last_day':PT.Mnt_adgroup_data.get_last_day()});
}

PT.Mnt_adgroup_data.table_obj.prototype.change_price_status_4data=function(data){
	var result=data.keyword;
	for (var i in result){
		var kw_id=result[i]['keyword_id'],obj=$('#'+kw_id).data('obj');
		obj.new_price_input.val(result[i]['new_price']);
		obj.nRow.attr('label_code',result[i]['label_code'])
		obj.is_del();
	}
	this.calc_action_count();
	PT.hide_loading();
}

PT.Mnt_adgroup_data.table_obj.prototype.init_scroll_event=function(){
	if($.browser.msie&&Number($.browser.version)<9){
		return;
	}
	var that=this;
	//关键词信息浮动
	$(window).on('scroll.PT.Table',function(){
		if(that.data_table==undefined){
			return;
		}		
		var body_ofset = document.body.scrollTop | document.documentElement.scrollTop;
		var body_ofset_left = document.body.scrollLeft | document.documentElement.scrollLeft;
		var base_top=that.data_table.offset().top-0;
		if (body_ofset>base_top&&base_top>0){
			if(this.fixed_header==undefined){
				this.fixed_header=new FixedHeader(that.data_table,{"offsetTop":0});
			}
		}else{
			if(this.fixed_header!=undefined){
				$(this.fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
			}
			this.fixed_header=null;
		}
	});
}

