PT.namespace('ShortMessageManange');
PT.ShortMessageManange = function() {
    var disable_send_sm = function () {
	    $('#recv_count').html('--');
	    $('#send_sm').attr('disabled', true);
    }

    var check_sm = function () {
	    if ($('#recv_count').html()=='--' || $('#send_sm').attr('disabled')) {
		    PT.alert('先点击确定目标客户');
	    } else if ($('#recv_count').html()=='0' || $('#send_sm').data('shop_ids').length==0) {
            PT.alert('未找到目标客户');
        } else if (!$.trim($('#title').val())) {
            PT.alert('必须填写标题');
        } else if (!$.trim($('#content').val())) {
            PT.alert('必须填写短信内容');
        } else {
            return true;
        }
    }
    
    var refresh_content_length = function () {
	    $('#content_length').html($('#content').val().length);
    }
    
    var init_dom = function() {

        //日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#order_end_starttime',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_end_endtime',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_create_endtime',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_create_starttime',
                timepicker: false,
                closeOnDateSelect : true
            });

        });
        
        $('#filter_form input, #filter_form select').change(disable_send_sm);
        
        $('#content').keyup(refresh_content_length);
        
	    $('#get_recv_count').click(function () {
		    PT.show_loading('正在计算目标客户数量');
		    PT.sendDajax({
			    'function':'ncrm_get_recv_count',
			    'nick':$('#nick').val(),
			    'order_create_starttime':$('#order_create_starttime').val(),
			    'order_create_endtime':$('#order_create_endtime').val(),
			    'order_end_starttime':$('#order_end_starttime').val(),
			    'order_end_endtime':$('#order_end_endtime').val(),
			    'order_cycle':$('#order_cycle').val(),
			    'pay_start':$('#pay_start').val(),
			    'pay_end':$('#pay_end').val(),
			    'contact_start':$('#contact_start').val(),
			    'contact_end':$('#contact_end').val(),
			    'consult':$('#consult').val(),
			    'category':$('#category').val(),
			    'callback':'PT.ShortMessageManange.get_recv_count_callback'
		    });
	    });
	    
	    $('#send_sm').click(function () {
	        if (check_sm()) {
		        PT.confirm('确定要发送吗？', function () {
			        PT.show_loading('正在发送短信');
			        PT.sendDajax({
			            'function':'ncrm_send_sm',
			            'shop_ids':$.toJSON($('#send_sm').data('shop_ids')),
			            'condition':$.toJSON($('#send_sm').data('condition')),
			            'title':$('#title').val(),
			            'content':$('#content').val(),
			            'callback':'PT.ShortMessageManange.send_sm_callback'
			        });
		        }, null, null);
	        }
	    });
        
        $('#table_sm').on('click', 'a.show', function () {
	        disable_send_sm();
	        var sm = $(this).closest('tr');
	        $('#recv_count').html(sm.attr('send_count'));
	        $('#title').val(sm.attr('title'));
	        $('#content').val(sm.attr('content'));
	        refresh_content_length();
	        var condition = $.evalJSON(sm.attr('condition') || '{}');
	        $('#nick').val(condition.nick);
	        $('#order_create_starttime').val(condition.order_create_starttime);
	        $('#order_create_endtime').val(condition.order_create_endtime);
	        $('#order_end_starttime').val(condition.order_end_starttime);
	        $('#order_end_endtime').val(condition.order_end_endtime);
	        $('#order_cycle').val(condition.order_cycle);
	        $('#pay_start').val(condition.pay_start);
	        $('#pay_end').val(condition.pay_end);
	        $('#contact_start').val(condition.contact_start);
	        $('#contact_end').val(condition.contact_end);
	        $('#consult').val(condition.consult);
	        $('#category').val(condition.category);
	        $(document).scrollTop(0);
        });
	    
	    $('#table_sm').on('click', 'a.retry', function () {
		    PT.show_loading('正在重试发送短信');
		    PT.sendDajax({
		        'function':'ncrm_send_sm',
		        'sm_id':$(this).closest('tr').attr('id'),
		        'content':$(this).closest('tr').attr('content'),
                'callback':'PT.ShortMessageManange.send_sm_callback'
		    });
	    });

    };

    return {
        init: function() {
            init_dom();
        },
        disable_send_sm:disable_send_sm,
        get_recv_count_callback: function (_shop_ids, _condition) {
            $('#recv_count').html(_shop_ids.length);
            $('#send_sm').data('shop_ids', _shop_ids);
            $('#send_sm').data('condition', _condition);
	        $('#title').attr('disabled', false);
	        $('#content').attr('disabled', false);
	        $('#send_sm').attr('disabled', false);
        },
        send_sm_callback: function (send_count, tmoney) {
	        var msg = '给'+send_count+'个客户发送了短信';
	        if (tmoney!=null) {
		        msg+='，平台余额为'+tmoney+'元';
	        }
	        PT.alert(msg, null, function () {PT.show_loading('正在刷新页面');window.location.reload();});
        }
    }
}();
