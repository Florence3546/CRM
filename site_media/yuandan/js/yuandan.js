PT.namespace('Yuandan');
PT.Yuandan = function () {
	var active_clock = function () {
		var interval_id = Number($('#interval_id').val());
		if (interval_id) {
			window.clearInterval(interval_id);
		}
		interval_id = self.setInterval(function () {
								var today = new Date();
								var tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate()+1);
								var count_down = new Date();
								count_down.setTime(tomorrow-today);
								var hours = count_down.getUTCHours();
								hours = hours<10?'0'+String(hours):String(hours);
								var minutes = count_down.getUTCMinutes();
								minutes = minutes<10?'0'+String(minutes):String(minutes);
								var seconds = count_down.getUTCSeconds();
								seconds = seconds<10?'0'+String(seconds):String(seconds);
								count_down = hours+minutes+seconds;
								$('#yuandan_promotion_countdown span').each(function (i) {
									$(this).html(count_down[i]);
								});
							}, 500);
		$('#interval_id').val(interval_id);
	}
	return {
		init: function () {
			PT.sendDajax({
				'function':'web_get_yuandan_promotion',
				'callback':'PT.Yuandan.init_callback'
				});
		},
		init_callback: function (today_order_count, item_code) {
			var remain_count = today_order_count>100?0:100-today_order_count, promotion_url = '', promotion_img = '';
//			remain_count = 0;
//			item_code = 'ts-25811-1';
			if (remain_count==0) {
				promotion_url = '';
				promotion_img = '/site_media/yuandan/img/0.jpg';
			} else if (item_code=='ts-25811-1') {
                promotion_url = 'http://tb.cn/dUBJBNy';
                promotion_img = '/site_media/yuandan/img/90.jpg';
			} else if (item_code=='ts-25811-8') {
                promotion_url = 'http://tb.cn/aPxIBNy';
                promotion_img = '/site_media/yuandan/img/60.jpg';
            }
            if (remain_count<10) {
	            remain_count = '00'+String(remain_count);
            } else if (remain_count<100) {
                remain_count = '0'+String(remain_count);
            } else {
	            remain_count = String(remain_count);
            }
            if ($('#modal_yuandan_promotion').length==0) {
	            $('body').append(
		            '<div id="modal_yuandan_promotion" class="modal hide fade bd_none" data-width="800">'+
			            '<div class="modal-body p0 rel">'+
				            '<span class="abs r0 poi bg_black white f40 h30 lh24 p0_3 opt7" data-dismiss="modal">×</span>'+
				            '<img src="'+promotion_img+'">'+
				            (promotion_url?
				            '<a href="'+promotion_url+'" id="yuandan_promotion_url" target="_blank" style="position:absolute;top:120px;left:100px;width:610px;height:220px;"></a>'+
				            '<div id="yuandan_promotion_countdown" class="abs white f48 lh40" style="bottom:21px;left:203px;">'+
					            '<input type="hidden" id="interval_id" value="">'+
					            '<span class="dib p0_3 mr10">0</span><span class="dib p0_3 mr15">0</span><span class="dib p0_3 mr10">0</span><span class="dib p0_3 mr15">0</span><span class="dib p0_3 mr10">0</span><span class="dib p0_3">0</span>'+
				            '</div>'+
				            '<div class="abs white f48 lh40" style="bottom:21px;right:12px;">'+
					            '<span class="dib p0_3">'+remain_count[0]+'</span><span class="dib p0_3 ml10">'+remain_count[1]+'</span><span class="dib p0_3 ml10">'+remain_count[2]+'</span>'+
				            '</div>':
				            '<a href="aliim:sendmsg?uid=cntaobao&siteid=cntaobao&touid=cntaobao派生科技" style="position:absolute;bottom:130px;right:120px;"><img src="/site_media/jl5/images/ww.png" width="50" class="vb"/><span class="f20 red b">点击了解</span></a>'+
                            '<div class="abs white f48 lh40" style="bottom:21px;left:203px;">'+
                                '<span class="dib p0_3 mr10">0</span><span class="dib p0_3 mr15">0</span><span class="dib p0_3 mr10">0</span><span class="dib p0_3 mr15">0</span><span class="dib p0_3 mr10">0</span><span class="dib p0_3">0</span>'+
                            '</div>'+
                            '<div class="abs white f48 lh40" style="bottom:21px;right:12px;">'+
                                '<span class="dib p0_3">0</span><span class="dib p0_3 ml10">0</span><span class="dib p0_3 ml10">0</span>'+
                            '</div>'
				            )+
			            '</div>'+
		            '</div>'
	            );
	            if (promotion_url) {
		            active_clock();
		            $('#yuandan_promotion_url').unbind('click');
		            $('#yuandan_promotion_url').click(function () {
			            PT.sendDajax({'function':'web_yuandan_promotion_clicked'});
		            });
	            }
            }
	        $('#modal_yuandan_promotion').modal('show');
		}
	};
}();