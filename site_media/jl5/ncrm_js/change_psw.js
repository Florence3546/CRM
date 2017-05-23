PT.namespace('ChangePsw');
PT.ChangePsw = function() {

	var display_error = function(index, msg){
		$('.error_hint:eq('+index+')').text(msg);
		$('.error_hint:eq('+index+')').removeClass('hide');
		$('.hint:eq('+index+')').addClass('hide');
	}
	
	var hide_error = function(index){
		$('.error_hint:eq('+index+')').addClass('hide');
	}
	
    var init_dom = function() {
    	
    	$('#save_psw').click(function(){
    		var old_psw = $('#id_old_password').val();
    		var new_psw = $('#id_password').val();
    		if(old_psw==''){
    			display_error(0, "请输入旧密码！");
    			return false;
    		}else{
    			hide_error(0);
    		}
    		if(new_psw==''){
    			display_error(1, "请输入新密码！");
    			return false;
    		}else{
    			hide_error(1);
    		}
    		if(new_psw != $('#id_repsw').val()){
    			display_error(2, "新旧密码不一致哟亲！");
    			return false;
    		}else{
    			PT.sendDajax({'function':'ncrm_change_psw', 'old_psw':old_psw, 'new_psw':new_psw});
    		}
    	});
    };

    return {
        init: function() {
            init_dom();
        },
        
    }
}();
