PT.namespace('Base_adg');
PT.Base_adg = function () {
	var adgroup_id=$('#adgroup_id').val(), campaign_id=$('#campaign_id').val();
	
	var init_dom=function() {

		$('#contact_consult').hover(function(){
			$('#contact_telephone').stop().animate({'marginLeft':0},300);
		},function(){
			$('#contact_telephone').stop().animate({'marginLeft':-181},100);
		});

		$('#show_adgroup_box').click(function(){
			$('#adgroup_box').modal();
			
			if($(this).attr('switch')==undefined){
				get_adgroup_by_id();
				PT.sendDajax({'function':'web_get_adgroup_trend','adgroup_id':adgroup_id,'name_space':'Base_adg'});	
			}
			
			$(this).attr('switch',1);
		});
				
		$('#sync_adg').click(function(){			
			PT.show_loading("正在同步当前宝贝数据，可能用时较长");
			PT.sendDajax({'function':'web_sync_current_adg','adg_id':adgroup_id,'camp_id':campaign_id, 'rpt_days':15});
		});
		
		$('#item_picture').mouseenter(function(){
			$('#item_picture_big').stop().fadeTo(300,1);
		});
		
		$('#item_picture_big').mouseleave(function(){
			$('#item_picture_big').stop().fadeTo(300,0).queue(function(next){
				$(this).hide();
				$(this).dequeue();	
			});	
		});
	};
	
	var get_adgroup_by_id=function(){
		var request_data=['default_price',
						  'item.title',
						  'item.price',
						  'item.pic_url',
						  'item.item_id',
						  'campaign.title',
						  'rpt_sum.impressions',
						  'rpt_sum.click',
						  'rpt_sum.ctr',
						  'rpt_sum.cpc',
						  'rpt_sum.paycount',
						  'rpt_sum.favcount',
						  'rpt_sum.conv',
						  'rpt_sum.roi',
						  'rpt_sum.favcount',
						  'rpt_sum.cost',
						  'rpt_sum.pay',
						  'online_status'
						  ];
		request_data=$.toJSON(request_data)
		PT.sendDajax({'function':'web_get_adgroup_by_id','adgroup_id':adgroup_id,data:request_data,call_back:'PT.Base_adg.adgroup_callback','last_day':$('#adgroup_last_day').val(),'auto_hide':0});
	}

	return {
        init: function (){
			PT.initDashboardDaterange();
			init_dom();
        },
		show_adgroup_trend:function(category_list,series_cfg_list){
			PT.draw_trend_chart( 'adgroup_trend_chart', category_list, series_cfg_list);
		},
		adgroup_callback:function(data){
			var dom=template.render('template_adgroup_info',data);
			$('#adgroup_detail_box').html(dom);
			$('#adgroup_detail_box i.tooltips').tooltip();
			$('#adgroup_info_tip').hide();
		},
		adgroup_select_call_back:function(day){
			$('#adgroup_last_day').val(day);
			$('#adgroup_info_tip').show();
			get_adgroup_by_id();
		},
		sync_adg_back:function(msg){
			msg+='即将刷新页面';
			PT.confirm(msg,function(){window.location.reload();});
		}
	}
}();