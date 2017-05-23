PT.namespace('SysCssType');
PT.SysCssType = function(){
	var system_input_default_bind = function(obj){
		// 该方法需要保证两点： 1) obj 元素应为 input[type=text] 元素 2) 该元素中一定要含有 default_title属性
		$(obj).focus(PT.SysCssType.Input.input_default_title_focus);
		$(obj).blur(PT.SysCssType.Input.input_default_title_blur);
	}
	
	var system_checkbox_msg_bind = function(obj,msg){
		// 该方法需要保证： obj 元素应为 input[type=checkbox] 元素
		// 效果： 在当前checkbox元素后面添加一个span消息元素 
		$(obj).click(function(){
			var avgs = {'msg':msg};
			PT.SysCssType.CheckBox.check_box_exec(this, PT.SysCssType.CheckBox.generete_next_span_msg,PT.SysCssType.CheckBox.remove_next_span_msg,avgs);
		})
	}
	
	return {
		system_input_default_bind:system_input_default_bind,
		system_checkbox_msg_bind:system_checkbox_msg_bind
	}
}();

PT.namespace('SysCssType.Input')
PT.SysCssType.Input = function(){
	// input 默认值事件，要求：元素需定义两个属性 1) sys_type = input_default_title    2) default_title : 默认名称
	var INPUT_LOST_DEFAULT_TITLE_COLOR = 'black' ;
	var INPUT_RESTORE_DEFAULT_TITLE_COLOR = 'gray' ;
	
	var input_default_title_focus = function(){
		var obj = $(this);
		var title = obj.attr("default_title");
		
		// 此处是否考虑接口提示，以下系统方法都没有添加接口提示功能
//		if(title == undefined){
//			PT.alert('使用系统类型 input_default_title_focus 元素需要提供属性 default_title, 如：default_title="类目ID"')
//			return
//		}
		
		if (title == obj.val()){
			obj.css({"color":INPUT_LOST_DEFAULT_TITLE_COLOR});
			obj.val("");
		}
	} ;
	
	var input_default_title_blur = function(){
		var obj = $(this);
		var title = obj.attr("default_title");
		if (obj.val() == undefined || obj.val() == ""){
			obj.css({"color":INPUT_RESTORE_DEFAULT_TITLE_COLOR});
			obj.val(title);
		}
	} ; 
	 
	var input_group_only_one = function(default_title,input_list){
		for(var i = 0 ; i < input_list.length ; i++){
			var temp = $(input_list[i]);
			var temp_title = temp.attr("default_title");
			if (temp_title != default_title){
				temp.css({"color":INPUT_RESTORE_DEFAULT_TITLE_COLOR});
				temp.val(temp_title);
			}
		}
	} ;
	
	return {
		input_default_title_focus:input_default_title_focus,
		input_default_title_blur:input_default_title_blur,
		input_group_only_one:input_group_only_one
	}
}();

PT.namespace('SysCssType.CheckBox')
PT.SysCssType.CheckBox = function(){
	var generete_next_span_msg = function(obj,avgs){
		var obj = $(obj);
		var msg = avgs.msg;
		var span_element = '<span style="color:red">&nbsp;'+msg+'&nbsp;</span>' ; 
		$(obj).after(span_element);
	};
	
	var remove_next_span_msg = function(obj,avgs){
		var obj = $(obj);
		var msg = avgs.msg;
		var next_obj = obj.next();
		if (next_obj.length > 0 && next_obj[0].tagName.toUpperCase() == "SPAN"){
			var content = next_obj.text().replace(/\s/g , '');
			var msg = msg.replace(/\s/g , '');
			if(content == msg){
				next_obj.remove();
			}
		}	
	}
	
	// 判定checkbox执行方式
	var check_box_exec = function(obj, success_func,fail_func,avgs){
		var check_flag = $(obj).attr('checked');
		if (check_flag != undefined){
			success_func(obj,avgs);
		}else{
			fail_func(obj,avgs);
		}
	} ;
	
	return {
		check_box_exec:check_box_exec,
		generete_next_span_msg:generete_next_span_msg,
		remove_next_span_msg:remove_next_span_msg
	}
}();

