PT.namespace('NcrmPsuserRoster');
PT.NcrmPsuserRoster = function(){


    var userTable;
    var get_data_by_params = function(){

        var gender = $("#gender").val();
        var department = $("#department").val();
        var position = $("#position").val();
        var status = $("#status").val();
        var searchtxt = $("#searchtxt").val();
        var date = $("#date").val();
        var date_min = $("#date_min").val();
        var date_max = $("#date_max").val();
        
        var date_cell_num = 0;
        //时间选择条件
        if(date=='生日日期'){
            date_cell_num = 7;
        }else if (date=='合同截止日期'){
            date_cell_num = 6;
        }else if (date=='入职日期'){
            date_cell_num = 5;
        }
        var all_tr = $("#psuser tbody tr");
        var result_size = 0;
        
        all_tr.each(function(){
            var flag = true;
            var _gender = $(this).children('td').eq(1).html();
            var _department = $(this).children('td').eq(2).html();
            var _position = $(this).children('td').eq(3).html();
            var _status = $(this).children('td').eq(4).html();
            
            var _name_cn = $(this).children('td').eq(0).html();
            var _qq = $(this).children('td').eq(10).html();
            var _ww = $(this).children('td').eq(9).html();

            //判断是否满足文字输入区域条件
            if(_name_cn.indexOf(searchtxt)<0&&_qq.indexOf(searchtxt)<0
                &&_ww.indexOf(searchtxt)<0){
                flag = false;
            }

            //判断是否下拉框选择条件
            if(_gender.indexOf(gender)<0){
               flag = false;
            }
            if(_department.indexOf(department)<0){
               flag = false;
            }
            if(_position.indexOf(position)<0){
               flag = false;
            }
            if(_status.indexOf(status)<0 || (status=='' && _status == '离职')){
               flag = false;
            }
            
            //时间选择条件
            if(date_cell_num>0){
                var _date = $(this).children('td').eq(date_cell_num).html();
                
                if(_date==""){
                    flag = false;
                }
	            if(new Date(_date)<new Date(date_min)){
	                 flag = false;
	            }
	            
	            if(new Date(_date)>new Date(date_max)){
                     flag = false;
                }
            }
     
            //当所有条件都满足时则显示，只要有一个条件不满足，则不显示
            if(flag){
                $(this).show();
                result_size+=1;
            }else{
                $(this).hide();
            }
        });
        
        $("#psuser_info").html("总共"+result_size+"条记录");
        
        $("#search").attr("value","搜索("+result_size+")")
    }

	
	var	init_table = function() {
        if(userTable){
            userTable.fnClearTable();
            userTable.fnDestroy();
        }
        userTable = $('table[id=psuser]').dataTable({
            'autoWidth': false,
            'bDestroy': true,
            'aaSorting': [
                [0, 'desc']
            ],
            'iDisplayLength': 1000,
            'sDom': "T<'row-fluid't<'row-fluid mt10'<'span12 pl10'i><'span12 pr10 tr'p>>",
            'oLanguage': {
                'sInfo': '总共_TOTAL_条记录',
                'sInfoEmpty': '',
                'sEmptyTable': '正在获取数据.......',
                'sZeroRecords': '亲，没有找到匹配的关键词',
                'sInfoFiltered': '(从 _MAX_ 条记录中过滤)',
                'oPaginate': {
                    'sNext': '下一页',
                    'sPrevious': '上一页'
                }
            }
        });
    }

	var init_dom=function(){
	  	//日期时间选择器
	    require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
	        var startDate = new Datetimepicker({
	            start: '#date_min',
	            timepicker: false,
	            closeOnDateSelect : true
	        });
	        var endDate = new Datetimepicker({
	            start: '#date_max',
	            timepicker: false,
	            closeOnDateSelect : true
	        });
	        
	        startDate.on('hidePanel',function(){
               get_data_by_params();
            })
	        
	        endDate.on('hidePanel',function(){
	           get_data_by_params();
	        })
	    });

	    $("#reset").click(function(){
	    	$("#psuser tbody tr").show();
	    	$("#psuser_info").html("总共"+$("#psuser tbody tr").length+"条记录");
	    	$("#search").attr("value","搜索("+$("#psuser tbody tr").length+")")
	    });
	    
	    $("#searchdiv").change(function(){
	    	get_data_by_params();
	    });
	    
	    $("#searchtxt").keyup(function(e){
            if (e.keyCode==13) {
                get_data_by_params();
            }
	    });
	    
		$("#search").click(function(){
			get_data_by_params();
		});		
		
		$("#search").attr("value","搜索("+$("#psuser tbody tr").length+")")
	}
		
	return {
		init:function(){
			init_dom();
			init_table();
		}
	}
}();