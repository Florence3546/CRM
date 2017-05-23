PT.namespace('Attention');
PT.Attention = function () {
	
	var get_last_day=function (){
		return $('#dashboard-report-range').find('input[name="last_day"]').val();
	}
	
	var show_big_pic=function(obj){
		obj.table_obj.find('.item_picture').tooltip({
			'trigger':'hover',
			'title':get_picture_html,
			'html':true,
			'placement':'right'
		});
	}
	
	var get_picture_html=function(){
		eval("var data="+$(this).attr('data'));
		return template.render('template_item_picture',data);
	}

	var init_table=function(){
		PT.instance_table=new PT.Attention.table_obj('common_table','template_common_table_tr');
		PT.instance_table.init_ajax_event_list.push(show_big_pic);
	}
	
	var auto_set_attention_kw = function(is_check_rpt) {
		PT.show_loading('正在设置关注词');
        PT.sendDajax({'function': 'qnpc_auto_set_attention_kw'});
    }
	
	var init_dom=function(){
		$('#auto_set_attention_kw').click(function(){
			auto_set_attention_kw();
		});
	}

    return {
        //main function to initiate the module
        init: function () {
			PT.initDashboardDaterange();
			init_dom();
			PT.Base.set_nav_activ(2,2);
            init_table();
        },
		get_last_day:get_last_day
		,
		table_callback: function(data){
			PT.instance_table.call_back(data);
		},
		select_call_back:function(){
			PT.instance_table.loading_table();
			PT.instance_table.data_table.fnDestroy();			
			PT.instance_table.get_keyword_data();
		},
		confirm_download_rpt:function(){
			PT.show_loading('正在下载报表');
			window.location.reload();
		}
    }

}();


//继承PT.Table.BaseTableObj的属性
PT.Attention.table_obj=function(table_id,temp_id){
	PT.Table.BaseTableObj.call(this,table_id,temp_id);	
}
//继承PT.Table.BaseTableObj的属性方法
PT.Attention.table_obj.prototype=PT.Table.BaseTableObj.prototype;

//获取关键词列表
PT.Attention.table_obj.prototype.get_keyword_data=function(){
	PT.sendDajax({'function':'web_get_attention_list','last_day':PT.Attention.get_last_day()});
}

//重写后台回调函数
PT.Attention.table_obj.prototype.call_back=function(json){
	if(json.keyword.length){
		this.recount_table_width(json.custom_column);
		this.layout_keyword(json);
		this.sort_table(json.custom_column);
		$('#loading_keyword').hide();
		$('#fixed_box').show();
	}else{
		$('#loading_keyword').hide();
		$('#no_keyword').show();	
	}
	this.update_all_style();
}

//填充表格数据
PT.Attention.table_obj.prototype.layout_keyword=function(json){
	PT.console('begin layout keyword');
	var tr_str=[],kw_count=0,d;
	
	for (d in json.keyword){
		if(!isNaN(d)){
			tr_str+=template.render(this.temp_id,json.keyword[d]);
			kw_count++;
		}
	}
	this.table_obj.find('tbody tr:not(#nosearch_table)').remove();
	this.table_obj.find('tbody').append(tr_str);
}

PT.Attention.table_obj.prototype.init_scroll_event=function(){
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
		var base_top=that.data_table.offset().top-40;
		if (body_ofset>base_top&&base_top>0){
			$('#fixed_box').addClass('active').css({'marginLeft':-body_ofset_left+16,'width':$('#fixed_box').parent().width()});
			if(this.fixed_header==undefined){
				this.fixed_header=new FixedHeader(that.data_table,{"offsetTop":40});
			}
		}else{
			$('#fixed_box').removeClass('active').css({'marginLeft':0,'width':'auto'});

				if(this.fixed_header!=undefined){
					$(this.fixed_header.fnGetSettings().aoCache[0].nWrapper).remove();
				}
				this.fixed_header=null;	

		}
	});
}