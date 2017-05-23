PT.namespace('WorkBenchOperator');
PT.WorkBenchOperator = function() {

	var init_sort=function(){
		if($('#id_operate_workbench>tbody>tr:eq(0)>td').length>1){
			PT.operate_workbench=$('#id_operate_workbench').dataTable({
				"bPaginate": false,
				"bFilter": false,
				"bInfo": false,
				"aoColumns": [{"bSortable": false},
				              {"bSortable": true},
				              {"bSortable": true},
				              {"bSortable": true},
				              {"bSortable": true},
				              {"bSortable": true},
				              {"bSortable": true},
				              {"bSortable": true},
				              {"bSortable": true},
				              {"bSortable": false},
				              {"bSortable": false},
				              {"bSortable": false},
				              ]
			});
		}
	};
	
    var init_dom = function() {
    	//日期时间选择器
        require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
            new Datetimepicker({
                start: '#order_end_startdate',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_end_enddate',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_create_startdate',
                timepicker: false,
                closeOnDateSelect : true
            });
            new Datetimepicker({
                start: '#order_create_enddate',
                timepicker: false,
                closeOnDateSelect : true
            });
        });
        
        init_sort();
    	
    	$('.show_more').click(function(){
    		var pos = parseInt($(this).attr('position'));
    		if(pos>0){
    			$(this).parent().removeClass('h160');
    			$(this).text('收起');
    			$(this).attr('position', -1);
    		}else{
    			$(this).parent().addClass('h160');
    			$(this).text('展开');
    			$(this).attr('position', 1);
    		}
    	});
    	
        $('.tips').tooltip();
    };

    return {
        init: function() {
            init_dom();
        },
    }
}();
