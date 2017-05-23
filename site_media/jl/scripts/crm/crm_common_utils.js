PT.namespace('CommonUtils')
PT.CommonUtils = function(){
	var get_checkbox_val = function(obj){
		var value = 0;
    	if ($(obj).attr('checked') != undefined){
    		value = 1;
    	}
    	return value
	}
	
	return {
		checkbox_val : get_checkbox_val
	}
	
}();