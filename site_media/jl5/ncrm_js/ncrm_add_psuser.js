PT.namespace('NcrmAddPSUser');
PT.NcrmAddPSUser = function(){

	var init_dom = function(){
		//日期时间选择器
	    require(['dom', 'gallery/datetimepicker/1.1/index'], function(DOM, Datetimepicker) {
	        new Datetimepicker({
	            start: '#birthday',
	            timepicker: false,
	            closeOnDateSelect : true
	        });
	        new Datetimepicker({
	            start: '#entry_date',
	            timepicker: false,
	            closeOnDateSelect : true
	        });
	        new Datetimepicker({
	            start: '#contract_start',
	            timepicker: false,
	            closeOnDateSelect : true
	        });
	        new Datetimepicker({
	            start: '#contract_end',
	            timepicker: false,
	            closeOnDateSelect : true
	        });
	        new Datetimepicker({
                start: '#probation_date',
                timepicker: false,
                closeOnDateSelect : true
            });
	        
	    });
	    
		$('#add_supplier').vaildata({'placement':'right','call_back':function(obj){
		    PT.show_loading('正在保存数据...')
		    var params = {
		                  'function':'ncrm_save_psuser',
		                  'callback':'PT.NcrmAddPSUser.save_psuser_callback'
		    }
		    var forms = $("#add_supplier").serializeArray();
		    for (var index in forms){
		      params[forms[index].name] = forms[index].value
		    }
	        PT.sendDajax(params);
	    }});
	    
	    //用户名输入框失去焦点后校验其唯一性
	    $('#name').blur(function(){
	       var params = {
	                      'function':'ncrm_check_psuser_name_unique',
	                      'callback':'PT.NcrmAddPSUser.check_psuser_name_callback',
	                      'name':$.trim($(this).val()),
	                      'id':$("#psuser_id_update").val()
	        }
	        PT.sendDajax(params);
	    });
	    
	    $("#reset_pass").click(function(){
		    PT.show_loading('密码重置中...');
	        var params = {
	                  'function':'ncrm_reset_password',
	                  'user_id':$('#psuser_id_update').val(),
	                  'callback':'PT.NcrmAddPSUser.reset_password_callback'
	                }
	        PT.sendDajax(params);
		});
		
		$('#position').change(function () {
			$('#perms').val($('#position option:selected').attr('perms'));
		});
	}
	return {
		init:function(){
			init_dom();
		},
		save_psuser_callback:function(data){
		     if(data.result=="success"){
		          $("#psuser_id_update").val(data.psuser_id);
		          $("#name").attr("readonly","readOnly");
                 PT.alert(data.msg,null,function(){
                    window.close();
                 });
		     }else{
                 PT.alert(data.msg);
             }


        },
        check_psuser_name_callback:function(data){
            if(data.msg!="none"){
                PT.alert(data.msg);
            }
        },
        reset_password_callback:function(data){
            if(data.msg!="none"){
                PT.alert(data.msg);
            }
        }
	}
}();
