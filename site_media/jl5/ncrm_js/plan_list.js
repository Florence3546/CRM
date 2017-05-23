PT.namespace('PlanList');
PT.PlanList = function() {

    var init_dom = function() {
		//日期时间选择器
		require(['dom', 'gallery/datetimepicker/1.1/index'], function (DOM, Datetimepicker) {
		    var b,c;
		    b= new Datetimepicker({
		            start : '#start_time',
		            timepicker:false,
                    closeOnDateSelect : true
		        });
		    c= new Datetimepicker({
		            start : '#end_time',
		            timepicker:false,
                    closeOnDateSelect : true
		        });
		});

    }

    return {
        init: function() {
            init_dom();
        },
        loading_plan_process:function(){
            var id_list = [];
            var tr_list =  $("#plan_list_table>tbody>tr");
            for ( var i = 0 ; i < tr_list.length ; i++){
                var plan_id = $(tr_list[i]).attr('plan_id').replace(/\s/g,'');
                if(/[0-9]+/.test(plan_id)){
                    id_list.push(plan_id);
                }
            }
            if(id_list.length > 0 ){
                PT.sendDajax({
	               'function':'ncrm_get_plan_list_info',
	               'plan_id_list':$.toJSON(id_list),
	               'call_back':'PT.PlanList.get_plan_list_info_back'
	             });
            }
        },
        get_plan_list_info_back:function(json){
			if ( json.error == ""){
                for(var plan_id in json.data){
                    var data = json.data[plan_id];
                    var html = template.render('plan_process_div',{"data":data ,"describption":json.describption});
                    $("#plan_list_table tbody tr[plan_id="+plan_id+"] .plan_process").html(html);

                }

                $("#plan_list_table tbody tr .event_detail").click(function(){
                    var obj = $(this);
                    var tr_obj = obj.parents("tr:first");
                    var plan_id = tr_obj.attr('plan_id');
                    var event_name = obj.attr("event_name");

                    var counter = obj.attr("counter");
                    if(parseInt(counter) > 0){
	                    if(parseInt(plan_id) > 0 && event_name != ""){
	                       PT.show_loading("正在获取数据");
		                    PT.sendDajax({
			                   'function':'ncrm_get_plan_event_detail',
			                   'plan_id':plan_id,
			                   'event_name':event_name,
			                   'call_back':'PT.PlanList.plan_event_detail_back'
			                 });
	                    } else {
	                        PT.alert("出错，请联系开发人员");
	                    }
                    } else {
                        PT.alert("当前指标为0，无任何详情数据。");
                    }
                });
			} else {
			    PT.alert(json.error);
			}
        },
        plan_event_detail_back:function(json){
            if ( json.error == ""){
                if ( json.data.length > 0 ){
	                var mark = json.mark;
	                var model_id = "id_"+mark+"_layout";
	                var tr_id = "id_"+mark+"_layout_tr";
	                var html = "";
	                for(var i=0 ; i < json.data.length ; i ++){
	                    var data = json.data[i];
	                    template.isEscape = false;
	                    html += template.render(tr_id,data);
	                    template.isEscape = true;
	                }
	                $("#"+model_id+" .content").html(html);
	                $("#"+model_id+" .user_counter").html(json.shop_counter);
	                $("#"+model_id).modal();
                } else {
                    PT.alert("当前指标为0，无任何详情数据。");
                }
            } else {
                PT.alert(json.error);
            }
        }
    }
}();
