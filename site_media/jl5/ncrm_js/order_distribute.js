PT.namespace('OrderDistribute');
PT.OrderDistribute = function() {


    var init_dom = function() {


    	require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#id_order_start_date',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '#id_order_end_date',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '#id_distribute_start_date',
                timepicker: false,
                closeOnDateSelect : true
            });

            new Datetimepicker({
                start: '#id_distribute_end_date',
                timepicker: false,
                closeOnDateSelect : true
            });
        });

    	$("#search_order_distribute").click(function(){
    	   PT.show_loading("正在查询订单");
    	   $('#form_search_order_distribute').submit();
    	});

    	// 自定义表单重设按钮
        $('#reset_form').click(function () {
	        $('#form_search_order_distribute :text:visible').val('');
	        $('#form_search_order_distribute input').val('');
	        $('#form_search_order_distribute #id_page_no').find("option").first().attr({"selected":"selected"});
            $('#form_search_order_distribute #id_category').val("");
        });
    }

    return {
        init: function() {
            init_dom();
        }
    }
}();
