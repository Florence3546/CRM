PT.namespace('CheckLib');
PT.CheckLib = function(){
	var all_digit = function(msg){
		var msg = msg.replace(' ','');
		for(var index in msg ){
			var char_num = msg[index].charCodeAt();
			if (char_num < 48 || char_num > 57){
				PT.alert("当前输入框仅允许输入 数字 ，不允许有其他字符。");
				return false
			}
		}
		return true
	}
	
	return {
		all_digit:all_digit
	}
}();
